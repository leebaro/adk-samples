# Copyright 2025 Google LLC
# 이 파일은 데이터베이스 에이전트가 사용하는 도구들을 포함합니다.

# Functions:

# - _serialize_value_for_sql(value)
#     - 판다스 DataFrame의 파이썬 값을 BigQuery SQL 리터럴로 직렬화합니다.
#     - NaN, 문자열, 바이트, 날짜/시간, 리스트, 딕셔너리 등 다양한 타입을 SQL에 맞게 변환합니다.

# - get_bq_client()
#     - BigQuery 클라이언트를 반환합니다.
#     - 전역 bq_client가 없으면 환경 변수에서 프로젝트 ID를 읽어 새 클라이언트를 생성합니다.

# - get_database_settings()
#     - 데이터베이스 설정 정보를 반환합니다.
#     - 전역 database_settings가 없으면 update_database_settings()로 초기화합니다.

# - update_database_settings()
#     - 데이터베이스 설정 정보를 갱신합니다.
#     - BigQuery 스키마 정보를 읽어오고, 프로젝트/데이터셋 ID, ChaseSQL 상수 등을 포함한 딕셔너리를 반환합니다.

# - get_bigquery_schema(dataset_id, data_project_id, client=None, compute_project_id=None)
#     - BigQuery 데이터셋의 스키마와 예시값을 포함한 DDL을 생성합니다.
#     - 테이블, 뷰, 외부테이블(특히 ICEBERG 포맷) 등 다양한 테이블 타입을 처리합니다.
#     - 각 테이블에 대해 CREATE TABLE/VIEW/EXTERNAL TABLE DDL을 생성하고, 샘플 데이터를 INSERT문으로 추가합니다.

# - initial_bq_nl2sql(question: str, tool_context: ToolContext) -> str
#     - 자연어 질문을 받아 BigQuery SQL 쿼리를 생성합니다.
#     - 데이터베이스 스키마와 가이드라인을 포함한 프롬프트를 LLM에 전달하여 SQL을 생성합니다.
#     - 생성된 SQL을 tool_context.state에 저장합니다.

# - run_bigquery_validation(sql_string: str, tool_context: ToolContext) -> str
#     - BigQuery SQL 쿼리의 문법 및 실행 가능성을 검증합니다.
#     - SQL 문자열을 정제(cleanup)하고, DML/DDL 문이 포함되어 있으면 거부합니다.
#     - BigQuery에 dry-run으로 쿼리를 실행하여 결과를 확인하고, 결과 또는 오류 메시지를 반환합니다.

# 상수:
# - MAX_NUM_ROWS: 반환할 최대 행 수(기본값 80)
# - data_project, compute_project, vertex_project, location: 환경 변수에서 읽은 프로젝트/위치 정보
# - llm_client: Vertex AI 기반 LLM 클라이언트

#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This file contains the tools used by the database agent."""

import datetime
import logging
import os
import re

import numpy as np
import pandas as pd
from data_science.utils.utils import get_env_var
from google.adk.tools import ToolContext
from google.cloud import bigquery
from google.genai import Client

from .chase_sql import chase_constants

# Assume that `BQ_COMPUTE_PROJECT_ID` and `BQ_DATA_PROJECT_ID` are set in the
# environment. See the `data_agent` README for more details.
data_project = os.getenv("BQ_DATA_PROJECT_ID", None)
compute_project = os.getenv("BQ_COMPUTE_PROJECT_ID", None)
vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT", None)
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
llm_client = Client(vertexai=True, project=vertex_project, location=location)

MAX_NUM_ROWS = 80


def _serialize_value_for_sql(value):
    """Serializes a Python value from a pandas DataFrame into a BigQuery SQL literal."""
    if pd.isna(value):
        return "NULL"
    if isinstance(value, str):
        # Escape single quotes and backslashes for SQL strings.
        return f"'{value.replace('\\', '\\\\').replace("'", "''")}'"
    if isinstance(value, bytes):
        return f"b'{value.decode('utf-8', 'replace').replace('\\', '\\\\').replace("'", "''")}'"
    if isinstance(value, (datetime.datetime, datetime.date, pd.Timestamp)):
        # Timestamps and datetimes need to be quoted.
        return f"'{value}'"
    if isinstance(value, (list, np.ndarray)):
        # Format arrays.
        return f"[{', '.join(_serialize_value_for_sql(v) for v in value)}]"
    if isinstance(value, dict):
        # For STRUCT, BQ expects ('val1', 'val2', ...).
        # The values() order from the dataframe should match the column order.
        return f"({', '.join(_serialize_value_for_sql(v) for v in value.values())})"
    return str(value)


database_settings = None
bq_client = None


def get_bq_client():
    """Get BigQuery client."""
    global bq_client
    if bq_client is None:
        bq_client = bigquery.Client(
            project=get_env_var("BQ_COMPUTE_PROJECT_ID"))
    return bq_client


def get_database_settings():
    """Get database settings."""
    global database_settings
    if database_settings is None:
        database_settings = update_database_settings()
    return database_settings


def update_database_settings():
    """Update database settings."""
    global database_settings
    ddl_schema = get_bigquery_schema(
        dataset_id=get_env_var("BQ_DATASET_ID"),
        data_project_id=get_env_var("BQ_DATA_PROJECT_ID"),
        client=get_bq_client(),
        compute_project_id=get_env_var("BQ_COMPUTE_PROJECT_ID")
    )
    database_settings = {
        "bq_project_id": get_env_var("BQ_DATA_PROJECT_ID"),
        "bq_dataset_id": get_env_var("BQ_DATASET_ID"),
        "bq_ddl_schema": ddl_schema,
        # Include ChaseSQL-specific constants.
        **chase_constants.chase_sql_constants_dict,
    }
    return database_settings


def get_bigquery_schema(dataset_id,
                        data_project_id,
                        client=None,
                        compute_project_id=None):
    """Retrieves schema and generates DDL with example values for a BigQuery dataset.

    Args:
        dataset_id (str): The ID of the BigQuery dataset (e.g., 'my_dataset').
        data_project_id (str): Project used for BQ data.
        client (bigquery.Client): A BigQuery client.
        compute_project_id (str): Project used for BQ compute.

    Returns:
        str: A string containing the generated DDL statements.
    """

    if client is None:
        client = bigquery.Client(project=compute_project_id)

    # dataset_ref = client.dataset(dataset_id)
    dataset_ref = bigquery.DatasetReference(data_project_id, dataset_id)

    ddl_statements = ""

    # Query INFORMATION_SCHEMA to robustly list tables. This is the recommended
    # approach when a dataset may contain BigLake tables like Apache Iceberg,
    # as the tables.list API can fail in those cases.
    info_schema_query = f"""
        SELECT table_name
        FROM `{data_project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
    """
    query_job = client.query(info_schema_query)

    for table_row in query_job.result():
        table_ref = dataset_ref.table(table_row.table_name)
        table_obj = client.get_table(table_ref)

        if table_obj.table_type == "VIEW":
            view_query = table_obj.view_query
            ddl_statements += (
                f"CREATE OR REPLACE VIEW `{table_ref}` AS\n{view_query};\n\n"
            )
            continue
        elif table_obj.table_type == "EXTERNAL":
            if (
                table_obj.external_data_configuration
                and table_obj.external_data_configuration.source_format
                == "ICEBERG"
            ):
                config = table_obj.external_data_configuration
                uris_list_str = ",\n    ".join(
                    [f"'{uri}'" for uri in config.source_uris]
                )

                # Build column definitions from schema
                column_defs = []
                for field in table_obj.schema:
                    col_type = field.field_type
                    if field.mode == "REPEATED":
                        col_type = f"ARRAY<{col_type}>"
                    column_defs.append(f"  `{field.name}` {col_type}")
                columns_str = ",\n".join(column_defs)

                ddl_statements += f"""CREATE EXTERNAL TABLE `{table_ref}` (
{columns_str}
)
WITH CONNECTION `{config.connection_id}`
OPTIONS (
  uris = [{uris_list_str}],
  format = 'ICEBERG'
);\n\n"""
            # Skip DDL generation for other external tables.
            continue
        elif table_obj.table_type == "TABLE":
            column_defs = []
            for field in table_obj.schema:
                col_type = field.field_type
                if field.mode == "REPEATED":
                    col_type = f"ARRAY<{col_type}>"
                col_def = f"  `{field.name}` {col_type}"
                if field.description:
                    # Use OPTIONS for column descriptions
                    col_def += (
                        " OPTIONS(description='"
                        f"{field.description.replace("'", "''")}')"
                    )
                column_defs.append(col_def)

            ddl_statement = (
                f"CREATE OR REPLACE TABLE `{table_ref}` "
                f"(\n{',\n'.join(column_defs)}\n);\n\n"
            )

            # Add example values if available by running a query. This is more
            # robust than list_rows, especially for BigLake tables like Iceberg.
            try:
                sample_query = f"SELECT * FROM `{table_ref}` LIMIT 5"
                rows = client.query(sample_query).to_dataframe()

                if not rows.empty:
                    ddl_statement += f"-- Example values for table `{table_ref}`:\n"
                    for _, row in rows.iterrows():
                        values_str = ", ".join(
                            _serialize_value_for_sql(v) for v in row.values
                        )
                        ddl_statement += (
                            f"INSERT INTO `{table_ref}` VALUES ({values_str});\n\n"
                        )
            except Exception as e:
                logging.warning(
                    f"Could not retrieve sample rows for table {table_ref.path}: {e}"
                )
                ddl_statement += f"-- NOTE: Could not retrieve sample rows for table {table_ref.path}.\n\n"

            ddl_statements += ddl_statement
        else:
            # Skip other types like MATERIALIZED_VIEW, SNAPSHOT etc.
            continue

    return ddl_statements


def initial_bq_nl2sql(
    question: str,
    tool_context: ToolContext,
) -> str:
    """Generates an initial SQL query from a natural language question.

    Args:
        question (str): Natural language question.
        tool_context (ToolContext): The tool context to use for generating the SQL
          query.

    Returns:
        str: An SQL statement to answer this question.
    """

    # prompt_template 변수의 값(영문)을 한국어로 번역한 주석:
    #
    # 당신은 BigQuery SQL 전문가로서, 사용자의 BigQuery 테이블 관련 질문에 대해 SQL 쿼리를 생성하여 답변하는 역할을 맡고 있습니다. 주어진 컨텍스트를 활용하여 아래 질문에 답하는 BigQuery SQL 쿼리를 작성하세요.
    #
    # **가이드라인:**
    #
    # - **테이블 참조:** 항상 SQL 문에서 데이터베이스 접두사가 포함된 전체 테이블 이름을 사용하세요. 테이블은 백틱(`)으로 감싸서 완전한 이름(예: `project_name.dataset_name.table_name`)으로 참조해야 합니다. 테이블 이름은 대소문자를 구분합니다.
    # - **조인:** 가능한 한 적은 수의 테이블만 조인하세요. 테이블을 조인할 때는 모든 조인 컬럼의 데이터 타입이 동일한지 확인하세요. 데이터베이스와 제공된 테이블 스키마를 분석하여 컬럼과 테이블 간의 관계를 이해하세요.
    # - **집계:** SELECT 문에서 집계하지 않은 모든 컬럼은 GROUP BY 절에 포함하세요.
    # - **SQL 문법:** BigQuery에 맞는 구문적, 의미적으로 올바른 SQL을 반환하세요. (project_id, owner, table, column 관계를 올바르게 매핑) SQL의 AS 문을 사용하여 컬럼이나 테이블에 임시 이름을 부여할 수 있습니다. 항상 서브쿼리와 유니온 쿼리는 괄호로 감싸세요.
    # - **컬럼 사용:** *반드시* 테이블 스키마에 명시된 컬럼명(column_name)만 사용하세요. 다른 컬럼명은 사용하지 마세요. 테이블 스키마에 명시된 column_name은 반드시 해당 table_name에만 연결하세요.
    # - **필터:** 반환되는 전체 행 수를 줄이기 위해 효과적으로 쿼리를 작성하세요. 예를 들어, WHERE, HAVING 등 필터나 COUNT, SUM 등의 집계 함수를 사용할 수 있습니다.
    # - **행 제한:** 반환되는 최대 행 수는 {MAX_NUM_ROWS} 미만이어야 합니다.
    #
    # **스키마:**
    #
    # 데이터베이스 구조는 다음 테이블 스키마(샘플 행 포함 가능)로 정의됩니다:
    #
    # ```
    # {SCHEMA}
    # ```
    #
    # **자연어 질문:**
    #
    # ```
    # {QUESTION}
    # ```
    #
    # **단계별로 생각하세요:** 스키마, 질문, 가이드라인, 모범 사례를 신중히 고려하여 올바른 BigQuery SQL을 생성하세요.
    prompt_template = """
You are a BigQuery SQL expert tasked with answering user's questions about BigQuery tables by generating SQL queries in the GoogleSql dialect.  Your task is to write a Bigquery SQL query that answers the following question while using the provided context.

**Guidelines:**

- **Table Referencing:** Always use the full table name with the database prefix in the SQL statement.  Tables should be referred to using a fully qualified name with enclosed in backticks (`) e.g. `project_name.dataset_name.table_name`.  Table names are case sensitive.
- **Joins:** Join as few tables as possible. When joining tables, ensure all join columns are the same data type. Analyze the database and the table schema provided to understand the relationships between columns and tables.
- **Aggregations:**  Use all non-aggregated columns from the `SELECT` statement in the `GROUP BY` clause.
- **SQL Syntax:** Return syntactically and semantically correct SQL for BigQuery with proper relation mapping (i.e., project_id, owner, table, and column relation). Use SQL `AS` statement to assign a new name temporarily to a table column or even a table wherever needed. Always enclose subqueries and union queries in parentheses.
- **Column Usage:** Use *ONLY* the column names (column_name) mentioned in the Table Schema. Do *NOT* use any other column names. Associate `column_name` mentioned in the Table Schema only to the `table_name` specified under Table Schema.
- **FILTERS:** You should write query effectively  to reduce and minimize the total rows to be returned. For example, you can use filters (like `WHERE`, `HAVING`, etc. (like 'COUNT', 'SUM', etc.) in the SQL query.
- **LIMIT ROWS:**  The maximum number of rows returned should be less than {MAX_NUM_ROWS}.

**Schema:**

The database structure is defined by the following table schemas (possibly with sample rows):

```
{SCHEMA}
```

**Natural language question:**

```
{QUESTION}
```

**Think Step-by-Step:** Carefully consider the schema, question, guidelines, and best practices outlined above to generate the correct BigQuery SQL.

   """

    ddl_schema = tool_context.state["database_settings"]["bq_ddl_schema"]

    prompt = prompt_template.format(
        MAX_NUM_ROWS=MAX_NUM_ROWS, SCHEMA=ddl_schema, QUESTION=question
    )

    response = llm_client.models.generate_content(
        model=os.getenv("BASELINE_NL2SQL_MODEL"),
        contents=prompt,
        config={"temperature": 0.1},
    )

    sql = response.text
    if sql:
        sql = sql.replace("```sql", "").replace("```", "").strip()

    print("\n sql:", sql)

    tool_context.state["sql_query"] = sql

    return sql


def run_bigquery_validation(
    sql_string: str,
    tool_context: ToolContext,
) -> str:
    """Validates BigQuery SQL syntax and functionality.

    This function validates the provided SQL string by attempting to execute it
    against BigQuery in dry-run mode. It performs the following checks:

    1. **SQL Cleanup:**  Preprocesses the SQL string using a `cleanup_sql`
    function
    2. **DML/DDL Restriction:**  Rejects any SQL queries containing DML or DDL
       statements (e.g., UPDATE, DELETE, INSERT, CREATE, ALTER) to ensure
       read-only operations.
    3. **Syntax and Execution:** Sends the cleaned SQL to BigQuery for validation.
       If the query is syntactically correct and executable, it retrieves the
       results.
    4. **Result Analysis:**  Checks if the query produced any results. If so, it
       formats the first few rows of the result set for inspection.

    Args:
        sql_string (str): The SQL query string to validate.
        tool_context (ToolContext): The tool context to use for validation.

    Returns:
        str: A message indicating the validation outcome. This includes:
             - "Valid SQL. Results: ..." if the query is valid and returns data.
             - "Valid SQL. Query executed successfully (no results)." if the query
                is valid but returns no data.
             - "Invalid SQL: ..." if the query is invalid, along with the error
                message from BigQuery.
    """

    def cleanup_sql(sql_string):
        """Processes the SQL string to get a printable, valid SQL string."""

        # 1. Remove backslashes escaping double quotes
        sql_string = sql_string.replace('\\"', '"')

        # 2. Remove backslashes before newlines (the key fix for this issue)
        sql_string = sql_string.replace("\\\n", "\n")  # Corrected regex

        # 3. Replace escaped single quotes
        sql_string = sql_string.replace("\\'", "'")

        # 4. Replace escaped newlines (those not preceded by a backslash)
        sql_string = sql_string.replace("\\n", "\n")

        # 5. Add limit clause if not present
        if "limit" not in sql_string.lower():
            sql_string = sql_string + " limit " + str(MAX_NUM_ROWS)

        return sql_string

    logging.info("Validating SQL: %s", sql_string)
    sql_string = cleanup_sql(sql_string)
    logging.info("Validating SQL (after cleanup): %s", sql_string)

    final_result = {"query_result": None, "error_message": None}

    # More restrictive check for BigQuery - disallow DML and DDL
    if re.search(
        r"(?i)(update|delete|drop|insert|create|alter|truncate|merge)", sql_string
    ):
        final_result["error_message"] = (
            "Invalid SQL: Contains disallowed DML/DDL operations."
        )
        return final_result

    try:
        query_job = get_bq_client().query(sql_string)
        results = query_job.result()  # Get the query results

        if results.schema:  # Check if query returned data
            rows = [
                {
                    key: (
                        value
                        if not isinstance(value, datetime.date)
                        else value.strftime("%Y-%m-%d")
                    )
                    for (key, value) in row.items()
                }
                for row in results
            ][
                :MAX_NUM_ROWS
            ]  # Convert BigQuery RowIterator to list of dicts
            # return f"Valid SQL. Results: {rows}"
            final_result["query_result"] = rows

            tool_context.state["query_result"] = rows

        else:
            final_result["error_message"] = (
                "Valid SQL. Query executed successfully (no results)."
            )

    except (
        Exception
    ) as e:  # Catch generic exceptions from BigQuery  # pylint: disable=broad-exception-caught
        final_result["error_message"] = f"Invalid SQL: {e}"

    print("\n run_bigquery_validation final_result: \n", final_result)

    return final_result

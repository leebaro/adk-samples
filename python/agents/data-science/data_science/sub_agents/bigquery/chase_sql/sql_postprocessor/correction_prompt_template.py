# Copyright 2025 Google LLC
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

"""Prompt template for making any corrections to the translation of SQL."""
"""SQL 번역에 대한 수정 작업을 수행하기 위한 프롬프트 템플릿."""

"""
여러 데이터베이스와 SQL 방언에 대한 전문가입니다.
다음 SQL 방언으로 포맷된 SQL 쿼리가 제공됩니다:
{sql_dialect}

SQL 쿼리는 다음과 같습니다:
{sql_query}
{schema_insert}
이 SQL 쿼리에는 다음과 같은 오류가 있을 수 있습니다:
{errors}

SQL 쿼리를 수정하여 해당 SQL 방언에 맞게 올바르게 포맷되도록 해 주세요:
{sql_dialect}

쿼리 내의 테이블 또는 열 이름을 변경하지 마십시오. 그러나 열 이름을 테이블 이름으로 자격을 부여할 수 있습니다.
쿼리 내의 리터럴을 변경하지 마십시오.
지정된 SQL 방언에 맞게 쿼리를 재작성할 수 있지만, 다른 변경은 허용되지 않습니다.
수정된 SQL 쿼리 외의 다른 정보를 반환하지 마십시오.

수정된 SQL 쿼리:
"""


CORRECTION_PROMPT_TEMPLATE_V1_0 = """
You are an expert in multiple databases and SQL dialects.
You are given a SQL query that is formatted for the SQL dialect:
{sql_dialect}

The SQL query is:
{sql_query}
{schema_insert}
This SQL query could have the following errors:
{errors}

Please correct the SQL query to make sure it is formatted correctly for the SQL dialect:
{sql_dialect}

DO not change any table or column names in the query. However, you may qualify column names with table names.
Do not change any literals in the query.
You may *only* rewrite the query so that it is formatted correctly for the specified SQL dialect.
Do not return any other information other than the corrected SQL query.

Corrected SQL query:
"""

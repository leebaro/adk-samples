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

"""Query Plan (QP) prompt template."""
"""
당신은 숙련된 데이터베이스 전문가입니다.
이제 데이터베이스 정보, 질문, 그리고 추가 정보를 바탕으로 GoogleSQL 또는 BigQuery 쿼리를 생성해야 합니다.
데이터베이스 구조는 테이블 스키마(일부 컬럼은 options에 추가 설명이 제공됨)로 정의됩니다.

테이블 스키마 정보와 `Question`이 주어집니다. 테이블 생성문이 제공되며, 데이터베이스와 컬럼을 이해해야 합니다.

"쿼리 플랜 기반 SQL 생성(Query Plan Guided SQL Generation)" 방식을 사용하여 SQL 쿼리를 생성합니다. 이 방법은 질문을 더 작은 하위 질문으로 나눈 후,
이를 조합하여 최종 SQL 쿼리를 만드는 방식입니다. 이 접근법은 질문의 요구사항을 이해하고 SQL 쿼리를 효율적으로 구조화하는 데 도움이 됩니다.

데이터베이스 관리자 지침(이 지침을 반드시 무조건적으로 따르십시오. 힌트로 사용하거나 무시하지 마십시오.):
1. **SELECT 절:**
    - SELECT 문에서 필요한 컬럼만 명시적으로 지정하여 선택하십시오. 불필요한 컬럼이나 값을 피하십시오.

2. **집계(MAX/MIN):**
    - JOIN을 완료한 후에만 MAX() 또는 MIN()을 적용하십시오. GoogleSQL은 집계 함수에 대해 유사한 문법을 지원하므로, JOIN 이후에 MAX(), MIN()을 사용하십시오.

3. **ORDER BY와 Distinct 값:**
    - GoogleSQL에서는 GROUP BY <column>을 ORDER BY <column> ASC|DESC 전에 사용할 수 있습니다.

4. **NULL 처리:**
    - NULL 값을 필터링하려면 JOIN을 사용하거나 WHERE <column> IS NOT NULL 절을 추가하십시오.

5. **FROM/JOIN 절:**
    - 쿼리에 꼭 필요한 테이블만 포함하십시오. BigQuery는 INNER JOIN, LEFT JOIN, RIGHT JOIN을 지원하므로 관계에 따라 적절히 사용하십시오.

6. **힌트 엄수:**
    - 쿼리 작성 시 명시된 조건을 반드시 정확히 따르십시오.

7. **질문 철저 분석:**
    - 쿼리에서 모든 조건이나 제약사항이 완전히 반영되었는지 확인하십시오.

8. **DISTINCT 키워드:**
    - 고유 값이 필요할 때(예: ID, URL 등) SELECT DISTINCT를 사용하십시오.

9. **컬럼 선택:**
    - 컬럼 설명과 힌트를 주의 깊게 읽고, 특히 여러 테이블에 유사한 컬럼이 있을 때 올바른 컬럼을 선택하십시오.

10. **문자열 연결:**
    - GoogleSQL에서는 문자열 연결에 CONCAT()을 사용합니다. || 대신 CONCAT(column1, ' ', column2)를 사용하십시오.

11. **JOIN 우선:**
    - 적절할 때 INNER JOIN을 사용하고, JOIN으로 동일한 결과를 얻을 수 있다면 중첩 SELECT문을 피하십시오.

12. **GoogleSQL 함수만 사용:**
    - GoogleSQL에서 지원하는 함수만 사용하십시오. SQLite 전용 함수는 사용하지 말고, GoogleSQL 함수로 대체하십시오(예: STRFTIME 대신 FORMAT_DATE).

13. **날짜 처리:**
    - GoogleSQL은 FORMAT_DATE('%Y', date_column)으로 연도를 추출할 수 있습니다. FORMAT_DATE, DATE_SUB, DATE_DIFF 등 날짜 함수를 사용하십시오.

14. **테이블명 및 참조:**
    - BigQuery 규칙에 따라 항상 데이터베이스 접두사가 포함된 전체 테이블명을 사용하십시오. 예: "SELECT * FROM example_bigquery_database.table_a"

15. **GROUP BY 또는 집계:**
    - GROUP BY가 있는 쿼리에서는 SELECT 목록의 모든 컬럼이 GROUP BY에 포함되거나 집계 함수(MAX, MIN, AVG, COUNT, SUM 등)로 사용되어야 합니다.

아래는 예시입니다
===========

이제 실제 질문입니다. 위의 지침과 예시를 따라, Recursive Divide-and-Conquer 접근법으로 GoogleSQL을 생성하십시오.
전략의 모든 단계를 따르십시오. 최종 쿼리에 도달하면, 쿼리 문자열만 ```sql ... ``` 형식으로 출력하십시오. 반드시 하나의 쿼리만 출력하십시오.

**************************
【Table creation statements】
{SCHEMA}

**************************
【Question】
Question:
{QUESTION}

**************************
【Answer】
질문을 반복하고 재귀적 분할정복 방식으로 SQL을 생성합니다.
Here are some examples
===========
Example 1

**************************
【Table creation statements】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.restaurant.generalinfo
(
 id_restaurant INT64,
 food_type STRING OPTIONS(description="the food type"),
 city STRING OPTIONS(description="the city where the restaurant is located in"),
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.restaurant.location
(
 id_restaurant INT64,
 street_name STRING OPTIONS(description="the street name of the restaurant"),
 city STRING OPTIONS(description="the city where the restaurant is located in foreign key (id_restaurant) references generalinfo (id_restaurant) on update cascade on delete cascade"),
);

**************************
【Question】
Question:
How many Thai restaurants can be found in San Pablo Ave, Albany? Thai restaurant refers to food_type = 'thai'; San Pablo Ave Albany refers to street_name = 'san pablo ave' AND T1.city = 'albany'

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
**Question**: How many Thai restaurants can be found in San Pablo Ave, Albany? Thai restaurant refers to food_type = 'thai'; San Pablo Ave Albany refers to street_name = 'san pablo ave' AND T1.city = 'albany'


**Query Plan**:

** Preparation Steps:**
1. 프로세스 초기화: 쿼리를 실행하기 위해 준비를 시작합니다.
2. 저장 공간 준비: 임시 결과를 저장하기 위한 저장 공간(레지스터)을 설정하고, 이를 NULL로 초기화합니다.
3. 위치 테이블 열기: 위치 테이블을 열어 해당 테이블에서 데이터를 읽을 수 있도록 합니다.
4. 일반 정보 테이블 열기: 일반 정보 테이블을 열어 해당 테이블에서 데이터를 읽을 수 있도록 합니다.

** Matching Restaurants:**
1. 위치 테이블 읽기 시작: 위치 테이블의 첫 번째 행으로 이동합니다.
2. 도로 이름 일치 확인: 위치 테이블의 현재 행의 street_name 열을 확인합니다. "san pablo ave"가 아니면 이 행을 건너뜁니다.
3. 일치하는 행 식별: 이 위치 항목의 식별자(행 ID)를 저장합니다.
4. 일반 정보에서 일치하는 행 찾기: 위치에서 얻은 행 ID를 사용하여 일반 정보에서 일치하는 행을 직접 찾습니다.
5. 음식 유형 일치 여부 확인: 일반 정보의 음식 유형 열을 확인합니다. "태국"이 아니면 이 행을 건너뜁니다.
6. 도시 일치 여부 확인: 일반 정보의 도시 열을 확인합니다. "알바니"가 아니면 이 행을 건너뜁니다.

** 레스토랑 계수:**
1. 이 행을 최종 계수에 포함할 준비를 합니다: 모든 검사가 통과되면 이 행을 최종 계수에 포함할 준비를 합니다.
2. 일치하는 행을 계산하세요: 모든 기준을 충족하는 각 행에 대해 계산 값을 증가시킵니다.
3. 위치 테이블로 돌아가 다음 행으로 이동하세요: 위치 테이블로 돌아가 다음 행으로 이동한 후, 모든 행이 확인될 때까지 이 과정을 반복합니다.
4. 최종 계산을 완료하세요: 모든 행이 확인되면 일치하는 행의 최종 계산을 완료합니다.
5. 결과를 준비하세요: 최종 계산 결과를 복사하여 출력 준비를 완료합니다.

** 결과 출력:**
1. 결과 출력: 모든 지정된 기준에 맞는 레스토랑의 최종 개수를 출력합니다.
2. 프로세스 종료: 쿼리 실행 프로세스를 중단합니다.
3. 설정 단계: 실제 쿼리 실행을 시작하기 전에 시스템은 "san pablo ave", "thai", "albany"와 같은 특정 값을 준비합니다.

**Final Optimized SQL Query:**
```sql
SELECT COUNT(T1.id_restaurant)
 FROM `{BQ_DATA_PROJECT_ID}`.restaurant.generalinfo AS T1
 INNER JOIN `{BQ_DATA_PROJECT_ID}`.restaurant.location AS T2 ON T1.id_restaurant = T2.id_restaurant
 WHERE T1.food_type = 'thai' AND T1.city = 'albany' AND T2.street_name = 'san pablo ave'
```

===========
Example 2

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.financial.account (
   account_id INT64,
   district_id INT64,
   frequency STRING,
   date DATE,
);
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.financial.client (
   client_id INT64,
   gender STRING,
   birth_date DATE,
   district_id INT64,
);
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.financial.district (
   district_id INT64,
   a4 STRING OPTIONS(description="Assuming A4 and A11 are strings due to examples"),
   a11 STRING,
);

**************************
【Question】
Question:
What is the gender of the youngest client who opened account in the lowest average salary branch? Given that Later birthdate refers to younger age; A11 refers to average salary
최저 평균 급여 지점에서 계좌를 개설한 가장 젊은 고객의 성별은 무엇인가요? 출생일이 늦을수록 연령이 젊음을 의미하며; A11은 평균 급여를 의미합니다.
**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
**Question**: What is the gender of the youngest client who opened account in the lowest average salary branch? Given that Later birthdate refers to younger age; A11 refers to average salary

**Query Plan**:

** Preparation Steps: **
1. Initialize the process: Begin setting up the necessary environment to execute the query efficiently.
2. Open required tables: Access the client, account, and district tables to retrieve relevant data.
3. Prepare temporary storage: Allocate space to store intermediate results such as the lowest average salary and corresponding district information.
** 준비 단계: **
1. 프로세스 초기화: 쿼리를 효율적으로 실행하기 위해 필요한 환경을 설정합니다.
2. 필요한 테이블 열기: 고객, 계정, 지역 테이블에 접근하여 관련 데이터를 가져옵니다.
3. 임시 저장 공간 준비: 최저 평균 급여와 해당 지역 정보와 같은 중간 결과를 저장하기 위해 공간을 할당합니다.

** Identify the Branch with Lowest Average Salary: **
1. Scan the district table: Retrieve all records from the district table to analyze average salaries.
2. Extract average salaries: For each district, note the value in the A11 column, which represents the average salary.
3. Determine the lowest salary: Compare all extracted average salaries to identify the minimum value.
4. Store corresponding district_id: Record the district_id associated with the lowest average salary for further processing.

** 최저 평균 급여를 가진 지점 식별: **
1. 지역 테이블 스캔: 지역 테이블의 모든 기록을 가져와 평균 급여를 분석합니다.
2. 평균 급여 추출: 각 지역별로 A11 열의 값을 기록합니다. 이 값은 평균 급여를 나타냅니다.
3. 최저 급여 결정: 추출된 모든 평균 급여를 비교하여 최소 값을 식별합니다.
4. 해당 지역 ID 저장: 최저 평균 급여와 연관된 지역 ID를 기록하여 추가 처리를 위해 저장합니다.


** Find Clients in the Identified District: **
1. Join client and account tables: Merge records where client.client_id matches account.account_id to associate clients with their accounts.
2. Filter by district_id: Select only those records where account.district_id matches the previously identified district_id with the lowest average salary.
3. Handle potential duplicates: Ensure that each client is uniquely identified even if they have multiple accounts in the same district.

** 지정된 지역에서 고객 찾기: **  
1. 고객 및 계정 테이블 결합: 고객.고객_ID가 계정.계정_ID와 일치하는 기록을 병합하여 고객을 해당 계정과 연결합니다.
2. 지역 ID로 필터링: 계정.지역_ID가 이전에 식별된 지역 ID 중 평균 급여가 가장 낮은 것과 일치하는 기록만 선택합니다.
3. 중복 처리: 동일한 지역 내에서도 여러 계정을 가진 고객이더라도 각 고객이 고유하게 식별되도록 합니다.


** 가장 젊은 고객 식별: **
1. 생년월일 추출: 필터링된 고객 기록에서 각 고객의 생년월일을 추출합니다.
2. 최신 생년월일 확인: 필터링된 목록에서 가장 최근(최신) 생년월일을 확인하여 가장 젊은 고객을 식별합니다.
3. 생년월일 중복 처리: 여러 고객이 동일한 최신 생년월일을 공유하는 경우, 다중 결과를 처리하거나 단일 고객을 선택하기 위한 추가 기준을 결정합니다.

** 성별 정보 검색: **
1. 성별 열 선택: 가장 젊은 고객의 기록에서 성별 열의 값을 추출합니다.
2. 결과 준비: 검색된 성별 정보를 명확하고 정확하게 표시하기 위해 형식을 지정합니다.

** 결과 최종화 및 전달: **
1. 최종 결과 컴파일: 추출된 성별 정보를 일관되고 이해하기 쉬운 출력으로 구성합니다.
2. 리소스 정리: 열린 테이블 연결을 닫고 쿼리 실행 중에 사용된 임시 저장소를 해제합니다.
3. 결과 출력: 최저 평균 급여 지점에서 계좌를 개설한 가장 젊은 고객의 성별을 표시합니다.

**Final Optimized SQL Query:**
```sql
SELECT `T1`.`gender`
 FROM `{BQ_DATA_PROJECT_ID}.financial.client` AS `T1`
 INNER JOIN `{BQ_DATA_PROJECT_ID}.financial.district` AS `T2`
 ON `T1`.`district_id` = `T2`.`district_id`
 ORDER BY `T2`.`A11` ASC, `T1`.`birth_date` DESC NULLS LAST
 LIMIT 1
```
===========
Example 3 (dividing into two parallel sub-questions)

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.olympics.games
(
 id INT64,
 games_year INT64 OPTIONS(description="description: the year of the game"),
 games_name STRING,
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.olympics.games_city
(
 games_id INT64,
 city_id INT64 OPTIONS(description="the id of the city that held the game Maps to city(id)"),
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.olympics.city
(
 id INT64,
 city_name STRING,
);

**************************
【Question】
Question:
From 1900 to 1992, how many games did London host? From 1900 to 1992 refers to games_year BETWEEN 1900 AND 1992; London refers to city_name = 'London'; games refer to games_name;
1900년부터 1992년까지 런던에서 개최된 대회는 몇 개입니까? 1900년부터 1992년까지는 1900년과 1992년 사이의 대회 수를 의미합니다; 런던은 도시 이름이 '런던'인 곳을 의미합니다; 대회는 대회 이름을 의미합니다;

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
**Question**: From 1900 to 1992, how many games did London host? From 1900 to 1992 refers to games_year BETWEEN 1900 AND 1992; London refers to city_name = 'London'; games refer to games_name;

**Query Plan**:

** Preparation Steps: **
1.Initialize the process: Set up the environment to begin query execution, including necessary variables and temporary storage.
2. Open required tables: Open the games_city, city, and games tables to access relevant data.
3. Prepare filtering values: Set up the specific values to filter the data, such as the year range (1900-1992) and the city name 'London'.

1. 프로세스 초기화: 쿼리 실행을 시작하기 위해 필요한 변수와 임시 저장 공간을 포함한 환경을 설정합니다.
2. 필요한 테이블 열기: 관련 데이터를 액세스하기 위해 games_city, city 및 games 테이블을 열습니다.
3. 필터링 값 준비: 데이터 필터링을 위해 특정 값을 설정합니다. 예를 들어 연도 범위(1900-1992)와 도시 이름 'London' 등이 포함됩니다.


** Filter and Identify Relevant Data: **
1. Scan games_city table: Retrieve records from the games_city table to match games with the cities where they were hosted.
2. Fetch the corresponding city_id: For each row in games_city, extract the city_id to find out which city hosted the game.
3 .Match city_id with city_name: Use the city_id to look up the corresponding city_name in the city table.
4. Filter by city_name = 'London': Select only those rows where the city_name is 'London'.

** 관련 데이터 필터링 및 식별: ** 
1. games_city 테이블 스캔: games_city 테이블에서 기록을 검색하여 게임이 개최된 도시와 일치시키는 기록을 추출합니다.
2. 해당 city_id 가져오기: games_city 테이블의 각 행에서 city_id를 추출하여 해당 게임이 개최된 도시를 확인합니다.  
3. city_id와 city_name 일치시키기: city_id를 사용하여 city 테이블에서 해당 city_name을 조회합니다.  
4. city_name = 'London'로 필터링: city_name이 'London'인 행만 선택합니다.

** Further Filter by Year Range: **
1. Extract games_id: For rows that match 'London', retrieve the games_id from the games_city table.
2. Find matching games_year: Use the games_id to look up the corresponding games_year in the games table.
3. Filter by games_year between 1900 and 1992: Select only those rows where the games_year falls within the specified range (1900-1992).

** 연도 범위로 추가 필터링: **
1. games_id 추출: 'London'과 일치하는 행에서 games_city 테이블의 games_id를 가져옵니다.
2. 일치하는 games_year 찾기: games_id를 사용하여 games 테이블에서 해당 games_year을 조회합니다.
3. games_year가 1900과 1992 사이인 행 필터링: 지정된 범위(1900-1992)에 해당하는 행만 선택합니다.

** Count the Matching Rows: **
1. Initialize the count: Prepare to count the number of matching rows that meet all the criteria.
2. Count the valid entries: For each row that matches the conditions (city_name = 'London' and games_year between 1900 and 1992), increment the count.
3. Store the final count: Once all rows have been processed, store the total count as the final result.

** 일치하는 행 계산: **
1. 카운트 초기화: 모든 기준을 충족하는 일치하는 행의 수를 계산할 준비를 합니다.
2. 유효한 항목 수 계산: 조건(도시 이름 = '런던' 및 게임 연도 1900-1992 사이)에 일치하는 각 행에 대해 카운트를 증가시킵니다.
3. 최종 카운트 저장: 모든 행이 처리되면 총 카운트를 최종 결과로 저장합니다.

** Finalize and Deliver the Result: **
1. Prepare the result for output: Format the final count of games hosted by London between 1900 and 1992.
2. Output the final count: Deliver the count as the query result.
3. Clean up resources: Close any open table connections and release temporary storage used during query execution.

** 결과 최종화 및 전달: **
1. 결과 출력 준비: 1900년부터 1992년까지 런던에서 개최된 게임의 최종 개수를 형식화합니다.
2. 최종 카운트 출력: 쿼리 결과로 카운트를 전달합니다.
3. 리소스 정리: 열린 테이블 연결을 닫고 쿼리 실행 중에 사용된 임시 저장소를 해제합니다.

**Final Optimized SQL Query:**
```sql
SELECT COUNT(T3.id)
 FROM `{BQ_DATA_PROJECT_ID}`.olympics.games_city AS T1
 INNER JOIN `{BQ_DATA_PROJECT_ID}`.olympics.city AS T2 ON T1.city_id = T2.id
 INNER JOIN `{BQ_DATA_PROJECT_ID}`.olympics.games AS T3 ON T1.games_id = T3.id
 WHERE T2.city_name = 'London' AND T3.games_year
 BETWEEN 1900 AND 1992
```

===========
Example 4

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.retails.employees (
   employee_id INT64,
   department_id INT64,
   salary INT64,
);

**************************
【Question】
Question:
How many employees earn over $100,000?

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
**Question:** How many employees earn over $100,000?

** Query Plan**:

** Preparation Steps: **
1.cInitialize the process: Begin by setting up the environment for query execution, including initializing variables and temporary storage.
2. Open the employees table: Access the employees table to retrieve the relevant data.

** Filtering Employees by Salary: **
1. Scan the employees table: Begin reading rows from the employees table.
2. Fetch the salary column: For each row, retrieve the value from the salary column.
3. Compare salary against $100,000: Check if the salary value is greater than $100,000.
4. Identify matching rows: For rows where the salary exceeds $100,000, prepare to count these entries.

** Counting the Matches: **
1. Initialize the count: Set up a counter to keep track of how many employees meet the salary condition.
2. Increment the count: For each row where the salary is above $100,000, increment the counter.
3. Store the final count: Once all rows have been processed, store the total count of matching employees.

** Finalize and Deliver the Result: **
1. Prepare the result for output: Format the final count for presentation.
2. Output the final count: Deliver the count as the query result, indicating how many employees earn over $100,000.
3. Clean up resources: Close the employees table and release any temporary storage used during query execution.

**Final Optimized SQL Query:**
```sql
SELECT COUNT(*) FROM `{BQ_DATA_PROJECT_ID}`.retails.employees WHERE salary > 100000;
```

===========
Example 6

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.airlines.Airlines
(
 FL_DATE STRING OPTIONS(description="flight date"),
 ORIGIN STRING OPTIONS(description="airport of origin"),
 DEST STRING OPTIONS(description="Destination airport"),
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.airlines.Airports
(
 Code STRING,
 Description STRING,
);

**************************
【Question】
Question:
How many flights were there from San Diego International airport to Los Angeles International airport in the August of 2018?
flights from refers to ORIGIN; San Diego International airport refers to Description = 'San Diego, CA: San Diego International'; flights to refers to DEST; Los Angeles International airport refers to Description = 'Los Angeles, CA: Los Angeles International'; in the August of 2018 refers to FL_DATE like '2018/8%';

**************************
【Answer】
**Repeating the question and generating the SQL with Recursive Divide-and-Conquer.**

**Question**: How many flights were there from San Diego International airport to Los Angeles International airport in the August of 2018? flights from refers to ORIGIN; San Diego International airport refers to Description = 'San Diego, CA: San Diego International'; flights to refers to DEST; Los Angeles International airport refers to Description = 'Los Angeles, CA: Los Angeles International'; in the August of 2018 refers to FL_DATE like '2018/8%';

** Query Plan**:

** Preparation Steps: **
1. Initialize the process: Set up the environment and prepare for query execution by initializing variables and temporary storage.
2. Open required tables: Open the Airlines and Airports tables to access relevant data.

** Identify Relevant Flights: **
1. Fetch the FL_DATE column: Start reading the FL_DATE column from the Airlines table.
2. Filter by August 2018: Use the condition FL_DATE LIKE '2018/8%' to filter flights that occurred in August 2018.
3. Join with Airports for ORIGIN: Identify flights originating from 'San Diego, CA: San Diego International' by joining the Airlines table with the Airports table on the ORIGIN field.
4. Join with Airports for DEST: Similarly, identify flights destined for 'Los Angeles, CA: Los Angeles International' by joining the Airlines table with the Airports table on the DEST field.

** Count the Matching Flights: **
1. Initialize the count: Set up a counter to keep track of how many flights match the criteria.
2. Increment the count: For each flight that meets the conditions (originating from San Diego International and destined for Los Angeles International in August 2018), increment the counter.
3. Store the final count: Once all rows have been processed, store the total count of matching flights.

** Finalize and Deliver the Result: **
1. Prepare the result for output: Format the final count for presentation, ensuring clarity and correctness.
2. Output the final count: Deliver the count as the query result, indicating how many flights met the specified criteria.
3. Clean up resources: Close any open table connections and release temporary storage used during query execution.

**Final Optimized SQL Query:**
```sql
SELECT COUNT(FL_DATE)
 FROM `{BQ_DATA_PROJECT_ID}`.airlines.Airlines
 WHERE FL_DATE LIKE '2018/8%'
 AND ORIGIN = (
   SELECT DISTINCT T2.ORIGIN
   FROM `{BQ_DATA_PROJECT_ID}`.airlines.Airports AS T1
   INNER JOIN `{BQ_DATA_PROJECT_ID}`.airlines.Airlines AS T2 ON T1.Code = T2.ORIGIN
   WHERE T1.Description = 'San Diego, CA: San Diego International' )
 AND DEST = (
   SELECT DISTINCT T4.DEST
   FROM `{BQ_DATA_PROJECT_ID}`.airlines.Airports AS T3
   INNER JOIN `{BQ_DATA_PROJECT_ID}`.airlines.Airlines AS T4 ON T3.Code = T4.DEST
   WHERE T3.Description = 'Los Angeles, CA: Los Angeles International' )
```

===========
Example 7

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.food_inspection.businesses
(
       `business_id` INT64,
       `name` STRING OPTIONS(description="the name of the eatery"),
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.food_inspection.inspections
(
       `business_id` INT64 OPTIONS(description="the unique id of the business"),
       `score` INT64 OPTIONS(description="description: the inspection score"),
       `date` DATE,
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.food_inspection.violations
(
       `business_id` INT64,
       `date` DATE,
);

**************************
【Question】
Question:
What are the names of the establishments that met all the required standards for 4 consecutive years?
establishment has the same meaning as business; score of 90 or more refers to score ≥ 90; year(date) = 2015; ; met all required standards for 4 consecutive years refers to COUNT(year(date)) = 4 where score = 100;

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.

**Question**: What are the names of the establishments that met all the required standards for 4 consecutive years? establishment has the same meaning as business; score of 90 or more refers to score ≥ 90; year(date) = 2015; ; met all required standards for 4 consecutive years refers to COUNT(year(date)) = 4 where score = 100;

** Query Plan**:

** Preparation Steps: **
1. Initialize the process: Set up the environment and prepare for query execution, including initializing variables and temporary storage.
2. Open required tables: Open the businesses, inspections, and violations tables to access relevant data.

** Filter and Identify Relevant Inspections: **
1. Scan the inspections table: Start reading rows from the inspections table.
2. Filter by score of 100: Select only those inspections where the score is 100, indicating that the establishment met all required standards.
3. Extract year from the inspection date: Use the FORMAT_DATE('%Y', date) function to extract the year from the inspection date.
4. Join with businesses table: Match each inspection to the corresponding business by joining on business_id.

** Identify Businesses Meeting Standards for 4 Consecutive Years: **
1. Aggregate by business and year: Group the data by business name and the extracted year to count the number of years each business met the required standards.
3. Apply row numbering: Use ROW_NUMBER() with a partition by business name and order by year to identify consecutive years.
3. Filter for 4 consecutive years: Group by business name and ensure that the count of years with the required score is exactly 4, indicating 4 consecutive years of meeting the standards.

** Count and Finalize the Results: **
1. Count the matching businesses: For each business, count the number of years that meet the criteria.
2. Select distinct business names: Extract the names of businesses that have met the required standards for 4 consecutive years.
3. Store and prepare the result: Once all businesses have been processed, store the result and prepare it for output.

** Deliver the Final Result: **
1. Prepare the result for output: Format the final list of business names for presentation.
2. Output the final result: Deliver the names of the businesses that met the required standards for 4 consecutive years.
3. Clean up resources: Close any open table connections and release temporary storage used during query execution.

**Final Optimized SQL Query:**
```sql
SELECT DISTINCT T4.name
 FROM ( SELECT T3.name, T3.years, row_number()
 OVER (PARTITION BY T3.name ORDER BY T3.years)
 AS rowNumber FROM ( SELECT DISTINCT name, FORMAT_DATE('%Y', date)
 AS years FROM `{BQ_DATA_PROJECT_ID}`.food_inspection.inspections AS T1
 INNER JOIN `{BQ_DATA_PROJECT_ID}`.food_inspection.businesses AS T2 ON T1.business_id = T2.business_id
 WHERE T1.score = 100 ) AS T3 ) AS T4
 GROUP BY T4.name, DATE_SUB(DATE(CONCAT(T4.years, '-01-01')), INTERVAL (T4.rowNumber - 1) YEAR) HAVING COUNT(T4.years) = 4
```

===========
Example 8

**************************
【Database Info】
CREATE TABLE `bigquery-public-data.covid19_symptom_search.symptom_search_sub_region_2_daily`
(
  country_region_code STRING,
  country_region STRING,
  sub_region_1 STRING,
  sub_region_1_code STRING,
  sub_region_2 STRING,
  sub_region_2_code STRING,
  place_id STRING,
  date DATE,
  symptom_Abdominal_obesity FLOAT64,
  symptom_Abdominal_pain FLOAT64,
  symptom_Acne FLOAT64
)
PARTITION BY date
CLUSTER BY country_region_code, sub_region_1_code, sub_region_2_code, sub_region_2;

**************************
【Question】
Question:
Find the day in which the symptom that occurs most frequently is headache.

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.

**Question**: Find the day in which the symptom that occurs most frequently is headache.

** Query Plan**:

**  Preparation Steps : **
1. Initialize the process: Set up the environment and prepare for query execution, including initializing variables and temporary storage.
2. Open the symptom_search_sub_region_2_daily table: Access the table containing daily symptom search data.

** Extract the headache symptom: **
1. Scan the table: Start reading rows from the symptom_search_sub_region_2_daily table.
2. Identify the headache symptom: Look for the column containing the headache symptom data.
3. Extract the headache symptom value: For each row, extract the value from the headache symptom column.
4. Aggregate by date: Group the data by date to count the occurrences of the headache symptom on each day.

** Sort by frequency: **
1. Order the results in descending order of symptom frequency.
2. Limit the results: Extract the single day with the highest count.

** Step 2: Identify Subtasks **
1. Extract relevant symptom column: While "headache" is not explicitly listed, its frequency might be tracked in a related table (e.g., symptom_search_country_daily) as per the given gold query.
2. Group data by day of the week: Use FORMAT_DATE('%A', date) to extract the day of the week from each date.
3. Aggregate by count: Count the occurrences of the "headache" symptom across dates and group by the day of the week.
4. Sort by frequency: Order the results in descending order of symptom frequency.
5. Limit the results: Extract the single day with the highest count.

** Step 3: Formulate the Query **
1. From the subtasks, the query will:
2. Select the day of the week using FORMAT_DATE('%A', date).
3. Aggregate counts grouped by the day.
4. Sort the results by the aggregated count in descending order.
5. Limit the results to the top record.

** Step 4: Construct the Query **
1. Combining all subtasks, the final query is:
2. SELECT COUNT(symptom_headache) FROM `{BQ_DATA_PROJECT_ID}`.covid19_symptom_search.symptom_search_sub_region_2_daily GROUP BY FORMAT_DATE('%A', date) ORDER BY COUNT(symptom_headache) DESC LIMIT 1;

** Step 5: Finalize the Query **
**Final Optimized SQL Query:**
```sql
SELECT
  FORMAT_DATE('%A', PARSE_DATE('%Y-%m-%d', date)) AS day,
  COUNT(*) AS headache_count
FROM
  `{BQ_DATA_PROJECT_ID}`.covid19_symptom_search.symptom_search_country_daily
GROUP BY
  day
ORDER BY
  headache_count DESC
LIMIT 1;
```

Now is the real question, following the instruction and examples, generate the GoogleSQL with Recursive Divide-and-Conquer approach.
Follow all steps from the strategy. When you get to the final query, output the query string ONLY in the format ```sql ... ```. Make sure you only output one single query.

**************************
【Table creation statements】
{SCHEMA}

**************************
【Question】
Question:
{QUESTION}

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
"""



QP_PROMPT_TEMPLATE = """
You are an experienced database expert.
Now you need to generate a GoogleSQL or BigQuery query given the database information, a question and some additional information.
The database structure is defined by table schemas (some columns provide additional column descriptions in the options).

Given the table schema information description and the `Question`. You will be given table creation statements and you need understand the database and columns.

You will be using a way called "Query Plan Guided SQL Generation" to generate the SQL query. This method involves breaking down the question into smaller sub-questions and then assembling them to form the final SQL query. This approach helps in understanding the question requirements and structuring the SQL query efficiently.

Database admin instructions (please *unconditionally* follow these instructions. Do *not* ignore them or use them as hints.):
1. **SELECT Clause:**
   - Select only the necessary columns by explicitly specifying them in the `SELECT` statement. Avoid redundant columns or values.

2. **Aggregation (MAX/MIN):**
   - Ensure `JOIN`s are completed before applying `MAX()` or `MIN()`. GoogleSQL supports similar syntax for aggregation functions, so use `MAX()` and `MIN()` as needed after `JOIN` operations.

3. **ORDER BY with Distinct Values:**
   - In GoogleSQL, `GROUP BY <column>` can be used before `ORDER BY <column> ASC|DESC` to get distinct values and sort them.

4. **Handling NULLs:**
   - To filter out NULL values, use `JOIN` or add a `WHERE <column> IS NOT NULL` clause.

5. **FROM/JOIN Clauses:**
   - Only include tables essential to the query. BigQuery supports `JOIN` types like `INNER JOIN`, `LEFT JOIN`, and `RIGHT JOIN`, so use these based on the relationships needed.

6. **Strictly Follow Hints:**
   - Carefully adhere to any specified conditions in the instructions for precise query construction.

7. **Thorough Question Analysis:**
   - Review all specified conditions or constraints in the question to ensure they are fully addressed in the query.

8. **DISTINCT Keyword:**
   - Use `SELECT DISTINCT` when unique values are needed, such as for IDs or URLs.

9. **Column Selection:**
   - Pay close attention to column descriptions and any hints to select the correct column, especially when similar columns exist across tables.

10. **String Concatenation:**
   - GoogleSQL uses `CONCAT()` for string concatenation. Avoid using `||` and instead use `CONCAT(column1, ' ', column2)` for concatenation.

11. **JOIN Preference:**
   - Use `INNER JOIN` when appropriate, and avoid nested `SELECT` statements if a `JOIN` will achieve the same result.

12. **GoogleSQL Functions Only:**
   - Use functions available in GoogleSQL. Avoid SQLite-specific functions and replace them with GoogleSQL equivalents (e.g., `FORMAT_DATE` instead of `STRFTIME`).

13. **Date Processing:**
   - GoogleSQL supports `FORMAT_DATE('%Y', date_column)` for extracting the year. Use date functions like `FORMAT_DATE`, `DATE_SUB`, and `DATE_DIFF` for date manipulation.

14. **Table Names and reference:**
   - As required by BigQuery, always use the full table name with the database prefix in the SQL statement. For example, "SELECT * FROM example_bigquery_database.table_a", not just "SELECT * FROM table_a"

15. **GROUP BY or AGGREGATE:**
   - In queries with GROUP BY, all columns in the SELECT list must either: Be included in the GROUP BY clause, or Be used in an aggregate function (e.g., MAX, MIN, AVG, COUNT, SUM).

Here are some examples
===========
Example 1

**************************
【Table creation statements】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.restaurant.generalinfo
(
 id_restaurant INT64,
 food_type STRING OPTIONS(description="the food type"),
 city STRING OPTIONS(description="the city where the restaurant is located in"),
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.restaurant.location
(
 id_restaurant INT64,
 street_name STRING OPTIONS(description="the street name of the restaurant"),
 city STRING OPTIONS(description="the city where the restaurant is located in foreign key (id_restaurant) references generalinfo (id_restaurant) on update cascade on delete cascade"),
);

**************************
【Question】
Question:
How many Thai restaurants can be found in San Pablo Ave, Albany? Thai restaurant refers to food_type = 'thai'; San Pablo Ave Albany refers to street_name = 'san pablo ave' AND T1.city = 'albany'

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
**Question**: How many Thai restaurants can be found in San Pablo Ave, Albany? Thai restaurant refers to food_type = 'thai'; San Pablo Ave Albany refers to street_name = 'san pablo ave' AND T1.city = 'albany'


**Query Plan**:

** Preparation Steps:**
1. Initialize the process: Start preparing to execute the query.
2. Prepare storage: Set up storage space (registers) to hold temporary results, initializing them to NULL.
3. Open the location table: Open the location table so we can read from it.
4. Open the generalinfo table: Open the generalinfo table so we can read from it.

** Matching Restaurants:**
1. Start reading the location table: Move to the first row in the location table.
2. Check if the street matches: Look at the street_name column of the current row in location. If it’s not "san pablo ave," skip this row.
3. Identify the matching row: Store the identifier (row ID) of this location entry.
4. Find the corresponding row in generalinfo: Use the row ID from location to directly find the matching row in generalinfo.
5. Check if the food type matches: Look at the food_type column in generalinfo. If it’s not "thai," skip this row.
6. Check if the city matches: Look at the city column in generalinfo. If it’s not "albany," skip this row.

** Counting Restaurants:**
1. Prepare to count this match: If all checks pass, prepare to include this row in the final count.
2. Count this match: Increment the count for each row that meets all the criteria.
3. Move to the next row in location: Go back to the location table and move to the next row, repeating the process until all rows are checked.
4. Finalize the count: Once all rows have been checked, finalize the count of matching rows.
5. Prepare the result: Copy the final count to prepare it for output.

** Delivering the Result:**
1. Output the result: Output the final count, which is the number of restaurants that match all the specified criteria.
2. End the process: Stop the query execution process.
3. Setup phase: Before starting the actual query execution, the system prepares the specific values it will be looking for, like "san pablo ave," "thai," and "albany."

**Final Optimized SQL Query:**
```sql
SELECT COUNT(T1.id_restaurant)
 FROM `{BQ_DATA_PROJECT_ID}`.restaurant.generalinfo AS T1
 INNER JOIN `{BQ_DATA_PROJECT_ID}`.restaurant.location AS T2 ON T1.id_restaurant = T2.id_restaurant
 WHERE T1.food_type = 'thai' AND T1.city = 'albany' AND T2.street_name = 'san pablo ave'
```

===========
Example 2

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.financial.account (
   account_id INT64,
   district_id INT64,
   frequency STRING,
   date DATE,
);
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.financial.client (
   client_id INT64,
   gender STRING,
   birth_date DATE,
   district_id INT64,
);
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.financial.district (
   district_id INT64,
   a4 STRING OPTIONS(description="Assuming A4 and A11 are strings due to examples"),
   a11 STRING,
);

**************************
【Question】
Question:
What is the gender of the youngest client who opened account in the lowest average salary branch? Given that Later birthdate refers to younger age; A11 refers to average salary

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
**Question**: What is the gender of the youngest client who opened account in the lowest average salary branch? Given that Later birthdate refers to younger age; A11 refers to average salary

**Query Plan**:

** Preparation Steps: **
1. Initialize the process: Begin setting up the necessary environment to execute the query efficiently.
2. Open required tables: Access the client, account, and district tables to retrieve relevant data.
3. Prepare temporary storage: Allocate space to store intermediate results such as the lowest average salary and corresponding district information.

** Identify the Branch with Lowest Average Salary: **
1. Scan the district table: Retrieve all records from the district table to analyze average salaries.
2. Extract average salaries: For each district, note the value in the A11 column, which represents the average salary.
3. Determine the lowest salary: Compare all extracted average salaries to identify the minimum value.
4. Store corresponding district_id: Record the district_id associated with the lowest average salary for further processing.

** Find Clients in the Identified District: **
1. Join client and account tables: Merge records where client.client_id matches account.account_id to associate clients with their accounts.
2. Filter by district_id: Select only those records where account.district_id matches the previously identified district_id with the lowest average salary.
3. Handle potential duplicates: Ensure that each client is uniquely identified even if they have multiple accounts in the same district.

** Identify the Youngest Client: **
1. Extract birth dates: From the filtered client records, retrieve the birth_date for each client.
2. Determine the latest birth date: Identify the most recent (latest) birth date, indicating the youngest client among the filtered list.
3. Handle ties in birth dates: If multiple clients share the same latest birth date, prepare to handle multiple results or decide on additional criteria to select a single client.

** Retrieve Gender Information: **
1. Select the gender column: From the record(s) of the youngest client(s), extract the value in the gender column.
2. Prepare the result: Format the retrieved gender information for presentation, ensuring clarity and correctness.

** Finalize and Deliver the Result: **
1. Compile the final result: Organize the extracted gender information into a coherent and understandable output.
2. Clean up resources: Close any open table connections and release temporary storage used during query execution.
3. Output the result: Present the gender of the youngest client who opened an account in the branch with the lowest average salary.

**Final Optimized SQL Query:**
```sql
SELECT `T1`.`gender`
 FROM `{BQ_DATA_PROJECT_ID}.financial.client` AS `T1`
 INNER JOIN `{BQ_DATA_PROJECT_ID}.financial.district` AS `T2`
 ON `T1`.`district_id` = `T2`.`district_id`
 ORDER BY `T2`.`A11` ASC, `T1`.`birth_date` DESC NULLS LAST
 LIMIT 1
```
===========
Example 3 (dividing into two parallel sub-questions)

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.olympics.games
(
 id INT64,
 games_year INT64 OPTIONS(description="description: the year of the game"),
 games_name STRING,
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.olympics.games_city
(
 games_id INT64,
 city_id INT64 OPTIONS(description="the id of the city that held the game Maps to city(id)"),
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.olympics.city
(
 id INT64,
 city_name STRING,
);

**************************
【Question】
Question:
From 1900 to 1992, how many games did London host? From 1900 to 1992 refers to games_year BETWEEN 1900 AND 1992; London refers to city_name = 'London'; games refer to games_name;

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
**Question**: From 1900 to 1992, how many games did London host? From 1900 to 1992 refers to games_year BETWEEN 1900 AND 1992; London refers to city_name = 'London'; games refer to games_name;

**Query Plan**:

** Preparation Steps: **
1.Initialize the process: Set up the environment to begin query execution, including necessary variables and temporary storage.
2. Open required tables: Open the games_city, city, and games tables to access relevant data.
3. Prepare filtering values: Set up the specific values to filter the data, such as the year range (1900-1992) and the city name 'London'.

** Filter and Identify Relevant Data: **
1. Scan games_city table: Retrieve records from the games_city table to match games with the cities where they were hosted.
2. Fetch the corresponding city_id: For each row in games_city, extract the city_id to find out which city hosted the game.
3 .Match city_id with city_name: Use the city_id to look up the corresponding city_name in the city table.
4. Filter by city_name = 'London': Select only those rows where the city_name is 'London'.

** Further Filter by Year Range: **
1. Extract games_id: For rows that match 'London', retrieve the games_id from the games_city table.
2. Find matching games_year: Use the games_id to look up the corresponding games_year in the games table.
3. Filter by games_year between 1900 and 1992: Select only those rows where the games_year falls within the specified range (1900-1992).

** Count the Matching Rows: **
1. Initialize the count: Prepare to count the number of matching rows that meet all the criteria.
2. Count the valid entries: For each row that matches the conditions (city_name = 'London' and games_year between 1900 and 1992), increment the count.
3. Store the final count: Once all rows have been processed, store the total count as the final result.

** Finalize and Deliver the Result: **
1. Prepare the result for output: Format the final count of games hosted by London between 1900 and 1992.
2. Output the final count: Deliver the count as the query result.
3. Clean up resources: Close any open table connections and release temporary storage used during query execution.

**Final Optimized SQL Query:**
```sql
SELECT COUNT(T3.id)
 FROM `{BQ_DATA_PROJECT_ID}`.olympics.games_city AS T1
 INNER JOIN `{BQ_DATA_PROJECT_ID}`.olympics.city AS T2 ON T1.city_id = T2.id
 INNER JOIN `{BQ_DATA_PROJECT_ID}`.olympics.games AS T3 ON T1.games_id = T3.id
 WHERE T2.city_name = 'London' AND T3.games_year
 BETWEEN 1900 AND 1992
```

===========
Example 4

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.retails.employees (
   employee_id INT64,
   department_id INT64,
   salary INT64,
);

**************************
【Question】
Question:
How many employees earn over $100,000?

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
**Question:** How many employees earn over $100,000?

** Query Plan**:

** Preparation Steps: **
1.cInitialize the process: Begin by setting up the environment for query execution, including initializing variables and temporary storage.
2. Open the employees table: Access the employees table to retrieve the relevant data.

** Filtering Employees by Salary: **
1. Scan the employees table: Begin reading rows from the employees table.
2. Fetch the salary column: For each row, retrieve the value from the salary column.
3. Compare salary against $100,000: Check if the salary value is greater than $100,000.
4. Identify matching rows: For rows where the salary exceeds $100,000, prepare to count these entries.

** Counting the Matches: **
1. Initialize the count: Set up a counter to keep track of how many employees meet the salary condition.
2. Increment the count: For each row where the salary is above $100,000, increment the counter.
3. Store the final count: Once all rows have been processed, store the total count of matching employees.

** Finalize and Deliver the Result: **
1. Prepare the result for output: Format the final count for presentation.
2. Output the final count: Deliver the count as the query result, indicating how many employees earn over $100,000.
3. Clean up resources: Close the employees table and release any temporary storage used during query execution.

**Final Optimized SQL Query:**
```sql
SELECT COUNT(*) FROM `{BQ_DATA_PROJECT_ID}`.retails.employees WHERE salary > 100000;
```

===========
Example 6

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.airlines.Airlines
(
 FL_DATE STRING OPTIONS(description="flight date"),
 ORIGIN STRING OPTIONS(description="airport of origin"),
 DEST STRING OPTIONS(description="Destination airport"),
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.airlines.Airports
(
 Code STRING,
 Description STRING,
);

**************************
【Question】
Question:
How many flights were there from San Diego International airport to Los Angeles International airport in the August of 2018?
flights from refers to ORIGIN; San Diego International airport refers to Description = 'San Diego, CA: San Diego International'; flights to refers to DEST; Los Angeles International airport refers to Description = 'Los Angeles, CA: Los Angeles International'; in the August of 2018 refers to FL_DATE like '2018/8%';

**************************
【Answer】
**Repeating the question and generating the SQL with Recursive Divide-and-Conquer.**

**Question**: How many flights were there from San Diego International airport to Los Angeles International airport in the August of 2018? flights from refers to ORIGIN; San Diego International airport refers to Description = 'San Diego, CA: San Diego International'; flights to refers to DEST; Los Angeles International airport refers to Description = 'Los Angeles, CA: Los Angeles International'; in the August of 2018 refers to FL_DATE like '2018/8%';

** Query Plan**:

** Preparation Steps: **
1. Initialize the process: Set up the environment and prepare for query execution by initializing variables and temporary storage.
2. Open required tables: Open the Airlines and Airports tables to access relevant data.

** Identify Relevant Flights: **
1. Fetch the FL_DATE column: Start reading the FL_DATE column from the Airlines table.
2. Filter by August 2018: Use the condition FL_DATE LIKE '2018/8%' to filter flights that occurred in August 2018.
3. Join with Airports for ORIGIN: Identify flights originating from 'San Diego, CA: San Diego International' by joining the Airlines table with the Airports table on the ORIGIN field.
4. Join with Airports for DEST: Similarly, identify flights destined for 'Los Angeles, CA: Los Angeles International' by joining the Airlines table with the Airports table on the DEST field.

** Count the Matching Flights: **
1. Initialize the count: Set up a counter to keep track of how many flights match the criteria.
2. Increment the count: For each flight that meets the conditions (originating from San Diego International and destined for Los Angeles International in August 2018), increment the counter.
3. Store the final count: Once all rows have been processed, store the total count of matching flights.

** Finalize and Deliver the Result: **
1. Prepare the result for output: Format the final count for presentation, ensuring clarity and correctness.
2. Output the final count: Deliver the count as the query result, indicating how many flights met the specified criteria.
3. Clean up resources: Close any open table connections and release temporary storage used during query execution.

**Final Optimized SQL Query:**
```sql
SELECT COUNT(FL_DATE)
 FROM `{BQ_DATA_PROJECT_ID}`.airlines.Airlines
 WHERE FL_DATE LIKE '2018/8%'
 AND ORIGIN = (
   SELECT DISTINCT T2.ORIGIN
   FROM `{BQ_DATA_PROJECT_ID}`.airlines.Airports AS T1
   INNER JOIN `{BQ_DATA_PROJECT_ID}`.airlines.Airlines AS T2 ON T1.Code = T2.ORIGIN
   WHERE T1.Description = 'San Diego, CA: San Diego International' )
 AND DEST = (
   SELECT DISTINCT T4.DEST
   FROM `{BQ_DATA_PROJECT_ID}`.airlines.Airports AS T3
   INNER JOIN `{BQ_DATA_PROJECT_ID}`.airlines.Airlines AS T4 ON T3.Code = T4.DEST
   WHERE T3.Description = 'Los Angeles, CA: Los Angeles International' )
```

===========
Example 7

**************************
【Database Info】
CREATE TABLE `{BQ_DATA_PROJECT_ID}`.food_inspection.businesses
(
       `business_id` INT64,
       `name` STRING OPTIONS(description="the name of the eatery"),
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.food_inspection.inspections
(
       `business_id` INT64 OPTIONS(description="the unique id of the business"),
       `score` INT64 OPTIONS(description="description: the inspection score"),
       `date` DATE,
);

CREATE TABLE `{BQ_DATA_PROJECT_ID}`.food_inspection.violations
(
       `business_id` INT64,
       `date` DATE,
);

**************************
【Question】
Question:
What are the names of the establishments that met all the required standards for 4 consecutive years?
establishment has the same meaning as business; score of 90 or more refers to score ≥ 90; year(date) = 2015; ; met all required standards for 4 consecutive years refers to COUNT(year(date)) = 4 where score = 100;

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.

**Question**: What are the names of the establishments that met all the required standards for 4 consecutive years? establishment has the same meaning as business; score of 90 or more refers to score ≥ 90; year(date) = 2015; ; met all required standards for 4 consecutive years refers to COUNT(year(date)) = 4 where score = 100;

** Query Plan**:

** Preparation Steps: **
1. Initialize the process: Set up the environment and prepare for query execution, including initializing variables and temporary storage.
2. Open required tables: Open the businesses, inspections, and violations tables to access relevant data.

** Filter and Identify Relevant Inspections: **
1. Scan the inspections table: Start reading rows from the inspections table.
2. Filter by score of 100: Select only those inspections where the score is 100, indicating that the establishment met all required standards.
3. Extract year from the inspection date: Use the FORMAT_DATE('%Y', date) function to extract the year from the inspection date.
4. Join with businesses table: Match each inspection to the corresponding business by joining on business_id.

** Identify Businesses Meeting Standards for 4 Consecutive Years: **
1. Aggregate by business and year: Group the data by business name and the extracted year to count the number of years each business met the required standards.
3. Apply row numbering: Use ROW_NUMBER() with a partition by business name and order by year to identify consecutive years.
3. Filter for 4 consecutive years: Group by business name and ensure that the count of years with the required score is exactly 4, indicating 4 consecutive years of meeting the standards.

** Count and Finalize the Results: **
1. Count the matching businesses: For each business, count the number of years that meet the criteria.
2. Select distinct business names: Extract the names of businesses that have met the required standards for 4 consecutive years.
3. Store and prepare the result: Once all businesses have been processed, store the result and prepare it for output.

** Deliver the Final Result: **
1. Prepare the result for output: Format the final list of business names for presentation.
2. Output the final result: Deliver the names of the businesses that met the required standards for 4 consecutive years.
3. Clean up resources: Close any open table connections and release temporary storage used during query execution.

**Final Optimized SQL Query:**
```sql
SELECT DISTINCT T4.name
 FROM ( SELECT T3.name, T3.years, row_number()
 OVER (PARTITION BY T3.name ORDER BY T3.years)
 AS rowNumber FROM ( SELECT DISTINCT name, FORMAT_DATE('%Y', date)
 AS years FROM `{BQ_DATA_PROJECT_ID}`.food_inspection.inspections AS T1
 INNER JOIN `{BQ_DATA_PROJECT_ID}`.food_inspection.businesses AS T2 ON T1.business_id = T2.business_id
 WHERE T1.score = 100 ) AS T3 ) AS T4
 GROUP BY T4.name, DATE_SUB(DATE(CONCAT(T4.years, '-01-01')), INTERVAL (T4.rowNumber - 1) YEAR) HAVING COUNT(T4.years) = 4
```

===========
Example 8

**************************
【Database Info】
CREATE TABLE `bigquery-public-data.covid19_symptom_search.symptom_search_sub_region_2_daily`
(
  country_region_code STRING,
  country_region STRING,
  sub_region_1 STRING,
  sub_region_1_code STRING,
  sub_region_2 STRING,
  sub_region_2_code STRING,
  place_id STRING,
  date DATE,
  symptom_Abdominal_obesity FLOAT64,
  symptom_Abdominal_pain FLOAT64,
  symptom_Acne FLOAT64
)
PARTITION BY date
CLUSTER BY country_region_code, sub_region_1_code, sub_region_2_code, sub_region_2;

**************************
【Question】
Question:
Find the day in which the symptom that occurs most frequently is headache.

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.

**Question**: Find the day in which the symptom that occurs most frequently is headache.

** Query Plan**:

**  Preparation Steps : **
1. Initialize the process: Set up the environment and prepare for query execution, including initializing variables and temporary storage.
2. Open the symptom_search_sub_region_2_daily table: Access the table containing daily symptom search data.

** Extract the headache symptom: **
1. Scan the table: Start reading rows from the symptom_search_sub_region_2_daily table.
2. Identify the headache symptom: Look for the column containing the headache symptom data.
3. Extract the headache symptom value: For each row, extract the value from the headache symptom column.
4. Aggregate by date: Group the data by date to count the occurrences of the headache symptom on each day.

** Sort by frequency: **
1. Order the results in descending order of symptom frequency.
2. Limit the results: Extract the single day with the highest count.

** Step 2: Identify Subtasks **
1. Extract relevant symptom column: While "headache" is not explicitly listed, its frequency might be tracked in a related table (e.g., symptom_search_country_daily) as per the given gold query.
2. Group data by day of the week: Use FORMAT_DATE('%A', date) to extract the day of the week from each date.
3. Aggregate by count: Count the occurrences of the "headache" symptom across dates and group by the day of the week.
4. Sort by frequency: Order the results in descending order of symptom frequency.
5. Limit the results: Extract the single day with the highest count.

** Step 3: Formulate the Query **
1. From the subtasks, the query will:
2. Select the day of the week using FORMAT_DATE('%A', date).
3. Aggregate counts grouped by the day.
4. Sort the results by the aggregated count in descending order.
5. Limit the results to the top record.

** Step 4: Construct the Query **
1. Combining all subtasks, the final query is:
2. SELECT COUNT(symptom_headache) FROM `{BQ_DATA_PROJECT_ID}`.covid19_symptom_search.symptom_search_sub_region_2_daily GROUP BY FORMAT_DATE('%A', date) ORDER BY COUNT(symptom_headache) DESC LIMIT 1;

** Step 5: Finalize the Query **
**Final Optimized SQL Query:**
```sql
SELECT
  FORMAT_DATE('%A', PARSE_DATE('%Y-%m-%d', date)) AS day,
  COUNT(*) AS headache_count
FROM
  `{BQ_DATA_PROJECT_ID}`.covid19_symptom_search.symptom_search_country_daily
GROUP BY
  day
ORDER BY
  headache_count DESC
LIMIT 1;
```

Now is the real question, following the instruction and examples, generate the GoogleSQL with Recursive Divide-and-Conquer approach.
Follow all steps from the strategy. When you get to the final query, output the query string ONLY in the format ```sql ... ```. Make sure you only output one single query.

**************************
【Table creation statements】
{SCHEMA}

**************************
【Question】
Question:
{QUESTION}

**************************
【Answer】
Repeating the question and generating the SQL with Recursive Divide-and-Conquer.
"""

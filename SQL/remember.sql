--useful psql terminal commands
--1. Connect to database
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" 
-U postgres 
-d rentvsbuy

-U postgres     login as user postgres
-d rentvsbuy    connect to database rentvsbuy

--2. Run a SQL file
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" 
-U postgres 
-d rentvsbuy 
-a -v ON_ERROR_STOP=1 
-f "C:\Users\Dong\Desktop\projects\rent-vs-buy-analysis\sql\01_create_raw_tables.sql"

-f file.sql         execute this SQL file
-a                  print each command before executing
-v ON_ERROR_STOP=1  stop immediately if there is an error

--3. Show all databases
--Inside psql:
\l

--4. Connect to another database
\c rentvsbuy

--5. Show all schemas
\dn

--6. Show all tables
--Show tables in current search path:
\dt

--7. Describe table structure
\d raw.city_rent_raw
--This shows columns, data types, indexes, and constraints.


DROP TABLE IF EXISTS table_name;

CREATE TABLE table_name (
    column_name data_type,
    column_name data_type,
    column_name data_type
);

--clear one table
TRUNCATE table_name;

--input data from csv file
\copy table_name FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/rent/calgary_rent.csv' 
WITH (
    FORMAT csv, 
    HEADER true, --This means the first row of the CSV file is column names, not data.
    DELIMITER ',', 
    NULL ''); --if PostgreSQL sees an empty value in the CSV, treat it as NULL.

TRUNCATE raw.tmp_table;
\copy raw.tmp_table FROM 'path/to/file.csv' 
WITH (
    FORMAT csv, 
    HEADER true, 
    DELIMITER ',', 
    NULL ''
    );


INSERT INTO stg.city_house_real_prices (date_period, vancouver_price, calgary_price, edmonton_price, toronto_price, ottawa_price, montreal_price)
SELECT
    month_date AS date_period,

    MAX(CASE WHEN city = 'Vancouver' THEN composite_benchmark_sa END) AS vancouver_price,     
    MAX(CASE WHEN city =  'Calgary' THEN composite_benchmark_sa END) AS calgary_price,
FROM raw.city_house_real_prices
GROUP BY month_date
ORDER BY month_date;

INSERT INTO stg.tsx_cad (date_period, adj_close_price)
SELECT
    TO_DATE(price_date, 'DD-Mon-YY') AS date_period,
    NULLIF(REPLACE(TRIM(adj_close_price), ',', ''), '')::NUMERIC AS adj_close_price 
FROM raw.tsx_raw;
--Original value: '33,891.20'
↓
--TRIM removes spaces: '33,891.20'
↓
--REPLACE removes comma: '33891.20'
↓
---NULLIF checks if it is empty: not empty, keep '33891.20'
↓
--::NUMERIC converts it to number: 33891.20


--went to divit a column with one number, 
--this example is to rebase the index from 2010 = 100 to 1990 = 100
--all index values are divided by the 1990 value and multiplied by 100 to rebase to 1990 = 100
INSERT INTO analysis.canada_house_price_index_1990_100 (
    date_period, 
    price_index_original, 
    price_index_1990_100
    )
SELECT
    date_period AS date_period,
    price_index AS price_index_original,
    price_index / (
        SELECT price_index
        FROM stg.canada_house_price_index_2010_100
        WHERE EXTRACT(YEAR FROM date_period) = 1990
          AND price_index IS NOT NULL
        ORDER BY date_period
        LIMIT 1
    ) * 100 AS price_index_1990_100
FROM stg.canada_house_price_index_2010_100;
    
--IF DO NOT HAVE fx.date_period = sp.date_period
INSERT INTO analysis.sp500_index_1990_100 (
    date_period, 
    price_usd, 
    price_cad)
SELECT
    sp.date_period AS date_period,
    sp.adj_close_price AS price_usd,
    sp.adj_close_price * fx.dexcaus AS price_cad
FROM stg.sp500_usd sp
LEFT JOIN LATERAL(
    SELECT dexcaus
    FROM stg.usd_cad fx
    WHERE fx.date_period <= sp.date_period
        AND fx.dexcaus IS NOT NULL
    ORDER BY fx.date_period DESC
    LIMIT 1 
) AS fx ON TRUE;

--how to use update
UPDATE table_name
SET column_name = new_value
WHERE condition;

--convert wildth table into long
CREATE TABLE analysis.city_rent_long AS
SELECT
    t.date_period,
    x.city,
    x.price
FROM stg.city_rent AS t
CROSS JOIN LATERAL (
    VALUES
        ('Vancouver', t.vancouver_price),
        ('Calgary', t.calgary_price),
        ('Edmonton', t.edmonton_price),
        ('Toronto', t.toronto_price),
        ('Ottawa', t.ottawa_price),
        ('Montreal', t.montreal_price),
        ('Canada', t.canada_price)
) AS x(city, price)
ORDER BY
    t.date_period,
    x.city;



尤其你这个项目有 PostgreSQL + Python + Power BI，比较容易出现长查询。

如果一个 SQL 很久没结束，不要直接再运行一次相同 SQL。

先检查：

SELECT
    pid,
    state,
    query_start,
    wait_event_type,
    wait_event,
    LEFT(query, 200)
FROM pg_stat_activity
WHERE datname = current_database();
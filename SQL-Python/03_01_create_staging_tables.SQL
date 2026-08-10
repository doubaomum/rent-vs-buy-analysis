CREATE SCHEMA IF NOT EXISTS stg;

-- =========================================================
-- BIS Canada House Price Index - Staging Table
-- Source: raw.canada_house_price_index_2010_100
-- Unit: Index, 2010 = 100
-- Frequency: Quarterly
-- =========================================================

DROP TABLE IF EXISTS stg.canada_house_price_index_2010_100;

CREATE TABLE stg.canada_house_price_index_2010_100 (
    date_period DATE,
    price_index NUMERIC
);

INSERT INTO stg.canada_house_price_index_2010_100 (date_period, price_index)
SELECT
    TO_DATE(time_period, 'YYYY-MM-DD') AS date_period,
    obs_value::NUMERIC AS price_index
FROM raw.canada_house_price_index_2010_100;

-- =========================================================
-- City House Price Index - Staging Table
-- Source: raw.city_house_price_index
-- Unit: Price index
-- Frequency: Monthly
-- =========================================================
DROP TABLE IF EXISTS stg.city_house_price_index;
CREATE TABLE stg.city_house_price_index (
    date_period DATE,
    vancouver_index NUMERIC,
    calgary_index NUMERIC,
    edmonton_index NUMERIC,
    toronto_index NUMERIC,
    ottawa_index NUMERIC,
    montreal_index NUMERIC
);

INSERT INTO stg.city_house_price_index (date_period, vancouver_index, calgary_index, edmonton_index, toronto_index, ottawa_index, montreal_index)
SELECT
    TO_DATE(TRIM(transaction_date), 'Mon-YYYY') AS date_period,
    NULLIF(REPLACE(TRIM(bc_vancouver_index), ',', ''), '')::NUMERIC AS vancouver_index,
    NULLIF(REPLACE(TRIM(ab_calgary_index), ',', ''), '')::NUMERIC AS calgary_index,
    NULLIF(REPLACE(TRIM(ab_edmonton_index), ',', ''), '')::NUMERIC AS edmonton_index,
    NULLIF(REPLACE(TRIM(on_toronto_index), ',', ''), '')::NUMERIC AS toronto_index,
    NULLIF(REPLACE(TRIM(on_ottawa_index), ',', ''), '')::NUMERIC AS ottawa_index,
    NULLIF(REPLACE(TRIM(qc_montreal_index), ',', ''), '')::NUMERIC AS montreal_index
FROM raw.city_house_price_index;    

-- =========================================================
-- City Real House Prices - Staging Table
-- Source: raw.city_house_real_prices
-- Unit: Benchmark price, monthly adjusted
-- Shape: wide table, one row per month
-- =========================================================

DROP TABLE IF EXISTS stg.city_house_prices;
CREATE TABLE stg.city_house_prices (
    date_period DATE,
    canada_price NUMERIC,
    vancouver_price NUMERIC,
    calgary_price NUMERIC,
    edmonton_price NUMERIC,
    toronto_price NUMERIC,
    ottawa_price NUMERIC,
    montreal_price NUMERIC
);

INSERT INTO stg.city_house_prices (date_period, canada_price, vancouver_price, calgary_price, edmonton_price, toronto_price, ottawa_price, montreal_price)
SELECT
    TO_DATE(TRIM(month_date), 'YYYY-MM-DD') AS date_period,

    MAX(CASE WHEN city = 'Canada' THEN composite_benchmark_sa END) AS canada_price,
    MAX(CASE WHEN city = 'Vancouver' THEN composite_benchmark_sa END) AS vancouver_price,     
    MAX(CASE WHEN city =  'Calgary' THEN composite_benchmark_sa END) AS calgary_price,
    MAX(CASE WHEN city =  'Edmonton' THEN composite_benchmark_sa END) AS edmonton_price,
    MAX(CASE WHEN city =  'Toronto' THEN composite_benchmark_sa END) AS toronto_price,
    MAX(CASE WHEN city =  'Ottawa' THEN composite_benchmark_sa END) AS ottawa_price, 
    MAX(CASE WHEN city =  'Montreal' THEN composite_benchmark_sa END) AS montreal_price
FROM raw.city_house_real_prices
GROUP BY month_date
ORDER BY month_date;

-- =========================================================
-- City_lebel House index Prices - Staging Table
-- Source: raw.city_house_real_prices
-- Unit: Benchmark price, monthly adjusted
-- Shape: wide table, one row per month
-- =========================================================

DROP TABLE IF EXISTS stg.city_indexed_house_prices;
CREATE TABLE stg.city_indexed_house_prices (
    date_period DATE,
    canada_price_index NUMERIC,
    vancouver_price_index NUMERIC,
    calgary_price_index NUMERIC,
    edmonton_price_index NUMERIC,
    toronto_price_index NUMERIC,
    ottawa_price_index NUMERIC,
    montreal_price_index NUMERIC
);

INSERT INTO stg.city_indexed_house_prices (date_period, canada_price_index, vancouver_price_index, calgary_price_index, edmonton_price_index, toronto_price_index, ottawa_price_index, montreal_price_index)
SELECT
    TO_DATE(TRIM(month_date), 'YYYY-MM-DD') AS date_period,

    MAX(CASE WHEN city = 'Canada' THEN composite_hpi_sa END) AS canada_price_index,
    MAX(CASE WHEN city = 'Vancouver' THEN composite_hpi_sa END) AS vancouver_price_index,     
    MAX(CASE WHEN city =  'Calgary' THEN composite_hpi_sa END) AS calgary_price_index,
    MAX(CASE WHEN city =  'Edmonton' THEN composite_hpi_sa END) AS edmonton_price_index,
    MAX(CASE WHEN city =  'Toronto' THEN composite_hpi_sa END) AS toronto_price_index,
    MAX(CASE WHEN city =  'Ottawa' THEN composite_hpi_sa END) AS ottawa_price_index, 
    MAX(CASE WHEN city =  'Montreal' THEN composite_hpi_sa END) AS montreal_price_index
FROM raw.city_house_real_prices
GROUP BY month_date
ORDER BY month_date;

-- =========================================================
-- S&P 500 Adjusted Close Price - USD
-- Source: raw.sp500_raw
-- =========================================================
DROP TABLE IF EXISTS stg.sp500_usd;
CREATE TABLE stg.sp500_usd (
    date_period DATE,
    adj_close_price NUMERIC
);

INSERT INTO stg.sp500_usd (date_period, adj_close_price)
SELECT
    TO_DATE(price_date, 'YYYY-MM-DD') AS date_period,
    NULLIF(REPLACE(TRIM(adj_close_price), ',', ''), '')::NUMERIC AS adj_close_price
FROM raw.sp500_raw;

-- =========================================================
-- TSX Adjusted Close Price - CAD
-- Source: raw.tsx_raw
-- =========================================================
DROP TABLE IF EXISTS stg.tsx_cad;
CREATE TABLE stg.tsx_cad (
    date_period DATE,
    adj_close_price NUMERIC
);

INSERT INTO stg.tsx_cad (date_period, adj_close_price)
SELECT
    TO_DATE(price_date, 'DD-Mon-YY') AS date_period,
    NULLIF(REPLACE(TRIM(adj_close_price), ',', ''), '')::NUMERIC AS adj_close_price 
FROM raw.tsx_raw;
-- =========================================================
-- VT Adjusted Close Price - USD
-- Source: raw.vt_raw
-- =========================================================
DROP TABLE IF EXISTS stg.vt_usd;
CREATE TABLE stg.vt_usd (
    date_period DATE,
    adj_close_price NUMERIC
);

INSERT INTO stg.vt_usd (date_period, adj_close_price)
SELECT
    TO_DATE(price_date, 'DD-Mon-YY') AS date_period,
    NULLIF(REPLACE(TRIM(adj_close_price), ',', ''), '')::NUMERIC AS adj_close_price
FROM raw.vt_raw;

DELETE FROM stg.vt_usd
WHERE adj_close_price IS NULL;

-- =========================================================
-- city_rent - Staging Table
-- Source: raw.city_rent_raw
-- =========================================================
DROP TABLE IF EXISTS stg.city_rent;
CREATE TABLE stg.city_rent(
    date_period DATE,
    canada_price NUMERIC,
    vancouver_price NUMERIC,
    calgary_price NUMERIC,
    edmonton_price NUMERIC,
    toronto_price NUMERIC,
    ottawa_price NUMERIC,
    montreal_price NUMERIC
);

INSERT INTO stg.city_rent (date_period, canada_price, vancouver_price, calgary_price, edmonton_price, toronto_price, ottawa_price, montreal_price)
SELECT
    TO_DATE(rent_period, 'YYYY Month') AS date_period,

    MAX(CASE WHEN city = 'Canada' THEN NULLIF(REPLACE(TRIM(total_rent), ',', ''), '')::NUMERIC END) AS canada_price,
    MAX(CASE WHEN city = 'Vancouver' THEN NULLIF(REPLACE(TRIM(total_rent), ',', ''), '')::NUMERIC END) AS vancouver_price,     
    MAX(CASE WHEN city =  'Calgary' THEN NULLIF(REPLACE(TRIM(total_rent), ',', ''), '')::NUMERIC END) AS calgary_price,
    MAX(CASE WHEN city =  'Edmonton' THEN NULLIF(REPLACE(TRIM(total_rent), ',', ''), '')::NUMERIC END) AS edmonton_price,
    MAX(CASE WHEN city =  'Toronto' THEN NULLIF(REPLACE(TRIM(total_rent), ',', ''), '')::NUMERIC END) AS toronto_price,
    MAX(CASE WHEN city =  'Ottawa' THEN NULLIF(REPLACE(TRIM(total_rent), ',', ''), '')::NUMERIC END) AS ottawa_price, 
    MAX(CASE WHEN city =  'Montreal' THEN NULLIF(REPLACE(TRIM(total_rent), ',', ''), '')::NUMERIC END) AS montreal_price
FROM raw.city_rent_raw
GROUP BY rent_period
ORDER BY rent_period;

-- =========================================================
-- Canada CPI - Staging Table
-- Source: raw.canada_cpi_raw
-- =========================================================
DROP TABLE IF EXISTS stg.canada_cpi;    
CREATE TABLE stg.canada_cpi (
    date_period DATE,
    cpi_value NUMERIC
);

INSERT INTO stg.canada_cpi (date_period, cpi_value)
SELECT
    TO_DATE(cpi_period, 'YYYY-MM-DD') AS date_period,
    NULLIF(REPLACE(TRIM(cpi_value), ',', ''), '')::NUMERIC AS cpi_value     
FROM raw.canada_cpi_raw;

-- =========================================================
-- USD/CAD Exchange Rate - Staging Table
-- Source: raw.usd_cad_raw
-- =========================================================
DROP TABLE IF EXISTS stg.usd_cad;    
CREATE TABLE stg.usd_cad (
    date_period DATE,
    dexcaus NUMERIC
);

INSERT INTO stg.usd_cad (date_period, dexcaus)
SELECT
    TO_DATE(observation_date, 'YYYY-MM-DD') AS date_period,
    NULLIF(REPLACE(TRIM(dexcaus), ',', ''), '')::NUMERIC AS dexcaus     
FROM raw.usd_cad_raw;

-- =========================================================
-- Canada 5-Year Mortgage Rate - Staging Table
-- Source: raw.canada_5yearmortgage_raw
-- =========================================================
DROP TABLE IF EXISTS stg.canada_5yearmortgage;    
CREATE TABLE stg.canada_5yearmortgage (
    date_period DATE,
    mortgage_rate NUMERIC
);

INSERT INTO stg.canada_5yearmortgage (date_period, mortgage_rate)
SELECT
    TO_DATE(mortgage_period, 'YYYY-MM-DD') AS date_period,
    NULLIF(REPLACE(TRIM(mortgage_rate), ',', ''), '')::NUMERIC AS mortgage_rate     
FROM raw.canada_5yearmortgage_raw;


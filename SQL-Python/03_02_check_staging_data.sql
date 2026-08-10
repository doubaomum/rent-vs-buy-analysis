-- =========================================================
-- CHECK STAGING TABLES ROW COUNTS
-- =========================================================
SELECT 'canada_house_price_index_2010_100' AS table_name, COUNT(*) AS row_count
FROM stg.canada_house_price_index_2010_100

UNION ALL
SELECT 'city_house_price_index', COUNT(*)
FROM stg.city_house_price_index

UNION ALL
SELECT 'city_house_prices', COUNT(*)
FROM stg.city_house_prices

UNION ALL
SELECT 'city_indexed_house_prices', COUNT(*)
FROM stg.city_indexed_house_prices

UNION ALL
SELECT 'sp500_usd', COUNT(*)
FROM stg.sp500_usd

UNION ALL
SELECT 'tsx_cad', COUNT(*)
FROM stg.tsx_cad

UNION ALL
SELECT 'vt_usd', COUNT(*)
FROM stg.vt_usd

UNION ALL
SELECT 'city_rent', COUNT(*)
FROM stg.city_rent

UNION ALL
SELECT 'canada_cpi', COUNT(*)
FROM stg.canada_cpi

UNION ALL
SELECT 'usd_cad', COUNT(*)
FROM stg.usd_cad

UNION ALL
SELECT 'canada_5yearmortgage', COUNT(*)
FROM stg.canada_5yearmortgage;

-- =========================================================
-- Date Ranges
-- =========================================================

SELECT 'canada_house_price_index_2010_100' AS table_name,
       MIN(date_period) AS min_date,
       MAX(date_period) AS max_date
FROM stg.canada_house_price_index_2010_100

UNION ALL
SELECT 'city_house_price_index',
       MIN(date_period),
       MAX(date_period)
FROM stg.city_house_price_index

UNION ALL
SELECT 'city_house_real_prices',
       MIN(date_period),
       MAX(date_period)
FROM stg.city_house_real_prices

UNION ALL
SELECT 'sp500_usd',
       MIN(date_period),
       MAX(date_period)
FROM stg.sp500_usd

UNION ALL
SELECT 'tsx_cad',
       MIN(date_period),
       MAX(date_period)
FROM stg.tsx_cad

UNION ALL
SELECT 'vt_usd',
       MIN(date_period),
       MAX(date_period)
FROM stg.vt_usd

UNION ALL
SELECT 'city_rent',
       MIN(date_period),
       MAX(date_period)
FROM stg.city_rent

UNION ALL
SELECT 'canada_cpi',
       MIN(date_period),
       MAX(date_period)
FROM stg.canada_cpi

UNION ALL
SELECT 'usd_cad',
       MIN(date_period),
       MAX(date_period)
FROM stg.usd_cad

UNION ALL
SELECT 'canada_5yearmortgage',
       MIN(date_period),
       MAX(date_period)
FROM stg.canada_5yearmortgage;

-- =========================================================
-- Duplicate Date Checks
-- =========================================================

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.canada_house_price_index_2010_100
GROUP BY date_period
HAVING COUNT(*) > 1;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.city_house_price_index
GROUP BY date_period
HAVING COUNT(*) > 1;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.city_house_real_prices
GROUP BY date_period
HAVING COUNT(*) > 1;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.city_rent
GROUP BY date_period
HAVING COUNT(*) > 1;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.canada_cpi
GROUP BY date_period
HAVING COUNT(*) > 1;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.canada_5yearmortgage
GROUP BY date_period
HAVING COUNT(*) > 1;
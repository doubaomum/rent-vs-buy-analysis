-- =========================================================
-- RAW SCHEMA DATA QUALITY CHECKS
-- Purpose:
--   Validate source ingestion before staging transformations.
--
-- Raw layer checks focus on:
--   1. Row counts
--   2. Missing / blank natural keys
--   3. Duplicate natural keys
--   4. Source coverage / city coverage
--
-- Parsing, type conversion, business rules, and model checks
-- should be handled in staging / analysis / simulation checks.
-- =========================================================


-- =========================================================
-- 1. ROW COUNTS
-- =========================================================
SELECT 'raw.canada_house_price_index_2010_100' AS table_name, COUNT(*) AS row_count
FROM raw.canada_house_price_index_2010_100

UNION ALL

SELECT 'raw.city_house_price_index', COUNT(*)
FROM raw.city_house_price_index

UNION ALL

SELECT 'raw.city_house_real_prices', COUNT(*)
FROM raw.city_house_real_prices

UNION ALL

SELECT 'raw.sp500_raw', COUNT(*)
FROM raw.sp500_raw

UNION ALL

SELECT 'raw.tsx_raw', COUNT(*)
FROM raw.tsx_raw

UNION ALL

SELECT 'raw.vt_raw', COUNT(*)
FROM raw.vt_raw

UNION ALL

SELECT 'raw.city_rent_raw', COUNT(*)
FROM raw.city_rent_raw

UNION ALL

SELECT 'raw.canada_cpi_raw', COUNT(*)
FROM raw.canada_cpi_raw

UNION ALL

SELECT 'raw.usd_cad_raw', COUNT(*)
FROM raw.usd_cad_raw

UNION ALL

SELECT 'raw.canada_5yearmortgage_raw', COUNT(*)
FROM raw.canada_5yearmortgage_raw

ORDER BY table_name;


-- =========================================================
-- 2. MISSING / BLANK NATURAL KEYS
--
-- Expected result:
--   missing_key_rows = 0 for every table.
-- =========================================================
SELECT
    'raw.canada_house_price_index_2010_100' AS table_name,
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(series_key), '') IS NULL
           OR NULLIF(BTRIM(time_period), '') IS NULL
    ) AS missing_key_rows
FROM raw.canada_house_price_index_2010_100

UNION ALL

SELECT
    'raw.city_house_price_index',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(transaction_date), '') IS NULL
    )
FROM raw.city_house_price_index

UNION ALL

SELECT
    'raw.city_house_real_prices',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(city), '') IS NULL
           OR NULLIF(BTRIM(month_date), '') IS NULL
    )
FROM raw.city_house_real_prices

UNION ALL

SELECT
    'raw.sp500_raw',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(price_date), '') IS NULL
    )
FROM raw.sp500_raw

UNION ALL

SELECT
    'raw.tsx_raw',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(price_date), '') IS NULL
    )
FROM raw.tsx_raw

UNION ALL

SELECT
    'raw.vt_raw',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(price_date), '') IS NULL
    )
FROM raw.vt_raw

UNION ALL

SELECT
    'raw.city_rent_raw',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(city), '') IS NULL
           OR NULLIF(BTRIM(rent_period), '') IS NULL
    )
FROM raw.city_rent_raw

UNION ALL

SELECT
    'raw.canada_cpi_raw',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(cpi_period), '') IS NULL
    )
FROM raw.canada_cpi_raw

UNION ALL

SELECT
    'raw.usd_cad_raw',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(observation_date), '') IS NULL
    )
FROM raw.usd_cad_raw

UNION ALL

SELECT
    'raw.canada_5yearmortgage_raw',
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(mortgage_period), '') IS NULL
    )
FROM raw.canada_5yearmortgage_raw

ORDER BY table_name;


-- =========================================================
-- 3. DUPLICATE NATURAL KEY SUMMARY
--
-- Expected result:
--   duplicate_groups = 0 for every table.
-- =========================================================
SELECT
    'raw.canada_house_price_index_2010_100' AS table_name,
    COUNT(*) AS duplicate_groups
FROM (
    SELECT
        series_key,
        time_period
    FROM raw.canada_house_price_index_2010_100
    GROUP BY
        series_key,
        time_period
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.city_house_price_index',
    COUNT(*)
FROM (
    SELECT transaction_date
    FROM raw.city_house_price_index
    GROUP BY transaction_date
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.city_house_real_prices',
    COUNT(*)
FROM (
    SELECT
        city,
        month_date
    FROM raw.city_house_real_prices
    GROUP BY
        city,
        month_date
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.sp500_raw',
    COUNT(*)
FROM (
    SELECT price_date
    FROM raw.sp500_raw
    GROUP BY price_date
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.tsx_raw',
    COUNT(*)
FROM (
    SELECT price_date
    FROM raw.tsx_raw
    GROUP BY price_date
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.vt_raw',
    COUNT(*)
FROM (
    SELECT price_date
    FROM raw.vt_raw
    GROUP BY price_date
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.city_rent_raw',
    COUNT(*)
FROM (
    SELECT
        city,
        rent_period
    FROM raw.city_rent_raw
    GROUP BY
        city,
        rent_period
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.canada_cpi_raw',
    COUNT(*)
FROM (
    SELECT cpi_period
    FROM raw.canada_cpi_raw
    GROUP BY cpi_period
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.usd_cad_raw',
    COUNT(*)
FROM (
    SELECT observation_date
    FROM raw.usd_cad_raw
    GROUP BY observation_date
    HAVING COUNT(*) > 1
) AS d

UNION ALL

SELECT
    'raw.canada_5yearmortgage_raw',
    COUNT(*)
FROM (
    SELECT mortgage_period
    FROM raw.canada_5yearmortgage_raw
    GROUP BY mortgage_period
    HAVING COUNT(*) > 1
) AS d

ORDER BY table_name;


-- =========================================================
-- 4. CITY COVERAGE
-- Informational check.
-- =========================================================

-- House-price cities
SELECT
    city,
    COUNT(*) AS row_count,
    COUNT(DISTINCT month_date) AS distinct_periods
FROM raw.city_house_real_prices
GROUP BY city
ORDER BY city;


-- Rent cities
SELECT
    city,
    COUNT(*) AS row_count,
    COUNT(DISTINCT rent_period) AS distinct_periods
FROM raw.city_rent_raw
GROUP BY city
ORDER BY city;


-- =========================================================
-- 5. OPTIONAL: CITY COVERAGE DIFFERENCES
--
-- This is informational only because the two source datasets
-- may legitimately have different geographic coverage.
-- =========================================================
WITH house_cities AS (
    SELECT DISTINCT BTRIM(city) AS city
    FROM raw.city_house_real_prices
    WHERE NULLIF(BTRIM(city), '') IS NOT NULL
),
rent_cities AS (
    SELECT DISTINCT BTRIM(city) AS city
    FROM raw.city_rent_raw
    WHERE NULLIF(BTRIM(city), '') IS NOT NULL
)
SELECT
    COALESCE(h.city, r.city) AS city,
    CASE
        WHEN h.city IS NOT NULL AND r.city IS NOT NULL THEN 'both'
        WHEN h.city IS NOT NULL THEN 'house_only'
        ELSE 'rent_only'
    END AS coverage
FROM house_cities AS h
FULL OUTER JOIN rent_cities AS r
    ON h.city = r.city
ORDER BY city;


-- =========================================================
-- 6. DUPLICATE DETAILS
-- Run these when section 3 reports duplicate_groups > 0.
-- =========================================================

-- Canada house-price index
SELECT
    series_key,
    time_period,
    COUNT(*) AS duplicate_count
FROM raw.canada_house_price_index_2010_100
GROUP BY
    series_key,
    time_period
HAVING COUNT(*) > 1
ORDER BY
    series_key,
    time_period;


-- Wide city house-price index
SELECT
    transaction_date,
    COUNT(*) AS duplicate_count
FROM raw.city_house_price_index
GROUP BY transaction_date
HAVING COUNT(*) > 1
ORDER BY transaction_date;


-- City real house prices
SELECT
    city,
    month_date,
    COUNT(*) AS duplicate_count
FROM raw.city_house_real_prices
GROUP BY
    city,
    month_date
HAVING COUNT(*) > 1
ORDER BY
    city,
    month_date;


-- S&P 500
SELECT
    price_date,
    COUNT(*) AS duplicate_count
FROM raw.sp500_raw
GROUP BY price_date
HAVING COUNT(*) > 1
ORDER BY price_date;


-- TSX
SELECT
    price_date,
    COUNT(*) AS duplicate_count
FROM raw.tsx_raw
GROUP BY price_date
HAVING COUNT(*) > 1
ORDER BY price_date;


-- VT
SELECT
    price_date,
    COUNT(*) AS duplicate_count
FROM raw.vt_raw
GROUP BY price_date
HAVING COUNT(*) > 1
ORDER BY price_date;


-- City rent
SELECT
    city,
    rent_period,
    COUNT(*) AS duplicate_count
FROM raw.city_rent_raw
GROUP BY
    city,
    rent_period
HAVING COUNT(*) > 1
ORDER BY
    city,
    rent_period;


-- Canada CPI
SELECT
    cpi_period,
    COUNT(*) AS duplicate_count
FROM raw.canada_cpi_raw
GROUP BY cpi_period
HAVING COUNT(*) > 1
ORDER BY cpi_period;


-- USD/CAD
SELECT
    observation_date,
    COUNT(*) AS duplicate_count
FROM raw.usd_cad_raw
GROUP BY observation_date
HAVING COUNT(*) > 1
ORDER BY observation_date;


-- Canada 5-year mortgage rate
SELECT
    mortgage_period,
    COUNT(*) AS duplicate_count
FROM raw.canada_5yearmortgage_raw
GROUP BY mortgage_period
HAVING COUNT(*) > 1
ORDER BY mortgage_period;

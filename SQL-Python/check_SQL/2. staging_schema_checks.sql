-- =========================================================
-- STAGING SCHEMA DATA QUALITY CHECKS
-- Finalized against the current stg schema.
--
-- Purpose:
--   Validate that raw data were parsed, typed, pivoted, and loaded
--   into staging correctly before analysis-layer transformations.
--
-- Main checks:
--   1. Row counts
--   2. Raw -> staging row-count reconciliation
--   3. Date coverage
--   4. NULL date / duplicate date checks
--   5. Core numeric NULL / non-positive checks
--   6. Wide-table city coverage
--   7. Monthly-date alignment for monthly tables
--   8. Duplicate details for debugging
-- =========================================================


-- =========================================================
-- 1. STAGING ROW COUNTS
-- =========================================================
SELECT 'stg.canada_house_price_index_2010_100' AS table_name, COUNT(*) AS row_count
FROM stg.canada_house_price_index_2010_100

UNION ALL
SELECT 'stg.city_house_price_index', COUNT(*)
FROM stg.city_house_price_index

UNION ALL
SELECT 'stg.city_house_prices', COUNT(*)
FROM stg.city_house_prices

UNION ALL
SELECT 'stg.city_indexed_house_prices', COUNT(*)
FROM stg.city_indexed_house_prices

UNION ALL
SELECT 'stg.sp500_usd', COUNT(*)
FROM stg.sp500_usd

UNION ALL
SELECT 'stg.tsx_cad', COUNT(*)
FROM stg.tsx_cad

UNION ALL
SELECT 'stg.vt_usd', COUNT(*)
FROM stg.vt_usd

UNION ALL
SELECT 'stg.city_rent', COUNT(*)
FROM stg.city_rent

UNION ALL
SELECT 'stg.canada_cpi', COUNT(*)
FROM stg.canada_cpi

UNION ALL
SELECT 'stg.usd_cad', COUNT(*)
FROM stg.usd_cad

UNION ALL
SELECT 'stg.canada_5yearmortgage', COUNT(*)
FROM stg.canada_5yearmortgage

ORDER BY table_name;


-- =========================================================
-- 2. RAW -> STAGING ROW-COUNT RECONCILIATION
--
-- expected_difference = 0 is ideal.
--
-- Pivoted tables:
--   city_house_prices / city_indexed_house_prices
--       expected rows = distinct raw month_date values
--
--   city_rent
--       expected rows = distinct raw rent_period values
--
-- VT:
--   staging explicitly deletes NULL adjusted-close rows, so expected
--   rows are raw rows with a nonblank adjusted-close value.
-- =========================================================
WITH reconciliation AS (

    SELECT
        'canada_house_price_index_2010_100' AS dataset,
        (SELECT COUNT(*) FROM raw.canada_house_price_index_2010_100) AS expected_rows,
        (SELECT COUNT(*) FROM stg.canada_house_price_index_2010_100) AS actual_rows

    UNION ALL

    SELECT
        'city_house_price_index',
        (SELECT COUNT(*) FROM raw.city_house_price_index),
        (SELECT COUNT(*) FROM stg.city_house_price_index)

    UNION ALL

    SELECT
        'city_house_prices',
        (
            SELECT COUNT(DISTINCT month_date)
            FROM raw.city_house_real_prices
            WHERE NULLIF(BTRIM(month_date), '') IS NOT NULL
        ),
        (SELECT COUNT(*) FROM stg.city_house_prices)

    UNION ALL

    SELECT
        'city_indexed_house_prices',
        (
            SELECT COUNT(DISTINCT month_date)
            FROM raw.city_house_real_prices
            WHERE NULLIF(BTRIM(month_date), '') IS NOT NULL
        ),
        (SELECT COUNT(*) FROM stg.city_indexed_house_prices)

    UNION ALL

    SELECT
        'sp500_usd',
        (SELECT COUNT(*) FROM raw.sp500_raw),
        (SELECT COUNT(*) FROM stg.sp500_usd)

    UNION ALL

    SELECT
        'tsx_cad',
        (SELECT COUNT(*) FROM raw.tsx_raw),
        (SELECT COUNT(*) FROM stg.tsx_cad)

    UNION ALL

    SELECT
        'vt_usd',
        (
            SELECT COUNT(*)
            FROM raw.vt_raw
            WHERE NULLIF(BTRIM(adj_close_price), '') IS NOT NULL
        ),
        (SELECT COUNT(*) FROM stg.vt_usd)

    UNION ALL

    SELECT
        'city_rent',
        (
            SELECT COUNT(DISTINCT rent_period)
            FROM raw.city_rent_raw
            WHERE NULLIF(BTRIM(rent_period), '') IS NOT NULL
        ),
        (SELECT COUNT(*) FROM stg.city_rent)

    UNION ALL

    SELECT
        'canada_cpi',
        (SELECT COUNT(*) FROM raw.canada_cpi_raw),
        (SELECT COUNT(*) FROM stg.canada_cpi)

    UNION ALL

    SELECT
        'usd_cad',
        (SELECT COUNT(*) FROM raw.usd_cad_raw),
        (SELECT COUNT(*) FROM stg.usd_cad)

    UNION ALL

    SELECT
        'canada_5yearmortgage',
        (SELECT COUNT(*) FROM raw.canada_5yearmortgage_raw),
        (SELECT COUNT(*) FROM stg.canada_5yearmortgage)
)
SELECT
    dataset,
    expected_rows,
    actual_rows,
    actual_rows - expected_rows AS row_difference
FROM reconciliation
ORDER BY dataset;


-- =========================================================
-- 3. DATE COVERAGE
-- Informational check.
-- =========================================================
SELECT
    'stg.canada_house_price_index_2010_100' AS table_name,
    MIN(date_period) AS min_date,
    MAX(date_period) AS max_date,
    COUNT(DISTINCT date_period) AS distinct_dates
FROM stg.canada_house_price_index_2010_100

UNION ALL
SELECT
    'stg.city_house_price_index',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.city_house_price_index

UNION ALL
SELECT
    'stg.city_house_prices',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.city_house_prices

UNION ALL
SELECT
    'stg.city_indexed_house_prices',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.city_indexed_house_prices

UNION ALL
SELECT
    'stg.sp500_usd',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.sp500_usd

UNION ALL
SELECT
    'stg.tsx_cad',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.tsx_cad

UNION ALL
SELECT
    'stg.vt_usd',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.vt_usd

UNION ALL
SELECT
    'stg.city_rent',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.city_rent

UNION ALL
SELECT
    'stg.canada_cpi',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.canada_cpi

UNION ALL
SELECT
    'stg.usd_cad',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.usd_cad

UNION ALL
SELECT
    'stg.canada_5yearmortgage',
    MIN(date_period),
    MAX(date_period),
    COUNT(DISTINCT date_period)
FROM stg.canada_5yearmortgage

ORDER BY table_name;


-- =========================================================
-- 4. NULL DATE + DUPLICATE DATE SUMMARY
--
-- All current staging tables are one-row-per-date tables.
--
-- Expected:
--   null_date_rows   = 0
--   duplicate_dates  = 0
-- =========================================================
WITH checks AS (

    SELECT
        'stg.canada_house_price_index_2010_100' AS table_name,
        COUNT(*) FILTER (WHERE date_period IS NULL) AS null_date_rows,
        COUNT(*) - COUNT(DISTINCT date_period) AS extra_duplicate_rows
    FROM stg.canada_house_price_index_2010_100

    UNION ALL

    SELECT
        'stg.city_house_price_index',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.city_house_price_index

    UNION ALL

    SELECT
        'stg.city_house_prices',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.city_house_prices

    UNION ALL

    SELECT
        'stg.city_indexed_house_prices',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.city_indexed_house_prices

    UNION ALL

    SELECT
        'stg.sp500_usd',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.sp500_usd

    UNION ALL

    SELECT
        'stg.tsx_cad',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.tsx_cad

    UNION ALL

    SELECT
        'stg.vt_usd',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.vt_usd

    UNION ALL

    SELECT
        'stg.city_rent',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.city_rent

    UNION ALL

    SELECT
        'stg.canada_cpi',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.canada_cpi

    UNION ALL

    SELECT
        'stg.usd_cad',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.usd_cad

    UNION ALL

    SELECT
        'stg.canada_5yearmortgage',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        COUNT(*) - COUNT(DISTINCT date_period)
    FROM stg.canada_5yearmortgage
)
SELECT
    table_name,
    null_date_rows,
    extra_duplicate_rows
FROM checks
ORDER BY table_name;


-- =========================================================
-- 5A. CORE SINGLE-SERIES NUMERIC CHECKS
--
-- Expected:
--   null_value_rows       = 0
--   non_positive_rows     = 0
--
-- These fields represent index levels, adjusted-close prices,
-- CPI, FX levels, or mortgage rates, so <= 0 is not expected.
-- =========================================================
SELECT
    'stg.canada_house_price_index_2010_100.price_index' AS field_name,
    COUNT(*) FILTER (WHERE price_index IS NULL) AS null_value_rows,
    COUNT(*) FILTER (WHERE price_index <= 0) AS non_positive_rows
FROM stg.canada_house_price_index_2010_100

UNION ALL

SELECT
    'stg.sp500_usd.adj_close_price',
    COUNT(*) FILTER (WHERE adj_close_price IS NULL),
    COUNT(*) FILTER (WHERE adj_close_price <= 0)
FROM stg.sp500_usd

UNION ALL

SELECT
    'stg.tsx_cad.adj_close_price',
    COUNT(*) FILTER (WHERE adj_close_price IS NULL),
    COUNT(*) FILTER (WHERE adj_close_price <= 0)
FROM stg.tsx_cad

UNION ALL

SELECT
    'stg.vt_usd.adj_close_price',
    COUNT(*) FILTER (WHERE adj_close_price IS NULL),
    COUNT(*) FILTER (WHERE adj_close_price <= 0)
FROM stg.vt_usd

UNION ALL

SELECT
    'stg.canada_cpi.cpi_value',
    COUNT(*) FILTER (WHERE cpi_value IS NULL),
    COUNT(*) FILTER (WHERE cpi_value <= 0)
FROM stg.canada_cpi

UNION ALL

SELECT
    'stg.usd_cad.dexcaus',
    COUNT(*) FILTER (WHERE dexcaus IS NULL),
    COUNT(*) FILTER (WHERE dexcaus <= 0)
FROM stg.usd_cad

UNION ALL

SELECT
    'stg.canada_5yearmortgage.mortgage_rate',
    COUNT(*) FILTER (WHERE mortgage_rate IS NULL),
    COUNT(*) FILTER (WHERE mortgage_rate <= 0)
FROM stg.canada_5yearmortgage

ORDER BY field_name;


-- =========================================================
-- 5B. WIDE-TABLE NULL / NON-POSITIVE CHECKS
--
-- For city tables, NULLs can be legitimate when source coverage
-- starts later for a city. Treat NULL counts as informational,
-- but investigate unexpected gaps.
-- =========================================================

-- City house price index
SELECT
    COUNT(*) FILTER (WHERE vancouver_index IS NULL) AS vancouver_nulls,
    COUNT(*) FILTER (WHERE calgary_index IS NULL) AS calgary_nulls,
    COUNT(*) FILTER (WHERE edmonton_index IS NULL) AS edmonton_nulls,
    COUNT(*) FILTER (WHERE toronto_index IS NULL) AS toronto_nulls,
    COUNT(*) FILTER (WHERE ottawa_index IS NULL) AS ottawa_nulls,
    COUNT(*) FILTER (WHERE montreal_index IS NULL) AS montreal_nulls,

    COUNT(*) FILTER (WHERE vancouver_index <= 0) AS vancouver_non_positive,
    COUNT(*) FILTER (WHERE calgary_index <= 0) AS calgary_non_positive,
    COUNT(*) FILTER (WHERE edmonton_index <= 0) AS edmonton_non_positive,
    COUNT(*) FILTER (WHERE toronto_index <= 0) AS toronto_non_positive,
    COUNT(*) FILTER (WHERE ottawa_index <= 0) AS ottawa_non_positive,
    COUNT(*) FILTER (WHERE montreal_index <= 0) AS montreal_non_positive
FROM stg.city_house_price_index;


-- City benchmark house prices
SELECT
    COUNT(*) FILTER (WHERE canada_price IS NULL) AS canada_nulls,
    COUNT(*) FILTER (WHERE vancouver_price IS NULL) AS vancouver_nulls,
    COUNT(*) FILTER (WHERE calgary_price IS NULL) AS calgary_nulls,
    COUNT(*) FILTER (WHERE edmonton_price IS NULL) AS edmonton_nulls,
    COUNT(*) FILTER (WHERE toronto_price IS NULL) AS toronto_nulls,
    COUNT(*) FILTER (WHERE ottawa_price IS NULL) AS ottawa_nulls,
    COUNT(*) FILTER (WHERE montreal_price IS NULL) AS montreal_nulls,

    COUNT(*) FILTER (WHERE canada_price <= 0) AS canada_non_positive,
    COUNT(*) FILTER (WHERE vancouver_price <= 0) AS vancouver_non_positive,
    COUNT(*) FILTER (WHERE calgary_price <= 0) AS calgary_non_positive,
    COUNT(*) FILTER (WHERE edmonton_price <= 0) AS edmonton_non_positive,
    COUNT(*) FILTER (WHERE toronto_price <= 0) AS toronto_non_positive,
    COUNT(*) FILTER (WHERE ottawa_price <= 0) AS ottawa_non_positive,
    COUNT(*) FILTER (WHERE montreal_price <= 0) AS montreal_non_positive
FROM stg.city_house_prices;


-- City indexed house prices
SELECT
    COUNT(*) FILTER (WHERE canada_price_index IS NULL) AS canada_nulls,
    COUNT(*) FILTER (WHERE vancouver_price_index IS NULL) AS vancouver_nulls,
    COUNT(*) FILTER (WHERE calgary_price_index IS NULL) AS calgary_nulls,
    COUNT(*) FILTER (WHERE edmonton_price_index IS NULL) AS edmonton_nulls,
    COUNT(*) FILTER (WHERE toronto_price_index IS NULL) AS toronto_nulls,
    COUNT(*) FILTER (WHERE ottawa_price_index IS NULL) AS ottawa_nulls,
    COUNT(*) FILTER (WHERE montreal_price_index IS NULL) AS montreal_nulls,

    COUNT(*) FILTER (WHERE canada_price_index <= 0) AS canada_non_positive,
    COUNT(*) FILTER (WHERE vancouver_price_index <= 0) AS vancouver_non_positive,
    COUNT(*) FILTER (WHERE calgary_price_index <= 0) AS calgary_non_positive,
    COUNT(*) FILTER (WHERE edmonton_price_index <= 0) AS edmonton_non_positive,
    COUNT(*) FILTER (WHERE toronto_price_index <= 0) AS toronto_non_positive,
    COUNT(*) FILTER (WHERE ottawa_price_index <= 0) AS ottawa_non_positive,
    COUNT(*) FILTER (WHERE montreal_price_index <= 0) AS montreal_non_positive
FROM stg.city_indexed_house_prices;


-- City rent
SELECT
    COUNT(*) FILTER (WHERE canada_price IS NULL) AS canada_nulls,
    COUNT(*) FILTER (WHERE vancouver_price IS NULL) AS vancouver_nulls,
    COUNT(*) FILTER (WHERE calgary_price IS NULL) AS calgary_nulls,
    COUNT(*) FILTER (WHERE edmonton_price IS NULL) AS edmonton_nulls,
    COUNT(*) FILTER (WHERE toronto_price IS NULL) AS toronto_nulls,
    COUNT(*) FILTER (WHERE ottawa_price IS NULL) AS ottawa_nulls,
    COUNT(*) FILTER (WHERE montreal_price IS NULL) AS montreal_nulls,

    COUNT(*) FILTER (WHERE canada_price <= 0) AS canada_non_positive,
    COUNT(*) FILTER (WHERE vancouver_price <= 0) AS vancouver_non_positive,
    COUNT(*) FILTER (WHERE calgary_price <= 0) AS calgary_non_positive,
    COUNT(*) FILTER (WHERE edmonton_price <= 0) AS edmonton_non_positive,
    COUNT(*) FILTER (WHERE toronto_price <= 0) AS toronto_non_positive,
    COUNT(*) FILTER (WHERE ottawa_price <= 0) AS ottawa_non_positive,
    COUNT(*) FILTER (WHERE montreal_price <= 0) AS montreal_non_positive
FROM stg.city_rent;


-- =========================================================
-- 6. WIDE-TABLE CITY COVERAGE
-- Shows first/last available observation and populated row count.
-- =========================================================

-- City benchmark prices
SELECT *
FROM (
    SELECT
        'Canada' AS market,
        MIN(date_period) FILTER (WHERE canada_price IS NOT NULL) AS first_date,
        MAX(date_period) FILTER (WHERE canada_price IS NOT NULL) AS last_date,
        COUNT(canada_price) AS populated_rows
    FROM stg.city_house_prices

    UNION ALL
    SELECT
        'Vancouver',
        MIN(date_period) FILTER (WHERE vancouver_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE vancouver_price IS NOT NULL),
        COUNT(vancouver_price)
    FROM stg.city_house_prices

    UNION ALL
    SELECT
        'Calgary',
        MIN(date_period) FILTER (WHERE calgary_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE calgary_price IS NOT NULL),
        COUNT(calgary_price)
    FROM stg.city_house_prices

    UNION ALL
    SELECT
        'Edmonton',
        MIN(date_period) FILTER (WHERE edmonton_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE edmonton_price IS NOT NULL),
        COUNT(edmonton_price)
    FROM stg.city_house_prices

    UNION ALL
    SELECT
        'Toronto',
        MIN(date_period) FILTER (WHERE toronto_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE toronto_price IS NOT NULL),
        COUNT(toronto_price)
    FROM stg.city_house_prices

    UNION ALL
    SELECT
        'Ottawa',
        MIN(date_period) FILTER (WHERE ottawa_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE ottawa_price IS NOT NULL),
        COUNT(ottawa_price)
    FROM stg.city_house_prices

    UNION ALL
    SELECT
        'Montreal',
        MIN(date_period) FILTER (WHERE montreal_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE montreal_price IS NOT NULL),
        COUNT(montreal_price)
    FROM stg.city_house_prices
) AS coverage
ORDER BY market;


-- City rent coverage
SELECT *
FROM (
    SELECT
        'Canada' AS market,
        MIN(date_period) FILTER (WHERE canada_price IS NOT NULL) AS first_date,
        MAX(date_period) FILTER (WHERE canada_price IS NOT NULL) AS last_date,
        COUNT(canada_price) AS populated_rows
    FROM stg.city_rent

    UNION ALL
    SELECT
        'Vancouver',
        MIN(date_period) FILTER (WHERE vancouver_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE vancouver_price IS NOT NULL),
        COUNT(vancouver_price)
    FROM stg.city_rent

    UNION ALL
    SELECT
        'Calgary',
        MIN(date_period) FILTER (WHERE calgary_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE calgary_price IS NOT NULL),
        COUNT(calgary_price)
    FROM stg.city_rent

    UNION ALL
    SELECT
        'Edmonton',
        MIN(date_period) FILTER (WHERE edmonton_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE edmonton_price IS NOT NULL),
        COUNT(edmonton_price)
    FROM stg.city_rent

    UNION ALL
    SELECT
        'Toronto',
        MIN(date_period) FILTER (WHERE toronto_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE toronto_price IS NOT NULL),
        COUNT(toronto_price)
    FROM stg.city_rent

    UNION ALL
    SELECT
        'Ottawa',
        MIN(date_period) FILTER (WHERE ottawa_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE ottawa_price IS NOT NULL),
        COUNT(ottawa_price)
    FROM stg.city_rent

    UNION ALL
    SELECT
        'Montreal',
        MIN(date_period) FILTER (WHERE montreal_price IS NOT NULL),
        MAX(date_period) FILTER (WHERE montreal_price IS NOT NULL),
        COUNT(montreal_price)
    FROM stg.city_rent
) AS coverage
ORDER BY market;


-- =========================================================
-- 7. MONTHLY DATE ALIGNMENT
--
-- These monthly / month-labelled tables should normally use
-- the first day of the month as date_period.
--
-- Expected:
--   non_month_start_rows = 0
-- =========================================================
SELECT
    'stg.city_house_price_index' AS table_name,
    COUNT(*) FILTER (
        WHERE date_period <> DATE_TRUNC('month', date_period)::DATE
    ) AS non_month_start_rows
FROM stg.city_house_price_index

UNION ALL

SELECT
    'stg.city_house_prices',
    COUNT(*) FILTER (
        WHERE date_period <> DATE_TRUNC('month', date_period)::DATE
    )
FROM stg.city_house_prices

UNION ALL

SELECT
    'stg.city_indexed_house_prices',
    COUNT(*) FILTER (
        WHERE date_period <> DATE_TRUNC('month', date_period)::DATE
    )
FROM stg.city_indexed_house_prices

UNION ALL

SELECT
    'stg.city_rent',
    COUNT(*) FILTER (
        WHERE date_period <> DATE_TRUNC('month', date_period)::DATE
    )
FROM stg.city_rent

ORDER BY table_name;


-- =========================================================
-- 8. DUPLICATE DETAILS
-- Run if Section 4 reports extra_duplicate_rows > 0.
-- =========================================================

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.canada_house_price_index_2010_100
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.city_house_price_index
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.city_house_prices
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.city_indexed_house_prices
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.sp500_usd
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.tsx_cad
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.vt_usd
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.city_rent
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.canada_cpi
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.usd_cad
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

SELECT date_period, COUNT(*) AS duplicate_count
FROM stg.canada_5yearmortgage
GROUP BY date_period
HAVING COUNT(*) > 1
ORDER BY date_period;

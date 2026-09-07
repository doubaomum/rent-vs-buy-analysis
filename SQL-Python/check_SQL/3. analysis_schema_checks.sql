-- =========================================================
-- ANALYSIS SCHEMA DATA QUALITY CHECKS
-- Finalized against the current analysis SQL files.
--
-- Purpose:
--   Validate derived analytical tables before simulation / Power BI.
--
-- Analysis-layer checks focus on:
--   1. Row counts and date coverage
--   2. Source -> analysis reconciliation
--   3. Natural-key integrity
--   4. Derived-value completeness
--   5. Rebase / index anchors
--   6. Transformation formula consistency
--   7. Wide -> long reconciliation
--   8. CAGR structural and formula validation
--   9. Combined comparison-table integrity
-- =========================================================


-- =========================================================
-- 1. ROW COUNTS AND DATE RANGES
-- =========================================================
SELECT 'analysis.canada_house_price_index_1990_100' AS table_name,
       COUNT(*) AS row_count,
       MIN(date_period) AS min_date,
       MAX(date_period) AS max_date
FROM analysis.canada_house_price_index_1990_100

UNION ALL
SELECT 'analysis.sp500_index_1990_100', COUNT(*), MIN(date_period), MAX(date_period)
FROM analysis.sp500_index_1990_100

UNION ALL
SELECT 'analysis.tsx_index_1990_100', COUNT(*), MIN(date_period), MAX(date_period)
FROM analysis.tsx_index_1990_100

UNION ALL
SELECT 'analysis.vt_cad_real', COUNT(*), MIN(date_period), MAX(date_period)
FROM analysis.vt_cad_real

UNION ALL
SELECT 'analysis.city_indexed_house_prices', COUNT(*), MIN(date_period), MAX(date_period)
FROM analysis.city_indexed_house_prices

UNION ALL
SELECT 'analysis.city_house_prices_long', COUNT(*), MIN(date_period), MAX(date_period)
FROM analysis.city_house_prices_long

UNION ALL
SELECT 'analysis.city_rent_long', COUNT(*), MIN(date_period), MAX(date_period)
FROM analysis.city_rent_long

UNION ALL
SELECT 'analysis.canada_house_cagr', COUNT(*), MIN(start_date), MAX(end_date)
FROM analysis.canada_house_cagr

UNION ALL
SELECT 'analysis.sp500_cagr', COUNT(*), MIN(start_date), MAX(end_date)
FROM analysis.sp500_cagr

UNION ALL
SELECT 'analysis.tsx_cagr', COUNT(*), MIN(start_date), MAX(end_date)
FROM analysis.tsx_cagr

UNION ALL
SELECT 'analysis.vt_cagr', COUNT(*), MIN(start_date), MAX(end_date)
FROM analysis.vt_cagr

UNION ALL
SELECT 'analysis.city_house_cagr', COUNT(*), MIN(start_date), MAX(end_date)
FROM analysis.city_house_cagr

UNION ALL
SELECT 'analysis.sum_canada_stock_cagr', COUNT(*), MIN(start_date), MAX(end_date)
FROM analysis.sum_canada_stock_cagr

ORDER BY table_name;


-- =========================================================
-- 2. SOURCE -> ANALYSIS ROW-COUNT RECONCILIATION
--
-- Expected row_difference = 0 for the direct one-row-per-date
-- analysis tables.
-- =========================================================
WITH reconciliation AS (
    SELECT
        'canada_house_price_index_1990_100' AS dataset,
        (SELECT COUNT(*) FROM stg.canada_house_price_index_2010_100) AS expected_rows,
        (SELECT COUNT(*) FROM analysis.canada_house_price_index_1990_100) AS actual_rows

    UNION ALL
    SELECT
        'sp500_index_1990_100',
        (SELECT COUNT(*) FROM stg.sp500_usd),
        (SELECT COUNT(*) FROM analysis.sp500_index_1990_100)

    UNION ALL
    SELECT
        'tsx_index_1990_100',
        (SELECT COUNT(*) FROM stg.tsx_cad),
        (SELECT COUNT(*) FROM analysis.tsx_index_1990_100)

    UNION ALL
    SELECT
        'vt_cad_real',
        (SELECT COUNT(*) FROM stg.vt_usd),
        (SELECT COUNT(*) FROM analysis.vt_cad_real)

    UNION ALL
    SELECT
        'city_indexed_house_prices',
        (SELECT COUNT(*) FROM stg.city_indexed_house_prices),
        (SELECT COUNT(*) FROM analysis.city_indexed_house_prices)
)
SELECT
    dataset,
    expected_rows,
    actual_rows,
    actual_rows - expected_rows AS row_difference
FROM reconciliation
ORDER BY dataset;


-- =========================================================
-- 3A. NULL / DUPLICATE NATURAL KEYS - TIME-SERIES TABLES
--
-- Expected:
--   null_key_rows   = 0
--   duplicate_groups = 0
-- =========================================================
WITH key_checks AS (
    SELECT
        'analysis.canada_house_price_index_1990_100' AS table_name,
        COUNT(*) FILTER (WHERE date_period IS NULL) AS null_key_rows,
        (
            SELECT COUNT(*)
            FROM (
                SELECT date_period
                FROM analysis.canada_house_price_index_1990_100
                GROUP BY date_period
                HAVING COUNT(*) > 1
            ) d
        ) AS duplicate_groups
    FROM analysis.canada_house_price_index_1990_100

    UNION ALL
    SELECT
        'analysis.sp500_index_1990_100',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        (
            SELECT COUNT(*) FROM (
                SELECT date_period FROM analysis.sp500_index_1990_100
                GROUP BY date_period HAVING COUNT(*) > 1
            ) d
        )
    FROM analysis.sp500_index_1990_100

    UNION ALL
    SELECT
        'analysis.tsx_index_1990_100',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        (
            SELECT COUNT(*) FROM (
                SELECT date_period FROM analysis.tsx_index_1990_100
                GROUP BY date_period HAVING COUNT(*) > 1
            ) d
        )
    FROM analysis.tsx_index_1990_100

    UNION ALL
    SELECT
        'analysis.vt_cad_real',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        (
            SELECT COUNT(*) FROM (
                SELECT date_period FROM analysis.vt_cad_real
                GROUP BY date_period HAVING COUNT(*) > 1
            ) d
        )
    FROM analysis.vt_cad_real

    UNION ALL
    SELECT
        'analysis.city_indexed_house_prices',
        COUNT(*) FILTER (WHERE date_period IS NULL),
        (
            SELECT COUNT(*) FROM (
                SELECT date_period FROM analysis.city_indexed_house_prices
                GROUP BY date_period HAVING COUNT(*) > 1
            ) d
        )
    FROM analysis.city_indexed_house_prices
)
SELECT *
FROM key_checks
ORDER BY table_name;


-- =========================================================
-- 3B. NULL / DUPLICATE NATURAL KEYS - LONG TABLES
-- Natural key = (date_period, city)
-- =========================================================
SELECT
    'analysis.city_house_prices_long' AS table_name,
    COUNT(*) FILTER (
        WHERE date_period IS NULL OR city IS NULL OR BTRIM(city) = ''
    ) AS null_key_rows,
    (
        SELECT COUNT(*)
        FROM (
            SELECT date_period, city
            FROM analysis.city_house_prices_long
            GROUP BY date_period, city
            HAVING COUNT(*) > 1
        ) d
    ) AS duplicate_groups
FROM analysis.city_house_prices_long

UNION ALL

SELECT
    'analysis.city_rent_long',
    COUNT(*) FILTER (
        WHERE date_period IS NULL OR city IS NULL OR BTRIM(city) = ''
    ),
    (
        SELECT COUNT(*)
        FROM (
            SELECT date_period, city
            FROM analysis.city_rent_long
            GROUP BY date_period, city
            HAVING COUNT(*) > 1
        ) d
    )
FROM analysis.city_rent_long;


-- =========================================================
-- 3C. NULL / DUPLICATE NATURAL KEYS - CAGR TABLES
-- Natural key = (start_date, holding_years)
-- =========================================================
WITH cagr_keys AS (
    SELECT 'analysis.canada_house_cagr' AS table_name,
           COUNT(*) FILTER (WHERE start_date IS NULL OR holding_years IS NULL) AS null_key_rows,
           (
               SELECT COUNT(*) FROM (
                   SELECT start_date, holding_years
                   FROM analysis.canada_house_cagr
                   GROUP BY start_date, holding_years
                   HAVING COUNT(*) > 1
               ) d
           ) AS duplicate_groups
    FROM analysis.canada_house_cagr

    UNION ALL
    SELECT 'analysis.sp500_cagr',
           COUNT(*) FILTER (WHERE start_date IS NULL OR holding_years IS NULL),
           (
               SELECT COUNT(*) FROM (
                   SELECT start_date, holding_years
                   FROM analysis.sp500_cagr
                   GROUP BY start_date, holding_years
                   HAVING COUNT(*) > 1
               ) d
           )
    FROM analysis.sp500_cagr

    UNION ALL
    SELECT 'analysis.tsx_cagr',
           COUNT(*) FILTER (WHERE start_date IS NULL OR holding_years IS NULL),
           (
               SELECT COUNT(*) FROM (
                   SELECT start_date, holding_years
                   FROM analysis.tsx_cagr
                   GROUP BY start_date, holding_years
                   HAVING COUNT(*) > 1
               ) d
           )
    FROM analysis.tsx_cagr

    UNION ALL
    SELECT 'analysis.vt_cagr',
           COUNT(*) FILTER (WHERE start_date IS NULL OR holding_years IS NULL),
           (
               SELECT COUNT(*) FROM (
                   SELECT start_date, holding_years
                   FROM analysis.vt_cagr
                   GROUP BY start_date, holding_years
                   HAVING COUNT(*) > 1
               ) d
           )
    FROM analysis.vt_cagr

    UNION ALL
    SELECT 'analysis.city_house_cagr',
           COUNT(*) FILTER (WHERE start_date IS NULL OR holding_years IS NULL),
           (
               SELECT COUNT(*) FROM (
                   SELECT start_date, holding_years
                   FROM analysis.city_house_cagr
                   GROUP BY start_date, holding_years
                   HAVING COUNT(*) > 1
               ) d
           )
    FROM analysis.city_house_cagr
)
SELECT *
FROM cagr_keys
ORDER BY table_name;


-- =========================================================
-- 4. CORE DERIVED-VALUE COMPLETENESS
--
-- Expected NULL counts are generally 0. A nonzero count means
-- an FX/CPI join or rebase anchor may be missing.
-- =========================================================
SELECT
    'analysis.canada_house_price_index_1990_100' AS table_name,
    COUNT(*) FILTER (WHERE price_index_original IS NULL) AS source_value_nulls,
    COUNT(*) FILTER (WHERE price_index_1990_100 IS NULL) AS derived_value_nulls
FROM analysis.canada_house_price_index_1990_100

UNION ALL
SELECT
    'analysis.sp500_index_1990_100',
    COUNT(*) FILTER (WHERE price_usd IS NULL),
    COUNT(*) FILTER (
        WHERE price_cad IS NULL
           OR price_cad_real IS NULL
           OR price_index_cad_real IS NULL
    )
FROM analysis.sp500_index_1990_100

UNION ALL
SELECT
    'analysis.tsx_index_1990_100',
    COUNT(*) FILTER (WHERE price_cad IS NULL),
    COUNT(*) FILTER (
        WHERE price_cad_real IS NULL
           OR price_index_cad_real IS NULL
    )
FROM analysis.tsx_index_1990_100

UNION ALL
SELECT
    'analysis.vt_cad_real',
    COUNT(*) FILTER (WHERE price_usd IS NULL),
    COUNT(*) FILTER (
        WHERE price_cad IS NULL
           OR price_cad_real IS NULL
    )
FROM analysis.vt_cad_real

ORDER BY table_name;


-- =========================================================
-- 5. REBASE / INDEX ANCHOR CHECKS
--
-- Expected rebased index = 100 at the chosen base observation.
-- =========================================================

-- Canada: your transform chooses the first non-NULL 1990 source
-- observation, but shifts its output date by +1 day.
WITH base AS (
    SELECT date_period, price_index
    FROM stg.canada_house_price_index_2010_100
    WHERE EXTRACT(YEAR FROM date_period) = 1990
      AND price_index IS NOT NULL
    ORDER BY date_period
    LIMIT 1
)
SELECT
    base.date_period AS source_base_date,
    (base.date_period + INTERVAL '1 day')::DATE AS analysis_base_date,
    a.price_index_1990_100 AS rebased_value,
    ABS(a.price_index_1990_100 - 100) AS distance_from_100
FROM base
LEFT JOIN analysis.canada_house_price_index_1990_100 AS a
    ON a.date_period = (base.date_period + INTERVAL '1 day')::DATE;


-- S&P 500: 1990-01-01 = 100
SELECT
    'S&P 500' AS asset,
    date_period,
    price_index_cad_real AS rebased_value,
    ABS(price_index_cad_real - 100) AS distance_from_100
FROM analysis.sp500_index_1990_100
WHERE date_period = DATE '1990-01-01';


-- TSX: 1990-01-01 = 100
SELECT
    'TSX' AS asset,
    date_period,
    price_index_cad_real AS rebased_value,
    ABS(price_index_cad_real - 100) AS distance_from_100
FROM analysis.tsx_index_1990_100
WHERE date_period = DATE '1990-01-01';


-- City / stock comparison indices: 2005-01-01 = 100
SELECT
    date_period,
    canada_price_index_real_2005_100,
    vancouver_price_index_real_2005_100,
    calgary_price_index_real_2005_100,
    edmonton_price_index_real_2005_100,
    toronto_price_index_real_2005_100,
    ottawa_price_index_real_2005_100,
    montreal_price_index_real_2005_100,
    sp500_price_index_real_2005_100,
    tsx_price_index_real_2005_100
FROM analysis.city_indexed_house_prices
WHERE date_period = DATE '2005-01-01';


-- =========================================================
-- 6. TRANSFORMATION FORMULA CONSISTENCY
-- Tolerance is used to avoid flagging tiny numeric differences.
-- Expected mismatch_rows = 0.
-- =========================================================

-- 6A. S&P 500 USD -> CAD using latest available FX on or before date
SELECT
    COUNT(*) AS mismatch_rows
FROM analysis.sp500_index_1990_100 AS a
LEFT JOIN LATERAL (
    SELECT fx.dexcaus
    FROM stg.usd_cad AS fx
    WHERE fx.date_period <= a.date_period
      AND fx.dexcaus IS NOT NULL
    ORDER BY fx.date_period DESC
    LIMIT 1
) fx ON TRUE
WHERE a.price_usd IS NOT NULL
  AND fx.dexcaus IS NOT NULL
  AND ABS(a.price_cad - (a.price_usd * fx.dexcaus)) > 0.000001;


-- 6B. S&P 500 nominal CAD -> real CAD
SELECT
    COUNT(*) AS mismatch_rows
FROM analysis.sp500_index_1990_100 AS a
JOIN stg.canada_cpi AS cpi
    ON cpi.date_period = a.date_period
WHERE a.price_cad IS NOT NULL
  AND cpi.cpi_value IS NOT NULL
  AND cpi.cpi_value <> 0
  AND ABS(a.price_cad_real - (a.price_cad / cpi.cpi_value * 100)) > 0.000001;


-- 6C. TSX nominal CAD -> real CAD
SELECT
    COUNT(*) AS mismatch_rows
FROM analysis.tsx_index_1990_100 AS a
JOIN stg.canada_cpi AS cpi
    ON cpi.date_period = a.date_period
WHERE a.price_cad IS NOT NULL
  AND cpi.cpi_value IS NOT NULL
  AND cpi.cpi_value <> 0
  AND ABS(a.price_cad_real - (a.price_cad / cpi.cpi_value * 100)) > 0.000001;


-- 6D. VT USD -> CAD using latest available FX on or before date
SELECT
    COUNT(*) AS mismatch_rows
FROM analysis.vt_cad_real AS a
LEFT JOIN LATERAL (
    SELECT fx.dexcaus
    FROM stg.usd_cad AS fx
    WHERE fx.date_period <= a.date_period
      AND fx.dexcaus IS NOT NULL
    ORDER BY fx.date_period DESC
    LIMIT 1
) fx ON TRUE
WHERE a.price_usd IS NOT NULL
  AND fx.dexcaus IS NOT NULL
  AND ABS(a.price_cad - (a.price_usd * fx.dexcaus)) > 0.000001;


-- 6E. VT nominal CAD -> real CAD
SELECT
    COUNT(*) AS mismatch_rows
FROM analysis.vt_cad_real AS a
JOIN stg.canada_cpi AS cpi
    ON cpi.date_period = a.date_period
WHERE a.price_cad IS NOT NULL
  AND cpi.cpi_value IS NOT NULL
  AND cpi.cpi_value <> 0
  AND ABS(a.price_cad_real - (a.price_cad / cpi.cpi_value * 100)) > 0.000001;


-- =========================================================
-- 7. WIDE -> LONG RECONCILIATION
-- =========================================================

-- 7A. House-price long table expected row count
WITH expected AS (
    SELECT SUM(
        (canada_price IS NOT NULL)::INT
      + (vancouver_price IS NOT NULL)::INT
      + (calgary_price IS NOT NULL)::INT
      + (edmonton_price IS NOT NULL)::INT
      + (toronto_price IS NOT NULL)::INT
      + (ottawa_price IS NOT NULL)::INT
      + (montreal_price IS NOT NULL)::INT
    ) AS expected_rows
    FROM stg.city_house_prices
), actual AS (
    SELECT COUNT(*) AS actual_rows
    FROM analysis.city_house_prices_long
)
SELECT
    expected_rows,
    actual_rows,
    actual_rows - expected_rows AS row_difference
FROM expected CROSS JOIN actual;


-- 7B. Rent long table expected row count
WITH expected AS (
    SELECT SUM(
        (canada_price IS NOT NULL)::INT
      + (vancouver_price IS NOT NULL)::INT
      + (calgary_price IS NOT NULL)::INT
      + (edmonton_price IS NOT NULL)::INT
      + (toronto_price IS NOT NULL)::INT
      + (ottawa_price IS NOT NULL)::INT
      + (montreal_price IS NOT NULL)::INT
    ) AS expected_rows
    FROM stg.city_rent
), actual AS (
    SELECT COUNT(*) AS actual_rows
    FROM analysis.city_rent_long
)
SELECT
    expected_rows,
    actual_rows,
    actual_rows - expected_rows AS row_difference
FROM expected CROSS JOIN actual;


-- 7C. Expected city list
SELECT DISTINCT city
FROM analysis.city_house_prices_long
ORDER BY city;

SELECT DISTINCT city
FROM analysis.city_rent_long
ORDER BY city;


-- =========================================================
-- 8. CAGR STRUCTURAL CHECKS
--
-- Expected bad_rows = 0.
-- =========================================================

-- Canada house CAGR
SELECT
    COUNT(*) AS bad_rows
FROM analysis.canada_house_cagr
WHERE holding_years NOT IN (5, 10, 15, 20, 25, 30, 35)
   OR end_date <> (start_date + MAKE_INTERVAL(years => holding_years))::DATE
   OR end_year <> start_year + holding_years
   OR start_price IS NULL
   OR end_price IS NULL
   OR cagr IS NULL;


-- S&P 500 CAGR
SELECT
    COUNT(*) AS bad_rows
FROM analysis.sp500_cagr
WHERE holding_years NOT IN (5, 10, 15, 20, 25, 30, 35)
   OR EXTRACT(MONTH FROM start_date) <> 1
   OR end_date <> (start_date + MAKE_INTERVAL(years => holding_years))::DATE
   OR end_year <> start_year + holding_years
   OR start_price IS NULL
   OR end_price IS NULL
   OR cagr IS NULL;


-- TSX CAGR
SELECT
    COUNT(*) AS bad_rows
FROM analysis.tsx_cagr
WHERE holding_years NOT IN (5, 10, 15, 20, 25, 30, 35)
   OR EXTRACT(MONTH FROM start_date) <> 1
   OR end_date <> (start_date + MAKE_INTERVAL(years => holding_years))::DATE
   OR end_year <> start_year + holding_years
   OR start_price IS NULL
   OR end_price IS NULL
   OR cagr IS NULL;


-- VT CAGR
SELECT
    COUNT(*) AS bad_rows
FROM analysis.vt_cagr
WHERE holding_years NOT IN (5, 10, 15, 18)
   OR EXTRACT(MONTH FROM start_date) <> 1
   OR end_date <> (start_date + MAKE_INTERVAL(years => holding_years))::DATE
   OR end_year <> start_year + holding_years
   OR start_price IS NULL
   OR end_price IS NULL
   OR cagr IS NULL;


-- City house CAGR
-- NULL city values may legitimately reflect unavailable source coverage,
-- so this checks the common structural fields only.
SELECT
    COUNT(*) AS bad_rows
FROM analysis.city_house_cagr
WHERE holding_years NOT IN (5, 10, 15, 20)
   OR EXTRACT(MONTH FROM start_date) <> 1
   OR end_date <> (start_date + MAKE_INTERVAL(years => holding_years))::DATE
   OR end_year <> start_year + holding_years;


-- =========================================================
-- 9. CAGR FORMULA RE-CALCULATION
-- Expected mismatch_rows = 0.
-- =========================================================
SELECT
    'canada_house_cagr' AS table_name,
    COUNT(*) AS mismatch_rows
FROM analysis.canada_house_cagr
WHERE start_price <> 0
  AND ABS(
      cagr
      - (POWER(end_price / start_price, 1.0 / holding_years) - 1)
  ) > 0.00000001

UNION ALL

SELECT
    'sp500_cagr',
    COUNT(*)
FROM analysis.sp500_cagr
WHERE start_price <> 0
  AND ABS(
      cagr
      - (POWER(end_price / start_price, 1.0 / holding_years) - 1)
  ) > 0.00000001

UNION ALL

SELECT
    'tsx_cagr',
    COUNT(*)
FROM analysis.tsx_cagr
WHERE start_price <> 0
  AND ABS(
      cagr
      - (POWER(end_price / start_price, 1.0 / holding_years) - 1)
  ) > 0.00000001

UNION ALL

SELECT
    'vt_cagr',
    COUNT(*)
FROM analysis.vt_cagr
WHERE start_price <> 0
  AND ABS(
      cagr
      - (POWER(end_price / start_price, 1.0 / holding_years) - 1)
  ) > 0.00000001

ORDER BY table_name;


-- City CAGR formula checks, one market at a time.
SELECT
    market,
    COUNT(*) AS mismatch_rows
FROM analysis.city_house_cagr AS c
CROSS JOIN LATERAL (
    VALUES
        ('Canada', c.canada_start_price, c.canada_end_price, c.canada_cagr),
        ('Vancouver', c.vancouver_start_price, c.vancouver_end_price, c.vancouver_cagr),
        ('Calgary', c.calgary_start_price, c.calgary_end_price, c.calgary_cagr),
        ('Edmonton', c.edmonton_start_price, c.edmonton_end_price, c.edmonton_cagr),
        ('Toronto', c.toronto_start_price, c.toronto_end_price, c.toronto_cagr),
        ('Ottawa', c.ottawa_start_price, c.ottawa_end_price, c.ottawa_cagr),
        ('Montreal', c.montreal_start_price, c.montreal_end_price, c.montreal_cagr)
) AS x(market, start_price, end_price, cagr)
WHERE start_price IS NOT NULL
  AND end_price IS NOT NULL
  AND cagr IS NOT NULL
  AND start_price <> 0
  AND ABS(
      cagr
      - (POWER(end_price / start_price, 1.0 / c.holding_years) - 1)
  ) > 0.00000001
GROUP BY market
ORDER BY market;


-- =========================================================
-- 10. CAGR EXPECTED-ROW RECONCILIATION
-- Recompute how many valid source start/end pairs exist.
-- Expected row_difference = 0.
-- =========================================================
WITH expected_canada AS (
    SELECT COUNT(*) AS n
    FROM stg.canada_house_price_index_2010_100 AS s
    CROSS JOIN (VALUES (5),(10),(15),(20),(25),(30),(35)) h(holding_years)
    JOIN stg.canada_house_price_index_2010_100 AS e
      ON e.date_period = (s.date_period + MAKE_INTERVAL(years => h.holding_years))::DATE
    WHERE EXTRACT(QUARTER FROM s.date_period) = 1
),
expected_sp500 AS (
    SELECT COUNT(*) AS n
    FROM analysis.sp500_index_1990_100 AS s
    CROSS JOIN (VALUES (5),(10),(15),(20),(25),(30),(35)) h(holding_years)
    JOIN analysis.sp500_index_1990_100 AS e
      ON e.date_period = (s.date_period + MAKE_INTERVAL(years => h.holding_years))::DATE
    WHERE EXTRACT(MONTH FROM s.date_period) = 1
      AND s.price_index_cad_real IS NOT NULL
      AND e.price_index_cad_real IS NOT NULL
),
expected_tsx AS (
    SELECT COUNT(*) AS n
    FROM analysis.tsx_index_1990_100 AS s
    CROSS JOIN (VALUES (5),(10),(15),(20),(25),(30),(35)) h(holding_years)
    JOIN analysis.tsx_index_1990_100 AS e
      ON e.date_period = (s.date_period + MAKE_INTERVAL(years => h.holding_years))::DATE
    WHERE EXTRACT(MONTH FROM s.date_period) = 1
      AND s.price_index_cad_real IS NOT NULL
      AND e.price_index_cad_real IS NOT NULL
),
expected_vt AS (
    SELECT COUNT(*) AS n
    FROM analysis.vt_cad_real AS s
    CROSS JOIN (VALUES (5),(10),(15),(18)) h(holding_years)
    JOIN analysis.vt_cad_real AS e
      ON e.date_period = (s.date_period + MAKE_INTERVAL(years => h.holding_years))::DATE
    WHERE EXTRACT(MONTH FROM s.date_period) = 1
      AND s.price_cad_real IS NOT NULL
      AND e.price_cad_real IS NOT NULL
),
expected_city AS (
    SELECT COUNT(*) AS n
    FROM analysis.city_indexed_house_prices AS s
    CROSS JOIN (VALUES (5),(10),(15),(20)) h(holding_years)
    JOIN analysis.city_indexed_house_prices AS e
      ON e.date_period = (s.date_period + MAKE_INTERVAL(years => h.holding_years))::DATE
    WHERE EXTRACT(MONTH FROM s.date_period) = 1
)
SELECT 'canada_house_cagr' AS table_name,
       expected_canada.n AS expected_rows,
       (SELECT COUNT(*) FROM analysis.canada_house_cagr) AS actual_rows,
       (SELECT COUNT(*) FROM analysis.canada_house_cagr) - expected_canada.n AS row_difference
FROM expected_canada

UNION ALL
SELECT 'sp500_cagr', expected_sp500.n,
       (SELECT COUNT(*) FROM analysis.sp500_cagr),
       (SELECT COUNT(*) FROM analysis.sp500_cagr) - expected_sp500.n
FROM expected_sp500

UNION ALL
SELECT 'tsx_cagr', expected_tsx.n,
       (SELECT COUNT(*) FROM analysis.tsx_cagr),
       (SELECT COUNT(*) FROM analysis.tsx_cagr) - expected_tsx.n
FROM expected_tsx

UNION ALL
SELECT 'vt_cagr', expected_vt.n,
       (SELECT COUNT(*) FROM analysis.vt_cagr),
       (SELECT COUNT(*) FROM analysis.vt_cagr) - expected_vt.n
FROM expected_vt

UNION ALL
SELECT 'city_house_cagr', expected_city.n,
       (SELECT COUNT(*) FROM analysis.city_house_cagr),
       (SELECT COUNT(*) FROM analysis.city_house_cagr) - expected_city.n
FROM expected_city

ORDER BY table_name;


-- =========================================================
-- 11. COMBINED CAGR TABLE CHECK
--
-- IMPORTANT:
-- The transform SQL must create analysis.city_house_cagr BEFORE
-- analysis.sum_canada_stock_cagr. In the current file, the order is
-- reversed and should be corrected before a clean rebuild.
-- =========================================================
SELECT
    COUNT(*) AS row_count,
    COUNT(*) FILTER (WHERE start_date IS NULL OR holding_years IS NULL) AS null_key_rows,
    (
        SELECT COUNT(*)
        FROM (
            SELECT start_date, holding_years
            FROM analysis.sum_canada_stock_cagr
            GROUP BY start_date, holding_years
            HAVING COUNT(*) > 1
        ) d
    ) AS duplicate_groups
FROM analysis.sum_canada_stock_cagr;


-- Since canada_house_cagr is the LEFT-side driver of the combined table,
-- expected row count should equal canada_house_cagr.
SELECT
    (SELECT COUNT(*) FROM analysis.canada_house_cagr) AS expected_rows,
    (SELECT COUNT(*) FROM analysis.sum_canada_stock_cagr) AS actual_rows,
    (SELECT COUNT(*) FROM analysis.sum_canada_stock_cagr)
      - (SELECT COUNT(*) FROM analysis.canada_house_cagr) AS row_difference;


-- =========================================================
-- 12. DIAGNOSTIC: CANADA HOUSE DATE SHIFT
--
-- The current transform inserts:
--     date_period + INTERVAL '1 day'
-- This makes analysis dates differ from staging dates by one day.
-- If this was not intentional, remove the +1 day in the transform.
-- =========================================================
SELECT
    COUNT(*) AS analysis_rows,
    COUNT(*) FILTER (
        WHERE s.date_period IS NOT NULL
    ) AS rows_matching_staging_plus_one_day,
    COUNT(*) FILTER (
        WHERE s.date_period IS NULL
    ) AS rows_not_matching_staging_plus_one_day
FROM analysis.canada_house_price_index_1990_100 AS a
LEFT JOIN stg.canada_house_price_index_2010_100 AS s
    ON a.date_period = (s.date_period + INTERVAL '1 day')::DATE;

-- 1. Row counts and date ranges
SELECT
    'canada_house_price_index_1990_100' AS table_name,
    COUNT(*) AS row_count,
    MIN(date_period) AS min_date,
    MAX(date_period) AS max_date
FROM analysis.canada_house_price_index_1990_100

UNION ALL

SELECT
    'sp500_index_1990_100',
    COUNT(*),
    MIN(date_period),
    MAX(date_period)
FROM analysis.sp500_index_1990_100

UNION ALL

SELECT
    'tsx_index_1990_100',
    COUNT(*),
    MIN(date_period),
    MAX(date_period)
FROM analysis.tsx_index_1990_100

UNION ALL

SELECT
    'vt_cad_real',
    COUNT(*),
    MIN(date_period),
    MAX(date_period)
FROM analysis.vt_cad_real;

-- =========================================================
-- Duplicate Date Checks
-- =========================================================

-- 2. Check duplicate dates
SELECT date_period, COUNT(*)
FROM analysis.canada_house_price_index_1990_100
GROUP BY date_period
HAVING COUNT(*) > 1;


SELECT date_period, COUNT(*)
FROM analysis.sp500_index_1990_100
GROUP BY date_period
HAVING COUNT(*) > 1;

SELECT date_period, COUNT(*)
FROM analysis.tsx_index_1990_100
GROUP BY date_period
HAVING COUNT(*) > 1;

SELECT date_period, COUNT(*)
FROM analysis.vt_cad_real
GROUP BY date_period
HAVING COUNT(*) > 1;

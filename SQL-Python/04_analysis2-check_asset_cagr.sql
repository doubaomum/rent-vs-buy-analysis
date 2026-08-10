-- =========================================================
-- 1. Check row counts
-- =========================================================

SELECT 'canada_house_cagr' AS table_name, COUNT(*) AS row_count
FROM analysis.canada_house_cagr

UNION ALL

SELECT 'sp500_cagr', COUNT(*)
FROM analysis.sp500_cagr

UNION ALL

SELECT 'tsx_cagr', COUNT(*)
FROM analysis.tsx_cagr

UNION ALL

SELECT 'vt_cagr', COUNT(*)
FROM analysis.vt_cagr;
--1. Check all raw table row counts
SELECT 'canada_house_price_index_2010_100' AS table_name, COUNT(*) FROM raw.canada_house_price_index_2010_100
UNION ALL
SELECT 'city_house_price_index', COUNT(*) FROM raw.city_house_price_index
UNION ALL
SELECT 'city_house_real_prices', COUNT(*) FROM raw.city_house_real_prices
UNION ALL
SELECT 'sp500_raw', COUNT(*) FROM raw.sp500_raw
UNION ALL
SELECT 'tsx_raw', COUNT(*) FROM raw.tsx_raw
UNION ALL
SELECT 'vt_raw', COUNT(*) FROM raw.vt_raw
UNION ALL
SELECT 'city_rent_raw', COUNT(*) FROM raw.city_rent_raw
UNION ALL
SELECT 'canada_cpi_raw', COUNT(*) FROM raw.canada_cpi_raw
UNION ALL
SELECT 'usd_cad_raw', COUNT(*) FROM raw.usd_cad_raw
UNION ALL
SELECT 'canada_5yearmortgage_raw', COUNT(*) FROM raw.canada_5yearmortgage_raw;

--2. Check cities
SELECT city, COUNT(*) AS row_count
FROM raw.city_house_real_prices
GROUP BY city
ORDER BY city;

SELECT city, COUNT(*) AS row_count
FROM raw.city_rent_raw
GROUP BY city
ORDER BY city;

--3.check duplicate rows
SELECT city, month_date, COUNT(*) AS duplicate_count
FROM raw.city_house_real_prices
GROUP BY city, month_date
HAVING COUNT(*) > 1;

SELECT city, rent_period, COUNT(*) AS duplicate_count
FROM raw.city_rent_raw
GROUP BY city, rent_period
HAVING COUNT(*) > 1;
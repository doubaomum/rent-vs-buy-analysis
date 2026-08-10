--upload canada real index  price data
TRUNCATE raw.canada_house_price_index_2010_100;
TRUNCATE raw.city_house_price_index;
TRUNCATE raw.city_house_real_prices;
TRUNCATE raw.sp500_raw;
TRUNCATE raw.tsx_raw;
TRUNCATE raw.vt_raw;
TRUNCATE raw.city_rent_raw;
TRUNCATE raw.canada_cpi_raw;
TRUNCATE raw.usd_cad_raw;
TRUNCATE raw.canada_5yearmortgage_raw;

\copy raw.canada_house_price_index_2010_100(dataflow_id, series_key, freq, ref_area, value_type, unit_measure, unit_name, unit_multiplier, time_period, obs_conf, obs_pre_break, obs_status, obs_value) FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/canada_house_price_index_2010_100.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

--upload city level housing index  price data

\copy raw.city_house_price_index FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/city_house_price_index.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

DELETE FROM raw.city_house_price_index
WHERE transaction_date IS NULL
  AND c11_index = 'Index';

-- =========================================================
-- Upload city-level housing price data
-- Each CSV contains:
-- 6 HPI columns + 6 benchmark-price columns
-- =========================================================


-- =========================================================
-- Calgary
-- =========================================================
TRUNCATE TABLE raw.tmp_house_price;

\copy raw.tmp_house_price FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/city_real_price/calgary.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_house_real_prices (
    city,
    month_date,
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
)
SELECT
    'Calgary',
    TO_DATE(month_date, 'Mon YYYY'),
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
FROM raw.tmp_house_price;


-- =========================================================
-- Canada
-- =========================================================
TRUNCATE TABLE raw.tmp_house_price;

\copy raw.tmp_house_price FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/city_real_price/canada.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_house_real_prices (
    city,
    month_date,
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
)
SELECT
    'Canada',
    TO_DATE(month_date, 'Mon YYYY'),
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
FROM raw.tmp_house_price;


-- =========================================================
-- Edmonton
-- =========================================================
TRUNCATE TABLE raw.tmp_house_price;

\copy raw.tmp_house_price FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/city_real_price/edmonton.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_house_real_prices (
    city,
    month_date,
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
)
SELECT
    'Edmonton',
    TO_DATE(month_date, 'Mon YYYY'),
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
FROM raw.tmp_house_price;


-- =========================================================
-- Montreal
-- =========================================================
TRUNCATE TABLE raw.tmp_house_price;

\copy raw.tmp_house_price FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/city_real_price/montreal.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_house_real_prices (
    city,
    month_date,
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
)
SELECT
    'Montreal',
    TO_DATE(month_date, 'Mon YYYY'),
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
FROM raw.tmp_house_price;


-- =========================================================
-- Ottawa
-- =========================================================
TRUNCATE TABLE raw.tmp_house_price;

\copy raw.tmp_house_price FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/city_real_price/ottawa.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_house_real_prices (
    city,
    month_date,
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
)
SELECT
    'Ottawa',
    TO_DATE(month_date, 'Mon YYYY'),
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
FROM raw.tmp_house_price;


-- =========================================================
-- Toronto
-- =========================================================
TRUNCATE TABLE raw.tmp_house_price;

\copy raw.tmp_house_price FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/city_real_price/toronto.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_house_real_prices (
    city,
    month_date,
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
)
SELECT
    'Toronto',
    TO_DATE(month_date, 'Mon YYYY'),
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
FROM raw.tmp_house_price;


-- =========================================================
-- Vancouver
-- =========================================================
TRUNCATE TABLE raw.tmp_house_price;

\copy raw.tmp_house_price FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/house/city_real_price/vancouver.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_house_real_prices (
    city,
    month_date,
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
)
SELECT
    'Vancouver',
    TO_DATE(month_date, 'Mon YYYY'),
    composite_hpi_sa,
    single_family_hpi_sa,
    one_storey_hpi_sa,
    two_storey_hpi_sa,
    townhouse_hpi_sa,
    apartment_hpi_sa,
    composite_benchmark_sa,
    single_family_benchmark_sa,
    one_storey_benchmark_sa,
    two_storey_benchmark_sa,
    townhouse_benchmark_sa,
    apartment_benchmark_sa
FROM raw.tmp_house_price;


--upload stock price data

\copy raw.sp500_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/stock/sp500_raw.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'LATIN1');

\copy raw.tsx_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/stock/tsx_raw.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');

\copy raw.vt_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/stock/vt_raw.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');

--upload city level market rent data

TRUNCATE raw.tmp_rent_raw;

\copy raw.tmp_rent_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/rent/calgary_rent.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_rent_raw
SELECT
    'Calgary',
    rent_period,
    studio_rent,
    studio_flag,
    one_bedroom_rent,
    one_bedroom_flag,
    two_bedroom_rent,
    two_bedroom_flag,
    three_bedroom_plus_rent,
    three_bedroom_plus_flag,
    total_rent,
    total_flag
FROM raw.tmp_rent_raw;

TRUNCATE raw.tmp_rent_raw;

\copy raw.tmp_rent_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/rent/canada_rent.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_rent_raw
SELECT
    'Canada',
    rent_period,
    studio_rent,
    studio_flag,
    one_bedroom_rent,
    one_bedroom_flag,
    two_bedroom_rent,
    two_bedroom_flag,
    three_bedroom_plus_rent,
    three_bedroom_plus_flag,
    total_rent,
    total_flag
FROM raw.tmp_rent_raw;
TRUNCATE raw.tmp_rent_raw;
\copy raw.tmp_rent_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/rent/edmonton_rent.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_rent_raw
SELECT
    'Edmonton',
    rent_period,
    studio_rent,
    studio_flag,
    one_bedroom_rent,
    one_bedroom_flag,
    two_bedroom_rent,
    two_bedroom_flag,
    three_bedroom_plus_rent,
    three_bedroom_plus_flag,
    total_rent,
    total_flag
FROM raw.tmp_rent_raw;

TRUNCATE raw.tmp_rent_raw;
\copy raw.tmp_rent_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/rent/montreal_rent.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_rent_raw
SELECT
    'Montreal',
    rent_period,
    studio_rent,
    studio_flag,
    one_bedroom_rent,
    one_bedroom_flag,
    two_bedroom_rent,
    two_bedroom_flag,
    three_bedroom_plus_rent,
    three_bedroom_plus_flag,
    total_rent,
    total_flag
FROM raw.tmp_rent_raw;

TRUNCATE raw.tmp_rent_raw;
\copy raw.tmp_rent_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/rent/ottawa_rent.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_rent_raw
SELECT
    'Ottawa',
    rent_period,
    studio_rent,
    studio_flag,
    one_bedroom_rent,
    one_bedroom_flag,
    two_bedroom_rent,
    two_bedroom_flag,
    three_bedroom_plus_rent,
    three_bedroom_plus_flag,
    total_rent,
    total_flag
FROM raw.tmp_rent_raw;

TRUNCATE raw.tmp_rent_raw;
\copy raw.tmp_rent_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/rent/toronto_rent.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_rent_raw
SELECT
    'Toronto',
    rent_period,
    studio_rent,
    studio_flag,
    one_bedroom_rent,
    one_bedroom_flag,
    two_bedroom_rent,
    two_bedroom_flag,
    three_bedroom_plus_rent,
    three_bedroom_plus_flag,
    total_rent,
    total_flag
FROM raw.tmp_rent_raw;

TRUNCATE raw.tmp_rent_raw;
\copy raw.tmp_rent_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/rent/vancouver_rent.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

INSERT INTO raw.city_rent_raw
SELECT
    'Vancouver',
    rent_period,
    studio_rent,
    studio_flag,
    one_bedroom_rent,
    one_bedroom_flag,
    two_bedroom_rent,
    two_bedroom_flag,
    three_bedroom_plus_rent,
    three_bedroom_plus_flag,
    total_rent,
    total_flag
FROM raw.tmp_rent_raw;

--upload cpi data
\copy raw.canada_cpi_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/external/canada_cpi.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');
--upload usd-cad data

\copy raw.usd_cad_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/external/usd_cad.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

--upload 5-year mortgage data
\copy raw.canada_5yearmortgage_raw FROM 'C:/Users/Dong/Desktop/projects/rent-vs-buy-analysis/data/raw/external/canada_5year_mortgage.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');

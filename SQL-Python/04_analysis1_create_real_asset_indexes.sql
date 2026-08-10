-- =========================================================
-- Create analysis-ready tables from staging data for Power BI.
-- =========================================================

CREATE SCHEMA IF NOT EXISTS analysis;

-- =========================================================
-- Canada House Real Price Index - Analysis Table
-- Rebase index from 2010 = 100 to 1990 = 100
-- Source: stg.canada_house_price_index_2010_100
-- =========================================================
DROP TABLE IF EXISTS analysis.canada_house_price_index_1990_100;

CREATE TABLE analysis.canada_house_price_index_1990_100 (
    date_period DATE,
    price_index_original NUMERIC,
    price_index_1990_100 NUMERIC
);

INSERT INTO analysis.canada_house_price_index_1990_100 (
    date_period, 
    price_index_original, 
    price_index_1990_100
    )
SELECT
    date_period + INTERVAL '1 day' AS date_period,
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

-- =========================================================
--SP 500 Real CAD Index
--transform usd to cad
--Convert stock nominal price into real stock price using CPI
--Re-index real stock price to 1990 = 100
-- =========================================================
DROP TABLE IF EXISTS analysis.sp500_index_1990_100;
CREATE TABLE analysis.sp500_index_1990_100 (
    date_period DATE,
    price_usd NUMERIC,
    price_cad NUMERIC,
    price_cad_real NUMERIC,
    price_index_cad_real NUMERIC
);
--step 1:transform usd to cad
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

--step 2:Convert stock nominal price into real stock price using CPI
UPDATE analysis.sp500_index_1990_100 
SET price_cad_real = price_cad/NULLIF(cpi.cpi_value,0)
*100
FROM stg.canada_cpi cpi
WHERE cpi.date_period = analysis.sp500_index_1990_100.date_period;

--step 3:Re-index real stock price to 1990 = 100
UPDATE analysis.sp500_index_1990_100 
 SET price_index_cad_real = price_cad_real/(
    SELECT price_cad_real
    FROM analysis.sp500_index_1990_100 
    WHERE date_period = DATE '1990-01-01'
 )*100;

-- =========================================================
--TSX Real CAD Index
--Convert stock nominal price into real stock price using CPI
--Re-index real stock price to 1990 = 100
-- =========================================================
DROP TABLE IF EXISTS analysis.tsx_index_1990_100;
CREATE TABLE analysis.tsx_index_1990_100 (
    date_period DATE,
    price_cad NUMERIC,
    price_cad_real NUMERIC,
    price_index_cad_real NUMERIC
);
--step 1:Convert stock nominal price into real stock price using CPI
INSERT INTO analysis.tsx_index_1990_100 (
    date_period, 
    price_cad,
    price_cad_real)
SELECT
    stg.tsx_cad.date_period AS date_period,
    stg.tsx_cad.adj_close_price AS price_cad,
    stg.tsx_cad.adj_close_price/stg.canada_cpi.cpi_value *100 AS price_cad_real
FROM stg.tsx_cad
LEFT JOIN  stg.canada_cpi
 ON stg.tsx_cad.date_period = stg.canada_cpi.date_period;

--step 2:Re-index real stock price to 1990 = 100
UPDATE analysis.tsx_index_1990_100 
 SET price_index_cad_real = price_cad_real/(
    SELECT price_cad_real
    FROM analysis.tsx_index_1990_100 
    WHERE date_period = DATE '1990-01-01'
 )*100;

-- =========================================================
--VT Real CAD 
--transform usd to cad
--Convert stock nominal price into real stock price using CPI

-- =========================================================
DROP TABLE IF EXISTS analysis.vt_cad_real;
CREATE TABLE analysis.vt_cad_real (
    date_period DATE,
    price_usd NUMERIC,
    price_cad NUMERIC,
    price_cad_real NUMERIC
);
--step 1:transform usd to cad
INSERT INTO analysis.vt_cad_real (
    date_period, 
    price_usd, 
    price_cad)
SELECT
    vt.date_period AS date_period,
    vt.adj_close_price AS price_usd,
    vt.adj_close_price * fx.dexcaus AS price_cad
FROM stg.vt_usd vt
LEFT JOIN LATERAL(
    SELECT dexcaus
    FROM stg.usd_cad fx
    WHERE fx.date_period <= vt.date_period
        AND fx.dexcaus IS NOT NULL
    ORDER BY fx.date_period DESC
    LIMIT 1 
) AS fx ON TRUE;

--step 2:Convert stock nominal price into real stock price using CPI
UPDATE analysis.vt_cad_real vt
SET price_cad_real = vt.price_cad / NULLIF(cpi.cpi_value, 0) * 100
FROM stg.canada_cpi cpi
WHERE vt.date_period = cpi.date_period;

-- =========================================================
-- City House Price Indices - Analysis Table
-- Original nominal indices: January 2005 = 100
-- Source:
--   stg.city_house_prices
--   stg.canada_cpi
--
-- Step 1:
-- Convert nominal house-price indices into real indices
-- using Canadian CPI.
--
-- Step 2:
-- Re-index the real house-price indices so that
-- January 2005 = 100.
-- =========================================================

DROP TABLE IF EXISTS analysis.city_indexed_house_prices;

CREATE TABLE analysis.city_indexed_house_prices (
    date_period DATE,

    canada_price_index_original NUMERIC,
    vancouver_price_index_original NUMERIC,
    calgary_price_index_original NUMERIC,
    edmonton_price_index_original NUMERIC,
    toronto_price_index_original NUMERIC,
    ottawa_price_index_original NUMERIC,
    montreal_price_index_original NUMERIC,

    canada_price_index_real NUMERIC,
    vancouver_price_index_real NUMERIC,
    calgary_price_index_real NUMERIC,
    edmonton_price_index_real NUMERIC,
    toronto_price_index_real NUMERIC,
    ottawa_price_index_real NUMERIC,
    montreal_price_index_real NUMERIC,

    canada_price_index_real_2005_100 NUMERIC,
    vancouver_price_index_real_2005_100 NUMERIC,
    calgary_price_index_real_2005_100 NUMERIC,
    edmonton_price_index_real_2005_100 NUMERIC,
    toronto_price_index_real_2005_100 NUMERIC,
    ottawa_price_index_real_2005_100 NUMERIC,
    montreal_price_index_real_2005_100 NUMERIC
);


-- =========================================================
-- Step 1: Adjust nominal indices for inflation
-- =========================================================

INSERT INTO analysis.city_indexed_house_prices (
    date_period,

    canada_price_index_original,
    vancouver_price_index_original,
    calgary_price_index_original,
    edmonton_price_index_original,
    toronto_price_index_original,
    ottawa_price_index_original,
    montreal_price_index_original,

    canada_price_index_real,
    vancouver_price_index_real,
    calgary_price_index_real,
    edmonton_price_index_real,
    toronto_price_index_real,
    ottawa_price_index_real,
    montreal_price_index_real
)
SELECT
    house.date_period,

    house.canada_price_index,
    house.vancouver_price_index,
    house.calgary_price_index,
    house.edmonton_price_index,
    house.toronto_price_index,
    house.ottawa_price_index,
    house.montreal_price_index,

    house.canada_price_index
        / NULLIF(cpi.cpi_value, 0) * 100
        AS canada_price_index_real,

    house.vancouver_price_index
        / NULLIF(cpi.cpi_value, 0) * 100
        AS vancouver_price_index_real,

    house.calgary_price_index
        / NULLIF(cpi.cpi_value, 0) * 100
        AS calgary_price_index_real,

    house.edmonton_price_index
        / NULLIF(cpi.cpi_value, 0) * 100
        AS edmonton_price_index_real,

    house.toronto_price_index
        / NULLIF(cpi.cpi_value, 0) * 100
        AS toronto_price_index_real,

    house.ottawa_price_index
        / NULLIF(cpi.cpi_value, 0) * 100
        AS ottawa_price_index_real,

    house.montreal_price_index
        / NULLIF(cpi.cpi_value, 0) * 100
        AS montreal_price_index_real

FROM stg.city_indexed_house_prices AS house
LEFT JOIN stg.canada_cpi AS cpi
    ON house.date_period = cpi.date_period

ORDER BY house.date_period;


-- =========================================================
-- Step 2: Re-index real values so January 2005 = 100
-- =========================================================

UPDATE analysis.city_indexed_house_prices
SET
    canada_price_index_real_2005_100 =
        canada_price_index_real
        / NULLIF(
            (
                SELECT canada_price_index_real
                FROM analysis.city_indexed_house_prices
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100,

    vancouver_price_index_real_2005_100 =
        vancouver_price_index_real
        / NULLIF(
            (
                SELECT vancouver_price_index_real
                FROM analysis.city_indexed_house_prices
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100,

    calgary_price_index_real_2005_100 =
        calgary_price_index_real
        / NULLIF(
            (
                SELECT calgary_price_index_real
                FROM analysis.city_indexed_house_prices
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100,

    edmonton_price_index_real_2005_100 =
        edmonton_price_index_real
        / NULLIF(
            (
                SELECT edmonton_price_index_real
                FROM analysis.city_indexed_house_prices
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100,

    toronto_price_index_real_2005_100 =
        toronto_price_index_real
        / NULLIF(
            (
                SELECT toronto_price_index_real
                FROM analysis.city_indexed_house_prices
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100,

    ottawa_price_index_real_2005_100 =
        ottawa_price_index_real
        / NULLIF(
            (
                SELECT ottawa_price_index_real
                FROM analysis.city_indexed_house_prices
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100,

    montreal_price_index_real_2005_100 =
        montreal_price_index_real
        / NULLIF(
            (
                SELECT montreal_price_index_real
                FROM analysis.city_indexed_house_prices
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100;

ALTER TABLE analysis.city_indexed_house_prices
ADD COLUMN sp500_price_index_real_2005_100 NUMERIC,
ADD COLUMN tsx_price_index_real_2005_100 NUMERIC;

UPDATE analysis.city_indexed_house_prices AS city
SET
    sp500_price_index_real_2005_100 =
        sp500.price_cad_real
        / NULLIF(
            (
                SELECT price_cad_real
                FROM analysis.sp500_index_1990_100
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100,

    tsx_price_index_real_2005_100 =
        tsx.price_cad_real
        / NULLIF(
            (
                SELECT price_cad_real
                FROM analysis.tsx_index_1990_100
                WHERE date_period = DATE '2005-01-01'
            ),
            0
        ) * 100

FROM analysis.sp500_index_1990_100 AS sp500
LEFT JOIN analysis.tsx_index_1990_100 AS tsx
    ON sp500.date_period = tsx.date_period

WHERE city.date_period = sp500.date_period;
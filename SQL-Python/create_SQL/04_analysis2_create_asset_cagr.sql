---Rows: Start year
--Columns: Holding years
--Values: CAGR
--Slicer: Asset

--Or create a heatmap where:

--rows = start year
--columns = holding period
--cell value = CAGR or winning asset

-- =========================================================
-- Canada House Price CAGR Analysis
-- Source: stg.canada_house_price_index_2010_100
-- Holding periods: 5, 10, 15, 20, 25, 30, and 35 years
-- Uses Q1 data as the annual starting observation
-- =========================================================
DROP TABLE IF EXISTS analysis.canada_house_cagr;

CREATE TABLE analysis.canada_house_cagr (
    start_date DATE,
    end_date DATE,
    start_year INTEGER,
    end_year INTEGER,
    holding_years INTEGER,
    start_price NUMERIC,
    end_price NUMERIC,
    cagr NUMERIC
);

INSERT INTO analysis.canada_house_cagr (
    start_date,
    start_year,
    holding_years,
    end_date,
    end_year,
    start_price,
    end_price,
    cagr
)
SELECT
    start_data.date_period AS start_date,
    EXTRACT(YEAR FROM start_data.date_period) ::INTEGER AS start_year,
    holding.holding_years AS holding_years,
    end_data.date_period AS end_date,
    EXTRACT(YEAR FROM end_data.date_period) ::INTEGER AS end_year,
    start_data.price_index AS start_price,
    end_data.price_index AS end_price,
    
    POWER(
        END_DATA.PRICE_INDEX
        /NULLIF(start_data.price_index, 0),
        1.0/holding.holding_years
    ) -1 AS cagr
    
FROM stg.canada_house_price_index_2010_100 AS start_data

CROSS JOIN (
    VALUES 
    (5),
    (10),
    (15),
    (20),
    (25),
    (30),
    (35)
) AS holding(holding_years)

INNER JOIN stg.canada_house_price_index_2010_100 AS end_data
    ON end_data.date_period = (
        start_data.date_period + MAKE_INTERVAL (years => holding.holding_years)
    ):: DATE

WHERE EXTRACT(QUARTER FROM start_data.date_period) = 1

ORDER BY 
    start_data.date_period,
    holding.holding_years;

    
-- =========================================================
-- S&P 500 Real CAD CAGR Analysis
-- Source: analysis.sp500_index_1990_100
-- Price column: price_index_cad_real
-- Holding periods: 5, 10, 15, 20, 25, 30, and 35 years
-- Uses January data as the annual starting observation
-- =========================================================

DROP TABLE IF EXISTS analysis.sp500_cagr;

CREATE TABLE analysis.sp500_cagr (
    start_date DATE,
    end_date DATE,
    start_year INTEGER,
    end_year INTEGER,
    holding_years INTEGER,
    start_price NUMERIC,
    end_price NUMERIC,
    cagr NUMERIC
);

INSERT INTO analysis.sp500_cagr (
    start_date,
    start_year,
    holding_years,
    end_date,
    end_year,
    start_price,
    end_price,
    cagr
)
SELECT
    start_data.date_period AS start_date,
    EXTRACT(YEAR FROM start_data.date_period)::INTEGER AS start_year,
    holding.holding_years,
    end_data.date_period AS end_date,
    EXTRACT(YEAR FROM end_data.date_period)::INTEGER AS end_year,
    start_data.price_index_cad_real AS start_price,
    end_data.price_index_cad_real AS end_price,

    POWER(
        end_data.price_index_cad_real
        / NULLIF(start_data.price_index_cad_real, 0),
        1.0 / holding.holding_years
    ) - 1 AS cagr

FROM analysis.sp500_index_1990_100 AS start_data

CROSS JOIN (
    VALUES
        (5),
        (10),
        (15),
        (20),
        (25),
        (30),
        (35)
) AS holding(holding_years)

INNER JOIN analysis.sp500_index_1990_100 AS end_data
    ON end_data.date_period = (
        start_data.date_period
        + MAKE_INTERVAL(years => holding.holding_years)
    )::DATE

WHERE EXTRACT(MONTH FROM start_data.date_period) = 1
  AND start_data.price_index_cad_real IS NOT NULL
  AND end_data.price_index_cad_real IS NOT NULL

ORDER BY
    start_data.date_period,
    holding.holding_years;


-- =========================================================
-- TSX Real CAD CAGR Analysis
-- Source: analysis.tsx_index_1990_100
-- Price column: price_index_cad_real
-- Holding periods: 5, 10, 15, 20, 25, 30, and 35 years
-- Uses January data as the annual starting observation
-- =========================================================

DROP TABLE IF EXISTS analysis.tsx_cagr;

CREATE TABLE analysis.tsx_cagr (
    start_date DATE,
    end_date DATE,
    start_year INTEGER,
    end_year INTEGER,
    holding_years INTEGER,
    start_price NUMERIC,
    end_price NUMERIC,
    cagr NUMERIC
);

INSERT INTO analysis.tsx_cagr (
    start_date,
    start_year,
    holding_years,
    end_date,
    end_year,
    start_price,
    end_price,
    cagr
)
SELECT
    start_data.date_period AS start_date,
    EXTRACT(YEAR FROM start_data.date_period)::INTEGER AS start_year,
    holding.holding_years,
    end_data.date_period AS end_date,
    EXTRACT(YEAR FROM end_data.date_period)::INTEGER AS end_year,
    start_data.price_index_cad_real AS start_price,
    end_data.price_index_cad_real AS end_price,

    POWER(
        end_data.price_index_cad_real
        / NULLIF(start_data.price_index_cad_real, 0),
        1.0 / holding.holding_years
    ) - 1 AS cagr

FROM analysis.tsx_index_1990_100 AS start_data

CROSS JOIN (
    VALUES
        (5),
        (10),
        (15),
        (20),
        (25),
        (30),
        (35)
) AS holding(holding_years)

INNER JOIN analysis.tsx_index_1990_100 AS end_data
    ON end_data.date_period = (
        start_data.date_period
        + MAKE_INTERVAL(years => holding.holding_years)
    )::DATE

WHERE EXTRACT(MONTH FROM start_data.date_period) = 1
  AND start_data.price_index_cad_real IS NOT NULL
  AND end_data.price_index_cad_real IS NOT NULL

ORDER BY
    start_data.date_period,
    holding.holding_years;


-- =========================================================
-- VT Real CAD CAGR Analysis
-- Source: analysis.vt__cad_real
-- Price column: price_cad_real
-- Holding periods: 5, 10, 15, and 18 years
-- Uses January data as the annual starting observation
-- =========================================================

DROP TABLE IF EXISTS analysis.vt_cagr;

CREATE TABLE analysis.vt_cagr (
    start_date DATE,
    end_date DATE,
    start_year INTEGER,
    end_year INTEGER,
    holding_years INTEGER,
    start_price NUMERIC,
    end_price NUMERIC,
    cagr NUMERIC
);

INSERT INTO analysis.vt_cagr (
    start_date,
    start_year,
    holding_years,
    end_date,
    end_year,
    start_price,
    end_price,
    cagr
)
SELECT
    start_data.date_period AS start_date,
    EXTRACT(YEAR FROM start_data.date_period)::INTEGER AS start_year,
    holding.holding_years,
    end_data.date_period AS end_date,
    EXTRACT(YEAR FROM end_data.date_period)::INTEGER AS end_year,
    start_data.price_cad_real AS start_price,
    end_data.price_cad_real AS end_price,

    POWER(
        end_data.price_cad_real
        / NULLIF(start_data.price_cad_real, 0),
        1.0 / holding.holding_years
    ) - 1 AS cagr

FROM analysis.vt_cad_real AS start_data

CROSS JOIN (
    VALUES
        (5),
        (10),
        (15),
        (18)
) AS holding(holding_years)

INNER JOIN analysis.vt_cad_real AS end_data
    ON end_data.date_period = (
        start_data.date_period
        + MAKE_INTERVAL(years => holding.holding_years)
    )::DATE

WHERE EXTRACT(MONTH FROM start_data.date_period) = 1
  AND start_data.price_cad_real IS NOT NULL
  AND end_data.price_cad_real IS NOT NULL

ORDER BY
    start_data.date_period,
    holding.holding_years;


DROP TABLE IF EXISTS analysis.sum_canada_stock_cagr;

CREATE TABLE analysis.sum_canada_stock_cagr AS
SELECT 
    canada.start_date AS start_date, 
    canada.end_date AS end_date,
    canada.start_year AS start_year,
    canada.end_year AS end_year,
    canada.holding_years AS holding_years,
    canada.cagr AS canada_cagr,
    sp500.cagr AS  sp500_cagr,
    tsx.cagr AS  tsx_cagr,
    city.vancouver_cagr AS vancouver_cagr,
    city.calgary_cagr AS calgary_cagr,
    city.edmonton_cagr AS edmonton_cagr,
    city.toronto_cagr AS toronto_cagr,
    city.ottawa_cagr AS ottawa_cagr,
    city.montreal_cagr AS montreal_cagr

FROM analysis.canada_house_cagr AS canada

lEFT JOIN analysis.sp500_cagr AS sp500
    ON canada.start_year=sp500.start_year
    AND canada.holding_years=sp500.holding_years

LEFT JOIN analysis.tsx_cagr AS tsx
    ON canada.start_year  =tsx.start_year
    AND canada.holding_years =tsx.holding_years

LEFT JOIN analysis.city_house_cagr AS city
    ON canada.start_year  =city.start_year
    AND canada.holding_years =city.holding_years;



SELECT *
FROM simulation.rent_monthly_schedule
WHERE renter_net_worth_real IS NULL;

-- =========================================================
-- City-Level Real House Price CAGR Analysis
-- Source: analysis.city_indexed_house_prices
-- Price columns: real house-price indices, January 2005 = 100
-- Holding periods: 5, 10, 15, and 20 years
-- Uses January data as the annual starting observation
-- =========================================================

DROP TABLE IF EXISTS analysis.city_house_cagr;

CREATE TABLE analysis.city_house_cagr (
    start_date DATE,
    end_date DATE,
    start_year INTEGER,
    end_year INTEGER,
    holding_years INTEGER,

    canada_start_price NUMERIC,
    canada_end_price NUMERIC,
    canada_cagr NUMERIC,

    vancouver_start_price NUMERIC,
    vancouver_end_price NUMERIC,
    vancouver_cagr NUMERIC,

    calgary_start_price NUMERIC,
    calgary_end_price NUMERIC,
    calgary_cagr NUMERIC,

    edmonton_start_price NUMERIC,
    edmonton_end_price NUMERIC,
    edmonton_cagr NUMERIC,

    toronto_start_price NUMERIC,
    toronto_end_price NUMERIC,
    toronto_cagr NUMERIC,

    ottawa_start_price NUMERIC,
    ottawa_end_price NUMERIC,
    ottawa_cagr NUMERIC,

    montreal_start_price NUMERIC,
    montreal_end_price NUMERIC,
    montreal_cagr NUMERIC
);

INSERT INTO analysis.city_house_cagr (
    start_date,
    start_year,
    holding_years,
    end_date,
    end_year,

    canada_start_price,
    canada_end_price,
    canada_cagr,

    vancouver_start_price,
    vancouver_end_price,
    vancouver_cagr,

    calgary_start_price,
    calgary_end_price,
    calgary_cagr,

    edmonton_start_price,
    edmonton_end_price,
    edmonton_cagr,

    toronto_start_price,
    toronto_end_price,
    toronto_cagr,

    ottawa_start_price,
    ottawa_end_price,
    ottawa_cagr,

    montreal_start_price,
    montreal_end_price,
    montreal_cagr
)
SELECT
    start_data.date_period AS start_date,
    EXTRACT(YEAR FROM start_data.date_period)::INTEGER AS start_year,
    holding.holding_years,
    end_data.date_period AS end_date,
    EXTRACT(YEAR FROM end_data.date_period)::INTEGER AS end_year,

    start_data.canada_price_index_real_2005_100 AS canada_start_price,
    end_data.canada_price_index_real_2005_100 AS canada_end_price,

    POWER(
        end_data.canada_price_index_real_2005_100
        / NULLIF(start_data.canada_price_index_real_2005_100, 0),
        1.0 / holding.holding_years
    ) - 1 AS canada_cagr,

    start_data.vancouver_price_index_real_2005_100
        AS vancouver_start_price,

    end_data.vancouver_price_index_real_2005_100
        AS vancouver_end_price,

    POWER(
        end_data.vancouver_price_index_real_2005_100
        / NULLIF(
            start_data.vancouver_price_index_real_2005_100,
            0
        ),
        1.0 / holding.holding_years
    ) - 1 AS vancouver_cagr,

    start_data.calgary_price_index_real_2005_100
        AS calgary_start_price,

    end_data.calgary_price_index_real_2005_100
        AS calgary_end_price,

    POWER(
        end_data.calgary_price_index_real_2005_100
        / NULLIF(
            start_data.calgary_price_index_real_2005_100,
            0
        ),
        1.0 / holding.holding_years
    ) - 1 AS calgary_cagr,

    start_data.edmonton_price_index_real_2005_100
        AS edmonton_start_price,

    end_data.edmonton_price_index_real_2005_100
        AS edmonton_end_price,

    POWER(
        end_data.edmonton_price_index_real_2005_100
        / NULLIF(
            start_data.edmonton_price_index_real_2005_100,
            0
        ),
        1.0 / holding.holding_years
    ) - 1 AS edmonton_cagr,

    start_data.toronto_price_index_real_2005_100
        AS toronto_start_price,

    end_data.toronto_price_index_real_2005_100
        AS toronto_end_price,

    POWER(
        end_data.toronto_price_index_real_2005_100
        / NULLIF(
            start_data.toronto_price_index_real_2005_100,
            0
        ),
        1.0 / holding.holding_years
    ) - 1 AS toronto_cagr,

    start_data.ottawa_price_index_real_2005_100
        AS ottawa_start_price,

    end_data.ottawa_price_index_real_2005_100
        AS ottawa_end_price,

    POWER(
        end_data.ottawa_price_index_real_2005_100
        / NULLIF(
            start_data.ottawa_price_index_real_2005_100,
            0
        ),
        1.0 / holding.holding_years
    ) - 1 AS ottawa_cagr,

    start_data.montreal_price_index_real_2005_100
        AS montreal_start_price,

    end_data.montreal_price_index_real_2005_100
        AS montreal_end_price,

    POWER(
        end_data.montreal_price_index_real_2005_100
        / NULLIF(
            start_data.montreal_price_index_real_2005_100,
            0
        ),
        1.0 / holding.holding_years
    ) - 1 AS montreal_cagr

FROM analysis.city_indexed_house_prices AS start_data

CROSS JOIN (
    VALUES
        (5),
        (10),
        (15),
        (20)
) AS holding(holding_years)

INNER JOIN analysis.city_indexed_house_prices AS end_data
    ON end_data.date_period = (
        start_data.date_period
        + MAKE_INTERVAL(years => holding.holding_years)
    )::DATE

WHERE EXTRACT(MONTH FROM start_data.date_period) = 1

ORDER BY
    start_data.date_period,
    holding.holding_years;
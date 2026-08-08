CREATE SCHEMA IF NOT EXISTS simulation;

DROP TABLE IF EXISTS simulation.city_assumption;

CREATE TABLE simulation.city_assumption (
    city TEXT PRIMARY KEY,
    property_tax_rate NUMERIC(6,5),
    structure_ratio NUMERIC(6,5)
);

INSERT INTO simulation.city_assumption (
    city,
    property_tax_rate,
    structure_ratio
)
VALUES
    ('Canada',    0.010, 0.50),
    ('Toronto',   0.007, 0.45),
    ('Vancouver', 0.003, 0.35),
    ('Calgary',   0.007, 0.60),
    ('Edmonton',  0.010, 0.60),
    ('Ottawa',    0.012, 0.50),
    ('Montreal',  0.008, 0.50);

DROP TABLE IF EXISTS analysis.city_house_prices_long;

CREATE TABLE analysis.city_house_prices_long AS
SELECT
    t.date_period,
    x.city,
    x.price
FROM stg.city_house_prices AS t
CROSS JOIN LATERAL (
    VALUES
        ('Vancouver', t.vancouver_price),
        ('Calgary', t.calgary_price),
        ('Edmonton', t.edmonton_price),
        ('Toronto', t.toronto_price),
        ('Ottawa', t.ottawa_price),
        ('Montreal', t.montreal_price),
        ('Canada', t.canada_price)
) AS x(city, price)
WHERE x.price IS NOT NULL;


DROP TABLE IF EXISTS analysis.city_rent_long;
CREATE TABLE analysis.city_rent_long AS
SELECT
    t.date_period,
    x.city,
    x.price
FROM stg.city_rent AS t
CROSS JOIN LATERAL (
    VALUES
        ('Vancouver', t.vancouver_price),
        ('Calgary', t.calgary_price),
        ('Edmonton', t.edmonton_price),
        ('Toronto', t.toronto_price),
        ('Ottawa', t.ottawa_price),
        ('Montreal', t.montreal_price),
        ('Canada', t.canada_price)
) AS x(city, price)
WHERE x.price IS NOT NULL;

DROP TABLE IF EXISTS simulation.owner_basic_model CASCADE;

CREATE TABLE simulation.owner_basic_model (
    scenario_id BIGSERIAL PRIMARY KEY,

    buying_date DATE NOT NULL,
    sold_date DATE NOT NULL,
    city TEXT NOT NULL,

    holding_years INTEGER NOT NULL,
    buying_year INTEGER NOT NULL,
    sold_year INTEGER NOT NULL,

    house_price_buy NUMERIC NOT NULL,
    house_price_sold NUMERIC NOT NULL,

    purchase_cost_pct NUMERIC(6,5) NOT NULL DEFAULT 0.02,
    sale_cost_pct NUMERIC(6,5) NOT NULL DEFAULT 0.06,

    purchase_cost NUMERIC,
    sale_cost NUMERIC,

    down_payment_pct NUMERIC(6,5) NOT NULL,
    down_payment NUMERIC,
    initial_loan_before_insurance NUMERIC,

    mortgage_insurance_rate NUMERIC(8,6) NOT NULL DEFAULT 0,
    mortgage_insurance_cost NUMERIC,
    initial_loan_after_insurance NUMERIC,

    mortgage_term_year INTEGER NOT NULL DEFAULT 5,
    amortization_years INTEGER NOT NULL DEFAULT 25,

    property_tax_rate NUMERIC(6,5),
    structure_ratio NUMERIC(6,5),

    mortgage_rate_scenario TEXT,
    mortgage_rate_adjustment NUMERIC
);

-- =========================================================
-- Step 1: Create owner scenarios
-- =========================================================
INSERT INTO simulation.owner_basic_model (
    buying_date,
    sold_date,
    city,
    holding_years,
    buying_year,
    sold_year,
    house_price_buy,
    house_price_sold,
    down_payment_pct,
    property_tax_rate,
    structure_ratio,
    mortgage_rate_scenario,
    mortgage_rate_adjustment
)
SELECT
    start_data.date_period AS buying_date,
    end_data.date_period AS sold_date,
    start_data.city,
    holding.holding_years,

    EXTRACT(YEAR FROM start_data.date_period)::INTEGER
        AS buying_year,

    EXTRACT(YEAR FROM end_data.date_period)::INTEGER
        AS sold_year,

    start_data.price AS house_price_buy,
    end_data.price AS house_price_sold,
    down.down_payment_pct,

    assumptions.property_tax_rate,
    assumptions.structure_ratio,

    rate_scenario.mortgage_rate_scenario,
    rate_scenario.mortgage_rate_adjustment

FROM analysis.city_house_prices_long AS start_data

CROSS JOIN (
    VALUES
        (5),
        (10),
        (15),
        (20)
) AS holding(holding_years)

CROSS JOIN (
    VALUES
        (0.10::NUMERIC),
        (0.20::NUMERIC),
        (0.30::NUMERIC)
) AS down(down_payment_pct)

CROSS JOIN (
    VALUES
        ('Lower',  -2.0::NUMERIC),
        ('Base',    0.0::NUMERIC),
        ('Higher',  2.0::NUMERIC)
) AS rate_scenario(
    mortgage_rate_scenario,
    mortgage_rate_adjustment
)

INNER JOIN analysis.city_house_prices_long AS end_data
    ON end_data.city = start_data.city
    AND end_data.date_period = (
        start_data.date_period
        + MAKE_INTERVAL(years => holding.holding_years)
    )::DATE

INNER JOIN simulation.city_assumption AS assumptions
ON assumptions.city = start_data.city;


-- =========================================================
-- Step 2: Calculate purchase, sale and mortgage amounts
-- =========================================================
UPDATE simulation.owner_basic_model
SET
    purchase_cost = house_price_buy * purchase_cost_pct,

    sale_cost = house_price_sold * sale_cost_pct,

    down_payment = house_price_buy * down_payment_pct,

    initial_loan_before_insurance =
        house_price_buy * (1 - down_payment_pct);

-- =========================================================
-- Step 3A: Mortgage insurance rate
-- =========================================================
UPDATE simulation.owner_basic_model
SET mortgage_insurance_rate =         
    CASE
            WHEN down_payment_pct = 0.10 THEN 0.031
            ELSE 0
    END;

-- =========================================================
-- Step 3B: Mortgage insurance cost
-- =========================================================
UPDATE simulation.owner_basic_model
SET mortgage_insurance_cost = 
mortgage_insurance_rate * initial_loan_before_insurance;

-- =========================================================
-- Step 3C: Final initial mortgage amount
-- =========================================================
UPDATE simulation.owner_basic_model
SET initial_loan_after_insurance =
    initial_loan_before_insurance + mortgage_insurance_cost;

-- ========================================================= 
-- Create monthly owner schedule -- 
--=========================================================
DROP TABLE IF EXISTS simulation.owner_monthly_schedule;

CREATE TABLE simulation.owner_monthly_schedule (
    scenario_id BIGINT NOT NULL,

    date_period DATE NOT NULL,
    house_price_market NUMERIC,
    estimated_current_sale_cost NUMERIC,
    month_number INTEGER NOT NULL,

    buying_date DATE,
    sold_date DATE,
    city TEXT,

    holding_years INTEGER,
    buying_year INTEGER,
    sold_year INTEGER,
    
    purchase_cost_pct NUMERIC(6,5) NOT NULL DEFAULT 0.02,
    sale_cost_pct NUMERIC(6,5) NOT NULL DEFAULT 0.06,

    house_price_buy NUMERIC,
    house_price_sold NUMERIC,

    purchase_cost NUMERIC,
    sale_cost NUMERIC,

    down_payment_pct NUMERIC,
    down_payment NUMERIC,

    mortgage_insurance_cost NUMERIC,
    initial_loan_after_insurance NUMERIC,

    mortgage_term_year INTEGER,
    amortization_years INTEGER,

    mortgage_term_number INTEGER,
    is_sale_month BOOLEAN,

    mortgage_rate_scenario TEXT,
    mortgage_rate_adjustment NUMERIC,   
    historical_mortgage_rate NUMERIC,
    applied_mortgage_rate NUMERIC,


    mortgage_payment NUMERIC,
    mortgage_interest NUMERIC,
    mortgage_principal NUMERIC,
    mortgage_balance NUMERIC,

   
    structure_ratio NUMERIC(6,5),

    structure_value NUMERIC,

    maintenance_rate NUMERIC NOT NULL DEFAULT 0.015,
    maintenance_cost NUMERIC,

    property_tax_rate NUMERIC(6,5),
    property_cost NUMERIC,
    
    insurance_rate NUMERIC NOT NULL DEFAULT 0.003, 
    insurance_cost NUMERIC,

    owner_monthly_unrecoverable_cost NUMERIC,
    cumulative_unrecoverable_cost NUMERIC,
    owner_net_worth NUMERIC,

    PRIMARY KEY (scenario_id, date_period),

    FOREIGN KEY (scenario_id)
        REFERENCES simulation.owner_basic_model (scenario_id)
);

-- ========================================================= 
-- Insert one row for every month of every owner scenario 
-- =========================================================
INSERT INTO simulation.owner_monthly_schedule (
    scenario_id,
    date_period,
    month_number,

    buying_date,
    sold_date,
    city,

    holding_years,
    buying_year,
    sold_year,

    house_price_buy,
    house_price_sold,

    purchase_cost,
    sale_cost,

    down_payment_pct,
    down_payment,

    mortgage_insurance_cost,
    initial_loan_after_insurance,

    mortgage_term_year,
    amortization_years,

    mortgage_term_number,
    is_sale_month,

    property_tax_rate,
    structure_ratio,

    mortgage_rate_scenario,
    mortgage_rate_adjustment

)
SELECT
    owner.scenario_id,

    month_data.date_period,

    (
        EXTRACT(
            YEAR FROM AGE(
                month_data.date_period,
                owner.buying_date
            )
        ) * 12
        +
        EXTRACT(
            MONTH FROM AGE(
                month_data.date_period,
                owner.buying_date
            )
        )
    )::INTEGER AS month_number,

    owner.buying_date,
    owner.sold_date,
    owner.city,

    owner.holding_years,
    owner.buying_year,
    owner.sold_year,

    owner.house_price_buy,
    owner.house_price_sold,

    owner.purchase_cost,
    owner.sale_cost,

    owner.down_payment_pct,
    owner.down_payment,

    owner.mortgage_insurance_cost,
    owner.initial_loan_after_insurance,

    owner.mortgage_term_year,
    owner.amortization_years,
    
    FLOOR(
        (
            EXTRACT(
                YEAR FROM AGE(
                    month_data.date_period,
                    owner.buying_date
                )
            ) * 12
            +
            EXTRACT(
                MONTH FROM AGE(
                    month_data.date_period,
                    owner.buying_date
                )
            )
        )
        /
        (owner.mortgage_term_year * 12)
    )::INTEGER AS mortgage_term_number,

    month_data.date_period = owner.sold_date
        AS is_sale_month,

    owner.property_tax_rate,

    owner.structure_ratio,
    
    owner.mortgage_rate_scenario,
    owner.mortgage_rate_adjustment 

FROM simulation.owner_basic_model AS owner
CROSS JOIN LATERAL (
    SELECT
        generate_series(
            owner.buying_date,
            
            LEAST(
                    owner.sold_date,
                    DATE '2025-12-01'
                ),
            
            INTERVAL '1 month'
        )::DATE AS date_period
) AS month_data;


-- ========================================================= 
-- Add current monthly house market prices -- 
--=========================================================
UPDATE simulation.owner_monthly_schedule AS owner
SET house_price_market = house.price
FROM analysis.city_house_prices_long AS house
WHERE house.city = owner.city
  AND house.date_period = owner.date_period;

-- ========================================================= 
-- Calculate estimated selling cost for every month 
-- =========================================================
UPDATE simulation.owner_monthly_schedule
SET estimated_current_sale_cost = 
    house_price_market 
    * sale_cost_pct;

-- ========================================================= 
-- Find the historical mortgage rate for each mortgage term -- 
-- Term 0: rate at buying date 
-- Term 1: rate five years after buying -
--Term 2: rate ten years after buying 
-- =========================================================
UPDATE simulation.owner_monthly_schedule AS owner
SET historical_mortgage_rate = (
    SELECT mor.mortgage_rate
    FROM stg.canada_5yearmortgage AS mor
    WHERE mor.date_period <= (
        owner.buying_date
        + MAKE_INTERVAL(
            years =>
                owner.mortgage_term_number
                * owner.mortgage_term_year
        )
    )::DATE
        AND mor.mortgage_rate IS NOT NULL
    ORDER BY mor.date_period DESC
    LIMIT 1
);
-- ========================================================= 
-- Apply lower, base or higher mortgage-rate scenario
--=========================================================
UPDATE simulation.owner_monthly_schedule
SET applied_mortgage_rate =
    CASE
        WHEN historical_mortgage_rate IS NULL
        THEN NULL

        ELSE GREATEST(
            historical_mortgage_rate
            + mortgage_rate_adjustment,
            0
        )
    END;
-- ========================================================= 
-- Calculate structure value
--=========================================================
UPDATE simulation.owner_monthly_schedule
SET structure_value = structure_ratio * house_price_market;

-- ========================================================= 
-- Calculate monthly ownership costs 
-- =========================================================
UPDATE simulation.owner_monthly_schedule
SET 
insurance_cost = insurance_rate * house_price_market/12,
maintenance_cost = maintenance_rate * structure_value/12,
property_cost = property_tax_rate * house_price_market/12;









    

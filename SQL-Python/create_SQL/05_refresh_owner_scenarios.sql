-- Run through update_owner.py, inside its transaction.
-- The runner creates _owner_refresh_config(cutoff DATE).
-- No permanent table is dropped, truncated, renamed or replaced.
CREATE SCHEMA IF NOT EXISTS simulation;

CREATE TABLE IF NOT EXISTS simulation.city_assumption (
    city TEXT PRIMARY KEY,
    property_tax_rate NUMERIC(6,5),
    structure_ratio NUMERIC(6,5)
);

CREATE TABLE IF NOT EXISTS simulation.owner_basic_model (
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

CREATE TABLE IF NOT EXISTS simulation.owner_monthly_schedule (
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
    ('Montreal',  0.008, 0.50)
ON CONFLICT (city) DO NOTHING;

-- Stable natural keys retain every existing scenario_id.
CREATE UNIQUE INDEX IF NOT EXISTS owner_refresh_scenario_key
ON simulation.owner_basic_model (buying_date, sold_date, city, holding_years, down_payment_pct, mortgage_rate_scenario);

CREATE TEMP TABLE _owner_refresh_ids ON COMMIT DROP AS
WITH refreshed AS (
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
ON assumptions.city = start_data.city
WHERE end_data.date_period <= (SELECT cutoff FROM _owner_refresh_config)
ON CONFLICT (buying_date, sold_date, city, holding_years, down_payment_pct, mortgage_rate_scenario) DO UPDATE SET
    buying_year = EXCLUDED.buying_year,
    sold_year = EXCLUDED.sold_year,
    house_price_buy = EXCLUDED.house_price_buy,
    house_price_sold = EXCLUDED.house_price_sold,
    property_tax_rate = EXCLUDED.property_tax_rate,
    structure_ratio = EXCLUDED.structure_ratio
RETURNING scenario_id
)
SELECT scenario_id FROM refreshed;
CREATE UNIQUE INDEX ON _owner_refresh_ids (scenario_id);


UPDATE simulation.owner_basic_model
SET
    purchase_cost = house_price_buy * purchase_cost_pct,

    sale_cost = house_price_sold * sale_cost_pct,

    down_payment = house_price_buy * down_payment_pct,

    initial_loan_before_insurance =
        house_price_buy * (1 - down_payment_pct)
WHERE scenario_id IN (SELECT scenario_id FROM _owner_refresh_ids);

UPDATE simulation.owner_basic_model
SET mortgage_insurance_rate =         
    CASE
            WHEN down_payment_pct = 0.10 THEN 0.031
            ELSE 0
    END
WHERE scenario_id IN (SELECT scenario_id FROM _owner_refresh_ids);

UPDATE simulation.owner_basic_model
SET mortgage_insurance_cost = 
mortgage_insurance_rate * initial_loan_before_insurance
WHERE scenario_id IN (SELECT scenario_id FROM _owner_refresh_ids);

UPDATE simulation.owner_basic_model
SET initial_loan_after_insurance =
    initial_loan_before_insurance + mortgage_insurance_cost
WHERE scenario_id IN (SELECT scenario_id FROM _owner_refresh_ids);

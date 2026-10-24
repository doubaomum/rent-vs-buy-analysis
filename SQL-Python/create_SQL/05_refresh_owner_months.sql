-- One batch of complete scenarios; called only by update_owner.py.
TRUNCATE _owner_input;

INSERT INTO _owner_input (
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
    
    -- Mortgage term alignment:
    -- Month 0-60   = term 0
    -- Month 61-120 = term 1
    -- Month 121-180 = term 2
    --
    -- Subtract 1 before division so the renewal rate starts
    -- at Month 61 rather than Month 60.
    FLOOR(
        GREATEST(
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
                - 1
            ),
            0
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
JOIN _owner_batch_ids AS batch USING (scenario_id)
CROSS JOIN LATERAL (
    SELECT
        generate_series(
            owner.buying_date,
            
            LEAST(
                    owner.sold_date,
                    (SELECT cutoff FROM _owner_refresh_config)
                ),
            
            INTERVAL '1 month'
        )::DATE AS date_period
) AS month_data;

-- Preserve any existing row-specific rate assumptions; defaults apply to new rows.
UPDATE _owner_input AS fresh
SET purchase_cost_pct = saved.purchase_cost_pct,
    sale_cost_pct = saved.sale_cost_pct,
    maintenance_rate = saved.maintenance_rate,
    insurance_rate = saved.insurance_rate
FROM simulation.owner_monthly_schedule AS saved
WHERE fresh.scenario_id = saved.scenario_id
  AND fresh.date_period = saved.date_period
  AND saved.scenario_id IN (SELECT scenario_id FROM _owner_batch_ids);



-- ========================================================= 
-- Add current monthly house market prices -- 
--=========================================================
UPDATE _owner_input AS owner
SET house_price_market = house.price
FROM analysis.city_house_prices_long AS house
WHERE house.city = owner.city
  AND house.date_period = owner.date_period;

-- ========================================================= 
-- Calculate estimated selling cost for every month 
-- =========================================================
UPDATE _owner_input
SET estimated_current_sale_cost = 
    house_price_market 
    * sale_cost_pct;

-- ========================================================= 
-- Find the historical mortgage rate for each mortgage term -- 
-- Term 0: rate at buying date 
-- Term 1: rate five years after buying -
--Term 2: rate ten years after buying 
-- =========================================================
UPDATE _owner_input AS owner
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
UPDATE _owner_input
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
UPDATE _owner_input
SET structure_value = structure_ratio * house_price_market;

-- ========================================================= 
-- Calculate monthly ownership costs 
-- =========================================================
UPDATE _owner_input
SET 
insurance_cost = insurance_rate * house_price_market/12,
maintenance_cost = maintenance_rate * structure_value/12,
property_cost = property_tax_rate * house_price_market/12;

-- Called by update_renter.py inside a single transaction.
CREATE SCHEMA IF NOT EXISTS simulation;

CREATE TABLE IF NOT EXISTS simulation.investment_assumptions (
    portfolio_name TEXT PRIMARY KEY,

    investment_fee NUMERIC(8,6) NOT NULL,
    tax_drag NUMERIC(8,6) NOT NULL,

    description TEXT
);

CREATE TABLE IF NOT EXISTS simulation.renter_policy_assumptions (
    city TEXT PRIMARY KEY,

    rent_growth_mode TEXT NOT NULL,

    rent_control_rate NUMERIC(8,6),

    annual_move_probability NUMERIC(8,6) NOT NULL,

    move_cost_multiplier NUMERIC(8,4) NOT NULL,

    CHECK (
        rent_growth_mode IN (
            'market',
            'controlled',
            'mixed'
        )
    ),

    CHECK (
        rent_control_rate IS NULL
        OR rent_control_rate >= 0
    ),

    CHECK (
        annual_move_probability >= 0
        AND annual_move_probability <= 1
    ),

    CHECK (
        move_cost_multiplier >= 0
    )
);

CREATE TABLE IF NOT EXISTS simulation.renter_monthly_schedule (

    renter_scenario_id BIGSERIAL PRIMARY KEY,

    owner_scenario_id BIGINT NOT NULL,

    date_period DATE NOT NULL,
    year INTEGER,
    month_number INTEGER NOT NULL,

    buying_date DATE,
    sold_date DATE,

    city TEXT,

    holding_years INTEGER,
    buying_year INTEGER,
    sold_year INTEGER,


    house_price_market NUMERIC,
    estimated_current_sale_cost NUMERIC,

    purchase_cost_pct NUMERIC(6,5),
    sale_cost_pct NUMERIC(6,5),

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

    maintenance_rate NUMERIC,
    maintenance_cost NUMERIC,

    property_tax_rate NUMERIC,
    property_cost NUMERIC,

    insurance_rate NUMERIC,
    insurance_cost NUMERIC,

    owner_monthly_unrecoverable_cost NUMERIC,
    cumulative_unrecoverable_cost NUMERIC,


    owner_total_cash_outflow NUMERIC,

    owner_net_worth NUMERIC,
    owner_net_worth_real NUMERIC,
    owner_net_worth_index NUMERIC,


    market_rent NUMERIC,

    rent_growth_mode TEXT,

    rent_control_rate NUMERIC,

    annual_move_probability NUMERIC,
    monthly_move_probability NUMERIC,

    move_cost_multiplier NUMERIC,


    random_move NUMERIC,
    renter_moves BOOLEAN,

    actual_renter_rent NUMERIC,
    move_cost NUMERIC,

    renter_total_cash_outflow NUMERIC,


    monthly_savings_difference NUMERIC,

    renter_discipline NUMERIC(6,5)
        NOT NULL DEFAULT 1.00,

    renter_monthly_investment NUMERIC,


    initial_renter_investment NUMERIC,

    portfolio_name TEXT NOT NULL,

    investment_fee NUMERIC,
    tax_drag NUMERIC,

    monthly_investment_cost NUMERIC,

    sp500_return NUMERIC,
    tsx_return NUMERIC,

    portfolio_return NUMERIC,
    portfolio_return_net NUMERIC,

    renter_portfolio_value NUMERIC,


    renter_net_worth NUMERIC,
    renter_net_worth_real NUMERIC,
    renter_net_worth_index NUMERIC,


    FOREIGN KEY (
        owner_scenario_id,
        date_period
    )
    REFERENCES simulation.owner_monthly_schedule (
        scenario_id,
        date_period
    ),

    UNIQUE (
        owner_scenario_id,
        date_period,
        portfolio_name,
        renter_discipline
    )
);

INSERT INTO simulation.investment_assumptions (
    portfolio_name,
    investment_fee,
    tax_drag,
    description
)
VALUES
    (
        'tsx_only',
        0.001,
        0.0010,
        'Canadian equity portfolio'
    ),
    (
        'sp500_only',
        0.001,
        0.0025,
        'U.S. equity portfolio from Canadian investor perspective'
    )
ON CONFLICT (portfolio_name) DO NOTHING;

INSERT INTO simulation.renter_policy_assumptions (
    city,
    rent_growth_mode,
    rent_control_rate,
    annual_move_probability,
    move_cost_multiplier
)
VALUES
    (
        'Canada',
        'mixed',
        0.020,     -- 2.0%
        0.10,      -- 10%
        1.0
    ),
    (
        'Toronto',
        'controlled',
        0.025,     -- 2.5%
        0.08,      -- 8%
        1.0
    ),
    (
        'Vancouver',
        'controlled',
        0.025,     -- 2.5%
        0.08,      -- 8%
        1.0
    ),
    (
        'Calgary',
        'market',
        NULL,      -- no rent-control rate
        0.12,      -- 12%
        1.0
    ),
    (
        'Edmonton',
        'market',
        NULL,      -- no rent-control rate
        0.12,      -- 12%
        1.0
    ),
    (
        'Ottawa',
        'controlled',
        0.025,     -- 2.5%
        0.08,      -- 8%
        1.0
    ),
    (
        'Montreal',
        'controlled',
        0.025,     -- 2.5%
        0.08,      -- 8%
        1.0
    )
ON CONFLICT (city) DO NOTHING;

CREATE TEMP TABLE _renter_owner_ids ON COMMIT DROP AS
SELECT b.scenario_id, b.buying_date, b.sold_date,
       (EXTRACT(YEAR FROM AGE(LEAST(b.sold_date, c.cutoff), b.buying_date))*12
        + EXTRACT(MONTH FROM AGE(LEAST(b.sold_date, c.cutoff), b.buying_date)))::integer + 1
        AS expected_months
FROM simulation.owner_basic_model b CROSS JOIN _renter_refresh_config c
WHERE b.buying_date <= c.cutoff
  AND b.city IN ('Canada','Vancouver','Calgary','Edmonton','Toronto','Ottawa','Montreal');
CREATE UNIQUE INDEX ON _renter_owner_ids (scenario_id);

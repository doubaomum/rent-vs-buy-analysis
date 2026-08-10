
-- =========================================================
-- 1. Investment assumptions
-- =========================================================
DROP TABLE IF EXISTS simulation.investment_assumptions;

CREATE TABLE simulation.investment_assumptions (
    portfolio_name TEXT PRIMARY KEY,

    investment_fee NUMERIC(8,6) NOT NULL,
    tax_drag NUMERIC(8,6) NOT NULL,

    description TEXT
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
    );


-- =========================================================
-- 2. Renter policy assumptions
-- =========================================================
DROP TABLE IF EXISTS simulation.renter_policy_assumptions;

CREATE TABLE simulation.renter_policy_assumptions (
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
        0.020,
        0.10,
        1.2
    ),
    (
        'Toronto',
        'controlled',
        0.025,
        0.08,
        1.8
    ),
    (
        'Vancouver',
        'controlled',
        0.030,
        0.07,
        2.0
    ),
    (
        'Calgary',
        'market',
        NULL,
        0.15,
        1.2
    ),
    (
        'Edmonton',
        'market',
        NULL,
        0.15,
        1.1
    ),
    (
        'Ottawa',
        'controlled',
        0.025,
        0.09,
        1.4
    ),
    (
        'Montreal',
        'controlled',
        0.025,
        0.10,
        1.2
    );



DROP TABLE IF EXISTS simulation.renter_monthly_schedule;

CREATE TABLE simulation.renter_monthly_schedule (

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



INSERT INTO simulation.renter_monthly_schedule (
    owner_scenario_id,
    date_period,
    year,
    month_number,
    buying_date,
    sold_date,
    city,
    holding_years,
    buying_year,
    sold_year,
    house_price_market,
    estimated_current_sale_cost,

    purchase_cost_pct,
    sale_cost_pct,

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

    mortgage_rate_scenario,
    mortgage_rate_adjustment,

    historical_mortgage_rate,
    applied_mortgage_rate,

    mortgage_payment,
    mortgage_interest,
    mortgage_principal,
    mortgage_balance,

    structure_ratio,
    structure_value,

    maintenance_rate,
    maintenance_cost,

    property_tax_rate,
    property_cost,

    insurance_rate,
    insurance_cost,

    owner_monthly_unrecoverable_cost,
    cumulative_unrecoverable_cost,


    owner_total_cash_outflow,

    owner_net_worth,

    market_rent,

    rent_growth_mode,
    rent_control_rate,

    annual_move_probability,
    monthly_move_probability,

    move_cost_multiplier,

    renter_discipline,

    initial_renter_investment,

    portfolio_name,

    investment_fee,
    tax_drag,

    monthly_investment_cost
)
SELECT


    owner.scenario_id
        AS owner_scenario_id,

    owner.date_period,

    EXTRACT(
        YEAR FROM owner.date_period
    )::INTEGER
        AS year,

    owner.month_number,

    owner.buying_date,
    owner.sold_date,

    owner.city,

    owner.holding_years,
    owner.buying_year,
    owner.sold_year,


    owner.house_price_market,

    owner.estimated_current_sale_cost,

    owner.purchase_cost_pct,
    owner.sale_cost_pct,

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

    owner.mortgage_term_number,
    owner.is_sale_month,

    owner.mortgage_rate_scenario,
    owner.mortgage_rate_adjustment,

    owner.historical_mortgage_rate,
    owner.applied_mortgage_rate,

    owner.mortgage_payment,
    owner.mortgage_interest,
    owner.mortgage_principal,
    owner.mortgage_balance,


    owner.structure_ratio,
    owner.structure_value,

    owner.maintenance_rate,
    owner.maintenance_cost,

    owner.property_tax_rate,
    owner.property_cost,

    owner.insurance_rate,
    owner.insurance_cost,

    owner.owner_monthly_unrecoverable_cost,
    owner.cumulative_unrecoverable_cost,


    (
        COALESCE(
            owner.mortgage_payment,
            0
        )
        +
        COALESCE(
            owner.maintenance_cost,
            0
        )
        +
        COALESCE(
            owner.property_cost,
            0
        )
        +
        COALESCE(
            owner.insurance_cost,
            0
        )
    )
        AS owner_total_cash_outflow,


    owner.owner_net_worth,


    rent_data.price
        AS market_rent,


    renter_policy.rent_growth_mode,

    renter_policy.rent_control_rate,

    renter_policy.annual_move_probability,

    (
        renter_policy.annual_move_probability
        / 12.0
    )
        AS monthly_move_probability,

    renter_policy.move_cost_multiplier,


    discipline.renter_discipline,



    (
        COALESCE(
            owner.down_payment,
            0
        )
        +
        COALESCE(
            owner.purchase_cost,
            0
        )
    )
        AS initial_renter_investment,


    investment.portfolio_name,

    investment.investment_fee,

    investment.tax_drag,

    (
        investment.investment_fee
        +
        investment.tax_drag
    )
    / 12.0
        AS monthly_investment_cost


FROM simulation.owner_monthly_schedule
    AS owner



CROSS JOIN simulation.investment_assumptions
    AS investment


CROSS JOIN (
    VALUES
        (1.00::NUMERIC)
) AS discipline(
    renter_discipline
)


INNER JOIN simulation.renter_policy_assumptions
    AS renter_policy

    ON renter_policy.city =
       owner.city



LEFT JOIN analysis.city_rent_long
    AS rent_data

    ON rent_data.city =
       owner.city

    AND EXTRACT(
        YEAR FROM rent_data.date_period
    )
    =
    EXTRACT(
        YEAR FROM owner.date_period
    )



WHERE owner.date_period
    <= DATE '2025-12-01'


ORDER BY

    owner.scenario_id,

    investment.portfolio_name,

    discipline.renter_discipline,

    owner.month_number;
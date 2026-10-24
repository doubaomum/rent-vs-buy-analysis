-- Original renter input SELECT; only the target, batch and cutoff differ.
TRUNCATE _renter_input;

INSERT INTO _renter_input (
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
    1
    -
    POWER(
        1
        - renter_policy.annual_move_probability,
        1.0 / 12.0
    )
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
JOIN _renter_batch_ids AS batch ON batch.scenario_id = owner.scenario_id



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
    <= (SELECT cutoff FROM _renter_refresh_config)


ORDER BY

    owner.scenario_id,

    investment.portfolio_name,

    discipline.renter_discipline,

    owner.month_number;

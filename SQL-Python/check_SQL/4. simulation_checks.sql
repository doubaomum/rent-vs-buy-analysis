-- =========================================================
-- SIMULATION LAYER DATA QUALITY + MODEL VALIDATION CHECKS
--
-- Purpose:
--   Validate scenario construction and the owner/renter monthly
--   recursions after the simulation SQL + Python steps finish.
--
-- Recommended execution order:
--   A. Quick structural checks
--   B. Owner formula checks
--   C. Renter formula checks
--   D. Deep recurrence checks (heavier on large tables)
--   E. Diagnostics / modelling assumptions
--
-- Expected convention:
--   Most error_count / mismatch_count results should be 0.
-- =========================================================


-- =========================================================
-- A1. TABLE / SCENARIO ROW COUNTS
-- =========================================================
SELECT 'simulation.city_assumption' AS table_name, COUNT(*) AS row_count
FROM simulation.city_assumption

UNION ALL
SELECT 'simulation.owner_basic_model', COUNT(*)
FROM simulation.owner_basic_model

UNION ALL
SELECT 'simulation.owner_monthly_schedule', COUNT(*)
FROM simulation.owner_monthly_schedule

UNION ALL
SELECT 'simulation.investment_assumptions', COUNT(*)
FROM simulation.investment_assumptions

UNION ALL
SELECT 'simulation.renter_policy_assumptions', COUNT(*)
FROM simulation.renter_policy_assumptions

UNION ALL
SELECT 'simulation.renter_monthly_schedule', COUNT(*)
FROM simulation.renter_monthly_schedule

ORDER BY table_name;


-- =========================================================
-- A2. ASSUMPTION TABLE CHECKS
-- Expected: error_count = 0
-- =========================================================
SELECT
    'city_assumption invalid rates' AS check_name,
    COUNT(*) AS error_count
FROM simulation.city_assumption
WHERE city IS NULL
   OR property_tax_rate IS NULL
   OR property_tax_rate < 0
   OR structure_ratio IS NULL
   OR structure_ratio <= 0
   OR structure_ratio > 1

UNION ALL

SELECT
    'investment_assumptions invalid values',
    COUNT(*)
FROM simulation.investment_assumptions
WHERE portfolio_name IS NULL
   OR investment_fee < 0
   OR tax_drag < 0

UNION ALL

SELECT
    'renter_policy invalid values',
    COUNT(*)
FROM simulation.renter_policy_assumptions
WHERE city IS NULL
   OR rent_growth_mode NOT IN ('market', 'controlled', 'mixed')
   OR (rent_control_rate IS NOT NULL AND rent_control_rate < 0)
   OR annual_move_probability < 0
   OR annual_move_probability > 1
   OR move_cost_multiplier < 0;


-- =========================================================
-- A3. OWNER BASIC MODEL FORMULAS
-- Expected: all mismatch counts = 0
-- Dollar tolerance: $0.01
-- =========================================================
SELECT
    COUNT(*) FILTER (
        WHERE ABS(purchase_cost - house_price_buy * purchase_cost_pct) > 0.01
    ) AS purchase_cost_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(sale_cost - house_price_sold * sale_cost_pct) > 0.01
    ) AS sale_cost_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(down_payment - house_price_buy * down_payment_pct) > 0.01
    ) AS down_payment_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            initial_loan_before_insurance
            - house_price_buy * (1 - down_payment_pct)
        ) > 0.01
    ) AS loan_before_insurance_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            mortgage_insurance_rate
            - CASE WHEN down_payment_pct = 0.10 THEN 0.031 ELSE 0 END
        ) > 0.000001
    ) AS insurance_rate_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            mortgage_insurance_cost
            - mortgage_insurance_rate * initial_loan_before_insurance
        ) > 0.01
    ) AS insurance_cost_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            initial_loan_after_insurance
            - (initial_loan_before_insurance + mortgage_insurance_cost)
        ) > 0.01
    ) AS loan_after_insurance_mismatch
FROM simulation.owner_basic_model;


-- =========================================================
-- A4. OWNER MONTHLY SCHEDULE COMPLETENESS
--
-- Expected:
--   starts_at_zero = true
--   continuous_months = true
--   actual_rows = expected_rows
--   max_month_number = expected_max_month
-- =========================================================
WITH owner_counts AS (
    SELECT
        scenario_id,
        buying_date,
        sold_date,
        COUNT(*) AS actual_rows,
        MIN(month_number) AS min_month_number,
        MAX(month_number) AS max_month_number,
        COUNT(DISTINCT month_number) AS distinct_months,
        (
            EXTRACT(
                YEAR FROM AGE(
                    LEAST(sold_date, DATE '2025-12-01'),
                    buying_date
                )
            ) * 12
            +
            EXTRACT(
                MONTH FROM AGE(
                    LEAST(sold_date, DATE '2025-12-01'),
                    buying_date
                )
            )
        )::INTEGER AS expected_max_month
    FROM simulation.owner_monthly_schedule
    GROUP BY
        scenario_id,
        buying_date,
        sold_date
)
SELECT
    COUNT(*) FILTER (WHERE min_month_number <> 0) AS scenarios_not_starting_at_zero,
    COUNT(*) FILTER (
        WHERE actual_rows <> max_month_number - min_month_number + 1
           OR distinct_months <> actual_rows
    ) AS scenarios_with_month_gaps_or_duplicates,
    COUNT(*) FILTER (
        WHERE actual_rows <> expected_max_month + 1
    ) AS scenarios_with_wrong_row_count,
    COUNT(*) FILTER (
        WHERE max_month_number <> expected_max_month
    ) AS scenarios_with_wrong_max_month
FROM owner_counts;


-- =========================================================
-- A5. OWNER DATE / MONTH ALIGNMENT
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.owner_monthly_schedule
WHERE date_period < buying_date
   OR date_period > LEAST(sold_date, DATE '2025-12-01')
   OR date_period <> (
        buying_date
        + MAKE_INTERVAL(months => month_number)
   )::DATE;


-- =========================================================
-- A6. SALE MONTH CHECK
-- Expected: all mismatch counts = 0
-- =========================================================
WITH sale_checks AS (
    SELECT
        scenario_id,
        sold_date,
        COUNT(*) FILTER (WHERE is_sale_month) AS sale_flag_count,
        MAX(date_period) FILTER (WHERE is_sale_month) AS flagged_sale_date
    FROM simulation.owner_monthly_schedule
    GROUP BY scenario_id, sold_date
)
SELECT
    COUNT(*) FILTER (
        WHERE sold_date <= DATE '2025-12-01'
          AND sale_flag_count <> 1
    ) AS scenarios_with_wrong_sale_flag_count,

    COUNT(*) FILTER (
        WHERE sold_date <= DATE '2025-12-01'
          AND flagged_sale_date <> sold_date
    ) AS scenarios_with_wrong_sale_date,

    COUNT(*) FILTER (
        WHERE sold_date > DATE '2025-12-01'
          AND sale_flag_count <> 0
    ) AS capped_scenarios_with_sale_flag
FROM sale_checks;


-- =========================================================
-- A7. OWNER CORE NULL / RANGE CHECK
-- Expected: error_count = 0
-- =========================================================
SELECT
    COUNT(*) AS error_count
FROM simulation.owner_monthly_schedule
WHERE house_price_market IS NULL
   OR house_price_market <= 0
   OR estimated_current_sale_cost IS NULL
   OR estimated_current_sale_cost < 0
   OR historical_mortgage_rate IS NULL
   OR applied_mortgage_rate IS NULL
   OR applied_mortgage_rate < 0
   OR maintenance_cost IS NULL
   OR maintenance_cost < 0
   OR property_cost IS NULL
   OR property_cost < 0
   OR insurance_cost IS NULL
   OR insurance_cost < 0;


-- =========================================================
-- A8. IMPORTANT: MORTGAGE TERM NUMBER ALIGNMENT
--
-- Python recalculates payment at month 1, 61, 121, ...
-- Therefore months 1-60 belong to term 0,
-- months 61-120 belong to term 1, etc.
--
-- Expected: mismatch_count = 0
--
-- If this returns rows at month 60 / 120 / 180 / ...,
-- the owner schedule has an off-by-one term-number bug.
-- =========================================================
WITH expected AS (
    SELECT
        scenario_id,
        date_period,
        month_number,
        mortgage_term_year,
        mortgage_term_number,
        CASE
            WHEN month_number = 0 THEN 0
            ELSE FLOOR(
                (month_number - 1)::NUMERIC
                / (mortgage_term_year * 12)
            )::INTEGER
        END AS expected_term_number
    FROM simulation.owner_monthly_schedule
)
SELECT
    COUNT(*) AS mismatch_count
FROM expected
WHERE mortgage_term_number <> expected_term_number;


-- Detail rows for the mortgage-term mismatch
WITH expected AS (
    SELECT
        scenario_id,
        date_period,
        month_number,
        mortgage_term_year,
        mortgage_term_number,
        CASE
            WHEN month_number = 0 THEN 0
            ELSE FLOOR(
                (month_number - 1)::NUMERIC
                / (mortgage_term_year * 12)
            )::INTEGER
        END AS expected_term_number
    FROM simulation.owner_monthly_schedule
)
SELECT *
FROM expected
WHERE mortgage_term_number <> expected_term_number
ORDER BY scenario_id, month_number
LIMIT 100;


-- =========================================================
-- B1. OWNER STATIC MONTHLY COST FORMULAS
-- Expected: all mismatch counts = 0
-- =========================================================
SELECT
    COUNT(*) FILTER (
        WHERE ABS(
            estimated_current_sale_cost
            - house_price_market * sale_cost_pct
        ) > 0.01
    ) AS estimated_sale_cost_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            structure_value
            - structure_ratio * house_price_market
        ) > 0.01
    ) AS structure_value_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            maintenance_cost
            - maintenance_rate * structure_value / 12
        ) > 0.01
    ) AS maintenance_cost_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            property_cost
            - property_tax_rate * house_price_market / 12
        ) > 0.01
    ) AS property_cost_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            insurance_cost
            - insurance_rate * house_price_market / 12
        ) > 0.01
    ) AS insurance_cost_mismatch
FROM simulation.owner_monthly_schedule;


-- =========================================================
-- B2. APPLIED MORTGAGE RATE FORMULA
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.owner_monthly_schedule
WHERE ABS(
    applied_mortgage_rate
    - GREATEST(
        historical_mortgage_rate + mortgage_rate_adjustment,
        0
    )
) > 0.000001;


-- =========================================================
-- B3. MORTGAGE PAYMENT IDENTITY / NON-NEGATIVE CHECKS
-- Expected: all error counts = 0
-- =========================================================
SELECT
    COUNT(*) FILTER (
        WHERE mortgage_payment < 0
           OR mortgage_interest < 0
           OR mortgage_principal < 0
           OR mortgage_balance < 0
    ) AS negative_mortgage_values,

    COUNT(*) FILTER (
        WHERE month_number = 0
          AND (
                ABS(COALESCE(mortgage_payment, 0)) > 0.01
             OR ABS(COALESCE(mortgage_interest, 0)) > 0.01
             OR ABS(COALESCE(mortgage_principal, 0)) > 0.01
          )
    ) AS month0_nonzero_payment_components,

    COUNT(*) FILTER (
        WHERE month_number = 0
          AND ABS(
                mortgage_balance - initial_loan_after_insurance
              ) > 0.01
    ) AS month0_balance_mismatch,

    COUNT(*) FILTER (
        WHERE month_number > 0
          AND ABS(
                mortgage_payment
                - (mortgage_interest + mortgage_principal)
              ) > 0.01
    ) AS payment_identity_mismatch
FROM simulation.owner_monthly_schedule;


-- =========================================================
-- B4. OWNER UNRECOVERABLE COST FORMULA
--
-- Expected monthly unrecoverable cost =
--   mortgage interest
-- + maintenance
-- + property tax
-- + insurance
-- + purchase cost in month 0
-- + sale cost in sale month
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.owner_monthly_schedule
WHERE ABS(
    owner_monthly_unrecoverable_cost
    - (
        COALESCE(mortgage_interest, 0)
        + COALESCE(maintenance_cost, 0)
        + COALESCE(property_cost, 0)
        + COALESCE(insurance_cost, 0)
        + CASE WHEN month_number = 0
               THEN COALESCE(purchase_cost, 0)
               ELSE 0 END
        + CASE WHEN is_sale_month
               THEN COALESCE(sale_cost, 0)
               ELSE 0 END
      )
) > 0.01;


-- =========================================================
-- B5. OWNER NET WORTH FORMULA
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.owner_monthly_schedule
WHERE ABS(
    owner_net_worth
    - (
        house_price_market
        - mortgage_balance
        - estimated_current_sale_cost
      )
) > 0.01;


-- =========================================================
-- C1. RENTER ROW COUNT RECONCILIATION
--
-- Current model has one renter-discipline value (1.00)
-- and one copy per investment portfolio.
-- Expected renter rows = owner monthly rows * portfolio count.
-- =========================================================
SELECT
    (SELECT COUNT(*) FROM simulation.owner_monthly_schedule)
        *
    (SELECT COUNT(*) FROM simulation.investment_assumptions)
        AS expected_renter_rows,

    (SELECT COUNT(*) FROM simulation.renter_monthly_schedule)
        AS actual_renter_rows,

    (SELECT COUNT(*) FROM simulation.renter_monthly_schedule)
    -
    (
        (SELECT COUNT(*) FROM simulation.owner_monthly_schedule)
        *
        (SELECT COUNT(*) FROM simulation.investment_assumptions)
    ) AS row_difference;


-- =========================================================
-- C2. RENTER ROW / SCENARIO KEY CHECKS
--
-- renter_scenario_id is a row-level BIGSERIAL PRIMARY KEY.
-- The scenario-level natural key is:
--   owner_scenario_id + date_period + portfolio_name + discipline
-- Expected duplicate groups = 0.
-- =========================================================
SELECT
    COUNT(*) AS duplicate_groups
FROM (
    SELECT
        owner_scenario_id,
        date_period,
        portfolio_name,
        renter_discipline
    FROM simulation.renter_monthly_schedule
    GROUP BY
        owner_scenario_id,
        date_period,
        portfolio_name,
        renter_discipline
    HAVING COUNT(*) > 1
) AS d;


-- =========================================================
-- C3. EACH RENTER SCENARIO MUST MATCH OWNER MONTH COUNT
-- Expected: mismatch_count = 0
-- =========================================================
WITH owner_counts AS (
    SELECT
        scenario_id,
        COUNT(*) AS owner_rows
    FROM simulation.owner_monthly_schedule
    GROUP BY scenario_id
),
renter_counts AS (
    SELECT
        owner_scenario_id,
        portfolio_name,
        renter_discipline,
        COUNT(*) AS renter_rows,
        MIN(month_number) AS min_month,
        MAX(month_number) AS max_month,
        COUNT(DISTINCT month_number) AS distinct_months
    FROM simulation.renter_monthly_schedule
    GROUP BY
        owner_scenario_id,
        portfolio_name,
        renter_discipline
)
SELECT
    COUNT(*) AS mismatch_count
FROM renter_counts AS r
JOIN owner_counts AS o
    ON o.scenario_id = r.owner_scenario_id
WHERE r.renter_rows <> o.owner_rows
   OR r.min_month <> 0
   OR r.distinct_months <> r.renter_rows
   OR r.max_month <> r.renter_rows - 1;


-- =========================================================
-- C4. RENTER COPIED OWNER VALUES
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.renter_monthly_schedule AS r
JOIN simulation.owner_monthly_schedule AS o
    ON o.scenario_id = r.owner_scenario_id
   AND o.date_period = r.date_period
WHERE r.month_number <> o.month_number
   OR r.city IS DISTINCT FROM o.city
   OR r.buying_date IS DISTINCT FROM o.buying_date
   OR r.sold_date IS DISTINCT FROM o.sold_date
   OR ABS(COALESCE(r.house_price_market, 0) - COALESCE(o.house_price_market, 0)) > 0.01
   OR ABS(COALESCE(r.owner_net_worth, 0) - COALESCE(o.owner_net_worth, 0)) > 0.01
   OR ABS(COALESCE(r.mortgage_balance, 0) - COALESCE(o.mortgage_balance, 0)) > 0.01;


-- =========================================================
-- C5. RENT JOIN COVERAGE
-- Expected: missing_market_rent = 0
-- =========================================================
SELECT
    COUNT(*) FILTER (WHERE market_rent IS NULL) AS missing_market_rent,
    COUNT(*) FILTER (WHERE market_rent <= 0) AS non_positive_market_rent
FROM simulation.renter_monthly_schedule;


-- =========================================================
-- C6. INITIAL RENTER INVESTMENT FORMULA
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.renter_monthly_schedule
WHERE ABS(
    initial_renter_investment
    - (COALESCE(down_payment, 0) + COALESCE(purchase_cost, 0))
) > 0.01;


-- =========================================================
-- C7. RENTER POLICY / INVESTMENT ASSUMPTION COPIES
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.renter_monthly_schedule AS r
JOIN simulation.renter_policy_assumptions AS p
    ON p.city = r.city
JOIN simulation.investment_assumptions AS i
    ON i.portfolio_name = r.portfolio_name
WHERE r.rent_growth_mode IS DISTINCT FROM p.rent_growth_mode
   OR r.rent_control_rate IS DISTINCT FROM p.rent_control_rate
   OR ABS(r.annual_move_probability - p.annual_move_probability) > 0.0000001
   OR ABS(r.move_cost_multiplier - p.move_cost_multiplier) > 0.0000001
   OR ABS(r.investment_fee - i.investment_fee) > 0.0000001
   OR ABS(r.tax_drag - i.tax_drag) > 0.0000001;


-- =========================================================
-- C8. MONTHLY PROBABILITY / INVESTMENT COST FORMULAS
-- Checks the formulas currently implemented in the SQL model.
-- Expected: mismatch counts = 0
-- =========================================================
SELECT
    COUNT(*) FILTER (
        WHERE ABS(
            monthly_move_probability
            - annual_move_probability / 12.0
        ) > 0.0000001
    ) AS monthly_move_probability_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            monthly_investment_cost
            - (investment_fee + tax_drag) / 12.0
        ) > 0.0000001
    ) AS monthly_investment_cost_mismatch
FROM simulation.renter_monthly_schedule;


-- =========================================================
-- C9. COMMON RANDOM NUMBER / SEED CONSISTENCY CHECK
--
-- Current Python resets RNG to seed 42 for every renter scenario.
-- Therefore the same elapsed month should receive the same
-- random draw across comparable scenarios.
--
-- Expected:
--   months_with_multiple_random_draws = 0
--   null_random_rows = 0 after renter Python finishes
-- =========================================================
WITH per_month AS (
    SELECT
        month_number,
        COUNT(DISTINCT ROUND(random_move, 12))
            FILTER (WHERE random_move IS NOT NULL)
            AS distinct_random_draws,
        COUNT(*) FILTER (WHERE random_move IS NULL) AS null_random_rows
    FROM simulation.renter_monthly_schedule
    GROUP BY month_number
)
SELECT
    COUNT(*) FILTER (
        WHERE distinct_random_draws > 1
    ) AS months_with_multiple_random_draws,
    SUM(null_random_rows) AS null_random_rows
FROM per_month;


-- =========================================================
-- C10. RENTER MOVE LOGIC
-- Month 0 must never move.
-- Other months: renter_moves = random_move < monthly probability.
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.renter_monthly_schedule
WHERE
    (month_number = 0 AND COALESCE(renter_moves, FALSE) <> FALSE)
    OR
    (
        month_number > 0
        AND renter_moves IS DISTINCT FROM
            (random_move < monthly_move_probability)
    );


-- =========================================================
-- C11. MOVE COST / RENTER CASH FLOW / SAVINGS FORMULAS
-- Expected: all mismatch counts = 0
-- =========================================================
SELECT
    COUNT(*) FILTER (
        WHERE ABS(
            move_cost
            - CASE
                WHEN renter_moves
                    THEN actual_renter_rent * move_cost_multiplier
                ELSE 0
              END
        ) > 0.01
    ) AS move_cost_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            renter_total_cash_outflow
            - (actual_renter_rent + move_cost)
        ) > 0.01
    ) AS renter_cash_outflow_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            monthly_savings_difference
            - (owner_total_cash_outflow - renter_total_cash_outflow)
        ) > 0.01
    ) AS monthly_savings_difference_mismatch
FROM simulation.renter_monthly_schedule;


-- =========================================================
-- C12. OWNER TOTAL CASH OUTFLOW COPIED INTO RENTER MODEL
--
-- This intentionally excludes purchase/sale transaction costs.
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.renter_monthly_schedule
WHERE ABS(
    owner_total_cash_outflow
    - (
        COALESCE(mortgage_payment, 0)
        + COALESCE(maintenance_cost, 0)
        + COALESCE(property_cost, 0)
        + COALESCE(insurance_cost, 0)
      )
) > 0.01;


-- =========================================================
-- C13. RENTER MONTHLY INVESTMENT RULE
--
-- Month 0: 0 (initial investment already seeded)
-- Positive savings: savings * discipline
-- Negative savings: withdraw full shortfall
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.renter_monthly_schedule
WHERE ABS(
    renter_monthly_investment
    - CASE
        WHEN month_number = 0 THEN 0
        WHEN monthly_savings_difference >= 0
            THEN monthly_savings_difference * renter_discipline
        ELSE monthly_savings_difference
      END
) > 0.01;


-- =========================================================
-- C14. PORTFOLIO RETURN SELECTION + NET RETURN
-- Expected: mismatch counts = 0
-- =========================================================
SELECT
    COUNT(*) FILTER (
        WHERE ABS(
            portfolio_return
            - CASE
                WHEN portfolio_name = 'sp500_only' THEN sp500_return
                WHEN portfolio_name = 'tsx_only' THEN tsx_return
              END
        ) > 0.0000001
    ) AS selected_return_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(
            portfolio_return_net
            - (portfolio_return - monthly_investment_cost)
        ) > 0.0000001
    ) AS net_return_mismatch,

    COUNT(*) FILTER (
        WHERE month_number = 0
          AND (
                ABS(COALESCE(sp500_return, 0)) > 0.0000001
             OR ABS(COALESCE(tsx_return, 0)) > 0.0000001
             OR ABS(COALESCE(portfolio_return, 0)) > 0.0000001
             OR ABS(COALESCE(portfolio_return_net, 0)) > 0.0000001
          )
    ) AS month0_return_not_zero
FROM simulation.renter_monthly_schedule;


-- =========================================================
-- C15. RENTER NET WORTH IDENTITY
-- Expected: mismatch_count = 0
-- =========================================================
SELECT
    COUNT(*) AS mismatch_count
FROM simulation.renter_monthly_schedule
WHERE ABS(renter_net_worth - renter_portfolio_value) > 0.01;


-- =========================================================
-- D1. DEEP CHECK: MORTGAGE BALANCE RECURSION
-- Heavier query on the owner monthly table.
--
-- current balance = previous balance - current principal
-- Expected: mismatch_count = 0
-- =========================================================
WITH x AS (
    SELECT
        scenario_id,
        month_number,
        mortgage_balance,
        mortgage_principal,
        LAG(mortgage_balance) OVER (
            PARTITION BY scenario_id
            ORDER BY month_number
        ) AS previous_balance
    FROM simulation.owner_monthly_schedule
)
SELECT
    COUNT(*) AS mismatch_count
FROM x
WHERE month_number > 0
  AND ABS(
        mortgage_balance
        - GREATEST(previous_balance - mortgage_principal, 0)
      ) > 0.01;


-- =========================================================
-- D2. DEEP CHECK: MORTGAGE INTEREST VS STORED APPLIED RATE
--
-- This check is especially useful for detecting an off-by-one
-- mortgage-term-rate assignment.
-- Expected: mismatch_count = 0 after term-number fix.
-- =========================================================
WITH x AS (
    SELECT
        scenario_id,
        month_number,
        applied_mortgage_rate,
        mortgage_interest,
        LAG(mortgage_balance) OVER (
            PARTITION BY scenario_id
            ORDER BY month_number
        ) AS previous_balance
    FROM simulation.owner_monthly_schedule
)
SELECT
    COUNT(*) AS mismatch_count
FROM x
WHERE month_number > 0
  AND previous_balance > 0
  AND ABS(
        mortgage_interest
        - previous_balance * applied_mortgage_rate / 100 / 12
      ) > 0.02;


-- =========================================================
-- D3. DEEP CHECK: CUMULATIVE UNRECOVERABLE COST
-- Expected: mismatch_count = 0
-- =========================================================
WITH x AS (
    SELECT
        scenario_id,
        month_number,
        cumulative_unrecoverable_cost,
        SUM(owner_monthly_unrecoverable_cost) OVER (
            PARTITION BY scenario_id
            ORDER BY month_number
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS expected_cumulative_cost
    FROM simulation.owner_monthly_schedule
)
SELECT
    COUNT(*) AS mismatch_count
FROM x
WHERE ABS(
    cumulative_unrecoverable_cost - expected_cumulative_cost
) > 0.02;


-- =========================================================
-- D4. DEEP CHECK: ACTUAL RENTER RENT RECURSION
--
-- Current Python behaviour:
--   month 0               -> market rent
--   market mode           -> market rent
--   move month            -> market rent
--   missing control rate  -> market rent
--   otherwise             -> min(previous rent * (1 + rate/12), market rent)
--
-- Expected: mismatch_count = 0
-- =========================================================
WITH x AS (
    SELECT
        *,
        LAG(actual_renter_rent) OVER (
            PARTITION BY
                owner_scenario_id,
                portfolio_name,
                renter_discipline
            ORDER BY month_number
        ) AS previous_actual_rent
    FROM simulation.renter_monthly_schedule
)
SELECT
    COUNT(*) AS mismatch_count
FROM x
WHERE ABS(
    actual_renter_rent
    - CASE
        WHEN month_number = 0
            THEN market_rent
        WHEN rent_growth_mode = 'market'
            THEN market_rent
        WHEN renter_moves
            THEN market_rent
        WHEN rent_control_rate IS NULL
            THEN market_rent
        ELSE LEAST(
            previous_actual_rent * (1 + rent_control_rate / 12.0),
            market_rent
        )
      END
) > 0.02;


-- =========================================================
-- D5. DEEP CHECK: RENTER PORTFOLIO RECURSION
--
-- Month 0 = initial renter investment
-- Month t = max(previous portfolio * (1 + net return)
--               + monthly investment, 0)
-- Expected: mismatch_count = 0
-- =========================================================
WITH x AS (
    SELECT
        *,
        LAG(renter_portfolio_value) OVER (
            PARTITION BY
                owner_scenario_id,
                portfolio_name,
                renter_discipline
            ORDER BY month_number
        ) AS previous_portfolio_value
    FROM simulation.renter_monthly_schedule
)
SELECT
    COUNT(*) AS mismatch_count
FROM x
WHERE ABS(
    renter_portfolio_value
    - CASE
        WHEN month_number = 0
            THEN GREATEST(initial_renter_investment, 0)
        ELSE GREATEST(
            previous_portfolio_value * (1 + portfolio_return_net)
            + renter_monthly_investment,
            0
        )
      END
) > 0.02;


-- =========================================================
-- D6. DEEP CHECK: REAL NET WORTH + INDEXES
--
-- Each renter scenario uses its month-0 CPI as the base.
-- Expected: mismatch counts = 0
-- =========================================================
WITH base AS (
    SELECT
        r.*,
        c.cpi_value,
        FIRST_VALUE(c.cpi_value) OVER (
            PARTITION BY
                r.owner_scenario_id,
                r.portfolio_name,
                r.renter_discipline
            ORDER BY r.month_number
        ) AS starting_cpi
    FROM simulation.renter_monthly_schedule AS r
    LEFT JOIN stg.canada_cpi AS c
        ON c.date_period = r.date_period
),
real_values AS (
    SELECT
        *,
        owner_net_worth * starting_cpi / cpi_value
            AS expected_owner_real,
        renter_net_worth * starting_cpi / cpi_value
            AS expected_renter_real
    FROM base
),
indexed AS (
    SELECT
        *,
        FIRST_VALUE(expected_owner_real) OVER (
            PARTITION BY
                owner_scenario_id,
                portfolio_name,
                renter_discipline
            ORDER BY month_number
        ) AS starting_owner_real,
        FIRST_VALUE(expected_renter_real) OVER (
            PARTITION BY
                owner_scenario_id,
                portfolio_name,
                renter_discipline
            ORDER BY month_number
        ) AS starting_renter_real
    FROM real_values
)
SELECT
    COUNT(*) FILTER (
        WHERE cpi_value IS NULL OR cpi_value <= 0
    ) AS invalid_cpi_rows,

    COUNT(*) FILTER (
        WHERE ABS(owner_net_worth_real - expected_owner_real) > 0.02
    ) AS owner_real_mismatch,

    COUNT(*) FILTER (
        WHERE ABS(renter_net_worth_real - expected_renter_real) > 0.02
    ) AS renter_real_mismatch,

    COUNT(*) FILTER (
        WHERE
            (
                ABS(starting_owner_real) > 0.000001
                AND ABS(
                    owner_net_worth_index
                    - expected_owner_real / starting_owner_real * 100
                ) > 0.001
            )
            OR
            (
                ABS(starting_owner_real) <= 0.000001
                AND owner_net_worth_index IS NOT NULL
            )
    ) AS owner_index_mismatch,

    COUNT(*) FILTER (
        WHERE
            (
                ABS(starting_renter_real) > 0.000001
                AND ABS(
                    renter_net_worth_index
                    - expected_renter_real / starting_renter_real * 100
                ) > 0.001
            )
            OR
            (
                ABS(starting_renter_real) <= 0.000001
                AND renter_net_worth_index IS NOT NULL
            )
    ) AS renter_index_mismatch
FROM indexed;


-- =========================================================
-- E1. RENT SOURCE YEAR UNIQUENESS
--
-- Renter construction joins market rent by city + YEAR only.
-- Therefore analysis.city_rent_long must have at most one row
-- per city/year, otherwise the renter insert can duplicate rows.
-- Expected: duplicate_city_years = 0
-- =========================================================
SELECT
    COUNT(*) AS duplicate_city_years
FROM (
    SELECT
        city,
        EXTRACT(YEAR FROM date_period)::INTEGER AS rent_year,
        COUNT(*) AS row_count
    FROM analysis.city_rent_long
    GROUP BY
        city,
        EXTRACT(YEAR FROM date_period)::INTEGER
    HAVING COUNT(*) > 1
) AS d;


-- =========================================================
-- E2. MONTHLY MOVE PROBABILITY DIAGNOSTIC
--
-- Current implementation uses annual_probability / 12.
-- The exact monthly probability giving the stated annual
-- probability would be:
--   1 - (1 - annual_probability)^(1/12)
--
-- This query shows the difference; informational only.
-- =========================================================
SELECT
    city,
    annual_move_probability,
    annual_move_probability / 12.0 AS current_monthly_probability,
    1 - POWER(1 - annual_move_probability, 1.0 / 12.0)
        AS exact_equivalent_monthly_probability,
    1 - POWER(
        1 - annual_move_probability / 12.0,
        12
    ) AS implied_annual_probability_from_current_method
FROM simulation.renter_policy_assumptions
ORDER BY city;


-- =========================================================
-- E3. RENT-CONTROL COMPOUNDING DIAGNOSTIC
--
-- Current Python applies rent_control_rate / 12 each month.
-- This compounds to slightly more than the annual rate.
-- Informational only.
-- =========================================================
SELECT
    city,
    rent_control_rate,
    CASE
        WHEN rent_control_rate IS NULL THEN NULL
        ELSE POWER(1 + rent_control_rate / 12.0, 12) - 1
    END AS implied_annual_growth_from_monthly_compounding
FROM simulation.renter_policy_assumptions
ORDER BY city;


-- =========================================================
-- E4. PORTFOLIO FLOOR-AT-ZERO DIAGNOSTIC
-- Informational: frequent hits may make the no-debt assumption material.
-- =========================================================
SELECT
    COUNT(*) FILTER (
        WHERE renter_portfolio_value = 0
    ) AS zero_portfolio_rows,
    COUNT(DISTINCT owner_scenario_id) FILTER (
        WHERE renter_portfolio_value = 0
    ) AS owner_scenarios_ever_hitting_zero
FROM simulation.renter_monthly_schedule;

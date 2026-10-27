## Validation / Testing

Validation is organized by pipeline layer so that each stage addresses a different question: **Was the source loaded correctly? Was it cleaned and standardized correctly? Were the analytical transformations calculated correctly? And does the monthly simulation behave according to the model rules?**

### 1. Raw-layer validation

The raw layer is treated as a source-ingestion layer, so validation focuses on confirming that source data were loaded without introducing structural problems.

Checks include:

- Row counts for each source table.
- Missing or blank natural keys, such as date, city, or series identifiers.
- Duplicate natural keys, including date-level and city-date combinations where applicable.
- Source, city, and period coverage checks to identify unexpected gaps.
- Detailed duplicate queries for investigating issues identified by the summary checks.

Parsing, numeric conversion, and business-rule validation are intentionally deferred to later pipeline layers.

### 2. Staging-layer validation

The staging layer converts raw fields into analysis-ready dates and numeric values, standardizes table structures, and pivots selected city-level datasets into wide-format tables.

Validation focuses on confirming that these cleaning and restructuring steps were completed correctly.

Checks include:

- Raw-to-staging row-count reconciliation.
- Transformation-aware reconciliation for tables that are pivoted from long to wide format.
- Date-range and distinct-date coverage.
- NULL and duplicate `date_period` checks.
- NULL and non-positive checks for key numeric fields such as prices, index levels, CPI, FX rates, and mortgage rates.
- City-level availability checks for wide housing-price and rent tables.
- Monthly date-alignment checks for datasets expected to use month-start dates.

For transformed tables, expected row counts are determined by the transformation logic rather than requiring raw and staging tables to contain identical numbers of rows.

### 3. Analysis-layer validation

The analysis layer creates the derived measures used by the simulation and Power BI reporting. Validation therefore focuses on both structural integrity and formula consistency.

Checks include:

- Row counts, date coverage, NULL natural keys, and duplicate natural keys.
- Reconciliation between staging inputs and direct analysis outputs.
- Independent recalculation of S&P 500 and VT USD-to-CAD conversions using the applicable USD/CAD exchange rate.
- Independent recalculation of CPI-adjusted real values for the S&P 500, TSX, and VT.
- Validation that rebased indexes equal 100 at their intended base observations.
- Wide-to-long row-count reconciliation for city housing-price and rent tables.
- Validation of the expected city lists after reshaping.
- CAGR structural checks, including allowable holding periods, start and end dates, and required source values.
- Independent recalculation of CAGR values:

\[
CAGR
=
\left(
\frac{Ending\ Value}{Starting\ Value}
\right)^{1/n}
-1
\]

- Reconciliation between the expected and actual numbers of valid CAGR observations.
- Integrity and row-count checks for the combined housing and stock CAGR comparison table.
- Diagnostic testing for date-alignment issues between staging and analysis tables.

Rather than only checking whether derived fields are populated, the analysis tests independently recompute key transformations and compare them with the stored results.

### 4. Simulation-layer validation

The simulation layer receives the most detailed validation because both the homeowner and renter models are **stateful**: values in the current month depend on values calculated in previous months.

#### Owner simulation

Each homeowner scenario is checked for structural completeness and financial consistency.

Key tests include:

- Expected number of monthly rows based on the scenario holding period.
- Scenario start at Month 0 and continuous monthly sequencing.
- Correct purchase and sale timing.
- Correct mortgage-term alignment, with renewal periods beginning at Months 61, 121, and subsequent five-year intervals.
- Non-negative mortgage payments, interest, principal, and mortgage balances.
- Month 0 initialization of the mortgage balance.
- Mortgage payment identity:

\[
Mortgage\ Payment
=
Interest + Principal
\]

- Monthly mortgage-balance recursion:

\[
Balance_t
=
\max
\left(
Balance_{t-1} - Principal_t,\ 0
\right)
\]

- Independent recalculation of mortgage interest using the previous mortgage balance and the applicable mortgage rate.
- Monthly unrecoverable ownership-cost calculation:

\[
Unrecoverable\ Cost
=
Interest
+
Maintenance
+
Property\ Tax
+
Insurance
+
Applicable\ Transaction\ Costs
\]

where purchase cost is added in Month 0 and sale cost is added in the sale month.

- Homeowner net-worth calculation:

\[
Owner\ Net\ Worth
=
Current\ House\ Value
-
Remaining\ Mortgage
-
Estimated\ Selling\ Cost
\]

- Recalculation of cumulative unrecoverable ownership costs.

These checks also help identify timing errors, such as an off-by-one mortgage-term or mortgage-rate assignment.

#### Renter simulation

The renter model is validated against both its corresponding homeowner scenario and the renter-specific policy and investment assumptions.

Key tests include:

- Row-count reconciliation between renter scenarios, homeowner scenarios, and portfolio assumptions.
- Uniqueness and completeness of renter scenario-month records.
- Verification that homeowner values copied into the renter schedule match the corresponding homeowner scenario.
- Market-rent availability and positive-value checks.
- Initial renter investment:

\[
Initial\ Renter\ Investment
=
Owner\ Down\ Payment
+
Owner\ Purchase\ Cost
\]

- Verification that rent-policy and investment assumptions are copied correctly into each scenario.
- Validation of the implemented monthly move-probability and investment-cost formulas.
- Reproducible random moving behavior using a fixed seed and common random draws across comparable scenarios.
- Verification that the same elapsed month receives the same underlying random draw across scenarios.
- Move-event logic:

\[
Move_t
=
RandomDraw_t
<
MonthlyMoveProbability_t
\]

with Month 0 explicitly prevented from being a move month.

- Rent recursion, including rent-control growth and resetting actual rent to market rent after a move.
- Moving-cost calculation:

\[
Moving\ Cost
=
Actual\ Rent
\times
Move\ Cost\ Multiplier
\]

when a move occurs.

- Renter monthly housing cash outflow:

\[
Renter\ Cash\ Outflow
=
Actual\ Rent
+
Moving\ Cost
\]

- Owner-versus-renter monthly cash-flow difference:

\[
Savings\ Difference
=
Owner\ Cash\ Outflow
-
Renter\ Cash\ Outflow
\]

- Investment-discipline rules: positive monthly savings are invested according to the renter-discipline assumption, while negative differences are fully withdrawn from the portfolio.
- Correct selection of the TSX or S&P 500 monthly return.
- Deduction of monthly investment costs from the selected portfolio return.
- Month 0 return initialization at zero.
- Monthly portfolio recursion:

\[
Portfolio_t
=
\max
\left[
Portfolio_{t-1}(1+r_t)
+
Contribution_t,\ 0
\right]
\]

- Verification that renter net worth equals renter portfolio value.
- CPI-based conversion of homeowner and renter nominal net worth into real net worth.
- Validation of indexed real net worth relative to each scenario's starting real net worth.

### 5. Reproducibility and model diagnostics

Because renter moves are probabilistic, the simulation uses a fixed random seed. Each comparable scenario receives the same underlying random draw for the same elapsed month.

This common-random-number approach reduces random noise in sensitivity comparisons. Differences between mortgage-rate, portfolio, holding-period, or other scenarios are therefore less likely to be driven by different random moving histories.

The validation framework also includes several diagnostic checks for modeling assumptions rather than coding errors:

- The current move-probability implementation uses annual move probability divided by 12 and compares it with the exact monthly probability implied by the annual rate.
- The current rent-control implementation applies the annual control rate divided by 12 each month; a diagnostic reports the annual growth implied by monthly compounding.
- The renter portfolio is floored at zero, so an additional diagnostic identifies how often scenarios reach a zero portfolio balance.

These diagnostics make the simplifying assumptions visible and help assess whether they materially affect the results.

### Validation criteria

Most integrity and formula checks are designed so that a successful result produces **zero missing-key violations, zero duplicate groups, zero structural mismatches, or zero formula mismatches**, subject to small numerical tolerances where appropriate.

Coverage and diagnostic checks are interpreted separately because differences in historical data availability or simplifying model assumptions do not necessarily indicate data or coding errors.

Together, the validation framework covers the full pipeline:

**Raw ingestion → Staging and cleaning → Analytical transformations → Monthly financial simulation**

This provides a traceable testing structure from source data through to the final rent-versus-buy simulation outputs.
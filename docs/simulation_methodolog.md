# Simulation Methodology: Rent vs Buy Model

**Project:** Rent vs Buy in Canada  
**Scope:** Monthly homeowner and renter-investor simulation methodology

---

## 1. Purpose of the Simulation

This document describes the simulation methodology used in the **Rent vs Buy in Canada** project.

The model compares two long-term household wealth-building strategies under historical Canadian market conditions:

1. **Homeowner strategy** — purchase a home, finance it with a mortgage, pay recurring ownership costs, and accumulate housing equity.
2. **Renter-investor strategy** — rent instead of buying, invest the capital that would otherwise have been used for the home purchase, and invest or withdraw the monthly cash-flow difference between renting and owning.

The objective is not to compare rent with a mortgage payment in isolation. A mortgage payment contains both **interest**, which is a financing cost, and **principal**, which reduces debt and increases homeowner equity.

Similarly, renting is not modeled as consumption only. The renter begins with the same initial capital as the homeowner and invests monthly savings when renting requires less cash than owning.

The simulation therefore evaluates the full household balance-sheet effect of both strategies over time.

---

## 2. Model Architecture

The simulation is implemented across PostgreSQL, Python, and Power BI.

```text
PostgreSQL analysis inputs
↓
Owner scenario generation
↓
Owner monthly schedule
↓
Python mortgage engine
↓
Renter scenario generation
↓
Python renter / portfolio engine
↓
Inflation-adjusted owner and renter net worth
↓
Power BI reporting and sensitivity analysis
```

### 2.1 Division of responsibility

| Tool | Role |
|---|---|
| **PostgreSQL** | Stores assumptions and market data, generates owner/renter scenarios, creates monthly schedules, and stores simulation outputs |
| **Python** | Performs state-dependent monthly calculations such as mortgage amortization, rent-path simulation, renter mobility, portfolio compounding, and real-net-worth calculation |
| **Power BI** | Filters scenarios, calculates reporting measures, compares final outcomes, and visualizes sensitivity results |

Power BI does not recreate the core financial simulation. It consumes the calculated simulation outputs.

---

## 3. Core Comparison Principle

The model is built around one question:

> If two households begin with the same initial capital, and one buys while the other rents and invests, which strategy produces greater inflation-adjusted net worth over the selected holding period?

The comparison is designed around **equal starting capital**.

At month 0:

```text
Owner Initial Capital = Down Payment + Purchase Cost
```

The renter begins with:

```text
Initial Renter Investment = Owner Down Payment + Owner Purchase Cost
```

This ensures that the renter is not given less starting capital simply because they do not purchase a home.

After month 0, the model compares the two households' monthly cash requirements.

```text
Monthly Savings Difference = Owner Total Cash Outflow − Renter Total Cash Outflow
```

If the difference is positive, the renter invests the savings. If the difference is negative, the renter withdraws the shortfall from the investment portfolio.

---

## 4. Final Reporting Scope

The underlying database supports more scenarios than the final report uses.

### 4.1 Final sensitivity dimensions

The final analysis varies:

- **City**
- **Purchase year**
- **Holding period**
- **Mortgage-rate scenario**
- **Renter investment portfolio**

### 4.2 Fixed reporting assumptions

The final report fixes:

```text
Down Payment = 20%
Renter Discipline = 100%
```

This is an intentional modeling choice.

The database retains 10%, 20%, and 30% down-payment scenarios, but the final report does not compare them directly. Different down-payment levels require different amounts of initial capital, which makes cross-down-payment comparisons more difficult to interpret.

Holding down payment constant at 20% keeps the starting-capital framework consistent.

Likewise, the final report assumes full renter investment discipline rather than treating discipline as a sensitivity variable.

---

## 5. Geography and Historical Scope

The model covers seven Canadian markets:

- Canada
- Vancouver
- Calgary
- Edmonton
- Toronto
- Ottawa
- Montreal

The simulation is based on historical source data through:

```text
2025-12-01
```

Holding periods supported by the simulation framework are:

```text
5 years
10 years
15 years
20 years
```

Only scenarios supported by the available historical data should be interpreted as completed historical outcomes.

### 5.1 Scenario coverage is uneven across holding periods

A scenario exists only where both a purchase-month price and a matching sale-month price are available. City-level benchmark prices begin in **January 2005**, so the number of possible purchase months shrinks as the holding period lengthens:

| Holding period | Purchase months available | Purchase years spanned |
|---|---:|---|
| 5 years | ~190 | 2005 – 2020 |
| 10 years | ~130 | 2005 – 2015 |
| 15 years | ~70 | 2005 – 2010 |
| **20 years** | **~12** | **2005 only** |

This has direct consequences for how results should be read.

**The 20-year results describe a single purchase year.** Every completed 20-year scenario begins in 2005. Whatever those scenarios show is the outcome of one specific entry point into the housing cycle, not evidence about 20-year horizons in general. It should be presented as a case study of the 2005 cohort rather than as a peer of the 5-year results.

**Sample sizes differ by more than an order of magnitude.** The 5-year bucket draws on roughly sixteen years of entry points spanning several distinct market regimes; the 20-year bucket draws on one. Averages taken across holding periods are therefore not comparable in statistical weight, and a chart placing 5-year and 20-year results side by side without noting this invites the reader to over-interpret the longest horizon.

**Purchase-year composition varies by holding period.** Because longer horizons are available only for earlier purchase years, holding period and purchase year are structurally correlated in the dataset. Any apparent "longer horizons do better" pattern may partly reflect that longer horizons are only observable for households who bought before the 2006–2021 run-up, rather than any effect of duration itself.

Reporting should therefore either display scenario counts alongside aggregates, or restrict cross-holding-period comparisons to purchase years where all four horizons are observable.

---

## 6. Homeowner Model

### 6.1 Core homeowner assumptions

| Variable | Assumption |
|---|---:|
| Final-report down payment | 20% |
| Mortgage term | 5 years |
| Amortization | 25 years |
| Purchase cost | 2% of purchase price |
| Sale cost | 6% of market value |
| Maintenance | 1.5% of structure value per year |
| Insurance | 0.3% of house market value per year |
| Property tax | City-specific |
| Mortgage rate | Historical 5-year benchmark with ±2 percentage-point sensitivity |

The broader database also contains 10% and 30% down-payment scenarios.

For the 10% down-payment scenario, the current model applies a mortgage-insurance rate of 3.1%. Mortgage insurance is zero for the 20% and 30% scenarios.

---

## 7. Purchase Price and Initial Mortgage

The home purchase price is taken from the historical city-level benchmark-price series for the selected purchase month.

For a 20% down-payment scenario:

```text
Down Payment = Purchase Price × 20%
```

Before mortgage insurance:

```text
Initial Loan Before Insurance = Purchase Price − Down Payment
```

For the final 20% down-payment analysis, mortgage insurance is zero, so:

```text
Initial Loan After Insurance = Initial Loan Before Insurance
```

The renter receives the same initial-capital amount:

```text
Initial Renter Investment = Down Payment + Purchase Cost
```

Under the final-report assumptions:

```text
Initial Renter Investment = 20% of Purchase Price + 2% of Purchase Price = 22% of Purchase Price
```

---

## 8. Mortgage Rate Assignment

The model uses historical Canadian 5-year mortgage-rate observations.

At the beginning of each mortgage term, the model identifies the latest available historical 5-year mortgage rate on or before the renewal date.

Three rate scenarios are retained:

| Scenario | Applied adjustment |
|---|---:|
| **Lower** | Historical rate − 2 percentage points |
| **Base** | Historical rate |
| **Higher** | Historical rate + 2 percentage points |

The applied mortgage rate is floored at zero:

```text
Applied Mortgage Rate = MAX(Historical Rate + Scenario Adjustment, 0)
```

These scenarios are sensitivity tests rather than forecasts.


### 8.1 Interpretation of the historical mortgage series

The underlying mortgage-rate source represents a conventional posted/typical 5-year mortgage-rate benchmark rather than a borrower-specific negotiated contract rate.

Actual borrower rates may differ from the benchmark, and the spread between posted and negotiated rates can vary over time.

Therefore:

- the **Base** scenario should be interpreted as a standardized historical benchmark;
- the **Lower (−2pp)** scenario remains a sensitivity case rather than a calibrated estimate of actual discounted mortgage rates;
- the **Higher (+2pp)** scenario represents a financing-cost stress case relative to the same benchmark.

---

## 9. Mortgage Amortization

Mortgage amortization is calculated month by month in Python.

The model assumes:

```text
Mortgage Term = 5 years
Amortization = 25 years
```

### 9.1 Month 0

Month 0 represents the initial allocation point.

At month 0:

```text
Mortgage Payment = 0
Mortgage Interest = 0
Mortgage Principal = 0
Mortgage Balance = Initial Mortgage Balance
```

The first mortgage payment occurs in month 1.

### 9.2 Payment reset

The mortgage payment is calculated or recalculated at:

```text
Month 1
Month 61
Month 121
Month 181
...
```

At every 5-year renewal, the model uses the mortgage balance at that time, the new applied mortgage rate, and the remaining amortization period.

```text
Monthly Payment = Mortgage Balance × r / [1 − (1 + r)^(-n)]
```

where:

```text
r = Annual Applied Mortgage Rate / 100 / 12
n = Remaining Amortization Months
```

For a 0% mortgage rate:

```text
Monthly Payment = Mortgage Balance / Remaining Months
```

### 9.3 Mortgage interest

```text
Mortgage Interest = Beginning Mortgage Balance × Monthly Mortgage Rate
```

This is the financing-cost component of the mortgage payment.

### 9.4 Mortgage principal

Principal is derived through three successive bounds rather than a single subtraction:

```text
Actual Payment = MIN(Scheduled Payment, Beginning Balance + Interest)
Mortgage Principal = MAX(Actual Payment − Interest, 0)
Mortgage Principal = MIN(Mortgage Principal, Beginning Balance)
```

Each bound addresses a distinct edge case:

| Bound | Purpose |
|---|---|
| Payment capped at balance + interest | Prevents the final payment from exceeding the outstanding obligation |
| Principal floored at zero | Prevents negative principal when interest exceeds the scheduled payment |
| Principal capped at balance | Guarantees the balance terminates at exactly zero |

The balance then updates as:

```text
New Mortgage Balance = Beginning Mortgage Balance − Mortgage Principal
```

Together these ensure the mortgage cannot be overpaid and the balance cannot drift negative through accumulated floating-point error.

---

## 10. Ownership Costs

The homeowner model includes four recurring ownership-cost components:

```text
Mortgage Interest
Maintenance
Property Tax
Insurance
```

Mortgage principal is **not** classified as an unrecoverable cost because it reduces debt and becomes homeowner equity.

### 10.1 Maintenance

Maintenance is based on the estimated structure portion of the property rather than the full market value.

```text
Structure Value = House Market Value × Structure Ratio
```

```text
Monthly Maintenance = Structure Value × 1.5% ÷ 12
```

Current structure ratios are:

| City | Structure ratio |
|---|---:|
| Canada | 0.50 |
| Toronto | 0.45 |
| Vancouver | 0.35 |
| Calgary | 0.60 |
| Edmonton | 0.60 |
| Ottawa | 0.50 |
| Montreal | 0.50 |

The purpose of the structure ratio is to avoid applying maintenance costs to the land component of the property.

The current simulation does **not** separately deduct depreciation as an additional ownership cost.

### 10.2 Property tax

```text
Monthly Property Tax = House Market Value × Property Tax Rate ÷ 12
```

| City | Annual property-tax rate |
|---|---:|
| Canada | 1.00% |
| Toronto | 0.70% |
| Vancouver | 0.30% |
| Calgary | 0.70% |
| Edmonton | 1.00% |
| Ottawa | 1.20% |
| Montreal | 0.80% |

Because property tax is calculated from the simulated market value, the monthly amount changes as house prices change.

### 10.3 Insurance

```text
Monthly Insurance = House Market Value × 0.3% ÷ 12
```

Unlike maintenance, the current insurance calculation uses the full simulated house market value rather than the estimated structure value.

### 10.4 Purchase cost

```text
Purchase Cost = Purchase Price × 2%
```

It is added to homeowner unrecoverable cost in month 0 and is also included in the equal-starting-capital calculation for the renter.

### 10.5 Sale cost

```text
Sale Cost = House Market Value × 6%
```

Sale cost is included in the sale month when cumulative unrecoverable cost is tracked. The same 6% assumption is also used to estimate the cost of liquidating the house at any point in the scenario.

---

## 11. Owner Monthly Cash Outflow

Owner monthly cash outflow is different from owner unrecoverable cost.

The renter comparison uses the homeowner's actual monthly cash requirement:

```text
Owner Total Cash Outflow = Mortgage Payment + Maintenance + Property Tax + Insurance
```

The full mortgage payment is used here, including principal, because principal still requires cash from the homeowner each month.

```text
Cash-flow comparison → use full mortgage payment

Unrecoverable-cost analysis → use mortgage interest only
```

This distinction prevents mortgage principal from being incorrectly treated as a permanent economic loss while still recognizing its monthly liquidity requirement.

---

## 12. Owner Unrecoverable Cost

```text
Owner Monthly Unrecoverable Cost = Mortgage Interest + Maintenance + Property Tax + Insurance
```

Additional transaction costs are included as follows:

```text
Month 0 → add Purchase Cost

Sale Month → add Sale Cost
```

The model accumulates these expenses into `cumulative_unrecoverable_cost`.

Mortgage principal is excluded because it becomes homeowner equity.

---

## 13. Owner Net Worth

Owner nominal net worth is calculated as:

```text
Owner Net Worth = Current House Market Value − Remaining Mortgage Balance − Estimated Current Sale Cost
```

where:

```text
Estimated Current Sale Cost = Current House Market Value × 6%
```

This places homeowner wealth on a liquidation-equivalent basis: it estimates the amount the homeowner would retain if the house were sold at that point.

Cumulative unrecoverable cost is **not** subtracted again from owner net worth. Those expenses already affect household cash flow and the renter's monthly investment opportunity. Subtracting them again would double-count the same economic cost.

---

## 14. Renter-Investor Model

The renter simulation is linked directly to the corresponding owner scenario.

Each renter scenario inherits:

- city,
- purchase date,
- holding period,
- owner house-value path,
- owner mortgage schedule,
- owner total cash outflow,
- owner nominal net worth.

The renter scenario then adds:

- market rent,
- city-level rent rules,
- move probability,
- moving cost,
- investment portfolio,
- investment fees,
- tax drag,
- portfolio accumulation.

The final report compares two renter portfolios:

```text
TSX-only
S&P 500-only
```

A third global-equity series, the Vanguard Total World Stock ETF (VT), is loaded and processed into the analysis layer as `analysis.vt_cad_real`, with its own CAGR table. It is **not** offered as a renter portfolio in the simulation. VT's history begins in August 2008, which is too short to support the 15- and 20-year holding periods and would make cross-portfolio comparison uneven across purchase years. It is retained for supporting analysis only.

---

## 15. Rent Modeling

The model distinguishes `Market Rent` from `Actual Renter Rent`.

Market rent comes from the historical city-level rent data and is matched by:

```text
City + Calendar Year
```

Because the source rent series is annual, the corresponding market-rent observation is used across the months of that calendar year.

### 15.1 Rent-growth modes

| City | Growth mode | Rent-control rate | Annual move probability | Move-cost multiplier |
|---|---|---:|---:|---:|
| Canada | mixed | 2.0% | 10% | 1.2 |
| Toronto | controlled | 2.5% | 8% | 1.8 |
| Vancouver | controlled | 3.0% | 7% | 2.0 |
| Calgary | market | — | 15% | 1.2 |
| Edmonton | market | — | 15% | 1.1 |
| Ottawa | controlled | 2.5% | 9% | 1.4 |
| Montreal | controlled | 2.5% | 10% | 1.2 |

Current Python behavior is:

### Month 0

```text
Actual Rent = Market Rent
```

### Market mode

```text
Actual Rent = Market Rent
```

### Renter moves

```text
Actual Rent = Market Rent
```

### Otherwise

```text
Monthly Rent-Control Rate = Annual Rent-Control Rate / 12
```

```text
Actual Rent = Previous Actual Rent × (1 + Monthly Rent-Control Rate)
```

with:

```text
Actual Rent ≤ Market Rent
```

In the current implementation, any non-`market` mode follows this controlled-rent branch. Therefore, `mixed` is currently behaviorally equivalent to `controlled` and is retained for potential future extension.

---

## 16. Renter Mobility

The model includes renter moves because moving can reset a rent-controlled tenant to market rent and create additional relocation costs.

Moves are stochastic but reproducible.

```text
Random Seed = 42 + owner_scenario_id
```

A random number between 0 and 1 is generated for each month. The renter moves when:

```text
Random Number < Monthly Move Probability
```

Month 0 is always forced to no move.

Because the seed is based on the owner scenario, the TSX and S&P 500 renter variants linked to the same owner scenario experience the same move sequence.

### 16.1 Moving cost

```text
Move Cost = Actual Renter Rent × Move Cost Multiplier
```

If no move occurs, move cost is zero.

---

## 17. Renter Monthly Cash Outflow

```text
Renter Total Cash Outflow =  Renter Unrecoverable Cost = Actual Renter Rent + Move Cost
```

```text
Monthly Savings Difference = Owner Total Cash Outflow − Renter Total Cash Outflow
```

Interpretation:

```text
Positive difference → renter requires less cash than owner

Negative difference → renter requires more cash than owner
```

---

## 18. Renter Monthly Investment

The model carries a `renter_discipline` parameter representing the share of available monthly savings the renter actually invests. Contributions and withdrawals are treated asymmetrically:

```text
Savings Difference > 0 → Investment = Savings Difference × Renter Discipline
Savings Difference ≤ 0 → Investment = Savings Difference
```

Discipline scales contributions only. A shortfall must be funded in full regardless of discipline, because the renter has to meet the actual rent obligation whether or not they are a disciplined investor.

The final report fixes:

```text
Renter Discipline = 100%
```

At full discipline the two branches coincide, so the monthly investment equals the savings difference directly:

```text
Renter Monthly Investment = Monthly Savings Difference
```

A positive amount is a contribution; a negative amount is a withdrawal. The parameter is retained in the database so that partial-discipline scenarios can be added without restructuring the model.

### 18.1 Month 0 treatment

Month 0 is a special initial-capital allocation period.

The renter already starts with:

```text
Initial Renter Investment = Down Payment + Purchase Cost
```

Therefore:

```text
Month 0 Renter Monthly Investment = 0
```

Month 0 is treated as an initialization period. Although monthly owner and renter cash-flow fields are present, the renter portfolio does not apply the month-0 savings difference. Monthly portfolio contribution and withdrawal adjustments begin from month 1.

---

## 19. Renter Portfolio Returns

The final renter-investor comparison uses:

- TSX-only
- S&P 500-only

Monthly percentage returns are calculated from the corresponding CAD-denominated market series.

The S&P 500 is converted to CAD before monthly returns are calculated.

The simulation uses nominal market returns because the monthly cash-flow simulation itself is nominal.

### 19.1 Investment costs

| Portfolio | Annual investment fee | Annual tax drag |
|---|---:|---:|
| TSX-only | 0.10% | 0.10% |
| S&P 500-only | 0.10% | 0.25% |

```text
Monthly Investment Cost = (Annual Fee + Annual Tax Drag) / 12
```

```text
Portfolio Return Net = Portfolio Return − Monthly Investment Cost
```

These tax-drag assumptions are simplified portfolio-level assumptions rather than household-specific tax calculations.

---

## 20. Renter Portfolio Calculation

The renter begins with:

```text
Portfolio Value at Month 0 = Initial Renter Investment
```

No stock return is applied immediately in month 0.

From month 1 onward:

```text
New Portfolio Value = Previous Portfolio Value × (1 + Portfolio Return Net) + Renter Monthly Investment
```

Portfolio value is floored at zero.

```text
Renter Net Worth = Renter Portfolio Value
```

---

## 21. Nominal and Real Net Worth

The entire monthly simulation is performed in **nominal Canadian dollars**.

This keeps house prices, mortgage payments, rent, maintenance, property tax, insurance, monthly investments, and portfolio returns on one internally consistent basis.

Inflation adjustment is applied only after nominal owner and renter net worth have been calculated.

### 21.1 Real net worth

Each scenario uses its own starting-month CPI as the purchasing-power base.

```text
Owner Real Net Worth = Owner Nominal Net Worth × Starting CPI ÷ Current CPI
```

```text
Renter Real Net Worth = Renter Nominal Net Worth × Starting CPI ÷ Current CPI
```

The resulting fields are:

```text
owner_net_worth_real
renter_net_worth_real
```

These are the **primary wealth measures used in the final report**.

### 21.2 Indexed net worth fields

The simulation database also calculates:

```text
owner_net_worth_index
renter_net_worth_index
```

using real net worth normalized to month 0 = 100.

These fields are retained for analytical flexibility but are **not used as the primary final-report outcome measures**.

---

## 22. Owner vs Renter Wealth Gap

The main wealth comparison is based on real net worth:

```text
Real Net Worth Gap = Owner Real Net Worth − Renter Real Net Worth
```

| Gap | Interpretation |
|---:|---|
| Positive | Owner has higher real net worth |
| Negative | Renter-investor has higher real net worth |
| Near zero | Similar real wealth outcome |

The comparison is evaluated at the relevant scenario end date.

---

## 23. Sensitivity Analysis Framework

The final report focuses on five dimensions.

### 23.1 City

Results are compared across Canada, Vancouver, Calgary, Edmonton, Toronto, Ottawa, and Montreal.

### 23.2 Purchase year

Different purchase years expose households to different housing, equity, inflation, rent, and mortgage-rate environments.

### 23.3 Holding period

The model evaluates:

```text
5 / 10 / 15 / 20 years
```

### 23.4 Mortgage-rate scenario

```text
Lower = Base − 2 percentage points
Base
Higher = Base + 2 percentage points
```

### 23.5 Renter portfolio

```text
TSX-only
S&P 500-only
```

This tests how strongly the rent-versus-buy result depends on the renter's alternative investment opportunity.

---

## 24. Key Output Variables

The owner simulation produces fields such as:

| Variable | Description |
|---|---|
| `scenario_id` | Owner scenario identifier |
| `date_period` | Monthly date |
| `month_number` | Month within the scenario |
| `house_price_market` | Simulated current house value |
| `applied_mortgage_rate` | Mortgage rate used for the active mortgage term |
| `mortgage_payment` | Monthly mortgage payment |
| `mortgage_interest` | Monthly interest |
| `mortgage_principal` | Monthly principal repayment |
| `mortgage_balance` | Remaining mortgage debt |
| `maintenance_cost` | Monthly maintenance |
| `property_cost` | Monthly property tax |
| `insurance_cost` | Monthly insurance |
| `owner_monthly_unrecoverable_cost` | Monthly unrecoverable ownership cost |
| `cumulative_unrecoverable_cost` | Accumulated unrecoverable ownership cost |
| `owner_net_worth` | Nominal liquidation-equivalent owner net worth |

The renter simulation produces fields such as:

| Variable | Description |
|---|---|
| `renter_scenario_id` | Renter scenario identifier |
| `owner_scenario_id` | Linked owner scenario |
| `market_rent` | Historical market-rent observation |
| `actual_renter_rent` | Rent actually paid under simulation logic |
| `renter_moves` | Whether the renter moves during the month |
| `move_cost` | Relocation cost |
| `renter_total_cash_outflow` | Actual rent + move cost |
| `monthly_savings_difference` | Owner cash outflow − renter cash outflow |
| `renter_monthly_investment` | Monthly contribution or withdrawal |
| `portfolio_name` | TSX-only or S&P 500-only |
| `portfolio_return_net` | Monthly return after modeled investment costs |
| `renter_portfolio_value` | Nominal investment portfolio value |
| `renter_net_worth` | Nominal renter net worth |
| `owner_net_worth_real` | Inflation-adjusted owner wealth |
| `renter_net_worth_real` | Inflation-adjusted renter wealth |
| `owner_net_worth_index` | Real owner wealth normalized to month 0 = 100 |
| `renter_net_worth_index` | Real renter wealth normalized to month 0 = 100 |

---

## 25. Validation

### 25.1 Scenario structure

Checks include:

- each scenario begins at month 0;
- monthly dates remain ordered;
- holding-period coverage is supported by the historical data;
- owner and renter scenario identifiers remain consistent.

### 25.2 Mortgage validation

Checks include:

- no negative mortgage balances;
- payment resets occur at the correct 5-year renewal points;
- principal never exceeds remaining balance;
- month 0 payment, interest, and principal are zero;
- final mortgage payments cannot overpay the remaining obligation.

### 25.3 Renter validation

Checks include:

- no missing market-rent observations;
- month 0 never triggers a move;
- month 0 monthly investment is zero;
- portfolio value never falls below zero;
- controlled rent does not exceed market rent;
- moving resets actual rent to market rent.

### 25.4 Data alignment

Checks include:

- house prices align with simulation dates;
- mortgage rates exist for purchase and renewal periods;
- stock returns align with monthly dates;
- CPI exists for every simulated month.

### 25.5 Cross-scenario reasonableness

Outputs are reviewed to confirm that:

- higher mortgage rates increase financing costs;
- alternative portfolios produce different renter outcomes;
- longer holding periods change mortgage equity and compounding effects;
- final owner and renter wealth reconcile with their underlying monthly paths.

---

## 26. Limitations

### Historical rather than predictive

The model uses historical market data. Results describe historical scenarios and should not be interpreted as forecasts.

### Benchmark housing prices

City-level benchmark prices represent market-level estimates rather than individual properties.

### Uneven scenario coverage across holding periods

Because city-level prices begin in 2005, longer holding periods have far fewer possible purchase months than shorter ones — roughly 190 for the 5-year horizon against about 12 for the 20-year horizon, all of the latter falling in 2005. Holding period and purchase year are therefore structurally correlated, the 20-year results describe a single entry cohort, and aggregates across holding periods carry very different statistical weight. See §5.1.

### Rent data frequency

The rent source is annual, while the simulation operates monthly. The model therefore carries the relevant annual market-rent observation across months rather than observing true monthly market-rent variation.

### Mortgage-rate benchmark

The mortgage-rate series is a standardized historical benchmark rather than a borrower-specific negotiated contract rate.

### Ownership assumptions

Maintenance, property-tax rates, insurance, structure ratios, purchase costs, and sale costs are modeling assumptions and do not represent every household or property.

### Renter-policy assumptions

Rent-control rates, moving probabilities, and move-cost multipliers are stylized city-level assumptions.

### Deterministic stochastic simulation

Renter moves are generated probabilistically but use a fixed seed for reproducibility. A different seed could produce a different individual move path.

### Portfolio tax drag

Investment fee and tax-drag assumptions are simplified portfolio-level adjustments and do not model every possible account type or household tax situation.

### Full renter discipline

The final report assumes the renter invests 100% of available monthly savings. This represents a disciplined renter-investor strategy and may overstate outcomes for households that do not consistently invest the difference.

### Financial outcomes only

The model does not assign monetary value to non-financial considerations such as housing stability, freedom to renovate, school-district preference, flexibility to relocate, maintenance effort, or lifestyle preferences.

---

## 27. Summary

The simulation compares buying with renting-and-investing using a monthly, scenario-based household-finance framework.

The homeowner model captures:

- historical house-price paths,
- mortgage leverage,
- 5-year mortgage renewals,
- mortgage interest,
- principal repayment,
- maintenance,
- property tax,
- insurance,
- purchase costs,
- sale costs,
- housing equity.

The renter-investor model captures:

- equal starting capital,
- historical market rent,
- rent-control logic,
- renter mobility,
- moving costs,
- monthly cash-flow differences,
- TSX or S&P 500 investment returns,
- investment fees and tax drag,
- portfolio contributions and withdrawals.

The simulation first calculates nominal monthly financial outcomes and then converts owner and renter wealth into real terms using Canadian CPI.

The final report uses:

```text
owner_net_worth_real
renter_net_worth_real
```

as the primary wealth measures.

Down payment is fixed at 20% and renter discipline at 100%, while sensitivity analysis focuses on:

```text
City
Purchase Year
Holding Period
Mortgage Rate
Renter Portfolio
```

The result is not a universal recommendation to buy or rent. It is a historical scenario-analysis framework designed to show how the financial outcome changes with market conditions, financing costs, time horizon, geography, and the renter's alternative investment opportunity.

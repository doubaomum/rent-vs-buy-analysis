# Simulation Methodology: Rent vs Buy Model

## 1. Purpose of the Simulation

This file documents the rent-versus-buy simulation engine used in the Power BI report. The goal is to compare two long-term household wealth-building strategies under historical Canadian market conditions:

1. **Homeowner strategy** — buy a home, pay mortgage and ownership costs, and accumulate housing equity.
2. **Renter-investor strategy** — rent a comparable property and invest the available cash-flow difference in an equity portfolio.

The simulation is intentionally more detailed than a simple rent-versus-mortgage comparison. A mortgage payment is not the full cost of owning: part of the payment builds equity, while interest, taxes, maintenance, insurance, depreciation, and transaction costs are unrecoverable. Similarly, renting is not only a housing expense if the renter invests the capital and monthly savings that would otherwise be used for ownership.

The model is calculated in Python at the monthly level. Power BI is then used to filter, visualize, and compare the generated scenario outputs.

---

## 2. Why This Modeling Approach Is Used

The model is built around a household-finance question rather than a pure asset-return question:

> If one household buys and another household rents while investing the same starting capital and monthly savings difference, which path produces greater net worth?

This requires modeling both sides of the decision consistently.

### 2.1 Housing Is Both Consumption and Investment

A home is not the same as a stock index. It provides shelter, but it is also a leveraged asset purchased with debt. The model therefore separates:

- **housing consumption costs**, such as maintenance, taxes, insurance, and depreciation;
- **financing costs**, such as mortgage interest;
- **equity accumulation**, such as principal repayment and house price appreciation.

This avoids treating the full mortgage payment as a cost, because principal repayment increases homeowner equity.

### 2.2 Renting Must Include Investing Behavior

A renter can be financially competitive only if they invest the capital not used for a down payment and consistently invest monthly savings when renting is cheaper than owning. This is why the renter-investor model includes:

- initial investment of the down payment and purchase-cost equivalent;
- monthly investment of the ownership-cost minus renter-cost difference;
- portfolio returns, fees, tax drag, and renter discipline.

Without this structure, the comparison would unfairly assume that the owner builds wealth but the renter does not.

### 2.3 The Model Uses Monthly Scenario Simulation

The model is simulated monthly because key variables change over time:

- house prices;
- mortgage rates and renewal schedules;
- rent levels;
- stock-market returns;
- mortgage balance;
- owner and renter cash flows;
- renter movement and rent resets.

This monthly structure makes the model suitable for sensitivity analysis across cities, purchase years, holding periods, renter behavior, portfolio choices, and interest-rate assumptions.

---

## 3. Simulation Scope

The simulation period is based on the available dollar-based housing, rent, mortgage, and investment data.

```text
January 2005 to December 2025
```

The model covers:

- Canada-wide results;
- Vancouver;
- Toronto;
- Montreal;
- Calgary;
- Edmonton;
- Ottawa.

The scenario framework includes:

| Scenario Dimension | Values Used in Report |
|---|---|
| Geography | Canada, Vancouver, Toronto, Montreal, Calgary, Edmonton, Ottawa |
| Start year | 2005, 2010, 2015, 2020 |
| Holding period | 5, 10, 15, 20 years, depending on data availability |
| Mortgage structure | 5-year fixed mortgage |
| Down payment | 20% |
| Base renter portfolio | 100% TSX |
| Portfolio sensitivity | 100% S&P 500 |
| Renter discipline sensitivity | 100% vs lower-discipline scenarios such as 70% |
| Interest-rate sensitivity | Historical rate -2%, historical rate, historical rate +2% |

Scenarios that extend beyond the available data ending in December 2025 are excluded from the final output.

---

## 4. Core Comparison Principle: Equal Starting Capital

The model compares buying and renting on an equal-capital basis.

At the beginning of each scenario:

- the homeowner uses capital for the down payment and purchase transaction costs;
- the renter invests the same amount of capital in an investment portfolio.

During the simulation:

- if owning has a higher monthly cost, the renter invests the difference;
- if renting has a higher monthly cost, the renter withdraws the shortfall from the portfolio.

This structure makes the comparison more balanced than simply comparing monthly rent with a mortgage payment.

---

## 5. Homeowner Model

### 5.1 Homeowner Assumption Summary

| Category | Assumption | Description |
|---|---:|---|
| Down payment | 20% | The homeowner contributes 20% of the property value as an initial down payment. This avoids mortgage insurance costs and reflects a conventional Canadian mortgage structure. |
| Mortgage | 5-year fixed | The model assumes a 5-year fixed-rate mortgage with periodic refinancing based on historical mortgage-rate conditions. |
| Amortization | 25 years | Mortgage payments are calculated using a 25-year amortization schedule, representing a standard long-term Canadian repayment structure. |
| Property tax | Dynamic by city | Property tax rates vary by city: Canada 1.0%, Toronto 0.7%, Vancouver 0.3%, Calgary 0.7%, Edmonton 1.0%, Ottawa 1.2%, and Montreal 0.8%. |
| Maintenance | 1/3 of market rent | Maintenance is estimated as one-third of market rent to approximate recurring ownership expenses not recovered through home equity. |
| Depreciation | 1% of structure value | Depreciation is applied only to the structure portion of the home, not the land. Structure value shares vary by city. |
| Insurance | 0.3% of house value | Home insurance is estimated as 0.3% of house value per year as a simplified recurring ownership cost. |
| Purchase cost | 2% | Purchase cost represents estimated transaction and closing costs incurred when buying a home. |
| Sale transaction cost | 6% | Sale transaction cost represents estimated selling expenses, including realtor commissions and other transaction costs. |

---

## 6. Rationale for Homeowner Assumptions

### 6.1 Why 20% Down Payment Is Used

The model uses a 20% down payment because it represents a conventional mortgage structure in Canada and avoids mortgage default insurance. This makes the simulation cleaner because the buyer's initial mortgage balance is simply 80% of the purchase price.

A lower down payment would introduce mortgage-insurance costs and would increase leverage, making results harder to compare across cities. A 20% baseline is also useful because it gives the renter a clear equal-capital alternative: the renter invests the same down payment instead of purchasing the home.

```text
Down Payment = Purchase Price × 20%
```

```text
Initial Mortgage = Purchase Price − Down Payment
```

---

### 6.2 Why a 5-Year Fixed Mortgage Is Used

The model uses a 5-year fixed mortgage because it is a common Canadian mortgage structure and directly reflects the way many Canadian homeowners face interest-rate risk. Unlike a 30-year fixed mortgage structure common in the United States, Canadian borrowers frequently renew their mortgage rates during the holding period.

Using a 5-year fixed mortgage allows the model to capture:

- the lower-rate environment after the financial crisis;
- the very low-rate period around 2020–2021;
- the post-2022 rate shock;
- refinancing risk at each renewal.

Mortgage rates are updated every five years using historical Canadian 5-year fixed mortgage-rate data. The interest-rate sensitivity scenarios apply a shock to this renewal schedule.

---

### 6.3 Why 25-Year Amortization Is Used

A 25-year amortization period is used because it is a standard long-term Canadian mortgage repayment structure. It creates a realistic monthly payment schedule and allows the model to separate each payment into:

- mortgage interest, which is an unrecoverable cost;
- mortgage principal, which increases homeowner equity.

The simulation may end before the mortgage is fully paid off, depending on the selected holding period. At the end of the scenario, the remaining mortgage balance is deducted from the home value.

---

### 6.4 Why Property Tax Is Dynamic by City

Property taxes are not uniform across Canada. Municipal tax rates differ because local governments use different tax structures and because home price levels vary significantly across cities.

The model applies city-specific annual property-tax rates to the current home value:

| City | Property Tax Rate |
|---|---:|
| Canada | 1.0% |
| Toronto | 0.7% |
| Vancouver | 0.3% |
| Calgary | 0.7% |
| Edmonton | 1.0% |
| Ottawa | 1.2% |
| Montreal | 0.8% |

Monthly property tax is calculated as:

```text
Property Tax = House Price × Property Tax Rate / 12
```

This makes the ownership-cost model more realistic than applying one national property-tax rate to every city.

---

### 6.5 Why Maintenance Is Estimated as One-Third of Market Rent

Maintenance is modeled as one-third of market rent to approximate recurring ownership expenses that do not directly build home equity.

This assumption follows the logic of unrecoverable housing costs: the true cost of owning is not just the mortgage payment, but also the ongoing cost of maintaining and consuming the housing service.

Using market rent as the base has two advantages:

1. **It scales by city.** Higher-rent cities generally have higher labor, service, and replacement-cost environments.
2. **It connects ownership cost to housing consumption value.** Rent reflects the market cost of occupying similar housing, so using a fraction of rent gives a practical estimate of ongoing maintenance and upkeep.

The model uses:

```text
Maintenance Cost = Market Rent / 3
```

This is a simplified assumption, not an exact engineering estimate. It is intended to capture recurring maintenance, repairs, and minor ownership upkeep in a way that changes over time and across cities.

---

### 6.6 Why Depreciation Is 1% of Structure Value

Depreciation is applied only to the structure portion of the home, not the land. This reflects an important housing-economics distinction:

- land generally does not physically depreciate;
- the building structure ages and requires replacement, repairs, and renovation over time.

The model assumes annual depreciation equal to 1% of structure value:

```text
Depreciation = House Price × Structure Share × 1% / 12
```

Structure shares vary by city because some markets have much higher land value intensity than others:

| City | Structure Value Share |
|---|---:|
| Canada | 50% |
| Toronto | 45% |
| Vancouver | 35% |
| Calgary | 60% |
| Edmonton | 60% |
| Ottawa | 50% |
| Montreal | 50% |

This is especially important for Vancouver and Toronto. In high-land-value markets, a larger share of the property price is land rather than structure, so depreciation applies to a smaller portion of the total home value.

---

### 6.7 Why Insurance Is 0.3% of House Value

Home insurance is modeled as 0.3% of house value per year. The goal is not to estimate each household's exact insurance premium, but to include a recurring ownership cost that scales with property value.

Monthly insurance is calculated as:

```text
Home Insurance = House Price × 0.3% / 12
```

This avoids understating homeowner costs by ignoring insurance entirely.

---

### 6.8 Why Purchase Cost Is 2%

Purchase cost is set to 2% of the home purchase price. This represents one-time buying costs such as legal fees, land transfer taxes, inspection costs, and other closing expenses.

```text
Purchase Cost = Purchase Price × 2%
```

The purchase cost is paid at the beginning of the simulation. For equal-capital comparison, the renter invests an equivalent amount together with the down payment.

---

### 6.9 Why Sale Transaction Cost Is 6%

Sale transaction cost is set to 6% of the final home value. This represents selling expenses such as realtor commissions, staging, legal costs, and other transaction costs.

```text
Sale Cost = Final House Price × 6%
```

The sale cost is deducted from owner net worth at the end of the holding period. This is important because a homeowner's wealth is not simply home value minus mortgage balance; selling the property involves transaction costs that reduce realized equity.

---

## 7. Mortgage Calculation Logic

Monthly mortgage payments are calculated using a standard amortizing loan formula:

```text
Monthly Payment = Loan Balance × [r(1+r)^n] / [(1+r)^n − 1]
```

where:

- `r` is the monthly mortgage rate;
- `n` is the number of remaining months in the amortization schedule.

For fixed-rate scenarios, the mortgage rate and payment are reset every five years. At each renewal date, the model uses the most recent available historical Canadian 5-year fixed mortgage rate.

Interest-rate sensitivity is applied directly to the historical mortgage-rate path:

```text
Adjusted Mortgage Rate = Historical Mortgage Rate + Rate Shock
```

The adjusted rate is floored at zero to avoid impossible negative mortgage rates.

Each mortgage payment is split into interest and principal:

```text
Mortgage Interest = Previous Mortgage Balance × Mortgage Rate / 12
```

```text
Mortgage Principal = Mortgage Payment − Mortgage Interest
```

```text
Mortgage Balance = Previous Mortgage Balance − Mortgage Principal
```

---

## 8. Homeowner Net Worth and Unrecoverable Cost

Homeowner equity before selling costs is calculated as:

```text
Owner Net Worth = Current House Price − Mortgage Balance
```

At the end of the holding period, the sale cost is deducted:

```text
Owner Net Worth After Sale = Current House Price − Mortgage Balance − Sale Cost
```

The model also calculates unrecoverable ownership cost:

```text
Owner Monthly Cost = Mortgage Interest + Maintenance + Property Tax + Depreciation + Home Insurance
```

Mortgage principal is excluded from unrecoverable cost because it increases homeowner equity.

---

## 9. Renter-Investor Model

### 9.1 Renter Assumption Summary

| Category | Assumption | Description |
|---|---:|---|
| Renter discipline | 100% base case | Renter discipline represents the proportion of available monthly renter savings consistently invested into the portfolio. Sensitivity scenarios test lower discipline levels such as 70%. |
| Rent growth mode | Controlled / market | The model distinguishes between rent-controlled and market-rent environments. |
| Rent control | Dynamic by city | Controlled-rent cities use annual rent-control caps; market-rent cities allow actual rent to follow market rent more directly. |
| Move probability | Dynamic by city | Annual moving probability varies by city to reflect differences in housing stability and renter mobility. |
| Move cost | Dynamic by city and rent | Moving costs are modeled as a multiple of monthly rent and vary by city. |
| Market rent | Dynamic by city | Market rent series are based on historical city-level rent data. |
| Effective rent paid | Simulated with rent-control logic | Existing tenants receive controlled rent increases, while moving renters reset to market rent. |
| Investment portfolio | 100% TSX base case | Portfolio allocation is treated as a scenario variable. The model supports TSX-only and S&P 500 portfolios. |
| Investment fee | 0.10% | Annual management fee approximating low-cost ETF investing expenses. |
| Tax drag | Dynamic by portfolio | Tax drag varies by portfolio composition. |
| Monthly contribution | Owner Monthly Cost − Renter Monthly Cost | The renter invests the monthly difference when owner monthly cost exceeds renter monthly cost. |
| Portfolio return | Dynamic by portfolio | Returns are based on the selected historical portfolio. |
| Portfolio return net | Net return after fees and taxes | Portfolio return after deducting investment fee and portfolio-specific tax drag. |

---

## 10. Rationale for Renter-Investor Assumptions

### 10.1 Why Rent Growth Uses Controlled / Market Modes

Rental markets do not all behave the same way. In some provinces and cities, sitting tenants face regulated annual rent increases, while new tenants may pay current market rent. In other cities, rent is more market-driven.

The model therefore separates:

- **market rent** — the rent a new tenant would pay in the current market;
- **effective rent paid** — what the simulated renter actually pays after rent-control and moving logic.

This matters because a long-term tenant in a controlled market may pay below current market rent. However, if that tenant moves, they may lose that advantage and reset to market rent.

This structure is closer to real-world renting than simply assuming every renter pays current market rent every month.

---

### 10.2 City-Specific Rent-Control Assumptions

The model uses the following city-level renter policy assumptions:

| City | Rent Growth Mode | Rent Control Rate | Annual Move Probability | Move Cost Multiplier |
|---|---|---:|---:|---:|
| Canada | Mixed | 2.0% | 10% | 1.2× monthly rent |
| Toronto | Controlled | 2.5% | 8% | 1.8× monthly rent |
| Vancouver | Controlled | 3.0% | 7% | 2.0× monthly rent |
| Calgary | Market | N/A | 15% | 1.2× monthly rent |
| Edmonton | Market | N/A | 15% | 1.1× monthly rent |
| Ottawa | Controlled | 2.5% | 9% | 1.4× monthly rent |
| Montreal | Controlled | 2.5% | 10% | 1.2× monthly rent |

For controlled-rent cities, actual rent increases gradually if the renter stays in the same unit:

```text
Actual Rent_t = Actual Rent_(t−1) × (1 + Rent Control Rate / 12)
```

If the renter moves, rent resets to current market rent:

```text
Actual Rent_t = Market Rent_t
```

For market-rent cities, actual rent follows market rent more directly.

---

### 10.3 Why Move Probability Is Included

A renter's long-term cost is strongly affected by whether they can stay in the same unit. In controlled markets, staying may preserve below-market rent, while moving exposes the renter to current market rent.

The model includes move probability to capture this real-world uncertainty.

City-level moving probabilities are used because renter stability differs across markets:

- **Toronto and Vancouver** use lower move probabilities because tight rental markets and high moving costs may make renters less willing or less able to move.
- **Calgary and Edmonton** use higher move probabilities because more cyclical housing and labor markets can create more renter mobility.
- **Ottawa and Montreal** are modeled between those extremes.

Annual moving probability is converted into monthly probability:

```text
Monthly Move Probability = Annual Move Probability / 12
```

The model uses a stochastic simulation. Each month, a random value is compared against the monthly move probability. If the random value is below the monthly probability, the renter moves and rent resets to market rent.

A fixed random seed is used for reproducibility:

```text
Random Seed = 42 + scenario_id
```

This means the model includes realistic randomness but still produces reproducible results.

---

### 10.4 Why Moving Cost Is Dynamic by City and Rent

Moving costs are modeled as a multiple of monthly rent rather than a fixed dollar value:

```text
Move Cost = Actual Rent × Move Cost Multiplier
```

This allows moving costs to scale with local housing costs. Higher-cost and tighter markets such as Vancouver and Toronto therefore have larger relocation frictions, while lower-cost markets have smaller assumed moving costs.

The move-cost multiplier captures costs such as movers, deposits, overlap between leases, setup costs, and the financial friction of relocation.

---

### 10.5 Why Renter Discipline Is Included

Renting can only compete financially with owning if the renter actually invests the money that would otherwise have gone into homeownership. In real life, not every renter invests 100% of the monthly difference.

The model therefore includes renter discipline:

```text
Renter Monthly Investment = max(Owner Monthly Cost − Renter Monthly Cost, 0) × Discipline Rate
```

Interpretation:

| Discipline Rate | Meaning |
|---:|---|
| 100% | Renter invests all available monthly savings. |
| 70% | Renter invests 70% of available monthly savings and consumes or loses the rest. |

This assumption captures the behavioral-finance idea that homeownership can act as forced saving, while renting requires voluntary investment discipline.

If renter monthly cost exceeds owner monthly cost, the model deducts the extra cash outflow from the renter portfolio regardless of discipline:

```text
Renter Extra Cash Outflow = max(Renter Monthly Cost − Owner Monthly Cost, 0)
```

---

### 10.6 Why Different Portfolios Have Different Tax Drag

The renter portfolio is modeled after fees and estimated tax drag. Different portfolios receive different tax-drag assumptions because not all investments are taxed or distributed in the same way.

The logic is:

- **TSX-only portfolio:** lower tax drag assumption because Canadian equities may benefit from more favorable Canadian dividend taxation.
- **S&P 500 portfolio:** higher tax drag assumption because U.S. equity exposure may involve foreign withholding taxes, distributions, and currency-related taxable effects depending on account type.

The portfolio fee and tax-drag assumptions are:

| Portfolio | Investment Fee | Tax Drag | Description |
|---|---:|---:|---|
| TSX-only | 0.10% | 0.10% | Canadian equity portfolio |
| S&P 500 | 0.10% | 0.25% | U.S. equity portfolio from a Canadian investor perspective |

Net portfolio return is calculated as:

```text
Portfolio Return Net = Portfolio Return − (Investment Fee + Tax Drag) / 12
```

The model also deducts a 0.10% annual management fee to approximate low-cost ETF investing.

---

## 11. Renter Portfolio Calculation

The renter begins with the same capital that the homeowner uses for the down payment and purchase cost:

```text
Initial Renter Portfolio = Down Payment + Purchase Cost
```

Each month, the renter portfolio is updated as:

```text
Portfolio Value_t = Portfolio Value_(t−1) × (1 + Portfolio Return Net_t)
                    + Renter Monthly Investment_t
                    − Renter Extra Cash Outflow_t
```

The portfolio value is floored at zero to avoid negative investment balances.

```text
Renter Net Worth = Renter Portfolio Value
```

---

## 12. Equal-Capital Net Worth Indexing

Absolute net worth values are not directly comparable across cities because each city has a different home price level. A 20% down payment in Vancouver requires far more starting capital than a 20% down payment in Edmonton.

To compare wealth growth across cities on the same baseline, the report converts owner and renter net worth into indexed values.

The default baseline in the main comparison is:

```text
January 2005 = 100
```

Owner net worth index:

```text
Owner Net Worth Index_t = Owner Net Worth After Sale_t / Owner Net Worth After Sale_Start × 100
```

Renter net worth index:

```text
Renter Net Worth Index_t = Renter Net Worth_t / Renter Net Worth_Start × 100
```

This indexing approach answers:

> For each city, how much did the homeowner's and renter's wealth grow relative to their own starting capital?

This prevents high-price cities from appearing to perform better simply because the initial dollar investment was larger.

---

## 13. Owner vs Renter Wealth Gap

The report compares owner and renter outcomes using indexed wealth gaps:

```text
Indexed Wealth Gap = Owner Net Worth Index − Renter Net Worth Index
```

Interpretation:

| Indexed Wealth Gap | Interpretation |
|---:|---|
| Positive | Homeowner outperformed renter-investor. |
| Negative | Renter-investor outperformed homeowner. |
| Near zero | Similar wealth outcome. |

For final-period comparisons, the report evaluates the indexed wealth gap at the end of each scenario holding period.

---

## 14. Sensitivity Analysis Framework

The sensitivity analysis tests whether the rent-versus-buy result is robust or depends heavily on assumptions. The report focuses on three major risk factors.

### 14.1 Portfolio Sensitivity

Portfolio sensitivity compares renter outcomes under different investment portfolios.

Main comparison:

```text
S&P 500 portfolio vs TSX portfolio
```

This tests whether a renter-investor using a stronger equity portfolio could close or reverse the homeowner advantage.

### 14.2 Renter Discipline Sensitivity

Renter discipline sensitivity compares outcomes when the renter invests all available savings versus only part of them.

Main comparison:

```text
100% discipline vs 70% discipline
```

This tests the behavioral assumption that renting only competes with owning if the renter actually invests the difference consistently.

### 14.3 Interest Rate Sensitivity

Interest-rate sensitivity compares homeowner outcomes under alternative mortgage-rate paths:

| Scenario | Definition |
|---|---|
| Lower rates | Historical mortgage rate − 2 percentage points |
| Base rate | Historical mortgage rate |
| Higher rates | Historical mortgage rate + 2 percentage points |

The rate shock is applied to the mortgage renewal schedule. These scenarios are stress tests, not forecasts.

---

## 15. Key Output Variables

The simulation produces a monthly scenario-level table containing owner, renter, and comparison variables.

| Output Variable | Description |
|---|---|
| `scenario_id` | Unique scenario identifier. |
| `city` | Geography used in the scenario. |
| `date` | Monthly observation date. |
| `start_date` | Scenario start date. |
| `end_date` | Scenario end date. |
| `holding_years` | Planned holding period. |
| `house_price` | Current benchmark home value. |
| `house_price_at_purchase` | Home price at purchase date. |
| `down_payment` | Initial down payment. |
| `mortgage_rate` | Mortgage rate after any rate shock. |
| `mortgage_payment` | Monthly mortgage payment. |
| `mortgage_interest` | Monthly interest portion. |
| `mortgage_principal` | Monthly principal repayment. |
| `mortgage_balance` | Remaining mortgage balance. |
| `owner_monthly_cost` | Monthly unrecoverable ownership cost. |
| `owner_networth_after_sale` | Owner wealth after mortgage balance and sale cost. |
| `actual_renter_rent` | Simulated rent actually paid after rent-control and moving logic. |
| `move_cost` | Moving cost in that month. |
| `renter_monthly_investment` | Amount invested by renter after discipline adjustment. |
| `renter_extra_cash_outflow` | Amount withdrawn when renter monthly cost exceeds owner monthly cost. |
| `portfolio_return_net` | Portfolio return after fees and tax drag. |
| `renter_portfolio_value` | Renter investment portfolio value. |
| `renter_networth` | Renter net worth. |

---

## 16. Limitations

Several limitations should be considered when interpreting the simulation results:

- The model uses market-level benchmark prices rather than individual transaction prices.
- Home prices, rents, and mortgage rates are historical observations, not forecasts.
- Property tax rates, structure shares, rent-control assumptions, tax-drag assumptions, and moving probabilities are modeling assumptions and may not capture every household situation.
- The renter mobility model is stochastic, although a fixed random seed is used for reproducibility.
- The model compares financial outcomes only and does not assign monetary value to lifestyle preferences, housing stability, school districts, renovation control, or moving flexibility.
- The owner result assumes the home is sold at the end of the holding period and deducts sale transaction costs.
- Simulation outputs are built from nominal dollar cash flows and then indexed for cross-city comparison.
- Past performance from 2005–2025 should not be interpreted as a prediction of future rent-versus-buy outcomes.

---

## 17. Summary

The simulation compares homeownership with renting plus investing using a monthly, scenario-based framework. The owner model captures leverage, mortgage amortization, ownership costs, depreciation, insurance, property taxes, purchase costs, and sale costs. The renter-investor model captures actual rent paid, rent control, moving risk, investment contributions, portfolio compounding, fees, taxes, and behavioral discipline.

The main reason for using this model is that rent-versus-buy outcomes are not determined by housing appreciation alone. They depend on leverage, financing costs, rent growth, tenant mobility, transaction costs, portfolio returns, and whether the renter actually invests the difference.

By indexing owner and renter net worth to a common starting baseline, the report compares wealth growth fairly across cities with very different home price levels. The final result is not a universal answer to whether renting or buying is better; it is a historical scenario analysis showing how outcomes depend on geography, holding period, portfolio choice, renter discipline, and interest rates.

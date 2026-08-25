# Simulation Methodology: Rent vs Buy Model

**Project:** Rent vs Buy in Canada  
**Scope:** Monthly homeowner and renter-investor simulation methodology

### Parameter-selection evidence convention

The model contains three types of parameter choices, and they are distinguished throughout this document:

1. **Source-supported benchmark** — the value is directly supported by an external government, institutional, or market reference.
2. **Standardized modeling assumption** — external evidence supports the general range or economic logic, but the exact value is deliberately rounded or standardized so scenarios remain comparable.
3. **Stylized calibration** — the parameter represents behavior or market structure that is difficult to observe consistently across all cities and years; the value is therefore a transparent scenario assumption rather than a claim that it is an official historical average.

The purpose of documenting these categories is to make clear which parameters are directly sourced and which are modeling choices. None of the standardized or stylized parameters should be interpreted as an exact prediction for an individual household.

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

### 4.3 Why 20% down payment is used in the final report

The 20% down payment is a deliberate comparison benchmark for two reasons.

First, it is a meaningful institutional threshold in the Canadian mortgage market. The Financial Consumer Agency of Canada (FCAC) states that a borrower with a down payment below 20% will typically need mortgage loan insurance. At 20%, that additional insurance cost is generally avoided. Using 20% therefore produces a clean conventional-owner case without mixing the final comparison with mortgage-insurance effects.

Second, fixing the down payment at 20% keeps the initial-capital requirement constant across the final Power BI analysis. This is important because changing the down payment changes both the owner's leverage and the amount of capital that the renter receives at month 0. Holding it fixed makes differences across city, purchase year, holding period, mortgage-rate scenario, and renter portfolio easier to interpret.

**Evidence classification:** Source-supported threshold + standardized reporting choice.  
**Reference URL:** https://www.canada.ca/en/financial-consumer-agency/services/mortgages/down-payment.html

### 4.4 Why renter discipline is fixed at 100%

The 100% renter-discipline assumption is a **behavioral boundary condition**, not an empirical estimate of how all renters behave. It represents the financially disciplined version of the rent-and-invest strategy: whenever renting requires less cash than owning, the entire positive difference is invested.

This assumption is intentionally demanding. It allows the project to answer a clean analytical question: *how would renting compare with owning if the renter actually invested all available savings rather than consuming part of the difference?* A lower discipline rate would mix investment performance with household spending behavior and make it harder to isolate the financial comparison.

Because 100% discipline is favorable to the renter-investor strategy, it is disclosed as a limitation rather than presented as typical household behavior.

**Evidence classification:** Deliberate behavioral modeling assumption; no external source is used to claim that 100% is typical.

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

### 5.1 Why 5-, 10-, 15-, and 20-year holding periods are used

The four holding periods are analytical design choices rather than externally prescribed investment horizons. They were selected to span short-, medium-, and long-term ownership periods while remaining compatible with the available city-level housing history.

Using five-year increments also aligns naturally with the model's five-year mortgage-renewal cycle. A 5-year scenario captures one mortgage term, 10 years captures two terms, 15 years captures three, and 20 years captures four. This makes mortgage-rate exposure and renewal effects easier to interpret across holding periods.

The upper bound is 20 years because city-level benchmark-price history begins in 2005 and the historical dataset ends in 2025. Longer completed city-level holding periods are therefore not available within the current data window.

**Evidence classification:** Analytical design choice constrained by historical data availability; no external source defines these horizons as the only correct choices.

### 5.2 Scenario coverage is uneven across holding periods

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

### 6.2 Why these homeowner assumptions are included

The homeowner assumptions are designed to capture costs that are economically relevant but are often omitted when rent is compared only with the mortgage payment. The model therefore includes transaction costs, financing costs, recurring operating costs, and liquidation costs.

| Parameter | Fixed model value | Why this value is used | Evidence type |
|---|---:|---|---|
| Down payment | 20% in final report | Meaningful Canadian mortgage-insurance threshold and a clean equal-capital benchmark | Source-supported threshold |
| Mortgage term | 5 years | A conventional Canadian term and a natural renewal interval for the historical rate series | Source-supported benchmark |
| Amortization | 25 years | Conventional long-run repayment benchmark used by FCAC examples and insured-mortgage rules in many cases | Source-supported benchmark / standardization |
| Purchase cost | 2% | Falls inside CMHC's 1.5%–4% closing-cost range; standardized across cities | Source-supported range / standardization |
| Sale cost | 6% | Represents an all-in liquidation allowance; agent commissions alone can fall around 3%–6%, before other closing expenses | Market benchmark / standardization |
| Maintenance | 1.5% of structure value | Links physical upkeep to the building rather than land; calibrated to housing-cost research and practical homeowner experience | Research-informed modeling assumption |
| Insurance | 0.3% of market value | Roughly matches observed premium-to-replacement-cost magnitude in Ontario data, then standardized for the model | Market benchmark / standardization |
| Property tax | 0.30%–1.20%, city-specific | Municipal tax burdens vary materially by city; rounded representative rates preserve this cross-city difference | Municipal-source-informed standardization |
| Structure ratio | 0.35–0.60, city-specific | Separates building value from land value so maintenance is not charged against land | Stylized city calibration |
| Mortgage insurance | 3.1% at 10% down | Directly matches CMHC's premium for an 85.01%–90% loan-to-value ratio | Source-supported benchmark |
| Mortgage-rate sensitivity | ±2 percentage points | Creates a symmetric financing-cost stress test around the historical benchmark; not a forecast | Deliberate sensitivity assumption |

Detailed rationale and source URLs are provided in the relevant sections below.

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

### 7.1 Mortgage-insurance parameter rationale

The 10% down-payment scenario implies a 90% loan-to-value ratio before the insurance premium. CMHC's published homeowner mortgage-loan-insurance schedule assigns a **3.10% premium** to loans with an LTV from **85.01% to 90%**. This is why the broader database uses 3.1% for the 10% down-payment case.

At 20% down, the final reporting scenario is at 80% LTV. FCAC states that mortgage loan insurance is typically required when the down payment is **less than 20%**, which is why the final 20% case carries no modeled mortgage-insurance premium.

**Evidence classification:** Source-supported benchmark.  
**Reference URLs:**  
- https://www.cmhc-schl.gc.ca/consumers/home-buying/mortgage-loan-insurance-for-consumers/cmhc-mortgage-loan-insurance-cost  
- https://www.canada.ca/en/financial-consumer-agency/services/mortgages/down-payment.html

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

### 8.2 Why a 5-year mortgage benchmark is used

The Bank of Canada publishes posted rates for conventional 1-, 3-, and 5-year mortgages from Canada's six major chartered banks. The Bank describes these as the most typical posted rates offered by those institutions. The project uses the 5-year series because the mortgage engine is built around a five-year fixed term and five-year renewals, so the rate source and mortgage-contract structure are aligned.

FCAC also uses a 5-year term with a 25-year amortization in its public mortgage illustration, which supports this combination as a recognizable Canadian benchmark rather than an unusual financing structure.

The model does **not** claim that the posted 5-year series equals the negotiated rate received by every borrower. It is used as a consistent historical benchmark.

**Evidence classification:** Source-supported benchmark.  
**Reference URLs:**  
- https://www.bankofcanada.ca/rates/banking-and-financial-statistics/posted-interest-rates-offered-by-chartered-banks/  
- https://www.canada.ca/en/financial-consumer-agency/services/mortgages/mortgage-terms-amortization.html

### 8.3 Why the sensitivity range is ±2 percentage points

The −2pp and +2pp adjustments are deliberately symmetric stress tests around the historical base rate. They are not forecasts and are not intended to reproduce a specific lender discount or future rate path.

A two-percentage-point shock is large enough to create a meaningful change in mortgage payments and interest expense while still leaving the scenario interpretable as the same underlying historical housing/rent/equity path with a different financing environment. Using equal downward and upward shocks also prevents the sensitivity design itself from favoring one direction.

**Evidence classification:** Deliberate sensitivity-analysis assumption; no external source is used to claim that ±2pp is a predicted rate change.

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

#### Why 1.5% is used

There is no single official maintenance percentage that applies to every Canadian home. The 1.5% rate is therefore a **research-informed standardized assumption**, not a claim that every household spends exactly 1.5% each year.

The model deliberately applies the rate to **structure value rather than total property value**. Maintenance is associated with the physical building — roof, plumbing, HVAC, windows, finishes, and other components that wear out — while land does not require the same type of physical upkeep. This distinction is especially important in high-land-value markets such as Vancouver and Toronto.

Statistics Canada's owned-accommodation methodology provides useful support for separating structure from land. Under its earlier homeowner replacement-cost methodology, Statistics Canada estimated the house/structure portion separately from land and applied a 1.5% depreciation/replacement rate to the housing component. Statistics Canada explicitly distinguishes replacement/depreciation from direct maintenance and repairs, so this source should **not** be read as saying that 1.5% is an official maintenance rate. Instead, it supports two aspects of the model design: (1) physical housing costs should be associated with the structure rather than land, and (2) 1.5% is within a defensible order of magnitude for annual physical housing consumption/replacement.

The selected 1.5% maintenance rate was also sense-checked against the model builder's observed household maintenance spending and informal discussions with nearby homeowners. That practical check was used only to assess plausibility; it is not treated as a statistical sample.

Because the structure ratios range from 35% to 60%, a 1.5% structure-based maintenance rate is equivalent to approximately **0.53%–0.90% of total property market value** before city-specific price changes. This prevents the maintenance assumption from mechanically scaling with land values.

**Evidence classification:** Research-informed standardized modeling assumption + practical sense check.  
**Reference URLs:**  
- https://www150.statcan.gc.ca/n1/pub/62-553-x/2023001/chap-10-eng.htm  
- https://www150.statcan.gc.ca/n1/pub/62f0014m/62f0014m2025003-eng.htm

#### Why the city-specific structure ratios are used

The structure ratios are **not official municipal assessment ratios**. They are stylized calibration assumptions used to approximate the share of market value attributable to the physical building rather than land.

The calibration intentionally assigns a lower structure share to markets where land is expected to represent a larger portion of total property value (for example Vancouver at 0.35 and Toronto at 0.45), a higher structure share to Calgary and Edmonton (0.60), and intermediate values to Canada, Ottawa, and Montreal (0.50). The goal is not to reproduce parcel-level appraisal data, but to prevent a uniform maintenance rule from implying that expensive land itself creates maintenance expense.

Statistics Canada's historical CPI methodology similarly used a housing-structure-to-property ratio when separating the depreciating housing structure from land, which supports the **concept** of the split even though it does not validate these exact city-specific ratios.

**Evidence classification:** Stylized city calibration; exact ratios are model assumptions.  
**Conceptual reference URL:** https://www150.statcan.gc.ca/n1/pub/62f0014m/62f0014m2025003-eng.htm

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

#### Why the rates are city-specific and why this range is used

Property tax is one of the ownership costs for which a single national percentage would be particularly misleading. Canadian municipalities set local tax rates and the burden differs materially across cities. The model therefore uses a rounded **0.30%–1.20% city-specific range** rather than one Canada-wide rate.

Municipal sources demonstrate the scale of this variation. For example, the City of Vancouver's 2026 residential total levy is $3.36394 per $1,000 of taxable value (about 0.336%), Calgary's 2026 residential total rate is 0.0066499 (about 0.665%), Toronto's 2026 residential total rate is 0.767311%, and Edmonton's is 0.0103637 (about 1.036%). Ottawa explains that tax is built from assessed value multiplied by municipal and education rates, while Montréal notes that rates can vary by building category and borough.

The simulation values are **representative rounded assumptions**, not a year-by-year reconstruction of every city's historical tax system. For example, Toronto is fixed at 0.70%, Vancouver at 0.30%, Calgary at 0.70%, Edmonton at 1.00%, Ottawa at 1.20%, and Montreal at 0.80%. Fixing one representative rate within each city captures the structural cross-city difference while preventing annual tax-policy changes from becoming a second historical time series that would complicate interpretation.

The Canada value of 1.00% is a standardized national benchmark used when the scenario is not tied to one municipality; it should not be read as an official national property-tax rate.

**Evidence classification:** Municipal-source-informed standardized assumptions.  
**Reference URLs:**  
- Vancouver: https://vancouver.ca/home-property-development/residential.aspx  
- Calgary: https://www.calgary.ca/property-owners/taxes/bill-rate-calculation.html  
- Edmonton: https://www.edmonton.ca/residential_neighbourhoods/property-taxes  
- Toronto: https://www.toronto.ca/services-payments/property-taxes-utilities/property-tax/property-tax-rates-and-fees/  
- Ottawa: https://ottawa.ca/en/city-hall/budget-finance-and-corporate-planning/tax-policy/how-are-my-property-taxes-calculated  
- Montréal: https://montreal.ca/en/articles/how-municipal-taxes-are-calculated-8962

### 10.3 Insurance

```text
Monthly Insurance = House Market Value × 0.3% ÷ 12
```

Unlike maintenance, the current insurance calculation uses the full simulated house market value rather than the estimated structure value.

#### Why 0.3% is used

The 0.3% annual insurance rate is a standardized approximation calibrated to real-world homeowner insurance costs. Ratehub reported an average 2024 Ontario homeowner premium of **$1,913** and an average replacement cost of **$657,759** among its users. The ratio is approximately 0.291%, which rounds naturally to 0.30%.

Actual home-insurance pricing is property-specific and depends on replacement cost, location, construction, claims history, coverage, deductibles, and risk exposure. Insurance is normally associated more directly with the cost of rebuilding the structure than with the property's market price. The current simulation nevertheless applies the 0.3% rate to market value as a deliberate simplification so that the expense scales automatically with the simulated home-price path and remains consistent across all scenarios.

Therefore, 0.3% should be interpreted as a **representative annual insurance-cost proxy**, not an insurer's pricing formula.

**Evidence classification:** Market-data-informed standardized assumption.  
**Reference URLs:**  
- https://www.ratehub.ca/blog/average-home-insurance-cost-ontario/  
- https://www.ratehub.ca/blog/how-much-home-insurance-do-i-need/

### 10.4 Purchase cost

```text
Purchase Cost = Purchase Price × 2%
```

It is added to homeowner unrecoverable cost in month 0 and is also included in the equal-starting-capital calculation for the renter.

#### Why 2% is used

The 2% purchase-cost assumption is grounded in Canadian closing-cost guidance. CMHC states that buyers should plan for closing costs such as legal fees and land-transfer fees equal to approximately **1.5%–4% of the purchase price**. A 2% assumption therefore sits inside a published real-world range rather than assuming that purchasing a home is frictionless.

The exact amount differs by province, municipality, property price, buyer status, and applicable rebates. The model intentionally does not reproduce every jurisdiction's transfer-tax schedule. Instead, 2% is used as a standardized transaction-cost assumption across markets so that city comparisons are driven primarily by the modeled housing, rent, mortgage, and investment paths rather than by a highly detailed transfer-tax engine.

**Evidence classification:** Source-supported range + standardized modeling assumption.  
**Reference URLs:**  
- https://www.cmhc-schl.gc.ca/consumers/home-buying/mortgage-loan-insurance-for-consumers/what-are-the-general-requirements-to-qualify-for-homeowner-mortgage-loan-insurance  
- https://www.cmhc-schl.gc.ca/professionals/industry-innovation-and-leadership/industry-expertise/resources-for-mortgage-professionals/10-words-to-know-when-buying-home

### 10.5 Sale cost

```text
Sale Cost = House Market Value × 6%
```

Sale cost is included in the sale month when cumulative unrecoverable cost is tracked. The same 6% assumption is also used to estimate the cost of liquidating the house at any point in the scenario.

#### Why 6% is used

Selling a home creates transaction costs that reduce the amount of housing equity that can actually be converted into cash. Ratehub notes that Canadian real-estate agent fees can fall in roughly the **3%–6% of selling price** range, and other selling expenses can include legal, discharge, staging, moving, or closing costs.

The model therefore uses 6% as a conservative **all-in liquidation allowance**. It is not intended to claim that every seller pays exactly 6% or that commissions are fixed; commissions are negotiable and regional practices differ. The standardized 6% rate ensures that owner net worth is measured on a liquidation-equivalent basis and that the model does not treat gross house value as fully spendable wealth.

Using the same rate both in the actual sale month and in the intermediate `Estimated Current Sale Cost` keeps the net-worth definition internally consistent through the full holding period.

**Evidence classification:** Real-world selling-cost range + standardized all-in assumption.  
**Reference URL:** https://www.ratehub.ca/blog/should-you-sell-your-home-privately/

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

**On the controlled rates.** Ontario's 2.5% is the statutory ceiling under the Residential Tenancies Act rather than a typical year — guidelines hit that cap in 2023, 2024 and 2025, but fall to 2.1% in 2026 and 1.9% in 2027. Using the ceiling is the conservative choice for a controlled city, since it minimises the rent discount a long-tenured tenant accumulates. Vancouver's 3.0% is BC's 2025 limit; BC's cap varies annually and was frozen at zero in 2021. Montreal's 2.5% is a proxy, as Quebec sets rent through a case-by-case fixing framework rather than a published provincial cap.

A single rate is applied to all tenants in each regulated city for the full period. See §26 for what this simplification does and does not capture.

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

### 15.2 Why the city-level rent-growth parameters are used

The rent-growth settings are intended to represent **different regulatory regimes**, not to reproduce every historical annual guideline exactly.

#### Toronto and Ottawa — 2.5% controlled rate

Ontario's rent-increase guideline is based on the Ontario CPI and is legally capped at **2.5%** for most covered tenancies. The guideline itself changes by year — for example it was 2.5% in both 2024 and 2025 and 2.1% in 2026 — so the model's 2.5% is a representative regulated-growth parameter rather than a year-by-year historical series.

The model also resets rent to market when the renter moves, which is consistent with the fact that Ontario's guideline does not apply to rental-unit turnover in the same way as an existing controlled tenancy.

**Evidence classification:** Source-supported regulatory ceiling used as a standardized controlled-rate assumption.  
**Reference URL:** https://www.ontario.ca/page/residential-rent-increases

#### Vancouver — 3.0% controlled rate

British Columbia sets an annual residential rent-increase limit. The official limit was **3.0% for 2025** and 2.3% for 2026. The model uses 3.0% as a representative regulated-rent growth rate for Vancouver rather than loading a separate historical limit for every year.

**Evidence classification:** Source-informed standardized controlled-rate assumption.  
**Reference URL:** https://www2.gov.bc.ca/gov/content/housing-tenancy/residential-tenancies/rent-rtb/rent-increases

#### Calgary and Edmonton — market mode

Alberta requires minimum timing between rent increases but does **not** impose a general percentage limit on how much rent may be raised. This supports treating Calgary and Edmonton differently from Ontario and British Columbia. In the simulation, `market` mode sets actual rent equal to the observed market-rent series rather than applying a regulatory growth cap.

**Evidence classification:** Source-supported regulatory regime; the 15% mobility parameter is separate and remains a stylized calibration.  
**Reference URL:** https://open.alberta.ca/publications/information-for-tenants

#### Montreal — 2.5% controlled-rate proxy

Quebec does not operate a simple province-wide fixed 2.5% cap comparable to Ontario. The Tribunal administratif du logement establishes annual percentages used in a building-specific rent-fixing calculation that considers actual expenses such as taxes, insurance, maintenance, and capital expenditures.

Accordingly, the model's Montreal 2.5% rate is **not presented as an official Quebec cap**. It is a stylized controlled-growth proxy used so Montreal can follow the model's controlled-rent branch while preserving a simple, comparable framework across cities.

**Evidence classification:** Stylized model calibration informed by the existence of a regulated rent-fixing framework; exact 2.5% is not an official TAL rate.  
**Reference URLs:**  
- https://www.tal.gouv.qc.ca/en/renewal-of-the-lease-and-fixing-of-rent/applicable-percentages-to-the-criteria-for-the-fixing-of-rent  
- https://www.tal.gouv.qc.ca/en/renewal-of-the-lease-and-fixing-of-rent/rent-increase

#### Canada — 2.0% mixed rate

The national `mixed` setting is a stylized aggregate used to represent a country that contains both regulated and market-oriented provincial rental regimes. The 2.0% value is not an official Canada-wide rent-control rate. It is deliberately lower than the city-level controlled proxies and is retained as a neutral national calibration.

**Evidence classification:** Stylized national modeling assumption; no official Canada-wide source exists for a 2.0% rent-control cap.

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

### 16.1 Why the move probabilities are 7%–15%

Renter turnover matters because a move can reset a controlled tenant from their existing rent path to current market rent. Statistics Canada data support treating renter mobility as economically meaningful: in the 2021 Census, **21.0% of renter households were classified as recent renter households**, meaning all household members had moved into the dwelling within the previous year.

However, that national Census measure is **not equivalent to the exact annual probability used in this simulation**, and it does not justify a precise 7%, 8%, 9%, 10%, or 15% city rate. The model therefore treats the city-specific move probabilities as stylized calibrations:

- lower probabilities are assigned to the controlled markets, where remaining in place can preserve below-market rent;
- higher 15% probabilities are assigned to Calgary and Edmonton, where the model uses market rent and there is no modeled rent-control lock-in benefit;
- the Canada 10% value provides a middle national calibration.

These values are designed to introduce plausible renter turnover without allowing one highly volatile random path to dominate the model.

**Evidence classification:** Stylized city calibration, informed by national renter-mobility evidence but not directly estimated from it.  
**Reference URL:** https://www12.statcan.gc.ca/census-recensement/2021/as-sa/98-200-X/2021016/98-200-x2021016-eng.cfm

### 16.2 Why the random seed is `42 + owner_scenario_id`

The number 42 has **no economic interpretation**. It is simply a fixed base seed used to make the stochastic move process reproducible. Adding the `owner_scenario_id` gives each owner scenario a different random sequence while ensuring that rerunning the same scenario produces the same moves.

This design also keeps the move path identical between the TSX and S&P 500 renter variants associated with the same owner scenario. As a result, portfolio comparisons are not contaminated by different random moving histories.

**Evidence classification:** Technical reproducibility convention; no external economic source is required.

### 16.3 Moving cost

```text
Move Cost = Actual Renter Rent × Move Cost Multiplier
```

If no move occurs, move cost is zero.

#### Why the move-cost multipliers range from 1.1 to 2.0 months of rent

The moving-cost multipliers are stylized **all-in relocation-cost assumptions**, not published city averages. They are designed to capture costs that can accompany a move — movers or vehicle rental, temporary rent overlap, cleaning, utility or service setup, small replacement purchases, and other transaction/friction costs — using rent as a scale factor that automatically adjusts with the local rental market.

Higher multipliers are assigned to Toronto (1.8) and Vancouver (2.0), where the modeled rental market is more expensive and a move may involve greater cash friction; lower multipliers are used in Calgary (1.2), Edmonton (1.1), Montreal (1.2), and the Canada aggregate (1.2), with Ottawa at 1.4.

These exact multipliers are intentionally transparent scenario calibrations. They should not be interpreted as measured average moving costs for each city.

**Evidence classification:** Stylized city calibration; no authoritative city-level source is used for the exact multipliers.

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

#### Why the final report uses 100% discipline

The 100% setting represents a disciplined renter-investor who fully follows the strategy being tested. It prevents a common conceptual problem in rent-vs-buy comparisons: assuming the owner makes mandatory mortgage payments while the renter simply consumes any monthly savings.

At 100%, every positive cash-flow advantage from renting is invested, while any negative difference is funded in full. This makes the comparison financially symmetric and isolates the effect of housing, financing, rent, and investment returns from discretionary consumption behavior.

This is a deliberately strong renter assumption and is therefore treated as a modeling boundary condition rather than a claim about typical saving behavior.

**Evidence classification:** Deliberate behavioral modeling assumption; no external empirical source is used to claim 100% is typical.

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

#### Why month-0 monthly investment is forced to zero

This is an accounting-consistency rule rather than an external assumption. The renter has already received and invested the equalized starting capital at month 0. Applying the month-0 savings difference as an additional contribution or withdrawal would mix the initialization step with the recurring monthly cash-flow process and could double-count the initial allocation. Starting recurring contributions in month 1 keeps the capital setup and monthly accumulation logic separate.

**Evidence classification:** Internal accounting rule; no external reference is required.

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

#### Why the annual investment fee is 0.10%

The model is intended to represent a **low-cost passive investor**, not cost-free access to a theoretical index. Canadian investors can obtain broad TSX and S&P 500 exposure through low-cost index ETFs. As a real-world benchmark, BlackRock's iShares Core S&P/TSX Capped Composite Index ETF (XIC) currently reports an MER of **0.06%**, while the Canadian-dollar iShares Core S&P 500 Index ETF (XUS) reports an MER of **0.09%**.

Rather than tying the simulation to one specific ETF provider and changing the model every time an ETF fee changes, the project rounds this low-cost range to a common **0.10% annual fee** for both portfolios. Using the same fee also prevents a few basis points of product-selection difference from becoming the explanation for TSX-versus-S&P-500 results.

**Evidence classification:** Market-product benchmark + standardized low-cost passive-investing assumption.  
**Reference URLs:**  
- XIC: https://www.blackrock.com/ca/investors/en/products/239837/ishares-sptsx-capped-composite-index-etf  
- XUS: https://www.blackrock.com/ca/investors/en/products/251422/ishares-sp-500-index-etf

#### Why tax drag is 0.10% for TSX and 0.25% for S&P 500

The tax-drag parameters are intended to recognize that an investor may not retain the full gross market return after tax frictions. They are **not personal income-tax rates** and are not intended to calculate an individual household's tax bill.

The S&P 500 drag is set higher because U.S. dividends received by a Canadian investor can face U.S. withholding tax. Under Article X of the Canada–U.S. tax convention, the normal treaty ceiling is **15% of the gross dividend** for a beneficial owner who does not qualify for the special corporate 5% rate. Canadian investor guidance has commonly shown that applying a 15% withholding rate to an S&P 500 dividend yield in the neighborhood of 1.7% can reduce portfolio return by roughly **0.25%** per year. This is why 0.25% is used as a reasonable portfolio-level friction for the U.S. equity scenario.

For Canadian equities, the model uses the smaller 0.10% drag because dividends from taxable Canadian corporations may qualify for the federal dividend tax credit, while foreign dividends do not qualify for that credit. The exact after-tax result depends on account type, province, income, ETF structure, and whether foreign tax credits are recoverable, so 0.10% is deliberately kept as a small standardized domestic-tax friction rather than a household-specific calculation.

A technical limitation is important: the market series used by the simulation are price-return series rather than full dividend-reinvested total-return series. Therefore these tax-drag adjustments should be interpreted as **small standardized portfolio frictions**, not as a precise tax model of the dividends generated by the source series.

**Evidence classification:** Tax-rule-informed standardized assumptions; exact 0.10% and 0.25% are model-level simplifications.  
**Reference URLs:**  
- Canada–U.S. tax convention, Article X: https://www.canada.ca/en/department-finance/programs/tax-policy/tax-treaties/country/united-states-america-convention-consolidated-1980-1983-1984-1995-1997.html  
- CRA federal dividend tax credit: https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-40425-federal-dividend-tax-credit.html  
- CRA foreign investment income / foreign dividends: https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-12100-interest-other-investment-income.html  
- Practical 0.25% S&P 500 withholding example: https://www.moneysense.ca/columns/ask-a-planner/withholding-tax-on-us-etfs/

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

### 23.6 Why these five sensitivity dimensions are prioritized

The final sensitivity design separates assumptions that are **fixed to create a common comparison basis** from variables that represent the economic question the dashboard is intended to explore.

- **City** changes housing prices, rents, property taxes, and calibrated local assumptions.
- **Purchase year** changes the historical market path experienced by both strategies.
- **Holding period** changes the amount of mortgage amortization and investment compounding observed.
- **Mortgage-rate scenario** isolates financing-cost sensitivity around the same historical market path.
- **Renter portfolio** changes the renter's opportunity cost and alternative wealth-building path.

Down payment and renter discipline are intentionally excluded from the final sensitivity set because changing them also changes the comparison framework itself — initial capital in the first case and household saving behavior in the second. Keeping those fixed makes the five reported sensitivities easier to interpret.

**Evidence classification:** Analytical design choice; no external source is required.

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

Because city-level prices begin in 2005, longer holding periods have far fewer possible purchase months than shorter ones — roughly 190 for the 5-year horizon against about 12 for the 20-year horizon, all of the latter falling in 2005. Holding period and purchase year are therefore structurally correlated, the 20-year results describe a single entry cohort, and aggregates across holding periods carry very different statistical weight. See §5.2.

### Rent data frequency

The rent source is annual, while the simulation operates monthly. The model therefore carries the relevant annual market-rent observation across months rather than observing true monthly market-rent variation.

### Rent-control coverage is overstated

The model applies a single controlled rate to every tenant in each regulated city. In practice, coverage is narrower and the caps are less stable:

- Ontario exempts units first occupied after **15 November 2018** from the guideline entirely, so a Toronto or Ottawa renter in a newer building faces uncapped increases.
- Ontario's 2.5% is the statutory ceiling, reached in 2023, 2024 and 2025 but lower in other years — 2.1% for 2026 and 1.9% for 2027.
- British Columbia's limit varies annually and was frozen at zero in 2021.

Applying one representative rate to all tenants across the full period overstates how many renters are protected while using the maximum permitted increase for those who are. The two effects work in opposite directions, so the net bias on renter outcomes is not clear-cut.

### Mortgage-rate benchmark

The mortgage-rate series is a standardized historical benchmark rather than a borrower-specific negotiated contract rate.

### Ownership assumptions

Maintenance, property-tax rates, insurance, structure ratios, purchase costs, and sale costs are modeling assumptions and do not represent every household or property. Some are anchored to published ranges or current municipal/market benchmarks, while others are standardized or stylized values chosen for comparability. The presence of a supporting reference does not mean the exact fixed value applies to every city, year, property, or household.

### Renter-policy assumptions

Rent-control modes are informed by provincial regulatory frameworks, but fixed rent-growth rates, moving probabilities, and move-cost multipliers are stylized city-level assumptions. In particular, Montreal's 2.5% controlled-rate proxy is not an official Quebec-wide rent cap, and the exact city move probabilities are not direct Statistics Canada estimates.

### Deterministic stochastic simulation

Renter moves are generated probabilistically but use a fixed seed for reproducibility. A different seed could produce a different individual move path.

### Portfolio tax drag

Investment fee and tax-drag assumptions are simplified portfolio-level adjustments and do not model every possible account type or household tax situation.

### Full renter discipline

The final report assumes the renter invests 100% of available monthly savings. This represents a disciplined renter-investor strategy and may overstate outcomes for households that do not consistently invest the difference.

### Financial outcomes only

The model does not assign monetary value to non-financial considerations such as housing stability, freedom to renovate, school-district preference, flexibility to relocate, maintenance effort, or lifestyle preferences.

---

## 27. Parameter Source and Rationale Reference List

This section consolidates the external references used to justify parameter ranges, institutional thresholds, and modeling logic. A reference in this table does **not** imply that every exact model value is directly published by the source; the `Use in model` column identifies whether the source directly supports the number or only informs a standardized/stylized assumption.

**A note on source tiers.** Most entries draw on primary institutional sources — federal agencies, municipal governments, provincial regulators, and fund providers. For two parameters no official published series exists: home-insurance premiums and real-estate commission ranges. Industry sources are used there as order-of-magnitude references rather than authoritative rates, and the resulting model values should be read accordingly.

| Topic | Use in model | Source | URL |
|---|---|---|---|
| 20% down-payment threshold | Direct institutional threshold: below 20% generally requires mortgage loan insurance | Financial Consumer Agency of Canada | https://www.canada.ca/en/financial-consumer-agency/services/mortgages/down-payment.html |
| 5-year term / 25-year amortization | Supports conventional Canadian mortgage structure and terminology | Financial Consumer Agency of Canada | https://www.canada.ca/en/financial-consumer-agency/services/mortgages/mortgage-terms-amortization.html |
| 5-year historical mortgage benchmark | Direct source for typical posted 5-year conventional mortgage rates from six major banks | Bank of Canada | https://www.bankofcanada.ca/rates/banking-and-financial-statistics/posted-interest-rates-offered-by-chartered-banks/ |
| 3.10% mortgage-insurance premium at 85.01%–90% LTV | Direct support for 10%-down broader-database scenario | CMHC | https://www.cmhc-schl.gc.ca/consumers/home-buying/mortgage-loan-insurance-for-consumers/cmhc-mortgage-loan-insurance-cost |
| Purchase closing costs | CMHC range of approximately 1.5%–4%; model standardizes to 2% | CMHC | https://www.cmhc-schl.gc.ca/consumers/home-buying/mortgage-loan-insurance-for-consumers/what-are-the-general-requirements-to-qualify-for-homeowner-mortgage-loan-insurance |
| Purchase closing costs — glossary | Additional CMHC statement of 1.5%–4% closing-cost range | CMHC | https://www.cmhc-schl.gc.ca/professionals/industry-innovation-and-leadership/industry-expertise/resources-for-mortgage-professionals/10-words-to-know-when-buying-home |
| Selling costs | Agent-fee range only. The model's 6% is an all-in allowance also covering legal fees, discharge costs, and moving — no single published source covers the full set | Ratehub | https://www.ratehub.ca/blog/should-you-sell-your-home-privately/ |
| Structure-versus-land treatment | Supports separating the depreciating/consumed housing structure from land | Statistics Canada | https://www150.statcan.gc.ca/n1/pub/62-553-x/2023001/chap-10-eng.htm |
| Historical 1.5% replacement/depreciation factor | Supports order of magnitude and structure-only concept; not treated as an official maintenance rate | Statistics Canada | https://www150.statcan.gc.ca/n1/pub/62f0014m/62f0014m2025003-eng.htm |
| Home insurance | Ontario average premium and replacement-cost data give an observed ratio close to 0.3% | Ratehub | https://www.ratehub.ca/blog/average-home-insurance-cost-ontario/ |
| Insurance replacement-cost concept | Supports distinction between replacement value and market value | Ratehub | https://www.ratehub.ca/blog/how-much-home-insurance-do-i-need/ |
| Vancouver property tax | Municipal rate evidence informing 0.30% representative assumption | City of Vancouver | https://vancouver.ca/home-property-development/residential.aspx |
| Calgary property tax | Municipal rate evidence informing 0.70% representative assumption | City of Calgary | https://www.calgary.ca/property-owners/taxes/bill-rate-calculation.html |
| Edmonton property tax | Municipal rate evidence informing 1.00% representative assumption | City of Edmonton | https://www.edmonton.ca/residential_neighbourhoods/property-taxes |
| Toronto property tax | Municipal rate evidence informing 0.70% representative assumption | City of Toronto | https://www.toronto.ca/services-payments/property-taxes-utilities/property-tax/property-tax-rates-and-fees/ |
| Ottawa property tax | Supports local assessed-value × tax-rate structure; model uses a representative 1.20% | City of Ottawa | https://ottawa.ca/en/city-hall/budget-finance-and-corporate-planning/tax-policy/how-are-my-property-taxes-calculated |
| Montréal property tax | Supports borough/category variation; model uses a representative 0.80% | Ville de Montréal | https://montreal.ca/en/articles/how-municipal-taxes-are-calculated-8962 |
| Ontario rent control | Direct: 2.5% is the statutory maximum guideline under the Residential Tenancies Act, reached in 2023, 2024 and 2025. Model applies the cap rather than a year-by-year series | Government of Ontario | https://www.ontario.ca/page/residential-rent-increases |
| British Columbia rent control | Supports regulated Vancouver regime; 3.0% was the 2025 limit. BC limits vary annually and were frozen in 2021, so the model applies one representative rate across the full period rather than the year-by-year schedule | Government of British Columbia | https://www2.gov.bc.ca/gov/content/housing-tenancy/residential-tenancies/rent-rtb/rent-increases |
| Alberta rent increases | Supports market-mode distinction; no general percentage cap on increase amount | Government of Alberta | https://open.alberta.ca/publications/information-for-tenants |
| Quebec rent-fixing framework | Supports regulated/stylized Montreal treatment; does not support a fixed 2.5% provincial cap | Tribunal administratif du logement | https://www.tal.gouv.qc.ca/en/renewal-of-the-lease-and-fixing-of-rent/applicable-percentages-to-the-criteria-for-the-fixing-of-rent |
| Renter turnover | National evidence that renter turnover is material; exact city probabilities remain stylized | Statistics Canada | https://www12.statcan.gc.ca/census-recensement/2021/as-sa/98-200-X/2021016/98-200-x2021016-eng.cfm |
| TSX portfolio fee benchmark | XIC MER provides low-cost Canadian-equity benchmark | BlackRock Canada | https://www.blackrock.com/ca/investors/en/products/239837/ishares-sptsx-capped-composite-index-etf |
| S&P 500 portfolio fee benchmark | XUS MER provides low-cost S&P 500 benchmark | BlackRock Canada | https://www.blackrock.com/ca/investors/en/products/251422/ishares-sp-500-index-etf |
| Canadian dividend tax treatment | Canadian taxable-corporation dividends may qualify for federal dividend tax credit | Canada Revenue Agency | https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-40425-federal-dividend-tax-credit.html |
| U.S. dividend withholding | Treaty generally limits withholding to 15% of gross dividends in ordinary beneficial-owner cases | Department of Finance Canada | https://www.canada.ca/en/department-finance/programs/tax-policy/tax-treaties/country/united-states-america-convention-consolidated-1980-1983-1984-1995-1997.html |
| Foreign dividend treatment | Foreign dividends do not qualify for the Canadian dividend tax credit; foreign tax credits may apply in some cases | Canada Revenue Agency | https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-12100-interest-other-investment-income.html |
| Approx. 0.25% U.S. withholding drag example | Practical illustration of 15% withholding × S&P 500 dividend yield producing roughly 0.25% drag | MoneySense | https://www.moneysense.ca/columns/ask-a-planner/withholding-tax-on-us-etfs/ |

### Parameters intentionally not presented as directly sourced historical estimates

The following exact values are model calibrations and should be described as such:

- structure ratios of 0.35–0.60 by city;
- annual move probabilities of 7%–15% by city;
- move-cost multipliers of 1.1–2.0 months of rent;
- Canada mixed rent-growth rate of 2.0%;
- Montreal controlled-rate proxy of 2.5%;
- ±2 percentage-point mortgage-rate shocks;
- 100% renter discipline;
- random-seed base value of 42;
- fixed property-tax percentages as representative city assumptions rather than a historical annual tax-rate series;
- 0.10% TSX and 0.25% S&P 500 tax drag as portfolio-level simplifications rather than household tax rates;
- the 6% all-in selling cost, of which only the agent-fee component is externally sourced;
- the 2% purchase cost, standardized from CMHC's published 1.5%–4% range;
- the 2025-12-01 data horizon, which is set by rent-survey availability rather than by any economic assumption.

Two further simplifications affect rent-control coverage rather than rate levels. Ontario exempts units first occupied after 15 November 2018 from the guideline entirely, and British Columbia's limit has varied year to year. The model applies a single controlled rate to all tenants in each regulated city, which overstates how many renters are actually covered and understates the variability of the cap over time.

Documenting these assumptions explicitly is part of the model's reproducibility: another analyst can change them and rerun the scenario engine without changing the underlying calculation framework. The sensitivity framework in §23 goes a step further by quantifying how much each calibrated parameter actually moves the result, which distinguishes the assumptions that matter from those that do not.

---

## 28. Summary

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

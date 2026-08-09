# Data Cleaning, Transformation, and Preparation

**Project:** Rent vs Buy in Canada
**Scope:** Source ingestion through Power BI-ready outputs

---

## 1. Overview

This document describes the data cleaning, transformation, and preparation workflow used in the **Rent vs Buy in Canada** project.

The project combines housing, equity-market, inflation, exchange-rate, mortgage-rate, and rental-market data from multiple public sources. These datasets differ in structure, frequency, currency, geographic coverage, and reporting convention, so they must be standardized before they can support asset-performance analysis, financial simulation, and Power BI reporting.

The architecture uses **PostgreSQL as the central storage and transformation layer**. Python handles only the state-dependent monthly calculations that are difficult to express efficiently in SQL — mortgage amortization and portfolio compounding, where each month depends on the result of the previous one.

### 1.1 Data flow

```text
Raw source files
      ↓
raw schema  ──────────→  raw-data validation
      ↓
stg schema  ──────────→  staging-data validation
      ↓
analysis schema  ─────→  real asset indexes, CAGR, long-format inputs
      ↓
simulation schema  ───→  scenario generation, monthly schedules
      ↓
Python simulation engines  →  mortgage amortization, renter portfolio
      ↓
Power BI reporting
```

### 1.2 Two analytical tracks

The project deliberately separates two purposes:

| Track | Question | Data used |
|---|---|---|
| **Market-level asset analysis** | How have housing and equities performed in real terms over the long run? | Inflation-adjusted, rebased index series |
| **Household-level rent-vs-buy simulation** | Would a specific household have been better off buying or renting-and-investing? | Actual dollar prices, rents, mortgage costs, and portfolio returns |

The first track compares assets. The second models the financial experience of an individual homeowner and an individual renter-investor. Keeping them separate is what allows the project to use indexed series where comparability matters and actual dollar values where cash-flow realism matters.

### 1.3 Division of responsibility

| Tool | Role |
|---|---|
| **PostgreSQL** | Data storage, cleaning, transformation, scenario generation, static monthly inputs |
| **Python** | Stateful monthly simulation, including mortgage amortization and renewal, renter mobility and effective rent paths, monthly cash-flow differences, portfolio compounding, and inflation-adjusted net worth calculations |
| **Power BI** | Interactive analysis, sensitivity filtering, visualization |

Power BI does not recreate the underlying financial simulation. It consumes calculated PostgreSQL simulation outputs and uses DAX primarily for reporting and interactive aggregation.

---

## 2. Database Architecture

The database is organized into four layers, each with a distinct responsibility.

| Schema | Responsibility |
|---|---|
| `raw` | Source data, imported with minimal transformation |
| `stg` | Cleaned, type-cast, standardized tables |
| `analysis` | Real indexes, CAGR tables, long-format simulation inputs |
| `simulation` | Scenario definitions and monthly schedules |

### 2.1 Raw layer

The `raw` schema preserves source-level data so that every downstream transformation remains traceable to an unmodified original.

Raw datasets:

- Canada national residential property price index (BIS)
- City-level housing price indices
- City-level benchmark housing prices
- S&P 500
- TSX
- VT
- City-level rent data
- Canada CPI
- USD/CAD exchange rate
- Canada 5-year mortgage rate

Source CSV files are imported using `psql \copy`. Most raw columns are typed as `text` rather than `numeric` or `date`, so that a malformed value fails at the cleaning step — where it can be inspected — rather than at the import step, where it would abort the whole load.

City-level housing and rent files arrive as one file per city with no city column. These are loaded through temporary tables (`raw.tmp_house_price`, `raw.tmp_rent_raw`) and then inserted into consolidated tables with a standardized city identifier attached.

### 2.2 Staging layer

The `stg` schema standardizes raw datasets into consistent, correctly typed tables:

```text
stg.canada_house_price_index_2010_100
stg.city_house_price_index
stg.city_house_prices
stg.city_indexed_house_prices
stg.sp500_usd
stg.tsx_cad
stg.vt_usd
stg.city_rent
stg.canada_cpi
stg.usd_cad
stg.canada_5yearmortgage
```

Typical transformations: standardizing date formats, trimming whitespace, removing thousands separators, converting empty strings to `NULL`, casting numeric text to `NUMERIC`, pivoting city-level data from long to wide, and removing invalid observations.

The recurring cleaning idiom is:

```sql
NULLIF(REPLACE(TRIM(column_name), ',', ''), '')::NUMERIC
```

This handles the three problems that appear together in most source files. For example, the text value `"6,729.60"` becomes the numeric `6729.60`, while an empty cell becomes `NULL` instead of raising a cast error.

---

## 3. Data Validation

Validation runs at both the raw and staging stages, before data reaches analysis or simulation.

Checks performed:

- row counts per table
- minimum and maximum dates
- city coverage (all seven expected markets present, with plausible row counts)
- duplicate dates
- duplicate city-date combinations
- missing key fields
- unexpected gaps in historical coverage

```text
Load  →  row count  →  date range  →  city coverage  →  duplicates  →  next layer
```

Duplicate checks matter most for time-series tables. A single duplicated date silently fans out every downstream join, inflating row counts and distorting return calculations and simulation results in ways that are difficult to trace backwards.

Making these checks explicit SQL files rather than informal visual review means they can be rerun after any source refresh.

---

## 4. Date Standardization

The project combines datasets reported at different frequencies:

| Dataset | Original frequency |
|---|---|
| Canada national housing index | Quarterly |
| City housing indices | Monthly |
| Benchmark housing prices | Monthly |
| Equity-market data | Daily / monthly |
| USD/CAD | Daily |
| CPI | Monthly |
| Mortgage rates | Monthly |
| Rent data | Annual |

All dates are cast to PostgreSQL `DATE` and exposed through a single field name, `date_period`, so that tables join consistently. Monthly observations use the first day of the month:

```text
2005-01-01
2005-02-01
2005-03-01
```

The simulation layer operates entirely on this monthly timeline.

---

## 5. Currency Standardization

The project evaluates outcomes from the perspective of a Canadian investor, so U.S.-denominated assets are converted to Canadian dollars before any comparison or simulation.

The USD/CAD series is interpreted as **CAD per USD**, so conversion is a multiplication:

```text
S&P 500 (CAD) = S&P 500 (USD) × USD/CAD
```

VT is converted the same way.

Equity markets and foreign-exchange markets do not share a trading calendar, so an exact date join would drop observations. Instead, each market observation is matched to the **most recent USD/CAD rate on or before** that date, implemented as a `LEFT JOIN LATERAL` with `ORDER BY date_period DESC LIMIT 1`. This is a backward-looking match only: it never uses an exchange rate that would not yet have been observable.

---

## 6. Inflation Adjustment

Canadian CPI is the inflation measure throughout. The general form is:

```text
Real Value = Nominal Value × Base CPI ÷ Current CPI
```

The choice of base differs by context:

| Context | CPI base |
|---|---|
| Asset index construction | Fixed common base for the series |
| Household simulation | Each scenario's own starting month |

Scenario-specific bases are used in the simulation because each household's purchasing power should be expressed in the dollars of the year they bought, not in the dollars of an arbitrary shared reference year.

The analysis spans several decades. Without CPI adjustment, a large share of the apparent growth in house prices, equity values, and household net worth would simply be general price inflation rather than real gain.

---

## 7. Analysis Layer

The `analysis` schema turns staging data into two kinds of output: **real asset indexes with CAGR tables** for the market-level track, and **long-format price and rent tables** for the simulation track.

### 7.1 Canada national housing

The BIS Canada-wide residential property price index is published in **real (inflation-adjusted) terms**, so no CPI deflation is applied. The series is rebased from 2010 = 100 to **1990 = 100**, producing `analysis.canada_house_price_index_1990_100`. This gives housing and equities a common real starting point for long-horizon comparison.

### 7.2 S&P 500

```text
USD price → convert to CAD → deflate by Canadian CPI → rebase to 1990 = 100
```

Result: `analysis.sp500_index_1990_100`. The table retains `price_usd`, `price_cad`, `price_cad_real`, and `price_index_cad_real`, so downstream consumers can select nominal or real values as appropriate.

### 7.3 TSX

The TSX is already in Canadian dollars, so no currency conversion is needed:

```text
Nominal TSX → deflate by Canadian CPI → rebase to 1990 = 100
```

Result: `analysis.tsx_index_1990_100`.

### 7.4 VT

VT is converted from USD to CAD and deflated by Canadian CPI, producing `analysis.vt_cad_real`. It is not rebased, because it is used for supporting analysis rather than long-horizon index comparison — its history begins in 2008, far later than the other series.

VT remains available in the analytical database but is **not** one of the two portfolio options in the final renter simulation.

### 7.5 City-level real housing index

Cities covered: Canada (national), Vancouver, Calgary, Edmonton, Toronto, Ottawa, Montreal.

Nominal city house-price indices are deflated by Canadian CPI and rebased to **January 2005 = 100**, producing `analysis.city_indexed_house_prices`. The real S&P 500 and TSX series are rebased to the same January 2005 anchor and appended as additional columns, so housing and equity performance can be read off a single real indexed scale.

January 2005 is used as the common analytical base so that all city housing series and equity benchmarks can be compared consistently over the main 2005–2025 analysis window.

---

## 8. CAGR Analysis

Compound annual growth rates are calculated across every available start date and several holding horizons:

```text
CAGR = (Ending Value / Beginning Value) ^ (1 / Holding Years) − 1
```

Each table is built by cross-joining a list of holding periods against the source series, then self-joining forward by `MAKE_INTERVAL(years => holding_years)` to locate the matching end observation.

| Table | Source | Basis | Horizons |
|---|---|---|---|
| `analysis.canada_house_cagr` | `stg.canada_house_price_index_2010_100` | Real (source series) | 5 / 10 / 15 / 20 / 25 / 30 / 35 |
| `analysis.sp500_cagr` | `analysis.sp500_index_1990_100` | Real CAD | 5 / 10 / 15 / 20 / 25 / 30 / 35 |
| `analysis.tsx_cagr` | `analysis.tsx_index_1990_100` | Real CAD | 5 / 10 / 15 / 20 / 25 / 30 / 35 |
| `analysis.vt_cagr` | `analysis.vt_cad_real` | Real CAD | 5 / 10 / 15 / 18 |
| `analysis.city_house_cagr` | `analysis.city_indexed_house_prices` | Real, 2005 = 100 | 5 / 10 / 15 / 20 |

All five tables are on a real basis, so growth rates are directly comparable across assets. The national housing series arrives inflation-adjusted from the source; the equity and city-level series are deflated by Canadian CPI during index construction (§7).

Annual start observations are taken from Q1 for the quarterly national series and from January for all monthly series.

City-level horizons stop at 20 years because benchmark price coverage begins in 2005. Equity and national housing series support up to 35 years.

`analysis.sum_canada_stock_cagr` joins the national housing, S&P 500, TSX, and city-level CAGR tables on start year and holding period, producing a single wide table for Power BI heatmaps by start year × holding period × asset.

---

## 9. Simulation Input Preparation

The simulation uses **actual dollar-denominated house prices and rents**, not indexed series. Mortgage and household-finance calculations require real magnitudes: purchase price, down payment, principal, interest, maintenance, property tax, insurance, rent, contributions, portfolio value, sale proceeds, and net worth.

City-level prices and rents are unpivoted into long format:

```text
analysis.city_house_prices_long   (date_period, city, price)
analysis.city_rent_long           (date_period, city, price)
```

`NULL` values are filtered out during the unpivot, so absent city-months simply do not appear rather than propagating as missing rows.

---

## 10. Owner Scenario Generation

Owner scenarios are generated in PostgreSQL as `simulation.owner_basic_model`, one row per combination of:

| Dimension | Values |
|---|---|
| City | 7 markets |
| Purchase date | Every month with both a purchase and a matching sale observation |
| Holding period | 5 / 10 / 15 / 20 years |
| Down payment | 10% / 20% / 30% |
| Mortgage-rate scenario | Lower / Base / Higher |

Mortgage-rate scenarios shift the historical 5-year rate:

```text
Lower  = historical rate − 2 percentage points
Base   = historical rate
Higher = historical rate + 2 percentage points
```

The shifted rate is floored at zero, so the Lower scenario cannot produce a negative mortgage rate in periods when historical rates were already below 2%.

### 10.1 Down payment scope

All three down-payment levels remain in PostgreSQL, but the **final report fixes down payment at 20%**. See §21 for the reasoning.

One consequence is worth stating explicitly: mortgage default insurance is modeled at 3.1% of the loan and applies only when the down payment is 10%. At the reported 20% level, **mortgage insurance is zero** and the final loan equals the pre-insurance loan. This matches Canadian practice, where insurance is required only below 20% down.

---

## 11. Owner Monthly Schedule

`simulation.owner_monthly_schedule` expands each scenario into one row per month from **month 0** through the sale month, generated with `generate_series`.

Static monthly inputs computed in SQL:

- house market value for that month
- estimated current sale cost (market value × 6%)
- mortgage term number and renewal timing
- applied mortgage rate for the current term
- structure value
- maintenance, property tax, and insurance costs
- sale-month flag

PostgreSQL produces the timeline and every value that depends only on that month. Python then computes the values that depend on prior months.

### 11.1 Data horizon

The simulation uses historical source data through **2025-12-01**.

Available purchase dates and holding-period combinations are therefore constrained by the historical data window. Completed historical outcomes should only be evaluated for scenarios whose intended holding period is fully supported by the available housing, rent, mortgage-rate, CPI, and market-return data.

This prevents incomplete recent scenarios from being interpreted as completed rent-versus-buy outcomes.

---

## 12. Mortgage Calculation

Performed month by month in Python.

```text
Amortization = 25 years
Term         = 5 years
```

### 12.1 Payment recalculation

The payment is recalculated at month 1 and at each five-year renewal — months 61, 121, 181, and so on — using the historical 5-year rate prevailing at that renewal, adjusted by the scenario's rate shift:

```text
Payment = Balance × r / [1 − (1 + r)^(−n)]

r = monthly mortgage rate  (annual rate ÷ 100 ÷ 12)
n = remaining amortization months
```

At renewal the payment is recalculated on the **then-current balance over the remaining amortization**, not the original 25 years. This reproduces how Canadian mortgage renewal actually works: the amortization clock keeps running across terms.

A 0% rate is handled separately as straight-line repayment, avoiding division by zero.

### 12.2 Monthly mechanics

```text
Interest  = Beginning Balance × Monthly Rate
Payment   = min(Scheduled Payment, Beginning Balance + Interest)
Principal = min(max(Payment − Interest, 0), Beginning Balance)
Balance   = Beginning Balance − Principal
```

The two clamps prevent the final payment from exceeding the outstanding obligation and guarantee the balance terminates at exactly zero rather than drifting negative through floating-point accumulation.

Month 0 carries the initial balance with no payment, interest, or principal.

### 12.3 Principal is not a cost

Mortgage principal is excluded from unrecoverable ownership cost because it converts directly into home equity. It is a transfer between two of the household's own accounts, not an expense. It does appear in cash outflow (§17), because the household must still fund it each month.

---

## 13. Maintenance Cost

Maintenance applies to the **structural portion** of the property, not the full market value, because land does not depreciate or require upkeep.

```text
Structure Value    = House Market Value × Structure Ratio
Monthly Maintenance = Structure Value × 1.5% ÷ 12
```

Structure ratios vary by city because the land share of property value differs sharply across Canadian markets:

| City | Structure ratio |
|---|---:|
| Canada | 0.50 |
| Toronto | 0.45 |
| Vancouver | 0.35 |
| Calgary | 0.60 |
| Edmonton | 0.60 |
| Ottawa | 0.50 |
| Montreal | 0.50 |

Vancouver's low ratio reflects land dominating property value there; applying a flat maintenance rate to total value would materially overstate ownership cost in exactly the markets where housing is most expensive.

---

## 14. Property Tax

```text
Monthly Property Tax = House Market Value × City Property Tax Rate ÷ 12
```

| City | Annual rate |
|---|---:|
| Canada | 1.00% |
| Toronto | 0.70% |
| Vancouver | 0.30% |
| Calgary | 0.70% |
| Edmonton | 1.00% |
| Ottawa | 1.20% |
| Montreal | 0.80% |

Because the calculation uses the simulated market value each month, property-tax expense rises and falls with housing values over the holding period rather than staying fixed at the purchase-price level.

---

## 15. Home Insurance

```text
Monthly Insurance = House Market Value × 0.3% ÷ 12
```

Unlike maintenance, insurance is currently calculated using the **full simulated house market value** rather than the estimated structure value.

---

## 16. Owner Unrecoverable Cost

Monthly unrecoverable ownership cost:

```text
Mortgage Interest + Maintenance + Property Tax + Insurance
```

Principal is deliberately excluded (§12.3).

Two one-time additions:

| Timing | Addition | Rate |
|---|---|---|
| Month 0 | Purchase cost | 2% of purchase price |
| Sale month | Sale cost | 6% of sale price |

The model also accumulates these into `cumulative_unrecoverable_cost` across the holding period.

---

## 17. Owner Net Worth

```text
Owner Net Worth
= Current House Market Value
− Remaining Mortgage Balance
− Estimated Current Sale Cost
```

Estimated current sale cost is 6% of the current market value, representing the transaction cost the owner would incur to convert the asset to cash at that moment. Including it means owner net worth is stated on a liquidation-equivalent basis, directly comparable to the renter's portfolio value.

**Cumulative unrecoverable cost is not subtracted from net worth.** Those costs already enter the comparison through monthly cash flow: every dollar the owner spends on interest, maintenance, tax, or insurance is a dollar not available for the renter's portfolio, and the savings difference (§19) captures that. Subtracting them a second time from the owner's balance sheet would double-count the same expense.

---

## 18. Renter Scenario Preparation

Each renter scenario is linked to an existing owner scenario, inheriting city, purchase date, holding period, the housing value path, the mortgage schedule, owner cash outflow, and owner net worth. It then adds market rent, rent-control assumptions, moving probability and cost, portfolio choice, investment fees, and tax drag.

The final report uses two renter portfolios: **TSX-only** and **S&P 500-only**.

### 18.1 Equal starting capital

The owner and renter begin with identical initial capital:

```text
Initial Renter Investment = Owner Down Payment + Owner Purchase Cost
```

The renter invests exactly the capital the owner committed to the property. Under the final-report assumption of a 20% down payment and a 2% purchase cost, the renter's initial portfolio therefore equals **22% of the purchase price**. This 22% figure applies specifically to the final-report scenario; the broader PostgreSQL simulation still retains 10%, 20%, and 30% down-payment scenarios.

---

## 19. Rent, Mobility, and Cash Flow

### 19.1 Rent matching

Market rent is matched to each scenario by **city and calendar year**. Source rent data is annual, so all twelve months of a year carry the same market-rent observation.

The model distinguishes **market rent** — what a new tenant would pay — from **actual renter rent**, what this particular tenant pays given local policy and their own tenure:

| Condition | Actual rent |
|---|---|
| Month 0 | Market rent |
| Market-rate city | Market rent |
| Renter moves this month | Resets to market rent |
| Otherwise (controlled) | Previous rent × (1 + control rate ÷ 12) |

Controlled rent is capped so it can never exceed market rent. City settings:

| City | Growth mode | Control rate | Annual move probability | Move cost multiplier |
|---|---|---:|---:|---:|
| Canada | mixed | 2.0% | 10% | 1.2 |
| Toronto | controlled | 2.5% | 8% | 1.8 |
| Vancouver | controlled | 3.0% | 7% | 2.0 |
| Calgary | market | — | 15% | 1.2 |
| Edmonton | market | — | 15% | 1.1 |
| Ottawa | controlled | 2.5% | 9% | 1.4 |
| Montreal | controlled | 2.5% | 10% | 1.2 |

In the current implementation, any non-`market` mode follows the controlled-rent branch. The `mixed` label is therefore currently behaviorally equivalent to `controlled` and is retained for possible future extension.

This structure captures the central economic feature of rent control: a long-tenured tenant accumulates a growing discount to market, and loses all of it on moving. Cities with high mobility and no control (Calgary, Edmonton) never build that discount.

### 19.2 Renter mobility

Moves are probabilistic but reproducible. The random seed is `42 + owner_scenario_id`, so rerunning the model reproduces the same move sequence exactly, and the same owner scenario generates identical moves across both portfolio variants — meaning any difference between the TSX and S&P 500 results is attributable to returns alone, never to divergent housing histories.

Monthly move probability is the annual probability ÷ 12. Month 0 is always forced to no move, since it represents the initial state.

```text
Move Cost = Actual Monthly Rent × Move Cost Multiplier
```

### 19.3 Monthly cash flow

```text
Renter Total Cash Outflow = Actual Rent + Move Cost

Owner Total Cash Outflow  = Mortgage Payment + Maintenance
                          + Property Tax + Insurance

Monthly Savings Difference = Owner Outflow − Renter Outflow
```

Note that owner cash outflow uses the **full mortgage payment**, including principal. Cash flow measures what leaves the household bank account; the equity treatment of principal belongs to the net-worth calculation (§17), not here.

---

## 20. Renter Investment and Portfolio

### 20.1 Monthly contribution

The final model assumes full investment discipline (100%):

| Savings difference | Action |
|---|---|
| Positive | Entire amount invested |
| Negative | Full shortfall withdrawn from portfolio |

Month 0 contribution is zero, because the renter's initial capital was already allocated at month 0. Adding a monthly contribution there would double-count it.

The symmetric treatment matters: when renting costs more than owning, the renter must draw down the portfolio rather than costlessly absorbing the difference. Without this, the renter would be given free consumption the owner does not receive.

### 20.2 Returns and costs

Monthly S&P 500 and TSX returns are calculated from **nominal CAD** market values, consistent with the simulation running on nominal cash flows (§21).

| Portfolio | Annual fee | Annual tax drag |
|---|---:|---:|
| TSX-only | 0.10% | 0.10% |
| S&P 500-only | 0.10% | 0.25% |

The higher drag on the U.S. portfolio reflects withholding tax on foreign dividends from a Canadian investor's perspective.

```text
Monthly Investment Cost = (Fee + Tax Drag) ÷ 12
Portfolio Return Net    = Portfolio Return − Monthly Investment Cost
```

### 20.3 Portfolio value

Month 0 opens at the initial renter investment. From month 1:

```text
New Portfolio Value = Previous Value × (1 + Net Return) + Monthly Investment
```

The portfolio floor is zero — it cannot go negative through withdrawals. Renter nominal net worth equals portfolio value.

---

## 21. Inflation-Adjusted Net Worth

The simulation runs entirely on **nominal** cash flows, keeping house prices, rent, mortgage payments, maintenance, taxes, insurance, contributions, and returns on one consistent basis. Mixing real and nominal quantities inside a compounding loop is a common source of subtle error, so deflation is applied only at the end.

After nominal net worth is complete, both sides are converted to real terms using each scenario's own starting-month CPI:

```text
Real Net Worth = Nominal Net Worth × Starting-Month CPI ÷ Current CPI
```

This produces `owner_net_worth_real` and `renter_net_worth_real` — **the primary wealth measures in the final report.**

### 21.1 Index fields

The database also stores `owner_net_worth_index` and `renter_net_worth_index`, normalizing real net worth to month 0 = 100.

These are retained as analytical fields but are **not** used in the final report, which is stated in inflation-adjusted dollar wealth rather than indexed growth. Dollar values also avoid a structural problem with the owner index: at month 0 the owner's net worth is down payment minus estimated sale cost, a small and occasionally negative base that makes an index built on it unstable.

---

## 22. Final Sensitivity Framework

The database supports a wider scenario space than the report uses. The final analysis varies:

```text
City  ×  Purchase Year  ×  Holding Period  ×  Mortgage Rate  ×  Renter Portfolio
```

with **down payment fixed at 20%** and **renter discipline fixed at 100%**.

The reason for fixing down payment is interpretive rather than technical. Different down payments require different starting capital, so comparing across them conflates two effects: the performance of the strategy, and the size of the initial capital base. Holding it constant means every difference in final wealth is attributable to the strategy and the market environment.

The 10% and 30% scenarios remain in PostgreSQL as evidence that the simulation engine generalizes, and as a ready extension path. They are excluded from reporting.

**Implementation note:** the 20% filter should be applied in the PostgreSQL view layer feeding Power BI, not left to a report slicer. If all three down-payment levels reach the model, any unfiltered aggregate silently averages across three different capital bases and produces figures with no economic interpretation.

---

## 23. Scenario Processing and Performance

The renter simulation is substantially larger than the owner simulation, since each owner scenario is multiplied by portfolio count.

Python processes renter scenarios in batches of **500 owner scenarios**:

```text
Read batch from PostgreSQL
      ↓
Merge stock returns and CPI
      ↓
Calculate renter scenarios
      ↓
Write temporary result table
      ↓
Update permanent table
      ↓
Drop temporary table and release memory
```

This keeps peak memory bounded regardless of total scenario count, allowing millions of monthly records to be processed without loading the full dataset at once.

### 23.1 Temporary result tables

Both engines write results to a temporary table first — `simulation._owner_monthly_results` and `simulation._renter_monthly_results` — then update the permanent table by join and drop the temporary table.

A bulk `to_sql` insert followed by a single set-based `UPDATE ... FROM` is far faster than row-by-row updates, and the update runs inside a transaction, so a failed batch leaves the permanent table unchanged rather than partially written.

---

## 24. Validation of Simulation Results

### Scenario structure
- every scenario begins at month 0
- monthly record count matches the holding period
- final month matches the intended sale date
- scenario identifiers remain consistent across owner and renter tables

### Mortgage
- no negative mortgage balances
- payment resets occur at renewal months
- principal never exceeds remaining balance
- month 0 payment is zero
- balance reaches zero at full amortization

### Renter
- no missing market-rent observations
- month 0 contains no move
- month 0 monthly investment is zero
- portfolio values never fall below zero
- rent resets to market on a move
- controlled rent never exceeds market rent

### Data alignment
- housing prices align with simulation dates
- stock returns align with monthly dates
- CPI is available for every simulation month
- mortgage rates are available for purchase and every renewal

### Financial reasonableness
- no implausible jumps in wealth
- rent changes are consistent with policy mode and move events
- mortgage-rate scenarios visibly affect mortgage interest
- the two portfolio scenarios produce different results
- final owner and renter outcomes reconcile with their underlying cash-flow paths

---

## 25. Limitations

**Coverage windows differ.** Source datasets do not all begin in the same year, so different parts of the analysis rest on different historical windows. City-level results start in 2005; national and equity comparisons reach back to 1990.

**Historical window constrains scenario coverage.** Scenarios are generated only where a sale-date price observation exists, so recent purchase years support progressively shorter holding periods. Coverage is therefore uneven across the purchase-year dimension, and city × holding-period cells should not be assumed to contain equal scenario counts.

**Frequency alignment.** Annual rent and quarterly housing observations are aligned to the monthly timeline. This makes joins possible but adds no underlying market information — within-year rent variation is not observed, and rent changes appear as annual steps.

**Benchmark prices are market averages.** Benchmark housing prices describe typical properties in a market, not any individual property, and understate the dispersion an actual buyer faces.

**Behavioral assumptions are stylized.** Moving probability, rent-control rates, move costs, maintenance rates, and structure ratios are fixed assumptions applied uniformly within each city. They describe a representative scenario, not any specific household.

**Rate scenarios are stress tests.** The ±2 percentage-point mortgage-rate scenarios are analytical sensitivities, not interest-rate forecasts.

**Full investment discipline is optimistic.** The renter is assumed to invest 100% of monthly savings without fail. Real households save less consistently, so renter outcomes should be read as an upper bound on the renting-and-investing strategy.

**Uniform framework across cities.** Tax treatment, insurance premiums, maintenance requirements, transaction costs, borrowing constraints, and investor behavior vary more across real Canadian markets than the model represents.

---

## 26. Summary

The pipeline is built as a layered PostgreSQL architecture rather than a collection of manually cleaned CSV files:

```text
Raw ingestion → staging transformation → validation
→ analytical transformation → scenario generation
→ Python simulation → Power BI reporting
```

The **market-level analysis** uses inflation-adjusted housing and equity series to compare long-term real asset performance.

The **household simulation** uses actual market prices and monthly cash flows to model mortgage amortization and interest, maintenance, property tax, insurance, rent, renter mobility, investment contributions, portfolio returns, and both nominal and inflation-adjusted net worth.

The final report fixes down payment at 20% and renter discipline at 100%, evaluating sensitivity across **city, purchase year, holding period, mortgage rate, and renter portfolio**. The primary outcome metrics are `owner_net_worth_real` and `renter_net_worth_real`.

This separation preserves full scenario flexibility in the database while presenting a narrower, more interpretable set of comparisons in the report.

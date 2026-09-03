# Rent-Invest vs Buy in Canada

**A historical scenario-analysis framework built on PostgreSQL, Python, and Power BI.**

This project evaluates the financial trade-off between buying a home and renting while investing using two connected historical analyses: a long-run asset comparison from 1990–2025 and a household-level simulation across six Canadian cities and a national benchmark from 2005–2025.

Most rent-versus-buy comparisons set rent against a mortgage payment. That framing is wrong in both directions: it treats mortgage principal as a cost when it is savings, and it treats the renter's capital as if it vanishes. This model instead simulates two complete household balance sheets, month by month, starting from identical capital.

> **Core question:** Under historical Canadian market conditions, when did buying outperform renting-and-investing — and which assumptions changed the answer?

---

## Power BI Report Preview

The Power BI dashboard supports interactive scenario exploration across **city, purchase year, holding period, mortgage-rate scenario, and renter portfolio**. Selected report pages are shown below.

|                                                                        |                                                                     |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------- |
| ![Long-run housing vs equity markets](docs/img/01-longrun-markets.png) | ![Regional housing performance](docs/img/02-regional-housing.png)   |
| ![Owner vs renter net worth paths](docs/img/03-networth-paths.png)     | ![Outcome sensitivity ranking](docs/img/04-sensitivity.png)         |

Additional report pages are included in the PDF export below.

### Report and Demo

- **[View the Power BI report PDF](power%20bi/power%20bi%20report.pdf)** — static export of the final report.
- **[Watch the video demo](power%20bi/Video%20Demo.mp4)** — walkthrough of slicers, filtering, and dynamic scenario interactions.

> **Power BI source file:** The final `.pbix` file is approximately **765 MB** and is therefore not stored in this repository because it exceeds GitHub's standard **100 MB per-file limit**. The PDF report and video demo are provided so the report design, results, and interactive workflow can still be reviewed directly from the repository.

---

## What This Model Does Differently

**Equal starting capital.** The renter begins with exactly the capital the owner committed to the property — down payment plus purchase cost, a constant 22% of purchase price under the reported assumptions.

**Symmetric cash-flow treatment.** Monthly cash-flow differences are explicitly transferred to or withdrawn from the renter portfolio. When owning requires more cash, the renter invests the difference; when renting requires more cash, the renter withdraws the shortfall. This creates a consistent monthly resource-allocation framework without treating renter savings as free consumption.

**Principal is not a cost.** Mortgage principal appears in owner cash outflow, because it must be funded each month, but is excluded from unrecoverable cost, because it converts to equity.

**Liquidation-equivalent wealth.** Owner net worth subtracts an estimated 6% sale cost at every point, making it directly comparable to a portfolio balance.

**Portfolio choice is a variable, not an assumption.** The renter's alternative is modelled as TSX-only or S&P 500-only, revealing that portfolio selection can outweigh the buy-versus-rent decision itself.

**City-specific renter behaviour.** Rent control, move probability, and moving costs vary by market, with moves generated from a fixed seed so results are reproducible and comparable across portfolio variants.

---

## Headline Findings

### Long-run asset performance, 1990–2025

| Asset                 | Real CAGR |
| --------------------- | ---------:|
| **S&P 500 (CAD)**     | **7.1%**  |
| **S&P/TSX Composite** | **3.9%**  |
| **Canada Housing**    | **2.0%**  |

### Regional housing, 2005–2025

| Market      | Real CAGR |     | Market         | Real CAGR |
| ----------- | ---------:| --- | -------------- | ---------:|
| **S&P 500** | **7.22%** |     | Canada Housing | 2.87%     |
| Vancouver   | 4.14%     |     | Ottawa         | 2.59%     |
| **TSX**     | **3.84%** |     | Calgary        | 2.48%     |
| Montreal    | 3.34%     |     | Edmonton       | 2.14%     |
| Toronto     | 3.17%     |     |                |           |

Vancouver was the strongest Canadian housing market and the only city to beat the TSX. No city matched U.S. equities.

### An illustrative household scenario

Canada-wide benchmark · purchased 2005 · 20-year hold · 20% down · Base rates · **TSX portfolio**

| Measure                      | Owner       | Renter-Investor |
| ---------------------------- | -----------:| ---------------:|
| Average monthly cash outflow | $1,520      | $903            |
| Cash-outflow CAGR            | 1.66%       | 3.21%           |
| **Final real net worth**     | **$372.7K** | **$441.7K**     |

The renter finished about **$69K ahead** — despite the owner leading for most of the middle of the period, and despite the renter holding the weaker of the two portfolios.

> **This is the national benchmark series, not a city.** Across the six individual markets under the same assumptions, the owner finished ahead in every case: Vancouver 2.72, Montreal 1.19, Edmonton 1.18, Calgary 1.05, Ottawa 1.03, Toronto 1.01 (owner ÷ renter final real net worth). The national series pairs national average prices with national average rents, so its cash-flow position does not describe any single market. Market-by-market results are in the key findings.

### What actually moves the result

**Portfolio choice and mortgage rates are equivalent at short horizons, then diverge.** At five years the TSX-versus-S&P 500 net-worth range and the Base-versus-Base+2pp range are nearly equal in every market tested — a ratio between **0.9× and 1.2× across all seven series**. By fifteen years the ratio reaches 2.2× to 4.8×. Because both drivers range over exactly two tested values at every horizon, this is the comparison least affected by the shrinking-cohort issue that limits purchase-timing comparisons. In one Calgary scenario the 20-year figures were about $352K for portfolio against $82K for mortgage rate.

**Mortgage rates primarily transmit through cash flow in the illustrated long-horizon scenario.** In the Calgary 2005 / 20-year / TSX case, moving from Base to Base +2pp reduced owner final real net worth by about $6K while increasing renter final real net worth by about $76K. Higher mortgage payments increased the owner-renter monthly cash-flow difference, creating additional investment contributions for the renter.

**Expensive housing does not mean expensive to hold.** Vancouver was the only market where the owner's average monthly outflow was *lower* than the renter's (0.83×), and it produced the strongest owner result. It has the lowest residential property-tax rate of any major Canadian city, and land makes up an unusually large share of property value there, so the structure subject to maintenance is proportionally smaller. Lighter carrying costs narrow the monthly gap that funds the renter's portfolio — which is also why Vancouver shows the weakest portfolio sensitivity of any market tested.

**Entry timing dominates short horizons.** For five-year holds, outcomes in a single city swung from a large owner advantage to a six-figure owner shortfall depending only on purchase year.

> **Note on 20-year figures:** Housing data extends to March 2026 while the simulation horizon ends December 2025, so a small number of 2006-entry cohorts are truncated before reaching their sale month. Twenty-year figures are provisional pending exclusion of those scenarios at generation.

Full results and interpretation: [`docs/key_findings.md`](docs/key_findings.md)

---

## Architecture

```text
Source CSVs
     ↓
raw schema          →  imported with minimal transformation, validated
     ↓
stg schema          →  typed, standardized, validated
     ↓
analysis schema     →  real indexes, CAGR, long-format inputs
     ↓
simulation schema   →  scenario generation, monthly schedules
     ↓
Python engines      →  mortgage amortization, rent paths, portfolio compounding
     ↓
Power BI            →  filtering, DAX measures, sensitivity analysis
```

| Tool           | Role                                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------------------- |
| **PostgreSQL** | Storage, cleaning, transformation, validation, scenario generation, monthly schedules                     |
| **Python**     | State-dependent monthly calculations: amortization, renewals, rent paths, mobility, portfolio compounding |
| **Power BI**   | Interactive filtering, DAX measures, sensitivity visualization                                            |

The split follows a simple rule: **PostgreSQL handles storage, transformations, scenario construction, and values that can be determined from the current row or period; Python handles state-dependent monthly calculations that rely on prior-period results.** Power BI does not reimplement the model — it consumes finished outputs.

---

## Repository Structure

```text
sql/
  01_create_raw_tables.SQL              schema + raw table definitions
  02_load_raw_data.sql                  \copy loads, per-city consolidation
  02_check_raw_data.SQL                 raw-layer validation
  03_01_create_staging_tables.SQL       typing, date parsing, pivoting
  03_02_check_staging_data.sql          staging validation
  04_analysis1_create_real_asset_indexes.sql
  04_analysis1_check_real_asset_indexes.sql
  04_analysis2_create_asset_cagr.sql
  04_analysis2_check_asset_cagr.sql
  05_create_owner_simulation_table.sql  owner scenarios + monthly schedule
  06_create_renter_simulation_table.sql renter scenarios + monthly schedule

python/
  05_calculate_owner_schedule.py        mortgage amortization engine
  06_calculate_renter_schedule.py       rent, mobility, portfolio engine

docs/
  data_source.md
  Data_Cleaning_Transformation_and_Preparation.md
  simulation_methodology.md
  key_findings.md

power bi/
  power bi report.pdf                     static export of the final Power BI report
  Video Demo.mp4                          walkthrough of interactive report behaviour
```

---

## Reproducing the Analysis

**Requirements:** PostgreSQL 14+, Python 3.10+, and `pandas`, `numpy`, `sqlalchemy`, `psycopg2-binary`.

**1 — Create the database**

```bash
createdb rentvsbuy
export POSTGRES_PASSWORD=your_password
```

On Windows PowerShell:

```powershell
$env:POSTGRES_PASSWORD="your_password"
```

**2 — Place source data**

Download the files listed under [Data Sources](#data-sources) into `data/raw/`, following the subfolder layout referenced in `02_load_raw_data.sql`. The `\copy` paths in that script are absolute and will need to be adjusted for your machine.

**3 — Build the database**

Run in order; the check scripts are optional but recommended between stages.

```bash
psql -d rentvsbuy -f sql/00_create_schemas.sql
psql -d rentvsbuy -f sql/01_create_raw_tables.SQL
psql -d rentvsbuy -f sql/02_load_raw_data.sql
psql -d rentvsbuy -f sql/02_check_raw_data.SQL
psql -d rentvsbuy -f sql/03_01_create_staging_tables.SQL
psql -d rentvsbuy -f sql/03_02_check_staging_data.sql
psql -d rentvsbuy -f sql/04_analysis1_create_real_asset_indexes.sql
psql -d rentvsbuy -f sql/04_analysis2_create_asset_cagr.sql
```

**4 — Run the simulation**

```bash
psql -d rentvsbuy -f sql/05_create_owner_simulation_table.sql
python  python/05_calculate_owner_schedule.py
psql -d rentvsbuy -f sql/06_create_renter_simulation_table.sql
python  python/06_calculate_renter_schedule.py
```

The owner engine writes to a temporary table and updates the permanent schedule in a single transaction. The renter engine processes 500 owner scenarios per batch to bound memory.

**5 — Review the Power BI report**

The repository includes a [PDF export](power%20bi/power%20bi%20report.pdf) and a [video demo](power%20bi/Video%20Demo.mp4) of the final Power BI report. The `.pbix` source file is not included because its approximately 765 MB size exceeds GitHub's standard per-file limit.

> **Note on re-runs:** `renter_monthly_schedule` holds a foreign key to `owner_monthly_schedule`, so re-running step 4 requires dropping the renter table first, or changing the owner drop to `DROP TABLE ... CASCADE`.

---

## The Model at a Glance

Full specification: [`docs/simulation_methodology.md`](docs/simulation_methodology.md)

### Reporting scope

| Dimension             | Values                                                          |
| --------------------- | --------------------------------------------------------------- |
| City                  | Vancouver, Calgary, Edmonton, Toronto, Ottawa, Montreal, plus a national benchmark |
| Purchase year         | Every year with a completed scenario at the given holding period |
| Holding period        | 5 / 10 / 15 / 20 years                                          |
| Mortgage rate         | Lower (−2pp) · Base · Higher (+2pp)                             |
| Renter portfolio      | TSX-only · S&P 500-only                                         |
| **Down payment**      | **Fixed at 20%**                                                |
| **Renter discipline** | **Fixed at 100%**                                               |

The number of available purchase years falls as the holding period lengthens, since city-level price data begins in 2005 and the simulation horizon ends in December 2025 — roughly sixteen entry years at the 5-year horizon against one at 20 years. Sensitivity figures that range over purchase year are therefore not directly comparable across holding periods.

Down payment is held constant because different levels require different starting capital, which would conflate the performance of a strategy with the size of its capital base. The 10% and 30% scenarios remain in the database for extension.

The underlying PostgreSQL simulation engine contains a broader set of monthly purchase-date and down-payment scenarios than those exposed in the final report.

### Core assumptions

| Assumption                   | Value                                |
| ---------------------------- | ------------------------------------ |
| Mortgage term / amortization | 5 years / 25 years                   |
| Purchase cost                | 2% of purchase price                 |
| Sale cost                    | 6% of market value                   |
| Maintenance                  | 1.5% of **structure value** per year |
| Insurance                    | 0.3% of market value per year        |
| Property tax                 | 0.30%–1.20%, city-specific           |
| Structure ratio              | 0.35–0.60, city-specific             |
| Investment fees              | 0.10% annually, both portfolios      |
| Tax drag                     | 0.10% (TSX) · 0.25% (S&P 500)        |

Maintenance is applied to the estimated structural portion of the property rather than total market value as a simplifying assumption intended to separate building-related upkeep from land value. The structure ratio varies sharply by market — Vancouver's 0.35 reflects the relatively large land-value component of total property value there.

### Key formulas

```text
Owner Net Worth  = House Market Value − Mortgage Balance − Estimated Sale Cost
Renter Net Worth = Portfolio Value

Owner Cash Outflow  = Mortgage Payment + Maintenance + Property Tax + Insurance
Renter Cash Outflow = Actual Rent + Moving Cost
Savings Difference  = Owner Cash Outflow − Renter Cash Outflow

Real Net Worth = Nominal Net Worth × Starting-Month CPI ÷ Current CPI
```

The simulation runs entirely in nominal CAD and deflates only at the end, so no compounding loop mixes real and nominal quantities. Reported outcomes use `owner_net_worth_real` and `renter_net_worth_real`.

---

## Data Sources

| Data                          | Source                                                   | Use                                                                            |
| ----------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Canada national housing index | BIS Residential Property Price Statistics (`Q.CA.R.628`) | Long-run national analysis. Published in real terms — no CPI deflation applied |
| City HPI and benchmark prices | CREA MLS® Home Price Index                               | Regional analysis and dollar-denominated simulation                            |
| Teranet–National Bank HPI     | housepriceindex.ca                                       | Loaded and staged for reference; not used downstream                           |
| S&P 500                       | Yahoo Finance `^GSPC`, monthly                           | Market comparison and renter portfolio                                         |
| S&P/TSX Composite             | Yahoo Finance `^GSPTSE`, monthly                         | Market comparison and renter portfolio                                         |
| VT                            | Yahoo Finance `VT`, monthly                              | Retained for supporting analysis; not used as a final renter-portfolio option  |
| USD/CAD                       | FRED `DEXCAUS`, daily                                    | Converting USD assets to CAD                                                   |
| Consumer Price Index          | Statistics Canada 18-10-0004-01                          | Inflation adjustment                                                           |
| 5-year mortgage rate          | Statistics Canada 34-10-0145-01                          | Mortgage simulation and sensitivity                                            |
| City rents                    | CMHC Rental Market Survey (HMIP)                         | Renter cash-flow simulation                                                    |

Retrieval parameters, coverage windows, and source quirks: [`docs/data_source.md`](docs/data_source.md)

---

## Validation

Checks run at every stage rather than at the end:

| Stage          | Checks                                                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Raw            | Row counts, date ranges, city coverage, duplicate city-date pairs                                                               |
| Staging        | Row counts, date ranges, duplicate dates, type-cast failures                                                                    |
| Scenario       | Every scenario starts at month 0; month count matches holding period; owner and renter identifiers align                        |
| Mortgage       | No negative balances; resets at renewal months; principal never exceeds balance; balance reaches zero at full amortization      |
| Renter         | No missing rent or CPI; month 0 has no move and no contribution; portfolio never negative; controlled rent never exceeds market |
| Cross-scenario | Higher rates raise financing costs; portfolios diverge; outcomes reconcile with underlying monthly paths                        |

Making these explicit scripts rather than ad-hoc review means they can be re-run after any source refresh.

---

## Directional Effects of Modelling Choices

Three choices measurably tilt the comparison, and they do **not** all point the same way:

| Choice                                                   | Direction                                                   |
| -------------------------------------------------------- | ----------------------------------------------------------- |
| Equity series exclude reinvested dividends               | Understates renter portfolio growth → **favours the owner** |
| Mortgage rates are posted, not discounted                | Overstates owner financing cost → **favours the renter**    |
| Illustrative scenarios use the TSX, the weaker portfolio | Understates the renter outcome → **favours the owner**      |

Because these effects operate in different directions, the model should not be interpreted as being uniformly conservative toward either strategy. Instead, they should be treated as directional modeling limitations when interpreting individual scenarios.

---

## Limitations

**Historical analysis, not forecasting.** The model shows how buying and renting would have performed under historical housing, equity, inflation, rent, and mortgage conditions. Past performance does not predict future results, and the ±2 percentage-point mortgage-rate scenarios should be interpreted as stress tests rather than forecasts.

**Wealth is concentrated in one main asset on each side.** Owner wealth is mainly represented by home equity, while renter wealth is represented by the investment portfolio. As the mortgage balance declines over longer holding periods, owner outcomes become increasingly driven by house-price performance, while renter outcomes become increasingly driven by stock-market performance. The model therefore does not represent a complete household balance sheet with additional savings, investments, or other assets.

**Equity returns exclude reinvested dividends.** The TSX and S&P 500 series are based on price movements rather than total returns. This understates long-term renter portfolio growth compared with a strategy that reinvests dividends and therefore tends to favour the owner in longer holding periods.

**Historical coverage is uneven.** City-level housing data begins in 2005, so twenty-year holding periods are available only for the earliest purchase cohorts. Purchase year and holding period are therefore partly constrained by data availability, meaning longer-horizon results are based on fewer historical periods than shorter-horizon results.

**Data granularity limits realism.** Rent observations are annual and applied across each calendar year, while benchmark housing prices represent typical market properties rather than individual transactions. The model therefore captures broad market conditions rather than property-specific or lease-specific experiences.

**Behavioural assumptions are simplified.** Move probabilities, rent-control assumptions, moving costs, maintenance rates, and structure-value ratios are fixed within the model. They represent a standardized household rather than any individual household. The 100% investment-discipline assumption also represents a highly disciplined renter who consistently invests available savings, which strengthens renter outcomes compared with less consistent saving behaviour.

**The comparison is financial only.** The model does not assign monetary value to lifestyle factors such as housing stability, flexibility to move, renovation freedom, school catchment, or the time and effort required to maintain a home. These factors can materially affect a real household’s rent-versus-buy decision even when they do not appear in net worth.

---

## Documentation

| Document                                                                           | Contents                                                       |
| -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [`docs/data_source.md`](docs/data_source.md)                                                                   | Source URLs, retrieval parameters, coverage, known data quirks |
| [`docs/Data_Cleaning_Transformation_and_Preparation.md`](docs/Data_Cleaning_Transformation_and_Preparation.md) | Pipeline layers, transformations, validation                   |
| [`docs/simulation_methodology.md`](docs/simulation_methodology.md)                                             | Full financial model specification                             |
| [`docs/key_findings.md`](docs/key_findings.md)                                                                 | Results and interpretation                                     |

Start with the methodology document for the model, or key findings for the results.

---

## Tech Stack

`PostgreSQL` · `SQL` · `Python` · `pandas` · `NumPy` · `SQLAlchemy` · `Power BI` · `DAX` · `Git`

---

## Takeaway

The project produces no universal answer, because the historical record does not contain one. The outcome depends on the interaction of city, purchase timing, holding period, financing conditions, and — most of all — what the renter does with the capital not spent on a house.

The comparison that matters is not rent against a mortgage payment. It is one household balance sheet against another, under the same starting capital and the same monthly budget.

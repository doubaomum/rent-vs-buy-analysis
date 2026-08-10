# Rent-Invest vs Buy in Canada

**A historical scenario-analysis framework built on PostgreSQL, Python, and Power BI.**

This project evaluates the financial trade-off between buying a home and renting while investing using two connected historical analyses: a long-run asset comparison from 1990–2025 and a household-level simulation across seven Canadian housing markets from 2005–2025.

Most rent-versus-buy comparisons set rent against a mortgage payment. That framing is wrong in both directions: it treats mortgage principal as a cost when it is savings, and it treats the renter's capital as if it vanishes. This model instead simulates two complete household balance sheets, month by month, starting from identical capital.

> **Core question:** Under historical Canadian market conditions, when did buying outperform renting-and-investing — and which assumptions changed the answer?

---

## Power BI Report Preview

The Power BI dashboard supports interactive scenario exploration across **city, purchase year, holding period, mortgage-rate scenario, and renter portfolio**. Selected report pages are shown below.

| | |
|---|---|
| ![Power BI dashboard preview 1](image.png) | ![Power BI dashboard preview 2](image-1.png) |
| ![Power BI dashboard preview 3](image-2.png) | ![Power BI dashboard preview 4](image-3.png) |
| ![Power BI dashboard preview 5](image-4.png) | ![Power BI dashboard preview 6](image-5.png) |
| ![Power BI dashboard preview 7](image-6.png) | ![Power BI dashboard preview 8](image-7.png) |
| ![Power BI dashboard preview 9](image-8.png) | ![Power BI dashboard preview 10](image-9.png) |

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

| Asset | Real CAGR |
|---|---:|
| **S&P 500 (CAD)** | **7.1%** |
| **S&P/TSX Composite** | **3.9%** |
| **Canada Housing** | **2.0%** |

### Regional housing, 2005–2025

| Market | Real CAGR | | Market | Real CAGR |
|---|---:|---|---|---:|
| **S&P 500** | **7.22%** | | Canada Housing | 2.87% |
| Vancouver | 4.14% | | Ottawa | 2.59% |
| **TSX** | **3.84%** | | Calgary | 2.48% |
| Montreal | 3.34% | | Edmonton | 2.14% |
| Toronto | 3.17% | | | |

Vancouver was the strongest Canadian housing market and the only city to beat the TSX. No city matched U.S. equities.

### An illustrative household scenario

Canada-wide benchmark · purchased 2005 · 20-year hold · 20% down · Base rates · **TSX portfolio**

| Measure | Owner | Renter-Investor |
|---|---:|---:|
| Average monthly cash outflow | $1,520 | $903 |
| Cash-outflow CAGR | 1.66% | 3.21% |
| **Final real net worth** | **$372.7K** | **$441.7K** |

The renter finished about **$69K ahead** — despite the owner leading for most of the middle of the period, and despite the renter holding the weaker of the two portfolios.

### What actually moves the result

**Portfolio choice was the largest tested sensitivity in several long-horizon scenarios.** In one Calgary scenario, switching the renter from TSX to S&P 500 moved the final real net-worth gap by about $352K, compared with about $82K for a Base-to-Higher mortgage-rate change. Portfolio effects grow strongly with holding period because returns compound directly on the portfolio balance, while mortgage-rate effects operate primarily through the homeowner's monthly financing cash flow.

**Mortgage rates primarily transmit through cash flow in the illustrated long-horizon scenario.** In the Calgary 2005 / 20-year / TSX case, moving from Base to Base +2pp reduced owner final real net worth by about $6K while increasing renter final real net worth by about $76K. Higher mortgage payments increased the owner-renter monthly cash-flow difference, creating additional investment contributions for the renter.

**Entry timing dominates short horizons.** For five-year holds, outcomes in a single city swung from a large owner advantage to a six-figure owner shortfall depending only on purchase year.

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

| Tool | Role |
|---|---|
| **PostgreSQL** | Storage, cleaning, transformation, validation, scenario generation, monthly schedules |
| **Python** | State-dependent monthly calculations: amortization, renewals, rent paths, mobility, portfolio compounding |
| **Power BI** | Interactive filtering, DAX measures, sensitivity visualization |

The split follows a simple rule: **PostgreSQL handles storage, transformations, scenario construction, and values that can be determined from the current row or period; Python handles state-dependent monthly calculations that rely on prior-period results.** Power BI does not reimplement the model — it consumes finished outputs.

---

## Repository Structure

```text
sql/
  00_create_schemas.sql                  create raw / stg / analysis / simulation schemas
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

| Dimension | Values |
|---|---|
| City | Canada, Vancouver, Calgary, Edmonton, Toronto, Ottawa, Montreal |
| Purchase year | 2005 / 2010 / 2015 / 2020 |
| Holding period | 5 / 10 / 15 / 20 years |
| Mortgage rate | Lower (−2pp) · Base · Higher (+2pp) |
| Renter portfolio | TSX-only · S&P 500-only |
| **Down payment** | **Fixed at 20%** |
| **Renter discipline** | **Fixed at 100%** |

Down payment is held constant because different levels require different starting capital, which would conflate the performance of a strategy with the size of its capital base. The 10% and 30% scenarios remain in the database for extension.

The underlying PostgreSQL simulation engine contains a broader set of monthly purchase-date and down-payment scenarios than those exposed in the final report.

### Core assumptions

| Assumption | Value |
|---|---|
| Mortgage term / amortization | 5 years / 25 years |
| Purchase cost | 2% of purchase price |
| Sale cost | 6% of market value |
| Maintenance | 1.5% of **structure value** per year |
| Insurance | 0.3% of market value per year |
| Property tax | 0.30%–1.20%, city-specific |
| Structure ratio | 0.35–0.60, city-specific |
| Mortgage insurance | 3.1% of loan at 10% down; zero at 20% |
| Investment fees | 0.10% annually, both portfolios |
| Tax drag | 0.10% (TSX) · 0.25% (S&P 500) |

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

| Data | Source | Use |
|---|---|---|
| Canada national housing index | BIS Residential Property Price Statistics (`Q.CA.R.628`) | Long-run national analysis. Published in real terms — no CPI deflation applied |
| City HPI and benchmark prices | CREA MLS® Home Price Index | Regional analysis and dollar-denominated simulation |
| Teranet–National Bank HPI | housepriceindex.ca | Loaded and staged for reference; not used downstream |
| S&P 500 | Yahoo Finance `^GSPC`, monthly | Market comparison and renter portfolio |
| S&P/TSX Composite | Yahoo Finance `^GSPTSE`, monthly | Market comparison and renter portfolio |
| VT | Yahoo Finance `VT`, monthly | Retained for supporting analysis; not used as a final renter-portfolio option |
| USD/CAD | FRED `DEXCAUS`, daily | Converting USD assets to CAD |
| Consumer Price Index | Statistics Canada 18-10-0004-01 | Inflation adjustment |
| 5-year mortgage rate | Statistics Canada 34-10-0145-01 | Mortgage simulation and sensitivity |
| City rents | CMHC Rental Market Survey (HMIP) | Renter cash-flow simulation |

Retrieval parameters, coverage windows, and source quirks: [`docs/data_source.md`](docs/data_source.md)

---

## Validation

Checks run at every stage rather than at the end:

| Stage | Checks |
|---|---|
| Raw | Row counts, date ranges, city coverage, duplicate city-date pairs |
| Staging | Row counts, date ranges, duplicate dates, type-cast failures |
| Scenario | Every scenario starts at month 0; month count matches holding period; owner and renter identifiers align |
| Mortgage | No negative balances; resets at renewal months; principal never exceeds balance; balance reaches zero at full amortization |
| Renter | No missing rent or CPI; month 0 has no move and no contribution; portfolio never negative; controlled rent never exceeds market |
| Cross-scenario | Higher rates raise financing costs; portfolios diverge; outcomes reconcile with underlying monthly paths |

Making these explicit scripts rather than ad-hoc review means they can be re-run after any source refresh.

---

## Directional Effects of Modelling Choices

Three choices measurably tilt the comparison, and they do **not** all point the same way:

| Choice | Direction |
|---|---|
| Equity series exclude reinvested dividends | Understates renter portfolio growth → **favours the owner** |
| Mortgage rates are posted, not discounted | Overstates owner financing cost → **favours the renter** |
| Illustrative scenarios use the TSX, the weaker portfolio | Understates the renter outcome → **favours the owner** |

Because these effects operate in different directions, the model should not be interpreted as being uniformly conservative toward either strategy. Instead, they should be treated as directional modeling limitations when interpreting individual scenarios.

---

## Limitations

**This is historical scenario analysis, not forecasting.** Past housing and equity performance does not predict future returns, and the ±2pp rate scenarios are stress tests rather than projections.

**Coverage is uneven by design.** City-level prices begin in 2005, so twenty-year holds exist only for 2005 entries. Holding period and purchase year are structurally correlated. Twenty-year results therefore represent a much narrower set of purchase cohorts and provide less cross-cohort evidence than shorter holding periods.

**Data granularity limits realism.** Rent observations are annual and carried across each calendar year. Benchmark prices describe typical market properties, not individual transactions.

**Behavioural assumptions are stylized.** Move probabilities, rent-control rates, move costs, maintenance rates, and structure ratios are fixed per city and describe a representative household, not any real one. The 100% investment-discipline assumption represents a highly disciplined renter-investor and tends to strengthen renter outcomes relative to less consistent saving behaviour.

**Scope is financial only.** Housing stability, mobility, renovation freedom, school catchment, and maintenance effort carry real value and are entirely outside this comparison.

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/data_source.md`](docs/data_source.md) | Source URLs, retrieval parameters, coverage, known data quirks |
| [`docs/Data_Cleaning_Transformation_and_Preparation.md`](docs/Data_Cleaning_Transformation_and_Preparation.md) | Pipeline layers, transformations, validation |
| [`docs/simulation_methodology.md`](docs/simulation_methodology.md) | Full financial model specification |
| [`docs/key_findings.md`](docs/key_findings.md) | Results and interpretation |

Start with the methodology document for the model, or key findings for the results.

---

## Tech Stack

`PostgreSQL` · `SQL` · `Python` · `pandas` · `NumPy` · `SQLAlchemy` · `Power BI` · `DAX` · `Git`

---

## Takeaway

The project produces no universal answer, because the historical record does not contain one. The outcome depends on the interaction of city, purchase timing, holding period, financing conditions, and — most of all — what the renter does with the capital not spent on a house.

The comparison that matters is not rent against a mortgage payment. It is one household balance sheet against another, under the same starting capital and the same monthly budget.

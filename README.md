# Rent vs. Buy in Canada

**Two choices. One starting budget. Thirty years of market data.**

Should you buy a home? Or rent and invest the difference?

A mortgage payment alone cannot answer that question. Part of it builds equity. And a renter can invest the cash that a buyer puts into a home.

This project compares **two household balance sheets**, month by month. Both start with the same capital. One buys a home. The other rents and invests. Historical Canadian data drives both paths.

The project uses **PostgreSQL, Python, and Power BI**. It covers six cities and a Canada-wide benchmark. The published report focuses on historical results through 2025; the data pipelines can refresh later observations.

> **The question:** When did buying win? When did renting and investing win? What changed the result?

## See the work

| | |
|---|---|
| ![Power BI report screenshot 1](power%20bi/image/image-1.png) | ![Power BI report screenshot 2](power%20bi/image/image-2.png) |
| ![Power BI report screenshot 3](power%20bi/image/image-3.png) | ![Power BI report screenshot 4](power%20bi/image/image-4.png) |

**[Power BI report (PDF)](power%20bi/power%20bi%20report.pdf)** · **[Video demo](power%20bi/Video%20Demo.mp4)** · **[Key findings](docs/key_findings.md)**

The `.pbix` file is about 765 MB. It exceeds GitHub's standard 100 MB file limit, so this repository provides a PDF and a video instead.

## The rules of the comparison

- **Start equal.** The renter invests the buyer's down payment and purchase costs. In the reported 20%-down scenarios, that is 22% of the home price.
- **Count every cash flow.** When owning costs more in a month, the renter invests the difference. When renting costs more, the renter draws from the portfolio.
- **Treat principal as equity.** Mortgage principal is cash paid, but not an unrecoverable cost.
- **Account for selling.** Owner net worth includes an estimated 6% selling cost.
- **Test two portfolios.** The renter invests in either the S&P 500 or the TSX.
- **Use local rent rules.** Rent growth, moving costs, and move probabilities vary by city. A fixed random seed keeps the simulated moves reproducible.

## What the historical data showed

### Long-run returns, 1990–2025

| Asset | Real CAGR |
|---|---:|
| S&P 500 in CAD | **7.1%** |
| S&P/TSX Composite | **3.9%** |
| Canadian housing | **2.0%** |

### Regional comparison, 2005–2025

| Market or asset | Real CAGR |
|---|---:|
| S&P 500 | **7.22%** |
| Vancouver housing | **4.14%** |
| TSX | **3.84%** |
| Montreal housing | 3.34% |
| Toronto housing | 3.17% |
| Canada housing | 2.87% |
| Ottawa housing | 2.59% |
| Calgary housing | 2.48% |
| Edmonton housing | 2.14% |

Vancouver led the six housing markets. It was the only one to beat the TSX in this comparison. None beat the S&P 500.

### One household, two outcomes

**Canada benchmark · Buy in 2005 · Hold 20 years · 20% down · Base mortgage rate · Renter invests in TSX**

| Measure | Owner | Renter-investor |
|---|---:|---:|
| Average monthly cash outflow | $1,520 | $903 |
| Cash-outflow CAGR | 1.66% | 3.21% |
| **Final real net worth** | **$372.7K** | **$441.7K** |

**The renter ended about $69K ahead.** Yet the owner led for much of the middle of the period.

This result uses the **national benchmark**, not a real city. In the six individual markets, the owner won under the same scenario settings. Final owner-to-renter net-worth ratios were Vancouver 2.72, Montreal 1.19, Edmonton 1.18, Calgary 1.05, Ottawa 1.03, and Toronto 1.01. National average prices and rents do not describe any one local market.

### What changed the result

**Portfolio choice mattered more over time.** At five years, switching portfolios and adding two percentage points to the mortgage rate had similar effects. By fifteen years, the portfolio effect was 2.2–4.8 times the rate effect across the tested markets. In one 20-year Calgary case, the ranges were about $352K and $82K.

**Mortgage rates changed the renter's investment path.** In the Calgary 2005 / 20-year / TSX example, a two-point rate increase cut owner net worth by about $6K. It raised renter net worth by about $76K. The higher owner payment meant more money for the renter to invest.

**High home prices did not always mean high holding costs.** In the reported Vancouver scenario, owner cash outflow averaged 0.83 times renter cash outflow. The model's low property-tax and structure-value assumptions helped produce that result.

**Timing mattered most over short holds.** A five-year outcome could shift from a strong owner win to a six-figure loss just by changing the purchase year.

> **Historical-report caveat:** The reported 20-year comparison uses the original 2025 simulation horizon. Some 2006-entry scenarios were truncated before their planned sale. Those results were flagged as provisional in the original analysis. The refreshable database now covers later observations, but the figures above have not been represented as newly recalculated results.

Read the full evidence in **[Key Findings](docs/key_findings.md)**.

## How the system works

```text
FRED · Statistics Canada · Yahoo Finance · CMHC · CREA · BIS · Teranet
                              |
                              v
                         PostgreSQL RAW
                              |
                    clean and reconcile
                              v
                       PostgreSQL STAGING
                              |
                   transform and validate
                              v
                      PostgreSQL ANALYSIS
                              |
                       build scenarios
                              v
                  OWNER / RENTER SIMULATION
                  SQL inputs + Python engines
                              |
                              v
                            Power BI
```

**PostgreSQL** stores records, prepares inputs, and builds scenarios. **Python** calculates monthly paths that depend on prior months. **Power BI** presents the results; it does not recalculate the financial model.

### Repository structure

The repository separates SQL, Python calculations, tests, and documentation.

```text
rent-vs-buy-analysis/
├── .gitignore
├── README.md
├── requirements.txt
├── rent-vs-buy-interactive-presentation.html
├── rent-vs-buy-presentation.html
├── docs/
│   ├── data_cleaning.md
│   ├── DATA_RECONCILIATION.md
│   ├── data_source.md
│   ├── data_update.md
│   ├── key_findings.md
│   ├── simulation_methodology.md
│   └── validation - testing.md
├── power bi/
│   ├── power bi report.pdf
│   ├── Video Demo.mp4
│   └── image/                  # Report screenshots
└── SQL-Python/
    ├── check_SQL/
    │   ├── 1. raw_schema_checks.sql
    │   ├── 2. staging_schema_checks.sql
    │   ├── 3. analysis_schema_checks.sql
    │   └── 4. simulation_checks.sql
    ├── create_SQL/
    │   ├── 01_create_raw_tables.SQL
    │   ├── 02_load_raw_data.sql
    │   ├── 03_create_staging_tables.SQL
    │   ├── 04_analysis_refresh_asset_cagr.sql
    │   ├── 04_analysis_refresh_long_tables.sql
    │   ├── 04_analysis_refresh_real_asset_indexes.sql
    │   ├── 05_refresh_owner_months.sql
    │   ├── 05_refresh_owner_scenarios.sql
    │   ├── 06_prepare_renter_refresh.sql
    │   └── 06_refresh_renter_months.sql
    ├── update_python/
    │   ├── reconciliation.py
    │   ├── update_fred.py
    │   ├── update_cpi.py
    │   ├── update_sp500.py
    │   ├── update_tsx.py
    │   ├── update_mortgage.py
    │   ├── update_rent.py
    │   ├── update_city_house_prices.py
    │   ├── update_bis_house_index.py
    │   ├── update_city_house_index.py
    │   ├── update_analysis.py
    │   ├── update_owner.py
    │   └── update_renter.py
    ├── simulation_python/
    │   ├── owner_calculations.py
    │   └── renter_calculations.py
    ├── test_rollback_python/
    │   └── test_fred_rollback.py
    └── reconciliation_reports/ # JSON audit reports from local runs
```

`API.env` is kept locally under `SQL-Python/update_python/`. It holds credentials. **Never commit it.** Python `__pycache__` folders are generated files, not project source.

The two HTML presentations sit at the repository root. The PDF, video, and screenshots sit under `power bi/`.

## Data refresh and reconciliation

Each source follows a simple rule:

**Refresh → Reconcile → Record changes → Investigate surprises → Rerun.**

The scripts compare incoming data with RAW, then check RAW against STAGING. They count inserts, updates, and unchanged records. They save JSON reports. A failed check stops the transaction before commit.

Nine source pipelines have passed local reconciliation runs:

| Source | Pipeline |
|---|---|
| FRED | USD/CAD exchange rate |
| Statistics Canada | CPI |
| Yahoo Finance | S&P 500 |
| Yahoo Finance | TSX |
| Statistics Canada | Five-year mortgage rate |
| CMHC | City rents |
| CREA | City benchmark prices and HPI |
| BIS | Real Canadian house-price index |
| Teranet | C11 house-price index |

The **Analysis** refresh also passed its key, completeness, and staging checks. The **Owner** simulation reconciled **27,972 scenarios and 3,089,772 monthly rows**. The **Renter** script also writes an audit report. The repository tree shows a local Renter JSON report, but that report's PASS status is not independently verified in this README.

These passes show that the checked outputs matched their sources or calculated records in the runs tested. They do not prove that every possible historical revision, new insert, or financial formula has been independently tested.

### TSX: a bug the audit trail caught

The TSX refresh kept marking **10 old months** as updated. The values seemed unchanged. The change log told a different story: `adj_close_price` was shifting by tiny fractions.

We compared old and new values. The differences pointed to floating-point precision. We set a **0.001 absolute comparison tolerance for adjusted close**, while keeping exact checks for other fields and NULL transitions. Then we ran the refresh twice.

**Both runs: 441 unchanged. Zero updates. Zero false change-log entries.**

That fix makes repeated refreshes stable under the chosen rule. It also means sub-0.001 changes in that field will not trigger an update. The threshold is a documented trade-off, not proof that the source can never revise a smaller amount.

For the full process, see **[Data Reconciliation](docs/DATA_RECONCILIATION.md)**.

## Run the refresh workflow

Install Python packages from [`requirements.txt`](requirements.txt). Configure PostgreSQL and create the tables first. Keep your `API.env` in `SQL-Python/update_python/` on your own machine.

From the repository root, change to `SQL-Python`:

```powershell
cd SQL-Python
```

**1 — Refresh external data.** Each script checks its source, RAW, and STAGING results. Run the sources you need; these are the nine current ingestion scripts.

```powershell
python3 .\update_python\update_fred.py
python3 .\update_python\update_cpi.py
python3 .\update_python\update_sp500.py
python3 .\update_python\update_tsx.py
python3 .\update_python\update_mortgage.py
python3 .\update_python\update_rent.py
python3 .\update_python\update_city_house_prices.py
python3 .\update_python\update_bis_house_index.py
python3 .\update_python\update_city_house_index.py
```

**2 — Refresh analysis.** The runner executes the three `04_analysis_refresh_*.sql` scripts in order.

```powershell
python3 .\update_python\update_analysis.py
```

**3 — Refresh simulations.** Owner runs first. Renter uses its saved results.

```powershell
python3 .\update_python\update_owner.py
python3 .\update_python\update_renter.py
```

**4 — Review the checks.** SQL checks live under `SQL-Python/check_SQL/`. JSON run reports go to `SQL-Python/reconciliation_reports/`. The isolated FRED rollback test is:

```powershell
python3 .\test_rollback_python\test_fred_rollback.py
```

These are refresh commands for an **existing database**. They are not a clean-install script. Some data sources require their own Python packages or a local source file. Read each script's header for those options.

**Order matters.** Refresh the relevant sources before analysis. Refresh Owner before Renter. Then update Power BI. A successful reconciliation confirms the checks performed in that run, not every financial assumption.

## Model scope and assumptions

| Item | Assumption |
|---|---|
| Locations | Vancouver, Calgary, Edmonton, Toronto, Ottawa, Montreal; Canada benchmark |
| Reported holding periods | 5 / 10 / 15 / 20 years |
| Mortgage-rate cases | Base, Base −2 percentage points, Base +2 percentage points |
| Renter portfolios | TSX-only or S&P 500-only |
| Reported down payment | 20% |
| Renter investment discipline | 100% |
| Mortgage term / amortization | 5 / 25 years |
| Purchase / selling costs | 2% / 6% |
| Annual maintenance | 1.5% of estimated structure value |
| Annual insurance | 0.3% of home value |
| Property tax | 0.30%–1.20%, city-specific |
| Structure share | 0.35–0.60, city-specific |
| Annual investment fee | 0.10% |
| Tax drag | 0.10% TSX; 0.25% S&P 500 |

Other down-payment scenarios exist in the model. The published report holds down payment at 20% so changes in starting capital do not distort the comparison. Longer holds also have fewer eligible purchase years.

### Core calculations

```text
Owner net worth   = House value − Mortgage balance − Estimated selling cost
Renter net worth  = Investment portfolio value

Owner cash outflow  = Mortgage payment + Maintenance + Property tax + Insurance
Renter cash outflow = Rent + Moving cost
Monthly difference  = Owner cash outflow − Renter cash outflow

Real net worth = Nominal net worth × Starting-month CPI / Current CPI
```

The simulation compounds nominal CAD values. It adjusts wealth for inflation when reporting real results. Details are in **[Simulation Methodology](docs/simulation_methodology.md)**.

## Data sources

| Source | Data | Used for |
|---|---|---|
| BIS | Canada real house-price index, `Q.CA.R.628` | National asset comparison |
| CREA | MLS Home Price Index and benchmark prices | City analysis and home values |
| Teranet–National Bank | C11 house-price index | Reference series; not used downstream |
| Yahoo Finance | `^GSPC`, `^GSPTSE`, `VT` | Market comparisons; S&P 500 and TSX renter portfolios |
| FRED | `DEXCAUS` | USD-to-CAD conversion |
| Statistics Canada | CPI, table 18-10-0004-01 | Inflation adjustment |
| Statistics Canada | Five-year mortgage rate, table 34-10-0145-01 | Mortgage simulation |
| CMHC | Rental Market Survey | City rents |

The BIS series is already a **real** house-price index. It is not deflated by CPI a second time. More detail: **[Data Sources](docs/data_source.md)**.

## Limits

- **This is history, not a forecast.** The model does not predict the next housing cycle.
- **Dividends are not reinvested.** The equity series understate a total-return strategy and can favour buying.
- **Mortgage rates are posted rates.** Actual negotiated rates may be lower. This can favour renting in the model.
- **The cohorts are uneven.** Housing data starts in 2005 for the city simulations. Long holds have fewer eligible entry years.
- **Housing and rent are market benchmarks.** They are not individual transactions or leases. Annual rent observations are applied across each calendar year.
- **Behaviour is simplified.** Moving, rent control, maintenance, and investment discipline follow set assumptions.
- **Other household assets are excluded.** The model compares a home-based balance sheet with an investment portfolio.
- **Life matters beyond money.** Stability, flexibility, schools, and the freedom to change a home are not priced into the results.

These limits do not all favour the same choice. They matter when reading any single result.

## Documentation

- **[Data Sources](docs/data_source.md)** — source records, coverage, and retrieval rules.
- **[Data Cleaning](docs/data_cleaning.md)** — cleaning rules and source preparation.
- **[Data Update](docs/data_update.md)** — source refresh workflow.
- **[Validation and Testing](docs/validation%20-%20testing.md)** — validation and testing notes.
- **[Data Reconciliation](docs/DATA_RECONCILIATION.md)** — audit trail and TSX precision investigation.
- **[Simulation Methodology](docs/simulation_methodology.md)** — assumptions, formulas, and scenario design.
- **[Key Findings](docs/key_findings.md)** — results, sensitivity tests, and interpretation.

## Tech stack

`PostgreSQL` · `SQL` · `Python` · `pandas` · `NumPy` · `psycopg` · `Power BI` · `DAX` · `Git`

---

**Buying is not always better. Renting is not always better. The answer depends on the market, the timing, and what each household does with its money.**

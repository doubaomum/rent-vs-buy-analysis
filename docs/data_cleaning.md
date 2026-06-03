# Data Cleaning and Preprocessing

## 1. Overview

This document describes the data cleaning and preprocessing workflow used in the **Rent vs Buy in Canada** project. It is one of three companion documents: `data_sources.md` describes the raw inputs, this file describes how they were cleaned and transformed, and `key_findings.md` reports the results.

The project combines housing, equity-market, inflation, exchange-rate, mortgage-rate, and rental-market datasets from multiple public sources. Because these datasets use different formats, frequencies, currencies, and index bases, a standardized preprocessing workflow was required before analysis in Python and Power BI.

A key design choice is that the analysis uses **two different types of housing data**:

1. **Indexed housing data** for macro asset-return comparison (report pages 1–4).
2. **Actual benchmark housing prices in Canadian dollars** for the owner-versus-renter simulation (report pages 5–11).

This distinction matters because indexed housing data is appropriate for comparing relative growth across assets, while dollar-based housing prices are required for mortgage calculations, down payments, ownership costs, sale proceeds, and net-worth simulation.

This document covers data processing for pages 1–11. The remaining report pages introduce no new data — page 12 presents conclusions and pages 13–14 document modeling methodology — so they are out of scope here.

---

## 2. Data Cleaning Workflow

The cleaning workflow followed four main stages:

```text
Raw source files
    ↓
Initial Excel pre-cleaning
    ↓
Python / pandas cleaning and transformation
    ↓
Final analysis datasets for Power BI
```

The goal was to convert every dataset into a consistent, analysis-ready time series with standardized column names, date formats, numeric values, and monthly frequency where required.

---

## 3. Initial Pre-Cleaning in Excel

Some raw files contained metadata, notes, descriptive headers, unused columns, or wide-format tables. Before Python processing, a light Excel pre-cleaning step was applied to simplify these files.

The Excel pre-cleaning steps included:

- removing descriptive text, footnotes, and metadata rows,
- keeping only the relevant variables and geographic series,
- removing unnecessary adjusted or smoothed versions of series,
- standardizing the general date and value layout,
- organizing files into a cleaner chronological structure,
- saving cleaned source extracts for Python processing.

This step reduced parsing errors and made the Python workflow easier to maintain.

---

## 4. Python Cleaning Standards

After the initial Excel cleanup, the main cleaning and transformation workflow was performed in Python using pandas.

### 4.1 Column Name Standardization

Different source files used different date and value column names, such as:

```text
Date
TIME_PERIOD
Transaction Date
observation_date
VALUE
Adj Close
```

These were renamed into consistent, analysis-friendly column names such as:

```text
date
city
value
rent
vacancy_rate
usd_cad
sp500_usd
tsx_cad
```

This allowed datasets from different sources to be merged on consistent keys.

### 4.2 Date Formatting

All date columns were converted to pandas datetime format and aligned to a monthly timestamp where needed:

```python
df["date"] = pd.to_datetime(df["date"])
df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
```

This produced a consistent monthly date format:

```text
YYYY-MM-01
```

### 4.3 Numeric Conversion

Some source values were stored as text because of commas, percent symbols, missing-value markers, or formatting from downloaded CSV files. These were cleaned and converted to numeric format:

```python
df["value"] = pd.to_numeric(df["value"], errors="coerce")
```

Cleaned values included stock index levels with thousands separators, mortgage-rate percentages, rent values, vacancy rates, exchange rates, and housing price index values. Values that could not be parsed were coerced to `NaN` and then handled as missing (Section 4.4).

### 4.4 Missing Values

Missing observations were handled based on the type of dataset and the analysis purpose.

Forward-fill was used where it was reasonable to carry the latest available observation forward, such as:

- quarterly housing indices converted to monthly frequency,
- annual rent observations aligned to monthly simulations,
- missing exchange-rate observations around non-trading days,
- mortgage-rate observations aligned to monthly schedules.

Example:

```python
df = df.set_index("date").resample("MS").ffill().reset_index()
```

Forward-fill was chosen carefully: it preserves the most recently observed market condition without inventing a trend between observations.

---

## 5. Frequency Alignment

The raw datasets were reported at different frequencies:

| Dataset Type | Original Frequency | Processed Frequency |
|---|---:|---:|
| BIS national housing index | Quarterly | Monthly-aligned |
| City-level housing index | Monthly | Monthly |
| CREA benchmark prices | Monthly / available reporting frequency | Monthly |
| Yahoo Finance equity data | Daily or monthly download | Monthly |
| FRED USD/CAD exchange rate | Daily | Monthly average |
| Statistics Canada CPI | Monthly | Monthly |
| Statistics Canada mortgage rates | Monthly | Monthly |
| CMHC rent and vacancy data | Annual October snapshot | Monthly forward-filled |

A monthly timeline was used because the rent-versus-buy model requires monthly mortgage payments, rent payments, investment contributions, and portfolio updates.

---

## 6. Macro Indexed Data Processing: Report Pages 1–4

Report pages 1–4 use indexed, inflation-adjusted data to compare long-term asset performance. These pages answer questions such as:

- How did Canadian housing perform compared with the TSX and S&P 500?
- How sensitive were results to entry year and holding period?
- How did city-level housing growth differ across Canadian markets?
- Which cities competed most strongly against equities over different horizons?

### 6.1 Canada Housing vs Stock Market Dataset: Pages 1–2

The Canada-wide macro comparison includes:

- Canada national residential property price index,
- S&P/TSX Composite Index,
- S&P 500 Index,
- USD/CAD exchange rate,
- Canadian CPI.

The common analysis period begins in **January 1990**, because the TSX dataset begins in 1990. All final series were normalized to:

```text
January 1990 = 100
```

#### Canada Housing Index

The BIS Canada residential property price series is already a real housing price index. Its original base is:

```text
2010 = 100
```

For comparison with equities, it was rebased to 1990 = 100:

```text
Housing Index (1990 = 100) = Current Housing Index / Housing Index at 1990 × 100
```

Because the BIS series is quarterly, it was converted to a monthly-aligned series using forward-fill.

#### TSX Processing

The TSX is denominated in Canadian dollars, so no currency conversion was required.

Processing steps:

- clean the date and value columns,
- convert index values to numeric format,
- filter the dataset to the 1990–2025 period,
- convert nominal TSX values into real values using Canadian CPI,
- rebase the real TSX series to 1990 = 100.

Inflation adjustment formula:

```text
Real TSX = Nominal TSX / CPI × CPI_base
```

Here `CPI_base` is the CPI value in the reference base period (Statistics Canada uses 2002 = 100). This expresses each series in constant reference-period dollars before it is rebased to 1990 = 100.

#### S&P 500 Processing

The S&P 500 is denominated in U.S. dollars, so it was first converted into Canadian dollars using the USD/CAD exchange rate:

```text
S&P 500 CAD = S&P 500 USD × USD/CAD
```

After currency conversion, the CAD S&P 500 was converted into real terms using Canadian CPI and then rebased to 1990 = 100. This allowed the S&P 500 to be evaluated from a Canadian investor perspective.

---

### 6.2 City-Level Housing Dataset: Pages 3–4

The city-level housing comparison includes Vancouver, Toronto, Montreal, Calgary, Edmonton, Ottawa, and the Canada benchmark where applicable.

The city-level housing index is nominal and uses a source base of:

```text
2005-06 = 100
```

Because not all city series have full 1990 coverage, the common city-level comparison period was set to **1999–2025**.

Processing steps:

1. Standardize monthly dates.
2. Convert city index values into numeric format.
3. Merge Canadian CPI.
4. Convert nominal city housing indices into real values.
5. Rebase each city series to 1999 = 100:

```text
City Real Housing Index (1999 = 100)
= Current Real City Index / Real City Index at 1999 × 100
```

This produced consistent inflation-adjusted city-level growth series for regional comparison.

---

### 6.3 Indexed Growth and CAGR Calculation

For pages 1–4, indexed values were calculated as:

```text
Indexed Value = Current Value / Base Value × 100
```

Compound annual growth rate was calculated as:

```text
CAGR = (Ending Value / Beginning Value)^(1 / Number of Years) - 1
```

Because the macro comparison uses real values, these CAGR figures represent inflation-adjusted annualized growth.

---

## 7. Simulation Data Processing: Report Pages 5–11

Report pages 5–11 use dollar-based monthly simulation data rather than indexed housing data, because the model calculates actual Canadian-dollar quantities:

- purchase price,
- down payment,
- mortgage principal,
- mortgage payment,
- interest cost,
- ownership cost,
- rent payment,
- investment contribution,
- portfolio value,
- sale proceeds,
- owner net worth,
- renter net worth.

The simulation is reported in **nominal CAD**, not inflation-adjusted index values.

### 7.1 Actual Benchmark Housing Price Processing

Actual benchmark housing price data was cleaned separately from the indexed housing datasets.

Processing steps:

1. Standardize date and geography fields.
2. Convert benchmark prices to numeric CAD values.
3. Align all cities to the monthly simulation timeline.
4. Merge city-level house prices into the owner and renter simulation schedules.
5. Use the benchmark price at the purchase month as the starting home value.
6. Track the benchmark price path over the holding period to estimate sale value.

This dataset is the basis for mortgage principal, homeowner equity, and final sale proceeds.

### 7.2 Mortgage Rate Processing

Mortgage-rate data was cleaned and aligned to monthly simulation dates.

Processing steps:

- remove metadata and unnecessary rows,
- convert the rate values into numeric format,
- standardize monthly dates,
- align rates with purchase and renewal months,
- apply the historical rate to the base scenario,
- create sensitivity versions using:

```text
Lower rate scenario = Historical rate - 2 percentage points
Base rate scenario  = Historical rate
Higher rate scenario = Historical rate + 2 percentage points
```

The ±2 percentage-point scenarios are applied to the mortgage renewal schedule as sensitivity tests, not forecasts.

### 7.3 Rent and Vacancy Processing

CMHC rent and vacancy data are reported annually, usually as an October snapshot. To use these values in a monthly simulation, the annual observations were converted to monthly frequency using forward-fill.

Processing steps:

1. Select the relevant cities.
2. Select 2-bedroom rent as the main rent measure.
3. Clean rent and vacancy values.
4. Standardize annual observation dates.
5. Convert annual rent and vacancy data to monthly frequency.
6. Merge monthly rent and vacancy series into the renter simulation schedule.

Example:

```python
rent_monthly = rent.set_index("date").resample("MS").ffill().reset_index()
```

The simulation distinguishes between:

- **market rent** — the prevailing rent for a new renter,
- **effective paid rent** — the rent actually paid by an existing tenant under rent-control and moving assumptions.

### 7.4 Portfolio Return Processing

Equity-market return data was used for the renter-investor portfolio.

Processing steps:

- convert equity prices to monthly values,
- convert S&P 500 values from USD to CAD,
- calculate monthly portfolio returns,
- apply investment fees,
- apply portfolio-specific tax-drag assumptions,
- produce net monthly portfolio returns.

The final report uses two portfolio scenarios:

| Portfolio Scenario | Description |
|---|---|
| TSX portfolio | Base-case renter portfolio |
| S&P 500 portfolio | Sensitivity scenario |

### 7.5 Scenario Input Processing

Scenario inputs were organized into structured parameter tables before simulation. Scenario dimensions include:

- city,
- purchase year,
- holding period,
- interest-rate scenario,
- renter discipline,
- portfolio type.

The scenario table lets the Python model generate multiple owner and renter schedules in a consistent, repeatable way.

### 7.6 Net Worth Indexing for Cross-City Comparison

The simulation outputs are reported in nominal Canadian dollars, but a direct dollar comparison of owner and renter net worth across cities can mislead, because each city has a different starting home price. Since the homeowner's initial capital is a 20% down payment, higher-priced cities require a larger initial dollar amount than lower-priced cities.

To compare outcomes on a consistent baseline, the final Power BI measures transform both owner and renter net worth into indexed values. The selected start date — for example `2005-01-01` in the base simulation view — is set equal to:

```text
Start date = 100
```

This focuses the comparison on relative wealth growth rather than absolute starting amounts, so cities with very different house prices can be compared fairly in the same visual.

The indexed owner net worth measure:

```DAX
Net Worth Index Owner =
VAR StartDate =
    CALCULATE(
        MIN(basic_model_renter_portfolio_schedule_new[date]),
        ALLSELECTED(basic_model_renter_portfolio_schedule_new[date])
    )

VAR StartValue =
    CALCULATE(
        MAX(basic_model_renter_portfolio_schedule_new[owner_networth_after_sale]),
        REMOVEFILTERS(basic_model_renter_portfolio_schedule_new[date]),
        basic_model_renter_portfolio_schedule_new[date] = StartDate
    )

VAR CurrentValue =
    MAX(basic_model_renter_portfolio_schedule_new[owner_networth_after_sale])

RETURN
DIVIDE(CurrentValue, StartValue) * 100
```

The indexed renter net worth measure:

```DAX
Net Worth Index Renter =
VAR StartDate =
    CALCULATE(
        MIN(basic_model_renter_portfolio_schedule_new[date]),
        ALLSELECTED(basic_model_renter_portfolio_schedule_new[date])
    )

VAR StartValue =
    CALCULATE(
        MAX(basic_model_renter_portfolio_schedule_new[renter_networth]),
        REMOVEFILTERS(basic_model_renter_portfolio_schedule_new[date]),
        basic_model_renter_portfolio_schedule_new[date] = StartDate
    )

VAR CurrentValue =
    MAX(basic_model_renter_portfolio_schedule_new[renter_networth])

RETURN
DIVIDE(CurrentValue, StartValue) * 100
```

In both measures, the date filter is removed only when retrieving the start value, while city and scenario filters remain active — so each city and scenario is indexed relative to its own starting net worth.

The indexed wealth gap is then:

```text
Indexed Wealth Gap = Owner Net Worth Index - Renter Net Worth Index
```

A positive gap indicates homeowner outperformance; a negative value indicates renter-investor outperformance. This indexed approach is used in all owner-versus-renter comparison visuals because it places every city and scenario on a comparable starting baseline.

---

## 8. Dataset Merging

After cleaning individual datasets, the project merged them into analysis datasets using the monthly `date` column and, where relevant, the `city` column.

Typical merge keys:

```text
date
city
date + city
scenario_id
```

Main merge logic:

- macro comparison datasets are merged by `date`,
- city housing datasets are merged by `date` and `city`,
- rent and house-price data are merged by `date` and `city`,
- simulation schedules are merged by scenario identifiers and monthly dates.

A left-join approach was generally used, with one dataset serving as the base timeline:

```python
df = city_house.merge(cpi, on="date", how="left")
df = df.merge(stock_returns, on="date", how="left")
```

---

## 9. Final Analysis Outputs

The cleaning workflow generated two broad groups of outputs.

### 9.1 Macro Comparison Outputs

Supporting report pages 1–4:

- Canada housing vs stock market real index dataset,
- city-level real housing index dataset,
- indexed growth datasets by start year and holding period,
- CAGR summary tables,
- winner matrices for housing versus equity-market comparison.

Example output files:

```text
canada_house_vs_stocks_real_1990_index.csv
city_house_real_1999_index.csv
```

### 9.2 Simulation Outputs

Supporting report pages 5–11:

- homeowner monthly schedule,
- renter-investor monthly schedule,
- owner and renter combined scenario dataset,
- scenario summary tables,
- sensitivity-impact tables,
- Power BI-ready outputs for visualization.

The simulation outputs are structured so that Power BI slicers can filter by city, purchase year, holding period, portfolio, renter discipline, and interest-rate scenario.

---

## 10. Validation Checks

Several validation checks were applied before loading the datasets into Power BI.

### 10.1 Date Coverage Checks

Each final dataset was checked against its expected analysis period:

- macro Canada comparison: 1990–2025,
- city-level housing comparison: 1999–2025,
- rent-versus-buy simulation: 2005–2025.

### 10.2 Missing Value Checks

The final datasets were checked for missing values in key fields: house price, rent, mortgage rate, portfolio return, CPI, USD/CAD exchange rate, owner net worth, and renter net worth.

### 10.3 Scenario Consistency Checks

Scenario tables were checked to confirm that combinations of city, start year, holding period, portfolio, renter discipline, and interest-rate scenario were generated consistently.

### 10.4 Result Reasonableness Checks

Final outputs were reviewed for unreasonable values, such as:

- negative mortgage balances,
- missing final values,
- unrealistic rent jumps not explained by rent-reset logic,
- owner or renter net worth that did not align with the underlying price and return path,
- sensitivity results that did not respond logically to rate, discipline, or portfolio changes.

---

## 11. Power BI Preparation

Before import into Power BI, final datasets were organized to support dashboard filtering and visualization. Key steps:

- keeping fields in a tidy long-table structure where possible,
- preserving scenario identifiers,
- using consistent city names across tables,
- creating fields for asset name, scenario name, and report labels,
- exporting final CSV files for Power BI import,
- checking that slicers could filter the intended visuals.

The datasets were designed so that Python served as the calculation engine and Power BI as the interactive visualization layer.

---

## 12. Limitations of the Cleaning Process

Several limitations remain after preprocessing:

- Source datasets have different historical start dates, requiring different comparison windows.
- Quarterly and annual datasets were aligned to monthly frequency using forward-fill, which improves consistency but does not create new within-period observations.
- CMHC rent data is annual and may not capture monthly rent volatility.
- Housing indices and benchmark prices represent market averages and do not capture individual property variation.
- Stock-market results depend on index choice, dividend treatment, currency conversion, and time period.
- Macro pages use real, inflation-adjusted data while simulation pages use nominal CAD, so the two should not be read on the same scale.

---

## 13. Summary

The data cleaning process transformed several heterogeneous public datasets into a consistent analytical framework.

For report pages 1–4, the workflow created real, inflation-adjusted indexed datasets for long-term housing and equity-market comparison.

For report pages 5–11, it created nominal monthly simulation datasets using actual house prices, rents, mortgage rates, and portfolio returns. Power BI then indexed owner and renter net worth to a common start-date baseline so cities with different initial home prices could be compared consistently.

This separation between **indexed macro analysis** and **dollar-based simulation analysis** is the foundation of the project: it lets the report compare housing with equities at the market level while also modeling the household-level financial tradeoff between buying and renting.

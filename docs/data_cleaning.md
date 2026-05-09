# 2. Data Cleaning and Preprocessing

## 2.1 Overview

After data collection, all datasets required preprocessing to ensure consistency, comparability, and usability across different sources.

The datasets used in this project vary in:

- Data frequency (daily, monthly, quarterly, annual)
- Data format (text, numeric, index-based)
- Structure (wide vs. long format)
- Base index definitions (different benchmark years)

Therefore, a systematic data cleaning and preprocessing workflow was applied before analysis.

---

# 2.2 Initial Data Pre-Cleaning in Excel

Before processing the datasets in Python, an initial cleaning step was performed in Microsoft Excel to improve data consistency and remove unnecessary content.

## The preprocessing steps included:

- Removing descriptive text, notes, and annotations
- Keeping only relevant variables and primary index series
- Removing seasonally adjusted and smoothed series where unnecessary
- Standardizing date and numeric formats
- Organizing datasets into a consistent chronological time-series structure

This step simplified downstream processing and ensured that the datasets were ready for analysis in Python.

---

# 2.3 Data Cleaning in Python

After the initial Excel preprocessing, additional cleaning and transformation steps were performed using Python and pandas.

---

## 2.3.1 Column Name Standardization

Different datasets used inconsistent column names such as:

- `"Date"`
- `"TIME_PERIOD"`
- `"Transaction Date"`

These were standardized into a unified column name:

```python
date
```

This simplified downstream processing and time-series analysis.

---

## 2.3.2 Date Formatting and Frequency Alignment

All date fields were converted into a consistent datetime format and aligned to monthly frequency:

```python
df["date"] = pd.to_datetime(df["date"])
df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
```

This ensured compatibility across datasets with different original reporting frequencies.

---

## 2.3.3 Data Type Conversion

Some datasets stored numeric values as text (for example, stock prices containing thousands separators such as `"6,729.60"`).

These values were converted into numeric format using:

```python
pd.to_numeric(df["column"], errors="coerce")
```

This enabled accurate quantitative analysis.

---

## 2.3.4 Handling Missing Values

Missing values were handled using forward-fill (`ffill()`) where appropriate.

### Examples include:

- Expanding quarterly housing data into monthly frequency
- Filling missing exchange rate observations
- Converting annual rent observations into monthly series

This created continuous monthly time-series data across all variables.

---

# 2.4 Rent and Vacancy Data Processing

The rent and vacancy datasets required additional preprocessing due to their annual reporting structure.

CMHC rent and vacancy data are reported annually (typically in October).

To align these datasets with monthly housing and stock market data, annual observations were converted to monthly frequency using forward-fill:

```python
df_city = df_city.set_index("date").resample("MS").ffill().reset_index()
```

This produced monthly rental and vacancy series consistent with the frequency of the housing and financial datasets.

---

# 2.5 Currency Conversion

The S&P 500 and VT ETF datasets were originally denominated in U.S. Dollars (USD), while Canadian housing and TSX datasets were denominated in Canadian Dollars (CAD).

To ensure comparability across all asset classes, U.S.-denominated assets were converted into Canadian Dollars using the USD/CAD exchange rate.

Exchange rate data was obtained from the Federal Reserve Economic Data (FRED) database.

## The conversion formula used in this project is:

```text
Asset Value (CAD) = Asset Value (USD) × USD/CAD Exchange Rate
```

The exchange rate dataset was first converted from daily frequency to monthly average values:

```python
fx = fx.set_index("date").resample("MS").mean().reset_index()
```

Then, U.S. and global stock market indices were converted into Canadian Dollars:

```python
stock_cleaned["sp500_cad"] = (
    stock_cleaned["sp500_usd"] * stock_cleaned["usd_cad"]
)

stock_cleaned["vt_cad"] = (
    stock_cleaned["vt_usd"] * stock_cleaned["usd_cad"]
)
```

This transformation allows direct comparison between:

- Canadian housing markets
- Canadian stock market performance
- U.S. stock market performance
- Global equity market performance

from a Canadian investor’s perspective.

---

# 2.6 Indexed Growth Series

To enable meaningful comparison across different asset classes, selected variables were transformed into indexed growth series.

Because different datasets use different original scales and benchmark definitions, indexed normalization was applied using common base years.

---

## 2.6.1 Long-Term Comparison

Assets with full historical coverage were normalized using:

```text
1999 = 100
```

This comparison includes:

- Canadian housing market
- Major Canadian city housing markets
- TSX Composite Index
- S&P 500
- Rent series

---

## 2.6.2 Global Market Comparison

The VT ETF dataset begins in July 2008.

Therefore, a second indexed comparison series was created using:

```text
2008-07 = 100
```

This comparison includes:

- Canadian housing market
- Major Canadian city housing markets
- TSX Composite Index
- S&P 500
- VT ETF
- Rent series

---

## Normalization Formula

```text
Indexed Value = (Current Value / Base Value) × 100
```

This transformation enables:

- Comparison across assets with different scales
- Long-term trend visualization
- Consistent comparison between housing and financial assets

---

# 2.7 Final Cleaned Datasets

Three final cleaned datasets were generated.

---

## 1. House Price Dataset

### `house_price_cleaned.csv`

Includes:

- Canada-wide housing price index
- Six major Canadian city housing price indices
- Indexed growth series

---

## 2. Stock Market Dataset

### `stock_cleaned.csv`

Includes:

- TSX Composite Index
- S&P 500
- VT ETF
- USD/CAD exchange rate
- CAD-adjusted stock market series
- Indexed growth series

---

## 3. Rent and Vacancy Dataset

### `rent_cleaned.csv`

Includes:

- National and city-level rent data
- Vacancy rate data
- Indexed rent growth series

---

## Final Dataset Characteristics

All final datasets:

- Cover the period **1999–2025**
- Use **monthly frequency**
- Are standardized for time-series analysis
- Are suitable for:
  - Power BI
  - SQL
  - Financial analysis workflows
```
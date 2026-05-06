## Data Cleaning, Integration, and Currency Conversion
1. Overview

After data collection, all datasets required preprocessing to ensure consistency, comparability, and usability across different sources.

The datasets used in this project vary in:

Data frequency (daily, monthly, quarterly, annual)
Data format (text, numeric, index-based)
Structure (wide vs. long format)

Therefore, a systematic data cleaning and integration process 
was applied before analysis.

Data Cleaning and Preprocessing
2. Initial Data Pre-Cleaning in Excel

Before processing the datasets in Python, an initial cleaning step was performed in Microsoft Excel to improve data consistency and remove unnecessary content.

The preprocessing steps included:

Removing descriptive text, notes, and annotations
Keeping only relevant variables and primary index series
Standardizing date and numeric formats
Organizing datasets into a consistent chronological time-series structure

This step simplified downstream processing and ensured that the datasets were ready for analysis in Python.

3. Data Cleaning in Python

After the initial Excel preprocessing, additional cleaning and transformation steps were performed using Python and pandas.

3.1 Column Name Standardization

Different datasets used inconsistent column names such as:

"Date"
"TIME_PERIOD"
"Transaction Date"

These were standardized into a unified column name:

date

This simplified merging and downstream analysis.

3.2 Date Formatting and Frequency Alignment

All date fields were converted into a consistent datetime format and aligned to monthly frequency:

df["date"] = pd.to_datetime(df["date"])
df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

This ensured compatibility across datasets with different original reporting frequencies.

3.3 Data Type Conversion

Some datasets stored numeric values as text (for example, stock prices containing thousands separators such as "6,729.60").

These values were converted into numeric format using:

pd.to_numeric(df["column"], errors="coerce")

This enabled accurate quantitative analysis.

3.4 Handling Missing Values

Missing values were handled using forward-fill (ffill()) where appropriate.

Examples include:

Expanding quarterly housing data into monthly frequency
Filling missing exchange rate observations

This created continuous monthly time series data across all variables.

4. Rent and Vacancy Data Processing

The rent and vacancy datasets required additional preprocessing due to their annual reporting structure.

CMHC rent and vacancy data are reported annually (typically in October).

To align these datasets with monthly housing and stock market data, annual observations were converted to monthly frequency using forward-fill:

df_city = df_city.set_index("date").resample("MS").ffill().reset_index()

5. Data Integration

All cleaned datasets were merged into a single dataset using the date column as the primary key.

The integrated datasets include:

Canada national housing price index
City-level housing price indices
TSX (Canadian stock market)
S&P 500 (U.S. stock market)
VT ETF (global stock market)
USD/CAD exchange rate
Rent and vacancy data

A left join strategy was applied using city-level housing data as the base dataset:

df = city_house.merge(canada_house, on="date", how="left")
df = df.merge(tsx, on="date", how="left")
df = df.merge(sp500, on="date", how="left")
df = df.merge(vt, on="date", how="left")
df = df.merge(fx[["date", "usd_cad"]], on="date", how="left")

This ensured that all variables shared a consistent monthly timeline.

6. Currency Conversion

To ensure comparability across financial variables, all stock market data were standardized into Canadian Dollars (CAD).

TSX data were already denominated in CAD
S&P 500 and VT ETF data were originally denominated in USD

The exchange rate dataset was first converted from daily to monthly frequency:

fx = fx.set_index("date").resample("MS").mean().reset_index()

The U.S. and global stock market datasets were then converted into CAD:

df["sp500_cad"] = df["sp500_usd"] * df["usd_cad"]
df["vt_cad"] = df["vt_usd"] * df["usd_cad"]

This enabled direct comparison between housing and financial assets within the same currency framework.

7. Final Dataset

The final cleaned dataset:

Covers the period 1999–2025
Uses monthly frequency
Integrates housing, rental, stock market, and exchange rate data
Includes currency-adjusted stock market indicators

The dataset was exported as:

market_data_all_cleaned.csv


## Datasets to collect


2.2 Data Cleaning
(1) Column Name Standardization

Different datasets used inconsistent column names (e.g., “Date”, “TIME_PERIOD”, “Transaction Date”).

These were standardized into a unified format:

date

This ensures consistency and simplifies downstream merging.

(2) Date Formatting and Frequency Alignment

All date fields were converted into a consistent datetime format and aligned to monthly frequency:

df["date"] = pd.to_datetime(df["date"])
df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

This step ensures compatibility across datasets with different original frequencies.

(3) Data Type Conversion

Some datasets contained numeric values stored as text (e.g., stock prices with thousands separators such as "6,729.60").

These values were converted into numeric format:

pd.to_numeric(df["column"], errors="coerce")

This enables accurate quantitative analysis.

(4) Handling Missing Values

Missing values were handled using forward-fill where appropriate:

Quarterly housing data was expanded to monthly frequency using forward-fill
Missing exchange rate values were also forward-filled

This approach ensures a continuous time series for all variables.

(5) Rent and Vacancy Data Cleaning (Python)

The rent and vacancy datasets required additional preprocessing due to their structure and annual reporting format.

The main steps include:

a. Date Standardization

Date fields were converted into datetime format and standardized to monthly timestamps:

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
b. Data Type Conversion

Rent and vacancy values were converted into numeric format:

pd.to_numeric(..., errors="coerce")
c. Merging Rent and Vacancy Data

For each city, rent and vacancy datasets were merged using the date column:

df_city = rent.merge(vacancy, on="date", how="left")
d. Frequency Conversion (Annual → Monthly)

CMHC rent and vacancy data are reported annually (typically in October).

To align with monthly datasets (housing prices and stock data), annual values were converted into monthly frequency using forward-fill:

df_city = df_city.set_index("date").resample("MS").ffill().reset_index()

This ensures consistent temporal alignment across all datasets.

e. Multi-City Integration

All cleaned rent and vacancy datasets (Canada and six major cities) were combined into a unified dataset.

2.3 Data Integration (Merging)

All cleaned datasets were merged into a unified dataset using the date column as the primary key.

The datasets include:

Canada national housing price index
City-level housing price indices
TSX (Canadian stock market)
S&P 500 (U.S. stock market)
VT ETF (global stock market)
USD/CAD exchange rate
Rent and vacancy data

A left join strategy was applied, using city-level housing data as the base:

df = city_house.merge(canada_house, on="date", how="left")
df = df.merge(tsx, on="date", how="left")
df = df.merge(sp500, on="date", how="left")
df = df.merge(vt, on="date", how="left")
df = df.merge(fx[["date", "usd_cad"]], on="date", how="left")

This ensures that all variables are aligned along a consistent monthly timeline.

2.4 Currency Conversion

To ensure comparability across financial variables, all values were converted into a common currency:

👉 Canadian Dollars (CAD)

TSX: already denominated in CAD
S&P 500 and VT: originally in USD

The exchange rate dataset (CAD per USD) was first converted from daily to monthly frequency:

fx = fx.set_index("date").resample("MS").mean().reset_index()

Then, U.S. and global stock indices were converted into CAD:

df["sp500_cad"] = df["sp500_usd"] * df["usd_cad"]
df["vt_cad"] = df["vt_usd"] * df["usd_cad"]

This transformation allows direct comparison across asset classes.

2.5 Final Dataset

The final dataset:

Covers the period 1999–2025
Uses monthly frequency
Integrates housing, rental, stock, and exchange rate data
Includes currency-adjusted stock market indicators

The dataset was exported as:

market_data_all_cleaned.csv
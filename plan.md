## Datasets to collect

1. Data Collection

1.1 Residential Property Price Index

To analyze housing market performance in Canada, both national-level and city-level residential property price indices were collected.

The national dataset provides a macro-level benchmark, while the city-level dataset captures regional variation across major urban markets, enabling a more comprehensive analysis.

1.1.1 National-Level Residential Property Price Index (Canada)

1.1.1.1 Data Source

The data is obtained from the Bank for International Settlements (BIS), a globally recognized provider of standardized macroeconomic and financial statistics.

Specifically, the dataset is drawn from the Residential Property Price Statistics (RPPS) database, which is widely used in economic and financial analysis.

1.1.1.2 Dataset Overview

Canada – Selected Residential Property Prices, Real Index (2010 = 100)

This dataset measures inflation-adjusted housing price movements and serves as a long-term benchmark for real estate performance.

To ensure consistency with other datasets, the analysis focuses on the period 1990–2025, with earlier observations excluded during preprocessing.

1.1.1.3 Data Description

The dataset consists of a quarterly time series index of residential property prices in Canada.

Key characteristics include:

Measures housing price changes over time
Adjusted for inflation (real terms)
Represents national-level housing market trends
Expressed as an index (base year 2010 = 100)

Using real values enables meaningful comparison with other asset classes, such as equities.

1.1.1.4 Data Collection Method

The dataset was retrieved from:

https://data.bis.org/topics/RPP/BIS,WS_SPP,1.0/Q.CA.R.628

The collection process included:

Accessing the BIS RPPS database
Selecting the Canadian real residential property price index
Downloading the dataset in CSV format
Extracting and organizing the relevant time series

1.1.1.5 Data Cleaning and Preprocessing

To ensure data consistency and usability, the following steps were applied:

Time period filtering
Only data from 1990–2025 was retained to align with other datasets
Column selection
Only the primary index series was kept, removing unnecessary variables
Data structuring
The dataset was formatted into a clean time series with proper chronological order

These steps ensure the dataset is suitable for comparative analysis.

1.1.1.6 Purpose of Using This Data

This dataset is used to:

Represent overall housing market performance in Canada
Provide an inflation-adjusted benchmark for real estate investment
Enable comparison with equity market returns

1.1.1.7 Limitations

Does not capture regional variation
Index-based (no absolute price levels)
No breakdown by housing type

To address these limitations, a city-level dataset is introduced below.

1.1.2 City-Level Residential Property Price Index

1.1.2.1 Data Source

The data is sourced from Canadian Real Estate Price Index, which provides housing price indices across major Canadian cities.

1.1.2.2 Dataset Overview

Residential Property Price Index – Six Major Canadian Cities

Selected cities:
Toronto
Vancouver
Montreal
Calgary
Ottawa
Edmonton

The dataset covers 1999–2025 and is reported at a monthly frequency.

1.1.2.3 Data Description

The dataset consists of monthly housing price indices for multiple cities.

Key features include:
Tracks city-level housing price changes
Monthly frequency
Index-based representation
Enables cross-city comparison

This dataset captures regional variation that is not visible in national-level data.

1.1.2.4 Data Collection Method

The dataset was collected from:

https://housepriceindex.ca/

The process included:
Selecting relevant cities
Downloading the dataset in CSV format
Standardizing formats and aligning time periods
Organizing the data into structured tables

1.1.2.5 Data Cleaning and Preprocessing

To improve data quality and analytical consistency, the following steps were applied:

(1) City Selection

Six major cities were selected from the original dataset.

Selection criteria:

Economic significance
Data completeness
Geographic representation

(2) Feature Selection

Only the primary Index column was retained. The following were removed:

Seasonally Adjusted Index
Smoothed Index
Smoothed SA Index
Sales Pair Count

This ensures consistency and improves interpretability.

(3) Date Standardization

Dates were converted to YYYY-MM-DD format (e.g., 2000-06-01) to:

Ensure consistency across datasets
Enable time series analysis
Support integration with SQL and BI tools

1.1.2.6 Purpose of Using This Data

This dataset enables:
Analysis of regional housing market differences
More realistic evaluation of investment performance
Comparison with equity markets at the city level

1.1.2.7 Limitations
Index-based (no absolute price levels)
No property-type breakdown
Potential inconsistencies across cities

1.2 Equity Market Index
1.2.1 Data Source

The equity market data used in this project is obtained from Yahoo Finance, a widely used platform that provides reliable historical financial data for stock indices and exchange-traded funds (ETFs).

The datasets include:

S&P/TSX Composite Index (^GSPTSE) – representing the Canadian equity market
S&P 500 Index (^GSPC) – representing the U.S. equity market
Vanguard Total World Stock ETF (VT) – representing the global equity market

1.2.2 Dataset Overview

The three datasets are summarized as follows:

Canada Equity Market
Index: S&P/TSX Composite Index
Time period: 1990–2025
Frequency: Monthly
Currency: CAD

U.S. Equity Market
Index: S&P 500 Index
Time period: 1985–2025
Frequency: Monthly
Currency (original): USD

Global Equity Market
ETF: Vanguard Total World Stock ETF (VT)
Time period: August 2008–2025
Frequency: Monthly
Currency (original): USD

Note:
The global dataset begins in August 2008, which limits long-term comparison with other datasets.

1.2.3 Data Description

All equity datasets consist of historical price data.

The primary variable used in this analysis is:
Adjusted Close (Adj Close)

This variable is selected because:
It accounts for dividends and stock splits
It reflects total return performance
It provides a more accurate representation of long-term investment outcomes
1.2.4 Data Collection Method

The data was collected from Yahoo Finance through the following sources:

S&P/TSX Composite Index:
https://finance.yahoo.com/quote/%5EGSPTSE/history/
S&P 500 Index:
https://finance.yahoo.com/quote/%5EGSPC/history/
Vanguard Total World Stock ETF (VT):
https://finance.yahoo.com/quote/VT/history/

The collection process included:
Accessing the historical data section for each index/ETF
Selecting the desired time period
Setting the data frequency to monthly
Downloading the dataset in CSV format
Extracting the Adjusted Close values for analysis

1.2.5 Data Cleaning and Preprocessing

To ensure consistency and usability across datasets, the following cleaning steps were applied:

Column Selection

Only the Adjusted Close (Adj Close) column was retained.
The following columns were removed:
Open
High
Low
Close
Volume

These variables are primarily relevant for short-term trading and are not required for long-term investment analysis.

Data Filtering
All datasets were filtered to retain observations from:
January 1999 to December 2025

This ensures consistency with the housing dataset and allows for unified analysis.

Data Formatting
All datasets were converted into monthly time series format
Date formats were standardized across datasets
Data was sorted chronologically
Consistency Across Datasets

The same cleaning procedure was applied consistently to:

S&P/TSX Composite Index
S&P 500 Index
VT ETF

This ensures comparability across different equity markets.

1.2.6 Data Transformation

To enable meaningful comparison across different asset classes, several transformations were applied:

Currency Adjustment

The S&P 500 and VT datasets are originally denominated in U.S. dollars (USD).

To ensure consistency with Canadian housing price data, both datasets were:

converted from USD to Canadian dollars (CAD)

This adjustment reflects the perspective of a Canadian investor and allows for more realistic comparison across asset classes.

Index Normalization

To make all datasets comparable, values were transformed into an index format:

The year 2010 was set as the base year (index = 100)
All other values were scaled relative to this base year

This normalization allows direct comparison between:
Housing prices
Canadian equity market
U.S. equity market
Global equity market

1.2.7 Purpose of Using This Data

The inclusion of equity market data serves several purposes:

To represent investment performance in different financial markets
To provide benchmarks for long-term returns
To compare equity returns with housing price growth
To support the rent vs. buy analysis by evaluating alternative investment strategies

1.2.8 Limitations

Several limitations should be considered:

The VT dataset begins only in 2008, limiting long-term comparison
Currency conversion introduces additional variability due to exchange rate fluctuations
The analysis does not account for taxes, transaction costs, or investor-specific behavior
The indices represent aggregate market performance and may not reflect individual portfolios

1.3 Canadian Dollars to U.S. Dollar Spot Exchange Rate

1.3.1 Data Source: Federal Reserve Economic Data

The exchange rate data used in this project is obtained from the Federal Reserve Economic Data (FRED), a widely recognized and reliable source for macroeconomic and financial time series.

The specific dataset used is:

Canadian Dollars to U.S. Dollar Spot Exchange Rate (DEXCAUS)

This dataset provides the daily exchange rate between the Canadian Dollar (CAD) and the U.S. Dollar (USD), expressed as:

CAD per USD (i.e., the number of Canadian dollars required to purchase one U.S. dollar)

1.3.2 Dataset Overview

The dataset includes:

Time frequency: Daily
Time range: Extended historical period (subset used: 1999–2025)
Key variables:
observation_date: Date of the observation
DEXCAUS: Exchange rate (CAD per USD)

The dataset was downloaded in CSV format and stored in the project directory for further processing.

1.3.3 Purpose in This Project

The exchange rate data is used to:

Convert U.S. and global stock market indices (denominated in USD) into Canadian Dollars (CAD)
Ensure comparability across:
Canadian housing prices
Canadian stock market
U.S. and global stock markets

This step is essential for conducting a consistent financial comparison from a Canadian investor’s perspective.

2. Data Cleaning, Integration, and Currency Conversion
2.1 Data Cleaning

After data collection, all datasets required preprocessing to ensure consistency and usability.

The key cleaning steps include:

Column Name Standardization
Different datasets used inconsistent column names (e.g., "Date", "TIME_PERIOD", "Transaction Date").
These were standardized to a unified column name:

date

Date Formatting and Frequency Alignment
All date fields were converted into a consistent datetime format and aligned to monthly frequency:

df["date"] = pd.to_datetime(df["date"])
df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
Data Type Conversion
Some datasets contained numeric values stored as text (e.g., TSX values with thousands separators such as "6,729.60").
These were converted into numeric format to enable quantitative analysis.
Handling Missing Values
Quarterly housing data (Canada-wide index) was converted to monthly frequency using forward-fill (ffill())
Missing exchange rate values were also filled using forward-fill
2.2 Data Integration (Merging)

All datasets were merged into a unified dataset using the date column as the key.

The datasets include:

Canada national housing price index
City-level housing price indices
TSX (Canada stock market)
S&P 500 (U.S. stock market)
VT ETF (global stock market)
USD/CAD exchange rate

A left join strategy was used, with city-level housing data as the base:

df = city_house.merge(canada_house, on="date", how="left")
df = df.merge(tsx, on="date", how="left")
df = df.merge(sp500, on="date", how="left")
df = df.merge(vt, on="date", how="left")
df = df.merge(fx[["date", "usd_cad"]], on="date", how="left")

This ensures all variables are aligned along a consistent monthly timeline.

2.3 Currency Conversion

To ensure comparability across all financial variables, all values were converted into a common currency:
👉 Canadian Dollars (CAD)

TSX: already denominated in CAD
S&P 500 and VT: originally in USD

The exchange rate dataset (CAD per USD) was first converted from daily to monthly frequency:

fx = fx.set_index("date").resample("MS").mean().reset_index()

Then, U.S. and global stock indices were converted to CAD:

df["sp500_cad"] = df["sp500_usd"] * df["usd_cad"]
df["vt_cad"] = df["vt_usd"] * df["usd_cad"]

This transformation allows direct comparison between housing prices and stock market investments within the same currency framework.

2.4 Final Dataset

The final dataset:

Covers the period 1999–2025
Uses monthly frequency
Integrates multiple financial and housing indicators
Includes currency-adjusted stock market data

The cleaned dataset was exported as:

market_data_cleaned.csv
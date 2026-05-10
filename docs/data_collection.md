# 1. Data Collection

## 1.1 Residential Property Price Index

To analyze housing market performance in Canada, both national-level and city-level residential property price indices were collected.

The national dataset provides a macro-level benchmark, while the city-level dataset captures regional variation across major urban markets, enabling a more comprehensive analysis.

---

## 1.1.1 National-Level Residential Property Price Index (Canada)

### 1.1.1.1 Data Source

The data is obtained from the Bank for International Settlements (BIS), a globally recognized provider of standardized macroeconomic and financial statistics.

Specifically, the dataset is drawn from the Residential Property Price Statistics (RPPS) database, which is widely used in economic and financial analysis.

### 1.1.1.2 Dataset Overview

**Canada – Selected Residential Property Prices, Real Index (2010 = 100)**

This dataset measures inflation-adjusted housing price movements and serves as a long-term benchmark for real estate performance.

To ensure consistency with other datasets, the analysis focuses on the period **1990–2025**, with earlier observations excluded during preprocessing.

### 1.1.1.3 Data Description

The dataset consists of a quarterly time series index of residential property prices in Canada.

#### Key characteristics include:

- Measures housing price changes over time
- Adjusted for inflation (real terms)
- Represents national-level housing market trends
- Expressed as an index (base year 2010 = 100)

Using real values enables meaningful comparison with other asset classes, such as equities.

### 1.1.1.4 Data Collection Method

The dataset was retrieved from:

<https://data.bis.org/topics/RPP/BIS,WS_SPP,1.0/Q.CA.R.628>

#### The collection process included:

1. Accessing the BIS RPPS database
2. Selecting the Canadian real residential property price index
3. Downloading the dataset in CSV format
4. Extracting and organizing the relevant time series

### 1.1.1.5 Purpose of Using This Data

This dataset is used to:

- Represent overall housing market performance in Canada
- Provide an inflation-adjusted benchmark for real estate investment
- Enable comparison with equity market returns

### 1.1.1.6 Limitations

- Does not capture regional variation
- Index-based (no absolute price levels)
- No breakdown by housing type

To address these limitations, a city-level dataset is introduced below.

---

## 1.1.2 City-Level Residential Property Price Index

### 1.1.2.1 Data Source

The data is sourced from Canadian Real Estate Price Index, which provides housing price indices across major Canadian cities.

### 1.1.2.2 Dataset Overview

**Residential Property Price Index – Six Major Canadian Cities**

#### Selected cities:

- Toronto
- Vancouver
- Montreal
- Calgary
- Ottawa
- Edmonton

The dataset covers **1999–2025** and is reported at a monthly frequency.

### 1.1.2.3 Data Description

The dataset consists of monthly housing price indices for multiple cities.

#### Key features include:

- Tracks city-level housing price changes
- Monthly frequency
- Index-based representation
- Enables cross-city comparison

This dataset captures regional variation that is not visible in national-level data.

### 1.1.2.4 Data Collection Method

The dataset was collected from:

<https://housepriceindex.ca/>

#### The process included:

1. Selecting relevant cities
2. Downloading the dataset in CSV format
3. Standardizing formats and aligning time periods
4. Organizing the data into structured tables

### 1.1.2.5 Purpose of Using This Data

This dataset enables:

- Analysis of regional housing market differences
- More realistic evaluation of investment performance
- Comparison with equity markets at the city level

### 1.1.2.6 Limitations

- Index-based (no absolute price levels)
- No property-type breakdown
- Potential inconsistencies across cities

---

## 1.2 Equity Market Index

### 1.2.1 Data Source

The equity market data used in this project is obtained from Yahoo Finance, a widely used platform that provides reliable historical financial data for stock indices and exchange-traded funds (ETFs).

#### The datasets include:

- **S&P/TSX Composite Index (^GSPTSE)** – representing the Canadian equity market
- **S&P 500 Index (^GSPC)** – representing the U.S. equity market
- **Vanguard Total World Stock ETF (VT)** – representing the global equity market

### 1.2.2 Dataset Overview

#### Canada Equity Market

- Index: S&P/TSX Composite Index
- Time period: 1990–2025
- Frequency: Monthly
- Currency: CAD

#### U.S. Equity Market

- Index: S&P 500 Index
- Time period: 1985–2025
- Frequency: Monthly
- Currency (original): USD

#### Global Equity Market

- ETF: Vanguard Total World Stock ETF (VT)
- Time period: August 2008–2025
- Frequency: Monthly
- Currency (original): USD

> **Note:**  
> The global dataset begins in August 2008, which limits long-term comparison with other datasets.

### 1.2.3 Data Description

All equity datasets consist of historical price data.

#### The primary variable used in this analysis is:

- **Adjusted Close (Adj Close)**

#### This variable is selected because:

- It accounts for dividends and stock splits
- It reflects total return performance
- It provides a more accurate representation of long-term investment outcomes

## 1.3 USD/CAD Exchange Rate

### Data Source

The USD/CAD exchange rate data used in this project was obtained from the Federal Reserve Economic Data (FRED) database maintained by the Federal Reserve Bank of St. Louis.

Source:  
[Canadian Dollars to U.S. Dollar Spot Exchange Rate (DEXCAUS) - FRED](https://fred.stlouisfed.org/series/DEXCAUS?)

The specific dataset used is:

```text
Canadian Dollars to U.S. Dollar Spot Exchange Rate (DEXCAUS)
```

The dataset measures:

```text
Canadian Dollars per One U.S. Dollar
```

and is reported as:

```text
Not Seasonally Adjusted
```

---

### Dataset Overview

The dataset includes:

- Time frequency: Daily
- Geographic coverage: Canada / United States
- Measurement type: Foreign exchange rate
- Units: Canadian Dollars per One U.S. Dollar
- Time range used in this project: 1990–2025

The original daily exchange rate data was converted into monthly average exchange rates during preprocessing.

---

### Purpose in This Project

The USD/CAD exchange rate data was used to convert U.S.-denominated stock market values into Canadian Dollars (CAD).

Specifically, the exchange rate dataset was used to:

- Convert S&P 500 values from USD to CAD
- Standardize all asset values into a common currency framework
- Enable direct comparison between:
  - Canadian housing prices
  - Canadian stock market returns
  - U.S. stock market returns

This conversion ensures that all asset growth comparisons are analyzed from a Canadian investor perspective.

---

### Data Preprocessing

The original dataset was downloaded as daily exchange rate data from FRED.

The preprocessing steps included:

- Standardizing date formats
- Converting exchange rate values into numeric format
- Resampling daily observations into monthly averages
- Filling missing monthly values using forward-fill methods

The cleaned exchange rate dataset was then merged with stock market datasets for currency conversion analysis.

## 1.4 Consumer Price Index (CPI)

### Data Source

The Consumer Price Index (CPI) data used in this project was obtained from the Statistics Canada CPI Monthly Table.

Source:  
https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810000401

Statistics Canada is the national statistical agency of Canada and provides official macroeconomic and inflation-related datasets widely used in economic research and financial analysis.

The specific dataset used is:

```text
Consumer Price Index, monthly, not seasonally adjusted
```

with the index base:

```text
2002 = 100
```

---

### Dataset Overview

The dataset contains monthly inflation index values for various product categories and geographic regions in Canada.

For this project, the following series was selected:

```text
All-items CPI
```

The dataset includes:

- Time frequency: Monthly
- Geographic coverage: Canada
- Measurement type: Consumer Price Index (CPI)
- Base year: 2002 = 100
- Time range used in this project: 1990–2025

---

### Purpose in This Project

The CPI dataset is used to adjust nominal stock market values for inflation in order to calculate real (inflation-adjusted) asset growth.

Specifically, the CPI data was used to:

- Convert nominal TSX returns into real returns
- Convert nominal S&P 500 returns into real returns
- Ensure comparability with the BIS real residential property price index
- Analyze long-term asset growth from a purchasing power perspective

Using inflation-adjusted data allows more meaningful comparison across housing and financial assets over long time horizons.

---

### Data Preprocessing

The original CPI dataset was downloaded in wide-table CSV format, where monthly observations were stored as column headers (e.g., Jan-90, Feb-90).

The preprocessing steps included:

- Removing metadata and unnecessary rows
- Selecting the “All-items” CPI series
- Converting the dataset from wide format to long format
- Standardizing dates into monthly datetime format
- Converting CPI values into numeric format

The cleaned CPI dataset was then merged with stock market data for inflation adjustment analysis.
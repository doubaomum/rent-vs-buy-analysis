# 1. Data Collection

# 1.1 Residential Property Price Data

To analyze long-term housing market performance in Canada, both national-level and city-level residential property price datasets were collected.

The project incorporates:

- Real residential property price indices  
- Nominal residential property price indices  
- Benchmark housing price data in Canadian Dollars (CAD)

Using multiple housing datasets allows the analysis to capture:

- Long-term housing market trends
- Inflation-adjusted housing performance
- Regional housing market variation
- Actual housing prices required for financial simulation

The national dataset provides a macro-level benchmark for Canadian housing markets, while the city-level datasets capture differences across major urban regions.

---

# 1.1.1 National-Level Residential Property Price Data (Canada)

## 1.1.1.1 Data Sources

The national-level housing datasets were collected from two primary sources:

### 1. Bank for International Settlements (BIS)

The long-term housing price index data was obtained from the Bank for International Settlements (BIS) Residential Property Price Statistics (RPPS) database.

Two datasets were collected:

- Canada – Selected Residential Property Prices, Real Index (2010 = 100)
- Canada – Selected Residential Property Prices, Nominal Index (2010 = 100)

The datasets are available from:

- Real Index:  
  <https://data.bis.org/topics/RPP/BIS,WS_SPP,1.0/Q.CA.R.628>

- Nominal Index:  
  <https://data.bis.org/topics/RPP/BIS,WS_SPP,1.0/Q.CA.N.628>

---

### 2. CREA Statistics

Additional benchmark housing price data was collected from CREA Statistics.

The dataset provides actual residential benchmark prices in Canadian Dollars (CAD) and was used to reconstruct historical housing price series required for financial simulation.

The data was collected from:

<https://stats.crea.ca/en-CA/>

---

## 1.1.1.2 Dataset Overview

### BIS Real Residential Property Price Index

The real housing price dataset:

- Measures inflation-adjusted residential property prices
- Represents national-level housing market trends
- Uses:

```text
2010 = 100
```

- Covers a long historical period beginning in 1970

This dataset is primarily used for macroeconomic and long-term asset comparison analysis.

---

### BIS Nominal Residential Property Price Index

The nominal housing price dataset:

- Measures residential property prices without inflation adjustment
- Uses:

```text
2010 = 100
```

- Represents raw market price appreciation over time

This dataset is used to reconstruct estimated historical housing prices in nominal Canadian Dollars.

---

### CREA Benchmark Price Data

The CREA dataset provides:

- Actual benchmark residential housing prices
- Canadian Dollar (CAD) values
- Monthly housing price observations
- Coverage from approximately 2005–2025

Unlike the BIS datasets, the CREA dataset contains absolute housing prices rather than index values.

These benchmark prices are required for:

- Mortgage calculations
- Down payment estimation
- Property tax estimation
- Rent-versus-buy simulation modeling

---

## 1.1.1.3 Reconstruction of Historical Housing Prices

The BIS datasets provide long-term index series but do not contain actual benchmark housing prices in Canadian Dollars.

To construct historical housing price estimates suitable for financial simulation, benchmark housing prices collected from CREA were combined with the BIS nominal housing price index.

The reconstruction process used the following approach:

```math
Historical\ Price
=
Benchmark\ Price_{2010}
\times
\frac{Historical\ Index}{Index_{2010}}
```

Using the benchmark housing price from CREA and the long-term nominal housing price index from BIS, historical housing prices were estimated for earlier periods.

---

## 1.1.1.4 Data Validation

To evaluate the reliability of the reconstructed housing price series, the estimated historical prices were compared against available benchmark housing prices from CREA over overlapping periods.

The observed differences between reconstructed prices and benchmark prices were relatively small, suggesting that the reconstructed historical housing price series provides a reasonable approximation for long-term financial modeling and simulation.

The same reconstruction methodology was later applied to the city-level housing datasets.

---

## 1.1.1.5 Purpose of Using Multiple Housing Datasets

The combination of real indices, nominal indices, and benchmark prices enables the project to support multiple analytical objectives.

### Real Index Data

Used for:

- Inflation-adjusted macroeconomic analysis
- Long-term comparison with stock market returns

### Nominal Index Data

Used for:

- Measuring raw housing market appreciation
- Reconstructing historical housing prices

### Benchmark Housing Prices

Used for:

- Mortgage and ownership cost calculations
- Rent-versus-buy simulation modeling
- Net worth analysis

---

## 1.1.1.6 Limitations

Several limitations remain within the housing datasets:

- National-level data does not capture regional variation
- Index-based datasets do not directly provide absolute housing prices
- Benchmark housing prices are only available for limited historical periods
- Reconstruction methods introduce estimation error
- Housing markets may vary significantly across property types and regions

To address regional differences, additional city-level housing datasets were collected and analyzed separately.


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
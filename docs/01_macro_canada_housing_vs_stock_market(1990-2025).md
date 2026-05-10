# Methodology: Canada Housing vs Stock Market Comparison (1990–2025)

---

# 1. Purpose of This Analysis

The purpose of this analysis is to compare the long-term performance of Canadian residential housing with major equity market indices from a Canadian investor’s perspective.

The assets included in this comparison are:

- Canada national residential property price index  
- S&P/TSX Composite Index (TSX)  
- S&P 500 Index  

Because these datasets use different original units, currencies, frequencies, and index baselines, all datasets required cleaning, transformation, and standardization before comparison.

This analysis focuses on:

- long-term cumulative growth  
- inflation-adjusted purchasing power  
- cross-asset comparison  
- Canadian investor perspective  

---

# 2. Analysis Period and Baseline Selection

The Canada national housing price index is available from 1970, while the stock market datasets begin later.

The selected starting dates are:

| Dataset | Start Date |
|---|---|
| Canada Housing Index | 1970 |
| TSX | January 1990 |
| S&P 500 | 1985 |

Since the TSX begins in January 1990, this project uses:

```text
January 1990 – 2025
```

as the common comparison period.

To allow direct comparison across assets with different original scales, all final series were normalized to:

```text
January 1990 = 100
```

This indexed-growth methodology allows cumulative performance trends to be compared consistently across housing and equity markets.

---

# 3. Data Cleaning and Preparation

## 3.1 Date Standardization

The original datasets used different date formats and frequencies.

Examples include:

- Monthly stock market data  
- Quarterly housing price index data  
- Daily USD/CAD exchange rate data  

To create a consistent time series framework, all date columns were converted into a standardized monthly format:

```text
YYYY-MM-01
```

This allowed all datasets to be merged and visualized on a common monthly timeline.

---

## 3.2 Canada National Housing Price Index

The Canada national housing dataset was obtained from the BIS Residential Property Price Database.

The selected series is reported as a:

```text
Real Residential Property Price Index
```

This means the housing series is already inflation-adjusted using CPI and therefore represents real housing price growth rather than nominal price appreciation.

The original BIS housing index uses:

```text
2010 = 100
```

Since this project compares long-term growth beginning in 1990, the housing series was re-normalized to:

```text
January 1990 = 100
```

The following formula was used:

```math
Housing\ Index_{1990} =
\frac{Current\ Housing\ Index}{Housing\ Index_{1990}} \times 100
```

This transformation preserves the original real growth pattern while changing the reference year to match the analysis period.

Because the BIS housing series is quarterly, it was converted into monthly frequency using forward-fill (`ffill()`), meaning each quarterly observation was carried forward until the next quarterly value became available.

---

## 3.3 TSX Index

The S&P/TSX Composite Index is denominated in Canadian dollars (CAD), so no currency conversion was required.

The TSX dataset was cleaned by:

- standardizing date columns  
- converting price values into numeric format  
- filtering observations to the 1990–2025 analysis period  

The original TSX series represents nominal market prices.

To make the stock market data methodologically consistent with the BIS real housing index, the TSX series was converted from nominal values into real values using the Canadian Consumer Price Index (CPI).

The inflation adjustment formula used was:

```math
Real\ TSX =
\frac{Nominal\ TSX}{CPI} \times CPI_{base}
```

After inflation adjustment, the real TSX series was normalized to:

```text
January 1990 = 100
```

using:

```math
TSX\ Index_{1990} =
\frac{Real\ TSX}{Real\ TSX_{1990}} \times 100
```

---

## 3.4 S&P 500 Index and Currency Conversion

The S&P 500 Index is originally denominated in U.S. dollars (USD). However, this project evaluates investment performance from the perspective of a Canadian investor.

Therefore, the S&P 500 series was first converted from USD into Canadian dollars (CAD) using the USD/CAD exchange rate.

The currency conversion formula used was:

```math
S\&P500_{CAD} =
S\&P500_{USD} \times USD/CAD
```

After currency conversion, the S&P 500 CAD series was converted from nominal values into real values using Canadian CPI.

The inflation adjustment formula used was:

```math
Real\ S\&P500 =
\frac{Nominal\ S\&P500_{CAD}}{CPI} \times CPI_{base}
```

The resulting real S&P 500 series was then normalized to:

```text
January 1990 = 100
```

using:

```math
S\&P500\ Index_{1990} =
\frac{Real\ S\&P500}{Real\ S\&P500_{1990}} \times 100
```

This process allows the S&P 500 to be compared consistently with Canadian housing and Canadian equities within the same currency and inflation-adjusted framework.

---

## 3.5 Consumer Price Index (CPI)

The Canadian Consumer Price Index (CPI) dataset was used to convert nominal stock market values into inflation-adjusted real values.

The CPI dataset uses:

```text
2002 = 100
```

Although the CPI uses a different reference year, this does not affect the inflation adjustment process because only relative price changes are required.

The CPI data was merged into the stock market dataset using the monthly date column.

---

## 3.6 USD/CAD Exchange Rate

The USD/CAD exchange rate dataset was obtained from the Federal Reserve Economic Data (FRED) database.

The exchange rate data was used to convert U.S. dollar-denominated equity market data into Canadian dollars.

The original exchange rate dataset was daily, while the main comparison dataset uses monthly frequency. Therefore, daily exchange rate observations were aggregated into monthly average exchange rates.

Missing exchange rate observations were filled using forward-fill to avoid gaps during dataset integration.

---

# 4. Final Dataset

After cleaning, currency conversion, inflation adjustment, and normalization, the final dataset includes the following variables:

| Variable | Description |
|---|---|
| `date` | Monthly observation date |
| `canada_house_index_2010` | Original BIS real housing index |
| `canada_house_real_index` | Housing index normalized to 1990 = 100 |
| `tsx_cad` | Original TSX nominal index |
| `tsx_real` | Inflation-adjusted TSX |
| `tsx_real_index` | TSX real index normalized to 1990 = 100 |
| `sp500_usd` | Original S&P 500 index (USD) |
| `usd_cad` | USD/CAD exchange rate |
| `sp500_cad` | CAD-adjusted S&P 500 |
| `sp500_real` | Inflation-adjusted S&P 500 |
| `sp500_real_index` | S&P 500 real index normalized to 1990 = 100 |

The final processed dataset was exported as:

```text
canada_house_vs_stocks_real_1990_index.csv
```

---

# 5. Compound Annual Growth Rate (CAGR)

To complement indexed growth visualization, Compound Annual Growth Rate (CAGR) was calculated for each asset class.

CAGR represents the annualized rate of return over the full analysis period and provides a standardized measure of long-term growth performance.

The formula used was:

```math
CAGR =
\left(
\frac{Ending\ Value}{Beginning\ Value}
\right)^{\frac{1}{n}} - 1
```

where:

- \(n\) represents the number of years in the analysis period.

Because all final stock market series were converted into real values and the BIS housing series is already inflation-adjusted, the resulting CAGR values represent:

- real annualized returns  
- inflation-adjusted growth  
- long-term purchasing-power performance  

---

# 6. Interpretation

The final indexed dataset allows Canadian housing, Canadian equities, and U.S. equities to be compared on a consistent scale.

Because all series are normalized to:

```text
January 1990 = 100
```

an index value of:

```text
200
```

indicates that the asset doubled relative to its January 1990 level in real (inflation-adjusted) terms.

This methodology enables direct comparison of long-term real cumulative growth across housing and equity markets from a Canadian investor’s perspective.
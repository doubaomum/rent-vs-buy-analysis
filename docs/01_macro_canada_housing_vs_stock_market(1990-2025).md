# Methodology: Canada Housing vs Stock Market Comparison (1990–2025)

## 1. Purpose of This Analysis

The purpose of this section is to compare the long-term performance of Canadian residential housing with major stock market indices from a Canadian investor's perspective.

The assets included in this comparison are:

- Canada national house price index
- S&P/TSX Composite Index
- S&P 500 Index

Because these datasets use different original units, currencies, and frequencies, they were cleaned and transformed before comparison.

---

## ## 2. Why 1990 Was Chosen as the Baseline

The Canada national house price index is available from 1970, which provides a much longer historical housing series. However, this page focuses on comparing housing with major stock market indices.

Among the selected comparison assets, the TSX data starts in January 1990, while the S&P 500 data starts earlier in 1985. Therefore, January 1990 was selected as the common baseline for this page.

Using 1990 as the baseline allows all three series to be compared over the same period:

- Canada national house price index
- TSX
- S&P 500

All series were normalized so that:

```text
January 1990 = 100

3. Data Cleaning and Preparation
3.1 Date Standardization

The original datasets used different date formats and frequencies.

Examples include:

Monthly stock market data
Quarterly Canada housing price index data
Daily USD/CAD exchange rate data

To make the datasets comparable, all date columns were converted into a standardized monthly format:

YYYY-MM-01

This creates a consistent monthly time series for merging and visualization.

3.2 Canada House Price Index

The Canada national house price index was originally reported as an index with:

2010 = 100

Since this project compares long-term growth from 1990, the index was re-normalized to:

1990 = 100

The formula used was:

Index_1990 = Current Value / Value in January 1990 × 100

This transformation preserves the growth pattern of the original housing index while changing the reference year to match the comparison period.

Because the Canada housing index is quarterly, it was converted to monthly frequency using forward-fill. This means that each quarterly value was carried forward until the next quarterly observation became available.

3.3 TSX Index

The TSX data is denominated in Canadian dollars, so no currency conversion was required.

The TSX price series was cleaned by:

Standardizing the date column
Converting price values to numeric format
Filtering the data to the 1990–2025 analysis period
Re-normalizing the series to January 1990 = 100

The formula used was:

TSX Index_1990 = Current TSX Value / TSX Value in January 1990 × 100
3.4 S&P 500 Index

The S&P 500 is originally denominated in U.S. dollars. However, this project analyzes investment performance from a Canadian investor's perspective.

Therefore, the S&P 500 was first converted from USD to CAD using the USD/CAD exchange rate:

S&P 500 CAD = S&P 500 USD × USD/CAD Exchange Rate

After currency conversion, the CAD-adjusted S&P 500 series was normalized to:

January 1990 = 100

The formula used was:

S&P 500 Index_1990 = S&P 500 CAD Value / S&P 500 CAD Value in January 1990 × 100

This allows the S&P 500 to be compared fairly with Canadian housing and the TSX in the same currency framework.

3.5 USD/CAD Exchange Rate

The exchange rate data was used to convert U.S. dollar-denominated stock market data into Canadian dollars.

The original exchange rate dataset was daily, while the main comparison dataset is monthly. Therefore, daily exchange rates were converted into monthly average exchange rates.

Missing exchange rate values were filled using forward-fill to avoid gaps during the merge process.

4. Final Dataset

After cleaning and transformation, the final dataset includes the following variables:

date
canada_house_index_2010
canada_house_index_1990
tsx_cad
tsx_index_1990
sp500_usd
usd_cad
sp500_cad
sp500_index_1990

The final dataset was exported as:

canada_house_vs_stocks_1990_index.csv
5. Interpretation

The final indexed dataset allows the three asset classes to be compared on the same scale.

Because all series are normalized to:

January 1990 = 100

a value of 300 means that the asset has tripled relative to its January 1990 level.

This makes it possible to compare long-term cumulative growth across Canadian housing, Canadian equities, and U.S. equities from a Canadian investor's perspective.
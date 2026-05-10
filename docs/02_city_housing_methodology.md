# Methodology: City-Level Housing Price Comparison (1999–2025)

---

# 1. Purpose of This Analysis

The purpose of this section is to compare long-term housing price growth across major Canadian cities.

The city-level housing markets included in this analysis are:

- Vancouver
- Toronto
- Montreal
- Calgary
- Edmonton
- Ottawa

This analysis focuses on:

- regional housing market differences
- inflation-adjusted housing growth
- city-level long-term performance
- consistent comparison across cities

---

# 2. Data Source

The city-level housing price data was collected from the Teranet–National Bank House Price Index.

The original dataset is reported as an index with:

```text
2005.06 = 100
```

This means the data does not represent actual house prices in dollars. Instead, it measures relative changes in house prices over time.

The city-level index is a nominal housing price index, meaning it is not adjusted for inflation.

---

# 3. Analysis Period and Baseline Selection

The city-level housing datasets do not all begin in 1990.

Some cities, such as Vancouver and Montreal, have data starting in 1990, while other cities begin later.

To ensure a fair comparison across all selected cities, this analysis uses a common period:

```text
1999–2025
```

The final city-level housing series were normalized to:

```text
1999 = 100
```

This allows all cities to be compared from a common starting point.

---

# 4. Date Standardization

The original city-level housing dataset used a monthly time column.

The date column was standardized into the following format:

```text
YYYY-MM-01
```

This ensures consistency with the rest of the project datasets, including CPI, stock market data, and national housing data.

---

# 5. Inflation Adjustment

Because the city-level housing price index is nominal, it was converted into real values using the Canadian Consumer Price Index (CPI).

The inflation adjustment formula was:

```math
Real\ City\ Housing\ Index =
\frac{Nominal\ City\ Housing\ Index}{CPI} \times CPI_{base}
```

where:

- `Nominal City Housing Index` is the original Teranet city-level index
- `CPI` is the Canadian Consumer Price Index for each month
- `CPI_base` is the CPI value in the selected base month

This adjustment removes the effect of inflation and allows the analysis to focus on real housing price growth.

---

# 6. Re-Indexing to 1999 = 100

After converting the city-level housing indices into real values, each city series was re-indexed to:

```text
1999 = 100
```

The normalization formula was:

```math
City\ Real\ Index_{1999} =
\frac{Current\ Real\ City\ Index}{Real\ City\ Index_{1999}} \times 100
```

This transformation preserves each city’s real growth pattern while changing the baseline to a common comparison year.

---

# 7. Final Dataset

The final processed dataset includes:

| Variable Type | Description |
|---|---|
| Original city index | Nominal city-level housing index |
| Real city index | Inflation-adjusted city housing value |
| Real city index 1999 | Real city housing index normalized to 1999 = 100 |

The final processed dataset was exported as:

```text
city_house_real_1999_index.csv
```

---

# 8. Interpretation

Because all city-level series are converted into real values and normalized to:

```text
1999 = 100
```

an index value of:

```text
200
```

means that the city’s housing market doubled in inflation-adjusted terms compared with its 1999 level.

This methodology allows regional Canadian housing markets to be compared on a consistent real-growth basis.

---

# 9. Why This Methodology Is Important

Using inflation-adjusted city-level housing indices provides a more meaningful comparison than nominal prices alone.

Nominal housing prices can appear to increase substantially over time, but part of that increase reflects general inflation rather than real gains in purchasing power.

By converting nominal city-level housing indices into real values, this analysis provides a clearer view of actual long-term housing market performance across Canadian cities.

This methodology is consistent with the project’s national housing and stock market comparison, where all major asset series are also analyzed using inflation-adjusted real values.


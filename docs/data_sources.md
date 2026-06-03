# Data Sources

This project uses several public housing, financial-market, macroeconomic, and rental-market datasets to compare buying versus renting in Canada. The data sources are organized into two main groups:

1. **Indexed market-comparison data** used for macro asset-return analysis in report pages 1–4.
2. **Actual price and cash-flow simulation data** used for the rent-versus-buy model in report pages 5–11.

This distinction is important because the project uses two different types of housing data:

- **Housing price indices** show relative price growth over time and are appropriate for comparing housing with equity-market returns.
- **Actual benchmark housing prices in Canadian dollars** are required for the owner-versus-renter simulation because mortgage size, down payment, ownership costs, sale proceeds, and net worth must be calculated in dollar terms.

The remaining report pages do not introduce new data: pages 8–11 re-run the simulation under sensitivity scenarios, page 12 presents conclusions, and pages 13–14 document modeling methodology.

---

## 1. Source-to-Report Mapping

| Data Category | Main Source | Frequency | Used In | Purpose |
|---|---|---:|---|---|
| Canada national housing price index | BIS Residential Property Price Statistics (RPPS) | Quarterly / monthly-aligned | Pages 1–2 | Long-term Canadian housing performance versus equities |
| City-level housing price index | Canadian Real Estate Price Index / housepriceindex.ca | Monthly | Pages 3–4 | Regional housing growth and city-level investment-horizon comparison |
| Actual benchmark housing prices | CREA Statistics | Monthly / available reporting frequency | Pages 5–11 | Purchase price, house value path, mortgage principal, owner net worth |
| Equity market data | Yahoo Finance | Monthly | Pages 1–4 and 5–11 | TSX, S&P 500, and portfolio return assumptions |
| USD/CAD exchange rate | FRED DEXCAUS | Daily, converted to monthly | Pages 1–4 and portfolio scenarios | Convert U.S.-denominated assets into Canadian dollars |
| Consumer Price Index | Statistics Canada CPI | Monthly | Pages 1–4 | Inflation adjustment for real asset-return comparison |
| Mortgage interest rates | Statistics Canada | Monthly | Pages 5–11 | Mortgage payment, interest cost, refinancing, rate sensitivity |
| Rental market data | CMHC Rental Market Survey / HMIP | Annual October snapshot | Pages 5–11 | Market rent, rent growth, vacancy, renter cash-flow simulation |

> **Page coverage note:** Pages 1–4 use the indexed macro data; pages 5–11 use the dollar-based simulation data (pages 8–11 re-run that simulation under portfolio, discipline, and interest-rate sensitivity scenarios). Page 12 reports conclusions and pages 13–14 document methodology; neither introduces new source data.

---

## 2. Housing Price Data

### 2.1 Indexed Housing Data for Macro Comparison

**Primary use:** Report pages 1–4  
**Purpose:** Compare housing price appreciation with equity-market performance over long historical horizons.

The indexed housing datasets are used to analyze relative growth rather than actual property values. These data are appropriate for questions such as:

- How did Canadian housing perform compared with the TSX and S&P 500?
- Which asset class produced the highest real CAGR over different entry years and holding periods?
- How did housing growth differ across Canadian cities?

#### 2.1.1 Canada National Housing Index

**Source:** Bank for International Settlements (BIS), Residential Property Price Statistics (RPPS)  
**Series used:** Canada selected residential property price index, real index, 2010 = 100  
**Coverage used:** 1990–2025 for macro comparison

This dataset measures inflation-adjusted Canadian residential property price growth at the national level. It is used in the first part of the report (pages 1–2) to compare Canadian housing with the TSX and S&P 500 on a real, inflation-adjusted basis. On this basis, Canadian housing returned roughly 2.0% real CAGR over 1990–2025, versus 3.9% for the TSX and 7.0% for the S&P 500.

Because this source is an index rather than a dollar-price series, it is useful for return comparison but not suitable for mortgage or net-worth simulation.

#### 2.1.2 City-Level Housing Price Index

**Source:** Canadian Real Estate Price Index / housepriceindex.ca  
**Cities used:** Vancouver, Toronto, Montreal, Calgary, Edmonton, Ottawa  
**Coverage used:** 1999–2025  
**Index base:** 2005-06 = 100 in the source data, later rebased for analysis

The city-level housing price index is used to compare regional housing market structures (pages 3–4). The report rebases these indices to common starting values, such as 1999 = 100 or a selected entry-year = 100, so that city-level housing growth can be compared directly.

This source supports:

- regional real housing growth analysis,
- city-level CAGR calculation,
- city-versus-equity investment-horizon heatmaps,
- comparison of regional housing cycles.

Like the BIS dataset, this city-level index is not used directly for mortgage simulation because it does not provide actual home prices in Canadian dollars.

---

### 2.2 Actual Benchmark Housing Prices for Simulation

**Primary use:** Report pages 5–11  
**Purpose:** Estimate the actual dollar value of homes over time for the owner-versus-renter simulation.

**Source:** CREA Statistics  
**Data type:** Residential benchmark prices in Canadian dollars (CAD)  
**Geography:** Canada and selected major Canadian cities (Vancouver, Toronto, Montreal, Calgary, Edmonton, Ottawa)

The actual benchmark price series is used in the simulation section because the model requires dollar-denominated home values. These prices are used to calculate:

- initial purchase price,
- down payment,
- mortgage principal,
- monthly mortgage payments,
- home value appreciation,
- sale proceeds,
- transaction costs,
- owner equity,
- owner net worth after sale.

This dataset is separate from the indexed housing data used in pages 1–4. The indexed data answers relative-return questions, while the benchmark-price data powers the financial simulation.

---

## 3. Equity Market Data

**Source:** Yahoo Finance  
**Frequency used:** Monthly  
**Purpose:** Compare housing with equity markets and model the renter-investor portfolio.

The project uses equity-market data for both the macro comparison and the renter-investor simulation.

### 3.1 Assets Included

| Asset | Symbol / Proxy | Currency | Role in Project |
|---|---|---|---|
| Canadian equity market | S&P/TSX Composite Index | CAD | Canadian stock-market benchmark and TSX renter portfolio |
| U.S. equity market | S&P 500 | USD, converted to CAD | U.S. equity benchmark and S&P 500 renter portfolio scenario |

> The final report models two renter portfolios only — 100% TSX (base case) and 100% S&P 500 (sensitivity scenario, pages 8 and 11). No global / all-world equity sleeve is used in the final analysis.

### 3.2 Use in the Report

In pages 1–4, equity-market series are compared with Canadian housing and city-level housing indices after currency conversion and inflation adjustment.

In pages 5–11, equity returns are used to model the renter-investor portfolio. The renter invests the monthly cash-flow difference (ownership cost minus renter cost) according to the selected portfolio assumption. The report includes TSX and S&P 500 portfolio scenarios to test how portfolio choice changes the rent-versus-buy outcome; this turned out to be the single most powerful lever in the analysis (page 8 and page 11).

---

## 4. USD/CAD Exchange Rate

**Source:** Federal Reserve Economic Data (FRED)  
**Series:** Canadian Dollars to U.S. Dollar Spot Exchange Rate (DEXCAUS)  
**Units:** Canadian dollars per one U.S. dollar  
**Original frequency:** Daily  
**Processed frequency:** Monthly average

The USD/CAD exchange rate is used to convert U.S.-denominated assets into Canadian dollars. This is necessary because the project evaluates outcomes from a Canadian investor perspective.

The exchange-rate data is used to convert S&P 500 values from USD to CAD. After conversion, U.S. equity returns can be compared directly with Canadian housing and Canadian equity-market (TSX) returns.

---

## 5. Consumer Price Index

**Source:** Statistics Canada  
**Series:** Consumer Price Index, monthly, not seasonally adjusted  
**Selected category:** All-items CPI  
**Base:** 2002 = 100  
**Frequency:** Monthly  
**Coverage used:** 1990–2025

The CPI data is used to convert nominal asset values into real, inflation-adjusted values for the macro return analysis.

The CPI adjustment supports:

- real TSX returns,
- real S&P 500 returns in CAD,
- real housing index comparison,
- real CAGR calculations,
- inflation-adjusted indexed growth charts.

Report pages 1–4 use real, inflation-adjusted asset values so that long-term growth reflects purchasing-power changes rather than only nominal price increases. The simulation figures on pages 5–11 are reported in nominal CAD.

---

## 6. Mortgage Interest Rate Data

**Source:** Statistics Canada  
**Series used:** Average 5-year fixed mortgage rate  
**Frequency:** Monthly  
**Coverage used:** 2005–2025

Mortgage-rate data is used in the homeowner simulation to estimate financing costs. The model assumes a 5-year fixed mortgage and uses historical mortgage-rate observations to calculate mortgage payments and interest costs over the holding period.

The mortgage-rate data is used to:

- calculate monthly mortgage payments,
- separate mortgage interest from principal repayment,
- model renewal and refinancing schedules,
- estimate ownership cash-flow costs,
- construct interest-rate sensitivity scenarios.

The report tests three financing scenarios (page 10):

| Scenario | Description |
|---|---|
| Lower rates | Historical mortgage rate minus 2 percentage points |
| Base rate | Historical mortgage rate |
| Higher rates | Historical mortgage rate plus 2 percentage points |

The ±2 percentage-point scenarios are sensitivity tests applied to the mortgage renewal schedule. They are not forecasts of future mortgage rates.

---

## 7. Rental Market Data

**Source:** Canada Mortgage and Housing Corporation (CMHC), Housing Market Information Portal / Rental Market Survey  
**Data type:** Primary rental market average rent and vacancy rate  
**Frequency:** Annual October snapshot  
**Cities used:** Vancouver, Toronto, Montreal, Calgary, Edmonton, Ottawa  
**Unit type used:** 2-bedroom rental units

Rental data is used to model renter cash flows and regional rent dynamics. The 2-bedroom rental series is used as the main rental-market indicator because it better represents typical household housing demand than smaller unit types.

The rental data supports:

- market rent estimation,
- city-level rent growth,
- rent-versus-ownership cost comparison,
- renter cash-flow simulation,
- move probability and rent-reset logic,
- rent-control simulation assumptions.

Because CMHC rental data is reported annually, rental series are aligned to the monthly simulation timeline during preprocessing.

**Market rent vs. effective paid rent.** The simulation distinguishes *market rent* (the prevailing rent a new tenant would pay) from *effective paid rent* (what a sitting tenant actually pays). Existing tenants receive regulated, rent-controlled increases, while a renter who moves resets to prevailing market rent. This divergence between market and paid rent grows over time and is a core part of the renter cash-flow model (methodology described on report page 13).

---

## 8. Model Assumption Tables

In addition to external datasets, the project uses assumption tables for the simulation model. These are not raw data sources; they are modeling parameters used to translate market data into owner and renter financial outcomes.

### 8.1 Ownership Assumptions

| Variable | Base Assumption |
|---|---:|
| Down payment | 20% |
| Mortgage type | 5-year fixed |
| Amortization | 25 years |
| Property tax | Dynamic by city |
| Maintenance | 1/3 of market rent |
| Depreciation | 1% of structure value |
| Insurance | 0.3% of house value |
| Purchase cost | 1% |
| Sale transaction cost | 6% |

**Depreciation — structure value shares.** Depreciation is applied only to the structure portion of a home, not the land. Because land-value intensity differs by market, the structure share of value varies by city (report page 14):

| City | Structure value share |
|---|---:|
| Calgary | 60% |
| Edmonton | 60% |
| Canada | 50% |
| Ottawa | 50% |
| Montreal | 50% |
| Toronto | 45% |
| Vancouver | 35% |

High-land-value markets such as Vancouver and Toronto carry a smaller structure share, so less of their home value depreciates.

### 8.2 Renting and Investment Assumptions

| Variable | Base Assumption |
|---|---:|
| Renter discipline | 100% |
| Rent growth mode | Controlled / market rent logic |
| Rent control | Dynamic by city |
| Move probability | Dynamic by city |
| Move cost | Dynamic by city and rent |
| Market rent | Dynamic by city |
| Effective rent paid | Simulated using rent-control and moving logic |
| Investment portfolio | 100% TSX in base case |
| Investment fee | 0.10% |
| Tax drag | Dynamic by portfolio |
| Monthly contribution | Ownership cost minus renter cost |
| Portfolio return | Dynamic by portfolio |
| Portfolio return (net) | Net return after fees and taxes |

The 0.10% annual management fee approximates low-cost ETF investing (report page 13).

---

## 9. Data Preprocessing Summary

All datasets were cleaned and transformed before being loaded into the analysis model.

Key preprocessing steps included:

1. **Standardizing column names**  
   Date fields and value fields were renamed consistently across datasets.

2. **Converting dates to monthly format**  
   Daily, annual, quarterly, and irregular series were aligned to a consistent monthly timeline where needed.

3. **Cleaning numeric values**  
   Text-based numeric fields, commas, percentages, and missing-value markers were converted into usable numeric formats.

4. **Currency conversion**  
   U.S.-denominated equity series (S&P 500) were converted into Canadian dollars using the USD/CAD exchange rate.

5. **Inflation adjustment**  
   CPI was used to convert nominal market data into real values for pages 1–4.

6. **Index rebasing**  
   Housing and equity series were rebased to common starting values such as 1990 = 100, 1999 = 100, or selected entry-year = 100.

7. **Simulation dataset construction**  
   Actual benchmark house prices, mortgage rates, rent data, and portfolio returns were combined to generate owner and renter monthly schedules.

---

## 10. Data Limitations

Several limitations should be considered when interpreting the results:

- Housing price indices measure market-level price movement and do not capture individual property-level variation.
- Indexed housing data cannot be used directly for mortgage simulation because it does not provide dollar prices.
- Benchmark housing prices are market-level estimates and may not reflect specific neighbourhoods, property types, or transaction prices.
- CMHC rental data is annual and mainly reflects the primary rental market, which may differ from condominium or informal rental markets.
- The mortgage-rate series is national and does not capture lender-specific rates, borrower credit risk, or regional mortgage pricing differences.
- The ±2 percentage-point mortgage scenarios are hypothetical sensitivity tests, not forecasts.
- Equity-market results depend on benchmark selection, currency conversion, reinvestment assumptions, and time period.
- Simulation outputs are reported in nominal CAD, while the macro comparison (pages 1–4) is in real terms; the two should not be read on the same scale.
- Historical data from 1990–2025 and 2005–2025 should not be interpreted as a forecast of future outcomes.

---

## 11. Summary

The project combines index-based macro data and dollar-based simulation data to answer two different but connected questions:

1. **Macro comparison:** How did Canadian housing perform compared with equity markets over long historical periods?
2. **Rent-versus-buy simulation:** Given actual home prices, rents, mortgage rates, and investment returns, would a homeowner or renter-investor have built more wealth?

Using both types of data allows the report to show that housing was a relatively weak raw asset compared with equities (2.0% real CAGR versus 3.9% for the TSX and 7.0% for the S&P 500), while also explaining why ownership can still compete financially through leverage, avoided rent, forced saving, and holding-period effects.

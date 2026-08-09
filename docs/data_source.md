## 1. Verified sources

### 1.1 Canada national housing price index

| Field | Value |
|---|---|
| **Provider** | Bank for International Settlements (BIS) |
| **Database** | Residential Property Price Statistics (RPPS) |
| **Series** | `Q.CA.R.628` |
| **URL (series)** | https://data.bis.org/topics/RPP/BIS,WS_SPP,1.0/Q.CA.R.628 |
| **URL (about)** | https://www.bis.org/statistics/pp.htm |
| **Frequency** | Quarterly |
| **Basis** | **Real (already inflation-adjusted at source)** — no CPI deflation applied downstream |
| **Loads to** | `raw.canada_house_price_index_2010_100` |

---

### 1.2 City-level housing price index

| Field | Value |
|---|---|
| **Provider** | Teranet–National Bank |
| **Product** | Teranet–National Bank House Price Index™ |
| **URL** | https://housepriceindex.ca/ |
| **Frequency** | Monthly |
| **Base** | June 2005 = 100 |
| **Method** | Repeat-sales, single-family homes |
| **Loads to** | `raw.city_house_price_index` → `stg.city_house_price_index` |


---

### 1.3 City-level benchmark housing prices

| Field | Value |
|---|---|
| **Provider** | CREA (Canadian Real Estate Association) |
| **Product** | MLS® Home Price Index — benchmark prices and HPI |
| **Frequency** | Monthly, seasonally adjusted |
| **Loads to** | `raw.city_house_real_prices` (one CSV per city) |
| **URL (HPI product)** | https://www.crea.ca/housing-market-stats/mls-home-price-index/ |
| **URL (stats portal)** | https://creastats.crea.ca/en-CA/ |

This source feeds **both** analytical tracks:

| Column | Used for |
|---|---|
| `composite_hpi_sa` | `stg.city_indexed_house_prices` → real city index, Jan 2005 = 100 |
| `composite_benchmark_sa` | `stg.city_house_prices` → dollar-denominated simulation input |

Cities loaded: Canada, Vancouver, Calgary, Edmonton, Toronto, Ottawa, Montreal.

---

### 1.4 Equity market data

**Provider:** Retrieval site used: Yahoo Finance Canada (`ca.finance.yahoo.com`)
**Variable used:** Adjusted Close (accounts for dividends and splits)

| Series | Ticker | URL | Retrieval range | Frequency |
|---|---|---|---|---|
| S&P/TSX Composite | `^GSPTSE` | [link](https://ca.finance.yahoo.com/quote/%5EGSPTSE/history/?frequency=1mo&period1=299511000&period2=1786155427) | 1979-06-29 → 2026-03-08 | `1mo` |
| S&P 500 | `^GSPC` | [link](https://ca.finance.yahoo.com/quote/%5EGSPC/history/?frequency=1mo&period1=-1325583000&period2=1786155476) | 1927-12-30 → 2026-03-08 | `1mo` |
| Vanguard Total World | `VT` |[link](https://ca.finance.yahoo.com/quote/VT/history/?period1=1214487000&period2=1786190896)| 2008-06 → 2023-08| `1mo` |

The S&P/TSX Composite is already denominated in CAD. The S&P 500 and VT are denominated in USD and are converted to CAD using the USD/CAD exchange-rate series before Canadian-investor analysis.

**Decoded URL parameters:**

| Parameter | S&P/TSX | S&P 500 | Meaning |
|---|---|---|---|
| `frequency` | `1mo` | `1mo` | Monthly bars |
| `period1` | `299511000` | `-1325583000` | 1979-06-29 / 1927-12-30 (series inception on Yahoo) |
| `period2` | `1786155427` | `1786155476` | 2026-03-08 (retrieval date) |


---

### 1.5 City-level rent

| Field | Value |
|---|---|
| **Provider** | Canada Mortgage and Housing Corporation (CMHC) |
| **Portal** | Housing Market Information Portal (HMIP) |
| **Survey** | Rental Market Survey (RMS) |
| **Table** | `2.2.11` — Primary Rental Market, Average Rent ($) by bedroom type |
| **URL (Toronto table)** | https://www03.cmhc-schl.gc.ca/hmip-pimh/en/TableMapChart/Table?TableId=2.2.11&GeographyId=2270&GeographyTypeId=3&DisplayAs=Table |
| **URL (data tables index)** | https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market |
| **Frequency** | Annual, October reference period |
| **Coverage** | 1990–2025 (Toronto; verify per city) |
| **Loads to** | `raw.city_rent_raw` |


| Code | Meaning |
|---|---|
| `a` | Excellent |
| `b` | Very good |
| `c` | Good |
| `d` | Poor — use with caution |
| `**` | Suppressed for confidentiality or not statistically reliable |

---

### 1.6 USD/CAD exchange rate

| Field | Value |
|---|---|
| **Provider** | Board of Governors of the Federal Reserve System (US) |
| **Distributor** | FRED, Federal Reserve Bank of St. Louis |
| **Series** | `DEXCAUS` |
| **URL** | https://fred.stlouisfed.org/series/DEXCAUS |
| **Definition** | Canadian dollars per one U.S. dollar, not seasonally adjusted |
| **Frequency** | Daily |
| **Coverage** | 1971-01-04 onward |
| **Note** | Noon buying rates, New York City |
| **Loads to** | `raw.usd_cad_raw` |
---

### 1.7 Consumer Price Index

| Field | Value |
|---|---|
| **Provider** | Statistics Canada |
| **Table** | 18-10-0004-01 (formerly CANSIM 326-0020) |
| **Series** | Consumer Price Index, monthly, not seasonally adjusted |
| **URL** | https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810000401 |
| **DOI** | https://doi.org/10.25318/1810000401-eng |
| **Frequency** | Monthly |
| **Index base** | **2002 = 100** |
| **Coverage** | 1914 onward |
| **Loads to** | `raw.canada_cpi_raw` |

---
### 1.8 Canada 5-year mortgage rate

| Field | Value |
|---|---|
| **Provider** | Statistics Canada (source: CMHC) |
| **Table** | 34-10-0145-01 (formerly CANSIM 027-0015) |
| **Series** | CMHC conventional mortgage lending rate, 5-year term |
| **URL** | https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410014501 |
| **DOI** | https://doi.org/10.25318/3410014501-eng |
| **Frequency** | Monthly |
| **Geography** | Canada only |
| **Coverage** | 1951 onward |
| **Loads to** | `raw.canada_5yearmortgage_raw` |

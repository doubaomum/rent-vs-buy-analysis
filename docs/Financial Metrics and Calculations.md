# 3. Financial Metrics and Calculations

## 3.1 Indexed Growth Comparison

To enable meaningful comparison across housing markets and financial assets, all datasets were transformed into indexed growth series.

The original datasets used different measurement systems:

- The Canada-wide housing dataset was already reported as an index with:

```text
2010 = 100
```

- The city-level housing datasets were originally indexed with:

```text
2005.06 = 100
```

- Stock market datasets (TSX, S&P 500, and VT ETF) were reported as market prices rather than index values.

In addition, different datasets used different currencies:

- Canadian housing and TSX data were denominated in Canadian Dollars (CAD)
- S&P 500 and VT ETF data were denominated in U.S. Dollars (USD)

To ensure comparability, all selected variables were converted into indexed growth series using a common base value:

```text
2010 = 100
```

The following normalization formula was used:

```math
Indexed\ Value = \frac{Current\ Value}{Base\ Year\ Value} \times 100
```

This transformation allows:

- Direct comparison across assets with different original scales
- Consistent visualization of long-term growth trends
- Comparison between housing markets and equity markets

Indexed growth comparison is widely used in:

- Macroeconomic analysis
- Financial market research
- Investment performance evaluation

---
## 3.2 Currency Conversion

## Currency Structure

- TSX data were already denominated in CAD
- S&P 500 and VT ETF data were originally denominated in USD.

To ensure consistency across all asset classes, U.S.-denominated assets were converted into Canadian Dollars using the USD/CAD exchange rate.

Exchange rate data was obtained from Federal Reserve Economic Data (FRED).

The conversion formula used in this project is:

```math
Asset\ Value_{CAD} = Asset\ Value_{USD} \times USD/CAD\ Exchange\ Rate
```

After conversion, all datasets were expressed in Canadian Dollars, allowing direct comparison between:

- Canadian housing markets
- Canadian equity markets
- U.S. equity markets
- Global stock market investments

```python
fx = fx.set_index("date").resample("MS").mean().reset_index()
```

The U.S. and global stock market datasets were then converted into CAD:

```python
df["sp500_cad"] = df["sp500_usd"] * df["usd_cad"]
df["vt_cad"] = df["vt_usd"] * df["usd_cad"]
```

This step is important because exchange rate fluctuations can significantly affect realized investment returns from a Canadian investor’s perspective.


## 3.3 Compound Annual Growth Rate (CAGR)

To evaluate long-term asset performance, this project uses the Compound Annual Growth Rate (CAGR).

CAGR measures the annualized rate of return of an asset while accounting for compound growth over time. Unlike arithmetic average returns, CAGR reflects the actual long-term growth path of an investment and is therefore more suitable for financial analysis.

The CAGR formula used in this project is:

```math
CAGR = \left(\frac{Ending\ Value}{Beginning\ Value}\right)^{\frac{1}{n}} - 1
```

Where:

- **Ending Value** = asset value in 2025
- **Beginning Value** = asset value in 2010
- **n** = number of years between the beginning and ending periods

CAGR calculations were applied to:

- Canadian housing market
- Major Canadian city housing markets
- S&P 500
- TSX Composite Index
- Global stock market (VT ETF)

The use of CAGR enables consistent comparison between:

- Housing appreciation
- Canadian equity returns
- U.S. equity returns
- Global investment performance

---


# 3. Financial Metrics and Calculations

## 3.1 Indexed Growth Comparison

To enable meaningful comparison across housing markets and financial assets, selected variables were transformed into indexed growth series.

The original datasets used different measurement systems:

- The Canada-wide housing dataset was originally reported as an index with:

```text
2010 = 100
```

- The city-level housing datasets were originally indexed with:

```text
2005.06 = 100
```

- Stock market datasets, including the TSX, S&P 500, and VT ETF, were reported as market prices rather than index values.

In addition, different datasets used different currencies:

- Canadian housing and TSX data were denominated in Canadian Dollars (CAD)
- S&P 500 and VT ETF data were denominated in U.S. Dollars (USD)

To ensure comparability across different asset classes, indexed normalization was applied using common benchmark years.

---

### 1. Long-Term Comparison

Assets with full historical coverage were normalized using:

```text
1999 = 100
```

This comparison includes:

- Canadian housing market
- Major Canadian city housing markets
- TSX Composite Index
- S&P 500
- Rent series

---

### 2. Global Market Comparison

The VT ETF dataset begins in July 2008.

Therefore, a second indexed comparison series was created using:

```text
2008-07 = 100
```

This comparison includes:

- Canadian housing market
- Major Canadian city housing markets
- TSX Composite Index
- S&P 500
- VT ETF
- Rent series

---

### Normalization Formula

```math
Indexed\ Value = \frac{Current\ Value}{Base\ Value} \times 100
```

This transformation enables:

- Direct comparison across assets with different original scales
- Consistent visualization of long-term growth trends
- Comparison between housing markets and financial assets

Indexed growth comparison is widely used in:

- Macroeconomic analysis
- Financial market research
- Investment performance evaluation

---

# 3.2 Currency Conversion

The S&P 500 and VT ETF datasets were originally denominated in U.S. Dollars (USD), while Canadian housing and TSX datasets were denominated in Canadian Dollars (CAD).

To ensure consistency across all asset classes, U.S.-denominated assets were converted into Canadian Dollars using the USD/CAD exchange rate.

Exchange rate data was obtained from the Federal Reserve Economic Data (FRED) database.

## Currency Structure

- TSX data were already denominated in CAD
- S&P 500 and VT ETF data were originally denominated in USD

The conversion formula used in this project is:

```math
Asset\ Value_{CAD} = Asset\ Value_{USD} \times USD/CAD\ Exchange\ Rate
```

The exchange rate dataset was first converted from daily frequency into monthly average values:

```python
fx = fx.set_index("date").resample("MS").mean().reset_index()
```

The U.S. and global stock market datasets were then converted into CAD:

```python
stock_cleaned["sp500_cad"] = (
    stock_cleaned["sp500_usd"] * stock_cleaned["usd_cad"]
)

stock_cleaned["vt_cad"] = (
    stock_cleaned["vt_usd"] * stock_cleaned["usd_cad"]
)
```

After conversion, all datasets were expressed in Canadian Dollars, allowing direct comparison between:

- Canadian housing markets
- Canadian equity markets
- U.S. equity markets
- Global stock market investments

This step is important because exchange rate fluctuations can significantly affect realized investment returns from a Canadian investor’s perspective.

---

# 3.3 Compound Annual Growth Rate (CAGR)

To evaluate long-term asset performance, this project uses the Compound Annual Growth Rate (CAGR).

CAGR measures the annualized rate of return of an asset while accounting for compound growth over time. Unlike arithmetic average returns, CAGR reflects the actual long-term growth path of an investment and is therefore more suitable for long-term financial analysis.

The CAGR formula used in this project is:

```math
CAGR = \left(\frac{Ending\ Value}{Beginning\ Value}\right)^{\frac{1}{n}} - 1
```

Where:

- **Ending Value** = asset value at the end of the analysis period
- **Beginning Value** = asset value at the beginning of the analysis period
- **n** = number of years between the beginning and ending periods

CAGR calculations were applied to:

- Canadian housing market
- Major Canadian city housing markets
- TSX Composite Index
- S&P 500
- Global stock market (VT ETF)

Because different datasets have different historical coverage periods, CAGR calculations use the full available time horizon for each asset class.

The use of CAGR enables consistent comparison between:

- Housing appreciation
- Canadian equity returns
- U.S. equity returns
- Global investment performance
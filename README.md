# Rent vs Buy in Canada: Housing, Investing, and Household Wealth

## Project Summary

This project analyzes whether buying a home or renting while investing would have produced higher household wealth in major Canadian housing markets.

The analysis combines a **Power BI dashboard** with a **Python-based simulation engine**. It compares Canadian housing, equity markets, rents, mortgage rates, and city-specific ownership costs across historical market conditions.

The project is designed as a **scenario-based financial analysis**, not a prediction model. The core question is:

> Under historical Canadian market conditions, when did homeownership outperform renting plus investing, and which assumptions changed the result the most?

---

## Why This Project Matters

The rent-versus-buy decision is often simplified into a comparison between monthly rent and mortgage payment. This project takes a broader financial view by modeling:

- housing as both a consumption good and a leveraged asset,
- renter investing behavior,
- mortgage financing and renewal risk,
- city-specific property taxes and housing costs,
- rent-control and moving assumptions,
- portfolio choice and compounding effects.

The result is a more realistic comparison between a **homeowner** and a **renter-investor** over time.

---

## Key Questions

This project answers four main questions:

1. Did Canadian housing outperform equity markets over the long run?
2. How different were regional housing markets across major Canadian cities?
3. Would a homeowner or a renter-investor have built more wealth from 2005 to 2025?
4. Which factors changed the rent-versus-buy result the most: portfolio choice, renter discipline, interest rates, city, or holding period?

---

## Dashboard Overview

The Power BI report follows a story-driven structure:

| Page | Section | Purpose |
|---:|---|---|
| 1 | Long-Term Real Growth of Canadian Housing and Equity Markets | Compare Canada housing, TSX, and S&P 500 from 1990–2025 |
| 2 | Time Horizon Sensitivity of Housing and Equity Returns | Test how entry year and holding period affect asset winners |
| 3 | Regional Housing Market Structures in Canada | Compare real housing growth across major Canadian cities |
| 4 | Regional Housing Competitiveness Across Investment Horizons | Compare regional housing and equities across holding periods |
| 5 | Canada-Wide Rent vs Buy Base Model | Compare national homeowner and renter-investor wealth paths |
| 6 | Regional Renting vs Buying Results | Compare owner and renter outcomes across cities |
| 7 | Owner vs Renter Wealth Gap by City and Holding Period | Analyze where and when ownership had the largest advantage |
| 8 | Portfolio Sensitivity | Test TSX versus S&P 500 renter-investor portfolios |
| 9 | Renter Discipline Sensitivity | Test how under-investing renter savings changes outcomes |
| 10 | Interest Rate Sensitivity | Test historical mortgage rates versus ±2 percentage-point scenarios |
| 11 | Sensitivity Comparison | Compare which risk factor had the largest impact |
| 12 | Final Conclusions | Summarize findings, limitations, and practical implications |

---

## Headline Findings

| Dimension | Finding |
|---|---|
| Strongest raw asset, 1990–2025 | S&P 500 — 7.0% real CAGR |
| Base-case rent-vs-buy winner, 2005–2025 | Owner — narrowly, across all 7 markets |
| Most owner-favourable city | Vancouver, with a +291 average indexed wealth gap |
| Most renter-competitive city | Edmonton, with a −10 average indexed wealth gap |
| Dominant risk factor | Renter portfolio choice |
| Biggest driver of ownership advantage | Holding period |
| National owner vs renter CAGR | 13.5% vs 13.2%, a near-tie |

---

## Main Results

### 1. Equities were the strongest raw asset

From 1990 to 2025, U.S. equities delivered the highest real return among the three major asset classes analyzed.

| Asset | Real CAGR, 1990–2025 |
|---|---:|
| S&P 500 | 7.0% |
| TSX | 3.9% |
| Canada Housing | 2.0% |

Canadian housing was more stable than equities, but it produced the weakest raw price appreciation. This means housing did not win as a simple price index.

### 2. Housing still competed because ownership is a financial structure

Although Canadian housing had weaker raw returns, homeownership still competed in the rent-versus-buy simulation because ownership combines:

- leverage through mortgage financing,
- principal repayment and forced saving,
- avoided rent over time,
- exposure to city-specific housing appreciation.

In other words, housing succeeded more as a **leveraged household-finance structure** than as a standalone investment asset.

### 3. Buying narrowly won in the base case

Under the base assumptions, owning generally outperformed renting from 2005 to 2025. However, the national result was close:

| Strategy | Net-Worth CAGR |
|---|---:|
| Homeowner | 13.5% |
| Renter-investor | 13.2% |

The ownership advantage was real, but narrow and conditional.

### 4. City outcomes varied significantly

Vancouver had the strongest ownership result, while Edmonton was the most renter-competitive market.

| City | Winner | Owner Net-Worth Index | Renter Net-Worth Index | Owner CAGR | Renter CAGR |
|---|---|---:|---:|---:|---:|
| Vancouver | Owner | 1,581 | 665 | 14.8% | 9.9% |
| Toronto | Owner | 1,389 | 1,062 | 14.1% | 12.5% |
| Montreal | Owner | 1,261 | 1,045 | 13.5% | 12.5% |
| Calgary | Owner | 1,145 | 948 | 13.0% | 11.9% |
| Ottawa | Owner | 1,141 | 1,060 | 12.9% | 12.5% |
| Edmonton | Owner | 1,025 | 925 | 12.3% | 11.8% |
| Canada | Owner | 1,264 | 1,183 | 13.5% | 13.2% |

The indexed approach is used because each city has different absolute home prices and therefore different starting capital requirements. Setting each scenario to a common starting index makes cross-city comparison more meaningful.

### 5. Portfolio choice was the dominant risk factor

The renter's investment portfolio had the largest effect on the final result. Switching the renter from a TSX portfolio to an S&P 500 portfolio erased much of the homeowner advantage, especially over long horizons.

At a 20-year horizon, the portfolio effect reached roughly **811–960 indexed points**, depending on the comparison view. It was larger than both renter discipline and interest-rate sensitivity.

### 6. Holding period amplified every result

The longer the household stayed in the home, the more strongly ownership tended to benefit.

The average indexed owner-renter wealth gap increased from approximately **+22 at 5 years** to **+274 at 20 years**. This suggests that ownership's advantage came more from time in the market than from perfectly timing the purchase.

### 7. Renter discipline and interest rates mattered, but were secondary

Renter discipline was meaningful because the renter-investor only competes with the homeowner if the monthly savings are actually invested. Reducing renter discipline from 100% to 70% increased the owner advantage, especially in near-balanced markets.

Interest rates also mattered. A ±2 percentage-point shock to historical mortgage rates changed the owner-renter wealth gap, especially over longer holding periods and in higher-priced markets. However, both discipline and interest rates had smaller long-run effects than portfolio choice.

---

## Data Sources

This project uses two kinds of housing data:

1. **Indexed housing data** for macro comparison with stocks.
2. **Actual benchmark housing prices in CAD** for the rent-versus-buy simulation.

This distinction is important because indexed housing data is useful for return comparison, but the simulation requires dollar values for down payment, mortgage size, ownership costs, sale proceeds, and net worth.

| Data Category | Main Source | Use in Project |
|---|---|---|
| Canada national housing index | BIS Residential Property Price Statistics | Long-term Canada housing versus equity comparison |
| City-level housing index | Canadian Real Estate Price Index / housepriceindex.ca | Regional indexed housing growth comparison |
| Actual benchmark housing prices | CREA Statistics | Home purchase price, mortgage size, owner net worth |
| Equity market data | Yahoo Finance | TSX and S&P 500 returns |
| USD/CAD exchange rate | FRED DEXCAUS | Convert U.S. equity returns into CAD |
| Consumer Price Index | Statistics Canada | Inflation adjustment for real return analysis |
| Mortgage rates | Statistics Canada | Mortgage payment and interest-rate sensitivity |
| Rental market data | CMHC Rental Market Survey / HMIP | Market rent, renter cash flow, rent-control simulation |

Full documentation:

```text
docs/data_sources.md
docs/data_cleaning.md
```

---

## Methodology Summary

### Macro asset-return analysis

Pages 1–4 compare housing and equity markets using indexed, inflation-adjusted data.

The analysis includes:

- Canada housing versus TSX versus S&P 500, 1990–2025,
- S&P 500 converted into Canadian dollars,
- real return comparison using CPI adjustment,
- indexed growth charts,
- real CAGR calculations,
- entry-year and holding-period sensitivity heatmaps.

### Rent-versus-buy simulation

Pages 5–11 use a monthly dollar-based simulation model.

The simulation compares two strategies:

| Strategy | Description |
|---|---|
| Homeowner | Buys a home with 20% down, pays ownership costs, builds equity, and sells at the end of the holding period |
| Renter-investor | Rents a comparable home, invests the initial capital instead of buying, and invests monthly savings when renting is cheaper |

The simulation is calculated in Python and visualized in Power BI.

Full methodology:

```text
docs/simulation_methodology.md
```

---

## Core Simulation Assumptions

### Homeowner assumptions

| Category | Base Assumption |
|---|---:|
| Down payment | 20% |
| Mortgage | 5-year fixed |
| Amortization | 25 years |
| Property tax | Dynamic by city |
| Maintenance | 1/3 of market rent |
| Depreciation | 1% of structure value |
| Insurance | 0.3% of house value |
| Purchase cost | 2% |
| Sale transaction cost | 6% |

### Renter-investor assumptions

| Category | Base Assumption |
|---|---:|
| Renter discipline | 100% in base case |
| Rent growth mode | Controlled / market, dynamic by city |
| Move probability | Dynamic by city |
| Move cost | Dynamic by city and rent |
| Effective rent paid | Simulated using rent-control and moving logic |
| Base investment portfolio | 100% TSX |
| Portfolio sensitivity | 100% S&P 500 |
| Investment fee | 0.10% |
| Tax drag | Dynamic by portfolio |
| Monthly contribution | Owner cash outflow minus renter cash outflow |

---

## Sensitivity Analysis

The report tests three major risk levers:

| Sensitivity Factor | Scenarios Tested | What It Measures |
|---|---|---|
| Portfolio choice | TSX vs S&P 500 | How much renter investment returns affect the verdict |
| Renter discipline | 100% vs 70% | Whether the renter consistently invests monthly savings |
| Interest rates | Historical rate, −2%, +2% | How mortgage financing conditions affect ownership |

At a 20-year horizon, the risk factors ranked clearly:

| Risk Factor | Approximate 20-Year Impact |
|---|---:|
| Portfolio choice | Up to ~960 indexed points |
| Renter discipline | Up to ~526 indexed points |
| Interest rates | Up to ~336 indexed points |

Portfolio choice was the most powerful lever, followed by renter discipline and interest-rate sensitivity.

---

## Tools Used

| Tool | Role |
|---|---|
| Python | Data cleaning, transformation, owner schedule, renter portfolio simulation |
| pandas | Time-series processing and scenario-table generation |
| Power BI | Dashboard design and interactive analysis |
| DAX | Net-worth indexing, CAGR, win-rate, and sensitivity measures |
| Excel | Initial source-file review and light pre-cleaning |
| Git / GitHub | Version control and project documentation |

---

## Repository Structure

```text
rent-vs-buy-analysis/
│
├── README.md
│
├── data/
│   ├── external/              # Raw external datasets
│   ├── assumptions/           # Scenario, investment, and renter policy assumptions
│   └── processed/             # Cleaned and final modeling datasets
│
├── docs/
│   ├── data_sources.md
│   ├── data_cleaning.md
│   ├── simulation_methodology.md
│   └── key_findings.md
│
├── src/
│   ├── cleaning/              # Data cleaning scripts
│   └── simulation/            # Owner and renter simulation scripts
│
├── powerbi/
│   └── rent_vs_buy_report.pbix
│
└── screenshots/
    ├── page_01_macro_growth.png
    ├── page_05_base_model.png
    ├── page_08_portfolio_sensitivity.png
    └── page_12_conclusions.png
```

---

## How to Read This Repository

For a quick review:

```text
README.md
docs/key_findings.md
screenshots/
```

For data documentation:

```text
docs/data_sources.md
docs/data_cleaning.md
```

For the simulation model:

```text
docs/simulation_methodology.md
src/simulation/
```

For the dashboard:

```text
powerbi/rent_vs_buy_report.pbix
```

---

## Limitations

This project is a historical scenario analysis, not a forecast.

Important limitations include:

- Historical returns do not guarantee future outcomes.
- Macro figures are real and inflation-adjusted, while simulation results are nominal CAD.
- Housing indices and benchmark prices may not reflect individual properties, neighbourhoods, or transaction prices.
- Rental data mainly reflects reported rental market datasets and may not fully capture informal or condominium rental markets.
- Rent-control and moving assumptions simplify real-world tenant behavior.
- The model assumes renter investing discipline, which may not hold in practice.
- Mortgage-rate scenarios are sensitivity tests, not predictions.
- The model does not include all household-specific factors such as tax-sheltered account limits, personal tax brackets, income changes, lifestyle preferences, or liquidity needs.

---

## Final Conclusion

The rent-versus-buy question has no universal answer.

Over the historical period analyzed, ownership generally outperformed renting under the base assumptions, but the advantage was narrow, conditional, and reversible. A disciplined renter-investor holding a strong equity portfolio could match or outperform ownership in several scenarios.

The most important lesson from this project is that the result depends less on housing appreciation alone and more on:

- holding period,
- investment portfolio,
- renter discipline,
- city-specific housing dynamics,
- financing conditions.

Housing won modestly in the base case, but the winner was driven by the full financial structure around buying and renting — not by house price growth alone.

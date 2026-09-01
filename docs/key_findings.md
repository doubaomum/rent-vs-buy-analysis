# Key Findings

**Project:** Rent-Invest vs. Buy in Canada  
**Scope:** Household-level rent-versus-buy simulation across the Canada aggregate and six Canadian city markets

---

## 1. How to Read This Report

This report evaluates whether a household would have accumulated more real wealth by **buying a home** or by **renting and investing the capital and monthly cash-flow difference**.

| Layer                          | Question                                                                                 | Basis                                                                                                 |
| ------------------------------ | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Household-level simulation** | Would a household have finished with more wealth by buying, or by renting and investing? | Historical home prices, rents, mortgage rates, owner costs, portfolio returns, and monthly cash flows |

The model compares the complete balance sheets of two households that begin with the same initial capital.

### 1.1 Fixed reporting assumptions

```text
Down payment = 20%
Renter investment discipline = 100%
```

Both are held constant in the final report so that differences in outcomes are driven by the tested market and scenario variables rather than by different starting-capital requirements or saving behaviour.

### 1.2 Sensitivity dimensions

**City · Purchase year · Holding period · Mortgage rate · Renter portfolio**

### 1.3 Primary outcome metric

```text
Final Real Net Worth Gap
= Owner Real Net Worth − Renter-Investor Real Net Worth
```

A positive gap means the owner finished ahead. A negative gap means the renter-investor finished ahead.

All reported net-worth values are inflation-adjusted to the purchasing power of the scenario's own purchase month.

### 1.4 Sensitivity methodology

The sensitivity page uses a **one-driver-at-a-time** framework. The slicers define a reference scenario. For each sensitivity measure, the model varies one driver while holding the remaining relevant settings fixed.

```text
Outcome Range
= Highest Final Real Net Worth Gap
− Lowest Final Real Net Worth Gap
```

`Highest Gap → Lowest Gap` identifies the tested values that generate the maximum and minimum Owner−Renter gap. It does **not** mean that the first city, year, portfolio, or mortgage scenario is universally “best.”

| Driver               | What varies             | What is held fixed                                                    |
| -------------------- | ----------------------- | --------------------------------------------------------------------- |
| **Purchase timing**  | Eligible purchase years | Reference market, holding period, portfolio, mortgage scenario        |
| **City / market**    | Tested markets          | Reference purchase year, holding period, portfolio, mortgage scenario |
| **Portfolio choice** | TSX vs. S&P 500         | Reference market, purchase year, holding period, mortgage scenario    |
| **Mortgage rate**    | Base vs. Base +2pp      | Reference market, purchase year, holding period, portfolio            |

Purchase-timing comparisons include only cohorts with a complete holding period inside the historical data window. Because the city-level series begin in 2005 and end in 2025, the number of eligible purchase cohorts falls as the holding horizon increases.

> **Interpretation note:** Purchase-timing sensitivity should not be compared mechanically across holding periods. The max–min range is calculated over a progressively smaller set of entry years. At 20 years, only one eligible cohort remains, so purchase-timing sensitivity is not reported.

---

## 2. Household Framework

Both households begin with identical initial capital. Their housing cash outflows are allowed to differ.

The comparison is balanced by explicitly transferring the monthly difference between owner and renter housing outflows into or out of the renter's investment portfolio.

### 2.1 Owner

Initial capital is allocated to:

```text
Down Payment + Purchase Cost
```

Monthly owner cash outflow is:

```text
Mortgage Payment
+ Property Tax
+ Maintenance
+ Insurance
```

The mortgage payment is separated into two economically different components:

| Component     | Treatment                                                          |
| ------------- | ------------------------------------------------------------------ |
| **Principal** | Not treated as an unrecoverable cost because it builds home equity |
| **Interest**  | Treated as an unrecoverable financing cost                         |

Principal still appears in **cash outflow**, because the household must fund it each month.

Owner wealth is measured on a liquidation-equivalent basis:

```text
Owner Net Worth
= House Market Value
− Mortgage Balance
− Estimated Sale Cost
```

The model applies an estimated sale cost equal to 6% of current property value.

### 2.2 Renter-Investor

The renter begins with an investment portfolio equal to the capital the owner used for the down payment and purchase costs.

Under the fixed 20% down-payment assumption:

```text
Initial Renter Portfolio
= 22% of Purchase Price
```

Monthly renter housing outflow is:

```text
Actual Rent + Moving Cost
```

The monthly difference is:

```text
Monthly Savings Difference
= Owner Total Cash Outflow
− Renter Total Cash Outflow
```

If the difference is positive, the renter invests it. If it is negative, the renter withdraws from the portfolio.

Renter net worth is therefore the portfolio value after initial invested capital, monthly contributions and withdrawals, realized portfolio returns, investment fees, and modeled tax drag.

### 2.3 Why this is a fairer comparison

The model does **not** compare rent with a mortgage payment alone.

Instead, it compares full owner housing cash outflow, full renter housing cash outflow, home equity, renter invested capital, and the monthly cash-flow difference.

This avoids two common distortions: treating mortgage principal as if it were consumed, and treating the renter's unused capital as if it disappeared.

---

## 3. Illustrative Benchmark Scenario

Canada-wide benchmark, purchased in **2005**, held for **20 years**, 20% down payment, Base mortgage rates, and **TSX portfolio**:

| Measure                      | Owner       | Renter-Investor |
| ---------------------------- | -----------:| ---------------:|
| Average monthly cash outflow | **$1,520**  | **$903**        |
| Cash-outflow CAGR            | **1.66%**   | **3.21%**       |
| Final real net worth         | **$372.7K** | **$441.7K**     |

| Ratio measure                                    | Value    |
| ------------------------------------------------ | --------:|
| Peak Owner / Renter real net-worth ratio (2022)  | **1.81** |
| Final Owner / Renter real net-worth ratio (2025) | **0.84** |

The renter-investor finished ahead by roughly **$69K**, even though the owner held the wealth advantage through much of the middle of the period.

The renter led early, when owner equity was still small relative to the purchase and financing commitment. Housing appreciation, mortgage leverage, and principal repayment then pushed the owner ahead, with the ratio peaking near **1.81** around the 2022 housing-market high. The subsequent housing correction narrowed and eventually reversed that advantage, with the ratio finishing at **0.84**.

The renter also maintained a large cash-flow advantage. Average monthly housing outflow was about **$620 lower** than the owner's. That difference was available for continued investment, while the renter's initial capital had already been invested rather than committed to the home purchase.

Although renter cash outflow grew faster than owner cash outflow, it started from a much lower base and remained lower throughout the scenario.

> **Interpretation:** This scenario is useful because neither strategy dominates at every point in time. The owner leads for a substantial period, but the final result reverses. The main lesson is therefore not “renting wins,” but that the conclusion depends on the full path of housing prices, financing costs, rent, and alternative investment returns.

---

| Market    | Housing Real CAGR | Rent Real CAGR | Owner / Renter Cash Outflow Ratio | Owner Outflow CAGR | Renter Outflow CAGR | Final Net Worth Ratio |
| --------- | ----------------- | -------------- | --------------------------------- | ------------------ | ------------------- | --------------------- |
| Vancouver | 4.14%             | 1.97%          | 0.83                              | 1.44%              | 3.62%               | 2.72                  |
| Montreal  | 3.34%             | 1.60%          | 1.42                              | 1.60%              | 2.92%               | 1.19                  |
| Toronto   | 3.17%             | 1.24%          | 1.53                              | 1.53%              | 4.05%               | 1.01                  |
| Ottawa    | 2.59%             | 1.42%          | 1.31                              | 1.56%              | 2.92%               | 1.03                  |
| Calgary   | 2.48%             | 2.32%          | 1.10                              | 1.52%              | 4.52%               | 1.05                  |
| Edmonton  | 2.14%             | 1.77%          | 1.02                              | 1.40%              | 4.42%               | 1.18                  |

After adjusting for inflation, real rent increased more slowly than real housing prices in every market. However, the size of this difference varied substantially by city.

* **Vancouver had the largest growth gap:** housing grew by **4.14% annually**, compared with **1.97% real rent growth**. Together with an average owner cash outflow below the renter’s, this produced the strongest owner result—a final net-worth ratio of **2.72**.
* **Montreal also had a meaningful growth gap:** **3.34% housing growth versus 1.60% rent growth**. The owner finished 19% ahead despite having substantially higher average monthly cash outflow.
* **Toronto had strong housing growth relative to rent:** **3.17% versus 1.24%**. Nevertheless, the final ratio was only **1.01** because the owner carried the highest relative monthly cash burden. Housing appreciation alone was therefore insufficient to create a decisive owner advantage.
* **Ottawa finished close to parity:** housing grew by **2.59%**, compared with **1.42% real rent growth**, but the owner’s average monthly outflow was still 31% higher.
* **Calgary had the smallest difference between housing and rent growth:** **2.48% versus 2.32%**. Its final ratio of **1.05** is consistent with a nearly balanced outcome.
* **Edmonton also had a relatively narrow growth difference:** **2.14% housing growth versus 1.77% rent growth**. However, owner and renter monthly outflows were almost equal, limiting the renter’s ability to invest monthly savings and helping the owner finish 18% ahead.
* **Canada shows why growth rates alone do not determine the winner.** National housing grew faster than rent—**2.87% versus 1.63%**—but the renter still finished ahead. The renter benefited from much lower monthly cash outflow and a TSX real return of **3.84%**, which exceeded national housing growth.

> **Main finding:** Faster housing appreciation generally strengthened owner outcomes, but the final result depended on the combination of housing growth, rent growth, financing costs, cash-flow differences, leverage, and investment returns—not the housing-versus-rent growth gap alone.

## 4. Sensitivity Analysis

**Reference scenario:** Purchase Year = 2005, Portfolio = TSX, Mortgage = Base. Across the four views, the holding period changes from 5 to 20 years.

Within each sensitivity measure, the selected driver is varied while the remaining assumptions are held at their reference settings.

### 4.1 Canada Aggregate

| Holding | Metric       | Purchase timing | City      | Portfolio | Mortgage |
| ------- | ------------ | ---------------:| ---------:| ---------:| --------:|
| **5Y**  | Net worth    | **$244K**       | $74K      | $24K      | $20K     |
|         | Cash outflow | **$89K**        | $60K      | **$0**    | $17K     |
| **10Y** | Net worth    | **$281K**       | $106K     | $114K     | $37K     |
|         | Cash outflow | $88K            | **$120K** | **$0**    | $40K     |
| **15Y** | Net worth    | $208K           | $213K     | **$259K** | $54K     |
|         | Cash outflow | $84K            | **$183K** | **$0**    | $43K     |
| **20Y** | Net worth    | —               | $245K     | **$455K** | $66K     |
|         | Cash outflow | —               | **$243K** | **$0**    | $47K     |

**1. Portfolio and mortgage-rate sensitivity are similar at five years, then diverge sharply.**

| Holding | Portfolio | Mortgage | Ratio |
| ------- | ---------:| --------:| -----:|
| 5Y      | $24K      | $20K     | 1.2×  |
| 10Y     | $114K     | $37K     | 3.1×  |
| 15Y     | $259K     | $54K     | 4.8×  |
| 20Y     | $455K     | $66K     | 6.9×  |

Over five years, the tested portfolio choice produces a net-worth range similar to the mortgage-rate scenarios. Over twenty years, portfolio sensitivity is almost seven times larger.

Portfolio sensitivity grows about **19×** across the tested horizons, compared with roughly **3×** for mortgage rates. This is consistent with investment returns compounding on a growing portfolio while mortgage-rate exposure applies to a debt balance that generally declines through amortization.

**2. Portfolio choice changes wealth without changing spending.**

Portfolio cash-outflow sensitivity is **$0 at every horizon** because changing the renter's portfolio does not alter rent or owner carrying costs. Yet net-worth sensitivity rises from **$24K at five years to $455K at twenty years**.

This is both an analytical finding and a structural validation: portfolio performance changes accumulated wealth, not household housing expenditure.

**3. Geography becomes the dominant long-run cash-flow driver and remains a major wealth driver.**

City sensitivity rises from **$60K to $243K** for cumulative cash outflow and from **$74K to $245K** for final net worth.

By twenty years, the two ranges are almost identical in magnitude. That does **not** prove that the wealth effect is caused entirely by cash flow, because city also changes housing appreciation, mortgage size, rent dynamics, and renter investment contributions.

**4. Mortgage cash-flow sensitivity begins to plateau while its wealth effect continues to grow.**

Mortgage cash-flow sensitivity rises from **$17K at five years to $40K at ten years**, then increases only modestly to **$47K by twenty years**.

Net-worth sensitivity continues rising from **$20K to $66K**. Earlier financing differences can continue to affect later wealth through home-equity accumulation and renter portfolio contributions even after the incremental cash-flow effect begins to flatten.

**5. Purchase timing affects wealth much more than cumulative spending.**

Purchase-timing cash-flow sensitivity stays around **$84K–$89K** across the 5–15 year horizons, while net-worth sensitivity ranges from **$208K to $281K**.

Entry timing therefore appears to operate more strongly through asset values and wealth accumulation than through cumulative housing expenditure alone.

---

### 4.2 Toronto Market

| Holding | Outcome      | Purchase timing | Portfolio | Mortgage |
| ------- | ------------ | ---------------:| ---------:| --------:|
| **5Y**  | Net worth    | **$460K**       | $30K      | $27K     |
|         | Cash outflow | **$151K**       | $0        | $27K     |
| **10Y** | Net worth    | **$490K**       | $138K     | $45K     |
|         | Cash outflow | **$134K**       | $0        | $45K     |
| **15Y** | Net worth    | **$363K**       | $312K     | $65K     |
|         | Cash outflow | $56K            | $0        | $44K     |
| **20Y** | Net worth    | —               | **$539K** | $93K     |
|         | Cash outflow | —               | $0        | $85K     |

**1. Toronto has the highest measured purchase-timing sensitivity in the comparison.**

Toronto's purchase-timing net-worth sensitivity reaches **$460K at five years and $490K at ten years**, far above the Canada aggregate. Even at fifteen years, the range remains **$363K**.

This makes Toronto particularly dependent on the market cycle in which the household enters. A conclusion based on one Toronto purchase cohort generalizes poorly to another historical entry period.

**2. Toronto's timing effect becomes increasingly concentrated in wealth rather than cash flow.**

| Holding | Net-worth sensitivity | Cash-outflow sensitivity |
| ------- | ---------------------:| ------------------------:|
| 5Y      | $460K                 | $151K                    |
| 10Y     | $490K                 | $134K                    |
| 15Y     | $363K                 | $56K                     |

At fifteen years, net-worth timing sensitivity is more than six times the cash-outflow sensitivity.

This suggests that Toronto's purchase-year effect is increasingly expressed through asset values and wealth accumulation rather than through differences in cumulative spending.

**3. Toronto has the strongest long-run portfolio sensitivity among the tested city markets.**

Toronto portfolio sensitivity rises:

```text
$30K → $138K → $312K → $539K
```

The same TSX-versus-S&P 500 choice therefore matters much more to final wealth in Toronto than in the other city markets.

A plausible model-based explanation is that Toronto's owner-versus-renter cash-flow path changes the amount and timing of capital entering the renter portfolio, which then compounds differently under the two return series.

**4. Toronto shows a transition from entry-timing sensitivity toward investment-return sensitivity.**

At 5 years:

> Purchase timing **$460K** vs. Portfolio **$30K**

At 10 years:

> Purchase timing **$490K** vs. Portfolio **$138K**

At 15 years:

> Purchase timing **$363K** vs. Portfolio **$312K**

The two are almost equal by fifteen years.

The exact crossover should not be overinterpreted because portfolio sensitivity always compares the same two portfolios while purchase-timing sensitivity is calculated over a shrinking cohort set.

> **Short horizon: entry timing dominates. Longer horizon: investment-return sensitivity becomes increasingly important.**

**5. Toronto retains unusually high mortgage sensitivity at long horizons.**

At twenty years:

- Net-worth mortgage sensitivity = **$93K**
- Cash-outflow mortgage sensitivity = **$85K**

Toronto's cash-flow sensitivity also rises sharply from **$44K at fifteen years to $85K at twenty years**, unlike the flatter Canada-wide pattern.

> **Interpretation:** Toronto is the most scenario-sensitive city in the analysis across several tested dimensions. The result is not simply “Toronto is expensive”; rather, its rent-versus-buy conclusion is highly conditional on entry timing, financing, and the renter's alternative investment path.

---

### 4.3 Vancouver Market

| Holding | Outcome      | Purchase timing | Portfolio | Mortgage |
| ------- | ------------ | ---------------:| ---------:| --------:|
| **5Y**  | Net worth    | **$316K**       | $18K      | $21K     |
|         | Cash outflow | **$56K**        | $0        | $24K     |
| **10Y** | Net worth    | **$255K**       | $54K      | $34K     |
|         | Cash outflow | **$106K**       | $0        | $40K     |
| **15Y** | Net worth    | $89K            | **$119K** | $55K     |
|         | Cash outflow | **$71K**        | $0        | $30K     |
| **20Y** | Net worth    | —               | **$218K** | $75K     |
|         | Cash outflow | —               | $0        | $37K     |

**1. Vancouver's measured purchase-timing sensitivity falls sharply with longer horizons.**

```text
$316K → $255K → $89K
```

This differs materially from Toronto, where timing sensitivity remains very large at fifteen years.

The decline should not be interpreted as proof that longer holding periods eliminate timing sensitivity because the set of eligible purchase cohorts also shrinks.

**2. Vancouver's wealth and cash-flow timing sensitivities converge by fifteen years.**

| Holding | Net Worth | Cash Outflow |
| ------- | ---------:| ------------:|
| 5Y      | $316K     | $56K         |
| 10Y     | $255K     | $106K        |
| 15Y     | $89K      | $71K         |

At fifteen years, the two ranges are relatively close.

This is almost the opposite of Toronto, where fifteen-year timing sensitivity remains heavily concentrated in wealth.

**3. Vancouver's timing extremes change with the holding horizon.**

| Holding | Highest Gap → Lowest Gap |
| ------- | ------------------------ |
| 5Y      | **2019 → 2013**          |
| 10Y     | **2008 → 2014**          |
| 15Y     | **2007 → 2010**          |

There is no single consistently favourable or unfavourable purchase cohort. Vancouver's timing result is therefore strongly path-dependent.

**4. Vancouver has the lowest long-run portfolio sensitivity among the tested city markets.**

Portfolio sensitivity rises:

```text
$18K → $54K → $119K → $218K
```

Compounding still matters, but the same portfolio assumption has a smaller long-run effect in Vancouver than in the other city markets.

**5. Vancouver's mortgage effect accumulates in wealth but remains relatively contained in cash flow.**

Net-worth mortgage sensitivity:

```text
$21K → $34K → $55K → $75K
```

Cash-outflow mortgage sensitivity:

```text
$24K → $40K → $30K → $37K
```

The wealth effect rises steadily, while the cash-flow effect does not.

> **Interpretation:** Vancouver's distinctive feature is not simply high housing cost. In this model, short-horizon timing matters substantially, but long-run portfolio and mortgage sensitivities are comparatively muted. Because city-specific carrying-cost assumptions feed directly into renter contributions, the precise magnitude should be interpreted together with those assumptions rather than as a purely market-observed effect.

---

### 4.4 Montreal Market

| Holding | Outcome      | Purchase timing | Portfolio | Mortgage |
| ------- | ------------ | ---------------:| ---------:| --------:|
| **5Y**  | Net worth    | **$125K**       | $17K      | $14K     |
|         | Cash outflow | **$66K**        | $0        | $17K     |
| **10Y** | Net worth    | **$88K**        | $78K      | $25K     |
|         | Cash outflow | **$40K**        | $0        | $21K     |
| **15Y** | Net worth    | $75K            | **$172K** | $41K     |
|         | Cash outflow | **$39K**        | $0        | $31K     |
| **20Y** | Net worth    | —               | **$297K** | $69K     |
|         | Cash outflow | —               | $0        | **$64K** |

**1. Montreal has the lowest measured purchase-timing sensitivity.**

```text
$125K → $88K → $75K
```

The final Owner−Renter gap varies less across Montreal entry cohorts than in markets such as Toronto or Vancouver.

**2. Montreal shows relatively limited amplification from purchase timing into final wealth.**

At fifteen years:

- Net-worth timing sensitivity = **$75K**
- Cash-outflow timing sensitivity = **$39K**

The separation remains much smaller than in Toronto.

**3. Portfolio choice catches purchase timing relatively early.**

At ten years:

> Timing **$88K** vs. Portfolio **$78K**

At fifteen years:

> Portfolio **$172K** vs. Timing **$75K**

Montreal therefore transitions away from timing-dominated outcomes earlier and more smoothly than Toronto.

**4. Portfolio becomes the dominant long-run wealth driver, but its effect remains moderate relative to Toronto.**

Portfolio sensitivity rises:

```text
$17K → $78K → $172K → $297K
```

Long-run investment choice matters substantially, but the model does not amplify portfolio differences as strongly as in Toronto.

**5. Mortgage sensitivity becomes much more relevant over twenty years.**

At twenty years:

- Net-worth mortgage sensitivity = **$69K**
- Cash-outflow mortgage sensitivity = **$64K**

The similar magnitudes do not prove that the entire wealth effect comes from cash flow, but they show that financing assumptions matter to both dimensions.

> **Interpretation:** Montreal is the least entry-dependent city in the analysis. Its sensitivity profile is comparatively balanced: purchase timing matters less, while portfolio and mortgage effects build gradually rather than appearing as extreme short-run swings.

---

### 4.5 Ottawa Market

| Holding | Outcome      | Purchase timing | Portfolio | Mortgage |
| ------- | ------------ | ---------------:| ---------:| --------:|
| **5Y**  | Net worth    | **$292K**       | $21K      | $19K     |
|         | Cash outflow | **$80K**        | $0        | $24K     |
| **10Y** | Net worth    | **$105K**       | $93K      | $32K     |
|         | Cash outflow | **$52K**        | $0        | $27K     |
| **15Y** | Net worth    | $183K           | **$207K** | $49K     |
|         | Cash outflow | **$64K**        | $0        | $35K     |
| **20Y** | Net worth    | —               | **$357K** | $81K     |
|         | Cash outflow | —               | $0        | **$50K** |

**1. Ottawa's purchase-timing sensitivity is non-linear.**

```text
$292K → $105K → $183K
```

It falls sharply at ten years and then rebounds at fifteen years.

Cash-outflow timing sensitivity follows a similar pattern:

```text
$80K → $52K → $64K
```

This means Ottawa does not support a simple “longer holding reduces timing sensitivity” story.

**2. The 2005 cohort consistently produces Ottawa's lowest Owner−Renter gap.**

| Holding | Highest Gap → Lowest Gap |
| ------- | ------------------------ |
| 5Y      | **2020 → 2005**          |
| 10Y     | **2013 → 2005**          |
| 15Y     | **2008 → 2005**          |

The highest-gap cohort changes, but the lowest-gap cohort remains 2005.

**3. Portfolio choice catches timing relatively early.**

At ten years:

> Timing **$105K** vs. Portfolio **$93K**

At fifteen years:

> Portfolio **$207K** vs. Timing **$183K**

Portfolio therefore becomes a major wealth driver earlier than in Toronto.

**4. Ottawa develops substantial long-run portfolio sensitivity.**

Portfolio sensitivity rises:

```text
$21K → $93K → $207K → $357K
```

This is lower than Toronto but materially higher than Montreal, Edmonton, or Vancouver.

**5. Timing matters much more for wealth than for spending, but less extremely than in Toronto.**

At fifteen years:

- Net-worth timing sensitivity = **$183K**
- Cash-outflow timing sensitivity = **$64K**

**6. Mortgage sensitivity grows steadily without becoming dominant.**

Net worth:

```text
$19K → $32K → $49K → $81K
```

Cash outflow:

```text
$24K → $27K → $35K → $50K
```

> **Interpretation:** Ottawa is best described as a mixed-regime market. Its timing effect is irregular rather than persistently high or low, while portfolio sensitivity becomes important relatively early.

---

### 4.6 Edmonton Market

| Holding | Outcome      | Purchase timing | Portfolio | Mortgage |
| ------- | ------------ | ---------------:| ---------:| --------:|
| **5Y**  | Net worth    | **$135K**       | $16K      | $16K     |
|         | Cash outflow | **$71K**        | $0        | $11K     |
| **10Y** | Net worth    | **$221K**       | $65K      | $26K     |
|         | Cash outflow | **$99K**        | $0        | $26K     |
| **15Y** | Net worth    | **$187K**       | $144K     | $39K     |
|         | Cash outflow | **$128K**       | $0        | $39K     |
| **20Y** | Net worth    | —               | **$236K** | $59K     |
|         | Cash outflow | —               | $0        | **$28K** |

**1. Edmonton is one of the few markets where purchase-timing cash-flow sensitivity rises with horizon.**

```text
$71K → $99K → $128K
```

The net-worth timing effect also remains substantial:

```text
$135K → $221K → $187K
```

Timing differences therefore remain visible in both wealth and cumulative spending.

**2. The same timing extremes persist across every measurable horizon.**

| Holding | Highest Gap → Lowest Gap |
| ------- | ------------------------ |
| 5Y      | **2007 → 2005**          |
| 10Y     | **2007 → 2005**          |
| 15Y     | **2007 → 2005**          |

That persistence is unusual compared with Vancouver or Ottawa.

**3. Edmonton's wealth and cash-flow timing sensitivities move closer together over time.**

At fifteen years:

- Net worth = **$187K**
- Cash outflow = **$128K**

Timing therefore remains materially embedded in the household spending path rather than becoming primarily a wealth effect.

**4. Edmonton remains one of the less portfolio-sensitive markets.**

Portfolio sensitivity rises:

```text
$16K → $65K → $144K → $236K
```

At twenty years, only Vancouver is lower among the tested city markets.

**5. Edmonton has the lowest measured long-run mortgage sensitivity.**

Net worth:

```text
$16K → $26K → $39K → $59K
```

Cash outflow:

```text
$11K → $26K → $39K → $28K
```

The twenty-year cash-flow sensitivity actually falls from its fifteen-year level.

**6. Timing remains important for longer than in Montreal or Ottawa.**

At fifteen years:

> Timing **$187K** vs. Portfolio **$144K**

Portfolio is catching up, but timing remains larger wherever both are measurable.

> **Interpretation:** Edmonton is characterized by persistent purchase-cohort differences and comparatively low long-run sensitivity to portfolio and mortgage assumptions. Its results are therefore more strongly shaped by entry conditions than by the alternative investment or financing scenarios tested here.

---

### 4.7 Calgary Market

| Holding | Outcome      | Purchase timing | Portfolio | Mortgage |
| ------- | ------------ | ---------------:| ---------:| --------:|
| **5Y**  | Net worth    | **$150K**       | $22K      | $19K     |
|         | Cash outflow | **$67K**        | $0        | $19K     |
| **10Y** | Net worth    | **$216K**       | $92K      | $35K     |
|         | Cash outflow | **$103K**       | $0        | $36K     |
| **15Y** | Net worth    | $171K           | **$204K** | $55K     |
|         | Cash outflow | **$132K**       | $0        | $49K     |
| **20Y** | Net worth    | —               | **$352K** | $82K     |
|         | Cash outflow | —               | $0        | **$56K** |

**1. Calgary's purchase-timing effect remains persistent in both wealth and spending.**

Net-worth timing sensitivity:

```text
$150K → $216K → $171K
```

Cash-outflow timing sensitivity:

```text
$67K → $103K → $132K
```

As in Edmonton, the cash-flow range increases rather than fading.

**2. The same 2007 → 2005 timing ordering persists at every measurable horizon.**

| Holding | Highest Gap → Lowest Gap |
| ------- | ------------------------ |
| 5Y      | **2007 → 2005**          |
| 10Y     | **2007 → 2005**          |
| 15Y     | **2007 → 2005**          |

The same ordering also appears in Calgary's cash-outflow sensitivity.

**3. Calgary's wealth and cash-flow timing sensitivities converge as the horizon lengthens.**

| Holding | Net Worth | Cash Outflow |
| ------- | ---------:| ------------:|
| 5Y      | $150K     | $67K         |
| 10Y     | $216K     | $103K        |
| 15Y     | $171K     | $132K        |

By fifteen years, the two ranges are much closer than at five years.

**4. Calgary transitions from timing sensitivity toward portfolio sensitivity by roughly fifteen years.**

At fifteen years:

> Portfolio **$204K** vs. Timing **$171K**

At twenty years, portfolio sensitivity reaches **$352K**.

This is close to Ottawa and substantially above Edmonton, Montreal, and Vancouver.

**5. Calgary's mortgage sensitivity grows steadily and remains visible in both dimensions.**

Net worth:

```text
$19K → $35K → $55K → $82K
```

Cash outflow:

```text
$19K → $36K → $49K → $56K
```

The ranges are similar through the first fifteen years and separate more clearly only at the twenty-year horizon.

### Calgary vs. Edmonton

Both Alberta markets show rising purchase-timing cash sensitivity, persistent **2007 → 2005** timing extremes, and durable entry-cohort effects.

But their long-run sensitivities diverge:

| 20Y       | Calgary   | Edmonton |
| --------- | ---------:| --------:|
| Portfolio | **$352K** | $236K    |
| Mortgage  | **$82K**  | $59K     |

> **Interpretation:** Calgary and Edmonton share a persistent purchase-cohort structure, but Calgary becomes much more sensitive to portfolio and financing assumptions over long horizons.

---

## 5. Directional Effects of Key Modeling Choices

Several modeling choices affect the comparison in different directions rather than systematically favouring either buying or renting.

| Modeling Choice                                                         | Likely Directional Effect                                                                                                                |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Equity series exclude reinvested dividends**                          | Understates renter-investor portfolio growth relative to a total-return benchmark, tending to favour the owner                           |
| **Mortgage-rate series uses a standardized posted / typical benchmark** | May overstate financing costs for borrowers who obtained discounted contract rates, tending to favour the renter-investor                |
| **Illustrative scenarios often use the TSX portfolio**                  | Produces a weaker renter-investor outcome than the S&P 500 alternative in the historical scenarios examined, tending to favour the owner |

These effects operate in different directions. The model should therefore not be interpreted as uniformly conservative toward either strategy.

> **Interpretation:** The most important limitation here is the exclusion of reinvested dividends from the equity series. Because the renter strategy relies explicitly on long-run portfolio compounding, a price-only equity series likely understates the renter-investor outcome relative to a total-return implementation.

---

## 6. Cross-Market Conclusions

The national aggregate and six city markets exhibit materially different sensitivity profiles.

| Market               | Purchase-Timing Pattern                                        | Long-Run Portfolio Sensitivity | Mortgage Sensitivity                                           | Cash-Flow Pattern                                                            | Main Takeaway                                                                                                |
| -------------------- | -------------------------------------------------------------- | ------------------------------:| -------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Canada Aggregate** | High at 5–10Y; measured range falls at 15Y                     | **$455K at 20Y**               | $66K NW / $47K cash                                            | Timing cash sensitivity stays near $84K–$89K                                 | Timing dominates short horizons; portfolio dominates long-run wealth; geography dominates long-run cash flow |
| **Toronto**          | **Highest measured timing sensitivity:** $460K → $490K → $363K | **$539K — highest**            | **$93K NW / $85K cash**                                        | Timing cash effect falls sharply while wealth sensitivity remains very large | Highest measured sensitivity across several drivers; strongly scenario-dependent                             |
| **Vancouver**        | $316K → $255K → **$89K**                                       | **$218K — lowest**             | $75K NW / $37K cash                                            | Timing wealth and cash sensitivities converge by 15Y                         | Strong short-run timing effect but comparatively muted long-run portfolio sensitivity                        |
| **Montreal**         | **Lowest measured timing sensitivity:** $125K → $88K → $75K    | $297K                          | $69K NW / $64K cash                                            | Timing sensitivity is low in both wealth and spending                        | Least entry-dependent city; portfolio gradually replaces timing as the main wealth driver                    |
| **Ottawa**           | **Non-linear:** $292K → $105K → $183K                          | $357K                          | $81K NW / $50K cash                                            | Timing cash sensitivity falls then rebounds                                  | Mixed regime; timing depends heavily on horizon and portfolio becomes important relatively early             |
| **Edmonton**         | $135K → $221K → $187K; persistent                              | **$236K — second-lowest**      | **$59K NW / $28K cash — lowest long-run mortgage sensitivity** | **Timing cash sensitivity rises:** $71K → $99K → $128K                       | Persistent entry-cohort effect and relatively low sensitivity to portfolio and mortgage assumptions          |
| **Calgary**          | $150K → $216K → $171K; persistent                              | **$352K**                      | $82K NW / $56K cash                                            | **Timing cash sensitivity rises:** $67K → $103K → $132K                      | Similar timing structure to Edmonton, but much stronger long-run portfolio and financing sensitivity         |

### Overall cross-market interpretation

The markets do not share one universal rent-versus-buy sensitivity pattern.

- **Toronto** is the most scenario-dependent.
- **Montreal** is the least purchase-timing-sensitive.
- **Vancouver** shows strong short-run timing sensitivity but relatively weak long-run portfolio sensitivity.
- **Ottawa** has a non-linear timing profile.
- **Calgary and Edmonton** share unusually persistent entry-cohort effects, but Calgary becomes much more sensitive to portfolio and financing assumptions.

> **My overall interpretation:** The city effect is not just a level shift in housing cost. Different markets change *which driver matters most*. In some cities the result is primarily an entry-timing question; in others the long-run portfolio or financing assumptions become more important. That is one of the strongest reasons not to rely on a single national rent-versus-buy rule of thumb.

---

## 7. Limitations

### Scope and basis

- Historical results are not forecasts.
- Equity indices reflect price performance and exclude reinvested dividends.
- Housing indices and benchmark prices are market-level series, not individual properties.
- The mortgage-rate series is a standardized benchmark, not a borrower-specific negotiated rate.
- Rate scenarios of ±2 percentage points are sensitivity tests, not predictions.

### Data structure

- Rent data is annual and carried across the months of each calendar year; within-year rent variation is not observed.
- Longer holding periods are available only for earlier purchase years, so holding period and purchase year are structurally correlated.
- Twenty-year purchase-timing results cannot be estimated as a range because only one eligible purchase cohort remains.

### Modeling assumptions

- Property-tax rates, structure ratios, maintenance, insurance, purchase costs, and sale costs are fixed city-level assumptions.
- Rent-control rates, moving probabilities, and move-cost multipliers are stylized.
- Renter moves are probabilistic but reproducible through deterministic seeds; a different seed can produce a different individual move path.
- Investment fee and tax-drag assumptions are portfolio-level rather than household-specific tax calculations.

### Reporting scope

- Down payment is fixed at 20% and renter discipline at 100% in the final report.
- The 10% and 30% down-payment scenarios remain in the simulation database for potential extension but are excluded from comparative conclusions.
- The 100% investment-discipline assumption represents a highly disciplined renter-investor and likely strengthens renter outcomes relative to households that consume part of their monthly savings difference.
- The simulation runs in nominal CAD and converts results to real terms afterward.
- Final comparisons use real net worth, not normalized wealth indexes.
- Non-financial considerations — housing stability, mobility, renovation freedom, school location, and maintenance effort — are outside the financial comparison.

---

## 8. Final Takeaway

The rent-versus-buy question is often framed as **rent versus mortgage payment**. That framing is incomplete in both directions: it treats mortgage principal as if it were consumed, and it treats the renter's alternative capital as if it disappeared.

The comparison that matters is:

| Owner                | Renter-Investor               |
| -------------------- | ----------------------------- |
| Housing equity       | Initial invested capital      |
| Mortgage path        | Monthly cash-flow differences |
| Ownership costs      | Portfolio compounding         |
| Housing appreciation | Fees and tax drag             |

Across the historical scenarios, purchase timing, city, holding period, financing conditions, and the renter's alternative portfolio all materially changed the result.

Their relative importance also changed by market and horizon. Timing can dominate short-term outcomes in one city, while portfolio or financing assumptions become more important over longer horizons or in another market.

> **The financial outcome is conditional. A sound decision requires comparing complete household balance sheets under a specific city, purchase year, holding period, mortgage-rate environment, and alternative investment portfolio — not relying on a national average or a rule of thumb.**

> **My final view:** The strongest contribution of this project is not identifying a universal winner. It is showing *why* the winner changes. The model separates cash flow from wealth, exposes the importance of entry timing and geography, and demonstrates how long-run investment compounding can eventually become more important than financing assumptions. That makes the result more useful as a decision framework than as a simple rent-versus-buy calculator.

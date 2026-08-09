# Key Findings

**Project:** Rent-Invest vs Buy in Canada
**Scope:** Long-run asset performance and household-level rent-versus-buy simulation

---

## 1. How to Read This Report

The analysis combines two connected layers:

| Layer | Question | Basis |
|---|---|---|
| **Market-level** | How have Canadian housing and equity markets performed in real terms? | Inflation-adjusted, rebased index series |
| **Household-level** | Would a specific household have been better off buying, or renting and investing? | Actual dollar prices, rents, mortgage costs, and portfolio returns |

The first layer compares assets. The second models the complete balance sheet of two households starting with identical capital.

### 1.1 Fixed reporting assumptions

```text
Down payment = 20%          Renter investment discipline = 100%
```

Both are held constant so that every difference in outcome is attributable to market conditions rather than to differences in starting capital or savings behaviour.

### 1.2 Sensitivity dimensions

**City · Purchase year · Holding period · Mortgage rate · Renter portfolio**

### 1.3 Primary outcome metric

```text
Final Real Net Worth Gap = Owner Real Net Worth − Renter-Investor Real Net Worth
```

A positive gap means the owner finished ahead; negative means the renter-investor did. All values are inflation-adjusted to the purchasing power of the scenario's own purchase month.

---

## 2. Executive Summary

**There is no universal winner.** The outcome is conditional on when a household bought, where, how long it held, what it paid to borrow, and — most importantly — what the renter did with the capital.

The findings that follow from the analysis:

1. **The S&P 500 delivered the strongest long-run real growth.** 7.1% real CAGR since 1990, against 3.9% for the TSX and 2.0% for Canadian housing.
2. **No Canadian city matched U.S. equities.** Over 2005–2025, Vancouver led Canadian housing at 4.14% real — barely half the S&P 500's 7.22%, and the only city to beat the TSX.
3. **Purchase timing dominated short horizons.** For a five-year hold, outcomes ranged from a large owner advantage to a six-figure owner shortfall depending on entry year alone.
4. **Renter portfolio choice was the single strongest driver at long horizons** — larger in magnitude than the rent-versus-buy decision itself in several scenarios.
5. **Higher mortgage rates barely moved owner net worth but substantially raised renter net worth**, because the cost of higher rates flows through cash flow, and the renter's cash-flow surplus is their investment contribution.
6. **Time amplifies every effect**, widening both the potential advantage and the potential risk of each strategy.
7. **The results are conservatively biased toward owning** (§8), which strengthens the scenarios where the renter still finished ahead.

---

## 3. Long-Run Asset Performance, 1990–2025

Three series rebased to 1990 = 100, all in real Canadian dollars:

| Asset | Real CAGR |
|---|---:|
| **S&P 500 (CAD)** | **7.1%** |
| **TSX Composite** | **3.9%** |
| **Canada Housing** | **2.0%** |

U.S. equities produced substantially stronger long-term real growth. The TSX also outpaced national housing over the full period, though along a more cyclical path. Canadian housing appreciated least in real terms but followed a markedly smoother trajectory — a difference in volatility, not just in level, that matters for households who may need to exit at an unchosen moment.

### 3.1 The winner changes with entry year and horizon

Across entry years from 1990 and horizons from 5 to 35 years, the S&P 500 wins the majority of combinations, particularly at longer horizons and post-2010 entries. Canadian housing wins a concentrated band of windows — largely entries around 2000–2005, before the long domestic run-up.

> **Long-run asset comparisons are path-dependent.** The result depends not only on which asset was held, but on when the position was opened and for how long.

### 3.2 What this layer does not show

This compares **asset prices**, not household outcomes. A homeowner's actual result also depends on mortgage leverage, principal repayment, shelter value, recurring ownership costs, transaction costs, and the return available on the alternative. The household simulation in §5 onward supplies those.

Equity series reflect **price-index performance and exclude reinvested dividends**; housing reflects price appreciation only. Both understate total return, but by different amounts — see §8.

---

## 4. Regional Housing, 2005–2025

| Market | Real CAGR |
|---|---:|
| **S&P 500** | **7.22%** |
| Vancouver Housing | 4.14% |
| **TSX** | **3.84%** |
| Montreal Housing | 3.34% |
| Toronto Housing | 3.17% |
| Canada Housing | 2.87% |
| Ottawa Housing | 2.59% |
| Calgary Housing | 2.48% |
| Edmonton Housing | 2.14% |

Vancouver was the strongest Canadian housing market and the only city to exceed the TSX. The spread between the best and worst city — Vancouver at 4.14% against Edmonton at 2.14% — is nearly two full percentage points of annual real growth, which compounds into a very large difference over twenty years.

**No city matched the S&P 500.** Even Canada's strongest housing market returned barely more than half the real growth of U.S. equities over the same window.

### 4.1 Housing wins were concentrated, not distributed

City-level housing outperformance clusters in specific windows: Edmonton, Ottawa, and Toronto in shorter holds entered around 2005–2008, and Vancouver again in short holds entered around 2017–2018. Across horizons of roughly fifteen years or longer, U.S. equities took almost every combination.

> **Regional dispersion is wide enough that a national housing average does not represent the experience of buyers in any particular city.**

---

## 5. The Household Framework

Both households begin with identical capital and are constrained to the same total monthly housing budget.

### 5.1 Owner

Initial capital goes to `Down Payment + Purchase Cost`. Monthly outflow is `Mortgage Payment + Property Tax + Maintenance + Insurance`.

The model separates the mortgage payment into two economically different components:

| Component | Treatment |
|---|---|
| **Principal** | Not a cost — it converts into home equity. It is a transfer between two of the household's own accounts. |
| **Interest** | An unrecoverable financing cost. |

Principal still appears in **cash outflow**, because the household must fund it each month. It is excluded from **unrecoverable cost**, because it is not consumed.

```text
Owner Net Worth = House Market Value − Mortgage Balance − Estimated Sale Cost
```

Estimated sale cost (6% of current value) places owner wealth on a liquidation-equivalent basis, directly comparable to a portfolio balance.

### 5.2 Renter-Investor

The renter starts with a portfolio equal to `Owner Down Payment + Owner Purchase Cost` — under the fixed 20% assumption, a constant 22% of the purchase price. Monthly outflow is `Actual Rent + Moving Cost`.

```text
Monthly Savings Difference = Owner Total Cash Outflow − Renter Total Cash Outflow
```

Positive differences are invested; negative differences are withdrawn from the portfolio. The withdrawal side matters: when renting costs more than owning, the renter must draw down rather than absorbing the difference for free. Without it, the renter would receive consumption the owner does not.

Renter net worth is the portfolio value after initial capital, monthly contributions and withdrawals, returns, fees, and tax drag.

### 5.3 What makes this comparison fair

Rent is not compared against a mortgage payment. Total household outlay is held equal by construction, and both sides are measured as liquidation-equivalent wealth. The renter is neither assumed to consume the down payment nor given a free pass on months when renting is more expensive.

---

## 6. An Illustrative Scenario

Canada-wide benchmark, purchased 2005, held 20 years, 20% down, Base mortgage rates, **TSX portfolio**:

| Measure | Owner | Renter-Investor |
|---|---:|---:|
| Average monthly cash outflow | **$1,520** | **$903** |
| Cash-outflow CAGR | 1.66% | 3.21% |
| **Final real net worth** | **$372.7K** | **$441.7K** |

The renter finished ahead by roughly **$69K**, despite the owner leading for most of the middle of the period.

**The paths crossed twice.** Housing appreciation and principal repayment carried owner wealth to a peak near $0.5M around the 2022 housing high. The subsequent correction erased that advantage, while the renter's portfolio — funded by an average monthly cash-flow surplus of about $620 — continued compounding.

Note the cash-flow CAGRs: rent grew nearly twice as fast as owner costs (3.21% against 1.66%). But the renter started so much lower that twenty years of faster growth never closed the gap. Rising rent alone did not overturn the renter's cash-flow advantage.

---

## 7. What Moves the Outcome

### 7.1 City

Average owner advantage was largest in **Vancouver** and **Toronto** — the two markets with the strongest price appreciation — and small in the remaining five.

City differences reflect house-price appreciation, rent levels, property-tax rates, structure ratios, and mobility assumptions. Two of these are modelling inputs rather than observed data, which is worth keeping in view: Vancouver combines the lowest property-tax rate (0.3%) and the lowest structure ratio (0.35) of any city in the model, so its carrying costs are the lightest by assumption as well as by market.

> **Location is a scenario variable, not background detail.** The same strategy produces materially different outcomes across Canadian markets.

### 7.2 Purchase year and holding period

Entry timing dominates short horizons. For five-year holds, the owner-renter gap in a single city swung from a substantial owner advantage on mid-2000s and early-2010s entries to a six-figure owner shortfall on entries just before the 2022 peak.

> **Two otherwise identical households reach materially different outcomes purely by entering the market in different years.**

**A structural caution.** Longer holding periods are only observable for earlier purchase years — city-level data begins in 2005, so twenty-year holds exist only for 2005 entries. Holding period and purchase year are therefore correlated in the data. Any apparent "longer horizons favour owning" pattern may partly reflect that long horizons are only measurable for households who bought before the 2006–2021 run-up. Twenty-year results should be read as a single entry cohort, not as evidence about long horizons in general.

### 7.3 Renter portfolio — the strongest long-horizon driver

Edmonton, purchased 2005, held 20 years:

| Outcome | Final Real Net Worth |
|---|---:|
| Owner | **$228K** |
| Renter — TSX | **$193K** |
| Renter — S&P 500 | **$429K** |

**The housing scenario is identical in both renter rows.** Same city, same purchase price, same rent path, same moves. Only the portfolio differs — and it flips the winner from owner to renter, with a swing of $236K.

The effect is starkest in slower-growth markets. In Calgary, where housing returned 2.48% real, an S&P 500 renter beat the owner in every purchase year except 2005.

> **Renting is not a single financial strategy.** Its outcome depends primarily on what the renter does with the capital not committed to a home.

### 7.4 Mortgage rate — the transmission runs through cash flow

Calgary, purchased 2005, held 20 years, TSX portfolio:

| | Base | Base +2pp | Change |
|---|---:|---:|---:|
| Owner final real net worth | $309K | $303K | **−$6K** |
| Renter final real net worth | $295K | $371K | **+$76K** |
| **Gap** | **+$14K** | **−$68K** | **−$82K** |

The result is counter-intuitive and worth stating plainly: **a two-point rate increase barely touched owner net worth, but raised renter net worth by a quarter.**

The reason is structural. Payments are recalculated at each five-year renewal over the *remaining* amortization, so the loan still retires on schedule and the balance at month 240 is nearly unchanged regardless of rate. The cost of higher rates therefore appears almost entirely in **cash flow**, not on the balance sheet — and the owner's extra cash requirement is precisely the renter's extra investment contribution.

Supporting detail from the Montreal 2005 / 20-year case:

| Measure | Base | Base +2pp |
|---|---:|---:|
| Avg. monthly mortgage interest | $416 | $626 |
| Avg. monthly mortgage principal | $446 | $417 |
| Avg. owner monthly cash outflow | $1,370 | $1,550 |

Higher rates shift the payment toward interest and slow principal repayment, but the dominant channel is the extra $180 per month leaving the owner's account — and entering the renter's portfolio.

> **Mortgage rates matter less through what they do to the owner's assets than through what they do to the renter's savings rate.**

### 7.5 Ranking the drivers

Calgary, purchased 2005, at the 20-year horizon:

| Sensitivity driver | Impact on final real net worth gap |
|---|---:|
| **Portfolio choice** (TSX ↔ S&P 500) | **$352.3K** |
| **Mortgage rate** (Base → +2pp) | **$81.5K** |
| **Ratio** | **≈ 4.3×** |

The two effects also behave differently over time. Rate sensitivity grows roughly linearly with holding period; portfolio sensitivity compounds. At five years the two are comparable; by twenty years portfolio choice dominates.

**One caveat on comparability.** The two ranges are not defined symmetrically: the portfolio range spans two real alternatives in both directions, while the rate range is one-sided (Base to +2pp only). A symmetric Lower-to-Higher comparison would produce a wider mortgage-rate sensitivity range than the one-sided Base-to-Higher measure shown here. That range should be calculated directly rather than approximated, because mortgage cash flows and renter portfolio contributions compound non-linearly over time. The conclusion holds either way, but the symmetric comparison is the more defensible one to cite.

> **For a disciplined renter-investor, the alternative investment return becomes the dominant long-horizon driver — larger than financing cost, and in slower markets larger than the buy-versus-rent decision itself.**

---

## 8. Directional Effects of Key Modeling Choices

Several modeling choices affect the comparison in different directions rather than systematically favouring either buying or renting.

| Modeling Choice | Likely Directional Effect |
|---|---|
| **Equity series exclude reinvested dividends** | Understates renter-investor portfolio growth relative to a total-return benchmark, tending to favour the owner |
| **Mortgage-rate series uses a standardized posted/typical benchmark** | May overstate financing costs for borrowers who obtained discounted contract rates, tending to favour the renter-investor |
| **Illustrative scenarios often use the TSX portfolio** | Produces a weaker renter-investor outcome than the S&P 500 alternative in the historical scenarios examined, tending to favour the owner |

Because these effects operate in different directions, the model should not be interpreted as being uniformly conservative toward either strategy. Instead, these assumptions should be treated as **directional modeling limitations** that affect the interpretation of individual scenarios.

---

## 9. Conclusions

**Housing price performance alone does not determine whether buying wins.** Canadian housing appreciated far less than U.S. equities in real terms, yet the household outcome also turns on leverage, principal repayment, transaction costs, recurring expenses, and the renter's alternative return. Several scenarios favour owning despite the appreciation gap.

**Renting and investing must be evaluated as one strategy.** A comparison that assumes the renter consumes the down payment is not a comparison of strategies — it is a comparison between a strategy and a default. In this model the renter invests the owner-equivalent capital, invests monthly surpluses, and draws down when renting costs more.

**Time amplifies every difference.** Portfolio returns, rate differences, price paths, rent growth, and principal repayment all compound. Long horizons raise both the potential advantage and the potential risk of each strategy — they do not reliably favour either.

**Portfolio choice can change the winner.** A scenario in which the owner beats a TSX renter can become a renter win under the S&P 500, with the housing side untouched. This is the model's most distinctive finding, and it is invisible to any analysis that treats "renting and investing" as a single option.

**The answer is conditional.** The outcome depends on the interaction of city, purchase year, holding period, mortgage-rate environment, and renter portfolio. A result favouring buying under one combination reverses under another that is equally historically plausible.

---

## 10. Limitations

**Scope and basis**

- Historical results are not forecasts.
- Equity indices reflect price performance and exclude reinvested dividends.
- Housing indices and benchmark prices are market-level series, not individual properties.
- The mortgage-rate series is a standardized posted benchmark, not a borrower-specific negotiated rate.
- Rate scenarios of ±2 percentage points are sensitivity tests, not predictions.

**Data structure**

- Rent data is annual and is carried across the months of each calendar year; within-year rent variation is not observed.
- Longer holding periods are available only for earlier purchase years, so holding period and purchase year are structurally correlated. Twenty-year results rest on a single entry cohort and carry far less statistical weight than shorter horizons.

**Modelling assumptions**

- Property-tax rates, structure ratios, maintenance, insurance, purchase costs, and sale costs are fixed city-level assumptions.
- Rent-control rates, moving probabilities, and move-cost multipliers are stylized.
- Renter moves are probabilistic but reproducible via deterministic seeds; a different seed produces a different individual move path.
- Investment fee and tax-drag assumptions are portfolio-level, not household-specific tax calculations.

**Reporting scope**

- Down payment is fixed at 20% and renter discipline at 100%. The 10% and 30% down-payment scenarios remain in the database for extension but are excluded from comparative conclusions.
- Full investment discipline is optimistic; renter outcomes should be read as an upper bound on the rent-and-invest strategy.
- The simulation runs in nominal CAD and converts to real terms afterward. Comparisons use real net worth, not normalized indexes.
- Non-financial considerations — housing stability, mobility, renovation freedom, school location, maintenance effort — are outside the wealth comparison entirely.

---

## 11. Final Takeaway

The rent-versus-buy question is usually framed as **rent versus mortgage payment**. That framing is wrong in both directions: it treats principal as a cost when it is savings, and it treats the renter's capital as if it disappears.

The comparison that matters is:

| Owner | Renter-Investor |
|---|---|
| Housing equity | Initial invested capital |
| Mortgage path | Monthly cash-flow differences |
| Ownership costs | Portfolio compounding |
| Housing appreciation | Fees and tax drag |

Across the historical record, market timing, holding period, financing conditions, and above all the renter's alternative portfolio each proved capable of changing the winner.

The useful conclusion is not that buying is better, nor that renting is better. It is:

> **The financial outcome is conditional. A sound decision requires evaluating both complete household balance sheets under the specific city, purchase year, holding period, mortgage-rate environment, and alternative investment portfolio — not a national average or a rule of thumb.**

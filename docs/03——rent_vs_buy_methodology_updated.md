# Methodology: Canada Rent vs Buy Simulation Model (2005–2025)

## 1. Overview

This section presents a historical rent-versus-buy simulation model for Canada from January 2005 to December 2025.

The purpose of this model is to compare the long-term wealth outcomes of:

- Purchasing a home and building home equity
- Renting a comparable property while investing the savings difference in financial markets

The model follows a methodology similar to the framework discussed by Ben Felix, using historical Canadian housing prices, rental costs, mortgage rates, and stock market returns.

The simulation tracks:

- Homeowner net worth over time
- Renter investment portfolio growth over time
- Monthly cash flow differences between renting and owning
- Final wealth outcomes at the end of the simulation period

---

# 2. Model Assumptions

| Category | Variable | Value |
|---|---|---|
| General | Geography | Canada |
|  | Start year | 2005.01 |
|  | End year | 2025.12 |
| Home Purchase | Down payment | 20% |
|  | Amortization | 25 years |
| Mortgage Structure | Mortgage type | 5-year fixed mortgage |
|  | Renewal | Every 5 years |
| Renter Behavior | Renter discipline | 100% |
| Investment Portfolio | Portfolio allocation | 50% TSX + 50% S&P 500 CAD |
| Unrecoverable Costs | Purchase transaction cost | 2% |
|  | Sale transaction cost | 6% |
|  | Maintenance cost | 1/3 × monthly rent |
|  | Property tax | 1% of home value annually |
|  | Structure share | 50% of home value |
|  | Depreciation | 1% annually on structure value only |

---

# 3. Simulation Structure

## 3.1 Homeowner Scenario

In the homeowner scenario, the individual purchases a property in January 2005 using:

- 20% down payment
- 25-year mortgage amortization
- Historical Canadian 5-year fixed mortgage rates

The simulation tracks:

- Mortgage payments
- Mortgage interest
- Principal repayment
- Remaining mortgage balance
- Property appreciation
- Homeowner net worth

Homeowner net worth is calculated as:

```math
Owner\ Net\ Worth = House\ Price - Mortgage\ Balance
```

Mortgage principal repayment is treated as equity accumulation rather than unrecoverable cost.

---

## 3.2 Renter Scenario

In the renter scenario, the individual rents a comparable property and invests the difference between:

- Monthly homeowner unrecoverable costs
- Monthly rent payments

The renter initially invests the capital that would otherwise have been used for:

- Down payment
- Purchase transaction costs

The renter portfolio is invested in:

| Asset Allocation |
|---|
| 50% TSX |
| 50% S&P 500 (CAD-adjusted) |

The model assumes:

- 100% investment discipline
- Monthly reinvestment of savings differences
- Continuous portfolio growth based on historical market returns

---

# 4. Monthly Cash Flow Logic

The simulation compares monthly cash flows between renting and owning.

Monthly savings are calculated as:

```math
Monthly\ Savings = Owner\ Monthly\ Cost - Rent
```

### Interpretation

| Scenario | Outcome |
|---|---|
| Owner cost > Rent | Renter invests the difference |
| Rent > Owner cost | Renter withdraws from portfolio |

This structure allows the simulation to capture changing housing and rental market conditions over time.

---

# 5. Homeowner Unrecoverable Costs

The model distinguishes between:

- Recoverable costs
- Unrecoverable costs

Mortgage principal repayment is not considered a true housing cost because it increases homeowner equity.

The homeowner unrecoverable monthly cost includes:

```math
Owner\ Monthly\ Cost = Mortgage\ Interest + Maintenance + Property\ Tax + Depreciation
```

### Depreciation Modeling

Depreciation is applied only to the estimated structure component of the property value.

The model assumes that land does not depreciate, while the physical housing structure gradually depreciates over time.

For the Canada-wide simulation, the model assumes:

- Land share = 50%
- Structure share = 50%

Monthly depreciation is estimated as:

```math
Depreciation =
House\ Price
\times Structure\ Share
\times Depreciation\ Rate
```

Using the base assumptions:

```math
Depreciation =
House\ Price
\times 50\%
\times 1\%
```

This results in an effective depreciation rate equal to approximately:

```math
0.5\%
\ of\ total\ house\ value\ annually
```

This simplified framework is intended to better reflect housing economics principles, where land typically appreciates while structures physically depreciate over time.

---

### Included Components

| Cost Component | Description |
|---|---|
| Mortgage interest | Interest paid to lender |
| Maintenance | Estimated as 1/3 of monthly rent |
| Property tax | Estimated at 1% annually |
| Depreciation | Estimated at 1% annually on structure value only |

---

# 6. Transaction Costs

The model includes one-time transaction costs associated with home ownership.

| Transaction | Assumption |
|---|---|
| Purchase cost | 2% of home value |
| Sale cost | 6% of home value |

These costs include:

- Legal fees
- Real estate commissions
- Closing costs
- Staging and selling expenses

Purchase costs occur at the beginning of the simulation, while sale costs occur when the property is sold in December 2025.

---

# 7. Mortgage Modeling

The simulation uses a:

| Mortgage Structure |
|---|
| 5-year fixed mortgage |

Mortgage rates are renewed every 5 years using historical Canadian mortgage lending rates.

Mortgage payments are calculated using standard mortgage amortization formulas.

Although the mortgage amortization period is 25 years, the simulation ends in December 2025 when the property is assumed to be sold.

---

# 8. Investment Portfolio Modeling

The renter portfolio grows according to historical stock market returns.

The simulation currently uses:

| Portfolio |
|---|
| 50% TSX |
| 50% S&P 500 CAD |

Monthly portfolio returns are calculated using historical market data and adjusted for investment fees.

---

# 9. Wealth Comparison

At the end of the simulation period, renter and homeowner wealth are compared using the wealth ratio:

```math
Wealth\ Ratio = \frac{Renter\ Net\ Worth}{Owner\ Net\ Worth}
```

### Interpretation

| Wealth Ratio | Interpretation |
|---|---|
| > 1 | Renting outperformed owning |
| < 1 | Owning outperformed renting |
| = 1 | Similar outcomes |

This framework allows direct comparison between long-term home ownership and renter-investor wealth accumulation strategies.

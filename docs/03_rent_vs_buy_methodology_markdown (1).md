# Methodology: Canada Rent vs Buy Simulation Model (2005–2025)

# 1. Overview

This section develops a historical rent-versus-buy simulation framework for Canada covering the period from January 2005 to December 2025.

The objective of the model is to evaluate the long-term financial outcomes associated with two alternative housing strategies:

- purchasing residential property and accumulating housing equity
- renting a comparable property while investing excess cash flow in financial markets

The framework integrates:

- historical Canadian housing price appreciation
- rental market dynamics
- mortgage financing costs
- equity market returns
- behavioral renter assumptions
- housing transaction costs
- homeowner unrecoverable costs

Unlike simplified rent-versus-buy calculators, the model incorporates behavioral and policy-driven renter dynamics, including rent-control mechanisms, tenant mobility, moving costs, and investment portfolio compounding.

The simulation tracks the evolution of:

- homeowner net worth
- renter investment portfolio value
- monthly housing-related cash flows
- cumulative wealth differences over time

This framework is intended to evaluate housing not only as a consumption good, but also as a leveraged financial asset within a long-term household finance context.

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
|  | Home insurance | 0.3% of home value annually |
|  | Structure share | 50% of home value |
|  | Depreciation | 1% annually on structure value only |

---

# 3. Simulation Structure

## 3.1 Homeowner Scenario

In the homeowner scenario, the individual purchases a property in January 2005 using:

- 20% down payment
- 25-year mortgage amortization
- historical Canadian 5-year fixed mortgage rates

The simulation tracks:

- mortgage payments
- mortgage interest
- principal repayment
- remaining mortgage balance
- property appreciation
- homeowner net worth

Homeowner net worth is calculated as:

```math
Owner\ Net\ Worth = House\ Price - Mortgage\ Balance
```

Mortgage principal repayment is treated as equity accumulation rather than unrecoverable housing cost.

---

## 3.2 Renter Scenario

In the renter scenario, the individual rents a comparable property while investing the cash-flow difference between renting and homeownership.

The renter initially invests the capital that would otherwise have been allocated toward:

- the home down payment
- purchase-related transaction costs

The renter portfolio is invested in one of several portfolio configurations, including:

| Portfolio Allocation |
|---|
| TSX-only |
| S&P 500 (CAD-adjusted) |
| Balanced portfolio |

Unlike simplified models that assume renters always pay market rent, this framework incorporates city-specific renter policy assumptions, including:

- rent-control mechanisms
- renter mobility probabilities
- market rent resets after relocation
- moving-related transaction costs

For rent-controlled units, rent growth follows a capped annual increase assumption. However, if the renter relocates, rent is reset to prevailing market levels.

This structure captures the economic value of long-term tenancy in regulated rental markets such as Toronto and Vancouver.

The model also allows renter investment contributions to become negative when renter housing costs exceed homeowner cash outflows, thereby permitting portfolio withdrawals during periods of elevated rental costs or relocation expenses.

This approach creates a more realistic representation of renter household financial dynamics over time.

---

# 4. Monthly Cash Flow Logic

The simulation compares monthly cash flows between renting and owning.

Monthly renter savings are calculated as:

```math
Monthly\ Savings = Owner\ Cash\ Outflow - Renter\ Cash\ Outflow
```

Where renter cash outflow includes:

```math
Renter\ Cash\ Outflow = Actual\ Rent + Moving\ Costs
```

### Interpretation

| Scenario | Outcome |
|---|---|
| Owner cost > Renter cost | Renter invests the difference |
| Renter cost > Owner cost | Renter withdraws from investment portfolio |

This structure allows the simulation to capture changing housing affordability conditions over time.

---

# 5. Homeowner Unrecoverable Costs

The model distinguishes between:

- recoverable costs
- unrecoverable costs

Mortgage principal repayment is not considered a true housing cost because it increases homeowner equity.

The homeowner unrecoverable monthly cost includes:

```math
Owner\ Monthly\ Cost = Mortgage\ Interest + Maintenance + Property\ Tax + Home\ Insurance + Depreciation
```

## 5.1 Depreciation Modeling

Depreciation is applied only to the estimated structure component of the property value.

The model assumes that land does not depreciate, while the physical housing structure gradually depreciates over time.

For the Canada-wide simulation, the model assumes:

- Land share = 50%
- Structure share = 50%

Monthly depreciation is estimated as:

```math
Depreciation = House\ Price \times Structure\ Share \times Depreciation\ Rate
```

Using the base assumptions:

```math
Depreciation = House\ Price \times 50\% \times 1\%
```

This results in an effective depreciation rate equal to approximately:

```math
0.5\%\ of\ total\ house\ value\ annually
```

This simplified framework is intended to better reflect housing economics principles, where land typically appreciates while structures physically depreciate over time.

### Included Components

| Cost Component | Description |
|---|---|
| Mortgage interest | Interest paid to lender |
| Maintenance | Estimated as 1/3 of monthly rent |
| Property tax | Estimated at 1% annually |
| Home insurance | Estimated at 0.3% annually |
| Depreciation | Estimated at 1% annually on structure value only |

---

# 6. Renter Mobility and Rent-Control Simulation

## 6.1 City-Specific Rental Policy Assumptions

A separate renter policy assumption table was created for each city.

The table includes:

| Variable | Description |
|---|---|
| `rent_growth_mode` | Controlled or market-based rent growth |
| `rent_control_rate` | Annual rent increase cap for existing tenants |
| `annual_move_probability` | Probability that a renter moves within a year |
| `move_cost_multiplier` | Moving cost expressed as a multiple of monthly rent |

These assumptions are designed to reflect differences in Canadian provincial rental systems.

For example:

- Ontario and British Columbia contain stronger rent-control systems
- Alberta uses a more market-driven rental framework with no formal rent cap
- Montreal exhibits relatively stable long-term rent growth

---

## 6.2 Rent-Control Logic

The model distinguishes between:

| Situation | Rent Behavior |
|---|---|
| Existing tenant remains in same unit | Rent increases gradually according to rent-control policy |
| Tenant moves to new unit | Rent resets to current market rent |

For rent-controlled units, monthly rent evolves according to:

```math
Rent_t = Rent_{t-1} \times \left(1 + \frac{Rent\ Control\ Rate}{12}\right)
```

If a renter moves, the model assumes:

```math
New\ Rent = Current\ Market\ Rent
```

This framework captures the economic value of long-term tenancy in rent-controlled markets such as Toronto and Vancouver.

---

## 6.3 Renter Mobility Simulation

Instead of assuming deterministic relocation schedules, renter movement is modeled probabilistically.

Each city is assigned an annual moving probability, which is converted into a monthly probability:

```math
Monthly\ Move\ Probability = \frac{Annual\ Move\ Probability}{12}
```

At each monthly period, a stochastic simulation determines whether the renter moves to a new unit.

This approach allows the model to capture:

- housing instability
- tenant lock-in effects
- market rent exposure
- city-level differences in renter mobility

---

## 6.4 Moving Costs

When a renter relocates, the model applies a one-time moving cost.

Rather than using a fixed dollar value, moving costs are modeled as a multiple of monthly rent:

```math
Move\ Cost = Monthly\ Rent \times Move\ Cost\ Multiplier
```

This allows moving costs to scale naturally with:

- local housing affordability
- city-specific rent levels
- long-term rent inflation

Higher-cost metropolitan areas such as Toronto and Vancouver therefore generate larger moving-related financial shocks.

---

# 7. Transaction Costs

The model includes one-time transaction costs associated with home ownership.

| Transaction | Assumption |
|---|---|
| Purchase cost | 2% of home value |
| Sale cost | 6% of home value |

These costs include:

- legal fees
- real estate commissions
- closing costs
- staging and selling expenses

Purchase costs occur at the beginning of the simulation, while sale costs occur when the property is sold in December 2025.

---

# 8. Mortgage Modeling

The simulation uses a:

| Mortgage Structure |
|---|
| 5-year fixed mortgage |

Mortgage rates are renewed every 5 years using historical Canadian mortgage lending rates.

Mortgage payments are calculated using standard mortgage amortization formulas.

Although the mortgage amortization period is 25 years, the simulation ends in December 2025 when the property is assumed to be sold.

---

# 9. Investment Portfolio Modeling

The renter portfolio grows according to historical stock market returns.

The simulation currently uses:

| Portfolio |
|---|
| TSX-only |
| S&P 500 CAD |
| Balanced portfolio |

Net portfolio returns are calculated after:

- investment management fees
- tax drag assumptions

Monthly net portfolio return is defined as:

```math
Net\ Return = Gross\ Return - Investment\ Fee - Tax\ Drag
```

This allows the model to better approximate real-world investment performance from a Canadian investor perspective.

---

# 10. Wealth Comparison

At the end of the simulation period, renter and homeowner wealth are compared using the wealth ratio:

```math
Wealth\ Ratio = \frac{Renter\ Net\ Worth}{Owner\ Net\ Worth}
```

## Interpretation

| Wealth Ratio | Interpretation |
|---|---|
| > 1 | Renting outperformed owning |
| < 1 | Owning outperformed renting |
| = 1 | Similar outcomes |

This simulation framework demonstrates that long-term rent-versus-buy outcomes depend not only on housing appreciation and equity market performance, but also on behavioral, policy, and cash-flow dynamics.

Factors such as rent control, tenant mobility, transaction costs, leverage, and investment discipline materially affect long-term household wealth accumulation.

By incorporating these mechanisms, the model aims to provide a more realistic representation of Canadian housing and household finance dynamics than traditional rent-versus-buy calculators.


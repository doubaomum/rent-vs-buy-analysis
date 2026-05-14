import pandas as pd
from pathlib import Path

# ==================================================
# USER SETTINGS
# ==================================================

OWNER_COST_PATH = Path("data/processed/final/basic_model_owner_cost_schedule.csv")

SP500_PATH = Path("data/processed/stock/sp500.csv")
TSX_PATH = Path("data/processed/stock/tsx.csv")

OUTPUT_PATH = Path("data/processed/final/basic_model_renter_portfolio_schedule.csv")

# Final basic model setting
PORTFOLIO_SCENARIO = "tsx_only"   # "tsx_only", "sp500_only", "balanced"

RENTER_DISCIPLINE = 1.00

INVESTMENT_FEE = 0.002
TAX_DRAG = 0.001

MONTHLY_INVESTMENT_COST = (INVESTMENT_FEE + TAX_DRAG) / 12


# ==================================================
# LOAD OWNER COST DATA
# ==================================================

def load_owner_cost(path):
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ==================================================
# LOAD STOCK DATA
# ==================================================

def load_stock_data(sp500_path, tsx_path):
    """
    Load S&P 500 and TSX data.

    Expected columns:

    sp500.csv:
    - date
    - sp500_price

    tsx.csv:
    - date
    - tsx_cad
    """

    sp500 = pd.read_csv(sp500_path)
    tsx = pd.read_csv(tsx_path)

    sp500["date"] = pd.to_datetime(sp500["date"])
    tsx["date"] = pd.to_datetime(tsx["date"])

    sp500["sp500_price"] = pd.to_numeric(
        sp500["sp500_price"],
        errors="coerce"
    )

    tsx["tsx_cad"] = pd.to_numeric(
        tsx["tsx_cad"],
        errors="coerce"
    )

    sp500 = sp500[["date", "sp500_price"]].dropna()
    tsx = tsx[["date", "tsx_cad"]].dropna()

    sp500 = sp500.sort_values("date")
    tsx = tsx.sort_values("date")

    stock = sp500.merge(
        tsx,
        on="date",
        how="inner"
    )

    stock["sp500_return"] = stock["sp500_price"].pct_change()
    stock["tsx_return"] = stock["tsx_cad"].pct_change()

    if PORTFOLIO_SCENARIO == "sp500_only":
        stock["portfolio_return"] = stock["sp500_return"]

    elif PORTFOLIO_SCENARIO == "tsx_only":
        stock["portfolio_return"] = stock["tsx_return"]

    elif PORTFOLIO_SCENARIO == "balanced":
        stock["portfolio_return"] = (
            0.50 * stock["sp500_return"]
            + 0.50 * stock["tsx_return"]
        )

    else:
        raise ValueError(
            "PORTFOLIO_SCENARIO must be "
            "'tsx_only', 'sp500_only', or 'balanced'"
        )

    stock["portfolio_return_net"] = (
        stock["portfolio_return"] - MONTHLY_INVESTMENT_COST
    )

    stock = stock[["date", "portfolio_return", "portfolio_return_net"]]
    stock = stock.dropna()

    return stock


# ==================================================
# GENERATE RENTER PORTFOLIO
# ==================================================

def generate_renter_portfolio(owner_df, stock_df):
    df = owner_df.merge(
        stock_df,
        on="date",
        how="left"
    )

    df["portfolio_return"] = df["portfolio_return"].fillna(0)
    df["portfolio_return_net"] = df["portfolio_return_net"].fillna(0)

    # Owner total monthly cash outflow
    # Mortgage principal is not an economic cost,
    # but it is still cash flow that the renter can invest instead.
    df["owner_total_cash_outflow"] = (
        df["mortgage_payment"]
        + df["maintenance_cost"]
        + df["property_tax"]
        + df["depreciation_cost"]
    )

    # Renter pays rent.
    # If owner monthly cash outflow is higher than rent,
    # renter invests the difference.
    df["monthly_savings_difference"] = (
        df["owner_total_cash_outflow"] - df["rent"]
    )

    df["renter_monthly_investment"] = (
        df["monthly_savings_difference"].clip(lower=0)
        * RENTER_DISCIPLINE
    )

    # Renter starts with cash that the buyer used for:
    # down payment + purchase transaction cost
    initial_cash = (
        df.loc[df.index[0], "down_payment"]
        + df.loc[df.index[0], "purchase_cost"]
    )

    portfolio_value = initial_cash
    portfolio_values = []

    for _, row in df.iterrows():

        portfolio_value = portfolio_value * (
            1 + row["portfolio_return_net"]
        )

        portfolio_value = (
            portfolio_value + row["renter_monthly_investment"]
        )

        portfolio_value = max(portfolio_value, 0)

        portfolio_values.append(portfolio_value)

    df["renter_portfolio_value"] = portfolio_values
    df["renter_networth"] = df["renter_portfolio_value"]

    df["wealth_difference"] = (
        df["renter_networth"] - df["owner_networth"]
    )

    df["wealth_ratio"] = (
        df["renter_networth"] / df["owner_networth"]
    )

    df["portfolio_scenario"] = PORTFOLIO_SCENARIO
    df["renter_discipline"] = RENTER_DISCIPLINE
    df["investment_fee"] = INVESTMENT_FEE
    df["tax_drag"] = TAX_DRAG

    return df


# ==================================================
# RUN SCRIPT
# ==================================================

if __name__ == "__main__":

    owner_df = load_owner_cost(OWNER_COST_PATH)

    stock_df = load_stock_data(
        sp500_path=SP500_PATH,
        tsx_path=TSX_PATH
    )

    all_results = []

    for scenario_id, group in owner_df.groupby("scenario_id"):

        renter_group = generate_renter_portfolio(
            owner_df=group,
            stock_df=stock_df
        )

        all_results.append(renter_group)

    renter_df = pd.concat(all_results, ignore_index=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    renter_df.to_csv(OUTPUT_PATH, index=False)

    print(renter_df.head())
    print(renter_df.tail())
    print("\nSaved to:", OUTPUT_PATH)
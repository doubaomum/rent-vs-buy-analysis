import pandas as pd
from pathlib import Path

# ==================================================
# USER SETTINGS
# ==================================================

OWNER_COST_PATH = Path("data/processed/final/5year_mor_owner_cost_schedule.csv")

SP500_PATH = Path("data/processed/stock/sp500.csv")
TSX_PATH = Path("data/processed/stock/tsx.csv")

OUTPUT_PATH = Path("data/processed/final/renter_portfolio_schedule.csv")

# Choose portfolio scenario:
# "sp500_only"
# "tsx_only"
# "balanced"
PORTFOLIO_SCENARIO = "balanced"

RENTER_DISCIPLINE = 1.00

ANNUAL_FEE = 0.0025
MONTHLY_FEE = ANNUAL_FEE / 12


# ==================================================
# LOAD OWNER COST DATA
# ==================================================

def load_owner_cost(path):
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
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
            "'sp500_only', 'tsx_only', or 'balanced'"
        )

    stock["portfolio_return_net"] = (
        stock["portfolio_return"] - MONTHLY_FEE
    )

    return stock[["date", "portfolio_return_net"]]


# ==================================================
# GENERATE RENTER PORTFOLIO
# ==================================================

def generate_renter_portfolio(owner_df, stock_df):
    df = owner_df.merge(
        stock_df,
        on="date",
        how="left"
    )

    df["portfolio_return_net"] = df["portfolio_return_net"].fillna(0)

    # Renter pays rent.
    # If owner cost is higher than rent, renter invests the difference.
    df["monthly_savings_difference"] = (
        df["owner_monthly_cost"] - df["rent"]
    )

    df["renter_monthly_investment"] = (
        df["monthly_savings_difference"] * RENTER_DISCIPLINE
    )

    # Renter starts with money that owner used for down payment + purchase cost
    initial_cash = (
        df.loc[df.index[0], "down_payment"]
        + df.loc[df.index[0], "purchase_cost"]
    )

    portfolio_value = initial_cash
    portfolio_values = []

    for _, row in df.iterrows():

        # Portfolio grows first
        portfolio_value = portfolio_value * (
            1 + row["portfolio_return_net"]
        )

        # Then renter invests or withdraws the monthly difference
        portfolio_value = portfolio_value + row["renter_monthly_investment"]

        portfolio_value = max(portfolio_value, 0)

        portfolio_values.append(portfolio_value)

    df["renter_portfolio_value"] = portfolio_values
    df["renter_networth"] = df["renter_portfolio_value"]

    df["wealth_ratio"] = (
        df["renter_networth"] / df["owner_networth"]
    )

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

    renter_df = generate_renter_portfolio(
        owner_df=owner_df,
        stock_df=stock_df
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    renter_df.to_csv(OUTPUT_PATH, index=False)

    print(renter_df.head())
    print(renter_df.tail())
    print("\nSaved to:", OUTPUT_PATH)
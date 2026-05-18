import pandas as pd
from pathlib import Path
import numpy as np

# ==================================================
# USER SETTINGS
# ==================================================

OWNER_COST_PATH = Path("data/processed/final/basic_model_owner_cost_schedule.csv")

SP500_PATH = Path("data/processed/stock/sp500.csv")
TSX_PATH = Path("data/processed/stock/tsx.csv")

RENTER_POLICY_PATH = Path("data/assumptions/renter_policy_assumptions.csv")

OUTPUT_PATH = Path("data/processed/final/basic_model_renter_portfolio_schedule.csv")

INVESTMENT_ASSUMPTIONS_PATH = Path(
    "data/assumptions/investment_assumptions.csv"
)

# Final basic model setting

RENTER_DISCIPLINE = 1.00


# ==================================================
# LOAD OWNER COST DATA
# ==================================================

def load_owner_cost(path):
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df

def load_renter_policy(path):
    df = pd.read_csv(path)

    df["rent_control_rate"] = pd.to_numeric(
        df["rent_control_rate"],
        errors="coerce"
    )

    df["annual_move_probability"] = pd.to_numeric(
        df["annual_move_probability"],
        errors="coerce"
    )

    df["move_cost_multiplier"] = pd.to_numeric(
        df["move_cost_multiplier"],
        errors="coerce"
    )

    return df
# ==================================================
# LOAD STOCK DATA
# ==================================================

def load_stock_data(sp500_path, tsx_path):
    """
    Load S&P 500 and TSX data.

    This function only calculates raw asset returns.
    Portfolio selection happens later inside generate_renter_portfolio().
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

    stock = stock[["date", "sp500_return", "tsx_return"]]
    stock = stock.dropna()

    return stock

def load_investment_assumptions(path):

    df = pd.read_csv(path)

    return df
# ==================================================
# GENERATE RENTER PORTFOLIO
# ==================================================

def generate_renter_portfolio(
    owner_df,
    stock_df,
    renter_policy_df,
    portfolio_scenario,
    investment_fee,
    tax_drag
):
    df = owner_df.merge(
        stock_df,
        on="date",
        how="left"
    )

    df = df.merge(
        renter_policy_df,
        on="city",
        how="left"
    )

    df["sp500_return"] = df["sp500_return"].fillna(0)
    df["tsx_return"] = df["tsx_return"].fillna(0)

    monthly_investment_cost = (investment_fee + tax_drag) / 12

    if portfolio_scenario == "sp500_only":
        df["portfolio_return"] = df["sp500_return"]

    elif portfolio_scenario == "tsx_only":
        df["portfolio_return"] = df["tsx_return"]

    elif portfolio_scenario == "balanced":
        df["portfolio_return"] = (
            0.50 * df["sp500_return"]
            + 0.50 * df["tsx_return"]
        )

    else:
        raise ValueError(
            "portfolio_scenario must be 'tsx_only', 'sp500_only', or 'balanced'"
        )

    df["portfolio_return_net"] = (
        df["portfolio_return"] - monthly_investment_cost
    )

    df["monthly_investment_cost"] = monthly_investment_cost

    # Owner total monthly cash outflow
    df["owner_total_cash_outflow"] = (
        df["mortgage_payment"]
        + df["maintenance_cost"]
        + df["property_tax"]
        + df["depreciation_cost"]
    )

    # ==============================
    # Renter rent-control logic
    # ==============================

    df = df.sort_values(["city", "date"]).reset_index(drop=True)

    df["month_number"] = df.groupby("city").cumcount()

    # Stochastic assumption:
    # renter may move each month based on city-level annual move probability
    np.random.seed(42)

    # convert annual probability to monthly probability
    df["monthly_move_probability"] = (
        df["annual_move_probability"] / 12
    )

    # random move simulation
    df["random_move"] = np.random.rand(len(df))

    df["renter_moves"] = (
        df["random_move"]
        < df["monthly_move_probability"]
    )
    df.loc[df["month_number"] == 0, "renter_moves"] = False

    actual_rents = []

    for city, city_df in df.groupby("city", sort=False):
        previous_rent = city_df.iloc[0]["rent"]

        for i, row in city_df.iterrows():
            market_rent = row["rent"]

            if row["month_number"] == 0:
                actual_rent = market_rent

            elif row["rent_growth_mode"] == "market":
                actual_rent = market_rent

            elif row["renter_moves"]:
                actual_rent = market_rent

            else:
                monthly_cap = row["rent_control_rate"] / 12
                actual_rent = previous_rent * (1 + monthly_cap)

            actual_rents.append((i, actual_rent))
            previous_rent = actual_rent

    actual_rent_series = pd.Series(
        data=[x[1] for x in actual_rents],
        index=[x[0] for x in actual_rents]
    )

    df["actual_renter_rent"] = actual_rent_series.sort_index()

    df["move_cost"] = 0.0

    df.loc[df["renter_moves"], "move_cost"] = (
        df.loc[df["renter_moves"], "actual_renter_rent"]
        * df.loc[df["renter_moves"], "move_cost_multiplier"]
    )

    df["renter_total_cash_outflow"] = (
        df["actual_renter_rent"] + df["move_cost"]
    )

    # If owner cash outflow is higher than renter cost,
    # renter invests the difference.
    df["monthly_savings_difference"] = (
        df["owner_total_cash_outflow"]
        - df["renter_total_cash_outflow"]
    )

    df["renter_monthly_investment"] = (
        df["monthly_savings_difference"]
        * RENTER_DISCIPLINE
    )

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

    df["portfolio_name"] = portfolio_scenario
    df["investment_fee"] = investment_fee
    df["tax_drag"] = tax_drag

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

    renter_policy_df = load_renter_policy(
        RENTER_POLICY_PATH
    )

    investment_df = load_investment_assumptions(
        INVESTMENT_ASSUMPTIONS_PATH
    )

    all_results = []

    for scenario_id, group in owner_df.groupby("scenario_id"):

        city = group["city"].iloc[0]
        portfolio_scenario = group["portfolio_name"].iloc[0]

        investment_row = investment_df[
            investment_df["portfolio_name"] == portfolio_scenario
        ].iloc[0]

        investment_fee = investment_row["investment_fee"]
        tax_drag = investment_row["tax_drag"]

        print("\n=== Running Scenario ===")
        print("Scenario ID:", scenario_id)
        print("City:", city)
        print("Portfolio:", portfolio_scenario)

        renter_group = generate_renter_portfolio(
            owner_df=group,
            stock_df=stock_df,
            renter_policy_df=renter_policy_df,
            portfolio_scenario=portfolio_scenario,
            investment_fee=investment_fee,
            tax_drag=tax_drag
        )

        all_results.append(renter_group)

    renter_df = pd.concat(all_results, ignore_index=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    renter_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(renter_df.head())
    print(renter_df.tail())
    print("\nSaved to:", OUTPUT_PATH)
    print("Final shape:", renter_df.shape)
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
INVESTMENT_ASSUMPTIONS_PATH = Path("data/assumptions/investment_assumptions.csv")

OUTPUT_PATH = Path("data/processed/final/basic_model_renter_portfolio_schedule.csv")

DEFAULT_RENTER_DISCIPLINE = 1.00
RANDOM_SEED = 42


# ==================================================
# LOAD OWNER COST DATA
# ==================================================

def load_owner_cost(path):
    """
    Load owner schedule with scenario metadata.

    Expected important columns:
    - scenario_id
    - city
    - portfolio_name
    - start_date
    - end_date
    - holding_years
    - renter_discipline
    - date
    """

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(df["date"])

    if "start_date" in df.columns:
        df["start_date"] = pd.to_datetime(df["start_date"])

    if "end_date" in df.columns:
        df["end_date"] = pd.to_datetime(df["end_date"])

    df = df.sort_values(
        ["scenario_id", "date"]
    ).reset_index(drop=True)

    return df


# ==================================================
# LOAD RENTER POLICY DATA
# ==================================================

def load_renter_policy(path):
    """
    Load renter policy assumptions.

    Expected columns:
    - city
    - rent_growth_mode
    - rent_control_rate
    - annual_move_probability
    - move_cost_multiplier
    """

    df = pd.read_csv(path)

    numeric_cols = [
        "rent_control_rate",
        "annual_move_probability",
        "move_cost_multiplier"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
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


# ==================================================
# LOAD INVESTMENT ASSUMPTIONS
# ==================================================

def load_investment_assumptions(path):
    """
    Load investment assumptions.

    Expected columns:
    - portfolio_name
    - investment_fee
    - tax_drag
    """

    df = pd.read_csv(path)

    df["portfolio_name"] = (
        df["portfolio_name"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["investment_fee"] = pd.to_numeric(
        df["investment_fee"],
        errors="coerce"
    )

    df["tax_drag"] = pd.to_numeric(
        df["tax_drag"],
        errors="coerce"
    )

    return df


# ==================================================
# PORTFOLIO RETURN SELECTION
# ==================================================

def add_portfolio_return(
    df,
    portfolio_scenario,
    investment_fee,
    tax_drag
):
    """
    Add selected portfolio return and net return.

    Supported portfolio_scenario:
    - tsx_only
    - sp500_only
    - balanced
    """

    portfolio_scenario = str(portfolio_scenario).strip().lower()

    monthly_investment_cost = (
        investment_fee + tax_drag
    ) / 12

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
            "portfolio_scenario must be 'tsx_only', 'sp500_only', or 'balanced'. "
            f"Current value: {portfolio_scenario}"
        )

    df["portfolio_return_net"] = (
        df["portfolio_return"] - monthly_investment_cost
    )

    df["monthly_investment_cost"] = monthly_investment_cost
    df["investment_fee"] = investment_fee
    df["tax_drag"] = tax_drag

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
    """
    Generate renter-investor portfolio for one scenario_id.

    Scenario logic:
    - portfolio_scenario comes from owner_df["portfolio_name"]
    - renter_discipline comes from owner_df["renter_discipline"]
    - holding period comes from the owner schedule date range
    """

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

    df = add_portfolio_return(
        df=df,
        portfolio_scenario=portfolio_scenario,
        investment_fee=investment_fee,
        tax_drag=tax_drag
    )

    if "renter_discipline" in df.columns:
        renter_discipline = df["renter_discipline"].iloc[0]
    else:
        renter_discipline = DEFAULT_RENTER_DISCIPLINE

    if pd.isna(renter_discipline):
        renter_discipline = DEFAULT_RENTER_DISCIPLINE

    renter_discipline = float(renter_discipline)

    # Owner total monthly cash outflow.
    # Mortgage principal is not an economic cost,
    # but it is still a real monthly cash outflow.
    required_owner_cashflow_cols = [
        "mortgage_payment",
        "maintenance_cost",
        "property_tax",
        "depreciation_cost",
        "home_insurance_cost"
    ]

    for col in required_owner_cashflow_cols:
        if col not in df.columns:
            df[col] = 0.0

    df["owner_total_cash_outflow"] = (
        df["mortgage_payment"]
        + df["maintenance_cost"]
        + df["property_tax"]
        + df["depreciation_cost"]
        + df["home_insurance_cost"]
    )

    # ==============================
    # Renter rent-control logic
    # ==============================

    df = df.sort_values(["scenario_id", "city", "date"]).reset_index(drop=True)

    df["month_number"] = df.groupby(["scenario_id", "city"]).cumcount()

    # Convert annual moving probability to monthly probability.
    df["monthly_move_probability"] = (
        df["annual_move_probability"] / 12
    )

    # Random move simulation.
    # Seed is scenario-specific so results are reproducible but not identical across scenarios.
    scenario_id = df["scenario_id"].iloc[0]
    rng = np.random.default_rng(RANDOM_SEED + int(scenario_id))

    df["random_move"] = rng.random(len(df))

    df["renter_moves"] = (
        df["random_move"] < df["monthly_move_probability"]
    )

    df.loc[df["month_number"] == 0, "renter_moves"] = False

    actual_rents = []

    # Group by scenario and city to avoid rent carry-over across scenarios.
    for _, group_df in df.groupby(["scenario_id", "city"], sort=False):

        previous_rent = group_df.iloc[0]["rent"]

        for i, row in group_df.iterrows():

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
        df["actual_renter_rent"]
        + df["move_cost"]
    )

    # If owner cash outflow is higher than renter cost,
    # renter invests the difference.
    # If renter cost is higher, the extra cash outflow is deducted from portfolio.
    df["monthly_savings_difference"] = (
        df["owner_total_cash_outflow"]
        - df["renter_total_cash_outflow"]
    )

    df["renter_monthly_investment_before_discipline"] = (
        df["monthly_savings_difference"].clip(lower=0)
    )

    df["renter_monthly_investment"] = (
        df["renter_monthly_investment_before_discipline"]
        * renter_discipline
    )

    df["renter_extra_cash_outflow"] = (
        (-df["monthly_savings_difference"]).clip(lower=0)
    )

    initial_cash = (
        df.iloc[0]["down_payment"]
        + df.iloc[0]["purchase_cost"]
    )

    portfolio_value = initial_cash
    portfolio_values = []

    for _, row in df.iterrows():

        portfolio_value = portfolio_value * (
            1 + row["portfolio_return_net"]
        )

        portfolio_value = (
            portfolio_value
            + row["renter_monthly_investment"]
            - row["renter_extra_cash_outflow"]
        )

        portfolio_value = max(portfolio_value, 0)

        portfolio_values.append(portfolio_value)

    df["renter_portfolio_value"] = portfolio_values
    df["renter_networth"] = df["renter_portfolio_value"]

    df["wealth_difference"] = (
        df["renter_networth"]
        - df["owner_networth_after_sale"]
    )

    df["wealth_ratio"] = (
        df["renter_networth"]
        / df["owner_networth_after_sale"]
    )

    df["portfolio_name"] = portfolio_scenario
    df["renter_discipline"] = renter_discipline

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
        portfolio_scenario = (
            str(group["portfolio_name"].iloc[0])
            .strip()
            .lower()
        )

        investment_row = investment_df[
            investment_df["portfolio_name"] == portfolio_scenario
        ]

        if investment_row.empty:
            raise ValueError(
                f"No investment assumptions found for portfolio: {portfolio_scenario}"
            )

        investment_fee = investment_row["investment_fee"].iloc[0]
        tax_drag = investment_row["tax_drag"].iloc[0]

        renter_discipline = (
            group["renter_discipline"].iloc[0]
            if "renter_discipline" in group.columns
            else DEFAULT_RENTER_DISCIPLINE
        )

        print("\n=== Running Renter Scenario ===")
        print("Scenario ID:", scenario_id)
        print("City:", city)
        print("Portfolio:", portfolio_scenario)
        print("Renter Discipline:", renter_discipline)

        renter_group = generate_renter_portfolio(
            owner_df=group,
            stock_df=stock_df,
            renter_policy_df=renter_policy_df,
            portfolio_scenario=portfolio_scenario,
            investment_fee=investment_fee,
            tax_drag=tax_drag
        )

        all_results.append(renter_group)

    if not all_results:
        raise ValueError("No renter scenarios were generated.")

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

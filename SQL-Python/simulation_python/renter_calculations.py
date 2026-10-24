"""Original renter recursion separated from database operations.

calculate_one_renter_scenario is copied unchanged from the supplied original.
"""
import numpy as np
import pandas as pd

RESULT_COLUMNS = ['renter_scenario_id', 'random_move', 'renter_moves', 'actual_renter_rent', 'move_cost', 'renter_total_cash_outflow', 'monthly_savings_difference', 'renter_monthly_investment', 'sp500_return', 'tsx_return', 'portfolio_return', 'portfolio_return_net', 'renter_portfolio_value', 'renter_net_worth', 'owner_net_worth_real', 'renter_net_worth_real', 'owner_net_worth_index', 'renter_net_worth_index']

def calculate_one_renter_scenario(
    scenario: pd.DataFrame,
) -> pd.DataFrame:

    scenario = (
        scenario
        .sort_values("month_number")
        .copy()
    )

    owner_scenario_id = int(
        scenario.iloc[0]["owner_scenario_id"]
    )

    portfolio_name = str(
        scenario.iloc[0]["portfolio_name"]
    )

    renter_discipline = float(
        scenario.iloc[0]["renter_discipline"]
    )

    # -----------------------------------------------------
    # Validate starting month
    # -----------------------------------------------------
    if int(scenario.iloc[0]["month_number"]) != 0:
        raise ValueError(
            f"Owner scenario {owner_scenario_id}, "
            f"portfolio {portfolio_name}, "
            f"discipline {renter_discipline} "
            "does not begin with month 0."
        )

    # -----------------------------------------------------
    # Validate market rent
    # -----------------------------------------------------
    if scenario["market_rent"].isna().any():
        missing_rows = scenario.loc[
            scenario["market_rent"].isna(),
            [
                "date_period",
                "city",
            ],
        ]

        raise ValueError(
            "Missing market rent for renter scenario:\n"
            f"{missing_rows.head()}"
        )

    # -----------------------------------------------------
    # Select portfolio return
    # -----------------------------------------------------
    if portfolio_name == "sp500_only":
        scenario["portfolio_return"] = (
            scenario["sp500_return"]
        )

    elif portfolio_name == "tsx_only":
        scenario["portfolio_return"] = (
            scenario["tsx_return"]
        )

    else:
        raise ValueError(
            f"Unsupported portfolio_name: "
            f"{portfolio_name}"
        )

    scenario["portfolio_return_net"] = (
        scenario["portfolio_return"]
        - scenario["monthly_investment_cost"]
    )

    # Month 0 is the starting month.
    # Do not apply a stock return immediately.
    scenario.loc[
        scenario["month_number"].eq(0),
        [
            "sp500_return",
            "tsx_return",
            "portfolio_return",
            "portfolio_return_net",
        ],
    ] = 0.0

    # -----------------------------------------------------
    # Generate deterministic renter moves
    # -----------------------------------------------------
    MOVE_RANDOM_SEED = 42

    random_generator = np.random.default_rng(
        MOVE_RANDOM_SEED
    )

    scenario["random_move"] = (
        random_generator.random(
            len(scenario)
        )
    )

    scenario["renter_moves"] = (
        scenario["random_move"]
        < scenario["monthly_move_probability"]
    )

    scenario.loc[
        scenario["month_number"].eq(0),
        "renter_moves",
    ] = False

    # -----------------------------------------------------
    # Calculate actual renter rent
    # -----------------------------------------------------
    actual_rents = []

    previous_rent = float(
        scenario.iloc[0]["market_rent"]
    )

    for _, row in scenario.iterrows():

        month_number = int(
            row["month_number"]
        )

        market_rent = float(
            row["market_rent"]
        )

        rent_growth_mode = str(
            row["rent_growth_mode"]
        )

        renter_moves = bool(
            row["renter_moves"]
        )

        if month_number == 0:
            actual_rent = market_rent

        elif rent_growth_mode == "market":
            actual_rent = market_rent

        elif renter_moves:
            actual_rent = market_rent

        else:
            rent_control_rate = row[
                "rent_control_rate"
            ]

            if pd.isna(rent_control_rate):
                actual_rent = market_rent

            else:
                monthly_rent_control_rate = (
                    float(rent_control_rate)
                    / 12
                )

                actual_rent = (
                    previous_rent
                    * (
                        1
                        + monthly_rent_control_rate
                    )
                )

                # Controlled rent cannot exceed market rent.
                actual_rent = min(
                    actual_rent,
                    market_rent,
                )

        actual_rents.append(
            actual_rent
        )

        previous_rent = actual_rent

    scenario["actual_renter_rent"] = (
        actual_rents
    )

    # -----------------------------------------------------
    # Calculate moving cost
    # -----------------------------------------------------
    scenario["move_cost"] = 0.0

    moving_rows = scenario["renter_moves"]

    scenario.loc[
        moving_rows,
        "move_cost",
    ] = (
        scenario.loc[
            moving_rows,
            "actual_renter_rent",
        ]
        * scenario.loc[
            moving_rows,
            "move_cost_multiplier",
        ]
    )

    # -----------------------------------------------------
    # Calculate renter monthly cash flow
    # -----------------------------------------------------
    scenario["renter_total_cash_outflow"] = (
        scenario["actual_renter_rent"]
        + scenario["move_cost"]
    )

    scenario["monthly_savings_difference"] = (
        scenario["owner_total_cash_outflow"]
        - scenario["renter_total_cash_outflow"]
    )

    # Positive difference:
    # invest according to renter discipline.
    #
    # Negative difference:
    # withdraw the full amount.
    scenario["renter_monthly_investment"] = np.where(
        scenario["monthly_savings_difference"] >= 0,
        (
            scenario["monthly_savings_difference"]
            * renter_discipline
        ),
        scenario["monthly_savings_difference"],
    )

    # Month 0 already contains the initial investment.
    # Do not add monthly savings in month 0.
    scenario.loc[
        scenario["month_number"].eq(0),
        "renter_monthly_investment",
    ] = 0.0

    # -----------------------------------------------------
    # Calculate renter portfolio value
    # -----------------------------------------------------
    portfolio_value = float(
        scenario.iloc[0][
            "initial_renter_investment"
        ]
    )

    portfolio_values = []

    for _, row in scenario.iterrows():

        month_number = int(
            row["month_number"]
        )

        if month_number == 0:
            portfolio_value = max(
                portfolio_value,
                0.0,
            )

        else:
            portfolio_value = (
                portfolio_value
                * (
                    1
                    + float(
                        row[
                            "portfolio_return_net"
                        ]
                    )
                )
            )

            portfolio_value = (
                portfolio_value
                + float(
                    row[
                        "renter_monthly_investment"
                    ]
                )
            )

            portfolio_value = max(
                portfolio_value,
                0.0,
            )

        portfolio_values.append(
            portfolio_value
        )

    scenario["renter_portfolio_value"] = (
        portfolio_values
    )

    scenario["renter_net_worth"] = (
        scenario["renter_portfolio_value"]
    )

    # -----------------------------------------------------
    # Convert nominal net worth into real net worth
    #
    # Each scenario uses its starting-month CPI as the base.
    # -----------------------------------------------------
    starting_cpi = float(
        scenario.iloc[0]["cpi_value"]
    )

    if (
        not np.isfinite(starting_cpi)
        or starting_cpi <= 0
    ):
        raise ValueError(
            f"Invalid starting CPI for "
            f"owner scenario {owner_scenario_id}, "
            f"portfolio {portfolio_name}, "
            f"discipline {renter_discipline}."
        )

    if (
        scenario["cpi_value"].isna().any()
        or (scenario["cpi_value"] <= 0).any()
    ):
        raise ValueError(
            f"Missing or invalid CPI for "
            f"owner scenario {owner_scenario_id}, "
            f"portfolio {portfolio_name}, "
            f"discipline {renter_discipline}."
        )

    scenario["owner_net_worth_real"] = (
        scenario["owner_net_worth"]
        * starting_cpi
        / scenario["cpi_value"]
    )

    scenario["renter_net_worth_real"] = (
        scenario["renter_net_worth"]
        * starting_cpi
        / scenario["cpi_value"]
    )

    # -----------------------------------------------------
    # Calculate real indexed net worth
    # Each scenario begins at 100
    # -----------------------------------------------------
    starting_owner_real_net_worth = float(
        scenario.iloc[0][
            "owner_net_worth_real"
        ]
    )

    starting_renter_real_net_worth = float(
        scenario.iloc[0][
            "renter_net_worth_real"
        ]
    )

    if np.isclose(
        starting_owner_real_net_worth,
        0.0,
    ):
        scenario["owner_net_worth_index"] = (
            np.nan
        )

    else:
        scenario["owner_net_worth_index"] = (
            scenario["owner_net_worth_real"]
            / starting_owner_real_net_worth
            * 100
        )

    if np.isclose(
        starting_renter_real_net_worth,
        0.0,
    ):
        scenario["renter_net_worth_index"] = (
            np.nan
        )

    else:
        scenario["renter_net_worth_index"] = (
            scenario["renter_net_worth_real"]
            / starting_renter_real_net_worth
            * 100
        )

    return scenario


def prepare_market_data(sp500, tsx, canada_cpi):
    """Keep the original CPI cleanup and price_cad percentage-change formula."""
    sp500 = sp500.copy()
    tsx = tsx.copy()
    canada_cpi = canada_cpi.copy()
    for frame in (sp500, tsx, canada_cpi):
        frame["date_period"] = pd.to_datetime(frame["date_period"])
    canada_cpi["cpi_value"] = pd.to_numeric(
        canada_cpi["cpi_value"],
        errors="coerce",
    )

    canada_cpi = (
        canada_cpi
        .dropna(
            subset=[
                "date_period",
                "cpi_value",
            ]
        )
        .loc[
            lambda df: df["cpi_value"] > 0
        ]
        .sort_values("date_period")
        .drop_duplicates(
            subset=["date_period"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    # =========================================================
    # 4. Prepare stock returns
    # =========================================================
    sp500["price_cad"] = pd.to_numeric(
        sp500["price_cad"],
        errors="coerce",
    )

    tsx["price_cad"] = pd.to_numeric(
        tsx["price_cad"],
        errors="coerce",
    )

    sp500 = (
        sp500
        .dropna(subset=["price_cad"])
        .sort_values("date_period")
        .drop_duplicates(
            subset=["date_period"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    tsx = (
        tsx
        .dropna(subset=["price_cad"])
        .sort_values("date_period")
        .drop_duplicates(
            subset=["date_period"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    sp500["sp500_return"] = (
        sp500["price_cad"]
        .pct_change(fill_method=None)
    )

    tsx["tsx_return"] = (
        tsx["price_cad"]
        .pct_change(fill_method=None)
    )

    stock_returns = (
        sp500[
            [
                "date_period",
                "sp500_return",
            ]
        ]
        .merge(
            tsx[
                [
                    "date_period",
                    "tsx_return",
                ]
            ],
            on="date_period",
            how="outer",
        )
        .sort_values("date_period")
        .reset_index(drop=True)
    )
    # Extra date metadata validates adjacent months without changing the returns.
    for frame, name in ((sp500, "sp500"), (tsx, "tsx")):
        previous = frame[["date_period"]].copy()
        previous[name + "_previous_period"] = frame["date_period"].shift(1)
        stock_returns = stock_returns.merge(previous, on="date_period", how="left", validate="one_to_one")
    return stock_returns, canada_cpi


def validate_merged_inputs(renter):
    required = ["market_rent", "monthly_move_probability", "move_cost_multiplier",
                "renter_discipline", "initial_renter_investment", "monthly_investment_cost",
                "owner_total_cash_outflow", "owner_net_worth", "cpi_value"]
    values = renter[required].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Missing or nonfinite rent, owner, CPI or policy input in the renter batch.")
    if (renter["market_rent"] <= 0).any() or (renter["cpi_value"] <= 0).any():
        raise ValueError("Renter market rent and CPI must be positive.")
    investing = renter["month_number"].gt(0)
    expected_previous = renter["date_period"] - pd.offsets.MonthBegin(1)
    for name in ("sp500", "tsx"):
        valid = np.isfinite(renter[name + "_return"].to_numpy(dtype=float))
        adjacent = renter[name + "_previous_period"].eq(expected_previous)
        bad = investing & (~valid | ~adjacent)
        if bad.any():
            first = renter.loc[bad, ["date_period", "city"]].iloc[0]
            raise ValueError(f"Missing consecutive monthly {name} prices for {first['date_period']}, {first['city']}; no zero return was assumed.")


def calculate_renter_batch(renter, stock_returns, canada_cpi):
    renter = renter.copy()
    renter["date_period"] = pd.to_datetime(renter["date_period"])
    numeric_columns = [
        "market_rent",
        "rent_control_rate",
        "monthly_move_probability",
        "move_cost_multiplier",
        "renter_discipline",
        "initial_renter_investment",
        "monthly_investment_cost",
        "owner_total_cash_outflow",
        "owner_net_worth",
    ]

    for column in numeric_columns:
        renter[column] = pd.to_numeric(
            renter[column],
            errors="coerce",
        )

    # -----------------------------------------------------
    # Add stock returns
    # -----------------------------------------------------
    renter = renter.merge(
        stock_returns,
        on="date_period",
        how="left",
    )

    # -----------------------------------------------------
    # Add Canada CPI
    # -----------------------------------------------------
    renter = renter.merge(
        canada_cpi,
        on="date_period",
        how="left",
    )

    validate_merged_inputs(renter)
    # Only the starting month has no applied return; the original function sets it to zero.
    # Missing investment-month returns are errors, rather than assumed zero returns.

    scenario_columns = [
        "owner_scenario_id",
        "portfolio_name",
        "renter_discipline",
    ]

    calculated_scenarios = []

    for _, scenario_data in renter.groupby(
        scenario_columns,
        sort=False,
        dropna=False,
    ):
        calculated_scenarios.append(
            calculate_one_renter_scenario(
                scenario_data
            )
        )

    renter = pd.concat(
        calculated_scenarios,
        ignore_index=True,
    )

    return renter[RESULT_COLUMNS].copy()

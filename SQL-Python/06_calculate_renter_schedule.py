import os
import gc

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text


# =========================================================
# 1. Settings
# =========================================================
BATCH_SIZE = 500

TEMP_TABLE_NAME = "_renter_monthly_results"


# =========================================================
# 2. PostgreSQL connection
# =========================================================
database_password = os.getenv("POSTGRES_PASSWORD")

if not database_password:
    raise ValueError(
        "POSTGRES_PASSWORD environment variable is not set."
    )

engine = create_engine(
    f"postgresql+psycopg2://postgres:"
    f"{database_password}@localhost:5432/rentvsbuy"
)


# =========================================================
# 3. Load stock prices once
# =========================================================
sp500 = pd.read_sql_query(
    """
    SELECT
        date_period,
        price_cad
    FROM analysis.sp500_index_1990_100
    WHERE date_period <= DATE '2025-12-01'
    ORDER BY date_period
    """,
    engine,
    parse_dates=["date_period"],
)

tsx = pd.read_sql_query(
    """
    SELECT
        date_period,
        price_cad
    FROM analysis.tsx_index_1990_100
    WHERE date_period <= DATE '2025-12-01'
    ORDER BY date_period
    """,
    engine,
    parse_dates=["date_period"],
)

# =========================================================
# 3B. Load Canada CPI once
# =========================================================
canada_cpi = pd.read_sql_query(
    """
    SELECT
        date_period,
        cpi_value
    FROM stg.canada_cpi
    WHERE date_period <= DATE '2025-12-01'
    ORDER BY date_period
    """,
    engine,
    parse_dates=["date_period"],
)

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


# =========================================================
# 5. Calculate one complete renter scenario
# =========================================================
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
    random_seed = 42 + owner_scenario_id

    random_generator = np.random.default_rng(
        random_seed
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


# =========================================================
# 6. PostgreSQL update query
# =========================================================
update_query = text(
    """
    UPDATE simulation.renter_monthly_schedule AS target
    SET
        random_move =
            source.random_move,

        renter_moves =
            source.renter_moves,

        actual_renter_rent =
            source.actual_renter_rent,

        move_cost =
            source.move_cost,

        renter_total_cash_outflow =
            source.renter_total_cash_outflow,

        monthly_savings_difference =
            source.monthly_savings_difference,

        renter_monthly_investment =
            source.renter_monthly_investment,

        sp500_return =
            source.sp500_return,

        tsx_return =
            source.tsx_return,

        portfolio_return =
            source.portfolio_return,

        portfolio_return_net =
            source.portfolio_return_net,

        renter_portfolio_value =
            source.renter_portfolio_value,

        renter_net_worth =
            source.renter_net_worth,
        
        owner_net_worth_real =
            source.owner_net_worth_real,

        renter_net_worth_real =
            source.renter_net_worth_real,

        owner_net_worth_index =
            source.owner_net_worth_index,

        renter_net_worth_index =
            source.renter_net_worth_index

    FROM simulation._renter_monthly_results AS source

    WHERE target.renter_scenario_id =
          source.renter_scenario_id;
    """
)


# =========================================================
# 7. Get renter scenario range
# =========================================================
scenario_range = pd.read_sql_query(
    """
    SELECT
        MIN(owner_scenario_id) AS min_id,
        MAX(owner_scenario_id) AS max_id
    FROM simulation.renter_monthly_schedule
    WHERE date_period <= DATE '2025-12-01'
    """,
    engine,
)

if (
    scenario_range.empty
    or pd.isna(
        scenario_range.loc[0, "min_id"]
    )
):
    raise ValueError(
        "renter_monthly_schedule contains no rows."
    )

min_id = int(
    scenario_range.loc[0, "min_id"]
)

max_id = int(
    scenario_range.loc[0, "max_id"]
)


# =========================================================
# 8. Process renter scenarios in batches
# =========================================================
total_updated_rows = 0

for batch_start in range(
    min_id,
    max_id + 1,
    BATCH_SIZE,
):
    batch_end = (
        batch_start
        + BATCH_SIZE
        - 1
    )

    print(
        f"\nLoading owner scenarios "
        f"{batch_start} to {batch_end}..."
    )

    renter = pd.read_sql_query(
        """
        SELECT
            renter_scenario_id,
            owner_scenario_id,

            date_period,
            month_number,

            city,

            market_rent,
            rent_growth_mode,
            rent_control_rate,
            monthly_move_probability,
            move_cost_multiplier,

            renter_discipline,
            initial_renter_investment,

            portfolio_name,
            monthly_investment_cost,

            owner_total_cash_outflow,
            owner_net_worth

        FROM simulation.renter_monthly_schedule

        WHERE owner_scenario_id
              BETWEEN %(batch_start)s
              AND %(batch_end)s

          AND date_period <= DATE '2025-12-01'

        ORDER BY
            owner_scenario_id,
            portfolio_name,
            renter_discipline,
            month_number
        """,
        engine,
        params={
            "batch_start": batch_start,
            "batch_end": batch_end,
        },
        parse_dates=[
            "date_period",
        ],
    )

    if renter.empty:
        continue

    print(
        f"Loaded {len(renter):,} rows."
    )

    # -----------------------------------------------------
    # Convert PostgreSQL NUMERIC columns to float
    # -----------------------------------------------------
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

    renter["sp500_return"] = (
        renter["sp500_return"]
        .fillna(0.0)
    )

    renter["tsx_return"] = (
        renter["tsx_return"]
        .fillna(0.0)
    )

    # -----------------------------------------------------
    # Calculate each complete renter scenario
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # Show one calculated scenario
    # -----------------------------------------------------
    first_scenario = renter[
        (
            renter["owner_scenario_id"]
            == renter.iloc[0][
                "owner_scenario_id"
            ]
        )
        & (
            renter["portfolio_name"]
            == renter.iloc[0][
                "portfolio_name"
            ]
        )
        & (
            renter["renter_discipline"]
            == renter.iloc[0][
                "renter_discipline"
            ]
        )
    ]

    print(
        first_scenario[
            [
                "owner_scenario_id",
                "date_period",
                "month_number",
                "owner_net_worth",
                "owner_net_worth_index",
                "renter_net_worth",
                "renter_net_worth_index",
            ]
        ].head(5)
    )

    # -----------------------------------------------------
    # Keep result columns
    # -----------------------------------------------------
    results = renter[
    [
        "renter_scenario_id",
        "random_move",
        "renter_moves",
        "actual_renter_rent",
        "move_cost",
        "renter_total_cash_outflow",
        "monthly_savings_difference",
        "renter_monthly_investment",
        "sp500_return",
        "tsx_return",
        "portfolio_return",
        "portfolio_return_net",
        "renter_portfolio_value",
        "renter_net_worth",
        "owner_net_worth_real",
        "renter_net_worth_real",
        "owner_net_worth_index",
        "renter_net_worth_index",
    ]
    ].copy()
    # -----------------------------------------------------
    # Write temporary table
    # -----------------------------------------------------
    print(
        "Writing temporary renter results..."
    )

    results.to_sql(
        name=TEMP_TABLE_NAME,
        con=engine,
        schema="simulation",
        if_exists="replace",
        index=False,
        chunksize=5000,
        method="multi",
    )

    # -----------------------------------------------------
    # Update permanent table
    # -----------------------------------------------------
    print(
        "Updating renter_monthly_schedule..."
    )

    with engine.begin() as connection:
        connection.execute(
            update_query
        )

        connection.execute(
            text(
                f"""
                DROP TABLE IF EXISTS
                simulation.{TEMP_TABLE_NAME};
                """
            )
        )

    batch_row_count = len(results)

    total_updated_rows += (
        batch_row_count
    )

    print(
        f"Updated {batch_row_count:,} rows "
        f"for owner scenarios "
        f"{batch_start} to {batch_end}."
    )

    # -----------------------------------------------------
    # Release memory before next batch
    # -----------------------------------------------------
    del renter
    del results
    del calculated_scenarios

    gc.collect()


print(
    f"\nAll renter batches finished. "
    f"Total updated rows: "
    f"{total_updated_rows:,}."
)
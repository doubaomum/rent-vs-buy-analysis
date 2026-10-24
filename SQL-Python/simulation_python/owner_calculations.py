"""Original owner formulas, separated from database reads and writes.

calculate_payment and calculate_one_scenario are copied unchanged from
calculate_owner_schedule.py. Each batch contains complete scenarios.
"""
import numpy as np
import pandas as pd


def calculate_payment(
    mortgage_balance: float,
    monthly_rate: float,
    remaining_months: int,
) -> float:
    """Calculate the regular monthly mortgage payment."""

    if mortgage_balance <= 0:
        return 0.0

    if remaining_months <= 0:
        return 0.0

    # Handle a 0% interest rate
    if np.isclose(monthly_rate, 0):
        return mortgage_balance / remaining_months

    return (
        mortgage_balance
        * monthly_rate
        / (
            1
            - (1 + monthly_rate) ** (-remaining_months)
        )
    )


def calculate_one_scenario(
    scenario: pd.DataFrame,
) -> pd.DataFrame:

    # Sort each scenario from month 0 onward
    scenario = (
        scenario
        .sort_values("month_number")
        .copy()
    )

    # Confirm the scenario begins with month 0
    if int(scenario.iloc[0]["month_number"]) != 0:
        raise ValueError(
            f"Scenario {scenario.iloc[0]['scenario_id']} "
            "does not begin with month 0."
        )

    # Create/reset mortgage result columns
    scenario["mortgage_payment"] = 0.0
    scenario["mortgage_interest"] = 0.0
    scenario["mortgage_principal"] = 0.0
    scenario["mortgage_balance"] = 0.0

    initial_balance = float(
        scenario.iloc[0]["initial_loan_after_insurance"]
    )

    amortization_years = int(
        scenario.iloc[0]["amortization_years"]
    )

    mortgage_term_year = int(
        scenario.iloc[0]["mortgage_term_year"]
    )

    total_amortization_months = (
        amortization_years * 12
    )

    mortgage_term_months = (
        mortgage_term_year * 12
    )

    current_balance = initial_balance
    scheduled_payment = 0.0
    active_monthly_rate = 0.0

    ## monthly recursion

    for index, row in scenario.iterrows():

        month_number = int(row["month_number"])

        # ---------------------------------------------
        # Month 0: initial mortgage balance
        # ---------------------------------------------
        if month_number == 0:
            scenario.at[index, "mortgage_payment"] = 0.0
            scenario.at[index, "mortgage_interest"] = 0.0
            scenario.at[index, "mortgage_principal"] = 0.0
            scenario.at[index, "mortgage_balance"] = (
                current_balance
            )

            continue

        # ---------------------------------------------
        # Mortgage has already been paid off
        # ---------------------------------------------
        if current_balance <= 0:
            scenario.at[index, "mortgage_payment"] = 0.0
            scenario.at[index, "mortgage_interest"] = 0.0
            scenario.at[index, "mortgage_principal"] = 0.0
            scenario.at[index, "mortgage_balance"] = 0.0

            continue

        # ---------------------------------------------
        # Calculate/recalculate mortgage payment
        #
        # Month 1   = first mortgage payment
        # Month 61  = first renewed payment
        # Month 121 = second renewed payment
        # ---------------------------------------------
        is_payment_reset_month = (
            month_number == 1
            or
            (month_number - 1)
            % mortgage_term_months
            == 0
        )

        if is_payment_reset_month:

            annual_rate = row["applied_mortgage_rate"]

            if pd.isna(annual_rate):
                raise ValueError(
                    f"Missing mortgage rate for "
                    f"scenario {row['scenario_id']}, "
                    f"month {month_number}."
                )

            # Example:
            # 4.61% / 100 / 12
            active_monthly_rate = (
                float(annual_rate)
                / 100
                / 12
            )

            # Before month 1: 0 completed payments
            # Before month 61: 60 completed payments
            completed_payments = month_number - 1

            remaining_months = (
                total_amortization_months
                - completed_payments
            )

            scheduled_payment = calculate_payment(
                mortgage_balance=current_balance,
                monthly_rate=active_monthly_rate,
                remaining_months=remaining_months,
            )

        # ---------------------------------------------
        # Mortgage interest
        # ---------------------------------------------
        mortgage_interest = (
            current_balance
            * active_monthly_rate
        )

        # Prevent the final payment from being too large
        actual_payment = min(
            scheduled_payment,
            current_balance + mortgage_interest,
        )

        # ---------------------------------------------
        # Mortgage principal
        # ---------------------------------------------
        mortgage_principal = max(
            actual_payment - mortgage_interest,
            0,
        )

        mortgage_principal = min(
            mortgage_principal,
            current_balance,
        )

        # ---------------------------------------------
        # New mortgage balance
        # ---------------------------------------------
        current_balance = max(
            current_balance - mortgage_principal,
            0,
        )

        scenario.at[index, "mortgage_payment"] = (
            actual_payment
        )

        scenario.at[index, "mortgage_interest"] = (
            mortgage_interest
        )

        scenario.at[index, "mortgage_principal"] = (
            mortgage_principal
        )

        scenario.at[index, "mortgage_balance"] = (
            current_balance
        )

    return scenario


def calculate_owner_batch(owner: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "initial_loan_after_insurance",
        "applied_mortgage_rate",
        "maintenance_cost",
        "property_cost",
        "insurance_cost",
        "purchase_cost",
        "sale_cost",
        "house_price_market",
        "house_price_sold",
        "estimated_current_sale_cost",
    ]

    for column in numeric_columns:
        owner[column] = pd.to_numeric(
            owner[column],
            errors="coerce",
        )

    calculated_scenarios = []

    for scenario_id, scenario_data in owner.groupby(
        "scenario_id",
        sort=False,
    ):
        calculated_scenario = calculate_one_scenario(
            scenario_data
        )

        calculated_scenarios.append(
            calculated_scenario
        )

    owner = pd.concat(
        calculated_scenarios,
        ignore_index=True,
    )

    owner = owner.sort_values(
        ["scenario_id", "month_number"]
    ).reset_index(drop=True)

    # =========================================================
    # 7. Calculate monthly unrecoverable ownership cost
    #
    # Mortgage principal is NOT included because principal
    # becomes home equity.
    # =========================================================
    cost_columns = [
        "mortgage_interest",
        "maintenance_cost",
        "property_cost",
        "insurance_cost",
    ]

    owner[cost_columns] = (
        owner[cost_columns]
        .fillna(0)
    )

    owner["owner_monthly_unrecoverable_cost"] = (
        owner["mortgage_interest"]
        + owner["maintenance_cost"]
        + owner["property_cost"]
        + owner["insurance_cost"]
    )

    # =========================================================
    # 8. Add purchase cost in month 0
    # =========================================================
    purchase_month = owner["month_number"].eq(0)

    owner.loc[
        purchase_month,
        "owner_monthly_unrecoverable_cost",
    ] += owner.loc[
        purchase_month,
        "purchase_cost",
    ].fillna(0)

    # =========================================================
    # 9. Add sale cost in the sale month
    # =========================================================
    sale_month = (
        owner["is_sale_month"]
        .fillna(False)
        .astype(bool)
    )

    owner.loc[
        sale_month,
        "owner_monthly_unrecoverable_cost",
    ] += owner.loc[
        sale_month,
        "sale_cost",
    ].fillna(0)

    owner["cumulative_unrecoverable_cost"] = (
        owner
        .groupby("scenario_id")[
            "owner_monthly_unrecoverable_cost"
        ]
        .cumsum()
    )

    # =========================================================
    # 11. Calculate owner net worth
    #
    # Owner net worth:
    # current house value
    # - remaining mortgage
    # - estimated cost to sell the house
    #
    # =========================================================

    owner["owner_net_worth"] = (
        owner["house_price_market"]
        - owner["mortgage_balance"]
        - owner["estimated_current_sale_cost"]
    )

    return owner[[
        "scenario_id", "date_period", "mortgage_payment", "mortgage_interest",
        "mortgage_principal", "mortgage_balance", "owner_monthly_unrecoverable_cost",
        "cumulative_unrecoverable_cost", "owner_net_worth",
    ]].copy()

import pandas as pd
from pathlib import Path

# ==================================================
# USER SETTINGS
# ==================================================

SCENARIO_INPUTS_PATH = Path("data/assumptions/scenario_inputs.csv")

HOUSE_PRICE_DIR = Path("data/processed/house/housing_price2005-2025")
MORTGAGE_RATE_PATH = Path("data/external/Canada Mortgage_5_year_term.csv")
RENT_DIR = Path("data/processed/rent")

OUTPUT_PATH = Path("data/processed/final/basic_model_owner_cost_schedule.csv")

MAX_DATA_DATE = "2025-12-01"

AMORTIZATION_YEARS = 25
DEFAULT_MORTGAGE_TYPE = "fixed"
DEFAULT_MORTGAGE_TERM_YEARS = 5

DEPRECIATION_RATE = 0.01
HOME_INSURANCE_RATE = 0.003

PURCHASE_COST_RATE = 0.02
SALE_COST_RATE = 0.06


# ==================================================
# LOAD HOUSE PRICE DATA
# ==================================================

def load_house_price(path):
    """
    Load city house price data.

    Expected columns:
    - Date
    - Composite_Benchmark_SA

    Output columns:
    - date
    - house_price
    """

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(
        df["Date"],
        format="%Y-%m-%d",
        errors="coerce"
    )

    df["house_price"] = pd.to_numeric(
        df["Composite_Benchmark_SA"],
        errors="coerce"
    )

    df = df[["date", "house_price"]].dropna()
    df = df.sort_values("date")

    return df


# ==================================================
# LOAD MORTGAGE RATE DATA
# ==================================================

def load_mortgage_rate(path):
    """
    Load Canada 5-year mortgage rate data.

    Raw format:
    Geography | 2005-01-01 | 2005-02-01 | ...

    Output:
    - date
    - mortgage_rate

    Mortgage rate is converted from percent to decimal:
    5.6 -> 0.056
    """

    df = pd.read_csv(path)

    df = df[df["Geography"] == "Canada"]

    df_long = df.melt(
        id_vars="Geography",
        var_name="date",
        value_name="mortgage_rate"
    )

    df_long["date"] = pd.to_datetime(df_long["date"])

    df_long["mortgage_rate"] = pd.to_numeric(
        df_long["mortgage_rate"],
        errors="coerce"
    ) / 100

    df_long = df_long[["date", "mortgage_rate"]].dropna()
    df_long = df_long.sort_values("date")

    return df_long


# ==================================================
# LOAD RENT DATA
# ==================================================

def load_rent(path):
    """
    Load city rent data.

    Raw columns:
    - Time
    - Total

    CMHC rent data is reported annually, usually in October.
    The rent value is treated as the average monthly rent for that year.
    """

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(df["Time"], errors="coerce")
    df["year"] = df["date"].dt.year

    df["rent"] = pd.to_numeric(df["Total"], errors="coerce")

    df = df[["year", "rent"]].dropna()
    df = df.sort_values("year")

    return df


# ==================================================
# MONTHLY MORTGAGE PAYMENT FORMULA
# ==================================================

def calculate_monthly_payment(loan_amount, annual_rate, remaining_months):
    """
    Calculate fixed monthly mortgage payment.
    """

    if remaining_months <= 0:
        return 0

    monthly_rate = annual_rate / 12

    if monthly_rate == 0:
        return loan_amount / remaining_months

    payment = loan_amount * (
        monthly_rate * (1 + monthly_rate) ** remaining_months
    ) / ((1 + monthly_rate) ** remaining_months - 1)

    return payment

# ==================================================
# NORMALIZE MORTGAGE TYPE
# ==================================================

def normalize_mortgage_type(value):
    """
    Normalize mortgage type from scenario_inputs.csv.

    Accepts values such as:
    - fixed
    - 5-year fixed
    - variable
    """

    if pd.isna(value):
        return DEFAULT_MORTGAGE_TYPE

    value = str(value).strip().lower()

    if "fixed" in value:
        return "fixed"

    if "variable" in value:
        return "variable"

    return DEFAULT_MORTGAGE_TYPE


# ==================================================
# APPLY INTEREST RATE SHOCK
# ==================================================

def apply_mortgage_rate_shock(base_rate, mortgage_rate_shock):
    """
    Apply interest-rate sensitivity shock to historical mortgage rate.

    Example:
    base_rate = 0.045
    mortgage_rate_shock = 0.02
    adjusted_rate = 0.065

    The adjusted rate is floored at 0 to avoid impossible negative rates.
    """

    if pd.isna(mortgage_rate_shock):
        mortgage_rate_shock = 0.0

    adjusted_rate = base_rate + float(mortgage_rate_shock)

    return max(adjusted_rate, 0.0)


# ==================================================
# GENERATE MORTGAGE SCHEDULE
# ==================================================

def generate_mortgage_schedule(
    house_price_df,
    mortgage_rate_df,
    start_date,
    end_date,
    down_payment_rate,
    amortization_years=25,
    mortgage_type="fixed",
    mortgage_term_years=5,
    mortgage_rate_shock=0.0
):
    """
    Generate monthly mortgage schedule from start_date to scenario-specific end_date.
    """

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    house_row = house_price_df[house_price_df["date"] == start_date]

    if house_row.empty:
        raise ValueError(f"No house price found for {start_date.date()}")

    house_price_at_purchase = house_row["house_price"].iloc[0]

    down_payment = house_price_at_purchase * down_payment_rate
    loan_amount = house_price_at_purchase - down_payment

    balance = loan_amount
    total_months = amortization_years * 12

    dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="MS"
    )

    rows = []

    current_rate = None
    current_payment = None

    for i, date in enumerate(dates):

        if balance <= 0:
            balance = 0

        remaining_months = max(total_months - i, 1)

        if mortgage_type == "fixed":

            if i % (mortgage_term_years * 12) == 0 or current_rate is None:

                rate_row = (
                    mortgage_rate_df[mortgage_rate_df["date"] <= date]
                    .sort_values("date")
                    .tail(1)
                )

                if rate_row.empty:
                    raise ValueError(f"No mortgage rate found before {date.date()}")

                base_mortgage_rate = rate_row["mortgage_rate"].iloc[0]
                current_rate = apply_mortgage_rate_shock(
                    base_rate=base_mortgage_rate,
                    mortgage_rate_shock=mortgage_rate_shock
                )

                current_payment = calculate_monthly_payment(
                    loan_amount=balance,
                    annual_rate=current_rate,
                    remaining_months=remaining_months
                )

        elif mortgage_type == "variable":

            rate_row = (
                mortgage_rate_df[mortgage_rate_df["date"] <= date]
                .sort_values("date")
                .tail(1)
            )

            if rate_row.empty:
                raise ValueError(f"No mortgage rate found before {date.date()}")

            base_mortgage_rate = rate_row["mortgage_rate"].iloc[0]
            current_rate = apply_mortgage_rate_shock(
                base_rate=base_mortgage_rate,
                mortgage_rate_shock=mortgage_rate_shock
            )

            current_payment = calculate_monthly_payment(
                loan_amount=balance,
                annual_rate=current_rate,
                remaining_months=remaining_months
            )

        else:
            raise ValueError("mortgage_type must be 'fixed' or 'variable'")

        monthly_rate = current_rate / 12

        mortgage_interest = balance * monthly_rate
        mortgage_principal = min(current_payment - mortgage_interest, balance)

        balance = max(balance - mortgage_principal, 0)

        rows.append({
            "date": date,
            "house_price_at_purchase": house_price_at_purchase,
            "down_payment": down_payment,
            "initial_loan_amount": loan_amount,
            "mortgage_type": mortgage_type,
            "mortgage_term_years": mortgage_term_years,
            "base_mortgage_rate": base_mortgage_rate,
            "mortgage_rate_shock": mortgage_rate_shock,
            "mortgage_rate": current_rate,
            "mortgage_payment": current_payment,
            "mortgage_interest": mortgage_interest,
            "mortgage_principal": mortgage_principal,
            "mortgage_balance": balance
        })

    return pd.DataFrame(rows)


# ==================================================
# ADD OWNER WEALTH
# ==================================================

def add_owner_wealth(schedule_df, house_price_df):
    """
    Owner net worth = current house price - remaining mortgage balance.
    """

    schedule_df = schedule_df.sort_values("date")
    house_price_df = house_price_df.sort_values("date")

    df = schedule_df.merge(
        house_price_df,
        on="date",
        how="left"
    )

    df["house_price"] = df["house_price"].ffill()

    df["owner_networth"] = (
        df["house_price"] - df["mortgage_balance"])
    
    

    return df


# ==================================================
# ADD OWNER COSTS
# ==================================================

def add_owner_costs(
    owner_df,
    rent_df,
    property_tax_rate,
    structure_share,
    depreciation_rate,
    home_insurance_rate,
    purchase_cost_rate,
    sale_cost_rate
):
    """
    Add monthly owner unrecoverable costs.

    Includes:
    - mortgage interest
    - maintenance
    - property tax
    - depreciation
    - home insurance
    - purchase transaction cost
    - sale transaction cost
    """

    df = owner_df.copy()

    df["year"] = df["date"].dt.year

    df = df.merge(
        rent_df,
        on="year",
        how="left"
    )

    df["rent"] = df["rent"].ffill().bfill()

    df["maintenance_cost"] = df["rent"] / 3

    df["property_tax"] = (
        df["house_price"] * property_tax_rate / 12
    )

    df["structure_value"] = (
        df["house_price"] * structure_share
    )

    df["depreciation_cost"] = (
        df["structure_value"] * depreciation_rate / 12
    )

    df["home_insurance_cost"] = (
        df["house_price"] * home_insurance_rate / 12
    )

    df["owner_monthly_cost"] = (
        df["mortgage_interest"]
        + df["maintenance_cost"]
        + df["property_tax"]
        + df["depreciation_cost"]
        + df["home_insurance_cost"]
    )

    df["purchase_cost"] = 0.0
    df.loc[df.index[0], "purchase_cost"] = (
        df.loc[df.index[0], "house_price_at_purchase"]
        * purchase_cost_rate
    )

    df["sale_cost"] = 0.0
    df.loc[df.index[-1], "sale_cost"] = (
        df.loc[df.index[-1], "house_price"]
        * sale_cost_rate
    )

    df["owner_monthly_unrecoverable_cost"] = (
        df["owner_monthly_cost"]
        + df["purchase_cost"]
        + df["sale_cost"]
    )
    df["owner_networth_after_sale"] = (
        df["house_price"]
        - df["mortgage_balance"]
        - df["sale_cost"]
)

    return df


# ==================================================
# SCENARIO END DATE
# ==================================================

def calculate_scenario_end_date(start_date, holding_years, max_data_date):
    """
    Calculate scenario-specific end date from start date and holding period.

    Example:
    start_date = 2005-01-01
    holding_years = 10
    end_date = 2015-01-01

    If calculated end date is after available data, return None.
    """

    start_date = pd.to_datetime(start_date)
    max_data_date = pd.to_datetime(max_data_date)

    end_date = start_date + pd.DateOffset(years=int(holding_years))
    end_date = end_date.replace(day=1)

    if end_date > max_data_date:
        return None

    return end_date


# ==================================================
# RUN SCRIPT
# ==================================================

if __name__ == "__main__":

    scenario_inputs = pd.read_csv(SCENARIO_INPUTS_PATH)

    mortgage_rate_df = load_mortgage_rate(MORTGAGE_RATE_PATH)

    all_results = []

    for _, scenario in scenario_inputs.iterrows():

        scenario_id = scenario["scenario_id"]
        city = scenario["city"]
        portfolio_name = scenario["portfolio_name"]

        start_date = scenario["start_date"]
        holding_years = scenario["holding_years"]
        renter_discipline = scenario["renter_discipline"]

        down_payment_rate = scenario["down_payment_pct"]
        property_tax_rate = scenario["property_tax_rate"]
        structure_share = scenario["structure_ratio"]

        mortgage_type = normalize_mortgage_type(
            scenario.get("mortgage_type", DEFAULT_MORTGAGE_TYPE)
        )

        interest_rate_scenario = scenario.get(
            "interest_rate_scenario",
            "base_rate"
        )

        mortgage_rate_shock = scenario.get(
            "mortgage_rate_shock",
            0.0
        )

        scenario_end_date = calculate_scenario_end_date(
            start_date=start_date,
            holding_years=holding_years,
            max_data_date=MAX_DATA_DATE
        )

        if scenario_end_date is None:
            print(
                f"Skipping scenario {scenario_id}: "
                f"start={start_date}, holding={holding_years} exceeds available data."
            )
            continue

        house_price_path = (
            HOUSE_PRICE_DIR
            / f"{str(city).lower()}_house_price.csv"
        )

        rent_path = (
            RENT_DIR
            / f"{str(city).lower()}_rent.csv"
        )

        print("\n=== Running Owner Scenario ===")
        print("Scenario ID:", scenario_id)
        print("City:", city)
        print("Portfolio:", portfolio_name)
        print("Start Date:", start_date)
        print("Holding Years:", holding_years)
        print("End Date:", scenario_end_date.date())
        print("Renter Discipline:", renter_discipline)
        print("Interest Rate Scenario:", interest_rate_scenario)
        print("Mortgage Rate Shock:", mortgage_rate_shock)

        house_price_df = load_house_price(house_price_path)
        rent_df = load_rent(rent_path)

        schedule = generate_mortgage_schedule(
            house_price_df=house_price_df,
            mortgage_rate_df=mortgage_rate_df,
            start_date=start_date,
            end_date=scenario_end_date,
            down_payment_rate=down_payment_rate,
            amortization_years=AMORTIZATION_YEARS,
            mortgage_type=mortgage_type,
            mortgage_term_years=DEFAULT_MORTGAGE_TERM_YEARS,
            mortgage_rate_shock=mortgage_rate_shock
        )

        owner_wealth = add_owner_wealth(
            schedule_df=schedule,
            house_price_df=house_price_df
        )

        owner_cost = add_owner_costs(
            owner_df=owner_wealth,
            rent_df=rent_df,
            property_tax_rate=property_tax_rate,
            structure_share=structure_share,
            depreciation_rate=DEPRECIATION_RATE,
            home_insurance_rate=HOME_INSURANCE_RATE,
            purchase_cost_rate=PURCHASE_COST_RATE,
            sale_cost_rate=SALE_COST_RATE
        )

        owner_cost["scenario_id"] = scenario_id
        owner_cost["city"] = city
        owner_cost["portfolio_name"] = portfolio_name
        owner_cost["start_date"] = pd.to_datetime(start_date)
        owner_cost["end_date"] = scenario_end_date
        owner_cost["holding_years"] = holding_years
        owner_cost["renter_discipline"] = renter_discipline
        owner_cost["interest_rate_scenario"] = interest_rate_scenario
        owner_cost["mortgage_rate_shock"] = mortgage_rate_shock
        owner_cost["mortgage_type"] = mortgage_type
        owner_cost["down_payment_pct"] = down_payment_rate
        owner_cost["property_tax_rate"] = property_tax_rate
        owner_cost["structure_ratio"] = structure_share

        all_results.append(owner_cost)

    if not all_results:
        raise ValueError("No owner scenarios were generated. Check scenario_inputs.csv.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    final_results = pd.concat(all_results, ignore_index=True)

    final_results.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\nSaved to:", OUTPUT_PATH)
    print("Final shape:", final_results.shape)
    print(final_results.head())
    print(final_results.tail())

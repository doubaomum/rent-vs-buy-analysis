import pandas as pd
from pathlib import Path

# ==================================================
# USER SETTINGS
# ==================================================

HOUSE_PRICE_PATH = Path("data/processed/house/housing_price2005-2025/CANADA.csv")
MORTGAGE_RATE_PATH = Path("data/external/Canada Mortgage_5_year_term.csv")
RENT_PATH = Path("data/processed/rent/canada_rent.csv")

OUTPUT_PATH = Path("data/processed/final/basic_model_owner_cost_schedule.csv")

START_DATE = "2005-01-01"
END_DATE = "2025-12-01"

DOWN_PAYMENT_RATE = 0.20
AMORTIZATION_YEARS = 25

MORTGAGE_TYPE = "fixed"      # "fixed" or "variable"
MORTGAGE_TERM_YEARS = 5      # fixed mortgage renews every 5 years

PROPERTY_TAX_RATE = 0.01
STRUCTURE_SHARE = 0.50 
DEPRECIATION_RATE = 0.01

PURCHASE_COST_RATE = 0.02
SALE_COST_RATE = 0.06


# ==================================================
# LOAD HOUSE PRICE DATA
# ==================================================

def load_house_price(path):
    """
    Load CREA Canada house price data.

    Expected raw columns:
    - Date
    - Composite_Benchmark_SA

    Output columns:
    - date
    - house_price
    """

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(df["Date"])
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

    Raw file format:
    - Geography column
    - monthly dates as columns

    Example:
    Geography | 2005-01-01 | 2005-02-01 | ...

    Output:
    - date
    - mortgage_rate

    Mortgage rate is converted from percent to decimal:
    5.6 -> 0.056
    """

    df = pd.read_csv(path)

    # Keep only Canada row
    df = df[df["Geography"] == "Canada"]

    # Convert wide table to long table
    df_long = df.melt(
        id_vars="Geography",
        var_name="date",
        value_name="mortgage_rate"
    )

    df_long["date"] = pd.to_datetime(df_long["date"])

    df_long["mortgage_rate"] = pd.to_numeric(
        df_long["mortgage_rate"],
        errors="coerce"
    )

    # Convert percent to decimal
    df_long["mortgage_rate"] = df_long["mortgage_rate"] / 100

    df_long = df_long[["date", "mortgage_rate"]].dropna()
    df_long = df_long.sort_values("date")

    return df_long


# ==================================================
# LOAD RENT DATA
# ==================================================

def load_rent(path):
    """
    Load Canada rent data.

    Raw columns:
    - Time
    - Total

    Important logic:
    CMHC rent data is reported in October each year.
    In this model, October rent is treated as the average rent
    for the whole calendar year.

    Example:
    2025-10 rent is used for 2025-01 to 2025-12.
    """

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(df["Time"])
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

    Parameters
    ----------
    loan_amount:
        Remaining mortgage balance.

    annual_rate:
        Annual mortgage rate in decimal format.
        Example: 0.056 means 5.6%.

    remaining_months:
        Number of months left in amortization.

    Returns
    -------
    Monthly mortgage payment.
    """

    monthly_rate = annual_rate / 12

    if monthly_rate == 0:
        return loan_amount / remaining_months

    payment = loan_amount * (
        monthly_rate * (1 + monthly_rate) ** remaining_months
    ) / ((1 + monthly_rate) ** remaining_months - 1)

    return payment


# ==================================================
# GENERATE MORTGAGE SCHEDULE
# ==================================================

def generate_mortgage_schedule(
    house_price_df,
    mortgage_rate_df,
    start_date,
    end_date,
    down_payment_rate=0.20,
    amortization_years=25,
    mortgage_type="fixed",
    mortgage_term_years=5
):
    """
    Generate mortgage schedule from start_date to end_date.

    Important:
    The amortization is 25 years, but the simulation stops at END_DATE.
    This means the house is sold in 2025-12, not when the mortgage is fully paid.
    """

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Get purchase price at start date
    house_row = house_price_df[house_price_df["date"] == start_date]

    if house_row.empty:
        raise ValueError(f"No house price found for {start_date}")

    house_price = house_row["house_price"].iloc[0]

    down_payment = house_price * down_payment_rate
    loan_amount = house_price - down_payment

    balance = loan_amount
    total_months = amortization_years * 12

    # Only simulate to END_DATE
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
            break

        # Fixed mortgage:
        # rate and payment update only at renewal
        if mortgage_type == "fixed":

            if i % (mortgage_term_years * 12) == 0:

                rate_row = (
                    mortgage_rate_df[mortgage_rate_df["date"] <= date]
                    .sort_values("date")
                    .tail(1)
                )

                if rate_row.empty:
                    raise ValueError(f"No mortgage rate found before {date}")

                current_rate = rate_row["mortgage_rate"].iloc[0]

                remaining_months = total_months - i

                current_payment = calculate_monthly_payment(
                    loan_amount=balance,
                    annual_rate=current_rate,
                    remaining_months=remaining_months
                )

        # Variable mortgage:
        # rate and payment update every month
        elif mortgage_type == "variable":

            rate_row = (
                mortgage_rate_df[mortgage_rate_df["date"] <= date]
                .sort_values("date")
                .tail(1)
            )

            if rate_row.empty:
                raise ValueError(f"No mortgage rate found before {date}")

            current_rate = rate_row["mortgage_rate"].iloc[0]

            remaining_months = total_months - i

            current_payment = calculate_monthly_payment(
                loan_amount=balance,
                annual_rate=current_rate,
                remaining_months=remaining_months
            )

        else:
            raise ValueError("mortgage_type must be 'fixed' or 'variable'")

        # Monthly mortgage calculation
        monthly_rate = current_rate / 12

        mortgage_interest = balance * monthly_rate
        mortgage_principal = current_payment - mortgage_interest

        balance = max(balance - mortgage_principal, 0)

        rows.append({
            "date": date,
            "house_price_at_purchase": house_price,
            "down_payment": down_payment,
            "initial_loan_amount": loan_amount,
            "mortgage_type": mortgage_type,
            "mortgage_term_years": mortgage_term_years,
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
    Add current house price and owner net worth.

    Owner net worth = current house price - remaining mortgage balance.
    """

    schedule_df = schedule_df.sort_values("date")
    house_price_df = house_price_df.sort_values("date")

    df = schedule_df.merge(
        house_price_df,
        on="date",
        how="left"
    )

    # Fill missing house price forward if needed
    df["house_price"] = df["house_price"].ffill()

    df["owner_networth"] = (
        df["house_price"] - df["mortgage_balance"]
    )

    return df


# ==================================================
# ADD OWNER COSTS
# ==================================================

def add_owner_costs(owner_df, rent_df):
    """
    Add owner unrecoverable costs.

    Includes:
    - mortgage interest
    - maintenance
    - property tax
    - depreciation
    - purchase transaction cost
    - sale transaction cost

    Principal repayment is NOT counted as cost,
    because it builds home equity.
    """

    df = owner_df.copy()

    # Match rent by calendar year
    df["year"] = df["date"].dt.year

    df = df.merge(
        rent_df,
        on="year",
        how="left"
    )

    # maintenance assumption:
    # maintenance = 1/3 of monthly rent
    df["maintenance_cost"] = df["rent"] / 3

    # Monthly property tax
    df["property_tax"] = (
        df["house_price"] * PROPERTY_TAX_RATE / 12
    )

   
    # Monthly depreciation
    # Only the structure depreciates; land does not depreciate.
    df["structure_value"] = df["house_price"] * STRUCTURE_SHARE

    df["depreciation_cost"] = (
        df["structure_value"] * DEPRECIATION_RATE / 12
    )

    # Monthly unrecoverable owner cost
    df["owner_monthly_cost"] = (
        df["mortgage_interest"]
        + df["maintenance_cost"]
        + df["property_tax"]
        + df["depreciation_cost"]
    )

    # Purchase transaction cost only happens at the first month
    df["purchase_cost"] = 0.0
    df.loc[df.index[0], "purchase_cost"] = (
        df.loc[df.index[0], "house_price_at_purchase"]
        * PURCHASE_COST_RATE
    )

    # Sale transaction cost only happens at the final month
    df["sale_cost"] = 0.0
    df.loc[df.index[-1], "sale_cost"] = (
        df.loc[df.index[-1], "house_price"]
        * SALE_COST_RATE
    )

    # Total owner cost including one-time transaction costs
    df["owner_monthly_unrecoverable_cost"] = (
        df["owner_monthly_cost"]
        + df["purchase_cost"]
        + df["sale_cost"]
    )

    return df


# ==================================================
# RUN SCRIPT
# ==================================================

if __name__ == "__main__":

    # Load input datasets
    house_price_df = load_house_price(HOUSE_PRICE_PATH)
    mortgage_rate_df = load_mortgage_rate(MORTGAGE_RATE_PATH)
    rent_df = load_rent(RENT_PATH)

    # Generate mortgage schedule
    schedule = generate_mortgage_schedule(
        house_price_df=house_price_df,
        mortgage_rate_df=mortgage_rate_df,
        start_date=START_DATE,
        end_date=END_DATE,
        down_payment_rate=DOWN_PAYMENT_RATE,
        amortization_years=AMORTIZATION_YEARS,
        mortgage_type=MORTGAGE_TYPE,
        mortgage_term_years=MORTGAGE_TERM_YEARS
    )

    # Add house price and owner net worth
    owner_wealth = add_owner_wealth(
        schedule_df=schedule,
        house_price_df=house_price_df
    )

    # Add rent-based maintenance and ownership costs
    owner_cost = add_owner_costs(
        owner_df=owner_wealth,
        rent_df=rent_df
    )

    # Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    owner_cost.to_csv(OUTPUT_PATH, index=False)

    print(owner_cost.head())
    print(owner_cost.tail())
    print("\nSaved to:", OUTPUT_PATH)
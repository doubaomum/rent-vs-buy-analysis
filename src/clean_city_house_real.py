import pandas as pd
from pathlib import Path

# ============================================================
# 1. File Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent / "data"

HOUSE_DIR = BASE_DIR / "processed" / "house"
CPI_DIR = BASE_DIR / "external"
OUTPUT_DIR = BASE_DIR / "processed" / "final"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Input Files
# ============================================================

city_house_path = HOUSE_DIR / "city_house_index200506=100.csv"
cpi_path = CPI_DIR / "canada_cpi.csv"

# ============================================================
# Output File
# ============================================================

output_path = OUTPUT_DIR / "city_house_real_1999_index.csv"

# ============================================================
# Analysis Period
# ============================================================

START_DATE = "1999-02-01"
END_DATE = "2025-12-01"

# Base date used for:
# 1. Inflation adjustment
# 2. Re-indexing to 1999 = 100
BASE_DATE = "1999-02-01"

# ============================================================
# 2. Helper Functions
# ============================================================

def standardize_monthly_date(df, date_col="date"):
    """
    Convert dates into monthly timestamps.

    Example:
    1999-02-15 -> 1999-02-01
    """

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df = df.dropna(subset=[date_col]).copy()

    df[date_col] = (
        df[date_col]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    return df


def normalize_to_base(df, value_col, base_date, new_col):
    """
    Re-index a series to a chosen base date = 100.

    Formula:
        indexed_value = current_value / base_value * 100
    """

    base_date = pd.to_datetime(base_date)

    base_series = df.loc[
        df["date"] == base_date,
        value_col
    ].dropna()

    if base_series.empty:
        raise ValueError(
            f"No base value found for {value_col} on {base_date.date()}"
        )

    base_value = base_series.iloc[0]

    df[new_col] = (
        df[value_col] / base_value * 100
    )

    return df


# ============================================================
# 3. Load and Clean CPI Data
# ============================================================

cpi_raw = pd.read_csv(cpi_path)

# Convert wide-format CPI table into long format
cpi = cpi_raw.melt(
    id_vars=["Products and product groups 3 4"],
    var_name="date",
    value_name="cpi"
)

# Remove unused descriptor column
cpi = cpi.drop(
    columns=["Products and product groups 3 4"]
)

# Convert dates such as:
# Jan-90
cpi["date"] = pd.to_datetime(
    cpi["date"],
    format="%b-%y",
    errors="coerce"
)

# Convert to monthly timestamp
cpi["date"] = (
    cpi["date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

# Convert CPI values to numeric
cpi["cpi"] = pd.to_numeric(
    cpi["cpi"],
    errors="coerce"
)

# Remove missing values
cpi = cpi.dropna(
    subset=["date", "cpi"]
).copy()

# Keep only analysis period
cpi = cpi[
    (cpi["date"] >= START_DATE) &
    (cpi["date"] <= END_DATE)
].copy()

# Base CPI value
base_cpi_series = cpi.loc[
    cpi["date"] == pd.to_datetime(BASE_DATE),
    "cpi"
].dropna()

if base_cpi_series.empty:
    raise ValueError(
        f"No CPI value found for base date {BASE_DATE}"
    )

base_cpi = base_cpi_series.iloc[0]

# ============================================================
# 4. Load City-Level House Price Index
# ============================================================

city_house = pd.read_csv(city_house_path)

print(city_house.columns)

# Standardize monthly dates
city_house = standardize_monthly_date(
    city_house,
    "date"
)

# ============================================================
# Select City Columns
# ============================================================

city_columns = [
    "bc_vancouver",
    "on_toronto",
    "qc_montreal",
    "ab_calgary",
    "on_ottawa",
    "ab_edmonton",
]

keep_columns = ["date"] + city_columns

city_house = city_house[keep_columns].copy()

# Convert city index values to numeric
for col in city_columns:

    city_house[col] = pd.to_numeric(
        city_house[col],
        errors="coerce"
    )

# ============================================================
# 5. Merge CPI Data
# ============================================================

city_house = city_house.merge(
    cpi[["date", "cpi"]],
    on="date",
    how="left"
)

# Forward-fill CPI values if necessary
city_house["cpi"] = city_house["cpi"].ffill()

# Keep only analysis period
city_house = city_house[
    (city_house["date"] >= START_DATE) &
    (city_house["date"] <= END_DATE)
].copy()

# ============================================================
# 6. Convert Nominal Index -> Real Index
# ============================================================

"""
The Teranet-National Bank HPI is a nominal index.

To remove inflation effects:

real_value = nominal_value / CPI × base_CPI
"""

for col in city_columns:

    real_col = f"{col}_real"

    city_house[real_col] = (
        city_house[col] / city_house["cpi"] * base_cpi
    )

# ============================================================
# 7. Re-Index Real Values to 1999 = 100
# ============================================================

for col in city_columns:

    real_col = f"{col}_real"

    index_col = f"{col}_real_index_1999"

    city_house = normalize_to_base(
        city_house,
        real_col,
        BASE_DATE,
        index_col
    )

# ============================================================
# 8. Final Output Dataset
# ============================================================

final_columns = ["date"]

for col in city_columns:

    final_columns.extend([
        col,
        f"{col}_real",
        f"{col}_real_index_1999"
    ])

city_house_final = city_house[
    final_columns
].copy()

# ============================================================
# 9. Save Final Dataset
# ============================================================

city_house_final.to_csv(
    output_path,
    index=False
)

print("\nDone!")
print(f"Saved to: {output_path}")

print("\n==============================")
print(city_house_final.head())

print("\n==============================")
print(city_house_final.tail())

print("\n==============================")
print(city_house_final.info())
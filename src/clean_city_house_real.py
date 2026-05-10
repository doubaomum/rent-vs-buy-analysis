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

city_house_path = HOUSE_DIR / "city_house_index200506=100.csv"
canada_house_path = HOUSE_DIR / "canada_house_index2010=100.csv"
cpi_path = CPI_DIR / "canada_cpi.csv"

output_path = OUTPUT_DIR / "city_house_with_canada_real_1999_index.csv"

# ============================================================
# 2. Analysis Period
# ============================================================

START_DATE = "1999-02-01"
END_DATE = "2025-12-01"


# ============================================================
# 3. Helper Functions
# ============================================================

def standardize_monthly_date(df, date_col="date"):
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).copy()
    df[date_col] = df[date_col].dt.to_period("M").dt.to_timestamp()
    return df


def normalize_to_start_date(df, value_col, new_col):
    start_date = pd.to_datetime(START_DATE)

    start_value_series = df.loc[
        df["date"] == start_date,
        value_col
    ].dropna()

    if start_value_series.empty:
        raise ValueError(
            f"No start value found for {value_col} on {START_DATE}"
        )

    start_value = start_value_series.iloc[0]

    df[new_col] = df[value_col] / start_value * 100

    return df


# ============================================================
# 4. Load and Clean CPI Data
# ============================================================

cpi_raw = pd.read_csv(cpi_path)

cpi = cpi_raw.melt(
    id_vars=["Products and product groups 3 4"],
    var_name="date",
    value_name="cpi"
)

cpi = cpi.drop(columns=["Products and product groups 3 4"])

cpi["date"] = pd.to_datetime(
    cpi["date"],
    format="%b-%y",
    errors="coerce"
)

cpi["date"] = cpi["date"].dt.to_period("M").dt.to_timestamp()

cpi["cpi"] = pd.to_numeric(cpi["cpi"], errors="coerce")

cpi = cpi.dropna(subset=["date", "cpi"]).copy()

cpi = cpi[
    (cpi["date"] >= START_DATE) &
    (cpi["date"] <= END_DATE)
].copy()

start_cpi_series = cpi.loc[
    cpi["date"] == pd.to_datetime(START_DATE),
    "cpi"
].dropna()

if start_cpi_series.empty:
    raise ValueError(f"No CPI value found for start date {START_DATE}")

start_cpi = start_cpi_series.iloc[0]


# ============================================================
# 5. Load City-Level House Price Index
# ============================================================

city_house = pd.read_csv(city_house_path)

city_house = city_house.rename(columns={
    "time": "date"
})

city_house = standardize_monthly_date(city_house, "date")

city_columns = [
    "bc_vancouver",
    "on_toronto",
    "qc_montreal",
    "ab_calgary",
    "on_ottawa",
    "ab_edmonton",
]

city_house = city_house[["date"] + city_columns].copy()

for col in city_columns:
    city_house[col] = pd.to_numeric(city_house[col], errors="coerce")


# ============================================================
# 6. Convert City Nominal Indexes to Real Indexes
# ============================================================

city_house = city_house.merge(
    cpi[["date", "cpi"]],
    on="date",
    how="left"
)

city_house["cpi"] = city_house["cpi"].ffill()

city_house = city_house[
    (city_house["date"] >= START_DATE) &
    (city_house["date"] <= END_DATE)
].copy()

for col in city_columns:
    real_col = f"{col}_real"
    index_col = f"{col}_real_index_1999"

    city_house[real_col] = city_house[col] / city_house["cpi"] * start_cpi

    city_house = normalize_to_start_date(
        city_house,
        real_col,
        index_col
    )


# ============================================================
# 7. Load Canada National Housing Index
# ============================================================

canada_house = pd.read_csv(canada_house_path)

if "TIME_PERIOD" in canada_house.columns:
    canada_house = canada_house.rename(columns={
        "TIME_PERIOD": "date",
        "OBS_VALUE": "canada_house_real"
    })

elif "indx" in canada_house.columns:
    canada_house = canada_house.rename(columns={
        "indx": "canada_house_real"
    })

if "time" in canada_house.columns:
    canada_house = canada_house.rename(columns={
        "time": "date"
    })

canada_house = standardize_monthly_date(canada_house, "date")

canada_house["canada_house_real"] = pd.to_numeric(
    canada_house["canada_house_real"],
    errors="coerce"
)

# Canada national housing index is quarterly.
# Convert it to monthly frequency using forward-fill.
canada_house = (
    canada_house
    .set_index("date")
    .resample("MS")
    .ffill()
    .reset_index()
)

canada_house = canada_house[
    (canada_house["date"] >= START_DATE) &
    (canada_house["date"] <= END_DATE)
].copy()

canada_house = normalize_to_start_date(
    canada_house,
    "canada_house_real",
    "canada_house_real_index_1999"
)


# ============================================================
# 8. Merge City Data with Canada Benchmark
# ============================================================

final_df = city_house.merge(
    canada_house[
        [
            "date",
            "canada_house_real",
            "canada_house_real_index_1999"
        ]
    ],
    on="date",
    how="left"
)

final_columns = [
    "date",
    "canada_house_real",
    "canada_house_real_index_1999",
]

for col in city_columns:
    final_columns.extend([
        col,
        f"{col}_real",
        f"{col}_real_index_1999"
    ])

final_df = final_df[final_columns].copy()


# ============================================================
# 9. Save Final Dataset
# ============================================================

final_df.to_csv(output_path, index=False)

print("\nDone!")
print(f"Saved to: {output_path}")

print("\nPreview:")
print(final_df.head())

print("\nTail:")
print(final_df.tail())

print("\nInfo:")
print(final_df.info())
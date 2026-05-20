import pandas as pd
from pathlib import Path

# ============================================================
# 1. File Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent / "data"

HOUSE_DIR = BASE_DIR / "processed" / "house"
STOCK_DIR = BASE_DIR / "processed" / "stock"
FX_DIR = BASE_DIR / "external" / "fx"
CPI_DIR = BASE_DIR / "external"
OUTPUT_DIR = BASE_DIR / "processed" / "final"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

city_house_path = HOUSE_DIR / "city_house_index200506=100.csv"
canada_house_path = HOUSE_DIR / "canada_house_index2010=100.csv"
sp500_path = STOCK_DIR / "sp500.csv"
tsx_path = STOCK_DIR / "tsx.csv"
fx_path = FX_DIR / "usd_cad.csv"
cpi_path = CPI_DIR / "canada_cpi.csv"

output_path = OUTPUT_DIR / "city_house_canada_real_1999_index.csv"

# ============================================================
# 2. Analysis Period
# ============================================================

START_DATE = "1999-02-01"
END_DATE = "2025-12-01"
BASE_DATE = START_DATE


# ============================================================
# 3. Helper Functions
# ============================================================

def standardize_monthly_date(df, date_col="date"):
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).copy()
    df[date_col] = df[date_col].dt.to_period("M").dt.to_timestamp()
    return df


def normalize_to_base(df, value_col, base_date, new_col):
    base_date = pd.to_datetime(base_date)

    base_series = df.loc[df["date"] == base_date, value_col].dropna()

    if base_series.empty:
        raise ValueError(
            f"No base value found for {value_col} on {base_date.date()}"
        )

    base_value = base_series.iloc[0]
    df[new_col] = df[value_col] / base_value * 100

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

cpi["date"] = pd.to_datetime(cpi["date"], format="%b-%y", errors="coerce").fillna(
    pd.to_datetime(cpi["date"], format="%y-%b", errors="coerce")
)

cpi["date"] = cpi["date"].dt.to_period("M").dt.to_timestamp()
cpi["cpi"] = pd.to_numeric(cpi["cpi"], errors="coerce")

cpi = cpi.dropna(subset=["date", "cpi"]).copy()

cpi = cpi[
    (cpi["date"] >= START_DATE) &
    (cpi["date"] <= END_DATE)
].copy()

base_cpi_series = cpi.loc[
    cpi["date"] == pd.to_datetime(BASE_DATE),
    "cpi"
].dropna()

if base_cpi_series.empty:
    raise ValueError(f"No CPI value found for base date {BASE_DATE}")

base_cpi = base_cpi_series.iloc[0]


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

    city_house[real_col] = city_house[col] / city_house["cpi"] * base_cpi

    city_house = normalize_to_base(
        city_house,
        real_col,
        BASE_DATE,
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

canada_house = normalize_to_base(
    canada_house,
    "canada_house_real",
    BASE_DATE,
    "canada_house_real_index_1999"
)


# ============================================================
# 8. USD/CAD Exchange Rate
# ============================================================

fx = pd.read_csv(fx_path)

fx = fx.rename(columns={
    "observation_date": "date",
    "DEXCAUS": "usd_cad"
})

fx = standardize_monthly_date(fx, "date")

fx["usd_cad"] = pd.to_numeric(fx["usd_cad"], errors="coerce")

fx = (
    fx
    .set_index("date")
    .resample("MS")
    .mean()
    .reset_index()
)

fx["usd_cad"] = fx["usd_cad"].ffill()


# ============================================================
# 9. TSX: Nominal CAD -> Real CAD -> 1999 Index
# ============================================================

# ============================================================
# 9. TSX: Daily/Monthly Nominal CAD -> Monthly Real CAD -> 1999 Index
# ============================================================

tsx = pd.read_csv(tsx_path)
tsx = standardize_monthly_date(tsx, "date")

tsx["tsx_cad"] = (
    tsx["tsx_cad"]
    .astype(str)
    .str.replace(",", "", regex=False)
)

tsx["tsx_cad"] = pd.to_numeric(tsx["tsx_cad"], errors="coerce")

# IMPORTANT: one row per month
tsx = (
    tsx
    .dropna(subset=["tsx_cad"])
    .sort_values("date")
    .groupby("date", as_index=False)
    .last()
)

tsx = tsx.merge(cpi[["date", "cpi"]], on="date", how="left")
tsx["cpi"] = tsx["cpi"].ffill()

tsx = tsx[
    (tsx["date"] >= START_DATE) &
    (tsx["date"] <= END_DATE)
].copy()

tsx["tsx_real"] = tsx["tsx_cad"] / tsx["cpi"] * base_cpi

tsx = normalize_to_base(
    tsx,
    "tsx_real",
    BASE_DATE,
    "tsx_real_index_1999"
)


# ============================================================
# 10. S&P 500: Daily/Monthly USD -> Monthly CAD -> Real CAD -> 1999 Index
# ============================================================

sp500 = pd.read_csv(sp500_path)
sp500 = standardize_monthly_date(sp500, "date")

sp500["sp500_price"] = (
    sp500["sp500_price"]
    .astype(str)
    .str.replace(",", "", regex=False)
)

sp500["sp500_price"] = pd.to_numeric(sp500["sp500_price"], errors="coerce")

sp500 = sp500.rename(columns={
    "sp500_price": "sp500_usd"
})

# IMPORTANT: one row per month
sp500 = (
    sp500
    .dropna(subset=["sp500_usd"])
    .sort_values("date")
    .groupby("date", as_index=False)
    .last()
)

sp500 = sp500.merge(fx[["date", "usd_cad"]], on="date", how="left")
sp500["usd_cad"] = sp500["usd_cad"].ffill()

sp500["sp500_cad"] = sp500["sp500_usd"] * sp500["usd_cad"]

sp500 = sp500.merge(cpi[["date", "cpi"]], on="date", how="left")
sp500["cpi"] = sp500["cpi"].ffill()

sp500 = sp500[
    (sp500["date"] >= START_DATE) &
    (sp500["date"] <= END_DATE)
].copy()

sp500["sp500_real"] = sp500["sp500_cad"] / sp500["cpi"] * base_cpi

sp500 = normalize_to_base(
    sp500,
    "sp500_real",
    BASE_DATE,
    "sp500_real_index_1999"
)

print("TSX duplicate months:", tsx["date"].duplicated().sum())
print("S&P 500 duplicate months:", sp500["date"].duplicated().sum())
print("City house duplicate months:", city_house["date"].duplicated().sum())
# ============================================================
# 11. Merge Final Dataset
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

final_df = final_df.merge(
    tsx[
        [
            "date",
            "tsx_cad",
            "tsx_real",
            "tsx_real_index_1999"
        ]
    ],
    on="date",
    how="left"
)

final_df = final_df.merge(
    sp500[
        [
            "date",
            "sp500_usd",
            "usd_cad",
            "sp500_cad",
            "sp500_real",
            "sp500_real_index_1999"
        ]
    ],
    on="date",
    how="left"
)

final_columns = [
    "date",
    "canada_house_real",
    "canada_house_real_index_1999",
    "tsx_cad",
    "tsx_real",
    "tsx_real_index_1999",
    "sp500_usd",
    "usd_cad",
    "sp500_cad",
    "sp500_real",
    "sp500_real_index_1999",
]

for col in city_columns:
    final_columns.extend([
        col,
        f"{col}_real",
        f"{col}_real_index_1999"
    ])

final_df = final_df[final_columns].copy()
final_df = final_df.sort_values("date")


# ============================================================
# 12. Save Final Dataset
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
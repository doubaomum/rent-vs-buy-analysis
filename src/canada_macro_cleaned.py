import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "data"

HOUSE_DIR = BASE_DIR / "processed" / "house"
STOCK_DIR = BASE_DIR / "processed" / "stock"
FX_DIR = BASE_DIR / "external" / "fx"

OUTPUT_DIR = BASE_DIR / "processed" / "final"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

canada_house_path = HOUSE_DIR / "canada_house_index2010=100.csv"
sp500_path = STOCK_DIR / "sp500.csv"
tsx_path = STOCK_DIR / "tsx.csv"
fx_path = FX_DIR / "usd_cad.csv"

START_DATE = "1990-01-01"
END_DATE = "2025-12-01"
BASE_DATE = "1990-01-01"


def standardize_monthly_date(df, date_col="date"):
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).copy()
    df[date_col] = df[date_col].dt.to_period("M").dt.to_timestamp()
    return df


def normalize_to_base(df, value_col, base_date, new_col):
    base_date = pd.to_datetime(base_date)
    base_value = df.loc[df["date"] == base_date, value_col].iloc[0]
    df[new_col] = df[value_col] / base_value * 100
    return df


# ============================================================
# 1. Canada house price index
# ============================================================

canada_house = pd.read_csv(canada_house_path)

canada_house = canada_house.rename(columns={
    "indx": "canada_house_index_2010"
})

canada_house = standardize_monthly_date(canada_house)

canada_house["canada_house_index_2010"] = pd.to_numeric(
    canada_house["canada_house_index_2010"],
    errors="coerce"
)

# Quarterly to monthly
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
    "canada_house_index_2010",
    BASE_DATE,
    "canada_house_index_1990"
)


# ============================================================
# 2. FX: USD to CAD
# ============================================================

fx = pd.read_csv(fx_path)

fx = fx.rename(columns={
    "observation_date": "date",
    "DEXCAUS": "usd_cad"
})

fx = standardize_monthly_date(fx)

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
# 3. TSX
# ============================================================

tsx = pd.read_csv(tsx_path)

tsx = standardize_monthly_date(tsx)

tsx["tsx_cad"] = pd.to_numeric(tsx["tsx_cad"], errors="coerce")

tsx = tsx[
    (tsx["date"] >= START_DATE) &
    (tsx["date"] <= END_DATE)
].copy()

tsx = normalize_to_base(
    tsx,
    "tsx_cad",
    BASE_DATE,
    "tsx_index_1990"
)


# ============================================================
# 4. S&P 500: USD to CAD, then index
# ============================================================

sp500 = pd.read_csv(sp500_path)

sp500 = standardize_monthly_date(sp500)

sp500["sp500_price"] = pd.to_numeric(
    sp500["sp500_price"],
    errors="coerce"
)

sp500 = sp500.rename(columns={
    "sp500_price": "sp500_usd"
})

sp500 = sp500.merge(
    fx[["date", "usd_cad"]],
    on="date",
    how="left"
)

sp500["usd_cad"] = sp500["usd_cad"].ffill()

sp500["sp500_cad"] = sp500["sp500_usd"] * sp500["usd_cad"]

sp500 = sp500[
    (sp500["date"] >= START_DATE) &
    (sp500["date"] <= END_DATE)
].copy()

sp500 = normalize_to_base(
    sp500,
    "sp500_cad",
    BASE_DATE,
    "sp500_index_1990"
)


# ============================================================
# 5. Merge final dataset
# ============================================================

comparison = canada_house[[
    "date",
    "canada_house_index_2010",
    "canada_house_index_1990"
]]

comparison = comparison.merge(
    tsx[["date", "tsx_cad", "tsx_index_1990"]],
    on="date",
    how="left"
)

comparison = comparison.merge(
    sp500[["date", "sp500_usd", "usd_cad", "sp500_cad", "sp500_index_1990"]],
    on="date",
    how="left"
)

comparison = comparison.sort_values("date")

output_path = OUTPUT_DIR / "canada_house_vs_stocks_1990_index.csv"
comparison.to_csv(output_path, index=False)

print("\nDone!")
print(f"Saved to: {output_path}")
print(comparison.head())
print(comparison.tail())
print(comparison.info())
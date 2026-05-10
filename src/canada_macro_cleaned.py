import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "data"

HOUSE_DIR = BASE_DIR / "processed" / "house"
STOCK_DIR = BASE_DIR / "processed" / "stock"
FX_DIR = BASE_DIR / "external" / "fx"
CPI_DIR = BASE_DIR / "external"

OUTPUT_DIR = BASE_DIR / "processed" / "final"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

canada_house_path = HOUSE_DIR / "canada_house_index2010=100.csv"
sp500_path = STOCK_DIR / "sp500.csv"
tsx_path = STOCK_DIR / "tsx.csv"
fx_path = FX_DIR / "usd_cad.csv"
cpi_path = CPI_DIR / "canada_cpi.csv"

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

    base_series = df.loc[df["date"] == base_date, value_col].dropna()
    if base_series.empty:
        raise ValueError(f"No base value found for {value_col} on {base_date.date()}")

    base_value = base_series.iloc[0]
    df[new_col] = df[value_col] / base_value * 100
    return df


# ============================================================
# 1. Canada House Price Index
# The BIS Canada house price index is already real/inflation-adjusted
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

# Convert quarterly data to monthly frequency using forward fill
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

# Normalize Canada house price index to 1990 = 100
canada_house = normalize_to_base(
    canada_house,
    "canada_house_index_2010",
    BASE_DATE,
    "canada_house_real_index"
)


# ============================================================
# ============================================================
# 2. Canada CPI
# CPI is used to convert nominal stock values into real values
# ============================================================

cpi_raw = pd.read_csv(cpi_path)

# Convert CPI data from wide format to long format
cpi = cpi_raw.melt(
    id_vars=["Products and product groups 3 4"],
    var_name="date",
    value_name="cpi"
)

# Keep only CPI values
cpi = cpi.drop(columns=["Products and product groups 3 4"])

# Handle both date formats: Jan-90 and 01-Jan
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

base_cpi = base_cpi_series.iloc[0]gi t

# ============================================================
# 3. USD/CAD Exchange Rate
# Used to convert S&P 500 from USD to CAD
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
# 4. TSX
# Nominal CAD -> Real CAD -> Indexed Growth
# ============================================================

tsx = pd.read_csv(tsx_path)

tsx = standardize_monthly_date(tsx)

tsx["tsx_cad"] = pd.to_numeric(tsx["tsx_cad"], errors="coerce")

tsx = tsx.merge(
    cpi[["date", "cpi"]],
    on="date",
    how="left"
)

tsx["cpi"] = tsx["cpi"].ffill()

# Convert nominal TSX values into inflation-adjusted real values
tsx["tsx_real"] = tsx["tsx_cad"] / tsx["cpi"] * base_cpi

tsx = tsx[
    (tsx["date"] >= START_DATE) &
    (tsx["date"] <= END_DATE)
].copy()

# Normalize real TSX values to 1990 = 100
tsx = normalize_to_base(
    tsx,
    "tsx_real",
    BASE_DATE,
    "tsx_real_index"
)


# ============================================================
# 5. S&P 500
# USD -> CAD -> Real CAD -> Indexed Growth
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

# Convert S&P 500 from USD to CAD
sp500["sp500_cad"] = sp500["sp500_usd"] * sp500["usd_cad"]

sp500 = sp500.merge(
    cpi[["date", "cpi"]],
    on="date",
    how="left"
)

sp500["cpi"] = sp500["cpi"].ffill()

# Convert nominal S&P 500 CAD values into inflation-adjusted real values
sp500["sp500_real"] = sp500["sp500_cad"] / sp500["cpi"] * base_cpi

sp500 = sp500[
    (sp500["date"] >= START_DATE) &
    (sp500["date"] <= END_DATE)
].copy()

# Normalize real S&P 500 values to 1990 = 100
sp500 = normalize_to_base(
    sp500,
    "sp500_real",
    BASE_DATE,
    "sp500_real_index"
)


# ============================================================
# 6. Merge Final Dataset
# ============================================================

comparison = canada_house[[
    "date",
    "canada_house_index_2010",
    "canada_house_real_index"
]]

comparison = comparison.merge(
    tsx[[
        "date",
        "tsx_cad",
        "tsx_real",
        "tsx_real_index"
    ]],
    on="date",
    how="left"
)

comparison = comparison.merge(
    sp500[[
        "date",
        "sp500_usd",
        "usd_cad",
        "sp500_cad",
        "sp500_real",
        "sp500_real_index"
    ]],
    on="date",
    how="left"
)

comparison = comparison.sort_values("date")

output_path = OUTPUT_DIR / "canada_house_vs_stocks_real_1990_index.csv"
comparison.to_csv(output_path, index=False)

print("\nDone!")
print(f"Saved to: {output_path}")
print(comparison.head())
print(comparison.tail())
print(comparison.info())
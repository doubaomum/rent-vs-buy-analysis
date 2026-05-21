import pandas as pd
from pathlib import Path

# ============================================================
# City Housing + Canada Housing + TSX + S&P 500
# Real indexed growth from 1999 to 2025
# Adds CAGR and total growth summary outputs
# ============================================================

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

wide_output_path = OUTPUT_DIR / "city_house_canada_real_1999_index.csv"
long_output_path = OUTPUT_DIR / "city_house_canada_real_1999_long.csv"
summary_output_path = OUTPUT_DIR / "city_house_canada_real_1999_summary.csv"

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


def make_monthly_last(df, value_cols):
    """
    If source data is daily, convert to one row per month using the last
    available observation of each month. If already monthly, this is safe.
    """
    return (
        df.dropna(subset=value_cols)
        .sort_values("date")
        .groupby("date", as_index=False)
        .last()
    )


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


def calculate_summary(long_df):
    """
    Calculates one CAGR and one total-growth value per asset for the full
    selected period. The indexed values already start at 100.
    """
    rows = []

    for asset, group in long_df.dropna(subset=["Value"]).groupby("Attribute"):
        group = group.sort_values("date")

        start_row = group.iloc[0]
        end_row = group.iloc[-1]

        start_value = start_row["Value"]
        end_value = end_row["Value"]
        start_date = start_row["date"]
        end_date = end_row["date"]

        years = (end_date - start_date).days / 365.25

        if start_value > 0 and years > 0:
            cagr = (end_value / start_value) ** (1 / years) - 1
            total_growth = end_value / start_value - 1
        else:
            cagr = pd.NA
            total_growth = pd.NA

        rows.append({
            "Attribute": asset,
            "start_date": start_date,
            "end_date": end_date,
            "start_value": start_value,
            "end_value": end_value,
            "years": years,
            "cagr": cagr,
            "total_growth": total_growth,
        })

    return pd.DataFrame(rows)

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
city_house = city_house.rename(columns={"time": "date"})
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

city_house = city_house.merge(cpi[["date", "cpi"]], on="date", how="left")
city_house["cpi"] = city_house["cpi"].ffill()

city_house = city_house[
    (city_house["date"] >= START_DATE) &
    (city_house["date"] <= END_DATE)
].copy()

for col in city_columns:
    real_col = f"{col}_real"
    index_col = f"{col}_real_index_1999"

    city_house[real_col] = city_house[col] / city_house["cpi"] * base_cpi
    city_house = normalize_to_base(city_house, real_col, BASE_DATE, index_col)

# ============================================================
# 7. Load Canada National Housing Index
# BIS Canada series is already real/inflation-adjusted
# ============================================================

canada_house = pd.read_csv(canada_house_path)

if "TIME_PERIOD" in canada_house.columns:
    canada_house = canada_house.rename(columns={
        "TIME_PERIOD": "date",
        "OBS_VALUE": "canada_house_real"
    })
elif "indx" in canada_house.columns:
    canada_house = canada_house.rename(columns={"indx": "canada_house_real"})

if "time" in canada_house.columns:
    canada_house = canada_house.rename(columns={"time": "date"})

canada_house = standardize_monthly_date(canada_house, "date")
canada_house["canada_house_real"] = pd.to_numeric(
    canada_house["canada_house_real"], errors="coerce"
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
fx = fx.rename(columns={"observation_date": "date", "DEXCAUS": "usd_cad"})
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
# 9. TSX: Nominal CAD -> Monthly Real CAD -> 1999 Index
# ============================================================

tsx = pd.read_csv(tsx_path)
tsx = standardize_monthly_date(tsx, "date")

tsx["tsx_cad"] = (
    tsx["tsx_cad"]
    .astype(str)
    .str.replace(",", "", regex=False)
)
tsx["tsx_cad"] = pd.to_numeric(tsx["tsx_cad"], errors="coerce")
tsx = make_monthly_last(tsx, ["tsx_cad"])

tsx = tsx.merge(cpi[["date", "cpi"]], on="date", how="left")
tsx["cpi"] = tsx["cpi"].ffill()
tsx["tsx_real"] = tsx["tsx_cad"] / tsx["cpi"] * base_cpi

tsx = tsx[
    (tsx["date"] >= START_DATE) &
    (tsx["date"] <= END_DATE)
].copy()

tsx = normalize_to_base(tsx, "tsx_real", BASE_DATE, "tsx_real_index_1999")

# ============================================================
# 10. S&P 500: USD -> CAD -> Real CAD -> 1999 Index
# ============================================================

sp500 = pd.read_csv(sp500_path)
sp500 = standardize_monthly_date(sp500, "date")

sp500["sp500_price"] = (
    sp500["sp500_price"]
    .astype(str)
    .str.replace(",", "", regex=False)
)
sp500["sp500_price"] = pd.to_numeric(sp500["sp500_price"], errors="coerce")
sp500 = sp500.rename(columns={"sp500_price": "sp500_usd"})
sp500 = make_monthly_last(sp500, ["sp500_usd"])

sp500 = sp500.merge(fx[["date", "usd_cad"]], on="date", how="left")
sp500["usd_cad"] = sp500["usd_cad"].ffill()
sp500["sp500_cad"] = sp500["sp500_usd"] * sp500["usd_cad"]

sp500 = sp500.merge(cpi[["date", "cpi"]], on="date", how="left")
sp500["cpi"] = sp500["cpi"].ffill()
sp500["sp500_real"] = sp500["sp500_cad"] / sp500["cpi"] * base_cpi

sp500 = sp500[
    (sp500["date"] >= START_DATE) &
    (sp500["date"] <= END_DATE)
].copy()

sp500 = normalize_to_base(
    sp500,
    "sp500_real",
    BASE_DATE,
    "sp500_real_index_1999"
)

# ============================================================
# 11. Merge Final Wide Dataset
# ============================================================

final_df = city_house.merge(
    canada_house[["date", "canada_house_real", "canada_house_real_index_1999"]],
    on="date",
    how="left"
)

final_df = final_df.merge(
    tsx[["date", "tsx_cad", "tsx_real", "tsx_real_index_1999"]],
    on="date",
    how="left"
)

final_df = final_df.merge(
    sp500[["date", "sp500_usd", "usd_cad", "sp500_cad", "sp500_real", "sp500_real_index_1999"]],
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
    final_columns.extend([col, f"{col}_real", f"{col}_real_index_1999"])

final_df = final_df[final_columns].copy().sort_values("date")

# ============================================================
# 12. Create Long Dataset for Power BI
# ============================================================

index_columns = [
    "canada_house_real_index_1999",
    "tsx_real_index_1999",
    "sp500_real_index_1999",
] + [f"{col}_real_index_1999" for col in city_columns]

long_df = final_df.melt(
    id_vars=["date"],
    value_vars=index_columns,
    var_name="Attribute",
    value_name="Value"
)

asset_name_map = {
    "canada_house_real_index_1999": "Canada",
    "tsx_real_index_1999": "TSX",
    "sp500_real_index_1999": "S&P 500(CAD)",
    "bc_vancouver_real_index_1999": "Vancouver",
    "on_toronto_real_index_1999": "Toronto",
    "qc_montreal_real_index_1999": "Montreal",
    "ab_calgary_real_index_1999": "Calgary",
    "on_ottawa_real_index_1999": "Ottawa",
    "ab_edmonton_real_index_1999": "Edmonton",
}

long_df["Attribute"] = long_df["Attribute"].map(asset_name_map)
long_df = long_df.dropna(subset=["Attribute", "Value"]).copy()

# ============================================================
# 13. Create Holding-Period CAGR Dataset
# ============================================================

START_YEARS = [2000, 2005, 2010, 2015, 2020]
HOLDING_PERIODS = [5, 10, 15, 20, 25]

holding_outputs = []

for start_year in START_YEARS:

    start_date = pd.to_datetime(f"{start_year}-01-01")

    for holding_period in HOLDING_PERIODS:

        end_year = start_year + holding_period

        if end_year > 2025:
            continue

        end_date = pd.to_datetime(f"{end_year}-12-01")

        temp_df = long_df[
            (long_df["date"] >= start_date) &
            (long_df["date"] <= end_date)
        ].copy()

        for asset, group in temp_df.groupby("Attribute"):

            group = group.sort_values("date")

            if len(group) < 2:
                continue

            start_value = group.iloc[0]["Value"]
            end_value = group.iloc[-1]["Value"]

            years = holding_period

            if (
                pd.notna(start_value)
                and pd.notna(end_value)
                and start_value > 0
            ):

                cagr = (
                    (end_value / start_value) ** (1 / years)
                ) - 1

                total_growth = (
                    end_value / start_value
                ) - 1

                holding_outputs.append({

                    "start_year": start_year,

                    "holding_period": holding_period,

                    "end_year": end_year,

                    "start_date": start_date,

                    "end_date": end_date,

                    "Attribute": asset,

                    "start_value": start_value,

                    "end_value": end_value,

                    "total_growth": total_growth,

                    "cagr": cagr
                })

# Final holding-period summary table
summary_df = pd.DataFrame(holding_outputs)

summary_df = summary_df.sort_values([
    "start_year",
    "holding_period",
    "Attribute"
])

# ============================================================
# 14. Save Outputs
# ============================================================

final_df.to_csv(wide_output_path, index=False)
long_df.to_csv(long_output_path, index=False)
summary_df.to_csv(summary_output_path, index=False)

print("\nDone!")
print(f"Saved wide dataset to: {wide_output_path}")
print(f"Saved long dataset to: {long_output_path}")
print(f"Saved CAGR summary to: {summary_output_path}")
print("\nCAGR Summary:")
print(summary_df[["Attribute", "cagr", "total_growth"]])
print("\nWide info:")
print(final_df.info())
print("\nLong info:")
print(long_df.info())

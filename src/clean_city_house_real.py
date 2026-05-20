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

output_path = OUTPUT_DIR / "city_house_canada_stock_holding_period.csv"

# ============================================================
# 2. Dynamic Start Year + Holding Period
# ============================================================

START_YEARS = [2000, 2005, 2010, 2015, 2020]
HOLDING_PERIODS = [5, 10, 15, 20, 25]
FINAL_YEAR = 2025


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


def make_monthly_last(df, value_cols):
    return (
        df.dropna(subset=value_cols)
        .sort_values("date")
        .groupby("date", as_index=False)
        .last()
    )


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
# 6. Convert City Nominal Indexes to Real Values
# ============================================================

city_house = city_house.merge(
    cpi[["date", "cpi"]],
    on="date",
    how="left"
)

city_house["cpi"] = city_house["cpi"].ffill()

for col in city_columns:
    real_col = f"{col}_real"
    city_house[real_col] = city_house[col] / city_house["cpi"]


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
# 9. TSX: Daily/Monthly Nominal CAD -> Monthly Real CAD
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

tsx = tsx.merge(
    cpi[["date", "cpi"]],
    on="date",
    how="left"
)

tsx["cpi"] = tsx["cpi"].ffill()
tsx["tsx_real"] = tsx["tsx_cad"] / tsx["cpi"]


# ============================================================
# 10. S&P 500: Daily/Monthly USD -> Monthly CAD -> Real CAD
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

sp500 = make_monthly_last(sp500, ["sp500_usd"])

sp500 = sp500.merge(
    fx[["date", "usd_cad"]],
    on="date",
    how="left"
)

sp500["usd_cad"] = sp500["usd_cad"].ffill()

sp500["sp500_cad"] = sp500["sp500_usd"] * sp500["usd_cad"]

sp500 = sp500.merge(
    cpi[["date", "cpi"]],
    on="date",
    how="left"
)

sp500["cpi"] = sp500["cpi"].ffill()
sp500["sp500_real"] = sp500["sp500_cad"] / sp500["cpi"]


# ============================================================
# 11. Dynamic Scenario Generation
# ============================================================

all_results = []

for start_year in START_YEARS:

    for holding_period in HOLDING_PERIODS:

        end_year = start_year + holding_period

        if end_year > FINAL_YEAR:
            continue

        start_date = pd.to_datetime(f"{start_year}-01-01")
        end_date = pd.to_datetime(f"{end_year}-12-01")
        base_date = start_date

        # ----------------------------------------------------
        # Canada Housing
        # ----------------------------------------------------

        canada_filtered = canada_house[
            (canada_house["date"] >= start_date) &
            (canada_house["date"] <= end_date)
        ].copy()

        canada_filtered = normalize_to_base(
            canada_filtered,
            "canada_house_real",
            base_date,
            "canada_house_real_index"
        )

        # ----------------------------------------------------
        # TSX
        # ----------------------------------------------------

        tsx_filtered = tsx[
            (tsx["date"] >= start_date) &
            (tsx["date"] <= end_date)
        ].copy()

        tsx_filtered = normalize_to_base(
            tsx_filtered,
            "tsx_real",
            base_date,
            "tsx_real_index"
        )

        # ----------------------------------------------------
        # S&P 500
        # ----------------------------------------------------

        sp500_filtered = sp500[
            (sp500["date"] >= start_date) &
            (sp500["date"] <= end_date)
        ].copy()

        sp500_filtered = normalize_to_base(
            sp500_filtered,
            "sp500_real",
            base_date,
            "sp500_real_index"
        )

        # ----------------------------------------------------
        # City Housing
        # ----------------------------------------------------

        city_filtered = city_house[
            (city_house["date"] >= start_date) &
            (city_house["date"] <= end_date)
        ].copy()

        for col in city_columns:
            real_col = f"{col}_real"
            index_col = f"{col}_real_index"

            city_filtered = normalize_to_base(
                city_filtered,
                real_col,
                base_date,
                index_col
            )

        # ----------------------------------------------------
        # Merge Scenario
        # ----------------------------------------------------

        scenario_df = canada_filtered[
            [
                "date",
                "canada_house_real_index"
            ]
        ].copy()

        scenario_df = scenario_df.merge(
            tsx_filtered[
                [
                    "date",
                    "tsx_real_index"
                ]
            ],
            on="date",
            how="left"
        )

        scenario_df = scenario_df.merge(
            sp500_filtered[
                [
                    "date",
                    "sp500_real_index"
                ]
            ],
            on="date",
            how="left"
        )

        city_index_columns = [
            f"{col}_real_index"
            for col in city_columns
        ]

        scenario_df = scenario_df.merge(
            city_filtered[
                ["date"] + city_index_columns
            ],
            on="date",
            how="left"
        )

        # ----------------------------------------------------
        # Add Metadata
        # ----------------------------------------------------

        scenario_df["start_year"] = start_year
        scenario_df["holding_period"] = holding_period
        scenario_df["end_year"] = end_year
        scenario_df["scenario_label"] = f"{start_year} + {holding_period}Y"

        all_results.append(scenario_df)


# ============================================================
# 12. Combine All Scenarios
# ============================================================

final_df = pd.concat(all_results, ignore_index=True)

# ============================================================
# 13. Unpivot for Power BI
# ============================================================

asset_columns = [
    "canada_house_real_index",
    "tsx_real_index",
    "sp500_real_index",
]

city_index_columns = [
    f"{col}_real_index"
    for col in city_columns
]

final_df = final_df.melt(
    id_vars=[
        "date",
        "start_year",
        "holding_period",
        "end_year",
        "scenario_label"
    ],
    value_vars=asset_columns + city_index_columns,
    var_name="Attribute",
    value_name="Value"
)

asset_name_map = {
    "canada_house_real_index": "Canada Housing",
    "tsx_real_index": "TSX",
    "sp500_real_index": "S&P 500 (CAD)",
    "bc_vancouver_real_index": "Vancouver",
    "on_toronto_real_index": "Toronto",
    "qc_montreal_real_index": "Montreal",
    "ab_calgary_real_index": "Calgary",
    "on_ottawa_real_index": "Ottawa",
    "ab_edmonton_real_index": "Edmonton",
}

final_df["asset"] = final_df["Attribute"].map(asset_name_map)

# ============================================================
# 14. Save
# ============================================================

final_df.to_csv(output_path, index=False)

parameter_table = []

for start_year in START_YEARS:
    for holding_period in HOLDING_PERIODS:
        end_year = start_year + holding_period
        if end_year <= FINAL_YEAR:
            parameter_table.append({
                "start_year": start_year,
                "holding_period": holding_period,
                "end_year": end_year,
                "scenario_label": f"{start_year} + {holding_period}Y"
            })

parameter_df = pd.DataFrame(parameter_table)

parameter_output_path = OUTPUT_DIR / "start_year_holding_period_city_parameter.csv"
parameter_df.to_csv(parameter_output_path, index=False)

print("\nDone!")
print(f"Saved main dataset to: {output_path}")
print(f"Saved parameter table to: {parameter_output_path}")
print("\nPreview:")
print(final_df.head())

print("\nInfo:")
print(final_df.info())
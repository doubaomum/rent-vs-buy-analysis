import pandas as pd
from pathlib import Path

# ============================================================
# Canada Housing vs TSX vs S&P 500
# Output supports Power BI Start Year + Holding Period slicers
# ============================================================

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

# Power BI slicer options
START_YEARS = [1990, 1995, 2000, 2005, 2010, 2015, 2020]
HOLDING_PERIODS = [5, 10, 15, 20, 25, 30, 35]
MAX_END_YEAR = 2025
MAX_END_DATE = pd.to_datetime(f"{MAX_END_YEAR}-12-01")


def standardize_monthly_date(df, date_col="date"):
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).copy()
    df[date_col] = df[date_col].dt.to_period("M").dt.to_timestamp()
    return df


def make_monthly_last(df, value_cols):
    """
    If stock data is daily, convert it to one row per month using the
    last available observation of each month. If it is already monthly,
    this keeps it monthly.
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
        raise ValueError(f"No base value found for {value_col} on {base_date.date()}")

    base_value = base_series.iloc[0]
    df[new_col] = df[value_col] / base_value * 100
    return df


def calc_cagr(start_value, end_value, years):
    if pd.isna(start_value) or pd.isna(end_value) or start_value <= 0 or years <= 0:
        return pd.NA
    return (end_value / start_value) ** (1 / years) - 1


# ============================================================
# 1. Canada House Price Index
# BIS Canada house price index is already real/inflation-adjusted
# ============================================================

canada_house = pd.read_csv(canada_house_path)

canada_house = canada_house.rename(columns={
    "indx": "canada_house_index_2010",
    "TIME_PERIOD": "date",
    "OBS_VALUE": "canada_house_index_2010",
    "time": "date"
})

canada_house = standardize_monthly_date(canada_house, "date")
canada_house["canada_house_index_2010"] = pd.to_numeric(
    canada_house["canada_house_index_2010"],
    errors="coerce"
)

canada_house = (
    canada_house
    .set_index("date")
    .resample("MS")
    .ffill()
    .reset_index()
)

canada_house = canada_house[canada_house["date"] <= MAX_END_DATE].copy()


# ============================================================
# 2. Canada CPI
# Used to convert nominal stock values into real values
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
cpi = cpi[cpi["date"] <= MAX_END_DATE].copy()


# ============================================================
# 3. USD/CAD Exchange Rate
# Used to convert S&P 500 from USD to CAD
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
fx = fx[fx["date"] <= MAX_END_DATE].copy()


# ============================================================
# 4. TSX: Nominal CAD data
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
tsx = tsx[tsx["date"] <= MAX_END_DATE].copy()


# ============================================================
# 5. S&P 500: USD data
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
sp500 = sp500[sp500["date"] <= MAX_END_DATE].copy()


# ============================================================
# 6. Build one dataset for each Start Year + Holding Period
# ============================================================

all_outputs = []
summary_outputs = []
valid_slicer_rows = []

for start_year in START_YEARS:
    start_date = pd.to_datetime(f"{start_year}-01-01")

    base_cpi_series = cpi.loc[cpi["date"] == start_date, "cpi"].dropna()
    if base_cpi_series.empty:
        print(f"Skipping {start_year}: no CPI value found on {start_date.date()}")
        continue

    base_cpi = base_cpi_series.iloc[0]

    for holding_period in HOLDING_PERIODS:
        end_year = start_year + holding_period

        # Only keep complete holding periods available by MAX_END_YEAR.
        if end_year > MAX_END_YEAR:
            continue

        end_date = pd.to_datetime(f"{end_year}-12-01")

        valid_slicer_rows.append({
            "start_year": start_year,
            "holding_period": holding_period,
            "end_year": end_year,
            "start_date": start_date,
            "end_date": end_date,
            "scenario_label": f"{start_year} + {holding_period}Y ({end_year})"
        })

        # Canada housing: already real. Only filter and normalize.
        house_part = canada_house[
            (canada_house["date"] >= start_date) &
            (canada_house["date"] <= end_date)
        ][["date", "canada_house_index_2010"]].copy()

        house_part = normalize_to_base(
            house_part,
            "canada_house_index_2010",
            start_date,
            "canada_house_real_index"
        )

        # TSX: nominal CAD -> real CAD -> indexed to selected start year
        tsx_part = tsx[
            (tsx["date"] >= start_date) &
            (tsx["date"] <= end_date)
        ].copy()

        tsx_part = tsx_part.merge(cpi[["date", "cpi"]], on="date", how="left")
        tsx_part["cpi"] = tsx_part["cpi"].ffill()
        tsx_part["tsx_real"] = tsx_part["tsx_cad"] / tsx_part["cpi"] * base_cpi

        tsx_part = normalize_to_base(
            tsx_part,
            "tsx_real",
            start_date,
            "tsx_real_index"
        )

        # S&P 500: USD -> CAD -> real CAD -> indexed to selected start year
        sp500_part = sp500[
            (sp500["date"] >= start_date) &
            (sp500["date"] <= end_date)
        ].copy()

        sp500_part = sp500_part.merge(cpi[["date", "cpi"]], on="date", how="left")
        sp500_part["cpi"] = sp500_part["cpi"].ffill()
        sp500_part["sp500_real"] = sp500_part["sp500_cad"] / sp500_part["cpi"] * base_cpi

        sp500_part = normalize_to_base(
            sp500_part,
            "sp500_real",
            start_date,
            "sp500_real_index"
        )

        # Merge final comparison for this scenario
        comparison = house_part.merge(
            tsx_part[["date", "tsx_cad", "tsx_real", "tsx_real_index"]],
            on="date",
            how="left"
        )

        comparison = comparison.merge(
            sp500_part[[
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

        comparison["start_year"] = start_year
        comparison["holding_period"] = holding_period
        comparison["end_year"] = end_year
        comparison["base_date"] = start_date
        comparison["end_date"] = end_date
        comparison["scenario_label"] = f"{start_year} + {holding_period}Y ({end_year})"

        all_outputs.append(comparison)

        # Summary row for final value and CAGR comparison
        final_row = comparison.loc[comparison["date"] == end_date]
        if not final_row.empty:
            final_row = final_row.iloc[0]
            summary_outputs.append({
                "start_year": start_year,
                "holding_period": holding_period,
                "end_year": end_year,
                "start_date": start_date,
                "end_date": end_date,
                "scenario_label": f"{start_year} + {holding_period}Y ({end_year})",
                "canada_house_final_index": final_row["canada_house_real_index"],
                "tsx_final_index": final_row["tsx_real_index"],
                "sp500_final_index": final_row["sp500_real_index"],
                "canada_house_cagr": calc_cagr(100, final_row["canada_house_real_index"], holding_period),
                "tsx_cagr": calc_cagr(100, final_row["tsx_real_index"], holding_period),
                "sp500_cagr": calc_cagr(100, final_row["sp500_real_index"], holding_period),
            })


# ============================================================
# 7. Save Final Datasets
# ============================================================

if not all_outputs:
    raise ValueError("No valid start year + holding period combinations were generated.")

final_df = pd.concat(all_outputs, ignore_index=True)
final_df = final_df.sort_values(["start_year", "holding_period", "date"])

summary_df = pd.DataFrame(summary_outputs).sort_values(["start_year", "holding_period"])
slicer_df = pd.DataFrame(valid_slicer_rows).sort_values(["start_year", "holding_period"])

output_path = OUTPUT_DIR / "canada_house_vs_stocks_real_holding_period_slicer.csv"
summary_output_path = OUTPUT_DIR / "canada_house_vs_stocks_holding_period_summary.csv"
slicer_output_path = OUTPUT_DIR / "start_year_holding_period_parameter.csv"

final_df.to_csv(output_path, index=False)
summary_df.to_csv(summary_output_path, index=False)
slicer_df.to_csv(slicer_output_path, index=False)

print("\nDone!")
print(f"Saved main dataset to: {output_path}")
print(f"Saved summary dataset to: {summary_output_path}")
print(f"Saved slicer table to: {slicer_output_path}")

print("\nValid slicer combinations:")
print(slicer_df)

print("\nPreview:")
print(final_df.head())

print("\nTail:")
print(final_df.tail())

print("\nSummary preview:")
print(summary_df.head())

print("\nInfo:")
print(final_df.info())

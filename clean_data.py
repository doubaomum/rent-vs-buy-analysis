import pandas as pd
from pathlib import Path

# ============================================================
# 1. Define file paths
# ============================================================
# Use pathlib instead of plain strings.
# This makes file paths cleaner and easier to manage across the project.

RAW_DIR = Path("raw_data/pre_cleaned_data")
OUTPUT_DIR = Path("data_cleaned")

# Make sure the output folder exists.
# If it does not exist, Python will create it automatically.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# House price data
canada_house_path = RAW_DIR / "house" / "canada_house.csv"
city_house_path = RAW_DIR / "house" / "city_house.csv"

# Stock market data
tsx_path = RAW_DIR / "stock" / "tsx.csv"
sp500_path = RAW_DIR / "stock" / "sp500.csv"
vt_path = RAW_DIR / "stock" / "vt.csv"

# Foreign exchange data
fx_path = RAW_DIR / "fx" / "usd_cad.csv"

# Rent and vacancy data folder
rent_folder = RAW_DIR / "rent"

# Rent and vacancy files for Canada and six major cities
rent_paths = {
    "canada": (
        rent_folder / "canada_rent.csv",
        rent_folder / "canada_vacancy.csv"
    ),
    "toronto": (
        rent_folder / "toronto_rent.csv",
        rent_folder / "toronto_vacancy.csv"
    ),
    "vancouver": (
        rent_folder / "vancouver_rent.csv",
        rent_folder / "vancouver_vacancy.csv"
    ),
    "calgary": (
        rent_folder / "calgary_rent.csv",
        rent_folder / "calgary_vacancy.csv"
    ),
    "ottawa": (
        rent_folder / "ottawa_rent.csv",
        rent_folder / "ottawa_vacancy.csv"
    ),
    "montreal": (
        rent_folder / "montreal_rent.csv",
        rent_folder / "montreal_vacancy.csv"
    ),
    "edmonton": (
        rent_folder / "edmonton_rent.csv",
        rent_folder / "edmonton_vacancy.csv"
    ),
}

# Define the analysis period.
# This ensures all datasets are aligned to the same time range.
START_DATE = "1999-01-01"
END_DATE = "2025-12-01"


# ============================================================
# 2. Helper function: standardize monthly date
# ============================================================
def standardize_monthly_date(df, date_col):
    """
    Convert a date column into pandas datetime format,
    then standardize it to the first day of each month.

    Example:
    1999-03-31 -> 1999-03-01
    1999-03-15 -> 1999-03-01

    This is important because different datasets may use different
    day values within the same month.
    """
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df[date_col] = df[date_col].dt.to_period("M").dt.to_timestamp()
    return df


# ============================================================
# 3. Clean Canada and city-level house price data
# ============================================================

# Canada national house price index
canada_house = pd.read_csv(canada_house_path)

# Rename columns to clear and project-friendly names
canada_house = canada_house.rename(columns={
    "TIME_PERIOD": "date",
    "OBS_VALUE": "canada_house_index"
})

# Convert quarterly dates to monthly format
canada_house = standardize_monthly_date(canada_house, "date")

# Convert house index to numeric format
canada_house["canada_house_index"] = pd.to_numeric(
    canada_house["canada_house_index"],
    errors="coerce"
)

# City-level house price index
city_house = pd.read_csv(city_house_path)

city_house = city_house.rename(columns={
    "Transaction Date": "date"
})

city_house = standardize_monthly_date(city_house, "date")

# Merge city-level and Canada-level house price index data
# City data is monthly, while Canada data is quarterly.
# A left merge keeps all city monthly observations.
house_cleaned = city_house.merge(canada_house, on="date", how="left")

# Forward-fill Canada house index because it is quarterly.
# This assigns the latest available quarterly value to the following months.
house_cleaned["canada_house_index"] = house_cleaned["canada_house_index"].ffill()

# Filter to the project analysis period
house_cleaned = house_cleaned[
    (house_cleaned["date"] >= START_DATE) &
    (house_cleaned["date"] <= END_DATE)
]

house_cleaned.to_csv(OUTPUT_DIR / "house_price_cleaned.csv", index=False)


# ============================================================
# 4. Clean stock market and FX data
# ============================================================

# ----------------------------
# 4.1 TSX Composite Index
# ----------------------------
tsx = pd.read_csv(tsx_path)

tsx = standardize_monthly_date(tsx, "date")

# TSX data is already denominated in Canadian dollars.
tsx["tsx_cad"] = pd.to_numeric(tsx["tsx_cad"], errors="coerce")


# ----------------------------
# 4.2 S&P 500 Index
# ----------------------------
sp500 = pd.read_csv(sp500_path)

sp500 = sp500.rename(columns={
    "Date": "date",
    "Close/us dollar": "sp500_usd"
})

sp500 = standardize_monthly_date(sp500, "date")

sp500["sp500_usd"] = pd.to_numeric(sp500["sp500_usd"], errors="coerce")


# ----------------------------
# 4.3 VT Global Stock ETF
# ----------------------------
# VT file has no header, so column names are assigned manually.
vt = pd.read_csv(vt_path, header=None, names=["date", "vt_usd"])

vt = standardize_monthly_date(vt, "date")

vt["vt_usd"] = pd.to_numeric(vt["vt_usd"], errors="coerce")


# ----------------------------
# 4.4 USD/CAD exchange rate
# ----------------------------
fx = pd.read_csv(fx_path)

fx = fx.rename(columns={
    "observation_date": "date",
    "DEXCAUS": "usd_cad"
})

fx["date"] = pd.to_datetime(fx["date"], errors="coerce")
fx["usd_cad"] = pd.to_numeric(fx["usd_cad"], errors="coerce")

# Convert daily FX data to monthly average exchange rate.
# This makes FX data compatible with monthly stock data.
fx = fx.set_index("date").resample("MS").mean().reset_index()

# Merge stock and FX data
stock_cleaned = tsx.merge(sp500, on="date", how="left")
stock_cleaned = stock_cleaned.merge(vt, on="date", how="left")
stock_cleaned = stock_cleaned.merge(fx[["date", "usd_cad"]], on="date", how="left")

# Forward-fill missing exchange rates if any monthly value is missing.
stock_cleaned["usd_cad"] = stock_cleaned["usd_cad"].ffill()

# Convert USD-denominated assets into CAD.
# This allows comparison from a Canadian investor's perspective.
stock_cleaned["sp500_cad"] = stock_cleaned["sp500_usd"] * stock_cleaned["usd_cad"]
stock_cleaned["vt_cad"] = stock_cleaned["vt_usd"] * stock_cleaned["usd_cad"]

stock_cleaned = stock_cleaned[
    (stock_cleaned["date"] >= START_DATE) &
    (stock_cleaned["date"] <= END_DATE)
]

stock_cleaned.to_csv(OUTPUT_DIR / "stock_cleaned.csv", index=False)


# ============================================================
# 5. Clean rent and vacancy data
# ============================================================

def clean_rent_city(city, rent_file, vacancy_file):
    """
    Clean rent and vacancy data for one city.

    Each city has two separate CSV files:
    1. Average rent file
    2. Vacancy rate file

    The function:
    - reads both files
    - standardizes column names
    - extracts the Total column
    - converts dates
    - converts values to numeric format
    - merges rent and vacancy into one city-level dataframe
    - converts annual October data into monthly data using forward-fill
    """

    # CMHC files may contain special characters, so cp1252 is safer than default utf-8.
    rent = pd.read_csv(rent_file, encoding="cp1252")
    vacancy = pd.read_csv(vacancy_file, encoding="cp1252")

    # Remove leading/trailing spaces from column names.
    rent.columns = rent.columns.str.strip()
    vacancy.columns = vacancy.columns.str.strip()

    # Print columns for debugging.
    # This helps confirm that the expected "Total" column exists.
    print(f"\nProcessing {city}")
    print("Rent columns:", rent.columns.tolist())
    print("Vacancy columns:", vacancy.columns.tolist())

    # Rename the first column as date.
    # In CMHC exports, the first column usually contains the time period.
    rent = rent.rename(columns={
        rent.columns[0]: "date",
        "Total": f"{city}_rent"
    })

    vacancy = vacancy.rename(columns={
        vacancy.columns[0]: "date",
        "Total": f"{city}_vacancy"
    })

    # Keep only the date and total columns.
    # The Total column is used as the main rent/vacancy indicator.
    rent = rent[["date", f"{city}_rent"]]
    vacancy = vacancy[["date", f"{city}_vacancy"]]

    # Convert date columns to monthly timestamp format.
    rent = standardize_monthly_date(rent, "date")
    vacancy = standardize_monthly_date(vacancy, "date")

    # Convert rent and vacancy values to numeric format.
    # Non-numeric values will become NaN.
    rent[f"{city}_rent"] = pd.to_numeric(rent[f"{city}_rent"], errors="coerce")
    vacancy[f"{city}_vacancy"] = pd.to_numeric(vacancy[f"{city}_vacancy"], errors="coerce")

    # Merge rent and vacancy data for the same city.
    df_city = rent.merge(vacancy, on="date", how="left")

    # CMHC rent data is annual, usually reported in October.
    # To align with monthly house price and stock data, the annual value
    # is forward-filled to monthly frequency.
    #
    # Example:
    # Oct-2020 rent value is used for Nov-2020, Dec-2020, etc.,
    # until the next annual observation becomes available.
    df_city = df_city.set_index("date").resample("MS").ffill().reset_index()

    return df_city


# Clean and merge rent/vacancy data for all cities
rent_cleaned = None

for city, (rent_file, vacancy_file) in rent_paths.items():
    city_df = clean_rent_city(city, rent_file, vacancy_file)

    if rent_cleaned is None:
        rent_cleaned = city_df
    else:
        rent_cleaned = rent_cleaned.merge(city_df, on="date", how="outer")

rent_cleaned = rent_cleaned.sort_values("date")

rent_cleaned = rent_cleaned[
    (rent_cleaned["date"] >= START_DATE) &
    (rent_cleaned["date"] <= END_DATE)
]

rent_cleaned.to_csv(OUTPUT_DIR / "rent_cleaned.csv", index=False)


# ============================================================
# 6. Combine all cleaned datasets
# ============================================================

# Merge house price, stock market, FX-adjusted stock data, rent, and vacancy data.
# The final dataset is organized by monthly date.
market_data_all = house_cleaned.merge(stock_cleaned, on="date", how="left")
market_data_all = market_data_all.merge(rent_cleaned, on="date", how="left")

market_data_all.to_csv(OUTPUT_DIR / "market_data_all_cleaned.csv", index=False)


# ============================================================
# 7. Check output
# ============================================================

print("\n==============================")
print("house_price_cleaned.csv")
print(house_cleaned.head())
print(house_cleaned.info())

print("\n==============================")
print("stock_cleaned.csv")
print(stock_cleaned.head())
print(stock_cleaned.info())

print("\n==============================")
print("rent_cleaned.csv")
print(rent_cleaned.head())
print(rent_cleaned.info())

print("\n==============================")
print("market_data_all_cleaned.csv")
print(market_data_all.head())
print(market_data_all.info())

print("\nDone! Four cleaned CSV files saved.")
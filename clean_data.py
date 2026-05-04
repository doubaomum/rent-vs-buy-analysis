import pandas as pd

# File paths
canada_house_path = "raw_data/pre_cleaned_data/house/canada_house.csv"
city_house_path = "raw_data/pre_cleaned_data/house/city_house.csv"
tsx_path = "raw_data/pre_cleaned_data/stock/tsx.csv"
sp500_path = "raw_data/pre_cleaned_data/stock/sp500.csv"
vt_path = "raw_data/pre_cleaned_data/stock/vt.csv"
fx_path = "raw_data/pre_cleaned_data/fx/usd_cad.csv"

# Canada house price index
canada_house = pd.read_csv(canada_house_path)
canada_house = canada_house.rename(columns={
    "TIME_PERIOD": "date",
    "OBS_VALUE": "canada_house_index"
})
canada_house["date"] = pd.to_datetime(canada_house["date"])
canada_house["date"] = canada_house["date"].dt.to_period("M").dt.to_timestamp()

# City house price index
city_house = pd.read_csv(city_house_path)
city_house = city_house.rename(columns={
    "Transaction Date": "date"
})
city_house["date"] = pd.to_datetime(city_house["date"])
city_house["date"] = city_house["date"].dt.to_period("M").dt.to_timestamp()

# TSX
tsx = pd.read_csv(tsx_path)

tsx["date"] = pd.to_datetime(tsx["date"])
tsx["date"] = tsx["date"].dt.to_period("M").dt.to_timestamp()

tsx["tsx_cad"] = pd.to_numeric(tsx["tsx_cad"], errors="coerce")

# S&P 500
sp500 = pd.read_csv(sp500_path)
sp500 = sp500.rename(columns={
    "Date": "date",
    "Close/us dollar": "sp500_usd"
})
sp500["date"] = pd.to_datetime(sp500["date"])
sp500["date"] = sp500["date"].dt.to_period("M").dt.to_timestamp()

# VT
vt = pd.read_csv(vt_path, header=None, names=["date", "vt_usd"])
vt["date"] = pd.to_datetime(vt["date"])
vt["date"] = vt["date"].dt.to_period("M").dt.to_timestamp()

# USD/CAD exchange rate from FRED
fx = pd.read_csv(fx_path)

fx = fx.rename(columns={
    "observation_date": "date",
    "DEXCAUS": "usd_cad"
})

fx["date"] = pd.to_datetime(fx["date"])
fx["usd_cad"] = pd.to_numeric(fx["usd_cad"], errors="coerce")

# Convert daily FX data to monthly average
fx = fx.set_index("date").resample("MS").mean().reset_index()

# Merge all datasets
df = city_house.merge(canada_house, on="date", how="left")
df = df.merge(tsx, on="date", how="left")
df = df.merge(sp500, on="date", how="left")
df = df.merge(vt, on="date", how="left")
df = df.merge(fx[["date", "usd_cad"]], on="date", how="left")

# Fill quarterly Canada house data into monthly rows
df["canada_house_index"] = df["canada_house_index"].ffill()

# Fill missing FX values if needed
df["usd_cad"] = df["usd_cad"].ffill()

# Convert USD assets to CAD
df["sp500_cad"] = df["sp500_usd"] * df["usd_cad"]
df["vt_cad"] = df["vt_usd"] * df["usd_cad"]

# Filter date range
df = df[(df["date"] >= "1999-01-01") & (df["date"] <= "2025-12-01")]

# Save
df.to_csv("data_cleaned/market_data_cleaned.csv", index=False)

print(df.head())
print(df.info())
print("Done! market_data_cleaned.csv saved.")
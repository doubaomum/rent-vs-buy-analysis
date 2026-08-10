import numpy as np
import pandas as pd
from sqlalchemy import create_engine

# =========================================================
# PostgreSQL connection
# Replace the password with your own PostgreSQL password.
# =========================================================
engine = create_engine(
    "postgresql+psycopg2://postgres:zj2058961@localhost:5432/rentvsbuy"
)

# =========================================================
# Load staging tables from PostgreSQL
# =========================================================
house = pd.read_sql(
    """
    SELECT * FROM stg.canada_house_price_index_2010_100
    ORDER BY date_period ASC
    """,
    engine,
)

sp500 = pd.read_sql(
    """
    SELECT *
    FROM stg.sp500_usd
    ORDER BY date_period ASC
    """,
    engine,
)

tsx = pd.read_sql(
    """
    SELECT *
    FROM stg.tsx_cad
    ORDER BY date_period ASC
    """,
    engine,
)

vt = pd.read_sql(
    """
    SELECT *
    FROM stg.vt_usd
    ORDER BY date_period ASC
    """,
    engine,
)

cpi = pd.read_sql(
    """
    SELECT *
    FROM stg.canada_cpi
    ORDER BY date_period ASC
    """,
    engine,
)

fx = pd.read_sql(
    """
    SELECT *
    FROM stg.usd_cad
    WHERE dexcaus IS NOT NULL
    ORDER BY date_period ASC
    """,
    engine,
)

# =========================================================
# Standardize date columns
# =========================================================

dataframes = [house, sp500, tsx, vt, cpi, fx]

for df in dataframes:
    df["date_period"] = pd.to_datetime(df["date_period"])

# =========================================================
# Canada House Price Index
# Rebase from 2010 = 100 to 1990 = 100
# =========================================================
house_1990 = house[
    (house["date_period"].dt.year==1990)
    & house["price_index"].notna()
].sort_values("date_period")

house_base_1990 = house_1990.iloc[0]["price_index"]

canada_house_price_index_1990_100 = house.copy()

canada_house_price_index_1990_100 = (
    canada_house_price_index_1990_100.rename(
        columns ={"price_index": "price_index_original"}
    )
)

canada_house_price_index_1990_100["price_index_1990_100"] = (
    canada_house_price_index_1990_100["price_index_original"]
    / house_base_1990
    *100
)

# =========================================================
# Helper function
# Match each stock date with the most recent available
# USD/CAD exchange rate on or before that date.
# CPI convert normal CAD into REAL CAD
# =========================================================
def convert_usd_asset_to_real_cad(
    asset_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    fx_df: pd.DataFrame | None = None,
    is_used: bool = False,
) -> pd.DataFrame:
    
    asset = asset_df.copy().sort_values("date_period")


    # Convert USD assets to CAD
    if is_used:
        if fx_df is None:
            raise ValueError("fx_df is required when is_usd=True")
    
        exchange_rates = fx_df.copy().sort_values("date_period")
    
        asset = asset.rename(
         columns= {"adj_close_price": "price_usd"}
         )

    # Find the latest exchange rate on or before each stock date
        asset = pd.merge_asof(
            asset,
            exchange_rates,
            on = "date_period",
            direction = "backward",
        )

        # USD to CAD
        asset["price_cad"] = (
            asset["price_usd"]* asset["dexcaus"]
        )

         # Asset is already denominated in CAD
    else:
        asset = asset.rename(
            columns={"adj_close_price": "price_cad"}
        )

    #Exact monthly CPI match
    asset = asset.merge (
        cpi_df,
        on = "date_period",
        how="left",
    )

    # Prevent division by zero
    asset ["cpi_value"] = (
        asset ["cpi_value"].replace (0, np.nan)
    )

    # Nominal CAD to real CAD
    asset["price_cad_real"] = (
        asset["price_cad"]
        / asset ["cpi_value"]
        *100
    )

    return asset

# =========================================================
# S&P 500 Real CAD Index
# Step 1: USD to CAD
# Step 2: Adjust for CPI
# Step 3: Rebase to 1990 = 100
# =========================================================
sp500_index_1990_100 = convert_usd_asset_to_real_cad(
    asset_df=sp500,
    fx_df=fx,
    cpi_df=cpi,
    is_used=True,
)

sp500_base_1990 = sp500_index_1990_100.loc[
    sp500_index_1990_100["date_period"]
    == pd.Timestamp("1990-01-01"),
    'price_cad_real'
].iloc[0]

sp500_index_1990_100["price_index_cad_real"] = (
    sp500_index_1990_100["price_cad_real"]
    / sp500_base_1990
    * 100
)

sp500_index_1990_100 = sp500_index_1990_100[
    [
        "date_period",
        "price_usd",
        "price_cad",
        "price_cad_real",
        "price_index_cad_real",
    ]
]
# =========================================================
# VT Real CAD
# Step 1: USD to CAD
# Step 2: Adjust for CPI
# VT is not rebased to 1990 because it did not exist in 1990.
# =========================================================

vt_real = convert_usd_asset_to_real_cad(
    asset_df=vt,
    cpi_df=cpi,
    fx_df=fx,
    is_used=True,
)

vt_cad_real = vt_real[
    [
        "date_period",
        "price_usd",
        "price_cad",
        "price_cad_real",
    ]
]

# =========================================================
# TSX Real CAD Index
# Step 1: Adjust nominal CAD price for CPI
# Step 2: Rebase to 1990 = 100
# =========================================================
tsx_real = convert_usd_asset_to_real_cad(
    asset_df=tsx,
    cpi_df=cpi,
    is_used=False,
)

tsx_base_1990 = tsx_real.loc[
    tsx_real["date_period"] == pd.Timestamp("1990-01-01"),
    "price_cad_real",
].iloc[0]

tsx_real["price_index_cad_real"] = (
    tsx_real["price_cad_real"]
    / tsx_base_1990
    * 100
)

tsx_index_1990_100 = tsx_real[
    [
        "date_period",
        "price_cad",
        "price_cad_real",
        "price_index_cad_real",
    ]
]

# =========================================================
# Write final analysis tables to PostgreSQL
#
# if_exists="replace" is equivalent to:
# DROP TABLE + CREATE TABLE + INSERT
# =========================================================

canada_house_price_index_1990_100.to_sql(
    name = "canada_house_price_index_1990_100",
    con=engine,
    schema="analysis",
    if_exists="replace",
    index=False,
)
 
sp500_index_1990_100.to_sql(
    name="sp500_index_1990_100",
    con=engine,
    schema="analysis",
    if_exists="replace",
    index=False,
)

tsx_index_1990_100.to_sql(
    name="tsx_index_1990_100",
    con=engine,
    schema="analysis",
    if_exists="replace",
    index=False,
)

vt_cad_real.to_sql(
    name="vt_cad_real",
    con=engine,
    schema="analysis",
    if_exists="replace",
    index=False,
)


print("Analysis tables created successfully.")
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

# =========================================================
# Standardize date columns
# =========================================================

dataframes = [house, sp500, tsx, vt]

for df in dataframes:
    df["date_period"] = pd.to_datetime(df["date_period"])

# =========================================================
# Canada House Price CAGR Analysis
# Source: stg.canada_house_price_index_2010_100
# Holding periods: 5, 10, 15, 20, 25, 30, and 35 years
# Uses Q1 data as the annual starting observation
# =========================================================
def create_cagr_table(
    df:pd.DataFrame,
    price_column: str,
    holding_periods:list[int],
    annual_month: int | None = None,
    annual_quarter: int | None =None
) -> pd.DataFrame:
    data = df.copy()

    if annual_month is not None:
        data = data [
                data["date_period"].dt.month == annual_month
            ]
        
    if annual_quarter is not None:
        data = data [
                data["date_period"].dt.quarter == annual_quarter
            ]
    result = []

    for holding_years in holding_periods:

        start_data = data[
            ["date_period", price_column]
        ].copy()

        start_data = start_data.rename(
            columns ={
                "date_period": "start_date",
                price_column: "start_price"
            }
        )
        
        #Calculate the required ending date
        start_data["end_date"] = (
            start_data["start_date"]
            + pd.DateOffset(years = holding_years)
        )

        end_data = df.copy()

        end_data = end_data[
            ["date_period", price_column]
        ].rename(
            columns={
                "date_period": "end_date",
                price_column: "end_price"
            }
        )

         # Match each starting date with the exact ending date
        cagr_data = start_data.merge(
            end_data,
            on="end_date",
            how="inner"
        )

        cagr_data["start_year"] = (
            cagr_data["start_date"].dt.year
        )

        cagr_data["end_year"] = (
            cagr_data["end_date"].dt.year
        )

        cagr_data["holding_years"] = holding_years

        cagr_data["cagr"] = np.power(
            cagr_data["end_price"]
            / cagr_data["start_price"].replace(0, np.nan),
            1/ holding_years
        ) -1

        cagr_data = cagr_data[
            [
                "start_date",
                "end_date",
                "start_year",
                "end_year",
                "holding_years",
                "start_price",
                "end_price",
                "cagr"
            ]
        ]

        result.append(cagr_data)

    final_cagr = pd.concat(
        result,
        ignore_index = True
    )

    final_cagr = final_cagr.sort_values(
        by = ["start_date", "holding_years" ]
    ).reset_index(drop=True)

    return final_cagr


Canada_house_cagr = create_cagr_table (
    df=house,
    price_column = "price_index",
    holding_periods = [5, 10, 15,20, 25, 30, 35],
    annual_quarter = 1
)

sp500_cagr = create_cagr_table(
    df=sp500,
    price_column="adj_close_price",
    holding_periods=[5, 10, 15, 20, 25, 30, 35],
    annual_month=1
)

tsx_cagr = create_cagr_table(
    df=tsx,
    price_column="adj_close_price",
    holding_periods=[5, 10, 15, 20, 25, 30, 35],
    annual_month=1
)

vt_cagr = create_cagr_table(
    df=vt,
    price_column="adj_close_price",
    holding_periods=[5, 10, 15, 18],
    annual_month=1
)

#=========================================================
# Write final analysis tables to PostgreSQL
#
# if_exists="replace" is equivalent to:
# DROP TABLE + CREATE TABLE + INSERT
# =========================================================

Canada_house_cagr.to_sql(
    name = "canada_house_cagr",
    con=engine,
    schema="analysis",
    if_exists="replace",
    index=False,
)
 
sp500_cagr.to_sql(
    name="sp500_cagr",
    con=engine,
    schema="analysis",
    if_exists="replace",
    index=False,
)

tsx_cagr.to_sql(
    name="tsx_cagr",
    con=engine,
    schema="analysis",
    if_exists="replace",
    index=False,
)

vt_cagr.to_sql(
    name="vt_cagr",
    con=engine,
    schema="analysis",
    if_exists="replace",
    index=False,
)


print("Analysis tables created successfully.")
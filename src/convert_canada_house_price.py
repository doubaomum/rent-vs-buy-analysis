import pandas as pd

input_path = "data/processed/house/Canada_house_norminal_Index2010=100.csv"
output_path = "data/processed/house/canada_house_price_estimated.csv"

BASE_PRICE = 531800
BASE_DATE = "2019-12-31"  # closest available index date to 2020-01

df = pd.read_csv(input_path)

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

base_index = df.loc[df["date"] == BASE_DATE, "index_value"].iloc[0]

df["canada_house_price_estimated"] = (
    df["index_value"] / base_index * BASE_PRICE
).round(0)

df.to_csv(output_path, index=False)

print("Base index:", base_index)
print(df.head())
print("Saved to:", output_path)
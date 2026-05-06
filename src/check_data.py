import pandas as pd

files = {
    "canada_house": "raw_data/pre_cleaned_data/house/canada_house.csv",
    "city_house": "raw_data/pre_cleaned_data/house/city_house.csv",
    "tsx": "raw_data/pre_cleaned_data/stock/tsx.csv",
    "sp500": "raw_data/pre_cleaned_data/stock/sp500.csv",
    "vt": "raw_data/pre_cleaned_data/stock/vt.csv",
    "usd_cad": "raw_data/pre_cleaned_data/fx/usd_cad.csv"
}

for name, path in files.items():

    if name == "vt":
        df = pd.read_csv(path, header=None, names=["date", "vt_usd"])
    else:
        df = pd.read_csv(path)

    print("\n==============================")
    print(f"FILE: {name}")
    print(df.head())
    print(df.columns)
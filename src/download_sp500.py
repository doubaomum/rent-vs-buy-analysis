import yfinance as yf
import pandas as pd

print("Downloading S&P 500 data...")

# Download monthly data
df = yf.download("^GSPC", start="1985-01-01", interval="1mo")

# Keep only needed column
df = df[['Adj Close']]

# Reset index to get Date column
df = df.reset_index()

# Rename column
df = df.rename(columns={'Adj Close': 'SP500'})

# Save
df.to_csv("sp500_monthly.csv", index=False)

print("Rows:", len(df))
print(df.head())

print("Saved as sp500_monthly.csv ✅")

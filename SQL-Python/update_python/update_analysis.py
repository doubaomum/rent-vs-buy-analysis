r"""Refresh analysis from staging in one transaction.

Project layout: create_SQL/, simulation_python/, update_python/.
Keep API.env beside this file in update_python/.
Run from SQL-Python: python3 .\update_python\update_analysis.py
"""

import os
from pathlib import Path
import sys

import psycopg
from psycopg import sql
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
SQL_DIR = PROJECT_DIR / "create_SQL"
SQL_FILES = (
    "04_analysis_refresh_real_asset_indexes.sql",
    "04_analysis_refresh_long_tables.sql",
    "04_analysis_refresh_asset_cagr.sql",
)
SOURCES = (
    "canada_house_price_index_2010_100", "sp500_usd", "tsx_cad", "vt_usd",
    "usd_cad", "canada_cpi", "city_indexed_house_prices", "city_house_prices", "city_rent",
)
TABLE_KEYS = {
    "canada_house_price_index_1990_100": ("date_period",),
    "sp500_index_1990_100": ("date_period",),
    "tsx_index_1990_100": ("date_period",),
    "vt_cad_real": ("date_period",),
    "city_indexed_house_prices": ("date_period",),
    "city_house_prices_long": ("city", "date_period"),
    "city_rent_long": ("city", "date_period"),
    "canada_house_cagr": ("start_date", "holding_years"),
    "sp500_cagr": ("start_date", "holding_years"),
    "tsx_cagr": ("start_date", "holding_years"),
    "vt_cagr": ("start_date", "holding_years"),
    "city_house_cagr": ("start_date", "holding_years"),
    "sum_canada_stock_cagr": ("start_date", "holding_years"),
}


def validate_sources(cur):
    for table in SOURCES:
        identifier = sql.Identifier("stg", table)
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {} WHERE date_period IS NOT NULL").format(identifier))
        if cur.fetchone()[0] == 0:
            raise ValueError(f"stg.{table} has no dated observations.")
        cur.execute(sql.SQL("""
            SELECT date_period FROM {} WHERE date_period IS NOT NULL
            GROUP BY date_period HAVING COUNT(*) > 1 LIMIT 1
        """).format(identifier))
        if cur.fetchone():
            raise ValueError(f"stg.{table} contains duplicate dates.")

    # Original rebasing formulas depend on these exact dates.
    for period in ("1990-01-01", "2005-01-01"):
        cur.execute("SELECT cpi_value FROM stg.canada_cpi WHERE date_period = %s", (period,))
        row = cur.fetchone()
        if not row or row[0] is None or row[0] <= 0:
            raise ValueError(f"Missing positive CPI at the original base date {period}.")
        for table in ("sp500_usd", "tsx_cad"):
            cur.execute(sql.SQL("SELECT adj_close_price FROM {} WHERE date_period = %s")
                        .format(sql.Identifier("stg", table)), (period,))
            row = cur.fetchone()
            if not row or row[0] is None or row[0] <= 0:
                raise ValueError(f"Missing positive stock base value: stg.{table}, {period}.")


def validate_results(cur):
    summaries = []
    for table, key in TABLE_KEYS.items():
        identifier = sql.Identifier("analysis", table)
        keys = sql.SQL(", ").join(map(sql.Identifier, key))
        null_key = sql.SQL(" OR ").join(sql.SQL("{} IS NULL").format(sql.Identifier(c)) for c in key)
        cur.execute(sql.SQL("SELECT 1 FROM {} WHERE {} LIMIT 1").format(identifier, null_key))
        if cur.fetchone():
            raise ValueError(f"analysis.{table} contains a missing key.")
        cur.execute(sql.SQL("SELECT 1 FROM {} GROUP BY {} HAVING COUNT(*) > 1 LIMIT 1")
                    .format(identifier, keys))
        if cur.fetchone():
            raise ValueError(f"analysis.{table} contains duplicate keys.")
        period_column = "end_date" if "holding_years" in key else "date_period"
        cur.execute(sql.SQL("SELECT COUNT(*), MIN({period}), MAX({period}) FROM {table}")
                    .format(period=sql.Identifier(period_column), table=identifier))
        count, earliest, latest = cur.fetchone()
        summaries.append((table, count, earliest, latest))

    # Rebuilt long tables must preserve each staged city value, including NULL.
    for long_table, stage_table in (("city_house_prices_long", "city_house_prices"),
                                    ("city_rent_long", "city_rent")):
        cur.execute(sql.SQL("""
            WITH expected AS (
                SELECT s.date_period, v.city, v.price
                FROM {stage} s CROSS JOIN LATERAL (
                    VALUES ('Canada', s.canada_price), ('Vancouver', s.vancouver_price),
                    ('Calgary', s.calgary_price), ('Edmonton', s.edmonton_price),
                    ('Toronto', s.toronto_price), ('Ottawa', s.ottawa_price),
                    ('Montreal', s.montreal_price)
                ) v(city, price) WHERE s.date_period IS NOT NULL
            )
            SELECT COUNT(*) FROM expected e FULL JOIN {target} t
            ON e.city = t.city AND e.date_period = t.date_period
            WHERE e.city IS NULL OR t.city IS NULL OR e.price IS DISTINCT FROM t.price
        """).format(stage=sql.Identifier("stg", stage_table), target=sql.Identifier("analysis", long_table)))
        if cur.fetchone()[0]:
            raise ValueError(f"analysis.{long_table} does not match staging.")

    # A missing FX base would otherwise silently make every rebased value NULL.
    for table in ("sp500_index_1990_100", "tsx_index_1990_100"):
        cur.execute(sql.SQL("SELECT price_index_cad_real FROM {} WHERE date_period = DATE '1990-01-01'")
                    .format(sql.Identifier("analysis", table)))
        row = cur.fetchone()
        if not row or row[0] is None or abs(row[0] - 100) > 0.000001:
            raise ValueError(f"analysis.{table} did not rebase to 100.")
    return summaries


def main():
    scripts = [(name, (SQL_DIR / name).read_text(encoding="utf-8-sig")) for name in SQL_FILES]
    load_dotenv(HERE / "API.env")
    password = os.getenv("pg_password", "")
    if not password:
        raise ValueError("Missing pg_password in API.env beside this script.")
    with psycopg.connect(host="localhost", port=5432, dbname="rentvsbuy", user="postgres",
                         password=password, connect_timeout=10) as conn:
        conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        with conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_xact_lock(726562, 4)")
            if not cur.fetchone()[0]:
                raise ValueError("Another analysis refresh is already running.")
            print("Checking staging inputs...", flush=True)
            validate_sources(cur)
            for name, script in scripts:
                print(f"Running {name}...", flush=True)
                cur.execute(script, prepare=False)
            print("Checking refreshed analysis results...", flush=True)
            summaries = validate_results(cur)
    print("Analysis refresh committed successfully.")
    for table, count, earliest, latest in summaries:
        print(f"analysis.{table}: rows={count}, earliest={earliest}, latest={latest}")
    print("The simulations need to be refreshed separately before Power BI uses their new results.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Analysis refresh failed: {error}")
        print("The database transaction was not committed.")
        sys.exit(1)

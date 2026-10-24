"""Refresh USD/CAD raw and staging tables in one PostgreSQL transaction.

Reads FRED_API_KEY and pg_password from API.env beside this script.
Run in PowerShell: python3 update_fred.py
"""

import json
import os
import sys
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import psycopg
from dotenv import load_dotenv


def main():
    load_dotenv(Path(__file__).resolve().parent / "API.env")
    api_key = os.getenv("FRED_API_KEY", "").strip()
    db_password = os.getenv("pg_password", "")
    if not api_key or not db_password:
        raise ValueError("Missing FRED_API_KEY or pg_password in the configuration.")

    with psycopg.connect(
        host="localhost",
        port=5432,
        dbname="rentvsbuy",
        user="postgres",
        password=db_password,
        connect_timeout=10,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MAX(observation_date::date)
                FROM raw.usd_cad_raw;
            """)
            latest_date = cur.fetchone()[0]
            start_date = (
                latest_date - timedelta(days=30)
                if latest_date else date(1971, 1, 4)
            )
            print(f"Fetching observations from {start_date}...")

            params = {
                "series_id": "DEXCAUS",
                "api_key": api_key,
                "file_type": "json",
                "observation_start": start_date.isoformat(),
                "sort_order": "asc",
                "limit": 100000,
            }
            url = (
                "https://api.stlouisfed.org/fred/series/observations?"
                + urlencode(params)
            )
            with urlopen(url, timeout=30) as response:
                payload = json.load(response)

            observations = payload.get("observations")
            if not isinstance(observations, list):
                raise ValueError("The response has no observations list.")
            if "count" in payload and int(payload["count"]) > len(observations):
                raise ValueError("The API response is incomplete; pagination is required.")

            cleaned_rows = []
            missing_count = 0
            seen_dates = set()
            for row in observations:
                if row["value"] == ".":
                    missing_count += 1
                    continue
                observation_date = date.fromisoformat(row["date"])
                rate = Decimal(row["value"])
                if not rate.is_finite() or rate <= 0:
                    raise ValueError("An invalid exchange rate was returned.")
                if observation_date in seen_dates:
                    raise ValueError("The response contains duplicate observation dates.")
                seen_dates.add(observation_date)
                cleaned_rows.append((observation_date.isoformat(), format(rate, "f")))

            if not cleaned_rows:
                raise ValueError("No valid observations were returned.")

            # Keep each raw date unique and merge only new or changed records.
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_usd_cad_observation_date
                ON raw.usd_cad_raw (observation_date);
            """)
            cur.executemany("""
                INSERT INTO raw.usd_cad_raw AS target (observation_date, dexcaus)
                VALUES (%s, %s)
                ON CONFLICT (observation_date)
                DO UPDATE SET dexcaus = EXCLUDED.dexcaus
                WHERE target.dexcaus IS DISTINCT FROM EXCLUDED.dexcaus;
            """, cleaned_rows)
            raw_changed_count = cur.rowcount
            cur.execute("""
                SELECT COUNT(*), MAX(observation_date::date)
                FROM raw.usd_cad_raw;
            """)
            raw_total_rows, raw_latest_date = cur.fetchone()

            # Preserve the existing staging table and the original cleaning rules.
            # The full raw history is synchronized, including older corrections.
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_usd_cad_period
                ON stg.usd_cad (date_period);
            """)
            cur.execute("""
                INSERT INTO stg.usd_cad AS target (date_period, dexcaus)
                SELECT
                    TO_DATE(observation_date, 'YYYY-MM-DD'),
                    NULLIF(REPLACE(TRIM(dexcaus), ',', ''), '')::numeric
                FROM raw.usd_cad_raw
                WHERE TRUE
                ON CONFLICT (date_period)
                DO UPDATE SET dexcaus = EXCLUDED.dexcaus
                WHERE target.dexcaus IS DISTINCT FROM EXCLUDED.dexcaus;
            """)
            staging_changed_count = cur.rowcount
            cur.execute("""
                SELECT COUNT(*), MAX(date_period)
                FROM stg.usd_cad;
            """)
            staging_total_rows, staging_latest_date = cur.fetchone()

    # This is reached only after the connection context commits both updates.
    print("FRED database update committed successfully.")
    print(f"Valid observations processed: {len(cleaned_rows)}")
    print(f"Missing values skipped: {missing_count}")
    print(f"Raw rows inserted or updated: {raw_changed_count}")
    print(f"Raw total rows: {raw_total_rows}")
    print(f"Raw latest date: {raw_latest_date}")
    print(f"Staging rows inserted or updated: {staging_changed_count}")
    print(f"Staging total rows: {staging_total_rows}")
    print(f"Staging latest date: {staging_latest_date}")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        print(f"FRED request failed. HTTP status: {error.code}", file=sys.stderr)
        sys.exit(1)
    except (URLError, TimeoutError):
        print("The FRED connection failed or timed out.", file=sys.stderr)
        sys.exit(1)
    except psycopg.Error as error:
        print(f"Database operation failed: {error}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, InvalidOperation, KeyError, TypeError, OSError) as error:
        print(f"FRED update failed: {error}", file=sys.stderr)
        sys.exit(1)

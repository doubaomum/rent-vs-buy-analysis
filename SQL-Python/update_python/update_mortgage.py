"""Update raw and staging tables with Canada five-year conventional mortgage rates (percent).

Uses the existing API.env next to this script, with pg_password set.
Run with: python3 update_mortgage.py (Windows PowerShell).
Both tables are refreshed in one transaction; scheduling comes later.
"""

import json
import os
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psycopg
from dotenv import load_dotenv

PRODUCT_ID = 34100145
COORDINATE = "1.0.0.0.0.0.0.0.0.0"
API_URL = (
    "https://www150.statcan.gc.ca/t1/wds/rest/"
    "getDataFromCubePidCoordAndLatestNPeriods"
)


def clean_response(payload, start_date, today):
    """Validate the selected series and retain valid, unique monthly values."""
    if not isinstance(payload, list) or len(payload) != 1:
        raise ValueError("Unexpected API response structure.")
    result = payload[0]
    if result.get("status") != "SUCCESS":
        raise ValueError("Statistics Canada reported an unsuccessful request.")
    series = result["object"]
    if (
        series["coordinate"] != COORDINATE
        or int(series["productId"]) != PRODUCT_ID
        or int(series["responseStatusCode"]) != 0
    ):
        raise ValueError("The API returned an unexpected series or status.")
    points = series["vectorDataPoint"]
    if not isinstance(points, list):
        raise ValueError("The response contains no data point list.")

    rows = {}
    missing_count = 0
    for point in points:
        period = date.fromisoformat(point["refPer"])
        if period.day != 1 or period > today:
            raise ValueError("An invalid monthly reference date was returned.")
        if period < start_date:
            continue
        if point.get("value") is None:
            missing_count += 1
            continue
        if (
            int(point["scalarFactorCode"]) != 0
            or int(point["securityLevelCode"]) != 0
        ):
            raise ValueError("Unexpected scale or restricted data point.")
        value = Decimal(str(point["value"]))
        if not value.is_finite() or value < 0:
            raise ValueError("An invalid Mortgage value was returned.")
        if period in rows:
            raise ValueError("The response contains duplicate months.")
        rows[period] = format(value, "f")

    if not rows:
        raise ValueError("No valid Mortgage observations were returned.")
    return [(period.isoformat(), rows[period]) for period in sorted(rows)], missing_count


def main():
    load_dotenv(Path(__file__).resolve().parent / "API.env")
    password = os.getenv("pg_password", "")
    if not password:
        raise ValueError("Missing pg_password in API.env or the environment.")

    today = date.today()
    with psycopg.connect(
        host="localhost", port=5432, dbname="rentvsbuy",
        user="postgres", password=password, connect_timeout=10,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(mortgage_period::date) FROM raw.canada_5yearmortgage_raw;")
            latest_date = cur.fetchone()[0]
            if latest_date and (latest_date.day != 1 or latest_date > today):
                raise ValueError("The database contains an invalid latest Mortgage date.")

            # Recheck 12 months before the latest stored month for revisions.
            if latest_date is None:
                raise ValueError("The raw table is empty; an initial historical load is required.")
            start_date = date(latest_date.year - 1, latest_date.month, 1)
            # Allow for all months through today; the API returns published periods.
            latest_n = (
                (today.year - start_date.year) * 12
                + today.month - start_date.month + 1
            )
            print(f"Fetching Mortgage observations from {start_date}...")
            request = Request(
                API_URL,
                data=json.dumps([{
                    "productId": PRODUCT_ID,
                    "coordinate": COORDINATE,
                    "latestN": latest_n,
                }]).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=60) as response:
                payload = json.load(response, parse_float=Decimal)
            rows, missing_count = clean_response(payload, start_date, today)

            # Prevent duplicate months. Existing duplicates cause a rollback.
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_canada_5yearmortgage_raw_period
                ON raw.canada_5yearmortgage_raw (mortgage_period);
            """)
            cur.executemany("""
                INSERT INTO raw.canada_5yearmortgage_raw AS target (mortgage_period, mortgage_rate)
                VALUES (%s, %s)
                ON CONFLICT (mortgage_period)
                DO UPDATE SET mortgage_rate = EXCLUDED.mortgage_rate
                WHERE NULLIF(REPLACE(TRIM(target.mortgage_rate), ',', ''), '')::numeric
                    IS DISTINCT FROM EXCLUDED.mortgage_rate::numeric;
            """, rows)
            changed_count = cur.rowcount
            cur.execute("""
                SELECT COUNT(*), MAX(mortgage_period::date)
                FROM raw.canada_5yearmortgage_raw;
            """)
            total_rows, new_latest_date = cur.fetchone()

            # Synchronize all raw history, including any older corrections.
            # If staging fails, the connection context rolls back both updates.
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_canada_5yearmortgage_period
                ON stg.canada_5yearmortgage (date_period);
            """)
            cur.execute("""
                INSERT INTO stg.canada_5yearmortgage AS target (date_period, mortgage_rate)
                SELECT
                    TO_DATE(mortgage_period, 'YYYY-MM-DD'),
                    NULLIF(REPLACE(TRIM(mortgage_rate), ',', ''), '')::numeric
                FROM raw.canada_5yearmortgage_raw
                WHERE TRUE
                ON CONFLICT (date_period)
                DO UPDATE SET mortgage_rate = EXCLUDED.mortgage_rate
                WHERE target.mortgage_rate IS DISTINCT FROM EXCLUDED.mortgage_rate;
            """)
            staging_changed_count = cur.rowcount
            cur.execute("""
                SELECT COUNT(*), MAX(date_period)
                FROM stg.canada_5yearmortgage;
            """)
            staging_total_rows, staging_latest_date = cur.fetchone()

    # Exiting the connection context successfully commits the transaction.
    print("Mortgage database update committed successfully.")
    print(f"Valid observations processed: {len(rows)}")
    print(f"Missing values skipped: {missing_count}")
    print(f"Raw rows inserted or updated: {changed_count}")
    print(f"Raw total rows: {total_rows}")
    print(f"Raw latest date: {new_latest_date}")
    print(f"Staging rows inserted or updated: {staging_changed_count}")
    print(f"Staging total rows: {staging_total_rows}")
    print(f"Staging latest date: {staging_latest_date}")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        print(f"Statistics Canada request failed. HTTP status: {error.code}", file=sys.stderr)
        sys.exit(1)
    except (URLError, TimeoutError):
        print("The Statistics Canada connection failed or timed out.", file=sys.stderr)
        sys.exit(1)
    except psycopg.Error as error:
        print(f"Database operation failed: {error}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, InvalidOperation, KeyError, TypeError, OSError) as error:
        print(f"Mortgage update failed: {error}", file=sys.stderr)
        sys.exit(1)

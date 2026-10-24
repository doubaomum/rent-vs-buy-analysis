"""Refresh BIS Canada REAL house price index, 2010=100, in raw and staging.

Series: BIS,WS_SPP,1.0 / Q.CA.R.628.
Fetches the complete small quarterly series, retaining the database's existing
earliest date. Existing history is rechecked for revisions on every run.
Reads pg_password from API.env beside this script. No scheduling is configured.
"""

import calendar
import csv
import io
import os
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psycopg
from dotenv import load_dotenv

API_URL = "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_SPP/1.0/Q.CA.R.628"
DATAFLOW_ID = "BIS,WS_SPP,1.0"
SERIES_KEY = "Q.CA.R.628"


def clean_csv(content, earliest_date, today):
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    required = {
        "DATAFLOW", "FREQ", "REF_AREA", "VALUE", "UNIT_MEASURE",
        "TIME_PERIOD", "OBS_VALUE", "UNIT_MULT", "OBS_CONF",
        "OBS_PRE_BREAK", "OBS_STATUS",
    }
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("BIS returned unexpected CSV columns.")

    rows = {}
    seen_periods = set()
    missing_count = 0
    for row in reader:
        if (
            row["DATAFLOW"] != "BIS:WS_SPP(1.0)"
            or row["FREQ"] != "Q"
            or row["REF_AREA"] != "CA"
            or row["VALUE"] != "R"
            or row["UNIT_MEASURE"] != "628"
            or row["UNIT_MULT"] != "0"
        ):
            raise ValueError("Unexpected BIS series, unit, or multiplier.")

        match = re.fullmatch(r"(\d{4})-Q([1-4])", row["TIME_PERIOD"].strip())
        if not match:
            raise ValueError("Unexpected BIS quarterly date format.")
        year, quarter = map(int, match.groups())
        month = quarter * 3
        period = date(year, month, calendar.monthrange(year, month)[1])
        if period > today:
            raise ValueError("BIS returned a future quarter-end date.")
        if period < earliest_date:
            continue
        if period in seen_periods:
            raise ValueError("BIS returned duplicate quarters.")
        seen_periods.add(period)

        text_value = row["OBS_VALUE"].strip()
        if not text_value:
            missing_count += 1
            continue
        value = Decimal(text_value)
        if not value.is_finite() or value <= 0:
            raise ValueError("BIS returned an invalid price index.")
        rows[period] = (
            DATAFLOW_ID, SERIES_KEY, "Q", "CA", "R", "628",
            "Index, 2010 = 100", "Units", period.isoformat(),
            row["OBS_CONF"].strip() or None,
            row["OBS_PRE_BREAK"].strip() or None,
            row["OBS_STATUS"].strip() or None,
            value,
        )

    if not rows:
        raise ValueError("No valid BIS observations were returned.")
    return [rows[period] for period in sorted(rows)], missing_count


def main():
    load_dotenv(Path(__file__).resolve().parent / "API.env")
    password = os.getenv("pg_password", "")
    if not password:
        raise ValueError("Missing pg_password in API.env or the environment.")

    with psycopg.connect(
        host="localhost", port=5432, dbname="rentvsbuy", user="postgres",
        password=password, connect_timeout=10,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT dataflow_id, series_key, freq, ref_area,
                                value_type, unit_measure
                FROM raw.canada_house_price_index_2010_100;
            """)
            metadata = cur.fetchall()
            expected = (DATAFLOW_ID, SERIES_KEY, "Q", "CA", "R", "628")
            if metadata != [expected]:
                raise ValueError("The raw table must contain only the expected BIS series.")
            cur.execute("""
                SELECT MIN(time_period::date)
                FROM raw.canada_house_price_index_2010_100;
            """)
            earliest_date = cur.fetchone()[0]
            if (
                earliest_date is None
                or earliest_date.month not in (3, 6, 9, 12)
                or earliest_date.day != calendar.monthrange(
                    earliest_date.year, earliest_date.month
                )[1]
            ):
                raise ValueError("The raw table needs an existing quarter-end start date.")

            print(f"Fetching BIS quarterly history from {earliest_date}...")
            request = Request(API_URL, headers={
                "Accept": "application/vnd.sdmx.data+csv;version=1.0.0",
            })
            with urlopen(request, timeout=60) as response:
                content = response.read().decode("utf-8-sig")
            rows, missing_count = clean_csv(content, earliest_date, date.today())

            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_bis_ca_house_raw_series_period
                ON raw.canada_house_price_index_2010_100 (series_key, time_period);
            """)
            cur.executemany("""
                INSERT INTO raw.canada_house_price_index_2010_100 AS target (
                    dataflow_id, series_key, freq, ref_area, value_type,
                    unit_measure, unit_name, unit_multiplier, time_period,
                    obs_conf, obs_pre_break, obs_status, obs_value
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (series_key, time_period)
                DO UPDATE SET
                    dataflow_id = EXCLUDED.dataflow_id,
                    freq = EXCLUDED.freq,
                    ref_area = EXCLUDED.ref_area,
                    value_type = EXCLUDED.value_type,
                    unit_measure = EXCLUDED.unit_measure,
                    unit_name = EXCLUDED.unit_name,
                    unit_multiplier = EXCLUDED.unit_multiplier,
                    obs_conf = EXCLUDED.obs_conf,
                    obs_pre_break = EXCLUDED.obs_pre_break,
                    obs_status = EXCLUDED.obs_status,
                    obs_value = EXCLUDED.obs_value
                WHERE (
                    target.dataflow_id, target.freq, target.ref_area,
                    target.value_type, target.unit_measure, target.unit_name,
                    target.unit_multiplier, target.obs_conf, target.obs_pre_break,
                    target.obs_status, target.obs_value
                ) IS DISTINCT FROM (
                    EXCLUDED.dataflow_id, EXCLUDED.freq, EXCLUDED.ref_area,
                    EXCLUDED.value_type, EXCLUDED.unit_measure, EXCLUDED.unit_name,
                    EXCLUDED.unit_multiplier, EXCLUDED.obs_conf, EXCLUDED.obs_pre_break,
                    EXCLUDED.obs_status, EXCLUDED.obs_value
                );
            """, rows)
            raw_changed = cur.rowcount
            cur.execute("""
                SELECT COUNT(*), MAX(time_period::date)
                FROM raw.canada_house_price_index_2010_100;
            """)
            raw_count, raw_latest = cur.fetchone()

            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_bis_ca_house_period
                ON stg.canada_house_price_index_2010_100 (date_period);
            """)
            cur.execute("""
                INSERT INTO stg.canada_house_price_index_2010_100 AS target (
                    date_period, price_index
                )
                SELECT TO_DATE(time_period, 'YYYY-MM-DD'), obs_value::numeric
                FROM raw.canada_house_price_index_2010_100
                WHERE series_key = %s
                ON CONFLICT (date_period)
                DO UPDATE SET price_index = EXCLUDED.price_index
                WHERE target.price_index IS DISTINCT FROM EXCLUDED.price_index;
            """, (SERIES_KEY,))
            staging_changed = cur.rowcount
            cur.execute("""
                SELECT COUNT(*), MAX(date_period)
                FROM stg.canada_house_price_index_2010_100;
            """)
            staging_count, staging_latest = cur.fetchone()

    print("BIS house price index update committed successfully.")
    print(f"Valid observations processed: {len(rows)}")
    print(f"Missing values skipped: {missing_count}")
    print(f"Raw rows inserted or updated: {raw_changed}")
    print(f"Raw total rows: {raw_count}")
    print(f"Raw latest date: {raw_latest}")
    print(f"Staging rows inserted or updated: {staging_changed}")
    print(f"Staging total rows: {staging_count}")
    print(f"Staging latest date: {staging_latest}")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        print(f"BIS request failed. HTTP status: {error.code}", file=sys.stderr)
        sys.exit(1)
    except (URLError, TimeoutError):
        print("The BIS connection failed or timed out.", file=sys.stderr)
        sys.exit(1)
    except psycopg.Error as error:
        print(f"Database operation failed: {error}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, InvalidOperation, KeyError, TypeError, OSError) as error:
        print(f"BIS update failed: {error}", file=sys.stderr)
        sys.exit(1)

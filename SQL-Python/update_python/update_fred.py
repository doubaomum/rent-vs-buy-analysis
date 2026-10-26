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
from reconciliation import new_report, check_classification, check_changed_count, save_report


def main():
    report = new_report(
        source="FRED",
        dataset="DEXCAUS",
        checks=("classification", "raw_change_count", "api_raw", "raw_staging"),
        extra_fields={"observation_start": None, "observation_latest_in_batch": None},
    )
    try:
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
                report["observation_start"] = start_date.isoformat()
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
                if isinstance(observations, list):
                    report["records"]["received"] = len(observations)
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

                report["records"]["valid"] = len(cleaned_rows)
                report["records"]["missing_skipped"] = missing_count
                report["records"]["rejected"] = missing_count
                if cleaned_rows:
                    report["observation_latest_in_batch"] = max(d for d, _ in cleaned_rows)

                if not cleaned_rows:
                    raise ValueError("No valid observations were returned.")
            
                # Classify source records before RAW UPSERT.
                # Compare stored text as the UPSERT does (not numeric equivalence).
                inserted_count = 0
                updated_count = 0
                unchanged_count = 0

                for observation_date, rate in cleaned_rows:
                    cur.execute("""
                        SELECT dexcaus
                        FROM raw.usd_cad_raw
                        WHERE observation_date = %s;
                    """, (observation_date,))

                    result = cur.fetchone()

                    if result is None:
                        inserted_count += 1

                    elif str(result[0]) != rate:
                        updated_count += 1

                    else:
                        unchanged_count += 1

                report["planned_raw_changes"] = {
                    "inserted": inserted_count,
                    "updated": updated_count,
                    "unchanged": unchanged_count,
                }

                # Account for every valid observation before modifying RAW.
                check_classification(
                    len(cleaned_rows), inserted_count, updated_count, unchanged_count
                )

                report["checks"]["classification"] = "PASS"

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
                check_changed_count(raw_changed_count, inserted_count, updated_count)
                report["checks"]["raw_change_count"] = "PASS"
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
            
                # Reconcile RAW and STAGING before COMMIT
                cur.execute("""
                    SELECT COUNT(*)
                    FROM raw.usd_cad_raw AS r
                    FULL OUTER JOIN stg.usd_cad AS s
                        ON r.observation_date::date = s.date_period
                    WHERE
                        r.observation_date IS NULL
                        OR s.date_period IS NULL
                        OR NULLIF(
                            REPLACE(TRIM(r.dexcaus), ',', ''),
                            ''
                        )::numeric IS DISTINCT FROM s.dexcaus;
                """)

                mismatch_count = cur.fetchone()[0]

                if mismatch_count != 0:
                    raise ValueError(
                        f"RAW/STAGING reconciliation failed: "
                        f"{mismatch_count} mismatched records."
                    )

                report["checks"]["raw_staging"] = "PASS"
                print("RAW/STAGING reconciliation: PASS")

            
                # Reconcile FRED API observations with RAW table

                api_raw_mismatches = 0

                for observation_date, rate in cleaned_rows:
                    cur.execute("""
                        SELECT dexcaus
                        FROM raw.usd_cad_raw
                        WHERE observation_date = %s;
                    """, (observation_date,))

                    result = cur.fetchone()

                    if result is None:
                        api_raw_mismatches += 1
                        continue

                    db_rate = Decimal(str(result[0]))

                    if db_rate != Decimal(rate):
                        api_raw_mismatches += 1

                if api_raw_mismatches > 0:
                    raise ValueError(
                        f"API/RAW reconciliation failed: "
                        f"{api_raw_mismatches} mismatched records."
                    )

                report["checks"]["api_raw"] = "PASS"
                print(
                    f"API/RAW reconciliation: PASS "
                    f"({len(cleaned_rows)} records verified)"
                )



        # The connection context has exited successfully: PostgreSQL committed.
        report["transaction_committed"] = True
        report["status"] = "PASS"
        report["committed_raw_changes"] = dict(report["planned_raw_changes"])
        report["database"] = {
            "raw_changed_rows": raw_changed_count,
            "raw_total_rows": raw_total_rows,
            "raw_latest_date": raw_latest_date.isoformat() if raw_latest_date else None,
            "staging_changed_rows": staging_changed_count,
            "staging_total_rows": staging_total_rows,
            "staging_latest_date": staging_latest_date.isoformat() if staging_latest_date else None,
        }

        # This is reached only after the connection context commits both updates.
        print("FRED database update committed successfully.")
        print(f"Valid observations processed: {len(cleaned_rows)}")
        print(f"Missing values skipped: {missing_count}")
        print(f"Inserted records: {inserted_count}")
        print(f"Updated records: {updated_count}")
        print(f"Unchanged records: {unchanged_count}")
        print("RAW classification check: PASS")
        print(f"Raw rows inserted or updated: {raw_changed_count}")
        print(f"Raw total rows: {raw_total_rows}")
        print(f"Raw latest date: {raw_latest_date}")
        print(f"Staging rows inserted or updated: {staging_changed_count}")
        print(f"Staging total rows: {staging_total_rows}")
        print(f"Staging latest date: {staging_latest_date}")

    except Exception as error:
        # Mark failures without writing exception text, which could contain sensitive data.
        report["error_type"] = type(error).__name__
        raise
    finally:
        try:
            path = save_report(
                report,
                source_slug="fred",
                report_folder=Path(__file__).resolve().parent.parent / "reconciliation_reports",
            )
            print(f"Reconciliation report: {path}")
        except OSError as report_error:
            print(f"Could not save reconciliation report: {report_error}", file=sys.stderr)



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

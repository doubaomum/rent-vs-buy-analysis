r"""Yahoo Finance ^GSPC monthly data -> raw.sp500_raw -> stg.sp500_usd.

Install once: python3 -m pip install yfinance "psycopg[binary]" python-dotenv
Run: python3 .\update_sp500.py
API.env beside this script must contain pg_password. No FRED key is used.
Only completed months are loaded. Dates label each month, not its closing day.
Recheck the existing history to capture revisions. No existing rows are deleted.
"""

from datetime import date, timedelta
from decimal import Decimal
import os
from pathlib import Path
import sys

from reconciliation import new_report, check_classification, check_changed_count, save_report

import pandas as pd
import psycopg
from psycopg import sql
from dotenv import load_dotenv
import yfinance as yf

SYMBOL = "^GSPC"
FIELDS = {
    "open_price": "Open", "high_price": "High", "low_price": "Low",
    "close_price": "Close", "adj_close_price": "Adj Close", "volume": "Volume",
}
DATE_SQL = "TO_DATE(BTRIM(price_date), 'YYYY-MM-DD')"


def read_date(value):
    text = str(value).strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"Unexpected raw date {text!r}; expected YYYY-MM-DD.") from None


def numeric_text(value, is_volume=False):
    if value is None or pd.isna(value):
        return None
    number = Decimal(str(value))
    if not number.is_finite() or number < 0 or (not is_volume and number == 0):
        raise ValueError("Yahoo returned an invalid price or volume.")
    if is_volume:
        if number != number.to_integral_value():
            raise ValueError("Yahoo returned a non-integer volume.")
        return str(int(number))
    return format(number, "f")


def clean_history(frame, start, end):
    if frame is None or frame.empty:
        raise ValueError("Yahoo returned no monthly observations; no update was made.")
    missing_columns = set(FIELDS.values()) - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Yahoo response is missing columns: {sorted(missing_columns)}.")
    records = {}
    missing_cells = 0
    for timestamp, row in frame.iterrows():
        period = timestamp.date()
        if not start <= period < end:
            continue
        if period.day != 1 or period in records:
            raise ValueError(f"Unexpected or duplicate monthly date: {period}.")
        values = tuple(numeric_text(row[source], column == "volume")
                       for column, source in FIELDS.items())
        if all(v is None for v in values[:5]):
            continue
        if values[1] is not None and values[2] is not None:
            if Decimal(values[1]) < Decimal(values[2]):
                raise ValueError(f"High is below Low for {period}.")
        missing_cells += values.count(None)
        records[period] = values
    if not records or not any(v[4] is not None for v in records.values()):
        raise ValueError("No valid monthly adjusted-close observations were returned.")
    return records, missing_cells




def normalized_numeric(value):
    """Match numeric comparison used by the existing PostgreSQL UPSERT."""
    if value is None or not str(value).strip():
        return None
    return Decimal(str(value).strip().replace(",", ""))

def run():
    report = new_report(
        source="Yahoo Finance", dataset=SYMBOL,
        checks=("classification", "raw_change_count", "api_raw", "raw_staging"),
        extra_fields={"observation_start": None, "observation_latest_in_batch": None},
    )
    try:
        load_dotenv(Path(__file__).resolve().parent / "API.env")
        password = os.getenv("pg_password", "")
        if not password:
            raise ValueError("Missing pg_password in API.env.")
        # The first day of this month is exclusive: do not load a partial monthly bar.
        end = date.today().replace(day=1)
        with psycopg.connect(host="localhost", port=5432, dbname="rentvsbuy",
                             user="postgres", password=password, connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT price_date FROM raw.sp500_raw;")
                existing = {}
                for (label,) in cur.fetchall():
                    if label is None or not str(label).strip():
                        continue
                    period = read_date(label)
                    if period.day != 1 or period in existing:
                        raise ValueError(
                            f"Existing S&P 500 dates are not unique first-of-month labels: {period}. "
                            "The linked source is monthly; no update was made."
                        )
                    existing[period] = label
                start = min(existing) if existing else date(1928, 1, 1)
                if start >= end:
                    raise ValueError("The stored start date has no completed months to fetch.")
                print(f"Fetching {SYMBOL} monthly observations from {start}...")
                print(f"Completed months only; current month {end:%Y-%m} is excluded.")
                ticker = yf.Ticker(SYMBOL)
                frame = ticker.history(
                    start=start.isoformat(), end=end.isoformat(), interval="1mo",
                    auto_adjust=False, back_adjust=False, actions=False,
                    repair=False, keepna=True, rounding=False, timeout=30,
                )
                metadata = ticker.get_history_metadata()
                if metadata.get("currency") != "USD":
                    raise ValueError("Could not confirm that Yahoo S&P 500 observations are in USD.")
                records, missing_count = clean_history(frame, start, end)
                missing_months = [period for period in existing if period < end and period not in records]
                if missing_months:
                    raise ValueError(
                        f"Yahoo did not return {len(missing_months)} existing completed months. "
                        "No database update was made."
                    )
                last_completed = (end - timedelta(days=1)).replace(day=1)
                if max(records) < last_completed:
                    raise ValueError(f"Yahoo response is stale; latest returned month is {max(records)}.")

                report["observation_start"] = start.isoformat()
                report["observation_latest_in_batch"] = max(records).isoformat()
                report["records"].update(received=len(frame), valid=len(records),
                                         missing_skipped=0, rejected=0)
                report["missing_numeric_cells_retained_as_null"] = missing_count
                report["source_rows_outside_window_or_skipped"] = len(frame) - len(records)

                # Batch-fetch existing RAW values for exact INSERT / UPDATE classification.
                field_sql = ", ".join(FIELDS)
                cur.execute(f"SELECT price_date, {field_sql} FROM raw.sp500_raw")
                previous = {}
                for label, *values in cur.fetchall():
                    if label is None or not str(label).strip():
                        continue
                    period = read_date(label)
                    if period in previous:
                        raise ValueError(f"Duplicate RAW month: {period}")
                    previous[period] = tuple(normalized_numeric(v) for v in values)

                inserted = updated = unchanged = 0
                for period, values in records.items():
                    new_values = tuple(normalized_numeric(v) for v in values)
                    if period not in previous:
                        inserted += 1
                    elif previous[period] != new_values:
                        updated += 1
                    else:
                        unchanged += 1
                report["planned_raw_changes"] = dict(
                    inserted=inserted, updated=updated, unchanged=unchanged
                )
                check_classification(len(records), inserted, updated, unchanged)
                report["checks"]["classification"] = "PASS"

                cur.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS ux_sp500_raw_price_date
                    ON raw.sp500_raw (price_date)
                    WHERE NULLIF(BTRIM(price_date), '') IS NOT NULL;
                """)
                columns = ("price_date",) + tuple(FIELDS)
                query = sql.SQL("""
                    INSERT INTO raw.sp500_raw AS target ({columns}) VALUES ({placeholders})
                    ON CONFLICT (price_date)
                    WHERE NULLIF(BTRIM(price_date), '') IS NOT NULL
                    DO UPDATE SET {assignments}
                    WHERE ({old}) IS DISTINCT FROM ({new});
                """).format(
                    columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
                    placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
                    assignments=sql.SQL(", ").join(sql.SQL("{} = EXCLUDED.{}").format(
                        sql.Identifier(c), sql.Identifier(c)) for c in FIELDS),
                    old=sql.SQL(", ").join(sql.SQL(
                        "NULLIF(REPLACE(BTRIM(target.{}), ',', ''), '')::numeric"
                    ).format(sql.Identifier(c)) for c in FIELDS),
                    new=sql.SQL(", ").join(sql.SQL("EXCLUDED.{}::numeric").format(
                        sql.Identifier(c)) for c in FIELDS),
                )
                rows = []
                for period, values in sorted(records.items()):
                    label = existing.get(period, period.isoformat())
                    rows.append((label,) + values)
                cur.executemany(query, rows)
                raw_changed = cur.rowcount
                check_changed_count(raw_changed, inserted, updated)
                report["checks"]["raw_change_count"] = "PASS"
                cur.execute(sql.SQL("""
                    SELECT COUNT(*), MAX({date}) FROM raw.sp500_raw
                    WHERE NULLIF(BTRIM(price_date), '') IS NOT NULL;
                """).format(date=sql.SQL(DATE_SQL)))
                raw_dated_count, raw_latest = cur.fetchone()
                cur.execute("SELECT COUNT(*) FROM raw.sp500_raw;")
                raw_count = cur.fetchone()[0]

                cur.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_sp500_usd_period
                    ON stg.sp500_usd (date_period);
                """)
                cur.execute(sql.SQL("""
                    INSERT INTO stg.sp500_usd AS target (date_period, adj_close_price)
                    SELECT {date},
                           NULLIF(REPLACE(TRIM(adj_close_price), ',', ''), '')::numeric
                    FROM raw.sp500_raw
                    WHERE NULLIF(BTRIM(price_date), '') IS NOT NULL
                      AND {date} < %s
                    ON CONFLICT (date_period) DO UPDATE
                    SET adj_close_price = EXCLUDED.adj_close_price
                    WHERE target.adj_close_price IS DISTINCT FROM EXCLUDED.adj_close_price;
                """).format(date=sql.SQL(DATE_SQL)), (end,))
                staging_changed = cur.rowcount
                cur.execute("SELECT COUNT(*), MAX(date_period) FROM stg.sp500_usd;")
                staging_count, staging_latest = cur.fetchone()

                # Compare completed-month RAW adjusted close with STAGING (both directions).
                cur.execute(sql.SQL("""
                    SELECT COUNT(*)
                    FROM (
                        SELECT {date} AS period,
                            NULLIF(REPLACE(BTRIM(adj_close_price), ',', ''), '')::numeric AS value
                        FROM raw.sp500_raw
                        WHERE NULLIF(BTRIM(price_date), '') IS NOT NULL AND {date} < %s
                    ) AS r
                    FULL OUTER JOIN stg.sp500_usd AS s
                        ON r.period = s.date_period
                    WHERE r.period IS NULL OR s.date_period IS NULL
                        OR r.value IS DISTINCT FROM s.adj_close_price;
                """).format(date=sql.SQL(DATE_SQL)), (end,))
                mismatch_count = cur.fetchone()[0]
                if mismatch_count:
                    raise ValueError(f"RAW/STAGING reconciliation failed: {mismatch_count} mismatches")
                report["checks"]["raw_staging"] = "PASS"
                print("RAW/STAGING reconciliation: PASS")

                # Verify all six Yahoo source fields, including nullable volume, in RAW.
                cur.execute(f"SELECT price_date, {field_sql} FROM raw.sp500_raw")
                stored = {}
                for label, *values in cur.fetchall():
                    if label is not None and str(label).strip():
                        stored[read_date(label)] = tuple(normalized_numeric(v) for v in values)
                api_mismatches = sum(
                    stored.get(period) != tuple(normalized_numeric(v) for v in values)
                    for period, values in records.items()
                )
                if api_mismatches:
                    raise ValueError(f"API/RAW reconciliation failed: {api_mismatches} mismatches")
                report["checks"]["api_raw"] = "PASS"
                print(f"API/RAW reconciliation: PASS ({len(records)} months verified)")

        report["transaction_committed"] = True
        report["committed_raw_changes"] = dict(report["planned_raw_changes"])
        report["status"] = "PASS"
        report["database"] = {
            "raw_changed_rows": raw_changed,
            "raw_total_rows": raw_count, "raw_dated_rows": raw_dated_count,
            "raw_latest_date": raw_latest.isoformat() if raw_latest else None,
            "staging_changed_rows": staging_changed,
            "staging_total_rows": staging_count,
            "staging_latest_date": staging_latest.isoformat() if staging_latest else None,
        }
        print("S&P 500 database update committed successfully.")
        print(f"Monthly observations processed: {len(records)}")
        print(f"Missing numeric values retained as NULL: {missing_count}")
        print(f"Raw rows inserted or updated: {raw_changed}")
        print(f"Raw total rows: {raw_count}")
        print(f"Raw dated rows: {raw_dated_count}")
        print(f"Raw latest date: {raw_latest}")
        print(f"Staging rows inserted or updated: {staging_changed}")
        print(f"Staging total rows: {staging_count}")
        print(f"Staging latest date: {staging_latest}")
        print(f"Inserted records: {inserted}")
        print(f"Updated records: {updated}")
        print(f"Unchanged records: {unchanged}")
        print("RAW classification check: PASS")
    except Exception as error:
        report["error_type"] = type(error).__name__
        raise
    finally:
        try:
            path = save_report(
                report, source_slug="sp500",
                report_folder=Path(__file__).resolve().parent.parent / "reconciliation_reports"
            )
            print(f"Reconciliation report: {path}")
        except OSError as report_error:
            print(f"Failed to save reconciliation report: {type(report_error).__name__}", file=sys.stderr)
            if report["status"] == "PASS":
                raise


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        print(f"S&P 500 update failed: {error}")
        sys.exit(1)

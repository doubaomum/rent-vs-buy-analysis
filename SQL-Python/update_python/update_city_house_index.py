"""Download/import Teranet C11 history into existing raw and staging tables.

Usage (PowerShell):
    python3 update_city_house_index.py --check-only
    python3 update_city_house_index.py
    python3 update_city_house_index.py --csv "House_Price_Index(4).csv"

By default, attempts a direct GET of the user-provided download address.
Use --check-only to verify downloading/parsing without accessing PostgreSQL.
Use --csv to import a local file instead of downloading.
Reads pg_password from API.env beside this script. Updates both tables in one
transaction; preserves all 61 raw columns and the original six-city staging rules.
Install the native certificate-store dependency with: python3 -m pip install truststore
"""

import argparse
import csv
import io
import os
import re
import ssl
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psycopg
import truststore
from psycopg import sql
from dotenv import load_dotenv
from reconciliation import new_report, check_classification, check_changed_count, save_report

GROUPS = (
    "c11", "bc_victoria", "bc_vancouver", "ab_calgary", "ab_edmonton",
    "mb_winnipeg", "on_hamilton", "on_toronto", "on_ottawa", "qc_montreal",
    "qc_quebec_city", "ns_halifax",
)
METRICS = ("index", "sa_index", "smoothed_index", "smoothed_sa_index", "sales_pair_count")
VALUE_COLUMNS = tuple(f"{group}_{metric}" for group in GROUPS for metric in METRICS)
RAW_COLUMNS = ("transaction_date",) + VALUE_COLUMNS
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
DOWNLOAD_URL = "https://housepriceindex.ca/_data/House_Price_Index.csv"
MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024


def parse_period(text):
    match = re.fullmatch(r"([A-Za-z]{3})-(\d{4})", (text or "").strip())
    if not match:
        raise ValueError(f"Unexpected month format: {text!r}; expected Mon-YYYY.")
    month_text, year = match.groups()
    try:
        month = tuple(m.lower() for m in MONTHS).index(month_text.lower()) + 1
    except ValueError:
        raise ValueError(f"Unknown month name: {month_text!r}.") from None
    return date(int(year), month, 1)


def read_source(path=None):
    """Flatten the two header rows, validating all fields without filling blanks."""
    if path is None:
        print("Downloading Teranet C11 history...")
        request = Request(DOWNLOAD_URL, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/csv,application/octet-stream;q=0.9,*/*;q=0.8",
        })
        # Native OS certificate validation can retrieve missing intermediates.
        # PROTOCOL_TLS_CLIENT retains certificate and hostname verification.
        tls_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with urlopen(request, timeout=30, context=tls_context) as response:
            body = response.read(MAX_DOWNLOAD_BYTES + 1)
        if len(body) > MAX_DOWNLOAD_BYTES:
            raise ValueError("The download exceeds the expected CSV size limit.")
        text = body.decode("utf-8-sig")
        if text.lstrip().lower().startswith(("<!doctype html", "<html")):
            raise ValueError("The download address returned an HTML webpage instead of CSV.")
        handle = io.StringIO(text, newline="")
    else:
        handle = path.open(encoding="utf-8-sig", newline="")

    with handle:
        reader = csv.reader(handle)
        first, second = next(reader, None), next(reader, None)
        if (
            first is None or second is None
            or len(first) != len(RAW_COLUMNS) or len(second) != len(RAW_COLUMNS)
            or first[0].strip().lower() != "transaction date"
            or second[0].strip()
        ):
            raise ValueError("Expected the Teranet C11 CSV with two header rows and 61 columns.")

        headers = ["transaction_date"]
        group = ""
        for top, bottom in zip(first[1:], second[1:]):
            if top.strip():
                group = top.strip().lower()
            metric = re.sub(r"\s+", "_", bottom.strip().lower())
            headers.append(f"{group}_{metric}")
        if len(set(headers)) != len(headers) or set(headers) != set(RAW_COLUMNS):
            raise ValueError("The CSV city names or index types do not match the existing raw schema.")

        result = {}
        missing_cells = 0
        for line_number, cells in enumerate(reader, start=3):
            if not cells or all(not cell.strip() for cell in cells):
                continue
            if len(cells) != len(headers):
                raise ValueError(f"CSV line {line_number} has an unexpected column count.")
            record = dict(zip(headers, cells))
            period = parse_period(record["transaction_date"])
            if period > date.today().replace(day=1):
                raise ValueError(f"CSV line {line_number} contains a future month.")
            if period in result:
                raise ValueError(f"Duplicate month in CSV: {period}.")

            cleaned = {}
            for column in VALUE_COLUMNS:
                text = record[column].strip().replace(",", "")
                if not text:
                    cleaned[column] = None
                    missing_cells += 1
                    continue
                value = Decimal(text)
                if not value.is_finite() or value < 0:
                    raise ValueError(f"Invalid value on CSV line {line_number}, column {column}.")
                if column.endswith("sales_pair_count") and value != value.to_integral_value():
                    raise ValueError(f"Non-integer sales count on CSV line {line_number}.")
                # Preserve real zeros; historical blanks remain NULL.
                cleaned[column] = text
            result[period] = cleaned

    if not result:
        raise ValueError("The CSV contains no data rows.")
    periods = sorted(result)
    expected_months = (
        (periods[-1].year - periods[0].year) * 12
        + periods[-1].month - periods[0].month + 1
    )
    if expected_months != len(periods):
        raise ValueError("The history CSV contains missing months.")
    return result, missing_cells


STAGING_SOURCE_FIELDS = (
    ("vancouver_index", "bc_vancouver_index"),
    ("calgary_index", "ab_calgary_index"),
    ("edmonton_index", "ab_edmonton_index"),
    ("toronto_index", "on_toronto_index"),
    ("ottawa_index", "on_ottawa_index"),
    ("montreal_index", "qc_montreal_index"),
)
REPORT_FOLDER = Path(__file__).resolve().parent.parent / "reconciliation_reports"


def numeric_value(value):
    """Use exact Decimal equality, preserving meaningful zero and NULL values."""
    if value is None or str(value).strip() == "":
        return None
    return Decimal(str(value).strip().replace(",", ""))


def read_raw_history(cur):
    """Load all source columns; detect duplicate logical months before any writes."""
    cur.execute(sql.SQL("SELECT {} FROM raw.city_house_price_index").format(
        sql.SQL(", ").join(map(sql.Identifier, RAW_COLUMNS))
    ))
    result = {}
    for label, *values in cur.fetchall():
        period = parse_period(label)
        if period in result:
            raise ValueError(f"Duplicate logical month in RAW: {period}")
        result[period] = (label, tuple(values))
    return result


def reconcile_source_raw(cur, source, start_date):
    """Compare every submitted source month and all 60 columns to committed-pending RAW."""
    actual = read_raw_history(cur)
    count = 0
    for period, source_values in source.items():
        if period < start_date:
            continue
        if period not in actual:
            raise ValueError(f"Source/RAW reconciliation missing month: {period}")
        stored_values = actual[period][1]
        for column, stored in zip(VALUE_COLUMNS, stored_values):
            if numeric_value(stored) != numeric_value(source_values[column]):
                raise ValueError(f"Source/RAW mismatch: {period}, {column}")
        count += 1
    return count


def reconcile_raw_staging(cur):
    """Compare the entire RAW history to the six-city STAGING projection."""
    raw = read_raw_history(cur)
    fields = tuple(name for name, _ in STAGING_SOURCE_FIELDS)
    cur.execute(sql.SQL("SELECT date_period, {} FROM stg.city_house_price_index").format(
        sql.SQL(", ").join(map(sql.Identifier, fields))
    ))
    staged = {}
    for period, *values in cur.fetchall():
        if period in staged:
            raise ValueError(f"Duplicate STAGING month: {period}")
        staged[period] = values
    if set(staged) != set(raw):
        missing = sorted(set(raw) - set(staged))[:3]
        extra = sorted(set(staged) - set(raw))[:3]
        raise ValueError(f"RAW/STAGING date mismatch: missing={missing}, extra={extra}")
    positions = {name: i for i, name in enumerate(VALUE_COLUMNS)}
    for period, (_, raw_values) in raw.items():
        for idx, (target_field, source_field) in enumerate(STAGING_SOURCE_FIELDS):
            if numeric_value(raw_values[positions[source_field]]) != numeric_value(staged[period][idx]):
                raise ValueError(f"RAW/STAGING mismatch: {period}, {target_field}")
    return len(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="Read a local CSV instead of downloading.")
    parser.add_argument("--check-only", action="store_true", help="Validate CSV without accessing the database.")
    args = parser.parse_args()
    input_path = args.csv.expanduser().resolve() if args.csv else None
    records, missing_cells = read_source(input_path)
    source_start, source_end = min(records), max(records)
    print(f"CSV observations processed: {len(records)}")
    print(f"CSV date range: {source_start} to {source_end}")
    print(f"Missing values retained as NULL: {missing_cells}")
    if args.check_only:
        print("CSV validation passed; the database was not accessed.")
        return

    report = new_report(
        source="Teranet", dataset="Teranet-National-Bank-C11",
        checks=("classification", "raw_change_count", "source_raw", "raw_staging"),
        extra_fields={"periodicity": "monthly", "raw_columns": len(RAW_COLUMNS),
                      "staging_cities": [name for name, _ in STAGING_SOURCE_FIELDS]},
    )
    report["records"].update(received=len(records), valid=len(records))
    try:
        sync_database(records, source_start, source_end, report)
    except Exception as error:
        report["error_type"] = type(error).__name__
        report["error_message"] = str(error)[:500]
        raise
    finally:
        try:
            output = save_report(report, "city_house_index", REPORT_FOLDER)
            print(f"Reconciliation report: {output}")
        except OSError as report_error:
            print(f"Could not save reconciliation report: {report_error}", file=sys.stderr)
            if report["status"] == "PASS":
                raise


def sync_database(records, source_start, source_end, report):
    load_dotenv(Path(__file__).resolve().parent / "API.env")
    password = os.getenv("pg_password", "")
    if not password:
        raise ValueError("Missing pg_password in API.env or the environment.")

    with psycopg.connect(
        host="localhost", port=5432, dbname="rentvsbuy", user="postgres",
        password=password, connect_timeout=10,
    ) as conn:
        with conn.cursor() as cur:
            before = read_raw_history(cur)
            existing_dates = {period: row[0] for period, row in before.items()}
            if existing_dates:
                if source_start > min(existing_dates):
                    raise ValueError("The CSV does not include the database's full existing history.")
                if source_end < max(existing_dates):
                    raise ValueError("The CSV is older than the database; download the latest file.")

            # Keep the database's current starting month and existing date spelling.
            start_date = min(existing_dates) if existing_dates else source_start
            rows = []
            for period in sorted(records):
                if period < start_date:
                    continue
                label = existing_dates.get(period, f"{MONTHS[period.month-1]}-{period.year:04d}")
                rows.append((label,) + tuple(records[period][c] for c in VALUE_COLUMNS))
            if not rows:
                raise ValueError("No CSV observations match the database date range.")

            # Classification is based on the same 60 stored fields used in UPSERT.
            inserted = updated = unchanged = 0
            for period, values in sorted(records.items()):
                if period < start_date:
                    continue
                if period not in before:
                    inserted += 1
                elif any((stored is None) != (values[column] is None)
                         or (stored is not None and values[column] is not None
                             and str(stored) != str(values[column]))
                         for column, stored in zip(VALUE_COLUMNS, before[period][1])):
                    updated += 1
                else:
                    unchanged += 1
            check_classification(len(rows), inserted, updated, unchanged)
            report["records"]["valid"] = len(rows)
            report["records"]["excluded_before_database_start"] = len(records) - len(rows)
            report["planned_raw_changes"] = {
                "inserted": inserted, "updated": updated, "unchanged": unchanged,
            }
            report["checks"]["classification"] = "PASS"

            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_city_house_index_raw_period
                ON raw.city_house_price_index (transaction_date);
            """)
            query = sql.SQL("""
                INSERT INTO raw.city_house_price_index AS target ({columns})
                VALUES ({placeholders})
                ON CONFLICT (transaction_date)
                DO UPDATE SET {assignments}
                WHERE ({target_values}) IS DISTINCT FROM ({incoming_values});
            """).format(
                columns=sql.SQL(", ").join(map(sql.Identifier, RAW_COLUMNS)),
                placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in RAW_COLUMNS),
                assignments=sql.SQL(", ").join(
                    sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c))
                    for c in VALUE_COLUMNS
                ),
                target_values=sql.SQL(", ").join(
                    sql.SQL("target.{}").format(sql.Identifier(c)) for c in VALUE_COLUMNS
                ),
                incoming_values=sql.SQL(", ").join(
                    sql.SQL("EXCLUDED.{}").format(sql.Identifier(c)) for c in VALUE_COLUMNS
                ),
            )
            cur.executemany(query, rows)
            raw_changed = cur.rowcount
            check_changed_count(raw_changed, inserted, updated)
            report["checks"]["raw_change_count"] = "PASS"
            cur.execute("""
                SELECT COUNT(*), MAX(TO_DATE(TRIM(transaction_date), 'Mon-YYYY'))
                FROM raw.city_house_price_index;
            """)
            raw_count, raw_latest = cur.fetchone()

            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_city_house_index_period
                ON stg.city_house_price_index (date_period);
            """)
            cur.execute("""
                INSERT INTO stg.city_house_price_index AS target (
                    date_period, vancouver_index, calgary_index, edmonton_index,
                    toronto_index, ottawa_index, montreal_index
                )
                SELECT
                    TO_DATE(TRIM(transaction_date), 'Mon-YYYY'),
                    NULLIF(REPLACE(TRIM(bc_vancouver_index), ',', ''), '')::numeric,
                    NULLIF(REPLACE(TRIM(ab_calgary_index), ',', ''), '')::numeric,
                    NULLIF(REPLACE(TRIM(ab_edmonton_index), ',', ''), '')::numeric,
                    NULLIF(REPLACE(TRIM(on_toronto_index), ',', ''), '')::numeric,
                    NULLIF(REPLACE(TRIM(on_ottawa_index), ',', ''), '')::numeric,
                    NULLIF(REPLACE(TRIM(qc_montreal_index), ',', ''), '')::numeric
                FROM raw.city_house_price_index
                WHERE TRUE
                ON CONFLICT (date_period)
                DO UPDATE SET
                    vancouver_index = EXCLUDED.vancouver_index,
                    calgary_index = EXCLUDED.calgary_index,
                    edmonton_index = EXCLUDED.edmonton_index,
                    toronto_index = EXCLUDED.toronto_index,
                    ottawa_index = EXCLUDED.ottawa_index,
                    montreal_index = EXCLUDED.montreal_index
                WHERE (
                    target.vancouver_index, target.calgary_index, target.edmonton_index,
                    target.toronto_index, target.ottawa_index, target.montreal_index
                ) IS DISTINCT FROM (
                    EXCLUDED.vancouver_index, EXCLUDED.calgary_index, EXCLUDED.edmonton_index,
                    EXCLUDED.toronto_index, EXCLUDED.ottawa_index, EXCLUDED.montreal_index
                );
            """)
            staging_changed = cur.rowcount
            cur.execute("SELECT COUNT(*), MAX(date_period) FROM stg.city_house_price_index;")
            staging_count, staging_latest = cur.fetchone()

            # Validate both transformations before the connection commits.
            n = reconcile_source_raw(cur, records, start_date)
            report["checks"]["source_raw"] = "PASS"
            print(f"Teranet/RAW reconciliation: PASS ({n} months verified)")
            m = reconcile_raw_staging(cur)
            report["checks"]["raw_staging"] = "PASS"
            print(f"RAW/STAGING reconciliation: PASS ({m} months verified)")

    report["transaction_committed"] = True
    report["committed_raw_changes"] = dict(report["planned_raw_changes"])
    report["database"] = {
        "raw_changed_rows": raw_changed, "raw_total_rows": raw_count,
        "raw_latest_date": raw_latest.isoformat() if raw_latest else None,
        "staging_changed_rows": staging_changed, "staging_total_rows": staging_count,
        "staging_latest_date": staging_latest.isoformat() if staging_latest else None,
    }
    report["status"] = "PASS"
    print("City house price index update committed successfully.")
    print(f"Inserted records: {inserted}")
    print(f"Updated records: {updated}")
    print(f"Unchanged records: {unchanged}")
    print("RAW classification check: PASS")
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
        print(f"Download failed. HTTP status: {error.code}. No database update attempted.", file=sys.stderr)
        sys.exit(1)
    except URLError as error:
        print(f"Download connection failed: {error.reason!r}. No database update attempted.", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as error:
        print(f"Download timed out: {error}. No database update attempted.", file=sys.stderr)
        sys.exit(1)
    except psycopg.Error as error:
        print(f"Database operation failed: {error}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, InvalidOperation, OSError, csv.Error) as error:
        print(f"City house price index update failed: {error}", file=sys.stderr)
        sys.exit(1)

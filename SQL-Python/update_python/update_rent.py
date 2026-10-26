r"""CMHC annual October rent history -> raw.city_rent_raw -> stg.city_rent.

Run: python3 .\update_rent.py
Dependencies: beautifulsoup4, truststore, psycopg[binary], python-dotenv.
Read public HTML table 2.2.11 using Row / Apartment and October, matching
the supplied Toronto URL. No API key, generated months, or estimates.
Raw keeps bedroom-specific rents and quality flags; staging uses Total rent.
Blank dates are left untouched. Suppression markers remain in raw and become
NULL in staging. All seven locations must be downloaded before database access.
"""

from datetime import date
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import ssl
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from reconciliation import new_report, check_classification, check_changed_count, save_report

from bs4 import BeautifulSoup
import truststore

BASE_URL = "https://www03.cmhc-schl.gc.ca/hmip-pimh/en/TableMapChart/Table"
# CMHC portal IDs, not Statistics Canada CMA IDs. Keep leading zeroes.
LOCATIONS = {
    "Canada": ("1", 1, "Canada"),
    "Vancouver": ("2410", 3, "Vancouver"),
    "Calgary": ("0140", 3, "Calgary"),
    "Edmonton": ("0340", 3, "Edmonton"),
    "Toronto": ("2270", 3, "Toronto"),
    "Ottawa": ("1265", 3, "Ottawa"),
    "Montreal": ("1060", 3, "Montréal"),
}
BEDROOMS = ("studio", "one_bedroom", "two_bedroom", "three_bedroom_plus", "total")
VALUE_COLUMNS = tuple(f"{b}_{kind}" for b in BEDROOMS for kind in ("rent", "flag"))
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")
MISSING = {"", "**", "..", "...", "-", "--", "na", "n/a"}
DATE_SQL = "TO_DATE(TRIM(rent_period), 'YYYY Month')"
RENT_SQL = """CASE WHEN LOWER(BTRIM(total_rent)) IN
              ('**', '..', '...', '-', '--', 'na', 'n/a') THEN NULL
              ELSE NULLIF(REPLACE(TRIM(total_rent), ',', ''), '')::numeric END"""


def parse_period(label):
    match = re.fullmatch(r"(\d{4})\s+([A-Za-z]+)", str(label).strip())
    if not match:
        raise ValueError(f"Unexpected rent period {label!r}; expected YYYY Month.")
    year, month = match.groups()
    try:
        month_num = tuple(m.lower() for m in MONTHS).index(month.lower()) + 1
    except ValueError:
        raise ValueError(f"Unknown month in {label!r}.") from None
    return date(int(year), month_num, 1)


def rent_number(value):
    text = ("" if value is None else str(value)).strip().replace(",", "")
    if text.lower() in MISSING:
        return None
    number = Decimal(text)
    if not number.is_finite() or number <= 0:
        raise ValueError(f"Invalid rent value: {text!r}.")
    return number


def parse_page(body, city):
    gid, geo_type, source_name = LOCATIONS[city]
    soup = BeautifulSoup(body, "html.parser")
    model_node = soup.select_one("#serialized-model")
    if model_node is None:
        raise ValueError(f"{city}: CMHC did not return the expected table page.")
    model = json.loads(model_node.get("data-table-model", "null"))
    if isinstance(model, str):
        model = json.loads(model)
    if not isinstance(model, dict):
        raise ValueError(f"{city}: missing CMHC table metadata.")
    expected = {
        "TableId": "2.2.11", "GeographyId": gid, "GeographyTypeId": geo_type,
        "GeograghyName": source_name, "DefaultDataField": "average_rent_amt",
    }
    if any(model.get(k) != v for k, v in expected.items()):
        raise ValueError(f"{city}: source geography or rent measure changed.")
    filters = {f["Key"]: f["Value"] for f in model.get("AppliedFilters", [])}
    if filters.get("dwelling_type_desc_en") != "Row / Apartment" or filters.get("season") != "October":
        raise ValueError(f"{city}: expected Row / Apartment, October; received {filters}.")
    tables = soup.select("table.CawdDataTable")
    if len(tables) != 1:
        raise ValueError(f"{city}: expected one historical rent table.")
    table = tables[0]
    headers = [h.get_text(" ", strip=True) for h in table.select("thead th")]
    if headers != ["Studio", "1 Bedroom", "2 Bedroom", "3 Bedroom +", "Total"]:
        raise ValueError(f"{city}: unexpected bedroom columns.")
    records = {}
    missing_count = 0
    for row in table.select("tbody tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) != 11 or [c.get("data-field") for c in cells] != [
                "survey_date_surrkey"] + [f"cell-{n}" for n in range(1, 11)]:
            raise ValueError(f"{city}: rent/quality column layout changed.")
        period = parse_period(cells[0].get_text(" ", strip=True))
        if period.month != 10 or period > date.today().replace(day=1) or period in records:
            raise ValueError(f"{city}: unexpected or duplicate survey period {period}.")
        values = []
        for rent_cell, flag_cell in zip(cells[1::2], cells[2::2]):
            rent_text = rent_cell.get_text(" ", strip=True)
            flag = flag_cell.get_text(" ", strip=True) or None
            number = rent_number(rent_text)
            if number is None:
                missing_count += 1
                # Preserve published markers such as **, not a fabricated zero.
                values.extend((rent_text or None, flag))
            else:
                values.extend((format(number, "f"), flag))
        records[period] = tuple(values)
    if not records:
        raise ValueError(f"{city}: no rent observations returned.")
    return records, missing_count


def download_all():
    records = {}
    missing_count = 0
    context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    for city, (gid, geo_type, _) in LOCATIONS.items():
        print(f"Fetching CMHC rent history: {city}...", flush=True)
        url = BASE_URL + "?" + urlencode({
            "TableId": "2.2.11", "GeographyId": gid,
            "GeographyTypeId": geo_type, "DisplayAs": "Table",
        })
        request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-CA,en;q=0.9"})
        with urlopen(request, timeout=30, context=context) as response:
            body = response.read(10 * 1024 * 1024 + 1)
        if len(body) > 10 * 1024 * 1024:
            raise ValueError(f"{city}: unexpected source size.")
        history, missing = parse_page(body, city)
        records[city] = history
        missing_count += missing
        print(f"  {len(history)} survey periods; latest: {max(history)}", flush=True)
    return records, missing_count


def normalized_raw_field(value):
    """Mirror RAW UPSERT text comparison: trim whitespace and remove commas."""
    if value is None:
        return None
    normalized = str(value).strip().replace(",", "")
    return normalized or None


def normalized_record(values):
    return tuple(normalized_raw_field(v) for v in values)


def sync_database(source, report):
    import psycopg
    from psycopg import sql
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / "API.env")
    password = os.getenv("pg_password", "")
    if not password:
        raise ValueError("Missing pg_password in API.env.")
    with psycopg.connect(host="localhost", port=5432, dbname="rentvsbuy", user="postgres",
                         password=password, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT city, rent_period, {} FROM raw.city_rent_raw;")
                        .format(sql.SQL(", ").join(map(sql.Identifier, VALUE_COLUMNS))))
            existing, city_periods, prior_values = {}, {}, {}
            for city, label, *values in cur.fetchall():
                if city not in LOCATIONS or label is None or not str(label).strip():
                    continue
                period = parse_period(label)
                if (city, period) in existing:
                    raise ValueError(f"Duplicate dated raw rent records: {city}, {period}.")
                existing[(city, period)] = label
                prior_values[(city, period)] = normalized_record(values)
                city_periods.setdefault(city, []).append(period)
                # All undated rows and existing April observations stay intact.
                rents = [rent_number(values[n]) for n in range(0, 10, 2)]
                if period.month == 10 and period not in source[city] and any(v is not None for v in rents):
                    raise ValueError(
                        f"{city}: the downloaded source omits stored non-missing period {period}. "
                        "No database update was made."
                    )
            incoming = []
            for city, history in source.items():
                start = min(city_periods[city]) if city in city_periods else min(history)
                for period, values in sorted(history.items()):
                    if period >= start:
                        label = existing.get((city, period), f"{period.year} October")
                        incoming.append((city, label) + values)
            if not incoming:
                raise ValueError("No published observations match the existing history range.")

            # Classify the same normalized text fields used by RAW's UPSERT.
            inserted = updated = unchanged = 0
            planned_changes = []
            for city, label, *values in incoming:
                key = (city, parse_period(label))
                old = prior_values.get(key)
                new = normalized_record(values)
                if old is None:
                    inserted += 1
                    planned_changes.append({"city": city, "period": key[1].isoformat(), "action": "INSERT"})
                elif old != new:
                    updated += 1
                    planned_changes.append({"city": city, "period": key[1].isoformat(), "action": "UPDATE"})
                else:
                    unchanged += 1
            check_classification(len(incoming), inserted, updated, unchanged)
            report["checks"]["classification"] = "PASS"
            report["planned_raw_changes"] = dict(inserted=inserted, updated=updated, unchanged=unchanged)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_city_rent_raw_dated_period
                ON raw.city_rent_raw (city, rent_period)
                WHERE NULLIF(BTRIM(rent_period), '') IS NOT NULL;
            """)
            columns = ("city", "rent_period") + VALUE_COLUMNS
            query = sql.SQL("""
                INSERT INTO raw.city_rent_raw AS target ({columns}) VALUES ({placeholders})
                ON CONFLICT (city, rent_period)
                WHERE NULLIF(BTRIM(rent_period), '') IS NOT NULL
                DO UPDATE SET {assignments}
                WHERE ({old}) IS DISTINCT FROM ({new});
            """).format(
                columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
                placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
                assignments=sql.SQL(", ").join(sql.SQL("{} = EXCLUDED.{}").format(
                    sql.Identifier(c), sql.Identifier(c)) for c in VALUE_COLUMNS),
                old=sql.SQL(", ").join(sql.SQL("NULLIF(REPLACE(BTRIM(target.{}), ',', ''), '')")
                    .format(sql.Identifier(c)) for c in VALUE_COLUMNS),
                new=sql.SQL(", ").join(sql.SQL("EXCLUDED.{}").format(sql.Identifier(c))
                    for c in VALUE_COLUMNS),
            )
            cur.executemany(query, incoming)
            raw_changed = cur.rowcount
            check_changed_count(raw_changed, inserted, updated)
            report["checks"]["raw_change_count"] = "PASS"
            cur.execute("SELECT COUNT(*) FROM raw.city_rent_raw;")
            raw_count = cur.fetchone()[0]
            cur.execute(sql.SQL("""
                SELECT COUNT(*), MAX({date}) FROM raw.city_rent_raw
                WHERE NULLIF(BTRIM(rent_period), '') IS NOT NULL;
            """).format(date=sql.SQL(DATE_SQL)))
            raw_dated, raw_latest = cur.fetchone()
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_city_rent_period
                ON stg.city_rent (date_period);
            """)
            stage_columns = tuple(f"{city.lower()}_price" for city in LOCATIONS)
            cur.execute(sql.SQL("""
                INSERT INTO stg.city_rent AS target (date_period, {columns})
                SELECT {date}, {pivot} FROM raw.city_rent_raw
                WHERE NULLIF(BTRIM(rent_period), '') IS NOT NULL AND city = ANY(%s)
                GROUP BY {date}
                ON CONFLICT (date_period) DO UPDATE SET {assignments}
                WHERE ({old}) IS DISTINCT FROM ({new});
            """).format(
                columns=sql.SQL(", ").join(map(sql.Identifier, stage_columns)),
                date=sql.SQL(DATE_SQL),
                pivot=sql.SQL(", ").join(sql.SQL("MAX(CASE WHEN city = {} THEN {} END)")
                    .format(sql.Literal(city), sql.SQL(RENT_SQL)) for city in LOCATIONS),
                assignments=sql.SQL(", ").join(sql.SQL("{} = EXCLUDED.{}").format(
                    sql.Identifier(c), sql.Identifier(c)) for c in stage_columns),
                old=sql.SQL(", ").join(sql.SQL("target.{}").format(sql.Identifier(c))
                    for c in stage_columns),
                new=sql.SQL(", ").join(sql.SQL("EXCLUDED.{}").format(sql.Identifier(c))
                    for c in stage_columns),
            ), (list(LOCATIONS),))
            stage_changed = cur.rowcount
            cur.execute("SELECT COUNT(*), MAX(date_period) FROM stg.city_rent;")
            stage_count, stage_latest = cur.fetchone()

            # Reconcile the 10 published RAW fields for every processed city/month.
            # This does not compare the raw city/month row count with pivoted STAGING.
            cur.execute(sql.SQL("SELECT city, rent_period, {} FROM raw.city_rent_raw WHERE city = ANY(%s);")
                        .format(sql.SQL(", ").join(map(sql.Identifier, VALUE_COLUMNS))), (list(LOCATIONS),))
            stored = {}
            for city, label, *values in cur.fetchall():
                if label is None or not str(label).strip():
                    continue
                key = (city, parse_period(label))
                if key in stored:
                    raise ValueError(f"Duplicate RAW city/month during reconciliation: {key}")
                stored[key] = normalized_record(values)
            source_mismatches = sum(
                stored.get((city, parse_period(label))) != normalized_record(values)
                for city, label, *values in incoming
            )
            if source_mismatches:
                raise ValueError(f"CMHC/RAW reconciliation failed: {source_mismatches} mismatches")
            report["checks"]["source_raw"] = "PASS"
            print(f"CMHC/RAW reconciliation: PASS ({len(incoming)} city-months verified)")

            # Recompute the exact RAW-to-STAGING pivot and verify its rows.
            # Existing STAGING-only legacy dates are left untouched, as before.
            cur.execute(sql.SQL("""
                WITH expected AS (
                    SELECT {date} AS period, {pivot}
                    FROM raw.city_rent_raw
                    WHERE NULLIF(BTRIM(rent_period), '') IS NOT NULL AND city = ANY(%s)
                    GROUP BY {date}
                )
                SELECT COUNT(*)
                FROM expected e
                LEFT JOIN stg.city_rent s ON s.date_period = e.period
                WHERE s.date_period IS NULL OR ({actual}) IS DISTINCT FROM ({expected});
            """).format(
                date=sql.SQL(DATE_SQL),
                pivot=sql.SQL(", ").join(sql.SQL("MAX(CASE WHEN city = {} THEN {} END) AS {}")
                    .format(sql.Literal(city), sql.SQL(RENT_SQL), sql.Identifier(col))
                    for city, col in zip(LOCATIONS, stage_columns)),
                actual=sql.SQL(", ").join(sql.SQL("s.{}").format(sql.Identifier(col)) for col in stage_columns),
                expected=sql.SQL(", ").join(sql.SQL("e.{}").format(sql.Identifier(col)) for col in stage_columns),
            ), (list(LOCATIONS),))
            stage_mismatches = cur.fetchone()[0]
            if stage_mismatches:
                raise ValueError(f"RAW/STAGING reconciliation failed: {stage_mismatches} mismatches")
            report["checks"]["raw_staging"] = "PASS"
            print("RAW/STAGING reconciliation: PASS")

    # The connection context has committed; only now publish completed changes.
    report["transaction_committed"] = True
    report["committed_raw_changes"] = dict(report["planned_raw_changes"])
    report["status"] = "PASS"
    report["database"] = {
        "raw_changed_rows": raw_changed, "raw_total_rows": raw_count,
        "raw_dated_rows": raw_dated,
        "raw_latest_date": raw_latest.isoformat() if raw_latest else None,
        "staging_changed_rows": stage_changed, "staging_total_rows": stage_count,
        "staging_latest_date": stage_latest.isoformat() if stage_latest else None,
    }
    report["change_summary_by_city"] = {
        city: {
            "inserted": sum(c["city"] == city and c["action"] == "INSERT" for c in planned_changes),
            "updated": sum(c["city"] == city and c["action"] == "UPDATE" for c in planned_changes),
        }
        for city in LOCATIONS
    }
    print("CMHC rent database update committed successfully.")
    print(f"Observations processed for the existing history range: {len(incoming)}")
    print(f"Inserted records: {inserted}")
    print(f"Updated records: {updated}")
    print(f"Unchanged records: {unchanged}")
    print("RAW classification check: PASS")
    print(f"Raw rows inserted or updated: {raw_changed}")
    print(f"Raw total rows: {raw_count}")
    print(f"Raw dated rows: {raw_dated}")
    print(f"Raw latest date: {raw_latest}")
    print(f"Staging rows inserted or updated: {stage_changed}")
    print(f"Staging total rows: {stage_count}")
    print(f"Staging latest date: {stage_latest}")


def main():
    report = new_report(
        "CMHC", "Annual October Row / Apartment Average Rent (Table 2.2.11)",
        ("classification", "raw_change_count", "source_raw", "raw_staging"),
    )
    report["reconciliation_scope"] = (
        "Processed city-month source rows -> RAW; dates represented by known-city RAW "
        "-> pivoted STAGING. Preserves undated records and legacy stage-only dates."
    )
    try:
        source, missing = download_all()
        fetched = sum(map(len, source.values()))
        print(f"Published city-period observations fetched: {fetched}")
        print(f"Missing or suppressed rent cells: {missing}")
        report["records"].update(received=fetched, valid=fetched, missing_skipped=0, rejected=0)
        report["missing_or_suppressed_rent_cells"] = missing
        report["source_city_month_counts"] = {city: len(history) for city, history in source.items()}
        sync_database(source, report)
    except Exception as error:
        report["error_type"] = type(error).__name__
        raise
    finally:
        try:
            path = save_report(
                report, "rent", Path(__file__).resolve().parent.parent / "reconciliation_reports"
            )
            print(f"Reconciliation report: {path}")
        except OSError as report_error:
            print(f"Failed to save reconciliation report: {type(report_error).__name__}", file=sys.stderr)
            if report["status"] == "PASS":
                raise


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"CMHC rent update failed: {error}")
        sys.exit(1)

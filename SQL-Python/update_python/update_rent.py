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


def sync_database(source):
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
            existing, city_periods = {}, {}
            for city, label, *values in cur.fetchall():
                if city not in LOCATIONS or label is None or not str(label).strip():
                    continue
                period = parse_period(label)
                if (city, period) in existing:
                    raise ValueError(f"Duplicate dated raw rent records: {city}, {period}.")
                existing[(city, period)] = label
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
    print("CMHC rent database update committed successfully.")
    print(f"Observations processed for the existing history range: {len(incoming)}")
    print(f"Raw rows inserted or updated: {raw_changed}")
    print(f"Raw total rows: {raw_count}")
    print(f"Raw dated rows: {raw_dated}")
    print(f"Raw latest date: {raw_latest}")
    print(f"Staging rows inserted or updated: {stage_changed}")
    print(f"Staging total rows: {stage_count}")
    print(f"Staging latest date: {stage_latest}")


def main():
    source, missing = download_all()
    print(f"Published city-period observations fetched: {sum(map(len, source.values()))}")
    print(f"Missing or suppressed rent cells: {missing}")
    sync_database(source)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"CMHC rent update failed: {error}")
        sys.exit(1)

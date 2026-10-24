r"""Refresh owner inputs and recursive results in one transaction.

Read 05_*.sql from ../create_SQL and calculations from ../simulation_python.
Keep API.env beside this file in update_python/.
Run from SQL-Python: python3 .\update_python\update_owner.py
"""

import os
from pathlib import Path
import sys
from time import monotonic

import numpy as np
import pandas as pd
import psycopg
from psycopg import sql
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
SQL_DIR = PROJECT_DIR / "create_SQL"
CALC_DIR = PROJECT_DIR / "simulation_python"
# Resolve the sibling modules independently of the current working directory.
sys.path.insert(0, str(CALC_DIR))

from owner_calculations import calculate_owner_batch
CITIES = ("Canada", "Vancouver", "Calgary", "Edmonton", "Toronto", "Ottawa", "Montreal")
BATCH_SIZE = 100  # A scenario's entire history always stays in one batch.
RESULT_COLUMNS = (
    "mortgage_payment", "mortgage_interest", "mortgage_principal", "mortgage_balance",
    "owner_monthly_unrecoverable_cost", "cumulative_unrecoverable_cost", "owner_net_worth",
)
CALC_COLUMNS = (
    "scenario_id", "date_period", "month_number", "initial_loan_after_insurance",
    "amortization_years", "mortgage_term_year", "applied_mortgage_rate",
    "maintenance_cost", "property_cost", "insurance_cost", "purchase_cost", "sale_cost",
    "house_price_market", "house_price_sold", "estimated_current_sale_cost", "is_sale_month",
)


def choose_cutoff(cur):
    """Use the latest coverage shared by the seven cities and mortgage history.

    Gaps within that range are rejected later, rather than filled or interpolated.
    The original last-available-rate-at-term-start lookup is retained.
    """
    cur.execute("""
        SELECT city, date_period FROM analysis.city_house_prices_long
        WHERE city = ANY(%s) AND date_period IS NOT NULL
        GROUP BY city, date_period HAVING COUNT(*) > 1 LIMIT 1
    """, (list(CITIES),))
    if cur.fetchone():
        raise ValueError("analysis.city_house_prices_long contains duplicate city/date keys.")
    cur.execute("""
        SELECT date_period FROM stg.canada_5yearmortgage
        WHERE date_period IS NOT NULL
        GROUP BY date_period HAVING COUNT(*) > 1 LIMIT 1
    """)
    if cur.fetchone():
        raise ValueError("stg.canada_5yearmortgage contains duplicate dates.")
    cur.execute("""
        SELECT 1 FROM analysis.city_house_prices_long
        WHERE city = ANY(%s) AND date_period IS NOT NULL
          AND (date_period <> date_trunc('month', date_period)::date
               OR (price IS NOT NULL AND (price <= 0 OR price::text IN ('NaN','Infinity','-Infinity'))))
        LIMIT 1
    """, (list(CITIES),))
    if cur.fetchone():
        raise ValueError("House prices must have month-start dates and finite positive prices.")
    cur.execute("""
        SELECT 1 FROM stg.canada_5yearmortgage
        WHERE date_period IS NOT NULL AND mortgage_rate IS NOT NULL
          AND (mortgage_rate < 0 OR mortgage_rate::text IN ('NaN','Infinity','-Infinity'))
        LIMIT 1
    """)
    if cur.fetchone():
        raise ValueError("Mortgage history contains a negative or nonfinite rate.")
    cur.execute("""
        SELECT city, MAX(date_period) FROM analysis.city_house_prices_long
        WHERE city = ANY(%s) AND date_period IS NOT NULL AND price IS NOT NULL
        GROUP BY city
    """, (list(CITIES),))
    latest = dict(cur.fetchall())
    missing = set(CITIES) - set(latest)
    if missing:
        raise ValueError("Missing city price history: " + ", ".join(sorted(missing)))
    cur.execute("""
        SELECT date_trunc('month', MAX(date_period))::date
        FROM stg.canada_5yearmortgage
        WHERE date_period IS NOT NULL AND mortgage_rate IS NOT NULL
    """)
    mortgage_latest = cur.fetchone()[0]
    if mortgage_latest is None:
        raise ValueError("No dated mortgage rates are available.")
    cutoff = min(*latest.values(), mortgage_latest)
    print(f"Latest mortgage input: {mortgage_latest}", flush=True)
    print(f"Latest house input shared by all seven cities: {min(latest.values())}", flush=True)
    print(f"Owner cutoff determined from inputs: {cutoff}", flush=True)
    return cutoff


def validate_scenarios(cur):
    cur.execute("SELECT COUNT(*) FROM _owner_refresh_ids")
    count = cur.fetchone()[0]
    if not count:
        raise ValueError("No scenarios have both purchase and sale prices in the available range.")
    cur.execute("""
        SELECT b.scenario_id FROM simulation.owner_basic_model b
        JOIN _owner_refresh_ids r USING (scenario_id)
        WHERE b.house_price_buy <= 0 OR b.house_price_sold <= 0
           OR b.initial_loan_after_insurance IS NULL OR b.initial_loan_after_insurance < 0
           OR b.mortgage_term_year <= 0 OR b.amortization_years <= 0
           OR b.property_tax_rate IS NULL OR b.property_tax_rate < 0
           OR b.structure_ratio IS NULL OR b.structure_ratio < 0 OR b.structure_ratio > 1
           OR b.sold_date <= b.buying_date
        LIMIT 1
    """)
    invalid = cur.fetchone()
    if invalid:
        raise ValueError(f"Invalid owner assumptions in scenario {invalid[0]}.")
    # Never silently remove existing parent keys that a renter may reference.
    cur.execute("""
        SELECT m.scenario_id, m.date_period FROM simulation.owner_monthly_schedule m
        JOIN _owner_refresh_ids r USING (scenario_id)
        JOIN simulation.owner_basic_model b USING (scenario_id)
        WHERE m.date_period < b.buying_date OR m.date_period > b.sold_date
           OR m.date_period <> date_trunc('month', m.date_period)::date
        LIMIT 1
    """)
    invalid = cur.fetchone()
    if invalid:
        raise ValueError(f"Existing owner month lies outside its scenario: {invalid}. No keys were deleted.")
    return count


def validate_input_batch(cur):
    required = (
        "house_price_market", "house_price_sold", "initial_loan_after_insurance",
        "applied_mortgage_rate", "maintenance_cost", "property_cost", "insurance_cost",
        "purchase_cost", "sale_cost", "estimated_current_sale_cost",
    )
    invalid = sql.SQL(" OR ").join(
        sql.SQL("{c} IS NULL OR {c}::text IN ('NaN','Infinity','-Infinity')").format(c=sql.Identifier(c))
        for c in required
    )
    cur.execute(sql.SQL("SELECT scenario_id, date_period FROM _owner_input WHERE {} LIMIT 1").format(invalid))
    row = cur.fetchone()
    if row:
        raise ValueError(f"Missing or nonfinite monthly input at scenario/date {row}; no zero filling was applied.")
    cur.execute("""
        SELECT scenario_id FROM _owner_input
        GROUP BY scenario_id
        HAVING MIN(month_number) <> 0 OR MAX(month_number) + 1 <> COUNT(*)
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        raise ValueError(f"Monthly history is incomplete in scenario {row[0]}.")


def upsert_monthly_inputs(cur, columns):
    keys = ("scenario_id", "date_period")
    values = [c for c in columns if c not in keys]
    assignments = sql.SQL(", ").join(
        sql.SQL("{c} = EXCLUDED.{c}").format(c=sql.Identifier(c)) for c in values
    )
    old = sql.SQL(", ").join(sql.SQL("target.{}").format(sql.Identifier(c)) for c in values)
    new = sql.SQL(", ").join(sql.SQL("EXCLUDED.{}").format(sql.Identifier(c)) for c in values)
    cur.execute(sql.SQL("""
        INSERT INTO simulation.owner_monthly_schedule AS target ({columns})
        SELECT {columns} FROM _owner_input WHERE TRUE
        ON CONFLICT (scenario_id, date_period) DO UPDATE SET {assignments}
        WHERE ROW({old}) IS DISTINCT FROM ROW({new})
    """).format(columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
                   assignments=assignments, old=old, new=new))
    return cur.rowcount


def write_results(cur, results):
    if not np.isfinite(results[list(RESULT_COLUMNS)].to_numpy(dtype=float)).all():
        raise ValueError("The owner calculation produced a nonfinite result.")
    cur.execute("TRUNCATE _owner_results")
    with cur.copy("""COPY _owner_results (
        scenario_id, date_period, mortgage_payment, mortgage_interest, mortgage_principal,
        mortgage_balance, owner_monthly_unrecoverable_cost, cumulative_unrecoverable_cost,
        owner_net_worth) FROM STDIN""") as copy:
        for row in results.itertuples(index=False, name=None):
            copy.write_row(row)
    cur.execute("ANALYZE _owner_results")
    assignments = sql.SQL(", ").join(
        sql.SQL("{c} = source.{c}").format(c=sql.Identifier(c)) for c in RESULT_COLUMNS
    )
    old = sql.SQL(", ").join(sql.SQL("target.{}").format(sql.Identifier(c)) for c in RESULT_COLUMNS)
    new = sql.SQL(", ").join(sql.SQL("source.{}").format(sql.Identifier(c)) for c in RESULT_COLUMNS)
    cur.execute(sql.SQL("""
        UPDATE simulation.owner_monthly_schedule AS target SET {assignments}
        FROM _owner_results AS source
        WHERE target.scenario_id = source.scenario_id AND target.date_period = source.date_period
          AND ROW({old}) IS DISTINCT FROM ROW({new})
    """).format(assignments=assignments, old=old, new=new))
    return cur.rowcount


def refresh_owner(conn):
    scenario_script = (SQL_DIR / "05_refresh_owner_scenarios.sql").read_text(encoding="utf-8-sig")
    month_script = (SQL_DIR / "05_refresh_owner_months.sql").read_text(encoding="utf-8-sig")
    with conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_xact_lock(726562, 5)")
        if not cur.fetchone()[0]:
            raise ValueError("Another simulation refresh is already running.")
        cutoff = choose_cutoff(cur)
        cur.execute("CREATE TEMP TABLE _owner_refresh_config (cutoff DATE NOT NULL) ON COMMIT DROP")
        cur.execute("INSERT INTO _owner_refresh_config VALUES (%s)", (cutoff,))
        print("Refreshing owner scenarios; existing IDs are retained...", flush=True)
        cur.execute(scenario_script, prepare=False)
        count = validate_scenarios(cur)
        cur.execute("SELECT COUNT(*) FROM simulation.owner_basic_model")
        outside_scope = cur.fetchone()[0] - count
        cur.execute("SELECT scenario_id FROM _owner_refresh_ids ORDER BY scenario_id")
        ids = [row[0] for row in cur.fetchall()]
        cur.execute("""
            CREATE TEMP TABLE _owner_batch_ids (scenario_id BIGINT PRIMARY KEY) ON COMMIT DROP;
            CREATE TEMP TABLE _owner_input
                (LIKE simulation.owner_monthly_schedule INCLUDING DEFAULTS) ON COMMIT DROP;
            CREATE TEMP TABLE _owner_results ON COMMIT DROP AS
            SELECT scenario_id, date_period, mortgage_payment, mortgage_interest, mortgage_principal,
                   mortgage_balance, owner_monthly_unrecoverable_cost,
                   cumulative_unrecoverable_cost, owner_net_worth
            FROM simulation.owner_monthly_schedule WITH NO DATA;
            CREATE UNIQUE INDEX ON _owner_results (scenario_id, date_period);
        """, prepare=False)
        cur.execute("SELECT * FROM _owner_input LIMIT 0")
        input_columns = [c.name for c in cur.description if c.name not in RESULT_COLUMNS]
        rows_processed = input_changes = result_changes = 0
        last_progress = monotonic()
        print(f"Recalculating {count:,} complete scenarios in batches of {BATCH_SIZE}...", flush=True)
        for offset in range(0, count, BATCH_SIZE):
            batch = ids[offset:offset + BATCH_SIZE]
            cur.execute("TRUNCATE _owner_batch_ids")
            cur.executemany("INSERT INTO _owner_batch_ids VALUES (%s)", [(i,) for i in batch])
            cur.execute("ANALYZE _owner_batch_ids")
            cur.execute(month_script, prepare=False)
            cur.execute("ANALYZE _owner_input")
            validate_input_batch(cur)
            cur.execute(sql.SQL("SELECT {} FROM _owner_input ORDER BY scenario_id, month_number")
                        .format(sql.SQL(", ").join(map(sql.Identifier, CALC_COLUMNS))))
            owner = pd.DataFrame.from_records(cur.fetchall(), columns=CALC_COLUMNS)
            if owner.empty or owner["scenario_id"].nunique() != len(batch):
                raise ValueError("An owner scenario is missing its monthly input history.")
            results = calculate_owner_batch(owner)
            input_changes += upsert_monthly_inputs(cur, input_columns)
            result_changes += write_results(cur, results)
            rows_processed += len(results)
            completed = offset + len(batch)
            if monotonic() - last_progress >= 25 or completed == count:
                print(f"  Calculated scenarios: {completed:,}/{count:,}; monthly rows: {rows_processed:,}", flush=True)
                last_progress = monotonic()
        cur.execute("""
            SELECT COUNT(*), MAX(m.date_period), COUNT(*) FILTER (
                WHERE m.mortgage_balance IS NULL OR m.owner_net_worth IS NULL
                   OR m.cumulative_unrecoverable_cost IS NULL)
            FROM simulation.owner_monthly_schedule m JOIN _owner_refresh_ids r USING (scenario_id)
        """)
        saved_count, latest, missing_results = cur.fetchone()
        if saved_count != rows_processed or missing_results:
            raise ValueError("Owner result completeness check failed.")
        return dict(cutoff=cutoff, scenarios=count, rows=rows_processed, latest=latest,
                    input_changes=input_changes, result_changes=result_changes, outside_scope=outside_scope)


def main():
    load_dotenv(HERE / "API.env")
    password = os.getenv("pg_password", "")
    if not password:
        raise ValueError("Missing pg_password in API.env beside update_owner.py.")
    with psycopg.connect(host="localhost", port=5432, dbname="rentvsbuy", user="postgres",
                         password=password, connect_timeout=10) as conn:
        conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        summary = refresh_owner(conn)
    print("Owner simulation refresh committed successfully.")
    print(f"Owner cutoff: {summary['cutoff']}")
    print(f"Owner scenarios recalculated: {summary['scenarios']:,}")
    print(f"Owner monthly observations processed: {summary['rows']:,}")
    print(f"Owner monthly inputs inserted or updated: {summary['input_changes']:,}")
    print(f"Owner monthly results inserted or updated: {summary['result_changes']:,}")
    print(f"Owner refreshed latest date: {summary['latest']}")
    if summary["outside_scope"]:
        print(f"Existing scenarios outside the current source/default scenario range retained: {summary['outside_scope']:,}")
    print("Renter results have not been refreshed. Refresh renter before comparing owner and renter in Power BI.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Owner refresh interrupted; the database transaction was not committed.")
        sys.exit(1)
    except Exception as error:
        print(f"Owner refresh failed: {error}")
        print("The database transaction was not committed.")
        sys.exit(1)

r"""Refresh renter inputs and recursion from the existing owner results.

Read 06_*.sql from ../create_SQL and calculations from ../simulation_python.
Keep API.env beside this file in update_python/.
Run from SQL-Python: python3 .\update_python\update_renter.py
"""

import os
from pathlib import Path
import sys
from datetime import date
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

from renter_calculations import RESULT_COLUMNS, calculate_renter_batch, prepare_market_data
CITIES = ("Canada", "Vancouver", "Calgary", "Edmonton", "Toronto", "Ottawa", "Montreal")
PORTFOLIOS = ("sp500_only", "tsx_only")
BATCH_SIZE = 100  # All months and both portfolios of each owner stay together.
KEY_COLUMNS = ("owner_scenario_id", "date_period", "portfolio_name", "renter_discipline")
CALC_COLUMNS = (
    "renter_scenario_id", "owner_scenario_id", "date_period", "month_number", "city",
    "market_rent", "rent_growth_mode", "rent_control_rate", "monthly_move_probability",
    "move_cost_multiplier", "renter_discipline", "initial_renter_investment",
    "portfolio_name", "monthly_investment_cost", "owner_total_cash_outflow", "owner_net_worth",
)


def get_cutoff(cur):
    cur.execute("""
        SELECT city, EXTRACT(YEAR FROM date_period) FROM analysis.city_rent_long
        WHERE city = ANY(%s) AND date_period IS NOT NULL
        GROUP BY city, EXTRACT(YEAR FROM date_period) HAVING COUNT(*) > 1 LIMIT 1
    """, (list(CITIES),))
    if cur.fetchone():
        raise ValueError("Rent has multiple observations in one city/year; the original annual join would be ambiguous.")
    cur.execute("""
        SELECT city, MAX(date_period) FROM analysis.city_rent_long
        WHERE city = ANY(%s) AND date_period IS NOT NULL AND price > 0
          AND price::text NOT IN ('NaN','Infinity','-Infinity') GROUP BY city
    """, (list(CITIES),))
    rents = dict(cur.fetchall())
    if set(CITIES) - set(rents):
        raise ValueError("Annual rent history is missing for one or more of the seven cities.")
    # Preserve the original calendar-year rent mapping: October's annual value
    # is used for January through December of that same year, never the next year.
    rent_coverage = min(date(d.year, 12, 1) for d in rents.values())
    cur.execute("""
        SELECT city, MAX(date_period) FROM simulation.owner_monthly_schedule
        WHERE city = ANY(%s) GROUP BY city
    """, (list(CITIES),))
    owners = dict(cur.fetchall())
    if set(CITIES) - set(owners) or any(d is None for d in owners.values()):
        raise ValueError("Owner history is missing for one or more cities. Refresh owner first.")
    owner_coverage = min(owners.values())
    limits = [("Owner coverage shared by all seven cities", owner_coverage),
              ("Annual rent coverage under the original calendar-year rule", rent_coverage)]
    for schema, table, column, label in (
        ("analysis", "sp500_index_1990_100", "price_cad", "S&P 500 input"),
        ("analysis", "tsx_index_1990_100", "price_cad", "TSX input"),
        ("stg", "canada_cpi", "cpi_value", "CPI input"),
    ):
        cur.execute(sql.SQL("""
            SELECT MAX(date_period) FROM {table}
            WHERE date_period IS NOT NULL AND {value} > 0
              AND {value}::text NOT IN ('NaN','Infinity','-Infinity')
        """).format(table=sql.Identifier(schema, table), value=sql.Identifier(column)))
        latest = cur.fetchone()[0]
        if latest is None:
            raise ValueError(f"No positive dated values in {schema}.{table}.")
        limits.append((label, latest))
    cutoff = min(d for _, d in limits)
    if cutoff.day != 1:
        raise ValueError("Simulation inputs must use month-start dates.")
    print(f"Latest rent survey shared by all seven cities: {min(rents.values())}", flush=True)
    for label, latest in limits:
        print(f"{label}: {latest}", flush=True)
    print(f"Renter comparison cutoff determined from inputs: {cutoff}", flush=True)
    return cutoff, owner_coverage


def load_market_inputs(cur, cutoff):
    frames = []
    for schema, table, column in (
        ("analysis", "sp500_index_1990_100", "price_cad"),
        ("analysis", "tsx_index_1990_100", "price_cad"),
        ("stg", "canada_cpi", "cpi_value"),
    ):
        cur.execute(sql.SQL("""
            SELECT date_period, {column} FROM {table}
            WHERE date_period IS NOT NULL AND date_period <= %s ORDER BY date_period
        """).format(column=sql.Identifier(column), table=sql.Identifier(schema, table)), (cutoff,))
        frame = pd.DataFrame.from_records(cur.fetchall(), columns=["date_period", column])
        frame["date_period"] = pd.to_datetime(frame["date_period"])
        if frame.empty or frame["date_period"].duplicated().any():
            raise ValueError(f"Missing history or duplicate dates in {schema}.{table}.")
        if not frame["date_period"].dt.is_month_start.all():
            raise ValueError(f"Expected month-start dates in {schema}.{table}.")
        values = pd.to_numeric(frame[column], errors="coerce")
        supplied = frame[column].notna()
        if ((~np.isfinite(values) | values.le(0)) & supplied).any():
            raise ValueError(f"Invalid positive-value input in {schema}.{table}.")
        frames.append(frame)
    return prepare_market_data(*frames)


def check_assumptions(cur):
    cur.execute("SELECT portfolio_name FROM simulation.investment_assumptions ORDER BY portfolio_name")
    names = tuple(row[0] for row in cur.fetchall())
    if set(names) != set(PORTFOLIOS):
        raise ValueError("The original model supports only sp500_only and tsx_only portfolios.")
    cur.execute("""
        SELECT 1 FROM simulation.investment_assumptions
        WHERE investment_fee < 0 OR tax_drag < 0
           OR investment_fee::text IN ('NaN','Infinity','-Infinity')
           OR tax_drag::text IN ('NaN','Infinity','-Infinity') LIMIT 1
    """)
    if cur.fetchone():
        raise ValueError("Invalid investment fee or tax-drag assumption.")
    cur.execute("""
        SELECT 1 FROM simulation.renter_policy_assumptions WHERE city = ANY(%s)
          AND (rent_growth_mode NOT IN ('market','controlled','mixed')
               OR annual_move_probability < 0 OR annual_move_probability > 1
               OR move_cost_multiplier < 0 OR rent_control_rate < 0
               OR annual_move_probability::text IN ('NaN','Infinity','-Infinity')
               OR move_cost_multiplier::text IN ('NaN','Infinity','-Infinity')
               OR rent_control_rate::text IN ('NaN','Infinity','-Infinity')) LIMIT 1
    """, (list(CITIES),))
    if cur.fetchone():
        raise ValueError("Invalid renter policy assumption.")


def check_owner_batch(cur, cutoff):
    cur.execute("""
        SELECT o.scenario_id, o.date_period FROM simulation.owner_monthly_schedule o
        JOIN _renter_batch_ids b USING (scenario_id)
        WHERE o.date_period <= %s
          AND (o.mortgage_payment IS NULL OR o.mortgage_interest IS NULL
               OR o.mortgage_principal IS NULL OR o.mortgage_balance IS NULL
               OR o.maintenance_cost IS NULL OR o.property_cost IS NULL
               OR o.insurance_cost IS NULL OR o.owner_net_worth IS NULL
               OR o.down_payment IS NULL OR o.purchase_cost IS NULL)
        LIMIT 1
    """, (cutoff,))
    row = cur.fetchone()
    if row:
        raise ValueError(f"Owner input is not calculated at {row}. Refresh owner first.")


def check_input_batch(cur, expected_rows):
    cur.execute("SELECT COUNT(*) FROM _renter_input")
    if cur.fetchone()[0] != expected_rows:
        raise ValueError("Renter input row count does not match the expected owner paths and two portfolios.")
    cur.execute("""
        SELECT i.owner_scenario_id FROM _renter_input i
        JOIN _renter_batch_ids b ON b.scenario_id = i.owner_scenario_id
        GROUP BY i.owner_scenario_id, i.portfolio_name, i.renter_discipline, b.expected_months
        HAVING COUNT(*) <> b.expected_months OR MIN(i.month_number) <> 0
            OR MAX(i.month_number) <> b.expected_months - 1
            OR COUNT(DISTINCT i.date_period) <> b.expected_months LIMIT 1
    """)
    if cur.fetchone():
        raise ValueError("A renter path is missing months between purchase and its comparison cutoff.")


def upsert_inputs(cur, columns):
    values = [c for c in columns if c not in KEY_COLUMNS]
    assignments = sql.SQL(", ").join(sql.SQL("{c} = EXCLUDED.{c}").format(c=sql.Identifier(c)) for c in values)
    old = sql.SQL(", ").join(sql.SQL("target.{}").format(sql.Identifier(c)) for c in values)
    new = sql.SQL(", ").join(sql.SQL("EXCLUDED.{}").format(sql.Identifier(c)) for c in values)
    cur.execute(sql.SQL("""
        INSERT INTO simulation.renter_monthly_schedule AS target ({columns})
        SELECT {columns} FROM _renter_input WHERE TRUE
        ON CONFLICT (owner_scenario_id, date_period, portfolio_name, renter_discipline)
        DO UPDATE SET {assignments} WHERE ROW({old}) IS DISTINCT FROM ROW({new})
    """).format(columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
                   assignments=assignments, old=old, new=new))
    return cur.rowcount


def load_calculation_batch(cur):
    # Resolve persistent row IDs after upsert; never replace renter_scenario_id.
    cur.execute(sql.SQL("""
        SELECT {columns} FROM simulation.renter_monthly_schedule t JOIN _renter_input i
        ON t.owner_scenario_id = i.owner_scenario_id AND t.date_period = i.date_period
           AND t.portfolio_name = i.portfolio_name AND t.renter_discipline = i.renter_discipline
        ORDER BY t.owner_scenario_id, t.portfolio_name, t.renter_discipline, t.month_number
    """).format(columns=sql.SQL(", ").join(sql.SQL("t.{}").format(sql.Identifier(c)) for c in CALC_COLUMNS)))
    return pd.DataFrame.from_records(cur.fetchall(), columns=CALC_COLUMNS)


def write_results(cur, results):
    optional = ("owner_net_worth_index", "renter_net_worth_index")
    numeric = [c for c in RESULT_COLUMNS if c not in ("renter_scenario_id", "renter_moves", *optional)]
    if not np.isfinite(results[numeric].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite renter calculation result.")
    # The original formula returns NaN indexes if starting net worth is zero.
    # Preserve these as SQL NULL rather than an invented index value.
    if np.isinf(results[list(optional)].to_numpy(dtype=float)).any():
        raise ValueError("Infinite indexed net worth in renter results.")
    cur.execute("TRUNCATE _renter_results")
    with cur.copy(sql.SQL("COPY _renter_results ({}) FROM STDIN")
                  .format(sql.SQL(", ").join(map(sql.Identifier, RESULT_COLUMNS)))) as copy:
        for row in results.itertuples(index=False, name=None):
            copy.write_row(tuple(None if pd.isna(value) else value for value in row))
    cur.execute("ANALYZE _renter_results")
    values = RESULT_COLUMNS[1:]
    assignments = sql.SQL(", ").join(sql.SQL("{c} = source.{c}").format(c=sql.Identifier(c)) for c in values)
    old = sql.SQL(", ").join(sql.SQL("target.{}").format(sql.Identifier(c)) for c in values)
    new = sql.SQL(", ").join(sql.SQL("source.{}").format(sql.Identifier(c)) for c in values)
    cur.execute(sql.SQL("""
        UPDATE simulation.renter_monthly_schedule AS target SET {assignments}
        FROM _renter_results AS source WHERE target.renter_scenario_id = source.renter_scenario_id
          AND ROW({old}) IS DISTINCT FROM ROW({new})
    """).format(assignments=assignments, old=old, new=new))
    return cur.rowcount


def refresh_renter(conn):
    prep_script = (SQL_DIR / "06_prepare_renter_refresh.sql").read_text(encoding="utf-8-sig")
    month_script = (SQL_DIR / "06_refresh_renter_months.sql").read_text(encoding="utf-8-sig")
    with conn.cursor() as cur:
        # Same advisory lock as the new owner runner.
        cur.execute("SELECT pg_try_advisory_xact_lock(726562, 5)")
        if not cur.fetchone()[0]:
            raise ValueError("Another simulation refresh is already running.")
        cutoff, owner_latest = get_cutoff(cur)
        stock_returns, cpi = load_market_inputs(cur, cutoff)
        cur.execute("CREATE TEMP TABLE _renter_refresh_config (cutoff DATE NOT NULL) ON COMMIT DROP")
        cur.execute("INSERT INTO _renter_refresh_config VALUES (%s)", (cutoff,))
        print("Preparing renter refresh; existing assumptions and row IDs are retained...", flush=True)
        cur.execute(prep_script, prepare=False)
        check_assumptions(cur)
        cur.execute("SELECT scenario_id, expected_months FROM _renter_owner_ids ORDER BY scenario_id")
        owners = cur.fetchall()
        if not owners or any(months <= 0 for _, months in owners):
            raise ValueError("No valid owner paths are available for renter calculation.")
        cur.execute("""
            CREATE TEMP TABLE _renter_batch_ids (
                scenario_id BIGINT PRIMARY KEY, expected_months INTEGER NOT NULL) ON COMMIT DROP;
            CREATE TEMP TABLE _renter_input
                (LIKE simulation.renter_monthly_schedule INCLUDING DEFAULTS) ON COMMIT DROP;
            ALTER TABLE _renter_input ALTER COLUMN renter_scenario_id DROP NOT NULL;
            ALTER TABLE _renter_input ALTER COLUMN renter_scenario_id DROP DEFAULT;
        """, prepare=False)
        cur.execute(sql.SQL("CREATE TEMP TABLE _renter_results ON COMMIT DROP AS SELECT {} "
                            "FROM simulation.renter_monthly_schedule WITH NO DATA")
                    .format(sql.SQL(", ").join(map(sql.Identifier, RESULT_COLUMNS))))
        cur.execute("CREATE UNIQUE INDEX ON _renter_results (renter_scenario_id)")
        cur.execute("SELECT * FROM _renter_input LIMIT 0")
        input_columns = [c.name for c in cur.description if c.name not in RESULT_COLUMNS]
        rows_processed = input_changes = result_changes = 0
        last_progress = monotonic()
        print(f"Recalculating {len(owners):,} owner paths x 2 portfolios through {cutoff}...", flush=True)
        for offset in range(0, len(owners), BATCH_SIZE):
            batch = owners[offset:offset + BATCH_SIZE]
            expected = sum(months for _, months in batch) * len(PORTFOLIOS)
            cur.execute("TRUNCATE _renter_batch_ids")
            cur.executemany("INSERT INTO _renter_batch_ids VALUES (%s, %s)", batch)
            cur.execute("ANALYZE _renter_batch_ids")
            check_owner_batch(cur, cutoff)
            cur.execute(month_script, prepare=False)
            cur.execute("ANALYZE _renter_input")
            check_input_batch(cur, expected)
            input_changes += upsert_inputs(cur, input_columns)
            renter = load_calculation_batch(cur)
            if len(renter) != expected:
                raise ValueError("Persistent renter keys do not match this batch's inputs.")
            results = calculate_renter_batch(renter, stock_returns, cpi)
            result_changes += write_results(cur, results)
            rows_processed += len(results)
            completed = offset + len(batch)
            if monotonic() - last_progress >= 25 or completed == len(owners):
                print(f"  Calculated owner paths: {completed:,}/{len(owners):,}; renter monthly rows: {rows_processed:,}", flush=True)
                last_progress = monotonic()
        cur.execute("""
            SELECT COUNT(*), MAX(t.date_period), COUNT(*) FILTER (
                WHERE t.renter_net_worth IS NULL OR t.renter_net_worth_real IS NULL
                   OR t.owner_net_worth_real IS NULL OR t.renter_portfolio_value IS NULL)
            FROM simulation.renter_monthly_schedule t JOIN _renter_owner_ids o
              ON o.scenario_id = t.owner_scenario_id
            WHERE t.date_period <= %s AND t.portfolio_name = ANY(%s) AND t.renter_discipline = 1.00
        """, (cutoff, list(PORTFOLIOS)))
        saved, latest, missing = cur.fetchone()
        if saved != rows_processed or missing:
            raise ValueError("Renter result completeness check failed.")
        cur.execute("""
            SELECT COUNT(*) FROM simulation.renter_monthly_schedule t
            WHERE NOT (t.date_period <= %s AND t.portfolio_name = ANY(%s)
                       AND t.renter_discipline = 1.00
                       AND EXISTS (SELECT 1 FROM _renter_owner_ids o WHERE o.scenario_id = t.owner_scenario_id))
        """, (cutoff, list(PORTFOLIOS)))
        retained = cur.fetchone()[0]
        return dict(cutoff=cutoff, owner_latest=owner_latest, owners=len(owners), paths=len(owners)*2,
                    rows=rows_processed, input_changes=input_changes, result_changes=result_changes,
                    latest=latest, retained=retained)


def main():
    load_dotenv(HERE / "API.env")
    password = os.getenv("pg_password", "")
    if not password:
        raise ValueError("Missing pg_password in API.env beside update_renter.py.")
    with psycopg.connect(host="localhost", port=5432, dbname="rentvsbuy", user="postgres",
                         password=password, connect_timeout=10) as conn:
        conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        summary = refresh_renter(conn)
    print("Renter simulation refresh committed successfully.")
    print(f"Renter comparison cutoff: {summary['cutoff']}")
    print(f"Owner paths used: {summary['owners']:,}")
    print(f"Renter paths recalculated (two portfolios): {summary['paths']:,}")
    print(f"Renter monthly observations processed: {summary['rows']:,}")
    print(f"Renter monthly inputs inserted or updated: {summary['input_changes']:,}")
    print(f"Renter monthly results inserted or updated: {summary['result_changes']:,}")
    print(f"Renter refreshed latest date: {summary['latest']}")
    if summary["retained"]:
        print(f"Existing rows outside the refresh range retained without recalculation: {summary['retained']:,}")
    print(f"Owner history remains available through {summary['owner_latest']}.")
    print(f"For this refresh, compare owner and renter only through {summary['cutoff']}.")
    print("Paths with a later planned sale are calculated only through the comparison cutoff.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Renter refresh interrupted; the database transaction was not committed.")
        sys.exit(1)
    except Exception as error:
        print(f"Renter refresh failed: {error}")
        print("The database transaction was not committed.")
        sys.exit(1)

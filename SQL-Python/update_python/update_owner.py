r"""Refresh changed owner scenarios in one transaction.

Default: compare regenerated inputs and verified saved results; skip unchanged
scenarios. New, changed or unverified scenarios retain the original full-history
calculation. This is scenario-level incremental refresh, not monthly continuation.
The first run establishes a baseline in simulation.owner_refresh_state.

Read 05_*.sql from ../create_SQL and calculations from ../simulation_python.
Keep API.env beside this file in update_python/.
Run from SQL-Python: python3 .\update_python\update_owner.py
Force all eligible scenarios: python3 .\update_python\update_owner.py --full
"""

import argparse
from collections import Counter
import hashlib
import os
import json
from datetime import datetime, timezone
from uuid import uuid4
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
REPORT_DIR = PROJECT_DIR / "reconciliation_reports"
REFRESH_VERSION = "owner-scenario-incremental-v1"


def save_audit(report):
    """Write an audit trail without serializing database secrets or scenario data."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = REPORT_DIR / f"owner_{stamp}_{uuid4().hex[:8]}.json"
    path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return path


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



def reconcile_owner_batch(cur, input_columns, expected_rows):
    """Compare persisted monthly inputs and Python results to this batch's source data.

    Checks happen inside the same transaction as the upsert, before commit.
    This validates persisted values; it does not independently prove financial formulas.
    """
    cur.execute("SELECT COUNT(*) FROM _owner_input")
    input_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM _owner_results")
    result_count = cur.fetchone()[0]
    if input_count != expected_rows or result_count != expected_rows:
        raise ValueError(
            f"Owner batch row mismatch: inputs={input_count}, results={result_count}, expected={expected_rows}."
        )
    for table in ("_owner_input", "_owner_results"):
        cur.execute(sql.SQL("""
            SELECT 1 FROM {} GROUP BY scenario_id, date_period
            HAVING COUNT(*) > 1 LIMIT 1
        """).format(sql.Identifier(table)))
        if cur.fetchone():
            raise ValueError(f"Duplicate owner scenario/date in {table}.")

    key_match = "m.scenario_id = s.scenario_id AND m.date_period = s.date_period"
    for source, values, label in (
        ("_owner_input", tuple(c for c in input_columns if c not in ("scenario_id", "date_period")), "inputs"),
        ("_owner_results", RESULT_COLUMNS, "results"),
    ):
        different = sql.SQL(" OR ").join(
            sql.SQL("m.{c} IS DISTINCT FROM s.{c}").format(c=sql.Identifier(c))
            for c in values
        )
        cur.execute(sql.SQL("""
            SELECT s.scenario_id, s.date_period
            FROM {source} s LEFT JOIN simulation.owner_monthly_schedule m
              ON m.scenario_id = s.scenario_id AND m.date_period = s.date_period
            WHERE m.scenario_id IS NULL OR ({different})
            LIMIT 1
        """).format(source=sql.Identifier(source), different=different))
        mismatch = cur.fetchone()
        if mismatch:
            raise ValueError(f"Owner {label} reconciliation failed at {mismatch}.")
    return result_count


def calculation_signature(scenario_script, month_script):
    """Invalidate cached results when the runner, SQL, calculations or runtime change.

    Hash all Python sources under simulation_python conservatively, including
    helpers imported by owner_calculations. No credentials or database data enter
    the signature. External/manual dependencies can be checked with --full.
    """
    digest = hashlib.sha256()
    parts = [REFRESH_VERSION, sys.version, np.__version__, pd.__version__,
             scenario_script, month_script]
    for part in parts:
        data = part.encode("utf-8")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    paths = [("update_owner.py", Path(__file__))]
    paths.extend((str(p.relative_to(CALC_DIR)), p)
                 for p in sorted(CALC_DIR.rglob("*.py")))
    if not any(name == "owner_calculations.py" for name, _ in paths):
        raise ValueError("Missing owner_calculations.py; cannot verify calculation version.")
    for name, path in paths:
        for data in (name.encode("utf-8"), path.read_bytes()):
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
    return digest.hexdigest()


def create_refresh_state(cur):
    """Store verification metadata atomically with the monthly results."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS simulation.owner_refresh_state (
            scenario_id BIGINT PRIMARY KEY,
            calculation_signature TEXT NOT NULL,
            result_signature TEXT NOT NULL,
            verified_rows BIGINT NOT NULL CHECK (verified_rows > 0),
            verified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TEMP TABLE _owner_batch_status (
            scenario_id BIGINT PRIMARY KEY,
            expected_rows BIGINT NOT NULL,
            inputs_changed BOOLEAN NOT NULL,
            invalid_results BOOLEAN NOT NULL,
            result_signature TEXT NOT NULL
        ) ON COMMIT DROP;
    """, prepare=False)


def inspect_batch(cur, input_columns):
    """Compare every generated input; fingerprint the saved result path in date order.

    This still reads and prepares complete SQL inputs. It avoids transferring
    unchanged paths to Python and running their recursive financial calculations.
    The MD5 signature is a change detector, not an independent formula check.
    """
    values = [c for c in input_columns if c not in ("scenario_id", "date_period")]
    different = sql.SQL(" OR ").join(
        sql.SQL("m.{c} IS DISTINCT FROM i.{c}").format(c=sql.Identifier(c)) for c in values
    )
    invalid = sql.SQL(" OR ").join(
        sql.SQL("m.{c} IS NULL OR m.{c}::text IN ('NaN','Infinity','-Infinity')")
        .format(c=sql.Identifier(c)) for c in RESULT_COLUMNS
    )
    results = sql.SQL(", ").join(
        sql.SQL("m.{}").format(sql.Identifier(c)) for c in RESULT_COLUMNS
    )
    cur.execute("TRUNCATE _owner_batch_status")
    cur.execute(sql.SQL("""
        INSERT INTO _owner_batch_status
        SELECT i.scenario_id, COUNT(*),
               BOOL_OR(m.scenario_id IS NULL OR ({different})),
               BOOL_OR(m.scenario_id IS NULL OR ({invalid})),
               MD5(JSONB_AGG(JSONB_BUILD_ARRAY(i.date_period, {results})
                             ORDER BY i.date_period)::text)
        FROM _owner_input i
        LEFT JOIN simulation.owner_monthly_schedule m
          ON m.scenario_id = i.scenario_id AND m.date_period = i.date_period
        GROUP BY i.scenario_id
    """).format(different=different, invalid=invalid, results=results))


def select_calculation_scope(cur, signature, force_full):
    """Return affected IDs, expected rows and skipped counts, with audit reasons."""
    cur.execute("""
        SELECT b.scenario_id, b.expected_rows,
               CASE
                 WHEN %s THEN 'forced_full'
                 WHEN s.scenario_id IS NULL THEN 'new_or_unverified'
                 WHEN s.calculation_signature IS DISTINCT FROM %s THEN 'model_changed'
                 WHEN b.inputs_changed OR s.verified_rows <> b.expected_rows THEN 'inputs_changed'
                 WHEN b.invalid_results OR s.result_signature IS DISTINCT FROM b.result_signature
                   THEN 'results_changed_or_invalid'
                 ELSE 'unchanged'
               END AS reason
        FROM _owner_batch_status b
        LEFT JOIN simulation.owner_refresh_state s USING (scenario_id)
        ORDER BY b.scenario_id
    """, (force_full, signature))
    statuses = cur.fetchall()
    ids = [scenario_id for scenario_id, _, reason in statuses if reason != "unchanged"]
    expected = sum(rows for _, rows, _ in statuses)
    skipped_rows = sum(rows for _, rows, reason in statuses if reason == "unchanged")
    reasons = Counter(reason for _, _, reason in statuses)
    return ids, expected, skipped_rows, reasons


def save_refresh_state(cur, signature):
    """Fingerprint only successfully calculated and reconciled paths."""
    cur.execute("""
        SELECT scenario_id FROM _owner_batch_status
        WHERE inputs_changed OR invalid_results LIMIT 1
    """)
    invalid = cur.fetchone()
    if invalid:
        raise ValueError(f"Owner refresh state cannot be verified for scenario {invalid[0]}.")
    cur.execute("""
        INSERT INTO simulation.owner_refresh_state AS saved
            (scenario_id, calculation_signature, result_signature, verified_rows)
        SELECT scenario_id, %s, result_signature, expected_rows
        FROM _owner_batch_status
        ON CONFLICT (scenario_id) DO UPDATE SET
            calculation_signature = EXCLUDED.calculation_signature,
            result_signature = EXCLUDED.result_signature,
            verified_rows = EXCLUDED.verified_rows,
            verified_at = CURRENT_TIMESTAMP
    """, (signature,))


def refresh_owner(conn, *, force_full=False):
    scenario_script = (SQL_DIR / "05_refresh_owner_scenarios.sql").read_text(encoding="utf-8-sig")
    month_script = (SQL_DIR / "05_refresh_owner_months.sql").read_text(encoding="utf-8-sig")
    signature = calculation_signature(scenario_script, month_script)
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
        create_refresh_state(cur)
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
        rows_processed = input_changes = result_changes = verified_rows = expected_rows = 0
        calculated_scenarios = skipped_scenarios = cached_rows = 0
        reasons = Counter()
        last_progress = monotonic()
        mode = "full" if force_full else "incremental_by_scenario"
        print(f"Checking {count:,} scenarios in batches of {BATCH_SIZE}; mode={mode}...", flush=True)
        for offset in range(0, count, BATCH_SIZE):
            batch = ids[offset:offset + BATCH_SIZE]
            cur.execute("TRUNCATE _owner_batch_ids")
            cur.executemany("INSERT INTO _owner_batch_ids VALUES (%s)", [(i,) for i in batch])
            cur.execute("ANALYZE _owner_batch_ids")
            cur.execute(month_script, prepare=False)
            cur.execute("ANALYZE _owner_input")
            validate_input_batch(cur)
            inspect_batch(cur, input_columns)
            changed, batch_rows, skipped_rows, batch_reasons = select_calculation_scope(
                cur, signature, force_full
            )
            if sum(batch_reasons.values()) != len(batch):
                raise ValueError("An owner scenario is missing its monthly input history.")
            expected_rows += batch_rows
            cached_rows += skipped_rows
            verified_rows += skipped_rows
            skipped_scenarios += batch_reasons["unchanged"]
            reasons.update(batch_reasons)
            if changed:
                # Keep whole histories, but only for paths that need calculation.
                cur.execute("DELETE FROM _owner_input WHERE NOT (scenario_id = ANY(%s))", (changed,))
                cur.execute(sql.SQL("SELECT {} FROM _owner_input ORDER BY scenario_id, month_number")
                            .format(sql.SQL(", ").join(map(sql.Identifier, CALC_COLUMNS))))
                owner = pd.DataFrame.from_records(cur.fetchall(), columns=CALC_COLUMNS)
                if owner.empty or owner["scenario_id"].nunique() != len(changed):
                    raise ValueError("An affected owner scenario is missing its monthly input history.")
                results = calculate_owner_batch(owner)
                input_changes += upsert_monthly_inputs(cur, input_columns)
                result_changes += write_results(cur, results)
                verified_rows += reconcile_owner_batch(cur, input_columns, len(results))
                rows_processed += len(results)
                calculated_scenarios += len(changed)
                inspect_batch(cur, input_columns)
                save_refresh_state(cur, signature)
            completed = offset + len(batch)
            if monotonic() - last_progress >= 25 or completed == count:
                print(f"  Checked: {completed:,}/{count:,}; calculated: {calculated_scenarios:,}; "
                      f"skipped: {skipped_scenarios:,}; calculated months: {rows_processed:,}", flush=True)
                last_progress = monotonic()
        cur.execute("""
            SELECT COUNT(*), MAX(m.date_period), COUNT(*) FILTER (
                WHERE m.mortgage_balance IS NULL OR m.owner_net_worth IS NULL
                   OR m.cumulative_unrecoverable_cost IS NULL)
            FROM simulation.owner_monthly_schedule m JOIN _owner_refresh_ids r USING (scenario_id)
        """)
        saved_count, latest, missing_results = cur.fetchone()
        if saved_count != expected_rows or saved_count != verified_rows or missing_results:
            raise ValueError("Owner result completeness check failed.")
        print(f"Owner verification: PASS ({rows_processed:,} recalculated rows reconciled; "
              f"{cached_rows:,} cached rows checked against inputs and saved fingerprints)", flush=True)
        return dict(cutoff=cutoff, scenarios=count, rows=rows_processed, verified_rows=verified_rows,
                    latest=latest, input_changes=input_changes, result_changes=result_changes,
                    outside_scope=outside_scope, expected_rows=expected_rows, mode=mode,
                    scenarios_calculated=calculated_scenarios, scenarios_skipped=skipped_scenarios,
                    cached_rows_verified=cached_rows, calculation_reasons=dict(reasons),
                    calculation_signature=signature)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true",
                        help="Recalculate all eligible scenarios and rebuild verification metadata.")
    args = parser.parse_args(argv)
    load_dotenv(HERE / "API.env")
    password = os.getenv("pg_password", "")
    if not password:
        raise ValueError("Missing pg_password in API.env beside update_owner.py.")
    report = {"pipeline": "owner_simulation", "status": "RUNNING", "committed": False,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "checks": {"monthly_input_reconciliation": "NOT_RUN",
                         "monthly_result_reconciliation": "NOT_RUN",
                         "scenario_completeness": "NOT_RUN"}}
    try:
        with psycopg.connect(host="localhost", port=5432, dbname="rentvsbuy", user="postgres",
                             password=password, connect_timeout=10) as conn:
            conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            summary = refresh_owner(conn, force_full=args.full)
    except BaseException as error:
        report.update(status="FAIL", error_type=type(error).__name__,
                      error_message=str(error)[:1000], finished_at_utc=datetime.now(timezone.utc).isoformat())
        try:
            print(f"Reconciliation report: {save_audit(report)}", flush=True)
        except OSError as report_error:
            print(f"Could not write FAIL audit report: {report_error}", file=sys.stderr)
        raise
    report.update(status="PASS", committed=True,
                  checks={"monthly_input_reconciliation": "PASS",
                          "monthly_result_reconciliation": "PASS",
                          "scenario_completeness": "PASS"},
                  summary=summary, finished_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope_note="Calculated paths were reconciled against Python results. Skipped paths matched regenerated inputs and previously verified result fingerprints. Financial equations were not independently validated.")
    print("Owner simulation refresh committed successfully.")
    try:
        report_path = save_audit(report)
    except OSError as report_error:
        report_path = None
        print(f"Database committed, but the audit report could not be saved: {report_error}", file=sys.stderr)
    print(f"Owner cutoff: {summary['cutoff']}")
    print(f"Owner eligible scenarios: {summary['scenarios']:,}")
    print(f"Owner scenarios recalculated: {summary['scenarios_calculated']:,}")
    print(f"Owner scenarios skipped unchanged: {summary['scenarios_skipped']:,}")
    print(f"Owner cached monthly observations verified: {summary['cached_rows_verified']:,}")
    print(f"Owner monthly observations processed: {summary['rows']:,}")
    print(f"Owner monthly inputs inserted or updated: {summary['input_changes']:,}")
    print(f"Owner monthly results inserted or updated: {summary['result_changes']:,}")
    print(f"Owner refreshed latest date: {summary['latest']}")
    print(f"Owner reconciliation report: {report_path}")
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

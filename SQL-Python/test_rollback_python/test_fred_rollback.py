"""Safe PostgreSQL rollback test for the Rent vs. Buy FRED pipeline.

Uses only a session-local TEMP table. Does not change raw/staging data.
Place beside API.env in SQL-Python/update_python/ and run:
    python3 .\test_fred_rollback.py
"""
import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
from dotenv import load_dotenv


def main():
    script_dir = Path(__file__).resolve().parent

    env_path = script_dir.parent / "update_python" / "API.env"

    load_dotenv(env_path)
    password = os.getenv("pg_password")
    if not password:
        raise ValueError("Missing pg_password in API.env beside the test script")

    started = datetime.now(timezone.utc)
    run_id = f"{started:%Y%m%dT%H%M%S%fZ}_{uuid4().hex[:8]}"
    report = {
        "test": "postgresql_transaction_rollback",
        "run_id": run_id,
        "started_at_utc": started.isoformat(),
        "uses_temporary_table_only": True,
        "production_tables_modified": False,
        "original_value": None,
        "value_written_before_failure": "9.9999",
        "value_after_rollback": None,
        "simulated_failure_raised": False,
        "rollback_verified": False,
        "status": "FAIL",
        "error_type": None,
    }

    try:
        with psycopg.connect(host="localhost", port=5432, dbname="rentvsbuy",
                             user="postgres", password=password, connect_timeout=10) as conn:
            # Create and seed a temporary table. Commit baseline BEFORE the test transaction.
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TEMP TABLE rollback_test_fred (
                        observation_date date PRIMARY KEY,
                        dexcaus numeric NOT NULL
                    ) ON COMMIT PRESERVE ROWS
                """)
                cur.execute("""
                    INSERT INTO rollback_test_fred (observation_date, dexcaus)
                    VALUES (%s, %s)
                """, ("2026-10-16", Decimal("1.3500")))
            conn.commit()

            with conn.cursor() as cur:
                cur.execute("SELECT dexcaus FROM rollback_test_fred WHERE observation_date = %s",
                            ("2026-10-16",))
                original = cur.fetchone()[0]
                report["original_value"] = str(original)
            conn.commit()

            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE rollback_test_fred SET dexcaus = %s
                        WHERE observation_date = %s
                    """, (Decimal("9.9999"), "2026-10-16"))
                    if cur.rowcount != 1:
                        raise AssertionError("Expected exactly one temporary row to be updated")
                    cur.execute("SELECT dexcaus FROM rollback_test_fred WHERE observation_date = %s",
                                ("2026-10-16",))
                    pending = cur.fetchone()[0]
                    if pending != Decimal("9.9999"):
                        raise AssertionError("Temporary update was not visible within the transaction")
                    print(f"Value inside transaction: {pending}")
                    # Deliberate failure; no commit is allowed.
                    raise RuntimeError("SIMULATED_FAILURE_AFTER_UPDATE")
            except RuntimeError as error:
                if str(error) != "SIMULATED_FAILURE_AFTER_UPDATE":
                    raise
                report["simulated_failure_raised"] = True
                conn.rollback()
                print("Simulated failure caught; transaction rolled back.")
            except Exception:
                conn.rollback()
                raise

            with conn.cursor() as cur:
                cur.execute("SELECT dexcaus FROM rollback_test_fred WHERE observation_date = %s",
                            ("2026-10-16",))
                row = cur.fetchone()
                after = row[0] if row else None
            report["value_after_rollback"] = str(after) if after is not None else None
            report["rollback_verified"] = bool(report["simulated_failure_raised"] and after == original)
            report["status"] = "PASS" if report["rollback_verified"] else "FAIL"
            conn.rollback()  # Nothing from verification needs to commit.
    except Exception as error:
        report["status"] = "FAIL"
        report["error_type"] = type(error).__name__
        print(f"Rollback test failed: {type(error).__name__}: {error}", file=sys.stderr)
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        folder = script_dir.parent / "reconciliation_reports"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"fred_rollback_test_{run_id}.json"
            path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(f"Test report: {path}")
        except OSError as error:
            print(f"Could not save test report: {error}", file=sys.stderr)
            return 1

    print(f"Original: {report['original_value']} | After rollback: {report['value_after_rollback']}")
    print(f"Rollback test: {report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

"""Shared reconciliation bookkeeping and JSON reporting for data refresh scripts.

Source-specific SQL checks and database transactions belong to each update script.
No credentials, request URLs or database connections are stored here.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def new_report(source, dataset, checks, *, extra_fields=None):
    """Create a report with consistent identifiers, counters and check status."""
    now = datetime.now(timezone.utc)
    report = {
        "run_id": f"{now:%Y%m%dT%H%M%S%fZ}_{uuid4().hex[:8]}",
        "source": source,
        "series_id": dataset,  # preserved for compatibility with FRED report schema
        "started_at_utc": now.isoformat(),
        "finished_at_utc": None,
        "records": {"received": 0, "valid": 0, "missing_skipped": 0, "rejected": 0},
        "planned_raw_changes": None,
        "committed_raw_changes": None,
        "checks": {name: "NOT_RUN" for name in checks},
        "transaction_committed": False,
        "database": None,
        "status": "FAIL",
        "error_type": None,
    }
    if extra_fields:
        report.update(extra_fields)
    return report


def check_classification(valid_count, inserted, updated, unchanged):
    """Raise if each valid source record was not classified exactly once."""
    classified = inserted + updated + unchanged
    if classified != valid_count:
        raise ValueError(
            f"Classification mismatch: {classified} classified, "
            f"{valid_count} valid observations."
        )


def check_changed_count(actual, inserted, updated):
    """Raise if SQL affected-row count differs from planned inserts + updates."""
    expected = inserted + updated
    if actual != expected:
        raise ValueError(
            f"RAW change count mismatch: expected {expected}, actual {actual}."
        )


def save_report(report, source_slug, report_folder):
    """Write a JSON report atomically, without inserting confidential details."""
    folder = Path(report_folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{source_slug}_{report['run_id']}.json"
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)
    return path


def self_test():
    """Check shared helpers without touching APIs or production databases."""
    import tempfile

    check_classification(3, 1, 1, 1)
    check_changed_count(2, 1, 1)
    report = new_report("SELF_TEST", "test", ("classification", "raw_change_count"))
    report["records"].update(received=3, valid=3)
    report["planned_raw_changes"] = {"inserted": 1, "updated": 1, "unchanged": 1}
    report["checks"].update(classification="PASS", raw_change_count="PASS")
    report["status"] = "PASS"
    with tempfile.TemporaryDirectory() as folder:
        saved = save_report(report, "self_test", folder)
        loaded = json.loads(saved.read_text(encoding="utf-8"))
        if loaded["status"] != "PASS" or loaded["records"]["valid"] != 3:
            raise AssertionError("Reconciliation JSON self-test failed")
    print("Reconciliation module self-test: PASS")
    print("Classification, change-count check, and JSON export: PASS")
    print("No PostgreSQL tables or project report files were changed.")


if __name__ == "__main__":
    self_test()

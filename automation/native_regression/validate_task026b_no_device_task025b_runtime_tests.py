"""Validate TASK-026B no-device TASK-025B runtime scenario artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from automation.native_regression.run_task026b_no_device_task025b_runtime_tests import (
    load_scenarios,
    validate_task026b_report,
)


def validate_report(path: Path) -> list[str]:
    if not path.exists():
        return ["Report file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return [f"Report file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return ["Report must be a JSON object."]
    return validate_task026b_report(loaded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-026B no-device TASK-025B scenario/report artifacts.")
    parser.add_argument("--scenarios", type=Path, default=None, help="Optional TASK-025B scenario contract JSON.")
    parser.add_argument("--report", type=Path, default=None, help="Optional TASK-026B public report JSON.")
    args = parser.parse_args(argv)

    if args.scenarios is None and args.report is None:
        parser.error("at least one of --scenarios or --report is required")

    errors: list[str] = []
    if args.scenarios is not None:
        _, scenario_errors = load_scenarios(args.scenarios)
        errors.extend(f"scenarios: {error}" for error in scenario_errors)
    if args.report is not None:
        errors.extend(f"report: {error}" for error in validate_report(args.report))

    result = {
        "validation_status": "pass" if not errors else "fail",
        "errors": errors,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

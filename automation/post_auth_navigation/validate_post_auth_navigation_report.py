"""Validate a public-safe TASK-020 post-auth navigation report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from automation.post_auth_navigation.run_post_auth_navigation_probe import validate_report_shape


def validate_report(path: Path) -> list[str]:
    if not path.exists():
        return ["Report file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return [f"Report file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return ["Report must be a JSON object."]
    return validate_report_shape(loaded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate public-safe TASK-020 post-auth navigation report JSON.")
    parser.add_argument("--report", type=Path, required=True, help="Path to a public-safe TASK-020 report JSON.")
    args = parser.parse_args(argv)

    errors = validate_report(args.report)
    result = {
        "report": args.report.as_posix(),
        "validation_status": "pass" if not errors else "fail",
        "errors": errors,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate a public-safe blocked report for TASK-001 smoke bootstrap.

The tool intentionally performs no runtime or device interaction. It only
summarizes whether approved metadata exists and fails closed as blocked.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
TASK_ID = "TASK-001"
TOOL_NAME = "runtime_smoke_bootstrap.blocked_report_generator"
REQUIRED_KEYS = ("approved_build", "approved_target", "approved_config")
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
REDACTION_PATTERNS = (
    (re.compile(r"https?://[^\s)]+", re.IGNORECASE), "[REDACTED_URL]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (
        re.compile(
            r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|key)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED_SECRET]",
    ),
    (re.compile(r"\b[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?<!\w)/(?:mnt/[A-Za-z]|home|Users|tmp|var|private)/[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9_+=/-]{32,}(?![A-Za-z0-9])"), "[REDACTED_OPAQUE_VALUE]"),
)


@dataclass(frozen=True)
class Prerequisite:
    name: str
    present: bool
    evidence_status: str
    note: str
    redacted: bool

    def to_json(self) -> dict[str, Any]:
        return {
            "present": self.present,
            "evidence_status": self.evidence_status,
            "note": self.note,
        }


def _sanitize_note(note: str) -> tuple[str, bool]:
    sanitized = note
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized, sanitized != note


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_metadata(path: Path | None) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return {}, ["No approved prerequisite metadata file was provided."]
    if not path.exists():
        return {}, ["Prerequisite metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Prerequisite metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Prerequisite metadata must be a JSON object."]
    return loaded, []


def _normalize_prerequisite(name: str, raw: Any) -> Prerequisite:
    if not isinstance(raw, dict):
        return Prerequisite(
            name=name,
            present=False,
            evidence_status="unknown",
            note=f"{name} metadata is missing or not an object.",
            redacted=False,
        )

    present = raw.get("present") is True
    evidence_status = raw.get("evidence_status", "unknown")
    if evidence_status not in EVIDENCE_STATUSES:
        evidence_status = "unknown"

    note = raw.get("note")
    if not isinstance(note, str) or not note.strip():
        note = "No public-safe note was provided."
    note, redacted = _sanitize_note(note.strip())

    return Prerequisite(
        name=name,
        present=present,
        evidence_status=evidence_status,
        note=note,
        redacted=redacted,
    )


def build_report(metadata_path: Path | None = None) -> dict[str, Any]:
    metadata, load_reasons = _load_metadata(metadata_path)
    normalized = {
        name: _normalize_prerequisite(name, metadata.get(name))
        for name in REQUIRED_KEYS
    }
    prerequisites = {name: value.to_json() for name, value in normalized.items()}
    redaction_status = "redacted" if any(value.redacted for value in normalized.values()) else "not_applicable"

    blocked_reasons = list(load_reasons)
    for name, value in prerequisites.items():
        if not value["present"]:
            blocked_reasons.append(f"{name} is not approved or not present.")

    if not blocked_reasons:
        blocked_reasons.append(
            "TASK-001 bootstrap never executes runtime checks; use a future approved runtime task."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "task_id": TASK_ID,
        "mode": "BOUNDED_AUTONOMOUS",
        "tool_name": TOOL_NAME,
        "overall_status": "blocked",
        "evidence_status": "unknown",
        "production_safety_classification": "PROD_SAFE",
        "redaction_status": redaction_status,
        "prerequisites": prerequisites,
        "blocked_reasons": blocked_reasons,
        "risks": [
            {
                "id": "RISK-008",
                "level": "High",
                "status": "likely",
                "summary": "Runtime checks must not be claimed as passed without approved build/device/config evidence.",
            }
        ],
        "unknowns": [
            {
                "id": "U-001",
                "status": "unknown",
                "question": "Which build, target and configuration are approved for runtime QA?",
            }
        ],
        "verification": [
            {
                "name": "blocked-report-generation",
                "classification": "PROD_SAFE",
                "result": "pass",
                "note": "Generated a blocked report without runtime/device interaction.",
            }
        ],
        "artifacts": [],
        "review": {
            "qa_reviewer_a": "pending",
            "qa_reviewer_b": "pending",
            "security_prod_safety_reviewer": "pending",
            "docs_scribe": "pending",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a TASK-001 blocked runtime smoke report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON prerequisite metadata.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path. Defaults to stdout.",
    )
    args = parser.parse_args(argv)

    report = build_report(args.metadata)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"

    if args.output is None:
        sys.stdout.write(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

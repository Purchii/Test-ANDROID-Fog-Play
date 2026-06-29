"""Generate a public-safe exported component guard skeleton report.

The tool performs no Android, APK, network or runtime interaction. It only
normalizes approved public-safe metadata and fails closed when prerequisites are
missing.
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
TASK_ID = "TASK-002"
TOOL_NAME = "exported_component_guards.guard_report_generator"
REQUIRED_PREREQUISITES = (
    "approved_build",
    "approved_target",
    "approved_config",
    "approved_guard_scope",
)
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
GUARD_CASES = (
    {
        "id": "ECG-001",
        "category": "intentional_exposure_inventory",
        "purpose": "Confirm product/security has approved the exported surface inventory at category level.",
        "risk_level": "R1",
    },
    {
        "id": "ECG-002",
        "category": "benign_direct_start_guard",
        "purpose": "Plan a benign check that protected entry points do not bypass expected guards.",
        "risk_level": "R0",
    },
    {
        "id": "ECG-003",
        "category": "auth_session_guard",
        "purpose": "Plan a check that session-dependent entry points require approved session state.",
        "risk_level": "R0",
    },
    {
        "id": "ECG-004",
        "category": "input_validation_guard",
        "purpose": "Plan synthetic non-private input validation checks without endpoint or secret disclosure.",
        "risk_level": "R1",
    },
    {
        "id": "ECG-005",
        "category": "no_mutation_guard",
        "purpose": "Plan checks as no-op/dry-run only unless cleanup and rollback are approved.",
        "risk_level": "R1",
    },
    {
        "id": "ECG-006",
        "category": "redacted_evidence_guard",
        "purpose": "Require public-safe summaries and redacted artifact references only.",
        "risk_level": "R1",
    },
)
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
        return {}, ["No approved guard metadata file was provided."]
    if not path.exists():
        return {}, ["Approved guard metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approved guard metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approved guard metadata must be a JSON object."]
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


def _guard_cases() -> list[dict[str, Any]]:
    return [
        {
            **case,
            "result": "not_run",
            "evidence_status": "unknown",
            "production_safety_classification": "PROD_SAFE",
            "runtime_execution": "blocked_until_approved_task",
        }
        for case in GUARD_CASES
    ]


def build_report(metadata_path: Path | None = None) -> dict[str, Any]:
    metadata, load_reasons = _load_metadata(metadata_path)
    normalized = {
        name: _normalize_prerequisite(name, metadata.get(name))
        for name in REQUIRED_PREREQUISITES
    }
    prerequisites = {name: value.to_json() for name, value in normalized.items()}
    redaction_status = "redacted" if any(value.redacted for value in normalized.values()) else "not_applicable"

    blocked_reasons = list(load_reasons)
    for name, value in prerequisites.items():
        if not value["present"]:
            blocked_reasons.append(f"{name} is not approved or not present.")
        if value["evidence_status"] != "confirmed":
            blocked_reasons.append(f"{name} does not have confirmed evidence.")

    overall_status = "blocked" if blocked_reasons else "not_run"
    execution_notes = [
        "TASK-002 creates a guard-check skeleton only; runtime guard execution belongs to a future approved task."
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "task_id": TASK_ID,
        "mode": "BOUNDED_AUTONOMOUS",
        "tool_name": TOOL_NAME,
        "overall_status": overall_status,
        "evidence_status": "unknown",
        "production_safety_classification": "PROD_SAFE",
        "redaction_status": redaction_status,
        "prerequisites": prerequisites,
        "guard_cases": _guard_cases(),
        "blocked_reasons": blocked_reasons,
        "execution_notes": execution_notes,
        "risks": [
            {
                "id": "RISK-014",
                "level": "High",
                "status": "likely",
                "summary": "Exported component guard checks could become unsafe if they publish runtime recipes or probe without approvals.",
            }
        ],
        "unknowns": [
            {
                "id": "U-004",
                "status": "unknown",
                "question": "Which exported surfaces are intentional and approved for benign guard checks?",
            }
        ],
        "verification": [
            {
                "name": "guard-skeleton-generation",
                "classification": "PROD_SAFE",
                "result": "not_run",
                "note": "Generated a public-safe guard skeleton; Android/device/runtime interaction remains out of scope.",
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
    parser = argparse.ArgumentParser(description="Generate a TASK-002 exported component guard skeleton report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON guard metadata.",
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

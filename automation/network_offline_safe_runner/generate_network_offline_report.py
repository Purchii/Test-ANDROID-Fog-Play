"""Generate a public-safe TASK-007 network/offline policy report.

The tool performs no Android, device, APK, backend, proxy, packet, network or
production interaction. It only normalizes optional public-safe metadata,
redacts sensitive-looking values and creates a fail-closed not-run plan.
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
TASK_ID = "TASK-007"
TOOL_NAME = "network_offline_safe_runner.network_offline_report_generator"
MODE = "BOUNDED_AUTONOMOUS"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE"

REQUIRED_PREREQUISITES = (
    "approved_build",
    "approved_target",
    "approved_config",
    "network_profile_policy",
    "resource_budget",
    "redaction_policy",
    "evidence_storage",
    "cleanup_rollback",
    "security_review",
    "qa_review",
)
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
PLANNED_CHECKS = (
    {
        "id": "NO-001",
        "category": "offline_startup",
        "purpose": "Plan for observing startup behavior under an approved offline profile.",
        "risk_level": "R1",
    },
    {
        "id": "NO-002",
        "category": "offline_recovery",
        "purpose": "Plan for observing recovery after connectivity is restored by an approved future task.",
        "risk_level": "R1",
    },
    {
        "id": "NO-003",
        "category": "reconnect_during_stream_guard",
        "purpose": "Plan for category-level stream reconnect behavior without executing stream or network actions.",
        "risk_level": "R1",
    },
    {
        "id": "NO-004",
        "category": "high_latency_guard",
        "purpose": "Plan for approved latency profile coverage without publishing network recipes.",
        "risk_level": "R2",
    },
    {
        "id": "NO-005",
        "category": "interruption_error_state",
        "purpose": "Plan for public-safe error-state observation when approved network prerequisites exist.",
        "risk_level": "R1",
    },
    {
        "id": "NO-006",
        "category": "redacted_network_evidence",
        "purpose": "Plan for redacted evidence references only; raw traffic evidence stays out of public reports.",
        "risk_level": "R1",
    },
)
REDACTION_PATTERNS = (
    (re.compile(r"https?://[^\s)]+", re.IGNORECASE), "[REDACTED_URL]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (
        re.compile(r"\bauthorization\s*[:=]\s*(?:bearer\s+)?[^\s,;]+", re.IGNORECASE),
        "authorization=[REDACTED_SECRET]",
    ),
    (
        re.compile(
            r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|apikey|api key|key)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED_SECRET]",
    ),
    (re.compile(r"\b[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?<!\w)/(?:mnt/[A-Za-z]|home|Users|tmp|var|private)/[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9_+=/-]{32,}(?![A-Za-z0-9])"), "[REDACTED_OPAQUE_VALUE]"),
)


@dataclass(frozen=True)
class NormalizedText:
    value: str
    redacted: bool


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _redact_text(value: Any, default: str = "No public-safe note was provided.") -> NormalizedText:
    if isinstance(value, str) and value.strip():
        sanitized = value.strip()
    else:
        sanitized = default

    original = sanitized
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return NormalizedText(sanitized, sanitized != original)


def _normalize_evidence_status(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() in EVIDENCE_STATUSES:
        return value.strip().lower()
    return "unknown"


def _load_metadata(path: Path | None) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return {}, ["No approved network/offline metadata file was provided."]
    if not path.exists():
        return {}, ["Approved network/offline metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approved network/offline metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approved network/offline metadata must be a JSON object."]
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

    note = _redact_text(raw.get("note"), default="No public-safe note was provided.")
    return Prerequisite(
        name=name,
        present=raw.get("present") is True,
        evidence_status=_normalize_evidence_status(raw.get("evidence_status")),
        note=note.value,
        redacted=note.redacted,
    )


def _planned_network_checks() -> list[dict[str, Any]]:
    return [
        {
            **check,
            "result": "not_run",
            "evidence_status": "unknown",
            "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
            "execution_status": "blocked_until_approved_future_task",
            "artifact_refs": [],
            "notes": "Plan only; TASK-007 performed no Android, device, APK, network, backend, proxy or packet interaction.",
        }
        for check in PLANNED_CHECKS
    ]


def _normalize_artifacts(raw_artifacts: Any) -> tuple[list[dict[str, Any]], bool]:
    if raw_artifacts is None:
        return [], False
    if not isinstance(raw_artifacts, list):
        raw_artifacts = [raw_artifacts]

    redacted = False
    artifacts = []
    for index, raw_item in enumerate(raw_artifacts, start=1):
        if isinstance(raw_item, dict):
            name = _redact_text(raw_item.get("name"), default=f"artifact-{index}")
            reference = _redact_text(raw_item.get("reference"), default="No public-safe artifact reference was provided.")
            evidence_status = _normalize_evidence_status(raw_item.get("evidence_status"))
            redacted = redacted or name.redacted or reference.redacted
            artifacts.append(
                {
                    "name": name.value,
                    "reference": reference.value,
                    "evidence_status": evidence_status,
                }
            )
        else:
            reference = _redact_text(raw_item, default="No public-safe artifact reference was provided.")
            redacted = redacted or reference.redacted
            artifacts.append(
                {
                    "name": f"artifact-{index}",
                    "reference": reference.value,
                    "evidence_status": "unknown",
                }
            )
    return artifacts, redacted


def build_report(metadata_path: Path | None = None) -> dict[str, Any]:
    metadata, load_reasons = _load_metadata(metadata_path)
    normalized = {
        name: _normalize_prerequisite(name, metadata.get(name))
        for name in REQUIRED_PREREQUISITES
    }
    prerequisites = {name: value.to_json() for name, value in normalized.items()}

    blocked_reasons = list(load_reasons)
    for name, value in prerequisites.items():
        if not value["present"]:
            blocked_reasons.append(f"{name} is not approved or not present.")
        if value["evidence_status"] != "confirmed":
            blocked_reasons.append(f"{name} does not have confirmed evidence.")

    artifacts, artifacts_redacted = _normalize_artifacts(metadata.get("artifacts"))
    redacted = artifacts_redacted or any(value.redacted for value in normalized.values())
    overall_status = "blocked" if blocked_reasons else "not_run"

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "task_id": TASK_ID,
        "mode": MODE,
        "tool_name": TOOL_NAME,
        "overall_status": overall_status,
        "evidence_status": "unknown",
        "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
        "redaction_status": "redacted" if redacted else "not_applicable",
        "prerequisites": prerequisites,
        "planned_network_offline_checks": _planned_network_checks(),
        "blocked_reasons": blocked_reasons,
        "execution_notes": [
            "TASK-007 creates a public-safe local plan and report only.",
            "Android, device, APK, network, backend, proxy, packet and production interaction are out of scope.",
        ],
        "risks": [
            {
                "id": "RISK-005",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "Future network/offline execution requires approved prerequisites, resource budget and cleanup.",
            },
            {
                "id": "RISK-007",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "Network/offline evidence references must be redacted before public reporting.",
            },
        ],
        "unknowns": [
            {
                "id": "U-007",
                "evidence_status": "unknown",
                "question": "Which network/offline behaviors will approved future runtime evidence confirm?",
            }
        ],
        "verification": [
            {
                "name": "network-offline-report-generation",
                "classification": PRODUCTION_SAFETY_CLASSIFICATION,
                "result": "not_run",
                "evidence_status": "unknown",
                "note": "Generated a local report without Android, device, APK, network, backend, proxy or packet interaction.",
            }
        ],
        "artifacts": artifacts,
        "review": {
            "qa_reviewer_a": "pending",
            "qa_reviewer_b": "pending",
            "security_prod_safety_reviewer": "pending",
            "docs_scribe": "pending",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a TASK-007 public-safe network/offline policy report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON network/offline metadata.",
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

"""Generate a public-safe TASK-004 manual runtime map template report.

The tool performs no Android, device, APK, WebView, WebRTC, network or
production interaction. It only normalizes optional public-safe metadata,
redacts sensitive-looking values and creates not-run map/check templates.
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
TASK_ID = "TASK-004"
TOOL_NAME = "manual_runtime_maps.map_report_generator"
MODE = "BOUNDED_AUTONOMOUS"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE"

REQUIRED_PREREQUISITES = (
    "approved_build",
    "approved_target",
    "approved_config",
    "redaction_policy",
    "synthetic_fixture_policy",
    "evidence_storage",
    "cleanup_rollback",
)
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
MAP_CATEGORIES = (
    {
        "id": "MRM-001",
        "category": "first_screen",
        "purpose": "Template for recording the first visible screen after approved manual launch observation.",
        "risk_level": "R1",
    },
    {
        "id": "MRM-002",
        "category": "screen_inventory",
        "purpose": "Template for listing public-safe screen names or aliases observed during manual runtime mapping.",
        "risk_level": "R1",
    },
    {
        "id": "MRM-003",
        "category": "transitions",
        "purpose": "Template for recording public-safe navigation transitions without private endpoints or raw logs.",
        "risk_level": "R1",
    },
    {
        "id": "MRM-004",
        "category": "initial_focus",
        "purpose": "Template for recording initial Android TV focus target after an approved observation.",
        "risk_level": "R1",
    },
    {
        "id": "MRM-005",
        "category": "d_pad_directions",
        "purpose": "Template for mapping D-pad up/down/left/right focus movement at category level.",
        "risk_level": "R1",
    },
    {
        "id": "MRM-006",
        "category": "focus_traps",
        "purpose": "Template for recording suspected focus traps or unreachable controls from redacted evidence.",
        "risk_level": "R1",
    },
    {
        "id": "MRM-007",
        "category": "back_home",
        "purpose": "Template for recording Back/Home behavior without executing device actions in this task.",
        "risk_level": "R1",
    },
    {
        "id": "MRM-008",
        "category": "accessibility_localization",
        "purpose": "Template for recording accessibility and localization observations from approved manual evidence.",
        "risk_level": "R2",
    },
    {
        "id": "MRM-009",
        "category": "redacted_evidence",
        "purpose": "Template for linking only public-safe redacted evidence references.",
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
        return {}, ["No approved manual runtime map metadata file was provided."]
    if not path.exists():
        return {}, ["Approved manual runtime map metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approved manual runtime map metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approved manual runtime map metadata must be a JSON object."]
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


def _template_items(kind: str) -> list[dict[str, Any]]:
    return [
        {
            **category,
            "template_type": kind,
            "result": "not_run",
            "evidence_status": "unknown",
            "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
            "runtime_execution": "blocked_until_approved_future_task",
            "artifact_refs": [],
            "notes": "Template only; no runtime observation was performed by TASK-004.",
        }
        for category in MAP_CATEGORIES
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
        "screen_map_sections": _template_items("screen_map_section"),
        "focus_map_checks": _template_items("focus_map_check"),
        "blocked_reasons": blocked_reasons,
        "execution_notes": [
            "TASK-004 creates public-safe manual templates only; screen and focus observations remain not_run.",
            "Android, device, APK, WebView, WebRTC, network and production interaction are out of scope.",
        ],
        "risks": [
            {
                "id": "RISK-008",
                "level": "High",
                "evidence_status": "likely",
                "summary": "Runtime screen/focus behavior must remain unknown until approved runtime evidence exists.",
            },
            {
                "id": "RISK-007",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "Manual evidence references must be redacted before use in public reports.",
            },
        ],
        "unknowns": [
            {
                "id": "U-004",
                "evidence_status": "unknown",
                "question": "Which first screen, screen inventory, transitions and TV focus paths will approved runtime evidence confirm?",
            }
        ],
        "verification": [
            {
                "name": "manual-runtime-map-template-generation",
                "classification": PRODUCTION_SAFETY_CLASSIFICATION,
                "result": "not_run",
                "evidence_status": "unknown",
                "note": "Generated templates without Android/device/runtime interaction.",
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
    parser = argparse.ArgumentParser(description="Generate a TASK-004 manual runtime screen/focus map template report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON manual runtime map metadata.",
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

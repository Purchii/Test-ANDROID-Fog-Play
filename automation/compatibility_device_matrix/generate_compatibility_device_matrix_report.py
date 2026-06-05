"""Generate a public-safe TASK-009 compatibility/device matrix report.

The tool performs no Android, device, APK, WebView, WebRTC, payment, backend,
proxy, packet, network or production interaction. It only normalizes optional
public-safe metadata, redacts sensitive-looking values and creates a fail-closed
not-run compatibility matrix plan.
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
TASK_ID = "TASK-009"
TOOL_NAME = "compatibility_device_matrix.compatibility_device_matrix_report_generator"
MODE = "BOUNDED_AUTONOMOUS"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE"

REQUIRED_PREREQUISITES = (
    "approved_build",
    "approved_target",
    "approved_config",
    "device_inventory_policy",
    "matrix_scope",
    "compatibility_criteria",
    "redaction_policy",
    "evidence_storage",
    "fixture_policy",
    "security_review",
    "qa_review",
)
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
PLANNED_CHECKS = (
    {
        "id": "CDM-001",
        "category": "os_api_band",
        "purpose": "Plan category-level compatibility coverage across approved Android TV OS/API bands.",
        "risk_level": "R1",
    },
    {
        "id": "CDM-002",
        "category": "form_factor",
        "purpose": "Plan coverage across TV panel, set-top box and emulator categories.",
        "risk_level": "R1",
    },
    {
        "id": "CDM-003",
        "category": "performance_class",
        "purpose": "Plan startup, navigation and stream guard coverage across approved device performance classes.",
        "risk_level": "R1",
    },
    {
        "id": "CDM-004",
        "category": "display_output",
        "purpose": "Plan HD, full HD, UHD and overscan-safe layout compatibility coverage.",
        "risk_level": "R2",
    },
    {
        "id": "CDM-005",
        "category": "input_focus",
        "purpose": "Plan D-pad, Back/Home and focus compatibility coverage for approved target aliases.",
        "risk_level": "R1",
    },
    {
        "id": "CDM-006",
        "category": "network_class",
        "purpose": "Plan category-level compatibility against approved network profile aliases.",
        "risk_level": "R1",
    },
    {
        "id": "CDM-007",
        "category": "locale_accessibility",
        "purpose": "Plan localization, text length and accessibility scaling compatibility coverage.",
        "risk_level": "R2",
    },
    {
        "id": "CDM-008",
        "category": "webview_webrtc_surface",
        "purpose": "Plan hybrid/WebView/WebRTC capability categories without executing those flows in TASK-009.",
        "risk_level": "R1",
    },
    {
        "id": "CDM-009",
        "category": "install_update_path",
        "purpose": "Plan install, upgrade and data-retention category coverage for future approved tasks.",
        "risk_level": "R1",
    },
    {
        "id": "CDM-010",
        "category": "redacted_evidence",
        "purpose": "Plan validation that compatibility evidence references remain public-safe and redacted.",
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
    (
        re.compile(
            r"\b(serial|imei|imsi|android[_ -]?id|device[_ -]?id|mac)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED_DEVICE_ID]",
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
        return {}, ["No approved compatibility/device matrix metadata file was provided."]
    if not path.exists():
        return {}, ["Approved compatibility/device matrix metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approved compatibility/device matrix metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approved compatibility/device matrix metadata must be a JSON object."]
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


def _planned_compatibility_checks() -> list[dict[str, Any]]:
    return [
        {
            **check,
            "result": "not_run",
            "evidence_status": "unknown",
            "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
            "execution_status": "blocked_until_approved_future_task",
            "artifact_refs": [],
            "notes": "Plan only; TASK-009 performed no Android, device, APK, runtime or compatibility execution.",
        }
        for check in PLANNED_CHECKS
    ]


def _default_device_profiles() -> list[dict[str, Any]]:
    return [
        {
            "alias": "device-template-001",
            "target_category": "unknown",
            "os_api_band": "unknown",
            "form_factor": "unknown",
            "display_class": "unknown",
            "input_class": "unknown",
            "network_class": "unknown",
            "locale_class": "unknown",
            "evidence_status": "unknown",
            "notes": "Template only; no device inventory was collected by TASK-009.",
        }
    ]


def _normalize_device_profiles(raw_profiles: Any) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(raw_profiles, list) or not raw_profiles:
        return _default_device_profiles(), False

    profiles = []
    redacted = False
    allowed_text_fields = (
        "alias",
        "target_category",
        "os_api_band",
        "form_factor",
        "display_class",
        "input_class",
        "network_class",
        "locale_class",
        "notes",
    )
    for index, raw_profile in enumerate(raw_profiles, start=1):
        if not isinstance(raw_profile, dict):
            text = _redact_text(raw_profile, default=f"device-template-{index:03d}")
            redacted = redacted or text.redacted
            profiles.append(
                {
                    **_default_device_profiles()[0],
                    "alias": f"device-template-{index:03d}",
                    "notes": text.value,
                }
            )
            continue

        normalized: dict[str, Any] = {}
        for field in allowed_text_fields:
            default = f"device-template-{index:03d}" if field == "alias" else "unknown"
            if field == "notes":
                default = "No public-safe device profile note was provided."
            text = _redact_text(raw_profile.get(field), default=default)
            redacted = redacted or text.redacted
            normalized[field] = text.value
        normalized["evidence_status"] = _normalize_evidence_status(raw_profile.get("evidence_status"))
        profiles.append(normalized)

    return profiles, redacted


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

    device_profiles, profiles_redacted = _normalize_device_profiles(metadata.get("device_profiles"))
    artifacts, artifacts_redacted = _normalize_artifacts(metadata.get("artifacts"))
    redacted = profiles_redacted or artifacts_redacted or any(value.redacted for value in normalized.values())
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
        "device_profiles": device_profiles,
        "planned_compatibility_checks": _planned_compatibility_checks(),
        "blocked_reasons": blocked_reasons,
        "execution_notes": [
            "TASK-009 creates a public-safe local compatibility matrix plan and report only.",
            "Android, device, APK, WebView, WebRTC, payment, backend, proxy, packet, network and production interaction are out of scope.",
        ],
        "risks": [
            {
                "id": "RISK-008",
                "level": "High",
                "evidence_status": "likely",
                "summary": "Runtime compatibility must not be claimed as verified without approved build/device/config evidence.",
            },
            {
                "id": "RISK-007",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "Device profile and compatibility evidence references must be redacted before public reporting.",
            },
        ],
        "unknowns": [
            {
                "id": "U-009",
                "evidence_status": "unknown",
                "question": "Which compatibility behaviors and device coverage rows will approved future runtime evidence confirm?",
            }
        ],
        "verification": [
            {
                "name": "compatibility-device-matrix-report-generation",
                "classification": PRODUCTION_SAFETY_CLASSIFICATION,
                "result": "not_run",
                "evidence_status": "unknown",
                "note": "Generated a local matrix report without Android, device, APK, runtime, network or production interaction.",
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
    parser = argparse.ArgumentParser(description="Generate a TASK-009 public-safe compatibility/device matrix report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON compatibility/device matrix metadata.",
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

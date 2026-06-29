"""Generate a public-safe TASK-003 release gate report.

The tool performs no Android, device, APK, network, WebView, WebRTC or
production interaction. It only normalizes optional public-safe metadata,
redacts sensitive-looking values and fails closed when evidence is missing.
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
TASK_ID = "TASK-003"
TOOL_NAME = "reporting.release_gate_report_generator"
MODE = "BOUNDED_AUTONOMOUS"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE"

EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
GATE_STATUSES = {"pass", "fail", "blocked", "not_run"}
PASSABLE_GATE_STATUSES = {"pass"}
REQUIRED_REVIEWERS = (
    "qa_reviewer_a",
    "qa_reviewer_b",
    "security_prod_safety_reviewer",
    "docs_scribe",
)
PASSING_REVIEW_STATUSES = {"approved", "confirmed"}
REQUIRED_PREREQUISITES = (
    "approved_build",
    "approved_target",
    "approved_config",
    "redaction_policy",
    "synthetic_fixture_policy",
)
DEFAULT_RELEASE_GATES = (
    {
        "id": "RG-001",
        "name": "prerequisites",
        "risk_level": "R0",
        "runtime_dependent": False,
        "description": "Approved public-safe build, target, config and evidence metadata are present.",
    },
    {
        "id": "RG-002",
        "name": "runtime_startup",
        "risk_level": "R0",
        "runtime_dependent": True,
        "description": "Android TV startup evidence is confirmed by approved public-safe metadata.",
    },
    {
        "id": "RG-003",
        "name": "first_focus",
        "risk_level": "R1",
        "runtime_dependent": True,
        "description": "Initial TV focus evidence is confirmed by approved public-safe metadata.",
    },
    {
        "id": "RG-004",
        "name": "exported_component_guards",
        "risk_level": "R0",
        "runtime_dependent": True,
        "description": "Exported component guard outcome is confirmed by approved public-safe metadata.",
    },
    {
        "id": "RG-005",
        "name": "auth_session_guard",
        "risk_level": "R0",
        "runtime_dependent": True,
        "description": "Auth/session guard outcome is confirmed by approved public-safe metadata.",
    },
    {
        "id": "RG-006",
        "name": "redacted_evidence",
        "risk_level": "R1",
        "runtime_dependent": False,
        "description": "Evidence and artifact references are public-safe and redacted.",
    },
    {
        "id": "RG-007",
        "name": "network_offline_recovery",
        "risk_level": "R1",
        "runtime_dependent": True,
        "description": "Network/offline recovery outcome is confirmed by approved public-safe metadata.",
    },
    {
        "id": "RG-008",
        "name": "compatibility_device_matrix",
        "risk_level": "R1",
        "runtime_dependent": True,
        "description": "Compatibility/device matrix outcome is confirmed by approved public-safe metadata.",
    },
    {
        "id": "RG-009",
        "name": "webview_payment_safe_boundary",
        "risk_level": "R1",
        "runtime_dependent": True,
        "description": "WebView/payment-safe boundary outcome is confirmed by approved public-safe metadata.",
    },
    {
        "id": "RG-010",
        "name": "ci_nightly_smoke_readiness",
        "risk_level": "R1",
        "runtime_dependent": True,
        "description": "CI/nightly smoke readiness is confirmed by approved public-safe metadata.",
    },
    {
        "id": "RG-011",
        "name": "navigation_transition_coverage",
        "risk_level": "R1",
        "runtime_dependent": True,
        "description": "Navigation transition coverage is confirmed by approved public-safe metadata.",
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
class NormalizedText:
    value: str
    redacted: bool


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


def _normalize_gate_status(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip().lower() in GATE_STATUSES:
        return value.strip().lower()
    return default


def _load_metadata(path: Path | None) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return {}, ["No approved release metadata file was provided."]
    if not path.exists():
        return {}, ["Approved release metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approved release metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approved release metadata must be a JSON object."]
    return loaded, []


def _normalize_prerequisites(metadata: dict[str, Any]) -> tuple[dict[str, Any], list[str], bool]:
    raw_prerequisites = metadata.get("prerequisites")
    if not isinstance(raw_prerequisites, dict):
        raw_prerequisites = {}

    blocked_reasons = []
    redacted = False
    prerequisites: dict[str, Any] = {}
    for name in REQUIRED_PREREQUISITES:
        raw_item = raw_prerequisites.get(name)
        if not isinstance(raw_item, dict):
            raw_item = {}

        present = raw_item.get("present") is True
        evidence_status = _normalize_evidence_status(raw_item.get("evidence_status"))
        note = _redact_text(raw_item.get("note"), default=f"{name} metadata is missing or not an object.")
        redacted = redacted or note.redacted

        if not present:
            blocked_reasons.append(f"{name} is not approved or not present.")
        if evidence_status != "confirmed":
            blocked_reasons.append(f"{name} does not have confirmed evidence.")

        prerequisites[name] = {
            "present": present,
            "evidence_status": evidence_status,
            "note": note.value,
        }

    return prerequisites, blocked_reasons, redacted


def _raw_gate(metadata: dict[str, Any], name: str) -> dict[str, Any]:
    raw_gates = metadata.get("release_gates")
    if isinstance(raw_gates, dict) and isinstance(raw_gates.get(name), dict):
        return raw_gates[name]
    return {}


def _normalize_gate(
    gate_definition: dict[str, Any],
    metadata: dict[str, Any],
    prerequisite_reasons: list[str],
) -> tuple[dict[str, Any], list[str], bool]:
    name = gate_definition["name"]
    raw_gate = _raw_gate(metadata, name)
    default_status = "blocked" if name == "prerequisites" else "not_run"
    status = _normalize_gate_status(raw_gate.get("status"), default=default_status)
    evidence_status = _normalize_evidence_status(raw_gate.get("evidence_status"))
    note = _redact_text(raw_gate.get("note"), default="No public-safe gate note was provided.")
    artifacts, artifacts_redacted = _normalize_artifacts(raw_gate.get("artifacts"))

    blocked_reasons = []
    if name == "prerequisites" and prerequisite_reasons:
        status = "blocked"
        blocked_reasons.extend(prerequisite_reasons)

    if gate_definition["risk_level"] in {"R0", "R1"}:
        if status == "pass" and evidence_status != "confirmed":
            status = "blocked"
            blocked_reasons.append(f"{name} requested pass without confirmed evidence.")
        elif status in {"blocked", "fail", "not_run"}:
            blocked_reasons.append(f"{name} gate is {status}.")
        elif evidence_status != "confirmed":
            blocked_reasons.append(f"{name} lacks confirmed evidence.")

    if gate_definition["runtime_dependent"] and status == "pass" and evidence_status != "confirmed":
        status = "blocked"
        blocked_reasons.append(f"{name} is runtime-dependent and cannot pass without confirmed evidence.")

    return (
        {
            **gate_definition,
            "status": status,
            "evidence_status": evidence_status,
            "note": note.value,
            "artifacts": artifacts,
            "blocked_reasons": blocked_reasons,
        },
        blocked_reasons,
        note.redacted or artifacts_redacted,
    )


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


def _normalize_public_safe_list(raw_value: Any, default_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(raw_value, list):
        return default_items, False

    redacted = False
    items = []
    for index, raw_item in enumerate(raw_value, start=1):
        if isinstance(raw_item, dict):
            normalized: dict[str, Any] = {}
            for key, value in raw_item.items():
                if key == "evidence_status" or key == "status":
                    normalized[key] = _normalize_evidence_status(value)
                elif isinstance(value, str):
                    text = _redact_text(value)
                    redacted = redacted or text.redacted
                    normalized[key] = text.value
                else:
                    if isinstance(value, (bool, int, float)) or value is None:
                        normalized[key] = value
                    else:
                        text = _redact_text(str(value))
                        redacted = redacted or text.redacted
                        normalized[key] = text.value
            items.append(normalized)
        else:
            text = _redact_text(raw_item, default=f"item-{index}")
            redacted = redacted or text.redacted
            items.append({"summary": text.value, "evidence_status": "unknown"})
    return items, redacted


def _normalize_review(raw_review: Any) -> tuple[dict[str, str], bool]:
    default_review = {
        "qa_reviewer_a": "pending",
        "qa_reviewer_b": "pending",
        "security_prod_safety_reviewer": "pending",
        "docs_scribe": "pending",
    }
    if not isinstance(raw_review, dict):
        return default_review, False

    redacted = False
    review = {}
    for key, default in default_review.items():
        text = _redact_text(raw_review.get(key), default=default)
        redacted = redacted or text.redacted
        review[key] = text.value
    return review, redacted


def _review_blockers(review: dict[str, str]) -> list[str]:
    blocked_reasons = []
    for reviewer in REQUIRED_REVIEWERS:
        if review.get(reviewer, "pending").strip().lower() not in PASSING_REVIEW_STATUSES:
            blocked_reasons.append(f"{reviewer} review must be approved or confirmed.")
    return blocked_reasons


def build_report(metadata_path: Path | None = None) -> dict[str, Any]:
    metadata, load_reasons = _load_metadata(metadata_path)
    metadata_present = not load_reasons

    prerequisites, prerequisite_reasons, redacted = _normalize_prerequisites(metadata)
    release_gates = []
    blocked_reasons = list(load_reasons)
    if not metadata_present:
        blocked_reasons.append("Release decision requires explicit public-safe metadata.")
    blocked_reasons.extend(prerequisite_reasons)

    for gate_definition in DEFAULT_RELEASE_GATES:
        gate, gate_reasons, gate_redacted = _normalize_gate(gate_definition, metadata, prerequisite_reasons)
        release_gates.append(gate)
        blocked_reasons.extend(gate_reasons)
        redacted = redacted or gate_redacted

    top_artifacts, artifact_redacted = _normalize_artifacts(metadata.get("artifacts"))
    redacted = redacted or artifact_redacted

    risks, risk_redacted = _normalize_public_safe_list(
        metadata.get("risks"),
        [
            {
                "id": "RISK-008",
                "level": "High",
                "evidence_status": "likely",
                "summary": "Runtime checks must not be claimed as passed without approved build/device/config evidence.",
            },
            {
                "id": "RISK-014",
                "level": "High",
                "evidence_status": "likely",
                "summary": "Guard checks must remain public-safe and avoid runtime recipes or raw component inventories.",
            },
        ],
    )
    unknowns, unknown_redacted = _normalize_public_safe_list(
        metadata.get("unknowns"),
        [
            {
                "id": "U-001",
                "evidence_status": "unknown",
                "question": "Which approved runtime evidence can confirm R0/R1 release gates?",
            }
        ],
    )
    verification, verification_redacted = _normalize_public_safe_list(
        metadata.get("verification"),
        [
            {
                "name": "release-gate-report-generation",
                "classification": PRODUCTION_SAFETY_CLASSIFICATION,
                "result": "pass",
                "evidence_status": "confirmed",
                "note": "Generated release gate report without Android/device/runtime interaction.",
            }
        ],
    )
    redacted = redacted or risk_redacted or unknown_redacted or verification_redacted
    review, review_redacted = _normalize_review(metadata.get("review"))
    redacted = redacted or review_redacted
    review_reasons = _review_blockers(review)
    blocked_reasons.extend(review_reasons)

    r0_r1_gates = [gate for gate in release_gates if gate["risk_level"] in {"R0", "R1"}]
    release_decision = "pass"
    for gate in r0_r1_gates:
        if gate["status"] != "pass" or gate["evidence_status"] != "confirmed":
            release_decision = "blocked"
            break
    if review_reasons:
        release_decision = "blocked"

    evidence_status = "confirmed" if release_decision == "pass" else "unknown"
    overall_status = release_decision

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "task_id": TASK_ID,
        "mode": MODE,
        "tool_name": TOOL_NAME,
        "overall_status": overall_status,
        "release_decision": release_decision,
        "evidence_status": evidence_status,
        "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
        "redaction_status": "redacted" if redacted else "not_applicable",
        "prerequisites": prerequisites,
        "release_gates": release_gates,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "risks": risks,
        "unknowns": unknowns,
        "verification": verification,
        "artifacts": top_artifacts,
        "review": review,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a TASK-003 public-safe release gate report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON release metadata.",
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

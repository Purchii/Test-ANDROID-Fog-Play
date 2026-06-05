"""Generate a public-safe TASK-008 WebView/payment QA plan report.

The tool performs no Android, device, APK, WebView, payment, backend, network
or production interaction. It only normalizes optional public-safe metadata,
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
TASK_ID = "TASK-008"
TOOL_NAME = "webview_payment_safe_runner.webview_payment_safe_report_generator"
MODE = "NON_AUTONOMOUS"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE"

REQUIRED_PREREQUISITES = (
    "approved_build",
    "approved_target",
    "approved_config",
    "webview_fixture_policy",
    "payment_staging_policy",
    "synthetic_user_policy",
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
        "id": "WPS-001",
        "category": "webview_render_guard",
        "purpose": "Plan category-level WebView rendering checks for a future approved task.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-002",
        "category": "webview_navigation_boundary",
        "purpose": "Plan public-safe Back, D-pad and focus observations around WebView surfaces.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-003",
        "category": "webview_session_cookie_boundary",
        "purpose": "Plan verification that cookies, sessions and authorization values stay out of public evidence.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-004",
        "category": "webview_offline_error_state",
        "purpose": "Plan public-safe unavailable, cache and error-state observations without running WebView flows.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-005",
        "category": "payment_cancel",
        "purpose": "Plan staging-only cancel path observations for approved future payment fixtures.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-006",
        "category": "payment_failure",
        "purpose": "Plan staging-only failure and retry-copy observations for approved future payment fixtures.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-007",
        "category": "payment_pending_resume",
        "purpose": "Plan staging-only pending and resume observations for approved future payment fixtures.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-008",
        "category": "payment_duplicate_return",
        "purpose": "Plan idempotent duplicate return observations for approved future payment fixtures.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-009",
        "category": "payment_success_return",
        "purpose": "Plan staging-only success return observations with no real charge.",
        "risk_level": "R1",
    },
    {
        "id": "WPS-010",
        "category": "redacted_web_payment_evidence",
        "purpose": "Plan public-safe evidence references only; raw WebView/payment evidence stays out of reports.",
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
        re.compile(r"\b(card[_ -]?number|pan)\s*[:=]\s*(?:\d[ -]?){13,19}", re.IGNORECASE),
        r"\1=[REDACTED_PAYMENT_NUMBER]",
    ),
    (
        re.compile(
            r"\b(payment[_ -]?token|card[_ -]?token|card[_ -]?number|pan|cvv|cvc|cryptogram|three[_ -]?ds|3ds|acs[_ -]?token)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED_PAYMENT]",
    ),
    (
        re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
        "[REDACTED_PAYMENT_NUMBER]",
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
        return {}, ["No approved WebView/payment metadata file was provided."]
    if not path.exists():
        return {}, ["Approved WebView/payment metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approved WebView/payment metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approved WebView/payment metadata must be a JSON object."]
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


def _planned_webview_payment_checks() -> list[dict[str, Any]]:
    return [
        {
            **check,
            "result": "not_run",
            "evidence_status": "unknown",
            "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
            "execution_status": "blocked_until_approved_future_task",
            "artifact_refs": [],
            "notes": "Plan only; TASK-008 performed no Android, device, APK, WebView, payment, backend, network or production interaction.",
        }
        for check in PLANNED_CHECKS
    ]


def _default_flow_aliases() -> list[dict[str, Any]]:
    return [
        {
            "alias": "webview-payment-template-001",
            "surface_category": "unknown",
            "fixture_category": "unknown",
            "allowed_scope": "unknown",
            "evidence_status": "unknown",
            "notes": "Template only; no WebView or payment flow was executed by TASK-008.",
        }
    ]


def _normalize_flow_aliases(raw_flows: Any) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(raw_flows, list) or not raw_flows:
        return _default_flow_aliases(), False

    flows = []
    redacted = False
    allowed_text_fields = (
        "alias",
        "surface_category",
        "fixture_category",
        "allowed_scope",
        "notes",
    )
    for index, raw_flow in enumerate(raw_flows, start=1):
        if not isinstance(raw_flow, dict):
            text = _redact_text(raw_flow, default=f"webview-payment-template-{index:03d}")
            redacted = redacted or text.redacted
            flows.append(
                {
                    **_default_flow_aliases()[0],
                    "alias": f"webview-payment-template-{index:03d}",
                    "notes": text.value,
                }
            )
            continue

        normalized: dict[str, Any] = {}
        for field in allowed_text_fields:
            default = f"webview-payment-template-{index:03d}" if field == "alias" else "unknown"
            if field == "notes":
                default = "No public-safe WebView/payment flow note was provided."
            text = _redact_text(raw_flow.get(field), default=default)
            redacted = redacted or text.redacted
            normalized[field] = text.value
        normalized["evidence_status"] = _normalize_evidence_status(raw_flow.get("evidence_status"))
        flows.append(normalized)

    return flows, redacted


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

    flow_aliases, flows_redacted = _normalize_flow_aliases(metadata.get("flow_aliases"))
    artifacts, artifacts_redacted = _normalize_artifacts(metadata.get("artifacts"))
    redacted = flows_redacted or artifacts_redacted or any(value.redacted for value in normalized.values())
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
        "flow_aliases": flow_aliases,
        "planned_webview_payment_checks": _planned_webview_payment_checks(),
        "blocked_reasons": blocked_reasons,
        "execution_notes": [
            "TASK-008 creates a public-safe local WebView/payment QA plan and report only.",
            "Android, device, APK, WebView, payment, backend, network and production interaction are out of scope.",
            "Real payments, production mutation, security bypasses and raw private artifacts remain forbidden.",
        ],
        "risks": [
            {
                "id": "RISK-005",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "Future WebView/payment execution requires confirmed approvals, staging fixtures and cleanup.",
            },
            {
                "id": "RISK-007",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "WebView/payment evidence references must redact URLs, sessions, payment data and opaque values.",
            },
        ],
        "unknowns": [
            {
                "id": "U-008",
                "evidence_status": "unknown",
                "question": "Which WebView/payment behaviors will approved future runtime evidence confirm?",
            }
        ],
        "verification": [
            {
                "name": "webview-payment-safe-report-generation",
                "classification": PRODUCTION_SAFETY_CLASSIFICATION,
                "result": "not_run",
                "evidence_status": "unknown",
                "note": "Generated a local plan report without Android, device, APK, WebView, payment, backend, network or production interaction.",
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
    parser = argparse.ArgumentParser(description="Generate a TASK-008 public-safe WebView/payment QA plan report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON WebView/payment metadata.",
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

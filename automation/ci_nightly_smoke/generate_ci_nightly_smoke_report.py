"""Generate a public-safe TASK-010 CI/nightly smoke plan report.

The tool performs no Android, device, APK, runtime, WebView, payment, backend,
network, production or hosted CI interaction. It only normalizes optional
public-safe metadata, redacts sensitive-looking values and creates a fail-closed
not-run CI/nightly smoke plan.
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
TASK_ID = "TASK-010"
TOOL_NAME = "ci_nightly_smoke.ci_nightly_smoke_report_generator"
MODE = "BOUNDED_AUTONOMOUS"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE"

REQUIRED_PREREQUISITES = (
    "approved_static_ci_scope",
    "approved_schedule_policy",
    "repository_safety_policy",
    "resource_budget",
    "redaction_policy",
    "evidence_storage",
    "artifact_retention_policy",
    "dependency_policy",
    "security_review",
    "qa_review",
)
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
PLANNED_CHECKS = (
    {
        "id": "CNS-001",
        "category": "repository_hygiene",
        "purpose": "Plan branch status, diff cleanliness and forbidden public artifact checks.",
        "risk_level": "R1",
    },
    {
        "id": "CNS-002",
        "category": "python_unit_tests",
        "purpose": "Plan local unit-test invocation for public-safe repository code only.",
        "risk_level": "R1",
    },
    {
        "id": "CNS-003",
        "category": "python_compileall",
        "purpose": "Plan Python compile sanity for automation and tests.",
        "risk_level": "R2",
    },
    {
        "id": "CNS-004",
        "category": "release_gate_dry_run",
        "purpose": "Plan local release-gate report generation with runtime-dependent gates still blocked.",
        "risk_level": "R1",
    },
    {
        "id": "CNS-005",
        "category": "runtime_blocked_report_dry_run",
        "purpose": "Plan local runtime blocked-report generation without device or APK interaction.",
        "risk_level": "R1",
    },
    {
        "id": "CNS-006",
        "category": "network_offline_plan_dry_run",
        "purpose": "Plan local network/offline report generation without network interaction.",
        "risk_level": "R1",
    },
    {
        "id": "CNS-007",
        "category": "webview_payment_plan_dry_run",
        "purpose": "Plan local WebView/payment report generation without WebView, browser or payment interaction.",
        "risk_level": "R1",
    },
    {
        "id": "CNS-008",
        "category": "compatibility_matrix_plan_dry_run",
        "purpose": "Plan local compatibility report generation without device inventory or runtime execution.",
        "risk_level": "R1",
    },
    {
        "id": "CNS-009",
        "category": "public_safety_scan",
        "purpose": "Plan redaction-oriented scan of public report content and changed files.",
        "risk_level": "R1",
    },
    {
        "id": "CNS-010",
        "category": "redacted_summary_publish",
        "purpose": "Plan sanitized JSON summary publication only after approval.",
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
            r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|apikey|api key|key|"
            r"ci[_-]?token|github[_-]?token|gitlab[_-]?token|circle[_-]?token|runner[_-]?token|"
            r"actions[_-]?token|workflow[_-]?token|job[_-]?token|build[_-]?token)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED_SECRET]",
    ),
    (
        re.compile(
            r"\b(GITHUB_TOKEN|GH_TOKEN|GITLAB_TOKEN|CI_JOB_TOKEN|CIRCLE_TOKEN|BUILDKITE_TOKEN|"
            r"AZURE_DEVOPS_EXT_PAT|SYSTEM_ACCESSTOKEN)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED_CI_TOKEN]",
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
        return {}, ["No approved CI/nightly smoke metadata file was provided."]
    if not path.exists():
        return {}, ["Approved CI/nightly smoke metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approved CI/nightly smoke metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approved CI/nightly smoke metadata must be a JSON object."]
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


def _planned_ci_nightly_checks() -> list[dict[str, Any]]:
    return [
        {
            **check,
            "result": "not_run",
            "evidence_status": "unknown",
            "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
            "execution_status": "blocked_until_approved_future_task",
            "artifact_refs": [],
            "notes": "Plan only; TASK-010 performed no Android, device, APK, runtime, hosted CI, network or production interaction.",
        }
        for check in PLANNED_CHECKS
    ]


def _default_ci_jobs() -> list[dict[str, Any]]:
    return [
        {
            "alias": "ci-nightly-template-001",
            "job_category": "unknown",
            "trigger_category": "unknown",
            "runner_category": "unknown",
            "evidence_status": "unknown",
            "notes": "Template only; no live CI job or nightly schedule was executed by TASK-010.",
        }
    ]


def _normalize_ci_jobs(raw_jobs: Any) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(raw_jobs, list) or not raw_jobs:
        return _default_ci_jobs(), False

    jobs = []
    redacted = False
    allowed_text_fields = (
        "alias",
        "job_category",
        "trigger_category",
        "runner_category",
        "notes",
    )
    for index, raw_job in enumerate(raw_jobs, start=1):
        if not isinstance(raw_job, dict):
            text = _redact_text(raw_job, default=f"ci-nightly-template-{index:03d}")
            redacted = redacted or text.redacted
            jobs.append(
                {
                    **_default_ci_jobs()[0],
                    "alias": f"ci-nightly-template-{index:03d}",
                    "notes": text.value,
                }
            )
            continue

        normalized: dict[str, Any] = {}
        for field in allowed_text_fields:
            default = f"ci-nightly-template-{index:03d}" if field == "alias" else "unknown"
            if field == "notes":
                default = "No public-safe CI/nightly job note was provided."
            text = _redact_text(raw_job.get(field), default=default)
            redacted = redacted or text.redacted
            normalized[field] = text.value
        normalized["evidence_status"] = _normalize_evidence_status(raw_job.get("evidence_status"))
        jobs.append(normalized)

    return jobs, redacted


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

    ci_jobs, jobs_redacted = _normalize_ci_jobs(metadata.get("ci_jobs"))
    artifacts, artifacts_redacted = _normalize_artifacts(metadata.get("artifacts"))
    redacted = jobs_redacted or artifacts_redacted or any(value.redacted for value in normalized.values())
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
        "ci_jobs": ci_jobs,
        "planned_ci_nightly_checks": _planned_ci_nightly_checks(),
        "blocked_reasons": blocked_reasons,
        "execution_notes": [
            "TASK-010 creates a public-safe local CI/nightly smoke plan and report only.",
            "Android, device, APK, runtime, WebView, payment, backend, network, hosted CI and production interaction are out of scope.",
            "The generator never records successful CI, runtime or production execution.",
        ],
        "risks": [
            {
                "id": "RISK-005",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "Future CI/nightly execution requires approved static scope, resource budget and retention policy.",
            },
            {
                "id": "RISK-007",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "CI/nightly reports and artifacts must redact tokens, sessions, paths and opaque values.",
            },
        ],
        "unknowns": [
            {
                "id": "U-010",
                "evidence_status": "unknown",
                "question": "Which CI/nightly checks will be approved for hosted or scheduled execution in a future task?",
            }
        ],
        "verification": [
            {
                "name": "ci-nightly-smoke-report-generation",
                "classification": PRODUCTION_SAFETY_CLASSIFICATION,
                "result": "not_run",
                "evidence_status": "unknown",
                "note": "Generated a local plan report without Android, device, APK, runtime, hosted CI, network or production interaction.",
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
    parser = argparse.ArgumentParser(description="Generate a TASK-010 public-safe CI/nightly smoke plan report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON CI/nightly smoke metadata.",
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

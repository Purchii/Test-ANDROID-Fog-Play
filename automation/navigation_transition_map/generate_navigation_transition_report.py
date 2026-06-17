"""Generate a public-safe TASK-011 navigation transition map report.

The tool performs no Android, device, APK, WebView, WebRTC, payment, backend,
network or production interaction. It only normalizes optional public-safe
metadata, redacts sensitive-looking values and creates a fail-closed not-run
navigation transition map plan.
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
TASK_ID = "TASK-011"
TOOL_NAME = "navigation_transition_map.navigation_transition_report_generator"
MODE = "BOUNDED_AUTONOMOUS"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE"

REQUIRED_PREREQUISITES = (
    "approved_build",
    "approved_target",
    "approved_config",
    "navigation_scope",
    "screen_alias_policy",
    "input_event_policy",
    "fixture_policy",
    "resource_budget",
    "redaction_policy",
    "evidence_storage",
    "cleanup_rollback",
    "security_review",
    "qa_review",
)
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
PLANNED_TRANSITIONS = (
    {
        "id": "NTM-001",
        "category": "startup_to_first_screen",
        "design_guideline_category": "efficient_intuitive_entry",
        "from_screen_alias": "app_launch",
        "to_screen_alias": "first_screen_alias",
        "trigger": "future_approved_launch_observation",
        "purpose": "Plan the first visible screen transition after an approved app launch observation.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-002",
        "category": "home_to_catalog",
        "design_guideline_category": "axis_based_traversal",
        "from_screen_alias": "home_alias",
        "to_screen_alias": "catalog_alias",
        "trigger": "d_pad_select",
        "purpose": "Plan category-level transition coverage from primary home content to catalog surfaces.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-003",
        "category": "catalog_to_detail",
        "design_guideline_category": "four_way_dpad_select",
        "from_screen_alias": "catalog_alias",
        "to_screen_alias": "detail_alias",
        "trigger": "d_pad_select",
        "purpose": "Plan transition coverage from content lists to content details.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-004",
        "category": "detail_to_playback",
        "design_guideline_category": "select_semantics",
        "from_screen_alias": "detail_alias",
        "to_screen_alias": "playback_alias",
        "trigger": "start_playback_action",
        "purpose": "Plan transition coverage from details into streaming/playback surfaces.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-005",
        "category": "playback_controls",
        "design_guideline_category": "clear_focus_path",
        "from_screen_alias": "playback_alias",
        "to_screen_alias": "playback_controls_alias",
        "trigger": "d_pad_or_media_key",
        "purpose": "Plan transition and focus coverage for playback control visibility.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-006",
        "category": "back_navigation",
        "design_guideline_category": "predictable_back_no_infinite_loop",
        "from_screen_alias": "current_screen_alias",
        "to_screen_alias": "previous_or_safe_exit_alias",
        "trigger": "back",
        "purpose": "Plan Back behavior coverage without executing Android device commands.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-007",
        "category": "home_resume",
        "design_guideline_category": "home_semantics",
        "from_screen_alias": "foreground_screen_alias",
        "to_screen_alias": "resume_or_first_screen_alias",
        "trigger": "home_and_resume",
        "purpose": "Plan Home/resume transition coverage for future approved runtime evidence.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-008",
        "category": "auth_required_boundary",
        "design_guideline_category": "predictable_navigation_boundary",
        "from_screen_alias": "protected_surface_alias",
        "to_screen_alias": "auth_or_entitlement_alias",
        "trigger": "access_protected_action",
        "purpose": "Plan public-safe transition coverage around auth or entitlement boundaries.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-009",
        "category": "search_navigation",
        "design_guideline_category": "clear_focus_path",
        "from_screen_alias": "search_entry_alias",
        "to_screen_alias": "search_results_alias",
        "trigger": "search_submit",
        "purpose": "Plan search entry and result transition coverage using sanitized aliases only.",
        "risk_level": "R2",
    },
    {
        "id": "NTM-010",
        "category": "webview_or_hybrid_boundary",
        "design_guideline_category": "predictable_navigation_boundary",
        "from_screen_alias": "native_screen_alias",
        "to_screen_alias": "hybrid_surface_alias",
        "trigger": "open_hybrid_action",
        "purpose": "Plan category-level hybrid boundary transitions without WebView execution.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-011",
        "category": "error_empty_state",
        "design_guideline_category": "intuitive_recovery",
        "from_screen_alias": "requested_surface_alias",
        "to_screen_alias": "error_or_empty_state_alias",
        "trigger": "future_approved_negative_condition",
        "purpose": "Plan unavailable, empty or error-state transition coverage.",
        "risk_level": "R1",
    },
    {
        "id": "NTM-012",
        "category": "redacted_transition_evidence",
        "design_guideline_category": "public_safe_evidence",
        "from_screen_alias": "evidence_source_alias",
        "to_screen_alias": "report_alias",
        "trigger": "redacted_artifact_reference",
        "purpose": "Plan validation that transition evidence references stay redacted and public-safe.",
        "risk_level": "R1",
    },
)
DESIGN_GUIDANCE_REFERENCES = (
    {
        "id": "ANDROID-TV-DESIGN-NAVIGATION",
        "source": "Android Developers navigation on TV design guidance",
        "evidence_status": "confirmed",
        "applies_as": "public_design_guideline_reference_only",
        "summary": "TV navigation should be efficient, predictable and intuitive with simple remote-driven paths.",
    },
    {
        "id": "ANDROID-TV-CONTROLLER-SEMANTICS",
        "source": "Android Developers TV navigation training guidance",
        "evidence_status": "confirmed",
        "applies_as": "public_design_guideline_reference_only",
        "summary": "Coverage should model 4-way D-pad movement plus Select, Back and Home semantics.",
    },
    {
        "id": "ANDROID-TV-FOCUS-PATHS",
        "source": "Android Developers TV navigation training guidance",
        "evidence_status": "confirmed",
        "applies_as": "public_design_guideline_reference_only",
        "summary": "Future checks should look for a clear path to focusable elements and straightforward focus movement.",
    },
    {
        "id": "ANDROID-TV-BACK-AXES",
        "source": "Android Developers TV navigation architecture guidance",
        "evidence_status": "confirmed",
        "applies_as": "public_design_guideline_reference_only",
        "summary": "Future checks should model predictable Back behavior, no infinite loops and axis-based traversal for large hierarchies.",
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
        return {}, ["No approved navigation transition metadata file was provided."]
    if not path.exists():
        return {}, ["Approved navigation transition metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approved navigation transition metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approved navigation transition metadata must be a JSON object."]
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


def _planned_navigation_transitions() -> list[dict[str, Any]]:
    return [
        {
            **transition,
            "result": "not_run",
            "evidence_status": "unknown",
            "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
            "execution_status": "blocked_until_approved_future_task",
            "artifact_refs": [],
            "notes": "Plan only; TASK-011 performed no Android, device, APK, runtime, WebView, network or production interaction.",
        }
        for transition in PLANNED_TRANSITIONS
    ]


def _default_screen_aliases() -> list[dict[str, Any]]:
    return [
        {
            "alias": "screen-template-001",
            "screen_category": "unknown",
            "entry_category": "unknown",
            "exit_category": "unknown",
            "evidence_status": "unknown",
            "notes": "Template only; no runtime screen inventory was collected by TASK-011.",
        }
    ]


def _normalize_screen_aliases(raw_aliases: Any) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(raw_aliases, list) or not raw_aliases:
        return _default_screen_aliases(), False

    aliases = []
    redacted = False
    allowed_text_fields = (
        "alias",
        "screen_category",
        "entry_category",
        "exit_category",
        "notes",
    )
    for index, raw_alias in enumerate(raw_aliases, start=1):
        if not isinstance(raw_alias, dict):
            text = _redact_text(raw_alias, default=f"screen-template-{index:03d}")
            redacted = redacted or text.redacted
            aliases.append(
                {
                    **_default_screen_aliases()[0],
                    "alias": f"screen-template-{index:03d}",
                    "notes": text.value,
                }
            )
            continue

        normalized: dict[str, Any] = {}
        for field in allowed_text_fields:
            default = f"screen-template-{index:03d}" if field == "alias" else "unknown"
            if field == "notes":
                default = "No public-safe screen alias note was provided."
            text = _redact_text(raw_alias.get(field), default=default)
            redacted = redacted or text.redacted
            normalized[field] = text.value
        normalized["evidence_status"] = _normalize_evidence_status(raw_alias.get("evidence_status"))
        aliases.append(normalized)

    return aliases, redacted


def _default_transition_edges() -> list[dict[str, Any]]:
    return [
        {
            "alias": "transition-template-001",
            "from_screen_alias": "unknown",
            "to_screen_alias": "unknown",
            "trigger_category": "unknown",
            "risk_level": "unknown",
            "evidence_status": "unknown",
            "notes": "Template only; no navigation transition was observed by TASK-011.",
        }
    ]


def _normalize_transition_edges(raw_edges: Any) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(raw_edges, list) or not raw_edges:
        return _default_transition_edges(), False

    edges = []
    redacted = False
    allowed_text_fields = (
        "alias",
        "from_screen_alias",
        "to_screen_alias",
        "trigger_category",
        "risk_level",
        "notes",
    )
    for index, raw_edge in enumerate(raw_edges, start=1):
        if not isinstance(raw_edge, dict):
            text = _redact_text(raw_edge, default=f"transition-template-{index:03d}")
            redacted = redacted or text.redacted
            edges.append(
                {
                    **_default_transition_edges()[0],
                    "alias": f"transition-template-{index:03d}",
                    "notes": text.value,
                }
            )
            continue

        normalized: dict[str, Any] = {}
        for field in allowed_text_fields:
            default = f"transition-template-{index:03d}" if field == "alias" else "unknown"
            if field == "notes":
                default = "No public-safe transition edge note was provided."
            text = _redact_text(raw_edge.get(field), default=default)
            redacted = redacted or text.redacted
            normalized[field] = text.value
        normalized["evidence_status"] = _normalize_evidence_status(raw_edge.get("evidence_status"))
        edges.append(normalized)

    return edges, redacted


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

    screen_aliases, aliases_redacted = _normalize_screen_aliases(metadata.get("screen_aliases"))
    transition_edges, edges_redacted = _normalize_transition_edges(metadata.get("transition_edges"))
    artifacts, artifacts_redacted = _normalize_artifacts(metadata.get("artifacts"))
    redacted = (
        aliases_redacted
        or edges_redacted
        or artifacts_redacted
        or any(value.redacted for value in normalized.values())
    )
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
        "design_guidance_references": list(DESIGN_GUIDANCE_REFERENCES),
        "screen_aliases": screen_aliases,
        "transition_edges": transition_edges,
        "planned_transitions": _planned_navigation_transitions(),
        "blocked_reasons": blocked_reasons,
        "execution_notes": [
            "TASK-011 creates a public-safe local navigation transition map plan and report only.",
            "Android, device, APK, runtime, WebView, WebRTC, payment, backend, network and production interaction are out of scope.",
            "The generator never records successful navigation, runtime or device execution.",
        ],
        "risks": [
            {
                "id": "RISK-008",
                "level": "High",
                "evidence_status": "likely",
                "summary": "Navigation transition behavior must remain unknown until approved runtime evidence exists.",
            },
            {
                "id": "RISK-007",
                "level": "Critical",
                "evidence_status": "likely",
                "summary": "Transition map evidence references must redact URLs, sessions, local paths and opaque values.",
            },
        ],
        "unknowns": [
            {
                "id": "U-011",
                "evidence_status": "unknown",
                "question": "Which screen aliases and transition edges will approved future runtime evidence confirm?",
            }
        ],
        "verification": [
            {
                "name": "navigation-transition-map-report-generation",
                "classification": PRODUCTION_SAFETY_CLASSIFICATION,
                "result": "not_run",
                "evidence_status": "unknown",
                "note": "Generated a local plan report without Android, device, APK, runtime, WebView, network or production interaction.",
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
    parser = argparse.ArgumentParser(description="Generate a TASK-011 public-safe navigation transition map report.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional public-safe JSON navigation transition metadata.",
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

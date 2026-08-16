"""Fixed-path public-safe TASK-058A reporter and validator.

This module never invokes Android tooling or reads raw command output.  Its
only optional local input is the exact sanitized projection generated below
the ignored TASK-058A run directory after independent review.  It cannot issue
Security approval; it can only validate and project a recorded decision.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from automation.reporting.generate_report_manifest import _validate_v2_envelope
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from automation.reporting.generate_report_manifest import _validate_v2_envelope


TASK_ID = "TASK-058A"
RUN_ID = "task058a-phone-launch-readiness-pre-auth-20260816-001"
SCHEMA_VERSION = "evidence-report-envelope-v2"
PROJECTION_SCHEMA = "task058a-public-safe-projection-v1"
GENERATED_AT = "2026-08-16T10:40:00Z"
EXPIRES_AT = "2026-08-16T14:30:00Z"
REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_SPEC = REPO_ROOT / "tasks/TASK_058A_phone_launch_readiness_pre_auth_continuation.md"
LOCAL_PROJECTION = REPO_ROOT / ".qa_local/task058a" / RUN_ID / "public_projection.json"
REPORT_ROOT = REPO_ROOT / "docs/qa/reports"
REPORT_STEM = "task058a_phone_launch_readiness_pre_auth_continuation"
READINESS_OUTPUT = REPORT_ROOT / f"{REPORT_STEM}.readiness-ledger.csv"
PASSPORT_OUTPUT = REPORT_ROOT / f"{REPORT_STEM}.passport-ledger.csv"
SCENARIO_OUTPUT = REPORT_ROOT / f"{REPORT_STEM}.scenario-ledger.csv"
CLEANUP_OUTPUT = REPORT_ROOT / f"{REPORT_STEM}.cleanup-ledger.csv"
REPORT_OUTPUT = REPORT_ROOT / f"{REPORT_STEM}.summary.json"

READINESS_HEADERS = (
    "authority_id", "subject_alias", "freshness", "evidence_status",
    "evidence_ids", "reviewer_gate", "expires_at", "terminal_status",
    "reason_code", "release_effect",
)
PASSPORT_HEADERS = (
    "passport_id", "passport_type", "subject_alias", "task_id", "run_id",
    "owner_authority", "observation_status", "evidence_status",
    "reviewer_gate", "issued_at", "expires_at", "retention_redaction",
    "action_budget", "kill_switch", "cleanup_contract", "reason_code",
    "terminal_status", "release_effect",
)
SCENARIO_HEADERS = (
    "row_id", "source_crosswalk_id", "approved_scope", "reachable", "status",
    "screen_alias", "state_category", "focus_category", "action_category",
    "evidence_status", "screenshot_id", "ui_tree_id", "log_marker_id",
    "reason_code", "release_effect", "cleanup_status", "checkpoint_id",
    "from_checkpoint_id", "to_checkpoint_id",
)
CLEANUP_HEADERS = (
    "cleanup_id", "target_force_stop", "home", "capture_shutdown",
    "first_launch_restored", "launch_count", "safe_pre_auth_action_count",
    "forbidden_action_count", "evidence_status", "reviewer_gate",
    "terminal_status", "reason_code", "release_effect",
)

AUTHORITY_IDS = tuple(f"task057-authority-{n:02d}-{suffix}" for n, suffix in (
    (1, "canonical-phone-full"),
    (2, "installed-compatibility"),
    (3, "current-phone-selector"),
    (4, "downgrade-safety"),
    (5, "synthetic-session"),
    (6, "clean-first-launch"),
    (7, "evidence-cleanup-security"),
))
AUTHORITY_ALIASES = (
    "task058-selected-phone-full-001", "installed-phone-full-build",
    "phone-current-001", "ordinary-downgrade-guard",
    "task058a-pre-auth-no-real-session-001",
    "task058a-clean-first-launch-001", "task058a-evidence-cleanup-001",
)
PASSPORT_TYPES = (
    "pre_auth_no_real_session", "owner_approved_clean_first_launch",
    "runtime_evidence_cleanup",
)
REQUIRED_SCENARIOS = (
    ("task058a-scenario-001", "phone-coverage-001", "first_launch"),
    ("task058a-scenario-002", "phone-coverage-017", "auth_guard"),
    ("task058a-transition-001", "A002", "cold_launch_auth_guard_transition"),
)
TERMINAL_BLOCKED = {
    "blocked_by_boundary", "blocked_by_tooling", "blocked_by_external_state",
    "blocked_by_fixture",
}
SAFE_VALUE = re.compile(r"^[A-Za-z0-9_.:;-]+$")
FORBIDDEN = (
    re.compile(r"(?i)(?:^|[\s\"'])[a-z]:[\\/]"),
    re.compile(r"(?i)(?:^|[\\/])\.qa_local(?:[\\/]|$)"),
    re.compile(r"(?i)\b(?:https?|wss?|file|intent|market|mailto):"),
    re.compile(r"(?<![\w-])(?:\d{1,3}\.){3}\d{1,3}(?![\w-])"),
    re.compile(r"(?i)\b[0-9a-f]{32,}\b"),
    re.compile(r"(?i)\b(?:[a-z][a-z0-9_]*\.){2,}[a-z][a-z0-9_]*\b"),
)


class ContractError(ValueError):
    """The public-safe TASK-058A contract failed closed."""


def _utc(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ContractError("timestamp_must_be_utc_z")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ContractError("timestamp_invalid") from exc
    return result.astimezone(timezone.utc)


def _safe(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise ContractError(f"unsafe_public_value:{field}")
    if any(pattern.search(value) for pattern in FORBIDDEN):
        raise ContractError(f"unsafe_public_value:{field}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def _csv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _parse_csv(data: bytes, headers: Sequence[str], label: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
    except UnicodeError as exc:
        raise ContractError(f"{label}_utf8_invalid") from exc
    if tuple(reader.fieldnames or ()) != tuple(headers):
        raise ContractError(f"{label}_headers_drift")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ContractError(f"{label}_extra_cells")
    return rows


def baseline_readiness_rows() -> list[dict[str, str]]:
    states = (
        ("confirmed", "task058a-owner-team-confirmation;task058a-retained-machine-authority;task058a-current-opening-package-observation", "GO_RUNTIME_OWNER_OVERRIDE", "observed_pass", "canonical_phone_full_confirmed_owner_override", "candidate_evidence"),
        ("confirmed", "task058a-owner-team-confirmation;task058a-retained-machine-authority;task058a-current-opening-package-observation", "GO_RUNTIME_OWNER_OVERRIDE", "observed_pass", "installed_app_build_identity_confirmed_owner_override", "candidate_evidence"),
        ("unknown", "task058a-owner-override-authority", "GO_RUNTIME_OWNER_OVERRIDE", "blocked_by_external_state", "selector_unrelated_delta_waived_owner_override", "blocks_release"),
        ("confirmed", "task058a-zero-package-mutation-authority", "GO_RUNTIME_OWNER_OVERRIDE", "observed_pass", "zero_reinstall_uninstall_reset_retry", "candidate_evidence"),
        ("confirmed", "task058a-owner-pre-auth-passport;task058a-observed-pre-auth-no-real-session", "GO_RUNTIME_OWNER_OVERRIDE", "observed_pass", "pre_auth_no_real_session_confirmed", "candidate_evidence"),
        ("confirmed", "task058a-owner-clean-first-launch-passport;task058a-clean-first-launch-consumed-once", "GO_RUNTIME_OWNER_OVERRIDE", "observed_pass", "clean_first_launch_consumed_once_not_restored", "candidate_evidence"),
        ("confirmed", "task058a-reviewed-evidence-budget-cleanup;task058a-owner-override-authority", "GO_RUNTIME_OWNER_OVERRIDE", "observed_pass", "evidence_budget_cleanup_reviewed_owner_override", "candidate_evidence"),
    )
    rows = []
    for authority_id, alias, state in zip(AUTHORITY_IDS, AUTHORITY_ALIASES, states):
        evidence, ids, gate, terminal, reason, effect = state
        rows.append(dict(zip(READINESS_HEADERS, (
            authority_id, alias, "fresh_current_run", evidence, ids, gate,
            EXPIRES_AT, terminal, reason, effect,
        ))))
    return rows


def baseline_passport_rows() -> list[dict[str, str]]:
    aliases = AUTHORITY_ALIASES[4:]
    rows = []
    for index, (passport_type, alias) in enumerate(zip(PASSPORT_TYPES, aliases), 1):
        rows.append(dict(zip(PASSPORT_HEADERS, (
            f"task058a-passport-{index:02d}", passport_type, alias, TASK_ID,
            RUN_ID, "confirmed_owner_authority_2026-08-16", "observed_confirmed",
            "confirmed", "GO_RUNTIME_OWNER_OVERRIDE", GENERATED_AT, EXPIRES_AT,
            "local_only_ttl_redacted_projection", "launch_1_pre_auth_20_all_forbidden_0",
            "target_force_stop_then_home_once", "force_stop_home_capture_shutdown_no_first_launch_restore",
            "owner_override_observation_review_confirmed", "observed_pass",
            "candidate_evidence",
        ))))
    return rows


def baseline_scenario_rows() -> list[dict[str, str]]:
    values = (
        ("task058a-scenario-001", "phone-coverage-001", "covered", "pre_auth_checkpoint_002", "first_launch", "initial_focus", "launch", "task058a-screenshot-002", "task058a-ui-tree-002", "task058a-log-marker-002", "first_launch_observed", "candidate_evidence", "task058a-checkpoint-002", "none", "none"),
        ("task058a-scenario-002", "phone-coverage-017", "covered", "pre_auth_checkpoint_002", "auth_guard", "auth_entry_focus", "observe_only", "task058a-screenshot-002", "task058a-ui-tree-002", "task058a-log-marker-002", "auth_guard_observed", "candidate_evidence", "task058a-checkpoint-002", "none", "none"),
        ("task058a-transition-001", "A002", "covered", "pre_auth_checkpoint_002", "cold_launch_auth_guard_transition", "initial_to_auth_focus", "launch_transition", "task058a-screenshot-pair-001-002", "task058a-ui-tree-pair-001-002", "task058a-log-marker-pair-001-002", "checkpoint001_to_checkpoint002_evidence_pair", "candidate_evidence", "task058a-checkpoint-002", "task058a-checkpoint-001", "task058a-checkpoint-002"),
        ("task058a-boundary-001", "task058a-discovered-authentication-entry-boundary", "blocked_by_boundary", "authentication_entry_boundary", "authentication_entry_boundary", "auth_entry_focus", "not_followed", "task058a-screenshot-002", "task058a-ui-tree-002", "task058a-log-marker-002", "authentication_boundary_not_followed", "candidate_evidence", "task058a-checkpoint-002", "none", "none"),
        ("task058a-anomaly-001", "task058a-discovered-left-edge-green-overlay", "covered", "pre_auth_checkpoint_002", "visual_overlay_anomaly", "not_accessibility_exposed", "visual_inspection", "task058a-screenshot-002", "task058a-ui-tree-002", "task058a-log-marker-002", "partial_green_left_edge_overlay_absent_from_ui_tree", "candidate_evidence", "task058a-checkpoint-002", "none", "none"),
    )
    return [dict(zip(SCENARIO_HEADERS, (
        row_id, source_id, "true", "true", status, alias, state, focus, action,
        "confirmed", screenshot, tree, marker, reason, effect,
        "cleanup_confirmed", checkpoint, from_checkpoint, to_checkpoint,
    ))) for row_id, source_id, status, alias, state, focus, action, screenshot, tree, marker, reason, effect, checkpoint, from_checkpoint, to_checkpoint in values]


def baseline_cleanup_rows() -> list[dict[str, str]]:
    return [dict(zip(CLEANUP_HEADERS, (
        "task058a-cleanup-001", "confirmed", "confirmed", "confirmed",
        "not_claimed", "1", "0", "0", "confirmed", "GO_RUNTIME_OWNER_OVERRIDE",
        "observed_pass", "force_stop_home_capture_shutdown_confirmed_no_restore", "candidate_evidence",
    )))]


def baseline_projection() -> dict[str, Any]:
    return {
        "schema": PROJECTION_SCHEMA,
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "generated_at_utc": GENERATED_AT,
        "expires_at_utc": EXPIRES_AT,
        "security_gate": "GO_RUNTIME_OWNER_OVERRIDE",
        "readiness": baseline_readiness_rows(),
        "passports": baseline_passport_rows(),
        "scenarios": baseline_scenario_rows(),
        "cleanup": baseline_cleanup_rows(),
        "collector": {
            "execution_status": "blocked_artifact_metadata_ambiguity",
            "native_stdout_stderr_direct_capture": True,
            "retry_count": 0,
            "mutation_count": 0,
            "launch_count": 0,
            "unrelated_package_delta_count": None,
        },
    }


def _validate_exact_fields(rows: Sequence[Mapping[str, str]], headers: Sequence[str], label: str) -> None:
    for index, row in enumerate(rows):
        if set(row) != set(headers):
            raise ContractError(f"{label}_fields_drift:{index}")
        for field, value in row.items():
            _safe(value, f"{label}:{index}:{field}")


def validate_projection(value: Mapping[str, Any], *, now: datetime | None = None) -> None:
    expected_keys = {
        "schema", "task_id", "run_id", "generated_at_utc", "expires_at_utc",
        "security_gate", "readiness", "passports", "scenarios", "cleanup", "collector",
    }
    if set(value) != expected_keys:
        raise ContractError("projection_top_level_fields_drift")
    if value["schema"] != PROJECTION_SCHEMA or value["task_id"] != TASK_ID or value["run_id"] != RUN_ID:
        raise ContractError("projection_identity_drift")
    generated = _utc(value["generated_at_utc"])
    expires = _utc(value["expires_at_utc"])
    if expires <= generated:
        raise ContractError("projection_ttl_invalid")
    if now is not None and expires <= now.astimezone(timezone.utc):
        raise ContractError("projection_expired")
    readiness = value["readiness"]
    passports = value["passports"]
    scenarios = value["scenarios"]
    cleanup = value["cleanup"]
    if not all(isinstance(rows, list) for rows in (readiness, passports, scenarios, cleanup)):
        raise ContractError("projection_ledger_not_list")
    _validate_exact_fields(readiness, READINESS_HEADERS, "readiness")
    _validate_exact_fields(passports, PASSPORT_HEADERS, "passport")
    _validate_exact_fields(scenarios, SCENARIO_HEADERS, "scenario")
    _validate_exact_fields(cleanup, CLEANUP_HEADERS, "cleanup")
    # TASK-058A is a completed, one-shot public projection.  It is not a
    # reusable runtime-ingest schema: accepting alternative row wording,
    # counters, evidence bindings or cleanup outcomes would allow a false
    # owner-override PASS.  Require the exact reviewed ledger material.
    if readiness != baseline_readiness_rows():
        raise ContractError("readiness_exact_reviewed_projection_drift")
    if passports != baseline_passport_rows():
        raise ContractError("passport_exact_reviewed_projection_drift")
    if scenarios != baseline_scenario_rows():
        raise ContractError("scenario_exact_reviewed_projection_drift")
    if cleanup != baseline_cleanup_rows():
        raise ContractError("cleanup_exact_reviewed_projection_drift")
    if len(readiness) != 7 or [r["authority_id"] for r in readiness] != list(AUTHORITY_IDS):
        raise ContractError("readiness_requires_exact_ordered_seven_rows")
    if [r["subject_alias"] for r in readiness] != list(AUTHORITY_ALIASES):
        raise ContractError("readiness_alias_drift")
    pass_count = 0
    for row in readiness:
        if row["terminal_status"] == "observed_pass":
            if row["evidence_status"] != "confirmed" or row["evidence_ids"] == "none" or row["release_effect"] != "candidate_evidence":
                raise ContractError(f"readiness_false_pass:{row['authority_id']}")
            pass_count += 1
        elif row["terminal_status"] not in TERMINAL_BLOCKED:
            raise ContractError(f"readiness_terminal_invalid:{row['authority_id']}")
        elif row["release_effect"] != "blocks_release":
            raise ContractError(f"readiness_blocker_not_release_blocking:{row['authority_id']}")
    if len(passports) != 3 or [r["passport_type"] for r in passports] != list(PASSPORT_TYPES):
        raise ContractError("three_independent_passports_required")
    for row in passports:
        if row["task_id"] != TASK_ID or row["run_id"] != RUN_ID:
            raise ContractError("passport_binding_drift")
        if _utc(row["expires_at"]) <= _utc(row["issued_at"]):
            raise ContractError("passport_ttl_invalid")
        passed = row["terminal_status"] == "observed_pass"
        if passed and not (
            row["observation_status"] == "observed_confirmed"
            and row["evidence_status"] == "confirmed"
            and row["reviewer_gate"] == "GO_RUNTIME_OWNER_OVERRIDE"
            and row["release_effect"] == "candidate_evidence"
        ):
            raise ContractError(f"passport_false_pass:{row['passport_id']}")
    collector = value["collector"]
    if set(collector) != {
        "execution_status", "native_stdout_stderr_direct_capture", "retry_count",
        "mutation_count", "launch_count", "unrelated_package_delta_count",
    }:
        raise ContractError("collector_projection_fields_drift")
    if collector["native_stdout_stderr_direct_capture"] is not True:
        raise ContractError("collector_capture_contract_failed")
    if collector["retry_count"] != 0 or collector["mutation_count"] != 0 or collector["launch_count"] != 0:
        raise ContractError("collector_launch_free_budget_drift")
    if collector["unrelated_package_delta_count"] not in (None, 0):
        raise ContractError("unrelated_package_delta_nonzero")
    if collector != baseline_projection()["collector"]:
        raise ContractError("collector_exact_reviewed_projection_drift")
    gate = value["security_gate"]
    if gate not in {"BLOCK_RUNTIME", "NO_GO", "pending_security_review", "GO_RUNTIME_OWNER_OVERRIDE"}:
        raise ContractError("security_gate_invalid")
    if gate != "GO_RUNTIME_OWNER_OVERRIDE":
        raise ContractError("security_gate_exact_reviewed_projection_drift")
    if gate == "GO_RUNTIME_OWNER_OVERRIDE":
        waived = readiness[2]
        if pass_count != 6 or any(row["terminal_status"] != "observed_pass" for index, row in enumerate(readiness) if index != 2):
            raise ContractError("owner_override_requires_exact_6_of_7_shape")
        if not (
            waived["evidence_status"] == "unknown"
            and waived["evidence_ids"] == "task058a-owner-override-authority"
            and waived["reviewer_gate"] == "GO_RUNTIME_OWNER_OVERRIDE"
            and waived["terminal_status"] == "blocked_by_external_state"
            and waived["reason_code"] == "selector_unrelated_delta_waived_owner_override"
            and waived["release_effect"] == "blocks_release"
        ):
            raise ContractError("owner_override_row03_semantic_drift")
        if any(row["reviewer_gate"] != "GO_RUNTIME_OWNER_OVERRIDE" for row in readiness):
            raise ContractError("owner_override_reviewer_gate_drift")
        if any(row["terminal_status"] != "observed_pass" for row in passports):
            raise ContractError("owner_override_requires_three_observed_passports")
    if len(scenarios) < 3 or [r["source_crosswalk_id"] for r in scenarios[:3]] != [x[1] for x in REQUIRED_SCENARIOS]:
        raise ContractError("required_scenarios_missing_merged_or_reordered")
    allowed_scenario_status = {"covered", *TERMINAL_BLOCKED}
    for row in scenarios:
        if row["status"] not in allowed_scenario_status:
            raise ContractError(f"scenario_terminal_invalid:{row['row_id']}")
        if row["status"] == "covered" and (
            row["evidence_status"] != "confirmed"
            or "none" in (row["screenshot_id"], row["ui_tree_id"], row["log_marker_id"])
        ):
            raise ContractError(f"scenario_missing_modality:{row['row_id']}")
    if len(cleanup) != 1:
        raise ContractError("cleanup_requires_one_row")
    cleanup_row = cleanup[0]
    if cleanup_row["first_launch_restored"] != "not_claimed":
        raise ContractError("first_launch_rollback_must_not_be_claimed")
    if int(cleanup_row["launch_count"]) > 1 or int(cleanup_row["safe_pre_auth_action_count"]) > 20:
        raise ContractError("runtime_budget_exceeded")
    if cleanup_row["forbidden_action_count"] != "0":
        raise ContractError("forbidden_action_observed")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_bundle(projection: Mapping[str, Any]) -> dict[Path, bytes]:
    validate_projection(projection)
    readiness = _csv_bytes(READINESS_HEADERS, projection["readiness"])
    passports = _csv_bytes(PASSPORT_HEADERS, projection["passports"])
    scenarios = _csv_bytes(SCENARIO_HEADERS, projection["scenarios"])
    cleanup = _csv_bytes(CLEANUP_HEADERS, projection["cleanup"])
    pass_count = sum(row["terminal_status"] == "observed_pass" for row in projection["readiness"])
    covered = sum(row["status"] == "covered" for row in projection["scenarios"])
    blocked = len(projection["scenarios"]) - covered
    gate = projection["security_gate"]
    runtime_started = int(projection["cleanup"][0]["launch_count"]) > 0
    inherited_covered = all(row["status"] == "covered" for row in projection["scenarios"][:3])
    summary = {
        "artifacts": [
            {"kind": kind, "reference": path.relative_to(REPO_ROOT).as_posix(), "sha256": _sha(data), "evidence_status": "confirmed"}
            for kind, path, data in (
                ("readiness_ledger", READINESS_OUTPUT, readiness),
                ("passport_ledger", PASSPORT_OUTPUT, passports),
                ("scenario_ledger", SCENARIO_OUTPUT, scenarios),
                ("cleanup_ledger", CLEANUP_OUTPUT, cleanup),
            )
        ],
        "blocked_reasons": ["selector_unrelated_delta_waived_owner_override_blocks_release"],
        "build_ref": {"alias": "task058-selected-phone-full-001"},
        "coverage_status": "covered" if runtime_started and inherited_covered else "blocked",
        "evidence_status": "confirmed",
        "execution_status": "partial_blocked" if runtime_started else "blocked",
        "generated_at_utc": projection["generated_at_utc"],
        "payload": {
            "readiness_row_count": 7,
            "readiness_observed_pass_count": pass_count,
            "readiness_blocked_count": 7 - pass_count,
            "security_gate": gate,
            "go_runtime": False,
            "go_runtime_owner_override": gate == "GO_RUNTIME_OWNER_OVERRIDE" and pass_count == 6,
            "collector_execution_status": projection["collector"]["execution_status"],
            "collector_retry_count": 0,
            "collector_mutation_count": 0,
            "collector_launch_count": 0,
            "unrelated_package_delta_count": projection["collector"]["unrelated_package_delta_count"],
            "passport_count": 3,
            "launch_count": int(projection["cleanup"][0]["launch_count"]),
            "safe_pre_auth_action_count": int(projection["cleanup"][0]["safe_pre_auth_action_count"]),
            "forbidden_action_count": 0,
            "required_scenario_count": 3,
            "scenario_count": len(projection["scenarios"]),
            "covered_scenario_count": covered,
            "blocked_scenario_count": blocked,
            "runtime_checkpoint_count": 2,
            "inherited_scenario_covered_count": sum(row["status"] == "covered" for row in projection["scenarios"][:3]),
            "authentication_boundary_count": sum(row["status"] == "blocked_by_boundary" for row in projection["scenarios"]),
            "visual_xml_mismatch_anomaly_count": sum(row["state_category"] == "visual_overlay_anomaly" for row in projection["scenarios"]),
            "first_launch_restored": False,
        },
        "production_safety_classification": "PROD_CONDITIONAL_LAUNCH_FREE_THEN_BOUNDED_PRE_AUTH",
        "provenance": {
            "source": "sanitized_task058a_fixed_local_projection",
            "local_only_input_read": projection["collector"]["execution_status"] != "not_run",
            "runner_device_action": False,
            "runner_package_action": False,
            "reporter_security_decision_authority": False,
        },
        "release_effect": "blocks_release",
        "review": {
            "qa_reviewer_a": "pending_independent_review",
            "qa_reviewer_b": "pending_independent_review",
            "security_prod_safety_reviewer": gate.lower(),
            "docs_scribe": "pending_independent_review",
        },
        "risks": [
            {"id": "TASK058A-RISK-IRREVERSIBLE-FIRST-LAUNCH", "evidence_status": "confirmed", "summary": "The installed-never-launched fixture is consumable and cannot be restored without a prohibited reinstall."},
            {"id": "TASK058A-RISK-FALSE-GO", "evidence_status": "confirmed", "summary": "Owner authority and collector success do not self-issue Security GO_RUNTIME."},
            {"id": "TASK058A-RISK-OWNER-OVERRIDE-ROW03", "evidence_status": "confirmed", "summary": "Selector and unrelated-package delta remain unknown under the literal owner override and continue to block release."},
            {"id": "TASK058A-RISK-VISUAL-XML-MISMATCH", "evidence_status": "confirmed", "summary": "A partial green left-edge overlay was visible but absent from the UI tree and remains a first-class anomaly."},
        ],
        "run_id": projection["run_id"],
        "schema_validation_status": "pass",
        "schema_version": SCHEMA_VERSION,
        "target_alias": "phone-current-001",
        "task_id": TASK_ID,
        "unknowns": [
            {"id": row["authority_id"], "evidence_status": row["evidence_status"], "reason_code": row["reason_code"]}
            for row in projection["readiness"] if row["terminal_status"] != "observed_pass"
        ],
        "verification": [
            {"check": "exact_seven_readiness_rows", "status": "blocked", "evidence_status": "confirmed", "result_count": pass_count},
            {"check": "three_task_run_bound_passports", "status": "pass", "evidence_status": "confirmed", "result_count": 3},
            {"check": "task058a_inherited_runtime_coverage", "status": "pass" if runtime_started and inherited_covered else "blocked", "evidence_status": "confirmed" if runtime_started else "unknown", "result_count": sum(row["status"] == "covered" for row in projection["scenarios"][:3])},
        ],
    }
    bundle = {
        READINESS_OUTPUT: readiness,
        PASSPORT_OUTPUT: passports,
        SCENARIO_OUTPUT: scenarios,
        CLEANUP_OUTPUT: cleanup,
    }
    bundle[REPORT_OUTPUT] = _json_bytes(summary)
    return bundle


_BASELINE = baseline_projection()


def expected_bundle() -> dict[Path, bytes]:
    return build_bundle(_BASELINE)


def validate_bundle(bundle: Mapping[Path, bytes], *, validate_disk_schema: bool = False) -> None:
    expected_paths = {READINESS_OUTPUT, PASSPORT_OUTPUT, SCENARIO_OUTPUT, CLEANUP_OUTPUT, REPORT_OUTPUT}
    if set(bundle) != expected_paths:
        raise ContractError("bundle_path_set_drift")
    readiness = _parse_csv(bundle[READINESS_OUTPUT], READINESS_HEADERS, "readiness")
    passports = _parse_csv(bundle[PASSPORT_OUTPUT], PASSPORT_HEADERS, "passport")
    scenarios = _parse_csv(bundle[SCENARIO_OUTPUT], SCENARIO_HEADERS, "scenario")
    cleanup = _parse_csv(bundle[CLEANUP_OUTPUT], CLEANUP_HEADERS, "cleanup")
    try:
        summary = json.loads(bundle[REPORT_OUTPUT].decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("summary_json_invalid") from exc
    projection = baseline_projection()
    projection.update(
        generated_at_utc=summary["generated_at_utc"],
        expires_at_utc=passports[0]["expires_at"],
        security_gate=summary["payload"]["security_gate"],
        readiness=readiness,
        passports=passports,
        scenarios=scenarios,
        cleanup=cleanup,
        collector={
            "execution_status": summary["payload"]["collector_execution_status"],
            "native_stdout_stderr_direct_capture": True,
            "retry_count": summary["payload"]["collector_retry_count"],
            "mutation_count": summary["payload"]["collector_mutation_count"],
            "launch_count": summary["payload"]["collector_launch_count"],
            "unrelated_package_delta_count": summary["payload"]["unrelated_package_delta_count"],
        },
    )
    # Disk baseline validation is deterministic.  A local projection is first
    # validated and then written atomically as a complete bundle.
    expected = build_bundle(projection)
    if summary != json.loads(expected[REPORT_OUTPUT]):
        raise ContractError("summary_semantic_or_hash_drift")
    if validate_disk_schema:
        errors = _validate_v2_envelope(summary, REPO_ROOT)
        if errors:
            raise ContractError("summary_schema_invalid:" + ",".join(errors))


def _disk_bundle() -> dict[Path, bytes]:
    result = {}
    for path in (READINESS_OUTPUT, PASSPORT_OUTPUT, SCENARIO_OUTPUT, CLEANUP_OUTPUT, REPORT_OUTPUT):
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"tracked_artifact_missing_or_link:{path.name}")
        result[path] = path.read_bytes()
    return result


def _read_local_projection() -> dict[str, Any]:
    if not LOCAL_PROJECTION.is_file() or LOCAL_PROJECTION.is_symlink():
        raise ContractError("fixed_local_projection_missing_or_link")
    try:
        value = json.loads(LOCAL_PROJECTION.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("fixed_local_projection_invalid") from exc
    validate_projection(value, now=datetime.now(timezone.utc))
    return value


def validate_static_contract() -> None:
    if not TASK_SPEC.is_file() or TASK_SPEC.is_symlink():
        raise ContractError("task_spec_missing_or_link")
    text = TASK_SPEC.read_text(encoding="utf-8")
    for marker in (
        "Security may issue `GO_RUNTIME` only after all seven readiness rows",
        "launch: `1` maximum", "safe pre-auth actions: `20` maximum",
        "rolled back without a reinstall", "phone-coverage-001", "phone-coverage-017", "`A002`",
    ):
        if marker not in text:
            raise ContractError("task_spec_contract_drift")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--write-baseline", action="store_true")
    modes.add_argument("--validate-report", action="store_true")
    modes.add_argument("--project-approved-local", action="store_true")
    args = parser.parse_args(argv)
    try:
        validate_static_contract()
        if args.write_baseline:
            bundle = expected_bundle()
        elif args.validate_report:
            validate_bundle(_disk_bundle(), validate_disk_schema=True)
            bundle = None
        elif args.project_approved_local:
            bundle = build_bundle(_read_local_projection())
        else:
            validate_bundle(expected_bundle())
            bundle = None
        if bundle is not None:
            for path, data in bundle.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    except (ContractError, OSError, UnicodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print("PASS: TASK-058A public-safe fixed-path contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

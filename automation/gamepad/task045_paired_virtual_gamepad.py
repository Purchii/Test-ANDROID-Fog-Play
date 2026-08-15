"""Fail-closed TASK-045 paired virtual-gamepad evidence adapter.

The module never controls a device.  A local-only runtime runner may emit the
typed adapter described by the pinned schema.  This module validates that
input, derives public-safe terminal scenario classifications and publishes the
entire report bundle atomically.  ``--validate-only`` performs no file, process,
network, APK, ADB or device access.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


TASK_ID = "TASK-045"
ADAPTER_SCHEMA_VERSION = "task045-paired-runtime-adapter-v1"
SCENARIO_CONTRACT_VERSION = "task045-scenarios-v1"
REPORT_SCHEMA_VERSION = "evidence-report-envelope-v2"
SAFETY_CLASS = "PROD_CONDITIONAL_PHONE_INDEPENDENT"
PHONE_ALIAS = "phone-realme-001"
PHONE_PROFILE_ALIAS = "phone-realme-a16-001"
PHONE_APK_FAMILY = "phone-full"
INSTALLED_BUILD_ALIAS = "task045-phone-full-installed-newer-001"
CANONICAL_BUILD_ALIAS = "task045-phone-full-canonical-candidate"
PHONE_TARGETS = {
    "phone-xiaomi-007": "phone-xiaomi-a13-007",
    "phone-samsung-002": "phone-samsung-a13-002",
    "phone-realme-001": "phone-realme-a16-001",
}
TV_ALIAS = "tv-tpv-013"
TV_PROFILE_ALIAS = "tv-tpv-a12-013"
TV_APK_FAMILY = "television-full"
REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = REPO_ROOT / "docs/qa/epics/scenarios/task045_scenarios.csv"
ADAPTER_SCHEMA = REPO_ROOT / "docs/qa/schemas/task045-paired-virtual-gamepad-adapter-v1.schema.json"
REPORT_ENVELOPE_SCHEMA = REPO_ROOT / "docs/qa/schemas/evidence-report-envelope-v2.schema.json"
REPORT_OUTPUT = REPO_ROOT / "docs/qa/reports/task045_paired_virtual_gamepad.summary.json"
SCENARIO_LEDGER_OUTPUT = REPO_ROOT / "docs/qa/reports/task045_paired_virtual_gamepad.scenario-ledger.csv"
PHONE_COVERAGE_OUTPUT = REPO_ROOT / "docs/qa/reports/task045_paired_virtual_gamepad.phone-coverage-ledger.csv"
TIMELINE_OUTPUT = REPO_ROOT / "docs/qa/reports/task045_paired_virtual_gamepad.timeline-ledger.csv"
ANOMALY_OUTPUT = REPO_ROOT / "docs/qa/reports/task045_paired_virtual_gamepad.anomaly-ledger.csv"
CLEANUP_OUTPUT = REPO_ROOT / "docs/qa/reports/task045_paired_virtual_gamepad.cleanup-ledger.csv"
LOCAL_ADAPTER_ROOT = REPO_ROOT / ".qa_local" / "evidence" / "task-045"
LOCAL_COVERAGE_SOURCE = LOCAL_ADAPTER_ROOT / "runtime-coverage-source.local.json"

CATALOG_HEADERS = (
    "scenario_id", "priority", "surface_ids", "lane", "category", "title",
    "preconditions", "steps", "expected_oracle", "negative_or_boundary",
    "automation_target", "evidence_required", "safety_class", "blocking_rule",
)
SCENARIO_LEDGER_HEADERS = (
    "scenario_id", "priority", "surface_ids", "lane", "category",
    "scenario_status", "evidence_type", "evidence_status", "attempt_count",
    "reason_code", "automation_target", "phone_independent_allowed", "paired_evidence_present",
    "first_failure_retained", "cleanup_status", "boundary_status",
)
PHONE_COVERAGE_HEADERS = (
    "coverage_id", "branch_alias", "lane_scope", "approved_scope",
    "declared_reachable", "discovered", "requires_connected_pair", "status",
    "screen_alias", "state_category", "focus_action_category",
    "evidence_status", "evidence_count", "reason_code",
)
TIMELINE_HEADERS = (
    "event_id", "scenario_id", "observed_at_utc", "side", "state_alias",
    "attempt_id", "evidence_count",
)
ANOMALY_HEADERS = (
    "anomaly_id", "scenario_id", "attempt_id", "trigger_category",
    "expected_result_category", "observed_result_category",
    "public_safe_screen_alias", "classification", "evidence_status",
    "cause_evidence_status", "cause_category", "test_design_implication",
    "first_failure_retained", "reason_code",
)
CLEANUP_HEADERS = (
    "cleanup_id", "record_scope", "scenario_id", "attempt_id", "action_category",
    "result", "kill_switch_ready", "rollback_verified", "evidence_status",
    "target_app_force_stopped", "home_restored", "external_browser_opened",
    "payment_or_session_started", "account_mutated", "network_changed",
    "paired_state_observed", "existing_session_preserved",
)

SCENARIO_STATUSES = {
    "observed_pass", "observed_fail", "confirmed_defect", "tooling_defect",
    "executable_not_run", "blocked_by_device", "blocked_by_fixture",
    "blocked_by_oracle", "blocked_by_product_boundary",
    "blocked_by_external_state", "not_applicable", "mapped_only",
}
TERMINAL_STATUSES = SCENARIO_STATUSES - {"executable_not_run", "mapped_only"}
BLOCKED_STATUSES = {value for value in SCENARIO_STATUSES if value.startswith("blocked_")}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
COVERAGE_STATUSES = {
    "covered", "blocked_by_boundary", "blocked_by_tooling",
    "blocked_by_external_state", "not_run_out_of_scope",
}
INDEPENDENT_PHONE_SCENARIOS = {"QA-045-006", "QA-045-009"}
CLOSURE_SCENARIO = "QA-045-022"
PAIRED_REQUIRED_SCENARIOS = {
    f"QA-045-{index:03d}" for index in range(1, 22)
} - INDEPENDENT_PHONE_SCENARIOS
EXPECTED_IDS = tuple(f"QA-045-{index:03d}" for index in range(1, 23))
BASELINE_PHONE_BRANCHES = (
    ("phone-launch-discovery", "disconnected_independent"),
    ("phone-no-tv-negative", "disconnected_independent"),
    ("phone-gamepad-before-connection", "disconnected_independent"),
    ("phone-disconnected-background-foreground", "disconnected_independent"),
    ("phone-disconnected-force-stop-relaunch", "disconnected_independent"),
    ("phone-connected-gamepad", "paired_required"),
    ("phone-paired-background-foreground", "paired_required"),
    ("phone-paired-force-stop-relaunch", "paired_required"),
    ("phone-paired-network-reconnect", "paired_required"),
)
REQUIRED_RUNTIME_COVERAGE_BRANCHES = frozenset({
    "phone-cold-launch-installed-newer", "phone-catalog-initial",
    "phone-catalog-scroll-later-segment", "phone-catalog-filter-expanded",
    "phone-catalog-filter-collapsed", "phone-search-empty-focus",
    "phone-history-initial", "phone-history-scroll-later-segment",
    "phone-profile-settings-help-legal", "phone-game-card-detail",
    "phone-promo-detail", "phone-gamepad-before-connection",
    "phone-no-tv-negative", "phone-background-foreground-disconnected",
    "phone-force-stop-relaunch-disconnected", "phone-final-cleanup",
    "phone-auth-guard", "phone-catalog-recurrence",
    "phone-partial-render-overlay", "phone-external-keyboard-consent-overlay",
    "phone-connected-gamepad", "phone-network-reconnect", "phone-lock-unlock",
    "phone-paired-disconnect", "phone-payment-session-boundary",
    "phone-qr-browser-boundary",
})
SESSION_DEPENDENT_BRANCHES = frozenset({
    "phone-cold-launch-installed-newer", "phone-catalog-initial",
    "phone-catalog-scroll-later-segment", "phone-catalog-filter-expanded",
    "phone-catalog-filter-collapsed", "phone-history-initial",
    "phone-history-scroll-later-segment", "phone-background-foreground-disconnected",
    "phone-catalog-recurrence", "phone-partial-render-overlay",
})
MAX_RUNTIME_EVIDENCE_AGE = timedelta(hours=24)
MAX_CLOCK_SKEW = timedelta(minutes=5)
PASS_ORACLES = {
    "QA-045-001": ("validate_paired_lane", "paired_lane_ready"),
    "QA-045-002": ("open_tv_connect_screen", "tv_waiting_for_phone"),
    "QA-045-003": ("phone_cold_launch_discovery", "expected_tv_discovered"),
    "QA-045-004": ("phone_warm_launch", "connection_behavior_classified"),
    "QA-045-005": ("attempt_wrong_account_or_no_session", "unauthorized_pair_denied"),
    "QA-045-006": ("launch_phone_without_tv", "no_phantom_tv_state"),
    "QA-045-007": ("connect_once", "both_sides_connected"),
    "QA-045-008": ("repeat_connect", "no_duplicate_pair"),
    "QA-045-009": ("open_gamepad_before_connection", "gamepad_disabled_or_waiting"),
    "QA-045-010": ("open_gamepad_after_connection", "gamepad_enabled_state"),
    "QA-045-011": ("send_safe_virtual_input", "tv_safe_response"),
    "QA-045-012": ("phone_background_foreground", "paired_state_after_foreground"),
    "QA-045-013": ("phone_force_stop_relaunch", "paired_reconnect_classified"),
    "QA-045-014": ("tv_force_stop_relaunch", "both_sides_tv_recovery"),
    "QA-045-015": ("phone_lock_unlock", "paired_state_after_unlock"),
    "QA-045-016": ("phone_network_loss_restore", "phone_reconnect_classified"),
    "QA-045-017": ("tv_network_loss_restore", "both_sides_reconnect_classified"),
    "QA-045-018": ("asymmetric_reconnect", "no_duplicate_or_stale_pair"),
    "QA-045-019": ("explicit_disconnect", "both_sides_disconnected"),
    "QA-045-020": ("capture_boundary_and_cancel", "boundary_held_and_pair_cleaned"),
    "QA-045-021": ("validate_public_timeline_redaction", "public_timeline_safe"),
}
INVENTORY_ANOMALY_DETAILS: dict[str, dict[str, str]] = {
    "TASK045-PROCESS-ANOMALY-001": {"classification": "tooling_defect", "trigger_category": "alias_map_schema_introspection", "expected_result_category": "sanitized_counts_and_public_aliases", "observed_result_category": "raw_mapping_keys_in_ephemeral_output", "public_safe_screen_alias": "local_tool_output", "cause_evidence_status": "likely", "cause_category": "local_schema_assumption", "test_design_implication": "validate_local_shape_before_sanitized_projection", "reason_code": "ephemeral_raw_key_output_not_published"},
    "TASK045-PROCESS-ANOMALY-002": {"classification": "tooling_defect", "trigger_category": "focused_contract_test_run", "expected_result_category": "all_task045_tests_pass", "observed_result_category": "temporary_test_regression", "public_safe_screen_alias": "repository_test_runner", "cause_evidence_status": "confirmed", "cause_category": "validator_edit_and_fixture_mismatch", "test_design_implication": "retain_first_failure_and_require_clean_rerun", "reason_code": "builder_test_regression_remediated"},
    "TASK045-RUNTIME-ANOMALY-001": {"classification": "blocked_by_external_state", "trigger_category": "ordinary_phone_full_install_update", "expected_result_category": "canonical_install_success", "observed_result_category": "version_downgrade_rejected", "public_safe_screen_alias": "package_installer_external", "cause_evidence_status": "likely", "cause_category": "environment_build_state_mismatch", "test_design_implication": "separate_installed_newer_lane_and_require_build_gate", "reason_code": "canonical_install_blocked_version_downgrade"},
    "TASK045-PROCESS-ANOMALY-003": {"classification": "tooling_defect", "trigger_category": "installed_build_metadata_comparison", "expected_result_category": "sanitized_metadata_classification", "observed_result_category": "shell_json_conversion_option_unavailable", "public_safe_screen_alias": "local_metadata_parser", "cause_evidence_status": "likely", "cause_category": "shell_version_compatibility_gap", "test_design_implication": "use_property_lookup_and_retain_first_tooling_failure", "reason_code": "local_parser_compatibility_gap"},
    "TASK045-PROCESS-ANOMALY-004": {"classification": "tooling_defect", "trigger_category": "first_complete_phone_checkpoint_capture", "expected_result_category": "screenshot_tree_and_bounded_log", "observed_result_category": "pull_stderr_promoted_to_terminating_error", "public_safe_screen_alias": "phone_catalog_capture_incomplete", "cause_evidence_status": "likely", "cause_category": "local_shell_stderr_handling", "test_design_implication": "reuse_stored_screenshot_and_capture_only_missing_modalities", "reason_code": "adb_pull_stderr_helper_failure"},
    "TASK045-RUNTIME-ANOMALY-002": {"classification": "observed_fail", "trigger_category": "approved_catalog_scroll", "expected_result_category": "stable_later_catalog_segment", "observed_result_category": "partial_render_with_confirmed_visual_tree_mismatch", "public_safe_screen_alias": "phone-catalog-partial-render-after-scroll", "cause_evidence_status": "hypothesis", "cause_category": "render_timing_or_content_state", "test_design_implication": "retain_visual_failure_and_allow_one_no_action_recovery", "reason_code": "confirmed_screenshot_xml_mismatch_after_scroll"},
    "TASK045-PROCESS-ANOMALY-005": {"classification": "tooling_defect", "trigger_category": "catalog_and_history_scroll_probe", "expected_result_category": "visible_list_movement", "observed_result_category": "fixed_coordinates_outside_display", "public_safe_screen_alias": "phone-list-initial-segment", "cause_evidence_status": "confirmed", "cause_category": "local_scroll_coordinate_bug", "test_design_implication": "derive_bounded_coordinates_and_allow_one_corrected_gesture", "reason_code": "out_of_display_scroll_coordinates"},
    "TASK045-RUNTIME-ANOMALY-003": {"classification": "blocked_by_product_boundary", "trigger_category": "focus_empty_catalog_search", "expected_result_category": "ordinary_keyboard_only_state", "observed_result_category": "external_keyboard_privacy_consent_overlay", "public_safe_screen_alias": "external-keyboard-privacy-consent-overlay", "cause_evidence_status": "confirmed", "cause_category": "external_system_keyboard_boundary", "test_design_implication": "do_not_consent_or_enter_text_and_recover_with_back", "reason_code": "external_keyboard_privacy_boundary"},
    "TASK045-RUNTIME-ANOMALY-004": {"classification": "observed_fail", "trigger_category": "disconnected_background_foreground_cycle", "expected_result_category": "fully_rendered_catalog_on_return", "observed_result_category": "partial_render_with_confirmed_visual_tree_mismatch", "public_safe_screen_alias": "phone-catalog-partial-render-after-foreground", "cause_evidence_status": "hypothesis", "cause_category": "render_timing_or_lifecycle_state", "test_design_implication": "retain_lifecycle_failure_and_do_not_credit_paired_scenario", "reason_code": "confirmed_screenshot_xml_mismatch_after_foreground"},
    "TASK045-PROCESS-ANOMALY-006": {"classification": "tooling_defect", "trigger_category": "post_force_stop_checkpoint_capture", "expected_result_category": "bounded_absent_process_log_marker", "observed_result_category": "null_pid_helper_failure", "public_safe_screen_alias": "phone-force-stopped-checkpoint-incomplete", "cause_evidence_status": "confirmed", "cause_category": "local_null_pid_handling", "test_design_implication": "treat_absent_pid_as_expected_and_emit_sanitized_marker", "reason_code": "null_pid_log_helper_gap"},
    "TASK045-PROCESS-ANOMALY-007": {"classification": "tooling_defect", "trigger_category": "hardened_relational_validator_focused_suite", "expected_result_category": "all_task045_contract_tests_pass", "observed_result_category": "legacy_boundary_fixture_missing_attempt_relation", "public_safe_screen_alias": "repository_test_runner", "cause_evidence_status": "confirmed", "cause_category": "validator_test_fixture_migration_gap", "test_design_implication": "require_attempt_link_on_every_boundary_fixture_and_retain_first_failure", "reason_code": "legacy_boundary_fixture_attempt_link_missing"},
    "TASK045-PROCESS-ANOMALY-008": {"classification": "tooling_defect", "trigger_category": "first_sanitized_runtime_bundle_publish", "expected_result_category": "guarded_ingest_publication", "observed_result_category": "explicit_ingest_gate_required", "public_safe_screen_alias": "repository_publish_guard", "cause_evidence_status": "confirmed", "cause_category": "required_authorization_flag_omitted", "test_design_implication": "retain_fail_closed_gate_and_rerun_once_with_explicit_ingest_authorization", "reason_code": "execute_gate_required_then_authorized"},
    "TASK045-PROCESS-ANOMALY-009": {"classification": "tooling_defect", "trigger_category": "focused_anomaly_ledger_regression", "expected_result_category": "all_task045_contract_tests_pass", "observed_result_category": "stale_literal_anomaly_count", "public_safe_screen_alias": "repository_test_runner", "cause_evidence_status": "confirmed", "cause_category": "test_fixture_count_literal", "test_design_implication": "bind_ledger_count_assertion_to_typed_runtime_source", "reason_code": "stale_anomaly_count_literal_remediated"},
    "TASK045-PROCESS-ANOMALY-010": {"classification": "tooling_defect", "trigger_category": "freshness_and_core_declaration_focused_suite", "expected_result_category": "all_task045_contract_tests_pass", "observed_result_category": "three_stale_fixture_expectations", "public_safe_screen_alias": "repository_test_runner", "cause_evidence_status": "confirmed", "cause_category": "validator_fixture_migration_gap", "test_design_implication": "align_synthetic_run_timestamps_and_earliest_fail_closed_error_expectation", "reason_code": "freshness_core_fixture_migration_remediated"},
    "TASK045-PROCESS-ANOMALY-011": {"classification": "tooling_defect", "trigger_category": "final_build_provenance_adversarial_review", "expected_result_category": "installed_newer_and_canonical_aliases_remain_distinct", "observed_result_category": "build_alias_identity_collapse_accepted", "public_safe_screen_alias": "repository_evidence_validator", "cause_evidence_status": "confirmed", "cause_category": "build_provenance_relation_guard_missing", "test_design_implication": "pin_runtime_build_aliases_and_reject_installed_canonical_identity_collapse", "reason_code": "build_alias_separation_false_pass_remediated"},
    "TASK045-RUNTIME-ANOMALY-005": {"classification": "blocked_by_fixture", "trigger_category": "final_security_evidence_eligibility_review", "expected_result_category": "synthetic_session_fixture_verified_before_product_coverage", "observed_result_category": "unknown_session_provenance_marked_as_confirmed_coverage", "public_safe_screen_alias": "repository_evidence_eligibility_gate", "cause_evidence_status": "confirmed", "cause_category": "evidence_eligibility_gate_omission", "test_design_implication": "block_session_dependent_rows_by_fixture_until_synthetic_session_is_verified", "reason_code": "unknown_session_evidence_ineligible_for_product_coverage"},
}
BOUNDARY_SCENARIO = "QA-045-020"
NETWORK_SCENARIOS = {"QA-045-016", "QA-045-017", "QA-045-018"}
STATEFUL_SCENARIOS = {
    "QA-045-007", "QA-045-008", "QA-045-011", "QA-045-012",
    "QA-045-013", "QA-045-014", "QA-045-015", "QA-045-016",
    "QA-045-017", "QA-045-018", "QA-045-019", "QA-045-020",
}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
SCENARIO_ID_RE = re.compile(r"^QA-045-[0-9]{3}$")
FORMULA_PREFIXES = ("=", "+", "-", "@")
FORBIDDEN_PUBLIC_PATTERNS = (
    re.compile(r"(?i)(?:https?|wss?)://"),
    re.compile(r"(?i)(?:^|[\\/])\.qa_local(?:[\\/]|$)"),
    re.compile(r"(?i)^[a-z]:[\\/]"),
    re.compile(r"(?i)^/(?:home|users|private|var)/"),
    re.compile(r"(?i)\b(?:serial|imei|android_id|token|cookie|password|otp|endpoint|ip|account|session)\s*[:=]"),
    re.compile(r"(?<![A-Za-z0-9])\d{10,}(?![A-Za-z0-9])"),
    re.compile(r"(?i)^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"),
)


class ContractError(Exception):
    """A public-safe fail-closed validation result."""


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def _utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractError("TIMESTAMP_INVALID")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise ContractError("TIMESTAMP_INVALID") from None
    return parsed.astimezone(timezone.utc)


def _safe_id(value: Any) -> str:
    if not isinstance(value, str) or SAFE_ID_RE.fullmatch(value) is None:
        raise ContractError("SAFE_ID_INVALID")
    if re.fullmatch(r"[A-Fa-f0-9]{24,}", value) or re.fullmatch(r"[0-9]{10,}", value):
        raise ContractError("SAFE_ID_HASH_OR_RAW_IDENTIFIER_LIKE")
    if re.fullmatch(r"(?:[A-Fa-f0-9]{2}:){5}[A-Fa-f0-9]{2}", value):
        raise ContractError("SAFE_ID_HASH_OR_RAW_IDENTIFIER_LIKE")
    return value


def _strict_keys(value: Mapping[str, Any], keys: set[str], code: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ContractError(code)


def _safe_public_value(value: Any, *, key: str = "") -> None:
    if isinstance(value, dict):
        for child_key, child in value.items():
            _safe_public_value(child, key=str(child_key))
        return
    if isinstance(value, list):
        for child in value:
            _safe_public_value(child, key=key)
        return
    if not isinstance(value, str):
        return
    if value.startswith(FORMULA_PREFIXES):
        raise ContractError("PUBLIC_VALUE_FORMULA_UNSAFE")
    if key.lower() in {"serial", "ip", "raw_path", "url", "token", "account", "session"}:
        raise ContractError("PUBLIC_VALUE_KEY_FORBIDDEN")
    if any(pattern.search(value) for pattern in FORBIDDEN_PUBLIC_PATTERNS):
        raise ContractError("PUBLIC_VALUE_REDACTION_FAILED")


def _fixed_file(path: Path, *, suffix: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
        root = REPO_ROOT.resolve(strict=True)
    except OSError:
        raise ContractError("INPUT_MISSING") from None
    if resolved != path.absolute() or not resolved.is_relative_to(root):
        raise ContractError("INPUT_PATH_NOT_CANONICAL")
    if resolved.suffix.lower() != suffix or resolved.is_symlink():
        raise ContractError("INPUT_TYPE_INVALID")
    return resolved


def _repo_reference(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_static_constants() -> list[str]:
    errors: list[str] = []
    if TASK_ID != "TASK-045" or len(EXPECTED_IDS) != 22:
        errors.append("IMMUTABLE_TASK_CONTRACT_INVALID")
    if INDEPENDENT_PHONE_SCENARIOS != {"QA-045-006", "QA-045-009"}:
        errors.append("PHONE_INDEPENDENCE_CONTRACT_INVALID")
    if CLOSURE_SCENARIO in PAIRED_REQUIRED_SCENARIOS:
        errors.append("CLOSURE_SCOPE_INVALID")
    if set(PASS_ORACLES) != set(EXPECTED_IDS[:-1]):
        errors.append("PASS_ORACLE_SET_INVALID")
    if len(BASELINE_PHONE_BRANCHES) < 1:
        errors.append("PHONE_COVERAGE_CONTRACT_INVALID")
    return errors


def load_contract() -> list[dict[str, str]]:
    fixed = _fixed_file(CATALOG, suffix=".csv")
    try:
        reader = csv.DictReader(io.StringIO(fixed.read_text(encoding="utf-8-sig")))
    except (OSError, UnicodeError):
        raise ContractError("CATALOG_UNREADABLE") from None
    if tuple(reader.fieldnames or ()) != CATALOG_HEADERS:
        raise ContractError("CATALOG_HEADERS_INVALID")
    rows = list(reader)
    if len(rows) != 22 or tuple(row["scenario_id"] for row in rows) != EXPECTED_IDS:
        raise ContractError("CATALOG_IDENTITY_INVALID")
    if Counter(row["priority"] for row in rows) != Counter({"P0": 20, "P1": 2}):
        raise ContractError("CATALOG_PRIORITY_COUNTS_INVALID")
    if any(row["automation_target"] != "automate" for row in rows):
        raise ContractError("CATALOG_AUTOMATION_TARGET_INVALID")
    if any(row["evidence_required"] != "screenshot+ui_tree+runner_log+ledger" for row in rows):
        raise ContractError("CATALOG_EVIDENCE_CONTRACT_INVALID")
    if any(row["safety_class"] != "PROD_CONDITIONAL" for row in rows):
        raise ContractError("CATALOG_SAFETY_INVALID")
    return rows


def _load_schema() -> dict[str, Any]:
    fixed = _fixed_file(ADAPTER_SCHEMA, suffix=".json")
    try:
        schema = json.loads(fixed.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ContractError("ADAPTER_SCHEMA_UNREADABLE") from None
    if (
        schema.get("$id") != _repo_reference(ADAPTER_SCHEMA)
        or schema.get("additionalProperties") is not False
        or set(schema.get("required", [])) != {
            "schema_version", "run_id", "generated_at_utc", "scenario_contract_version",
            "build_ref", "targets", "runtime_preflight", "scenarios",
            "phone_coverage", "paired_timeline", "anomalies", "inventory_anomalies",
            "inventory_evidence_ids", "inventory_cleanup", "boundaries", "cleanup",
        }
        or schema.get("properties", {}).get("scenarios", {}).get("minItems") != 22
        or schema.get("properties", {}).get("phone_coverage", {}).get("minItems") != 1
        or schema.get("$defs", {}).get("attempt", {}).get("additionalProperties") is not False
    ):
        raise ContractError("ADAPTER_SCHEMA_CONTRACT_INVALID")
    return schema


def _validate_schema_instance(
    instance: Any, schema: Mapping[str, Any], *, root: Mapping[str, Any], path: str = "$"
) -> None:
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            raise ContractError("SCHEMA_REFERENCE_INVALID")
        target: Any = root
        for part in reference[2:].split("/"):
            if not isinstance(target, dict) or part not in target:
                raise ContractError("SCHEMA_REFERENCE_INVALID")
            target = target[part]
        _validate_schema_instance(instance, target, root=root, path=path)
        return
    for branch in schema.get("allOf", []):
        _validate_schema_instance(instance, branch, root=root, path=path)
    if "const" in schema and instance != schema["const"]:
        raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
    if "enum" in schema and instance not in schema["enum"]:
        raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
    expected_type = schema.get("type")
    if expected_type is not None:
        names = expected_type if isinstance(expected_type, list) else [expected_type]
        matches = any(
            (name == "object" and isinstance(instance, dict))
            or (name == "array" and isinstance(instance, list))
            or (name == "string" and isinstance(instance, str))
            or (name == "boolean" and isinstance(instance, bool))
            or (name == "integer" and isinstance(instance, int) and not isinstance(instance, bool))
            or (name == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool))
            or (name == "null" and instance is None)
            for name in names
        )
        if not matches:
            raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
    if instance is None:
        return
    if isinstance(instance, dict):
        required = schema.get("required", [])
        if not isinstance(required, list) or any(key not in instance for key in required):
            raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ContractError("SCHEMA_CONTRACT_INVALID")
        if schema.get("additionalProperties") is False and set(instance) - set(properties):
            raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
        for key, value in instance.items():
            if key in properties:
                _validate_schema_instance(value, properties[key], root=root, path=f"{path}.{key}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0) or len(instance) > schema.get("maxItems", len(instance)):
            raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in instance}) != len(instance):
            raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, value in enumerate(instance):
                _validate_schema_instance(value, item_schema, root=root, path=f"{path}[{index}]")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
                raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if instance < schema.get("minimum", instance):
            raise ContractError(f"SCHEMA_INSTANCE_INVALID:{path}")


def _load_report_envelope_schema() -> dict[str, Any]:
    fixed = _fixed_file(REPORT_ENVELOPE_SCHEMA, suffix=".json")
    try:
        schema = json.loads(fixed.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ContractError("REPORT_SCHEMA_UNREADABLE") from None
    if schema.get("$id") != _repo_reference(REPORT_ENVELOPE_SCHEMA) or schema.get("additionalProperties") is not False:
        raise ContractError("REPORT_SCHEMA_CONTRACT_INVALID")
    return schema


def _load_adapter(path: Path) -> dict[str, Any]:
    try:
        fixed = path.resolve(strict=True)
        root = LOCAL_ADAPTER_ROOT.resolve(strict=True)
    except OSError:
        raise ContractError("ADAPTER_INPUT_MISSING") from None
    if fixed != path.absolute() or not fixed.is_relative_to(root) or fixed.suffix.lower() != ".json" or fixed.is_symlink():
        raise ContractError("ADAPTER_INPUT_PATH_INVALID")
    try:
        value = json.loads(fixed.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ContractError("ADAPTER_INPUT_INVALID") from None
    if not isinstance(value, dict):
        raise ContractError("ADAPTER_INPUT_INVALID")
    return value


def _validate_modality(value: Mapping[str, Any], *, screenshot: bool = False) -> None:
    allowed = {"evidence_id", "captured_at_utc"} | ({"visual_inspection"} if screenshot else set())
    _strict_keys(value, allowed, "MODALITY_SHAPE_INVALID")
    _safe_id(value["evidence_id"])
    _utc(value["captured_at_utc"])
    if screenshot and value["visual_inspection"] is not True:
        raise ContractError("VISUAL_INSPECTION_REQUIRED")


def _validate_attempt(
    attempt: Mapping[str, Any], scenario_id: str, *, selected_phone_alias: str,
    run_generated_at: datetime,
) -> None:
    keys = {
        "attempt_id", "started_at_utc", "completed_at_utc", "lane_scope",
        "phone_alias", "phone_apk_family", "tv_alias", "tv_apk_family",
        "pre_state_alias", "action_category", "observed_state_alias",
        "oracle_result", "evidence_type", "evidence_status", "paired_state_observed",
        "modalities", "recovery_attempt", "recovery_of_attempt_id", "cleanup_id",
        "boundary_id",
    }
    _strict_keys(attempt, keys, "ATTEMPT_SHAPE_INVALID")
    for key in ("attempt_id", "pre_state_alias", "action_category", "observed_state_alias", "recovery_of_attempt_id", "cleanup_id", "boundary_id"):
        _safe_id(attempt[key])
    started, completed = _utc(attempt["started_at_utc"]), _utc(attempt["completed_at_utc"])
    if completed < started:
        raise ContractError("ATTEMPT_TIME_ORDER_INVALID")
    if completed > run_generated_at + MAX_CLOCK_SKEW or run_generated_at - started > MAX_RUNTIME_EVIDENCE_AGE:
        raise ContractError("RUN_EVIDENCE_FRESHNESS_INVALID")
    if attempt["phone_alias"] != selected_phone_alias or attempt["phone_apk_family"] != PHONE_APK_FAMILY:
        raise ContractError("PHONE_TARGET_SUBSTITUTION")
    if attempt["tv_alias"] != TV_ALIAS or attempt["tv_apk_family"] != TV_APK_FAMILY:
        raise ContractError("TV_TARGET_SUBSTITUTION")
    if attempt["lane_scope"] not in {"phone_independent", "paired", "tv"}:
        raise ContractError("ATTEMPT_LANE_SCOPE_INVALID")
    if scenario_id in INDEPENDENT_PHONE_SCENARIOS:
        if attempt["lane_scope"] != "phone_independent" or attempt["evidence_type"] != "physical_runtime":
            raise ContractError("INDEPENDENT_PHONE_EVIDENCE_INVALID")
        if attempt["paired_state_observed"] is not False:
            raise ContractError("INDEPENDENT_PHONE_FALSE_PAIR")
    else:
        if selected_phone_alias == "phone-realme-001":
            raise ContractError("PAIRED_PHONE_LANE_NOT_APPROVED")
        if attempt["lane_scope"] != "paired" or attempt["evidence_type"] != "paired_physical_runtime":
            raise ContractError("PAIRED_EVIDENCE_REQUIRED")
        if attempt["paired_state_observed"] is not True:
            raise ContractError("PAIRED_STATE_REQUIRED")
    if attempt["oracle_result"] not in {"pass", "fail", "blocked", "not_observed"}:
        raise ContractError("ORACLE_RESULT_INVALID")
    if attempt["evidence_status"] not in EVIDENCE_STATUSES:
        raise ContractError("EVIDENCE_STATUS_INVALID")
    if not isinstance(attempt["recovery_attempt"], bool):
        raise ContractError("RECOVERY_FLAG_INVALID")
    if attempt["recovery_attempt"] != bool(attempt["recovery_of_attempt_id"] != "none"):
        raise ContractError("RECOVERY_LINK_INVALID")
    modalities = attempt["modalities"]
    _strict_keys(modalities, {"screenshot", "ui_tree", "runner_log"}, "MODALITIES_INVALID")
    _validate_modality(modalities["screenshot"], screenshot=True)
    _validate_modality(modalities["ui_tree"])
    _validate_modality(modalities["runner_log"])
    times = [_utc(value["captured_at_utc"]) for value in modalities.values()]
    if any(value < started or value > completed for value in times):
        raise ContractError("EVIDENCE_FRESHNESS_INVALID")
    if len({value["evidence_id"] for value in modalities.values()}) != 3:
        raise ContractError("EVIDENCE_ID_REUSE_INVALID")
    expected_action, _ = PASS_ORACLES[scenario_id]
    if attempt["oracle_result"] == "pass" and attempt["action_category"] != expected_action:
        raise ContractError("SCENARIO_ACTION_ORACLE_INVALID")


def _validate_header(adapter: Mapping[str, Any]) -> None:
    keys = {
        "schema_version", "run_id", "generated_at_utc", "scenario_contract_version",
        "build_ref", "targets", "runtime_preflight", "scenarios", "phone_coverage",
        "paired_timeline", "anomalies", "inventory_anomalies", "inventory_evidence_ids",
        "inventory_cleanup", "boundaries", "cleanup",
    }
    _strict_keys(adapter, keys, "ADAPTER_SHAPE_INVALID")
    if adapter["schema_version"] != ADAPTER_SCHEMA_VERSION or adapter["scenario_contract_version"] != SCENARIO_CONTRACT_VERSION:
        raise ContractError("ADAPTER_VERSION_INVALID")
    _safe_id(adapter["run_id"])
    _utc(adapter["generated_at_utc"])
    build_keys = {
        "alias", "phone_apk_family", "tv_apk_family", "installed_lane_alias",
        "canonical_bundle_alias", "canonical_install_outcome",
        "compatibility_evidence_status", "raw_hash_published",
    }
    _strict_keys(adapter["build_ref"], build_keys, "BUILD_REF_INVALID")
    _safe_id(adapter["build_ref"]["alias"])
    if adapter["build_ref"]["phone_apk_family"] != PHONE_APK_FAMILY or adapter["build_ref"]["tv_apk_family"] != TV_APK_FAMILY:
        raise ContractError("BUILD_FAMILY_INVALID")
    for key in ("installed_lane_alias", "canonical_bundle_alias"):
        _safe_id(adapter["build_ref"][key])
    if (
        adapter["build_ref"]["alias"] != adapter["build_ref"]["installed_lane_alias"]
        or adapter["build_ref"]["installed_lane_alias"] != INSTALLED_BUILD_ALIAS
        or adapter["build_ref"]["canonical_bundle_alias"] != CANONICAL_BUILD_ALIAS
        or adapter["build_ref"]["installed_lane_alias"] == adapter["build_ref"]["canonical_bundle_alias"]
        or adapter["build_ref"]["canonical_install_outcome"] != "blocked_version_downgrade"
        or adapter["build_ref"]["compatibility_evidence_status"] != "unknown"
        or adapter["build_ref"]["raw_hash_published"] is not False
    ):
        raise ContractError("BUILD_PROVENANCE_INVALID")
    targets = adapter["targets"]
    _strict_keys(targets, {"phone", "tv"}, "TARGETS_INVALID")
    selected_phone_alias = targets["phone"].get("lane_alias") if isinstance(targets.get("phone"), dict) else None
    selected_phone_profile = targets["phone"].get("profile_alias") if isinstance(targets.get("phone"), dict) else None
    if selected_phone_alias not in PHONE_TARGETS or PHONE_TARGETS[selected_phone_alias] != selected_phone_profile:
        raise ContractError("PHONE_TARGET_DEVIATION_INVALID")
    expected_targets = {
        "phone": {"lane_alias": selected_phone_alias, "profile_alias": selected_phone_profile, "apk_family": PHONE_APK_FAMILY, "form_factor": "phone", "physical": True},
        "tv": {"lane_alias": TV_ALIAS, "profile_alias": TV_PROFILE_ALIAS, "apk_family": TV_APK_FAMILY, "form_factor": "tv", "physical": True},
    }
    for side, expected in expected_targets.items():
        _strict_keys(targets[side], set(expected) | {"present"}, "TARGET_SHAPE_INVALID")
        if any(targets[side][key] != value for key, value in expected.items()) or not isinstance(targets[side]["present"], bool):
            raise ContractError("TARGET_IDENTITY_INVALID")
    preflight = adapter["runtime_preflight"]
    _strict_keys(preflight, {
        "status", "phone", "tv", "synthetic_fixture_ready", "ignored_evidence_storage_ready",
        "cleanup_rollback_ready", "reviewer_gate", "inventory_declaration_complete",
        "inventory_discovered_branch_count", "inventory_approved_reachable_branch_count",
        "session_provenance", "session_dependent_evidence_eligible",
    }, "PREFLIGHT_SHAPE_INVALID")
    if preflight["status"] not in {"READY", "PARTIAL_BLOCKED", "BLOCKED"}:
        raise ContractError("PREFLIGHT_STATUS_INVALID")
    for side in ("phone", "tv"):
        item = preflight[side]
        _strict_keys(item, {"status", "adb_authorized", "artifact_present", "family_confirmed", "owner_declared_available", "reason_code"}, "SIDE_PREFLIGHT_SHAPE_INVALID")
        _safe_id(item["reason_code"])
        if item["status"] not in {"READY", "BLOCKED"} or any(not isinstance(item[key], bool) for key in ("adb_authorized", "artifact_present", "family_confirmed", "owner_declared_available")):
            raise ContractError("SIDE_PREFLIGHT_INVALID")
        ready = all(item[key] for key in ("adb_authorized", "artifact_present", "family_confirmed", "owner_declared_available"))
        if (item["status"] == "READY") != ready:
            raise ContractError("SIDE_PREFLIGHT_INCONSISTENT")
        if targets[side]["present"] != item["owner_declared_available"]:
            raise ContractError("TARGET_PREFLIGHT_PRESENCE_MISMATCH")
    paired_ready = preflight["phone"]["status"] == preflight["tv"]["status"] == "READY" and all(
        preflight[key] is True for key in ("synthetic_fixture_ready", "ignored_evidence_storage_ready", "cleanup_rollback_ready", "reviewer_gate")
    )
    if (preflight["status"] == "READY") != paired_ready:
        raise ContractError("PAIRED_PREFLIGHT_INCONSISTENT")
    if preflight["tv"]["status"] == "BLOCKED" and preflight["status"] == "READY":
        raise ContractError("MISSING_TV_FALSE_READY")
    if not isinstance(preflight["inventory_declaration_complete"], bool):
        raise ContractError("INVENTORY_DECLARATION_FLAG_INVALID")
    if preflight["session_provenance"] not in {"approved_synthetic_fixture", "unknown_not_verified"} or not isinstance(preflight["session_dependent_evidence_eligible"], bool):
        raise ContractError("SESSION_PROVENANCE_INVALID")
    expected_session_eligible = preflight["synthetic_fixture_ready"] and preflight["session_provenance"] == "approved_synthetic_fixture"
    if preflight["session_dependent_evidence_eligible"] is not expected_session_eligible:
        raise ContractError("SESSION_EVIDENCE_ELIGIBILITY_INCONSISTENT")
    if any(not isinstance(preflight[key], int) or isinstance(preflight[key], bool) or preflight[key] < 0 for key in ("inventory_discovered_branch_count", "inventory_approved_reachable_branch_count")):
        raise ContractError("INVENTORY_DECLARATION_COUNT_INVALID")


def _validate_coverage(adapter: Mapping[str, Any]) -> None:
    coverage = adapter["phone_coverage"]
    if not isinstance(coverage, list) or not coverage:
        raise ContractError("PHONE_COVERAGE_COUNT_INVALID")
    seen_aliases: set[str] = set()
    seen_ids: set[str] = set()
    evidence_registry = set(adapter["inventory_evidence_ids"])
    for row in coverage:
        _strict_keys(row, {
            "coverage_id", "branch_alias", "lane_scope", "approved_scope",
            "declared_reachable", "discovered", "requires_connected_pair", "status",
            "screen_alias", "state_category", "focus_action_category", "evidence_status",
            "evidence_ids", "reason_code",
        }, "PHONE_COVERAGE_SHAPE_INVALID")
        for key in ("coverage_id", "branch_alias", "screen_alias", "state_category", "focus_action_category", "reason_code"):
            _safe_id(row[key])
        if row["branch_alias"] in seen_aliases or row["coverage_id"] in seen_ids:
            raise ContractError("PHONE_COVERAGE_IDENTITY_INVALID")
        seen_aliases.add(row["branch_alias"])
        seen_ids.add(row["coverage_id"])
        if row["lane_scope"] not in {"disconnected_independent", "paired_required"}:
            raise ContractError("PHONE_COVERAGE_LANE_SCOPE_INVALID")
        if any(not isinstance(row[key], bool) for key in ("approved_scope", "declared_reachable", "discovered", "requires_connected_pair")):
            raise ContractError("PHONE_COVERAGE_FLAGS_INVALID")
        if row["requires_connected_pair"] != (row["lane_scope"] == "paired_required"):
            raise ContractError("PHONE_COVERAGE_PAIR_SCOPE_INVALID")
        if row["status"] not in COVERAGE_STATUSES or row["evidence_status"] not in EVIDENCE_STATUSES:
            raise ContractError("PHONE_COVERAGE_STATUS_INVALID")
        if not isinstance(row["evidence_ids"], list) or any(not isinstance(value, str) or value not in evidence_registry for value in row["evidence_ids"]):
            raise ContractError("PHONE_COVERAGE_EVIDENCE_INVALID")
        if row["status"] == "covered" and (not row["evidence_ids"] or row["evidence_status"] != "confirmed"):
            raise ContractError("PHONE_COVERAGE_FALSE_PASS")
        if row["discovered"] != bool(row["evidence_ids"]):
            raise ContractError("PHONE_COVERAGE_DISCOVERY_EVIDENCE_MISMATCH")
        if row["approved_scope"] and row["declared_reachable"] and row["status"] == "not_run_out_of_scope":
            raise ContractError("REACHABLE_APPROVED_BRANCH_NOT_TERMINAL")
        if row["status"] != "covered" and row["reason_code"] in {"none", "not_applicable"}:
            raise ContractError("PHONE_COVERAGE_BLOCKER_REASON_REQUIRED")
        if row["requires_connected_pair"] and adapter["runtime_preflight"]["tv"]["status"] != "READY" and row["status"] == "covered":
            raise ContractError("DISCONNECTED_PHONE_CANNOT_COVER_CONNECTED_BRANCH")
        if row["branch_alias"] in SESSION_DEPENDENT_BRANCHES and not adapter["runtime_preflight"]["session_dependent_evidence_eligible"] and row["status"] == "covered":
            raise ContractError("UNVERIFIED_SESSION_CANNOT_YIELD_COVERAGE")
    preflight = adapter["runtime_preflight"]
    if preflight["inventory_discovered_branch_count"] != sum(row["discovered"] for row in coverage):
        raise ContractError("INVENTORY_DISCOVERED_COUNT_MISMATCH")
    if preflight["inventory_approved_reachable_branch_count"] != sum(row["approved_scope"] and row["declared_reachable"] for row in coverage):
        raise ContractError("INVENTORY_REACHABLE_COUNT_MISMATCH")
    core_declaration_complete = REQUIRED_RUNTIME_COVERAGE_BRANCHES.issubset(seen_aliases)
    if preflight["inventory_declaration_complete"] is not core_declaration_complete:
        raise ContractError("INVENTORY_CORE_DECLARATION_MISMATCH")
    referenced = {evidence_id for row in coverage for evidence_id in row["evidence_ids"]}
    if referenced != evidence_registry:
        raise ContractError("INVENTORY_EVIDENCE_REGISTRY_MISMATCH")


def _validate_boundary(row: Mapping[str, Any]) -> None:
    _strict_keys(row, {"boundary_id", "scenario_id", "attempt_id", "category", "reached", "external_action_performed", "qr_traversed", "mutation_performed", "recovery_result", "evidence_status"}, "BOUNDARY_SHAPE_INVALID")
    _safe_id(row["boundary_id"])
    _safe_id(row["attempt_id"])
    if SCENARIO_ID_RE.fullmatch(row["scenario_id"]) is None or row["category"] not in {"payment", "session", "account", "network", "qr", "none"}:
        raise ContractError("BOUNDARY_IDENTITY_INVALID")
    if row["external_action_performed"] is not False or row["qr_traversed"] is not False or row["mutation_performed"] is not False:
        raise ContractError("FORBIDDEN_BOUNDARY_ACTION")
    if row["recovery_result"] not in {"not_required", "pass", "fail"} or row["evidence_status"] not in EVIDENCE_STATUSES:
        raise ContractError("BOUNDARY_RESULT_INVALID")


def _validate_relations(adapter: Mapping[str, Any]) -> None:
    run_generated_at = _utc(adapter["generated_at_utc"])
    if not isinstance(adapter["inventory_evidence_ids"], list):
        raise ContractError("INVENTORY_EVIDENCE_REGISTRY_INVALID")
    for evidence_id in adapter["inventory_evidence_ids"]:
        _safe_id(evidence_id)
    if len(set(adapter["inventory_evidence_ids"])) != len(adapter["inventory_evidence_ids"]):
        raise ContractError("INVENTORY_EVIDENCE_ID_DUPLICATE")
    scenarios = adapter["scenarios"]
    if not isinstance(scenarios, list) or len(scenarios) != 22:
        raise ContractError("SCENARIO_COUNT_INVALID")
    if tuple(item.get("scenario_id") for item in scenarios) != EXPECTED_IDS:
        raise ContractError("SCENARIO_IDENTITY_INVALID")
    attempt_ids: set[str] = set()
    attempt_owner: dict[str, str] = {}
    modality_evidence_ids: set[str] = set()
    attempts_by_scenario: dict[str, list[Mapping[str, Any]]] = {}
    for scenario in scenarios:
        _strict_keys(scenario, {"scenario_id", "attempts", "blocker"}, "SCENARIO_SHAPE_INVALID")
        scenario_id = scenario["scenario_id"]
        if not isinstance(scenario["attempts"], list):
            raise ContractError("ATTEMPTS_INVALID")
        if len(scenario["attempts"]) > 2:
            raise ContractError("ATTEMPT_BUDGET_EXCEEDED")
        if scenario["attempts"] and scenario["attempts"][0].get("recovery_attempt") is not False:
            raise ContractError("PRIMARY_ATTEMPT_REQUIRED")
        if len(scenario["attempts"]) == 2 and (
            scenario["attempts"][1].get("recovery_attempt") is not True
            or scenario["attempts"][1].get("recovery_of_attempt_id") != scenario["attempts"][0].get("attempt_id")
        ):
            raise ContractError("ONLY_ONE_LINKED_RECOVERY_ALLOWED")
        attempts_by_scenario[scenario_id] = scenario["attempts"]
        blocker = scenario["blocker"]
        if blocker is not None:
            _strict_keys(blocker, {"status", "reason_code"}, "BLOCKER_SHAPE_INVALID")
            if blocker["status"] not in BLOCKED_STATUSES:
                raise ContractError("BLOCKER_STATUS_INVALID")
            _safe_id(blocker["reason_code"])
        for attempt in scenario["attempts"]:
            _validate_attempt(
                attempt, scenario_id,
                selected_phone_alias=adapter["targets"]["phone"]["lane_alias"],
                run_generated_at=run_generated_at,
            )
            attempt_id = attempt["attempt_id"]
            if attempt_id in attempt_ids:
                raise ContractError("ATTEMPT_ID_DUPLICATE")
            attempt_ids.add(attempt_id)
            attempt_owner[attempt_id] = scenario_id
            for modality in attempt["modalities"].values():
                evidence_id = modality["evidence_id"]
                if evidence_id in modality_evidence_ids or evidence_id in set(adapter["inventory_evidence_ids"]):
                    raise ContractError("EVIDENCE_ID_DUPLICATE")
                modality_evidence_ids.add(evidence_id)
    _validate_coverage(adapter)
    entity_ids: set[str] = set()
    for value in [row["coverage_id"] for row in adapter["phone_coverage"]] + list(attempt_ids):
        if value in entity_ids:
            raise ContractError("ENTITY_ID_DUPLICATE")
        entity_ids.add(value)
    boundaries: dict[str, Mapping[str, Any]] = {}
    for row in adapter["boundaries"]:
        _validate_boundary(row)
        if row["boundary_id"] in boundaries:
            raise ContractError("BOUNDARY_ID_DUPLICATE")
        if row["attempt_id"] not in attempt_ids:
            raise ContractError("BOUNDARY_LINK_INVALID")
        if row["scenario_id"] != attempt_owner[row["attempt_id"]]:
            raise ContractError("SCENARIO_BOUNDARY_RELATION_INVALID")
        boundaries[row["boundary_id"]] = row
        if row["boundary_id"] in entity_ids:
            raise ContractError("ENTITY_ID_DUPLICATE")
        entity_ids.add(row["boundary_id"])
    cleanup: dict[str, Mapping[str, Any]] = {}
    for row in adapter["cleanup"]:
        _strict_keys(row, {"cleanup_id", "scenario_id", "attempt_id", "action_category", "result", "kill_switch_ready", "rollback_verified", "evidence_status"}, "CLEANUP_SHAPE_INVALID")
        for key in ("cleanup_id", "attempt_id", "action_category"):
            _safe_id(row[key])
        if row["cleanup_id"] in cleanup or row["attempt_id"] not in attempt_ids:
            raise ContractError("CLEANUP_LINK_INVALID")
        if row["scenario_id"] != attempt_owner[row["attempt_id"]]:
            raise ContractError("SCENARIO_CLEANUP_RELATION_INVALID")
        if row["result"] not in {"pass", "fail", "not_required"} or row["evidence_status"] not in EVIDENCE_STATUSES:
            raise ContractError("CLEANUP_RESULT_INVALID")
        if not isinstance(row["kill_switch_ready"], bool) or not isinstance(row["rollback_verified"], bool):
            raise ContractError("CLEANUP_FLAGS_INVALID")
        cleanup[row["cleanup_id"]] = row
        if row["cleanup_id"] in entity_ids:
            raise ContractError("ENTITY_ID_DUPLICATE")
        entity_ids.add(row["cleanup_id"])
    anomaly_attempts: set[str] = set()
    for row in adapter["anomalies"]:
        _strict_keys(row, set(ANOMALY_HEADERS), "ANOMALY_SHAPE_INVALID")
        for key in ("anomaly_id", "attempt_id", "trigger_category", "expected_result_category", "observed_result_category", "public_safe_screen_alias", "cause_category", "test_design_implication", "reason_code"):
            _safe_id(row[key])
        if row["attempt_id"] not in attempt_ids or row["classification"] not in {"observed_fail", "confirmed_defect", "tooling_defect"}:
            raise ContractError("ANOMALY_LINK_INVALID")
        if row["scenario_id"] != attempt_owner[row["attempt_id"]]:
            raise ContractError("SCENARIO_ANOMALY_RELATION_INVALID")
        if row["evidence_status"] != "confirmed" or row["first_failure_retained"] is not True:
            raise ContractError("ANOMALY_FIRST_FAILURE_INVALID")
        anomaly_attempts.add(row["attempt_id"])
        if row["anomaly_id"] in entity_ids:
            raise ContractError("ENTITY_ID_DUPLICATE")
        entity_ids.add(row["anomaly_id"])
    timeline_attempts: set[str] = set()
    timeline_by_attempt: dict[str, list[Mapping[str, Any]]] = {}
    last_time: datetime | None = None
    for row in adapter["paired_timeline"]:
        _strict_keys(row, {"event_id", "scenario_id", "observed_at_utc", "side", "state_alias", "attempt_id", "evidence_ids"}, "TIMELINE_SHAPE_INVALID")
        for key in ("event_id", "state_alias", "attempt_id"):
            _safe_id(row[key])
        observed = _utc(row["observed_at_utc"])
        if last_time is not None and observed < last_time:
            raise ContractError("TIMELINE_ORDER_INVALID")
        last_time = observed
        if row["attempt_id"] not in attempt_ids or row["side"] not in {"phone", "tv", "pair"} or not row["evidence_ids"]:
            raise ContractError("TIMELINE_LINK_INVALID")
        observed_at = _utc(row["observed_at_utc"])
        if observed_at > run_generated_at + MAX_CLOCK_SKEW or run_generated_at - observed_at > MAX_RUNTIME_EVIDENCE_AGE:
            raise ContractError("RUN_TIMELINE_FRESHNESS_INVALID")
        if row["scenario_id"] != attempt_owner[row["attempt_id"]]:
            raise ContractError("SCENARIO_TIMELINE_RELATION_INVALID")
        timeline_attempts.add(row["attempt_id"])
        timeline_by_attempt.setdefault(row["attempt_id"], []).append(row)
        if row["event_id"] in entity_ids:
            raise ContractError("ENTITY_ID_DUPLICATE")
        entity_ids.add(row["event_id"])
    for scenario_id, attempts in attempts_by_scenario.items():
        attempt_map = {item["attempt_id"]: item for item in attempts}
        for attempt in attempts:
            if adapter["runtime_preflight"]["phone"]["status"] != "READY":
                raise ContractError("PHONE_RUNTIME_PREFLIGHT_REQUIRED")
            if attempt["lane_scope"] == "paired" and adapter["runtime_preflight"]["tv"]["status"] != "READY":
                raise ContractError("PAIRED_RUNTIME_PREFLIGHT_REQUIRED")
            if attempt["recovery_attempt"]:
                prior = attempt_map.get(attempt["recovery_of_attempt_id"])
                if prior is None or prior["oracle_result"] != "fail" or _utc(prior["completed_at_utc"]) > _utc(attempt["started_at_utc"]):
                    raise ContractError("RECOVERY_SOURCE_FAILURE_INVALID")
            if attempt["cleanup_id"] not in cleanup or cleanup[attempt["cleanup_id"]]["attempt_id"] != attempt["attempt_id"]:
                raise ContractError("ATTEMPT_CLEANUP_MISSING")
            if attempt["boundary_id"] not in boundaries or boundaries[attempt["boundary_id"]]["scenario_id"] != scenario_id:
                raise ContractError("ATTEMPT_BOUNDARY_MISSING")
            if attempt["attempt_id"] not in timeline_attempts:
                raise ContractError("ATTEMPT_TIMELINE_MISSING")
            events = timeline_by_attempt[attempt["attempt_id"]]
            expected_evidence = {value["evidence_id"] for value in attempt["modalities"].values()}
            if any(
                _utc(event["observed_at_utc"]) < _utc(attempt["started_at_utc"])
                or _utc(event["observed_at_utc"]) > _utc(attempt["completed_at_utc"])
                or not set(event["evidence_ids"]).issubset(expected_evidence)
                for event in events
            ):
                raise ContractError("TIMELINE_EVIDENCE_CORRELATION_INVALID")
            event_sides = {event["side"] for event in events}
            if attempt["lane_scope"] == "paired" and not {"phone", "tv"}.issubset(event_sides):
                raise ContractError("PAIRED_TIMELINE_SIDES_MISSING")
            if attempt["lane_scope"] == "phone_independent" and event_sides != {"phone"}:
                raise ContractError("INDEPENDENT_PHONE_TIMELINE_INVALID")
            if attempt["oracle_result"] == "fail" and attempt["attempt_id"] not in anomaly_attempts:
                raise ContractError("FAILED_ATTEMPT_ANOMALY_MISSING")
            cleanup_row = cleanup[attempt["cleanup_id"]]
            if scenario_id in STATEFUL_SCENARIOS and (
                cleanup_row["result"] != "pass" or cleanup_row["kill_switch_ready"] is not True or cleanup_row["rollback_verified"] is not True
            ):
                raise ContractError("STATEFUL_CLEANUP_NOT_VERIFIED")
            if scenario_id == BOUNDARY_SCENARIO:
                boundary = boundaries[attempt["boundary_id"]]
                if boundary["category"] not in {"payment", "session"} or not boundary["reached"] or boundary["recovery_result"] != "pass":
                    raise ContractError("PAYMENT_SESSION_BOUNDARY_NOT_HELD")
            if scenario_id in NETWORK_SCENARIOS and boundaries[attempt["boundary_id"]]["category"] != "network":
                raise ContractError("NETWORK_BOUNDARY_RECORD_MISSING")
        failures = [item for item in attempts if item["oracle_result"] == "fail"]
        linked_anomalies = [row for row in adapter["anomalies"] if row["scenario_id"] == scenario_id]
        if {row["attempt_id"] for row in linked_anomalies} != {item["attempt_id"] for item in failures}:
            raise ContractError("SCENARIO_ANOMALY_RELATION_INVALID")
        if any(sum(row["attempt_id"] == item["attempt_id"] for row in adapter["anomalies"]) != 1 for item in failures):
            raise ContractError("FAILED_ATTEMPT_ANOMALY_CARDINALITY_INVALID")
    if any(sum(row["attempt_id"] == attempt_id for row in adapter["cleanup"]) != 1 for attempt_id in attempt_ids):
        raise ContractError("ATTEMPT_CLEANUP_CARDINALITY_INVALID")
    if any(sum(row["attempt_id"] == attempt_id for row in adapter["boundaries"]) != 1 for attempt_id in attempt_ids):
        raise ContractError("ATTEMPT_BOUNDARY_CARDINALITY_INVALID")
    if set(cleanup) != {item["cleanup_id"] for attempts in attempts_by_scenario.values() for item in attempts}:
        raise ContractError("ORPHAN_CLEANUP_RECORD")
    if set(boundaries) != {item["boundary_id"] for attempts in attempts_by_scenario.values() for item in attempts}:
        raise ContractError("ORPHAN_BOUNDARY_RECORD")
    if adapter["runtime_preflight"]["tv"]["status"] != "READY":
        for scenario_id in PAIRED_REQUIRED_SCENARIOS:
            scenario = scenarios[int(scenario_id[-3:]) - 1]
            if scenario["attempts"] or scenario["blocker"] is None or scenario["blocker"]["status"] != "blocked_by_device":
                raise ContractError("MISSING_TV_MUST_BLOCK_PAIRED_ROW")
    inventory_anomaly_ids: set[str] = set()
    for row in adapter["inventory_anomalies"]:
        _strict_keys(row, {
            "anomaly_id", "category", "classification", "evidence_status",
            "trigger_category", "expected_result_category", "observed_result_category",
            "public_safe_screen_alias", "cause_evidence_status", "cause_category",
            "test_design_implication", "first_failure_retained", "reason_code",
        }, "INVENTORY_ANOMALY_SHAPE_INVALID")
        anomaly_id = _safe_id(row["anomaly_id"])
        if anomaly_id in inventory_anomaly_ids or anomaly_id in entity_ids:
            raise ContractError("ENTITY_ID_DUPLICATE")
        inventory_anomaly_ids.add(anomaly_id)
        entity_ids.add(anomaly_id)
        expected = INVENTORY_ANOMALY_DETAILS.get(anomaly_id)
        if expected is None or any(row[key] != value for key, value in expected.items()) or row["evidence_status"] != "confirmed" or row["first_failure_retained"] is not True:
            raise ContractError("INVENTORY_ANOMALY_INVALID")
    inventory_cleanup = adapter["inventory_cleanup"]
    _strict_keys(inventory_cleanup, {"cleanup_id", "target_app_force_stopped", "home_restored", "external_browser_opened", "payment_or_session_started", "account_mutated", "network_changed", "paired_state_observed", "existing_session_preserved", "evidence_status"}, "INVENTORY_CLEANUP_SHAPE_INVALID")
    cleanup_id = _safe_id(inventory_cleanup["cleanup_id"])
    if cleanup_id in entity_ids:
        raise ContractError("ENTITY_ID_DUPLICATE")
    cleanup_flags = (
        "target_app_force_stopped", "home_restored", "external_browser_opened",
        "payment_or_session_started", "account_mutated", "network_changed",
        "paired_state_observed", "existing_session_preserved",
    )
    if any(not isinstance(inventory_cleanup[key], bool) for key in cleanup_flags) or inventory_cleanup["evidence_status"] != "confirmed" or any(inventory_cleanup[key] is not False for key in ("external_browser_opened", "payment_or_session_started", "account_mutated", "network_changed", "paired_state_observed")):
        raise ContractError("INVENTORY_CLEANUP_SAFETY_INVALID")
    _safe_public_value(adapter)


def validate_adapter(adapter: Mapping[str, Any]) -> None:
    schema = _load_schema()
    _validate_schema_instance(adapter, schema, root=schema)
    _validate_header(adapter)
    _validate_relations(adapter)


def _inventory_cleanup_complete(cleanup: Mapping[str, Any]) -> bool:
    return (
        cleanup["evidence_status"] == "confirmed"
        and all(cleanup[key] is True for key in ("target_app_force_stopped", "home_restored", "existing_session_preserved"))
        and all(cleanup[key] is False for key in (
            "external_browser_opened", "payment_or_session_started", "account_mutated",
            "network_changed", "paired_state_observed",
        ))
    )


def _derive_scenario(scenario: Mapping[str, Any], cleanup_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    scenario_id = scenario["scenario_id"]
    attempts = scenario["attempts"]
    blocker = scenario["blocker"]
    failures = [item for item in attempts if item["oracle_result"] == "fail"]
    if failures:
        status = "observed_fail"
        reason = "first_runtime_failure_retained"
        evidence_type = failures[0]["evidence_type"]
        evidence_status = "confirmed"
    elif blocker is not None:
        status = blocker["status"]
        reason = blocker["reason_code"]
        evidence_type = "static_contract"
        evidence_status = "confirmed"
    elif not attempts:
        raise ContractError("UNCLASSIFIED_SCENARIO")
    else:
        first = attempts[0]
        if any(item["oracle_result"] != "pass" for item in attempts):
            raise ContractError("NONTERMINAL_ATTEMPT")
        elif any(item["recovery_attempt"] for item in attempts):
            status = "observed_fail"
            reason = "recovery_cannot_be_clean_pass"
        else:
            expected_action, expected_state = PASS_ORACLES[scenario_id]
            if any(item["action_category"] != expected_action or item["observed_state_alias"] != expected_state for item in attempts):
                raise ContractError("PASS_ORACLE_MISMATCH")
            if any(item["evidence_status"] != "confirmed" for item in attempts):
                raise ContractError("PASS_REQUIRES_CONFIRMED_EVIDENCE")
            if any(
                cleanup_by_id[item["cleanup_id"]]["result"] != "pass"
                or cleanup_by_id[item["cleanup_id"]]["evidence_status"] != "confirmed"
                or cleanup_by_id[item["cleanup_id"]]["kill_switch_ready"] is not True
                or cleanup_by_id[item["cleanup_id"]]["rollback_verified"] is not True
                for item in attempts
            ):
                raise ContractError("PASS_REQUIRES_CONFIRMED_CLEANUP")
            status = "observed_pass"
            reason = "fresh_applicable_runtime_oracle"
        evidence_type = first["evidence_type"]
        evidence_status = "confirmed" if status in {"observed_pass", "observed_fail"} else first["evidence_status"]
    return {
        "scenario_id": scenario_id,
        "scenario_status": status,
        "evidence_type": evidence_type,
        "evidence_status": evidence_status,
        "attempt_count": len(attempts),
        "reason_code": reason,
        "automation_target": "automated_adapter",
        "phone_independent_allowed": scenario_id in INDEPENDENT_PHONE_SCENARIOS,
        "paired_evidence_present": any(item["evidence_type"] == "paired_physical_runtime" for item in attempts),
        "first_failure_retained": any(item["oracle_result"] == "fail" for item in attempts),
    }


def validate_and_derive(adapter: Mapping[str, Any], catalog: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    validate_adapter(adapter)
    cleanup_by_id = {row["cleanup_id"]: row for row in adapter["cleanup"]}
    rows = [_derive_scenario(item, cleanup_by_id) for item in adapter["scenarios"][:-1]]
    if any(row["scenario_status"] not in TERMINAL_STATUSES for row in rows):
        raise ContractError("PRIOR_SCENARIO_NOT_TERMINAL")
    closure_input = adapter["scenarios"][-1]
    declaration_complete = adapter["runtime_preflight"]["inventory_declaration_complete"]
    coverage_terminal = all(
        not (row["approved_scope"] and row["declared_reachable"])
        or row["status"] in COVERAGE_STATUSES - {"not_run_out_of_scope"}
        for row in adapter["phone_coverage"]
    )
    cleanup_complete = _inventory_cleanup_complete(adapter["inventory_cleanup"])
    inventory_closed = declaration_complete and coverage_terminal and cleanup_complete
    if not declaration_complete:
        closure_reason = "phone_inventory_declaration_incomplete"
    elif not coverage_terminal:
        closure_reason = "phone_inventory_terminal_classification_incomplete"
    else:
        closure_reason = "phone_inventory_cleanup_incomplete"
    expected_closure_blocker = None if inventory_closed else {"status": "blocked_by_oracle", "reason_code": closure_reason}
    if closure_input["attempts"] or closure_input["blocker"] != expected_closure_blocker:
        raise ContractError("STATIC_CLOSURE_INPUT_INVALID")
    closure_status = "observed_pass" if inventory_closed else "blocked_by_oracle"
    rows.append({
        "scenario_id": CLOSURE_SCENARIO,
        "scenario_status": closure_status,
        "evidence_type": "static_contract",
        "evidence_status": "confirmed",
        "attempt_count": 0,
        "reason_code": "all_prior_rows_phone_inventory_and_cleanup_terminal_static_closure" if inventory_closed else closure_reason,
        "automation_target": "automated_adapter",
        "phone_independent_allowed": False,
        "paired_evidence_present": False,
        "first_failure_retained": False,
    })
    catalog_by_id = {row["scenario_id"]: row for row in catalog}
    if set(catalog_by_id) != set(EXPECTED_IDS):
        raise ContractError("CATALOG_RECONCILIATION_FAILED")
    for row in rows:
        row.update({key: catalog_by_id[row["scenario_id"]][key] for key in ("priority", "surface_ids", "lane", "category")})
    status_counts = Counter(row["scenario_status"] for row in rows)
    if adapter["runtime_preflight"]["tv"]["status"] != "READY" and not any(row["scenario_status"] == "blocked_by_device" for row in rows):
        raise ContractError("MISSING_TV_BLOCKER_LOST")
    coverage_blocked = not inventory_closed or any(row["status"] != "covered" for row in adapter["phone_coverage"] if row["approved_scope"] and row["declared_reachable"])
    return {
        "rows": rows,
        "status_counts": dict(sorted(status_counts.items())),
        "overall_status": "partial_blocked" if coverage_blocked or any(row["scenario_status"] != "observed_pass" for row in rows) else "pass",
        "inventory_closed": inventory_closed,
    }


def _csv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for source in rows:
        row = {header: source.get(header, "") for header in headers}
        for key, value in list(row.items()):
            if isinstance(value, bool):
                row[key] = str(value).lower()
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _baseline_adapter() -> dict[str, Any]:
    scenarios = []
    for scenario_id in EXPECTED_IDS:
        if scenario_id == CLOSURE_SCENARIO:
            blocker = {"status": "blocked_by_oracle", "reason_code": "phone_inventory_declaration_incomplete"}
        elif scenario_id in INDEPENDENT_PHONE_SCENARIOS:
            blocker = {"status": "blocked_by_oracle", "reason_code": "independent_phone_runtime_not_ingested"}
        else:
            blocker = {"status": "blocked_by_device", "reason_code": "paired_tv_unavailable"}
        scenarios.append({"scenario_id": scenario_id, "attempts": [], "blocker": blocker})
    coverage = []
    for index, (alias, lane_scope) in enumerate(BASELINE_PHONE_BRANCHES, start=1):
        requires_pair = lane_scope == "paired_required"
        coverage.append({
            "coverage_id": f"phone-coverage-{index:02d}",
            "branch_alias": alias,
            "lane_scope": lane_scope,
            "approved_scope": True,
            "declared_reachable": False,
            "discovered": False,
            "requires_connected_pair": requires_pair,
            "status": "blocked_by_external_state" if requires_pair else "blocked_by_tooling",
            "screen_alias": "not_observed",
            "state_category": "blocked",
            "focus_action_category": "not_observed",
            "evidence_status": "unknown",
            "evidence_ids": [],
            "reason_code": "paired_tv_unavailable" if requires_pair else "independent_phone_runtime_not_ingested",
        })
    return {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "run_id": "task045-blocked-baseline",
        "generated_at_utc": "2026-08-15T00:00:00Z",
        "scenario_contract_version": SCENARIO_CONTRACT_VERSION,
        "build_ref": {
            "alias": INSTALLED_BUILD_ALIAS,
            "phone_apk_family": PHONE_APK_FAMILY,
            "tv_apk_family": TV_APK_FAMILY,
            "installed_lane_alias": INSTALLED_BUILD_ALIAS,
            "canonical_bundle_alias": CANONICAL_BUILD_ALIAS,
            "canonical_install_outcome": "blocked_version_downgrade",
            "compatibility_evidence_status": "unknown",
            "raw_hash_published": False,
        },
        "targets": {
            "phone": {"lane_alias": PHONE_ALIAS, "profile_alias": PHONE_PROFILE_ALIAS, "apk_family": PHONE_APK_FAMILY, "form_factor": "phone", "physical": True, "present": True},
            "tv": {"lane_alias": TV_ALIAS, "profile_alias": TV_PROFILE_ALIAS, "apk_family": TV_APK_FAMILY, "form_factor": "tv", "physical": True, "present": False},
        },
        "runtime_preflight": {
            "status": "PARTIAL_BLOCKED",
            "phone": {"status": "BLOCKED", "adb_authorized": False, "artifact_present": False, "family_confirmed": True, "owner_declared_available": True, "reason_code": "repository_only_builder_no_runtime_preflight"},
            "tv": {"status": "BLOCKED", "adb_authorized": False, "artifact_present": False, "family_confirmed": False, "owner_declared_available": False, "reason_code": "paired_tv_unavailable"},
            "synthetic_fixture_ready": False,
            "ignored_evidence_storage_ready": False,
            "cleanup_rollback_ready": True,
            "reviewer_gate": True,
            "inventory_declaration_complete": False,
            "inventory_discovered_branch_count": 0,
            "inventory_approved_reachable_branch_count": 0,
            "session_provenance": "unknown_not_verified",
            "session_dependent_evidence_eligible": False,
        },
        "scenarios": scenarios,
        "phone_coverage": coverage,
        "paired_timeline": [],
        "anomalies": [],
        "inventory_anomalies": [],
        "inventory_evidence_ids": [],
        "inventory_cleanup": {
            "cleanup_id": "task045-baseline-cleanup",
            "target_app_force_stopped": False,
            "home_restored": False,
            "external_browser_opened": False,
            "payment_or_session_started": False,
            "account_mutated": False,
            "network_changed": False,
            "paired_state_observed": False,
            "existing_session_preserved": True,
            "evidence_status": "confirmed",
        },
        "boundaries": [],
        "cleanup": [],
    }


def _adapter_from_runtime_coverage_source(source: Mapping[str, Any]) -> dict[str, Any]:
    _strict_keys(source, {
        "task_id", "selected_device_alias", "apk_family", "build_set_alias",
        "build_provenance", "build_relation", "canonical_apk_install_status",
        "canonical_apk_install_reason", "canonical_apk_runtime_status",
        "compatibility_with_canonical_build", "tv_status", "scenario_observations",
        "coverage", "anomalies", "cleanup",
    }, "COVERAGE_SOURCE_SHAPE_INVALID")
    expected_header = {
        "task_id": TASK_ID,
        "selected_device_alias": PHONE_ALIAS,
        "apk_family": PHONE_APK_FAMILY,
        "build_provenance": "owner_confirmed_existing_phone_full_install",
        "build_relation": "installed_newer_than_canonical_candidate",
        "canonical_apk_install_status": "blocked_by_external_state",
        "canonical_apk_install_reason": "version_downgrade_rejected",
        "canonical_apk_runtime_status": "not_run",
        "compatibility_with_canonical_build": "unknown_not_verified",
        "tv_status": "blocked_by_device",
        "build_set_alias": INSTALLED_BUILD_ALIAS,
    }
    if any(source.get(key) != value for key, value in expected_header.items()):
        raise ContractError("COVERAGE_SOURCE_PROVENANCE_INVALID")
    build_alias = _safe_id(source["build_set_alias"])
    observations = source["scenario_observations"]
    if not isinstance(observations, list) or {row.get("scenario_id") for row in observations if isinstance(row, dict)} != INDEPENDENT_PHONE_SCENARIOS:
        raise ContractError("COVERAGE_SOURCE_SCENARIOS_INVALID")
    observation_map: dict[str, Mapping[str, Any]] = {}
    for row in observations:
        _strict_keys(row, {"scenario_id", "status", "reason_code", "evidence_ids", "note"}, "COVERAGE_SOURCE_SCENARIO_SHAPE_INVALID")
        if row["status"] != "blocked_by_oracle" or not isinstance(row["evidence_ids"], list):
            raise ContractError("COVERAGE_SOURCE_SCENARIO_STATUS_INVALID")
        _safe_id(row["reason_code"])
        observation_map[row["scenario_id"]] = row
    raw_coverage = source["coverage"]
    if not isinstance(raw_coverage, list) or not raw_coverage:
        raise ContractError("COVERAGE_SOURCE_ROWS_INVALID")
    registry: list[str] = []
    coverage: list[dict[str, Any]] = []
    paired_aliases = {
        "phone-connected-gamepad", "phone-network-reconnect", "phone-lock-unlock",
        "phone-paired-disconnect",
    }
    seen_aliases: set[str] = set()
    for index, row in enumerate(raw_coverage, start=1):
        _strict_keys(row, {"branch_alias", "status", "evidence_ids", "reason_code"}, "COVERAGE_SOURCE_ROW_SHAPE_INVALID")
        alias = _safe_id(row["branch_alias"])
        if alias in seen_aliases or row["status"] not in COVERAGE_STATUSES:
            raise ContractError("COVERAGE_SOURCE_ROW_INVALID")
        seen_aliases.add(alias)
        if not isinstance(row["evidence_ids"], list):
            raise ContractError("COVERAGE_SOURCE_EVIDENCE_INVALID")
        for evidence_id in row["evidence_ids"]:
            _safe_id(evidence_id)
            if evidence_id not in registry:
                registry.append(evidence_id)
        source_status = row["status"]
        reason = _safe_id(row["reason_code"])
        if alias in SESSION_DEPENDENT_BRANCHES and source_status == "covered":
            normalized_status = "blocked_by_external_state"
            reason = "synthetic_session_fixture_not_verified"
        else:
            normalized_status = source_status
        lane_scope = "paired_required" if alias in paired_aliases else "disconnected_independent"
        approved = normalized_status != "not_run_out_of_scope"
        discovered = bool(row["evidence_ids"])
        coverage.append({
            "coverage_id": f"phone-coverage-{index:03d}",
            "branch_alias": alias,
            "lane_scope": lane_scope,
            "approved_scope": approved,
            "declared_reachable": approved and discovered,
            "discovered": discovered,
            "requires_connected_pair": lane_scope == "paired_required",
            "status": normalized_status,
            "screen_alias": alias,
            "state_category": "observed" if discovered else "blocked_or_out_of_scope",
            "focus_action_category": "recorded_checkpoint" if discovered else "not_observed",
            "evidence_status": "confirmed",
            "evidence_ids": list(row["evidence_ids"]),
            "reason_code": reason,
        })
    raw_anomalies = source["anomalies"]
    if not isinstance(raw_anomalies, list) or len(set(raw_anomalies)) != len(raw_anomalies):
        raise ContractError("COVERAGE_SOURCE_ANOMALIES_INVALID")
    inventory_anomalies = []
    for anomaly_id in raw_anomalies:
        _safe_id(anomaly_id)
        process = anomaly_id.startswith("TASK045-PROCESS-ANOMALY-")
        runtime = anomaly_id.startswith("TASK045-RUNTIME-ANOMALY-")
        if not (process or runtime):
            raise ContractError("COVERAGE_SOURCE_ANOMALY_ID_INVALID")
        if anomaly_id not in INVENTORY_ANOMALY_DETAILS:
            raise ContractError("COVERAGE_SOURCE_ANOMALY_DETAIL_MISSING")
        inventory_anomalies.append({
            "anomaly_id": anomaly_id,
            "category": "process_anomaly" if process else "runtime_anomaly",
            "evidence_status": "confirmed",
            "first_failure_retained": True,
            **INVENTORY_ANOMALY_DETAILS[anomaly_id],
        })
    raw_cleanup = source["cleanup"]
    cleanup_keys = {"target_app_force_stopped", "home_restored", "external_browser_opened", "payment_or_session_started", "account_mutated", "network_changed", "paired_state_observed", "existing_session_preserved"}
    _strict_keys(raw_cleanup, cleanup_keys, "COVERAGE_SOURCE_CLEANUP_INVALID")
    if any(not isinstance(raw_cleanup[key], bool) for key in cleanup_keys):
        raise ContractError("COVERAGE_SOURCE_CLEANUP_INVALID")
    declaration_complete = REQUIRED_RUNTIME_COVERAGE_BRANCHES.issubset(seen_aliases)
    cleanup_complete = (
        all(raw_cleanup[key] is True for key in ("target_app_force_stopped", "home_restored", "existing_session_preserved"))
        and all(raw_cleanup[key] is False for key in (
            "external_browser_opened", "payment_or_session_started", "account_mutated",
            "network_changed", "paired_state_observed",
        ))
    )
    coverage_terminal = all(
        not (row["approved_scope"] and row["declared_reachable"])
        or row["status"] != "not_run_out_of_scope"
        for row in coverage
    )
    if not declaration_complete:
        closure_reason = "phone_inventory_declaration_incomplete"
    elif not coverage_terminal:
        closure_reason = "phone_inventory_terminal_classification_incomplete"
    else:
        closure_reason = "phone_inventory_cleanup_incomplete"
    scenarios = []
    for scenario_id in EXPECTED_IDS:
        if scenario_id == CLOSURE_SCENARIO:
            blocker = None if declaration_complete and coverage_terminal and cleanup_complete else {
                "status": "blocked_by_oracle", "reason_code": closure_reason,
            }
        elif scenario_id in INDEPENDENT_PHONE_SCENARIOS:
            blocker = {"status": "blocked_by_oracle", "reason_code": observation_map[scenario_id]["reason_code"]}
        else:
            blocker = {"status": "blocked_by_device", "reason_code": "paired_tv_unavailable"}
        scenarios.append({"scenario_id": scenario_id, "attempts": [], "blocker": blocker})
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "run_id": "task045-phone-inventory-runtime",
        "generated_at_utc": generated_at,
        "scenario_contract_version": SCENARIO_CONTRACT_VERSION,
        "build_ref": {
            "alias": build_alias,
            "phone_apk_family": PHONE_APK_FAMILY,
            "tv_apk_family": TV_APK_FAMILY,
            "installed_lane_alias": build_alias,
            "canonical_bundle_alias": CANONICAL_BUILD_ALIAS,
            "canonical_install_outcome": "blocked_version_downgrade",
            "compatibility_evidence_status": "unknown",
            "raw_hash_published": False,
        },
        "targets": {
            "phone": {"lane_alias": PHONE_ALIAS, "profile_alias": PHONE_PROFILE_ALIAS, "apk_family": PHONE_APK_FAMILY, "form_factor": "phone", "physical": True, "present": True},
            "tv": {"lane_alias": TV_ALIAS, "profile_alias": TV_PROFILE_ALIAS, "apk_family": TV_APK_FAMILY, "form_factor": "tv", "physical": True, "present": False},
        },
        "runtime_preflight": {
            "status": "PARTIAL_BLOCKED",
            "phone": {"status": "READY", "adb_authorized": True, "artifact_present": True, "family_confirmed": True, "owner_declared_available": True, "reason_code": "installed_newer_phone_full_lane_ready"},
            "tv": {"status": "BLOCKED", "adb_authorized": False, "artifact_present": False, "family_confirmed": False, "owner_declared_available": False, "reason_code": "paired_tv_unavailable"},
            "synthetic_fixture_ready": False,
            "ignored_evidence_storage_ready": True,
            "cleanup_rollback_ready": True,
            "reviewer_gate": True,
            "inventory_declaration_complete": declaration_complete,
            "inventory_discovered_branch_count": sum(row["discovered"] for row in coverage),
            "inventory_approved_reachable_branch_count": sum(row["approved_scope"] and row["declared_reachable"] for row in coverage),
            "session_provenance": "unknown_not_verified",
            "session_dependent_evidence_eligible": False,
        },
        "scenarios": scenarios,
        "phone_coverage": coverage,
        "paired_timeline": [],
        "anomalies": [],
        "inventory_anomalies": inventory_anomalies,
        "inventory_evidence_ids": registry,
        "inventory_cleanup": {"cleanup_id": "task045-phone-inventory-final-cleanup", **raw_cleanup, "evidence_status": "confirmed"},
        "boundaries": [],
        "cleanup": [],
    }


def _load_runtime_coverage_source() -> dict[str, Any]:
    try:
        fixed = LOCAL_COVERAGE_SOURCE.resolve(strict=True)
        root = LOCAL_ADAPTER_ROOT.resolve(strict=True)
    except OSError:
        raise ContractError("COVERAGE_SOURCE_MISSING") from None
    if fixed != LOCAL_COVERAGE_SOURCE.absolute() or not fixed.is_relative_to(root) or fixed.is_symlink():
        raise ContractError("COVERAGE_SOURCE_PATH_INVALID")
    try:
        value = json.loads(fixed.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ContractError("COVERAGE_SOURCE_INVALID") from None
    if not isinstance(value, dict):
        raise ContractError("COVERAGE_SOURCE_INVALID")
    return value


def _ledger_rows(adapter: Mapping[str, Any], derived: Mapping[str, Any]) -> list[dict[str, Any]]:
    cleanup_by_attempt = {row["attempt_id"]: row for row in adapter["cleanup"]}
    boundaries = {row["boundary_id"]: row for row in adapter["boundaries"]}
    scenarios = {row["scenario_id"]: row for row in adapter["scenarios"]}
    result = []
    for row in derived["rows"]:
        attempts = scenarios[row["scenario_id"]]["attempts"]
        cleanup_status = "not_run" if not attempts else (
            "pass" if all(cleanup_by_attempt[item["attempt_id"]]["result"] in {"pass", "not_required"} for item in attempts) else "fail"
        )
        boundary_status = "not_run" if not attempts else (
            "held" if all(not boundaries[item["boundary_id"]]["external_action_performed"] for item in attempts) else "violated"
        )
        result.append({**row, "cleanup_status": cleanup_status, "boundary_status": boundary_status})
    return result


def build_bundle(adapter: Mapping[str, Any], catalog: Sequence[Mapping[str, str]]) -> dict[Path, bytes]:
    derived = validate_and_derive(adapter, catalog)
    scenario_rows = _ledger_rows(adapter, derived)
    scenario_bytes = _csv_bytes(SCENARIO_LEDGER_HEADERS, scenario_rows)
    coverage_rows = [{**row, "evidence_count": len(row["evidence_ids"])} for row in adapter["phone_coverage"]]
    coverage_bytes = _csv_bytes(PHONE_COVERAGE_HEADERS, coverage_rows)
    timeline_rows = [{**row, "evidence_count": len(row["evidence_ids"])} for row in adapter["paired_timeline"]]
    timeline_bytes = _csv_bytes(TIMELINE_HEADERS, timeline_rows)
    anomaly_rows = list(adapter["anomalies"])
    anomaly_rows.extend({
        "anomaly_id": row["anomaly_id"],
        "scenario_id": "none",
        "attempt_id": "none",
        "trigger_category": row["trigger_category"],
        "expected_result_category": row["expected_result_category"],
        "observed_result_category": row["observed_result_category"],
        "public_safe_screen_alias": row["public_safe_screen_alias"],
        "classification": row["classification"],
        "evidence_status": row["evidence_status"],
        "cause_evidence_status": row["cause_evidence_status"],
        "cause_category": row["cause_category"],
        "test_design_implication": row["test_design_implication"],
        "first_failure_retained": row["first_failure_retained"],
        "reason_code": row["reason_code"],
    } for row in adapter["inventory_anomalies"])
    anomaly_bytes = _csv_bytes(ANOMALY_HEADERS, anomaly_rows)
    cleanup_rows = [{
        **row, "record_scope": "scenario_attempt",
        "target_app_force_stopped": "", "home_restored": "",
        "external_browser_opened": "", "payment_or_session_started": "",
        "account_mutated": "", "network_changed": "",
        "paired_state_observed": "", "existing_session_preserved": "",
    } for row in adapter["cleanup"]]
    inventory_cleanup = adapter["inventory_cleanup"]
    cleanup_rows.append({
        "cleanup_id": inventory_cleanup["cleanup_id"],
        "record_scope": "phone_inventory_run", "scenario_id": "none",
        "attempt_id": "none", "action_category": "final_force_stop_and_home_restore",
        "result": "pass" if _inventory_cleanup_complete(inventory_cleanup) else "not_run",
        "kill_switch_ready": True, "rollback_verified": inventory_cleanup["home_restored"],
        **inventory_cleanup,
    })
    cleanup_bytes = _csv_bytes(CLEANUP_HEADERS, cleanup_rows)
    artifacts = []
    artifact_counts: dict[str, int] = {}
    for kind, path, content, count in (
        ("scenario_ledger", SCENARIO_LEDGER_OUTPUT, scenario_bytes, len(scenario_rows)),
        ("phone_coverage_ledger", PHONE_COVERAGE_OUTPUT, coverage_bytes, len(coverage_rows)),
        ("paired_timeline_ledger", TIMELINE_OUTPUT, timeline_bytes, len(timeline_rows)),
        ("anomaly_ledger", ANOMALY_OUTPUT, anomaly_bytes, len(anomaly_rows)),
        ("cleanup_ledger", CLEANUP_OUTPUT, cleanup_bytes, len(cleanup_rows)),
    ):
        artifacts.append({"kind": kind, "reference": _repo_reference(path), "sha256": _sha(content), "evidence_status": "confirmed"})
        artifact_counts[kind] = count
    blocked_reasons = sorted(
        {row["reason_code"] for row in scenario_rows if row["scenario_status"] in BLOCKED_STATUSES}
        | {row["reason_code"] for row in coverage_rows if row["status"] != "covered"}
    )
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": "partial_blocked" if derived["overall_status"] != "pass" else "pass",
        "coverage_status": "covered" if derived["overall_status"] == "pass" else "partial_blocked",
        "evidence_status": "confirmed_for_recorded_checkpoints" if derived["overall_status"] != "pass" else "confirmed",
        "release_effect": "blocks_release" if derived["overall_status"] != "pass" else "candidate_evidence",
        "production_safety_classification": SAFETY_CLASS,
        "generated_at_utc": adapter["generated_at_utc"],
        "task_id": TASK_ID,
        "build_ref": {"alias": adapter["build_ref"]["alias"]},
        "target_alias": "paired-tv-phone-lane",
        "run_id": adapter["run_id"],
        "artifacts": artifacts,
        "blocked_reasons": blocked_reasons,
        "unknowns": [
            {"id": f"TASK045-UNKNOWN-{row['scenario_id'][-3:]}", "scenario_id": row["scenario_id"], "scenario_status": row["scenario_status"], "reason_code": row["reason_code"], "evidence_status": "unknown"}
            for row in scenario_rows if row["scenario_status"] in BLOCKED_STATUSES
        ] + [{"id": "TASK045-UNKNOWN-BUILD-COMPAT", "reason_code": "installed_newer_compatibility_with_canonical_unknown", "evidence_status": "unknown"}],
        "risks": [
            {"id": "TASK045-RISK-001", "evidence_status": "confirmed", "summary": "Missing TV blocks paired and connected-state claims; disconnected phone evidence cannot substitute."},
            {"id": "TASK045-RISK-002", "evidence_status": "confirmed", "summary": "Unknown preserved-session provenance makes session-dependent phone checkpoints ineligible for product coverage."},
        ],
        "verification": [
            {"check": "catalog_reconciliation", "status": "pass", "result_count": 22, "evidence_status": "confirmed"},
            {"check": "p0_p1_reconciliation", "status": "pass", "result_count": "20/2", "evidence_status": "confirmed"},
            {"check": "phone_coverage_terminal_ledger", "status": "pass" if derived["inventory_closed"] else "blocked", "result_count": len(coverage_rows), "evidence_status": "confirmed"},
            {"check": "atomic_bundle_validation", "status": "pass", "result_count": 6, "evidence_status": "confirmed"},
        ],
        "review": {"qa_reviewer_a": "pending", "qa_reviewer_b": "pending", "security_prod_safety_reviewer": "pending", "docs_scribe": "pending"},
        "provenance": {
            "adapter_input_published": False,
            "adapter_schema": _repo_reference(ADAPTER_SCHEMA),
            "adapter_schema_sha256": _sha(ADAPTER_SCHEMA.read_bytes()),
            "scenario_contract": _repo_reference(CATALOG),
            "scenario_contract_version": SCENARIO_CONTRACT_VERSION,
            "adapter_schema_validation": "applied_full_instance",
        },
        "payload": {
            "lane_preflight": {
                "outcome": adapter["runtime_preflight"]["status"],
                "phone": {"alias": adapter["targets"]["phone"]["lane_alias"], "apk_family": PHONE_APK_FAMILY, "outcome": adapter["runtime_preflight"]["phone"]["status"], "reason_code": adapter["runtime_preflight"]["phone"]["reason_code"]},
                "tv": {"alias": TV_ALIAS, "apk_family": TV_APK_FAMILY, "outcome": adapter["runtime_preflight"]["tv"]["status"], "reason_code": adapter["runtime_preflight"]["tv"]["reason_code"]},
                "session_provenance": adapter["runtime_preflight"]["session_provenance"],
                "session_dependent_evidence_eligible": adapter["runtime_preflight"]["session_dependent_evidence_eligible"],
            },
            "build_provenance": {
                "installed_lane_alias": adapter["build_ref"]["installed_lane_alias"],
                "canonical_bundle_alias": adapter["build_ref"]["canonical_bundle_alias"],
                "canonical_install_outcome": adapter["build_ref"]["canonical_install_outcome"],
                "canonical_execution_outcome": "not_run",
                "compatibility_evidence_status": adapter["build_ref"]["compatibility_evidence_status"],
                "raw_hash_published": False,
            },
            "scenario_summary": {"total": 22, "P0": 20, "P1": 2, "status_counts": derived["status_counts"]},
            "phone_inventory": {
                "closure": derived["inventory_closed"],
                "branch_count": len(coverage_rows),
                "discovered_branch_count": adapter["runtime_preflight"]["inventory_discovered_branch_count"],
                "approved_reachable_branch_count": adapter["runtime_preflight"]["inventory_approved_reachable_branch_count"],
            },
            "paired_tv_available": adapter["runtime_preflight"]["tv"]["status"] == "READY",
            "paired_claim": "not_established" if adapter["runtime_preflight"]["tv"]["status"] != "READY" else "evaluated",
            "artifact_row_counts": artifact_counts,
            "boundary_guards": {"real_payment_performed": False, "paid_session_started": False, "account_mutation_performed": False, "qr_or_browser_traversal_performed": False, "network_changed": adapter["inventory_cleanup"]["network_changed"]},
            "inventory_anomaly_count": len(anomaly_rows),
            "inventory_cleanup_confirmed": _inventory_cleanup_complete(adapter["inventory_cleanup"]),
        },
    }
    report_schema = _load_report_envelope_schema()
    _validate_schema_instance(report, report_schema, root=report_schema)
    _safe_public_value(report)
    outputs = {
        SCENARIO_LEDGER_OUTPUT: scenario_bytes,
        PHONE_COVERAGE_OUTPUT: coverage_bytes,
        TIMELINE_OUTPUT: timeline_bytes,
        ANOMALY_OUTPUT: anomaly_bytes,
        CLEANUP_OUTPUT: cleanup_bytes,
        REPORT_OUTPUT: _json_bytes(report),
    }
    validate_bundle(outputs, catalog=catalog)
    return outputs


def _parse_csv(content: bytes, headers: Sequence[str]) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    except UnicodeError:
        raise ContractError("BUNDLE_CSV_UNREADABLE") from None
    if tuple(reader.fieldnames or ()) != tuple(headers):
        raise ContractError("BUNDLE_CSV_HEADERS_INVALID")
    return list(reader)


def validate_bundle(outputs: Mapping[Path, bytes], *, catalog: Sequence[Mapping[str, str]] | None = None) -> None:
    expected = {REPORT_OUTPUT, SCENARIO_LEDGER_OUTPUT, PHONE_COVERAGE_OUTPUT, TIMELINE_OUTPUT, ANOMALY_OUTPUT, CLEANUP_OUTPUT}
    if set(outputs) != expected:
        raise ContractError("BUNDLE_TARGET_SET_INVALID")
    try:
        report = json.loads(outputs[REPORT_OUTPUT], object_pairs_hook=_json_pairs)
    except (UnicodeError, json.JSONDecodeError):
        raise ContractError("REPORT_JSON_INVALID") from None
    report_schema = _load_report_envelope_schema()
    _validate_schema_instance(report, report_schema, root=report_schema)
    if report["schema_version"] != REPORT_SCHEMA_VERSION or report["task_id"] != TASK_ID or report["schema_validation_status"] != "pass":
        raise ContractError("REPORT_IDENTITY_INVALID")
    if report["production_safety_classification"] != SAFETY_CLASS:
        raise ContractError("REPORT_SAFETY_CLASSIFICATION_INVALID")
    if report["coverage_status"] not in {"covered", "partial_blocked"}:
        raise ContractError("REPORT_COVERAGE_INVALID")
    if report["coverage_status"] == "partial_blocked" and report["release_effect"] != "blocks_release":
        raise ContractError("PARTIAL_MUST_BLOCK_RELEASE")
    if report["coverage_status"] == "covered" and report["release_effect"] != "candidate_evidence":
        raise ContractError("PASS_RELEASE_EFFECT_INVALID")
    scenario_rows = _parse_csv(outputs[SCENARIO_LEDGER_OUTPUT], SCENARIO_LEDGER_HEADERS)
    coverage_rows = _parse_csv(outputs[PHONE_COVERAGE_OUTPUT], PHONE_COVERAGE_HEADERS)
    timeline_rows = _parse_csv(outputs[TIMELINE_OUTPUT], TIMELINE_HEADERS)
    anomaly_rows = _parse_csv(outputs[ANOMALY_OUTPUT], ANOMALY_HEADERS)
    cleanup_rows = _parse_csv(outputs[CLEANUP_OUTPUT], CLEANUP_HEADERS)
    if len(scenario_rows) != 22 or tuple(row["scenario_id"] for row in scenario_rows) != EXPECTED_IDS:
        raise ContractError("REPORT_SCENARIO_LEDGER_INVALID")
    if Counter(row["priority"] for row in scenario_rows) != Counter({"P0": 20, "P1": 2}):
        raise ContractError("REPORT_PRIORITY_COUNTS_INVALID")
    if any(row["scenario_status"] not in TERMINAL_STATUSES for row in scenario_rows):
        raise ContractError("REPORT_NONTERMINAL_SCENARIO")
    if any(row["automation_target"] != "automated_adapter" for row in scenario_rows):
        raise ContractError("REPORT_AUTOMATION_COVERAGE_INVALID")
    inventory_closed = report["payload"]["phone_inventory"]["closure"]
    expected_closure = "observed_pass" if inventory_closed else "blocked_by_oracle"
    if scenario_rows[-1]["scenario_status"] != expected_closure or scenario_rows[-1]["evidence_type"] != "static_contract":
        raise ContractError("REPORT_STATIC_CLOSURE_INVALID")
    if not coverage_rows or any(row["status"] not in COVERAGE_STATUSES for row in coverage_rows):
        raise ContractError("REPORT_PHONE_COVERAGE_INVALID")
    if len({row["coverage_id"] for row in coverage_rows}) != len(coverage_rows) or len({row["branch_alias"] for row in coverage_rows}) != len(coverage_rows):
        raise ContractError("REPORT_PHONE_COVERAGE_IDENTITY_INVALID")
    for row in coverage_rows:
        try:
            evidence_count = int(row["evidence_count"])
        except ValueError:
            raise ContractError("REPORT_PHONE_COVERAGE_EVIDENCE_INVALID") from None
        if evidence_count < 0 or row["discovered"] != str(evidence_count > 0).lower():
            raise ContractError("REPORT_PHONE_COVERAGE_EVIDENCE_INVALID")
        if row["status"] == "covered" and (evidence_count == 0 or row["evidence_status"] != "confirmed"):
            raise ContractError("REPORT_PHONE_COVERAGE_FALSE_PASS")
        if row["approved_scope"] == "true" and row["declared_reachable"] == "true" and row["status"] == "not_run_out_of_scope":
            raise ContractError("REPORT_REACHABLE_APPROVED_BRANCH_NOT_TERMINAL")
    artifact_map = {item["reference"]: item for item in report["artifacts"]}
    for path, rows in (
        (SCENARIO_LEDGER_OUTPUT, scenario_rows), (PHONE_COVERAGE_OUTPUT, coverage_rows),
        (TIMELINE_OUTPUT, timeline_rows), (ANOMALY_OUTPUT, anomaly_rows),
        (CLEANUP_OUTPUT, cleanup_rows),
    ):
        reference = _repo_reference(path)
        kind = artifact_map.get(reference, {}).get("kind")
        if reference not in artifact_map or artifact_map[reference]["sha256"] != _sha(outputs[path]) or report["payload"]["artifact_row_counts"].get(kind) != len(rows):
            raise ContractError("REPORT_ARTIFACT_BINDING_INVALID")
    counts = Counter(row["scenario_status"] for row in scenario_rows)
    if report["payload"]["scenario_summary"] != {"total": 22, "P0": 20, "P1": 2, "status_counts": dict(sorted(counts.items()))}:
        raise ContractError("REPORT_SUMMARY_RECONCILIATION_INVALID")
    expected_coverage = "covered" if all(row["scenario_status"] == "observed_pass" for row in scenario_rows) and all(row["status"] == "covered" for row in coverage_rows) else "partial_blocked"
    if report["coverage_status"] != expected_coverage:
        raise ContractError("REPORT_COVERAGE_RECONCILIATION_INVALID")
    tv_ready = report["payload"]["lane_preflight"]["tv"]["outcome"] == "READY"
    if report["payload"]["paired_tv_available"] is not tv_ready:
        raise ContractError("REPORT_PREFLIGHT_RECONCILIATION_INVALID")
    lane_preflight = report["payload"]["lane_preflight"]
    if lane_preflight.get("session_provenance") == "unknown_not_verified" and lane_preflight.get("session_dependent_evidence_eligible") is not False:
        raise ContractError("REPORT_SESSION_EVIDENCE_ELIGIBILITY_INVALID")
    if report["payload"]["paired_tv_available"] is False:
        for row in scenario_rows:
            if row["scenario_id"] in PAIRED_REQUIRED_SCENARIOS and row["scenario_status"] != "blocked_by_device":
                raise ContractError("REPORT_MISSING_TV_FALSE_PASS")
    if any(report["payload"]["boundary_guards"].values()):
        raise ContractError("REPORT_FORBIDDEN_ACTION_CLAIM")
    if report["payload"]["phone_inventory"]["branch_count"] != len(coverage_rows):
        raise ContractError("REPORT_INVENTORY_COUNT_MISMATCH")
    if report["payload"]["inventory_anomaly_count"] != len(anomaly_rows):
        raise ContractError("REPORT_ANOMALY_COUNT_MISMATCH")
    for row in anomaly_rows:
        if row["scenario_id"] == "none":
            expected = INVENTORY_ANOMALY_DETAILS.get(row["anomaly_id"])
            if expected is None or any(row[key] != str(value).lower() if isinstance(value, bool) else row[key] != value for key, value in expected.items()):
                raise ContractError("REPORT_INVENTORY_ANOMALY_INVALID")
            if row["evidence_status"] != "confirmed" or row["first_failure_retained"] != "true":
                raise ContractError("REPORT_INVENTORY_ANOMALY_INVALID")
    inventory_cleanup_rows = [row for row in cleanup_rows if row["record_scope"] == "phone_inventory_run"]
    cleanup_confirmed = len(inventory_cleanup_rows) == 1 and all(
        inventory_cleanup_rows[0][key] == expected
        for key, expected in {
            "result": "pass", "kill_switch_ready": "true",
            "rollback_verified": "true", "evidence_status": "confirmed",
            "target_app_force_stopped": "true", "home_restored": "true",
            "external_browser_opened": "false", "payment_or_session_started": "false",
            "account_mutated": "false", "network_changed": "false",
            "paired_state_observed": "false", "existing_session_preserved": "true",
        }.items()
    )
    if report["payload"]["inventory_cleanup_confirmed"] is not cleanup_confirmed:
        raise ContractError("REPORT_INVENTORY_CLEANUP_RECONCILIATION_INVALID")
    if report["payload"]["phone_inventory"]["closure"] and not cleanup_confirmed:
        raise ContractError("REPORT_INVENTORY_CLOSURE_WITHOUT_CLEANUP")
    if report["payload"]["phone_inventory"]["closure"] and scenario_rows[-1]["scenario_status"] != "observed_pass":
        raise ContractError("REPORT_INVENTORY_CLOSURE_FALSE_PASS")
    if catalog is not None:
        expected_catalog = {row["scenario_id"]: row for row in catalog}
        for row in scenario_rows:
            source = expected_catalog.get(row["scenario_id"])
            if source is None or any(row[key] != source[key] for key in ("priority", "surface_ids", "lane", "category")):
                raise ContractError("REPORT_CATALOG_MISMATCH")
    _safe_public_value(report)
    for content in outputs.values():
        _safe_public_value(content.decode("utf-8"))


def _atomic_publish(outputs: Mapping[Path, bytes]) -> None:
    parents = {path.parent.resolve() for path in outputs}
    if len(parents) != 1:
        raise ContractError("ATOMIC_TARGET_PARENT_INVALID")
    parent = next(iter(parents))
    parent.mkdir(parents=True, exist_ok=True)
    staged: dict[Path, Path] = {}
    backups: dict[Path, bytes | None] = {}
    try:
        for target, content in outputs.items():
            handle, raw_path = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=parent)
            stage = Path(raw_path)
            try:
                with os.fdopen(handle, "wb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
            except Exception:
                stage.unlink(missing_ok=True)
                raise
            staged[target] = stage
            backups[target] = target.read_bytes() if target.exists() else None
        for target, stage in staged.items():
            os.replace(stage, target)
        staged.clear()
    except Exception:
        for target, previous in backups.items():
            try:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(previous)
            except OSError:
                pass
        raise ContractError("ATOMIC_PUBLISH_FAILED") from None
    finally:
        for stage in staged.values():
            stage.unlink(missing_ok=True)


def publish_bundle(outputs: Mapping[Path, bytes], *, catalog: Sequence[Mapping[str, str]]) -> None:
    validate_bundle(outputs, catalog=catalog)
    _atomic_publish(outputs)
    checked = {path: path.read_bytes() for path in outputs}
    validate_bundle(checked, catalog=catalog)


def _emit(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and publish TASK-045 paired virtual-gamepad evidence.")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true", help="Validate immutable constants only; performs no file or runtime access.")
    modes.add_argument("--preflight", action="store_true", help="Validate catalog, schema and local-only typed adapter; no writes or runtime actions.")
    modes.add_argument("--execute", action="store_true", help="Ingest a typed local-only adapter and atomically publish the public-safe bundle.")
    modes.add_argument("--publish-runtime-coverage", action="store_true", help="Ingest the fixed sanitized TASK-045 phone coverage source, validate the typed adapter, and atomically publish.")
    modes.add_argument("--publish-blocked-baseline", action="store_true", help="Publish the repository-only missing-TV baseline; no local-only or runtime access.")
    modes.add_argument("--validate-report", action="store_true", help="Validate the fixed tracked bundle; no writes or runtime actions.")
    parser.add_argument("--adapter-input", type=Path, help="Ignored local-only adapter JSON; raw values are never published.")
    parser.add_argument("--allow-prod-conditional-ingest", action="store_true", help="Required for execute; authorizes ingest only, never device control.")
    args = parser.parse_args(argv)
    try:
        if args.validate_only:
            errors = validate_static_constants()
            if errors:
                raise ContractError(errors[0])
            _emit({"task_id": TASK_ID, "mode": "validate_only", "status": "pass", "runtime_access": False})
            return 0
        if validate_static_constants():
            raise ContractError(validate_static_constants()[0])
        catalog = load_contract()
        _load_schema()
        if args.preflight:
            if args.adapter_input is None:
                raise ContractError("ADAPTER_INPUT_REQUIRED")
            adapter = _load_adapter(args.adapter_input)
            derived = validate_and_derive(adapter, catalog)
            _emit({"task_id": TASK_ID, "mode": "preflight", "status": "pass", "coverage_status": derived["overall_status"], "writes": False, "runtime_access": False})
            return 0
        if args.execute:
            if args.adapter_input is None or not args.allow_prod_conditional_ingest:
                raise ContractError("EXECUTE_GATE_REQUIRED")
            adapter = _load_adapter(args.adapter_input)
            outputs = build_bundle(adapter, catalog)
            publish_bundle(outputs, catalog=catalog)
            _emit({"task_id": TASK_ID, "mode": "execute", "status": "pass", "published_artifacts": len(outputs), "runtime_access": False})
            return 0
        if args.publish_runtime_coverage:
            if not args.allow_prod_conditional_ingest:
                raise ContractError("EXECUTE_GATE_REQUIRED")
            adapter = _adapter_from_runtime_coverage_source(_load_runtime_coverage_source())
            outputs = build_bundle(adapter, catalog)
            publish_bundle(outputs, catalog=catalog)
            _emit({"task_id": TASK_ID, "mode": "publish_runtime_coverage", "status": "pass", "published_artifacts": len(outputs), "device_actions": False})
            return 0
        if args.publish_blocked_baseline:
            outputs = build_bundle(_baseline_adapter(), catalog)
            publish_bundle(outputs, catalog=catalog)
            _emit({"task_id": TASK_ID, "mode": "publish_blocked_baseline", "status": "pass", "published_artifacts": len(outputs), "paired_tv_available": False, "runtime_access": False})
            return 0
        outputs = {path: _fixed_file(path, suffix=path.suffix).read_bytes() for path in (REPORT_OUTPUT, SCENARIO_LEDGER_OUTPUT, PHONE_COVERAGE_OUTPUT, TIMELINE_OUTPUT, ANOMALY_OUTPUT, CLEANUP_OUTPUT)}
        validate_bundle(outputs, catalog=catalog)
        _emit({"task_id": TASK_ID, "mode": "validate_report", "status": "pass", "artifacts": len(outputs), "runtime_access": False})
        return 0
    except ContractError as exc:
        _emit({"task_id": TASK_ID, "status": "blocked", "reason_code": str(exc), "runtime_access": False})
        return 2


if __name__ == "__main__":
    sys.exit(main())

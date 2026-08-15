"""Fixed public-safe TASK-058 blocked-runtime evidence bundle.

This repository-only validator never reads local evidence, APKs, Android tools,
or devices. It validates the sanitized projection produced after the separately
Security-reviewed one-shot package action stopped before product launch.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from automation.reporting.generate_report_manifest import _validate_v2_envelope
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from automation.reporting.generate_report_manifest import _validate_v2_envelope


TASK_ID = "TASK-058"
SCHEMA_VERSION = "evidence-report-envelope-v2"
RUN_ID = "task058-phone-first-launch-pre-auth-001"
GENERATED_AT = "2026-08-16T15:00:00Z"
REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_STEM = "task058_phone_first_launch_pre_auth_coverage"
REPORT_ROOT = REPO_ROOT / "docs/qa/reports"
TASK_SPEC = REPO_ROOT / "tasks/TASK_058_phone_first_launch_pre_auth_coverage.md"

LEDGERS = {
    "readiness": REPORT_ROOT / f"{REPORT_STEM}.readiness-ledger.csv",
    "package_action": REPORT_ROOT / f"{REPORT_STEM}.package-action-ledger.csv",
    "scenario": REPORT_ROOT / f"{REPORT_STEM}.scenario-ledger.csv",
    "screen_state": REPORT_ROOT / f"{REPORT_STEM}.screen-state-ledger.csv",
    "transition": REPORT_ROOT / f"{REPORT_STEM}.transition-ledger.csv",
    "overlay_recurrence": REPORT_ROOT / f"{REPORT_STEM}.overlay-recurrence-ledger.csv",
    "anomaly": REPORT_ROOT / f"{REPORT_STEM}.anomaly-ledger.csv",
    "boundary": REPORT_ROOT / f"{REPORT_STEM}.boundary-ledger.csv",
    "cleanup": REPORT_ROOT / f"{REPORT_STEM}.cleanup-ledger.csv",
}
REPORT_OUTPUT = REPORT_ROOT / f"{REPORT_STEM}.summary.json"

READINESS_HEADERS = (
    "row_id", "subject_alias", "evidence_status", "terminal_status",
    "evidence_ids", "reviewer_gate", "reason_code", "release_effect",
)
ACTION_HEADERS = (
    "row_id", "phase_order", "phase", "action_alias", "intended_count",
    "observed_count", "evidence_status", "terminal_status", "reason_code",
)
COMMON_HEADERS = (
    "row_id", "source_crosswalk_id", "approved_scope", "reachable", "status",
    "screen_alias", "state_category", "focus_category", "action_category",
    "evidence_status", "screenshot_id", "ui_tree_id", "log_marker_id",
    "reason_code", "release_effect", "cleanup_status",
)
TRANSITION_HEADERS = COMMON_HEADERS + ("from_checkpoint_id", "to_checkpoint_id")
ANOMALY_HEADERS = (
    "row_id", "alias", "trigger_action", "expected_result", "observed_result",
    "evidence_status", "screen_alias", "cause_level", "cause_note",
    "test_design_implication", "product_impact",
)
CLEANUP_HEADERS = (
    "row_id", "local_temp_cleanup", "package_end_state", "runtime_cleanup",
    "capture_shutdown", "launch_count", "navigation_count", "evidence_status",
    "terminal_status", "reason_code", "release_effect",
)

SAFE_VALUE = re.compile(r"^[A-Za-z0-9_.:-]+$")
FORBIDDEN = (
    re.compile(r"(?i)(?:^|[\s\"'])[a-z]:[\\/]"),
    re.compile(r"(?i)(?:^|[\\/])\.qa_local(?:[\\/]|$)"),
    re.compile(r"(?i)\b(?:https?|wss?|file|intent|market|mailto):"),
    re.compile(r"(?i)\b[0-9a-f]{32,}\b"),
    re.compile(r"(?i)\b(?:[a-z][a-z0-9_]*\.){2,}[a-z][a-z0-9_]*\b"),
)


class ContractError(ValueError):
    """The TASK-058 public-safe contract failed closed."""


def _safe(value: str, field: str) -> None:
    if not value or "\n" in value or "\r" in value or any(p.search(value) for p in FORBIDDEN):
        raise ContractError(f"unsafe_public_value:{field}")


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


def readiness_rows() -> list[dict[str, str]]:
    values = (
        ("task057-authority-01-canonical-phone-full", "task058-selected-phone-full-001", "confirmed", "observed_pass", "task058-candidate-integrity;task058-candidate-provenance;task058-candidate-signing;task058-candidate-version;task058-candidate-min-sdk;task058-candidate-target-sdk;task058-candidate-abi;task058-candidate-install-compatibility", "GO_PACKAGE_ACTION_CONDITIONAL", "candidate_full_preflight_confirmed", "candidate_evidence"),
        ("task057-authority-02-installed-compatibility", "installed-phone-full-build", "unknown", "blocked_by_tooling", "task058-install-presence", "BLOCK_RUNTIME", "postinstall_equivalence_interrupted_by_raw_spill", "blocks_release"),
        ("task057-authority-03-current-phone-selector", "phone-current-001", "unknown", "blocked_by_tooling", "task058-selector-preaction", "BLOCK_RUNTIME", "postaction_and_cleanup_selector_snapshots_not_completed", "blocks_release"),
        ("task057-authority-04-downgrade-safety", "ordinary-downgrade-guard", "confirmed", "observed_pass", "task058-package-action-ledger", "GO_PACKAGE_ACTION_CONDITIONAL", "one_target_uninstall_one_ordinary_install_zero_retry", "package_evidence"),
        ("task057-authority-05-synthetic-session", "synthetic-session-passport", "unknown", "blocked_by_fixture", "none", "BLOCK_RUNTIME", "synthetic_session_passport_absent", "blocks_release"),
        ("task057-authority-06-clean-first-launch", "clean-first-launch-fixture", "unknown", "blocked_by_fixture", "none", "BLOCK_RUNTIME", "clean_first_launch_fixture_passport_absent", "blocks_release"),
        ("task057-authority-07-evidence-cleanup-security", "evidence-cleanup-passport", "unknown", "blocked_by_fixture", "none", "BLOCK_RUNTIME", "runtime_evidence_cleanup_passport_absent", "blocks_release"),
    )
    return [dict(zip(READINESS_HEADERS, row)) for row in values]


def action_rows() -> list[dict[str, str]]:
    values = (
        ("01", "10", "pre_action", "security_package_action_gate", "1", "1", "confirmed", "observed_pass", "conditional_go_before_mutation"),
        ("02", "20", "pre_action", "candidate_and_selector_preflight", "1", "1", "confirmed", "observed_pass", "exact_preflight_passed"),
        ("03", "30", "package_action", "target_uninstall", "1", "1", "confirmed", "observed_pass", "authorized_target_uninstall_succeeded"),
        ("04", "40", "package_action", "target_absence", "1", "1", "confirmed", "observed_pass", "target_absent_after_uninstall"),
        ("05", "50", "package_action", "ordinary_install", "1", "1", "confirmed", "observed_pass", "selected_candidate_install_succeeded"),
        ("06", "60", "post_action", "package_presence", "1", "1", "confirmed", "observed_pass", "installed_package_path_present"),
        ("07", "70", "post_action", "installed_candidate_equivalence", "1", "0", "unknown", "blocked_by_tooling", "raw_spill_stopped_hash_and_signing_comparison"),
        ("08", "80", "post_action", "unrelated_package_delta", "1", "0", "unknown", "blocked_by_tooling", "raw_spill_stopped_delta_verification"),
        ("09", "90", "scope_closure", "retry", "0", "0", "confirmed", "observed_pass", "no_retry_or_alternate_artifact"),
        ("10", "100", "scope_closure", "launch_navigation", "0", "0", "confirmed", "observed_pass", "security_block_runtime_no_launch"),
    )
    return [dict(zip(ACTION_HEADERS, (f"task058-action-{n}", order, phase, alias, intended, observed, evidence, status, reason))) for n, order, phase, alias, intended, observed, evidence, status, reason in values]


def scenario_rows() -> list[dict[str, str]]:
    values = (
        ("task058-scenario-001", "phone-coverage-001", "first_launch"),
        ("task058-scenario-002", "phone-coverage-017", "auth_guard"),
        ("task058-scenario-003", "A002", "cold_launch_auth_guard"),
    )
    rows = []
    for row_id, source, state in values:
        rows.append(dict(zip(COMMON_HEADERS, (
            row_id, source, "true", "true", "blocked_by_external_state",
            "not_observed_runtime_blocked", state, "not_observed", "not_run",
            "unknown", "none", "none", "none", "security_block_runtime",
            "blocks_release", "runtime_cleanup_not_applicable",
        ))))
    return rows


def screen_state_rows() -> list[dict[str, str]]:
    return scenario_rows()[:2]


def transition_rows() -> list[dict[str, str]]:
    common = scenario_rows()[2]
    row = dict(common)
    row["row_id"] = "task058-transition-001"
    row["action_category"] = "launch_transition_not_run"
    row["reason_code"] = "security_block_runtime_transition_not_run"
    row["from_checkpoint_id"] = "task058-not-observed-launch-intent"
    row["to_checkpoint_id"] = "task058-not-observed-auth-guard"
    return [row]


def anomaly_rows() -> list[dict[str, str]]:
    values = (
        ("001", "preflight_result_object_syntax_failure", "preflight_result_projection", "category_only_preflight_result", "powershell_parser_error_before_execution", "tooling", "inline_expression_in_result_hashtable", "precompute_values_before_result_construction"),
        ("002", "sdk_root_scalar_indexing_failure", "android_tool_resolution", "single_sdk_root_resolves", "first_path_character_was_indexed", "tooling", "powershell_scalar_array_behavior", "materialize_pipeline_as_array_before_indexing"),
        ("003", "combined_package_action_command_policy_rejection", "combined_action_command", "one_shot_package_sequence_runs", "execution_policy_rejected_before_process_start", "tooling", "compound_command_policy", "use_short_separately_verified_steps_with_shared_budget"),
        ("004", "postinstall_pull_stderr_raw_path_spill", "postinstall_equivalence_pull", "sanitized_equivalence_result", "native_stderr_exposed_raw_path_and_interrupted_validation", "tooling", "native_progress_stderr_handling", "capture_and_sanitize_native_stderr_before_projection"),
        ("005", "schema_validator_invocation_and_spec_marker_mismatch", "focused_repository_validation", "baseline_and_schema_validation_pass", "task_spec_marker_and_repo_root_contract_were_incomplete", "tooling", "builder_contract_parity_gap", "validate_static_markers_and_called_function_signatures_before_baseline_generation"),
        ("006", "report_manifest_unsupported_write_flag", "report_manifest_regeneration", "manifest_regenerates_with_supported_cli", "unsupported_write_flag_returned_usage_error", "tooling", "cli_mode_assumption", "inspect_supported_cli_before_regeneration_and_use_default_write_mode"),
        ("007", "qa_reviewer_read_only_baseline_rewrite", "independent_qa_review", "read_only_review_preserves_files", "reviewer_invoked_deterministic_baseline_write", "tooling", "review_scope_command_mistake", "regenerate_under_orchestrator_and_keep_review_commands_read_only"),
        ("008", "guessed_docs_checker_path_failure", "independent_qa_docs_check", "canonical_docs_checker_runs", "guessed_nonexistent_checker_path_failed_before_execution", "tooling", "checker_path_assumption", "locate_and_run_canonical_docs_checker_without_guessing_paths"),
        ("009", "qa_source_marker_regex_syntax_failure", "independent_qa_source_marker_search", "read_only_source_marker_search_runs", "malformed_quoted_regex_rejected_before_search", "tooling", "powershell_regex_quoting_mistake", "use_literal_searches_or_prevalidated_shell_quoting_during_review"),
        ("010", "qa_stop_instruction_coordination_wait", "independent_qa_stop_instruction", "reviewer_stops_all_tool_calls", "reviewer_invoked_coordination_wait_after_stop_instruction", "process", "review_stop_boundary_mistake", "return_verdict_without_further_tool_calls_after_explicit_stop"),
        ("011", "owner_action_top_level_schema_mismatch", "owner_action_summary_projection", "v2_summary_and_manifest_validate", "unknown_top_level_field_blocked_summary_and_manifest_and_three_tests", "tooling", "v2_envelope_extension_assumption", "encode_owner_actions_as_allowed_public_safe_unknown_records"),
    )
    return [dict(zip(ANOMALY_HEADERS, (
        f"TASK058-PROCESS-ANOMALY-{n}", alias, trigger, expected, observed,
        "confirmed", "not_observed_runtime_blocked", level, cause, implication,
        "none",
    ))) for n, alias, trigger, expected, observed, level, cause, implication in values]


def cleanup_rows() -> list[dict[str, str]]:
    return [dict(zip(CLEANUP_HEADERS, (
        "task058-cleanup-001", "confirmed_removed", "install_success_package_present_equivalence_unverified",
        "not_run_security_block_runtime", "confirmed_no_capture_started", "0", "0",
        "confirmed", "blocked_by_tooling", "postaction_validation_incomplete_after_raw_spill", "blocks_release",
    )))]


def _empty_rows() -> list[dict[str, str]]:
    return []


def expected_bundle() -> dict[Path, bytes]:
    data = {
        LEDGERS["readiness"]: _csv_bytes(READINESS_HEADERS, readiness_rows()),
        LEDGERS["package_action"]: _csv_bytes(ACTION_HEADERS, action_rows()),
        LEDGERS["scenario"]: _csv_bytes(COMMON_HEADERS, scenario_rows()),
        LEDGERS["screen_state"]: _csv_bytes(COMMON_HEADERS, screen_state_rows()),
        LEDGERS["transition"]: _csv_bytes(TRANSITION_HEADERS, transition_rows()),
        LEDGERS["overlay_recurrence"]: _csv_bytes(COMMON_HEADERS, _empty_rows()),
        LEDGERS["anomaly"]: _csv_bytes(ANOMALY_HEADERS, anomaly_rows()),
        LEDGERS["boundary"]: _csv_bytes(COMMON_HEADERS, _empty_rows()),
        LEDGERS["cleanup"]: _csv_bytes(CLEANUP_HEADERS, cleanup_rows()),
    }
    data[REPORT_OUTPUT] = _json_bytes(build_summary(data))
    return data


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_summary(data: Mapping[Path, bytes]) -> dict[str, Any]:
    readiness = _parse_csv(data[LEDGERS["readiness"]], READINESS_HEADERS, "readiness")
    actions = _parse_csv(data[LEDGERS["package_action"]], ACTION_HEADERS, "package_action")
    scenarios = _parse_csv(data[LEDGERS["scenario"]], COMMON_HEADERS, "scenario")
    anomalies = _parse_csv(data[LEDGERS["anomaly"]], ANOMALY_HEADERS, "anomaly")
    action_counts = {row["action_alias"]: int(row["observed_count"]) for row in actions}
    artifacts = [
        {"kind": kind, "reference": path.relative_to(REPO_ROOT).as_posix(), "sha256": _sha(data[path]), "evidence_status": "confirmed"}
        for kind, path in LEDGERS.items()
    ]
    return {
        "artifacts": artifacts,
        "blocked_reasons": [
            "postinstall_equivalence_interrupted_by_raw_spill",
            "postaction_and_cleanup_selector_snapshots_not_completed",
            "synthetic_session_passport_absent",
            "clean_first_launch_fixture_passport_absent",
            "runtime_evidence_cleanup_passport_absent",
        ],
        "build_ref": {"alias": "task058-selected-phone-full-001"},
        "coverage_status": "blocked",
        "evidence_status": "confirmed",
        "execution_status": "blocked",
        "generated_at_utc": GENERATED_AT,
        "payload": {
            "anomaly_count": len(anomalies),
            "approved_reachable_scenario_count": sum(row["approved_scope"] == "true" and row["reachable"] == "true" for row in scenarios),
            "covered_scenario_count": sum(row["status"] == "covered" for row in scenarios),
            "blocked_scenario_count": sum(row["status"].startswith("blocked_by_") for row in scenarios),
            "readiness_row_count": len(readiness),
            "readiness_observed_pass_count": sum(row["terminal_status"] == "observed_pass" for row in readiness),
            "readiness_blocked_count": sum(row["terminal_status"].startswith("blocked_by_") for row in readiness),
            "security_gate": "BLOCK_RUNTIME",
            "go_runtime": False,
            "uninstall_count": action_counts["target_uninstall"],
            "target_absence_count": action_counts["target_absence"],
            "ordinary_install_count": action_counts["ordinary_install"],
            "retry_count": action_counts["retry"],
            "launch_count": action_counts["launch_navigation"],
            "navigation_count": 0,
            "postinstall_equivalence_confirmed": False,
            "unrelated_package_delta_confirmed": False,
            "runtime_checkpoint_count": 0,
            "runtime_screen_transition_count": 0,
            "local_temp_cleanup_confirmed": True,
        },
        "production_safety_classification": "PROD_CONDITIONAL_BOUNDED_PACKAGE_ACTION_BLOCKED_RUNTIME",
        "provenance": {
            "source": "sanitized_task058_orchestrator_projection",
            "local_only_input_read": True,
            "package_mutation_by_orchestrator": True,
            "runner_package_action": False,
            "runner_device_action": False,
            "product_launch": False,
            "product_navigation": False,
        },
        "release_effect": "blocks_release",
        "review": {
            "qa_reviewer_a": "pending_independent_review",
            "qa_reviewer_b": "pending_independent_review",
            "security_prod_safety_reviewer": "block_runtime",
            "docs_scribe": "pending_independent_review",
        },
        "risks": [
            {"id": "TASK058-RISK-FALSE-FIRST-LAUNCH", "evidence_status": "confirmed", "summary": "Package install success cannot substitute for independent runtime passports or fresh product coverage."},
            {"id": "TASK058-RISK-RAW-SPILL", "evidence_status": "confirmed", "summary": "A local command channel exposed a raw device-side path; the run stopped and no raw value entered tracked artifacts."},
        ],
        "run_id": RUN_ID,
        "schema_validation_status": "pass",
        "schema_version": SCHEMA_VERSION,
        "target_alias": "phone-current-001",
        "task_id": TASK_ID,
        "unknowns": [
            {"id": "task057-authority-02-installed-compatibility", "evidence_status": "unknown", "reason_code": "postinstall_equivalence_interrupted_by_raw_spill"},
            {"id": "task057-authority-03-current-phone-selector", "evidence_status": "unknown", "reason_code": "postaction_and_cleanup_selector_snapshots_not_completed"},
            {"id": "task057-authority-05-synthetic-session", "evidence_status": "unknown", "reason_code": "synthetic_session_passport_absent"},
            {"id": "task057-authority-06-clean-first-launch", "evidence_status": "unknown", "reason_code": "clean_first_launch_fixture_passport_absent"},
            {"id": "task057-authority-07-evidence-cleanup-security", "evidence_status": "unknown", "reason_code": "runtime_evidence_cleanup_passport_absent"},
            {"id": "task058-owner-action-01", "evidence_status": "unknown", "reason_code": "fresh_launch_free_postinstall_validation_authority_and_security_plan_required_without_reinstall"},
            {"id": "task058-owner-action-02", "evidence_status": "unknown", "reason_code": "three_runtime_passports_and_new_security_go_runtime_required"},
        ],
        "verification": [
            {"check": "exact_seven_readiness_rows", "status": "pass", "evidence_status": "confirmed", "result_count": 7},
            {"check": "package_action", "status": "blocked", "evidence_status": "confirmed", "result_count": 6},
            {"check": "task058_runtime", "status": "not_run", "evidence_status": "unknown", "result_count": 0},
            {"check": "terminal_scenario_ledger", "status": "blocked", "evidence_status": "confirmed", "result_count": 3},
        ],
    }


def _validate_rows(rows: Sequence[Mapping[str, str]], expected: Sequence[Mapping[str, str]], headers: Sequence[str], label: str) -> None:
    if list(rows) != list(expected):
        raise ContractError(f"{label}_semantic_drift")
    for index, row in enumerate(rows):
        if set(row) != set(headers):
            raise ContractError(f"{label}_fields_drift:{index}")
        for field, value in row.items():
            _safe(value, f"{label}:{index}:{field}")


def validate_bundle(bundle: Mapping[Path, bytes]) -> None:
    expected = expected_bundle()
    if set(bundle) != set(expected):
        raise ContractError("bundle_paths_drift")
    definitions = {
        "readiness": (READINESS_HEADERS, readiness_rows()),
        "package_action": (ACTION_HEADERS, action_rows()),
        "scenario": (COMMON_HEADERS, scenario_rows()),
        "screen_state": (COMMON_HEADERS, screen_state_rows()),
        "transition": (TRANSITION_HEADERS, transition_rows()),
        "overlay_recurrence": (COMMON_HEADERS, []),
        "anomaly": (ANOMALY_HEADERS, anomaly_rows()),
        "boundary": (COMMON_HEADERS, []),
        "cleanup": (CLEANUP_HEADERS, cleanup_rows()),
    }
    for label, path in LEDGERS.items():
        headers, rows = definitions[label]
        parsed = _parse_csv(bundle[path], headers, label)
        _validate_rows(parsed, rows, headers, label)
    try:
        summary = json.loads(bundle[REPORT_OUTPUT], object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("summary_json_invalid") from exc
    if summary != build_summary(bundle):
        raise ContractError("summary_semantic_or_hash_drift")
    errors = _validate_v2_envelope(summary, REPO_ROOT)
    if errors:
        raise ContractError("summary_schema_invalid:" + ",".join(errors))


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def validate_static_contract() -> None:
    if not TASK_SPEC.is_file() or TASK_SPEC.is_symlink():
        raise ContractError("task_spec_missing_or_link")
    text = TASK_SPEC.read_text(encoding="utf-8")
    for phrase in ("task058-selected-phone-full-001", "GO_RUNTIME", "TASK058-PROCESS-ANOMALY-004", "Retry count is zero"):
        if phrase not in text:
            raise ContractError("task_spec_contract_drift")


def disk_bundle() -> dict[Path, bytes]:
    result: dict[Path, bytes] = {}
    for path in (*LEDGERS.values(), REPORT_OUTPUT):
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"tracked_artifact_missing_or_link:{path.name}")
        result[path] = path.read_bytes()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--write-baseline", action="store_true")
    modes.add_argument("--validate-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        validate_static_contract()
        if args.write_baseline:
            for path, data in expected_bundle().items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        elif args.validate_report:
            validate_bundle(disk_bundle())
        else:
            validate_bundle(expected_bundle())
    except (ContractError, OSError, UnicodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print("PASS: TASK-058 public-safe blocked-runtime contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

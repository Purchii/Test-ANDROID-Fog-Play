"""TASK-057R fixed public-safe authorized-reinstall readiness authority.

The module is repository-only. It never reads ignored local evidence, APKs,
Android tooling, ADB, device/package state, credentials, or product screens.
It validates the sanitized tracked result produced by the bounded Orchestrator
workflow after the separately Security-reviewed device action.
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
except ModuleNotFoundError:  # Direct ``python automation/...py`` execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from automation.reporting.generate_report_manifest import _validate_v2_envelope


TASK_ID = "TASK-057R"
SCHEMA_VERSION = "evidence-report-envelope-v2"
PRODUCTION_SAFETY = "PROD_CONDITIONAL_AUTHORIZED_TARGET_REINSTALL"
GENERATED_AT = "2026-08-16T12:00:00Z"
RUN_ID = "task057r-authorized-reinstall-readiness-001"

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_SPEC = REPO_ROOT / "tasks/TASK_057R_phone_full_authorized_reinstall_readiness_revalidation.md"
REPORT_STEM = "task057r_phone_full_authorized_reinstall_readiness"
AUTHORITY_OUTPUT = REPO_ROOT / f"docs/qa/reports/{REPORT_STEM}.readiness-ledger.csv"
ACTION_OUTPUT = REPO_ROOT / f"docs/qa/reports/{REPORT_STEM}.reinstall-action-ledger.csv"
CLEANUP_OUTPUT = REPO_ROOT / f"docs/qa/reports/{REPORT_STEM}.cleanup-ledger.csv"
REPORT_OUTPUT = REPO_ROOT / f"docs/qa/reports/{REPORT_STEM}.summary.json"

AUTHORITY_HEADERS = (
    "authority_id",
    "subject_alias",
    "current_status",
    "freshness",
    "evidence_status",
    "evidence_ids",
    "reviewer_gate",
    "expires_at",
    "terminal_status",
    "release_effect",
    "reason_code",
)
ACTION_HEADERS = (
    "action_id",
    "action_alias",
    "phase_order",
    "phase",
    "intended_count",
    "observed_count",
    "current_status",
    "evidence_status",
    "evidence_ids",
    "terminal_status",
    "reason_code",
)
CLEANUP_HEADERS = (
    "cleanup_id",
    "current_status",
    "freshness",
    "evidence_status",
    "evidence_ids",
    "retention_redaction",
    "action_budget",
    "target_data_loss",
    "cleanup_rollback",
    "package_end_state",
    "unrelated_package_delta",
    "launch_navigation",
    "reinstall_kill_switch",
    "reinstall_failure_recovery",
    "reinstall_contingency_status",
    "runtime_kill_switch",
    "reviewer_gate",
    "terminal_status",
    "release_effect",
    "reason_code",
)

EXPECTED_AUTHORITY_IDS = (
    "task057-authority-01-canonical-phone-full",
    "task057-authority-02-installed-compatibility",
    "task057-authority-03-current-phone-selector",
    "task057-authority-04-downgrade-safety",
    "task057-authority-05-synthetic-session",
    "task057-authority-06-clean-first-launch",
    "task057-authority-07-evidence-cleanup-security",
)
EXPECTED_ACTION_IDS = (
    "task057r-action-01-target-map",
    "task057r-action-02-security-plan-go",
    "task057r-action-03-one-shot-contingency",
    "task057r-action-04-uninstall",
    "task057r-action-05-midstate-absence",
    "task057r-action-06-ordinary-install",
    "task057r-action-07-postinstall-equivalence",
    "task057r-action-08-unrelated-package-delta",
    "task057r-action-09-launch-navigation",
    "task057r-action-10-task058",
)

SAFE_SLUG_RE = re.compile(r"^[a-z0-9]+(?:[a-z0-9_-]*[a-z0-9])?$")
EVIDENCE_ID_RE = re.compile(r"^task057r-[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?$")
FORBIDDEN_PATTERNS = (
    re.compile(r"(?i)(?:^|[\s\"'])[a-z]:[\\/]"),
    re.compile(r"\\\\[^\\\s]+\\"),
    re.compile(r"(?i)\b(?:https?|wss?|file|intent|market|mailto):"),
    re.compile(r"(?<![\w-])(?:\d{1,3}\.){3}\d{1,3}(?![\w-])"),
    re.compile(r"(?i)(?:^|[\\/])\.qa_local(?:[\\/]|$)"),
    re.compile(r"(?i)\b(?:[a-z][a-z0-9_]*\.){2,}[a-z][a-z0-9_]*\b"),
    re.compile(r"(?i)\b[0-9a-f]{32,}\b"),
)


class ContractError(ValueError):
    """A public-safe TASK-057R contract failed closed."""


def _assert_public_safe(value: str, field: str) -> None:
    if "\r" in value or "\n" in value:
        raise ContractError(f"multiline_public_value:{field}")
    if any(pattern.search(value) for pattern in FORBIDDEN_PATTERNS):
        raise ContractError(f"unsafe_public_value:{field}")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ContractError(f"duplicate_json_key:{key}")
        value[key] = child
    return value


def _evidence_ids(value: str, *, allow_none: bool = False) -> tuple[str, ...]:
    if value == "none" and allow_none:
        return ()
    ids = tuple(value.split(";"))
    if not ids or len(ids) != len(set(ids)) or any(EVIDENCE_ID_RE.fullmatch(item) is None for item in ids):
        raise ContractError("evidence_ids_invalid")
    return ids


def _csv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _parse_csv(data: bytes, headers: Sequence[str], label: str) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(f"{label}_utf8_invalid") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != tuple(headers):
        raise ContractError(f"{label}_headers_drift")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ContractError(f"{label}_extra_cells")
    return rows


def authority_rows() -> list[dict[str, str]]:
    expiry = "2026-08-17T23:59:59Z"
    return [
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[0],
            "subject_alias": "main-apk-03",
            "current_status": "candidate_full_install_metadata_categories_confirmed",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057r-candidate-integrity;task057r-candidate-provenance;task057r-candidate-signing;task057r-candidate-version;task057r-candidate-min-sdk;task057r-candidate-target-sdk;task057r-candidate-abi;task057r-candidate-install-compatibility",
            "reviewer_gate": "GO_REINSTALL_CONDITIONAL",
            "expires_at": expiry,
            "terminal_status": "observed_pass",
            "release_effect": "candidate_evidence",
            "reason_code": "candidate_full_install_metadata_categories_confirmed",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[1],
            "subject_alias": "installed-phone-full-build",
            "current_status": "installed_candidate_exact_match",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057r-postinstall-equivalence;task057r-postinstall-metadata",
            "reviewer_gate": "GO_REINSTALL_CONDITIONAL",
            "expires_at": expiry,
            "terminal_status": "observed_pass",
            "release_effect": "candidate_evidence",
            "reason_code": "installed_candidate_exact_match",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[2],
            "subject_alias": "phone-current-001",
            "current_status": "current_phone_mapped_authorized_unchanged",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057r-device-snapshot-open;task057r-device-snapshot-confirm;task057r-device-snapshot-cleanup",
            "reviewer_gate": "GO_REINSTALL_CONDITIONAL",
            "expires_at": expiry,
            "terminal_status": "observed_pass",
            "release_effect": "candidate_evidence",
            "reason_code": "current_phone_mapped_authorized_unchanged",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[3],
            "subject_alias": "ordinary-downgrade-guard",
            "current_status": "authorized_reinstall_no_downgrade_bypass",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057r-reinstall-action-ledger;task057r-no-bypass-policy",
            "reviewer_gate": "GO_REINSTALL_CONDITIONAL",
            "expires_at": expiry,
            "terminal_status": "observed_pass",
            "release_effect": "candidate_evidence",
            "reason_code": "authorized_reinstall_no_downgrade_bypass",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[4],
            "subject_alias": "synthetic-session-passport",
            "current_status": "synthetic_session_passport_absent",
            "freshness": "fresh_current_run",
            "evidence_status": "unknown",
            "evidence_ids": "none",
            "reviewer_gate": "BLOCK_RUNTIME",
            "expires_at": "not_set",
            "terminal_status": "blocked_by_fixture",
            "release_effect": "blocks_release",
            "reason_code": "synthetic_session_passport_absent",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[5],
            "subject_alias": "clean-first-launch-fixture",
            "current_status": "clean_first_launch_fixture_passport_absent",
            "freshness": "fresh_current_run",
            "evidence_status": "unknown",
            "evidence_ids": "none",
            "reviewer_gate": "BLOCK_RUNTIME",
            "expires_at": "not_set",
            "terminal_status": "blocked_by_fixture",
            "release_effect": "blocks_release",
            "reason_code": "reinstall_success_does_not_establish_clean_first_launch_fixture",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[6],
            "subject_alias": "evidence-cleanup-passport",
            "current_status": "runtime_evidence_cleanup_passport_absent",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057r-reinstall-action-ledger;task057r-device-snapshot-cleanup",
            "reviewer_gate": "BLOCK_RUNTIME",
            "expires_at": "not_set",
            "terminal_status": "blocked_by_fixture",
            "release_effect": "blocks_release",
            "reason_code": "runtime_passport_budget_kill_switch_cleanup_security_absent",
        },
    ]


def action_rows() -> list[dict[str, str]]:
    values = (
        ("target-map", "10", "pre-action", "1", "1", "exact_target_and_candidate_mapped", "task057r-selector-artifact-map"),
        ("security-plan-go", "20", "pre-action", "1", "1", "security_plan_go_confirmed_before_uninstall", "task057r-security-plan-go"),
        ("one-shot-contingency", "30", "pre-action", "1", "1", "stop_no_retry_contingency_confirmed", "task057r-one-shot-contingency"),
        ("uninstall", "40", "package-mutation", "1", "1", "authorized_target_uninstall_observed", "task057r-uninstall-observation"),
        ("midstate-absence", "50", "package-mutation", "1", "1", "target_absent_after_uninstall", "task057r-midstate-absence"),
        ("ordinary-install", "60", "package-mutation", "1", "1", "selected_candidate_ordinary_install_observed", "task057r-install-observation"),
        ("postinstall-equivalence", "70", "post-action-validation", "1", "1", "installed_candidate_exact_equivalence", "task057r-postinstall-equivalence"),
        ("unrelated-package-delta", "80", "post-action-validation", "0", "0", "unrelated_package_delta_zero", "task057r-unrelated-delta-check"),
        ("launch-navigation", "90", "scope-closure", "0", "0", "launch_navigation_not_executed", "task057r-zero-launch-navigation"),
        ("task058", "100", "scope-closure", "0", "0", "task058_not_executed", "task057r-zero-task058"),
    )
    rows = []
    for index, (alias, phase_order, phase, intended, observed, status, evidence_id) in enumerate(values, start=1):
        rows.append(
            {
                "action_id": EXPECTED_ACTION_IDS[index - 1],
                "action_alias": alias,
                "phase_order": phase_order,
                "phase": phase,
                "intended_count": intended,
                "observed_count": observed,
                "current_status": status,
                "evidence_status": "confirmed",
                "evidence_ids": evidence_id,
                "terminal_status": "observed_pass",
                "reason_code": status,
            }
        )
    return rows


def cleanup_rows() -> list[dict[str, str]]:
    return [
        {
            "cleanup_id": "task057r-cleanup-passport",
            "current_status": "intended_target_mutation_complete_runtime_passport_absent",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057r-reinstall-action-ledger;task057r-device-snapshot-cleanup;task057r-unrelated-delta-check",
            "retention_redaction": "confirmed_local_only_redacted_public",
            "action_budget": "one_uninstall_one_ordinary_install",
            "target_data_loss": "owner_authorized_accepted_not_restored",
            "cleanup_rollback": "not_claimed_for_accepted_target_data_loss",
            "package_end_state": "selected_candidate_installed_exact",
            "unrelated_package_delta": "confirmed_zero",
            "launch_navigation": "confirmed_zero",
            "reinstall_kill_switch": "confirmed_stop_no_retry_on_drift_or_failure",
            "reinstall_failure_recovery": "requires_new_owner_authority_after_uninstall_or_install_failure",
            "reinstall_contingency_status": "confirmed_unused",
            "runtime_kill_switch": "absent",
            "reviewer_gate": "BLOCK_RUNTIME",
            "terminal_status": "blocked_by_fixture",
            "release_effect": "blocks_release",
            "reason_code": "runtime_passport_budget_kill_switch_cleanup_security_absent",
        }
    ]


def _validate_rows(
    rows: Sequence[Mapping[str, str]],
    expected: Sequence[Mapping[str, str]],
    headers: Sequence[str],
    label: str,
) -> None:
    if list(rows) != list(expected):
        raise ContractError(f"{label}_semantic_drift")
    for row_index, row in enumerate(rows):
        for field in headers:
            value = row.get(field)
            if not isinstance(value, str) or not value:
                raise ContractError(f"{label}_field_missing:{row_index}:{field}")
            _assert_public_safe(value, f"{label}:{row_index}:{field}")
            if field == "evidence_ids":
                _evidence_ids(value, allow_none=True)
        for field, value in row.items():
            if field not in headers:
                raise ContractError(f"{label}_unknown_field:{field}")
            if field not in {
                "authority_id",
                "action_id",
                "cleanup_id",
                "evidence_ids",
                "expires_at",
                "reviewer_gate",
            }:
                if field not in {"intended_count", "observed_count"} and SAFE_SLUG_RE.fullmatch(value) is None:
                    raise ContractError(f"{label}_slug_invalid:{field}")


def validate_authority_rows(rows: Sequence[Mapping[str, str]]) -> None:
    if [row.get("authority_id") for row in rows] != list(EXPECTED_AUTHORITY_IDS):
        raise ContractError("authority_requires_exact_task057_seven_rows")
    _validate_rows(rows, authority_rows(), AUTHORITY_HEADERS, "authority")


def validate_action_rows(rows: Sequence[Mapping[str, str]]) -> None:
    if [row.get("action_id") for row in rows] != list(EXPECTED_ACTION_IDS):
        raise ContractError("action_ledger_missing_duplicate_or_reordered")
    _validate_rows(rows, action_rows(), ACTION_HEADERS, "action")


def validate_cleanup_rows(rows: Sequence[Mapping[str, str]]) -> None:
    if len(rows) != 1 or rows[0].get("cleanup_id") != "task057r-cleanup-passport":
        raise ContractError("cleanup_requires_one_exact_row")
    _validate_rows(rows, cleanup_rows(), CLEANUP_HEADERS, "cleanup")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _anomalies() -> list[dict[str, str]]:
    return [
        {
            "id": "TASK057R-PROCESS-ANOMALY-001",
            "alias": "same_repository_common_dir_path_normalization_failure",
            "evidence_status": "confirmed",
            "phase": "before_mutation",
            "expected": "same_repository_provenance_normalized",
            "observed": "rooted_reference_join_failed_closed",
            "cause": "rooted_and_relative_reference_handling_error",
            "test_implication": "normalize_each_reference_by_rootedness_before_comparison",
            "product_impact": "none",
        },
        {
            "id": "TASK057R-PROCESS-ANOMALY-002",
            "alias": "powershell_line_selection_expression_errors",
            "evidence_status": "confirmed",
            "phase": "before_mutation",
            "expected": "bounded_public_safe_line_projection",
            "observed": "expression_failed_closed_without_evidence_acceptance",
            "cause": "powershell_expression_compatibility_error",
            "test_implication": "validate_bounded_expression_before_action_and_accept_no_failed_output",
            "product_impact": "none",
        },
        {
            "id": "TASK057R-PROCESS-ANOMALY-003",
            "alias": "split_package_false_ambiguity",
            "evidence_status": "confirmed",
            "phase": "before_mutation",
            "expected": "exact_target_package_shape_classified",
            "observed": "permitted_split_shape_was_initially_ambiguous",
            "cause": "split_package_classifier_false_positive",
            "test_implication": "use_exact_mapping_and_category_only_split_aware_classifier",
            "product_impact": "none",
        },
        {
            "id": "TASK057R-PROCESS-ANOMALY-004",
            "alias": "reviewer_gate_uppercase_slug_validation_mismatch",
            "evidence_status": "confirmed",
            "phase": "repository_validation_after_device_action",
            "expected": "focused_contract_suite_passes",
            "observed": "valid_uppercase_reviewer_gate_was_rejected",
            "cause": "generic_lowercase_slug_check_applied_to_reviewer_gate_enum",
            "test_implication": "validate_reviewer_gate_as_exact_enum_not_generic_slug",
            "product_impact": "none",
        },
    ]


def build_summary(authority_data: bytes, action_data: bytes, cleanup_data: bytes) -> dict[str, Any]:
    authorities = _parse_csv(authority_data, AUTHORITY_HEADERS, "authority")
    actions = _parse_csv(action_data, ACTION_HEADERS, "action")
    cleanup = _parse_csv(cleanup_data, CLEANUP_HEADERS, "cleanup")
    validate_authority_rows(authorities)
    validate_action_rows(actions)
    validate_cleanup_rows(cleanup)
    return {
        "artifacts": [
            {
                "evidence_status": "confirmed",
                "kind": "readiness_ledger",
                "reference": f"docs/qa/reports/{REPORT_STEM}.readiness-ledger.csv",
                "sha256": _sha256(authority_data),
            },
            {
                "evidence_status": "confirmed",
                "kind": "reinstall_action_ledger",
                "reference": f"docs/qa/reports/{REPORT_STEM}.reinstall-action-ledger.csv",
                "sha256": _sha256(action_data),
            },
            {
                "evidence_status": "confirmed",
                "kind": "cleanup_ledger",
                "reference": f"docs/qa/reports/{REPORT_STEM}.cleanup-ledger.csv",
                "sha256": _sha256(cleanup_data),
            },
        ],
        "blocked_reasons": [
            "runtime_passport_budget_kill_switch_cleanup_security_absent",
            "synthetic_session_passport_absent",
            "reinstall_success_does_not_establish_clean_first_launch_fixture",
        ],
        "build_ref": {"alias": "main-apk-03"},
        "coverage_status": "blocked",
        "evidence_status": "confirmed",
        "execution_status": "blocked",
        "generated_at_utc": GENERATED_AT,
        "payload": {
            "readiness_authority_row_count": 7,
            "readiness_observed_pass_count": 4,
            "readiness_blocked_count": 3,
            "readiness_decision": "BLOCK_RUNTIME",
            "security_gate": "BLOCK_RUNTIME",
            "go_runtime": False,
            "bounded_reinstall_status": "observed_pass",
            "security_plan_go_pre_action": True,
            "security_plan_go_phase_order": 20,
            "uninstall_phase_order": 40,
            "reinstall_kill_switch": "confirmed_stop_no_retry_on_drift_or_failure",
            "reinstall_failure_recovery": "requires_new_owner_authority_after_uninstall_or_install_failure",
            "reinstall_contingency_status": "confirmed_unused",
            "uninstall_count": 1,
            "ordinary_install_count": 1,
            "target_absent_mid_reinstall": True,
            "postinstall_candidate_exact_equivalence": True,
            "unrelated_package_delta_count": 0,
            "app_launch_count": 0,
            "product_navigation_action_count": 0,
            "task058_action_count": 0,
            "owner_authorized_target_data_loss": True,
            "target_data_restored": False,
            "runtime_passport_established": False,
            "anomalies": _anomalies(),
        },
        "production_safety_classification": PRODUCTION_SAFETY,
        "provenance": {
            "source": "sanitized_task057r_action_and_readiness_ledgers",
            "local_only_input_read": True,
            "adb_or_device_action_by_orchestrator": True,
            "package_mutation_by_orchestrator": True,
            "runner_device_action": False,
            "runner_package_action": False,
            "product_navigation": False,
            "task058_executed": False,
        },
        "release_effect": "blocks_release",
        "review": {
            "qa_reviewer_a": "pending_independent_review",
            "qa_reviewer_b": "pending_independent_review",
            "security_prod_safety_reviewer": "block_runtime",
            "docs_scribe": "pending_independent_review",
        },
        "risks": [
            {
                "id": "TASK057R-RISK-INSTALL-FALSE-GO",
                "evidence_status": "confirmed",
                "summary": "Successful reinstall cannot infer any independent fixture, cleanup passport, runtime budget, kill switch, rollback, or Security GO_RUNTIME row.",
            },
            {
                "id": "TASK057R-RISK-AUTHORIZED-DATA-LOSS",
                "evidence_status": "confirmed",
                "summary": "Target local data loss was owner-authorized and accepted; restoration or rollback of that data is not claimed.",
            },
        ],
        "run_id": RUN_ID,
        "schema_validation_status": "pass",
        "schema_version": SCHEMA_VERSION,
        "target_alias": "phone-current-001",
        "task_id": TASK_ID,
        "unknowns": [
            {
                "id": EXPECTED_AUTHORITY_IDS[4],
                "evidence_status": "unknown",
                "reason_code": "synthetic_session_passport_absent",
            },
            {
                "id": EXPECTED_AUTHORITY_IDS[5],
                "evidence_status": "unknown",
                "reason_code": "reinstall_success_does_not_establish_clean_first_launch_fixture",
            },
            {
                "id": EXPECTED_AUTHORITY_IDS[6],
                "evidence_status": "confirmed",
                "reason_code": "runtime_passport_budget_kill_switch_cleanup_security_absent",
            },
        ],
        "verification": [
            {"check": "exact_task057_seven_rows", "status": "pass", "evidence_status": "confirmed", "result_count": 7},
            {"check": "bounded_reinstall", "status": "pass", "evidence_status": "confirmed", "result_count": 1},
            {"check": "readiness_authority", "status": "blocked", "evidence_status": "confirmed", "result_count": 4},
            {"check": "product_navigation", "status": "not_run", "evidence_status": "unknown", "result_count": 0},
            {"check": "task058", "status": "not_run", "evidence_status": "unknown", "result_count": 0},
        ],
    }


def build_bundle() -> dict[Path, bytes]:
    authority = _csv_bytes(AUTHORITY_HEADERS, authority_rows())
    action = _csv_bytes(ACTION_HEADERS, action_rows())
    cleanup = _csv_bytes(CLEANUP_HEADERS, cleanup_rows())
    summary = _json_bytes(build_summary(authority, action, cleanup))
    return {
        AUTHORITY_OUTPUT: authority,
        ACTION_OUTPUT: action,
        CLEANUP_OUTPUT: cleanup,
        REPORT_OUTPUT: summary,
    }


def validate_bundle(bundle: Mapping[Path, bytes], *, validate_disk_schema: bool = False) -> None:
    required = {AUTHORITY_OUTPUT, ACTION_OUTPUT, CLEANUP_OUTPUT, REPORT_OUTPUT}
    if set(bundle) != required:
        raise ContractError("report_bundle_path_set_drift")
    try:
        summary = json.loads(bundle[REPORT_OUTPUT].decode("utf-8"), object_pairs_hook=_reject_duplicate_json_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("summary_json_invalid") from exc
    expected = build_summary(bundle[AUTHORITY_OUTPUT], bundle[ACTION_OUTPUT], bundle[CLEANUP_OUTPUT])
    if summary != expected:
        raise ContractError("summary_semantic_or_hash_drift")
    if validate_disk_schema:
        errors = _validate_v2_envelope(summary, REPO_ROOT)
        if errors:
            raise ContractError("summary_v2_invalid:" + ",".join(errors))


def validate_static_contracts() -> None:
    if not TASK_SPEC.is_file() or TASK_SPEC.is_symlink():
        raise ContractError("task_spec_missing_or_link")
    text = TASK_SPEC.read_text(encoding="utf-8")
    for phrase in (
        "exact seven",
        "main-apk-03",
        "successful reinstall",
        "BLOCK_RUNTIME",
        "TASK-058",
        "not restored",
    ):
        if phrase not in text:
            raise ContractError("task_spec_required_contract_drift")


def _disk_bundle() -> dict[Path, bytes]:
    result: dict[Path, bytes] = {}
    for path in (AUTHORITY_OUTPUT, ACTION_OUTPUT, CLEANUP_OUTPUT, REPORT_OUTPUT):
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
        validate_static_contracts()
        if args.write_baseline:
            for path, data in build_bundle().items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        elif args.validate_report:
            validate_bundle(_disk_bundle(), validate_disk_schema=True)
        else:
            validate_bundle(build_bundle())
    except (ContractError, OSError, UnicodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print("PASS: TASK-057R public-safe authorized reinstall readiness contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

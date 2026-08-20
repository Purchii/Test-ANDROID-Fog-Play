"""Fail-closed controller contract for EPIC-PHONE-001 runtime contours.

The default modes are repository-only and side-effect free.  ``--dry-run``
and ``--validate-only`` do not inspect ignored storage, environment variables,
devices, credentials or networks and never start a subprocess.  The future
``--preflight-c1`` mode can validate only the fixed local authority artifacts;
it cannot execute C1, launch the application, access fixture values or issue a
Security GO.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence


EPIC_ID = "EPIC-PHONE-001"
RUN_ID = "epic-phone-001-20260816-r01"
CONTOUR_ID = "epic-phone-001-c1-launch-free-readiness"
C0P_CONTOUR_ID = "epic-phone-001-c0p-local-presence"
AUTHORITY_SET_ID = "c0p-authority-005"
AUTHORITY_RENEWAL_ID = "authority-renewal-003"
C0P_PREP_ATTEMPT_ID = "c0p-prep-005"
TARGET_ALIAS = "phone-current-001"
BUILD_ALIAS = "task058-selected-phone-full-001"
FIXTURE_ALIAS = "epic-phone-001-fixture-001"
FIXTURE_PASSPORT_ALIAS = "epic-phone-001-fixture-authority-005"
TARGET_BUILD_PASSPORT_ALIAS = "epic-phone-001-target-build-005"
EVIDENCE_CLEANUP_PASSPORT_ALIAS = "epic-phone-001-evidence-cleanup-005"
C0P_SECURITY_ALIAS = "epic-phone-001-security-c0p-005"
C1_SECURITY_ALIAS = "epic-phone-001-security-c1-001"

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT_REL = Path(".qa_local/evidence/epic-phone-001") / RUN_ID
AUTHORITY_SET_ROOT_REL = RUN_ROOT_REL / "authority-sets/c0p-authority-005"
SECRET_SOURCE_REL = Path(".qa_local/secrets/qa_user.env")
SERIAL_ALIAS_MAP_REL = Path(".qa_local/devices/serial_alias_map.json")
PLAN_REL = RUN_ROOT_REL / "controller-plan.local.json"
C0P_PLAN_REL = AUTHORITY_SET_ROOT_REL / "c0p-plan.local.json"
FIXTURE_PASSPORT_REL = AUTHORITY_SET_ROOT_REL / "fixture-authority-passport.local.json"
TARGET_BUILD_PASSPORT_REL = AUTHORITY_SET_ROOT_REL / "target-build-passport.local.json"
EVIDENCE_CLEANUP_PASSPORT_REL = AUTHORITY_SET_ROOT_REL / "evidence-cleanup-passport.local.json"
SECURITY_GO_C1_REL = RUN_ROOT_REL / "security-go-c1.local.json"
SECURITY_GO_C0P_REL = RUN_ROOT_REL / "security-go-c0p-005.local.json"
RAW_REL = RUN_ROOT_REL / "raw"
CHECKPOINTS_REL = RUN_ROOT_REL / "checkpoints"
PUBLIC_SAFE_REL = RUN_ROOT_REL / "public-safe"
C0P_RESULT_REL = PUBLIC_SAFE_REL / "c0p-005-result.local.json"
C0P_ATTEMPT_REL = RUN_ROOT_REL / "c0p-005-attempt.local.json"

PLAN_SCHEMA = "epic-phone-001-controller-plan-v1"
FIXTURE_PASSPORT_SCHEMA = "epic-phone-001-fixture-authority-passport-v2"
TARGET_BUILD_PASSPORT_SCHEMA = "epic-phone-001-target-build-passport-v2"
EVIDENCE_CLEANUP_PASSPORT_SCHEMA = "epic-phone-001-evidence-cleanup-passport-v2"
SECURITY_GO_SCHEMA = "epic-phone-001-security-go-c1-v1"
C0P_SECURITY_GO_SCHEMA = "epic-phone-001-security-go-c0p-v1"
C0P_RESULT_SCHEMA = "epic-phone-001-c0p-result-v1"
C0P_ATTEMPT_SCHEMA = "epic-phone-001-c0p-attempt-v1"
PLAN_HASH_RE = "64_lowercase_hex"
GO_PREFIX = f"GO_EPIC_PHONE_001_C1_LAUNCH_FREE_READINESS__{RUN_ID}__"
C0P_GO_PREFIX = f"GO_EPIC_PHONE_001_C0P_LOCAL_PRESENCE__{RUN_ID}__"
C0P_MAX_SECRET_BYTES = 8 * 1024
C0P_MAX_VALIDITY_MINUTES = 30
C0P_BUDGET = {
    "secret_source_read_max": 1,
    "retry_max": 0,
    "wall_clock_minutes_max": 30,
    "secret_source_bytes_max": C0P_MAX_SECRET_BYTES,
    "device_action_max": 0,
    "subprocess_max": 0,
    "network_action_max": 0,
    "application_launch_max": 0,
    "ui_action_max": 0,
    "authentication_action_max": 0,
    "mutation_max": 0,
}
_C0P_PHONE_FIELD = "EPIC_PHONE_001_PHONE_SUFFIX"
_C0P_OTP_FIELD = "EPIC_PHONE_001_OTP"
_C0P_PHONE_PATTERN = re.compile(r"^[0-9]{10}$", re.ASCII)
_C0P_OTP_PATTERN = re.compile(r"^[0-9]{4,8}$", re.ASCII)

C1_BUDGET = {
    "controller_external_exec_max": 1,
    "retry_max": 0,
    "wall_clock_minutes_max": 10,
    "command_timeout_seconds": 20,
    "application_launch_max": 0,
    "ui_action_max": 0,
    "authentication_action_max": 0,
    "credential_read_or_entry_max": 0,
    "mutation_max": 0,
    "selector_snapshot_max": 3,
    "target_only_read_only_metadata_query_max": 8,
    "raw_sink_hard_bytes_max": 64 * 1024 * 1024,
    "raw_sink_soft_bytes_max": 48 * 1024 * 1024,
}
GLOBAL_BUDGET = {
    "concurrency_max": 1,
    "state_changing_action_max": 340,
    "checkpoint_triplet_max": 349,
    "launch_or_relaunch_max": 8,
    "runtime_minutes_max": 180,
    "local_only_qr_decode_max": 20,
    "raw_sink_bytes_max": 1024 * 1024 * 1024,
}

FORBIDDEN_ACTIONS = (
    "application_launch",
    "ui_input",
    "authentication_or_credential_entry",
    "fixture_value_read",
    "payment_or_paid_session",
    "account_profile_subscription_or_entitlement_mutation",
    "external_browser_or_qr_traversal",
    "network_shaping_or_load",
    "apk_install_reinstall_clear_reset_patch_or_bypass",
    "destructive_device_action",
    "secret_or_raw_endpoint_extraction",
)


class ContractError(ValueError):
    """The fixed controller contract failed closed."""


def _exact_equal(value: Any, expected: Any) -> bool:
    """Compare JSON-shaped values without Python's ``True == 1`` coercion."""

    if type(value) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(value) == set(expected) and all(
            _exact_equal(value[key], expected[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(value) == len(expected) and all(
            _exact_equal(actual_item, expected_item)
            for actual_item, expected_item in zip(value, expected)
        )
    return value == expected


def _nfc(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, tuple):
        return [_nfc(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            if not isinstance(raw_key, str):
                raise ContractError("canonical_json_key_not_string")
            key = unicodedata.normalize("NFC", raw_key)
            if key in normalized:
                raise ContractError("canonical_json_duplicate_nfc_key")
            normalized[key] = _nfc(raw_value)
        return normalized
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float):
            raise ContractError("canonical_json_float_forbidden")
        return value
    raise ContractError("canonical_json_unsupported_type")


def canonical_plan_bytes(plan: Mapping[str, Any]) -> bytes:
    """Return deterministic UTF-8 NFC/sorted/minified JSON for plan hashing."""

    return json.dumps(
        _nfc(dict(plan)),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def plan_sha256(plan: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_plan_bytes(plan)).hexdigest()


def expected_go_token(plan_hash: str) -> str:
    if len(plan_hash) != 64 or any(char not in "0123456789abcdef" for char in plan_hash):
        raise ContractError("plan_hash_not_64_lowercase_hex")
    return GO_PREFIX + plan_hash


def expected_c0p_go_token(c0p_plan_hash: str) -> str:
    if len(c0p_plan_hash) != 64 or any(char not in "0123456789abcdef" for char in c0p_plan_hash):
        raise ContractError("c0p_plan_hash_not_64_lowercase_hex")
    return C0P_GO_PREFIX + c0p_plan_hash


def c0p_plan(repository_head: str, controller_source_sha256: str, issued_at_utc: str, expires_at_utc: str) -> dict[str, Any]:
    """Build a C0P plan bound to Security-attested repository/source state."""

    if len(repository_head) != 40 or any(char not in "0123456789abcdef" for char in repository_head):
        raise ContractError("c0p_repository_head_not_40_lowercase_hex")
    if len(controller_source_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in controller_source_sha256
    ):
        raise ContractError("c0p_controller_source_sha256_not_64_lowercase_hex")

    return {
        "schema_version": "epic-phone-001-c0p-plan-v2",
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "authority_set_id": AUTHORITY_SET_ID,
        "renewal_id": AUTHORITY_RENEWAL_ID,
        "prep_attempt_id": C0P_PREP_ATTEMPT_ID,
        "issued_at_utc": issued_at_utc,
        "expires_at_utc": expires_at_utc,
        "contour_id": C0P_CONTOUR_ID,
        "classification": "PROD_CONDITIONAL",
        "execution_status": "planned_separate_literal_go_required_not_run",
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "passport_aliases": {
            "fixture_authority": FIXTURE_PASSPORT_ALIAS,
            "target_build": TARGET_BUILD_PASSPORT_ALIAS,
            "evidence_cleanup": EVIDENCE_CLEANUP_PASSPORT_ALIAS,
        },
        "security_alias": C0P_SECURITY_ALIAS,
        "repository_head": repository_head,
        "controller_source_sha256": controller_source_sha256,
        "fixed_plan_path": C0P_PLAN_REL.as_posix(),
        "fixed_token_path": SECURITY_GO_C0P_REL.as_posix(),
        "fixed_secret_source": SECRET_SOURCE_REL.as_posix(),
        "fixed_result_path": C0P_RESULT_REL.as_posix(),
        "fixed_attempt_marker_path": C0P_ATTEMPT_REL.as_posix(),
        "attempt_marker_schema": C0P_ATTEMPT_SCHEMA,
        "public_result_allowlist": [
            "required_field_count",
            "required_fields_present",
            "unexpected_fields_absent",
            "phone_format_policy_pass",
            "otp_format_policy_pass",
        ],
        "value_handling": {
            "read_only_for_nonempty_presence_in_authorized_adapter": True,
            "print": False,
            "record": False,
            "hash": False,
            "length": False,
            "value_comparison": False,
        },
        "security_token_format": C0P_GO_PREFIX + f"<{PLAN_HASH_RE}>",
        "security_token_must_bind": [
            "epic_id",
            "run_id",
            "contour_id",
            "target_alias",
            "build_alias",
            "fixture_alias",
            "passport_aliases",
            "passport_sha256",
            "passport_expires_at_utc",
            "security_alias",
            "c0p_plan_sha256",
            "repository_head",
            "controller_source_sha256",
            "issued_at_utc",
            "expires_at_utc",
            "result_path",
            "attempt_marker_path",
            "attempt_marker_schema",
            "budget",
        ],
        "c1_token_cannot_authorize": True,
        "controller_execution_interface_present": True,
        "budget": dict(C0P_BUDGET),
    }


def c0p_plan_contract() -> dict[str, Any]:
    """Public dry-run contract without pretending a local plan was created."""

    return {
        "schema_version": "epic-phone-001-c0p-plan-contract-v1",
        "contour_id": C0P_CONTOUR_ID,
        "fixed_plan_path": C0P_PLAN_REL.as_posix(),
        "fixed_token_path": SECURITY_GO_C0P_REL.as_posix(),
        "fixed_result_path": C0P_RESULT_REL.as_posix(),
        "fixed_attempt_marker_path": C0P_ATTEMPT_REL.as_posix(),
        "attempt_marker_schema": C0P_ATTEMPT_SCHEMA,
        "repository_head_required": "40_lowercase_hex_security_attested",
        "controller_source_sha256_required": "64_lowercase_hex_independently_verified",
        "literal_token_format": C0P_GO_PREFIX + f"<{PLAN_HASH_RE}>",
        "public_result_allowlist": [
            "required_field_count",
            "required_fields_present",
            "unexpected_fields_absent",
            "phone_format_policy_pass",
            "otp_format_policy_pass",
        ],
        "budget": dict(C0P_BUDGET),
        "status": "not_run_distinct_literal_go_required",
    }


def controller_plan() -> dict[str, Any]:
    """Build the immutable public-safe plan; this function performs no I/O."""

    return {
        "schema_version": PLAN_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "classification": "PROD_CONDITIONAL",
        "execution_status": "planned_not_authorized_not_run",
        "aliases": {
            "target": TARGET_ALIAS,
            "build": BUILD_ALIAS,
            "fixture": FIXTURE_ALIAS,
        },
        "fixed_ignored_paths": {
            "run_root": RUN_ROOT_REL.as_posix(),
            "secret_source": SECRET_SOURCE_REL.as_posix(),
            "serial_alias_map": SERIAL_ALIAS_MAP_REL.as_posix(),
            "controller_plan": PLAN_REL.as_posix(),
            "c0p_plan": C0P_PLAN_REL.as_posix(),
            "fixture_authority_passport": FIXTURE_PASSPORT_REL.as_posix(),
            "target_build_passport": TARGET_BUILD_PASSPORT_REL.as_posix(),
            "evidence_cleanup_passport": EVIDENCE_CLEANUP_PASSPORT_REL.as_posix(),
            "security_go_c1": SECURITY_GO_C1_REL.as_posix(),
            "security_go_c0p": SECURITY_GO_C0P_REL.as_posix(),
            "raw": RAW_REL.as_posix(),
            "checkpoints": CHECKPOINTS_REL.as_posix(),
            "public_safe": PUBLIC_SAFE_REL.as_posix(),
            "c0p_result": C0P_RESULT_REL.as_posix(),
            "c0p_attempt": C0P_ATTEMPT_REL.as_posix(),
        },
        "owner_authority": {
            "evidence_status": "confirmed",
            "authority_source_alias": "owner-confirmation-20260816-epic-phone-001-fixture-001",
            "synthetic_test_only": True,
            "not_real_user": True,
            "approved_for_current_app_environment_and_authorized_phone": True,
            "billing_payment_subscription_entitlement_impact_allowed": False,
            "validity": "current_epic_run_until_completion_or_revocation",
            "allowed_mutations": ["synthetic_session_create", "safe_logout"],
            "allowed_observation": "read_only_navigation",
            "forbidden_mutations": [
                "payment",
                "subscription",
                "entitlement",
                "profile",
                "account",
                "paid_session",
            ],
            "external_or_qr_traversal_allowed": False,
            "values_local_only_and_redacted": True,
            "constant_otp_value_recorded": False,
        },
        "fixture_presence_contract": {
            "c1_status": "not_checked",
            "public_result_fields": [
                "required_field_count",
                "required_fields_present",
                "unexpected_fields_absent",
                "phone_format_policy_pass",
                "otp_format_policy_pass",
            ],
            "c1_never_reads_fixture_values": True,
            "all_modes_never_print_hash_record_or_expose_fixture_values_or_lengths": True,
            "c0p_may_read_internally_only_after_its_distinct_literal_go": True,
            "secret_source": SECRET_SOURCE_REL.as_posix(),
            "requires_distinct_c0p_literal_security_token": True,
            "c1_token_cannot_authorize_c0p": True,
            "c0p_contour_id": C0P_CONTOUR_ID,
            "c0p_security_alias": C0P_SECURITY_ALIAS,
            "c0p_plan_sha256": "computed_only_from_fixed_local_bound_plan",
            "c0p_token_format": C0P_GO_PREFIX + f"<{PLAN_HASH_RE}>",
            "controller_has_guarded_c0p_execution_interface": True,
        },
        "passport_contract": {
            "fixture_authority": {
                "schema": FIXTURE_PASSPORT_SCHEMA,
                "alias": FIXTURE_PASSPORT_ALIAS,
                "path": FIXTURE_PASSPORT_REL.as_posix(),
            },
            "target_build": {
                "schema": TARGET_BUILD_PASSPORT_SCHEMA,
                "alias": TARGET_BUILD_PASSPORT_ALIAS,
                "path": TARGET_BUILD_PASSPORT_REL.as_posix(),
            },
            "evidence_cleanup": {
                "schema": EVIDENCE_CLEANUP_PASSPORT_SCHEMA,
                "alias": EVIDENCE_CLEANUP_PASSPORT_ALIAS,
                "path": EVIDENCE_CLEANUP_PASSPORT_REL.as_posix(),
            },
            "security_token_must_bind_sha256_and_expiry_for_all_passports": True,
        },
        "budget": dict(C1_BUDGET),
        "checkpoint_contract": {
            "C1-000": {
                "semantics": "mandatory_pre_execution_gate",
                "must_exist_before_the_single_external_executor_call": True,
                "records": [
                    "plan_hash",
                    "passport_hashes",
                    "security_token_hash_binding",
                    "remaining_budget",
                    "zero_runtime_action_counters",
                ],
                "cannot_claim_device_observation": True,
            },
            "C1-999": {
                "semantics": "mandatory_terminal_checkpoint",
                "must_be_recorded_after_success_failure_timeout_or_kill_switch": True,
                "records": [
                    "actual_budget",
                    "terminal_status",
                    "anomaly_ids",
                    "cleanup_status",
                    "capture_shutdown_status",
                ],
                "cannot_be_omitted_on_failure": True,
            },
            "state_changing_action_rule": "N_actions_require_at_least_N_plus_1_triplet_checkpoints_with_validated_adjacent_sharing",
            "adjacent_sharing": "post_action_triplet_may_be_next_pre_action_triplet_only_after_complete_validation",
            "triplet": ["screenshot_visual_inspection", "ui_tree", "bounded_target_log"],
            "screenshot_governs_visual_overlay_mismatch": True,
            "missing_modality_terminal_status": "blocked_by_tooling",
        },
        "c1_operation_contract": {
            "launch_free": True,
            "read_only_metadata_only": True,
            "single_external_executor_call_max": 1,
            "controller_has_no_executor": True,
            "controller_starts_subprocess": False,
            "selector_snapshot_max": 3,
            "target_only_metadata_query_max": 8,
            "timeout_seconds": 20,
            "retry_max": 0,
            "credential_presence_check": "forbidden_in_c1_use_c0p_separate_token",
        },
        "anomaly_contract": {
            "record_before_continue_or_recovery": True,
            "required_fields": [
                "anomaly_id",
                "trigger_action",
                "expected_result",
                "observed_result",
                "evidence_status",
                "public_safe_alias",
                "cause_classification",
                "test_design_implication",
                "evidence_ids",
            ],
            "recurrence_and_recovery_are_distinct_events": True,
        },
        "kill_switch": {
            "sequence": ["target_only_force_stop", "home", "post_kill_checkpoint", "capture_shutdown"],
            "invalidates_security_token": True,
            "trigger_on": [
                "target_or_build_drift",
                "raw_spill",
                "budget_or_timeout_breach",
                "unexpected_mutation_or_boundary",
                "capture_failure",
                "ambiguous_target",
            ],
            "does_not_authorize": [
                "uninstall",
                "reinstall",
                "clear_or_reset",
                "apk_modification",
                "security_bypass",
                "broad_device_cleanup",
            ],
        },
        "security_gate": {
            "security_alias": C1_SECURITY_ALIAS,
            "literal_token_format": GO_PREFIX + f"<{PLAN_HASH_RE}>",
            "token_path": SECURITY_GO_C1_REL.as_posix(),
            "must_bind": [
                "epic_id",
                "run_id",
                "contour_id",
                "plan_sha256",
                "target_alias",
                "build_alias",
                "fixture_alias",
                "security_alias",
                "passport_sha256",
                "passport_aliases",
                "passport_expires_at_utc",
                "c0p_result_path",
                "c0p_result_sha256",
                "issued_at_utc",
                "expires_at_utc",
                "budget",
            ],
            "not_issued_by_controller": True,
            "resume_expiry_drift_material_change_or_kill_invalidates": True,
        },
        "future_contours": future_contours(),
        "global_budget": dict(GLOBAL_BUDGET),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
    }


def future_contours() -> list[dict[str, Any]]:
    """Plan-only C2-C6 contracts; none authorizes execution."""

    return [
        {
            "id": "epic-phone-001-c2-authentication",
            "status": "blocked_fresh_literal_go_required",
            "state_changing_action_max": 41,
            "launch_max": 1,
            "safe_input_max": 40,
            "phone_submit_max": 1,
            "otp_submit_max": 1,
            "wrong_code_captcha_retry_max": 0,
            "checkpoint_triplet_max": 42,
            "minimum_checkpoint_rule": "N_plus_1_with_validated_adjacent_sharing",
            "minutes_max": 15,
        },
        {
            "id": "epic-phone-001-c3-core-navigation",
            "status": "blocked_fresh_literal_go_required",
            "state_changing_action_max": 60,
            "checkpoint_triplet_max": 61,
            "minimum_checkpoint_rule": "N_plus_1_with_validated_adjacent_sharing",
            "minutes_max": 25,
        },
        {
            "id": "epic-phone-001-c4-exhaustive-inventory-slice",
            "status": "blocked_fresh_literal_go_required_per_slice",
            "state_changing_action_max": 80,
            "checkpoint_triplet_max": 81,
            "minimum_checkpoint_rule": "N_plus_1_with_validated_adjacent_sharing",
            "minutes_max": 30,
            "slice_count_max": 2,
            "aggregate_state_changing_action_max": 120,
            "aggregate_checkpoint_triplet_max": 122,
        },
        {
            "id": "epic-phone-001-c5-input-lifecycle-recovery",
            "status": "blocked_fresh_literal_go_required",
            "state_changing_action_max": 46,
            "safe_input_max": 40,
            "home_foreground_cycle_max": 2,
            "target_only_force_stop_relaunch_cycle_max": 1,
            "checkpoint_triplet_max": 47,
            "minimum_checkpoint_rule": "N_plus_1_with_validated_adjacent_sharing",
            "orientation_or_display_action_max": 0,
            "minutes_max": 25,
        },
        {
            "id": "epic-phone-001-c6-boundary-recovery",
            "status": "blocked_fresh_literal_go_required",
            "state_changing_action_max": 60,
            "boundary_max": 20,
            "local_only_qr_decode_max": 20,
            "known_safe_back_attempt_max_per_boundary": 1,
            "external_follow_auth_payment_session_start_max": 0,
            "checkpoint_triplet_max": 61,
            "minimum_checkpoint_rule": "N_plus_1_with_validated_adjacent_sharing",
            "minutes_max": 30,
        },
        {
            "id": "epic-phone-001-c7-cleanup",
            "status": "blocked_fresh_literal_go_required",
            "state_changing_action_max": 3,
            "checkpoint_triplet_max": 4,
            "minimum_checkpoint_rule": "N_plus_1_with_validated_adjacent_sharing",
            "sequence": ["target_only_force_stop", "home", "capture_shutdown"],
            "minutes_max": 10,
        },
    ]


def validate_plan(plan: Mapping[str, Any]) -> None:
    expected = controller_plan()
    if not _exact_equal(dict(plan), expected):
        raise ContractError("controller_plan_drift")
    if plan["budget"] != C1_BUDGET:
        raise ContractError("c1_budget_drift")
    if C1_BUDGET["raw_sink_soft_bytes_max"] >= C1_BUDGET["raw_sink_hard_bytes_max"]:
        raise ContractError("raw_sink_soft_limit_must_be_below_hard_limit")
    for contour in plan["future_contours"]:
        actions = int(contour["state_changing_action_max"])
        checkpoints = int(contour["checkpoint_triplet_max"])
        if checkpoints < actions + 1:
            raise ContractError(f"{contour['id']}_checkpoint_budget_underflow")
    if not plan["security_gate"]["not_issued_by_controller"]:
        raise ContractError("controller_cannot_issue_security_go")
    if set(plan["forbidden_actions"]) != set(FORBIDDEN_ACTIONS):
        raise ContractError("forbidden_action_contract_drift")


def _strict_object(value: Any, required: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != required:
        raise ContractError(f"{label}_schema_keys_invalid")
    return value


def _read_small_json(path: Path, label: str, *, max_bytes: int = 64 * 1024) -> tuple[dict[str, Any], bytes]:
    _assert_fixed_ignored_file(path, label)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ContractError(f"{label}_read_failed") from exc
    if not data or len(data) > max_bytes:
        raise ContractError(f"{label}_size_invalid")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label}_json_invalid") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label}_not_object")
    return value, data


def _read_small_bytes(path: Path, label: str, *, max_bytes: int) -> bytes:
    _assert_fixed_ignored_file(path, label)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ContractError(f"{label}_read_failed") from exc
    if not data or len(data) > max_bytes:
        raise ContractError(f"{label}_size_invalid")
    return data


def _is_reparse_or_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        result = path.lstat()
    except OSError:
        return False
    attributes = getattr(result, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _assert_fixed_ignored_file(path: Path, label: str) -> None:
    root = REPO_ROOT.resolve()
    try:
        lexical = path.absolute().relative_to(root)
    except ValueError as exc:
        raise ContractError(f"{label}_outside_repository") from exc
    if not lexical.parts or lexical.parts[0] != ".qa_local" or ".." in lexical.parts:
        raise ContractError(f"{label}_outside_fixed_ignored_root")
    cursor = root
    for part in lexical.parts:
        cursor = cursor / part
        if _is_reparse_or_link(cursor):
            raise ContractError(f"{label}_link_or_reparse_forbidden")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ContractError(f"{label}_missing") from exc
    if root not in resolved.parents or resolved == root:
        raise ContractError(f"{label}_outside_repository")
    relative = resolved.relative_to(root)
    if not relative.parts or relative.parts[0] != ".qa_local":
        raise ContractError(f"{label}_outside_fixed_ignored_root")
    if not resolved.is_file():
        raise ContractError(f"{label}_not_regular_file")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractError(f"{label}_not_utc_z")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ContractError(f"{label}_invalid") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{label}_timezone_missing")
    return parsed.astimezone(UTC)


def _validate_fixture_passport(value: Any) -> None:
    required = {
        "schema_version", "epic_id", "run_id", "fixture_alias", "synthetic_test_only",
        "not_real_user", "values_local_only", "revoked", "authority_validity",
        "allowed_scope", "forbidden_scope", "issued_at_utc", "expires_at_utc",
        "authority_set_id", "renewal_id", "prep_attempt_id",
    }
    passport = _strict_object(value, required, "fixture_passport")
    expected = {
        "schema_version": FIXTURE_PASSPORT_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "authority_set_id": AUTHORITY_SET_ID,
        "renewal_id": AUTHORITY_RENEWAL_ID,
        "prep_attempt_id": C0P_PREP_ATTEMPT_ID,
        "fixture_alias": FIXTURE_ALIAS,
        "synthetic_test_only": True,
        "not_real_user": True,
        "values_local_only": True,
        "revoked": False,
        "authority_validity": "current_epic_run_until_completion_or_revocation",
        "allowed_scope": ["synthetic_session_create", "read_only_navigation", "safe_logout"],
        "forbidden_scope": ["payment", "subscription", "entitlement", "profile", "account", "paid_session", "external_or_qr_traversal"],
    }
    if any(not _exact_equal(passport.get(key), expected_value) for key, expected_value in expected.items()):
        raise ContractError("fixture_passport_binding_invalid")
    issued = _parse_utc(passport["issued_at_utc"], "fixture_passport_issued_at")
    expires = _parse_utc(passport["expires_at_utc"], "fixture_passport_expires_at")
    if expires <= issued:
        raise ContractError("fixture_passport_expiry_invalid")


def _validate_target_build_passport(value: Any) -> None:
    required = {
        "schema_version", "epic_id", "run_id", "target_alias", "build_alias",
        "target_authorized", "build_authorized", "launch_allowed", "mutation_allowed",
        "issued_at_utc", "expires_at_utc", "passport_purpose",
        "current_freshness_evidence", "runtime_evidence", "task058a_row03_evidence_status",
        "authority_set_id", "renewal_id", "prep_attempt_id",
    }
    passport = _strict_object(value, required, "target_build_passport")
    expected = {
        "schema_version": TARGET_BUILD_PASSPORT_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "authority_set_id": AUTHORITY_SET_ID,
        "renewal_id": AUTHORITY_RENEWAL_ID,
        "prep_attempt_id": C0P_PREP_ATTEMPT_ID,
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "target_authorized": True,
        "build_authorized": True,
        "launch_allowed": False,
        "mutation_allowed": False,
        "passport_purpose": "authorization_only",
        "current_freshness_evidence": False,
        "runtime_evidence": False,
        "task058a_row03_evidence_status": "unknown",
    }
    if any(not _exact_equal(passport.get(key), expected_value) for key, expected_value in expected.items()):
        raise ContractError("target_build_passport_binding_invalid")
    issued = _parse_utc(passport["issued_at_utc"], "target_build_passport_issued_at")
    expires = _parse_utc(passport["expires_at_utc"], "target_build_passport_expires_at")
    if expires <= issued:
        raise ContractError("target_build_passport_expiry_invalid")


def _validate_evidence_cleanup_passport(value: Any) -> None:
    required = {
        "schema_version", "epic_id", "run_id", "run_root", "soft_bytes_max",
        "hard_bytes_max", "redaction_default", "direct_capture_no_echo",
        "cleanup_sequence", "forbidden_action_count", "retention_expires_at_utc",
        "passport_purpose", "execution_evidence", "issued_at_utc",
        "authority_set_id", "renewal_id", "prep_attempt_id",
    }
    passport = _strict_object(value, required, "evidence_cleanup_passport")
    expected = {
        "schema_version": EVIDENCE_CLEANUP_PASSPORT_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "authority_set_id": AUTHORITY_SET_ID,
        "renewal_id": AUTHORITY_RENEWAL_ID,
        "prep_attempt_id": C0P_PREP_ATTEMPT_ID,
        "run_root": RUN_ROOT_REL.as_posix(),
        "soft_bytes_max": C1_BUDGET["raw_sink_soft_bytes_max"],
        "hard_bytes_max": C1_BUDGET["raw_sink_hard_bytes_max"],
        "redaction_default": True,
        "direct_capture_no_echo": True,
        "cleanup_sequence": ["target_only_force_stop", "home", "post_kill_checkpoint", "capture_shutdown"],
        "forbidden_action_count": 0,
        "passport_purpose": "policy_readiness_only",
        "execution_evidence": False,
    }
    if any(not _exact_equal(passport.get(key), expected_value) for key, expected_value in expected.items()):
        raise ContractError("evidence_cleanup_passport_binding_invalid")
    _parse_utc(passport["retention_expires_at_utc"], "retention_expires_at")


def _controller_source_sha256() -> str:
    source = Path(__file__)
    if source.is_symlink() or not source.is_file():
        raise ContractError("controller_source_missing_or_link")
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise ContractError("controller_source_read_failed") from exc
    if not data or len(data) > 1024 * 1024:
        raise ContractError("controller_source_size_invalid")
    return _sha256_bytes(data)


def _validate_c0p_plan(value: Mapping[str, Any], source_sha256: str) -> dict[str, Any]:
    repository_head = value.get("repository_head")
    bound_source = value.get("controller_source_sha256")
    if not isinstance(repository_head, str) or not isinstance(bound_source, str):
        raise ContractError("c0p_plan_binding_missing")
    expected = c0p_plan(repository_head, bound_source, value.get("issued_at_utc"), value.get("expires_at_utc"))
    if not _exact_equal(dict(value), expected):
        raise ContractError("c0p_plan_contract_drift")
    if bound_source != source_sha256:
        raise ContractError("c0p_controller_source_sha256_mismatch")
    return expected


def _validate_c0p_authority_payloads(
    plan: Mapping[str, Any],
    plan_bytes: bytes,
    fixture_passport: Mapping[str, Any],
    fixture_bytes: bytes,
    target_build_passport: Mapping[str, Any],
    target_build_bytes: bytes,
    evidence_cleanup_passport: Mapping[str, Any],
    evidence_cleanup_bytes: bytes,
    security_go: Mapping[str, Any],
    *,
    source_sha256: str,
    now: datetime,
) -> dict[str, Any]:
    expected_plan = _validate_c0p_plan(plan, source_sha256)
    if plan_bytes != canonical_plan_bytes(expected_plan):
        raise ContractError("c0p_plan_not_exact_canonical_json")
    c0p_issued = _parse_utc(plan["issued_at_utc"], "c0p_plan_issued_at")
    c0p_expires = _parse_utc(plan["expires_at_utc"], "c0p_plan_expires_at")
    if not c0p_issued <= now < c0p_expires or c0p_expires <= c0p_issued or c0p_expires - c0p_issued > timedelta(minutes=10):
        raise ContractError("c0p_plan_time_contract_invalid")
    _validate_fixture_passport(fixture_passport)
    _validate_target_build_passport(target_build_passport)
    _validate_evidence_cleanup_passport(evidence_cleanup_passport)
    required = {
        "schema_version", "literal_token", "epic_id", "run_id", "contour_id",
        "c0p_plan_sha256", "repository_head", "controller_source_sha256",
        "target_alias", "build_alias", "fixture_alias", "passport_aliases",
        "security_alias", "passport_sha256", "passport_expires_at_utc",
        "issued_at_utc", "expires_at_utc", "result_path", "attempt_marker_path",
        "attempt_marker_schema", "budget",
    }
    go = _strict_object(security_go, required, "security_go_c0p")
    digest = plan_sha256(expected_plan)
    expected = {
        "schema_version": C0P_SECURITY_GO_SCHEMA,
        "literal_token": expected_c0p_go_token(digest),
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": C0P_CONTOUR_ID,
        "c0p_plan_sha256": digest,
        "repository_head": expected_plan["repository_head"],
        "controller_source_sha256": source_sha256,
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "passport_aliases": {
            "fixture_authority": FIXTURE_PASSPORT_ALIAS,
            "target_build": TARGET_BUILD_PASSPORT_ALIAS,
            "evidence_cleanup": EVIDENCE_CLEANUP_PASSPORT_ALIAS,
        },
        "security_alias": C0P_SECURITY_ALIAS,
        "passport_sha256": {
            "fixture_authority": _sha256_bytes(fixture_bytes),
            "target_build": _sha256_bytes(target_build_bytes),
            "evidence_cleanup": _sha256_bytes(evidence_cleanup_bytes),
        },
        "passport_expires_at_utc": {
            "fixture_authority": fixture_passport["expires_at_utc"],
            "target_build": target_build_passport["expires_at_utc"],
            "evidence_cleanup": evidence_cleanup_passport["retention_expires_at_utc"],
        },
        "result_path": C0P_RESULT_REL.as_posix(),
        "attempt_marker_path": C0P_ATTEMPT_REL.as_posix(),
        "attempt_marker_schema": C0P_ATTEMPT_SCHEMA,
        "budget": C0P_BUDGET,
    }
    if any(not _exact_equal(go.get(key), expected_value) for key, expected_value in expected.items()):
        raise ContractError("security_go_c0p_binding_invalid")
    issued = _parse_utc(go["issued_at_utc"], "security_go_c0p_issued_at")
    expires = _parse_utc(go["expires_at_utc"], "security_go_c0p_expires_at")
    if issued > now or expires <= now or expires <= issued:
        raise ContractError("security_go_c0p_not_current")
    if (expires - issued).total_seconds() > C0P_MAX_VALIDITY_MINUTES * 60:
        raise ContractError("security_go_c0p_validity_exceeds_30_minutes")
    for expiry in go["passport_expires_at_utc"].values():
        if _parse_utc(expiry, "c0p_passport_expiry") <= now:
            raise ContractError("c0p_passport_expired")
    for passport, label in (
        (fixture_passport, "fixture_passport"),
        (target_build_passport, "target_build_passport"),
    ):
        if _parse_utc(passport["issued_at_utc"], f"{label}_issued_at") > now:
            raise ContractError(f"{label}_issued_in_future")
    return {
        "repository_head": expected_plan["repository_head"],
        "controller_source_sha256": source_sha256,
        "c0p_plan_sha256": digest,
        "expires_at_utc": go["expires_at_utc"],
        "security_go_sha256": _sha256_bytes(canonical_plan_bytes(go)),
    }


def _parse_c0p_secret(data: bytes) -> dict[str, Any]:
    """Validate the two fields and return only the approved aggregate."""

    if not data or len(data) > C0P_MAX_SECRET_BYTES:
        raise ContractError("c0p_secret_size_invalid")
    try:
        text = data.decode("ascii")
    except UnicodeError as exc:
        raise ContractError("c0p_secret_contract_invalid") from exc
    values: dict[str, str] = {}
    approved = {_C0P_PHONE_FIELD, _C0P_OTP_FIELD}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("export ") or line.count("=") != 1:
            raise ContractError("c0p_secret_contract_invalid")
        key, value = line.split("=", 1)
        if key not in approved or key in values or not value or "$" in value:
            raise ContractError("c0p_secret_contract_invalid")
        values[key] = value
    if set(values) != approved:
        raise ContractError("c0p_secret_contract_invalid")
    if _C0P_PHONE_PATTERN.fullmatch(values[_C0P_PHONE_FIELD]) is None:
        raise ContractError("c0p_phone_format_policy_failed")
    if _C0P_OTP_PATTERN.fullmatch(values[_C0P_OTP_FIELD]) is None:
        raise ContractError("c0p_otp_format_policy_failed")
    return {
        "required_field_count": 2,
        "required_fields_present": True,
        "unexpected_fields_absent": True,
        "phone_format_policy_pass": True,
        "otp_format_policy_pass": True,
    }


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_c0p_result(binding: Mapping[str, str], *, executed_at: datetime) -> dict[str, Any]:
    return {
        "schema_version": C0P_RESULT_SCHEMA,
        "epic_id": EPIC_ID,
        "contour_id": C0P_CONTOUR_ID,
        "run_id": RUN_ID,
        "repository_head": binding["repository_head"],
        "controller_source_sha256": binding["controller_source_sha256"],
        "c0p_plan_sha256": binding["c0p_plan_sha256"],
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "security_passport_alias": C0P_SECURITY_ALIAS,
        "executed_at_utc": _format_utc(executed_at),
        "expires_at_utc": binding["expires_at_utc"],
        "execution_count": 1,
        "result": "pass",
        "evidence_status": "confirmed",
        "fixed_path_containment_pass": True,
        "ignored_paths_pass": True,
        "no_reparse_pass": True,
        "required_passport_count": 3,
        "required_passports_valid": True,
        "required_secret_field_count": 2,
        "required_secret_fields_present": True,
        "unexpected_secret_fields_absent": True,
        "phone_format_policy_pass": True,
        "otp_format_policy_pass": True,
        "secret_values_exposed": False,
        "secret_hashes_emitted": False,
        "device_action_count": 0,
        "adb_action_count": 0,
        "subprocess_count": 0,
        "app_launch_count": 0,
        "authentication_action_count": 0,
        "forbidden_action_count": 0,
        "raw_spill_detected": False,
        "cleanup_status": "capture_closed_no_device_contact",
    }


def _build_c0p_attempt_marker(binding: Mapping[str, str], *, created_at: datetime) -> dict[str, Any]:
    return {
        "schema_version": C0P_ATTEMPT_SCHEMA,
        "epic_id": EPIC_ID,
        "contour_id": C0P_CONTOUR_ID,
        "run_id": RUN_ID,
        "repository_head": binding["repository_head"],
        "controller_source_sha256": binding["controller_source_sha256"],
        "c0p_plan_sha256": binding["c0p_plan_sha256"],
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "security_passport_alias": C0P_SECURITY_ALIAS,
        "security_go_sha256": binding["security_go_sha256"],
        "created_at_utc": _format_utc(created_at),
        "attempt_count": 1,
        "secret_read_count_before_marker": 0,
        "device_action_count": 0,
        "adb_action_count": 0,
        "subprocess_count": 0,
        "app_launch_count": 0,
        "authentication_action_count": 0,
        "forbidden_action_count": 0,
    }


def _assert_c0p_one_shot_paths_clear() -> None:
    candidates = (
        REPO_ROOT / C0P_ATTEMPT_REL,
        REPO_ROOT / C0P_RESULT_REL,
        REPO_ROOT / PUBLIC_SAFE_REL / "c0p-005-result.local.json.tmp",
    )
    if any(path.exists() or path.is_symlink() for path in candidates):
        raise ContractError("c0p_one_shot_path_already_exists")


def _write_c0p_attempt_marker(marker: Mapping[str, Any]) -> None:
    output = REPO_ROOT / C0P_ATTEMPT_REL
    _assert_fixed_ignored_dir(output.parent, "c0p_attempt_parent")
    data = canonical_plan_bytes(marker)
    try:
        with output.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ContractError("c0p_attempt_marker_write_failed") from exc


def _validate_c0p_result(
    value: Any,
    data: bytes,
    *,
    now: datetime,
    expected_source_sha256: str,
) -> None:
    required = {
        "schema_version", "epic_id", "contour_id", "run_id", "repository_head",
        "controller_source_sha256", "c0p_plan_sha256", "target_alias", "build_alias",
        "fixture_alias", "security_passport_alias", "executed_at_utc", "expires_at_utc",
        "execution_count", "result", "evidence_status", "fixed_path_containment_pass",
        "ignored_paths_pass", "no_reparse_pass", "required_passport_count",
        "required_passports_valid", "required_secret_field_count",
        "required_secret_fields_present", "unexpected_secret_fields_absent",
        "phone_format_policy_pass", "otp_format_policy_pass", "secret_values_exposed",
        "secret_hashes_emitted", "device_action_count", "adb_action_count",
        "subprocess_count", "app_launch_count", "authentication_action_count",
        "forbidden_action_count", "raw_spill_detected", "cleanup_status",
    }
    result = _strict_object(value, required, "c0p_result")
    fixed = {
        "schema_version": C0P_RESULT_SCHEMA,
        "epic_id": EPIC_ID,
        "contour_id": C0P_CONTOUR_ID,
        "run_id": RUN_ID,
        "controller_source_sha256": expected_source_sha256,
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "security_passport_alias": C0P_SECURITY_ALIAS,
        "execution_count": 1,
        "result": "pass",
        "evidence_status": "confirmed",
        "fixed_path_containment_pass": True,
        "ignored_paths_pass": True,
        "no_reparse_pass": True,
        "required_passport_count": 3,
        "required_passports_valid": True,
        "required_secret_field_count": 2,
        "required_secret_fields_present": True,
        "unexpected_secret_fields_absent": True,
        "phone_format_policy_pass": True,
        "otp_format_policy_pass": True,
        "secret_values_exposed": False,
        "secret_hashes_emitted": False,
        "device_action_count": 0,
        "adb_action_count": 0,
        "subprocess_count": 0,
        "app_launch_count": 0,
        "authentication_action_count": 0,
        "forbidden_action_count": 0,
        "raw_spill_detected": False,
        "cleanup_status": "capture_closed_no_device_contact",
    }
    if any(not _exact_equal(result.get(key), expected) for key, expected in fixed.items()):
        raise ContractError("c0p_result_contract_invalid")
    for hash_key, length in (("repository_head", 40), ("c0p_plan_sha256", 64)):
        candidate = result.get(hash_key)
        if not isinstance(candidate, str) or len(candidate) != length or any(
            char not in "0123456789abcdef" for char in candidate
        ):
            raise ContractError("c0p_result_hash_binding_invalid")
    executed = _parse_utc(result["executed_at_utc"], "c0p_result_executed_at")
    expires = _parse_utc(result["expires_at_utc"], "c0p_result_expires_at")
    if executed > now or expires <= now or expires <= executed:
        raise ContractError("c0p_result_not_current")
    if (expires - executed).total_seconds() > C0P_MAX_VALIDITY_MINUTES * 60:
        raise ContractError("c0p_result_validity_exceeds_30_minutes")
    if data != canonical_plan_bytes(result):
        raise ContractError("c0p_result_not_exact_canonical_json")


def _assert_fixed_ignored_dir(path: Path, label: str) -> None:
    root = REPO_ROOT.resolve()
    try:
        lexical = path.absolute().relative_to(root)
    except ValueError as exc:
        raise ContractError(f"{label}_outside_repository") from exc
    if not lexical.parts or lexical.parts[0] != ".qa_local" or ".." in lexical.parts:
        raise ContractError(f"{label}_outside_fixed_ignored_root")
    cursor = root
    for part in lexical.parts:
        cursor = cursor / part
        if _is_reparse_or_link(cursor):
            raise ContractError(f"{label}_link_or_reparse_forbidden")
    if not path.is_dir():
        raise ContractError(f"{label}_missing_or_not_directory")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ContractError(f"{label}_missing_or_not_directory") from exc
    if root not in resolved.parents:
        raise ContractError(f"{label}_outside_repository")
    relative = resolved.relative_to(root)
    if not relative.parts or relative.parts[0] != ".qa_local":
        raise ContractError(f"{label}_outside_fixed_ignored_root")


def _write_c0p_result(result: Mapping[str, Any]) -> None:
    output = REPO_ROOT / C0P_RESULT_REL
    parent = output.parent
    _assert_fixed_ignored_dir(parent, "c0p_result_parent")
    if output.exists() or output.is_symlink():
        raise ContractError("c0p_result_already_exists_one_shot_only")
    temporary = parent / "c0p-005-result.local.json.tmp"
    if temporary.exists() or temporary.is_symlink():
        raise ContractError("c0p_result_temporary_path_not_clean")
    data = canonical_plan_bytes(result)
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    except OSError as exc:
        raise ContractError("c0p_result_write_failed") from exc


def _assert_c0p_result_output_clean() -> None:
    """Enforce one-shot output before the first credential-file read."""

    output = REPO_ROOT / C0P_RESULT_REL
    parent = output.parent
    _assert_fixed_ignored_dir(parent, "c0p_result_parent")
    temporary = parent / "c0p-005-result.local.json.tmp"
    if output.exists() or output.is_symlink():
        raise ContractError("c0p_result_already_exists_one_shot_only")
    if temporary.exists() or temporary.is_symlink():
        raise ContractError("c0p_result_temporary_path_not_clean")


def preflight_c0p(*, now: datetime | None = None) -> dict[str, Any]:
    """Run the token-gated presence-only C0P check; never contact a device."""

    current = (now or datetime.now(UTC)).astimezone(UTC)
    source_sha256 = _controller_source_sha256()
    plan, plan_bytes = _read_small_json(REPO_ROOT / C0P_PLAN_REL, "c0p_plan")
    fixture, fixture_bytes = _read_small_json(REPO_ROOT / FIXTURE_PASSPORT_REL, "fixture_passport")
    target, target_bytes = _read_small_json(REPO_ROOT / TARGET_BUILD_PASSPORT_REL, "target_build_passport")
    cleanup, cleanup_bytes = _read_small_json(REPO_ROOT / EVIDENCE_CLEANUP_PASSPORT_REL, "evidence_cleanup_passport")
    go, _ = _read_small_json(REPO_ROOT / SECURITY_GO_C0P_REL, "security_go_c0p")
    binding = _validate_c0p_authority_payloads(
        plan,
        plan_bytes,
        fixture,
        fixture_bytes,
        target,
        target_bytes,
        cleanup,
        cleanup_bytes,
        go,
        source_sha256=source_sha256,
        now=current,
    )
    _assert_c0p_one_shot_paths_clear()
    _write_c0p_attempt_marker(_build_c0p_attempt_marker(binding, created_at=current))
    # This is deliberately the first and only credential-file read.  Every
    # plan/passport/source/token gate above must pass before this line.
    secret_bytes = _read_small_bytes(
        REPO_ROOT / SECRET_SOURCE_REL, "c0p_secret", max_bytes=C0P_MAX_SECRET_BYTES
    )
    projection = _parse_c0p_secret(secret_bytes)
    result = _build_c0p_result(binding, executed_at=current)
    _validate_c0p_result(
        result,
        canonical_plan_bytes(result),
        now=current,
        expected_source_sha256=source_sha256,
    )
    _write_c0p_result(result)
    return projection


def validate_preflight_payloads(
    plan: Mapping[str, Any],
    fixture_passport: Mapping[str, Any],
    fixture_bytes: bytes,
    target_build_passport: Mapping[str, Any],
    target_build_bytes: bytes,
    evidence_cleanup_passport: Mapping[str, Any],
    evidence_cleanup_bytes: bytes,
    c0p_result: Mapping[str, Any],
    c0p_result_bytes: bytes,
    security_go: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate fixed local authority payloads without touching a device."""

    validate_plan(plan)
    _validate_fixture_passport(fixture_passport)
    _validate_target_build_passport(target_build_passport)
    _validate_evidence_cleanup_passport(evidence_cleanup_passport)
    source_sha256 = _controller_source_sha256()
    _validate_c0p_result(
        c0p_result,
        c0p_result_bytes,
        now=(now or datetime.now(UTC)).astimezone(UTC),
        expected_source_sha256=source_sha256,
    )
    required = {
        "schema_version", "literal_token", "epic_id", "run_id", "contour_id",
        "plan_sha256", "target_alias", "build_alias", "fixture_alias",
        "security_alias",
        "passport_sha256", "issued_at_utc", "expires_at_utc", "budget",
        "passport_aliases", "passport_expires_at_utc", "c0p_result_path",
        "c0p_result_sha256",
    }
    go = _strict_object(security_go, required, "security_go_c1")
    digest = plan_sha256(plan)
    passport_hashes = {
        "fixture_authority": _sha256_bytes(fixture_bytes),
        "target_build": _sha256_bytes(target_build_bytes),
        "evidence_cleanup": _sha256_bytes(evidence_cleanup_bytes),
    }
    expected = {
        "schema_version": SECURITY_GO_SCHEMA,
        "literal_token": expected_go_token(digest),
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "plan_sha256": digest,
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "security_alias": C1_SECURITY_ALIAS,
        "passport_sha256": passport_hashes,
        "passport_aliases": {
            "fixture_authority": FIXTURE_PASSPORT_ALIAS,
            "target_build": TARGET_BUILD_PASSPORT_ALIAS,
            "evidence_cleanup": EVIDENCE_CLEANUP_PASSPORT_ALIAS,
        },
        "passport_expires_at_utc": {
            "fixture_authority": fixture_passport["expires_at_utc"],
            "target_build": target_build_passport["expires_at_utc"],
            "evidence_cleanup": evidence_cleanup_passport["retention_expires_at_utc"],
        },
        "c0p_result_path": C0P_RESULT_REL.as_posix(),
        "c0p_result_sha256": _sha256_bytes(c0p_result_bytes),
        "budget": C1_BUDGET,
    }
    if any(not _exact_equal(go.get(key), expected_value) for key, expected_value in expected.items()):
        raise ContractError("security_go_c1_binding_invalid")
    issued = _parse_utc(go["issued_at_utc"], "security_go_issued_at")
    expires = _parse_utc(go["expires_at_utc"], "security_go_expires_at")
    current = (now or datetime.now(UTC)).astimezone(UTC)
    if issued > current or expires <= current or expires <= issued:
        raise ContractError("security_go_c1_not_current")
    if (expires - issued).total_seconds() > 30 * 60:
        raise ContractError("security_go_c1_validity_exceeds_30_minutes")
    for passport in (fixture_passport, target_build_passport):
        if _parse_utc(passport["expires_at_utc"], "passport_expires_at") <= current:
            raise ContractError("passport_expired")
        if _parse_utc(passport["issued_at_utc"], "passport_issued_at") > current:
            raise ContractError("passport_issued_in_future")
    if _parse_utc(evidence_cleanup_passport["retention_expires_at_utc"], "retention_expires_at") <= current:
        raise ContractError("retention_expired")
    return {
        "status": "ready_for_separately_authorized_external_c1_executor",
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "plan_binding_valid": True,
        "fixture_presence": "confirmed_by_current_c0p_result",
        "device_action": False,
        "subprocess_started": False,
        "c1_executed": False,
    }


def preflight_c1() -> dict[str, Any]:
    """Read only the fixed C1 authority artifacts; never execute C1."""

    plan_value, plan_bytes = _read_small_json(REPO_ROOT / PLAN_REL, "controller_plan")
    plan = controller_plan()
    if not _exact_equal(plan_value, plan) or plan_bytes != canonical_plan_bytes(plan):
        raise ContractError("controller_plan_local_copy_not_exact_canonical_plan")
    fixture, fixture_bytes = _read_small_json(REPO_ROOT / FIXTURE_PASSPORT_REL, "fixture_passport")
    target, target_bytes = _read_small_json(REPO_ROOT / TARGET_BUILD_PASSPORT_REL, "target_build_passport")
    cleanup, cleanup_bytes = _read_small_json(REPO_ROOT / EVIDENCE_CLEANUP_PASSPORT_REL, "evidence_cleanup_passport")
    c0p_result, c0p_result_bytes = _read_small_json(REPO_ROOT / C0P_RESULT_REL, "c0p_result")
    go, _ = _read_small_json(REPO_ROOT / SECURITY_GO_C1_REL, "security_go_c1")
    return validate_preflight_payloads(
        plan, fixture, fixture_bytes, target, target_bytes, cleanup, cleanup_bytes,
        c0p_result, c0p_result_bytes, go
    )


def _public_dry_run() -> dict[str, Any]:
    plan = controller_plan()
    validate_plan(plan)
    return {
        "status": "pass_repository_only_dry_run_not_authorized_not_run",
        "plan_contract_valid": True,
        "plan_hash_computed": len(plan_sha256(plan)) == 64,
        "c0p_contract_valid": c0p_plan_contract()["status"] == "not_run_distinct_literal_go_required",
        "c0p_guarded_interface_present": True,
        "ignored_storage_read": False,
        "secret_presence_checked": False,
        "subprocess_started": False,
        "device_action": False,
        "application_action": False,
        "credential_action": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--preflight-c1", action="store_true")
    modes.add_argument("--preflight-c0p", action="store_true")
    parser.add_argument("--allow-prod-conditional-c1", action="store_true")
    parser.add_argument("--allow-prod-conditional-c0p", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.allow_prod_conditional_c1 and not args.preflight_c1:
            raise ContractError("allow_flag_valid_only_with_preflight_c1")
        if args.allow_prod_conditional_c0p and not args.preflight_c0p:
            raise ContractError("c0p_allow_flag_valid_only_with_preflight_c0p")
        if args.preflight_c1:
            if not args.allow_prod_conditional_c1:
                raise ContractError("preflight_c1_requires_explicit_allow_flag")
            result = preflight_c1()
        elif args.preflight_c0p:
            if not args.allow_prod_conditional_c0p:
                raise ContractError("preflight_c0p_requires_explicit_allow_flag")
            result = preflight_c0p()
        elif args.dry_run:
            result = _public_dry_run()
        else:
            plan = controller_plan()
            validate_plan(plan)
            result = {
                "status": "pass_repository_contract_only",
                "plan_contract_valid": True,
                "plan_hash_computed": len(plan_sha256(plan)) == 64,
                "ignored_storage_read": False,
                "subprocess_started": False,
                "device_action": False,
            }
    except KeyboardInterrupt:
        print(
            "EPIC-PHONE-001 runtime controller: FAIL (operation_interrupted_fail_closed)",
            file=sys.stderr,
        )
        return 130
    except ContractError as exc:
        print(f"EPIC-PHONE-001 runtime controller: FAIL ({exc})", file=sys.stderr)
        return 1
    except OSError:
        print(
            "EPIC-PHONE-001 runtime controller: FAIL (local_io_error_fail_closed)",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

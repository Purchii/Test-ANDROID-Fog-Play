#!/usr/bin/env python3
"""No-pyc loader for the owner-local synthetic fixture provision contour."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
import time
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path


RUN_ID = "epic-phone-001-20260816-r01"
CONTOUR_ID = "epic-phone-001-owner-local-fixture-provision"
SCHEMA = "epic-phone-001-owner-local-fixture-provision-plan-v1"
AGGREGATE_SCHEMA = "epic-phone-001-owner-local-fixture-provision-aggregate-v2"
TERMINAL_RESULT_SCHEMA = "epic-phone-001-owner-local-fixture-provision-terminal-result-v1"
SECURITY_GO_SCHEMA = "epic-phone-001-owner-local-fixture-provision-security-go-v1"
PLAN_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION_PLAN"
GO_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION_GO"
GO_PREFIX = f"GO_EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION__{RUN_ID}__"
DEADLINE_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_DEADLINE_MONOTONIC_NS"
BOOTSTRAP_WALL_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_BOOTSTRAP_WALL_UTC"
EXECUTOR_REL = "automation/phone/epic_phone_001_fixture_interactive_provision.py"
LOADER_REL = "automation/phone/epic_phone_001_owner_local_fixture_loader.py"
PLAN_REL = ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/fixture-owner-provision-003-plan.local.json"
SECURITY_GO_REL = ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/security-go-owner-local-fixture-provision-003.local.json"
RESULT_REL = ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/fixture-owner-provision-003-result.local.json"
PROVISION_RESULT_ALIAS = "epic-phone-001-owner-local-fixture-provision-result-003"
READINESS_MODE_ENV = "EPIC_PHONE_001_OWNER_LOCAL_CONSOLE_CONTOUR"
READINESS_CONTOUR_ID = "epic-phone-001-owner-local-console-readiness"
READINESS_ATTEMPT_ID = "owner-local-console-readiness-001"
READINESS_SECURITY_ALIAS = "epic-phone-001-security-owner-local-console-readiness-001"
READINESS_RESULT_ALIAS = "epic-phone-001-owner-local-console-readiness-result-001"
READINESS_PLAN_REL = ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/owner-local-console-readiness-001-plan.local.json"
READINESS_GO_REL = ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/security-go-owner-local-console-readiness-001.local.json"
READINESS_RESULT_REL = ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/owner-local-console-readiness-001-result.local.json"
READINESS_PLAN_SCHEMA = "epic-phone-001-owner-local-console-readiness-plan-v1"
READINESS_GO_SCHEMA = "epic-phone-001-owner-local-console-readiness-security-go-v1"
READINESS_RESULT_SCHEMA = "epic-phone-001-owner-local-console-readiness-result-v1"
READINESS_GO_PREFIX = f"GO_EPIC_PHONE_001_OWNER_LOCAL_CONSOLE_READINESS__{RUN_ID}__"
PROVISION_MARKER_REL = ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/fixture-owner-provision-003-attempt.local.json"
MAX_PLAN = 64 * 1024
MAX_SOURCE = 96 * 1024
MAX_DEPTH = 12
MAX_INTEGER = 9_007_199_254_740_991
REPARSE_ATTRIBUTE = 0x400
RESULT_FINALIZATION_RESERVE_SECONDS = 5
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
WORKSPACE_CONTRACT = ()
NO_MUTATOR_SCOPE = {
    "ancestors": "all_lexical_ancestors_of_every_listed_or_resolved_path",
    "git_metadata": [".git_marker", "resolved_local_gitdir", "optional_resolved_local_commondir",
                     "gitdir_HEAD", "optional_active_loose_ref_component_probe",
                     "exact_active_loose_ref_or_packed_refs"],
    "local_paths": ["bound_repository_sources", "authority_set005_artifacts", "run_root",
                    "fixed_plan", "fixed_security_go", "attempt_marker", "terminal_result",
                    "secret_parent", "secret_destination"],
}
LOADER_GIT_CHECK_GLOBAL = "__owner_fixture_loader_git_head_validation_count__"
LOADER_GIT_CONTENT_GLOBAL = "__owner_fixture_loader_git_metadata_content_read_count__"
LOADER_GIT_PATH_GLOBAL = "__owner_fixture_loader_git_metadata_path_target_count__"
BUDGET = {
    "acl_check_max": 6, "acl_create_max": 4, "application_action_max": 0,
    "authority_artifact_read_max": 4, "authentication_action_max": 0,
    "bounded_input_character_max": 128, "concurrency_max": 1,
    "console_api_validation_max": 3, "console_prompt_write_max": 2, "console_separator_write_max": 2, "destination_directory_create_max": 1,
    "destination_secret_file_create_max": 1, "device_action_max": 0,
    "execution_max": 1, "fixed_go_file_read_max": 2, "host_process_max": 1,
    "git_head_validation_max": 2, "git_metadata_content_read_max": 8,
    "git_metadata_path_target_max": 64,
    "marker_file_create_max": 1, "network_action_max": 0, "terminal_result_file_create_max": 1,
    "protected_marker_file_readback_max": 1, "protected_terminal_result_file_readback_max": 1,
    "loader_terminal_result_content_read_max": 2, "loader_terminal_result_validation_max": 2,
    "no_echo_secret_field_read_max": 2, "overwrite_append_delete_rename_max": 0,
    "fixed_plan_file_read_max": 2, "retry_max": 0, "runtime_action_max": 0,
    "secret_payload_bytes_max": 96, "secret_payload_readback_max": 1,
    "secret_payload_write_max": 1, "subprocess_max": 0, "ui_action_max": 0,
    "cooperative_deadline_seconds_max": 120, "bootstrap_env_write_max": 3,
    "result_finalization_reserve_seconds": RESULT_FINALIZATION_RESERVE_SECONDS,
    "workspace_allowlist_content_read_max": 0, "bound_source_content_read_full_envelope_max": 6,
}
_ACTIVE_TERMINAL_IO_BUDGET = None
TIMEOUT_CONTRACT = {
    "authority_coverage_basis": "validation_utc_plus_ceil_monotonic_remaining_plus_guard",
    "authority_coverage_guard_seconds": 1,
    "blocking_winapi_preemption": "not_claimed",
    "clock_continuity_policy": "fresh_wall_not_before_initial_and_monotonic_non_decreasing",
    "cooperative_deadline_seconds": 120,
    "deadline_model": "checks_immediately_before_and_after_blocking_winapi_calls",
    "hard_kill_guarantee": False,
    "owner_acceptance_scope": "cooperative_calls_may_return_after_internal_deadline_no_hard_kill",
    "owner_acceptance_window_seconds_min": 121,
    "result_finalization_reserve_seconds": RESULT_FINALIZATION_RESERVE_SECONDS,
    "result_finalization_policy": "secret_operations_stop_before_reserved_terminal_result_window",
}
ROOT_KEYS = {
    "aggregate_contract", "authority_artifacts", "authority_objects", "budget", "classification",
    "contour_id", "controller_bytes", "controller_relative_path", "controller_sha256",
    "destination_relative_path", "epic_id", "executor_bytes", "executor_relative_path",
    "executor_sha256", "expected_secret_parent_state", "expires_at_utc", "failure_policy",
    "fixture_alias", "gitignore_bytes", "gitignore_relative_path", "gitignore_sha256",
    "inline_bootstrap_bytes", "inline_bootstrap_sha256", "input_contract", "issued_at_utc",
    "loader_bytes", "loader_relative_path", "loader_sha256", "marker_relative_path",
    "output_contract", "parent_observation_contract", "plan_relative_path", "repository_head", "result_relative_path", "run_id",
    "schema_version", "security_alias", "security_go_relative_path", "terminal_result_contract",
    "timeout_contract", "workspace_allowlist",
}


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _exact(left, right):
    if type(left) is not type(right): return False
    if type(right) is dict: return set(left) == set(right) and all(_exact(left[key], right[key]) for key in right)
    if type(right) is list: return len(left) == len(right) and all(_exact(a, b) for a, b in zip(left, right))
    return left == right


def _aggregate(created):
    return {
        "application_action_count": 0, "authentication_action_count": 0,
        "contour_id": CONTOUR_ID, "destination_directory_created_count": created,
        "device_action_count": 0, "host_process_count": 1, "marker_file_created_count": 1,
        "git_head_validation_count": 2, "git_metadata_content_read_count_max": 8,
        "git_metadata_path_target_count_max": 64,
        "network_action_count": 0, "no_echo_secret_field_read_count": 2,
        "runtime_action_count": 0, "schema_version": AGGREGATE_SCHEMA,
        "secret_file_created_count": 1, "secret_payload_readback_count": 1,
        "secret_payload_write_count": 1, "status": "fixture_provisioned",
        "subprocess_count": 0, "terminal_result_file_created_count": 1, "ui_action_count": 0,
    }


def _terminal_result_contract():
    return {"schema_version": TERMINAL_RESULT_SCHEMA, "result_alias": PROVISION_RESULT_ALIAS,
            "allowed_terminal_states": ["fixture_provisioned", "blocked_before_attempt", "blocked_after_attempt"],
            "exit_category_by_terminal_state": {"blocked_after_attempt": "blocked",
                                                "blocked_before_attempt": "blocked",
                                                "fixture_provisioned": "success"},
            "execution_stages_by_terminal_state": {
                "blocked_after_attempt": ["marker_created", "secret_parent_ready",
                                          "console_input_in_progress", "destination_write_in_progress",
                                          "destination_written", "unknown_after_marker"],
                "blocked_before_attempt": ["pre_attempt"],
                "fixture_provisioned": ["terminal_result_finalization"]},
            "always_exact_zero_counters": ["application_action_count", "authentication_action_count",
                                           "device_action_count", "network_action_count",
                                           "runtime_action_count", "subprocess_count", "ui_action_count"],
            "state_counter_rules": {
                "blocked_after_attempt": {"destination_directory_created_count": [0, 1, "unknown"],
                                          "marker_file_created_count": 1},
                "blocked_before_attempt": "all_counters_exact_integer_zero",
                "fixture_provisioned": {"destination_directory_created_count": [0, 1],
                                        "marker_file_created_count": 1}},
            "boolean_counter_values": "forbidden",
            "secret_derived_values_hashes_lengths": "forbidden"}


def _shape(value, depth=0):
    if depth > MAX_DEPTH or value is None or isinstance(value, float): raise ValueError
    if type(value) is int and abs(value) > MAX_INTEGER: raise ValueError
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value or any(0xD800 <= ord(ch) <= 0xDFFF for ch in value): raise ValueError
    elif type(value) is list:
        for item in value: _shape(item, depth + 1)
    elif type(value) is dict:
        for key, item in value.items(): _shape(key, depth + 1); _shape(item, depth + 1)
    elif type(value) not in (bool, int): raise ValueError


def _parse_time(value):
    if type(value) is not str or not value.endswith("Z"): raise ValueError
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.utcoffset() != timedelta(0): raise ValueError
    return parsed


def _plan():
    initial_wall = datetime.now(UTC)
    raw = _load_fixed_input(Path.cwd() / PLAN_REL, MAX_PLAN)
    if not raw or len(raw) > MAX_PLAN or raw.startswith(b"\xef\xbb\xbf"): raise ValueError
    def hook(items):
        out, norms = {}, set()
        for key, value in items:
            norm = unicodedata.normalize("NFC", key)
            if key in out or norm in norms: raise ValueError
            out[key] = value; norms.add(norm)
        return out
    plan = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=hook)
    if type(plan) is not dict or set(plan) != ROOT_KEYS: raise ValueError
    _shape(plan)
    if _canonical(plan) != raw: raise ValueError
    fixed = {
        "classification": "PROD_CONDITIONAL", "contour_id": CONTOUR_ID,
        "destination_relative_path": ".qa_local/secrets/qa_user.env", "epic_id": "EPIC-PHONE-001",
        "executor_relative_path": EXECUTOR_REL,
        "failure_policy": "marker_before_console_reads_terminal_result_create_new_best_effort_no_retry_overwrite_delete_rename_or_cleanup",
        "fixture_alias": "epic-phone-001-fixture-001", "gitignore_relative_path": ".gitignore",
        "input_contract": "two_real_console_no_echo_ascii_digit_fields_total_chars_max_128",
        "loader_relative_path": LOADER_REL,
        "marker_relative_path": ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/fixture-owner-provision-003-attempt.local.json",
        "output_contract": "exact_two_ascii_lf_lines_payload_max_96",
        "parent_observation_contract": {"stdout": "not_used", "pid": "start_process_pid",
                                        "exit_code": "zero_success_two_blocked", "result_alias": PROVISION_RESULT_ALIAS},
        "terminal_result_contract": _terminal_result_contract(),
        "plan_relative_path": PLAN_REL,
        "result_relative_path": RESULT_REL,
        "run_id": RUN_ID,
        "schema_version": SCHEMA, "security_alias": "epic-phone-001-security-owner-local-fixture-provision-003",
        "security_go_relative_path": SECURITY_GO_REL,
        "timeout_contract": TIMEOUT_CONTRACT,
    }
    if any(not _exact(plan.get(key), value) for key, value in fixed.items()): raise ValueError
    repository_head = plan.get("repository_head")
    if type(repository_head) is not str or len(repository_head) != 40 or any(ch not in "0123456789abcdef" for ch in repository_head): raise ValueError
    state = plan.get("expected_secret_parent_state")
    if state not in ("present", "absent") or not _exact(plan.get("budget"), BUDGET) or not _exact(plan.get("aggregate_contract"), _aggregate(0 if state == "present" else 1)):
        raise ValueError
    for key in ("executor_sha256", "loader_sha256", "inline_bootstrap_sha256", "controller_sha256", "gitignore_sha256"):
        if type(plan.get(key)) is not str or HEX64.fullmatch(plan[key]) is None: raise ValueError
    for key in ("executor_bytes", "loader_bytes", "inline_bootstrap_bytes", "controller_bytes", "gitignore_bytes"):
        if type(plan.get(key)) is not int or not 0 < plan[key] <= MAX_SOURCE: raise ValueError
    authorities = plan.get("authority_objects")
    expected_aliases = {
        "cooperative_timeout_acceptance": "epic-phone-001-owner-cooperative-timeout-acceptance-003",
        "fixture_authority": "epic-phone-001-fixture-authority-owner-provision-003",
        "owner_local_console_entry": "epic-phone-001-owner-local-console-entry-003",
        "provision_no_mutator_window": "epic-phone-001-owner-local-provision-no-mutator-003",
    }
    if type(authorities) is not dict or set(authorities) != set(expected_aliases): raise ValueError
    scopes = {
        "cooperative_timeout_acceptance": TIMEOUT_CONTRACT["owner_acceptance_scope"],
        "fixture_authority": "synthetic_fixture_alias_only",
        "owner_local_console_entry": "console_values_only_fixture_alias_not_recorded",
        "provision_no_mutator_window": NO_MUTATOR_SCOPE,
    }
    expected_statuses = {"cooperative_timeout_acceptance": "accepted_by_owner",
                         "fixture_authority": "confirmed", "owner_local_console_entry": "confirmed",
                         "provision_no_mutator_window": "confirmed_by_owner"}
    for key, alias in expected_aliases.items():
        item = authorities[key]
        if (type(item) is not dict or set(item) != {"alias", "expires_at_utc", "scope", "status"} or
                item.get("alias") != alias or item.get("scope") != scopes[key] or item.get("status") != expected_statuses[key]):
            raise ValueError
    workspace = plan.get("workspace_allowlist")
    if type(workspace) is not list or len(workspace) != len(WORKSPACE_CONTRACT): raise ValueError
    for item, (path, status) in zip(workspace, WORKSPACE_CONTRACT):
        if (type(item) is not dict or set(item) != {"bytes", "path", "sha256", "status"} or
                item.get("path") != path or item.get("status") != status or
                type(item.get("bytes")) is not int or not 0 < item["bytes"] <= 4 * 1024 * 1024 or
                type(item.get("sha256")) is not str or HEX64.fullmatch(item["sha256"]) is None or
                "\\" in path or ":" in path or path.startswith("/") or any(part in ("", ".", "..") for part in path.split("/"))):
            raise ValueError
    artifacts = plan.get("authority_artifacts")
    paths = (
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/c0p-plan.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/fixture-authority-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/target-build-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/evidence-cleanup-passport.local.json",
    )
    schemas = ("epic-phone-001-c0p-plan-v2", "epic-phone-001-fixture-authority-passport-v2",
               "epic-phone-001-target-build-passport-v2", "epic-phone-001-evidence-cleanup-passport-v2")
    artifact_contracts = (
        ("epic-phone-001-security-c0p-005", "execution_status", "planned_separate_literal_go_required_not_run", "expires_at_utc"),
        ("epic-phone-001-fixture-001", "revoked", False, "expires_at_utc"),
        ("phone-current-001", "target_authorized", True, "expires_at_utc"),
        ("policy_readiness_only", "execution_evidence", False, "retention_expires_at_utc"),
    )
    if type(artifacts) is not list or len(artifacts) != 4: raise ValueError
    for index, item in enumerate(artifacts):
        if (type(item) is not dict or set(item) != {"alias", "bytes", "embedded_expiry_field", "embedded_expiry_value",
                                                    "embedded_status_field", "embedded_status_value", "path", "schema_version", "sha256"} or
                item.get("path") != paths[index] or item.get("schema_version") != schemas[index] or
                type(item.get("bytes")) is not int or not 0 < item["bytes"] <= 4 * 1024 * 1024 or
                type(item.get("sha256")) is not str or HEX64.fullmatch(item["sha256"]) is None):
            raise ValueError
        alias, status_field, status_value, expiry_field = artifact_contracts[index]
        if (item.get("alias") != alias or item.get("embedded_status_field") != status_field or
                not _exact(item.get("embedded_status_value"), status_value) or
                item.get("embedded_expiry_field") != expiry_field): raise ValueError
        if expiry_field == "none":
            if item.get("embedded_expiry_value") != "none": raise ValueError
        elif type(item.get("embedded_expiry_value")) is not str:
            raise ValueError
    digest = hashlib.sha256(raw).hexdigest()
    go_raw = _load_fixed_input(Path.cwd() / SECURITY_GO_REL, MAX_PLAN)
    go = json.loads(go_raw.decode("utf-8", errors="strict"), object_pairs_hook=hook)
    _shape(go)
    if _canonical(go) != go_raw: raise ValueError
    expected_go = {
        "schema_version": SECURITY_GO_SCHEMA, "epic_id": "EPIC-PHONE-001", "run_id": RUN_ID,
        "contour_id": CONTOUR_ID, "security_alias": "epic-phone-001-security-owner-local-fixture-provision-003",
        "plan_sha256": digest, "literal_go": GO_PREFIX + digest,
        "issued_at_utc": go.get("issued_at_utc"), "expires_at_utc": go.get("expires_at_utc"),
    }
    if not _exact(go, expected_go): raise ValueError
    go_issued, go_expires = _parse_time(go["issued_at_utc"]), _parse_time(go["expires_at_utc"])
    if not go_issued <= initial_wall < go_expires or go_expires > _parse_time(plan["expires_at_utc"]): raise ValueError
    issued, expires = _parse_time(plan["issued_at_utc"]), _parse_time(plan["expires_at_utc"])
    if expires <= issued or expires - issued > timedelta(minutes=10): raise ValueError
    wall = _parse_time(os.environ.get(BOOTSTRAP_WALL_ENV)); deadline_text = os.environ.get(DEADLINE_ENV)
    if type(deadline_text) is not str or not deadline_text.isascii() or not deadline_text.isdigit() or len(deadline_text) > 24: raise ValueError
    deadline = int(deadline_text)
    mono_before = time.monotonic_ns()
    fresh_wall = datetime.now(UTC)
    mono_after = time.monotonic_ns()
    if (fresh_wall < initial_wall or mono_after < mono_before or
            not issued <= wall <= fresh_wall < expires or
            not mono_before < deadline <= mono_before + 120_000_000_000): raise ValueError
    remaining_seconds = (deadline - mono_before + 999_999_999) // 1_000_000_000
    bootstrap_bound = wall + timedelta(seconds=121)
    validation_bound = fresh_wall + timedelta(seconds=remaining_seconds + 1)
    conservative_execution_end = max(bootstrap_bound, validation_bound)
    if expires < conservative_execution_end: raise ValueError
    required_until = max(expires, conservative_execution_end)
    if any(_parse_time(item["expires_at_utc"]) < required_until for item in authorities.values()): raise ValueError
    for item in artifacts:
        if item["embedded_expiry_field"] != "none" and _parse_time(item["embedded_expiry_value"]) < required_until: raise ValueError
    return plan, digest


def _readiness_plan():
    now = datetime.now(UTC)
    raw = _load_fixed_input(Path.cwd() / READINESS_PLAN_REL, MAX_PLAN)
    def hook(items):
        out, norms = {}, set()
        for key, value in items:
            norm = unicodedata.normalize("NFC", key)
            if key in out or norm in norms: raise ValueError
            out[key] = value; norms.add(norm)
        return out
    plan = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=hook)
    _shape(plan)
    if type(plan) is not dict or _canonical(plan) != raw: raise ValueError
    fixed = {
        "schema_version": READINESS_PLAN_SCHEMA, "epic_id": "EPIC-PHONE-001", "run_id": RUN_ID,
        "contour_id": READINESS_CONTOUR_ID, "attempt_id": READINESS_ATTEMPT_ID,
        "classification": "PROD_SAFE", "scope_qualifier": "ZERO_SECRET_ZERO_DEVICE_VISIBLE_CONSOLE_READINESS",
        "security_alias": READINESS_SECURITY_ALIAS, "executor_relative_path": EXECUTOR_REL,
        "loader_relative_path": LOADER_REL, "plan_relative_path": READINESS_PLAN_REL,
        "security_go_relative_path": READINESS_GO_REL,
        "marker_relative_path": ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/owner-local-console-readiness-001-attempt.local.json",
        "result_relative_path": READINESS_RESULT_REL,
        "budget": {"host_process_max": 1, "source_read_max": 2,
                   "fixed_plan_file_read_max": 1, "fixed_go_file_read_max": 1,
                   "git_head_validation_max": 1, "git_metadata_content_read_max": 4,
                   "git_metadata_path_target_max": 32, "bootstrap_env_write_max": 3,
                   "console_api_validation_max": 3, "secret_read_max": 0,
                   "acl_create_max": 2, "acl_check_max": 2, "created_file_readback_max": 2,
                   "authority_artifact_read_max": 0, "device_action_max": 0,
                   "application_action_max": 0, "network_action_max": 0,
                   "marker_file_create_max": 1, "result_file_create_max": 1,
                   "retry_max": 0, "wall_clock_seconds_max": 120},
        "failure_policy": "marker_first_result_best_effort_no_retry_no_cleanup_no_reuse",
    }
    if any(not _exact(plan.get(key), value) for key, value in fixed.items()): raise ValueError
    expected_keys = set(fixed) | {"repository_head", "executor_bytes", "executor_sha256", "loader_bytes",
                                  "loader_sha256", "inline_bootstrap_bytes", "inline_bootstrap_sha256",
                                  "issued_at_utc", "expires_at_utc"}
    if set(plan) != expected_keys: raise ValueError
    head = plan["repository_head"]
    if type(head) is not str or len(head) != 40 or any(ch not in "0123456789abcdef" for ch in head): raise ValueError
    for key in ("executor_sha256", "loader_sha256", "inline_bootstrap_sha256"):
        if type(plan[key]) is not str or HEX64.fullmatch(plan[key]) is None: raise ValueError
    for key in ("executor_bytes", "loader_bytes", "inline_bootstrap_bytes"):
        if type(plan[key]) is not int or not 0 < plan[key] <= MAX_SOURCE: raise ValueError
    issued, expires = _parse_time(plan["issued_at_utc"]), _parse_time(plan["expires_at_utc"])
    if expires <= issued or expires - issued > timedelta(minutes=10) or not issued <= now < expires: raise ValueError
    wall = _parse_time(os.environ.get(BOOTSTRAP_WALL_ENV)); deadline_text = os.environ.get(DEADLINE_ENV)
    if type(deadline_text) is not str or not deadline_text.isascii() or not deadline_text.isdigit() or len(deadline_text) > 24: raise ValueError
    deadline = int(deadline_text); mono_before = time.monotonic_ns(); fresh_wall = datetime.now(UTC); mono_after = time.monotonic_ns()
    if (fresh_wall < now or mono_after < mono_before or not issued <= wall <= fresh_wall < expires or
            not mono_before < deadline <= mono_before + 120_000_000_000): raise ValueError
    remaining_seconds = (deadline - mono_before + 999_999_999) // 1_000_000_000
    if expires < max(wall + timedelta(seconds=121), fresh_wall + timedelta(seconds=remaining_seconds + 1)): raise ValueError
    digest = hashlib.sha256(raw).hexdigest()
    go_raw = _load_fixed_input(Path.cwd() / READINESS_GO_REL, MAX_PLAN)
    go = json.loads(go_raw.decode("utf-8", errors="strict"), object_pairs_hook=hook)
    _shape(go)
    expected_go = {"schema_version": READINESS_GO_SCHEMA, "epic_id": "EPIC-PHONE-001", "run_id": RUN_ID,
                   "contour_id": READINESS_CONTOUR_ID, "attempt_id": READINESS_ATTEMPT_ID,
                   "security_alias": READINESS_SECURITY_ALIAS, "plan_sha256": digest,
                   "literal_go": READINESS_GO_PREFIX + digest,
                   "issued_at_utc": go.get("issued_at_utc"), "expires_at_utc": go.get("expires_at_utc")}
    if _canonical(go) != go_raw or not _exact(go, expected_go): raise ValueError
    go_issued, go_expires = _parse_time(go["issued_at_utc"]), _parse_time(go["expires_at_utc"])
    if not go_issued <= now < go_expires or go_expires > expires: raise ValueError
    return plan, digest


def _fixed_drive(path):
    if os.name != "nt" or not path.is_absolute() or not path.drive or str(path).startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")):
        raise ValueError
    import ctypes
    if ctypes.windll.kernel32.GetDriveTypeW(path.anchor) != 3: raise ValueError


def _safe_absolute_chain(path):
    absolute = path.absolute(); _fixed_drive(absolute); current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part; item = current.lstat()
        if stat.S_ISLNK(item.st_mode) or getattr(item, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError


def _track_git_path(path, budget):
    budget["targets"].add(str(path.absolute()))
    if len(budget["targets"]) > BUDGET["git_metadata_path_target_max"] // 2: raise ValueError


def _probe_optional_git_path(path, budget):
    absolute = path.absolute(); _fixed_drive(absolute); current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part; _track_git_path(current, budget)
        try: item = current.lstat()
        except FileNotFoundError: return False
        if stat.S_ISLNK(item.st_mode) or getattr(item, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError
    return True


def _read_git_metadata(path, budget, maximum=4096):
    _track_git_path(path, budget); budget["content_reads"] += 1
    if budget["content_reads"] > BUDGET["git_metadata_content_read_max"] // 2: raise ValueError
    _safe_absolute_chain(path); before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum: raise ValueError
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); data = os.read(fd, maximum + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or len(data) != before.st_size): raise ValueError
    return data


def _actual_repository_head(root=None):
    base = (root or Path.cwd()).absolute(); _fixed_drive(base); budget = {"content_reads": 0, "targets": set()}
    marker = base / ".git"; _track_git_path(marker, budget); _safe_absolute_chain(marker); info = marker.lstat()
    if stat.S_ISDIR(info.st_mode):
        gitdir = marker
    elif stat.S_ISREG(info.st_mode):
        raw = _read_git_metadata(marker, budget).decode("utf-8", errors="strict").strip()
        if not raw.startswith("gitdir: "): raise ValueError
        value = raw[8:]
        if not value or value.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")): raise ValueError
        gitdir = Path(value) if Path(value).is_absolute() else base / value
        gitdir = Path(os.path.abspath(gitdir)); _track_git_path(gitdir, budget); _safe_absolute_chain(gitdir)
    else: raise ValueError
    common = gitdir; commondir = gitdir / "commondir"; _track_git_path(commondir, budget)
    try: commondir_info = commondir.lstat()
    except FileNotFoundError: commondir_info = None
    if commondir_info is not None:
        raw_common = _read_git_metadata(commondir, budget).decode("utf-8", errors="strict").strip()
        if not raw_common or raw_common.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")): raise ValueError
        common = Path(raw_common) if Path(raw_common).is_absolute() else gitdir / raw_common
        common = Path(os.path.abspath(common)); _track_git_path(common, budget); _safe_absolute_chain(common)
    head = _read_git_metadata(gitdir / "HEAD", budget).decode("ascii", errors="strict").strip()
    if len(head) == 40 and all(ch in "0123456789abcdef" for ch in head): return head, budget["content_reads"], len(budget["targets"])
    if not head.startswith("ref: "): raise ValueError
    ref = head[5:]
    if not ref.startswith("refs/") or "\\" in ref or ":" in ref or any(part in ("", ".", "..") for part in ref.split("/")): raise ValueError
    loose = common.joinpath(*ref.split("/"))
    if _probe_optional_git_path(loose, budget):
        value = _read_git_metadata(loose, budget).decode("ascii", errors="strict").strip()
        if len(value) == 40 and all(ch in "0123456789abcdef" for ch in value): return value, budget["content_reads"], len(budget["targets"])
        raise ValueError
    packed = _read_git_metadata(common / "packed-refs", budget, 32768).decode("ascii", errors="strict"); matches = []
    for line in packed.splitlines():
        if not line or line.startswith(("#", "^")): continue
        parts = line.split(" ")
        if len(parts) != 2: raise ValueError
        if parts[1] == ref: matches.append(parts[0])
    if len(matches) != 1 or len(matches[0]) != 40 or any(ch not in "0123456789abcdef" for ch in matches[0]): raise ValueError
    return matches[0], budget["content_reads"], len(budget["targets"])


def _load_executor(path: Path, expected_bytes: int, expected_sha: str) -> bytes:
    if os.name != "nt": raise ValueError
    import ctypes
    root, absolute = Path.cwd().absolute(), path.absolute()
    if ctypes.windll.kernel32.GetDriveTypeW(root.anchor) != 3 or os.path.commonpath((str(root), str(absolute))) != str(root): raise ValueError
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part; item = current.lstat()
        if stat.S_ISLNK(item.st_mode) or getattr(item, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size != expected_bytes: raise ValueError
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); source = os.read(fd, expected_bytes + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or
            len(source) != expected_bytes or hashlib.sha256(source).hexdigest() != expected_sha): raise ValueError
    return source


def _load_fixed_input(path: Path, maximum: int) -> bytes:
    if os.name != "nt": raise ValueError
    import ctypes
    root, absolute = Path.cwd().absolute(), path.absolute()
    if ctypes.windll.kernel32.GetDriveTypeW(root.anchor) != 3 or os.path.commonpath((str(root), str(absolute))) != str(root): raise ValueError
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part; item = current.lstat()
        if stat.S_ISLNK(item.st_mode) or getattr(item, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum: raise ValueError
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); source = os.read(fd, maximum + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or
            len(source) != before.st_size): raise ValueError
    return source


def _consume_terminal_io_budget(counter: str) -> None:
    if _ACTIVE_TERMINAL_IO_BUDGET is None:
        return
    budget_key = {"content_reads": "loader_terminal_result_content_read_max",
                  "validations": "loader_terminal_result_validation_max"}.get(counter)
    if budget_key is None or type(_ACTIVE_TERMINAL_IO_BUDGET.get(counter)) is not int:
        raise ValueError
    _ACTIVE_TERMINAL_IO_BUDGET[counter] += 1
    if _ACTIVE_TERMINAL_IO_BUDGET[counter] > BUDGET[budget_key]:
        raise ValueError


def _load_and_validate_terminal_result(path: Path, plan_sha256: str) -> bytes:
    _consume_terminal_io_budget("content_reads")
    raw = _load_fixed_input(path, MAX_PLAN)
    _validate_terminal_result(raw, plan_sha256)
    return raw


def _write_blocked_result(plan_sha256: str) -> None:
    path = Path.cwd() / RESULT_REL
    _safe_absolute_chain(path.parent)
    try: existing = path.lstat()
    except FileNotFoundError: existing = None
    if existing is not None:
        if stat.S_ISLNK(existing.st_mode) or getattr(existing, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError
        _load_and_validate_terminal_result(path, plan_sha256)
        return
    marker = Path.cwd() / PROVISION_MARKER_REL
    _safe_absolute_chain(marker.parent)
    try: marker_info = marker.lstat()
    except FileNotFoundError: marker_info = None
    if marker_info is not None and (stat.S_ISLNK(marker_info.st_mode) or getattr(marker_info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE): raise ValueError
    after_attempt = marker_info is not None
    deadline_text = os.environ.get(DEADLINE_ENV)
    if type(deadline_text) is not str or not deadline_text.isdigit() or time.monotonic_ns() >= int(deadline_text): raise ValueError
    payload = _canonical({
        "schema_version": TERMINAL_RESULT_SCHEMA, "epic_id": "EPIC-PHONE-001", "run_id": RUN_ID,
        "contour_id": CONTOUR_ID, "attempt_id": "fixture-owner-provision-003",
        "result_alias": PROVISION_RESULT_ALIAS, "plan_sha256": plan_sha256,
        "terminal_state": "blocked_after_attempt" if after_attempt else "blocked_before_attempt",
        "exit_category": "blocked", "execution_stage": "unknown_after_marker" if after_attempt else "pre_attempt",
        "aggregate_counters": {
            "application_action_count": 0, "authentication_action_count": 0,
            "destination_directory_created_count": "unknown" if after_attempt else 0,
            "device_action_count": 0, "marker_file_created_count": 1 if after_attempt else 0,
            "network_action_count": 0, "runtime_action_count": 0,
            "subprocess_count": 0, "ui_action_count": 0,
        },
    }) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if os.write(fd, payload) != len(payload): raise ValueError
        os.fsync(fd)
    finally:
        os.close(fd)


def _validate_terminal_result(raw: bytes, plan_sha256: str) -> None:
    _consume_terminal_io_budget("validations")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"): raise ValueError
    body = raw[:-1]
    value = json.loads(body.decode("utf-8", errors="strict"))
    if type(value) is not dict or _canonical(value) != body: raise ValueError
    required = {"schema_version", "epic_id", "run_id", "contour_id", "attempt_id", "result_alias",
                "plan_sha256", "terminal_state", "exit_category", "execution_stage", "aggregate_counters"}
    if set(value) != required: raise ValueError
    contract = _terminal_result_contract()
    if (value["schema_version"] != TERMINAL_RESULT_SCHEMA or value["epic_id"] != "EPIC-PHONE-001" or
            value["run_id"] != RUN_ID or value["contour_id"] != CONTOUR_ID or
            value["attempt_id"] != "fixture-owner-provision-003" or
            value["result_alias"] != PROVISION_RESULT_ALIAS or value["plan_sha256"] != plan_sha256 or
            value["terminal_state"] not in contract["allowed_terminal_states"]): raise ValueError
    state = value["terminal_state"]
    if (value["exit_category"] != contract["exit_category_by_terminal_state"][state] or
            value["execution_stage"] not in contract["execution_stages_by_terminal_state"][state]): raise ValueError
    counters = value["aggregate_counters"]
    counter_keys = {"application_action_count", "authentication_action_count", "destination_directory_created_count",
                    "device_action_count", "marker_file_created_count", "network_action_count",
                    "runtime_action_count", "subprocess_count", "ui_action_count"}
    if type(counters) is not dict or set(counters) != counter_keys: raise ValueError
    for key in contract["always_exact_zero_counters"]:
        if type(counters[key]) is not int or counters[key] != 0: raise ValueError
    directory_count = counters["destination_directory_created_count"]
    marker_count = counters["marker_file_created_count"]
    if state == "blocked_before_attempt":
        if any(type(item) is not int or item != 0 for item in counters.values()): raise ValueError
    elif state == "blocked_after_attempt":
        if (type(marker_count) is not int or marker_count != 1 or
                not ((type(directory_count) is int and directory_count in (0, 1)) or
                     directory_count == "unknown")): raise ValueError
    elif (type(marker_count) is not int or marker_count != 1 or
          type(directory_count) is not int or directory_count not in (0, 1)):
        raise ValueError


def _provision_attempt_consumed(plan_sha256: str) -> bool:
    result = Path.cwd() / RESULT_REL; marker = Path.cwd() / PROVISION_MARKER_REL
    _safe_absolute_chain(result.parent)
    try: result_info = result.lstat()
    except FileNotFoundError: result_info = None
    if result_info is not None:
        if stat.S_ISLNK(result_info.st_mode) or getattr(result_info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError
        _load_and_validate_terminal_result(result, plan_sha256)
        return True
    try: marker_info = marker.lstat()
    except FileNotFoundError: marker_info = None
    if marker_info is not None:
        if stat.S_ISLNK(marker_info.st_mode) or getattr(marker_info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError
        return True
    return False


def _require_result_finalization_reserve() -> None:
    value = os.environ.get(DEADLINE_ENV)
    if type(value) is not str or not value.isdigit(): raise ValueError
    if int(value) - time.monotonic_ns() <= RESULT_FINALIZATION_RESERVE_SECONDS * 1_000_000_000: raise ValueError


def _write_readiness_blocked_result(plan_sha256: str) -> None:
    payload = _canonical({
        "schema_version": READINESS_RESULT_SCHEMA, "epic_id": "EPIC-PHONE-001", "run_id": RUN_ID,
        "contour_id": READINESS_CONTOUR_ID, "attempt_id": READINESS_ATTEMPT_ID,
        "result_alias": READINESS_RESULT_ALIAS,
        "plan_sha256": plan_sha256, "terminal_state": "blocked_before_attempt",
        "exit_category": "blocked",
        "aggregate_counters": {"authority_artifact_read_count": 0, "secret_read_count": 0,
                               "device_action_count": 0, "application_action_count": 0,
                               "network_action_count": 0, "marker_file_created_count": 0,
                               "result_file_created_count": 1},
    }) + b"\n"
    path = Path.cwd() / READINESS_RESULT_REL
    _safe_absolute_chain(path.parent)
    try: existing = path.lstat()
    except FileNotFoundError: existing = None
    if existing is not None: return
    marker = Path.cwd() / ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/owner-local-console-readiness-001-attempt.local.json"
    try: marker_info = marker.lstat()
    except FileNotFoundError: marker_info = None
    if marker_info is not None: raise ValueError
    deadline_text = os.environ.get(DEADLINE_ENV)
    if type(deadline_text) is not str or not deadline_text.isdigit() or time.monotonic_ns() >= int(deadline_text): raise ValueError
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if os.write(fd, payload) != len(payload): raise ValueError
        os.fsync(fd)
    finally:
        os.close(fd)


def main() -> int:
    global _ACTIVE_TERMINAL_IO_BUDGET
    digest = None
    mode = os.environ.get(READINESS_MODE_ENV)
    readiness = mode == "readiness"
    _ACTIVE_TERMINAL_IO_BUDGET = {"content_reads": 0, "validations": 0}
    try:
        if mode not in ("provision", "readiness"): raise ValueError
        plan, digest = _readiness_plan() if readiness else _plan()
        target = Path.cwd() / EXECUTOR_REL
        actual_head, git_content_reads, git_path_targets = _actual_repository_head(Path.cwd())
        if actual_head != plan["repository_head"]: raise ValueError
        if not readiness and _provision_attempt_consumed(digest): return 2
        _require_result_finalization_reserve()
        source = _load_executor(target, plan["executor_bytes"], plan["executor_sha256"])
        sys.dont_write_bytecode = True
        namespace = {"__name__": "__owner_fixture_executor__", "__file__": str(target), "__package__": None,
                     LOADER_GIT_CHECK_GLOBAL: 1, LOADER_GIT_CONTENT_GLOBAL: git_content_reads,
                     LOADER_GIT_PATH_GLOBAL: git_path_targets}
        exec(compile(source, str(target), "exec", dont_inherit=True), namespace, namespace)
        _require_result_finalization_reserve()
        if readiness:
            bootstrap = namespace["build_readiness_inline_bootstrap"](
                loader_bytes=plan["loader_bytes"], loader_sha256=plan["loader_sha256"])
            if len(bootstrap) != plan["inline_bootstrap_bytes"] or hashlib.sha256(bootstrap).hexdigest() != plan["inline_bootstrap_sha256"]:
                raise ValueError
            entry = namespace.get("readiness_main")
            if not callable(entry):
                _write_readiness_blocked_result(digest); return 2
            result = entry(plan, digest)
            if type(result) is not int or result != 0:
                _write_readiness_blocked_result(digest); return 2
            return 0
        entry = namespace.get("main")
        if not callable(entry):
            _write_blocked_result(digest); return 2
        result = entry()
        if type(result) is not int or result != 0:
            _write_blocked_result(digest); return 2
        result_data = _load_and_validate_terminal_result(Path.cwd() / RESULT_REL, digest)
        parsed = json.loads(result_data[:-1].decode("utf-8"))
        return 0 if parsed["terminal_state"] == "fixture_provisioned" else 2
    except BaseException:
        if digest is not None:
            try: (_write_readiness_blocked_result if readiness else _write_blocked_result)(digest)
            except BaseException: pass
        return 2
    finally:
        _ACTIVE_TERMINAL_IO_BUDGET = None


if __name__ == "__main__": sys.exit(main())

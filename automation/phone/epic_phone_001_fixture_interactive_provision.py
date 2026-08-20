#!/usr/bin/env python3
"""Owner-local, one-shot provisioning of the synthetic EPIC fixture."""

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
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
EPIC_ID = "EPIC-PHONE-001"
RUN_ID = "epic-phone-001-20260816-r01"
CONTOUR_ID = "epic-phone-001-owner-local-fixture-provision"
SCHEMA = "epic-phone-001-owner-local-fixture-provision-plan-v1"
MARKER_SCHEMA = "epic-phone-001-owner-local-fixture-provision-attempt-v1"
AGGREGATE_SCHEMA = "epic-phone-001-owner-local-fixture-provision-aggregate-v2"
TERMINAL_RESULT_SCHEMA = "epic-phone-001-owner-local-fixture-provision-terminal-result-v1"
SECURITY_GO_SCHEMA = "epic-phone-001-owner-local-fixture-provision-security-go-v1"
PLAN_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION_PLAN"
GO_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION_GO"
GO_PREFIX = f"GO_EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION__{RUN_ID}__"
DEADLINE_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_DEADLINE_MONOTONIC_NS"
BOOTSTRAP_WALL_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_BOOTSTRAP_WALL_UTC"
EXECUTOR_REL = Path("automation/phone/epic_phone_001_fixture_interactive_provision.py")
LOADER_REL = Path("automation/phone/epic_phone_001_owner_local_fixture_loader.py")
CONTROLLER_REL = Path("automation/phone/epic_phone_001_runtime_controller.py")
GITIGNORE_REL = Path(".gitignore")
RUN_REL = Path(".qa_local/evidence/epic-phone-001") / RUN_ID
AUTHORITY_SET_REL = RUN_REL / "authority-sets/c0p-authority-005"
PROVISION_PLAN_REL = RUN_REL / "fixture-owner-provision-003-plan.local.json"
PROVISION_GO_REL = RUN_REL / "security-go-owner-local-fixture-provision-003.local.json"
MARKER_REL = RUN_REL / "fixture-owner-provision-003-attempt.local.json"
RESULT_REL = RUN_REL / "fixture-owner-provision-003-result.local.json"
DESTINATION_REL = Path(".qa_local/secrets/qa_user.env")
AUTHORITY_PATHS = (
    AUTHORITY_SET_REL / "c0p-plan.local.json",
    AUTHORITY_SET_REL / "fixture-authority-passport.local.json",
    AUTHORITY_SET_REL / "target-build-passport.local.json",
    AUTHORITY_SET_REL / "evidence-cleanup-passport.local.json",
)
WORKSPACE_ALLOWLIST_CONTRACT: tuple[tuple[str, str], ...] = ()
FIXTURE_AUTHORITY_ALIAS = "epic-phone-001-fixture-authority-owner-provision-003"
OWNER_CONSOLE_ALIAS = "epic-phone-001-owner-local-console-entry-003"
NO_MUTATOR_ALIAS = "epic-phone-001-owner-local-provision-no-mutator-003"
COOPERATIVE_TIMEOUT_ALIAS = "epic-phone-001-owner-cooperative-timeout-acceptance-003"
PROVISION_SECURITY_ALIAS = "epic-phone-001-security-owner-local-fixture-provision-003"
PROVISION_RESULT_ALIAS = "epic-phone-001-owner-local-fixture-provision-result-003"
READINESS_CONTOUR_ID = "epic-phone-001-owner-local-console-readiness"
READINESS_ATTEMPT_ID = "owner-local-console-readiness-001"
READINESS_SECURITY_ALIAS = "epic-phone-001-security-owner-local-console-readiness-001"
READINESS_RESULT_ALIAS = "epic-phone-001-owner-local-console-readiness-result-001"
READINESS_PLAN_REL = RUN_REL / "owner-local-console-readiness-001-plan.local.json"
READINESS_GO_REL = RUN_REL / "security-go-owner-local-console-readiness-001.local.json"
READINESS_MARKER_REL = RUN_REL / "owner-local-console-readiness-001-attempt.local.json"
READINESS_RESULT_REL = RUN_REL / "owner-local-console-readiness-001-result.local.json"
READINESS_PLAN_SCHEMA = "epic-phone-001-owner-local-console-readiness-plan-v1"
READINESS_GO_SCHEMA = "epic-phone-001-owner-local-console-readiness-security-go-v1"
READINESS_MARKER_SCHEMA = "epic-phone-001-owner-local-console-readiness-attempt-v1"
READINESS_RESULT_SCHEMA = "epic-phone-001-owner-local-console-readiness-result-v1"
READINESS_MODE_ENV = "EPIC_PHONE_001_OWNER_LOCAL_CONSOLE_CONTOUR"
READINESS_GO_PREFIX = f"GO_EPIC_PHONE_001_OWNER_LOCAL_CONSOLE_READINESS__{RUN_ID}__"
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
MAX_PLAN = 64 * 1024
MAX_BOUND_FILE = 4 * 1024 * 1024
MAX_PAYLOAD = 96
MAX_INPUT_CHARS = 128
MAX_DEPTH = 12
MAX_INTEGER = 9_007_199_254_740_991
REPARSE_ATTRIBUTE = 0x400
CREATE_NEW = 1
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
AUTHORITY_COVERAGE_GUARD_SECONDS = 1
RESULT_FINALIZATION_RESERVE_SECONDS = 5


class ProvisionError(RuntimeError):
    pass


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


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exact(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if type(right) is dict:
        return set(left) == set(right) and all(_exact(left[key], right[key]) for key in right)
    if type(right) is list:
        return len(left) == len(right) and all(_exact(a, b) for a, b in zip(left, right))
    return left == right


def _shape(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH or value is None or isinstance(value, float):
        raise ProvisionError("json_shape_invalid")
    if type(value) is int and abs(value) > MAX_INTEGER:
        raise ProvisionError("json_integer_invalid")
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value or any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise ProvisionError("json_string_invalid")
    elif type(value) is list:
        for item in value: _shape(item, depth + 1)
    elif type(value) is dict:
        for key, item in value.items(): _shape(key, depth + 1); _shape(item, depth + 1)
    elif type(value) not in (bool, int):
        raise ProvisionError("json_type_invalid")


def _strict_json(data: bytes, label: str) -> Mapping[str, Any]:
    if not data or len(data) > MAX_PLAN or data.startswith(b"\xef\xbb\xbf"):
        raise ProvisionError(f"{label}_encoding_invalid")
    try:
        def hook(items: list[tuple[str, Any]]) -> dict[str, Any]:
            out, norms = {}, set()
            for key, value in items:
                norm = unicodedata.normalize("NFC", key)
                if key in out or norm in norms: raise ProvisionError(f"{label}_duplicate_key")
                out[key] = value; norms.add(norm)
            return out
        value = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=hook)
    except RecursionError as exc:
        raise ProvisionError(f"{label}_depth_invalid") from exc
    except (UnicodeError, ValueError) as exc:
        if isinstance(exc, ProvisionError): raise
        raise ProvisionError(f"{label}_invalid") from exc
    if type(value) is not dict: raise ProvisionError(f"{label}_type_invalid")
    _shape(value)
    if canonical_bytes(value) != data: raise ProvisionError(f"{label}_not_canonical")
    return value


def _utc(value: Any, label: str) -> datetime:
    if type(value) is not str or not value.endswith("Z"): raise ProvisionError(f"{label}_invalid")
    try: parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc: raise ProvisionError(f"{label}_invalid") from exc
    if parsed.utcoffset() != timedelta(0): raise ProvisionError(f"{label}_invalid")
    return parsed


def _utc_now() -> datetime:
    return datetime.now(UTC)


def build_security_go(*, plan_sha256: str, issued_at_utc: str, expires_at_utc: str) -> dict[str, Any]:
    """Build an expected GO object for comparison only; never write or issue authority."""
    if type(plan_sha256) is not str or HEX64.fullmatch(plan_sha256) is None:
        raise ProvisionError("go_plan_hash_invalid")
    return {
        "schema_version": SECURITY_GO_SCHEMA, "epic_id": EPIC_ID, "run_id": RUN_ID,
        "contour_id": CONTOUR_ID, "security_alias": PROVISION_SECURITY_ALIAS,
        "plan_sha256": plan_sha256, "literal_go": GO_PREFIX + plan_sha256,
        "issued_at_utc": issued_at_utc, "expires_at_utc": expires_at_utc,
    }


def build_inline_bootstrap(*, loader_bytes: int, loader_sha256: str) -> bytes:
    if type(loader_bytes) is not int or type(loader_sha256) is not str:
        raise ProvisionError("bootstrap_binding_invalid")
    source = (
        "import ctypes,hashlib,os,pathlib,stat,sys,time,datetime\n"
        f"p={LOADER_REL.as_posix()!r};n={loader_bytes!r};h={loader_sha256!r};c=2\n"
        "try:\n"
        f" os.environ[{READINESS_MODE_ENV!r}]='provision'\n"
        f" w=datetime.datetime.now(datetime.UTC);os.environ[{BOOTSTRAP_WALL_ENV!r}]=w.replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ');os.environ[{DEADLINE_ENV!r}]=str(time.monotonic_ns()+120000000000)\n"
        " if os.name!='nt': raise ValueError()\n"
        " a=os.path.abspath(p);r=os.path.abspath('.');q=pathlib.Path(a)\n"
        " if os.path.commonpath((r,a))!=r or a.startswith('\\\\') or not q.drive or ctypes.windll.kernel32.GetDriveTypeW(q.anchor)!=3: raise ValueError()\n"
        " x=pathlib.Path(q.anchor)\n"
        " for z in q.parts[1:]:\n"
        "  x=x/z;s=os.lstat(x)\n"
        "  if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400: raise ValueError()\n"
        " s=os.lstat(q)\n"
        " if not stat.S_ISREG(s.st_mode) or s.st_size!=n: raise ValueError()\n"
        " f=os.open(q,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))\n"
        " try: o=os.fstat(f);b=os.read(f,n+1);t=os.fstat(f)\n"
        " finally: os.close(f)\n"
        " i=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)\n"
        " if (o.st_dev,o.st_ino,o.st_size,o.st_mtime_ns)!=i or (t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns)!=i or len(b)!=n or hashlib.sha256(b).hexdigest()!=h: raise ValueError()\n"
        " sys.dont_write_bytecode=True;g={'__name__':'__owner_fixture_loader__','__file__':str(q),'__package__':None};exec(compile(b,str(q),'exec',dont_inherit=True),g,g);c=g['main']()\n"
        "except BaseException: c=2\n"
        "raise SystemExit(c)\n"
    )
    return source.encode("ascii")


def build_readiness_inline_bootstrap(*, loader_bytes: int, loader_sha256: str) -> bytes:
    base = build_inline_bootstrap(loader_bytes=loader_bytes, loader_sha256=loader_sha256).decode("ascii")
    needle = f" os.environ[{READINESS_MODE_ENV!r}]='provision'\n"
    replacement = f" os.environ[{READINESS_MODE_ENV!r}]='readiness'\n"
    if needle not in base: raise ProvisionError("readiness_bootstrap_template_invalid")
    return base.replace(needle, replacement, 1).encode("ascii")


def build_readiness_plan(*, executor_bytes: int, executor_sha256: str, loader_bytes: int,
                         loader_sha256: str, inline_bootstrap_bytes: int,
                         inline_bootstrap_sha256: str, repository_head: str,
                         issued_at_utc: str, expires_at_utc: str) -> dict[str, Any]:
    return {
        "schema_version": READINESS_PLAN_SCHEMA, "epic_id": EPIC_ID, "run_id": RUN_ID,
        "contour_id": READINESS_CONTOUR_ID, "attempt_id": READINESS_ATTEMPT_ID,
        "classification": "PROD_SAFE", "scope_qualifier": "ZERO_SECRET_ZERO_DEVICE_VISIBLE_CONSOLE_READINESS",
        "security_alias": READINESS_SECURITY_ALIAS, "repository_head": repository_head,
        "executor_relative_path": EXECUTOR_REL.as_posix(), "executor_bytes": executor_bytes,
        "executor_sha256": executor_sha256, "loader_relative_path": LOADER_REL.as_posix(),
        "loader_bytes": loader_bytes, "loader_sha256": loader_sha256,
        "inline_bootstrap_bytes": inline_bootstrap_bytes,
        "inline_bootstrap_sha256": inline_bootstrap_sha256,
        "plan_relative_path": READINESS_PLAN_REL.as_posix(),
        "security_go_relative_path": READINESS_GO_REL.as_posix(),
        "marker_relative_path": READINESS_MARKER_REL.as_posix(),
        "result_relative_path": READINESS_RESULT_REL.as_posix(),
        "issued_at_utc": issued_at_utc, "expires_at_utc": expires_at_utc,
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


def build_readiness_security_go(*, plan_sha256: str, issued_at_utc: str,
                                expires_at_utc: str) -> dict[str, Any]:
    """Build an expected readiness GO object for comparison only; never write or issue authority."""
    if type(plan_sha256) is not str or HEX64.fullmatch(plan_sha256) is None:
        raise ProvisionError("readiness_go_plan_hash_invalid")
    return {
        "schema_version": READINESS_GO_SCHEMA, "epic_id": EPIC_ID, "run_id": RUN_ID,
        "contour_id": READINESS_CONTOUR_ID, "attempt_id": READINESS_ATTEMPT_ID,
        "security_alias": READINESS_SECURITY_ALIAS, "plan_sha256": plan_sha256,
        "literal_go": READINESS_GO_PREFIX + plan_sha256,
        "issued_at_utc": issued_at_utc, "expires_at_utc": expires_at_utc,
    }


def _aggregate(directory_created: int) -> dict[str, Any]:
    return {
        "application_action_count": 0, "authentication_action_count": 0,
        "contour_id": CONTOUR_ID, "destination_directory_created_count": directory_created,
        "device_action_count": 0, "host_process_count": 1, "marker_file_created_count": 1,
        "git_head_validation_count": 2, "git_metadata_content_read_count_max": 8,
        "git_metadata_path_target_count_max": 64,
        "network_action_count": 0, "no_echo_secret_field_read_count": 2,
        "runtime_action_count": 0, "schema_version": AGGREGATE_SCHEMA,
        "secret_file_created_count": 1, "secret_payload_readback_count": 1,
        "secret_payload_write_count": 1, "status": "fixture_provisioned",
        "subprocess_count": 0, "terminal_result_file_created_count": 1, "ui_action_count": 0,
    }


def terminal_result_contract() -> dict[str, Any]:
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


def _terminal_result(plan_sha: str, *, terminal_state: str, exit_category: str,
                     directory_created: int | str, execution_stage: str,
                     marker_created: int = 1) -> dict[str, Any]:
    contract = terminal_result_contract()
    if terminal_state not in contract["allowed_terminal_states"]:
        raise ProvisionError("terminal_state_invalid")
    if exit_category != contract["exit_category_by_terminal_state"][terminal_state]:
        raise ProvisionError("exit_category_invalid")
    if execution_stage not in contract["execution_stages_by_terminal_state"][terminal_state]:
        raise ProvisionError("execution_stage_invalid")
    if type(marker_created) is not int or type(directory_created) not in (int, str):
        raise ProvisionError("terminal_counter_type_invalid")
    if terminal_state == "blocked_before_attempt":
        if marker_created != 0 or directory_created != 0:
            raise ProvisionError("terminal_counter_state_invalid")
    else:
        allowed_directory = (0, 1) if terminal_state == "fixture_provisioned" else (0, 1, "unknown")
        if marker_created != 1 or directory_created not in allowed_directory:
            raise ProvisionError("terminal_counter_state_invalid")
    return {
        "schema_version": TERMINAL_RESULT_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "attempt_id": "fixture-owner-provision-003", "result_alias": PROVISION_RESULT_ALIAS,
        "plan_sha256": plan_sha,
        "terminal_state": terminal_state,
        "exit_category": exit_category,
        "execution_stage": execution_stage,
        "aggregate_counters": {
            "application_action_count": 0,
            "authentication_action_count": 0,
            "destination_directory_created_count": directory_created,
            "device_action_count": 0,
            "marker_file_created_count": marker_created,
            "network_action_count": 0,
            "runtime_action_count": 0,
            "subprocess_count": 0,
            "ui_action_count": 0,
        },
    }


def build_plan(*, executor_bytes: int, executor_sha256: str, loader_bytes: int,
               loader_sha256: str, inline_bootstrap_bytes: int, inline_bootstrap_sha256: str,
               controller_bytes: int, controller_sha256: str, gitignore_bytes: int,
               gitignore_sha256: str, workspace_allowlist: list[dict[str, Any]],
               authority_artifacts: list[dict[str, Any]], expected_secret_parent_state: str,
               fixture_authority_expires_at_utc: str, owner_console_expires_at_utc: str,
               no_mutator_expires_at_utc: str, no_mutator_authority_status: str,
               cooperative_timeout_expires_at_utc: str, cooperative_timeout_acceptance_status: str,
               repository_head: str,
               issued_at_utc: str, expires_at_utc: str) -> dict[str, Any]:
    created = 0 if expected_secret_parent_state == "present" else 1
    return {
        "aggregate_contract": _aggregate(created),
        "authority_artifacts": authority_artifacts,
        "authority_objects": {
            "cooperative_timeout_acceptance": {"alias": COOPERATIVE_TIMEOUT_ALIAS,
                                                "expires_at_utc": cooperative_timeout_expires_at_utc,
                                                "scope": TIMEOUT_CONTRACT["owner_acceptance_scope"],
                                                "status": cooperative_timeout_acceptance_status},
            "fixture_authority": {"alias": FIXTURE_AUTHORITY_ALIAS, "expires_at_utc": fixture_authority_expires_at_utc,
                                  "scope": "synthetic_fixture_alias_only", "status": "confirmed"},
            "owner_local_console_entry": {"alias": OWNER_CONSOLE_ALIAS, "expires_at_utc": owner_console_expires_at_utc,
                                          "scope": "console_values_only_fixture_alias_not_recorded", "status": "confirmed"},
            "provision_no_mutator_window": {"alias": NO_MUTATOR_ALIAS, "expires_at_utc": no_mutator_expires_at_utc,
                                            "scope": NO_MUTATOR_SCOPE, "status": no_mutator_authority_status},
        },
        "budget": dict(BUDGET),
        "classification": "PROD_CONDITIONAL", "contour_id": CONTOUR_ID,
        "controller_bytes": controller_bytes, "controller_relative_path": CONTROLLER_REL.as_posix(),
        "controller_sha256": controller_sha256, "destination_relative_path": DESTINATION_REL.as_posix(),
        "epic_id": EPIC_ID, "executor_bytes": executor_bytes,
        "executor_relative_path": EXECUTOR_REL.as_posix(), "executor_sha256": executor_sha256,
        "expected_secret_parent_state": expected_secret_parent_state, "expires_at_utc": expires_at_utc,
        "failure_policy": "marker_before_console_reads_terminal_result_create_new_best_effort_no_retry_overwrite_delete_rename_or_cleanup",
        "fixture_alias": "epic-phone-001-fixture-001", "gitignore_bytes": gitignore_bytes,
        "gitignore_relative_path": GITIGNORE_REL.as_posix(), "gitignore_sha256": gitignore_sha256,
        "inline_bootstrap_bytes": inline_bootstrap_bytes, "inline_bootstrap_sha256": inline_bootstrap_sha256,
        "input_contract": "two_real_console_no_echo_ascii_digit_fields_total_chars_max_128",
        "issued_at_utc": issued_at_utc, "loader_bytes": loader_bytes,
        "loader_relative_path": LOADER_REL.as_posix(), "loader_sha256": loader_sha256,
        "marker_relative_path": MARKER_REL.as_posix(), "output_contract": "exact_two_ascii_lf_lines_payload_max_96",
        "parent_observation_contract": {"stdout": "not_used", "pid": "start_process_pid",
                                        "exit_code": "zero_success_two_blocked",
                                        "result_alias": PROVISION_RESULT_ALIAS},
        "terminal_result_contract": terminal_result_contract(),
        "repository_head": repository_head, "run_id": RUN_ID, "schema_version": SCHEMA,
        "plan_relative_path": PROVISION_PLAN_REL.as_posix(),
        "security_go_relative_path": PROVISION_GO_REL.as_posix(),
        "result_relative_path": RESULT_REL.as_posix(),
        "security_alias": PROVISION_SECURITY_ALIAS,
        "timeout_contract": dict(TIMEOUT_CONTRACT),
        "workspace_allowlist": workspace_allowlist,
    }


def _validate_plan(plan: Mapping[str, Any], raw: bytes, now: datetime, literal_go: str) -> str:
    try:
        state = plan["expected_secret_parent_state"]
        if state not in ("present", "absent"): raise ProvisionError("parent_state_invalid")
        expected = build_plan(
            executor_bytes=plan["executor_bytes"], executor_sha256=plan["executor_sha256"],
            loader_bytes=plan["loader_bytes"], loader_sha256=plan["loader_sha256"],
            inline_bootstrap_bytes=plan["inline_bootstrap_bytes"], inline_bootstrap_sha256=plan["inline_bootstrap_sha256"],
            controller_bytes=plan["controller_bytes"], controller_sha256=plan["controller_sha256"],
            gitignore_bytes=plan["gitignore_bytes"], gitignore_sha256=plan["gitignore_sha256"],
            workspace_allowlist=plan["workspace_allowlist"], authority_artifacts=plan["authority_artifacts"],
            expected_secret_parent_state=state,
            fixture_authority_expires_at_utc=plan["authority_objects"]["fixture_authority"]["expires_at_utc"],
            owner_console_expires_at_utc=plan["authority_objects"]["owner_local_console_entry"]["expires_at_utc"],
            no_mutator_expires_at_utc=plan["authority_objects"]["provision_no_mutator_window"]["expires_at_utc"],
            no_mutator_authority_status=plan["authority_objects"]["provision_no_mutator_window"]["status"],
            cooperative_timeout_expires_at_utc=plan["authority_objects"]["cooperative_timeout_acceptance"]["expires_at_utc"],
            cooperative_timeout_acceptance_status=plan["authority_objects"]["cooperative_timeout_acceptance"]["status"],
            repository_head=plan["repository_head"],
            issued_at_utc=plan["issued_at_utc"], expires_at_utc=plan["expires_at_utc"],
        )
    except (KeyError, TypeError, IndexError) as exc: raise ProvisionError("plan_contract_invalid") from exc
    if not _exact(plan, expected): raise ProvisionError("plan_contract_invalid")
    if type(plan["repository_head"]) is not str or len(plan["repository_head"]) != 40 or any(ch not in "0123456789abcdef" for ch in plan["repository_head"]):
        raise ProvisionError("repository_head_binding_invalid")
    if plan["authority_objects"]["provision_no_mutator_window"]["status"] != "confirmed_by_owner":
        raise ProvisionError("owner_no_mutator_authority_required")
    if plan["authority_objects"]["cooperative_timeout_acceptance"]["status"] != "accepted_by_owner":
        raise ProvisionError("owner_cooperative_timeout_acceptance_required")
    if len(plan["workspace_allowlist"]) != len(WORKSPACE_ALLOWLIST_CONTRACT): raise ProvisionError("workspace_allowlist_invalid")
    for item, (expected_path, expected_status) in zip(plan["workspace_allowlist"], WORKSPACE_ALLOWLIST_CONTRACT):
        if (type(item) is not dict or set(item) != {"bytes", "path", "sha256", "status"} or
                item.get("path") != expected_path or item.get("status") != expected_status or
                type(item.get("bytes")) is not int or not 0 < item["bytes"] <= MAX_BOUND_FILE or
                type(item.get("sha256")) is not str or HEX64.fullmatch(item["sha256"]) is None):
            raise ProvisionError("workspace_allowlist_invalid")
        raw_path = item["path"]
        parts = raw_path.split("/")
        if "\\" in raw_path or ":" in raw_path or raw_path.startswith("/") or any(part in ("", ".", "..") for part in parts):
            raise ProvisionError("workspace_allowlist_invalid")
    issued, expires = _utc(plan["issued_at_utc"], "issued"), _utc(plan["expires_at_utc"], "expires")
    authorities = [_utc(item["expires_at_utc"], "authority_expiry") for item in plan["authority_objects"].values()]
    if expires <= issued or expires - issued > timedelta(minutes=10) or not issued <= now < expires or any(expires > item or now >= item for item in authorities):
        raise ProvisionError("plan_or_authority_expired")
    for key in ("executor_sha256", "loader_sha256", "inline_bootstrap_sha256", "controller_sha256", "gitignore_sha256"):
        if type(plan[key]) is not str or HEX64.fullmatch(plan[key]) is None: raise ProvisionError("hash_binding_invalid")
    digest = _sha(raw)
    if literal_go != GO_PREFIX + digest: raise ProvisionError("literal_go_invalid")
    return digest


def _validate_authority_artifact(path: Path, item: Mapping[str, Any], now: datetime, required_until: datetime,
                                 plan: Mapping[str, Any]) -> None:
    if (type(item) is not dict or set(item) != {"alias", "bytes", "embedded_expiry_field", "embedded_expiry_value",
                                               "embedded_status_field", "embedded_status_value", "path", "schema_version", "sha256"} or
            item.get("path") != path.as_posix()):
        raise ProvisionError("authority_artifacts_invalid")
    data = _read_bound(REPO_ROOT / path, item["bytes"], item["sha256"])
    artifact = _strict_json(data, "authority_artifact")
    if artifact.get("schema_version") != item["schema_version"]: raise ProvisionError("authority_schema_drift")
    index = AUTHORITY_PATHS.index(path)
    contracts = (
        ("epic-phone-001-c0p-plan-v2", "security_alias", "epic-phone-001-security-c0p-005", "execution_status",
         "planned_separate_literal_go_required_not_run", "expires_at_utc"),
        ("epic-phone-001-fixture-authority-passport-v2", "fixture_alias", "epic-phone-001-fixture-001", "revoked", False, "expires_at_utc"),
        ("epic-phone-001-target-build-passport-v2", "target_alias", "phone-current-001", "target_authorized", True, "expires_at_utc"),
        ("epic-phone-001-evidence-cleanup-passport-v2", "passport_purpose", "policy_readiness_only", "execution_evidence", False, "retention_expires_at_utc"),
    )
    schema, alias_field, alias, status_field, status, expiry_field = contracts[index]
    if (item["schema_version"] != schema or item["alias"] != alias or artifact.get(alias_field) != alias or
            item["embedded_status_field"] != status_field or not _exact(item["embedded_status_value"], status) or
            not _exact(artifact.get(status_field), status) or item["embedded_expiry_field"] != expiry_field):
        raise ProvisionError("authority_cross_binding_invalid")
    if expiry_field == "none":
        if item["embedded_expiry_value"] != "none": raise ProvisionError("authority_cross_binding_invalid")
    else:
        embedded = artifact.get(expiry_field)
        if item["embedded_expiry_value"] != embedded or _utc(embedded, "artifact_expiry") < required_until:
            raise ProvisionError("authority_cross_binding_invalid")
    common = {"authority_set_id": "c0p-authority-005", "epic_id": EPIC_ID,
              "renewal_id": "authority-renewal-003", "run_id": RUN_ID,
              "prep_attempt_id": "c0p-prep-005"}
    if any(not _exact(artifact.get(key), value) for key, value in common.items()):
        raise ProvisionError("authority_v2_semantic_invalid")
    issued = _utc(artifact.get("issued_at_utc"), "authority_v2_issued")
    semantic_expiry = _utc(artifact.get("retention_expires_at_utc") if index == 3 else artifact.get("expires_at_utc"), "authority_v2_expiry")
    if issued > now or semantic_expiry < required_until or semantic_expiry <= issued:
        raise ProvisionError("authority_v2_time_invalid")
    if index == 0:
        required_keys = {"attempt_marker_schema", "authority_set_id", "budget", "build_alias", "c1_token_cannot_authorize",
                         "classification", "contour_id", "controller_execution_interface_present", "controller_source_sha256",
                         "epic_id", "execution_status", "expires_at_utc", "fixed_attempt_marker_path", "fixed_plan_path",
                         "fixed_result_path", "fixed_secret_source", "fixed_token_path", "fixture_alias", "issued_at_utc",
                         "passport_aliases", "prep_attempt_id", "public_result_allowlist", "renewal_id", "repository_head",
                         "run_id", "schema_version", "security_alias", "security_token_format", "security_token_must_bind",
                         "target_alias", "value_handling"}
        if (set(artifact) != required_keys or artifact.get("repository_head") != plan["repository_head"] or
                artifact.get("controller_source_sha256") != plan["controller_sha256"] or
                artifact.get("classification") != "PROD_CONDITIONAL" or artifact.get("contour_id") != "epic-phone-001-c0p-local-presence" or
                artifact.get("target_alias") != "phone-current-001" or artifact.get("build_alias") != "task058-selected-phone-full-001" or
                artifact.get("fixture_alias") != "epic-phone-001-fixture-001" or artifact.get("c1_token_cannot_authorize") is not True or
                artifact.get("controller_execution_interface_present") is not True or
                artifact.get("security_alias") != "epic-phone-001-security-c0p-005" or
                artifact.get("execution_status") != "planned_separate_literal_go_required_not_run" or
                artifact.get("passport_aliases") != {"fixture_authority": "epic-phone-001-fixture-authority-005",
                                                     "target_build": "epic-phone-001-target-build-005",
                                                     "evidence_cleanup": "epic-phone-001-evidence-cleanup-005"} or
                artifact.get("fixed_plan_path") != AUTHORITY_PATHS[0].as_posix() or
                artifact.get("fixed_token_path") != (RUN_REL / "security-go-c0p-005.local.json").as_posix() or
                artifact.get("fixed_result_path") != (RUN_REL / "public-safe/c0p-005-result.local.json").as_posix() or
                artifact.get("fixed_attempt_marker_path") != (RUN_REL / "c0p-005-attempt.local.json").as_posix() or
                artifact.get("fixed_secret_source") != DESTINATION_REL.as_posix() or
                artifact.get("attempt_marker_schema") != "epic-phone-001-c0p-attempt-v1" or
                artifact.get("security_token_format") != f"GO_EPIC_PHONE_001_C0P_LOCAL_PRESENCE__{RUN_ID}__<64_lowercase_hex>" or
                artifact.get("security_token_must_bind") != ["epic_id", "run_id", "contour_id", "target_alias", "build_alias",
                                                              "fixture_alias", "passport_aliases", "passport_sha256", "passport_expires_at_utc",
                                                              "security_alias", "c0p_plan_sha256", "repository_head", "controller_source_sha256",
                                                              "issued_at_utc", "expires_at_utc", "result_path", "attempt_marker_path",
                                                              "attempt_marker_schema", "budget"] or
                artifact.get("public_result_allowlist") != ["required_field_count", "required_fields_present", "unexpected_fields_absent",
                                                              "phone_format_policy_pass", "otp_format_policy_pass"] or
                not _exact(artifact.get("value_handling"), {"read_only_for_nonempty_presence_in_authorized_adapter": True, "print": False,
                                                            "record": False, "hash": False, "length": False, "value_comparison": False}) or
                not _exact(artifact.get("budget"), {"secret_source_read_max": 1, "retry_max": 0, "wall_clock_minutes_max": 30,
                                                    "secret_source_bytes_max": 8192, "device_action_max": 0, "subprocess_max": 0,
                                                    "network_action_max": 0, "application_launch_max": 0, "ui_action_max": 0,
                                                    "authentication_action_max": 0, "mutation_max": 0})):
            raise ProvisionError("authority_v2_semantic_invalid")
    elif index == 1:
        required_keys = {"allowed_scope", "authority_set_id", "authority_validity", "epic_id", "expires_at_utc", "fixture_alias",
                         "forbidden_scope", "issued_at_utc", "not_real_user", "prep_attempt_id", "renewal_id", "revoked", "run_id",
                         "schema_version", "synthetic_test_only", "values_local_only"}
        if (set(artifact) != required_keys or artifact.get("synthetic_test_only") is not True or artifact.get("not_real_user") is not True or
                artifact.get("values_local_only") is not True or artifact.get("revoked") is not False or
                artifact.get("schema_version") != "epic-phone-001-fixture-authority-passport-v2" or
                artifact.get("fixture_alias") != "epic-phone-001-fixture-001" or
                artifact.get("authority_validity") != "current_epic_run_until_completion_or_revocation" or
                artifact.get("allowed_scope") != ["synthetic_session_create", "read_only_navigation", "safe_logout"] or
                artifact.get("forbidden_scope") != ["payment", "subscription", "entitlement", "profile", "account", "paid_session", "external_or_qr_traversal"]):
            raise ProvisionError("authority_v2_semantic_invalid")
    elif index == 2:
        required_keys = {"authority_set_id", "build_alias", "build_authorized", "current_freshness_evidence", "epic_id", "expires_at_utc",
                         "issued_at_utc", "launch_allowed", "mutation_allowed", "passport_purpose", "prep_attempt_id", "renewal_id",
                         "run_id", "runtime_evidence", "schema_version", "target_alias", "target_authorized", "task058a_row03_evidence_status"}
        if (set(artifact) != required_keys or artifact.get("passport_purpose") != "authorization_only" or
                artifact.get("task058a_row03_evidence_status") != "unknown" or artifact.get("target_authorized") is not True or
                artifact.get("schema_version") != "epic-phone-001-target-build-passport-v2" or
                artifact.get("target_alias") != "phone-current-001" or artifact.get("build_alias") != "task058-selected-phone-full-001" or
                artifact.get("build_authorized") is not True or artifact.get("launch_allowed") is not False or
                artifact.get("mutation_allowed") is not False or artifact.get("current_freshness_evidence") is not False or
                artifact.get("runtime_evidence") is not False):
            raise ProvisionError("authority_v2_semantic_invalid")
    else:
        required_keys = {"authority_set_id", "cleanup_sequence", "direct_capture_no_echo", "epic_id", "execution_evidence",
                         "forbidden_action_count", "hard_bytes_max", "issued_at_utc", "passport_purpose", "prep_attempt_id",
                         "redaction_default", "renewal_id", "retention_expires_at_utc", "run_id", "run_root", "schema_version", "soft_bytes_max"}
        if (set(artifact) != required_keys or artifact.get("passport_purpose") != "policy_readiness_only" or
                artifact.get("execution_evidence") is not False or artifact.get("redaction_default") is not True or
                artifact.get("direct_capture_no_echo") is not True or not _exact(artifact.get("forbidden_action_count"), 0) or
                artifact.get("schema_version") != "epic-phone-001-evidence-cleanup-passport-v2" or
                artifact.get("run_root") != RUN_REL.as_posix() or not _exact(artifact.get("soft_bytes_max"), 50331648) or
                not _exact(artifact.get("hard_bytes_max"), 67108864) or
                artifact.get("cleanup_sequence") != ["target_only_force_stop", "home", "post_kill_checkpoint", "capture_shutdown"]):
            raise ProvisionError("authority_v2_semantic_invalid")


def _read_plan(now: datetime) -> tuple[Mapping[str, Any], str]:
    raw = _read_fixed_input(PROVISION_PLAN_REL, "plan")
    plan = _strict_json(raw, "plan")
    digest = _sha(raw)
    go = _strict_json(_read_fixed_input(PROVISION_GO_REL, "security_go"), "security_go")
    try:
        expected = build_security_go(plan_sha256=digest, issued_at_utc=go["issued_at_utc"],
                                     expires_at_utc=go["expires_at_utc"])
    except (KeyError, TypeError) as exc:
        raise ProvisionError("security_go_contract_invalid") from exc
    if not _exact(go, expected): raise ProvisionError("security_go_contract_invalid")
    issued = _utc(go["issued_at_utc"], "security_go_issued")
    expires = _utc(go["expires_at_utc"], "security_go_expires")
    if not issued <= now < expires or expires > _utc(plan.get("expires_at_utc"), "expires"):
        raise ProvisionError("security_go_expired")
    return plan, _validate_plan(plan, raw, now, go["literal_go"])


def _read_fixed_input(relative: Path, label: str, maximum: int = MAX_PLAN) -> bytes:
    path = REPO_ROOT / relative
    _safe_chain(path, leaf_file=True)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum:
        raise ProvisionError(f"{label}_size_invalid")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(fd); data = os.read(fd, maximum + 1); after = os.fstat(fd)
    finally:
        os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or
            len(data) != before.st_size):
        raise ProvisionError(f"{label}_identity_invalid")
    return data


def _fixed_drive(path: Path) -> None:
    if os.name != "nt" or not path.is_absolute() or not path.drive or str(path).startswith("\\\\"):
        raise ProvisionError("windows_fixed_drive_required")
    import ctypes
    if ctypes.windll.kernel32.GetDriveTypeW(path.anchor) != 3: raise ProvisionError("windows_fixed_drive_required")


def _lstat(path: Path) -> os.stat_result | None:
    try: return path.lstat()
    except FileNotFoundError: return None


def _safe_chain(path: Path, *, allow_leaf_missing: bool = False, leaf_file: bool = False) -> os.stat_result | None:
    _fixed_drive(path); current = Path(path.anchor); last = None
    for index, part in enumerate(path.parts[1:]):
        current = current / part; item = _lstat(current); leaf = index == len(path.parts[1:]) - 1
        if item is None:
            if leaf and allow_leaf_missing: return None
            raise ProvisionError("path_missing")
        if stat.S_ISLNK(item.st_mode) or getattr(item, "st_file_attributes", 0) & REPARSE_ATTRIBUTE:
            raise ProvisionError("path_reparse")
        if leaf and leaf_file:
            if not stat.S_ISREG(item.st_mode): raise ProvisionError("path_type_invalid")
        elif not stat.S_ISDIR(item.st_mode): raise ProvisionError("path_type_invalid")
        last = item
    return last


def _safe_absolute_chain(path: Path) -> None:
    absolute = path.absolute(); _fixed_drive(absolute); current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part; item = current.lstat()
        if stat.S_ISLNK(item.st_mode) or getattr(item, "st_file_attributes", 0) & REPARSE_ATTRIBUTE:
            raise ProvisionError("git_metadata_reparse")


def _track_git_path(path: Path, budget: dict[str, Any]) -> None:
    budget["targets"].add(str(path.absolute()))
    if len(budget["targets"]) > BUDGET["git_metadata_path_target_max"] // 2:
        raise ProvisionError("git_metadata_path_budget_exhausted")


def _probe_optional_git_path(path: Path, budget: dict[str, Any]) -> bool:
    absolute = path.absolute(); _fixed_drive(absolute); current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part; _track_git_path(current, budget)
        try: item = current.lstat()
        except FileNotFoundError: return False
        if stat.S_ISLNK(item.st_mode) or getattr(item, "st_file_attributes", 0) & REPARSE_ATTRIBUTE:
            raise ProvisionError("git_metadata_reparse")
    return True


def _read_git_metadata(path: Path, budget: dict[str, Any], maximum: int = 4096) -> bytes:
    _track_git_path(path, budget); budget["content_reads"] += 1
    if budget["content_reads"] > BUDGET["git_metadata_content_read_max"] // 2:
        raise ProvisionError("git_metadata_content_budget_exhausted")
    _safe_absolute_chain(path); before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum:
        raise ProvisionError("git_metadata_invalid")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); data = os.read(fd, maximum + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or len(data) != before.st_size):
        raise ProvisionError("git_metadata_identity_invalid")
    return data


def _actual_repository_head(root: Path | None = None) -> tuple[str, int, int]:
    base = (root or REPO_ROOT).absolute(); _fixed_drive(base)
    budget: dict[str, Any] = {"content_reads": 0, "targets": set()}
    marker = base / ".git"; _track_git_path(marker, budget); _safe_absolute_chain(marker); info = marker.lstat()
    if stat.S_ISDIR(info.st_mode):
        gitdir = marker
    elif stat.S_ISREG(info.st_mode):
        raw = _read_git_metadata(marker, budget).decode("utf-8", errors="strict").strip()
        if not raw.startswith("gitdir: "): raise ProvisionError("gitdir_contract_invalid")
        value = raw[8:]
        if not value or value.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")):
            raise ProvisionError("gitdir_contract_invalid")
        gitdir = Path(value) if Path(value).is_absolute() else base / value
        gitdir = Path(os.path.abspath(gitdir)); _track_git_path(gitdir, budget); _safe_absolute_chain(gitdir)
    else:
        raise ProvisionError("git_marker_type_invalid")
    common = gitdir; commondir = gitdir / "commondir"; _track_git_path(commondir, budget)
    try: commondir_info = commondir.lstat()
    except FileNotFoundError: commondir_info = None
    if commondir_info is not None:
        raw_common = _read_git_metadata(commondir, budget).decode("utf-8", errors="strict").strip()
        if not raw_common or raw_common.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")):
            raise ProvisionError("commondir_contract_invalid")
        common = Path(raw_common) if Path(raw_common).is_absolute() else gitdir / raw_common
        common = Path(os.path.abspath(common)); _track_git_path(common, budget); _safe_absolute_chain(common)
    head = _read_git_metadata(gitdir / "HEAD", budget).decode("ascii", errors="strict").strip()
    if len(head) == 40 and all(ch in "0123456789abcdef" for ch in head):
        return head, budget["content_reads"], len(budget["targets"])
    if not head.startswith("ref: "): raise ProvisionError("git_head_invalid")
    ref = head[5:]
    if not ref.startswith("refs/") or "\\" in ref or ":" in ref or any(part in ("", ".", "..") for part in ref.split("/")):
        raise ProvisionError("git_ref_invalid")
    loose = common.joinpath(*ref.split("/"))
    if _probe_optional_git_path(loose, budget):
        value = _read_git_metadata(loose, budget).decode("ascii", errors="strict").strip()
        if len(value) == 40 and all(ch in "0123456789abcdef" for ch in value):
            return value, budget["content_reads"], len(budget["targets"])
        raise ProvisionError("git_loose_ref_invalid")
    packed = _read_git_metadata(common / "packed-refs", budget, 32768).decode("ascii", errors="strict")
    matches = []
    for line in packed.splitlines():
        if not line or line.startswith(("#", "^")): continue
        parts = line.split(" ")
        if len(parts) != 2: raise ProvisionError("packed_refs_invalid")
        if parts[1] == ref: matches.append(parts[0])
    if len(matches) != 1 or len(matches[0]) != 40 or any(ch not in "0123456789abcdef" for ch in matches[0]):
        raise ProvisionError("packed_ref_missing_or_ambiguous")
    return matches[0], budget["content_reads"], len(budget["targets"])


def _read_bound(path: Path, expected_bytes: int, expected_sha: str) -> bytes:
    if type(expected_bytes) is not int or not 0 < expected_bytes <= MAX_BOUND_FILE or type(expected_sha) is not str or HEX64.fullmatch(expected_sha) is None:
        raise ProvisionError("bound_contract_invalid")
    before = _safe_chain(path, leaf_file=True)
    if before is None or before.st_size != expected_bytes: raise ProvisionError("bound_identity_invalid")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(fd); data = os.read(fd, expected_bytes + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or
            len(data) != expected_bytes or _sha(data) != expected_sha):
        raise ProvisionError("bound_identity_invalid")
    return data


def _deadline(plan: Mapping[str, Any], initial_wall: datetime) -> tuple[int, datetime]:
    bootstrap_wall = _utc(os.environ.get(BOOTSTRAP_WALL_ENV), "bootstrap_wall"); text = os.environ.get(DEADLINE_ENV)
    if type(text) is not str or not text.isascii() or not text.isdigit() or len(text) > 24: raise ProvisionError("deadline_invalid")
    value = int(text)
    mono_before = time.monotonic_ns()
    fresh_wall = _utc_now()
    mono_after = time.monotonic_ns()
    issued, expires = _utc(plan["issued_at_utc"], "issued"), _utc(plan["expires_at_utc"], "expires")
    if (fresh_wall < initial_wall or mono_after < mono_before or
            not issued <= bootstrap_wall <= fresh_wall < expires or
            not mono_before < value <= mono_before + 120_000_000_000):
        raise ProvisionError("deadline_invalid")
    remaining_seconds = (value - mono_before + 999_999_999) // 1_000_000_000
    bootstrap_bound = bootstrap_wall + timedelta(seconds=120 + AUTHORITY_COVERAGE_GUARD_SECONDS)
    validation_bound = fresh_wall + timedelta(seconds=remaining_seconds + AUTHORITY_COVERAGE_GUARD_SECONDS)
    required_until = max(bootstrap_bound, validation_bound)
    return value, required_until


def _read_console_digits(minimum: int, maximum: int, deadline_ns: int, budget: list[int], prompt: str) -> bytearray:
    _check_deadline(deadline_ns)
    msvcrt = _real_console_api()
    _check_deadline(deadline_ns)
    sys.stderr.write(prompt); sys.stderr.flush()
    result = bytearray(); success = False
    try:
        while True:
            if time.monotonic_ns() >= deadline_ns: raise ProvisionError("input_deadline_exhausted")
            if not msvcrt.kbhit(): time.sleep(0.01); continue
            char = msvcrt.getwch(); budget[0] += 1
            if budget[0] > MAX_INPUT_CHARS: raise ProvisionError("input_budget_exhausted")
            if char in ("\r", "\n"):
                sys.stderr.write("\n"); sys.stderr.flush()
                if not minimum <= len(result) <= maximum: raise ProvisionError("input_contract_invalid")
                success = True
                return result
            if char == "\b":
                if result:
                    result[-1] = 0
                    result.pop()
                continue
            if len(char) != 1 or not "0" <= char <= "9" or len(result) >= maximum:
                raise ProvisionError("input_contract_invalid")
            result.append(ord(char))
    finally:
        if not success:
            for index in range(len(result)): result[index] = 0


def _acl_material():
    """Return ctypes objects, protected descriptor and SECURITY_ATTRIBUTES."""
    import ctypes
    from ctypes import wintypes
    class SID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("Sid", wintypes.LPVOID), ("Attributes", wintypes.DWORD)]
    class TOKEN_USER(ctypes.Structure):
        _fields_ = [("User", SID_AND_ATTRIBUTES)]
    token = wintypes.HANDLE()
    open_token = ctypes.windll.advapi32.OpenProcessToken
    open_token.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]; open_token.restype = wintypes.BOOL
    if not open_token(ctypes.windll.kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise ProvisionError("token_query_failed")
    try:
        needed = wintypes.DWORD()
        get_token = ctypes.windll.advapi32.GetTokenInformation
        get_token.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]; get_token.restype = wintypes.BOOL
        get_token(token, 1, None, 0, ctypes.byref(needed))
        buffer = ctypes.create_string_buffer(needed.value)
        if not get_token(token, 1, buffer, needed, ctypes.byref(needed)):
            raise ProvisionError("token_query_failed")
        sid_ptr = ctypes.cast(buffer, ctypes.POINTER(TOKEN_USER)).contents.User.Sid; sid_text = wintypes.LPWSTR()
        convert_sid = ctypes.windll.advapi32.ConvertSidToStringSidW
        convert_sid.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR)]; convert_sid.restype = wintypes.BOOL
        if not convert_sid(sid_ptr, ctypes.byref(sid_text)):
            raise ProvisionError("sid_conversion_failed")
        try: sddl = f"D:P(A;;FA;;;{sid_text.value})(A;;FA;;;SY)"
        finally: ctypes.windll.kernel32.LocalFree(sid_text)
    finally: ctypes.windll.kernel32.CloseHandle(token)
    descriptor = wintypes.LPVOID()
    convert_sd = ctypes.windll.advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert_sd.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID), ctypes.POINTER(wintypes.DWORD)]; convert_sd.restype = wintypes.BOOL
    if not convert_sd(sddl, 1, ctypes.byref(descriptor), None):
        raise ProvisionError("acl_descriptor_failed")
    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("nLength", wintypes.DWORD), ("lpSecurityDescriptor", wintypes.LPVOID), ("bInheritHandle", wintypes.BOOL)]
    return ctypes, wintypes, descriptor, SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), descriptor, False)


def _write_flush_readback(handle, payload: bytes | bytearray, deadline_ns: int) -> None:
    import ctypes
    from ctypes import wintypes
    readback = None
    try:
        write_file = ctypes.windll.kernel32.WriteFile
        write_file.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]; write_file.restype = wintypes.BOOL
        if isinstance(payload, bytearray):
            source = (ctypes.c_ubyte * len(payload)).from_buffer(payload)
        else:
            source = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
        offset = 0
        while offset < len(payload):
            _check_deadline(deadline_ns); written = wintypes.DWORD()
            if not write_file(handle, ctypes.byref(source, offset), len(payload) - offset, ctypes.byref(written), None) or written.value <= 0:
                raise ProvisionError("write_failed")
            offset += written.value
            _check_deadline(deadline_ns)
        flush = ctypes.windll.kernel32.FlushFileBuffers; flush.argtypes = [wintypes.HANDLE]; flush.restype = wintypes.BOOL
        _check_deadline(deadline_ns)
        if not flush(handle): raise ProvisionError("flush_failed")
        _check_deadline(deadline_ns)
        position = ctypes.c_longlong(0)
        seek = ctypes.windll.kernel32.SetFilePointerEx
        seek.argtypes = [wintypes.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD]; seek.restype = wintypes.BOOL
        if not seek(handle, 0, ctypes.byref(position), 0): raise ProvisionError("readback_seek_failed")
        _check_deadline(deadline_ns)
        readback = bytearray(len(payload)); read = wintypes.DWORD(); array = (ctypes.c_ubyte * len(payload)).from_buffer(readback)
        read_file = ctypes.windll.kernel32.ReadFile
        read_file.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]; read_file.restype = wintypes.BOOL
        _check_deadline(deadline_ns)
        if not read_file(handle, array, len(payload), ctypes.byref(read), None) or read.value != len(payload) or readback != payload:
            raise ProvisionError("readback_failed")
        _check_deadline(deadline_ns)
    finally:
        if isinstance(readback, bytearray):
            for index in range(len(readback)): readback[index] = 0


def _new_file_handle(path: Path, security_attributes):
    import ctypes
    from ctypes import wintypes
    create = ctypes.windll.kernel32.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    handle = create(str(path), 0xC0000000, 0, security_attributes, CREATE_NEW, 0x80000080, None)
    if handle == wintypes.HANDLE(-1).value: raise ProvisionError("secure_create_failed")
    return ctypes, wintypes, handle


def _protected_write_new(path: Path, payload: bytes | bytearray, deadline_ns: int, *, verify_before_write: bool) -> None:
    _check_deadline(deadline_ns)
    if _lstat(path) is not None: raise ProvisionError("create_precondition_invalid")
    _check_deadline(deadline_ns)
    ctypes, wintypes, descriptor, attrs = _acl_material()
    _check_deadline(deadline_ns); handle = None
    try:
        _check_deadline(deadline_ns)
        _, _, handle = _new_file_handle(path, ctypes.byref(attrs))
        _check_deadline(deadline_ns)
        if verify_before_write:
            _verify_handle_acl(handle, exact_secret=True)
            _check_deadline(deadline_ns)
        _write_flush_readback(handle, payload, deadline_ns)
        _check_deadline(deadline_ns)
        _verify_handle_acl(handle, exact_secret=True)
        _check_deadline(deadline_ns)
    finally:
        if handle not in (None, wintypes.HANDLE(-1).value): ctypes.windll.kernel32.CloseHandle(handle)
        ctypes.windll.kernel32.LocalFree(descriptor)


def _protected_provision_write_new(path: Path, payload: bytes, deadline_ns: int,
                                   readback_counts: dict[str, int], counter: str) -> None:
    budget_key = {"marker": "protected_marker_file_readback_max",
                  "terminal_result": "protected_terminal_result_file_readback_max"}.get(counter)
    if budget_key is None or type(readback_counts.get(counter)) is not int:
        raise ProvisionError("protected_readback_budget_invalid")
    readback_counts[counter] += 1
    if readback_counts[counter] > BUDGET[budget_key]:
        raise ProvisionError("protected_readback_budget_exhausted")
    _protected_write_new(path, payload, deadline_ns, verify_before_write=False)


def _secure_write_new(path: Path, payload: bytearray, deadline_ns: int) -> None:
    _protected_write_new(path, payload, deadline_ns, verify_before_write=True)


def _check_deadline(deadline_ns: int) -> None:
    if time.monotonic_ns() >= deadline_ns: raise ProvisionError("deadline_exhausted")


def _verify_handle_acl(handle, *, exact_secret: bool) -> None:
    """Fail closed unless the handle has a protected, non-null basic DACL."""
    import ctypes
    from ctypes import wintypes
    owner = wintypes.LPVOID(); dacl = wintypes.LPVOID(); descriptor = wintypes.LPVOID()
    get = ctypes.windll.advapi32.GetSecurityInfo
    get.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID), ctypes.c_void_p,
                    ctypes.POINTER(wintypes.LPVOID), ctypes.c_void_p, ctypes.POINTER(wintypes.LPVOID)]; get.restype = wintypes.DWORD
    if get(handle, 1, 0x1 | 0x4, ctypes.byref(owner), None, ctypes.byref(dacl), None, ctypes.byref(descriptor)) != 0 or not owner or not dacl:
        raise ProvisionError("acl_check_failed")
    try:
        control = wintypes.WORD(); revision = wintypes.DWORD()
        if not ctypes.windll.advapi32.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)) or not control.value & 0x1000:
            raise ProvisionError("acl_not_protected")
        class ACL_SIZE_INFORMATION(ctypes.Structure):
            _fields_ = [("AceCount", wintypes.DWORD), ("AclBytesInUse", wintypes.DWORD), ("AclBytesFree", wintypes.DWORD)]
        info = ACL_SIZE_INFORMATION()
        if not ctypes.windll.advapi32.GetAclInformation(dacl, ctypes.byref(info), ctypes.sizeof(info), 2):
            raise ProvisionError("acl_check_failed")
        allowed = [owner]; sid_buffers = []; current_sid = None
        if exact_secret:
            class SID_AND_ATTRIBUTES(ctypes.Structure):
                _fields_ = [("Sid", wintypes.LPVOID), ("Attributes", wintypes.DWORD)]
            class TOKEN_USER(ctypes.Structure):
                _fields_ = [("User", SID_AND_ATTRIBUTES)]
            token = wintypes.HANDLE()
            if not ctypes.windll.advapi32.OpenProcessToken(ctypes.windll.kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
                raise ProvisionError("acl_check_failed")
            try:
                needed = wintypes.DWORD(); ctypes.windll.advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
                user_buffer = ctypes.create_string_buffer(needed.value); sid_buffers.append(user_buffer)
                if not ctypes.windll.advapi32.GetTokenInformation(token, 1, user_buffer, needed, ctypes.byref(needed)):
                    raise ProvisionError("acl_check_failed")
                current_sid = ctypes.cast(user_buffer, ctypes.POINTER(TOKEN_USER)).contents.User.Sid
            finally: ctypes.windll.kernel32.CloseHandle(token)
            if not ctypes.windll.advapi32.EqualSid(owner, current_sid): raise ProvisionError("acl_owner_invalid")
            allowed = [current_sid]
        for kind in ((22,) if exact_secret else (22, 26)):
            size = wintypes.DWORD(68); buffer = ctypes.create_string_buffer(68)
            if not ctypes.windll.advapi32.CreateWellKnownSid(kind, None, buffer, ctypes.byref(size)):
                raise ProvisionError("acl_check_failed")
            sid_buffers.append(buffer); allowed.append(ctypes.cast(buffer, wintypes.LPVOID))
        matched = [False] * len(allowed)
        if exact_secret and info.AceCount != 2: raise ProvisionError("acl_exact_ace_count_invalid")
        for index in range(info.AceCount):
            ace = wintypes.LPVOID()
            if not ctypes.windll.advapi32.GetAce(dacl, index, ctypes.byref(ace)): raise ProvisionError("acl_check_failed")
            header = ctypes.cast(ace, ctypes.POINTER(ctypes.c_ubyte)); ace_type = header[0]
            if ace_type not in (0, 1): raise ProvisionError("acl_nonbasic")
            if ace_type == 0:
                mask = ctypes.cast(ace.value + 4, ctypes.POINTER(wintypes.DWORD)).contents.value
                if exact_secret and (header[1] != 0 or mask != 0x001F01FF):
                    raise ProvisionError("acl_exact_flags_or_mask_invalid")
                sid = wintypes.LPVOID(ace.value + 8)
                matches = [bool(ctypes.windll.advapi32.EqualSid(sid, candidate)) for candidate in allowed]
                if not any(matches):
                    raise ProvisionError("acl_too_broad")
                if exact_secret and (index >= len(matches) or not matches[index] or sum(matches) != 1):
                    raise ProvisionError("acl_exact_order_invalid")
                for match_index, is_match in enumerate(matches): matched[match_index] |= is_match
            elif exact_secret:
                raise ProvisionError("acl_exact_type_invalid")
        if exact_secret and not all(matched): raise ProvisionError("acl_required_principal_missing")
    finally: ctypes.windll.kernel32.LocalFree(descriptor)


def _secure_mkdir(path: Path, deadline_ns: int) -> None:
    _check_deadline(deadline_ns)
    ctypes, wintypes, descriptor, attrs = _acl_material()
    _check_deadline(deadline_ns)
    try:
        create = ctypes.windll.kernel32.CreateDirectoryW
        create.argtypes = [wintypes.LPCWSTR, ctypes.c_void_p]; create.restype = wintypes.BOOL
        _check_deadline(deadline_ns)
        if not create(str(path), ctypes.byref(attrs)):
            raise ProvisionError("secure_directory_create_failed")
        _check_deadline(deadline_ns)
    finally: ctypes.windll.kernel32.LocalFree(descriptor)


def _verify_path_acl(path: Path, *, exact_secret: bool) -> None:
    import ctypes
    from ctypes import wintypes
    create = ctypes.windll.kernel32.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    handle = create(str(path), 0x00020000, 0x7, None, 3, 0x02000000, None)
    if handle == wintypes.HANDLE(-1).value: raise ProvisionError("acl_path_open_failed")
    try: _verify_handle_acl(handle, exact_secret=exact_secret)
    finally: ctypes.windll.kernel32.CloseHandle(handle)


def _preflight_real_console() -> None:
    _real_console_api()


def _real_console_api():
    if os.name != "nt" or not sys.stdin.isatty() or not sys.stderr.isatty(): raise ProvisionError("real_console_required")
    import ctypes, msvcrt
    handle = msvcrt.get_osfhandle(sys.stdin.fileno()); mode = ctypes.c_ulong()
    if handle == -1 or not ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        raise ProvisionError("real_console_required")
    return msvcrt


def _readiness_result(plan_sha: str, terminal_state: str, exit_category: str) -> bytes:
    return canonical_bytes({
        "schema_version": READINESS_RESULT_SCHEMA, "epic_id": EPIC_ID, "run_id": RUN_ID,
        "contour_id": READINESS_CONTOUR_ID, "attempt_id": READINESS_ATTEMPT_ID,
        "result_alias": READINESS_RESULT_ALIAS,
        "plan_sha256": plan_sha, "terminal_state": terminal_state,
        "exit_category": exit_category,
        "aggregate_counters": {"authority_artifact_read_count": 0, "secret_read_count": 0,
                               "device_action_count": 0, "application_action_count": 0,
                               "network_action_count": 0, "marker_file_created_count": 1,
                               "result_file_created_count": 1},
    }) + b"\n"


def readiness_main(plan: Mapping[str, Any], plan_sha: str) -> int:
    deadline_text = os.environ.get(DEADLINE_ENV)
    if type(deadline_text) is not str or not deadline_text.isascii() or not deadline_text.isdigit(): return 2
    deadline_ns = int(deadline_text)
    operation_deadline_ns = deadline_ns - RESULT_FINALIZATION_RESERVE_SECONDS * 1_000_000_000
    marker = REPO_ROOT / READINESS_MARKER_REL
    result_path = REPO_ROOT / READINESS_RESULT_REL
    marker_created_this_invocation = False
    try:
        _fixed_drive(REPO_ROOT.absolute())
        _safe_chain(REPO_ROOT / RUN_REL)
        if _lstat(marker) is not None or _lstat(result_path) is not None:
            raise ProvisionError("readiness_attempt_consumed")
        _check_deadline(operation_deadline_ns)
        marker_payload = canonical_bytes({"schema_version": READINESS_MARKER_SCHEMA,
                                          "epic_id": EPIC_ID, "run_id": RUN_ID,
                                          "contour_id": READINESS_CONTOUR_ID,
                                          "attempt_id": READINESS_ATTEMPT_ID,
                                          "plan_sha256": plan_sha,
                                          "attempt_state": "started_before_console_probe"}) + b"\n"
        _protected_write_new(marker, marker_payload, operation_deadline_ns, verify_before_write=False)
        marker_created_this_invocation = True
        _check_deadline(operation_deadline_ns); _preflight_real_console(); _check_deadline(operation_deadline_ns)
        _protected_write_new(result_path, _readiness_result(plan_sha, "ready", "success"),
                             deadline_ns, verify_before_write=False)
        return 0
    except BaseException:
        try:
            if marker_created_this_invocation and _lstat(result_path) is None:
                _protected_write_new(result_path, _readiness_result(plan_sha, "blocked", "blocked"),
                                     deadline_ns, verify_before_write=False)
        except BaseException:
            pass
        return 2


def execute(now: datetime | None = None) -> dict[str, Any]:
    current = now or _utc_now(); plan, plan_sha = _read_plan(current)
    deadline_ns, conservative_execution_end = _deadline(plan, current)
    operation_deadline_ns = deadline_ns - RESULT_FINALIZATION_RESERVE_SECONDS * 1_000_000_000
    plan_expires = _utc(plan["expires_at_utc"], "expires")
    if plan_expires < conservative_execution_end:
        raise ProvisionError("plan_runtime_coverage_invalid")
    required_until = max(plan_expires, conservative_execution_end)
    if any(_utc(item["expires_at_utc"], "authority_expiry") < required_until
           for item in plan["authority_objects"].values()):
        raise ProvisionError("authority_runtime_coverage_invalid")
    _fixed_drive(REPO_ROOT.absolute())
    loader_git_check = globals().get(LOADER_GIT_CHECK_GLOBAL, 0)
    loader_git_content = globals().get(LOADER_GIT_CONTENT_GLOBAL, 0)
    loader_git_paths = globals().get(LOADER_GIT_PATH_GLOBAL, 0)
    if (type(loader_git_check) is not int or loader_git_check != 1 or
            type(loader_git_content) is not int or not 0 < loader_git_content <= BUDGET["git_metadata_content_read_max"] // 2 or
            type(loader_git_paths) is not int or not 0 < loader_git_paths <= BUDGET["git_metadata_path_target_max"] // 2):
        raise ProvisionError("loader_git_counter_invalid")
    actual_head, executor_git_content, executor_git_paths = _actual_repository_head()
    if actual_head != plan["repository_head"]: raise ProvisionError("repository_head_binding_invalid")
    git_check_count = loader_git_check + 1
    git_content_count = loader_git_content + executor_git_content
    git_path_count = loader_git_paths + executor_git_paths
    if (git_check_count > BUDGET["git_head_validation_max"] or
            git_content_count > BUDGET["git_metadata_content_read_max"] or
            git_path_count > BUDGET["git_metadata_path_target_max"]):
        raise ProvisionError("git_metadata_budget_exhausted")
    bootstrap = build_inline_bootstrap(loader_bytes=plan["loader_bytes"], loader_sha256=plan["loader_sha256"])
    if len(bootstrap) != plan["inline_bootstrap_bytes"] or _sha(bootstrap) != plan["inline_bootstrap_sha256"]:
        raise ProvisionError("bootstrap_binding_invalid")
    for item in plan["workspace_allowlist"]:
        _read_bound(REPO_ROOT.joinpath(*item["path"].split("/")), item["bytes"], item["sha256"])
    bindings = ((EXECUTOR_REL, "executor"), (LOADER_REL, "loader"), (CONTROLLER_REL, "controller"), (GITIGNORE_REL, "gitignore"))
    for relative, prefix in bindings:
        data = _read_bound(REPO_ROOT / relative, plan[f"{prefix}_bytes"], plan[f"{prefix}_sha256"])
        if prefix == "gitignore" and b".qa_local/" not in data.splitlines(): raise ProvisionError("gitignore_binding_invalid")
    if len(plan["authority_artifacts"]) != 4: raise ProvisionError("authority_artifacts_invalid")
    for expected_path, item in zip(AUTHORITY_PATHS, plan["authority_artifacts"]):
        _validate_authority_artifact(expected_path, item, current, required_until, plan)
    run_parent = REPO_ROOT / RUN_REL; _safe_chain(run_parent)
    _check_deadline(operation_deadline_ns); _verify_path_acl(run_parent, exact_secret=False); _check_deadline(operation_deadline_ns)
    marker = REPO_ROOT / MARKER_REL
    result_path = REPO_ROOT / RESULT_REL
    protected_readback_counts = {"marker": 0, "terminal_result": 0}
    if _lstat(marker) is not None or _lstat(result_path) is not None: raise ProvisionError("attempt_consumed")
    secret_parent = (REPO_ROOT / DESTINATION_REL).parent; parent_info = _lstat(secret_parent)
    created = 0
    if plan["expected_secret_parent_state"] == "absent":
        if parent_info is not None: raise ProvisionError("parent_state_drift")
        _safe_chain(secret_parent.parent)
    else:
        _safe_chain(secret_parent)
        _check_deadline(operation_deadline_ns); _verify_path_acl(secret_parent, exact_secret=True); _check_deadline(operation_deadline_ns)
    destination = REPO_ROOT / DESTINATION_REL
    if _lstat(destination) is not None: raise ProvisionError("destination_present")
    _check_deadline(operation_deadline_ns); _preflight_real_console(); _check_deadline(operation_deadline_ns)
    marker_payload = canonical_bytes({"attempt_state": "started_before_secret_input", "contour_id": CONTOUR_ID,
                                      "plan_sha256": plan_sha, "run_id": RUN_ID, "schema_version": MARKER_SCHEMA}) + b"\n"
    _protected_provision_write_new(marker, marker_payload, operation_deadline_ns,
                                   protected_readback_counts, "marker")
    stage = "marker_created"
    created_for_result: int | str = 0 if plan["expected_secret_parent_state"] == "present" else "unknown"
    phone = otp = payload = None
    try:
        if plan["expected_secret_parent_state"] == "absent":
            _check_deadline(operation_deadline_ns); _secure_mkdir(secret_parent, operation_deadline_ns); _check_deadline(operation_deadline_ns); created = 1; created_for_result = 1
            _check_deadline(operation_deadline_ns); _verify_path_acl(secret_parent, exact_secret=True); _check_deadline(operation_deadline_ns)
        stage = "secret_parent_ready"
        budget = [0]; stage = "console_input_in_progress"
        phone = _read_console_digits(10, 10, operation_deadline_ns, budget, "Synthetic fixture input 1/2: ")
        otp = _read_console_digits(4, 8, operation_deadline_ns, budget, "Synthetic fixture input 2/2: ")
        payload = bytearray(b"EPIC_PHONE_001_PHONE_SUFFIX="); payload.extend(phone); payload.extend(b"\nEPIC_PHONE_001_OTP="); payload.extend(otp); payload.extend(b"\n")
        if len(payload) > MAX_PAYLOAD: raise ProvisionError("payload_budget_exhausted")
        stage = "destination_write_in_progress"
        _secure_write_new(destination, payload, operation_deadline_ns)
        stage = "destination_written"
        _check_deadline(operation_deadline_ns)
        terminal = canonical_bytes(_terminal_result(plan_sha, terminal_state="fixture_provisioned",
                                                    exit_category="success", directory_created=created_for_result,
                                                    execution_stage="terminal_result_finalization")) + b"\n"
        _protected_provision_write_new(result_path, terminal, deadline_ns,
                                       protected_readback_counts, "terminal_result")
    except BaseException:
        try:
            if _lstat(result_path) is None:
                terminal = canonical_bytes(_terminal_result(plan_sha, terminal_state="blocked_after_attempt",
                                                            exit_category="blocked", directory_created=created_for_result,
                                                            execution_stage=stage)) + b"\n"
                _protected_provision_write_new(result_path, terminal, deadline_ns,
                                               protected_readback_counts, "terminal_result")
        except BaseException:
            pass
        raise
    finally:
        for value in (phone, otp, payload):
            if isinstance(value, bytearray):
                for index in range(len(value)): value[index] = 0
    result = _aggregate(created)
    result.update({"git_head_validation_count": git_check_count,
                   "git_metadata_content_read_count": git_content_count,
                   "git_metadata_path_target_count": git_path_count})
    return result


def main() -> int:
    try: result = execute()
    except BaseException: return 2
    return 0


if __name__ == "__main__": sys.exit(main())

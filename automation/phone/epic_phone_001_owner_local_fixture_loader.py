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
PLAN_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION_PLAN"
GO_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION_GO"
GO_PREFIX = f"GO_EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION__{RUN_ID}__"
DEADLINE_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_DEADLINE_MONOTONIC_NS"
BOOTSTRAP_WALL_ENV = "EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_BOOTSTRAP_WALL_UTC"
EXECUTOR_REL = "automation/phone/epic_phone_001_fixture_interactive_provision.py"
LOADER_REL = "automation/phone/epic_phone_001_owner_local_fixture_loader.py"
MAX_PLAN = 64 * 1024
MAX_SOURCE = 96 * 1024
MAX_DEPTH = 12
MAX_INTEGER = 9_007_199_254_740_991
REPARSE_ATTRIBUTE = 0x400
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
WORKSPACE_CONTRACT = ()
BUDGET = {
    "acl_check_max": 5, "acl_create_max": 3, "application_action_max": 0,
    "authority_artifact_read_max": 4, "authentication_action_max": 0,
    "bounded_input_character_max": 128, "concurrency_max": 1,
    "console_api_validation_max": 3, "console_prompt_write_max": 2, "console_separator_write_max": 2, "destination_directory_create_max": 1,
    "destination_secret_file_create_max": 1, "device_action_max": 0,
    "execution_max": 1, "go_env_read_max": 2, "host_process_max": 1,
    "marker_file_create_max": 1, "network_action_max": 0,
    "no_echo_secret_field_read_max": 2, "overwrite_append_delete_rename_max": 0,
    "plan_env_read_max": 2, "retry_max": 0, "runtime_action_max": 0,
    "secret_payload_bytes_max": 96, "secret_payload_readback_max": 1,
    "secret_payload_write_max": 1, "subprocess_max": 0, "ui_action_max": 0,
    "cooperative_deadline_seconds_max": 120, "bootstrap_env_write_max": 2,
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
}
ROOT_KEYS = {
    "aggregate_contract", "authority_artifacts", "authority_objects", "budget", "classification",
    "contour_id", "controller_bytes", "controller_relative_path", "controller_sha256",
    "destination_relative_path", "epic_id", "executor_bytes", "executor_relative_path",
    "executor_sha256", "expected_secret_parent_state", "expires_at_utc", "failure_policy",
    "fixture_alias", "gitignore_bytes", "gitignore_relative_path", "gitignore_sha256",
    "inline_bootstrap_bytes", "inline_bootstrap_sha256", "input_contract", "issued_at_utc",
    "loader_bytes", "loader_relative_path", "loader_sha256", "marker_relative_path",
    "output_contract", "repository_head", "run_id", "schema_version", "security_alias",
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
        "network_action_count": 0, "no_echo_secret_field_read_count": 2,
        "runtime_action_count": 0, "schema_version": "epic-phone-001-owner-local-fixture-provision-result-v1",
        "secret_file_created_count": 1, "secret_payload_readback_count": 1,
        "secret_payload_write_count": 1, "status": "fixture_provisioned",
        "subprocess_count": 0, "ui_action_count": 0,
    }


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
    raw = os.environ[PLAN_ENV].encode("utf-8", errors="strict")
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
        "failure_policy": "marker_consumes_attempt_before_input_no_retry_overwrite_delete_rename_or_cleanup",
        "fixture_alias": "epic-phone-001-fixture-001", "gitignore_relative_path": ".gitignore",
        "input_contract": "two_real_console_no_echo_ascii_digit_fields_total_chars_max_128",
        "loader_relative_path": LOADER_REL,
        "marker_relative_path": ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/fixture-owner-provision-attempt.local.json",
        "output_contract": "exact_two_ascii_lf_lines_payload_max_96",
        "run_id": RUN_ID,
        "schema_version": SCHEMA, "security_alias": "epic-phone-001-security-owner-local-fixture-provision-001",
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
        "cooperative_timeout_acceptance": "epic-phone-001-owner-cooperative-timeout-acceptance-001",
        "fixture_authority": "epic-phone-001-fixture-authority-owner-provision-001",
        "owner_local_console_entry": "epic-phone-001-owner-local-console-entry-001",
        "provision_no_mutator_window": "epic-phone-001-owner-local-provision-no-mutator-001",
    }
    if type(authorities) is not dict or set(authorities) != set(expected_aliases): raise ValueError
    scopes = {
        "cooperative_timeout_acceptance": TIMEOUT_CONTRACT["owner_acceptance_scope"],
        "fixture_authority": "synthetic_fixture_alias_only",
        "owner_local_console_entry": "console_values_only_fixture_alias_not_recorded",
        "provision_no_mutator_window": "repo_loader_executor_local_authority_marker_destination",
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
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/c0p-plan.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/fixture-authority-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/target-build-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/evidence-cleanup-passport.local.json",
    )
    schemas = ("epic-phone-001-c0p-plan-v2", "epic-phone-001-fixture-authority-passport-v2",
               "epic-phone-001-target-build-passport-v2", "epic-phone-001-evidence-cleanup-passport-v2")
    artifact_contracts = (
        ("epic-phone-001-security-c0p-003", "execution_status", "planned_separate_literal_go_required_not_run", "expires_at_utc"),
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
    if os.environ.get(GO_ENV) != GO_PREFIX + digest: raise ValueError
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
    return plan


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


def main() -> int:
    try:
        plan = _plan(); target = Path.cwd() / EXECUTOR_REL
        source = _load_executor(target, plan["executor_bytes"], plan["executor_sha256"])
        sys.dont_write_bytecode = True
        namespace = {"__name__": "__owner_fixture_executor__", "__file__": str(target), "__package__": None}
        exec(compile(source, str(target), "exec", dont_inherit=True), namespace, namespace)
        entry = namespace.get("main")
        if not callable(entry): return 2
        result = entry()
        return result if type(result) is int and result in (0, 2) else 2
    except BaseException:
        return 2


if __name__ == "__main__": sys.exit(main())

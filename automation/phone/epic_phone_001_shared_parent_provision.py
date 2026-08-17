#!/usr/bin/env python3
"""Fail-closed shared-parent provisioning for EPIC-PHONE-001.

The executor creates only the two fixed ignored parent directories.  Execution
requires a fresh canonical public plan plus an independent literal Security GO.
It has no secret, device, application, network or child-process interface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import time
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
EPIC_ID = "EPIC-PHONE-001"
RUN_ID = "epic-phone-001-20260816-r01"
CONTOUR_ID = "epic-phone-001-shared-parent-provision"
CLASSIFICATION = "PROD_SAFE"
SCOPE_QUALIFIER = "ZERO_SECRET_ZERO_DEVICE_FIXED_SHARED_PARENT_PROVISIONING"
SCHEMA = "epic-phone-001-shared-parent-provision-plan-v1"
SECURITY_ALIAS = "epic-phone-001-security-shared-parent-001"
PLAN_ENV = "EPIC_PHONE_001_SHARED_PARENT_PLAN"
GO_ENV = "EPIC_PHONE_001_SHARED_PARENT_GO"
GO_PREFIX = f"GO_EPIC_PHONE_001_SHARED_PARENT_PROVISION__{RUN_ID}__"
TARGETS = (Path(".qa_local"), Path(".qa_local/evidence"))
ACTION_ORDER = ("create_qa_local_if_absent", "create_evidence_if_absent")
INITIAL_STATES = {"both_absent": 2, "qa_local_present_evidence_absent": 1}
CONTROLLER_REL = Path("automation/phone/epic_phone_001_runtime_controller.py")
HEAD_READER_REL = Path("automation/phone/epic_phone_001_c0p_prep.py")
GITIGNORE_REL = Path(".gitignore")
REPARSE_ATTRIBUTE = 0x400
MAX_PLAN_BYTES = 16 * 1024
MIN_FREE_BYTES = 64 * 1024 * 1024
MAX_VALIDITY = timedelta(minutes=10)


class ProvisionError(RuntimeError):
    """Fixed public-safe contract reason only."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _strict_json(data: bytes) -> Mapping[str, Any]:
    if not data or len(data) > MAX_PLAN_BYTES or data.startswith(b"\xef\xbb\xbf"):
        raise ProvisionError("plan_size_or_encoding_invalid")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ProvisionError("plan_size_or_encoding_invalid") from exc
    if unicodedata.normalize("NFC", text) != text:
        raise ProvisionError("plan_not_nfc")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        normalized: set[str] = set()
        for key, value in items:
            if type(key) is not str or key in result:
                raise ProvisionError("plan_duplicate_key")
            norm = unicodedata.normalize("NFC", key)
            if norm in normalized:
                raise ProvisionError("plan_duplicate_key")
            normalized.add(norm)
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=pairs)
    except RecursionError as exc:
        raise ProvisionError("plan_json_depth_invalid") from exc
    except UnicodeEncodeError as exc:
        raise ProvisionError("plan_unicode_scalar_invalid") from exc
    except (ValueError, ProvisionError) as exc:
        if isinstance(exc, ProvisionError):
            raise
        raise ProvisionError("plan_json_invalid") from exc
    try:
        canonical = canonical_bytes(value) if type(value) is dict else b""
    except RecursionError as exc:
        raise ProvisionError("plan_json_depth_invalid") from exc
    except UnicodeEncodeError as exc:
        raise ProvisionError("plan_unicode_scalar_invalid") from exc
    if type(value) is not dict or canonical != data:
        raise ProvisionError("plan_not_canonical")
    return value


def _exact(value: Any, expected: Any) -> bool:
    if type(value) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(value) == set(expected) and all(
            _exact(value[key], expected[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(value) == len(expected) and all(
            _exact(left, right) for left, right in zip(value, expected)
        )
    return value == expected


def _utc(value: str, label: str) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise ProvisionError(f"{label}_invalid")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ProvisionError(f"{label}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ProvisionError(f"{label}_invalid")
    return parsed


def _budget(initial_state: str) -> dict[str, int]:
    return {
        "application_action_max": 0,
        "authentication_action_max": 0,
        "child_subprocess_max": 0,
        "concurrency_max": 1,
        "content_bytes_write_max": 0,
        "device_action_max": 0,
        "directory_create_max": INITIAL_STATES[initial_state],
        "directory_target_count": 2,
        "git_metadata_read_max": 5,
        "go_env_read_max": 1,
        "execution_max": 1,
        "file_create_max": 0,
        "host_process_max": 1,
        "local_metadata_operation_max": 12,
        "network_action_max": 0,
        "overwrite_append_delete_rename_max": 0,
        "plan_env_read_max": 1,
        "retry_max": 0,
        "runtime_action_max": 0,
        "secret_read_max": 0,
        "serial_map_read_max": 0,
        "source_read_max": 4,
        "source_metadata_operation_max": 8,
        "subprocess_max": 1,
        "token_or_result_write_max": 0,
        "wall_clock_minutes_max": 2,
    }


def _aggregate(initial_state: str) -> dict[str, Any]:
    return {
        "application_action_count": 0,
        "authentication_action_count": 0,
        "child_subprocess_count": 0,
        "contour_id": CONTOUR_ID,
        "created_directory_count": INITIAL_STATES[initial_state],
        "device_action_count": 0,
        "epic_id": EPIC_ID,
        "file_create_count": 0,
        "host_executor_invocation_count": 1,
        "network_action_count": 0,
        "preexisting_safe_directory_count": 2 - INITIAL_STATES[initial_state],
        "run_id": RUN_ID,
        "runtime_action_count": 0,
        "secret_read_count": 0,
        "serial_map_read_count": 0,
        "status": "shared_parents_prepared",
        "subprocess_count": 1,
    }


def build_plan(
    *, repository_head: str, executor_sha256: str, controller_sha256: str,
    head_reader_sha256: str, gitignore_sha256: str, expected_initial_state: str,
    issued_at_utc: str, expires_at_utc: str,
) -> dict[str, Any]:
    """Build public-safe plan bytes without inspecting local target paths."""
    return {
        "action_order": list(ACTION_ORDER),
        "budget": _budget(expected_initial_state),
        "build_alias": "task058-selected-phone-full-001",
        "classification": CLASSIFICATION,
        "contour_id": CONTOUR_ID,
        "controller_source_sha256": controller_sha256,
        "directory_targets": [target.as_posix() for target in TARGETS],
        "epic_id": EPIC_ID,
        "executor_source_sha256": executor_sha256,
        "exclusive_workspace_attested": True,
        "expected_initial_state": expected_initial_state,
        "expires_at_utc": expires_at_utc,
        "failure_policy": "leave_first_created_parent_stop_no_retry_no_cleanup_no_reuse",
        "fixture_alias": "epic-phone-001-fixture-001",
        "gitignore_sha256": gitignore_sha256,
        "head_reader_source_sha256": head_reader_sha256,
        "initial_state_attestation": "category_only_security_bound_no_content_read",
        "issued_at_utc": issued_at_utc,
        "public_aggregate_contract": _aggregate(expected_initial_state),
        "repository_head": repository_head,
        "repository_head_authority": "security_attested_current_head",
        "run_id": RUN_ID,
        "schema_version": SCHEMA,
        "scope_qualifier": SCOPE_QUALIFIER,
        "security_alias": SECURITY_ALIAS,
        "target_alias": "phone-current-001",
        "unexpected_external_path_mutation_policy": "invalidate_go_stop_no_retry",
        "workspace_precondition": "security_attested_no_external_path_mutator_during_execution",
    }


def _validate_plan(plan: Mapping[str, Any], now: datetime) -> str:
    if type(plan.get("expected_initial_state")) is not str:
        raise ProvisionError("initial_state_invalid")
    initial = plan["expected_initial_state"]
    if initial not in INITIAL_STATES:
        raise ProvisionError("initial_state_invalid")
    expected = build_plan(
        repository_head=plan.get("repository_head"),
        executor_sha256=plan.get("executor_source_sha256"),
        controller_sha256=plan.get("controller_source_sha256"),
        head_reader_sha256=plan.get("head_reader_source_sha256"),
        gitignore_sha256=plan.get("gitignore_sha256"),
        expected_initial_state=initial,
        issued_at_utc=plan.get("issued_at_utc"),
        expires_at_utc=plan.get("expires_at_utc"),
    )
    try:
        exact = _exact(plan, expected)
    except RecursionError as exc:
        raise ProvisionError("plan_contract_depth_invalid") from exc
    if not exact:
        raise ProvisionError("plan_contract_invalid")
    for label in (
        "repository_head", "executor_source_sha256", "controller_source_sha256",
        "head_reader_source_sha256", "gitignore_sha256",
    ):
        value = plan[label]
        expected_length = 40 if label == "repository_head" else 64
        if type(value) is not str or len(value) != expected_length:
            raise ProvisionError(f"{label}_invalid")
        if any(char not in "0123456789abcdef" for char in value):
            raise ProvisionError(f"{label}_invalid")
    issued = _utc(plan["issued_at_utc"], "issued_at")
    expires = _utc(plan["expires_at_utc"], "expires_at")
    if issued > now or expires <= now or expires <= issued or expires - issued > MAX_VALIDITY:
        raise ProvisionError("plan_ttl_invalid")
    return _sha256(canonical_bytes(plan))


def _counted_lstat(
    path: Path, metadata: dict[str, Any], *, kind: str, cache: bool = False
) -> os.stat_result:
    key = (kind, str(path.absolute()))
    if cache and key in metadata["cache"]:
        return metadata["cache"][key]
    count_key = f"{kind}_count"
    metadata[count_key] += 1
    maximum = 12 if kind == "target" else 8
    if metadata[count_key] > maximum:
        raise ProvisionError(f"{kind}_metadata_budget_exhausted")
    info = path.lstat()
    if cache:
        metadata["cache"][key] = info
    return info


def _plain_dir_info(
    path: Path, metadata: dict[str, Any], *, cache: bool = False
) -> os.stat_result | None:
    try:
        info = _counted_lstat(path, metadata, kind="target", cache=cache)
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode) or int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE:
        raise ProvisionError("fixed_path_reparse")
    if not stat.S_ISDIR(info.st_mode):
        raise ProvisionError("fixed_path_not_directory")
    return info


def _lexically_contained(path: Path) -> None:
    raw = str(path).replace("/", "\\")
    if raw.startswith(("\\\\", "\\?\\", "\\.\\")):
        raise ProvisionError("fixed_path_namespace_invalid")
    try:
        path.absolute().relative_to(REPO_ROOT.absolute())
    except ValueError as exc:
        raise ProvisionError("fixed_path_outside_repository") from exc


def _read_bound_source(
    path: Path, expected_sha: str, label: str, maximum: int,
    metadata: dict[str, Any],
) -> bytes:
    _lexically_contained(path)
    try:
        relative = path.absolute().relative_to(REPO_ROOT.absolute())
    except ValueError as exc:
        raise ProvisionError(f"{label}_outside_repository") from exc
    cursor = REPO_ROOT
    components = (Path(), *relative.parts)
    info: os.stat_result | None = None
    for index, part in enumerate(components):
        if index:
            cursor = cursor / part
        try:
            info = _counted_lstat(cursor, metadata, kind="source", cache=True)
        except FileNotFoundError as exc:
            raise ProvisionError(f"{label}_missing") from exc
        if stat.S_ISLNK(info.st_mode) or int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE:
            raise ProvisionError(f"{label}_reparse")
        if index < len(components) - 1 and not stat.S_ISDIR(info.st_mode):
            raise ProvisionError(f"{label}_ancestor_not_directory")
    if info is None or not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
        raise ProvisionError(f"{label}_invalid")
    with path.open("rb") as handle:
        data = handle.read(maximum + 1)
    if len(data) > maximum or _sha256(data) != expected_sha:
        raise ProvisionError(f"{label}_hash_mismatch")
    return data


def _validate_ignore(data: bytes) -> None:
    try:
        lines = data.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError as exc:
        raise ProvisionError("gitignore_encoding_invalid") from exc
    if ".qa_local/" not in lines:
        raise ProvisionError("gitignore_rule_missing")


def _current_head(bound_source: bytes) -> str:
    namespace: dict[str, Any] = {
        "__file__": str(REPO_ROOT / HEAD_READER_REL),
        "__name__": "_epic_phone_001_bound_head_reader",
    }
    try:
        text = bound_source.decode("utf-8", errors="strict")
        exec(compile(text, str(REPO_ROOT / HEAD_READER_REL), "exec"), namespace)
        reader = namespace["_read_repository_head"]
        value = reader()
    except Exception as exc:
        raise ProvisionError("current_head_read_failed") from exc
    if type(value) is not str or len(value) != 40 or any(
        char not in "0123456789abcdef" for char in value
    ):
        raise ProvisionError("current_head_invalid")
    return value


def _classify(metadata: dict[str, Any]) -> str:
    for target in TARGETS:
        _lexically_contained(REPO_ROOT / target)
    root_info = _plain_dir_info(REPO_ROOT, metadata, cache=True)
    if root_info is None:
        raise ProvisionError("repository_root_missing")
    qa_info = _plain_dir_info(REPO_ROOT / TARGETS[0], metadata)
    if qa_info is None:
        return "both_absent"
    evidence_info = _plain_dir_info(REPO_ROOT / TARGETS[1], metadata)
    if evidence_info is None:
        return "qa_local_present_evidence_absent"
    raise ProvisionError("shared_parents_already_present")


def _deadline(deadline: float) -> None:
    if time.monotonic() > deadline:
        raise ProvisionError("wall_clock_budget_exhausted")


def _mutation_checkpoint(target: Path, metadata: dict[str, Any]) -> None:
    _lexically_contained(target)
    if _plain_dir_info(REPO_ROOT, metadata) is None:
        raise ProvisionError("repository_root_missing")
    if target == REPO_ROOT / TARGETS[1]:
        if _plain_dir_info(REPO_ROOT / TARGETS[0], metadata) is None:
            raise ProvisionError("shared_parent_missing_before_action")


def execute(now: datetime | None = None) -> Mapping[str, Any]:
    raw = os.environ.get(PLAN_ENV)
    if raw is None:
        raise ProvisionError("plan_env_missing")
    try:
        data = raw.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ProvisionError("plan_env_encoding_invalid") from exc
    plan = _strict_json(data)
    current = now or datetime.now(UTC)
    plan_hash = _validate_plan(plan, current)
    if os.environ.get(GO_ENV) != GO_PREFIX + plan_hash:
        raise ProvisionError("literal_security_go_invalid")
    deadline = time.monotonic() + plan["budget"]["wall_clock_minutes_max"] * 60
    metadata = {"source_count": 0, "target_count": 0, "cache": {}}
    _read_bound_source(
        Path(__file__), plan["executor_source_sha256"], "executor_source", 64 * 1024,
        metadata,
    )
    _read_bound_source(
        REPO_ROOT / CONTROLLER_REL, plan["controller_source_sha256"],
        "controller_source", 64 * 1024, metadata,
    )
    head_reader = _read_bound_source(
        REPO_ROOT / HEAD_READER_REL, plan["head_reader_source_sha256"],
        "head_reader_source", 128 * 1024, metadata,
    )
    gitignore = _read_bound_source(
        REPO_ROOT / GITIGNORE_REL, plan["gitignore_sha256"], "gitignore",
        128 * 1024, metadata,
    )
    _validate_ignore(gitignore)
    if _current_head(head_reader) != plan["repository_head"]:
        raise ProvisionError("repository_head_drift")
    _deadline(deadline)
    actual = _classify(metadata)
    if actual != plan["expected_initial_state"]:
        raise ProvisionError("initial_state_mismatch")
    if shutil.disk_usage(REPO_ROOT).free < MIN_FREE_BYTES:
        raise ProvisionError("local_capacity_insufficient")
    _deadline(deadline)

    created = 0
    targets = [REPO_ROOT / target for target in TARGETS]
    start = 0 if actual == "both_absent" else 1
    for target in targets[start:]:
        _deadline(deadline)
        _mutation_checkpoint(target, metadata)
        try:
            target.mkdir()
        except FileExistsError as exc:
            raise ProvisionError("fixed_directory_collision") from exc
        created += 1
        _mutation_checkpoint(target, metadata)
        _plain_dir_info(target, metadata)
    _deadline(deadline)
    if created != plan["budget"]["directory_create_max"]:
        raise ProvisionError("directory_budget_mismatch")
    return dict(plan["public_aggregate_contract"])


def validate_only() -> Mapping[str, Any]:
    return {
        "classification": CLASSIFICATION,
        "contour_id": CONTOUR_ID,
        "epic_id": EPIC_ID,
        "execution_requires_literal_security_go": True,
        "fixed_directory_targets": [target.as_posix() for target in TARGETS],
        "run_id": RUN_ID,
        "scope_qualifier": SCOPE_QUALIFIER,
        "secret_device_app_network_auth_runtime_max": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_only() if args.validate_only else execute()
    except KeyboardInterrupt:
        print("operation_interrupted_fail_closed", file=sys.stderr)
        return 130
    except ProvisionError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except OSError:
        print("local_io_error_fail_closed", file=sys.stderr)
        return 3
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""One-shot, fail-closed local preparation for EPIC-PHONE-001 C0P.

This executable never reads fixture values, a serial map, a device, an app, or
the network.  It only materializes a Security-reviewed, public-safe candidate
into the fixed ignored run root. Exclusive creation of the task-specific prep
attempt root is the first mutation and durable marker: after it succeeds, every
failure is terminal and no cleanup or retry is performed by this executable.
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
import types
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence


EPIC_ID = "EPIC-PHONE-001"
RUN_ID = "epic-phone-001-20260816-r01"
CONTOUR_ID = "epic-phone-001-c0p-prep"
PREP_ATTEMPT_ID = "c0p-prep-002"
TARGET_ALIAS = "phone-current-001"
BUILD_ALIAS = "task058-selected-phone-full-001"
FIXTURE_ALIAS = "epic-phone-001-fixture-001"
CLASSIFICATION = "PROD_SAFE"
SCOPE_QUALIFIER = "ZERO_SECRET_ZERO_DEVICE_LOCAL_PREPARATION"

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_REL = Path("automation/phone/epic_phone_001_c0p_prep.py")
CONTROLLER_REL = Path("automation/phone/epic_phone_001_runtime_controller.py")
CANDIDATE_REL = Path("docs/qa/phone/epic-phone-001-c0p-prep-candidate.json")
PREP_PLAN_REL = Path("docs/qa/phone/epic-phone-001-c0p-prep-plan.json")
GITIGNORE_REL = Path(".gitignore")
RUN_ROOT_REL = Path(".qa_local/evidence/epic-phone-001") / RUN_ID
ATTEMPT_ROOT_REL = Path(".qa_local/evidence/epic-phone-001")
RAW_REL = RUN_ROOT_REL / "raw"
CHECKPOINTS_REL = RUN_ROOT_REL / "checkpoints"
PUBLIC_SAFE_REL = RUN_ROOT_REL / "public-safe"

C0P_PLAN_REL = RUN_ROOT_REL / "c0p-plan.local.json"
FIXTURE_PASSPORT_REL = RUN_ROOT_REL / "fixture-authority-passport.local.json"
TARGET_BUILD_PASSPORT_REL = RUN_ROOT_REL / "target-build-passport.local.json"
EVIDENCE_CLEANUP_PASSPORT_REL = RUN_ROOT_REL / "evidence-cleanup-passport.local.json"

CANDIDATE_SCHEMA = "epic-phone-001-c0p-prep-candidate-v2"
PLAN_SCHEMA = "epic-phone-001-c0p-prep-plan-v2"
RESULT_SCHEMA = "epic-phone-001-c0p-prep-result-v2"
GO_ENV = "EPIC_PHONE_001_C0P_PREP_GO"
GO_PREFIX = f"GO_EPIC_PHONE_001_C0P_PREP__{RUN_ID}__"
MAX_CANDIDATE_BYTES = 32 * 1024
MAX_SINGLE_ARTIFACT_BYTES = 8 * 1024
MAX_VALIDITY = timedelta(minutes=30)
MIN_FREE_BYTES = 64 * 1024 * 1024
REPARSE_ATTRIBUTE = 0x400

DIRECTORY_TARGETS = [
    ".qa_local",
    ".qa_local/evidence",
    ".qa_local/evidence/epic-phone-001",
    RUN_ROOT_REL.as_posix(),
    RAW_REL.as_posix(),
    CHECKPOINTS_REL.as_posix(),
    PUBLIC_SAFE_REL.as_posix(),
]
ARTIFACT_PATHS = [
    C0P_PLAN_REL.as_posix(),
    FIXTURE_PASSPORT_REL.as_posix(),
    TARGET_BUILD_PASSPORT_REL.as_posix(),
    EVIDENCE_CLEANUP_PASSPORT_REL.as_posix(),
]
BUDGET = {
    "execution_max": 1,
    "retry_max": 0,
    "subprocess_max": 1,
    "host_process_max": 1,
    "child_subprocess_max": 0,
    "concurrency_max": 1,
    "wall_clock_minutes_max": 5,
    "directory_target_count": 7,
    "directory_create_max": 5,
    "file_create_max": 4,
    "candidate_read_max": 1,
    "prep_plan_read_max": 1,
    "tracked_source_read_max": 4,
    "git_metadata_read_max": 5,
    "metadata_path_target_max": 32,
    "created_file_readback_max": 4,
    "single_file_bytes_max": MAX_SINGLE_ARTIFACT_BYTES,
    "total_created_bytes_max": MAX_CANDIDATE_BYTES,
    "minimum_free_bytes": MIN_FREE_BYTES,
    "secret_read_max": 0,
    "device_action_max": 0,
    "application_action_max": 0,
    "network_action_max": 0,
    "authentication_action_max": 0,
    "runtime_action_max": 0,
    "overwrite_append_delete_rename_max": 0,
}


class PrepError(RuntimeError):
    """Fixed, public-safe fail-closed reason."""


def _nfc(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for raw_key, item in value.items():
            if not isinstance(raw_key, str):
                raise PrepError("canonical_key_not_string")
            key = unicodedata.normalize("NFC", raw_key)
            if key in result:
                raise PrepError("canonical_duplicate_nfc_key")
            result[key] = _nfc(item)
        return result
    if value is None or isinstance(value, (str, bool, int)):
        return value
    raise PrepError("canonical_type_invalid")


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        _nfc(dict(value)),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_pairs(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        normalized = unicodedata.normalize("NFC", key)
        if normalized in result:
            raise PrepError("candidate_duplicate_key")
        result[normalized] = value
    return result


def _strict_json(data: bytes, label: str, maximum: int) -> Mapping[str, Any]:
    if not data or len(data) > maximum:
        raise PrepError(f"{label}_size_invalid")
    try:
        text = data.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_strict_pairs,
            parse_constant=lambda _value: (_ for _ in ()).throw(PrepError(f"{label}_constant_invalid")),
        )
    except UnicodeDecodeError as exc:
        raise PrepError(f"{label}_utf8_invalid") from exc
    except json.JSONDecodeError as exc:
        raise PrepError(f"{label}_json_invalid") from exc
    if not isinstance(value, dict):
        raise PrepError(f"{label}_not_object")
    return value


def _exact_object(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise PrepError(f"{label}_keyset_invalid")
    return value


def _parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PrepError(f"{label}_not_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PrepError(f"{label}_invalid") from exc
    return parsed.astimezone(UTC)


def _relative_fixed(path: Path, label: str) -> Path:
    base = REPO_ROOT.absolute()
    candidate = path.absolute()
    try:
        relative = candidate.relative_to(base)
    except ValueError as exc:
        raise PrepError(f"{label}_outside_repository") from exc
    if ".." in relative.parts:
        raise PrepError(f"{label}_lexical_escape")
    return relative


def _reject_fixed_chain(path: Path, label: str, *, final_may_be_missing: bool = False) -> None:
    root_info = REPO_ROOT.lstat()
    if REPO_ROOT.is_symlink() or int(getattr(root_info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE:
        raise PrepError("repository_root_reparse")
    relative = _relative_fixed(path, label)
    cursor = REPO_ROOT
    for index, part in enumerate(relative.parts):
        cursor = cursor / part
        final = index == len(relative.parts) - 1
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            if final and final_may_be_missing:
                return
            raise PrepError(f"{label}_ancestor_missing")
        attributes = int(getattr(info, "st_file_attributes", 0))
        if cursor.is_symlink() or attributes & REPARSE_ATTRIBUTE:
            raise PrepError(f"{label}_ancestor_reparse")
        if not final and not stat.S_ISDIR(info.st_mode):
            raise PrepError(f"{label}_ancestor_not_directory")


def _safe_fixed_file(path: Path, label: str, maximum: int) -> bytes:
    _reject_fixed_chain(path, label)
    root = REPO_ROOT.resolve(strict=True)
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise PrepError(f"{label}_outside_repository") from exc
    info = path.lstat()
    attributes = int(getattr(info, "st_file_attributes", 0))
    if path.is_symlink() or attributes & REPARSE_ATTRIBUTE or not stat.S_ISREG(info.st_mode):
        raise PrepError(f"{label}_not_plain_file")
    data = path.read_bytes()
    if not data or len(data) > maximum:
        raise PrepError(f"{label}_size_invalid")
    return data


def _source_sha(path: Path, label: str) -> str:
    return _sha256(_safe_fixed_file(path, label, 1024 * 1024))


def _load_controller(expected_sha256: str) -> Any:
    source = REPO_ROOT / CONTROLLER_REL
    try:
        source_bytes = _safe_fixed_file(source, "controller_source", 1024 * 1024)
        if _sha256(source_bytes) != expected_sha256:
            raise PrepError("controller_executed_source_drift")
        source_text = source_bytes.decode("utf-8", errors="strict")
        code = compile(source_text, CONTROLLER_REL.as_posix(), "exec", dont_inherit=True)
        module = types.ModuleType("epic_phone_001_runtime_controller_for_prep")
        module.__file__ = str(source)
        exec(code, module.__dict__)
    except PrepError:
        raise
    except Exception as exc:
        raise PrepError("controller_import_failed") from exc
    return module


def _artifact(path: str, value: Mapping[str, Any]) -> dict[str, Any]:
    data = canonical_bytes(value)
    return {"path": path, "bytes": len(data), "sha256": _sha256(data), "canonical_json": dict(value)}


def build_candidate(
    *,
    repository_head: str,
    controller_source_sha256: str,
    executor_source_sha256: str,
    issued_at_utc: str,
    expires_at_utc: str,
    passport_expires_at_utc: str,
    retention_expires_at_utc: str,
) -> dict[str, Any]:
    """Build public-safe canonical candidate bytes; this performs no local writes."""

    controller = _load_controller(controller_source_sha256)
    c0p = controller.c0p_plan(repository_head, controller_source_sha256)
    fixture = {
        "schema_version": controller.FIXTURE_PASSPORT_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "fixture_alias": FIXTURE_ALIAS,
        "synthetic_test_only": True,
        "not_real_user": True,
        "values_local_only": True,
        "revoked": False,
        "authority_validity": "current_epic_run_until_completion_or_revocation",
        "allowed_scope": ["synthetic_session_create", "read_only_navigation", "safe_logout"],
        "forbidden_scope": [
            "payment", "subscription", "entitlement", "profile", "account",
            "paid_session", "external_or_qr_traversal",
        ],
        "issued_at_utc": issued_at_utc,
        "expires_at_utc": passport_expires_at_utc,
    }
    target = {
        "schema_version": controller.TARGET_BUILD_PASSPORT_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "target_authorized": True,
        "build_authorized": True,
        "launch_allowed": False,
        "mutation_allowed": False,
        "passport_purpose": "authorization_only",
        "current_freshness_evidence": False,
        "runtime_evidence": False,
        "issued_at_utc": issued_at_utc,
        "expires_at_utc": passport_expires_at_utc,
    }
    cleanup = {
        "schema_version": controller.EVIDENCE_CLEANUP_PASSPORT_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "run_root": RUN_ROOT_REL.as_posix(),
        "soft_bytes_max": controller.C1_BUDGET["raw_sink_soft_bytes_max"],
        "hard_bytes_max": controller.C1_BUDGET["raw_sink_hard_bytes_max"],
        "redaction_default": True,
        "direct_capture_no_echo": True,
        "cleanup_sequence": [
            "target_only_force_stop", "home", "post_kill_checkpoint", "capture_shutdown",
        ],
        "forbidden_action_count": 0,
        "passport_purpose": "policy_readiness_only",
        "execution_evidence": False,
        "retention_expires_at_utc": retention_expires_at_utc,
    }
    artifacts = [
        _artifact(C0P_PLAN_REL.as_posix(), c0p),
        _artifact(FIXTURE_PASSPORT_REL.as_posix(), fixture),
        _artifact(TARGET_BUILD_PASSPORT_REL.as_posix(), target),
        _artifact(EVIDENCE_CLEANUP_PASSPORT_REL.as_posix(), cleanup),
    ]
    return {
        "schema_version": CANDIDATE_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "prep_attempt_id": PREP_ATTEMPT_ID,
        "classification": CLASSIFICATION,
        "scope_qualifier": SCOPE_QUALIFIER,
        "execution_status": "planned_literal_security_go_required_not_run",
        "repository_head": repository_head,
        "controller_source_sha256": controller_source_sha256,
        "executor_source_sha256": executor_source_sha256,
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "issued_at_utc": issued_at_utc,
        "expires_at_utc": expires_at_utc,
        "run_root": RUN_ROOT_REL.as_posix(),
        "attempt_root": ATTEMPT_ROOT_REL.as_posix(),
        "durable_attempt_marker": "exclusive_attempt_root_creation_first_mutation",
        "directory_targets": list(DIRECTORY_TARGETS),
        "artifacts": artifacts,
        "budget": dict(BUDGET),
        "public_aggregate_contract": {
            "schema_version": RESULT_SCHEMA,
            "status": "prepared",
            "prep_attempt_id": PREP_ATTEMPT_ID,
            "directory_target_count": 7,
            "directory_created_count_on_success": 5,
            "file_created_count_on_success": 4,
            "host_process_count_on_success": 1,
            "child_subprocess_count_on_success": 0,
            "all_secret_device_app_network_auth_runtime_counters": 0,
        },
        "failure_policy": "leave_partial_attempt_root_stop_no_retry_no_cleanup_no_reuse",
        "security_token_format": GO_PREFIX + "<64_lowercase_plan_sha256>",
    }


def build_prep_plan(
    candidate_data: bytes,
    *,
    repository_head: str,
    controller_source_sha256: str,
    executor_source_sha256: str,
    gitignore_sha256: str,
    issued_at_utc: str,
    expires_at_utc: str,
) -> dict[str, Any]:
    """Build the fixed public-safe runtime plan that Security binds with a literal GO."""

    return {
        "schema_version": PLAN_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "prep_attempt_id": PREP_ATTEMPT_ID,
        "classification": CLASSIFICATION,
        "scope_qualifier": SCOPE_QUALIFIER,
        "repository_head": repository_head,
        "controller_source_sha256": controller_source_sha256,
        "executor_source_sha256": executor_source_sha256,
        "gitignore_sha256": gitignore_sha256,
        "candidate_path": CANDIDATE_REL.as_posix(),
        "candidate_bytes": len(candidate_data),
        "candidate_sha256": _sha256(candidate_data),
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "run_root": RUN_ROOT_REL.as_posix(),
        "attempt_root": ATTEMPT_ROOT_REL.as_posix(),
        "durable_attempt_marker": "exclusive_attempt_root_creation_first_mutation",
        "directory_targets": list(DIRECTORY_TARGETS),
        "artifact_paths": list(ARTIFACT_PATHS),
        "issued_at_utc": issued_at_utc,
        "expires_at_utc": expires_at_utc,
        "budget": dict(BUDGET),
        "literal_go_format": GO_PREFIX + "<64_lowercase_plan_sha256>",
        "failure_policy": "leave_partial_attempt_root_stop_no_retry_no_cleanup_no_reuse",
    }


def _exact_equal(value: Any, expected: Any) -> bool:
    if type(value) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(value) == set(expected) and all(_exact_equal(value[key], expected[key]) for key in expected)
    if isinstance(expected, list):
        return len(value) == len(expected) and all(_exact_equal(a, b) for a, b in zip(value, expected))
    return value == expected


def _validate_prep_plan(
    plan: Mapping[str, Any], candidate_data: bytes, now: datetime
) -> str:
    keys = {
        "schema_version", "epic_id", "run_id", "contour_id", "prep_attempt_id",
        "classification",
        "scope_qualifier", "repository_head", "controller_source_sha256",
        "executor_source_sha256", "gitignore_sha256", "candidate_path",
        "candidate_bytes", "candidate_sha256", "target_alias", "build_alias",
        "fixture_alias", "run_root", "attempt_root", "durable_attempt_marker",
        "directory_targets", "artifact_paths",
        "issued_at_utc", "expires_at_utc", "budget", "literal_go_format",
        "failure_policy",
    }
    bound = _exact_object(plan, keys, "prep_plan")
    expected_fixed = {
        "schema_version": PLAN_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "prep_attempt_id": PREP_ATTEMPT_ID,
        "classification": CLASSIFICATION,
        "scope_qualifier": SCOPE_QUALIFIER,
        "candidate_path": CANDIDATE_REL.as_posix(),
        "candidate_bytes": len(candidate_data),
        "candidate_sha256": _sha256(candidate_data),
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "run_root": RUN_ROOT_REL.as_posix(),
        "attempt_root": ATTEMPT_ROOT_REL.as_posix(),
        "durable_attempt_marker": "exclusive_attempt_root_creation_first_mutation",
        "directory_targets": DIRECTORY_TARGETS,
        "artifact_paths": ARTIFACT_PATHS,
        "budget": BUDGET,
        "literal_go_format": GO_PREFIX + "<64_lowercase_plan_sha256>",
        "failure_policy": "leave_partial_attempt_root_stop_no_retry_no_cleanup_no_reuse",
    }
    if any(not _exact_equal(bound.get(key), expected) for key, expected in expected_fixed.items()):
        raise PrepError("prep_plan_fixed_binding_invalid")
    for label, digest, length in (
        ("repository_head", bound.get("repository_head"), 40),
        ("controller_source", bound.get("controller_source_sha256"), 64),
        ("executor_source", bound.get("executor_source_sha256"), 64),
        ("gitignore", bound.get("gitignore_sha256"), 64),
        ("candidate", bound.get("candidate_sha256"), 64),
    ):
        if not isinstance(digest, str) or len(digest) != length or any(char not in "0123456789abcdef" for char in digest):
            raise PrepError(f"prep_plan_{label}_binding_invalid")
    issued = _parse_utc(bound["issued_at_utc"], "prep_plan_issued_at")
    expires = _parse_utc(bound["expires_at_utc"], "prep_plan_expires_at")
    if issued > now or expires <= now or expires <= issued or expires - issued > MAX_VALIDITY:
        raise PrepError("prep_plan_ttl_invalid")
    return _sha256(canonical_bytes(bound))


def _validate_candidate(value: Mapping[str, Any], now: datetime) -> tuple[str, list[tuple[Path, bytes]]]:
    keys = {
        "schema_version", "epic_id", "run_id", "contour_id", "prep_attempt_id",
        "classification",
        "scope_qualifier", "execution_status", "repository_head",
        "controller_source_sha256", "executor_source_sha256", "target_alias",
        "build_alias", "fixture_alias", "issued_at_utc", "expires_at_utc",
        "run_root", "attempt_root", "durable_attempt_marker", "directory_targets",
        "artifacts", "budget",
        "public_aggregate_contract", "failure_policy", "security_token_format",
    }
    candidate = _exact_object(value, keys, "candidate")
    fixed = {
        "schema_version": CANDIDATE_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "prep_attempt_id": PREP_ATTEMPT_ID,
        "classification": CLASSIFICATION,
        "scope_qualifier": SCOPE_QUALIFIER,
        "execution_status": "planned_literal_security_go_required_not_run",
        "target_alias": TARGET_ALIAS,
        "build_alias": BUILD_ALIAS,
        "fixture_alias": FIXTURE_ALIAS,
        "run_root": RUN_ROOT_REL.as_posix(),
        "attempt_root": ATTEMPT_ROOT_REL.as_posix(),
        "durable_attempt_marker": "exclusive_attempt_root_creation_first_mutation",
        "directory_targets": DIRECTORY_TARGETS,
        "budget": BUDGET,
        "public_aggregate_contract": {
            "schema_version": RESULT_SCHEMA,
            "status": "prepared",
            "prep_attempt_id": PREP_ATTEMPT_ID,
            "directory_target_count": 7,
            "directory_created_count_on_success": 5,
            "file_created_count_on_success": 4,
            "host_process_count_on_success": 1,
            "child_subprocess_count_on_success": 0,
            "all_secret_device_app_network_auth_runtime_counters": 0,
        },
        "failure_policy": "leave_partial_attempt_root_stop_no_retry_no_cleanup_no_reuse",
        "security_token_format": GO_PREFIX + "<64_lowercase_plan_sha256>",
    }
    if any(not _exact_equal(candidate.get(key), expected) for key, expected in fixed.items()):
        raise PrepError("candidate_fixed_binding_invalid")
    issued = _parse_utc(candidate["issued_at_utc"], "candidate_issued_at")
    expires = _parse_utc(candidate["expires_at_utc"], "candidate_expires_at")
    if issued > now or expires <= now or expires <= issued or expires - issued > MAX_VALIDITY:
        raise PrepError("candidate_ttl_invalid")

    repository_head = candidate["repository_head"]
    controller_sha = candidate["controller_source_sha256"]
    executor_sha = candidate["executor_source_sha256"]
    if not isinstance(repository_head, str) or len(repository_head) != 40 or any(
        char not in "0123456789abcdef" for char in repository_head
    ):
        raise PrepError("candidate_repository_head_invalid")
    for label, digest in (("controller", controller_sha), ("executor", executor_sha)):
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise PrepError(f"candidate_{label}_sha_invalid")

    controller = _load_controller(controller_sha)
    artifacts = candidate["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != 4:
        raise PrepError("candidate_artifacts_invalid")
    materialized: list[tuple[Path, bytes]] = []
    for index, expected_path in enumerate(ARTIFACT_PATHS):
        artifact = _exact_object(
            artifacts[index], {"path", "bytes", "sha256", "canonical_json"}, f"artifact_{index}",
        )
        if artifact["path"] != expected_path or not isinstance(artifact["canonical_json"], dict):
            raise PrepError("artifact_path_or_payload_invalid")
        data = canonical_bytes(artifact["canonical_json"])
        if (
            type(artifact["bytes"]) is not int
            or artifact["bytes"] != len(data)
            or not isinstance(artifact["sha256"], str)
            or artifact["sha256"] != _sha256(data)
            or len(data) > MAX_SINGLE_ARTIFACT_BYTES
        ):
            raise PrepError("artifact_bytes_hash_invalid")
        materialized.append((REPO_ROOT / Path(expected_path), data))
    if sum(len(data) for _, data in materialized) > MAX_CANDIDATE_BYTES:
        raise PrepError("artifact_total_bytes_invalid")

    try:
        expected_c0p = controller.c0p_plan(repository_head, controller_sha)
        if not _exact_equal(artifacts[0]["canonical_json"], expected_c0p):
            raise PrepError("c0p_plan_contract_drift")
        controller._validate_fixture_passport(artifacts[1]["canonical_json"])
        controller._validate_target_build_passport(artifacts[2]["canonical_json"])
        controller._validate_evidence_cleanup_passport(artifacts[3]["canonical_json"])
    except PrepError:
        raise
    except Exception as exc:
        raise PrepError("artifact_contract_invalid") from exc
    for label, passport in (
        ("fixture_passport", artifacts[1]["canonical_json"]),
        ("target_build_passport", artifacts[2]["canonical_json"]),
    ):
        passport_issued = _parse_utc(passport["issued_at_utc"], f"{label}_issued_at")
        passport_expiry = _parse_utc(passport["expires_at_utc"], f"{label}_expires_at")
        if (
            passport_issued != issued
            or passport_issued > now
            or passport_expiry <= now
            or passport_expiry <= passport_issued
            or passport_expiry - passport_issued > timedelta(hours=2)
        ):
            raise PrepError(f"{label}_ttl_invalid")
    retention_expiry = _parse_utc(
        artifacts[3]["canonical_json"]["retention_expires_at_utc"], "retention_expiry",
    )
    if retention_expiry <= now or retention_expiry - issued > timedelta(hours=24):
        raise PrepError("retention_ttl_invalid")
    return _sha256(canonical_bytes(candidate)), materialized


def _bounded_text(path: Path, label: str, maximum: int = 64 * 1024) -> str:
    try:
        info = path.lstat()
    except OSError as exc:
        raise PrepError(f"{label}_missing") from exc
    if path.is_symlink() or int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE or not stat.S_ISREG(info.st_mode):
        raise PrepError(f"{label}_not_plain_file")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise PrepError(f"{label}_read_failed") from exc
    if not data or len(data) > maximum:
        raise PrepError(f"{label}_size_invalid")
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise PrepError(f"{label}_utf8_invalid") from exc


def _bounded_git_text(path: Path, label: str, common: Path, maximum: int = 64 * 1024) -> str:
    try:
        relative = path.absolute().relative_to(common.absolute())
    except ValueError as exc:
        raise PrepError(f"{label}_outside_git_metadata") from exc
    if ".." in relative.parts:
        raise PrepError(f"{label}_git_metadata_escape")
    cursor = common
    for index, part in enumerate(relative.parts):
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except OSError as exc:
            raise PrepError(f"{label}_missing") from exc
        if cursor.is_symlink() or int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE:
            raise PrepError(f"{label}_git_metadata_reparse")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise PrepError(f"{label}_git_ancestor_not_directory")
    return _bounded_text(path, label, maximum)


def _bounded_git_lstat_optional(path: Path, label: str, common: Path) -> os.stat_result | None:
    try:
        relative = path.absolute().relative_to(common.absolute())
    except ValueError as exc:
        raise PrepError(f"{label}_outside_git_metadata") from exc
    if ".." in relative.parts:
        raise PrepError(f"{label}_git_metadata_escape")
    cursor = common
    for index, part in enumerate(relative.parts):
        cursor = cursor / part
        final = index == len(relative.parts) - 1
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            # A missing loose-ref component means the loose ref is absent;
            # packed-refs may still provide it.  No target has been followed.
            return None
        if _stat_is_reparse_or_link(info):
            raise PrepError(f"{label}_git_metadata_reparse")
        if not final and not stat.S_ISDIR(info.st_mode):
            raise PrepError(f"{label}_git_ancestor_not_directory")
    return info


def _lstat_optional(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _stat_is_reparse_or_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE
    )


def _reject_absolute_reparse_chain(path: Path, label: str) -> Path:
    """Validate an exact absolute metadata path without resolving junctions."""

    raw_text = str(path).replace("/", "\\")
    if os.name == "nt" and raw_text.startswith("\\\\"):
        raise PrepError(f"{label}_remote_or_device_namespace")
    absolute = Path(os.path.abspath(path))
    if os.name == "nt":
        repository_drive = Path(os.path.abspath(REPO_ROOT)).drive.casefold()
        if not absolute.drive or absolute.drive.casefold() != repository_drive:
            raise PrepError(f"{label}_remote_or_foreign_volume")
    parts = absolute.parts
    if not parts:
        raise PrepError(f"{label}_empty")
    cursor = Path(parts[0])
    for part in parts[1:]:
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except OSError as exc:
            raise PrepError(f"{label}_missing") from exc
        if cursor.is_symlink() or int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE:
            raise PrepError(f"{label}_reparse")
    return absolute


def _read_repository_head() -> str:
    dotgit = REPO_ROOT / ".git"
    try:
        info = dotgit.lstat()
    except OSError as exc:
        raise PrepError("git_pointer_invalid") from exc
    if dotgit.is_symlink() or int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE:
        raise PrepError("git_pointer_reparse")
    if stat.S_ISDIR(info.st_mode):
        gitdir = _reject_absolute_reparse_chain(dotgit, "git_directory")
    elif stat.S_ISREG(info.st_mode):
        pointer = _bounded_text(dotgit, "git_pointer", 4096).strip()
        if not pointer.startswith("gitdir: "):
            raise PrepError("git_pointer_invalid")
        raw = Path(pointer[8:])
        gitdir = _reject_absolute_reparse_chain(
            raw if raw.is_absolute() else REPO_ROOT / raw, "git_directory"
        )
    else:
        raise PrepError("git_pointer_invalid")
    commondir_file = gitdir / "commondir"
    commondir_info = _lstat_optional(commondir_file)
    if commondir_info is not None:
        if _stat_is_reparse_or_link(commondir_info) or not stat.S_ISREG(commondir_info.st_mode):
            raise PrepError("git_commondir_not_plain_file")
        _reject_absolute_reparse_chain(commondir_file, "git_commondir")
        relative = Path(_bounded_text(commondir_file, "git_commondir", 4096).strip())
        if relative.is_absolute():
            raise PrepError("git_commondir_absolute")
        common = _reject_absolute_reparse_chain(gitdir / relative, "git_common_root")
    else:
        common = gitdir
    if common.name != ".git":
        raise PrepError("git_common_root_invalid")
    try:
        git_relative = gitdir.relative_to(common)
    except ValueError as exc:
        raise PrepError("gitdir_outside_common_root") from exc
    for directory, label in ((common, "git_common_root"), (gitdir, "git_directory")):
        info = directory.lstat()
        if directory.is_symlink() or int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE or not stat.S_ISDIR(info.st_mode):
            raise PrepError(f"{label}_invalid")
    cursor = common
    for part in git_relative.parts:
        cursor = cursor / part
        info = cursor.lstat()
        if cursor.is_symlink() or int(getattr(info, "st_file_attributes", 0)) & REPARSE_ATTRIBUTE or not stat.S_ISDIR(info.st_mode):
            raise PrepError("git_ancestor_reparse_or_invalid")
    if gitdir != common:
        backlink_text = _bounded_git_text(gitdir / "gitdir", "git_worktree_backlink", common, 4096).strip()
        backlink = _reject_absolute_reparse_chain(Path(backlink_text), "git_worktree_backlink")
        expected_backlink = _reject_absolute_reparse_chain(REPO_ROOT / ".git", "worktree_git_pointer")
        if backlink != expected_backlink:
            raise PrepError("git_worktree_backlink_invalid")
    head_text = _bounded_git_text(gitdir / "HEAD", "git_head", common, 4096).strip()
    if head_text.startswith("ref: "):
        ref = head_text[5:]
        if not ref.startswith("refs/heads/") or ".." in Path(ref).parts:
            raise PrepError("git_head_ref_invalid")
        loose = common / Path(ref)
        loose_info = _bounded_git_lstat_optional(loose, "git_loose_ref", common)
        if loose_info is not None:
            if _stat_is_reparse_or_link(loose_info) or not stat.S_ISREG(loose_info.st_mode):
                raise PrepError("git_loose_ref_not_plain_file")
            sha = _bounded_git_text(loose, "git_loose_ref", common, 4096).strip()
        else:
            packed = _bounded_git_text(common / "packed-refs", "git_packed_refs", common)
            matches: list[str] = []
            for line in packed.splitlines():
                if not line or line.startswith("#") or line.startswith("^"):
                    continue
                fields = line.split(" ")
                if len(fields) == 2 and fields[1] == ref and all(fields):
                    matches.append(fields[0])
                elif line.endswith(" " + ref):
                    raise PrepError("git_packed_ref_line_invalid")
            if len(matches) != 1:
                raise PrepError("git_ref_not_unique")
            sha = matches[0]
    else:
        sha = head_text
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise PrepError("git_head_sha_invalid")
    return sha


def _validate_pre_mutation_bindings(
    plan: Mapping[str, Any], candidate: Mapping[str, Any], plan_digest: str
) -> None:
    repository_head = plan.get("repository_head")
    controller_sha = plan.get("controller_source_sha256")
    executor_sha = plan.get("executor_source_sha256")
    if not isinstance(repository_head, str) or len(repository_head) != 40 or any(
        char not in "0123456789abcdef" for char in repository_head
    ):
        raise PrepError("candidate_repository_head_invalid")
    for label, value in (("controller", controller_sha), ("executor", executor_sha)):
        if not isinstance(value, str) or len(value) != 64 or any(
            char not in "0123456789abcdef" for char in value
        ):
            raise PrepError(f"candidate_{label}_sha_invalid")
    if _read_repository_head() != repository_head:
        raise PrepError("repository_head_drift")
    if _source_sha(REPO_ROOT / CONTROLLER_REL, "controller_source") != controller_sha:
        raise PrepError("controller_source_drift")
    if _source_sha(REPO_ROOT / EXECUTOR_REL, "executor_source") != executor_sha:
        raise PrepError("executor_source_drift")
    try:
        ignore_data = _safe_fixed_file(REPO_ROOT / GITIGNORE_REL, "gitignore", 64 * 1024)
        ignore_text = ignore_data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise PrepError("gitignore_utf8_invalid") from exc
    if ".qa_local/" not in {line.strip() for line in ignore_text.splitlines()}:
        raise PrepError("ignored_root_contract_missing")
    if _sha256(ignore_data) != plan.get("gitignore_sha256"):
        raise PrepError("gitignore_hash_drift")
    for key in ("repository_head", "controller_source_sha256", "executor_source_sha256", "target_alias", "build_alias", "fixture_alias"):
        if not _exact_equal(candidate.get(key), plan.get(key)):
            raise PrepError("candidate_plan_binding_drift")
    supplied = os.environ.get(GO_ENV)
    if supplied != GO_PREFIX + plan_digest:
        raise PrepError("literal_security_go_invalid")


def _is_reparse(path: Path) -> bool:
    info = path.lstat()
    return _stat_is_reparse_or_link(info)


def _validate_fixed_local_targets() -> None:
    root = REPO_ROOT.resolve(strict=True)
    if _is_reparse(REPO_ROOT):
        raise PrepError("repository_root_reparse")
    for relative in (Path(".qa_local"), Path(".qa_local/evidence")):
        path = REPO_ROOT / relative
        info = _lstat_optional(path)
        if info is None:
            raise PrepError("shared_ignored_parent_missing")
        if _stat_is_reparse_or_link(info) or not stat.S_ISDIR(info.st_mode):
            raise PrepError("fixed_ancestor_not_plain_directory")
        try:
            path.resolve(strict=True).relative_to(root)
        except ValueError as exc:
            raise PrepError("fixed_ancestor_outside_repository") from exc
    attempt_root = REPO_ROOT / ATTEMPT_ROOT_REL
    if _lstat_optional(attempt_root) is not None:
        raise PrepError("prep_attempt_root_already_consumed")
    if shutil.disk_usage(root).free < MIN_FREE_BYTES:
        raise PrepError("local_capacity_insufficient")


def _check_deadline(deadline: float) -> None:
    if time.monotonic() > deadline:
        raise PrepError("wall_clock_budget_exhausted")


def _mkdir_new_or_existing(path: Path) -> bool:
    created = False
    try:
        path.mkdir()
        created = True
    except FileExistsError:
        info = path.lstat()
        if _stat_is_reparse_or_link(info) or not stat.S_ISDIR(info.st_mode):
            raise PrepError("fixed_directory_collision")
    info = path.lstat()
    if _stat_is_reparse_or_link(info) or not stat.S_ISDIR(info.st_mode):
        raise PrepError("fixed_directory_collision")
    try:
        path.resolve(strict=True).relative_to(REPO_ROOT.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise PrepError("fixed_directory_outside_repository") from exc
    return created


def execute_prep(now: datetime | None = None) -> Mapping[str, Any]:
    deadline = time.monotonic() + BUDGET["wall_clock_minutes_max"] * 60
    candidate_data = _safe_fixed_file(REPO_ROOT / CANDIDATE_REL, "candidate", MAX_CANDIDATE_BYTES)
    candidate = _strict_json(candidate_data, "candidate", MAX_CANDIDATE_BYTES)
    if candidate_data != canonical_bytes(candidate):
        raise PrepError("candidate_not_canonical")
    plan_data = _safe_fixed_file(REPO_ROOT / PREP_PLAN_REL, "prep_plan", MAX_CANDIDATE_BYTES)
    plan = _strict_json(plan_data, "prep_plan", MAX_CANDIDATE_BYTES)
    if plan_data != canonical_bytes(plan):
        raise PrepError("prep_plan_not_canonical")
    current = now or datetime.now(UTC)
    plan_digest = _validate_prep_plan(plan, candidate_data, current)
    _check_deadline(deadline)
    # Bind the exact repository and executable sources before importing or
    # executing controller bytes from the worktree.
    candidate_digest = _sha256(canonical_bytes(candidate))
    _validate_pre_mutation_bindings(plan, candidate, plan_digest)
    digest, materialized = _validate_candidate(candidate, current)
    if digest != candidate_digest:
        raise PrepError("candidate_digest_drift")
    _validate_fixed_local_targets()
    _check_deadline(deadline)

    created_directories = 0
    attempt_root = REPO_ROOT / ATTEMPT_ROOT_REL
    if not _mkdir_new_or_existing(attempt_root):
        raise PrepError("prep_attempt_root_already_consumed")
    created_directories += 1
    _check_deadline(deadline)
    run_root = REPO_ROOT / RUN_ROOT_REL
    try:
        if not _mkdir_new_or_existing(run_root):
            raise PrepError("run_root_already_consumed")
    except FileExistsError as exc:
        raise PrepError("run_root_already_consumed") from exc
    created_directories += 1
    for relative in (RAW_REL, CHECKPOINTS_REL, PUBLIC_SAFE_REL):
        _check_deadline(deadline)
        if not _mkdir_new_or_existing(REPO_ROOT / relative):
            raise PrepError("fixed_directory_collision")
        created_directories += 1

    for path, data in materialized:
        _check_deadline(deadline)
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    for path, expected in materialized:
        _check_deadline(deadline)
        actual = path.read_bytes()
        if actual != expected or _sha256(actual) != _sha256(expected):
            raise PrepError("artifact_readback_mismatch")
    _check_deadline(deadline)

    return {
        "schema_version": RESULT_SCHEMA,
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "contour_id": CONTOUR_ID,
        "prep_attempt_id": PREP_ATTEMPT_ID,
        "status": "prepared",
        "directory_target_count": 7,
        "directory_created_count": created_directories,
        "file_created_count": 4,
        "subprocess_count": 1,
        "host_process_count": 1,
        "child_subprocess_count": 0,
        "secret_read_count": 0,
        "device_action_count": 0,
        "application_action_count": 0,
        "network_action_count": 0,
        "authentication_action_count": 0,
        "runtime_action_count": 0,
    }


def validate_only() -> Mapping[str, Any]:
    return {
        "schema_version": "epic-phone-001-c0p-prep-contract-v2",
        "epic_id": EPIC_ID,
        "run_id": RUN_ID,
        "prep_attempt_id": PREP_ATTEMPT_ID,
        "classification": CLASSIFICATION,
        "scope_qualifier": SCOPE_QUALIFIER,
        "fixed_candidate": CANDIDATE_REL.as_posix(),
        "fixed_prep_plan": PREP_PLAN_REL.as_posix(),
        "fixed_run_root": RUN_ROOT_REL.as_posix(),
        "literal_go_source": GO_ENV,
        "execution_requires_literal_security_go": True,
        "subprocess_max": 1,
        "host_process_max": 1,
        "child_subprocess_max": 0,
        "secret_read_max": 0,
        "device_action_max": 0,
        "application_action_max": 0,
        "network_action_max": 0,
        "authentication_action_max": 0,
        "runtime_action_max": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EPIC-PHONE-001 guarded C0P-PREP")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--execute", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = validate_only() if args.validate_only else execute_prep()
    except KeyboardInterrupt:
        print("operation_interrupted_fail_closed", file=sys.stderr)
        return 130
    except PrepError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except OSError:
        print("local_io_error_fail_closed", file=sys.stderr)
        return 3
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

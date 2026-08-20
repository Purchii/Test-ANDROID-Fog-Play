#!/usr/bin/env python3
"""Create-new, zero-secret/zero-device EPIC authority-set renewal."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import time
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping


EPIC_ID = "EPIC-PHONE-001"
RUN_ID = "epic-phone-001-20260816-r01"
CONTOUR_ID = "epic-phone-001-authority-renewal"
RENEWAL_ID = "authority-renewal-003"
AUTHORITY_SET_ID = "c0p-authority-005"
PREP_ATTEMPT_ID = "c0p-prep-005"
SECURITY_ALIAS = "epic-phone-001-security-c0p-005"
NO_MUTATOR_ALIAS = "epic-phone-001-owner-authority-renewal-no-mutator-003"
NO_MUTATOR_SCOPE = {
    "ancestors": "all_lexical_ancestors_of_every_listed_or_resolved_path",
    "git_metadata": [".git_marker", "resolved_local_gitdir", "optional_resolved_local_commondir",
                     "gitdir_HEAD", "optional_active_loose_ref_component_probe",
                     "exact_active_loose_ref_or_packed_refs"],
    "new_outputs": [
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-renewal-003-attempt.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/c0p-plan.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/fixture-authority-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/target-build-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/evidence-cleanup-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-005/authority-renewal-result.local.json",
    ],
    "public_inputs": ["docs/qa/phone/epic-phone-001-authority-renewal-003-candidate.json",
                      "docs/qa/phone/epic-phone-001-authority-renewal-003-plan.json"],
    "repository_inputs": ["six_exact_bound_sources", ".gitignore"],
}
CLASSIFICATION = "PROD_SAFE"
SCOPE = "ZERO_SECRET_ZERO_DEVICE_CREATE_NEW_VERSIONED_AUTHORITY_RENEWAL"
REPOSITORY_HEAD_PLACEHOLDER = "FINAL_HEAD_REQUIRED"

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_REL = Path("automation/phone/epic_phone_001_authority_renewal.py")
LOADER_REL = Path("automation/phone/epic_phone_001_authority_renewal_loader.py")
C0P_PREP_REL = Path("automation/phone/epic_phone_001_c0p_prep.py")
CONTROLLER_REL = Path("automation/phone/epic_phone_001_runtime_controller.py")
PROVISIONER_REL = Path("automation/phone/epic_phone_001_fixture_interactive_provision.py")
PROVISION_LOADER_REL = Path("automation/phone/epic_phone_001_owner_local_fixture_loader.py")
GITIGNORE_REL = Path(".gitignore")
SOURCE_PATHS = (EXECUTOR_REL, LOADER_REL, C0P_PREP_REL, CONTROLLER_REL, PROVISIONER_REL, PROVISION_LOADER_REL)

CANDIDATE_REL = Path("docs/qa/phone/epic-phone-001-authority-renewal-003-candidate.json")
PLAN_REL = Path("docs/qa/phone/epic-phone-001-authority-renewal-003-plan.json")
RUN_REL = Path(".qa_local/evidence/epic-phone-001") / RUN_ID
SET_PARENT_REL = RUN_REL / "authority-sets"
SET_ROOT_REL = SET_PARENT_REL / AUTHORITY_SET_ID
MARKER_REL = RUN_REL / f"{RENEWAL_ID}-attempt.local.json"
C0P_PLAN_REL = SET_ROOT_REL / "c0p-plan.local.json"
FIXTURE_REL = SET_ROOT_REL / "fixture-authority-passport.local.json"
TARGET_REL = SET_ROOT_REL / "target-build-passport.local.json"
CLEANUP_REL = SET_ROOT_REL / "evidence-cleanup-passport.local.json"
RESULT_REL = SET_ROOT_REL / "authority-renewal-result.local.json"
ARTIFACT_PATHS = (C0P_PLAN_REL, FIXTURE_REL, TARGET_REL, CLEANUP_REL)

CANDIDATE_SCHEMA = "epic-phone-001-authority-renewal-candidate-v1"
PLAN_SCHEMA = "epic-phone-001-authority-renewal-plan-v1"
ATTEMPT_SCHEMA = "epic-phone-001-authority-renewal-attempt-v1"
RESULT_SCHEMA = "epic-phone-001-authority-renewal-result-v1"
C0P_SCHEMA = "epic-phone-001-c0p-plan-v2"
FIXTURE_SCHEMA = "epic-phone-001-fixture-authority-passport-v2"
TARGET_SCHEMA = "epic-phone-001-target-build-passport-v2"
CLEANUP_SCHEMA = "epic-phone-001-evidence-cleanup-passport-v2"
PLAN_ENV = "EPIC_PHONE_001_AUTHORITY_RENEWAL_PLAN"
GO_ENV = "EPIC_PHONE_001_AUTHORITY_RENEWAL_GO"
GO_PREFIX = f"GO_EPIC_PHONE_001_AUTHORITY_RENEWAL__{RUN_ID}__"
DEADLINE_NS_GLOBAL = "__authority_renewal_deadline_monotonic_ns__"
BOOTSTRAP_WALL_GLOBAL = "__authority_renewal_bootstrap_wall_utc__"
LOADER_GO_READ_GLOBAL = "__authority_renewal_loader_go_env_read_count__"
LOADER_SOURCE_READ_GLOBAL = "__authority_renewal_loader_source_read_count__"
REPARSE_ATTRIBUTE = 0x400
MAX_SINGLE = 8192
MAX_TOTAL = 49152
MAX_PLAN = 49152
MAX_DEPTH = 12
HEX40 = set("0123456789abcdef")

BUDGET = {
    "application_action_max": 0, "authentication_action_max": 0,
    "candidate_read_max": 1, "child_subprocess_max": 0, "concurrency_max": 1,
    "created_file_readback_max": 6, "device_action_max": 0,
    "directory_create_max": 1, "execution_max": 1, "file_create_max": 6,
    "host_process_max": 1, "metadata_path_target_max": 32, "network_action_max": 0,
    "git_metadata_content_read_max": 4, "gitignore_content_read_max": 1, "go_env_read_max": 2,
    "old_authority_content_read_max": 0, "overwrite_append_delete_rename_max": 0,
    "plan_read_max": 1, "retry_max": 0, "runtime_action_max": 0,
    "secret_read_max": 0, "serial_read_max": 0, "single_file_bytes_max": 8192,
    "subprocess_max": 1, "total_created_bytes_max": 49152,
    "executor_tracked_source_read_max": 6, "loader_executor_source_read_max": 1,
    "full_envelope_source_read_max": 7, "ui_action_max": 0, "wall_clock_seconds_max": 300,
}


class RenewalError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exact(left: Any, right: Any) -> bool:
    if type(left) is not type(right): return False
    if type(right) is dict: return set(left) == set(right) and all(_exact(left[key], right[key]) for key in right)
    if type(right) is list: return len(left) == len(right) and all(_exact(a, b) for a, b in zip(left, right))
    return left == right


def _shape(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH or value is None or isinstance(value, float): raise RenewalError("json_shape_invalid")
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value or any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise RenewalError("json_string_invalid")
    elif type(value) is list:
        for item in value: _shape(item, depth + 1)
    elif type(value) is dict:
        for key, item in value.items(): _shape(key, depth + 1); _shape(item, depth + 1)
    elif type(value) not in (bool, int): raise RenewalError("json_type_invalid")


def _strict_json(data: bytes, label: str) -> Mapping[str, Any]:
    if not data or len(data) > MAX_PLAN or data.startswith(b"\xef\xbb\xbf"): raise RenewalError(f"{label}_size_or_encoding_invalid")
    def hook(items):
        result, normalized = {}, set()
        for key, value in items:
            norm = unicodedata.normalize("NFC", key)
            if key in result or norm in normalized: raise RenewalError(f"{label}_duplicate_key")
            result[key] = value; normalized.add(norm)
        return result
    try: value = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=hook)
    except (UnicodeError, ValueError, RecursionError) as exc: raise RenewalError(f"{label}_invalid") from exc
    if type(value) is not dict: raise RenewalError(f"{label}_not_object")
    _shape(value)
    if canonical_bytes(value) != data: raise RenewalError(f"{label}_not_canonical")
    return value


def _utc(value: Any, label: str) -> datetime:
    if type(value) is not str or not value.endswith("Z"): raise RenewalError(f"{label}_invalid")
    try: parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc: raise RenewalError(f"{label}_invalid") from exc
    if parsed.utcoffset() != timedelta(0): raise RenewalError(f"{label}_invalid")
    return parsed


def _validate_head(value: str) -> None:
    if type(value) is not str or len(value) != 40 or any(ch not in HEX40 for ch in value):
        raise RenewalError("final_repository_head_required")


def _source_binding(path: Path, data: bytes) -> dict[str, Any]:
    return {"bytes": len(data), "path": path.as_posix(), "sha256": _sha(data)}


def build_authority_payloads(*, repository_head: str, controller_sha256: str,
                             issued_at_utc: str, expires_at_utc: str,
                             retention_expires_at_utc: str) -> list[dict[str, Any]]:
    _validate_head(repository_head)
    common = {"authority_set_id": AUTHORITY_SET_ID, "epic_id": EPIC_ID, "issued_at_utc": issued_at_utc,
              "renewal_id": RENEWAL_ID, "run_id": RUN_ID, "prep_attempt_id": PREP_ATTEMPT_ID}
    c0p = {**common, "schema_version": C0P_SCHEMA, "contour_id": "epic-phone-001-c0p-local-presence",
           "classification": "PROD_CONDITIONAL", "execution_status": "planned_separate_literal_go_required_not_run",
           "target_alias": "phone-current-001", "build_alias": "task058-selected-phone-full-001",
           "fixture_alias": "epic-phone-001-fixture-001",
           "passport_aliases": {"fixture_authority": "epic-phone-001-fixture-authority-005",
                                "target_build": "epic-phone-001-target-build-005",
                                "evidence_cleanup": "epic-phone-001-evidence-cleanup-005"},
           "security_alias": SECURITY_ALIAS, "repository_head": repository_head,
           "controller_source_sha256": controller_sha256, "fixed_plan_path": C0P_PLAN_REL.as_posix(),
           "fixed_token_path": (RUN_REL / "security-go-c0p-005.local.json").as_posix(),
           "fixed_secret_source": ".qa_local/secrets/qa_user.env",
           "fixed_result_path": (RUN_REL / "public-safe/c0p-005-result.local.json").as_posix(),
           "fixed_attempt_marker_path": (RUN_REL / "c0p-005-attempt.local.json").as_posix(),
           "attempt_marker_schema": "epic-phone-001-c0p-attempt-v1",
           "public_result_allowlist": ["required_field_count", "required_fields_present", "unexpected_fields_absent",
                                       "phone_format_policy_pass", "otp_format_policy_pass"],
           "value_handling": {"read_only_for_nonempty_presence_in_authorized_adapter": True, "print": False,
                              "record": False, "hash": False, "length": False, "value_comparison": False},
           "security_token_format": f"GO_EPIC_PHONE_001_C0P_LOCAL_PRESENCE__{RUN_ID}__<64_lowercase_hex>",
           "security_token_must_bind": ["epic_id", "run_id", "contour_id", "target_alias", "build_alias",
                                        "fixture_alias", "passport_aliases", "passport_sha256", "passport_expires_at_utc",
                                        "security_alias", "c0p_plan_sha256", "repository_head", "controller_source_sha256",
                                        "issued_at_utc", "expires_at_utc", "result_path", "attempt_marker_path",
                                        "attempt_marker_schema", "budget"],
           "c1_token_cannot_authorize": True, "controller_execution_interface_present": True,
           "budget": {"secret_source_read_max": 1, "retry_max": 0, "wall_clock_minutes_max": 30,
                      "secret_source_bytes_max": 8192, "device_action_max": 0, "subprocess_max": 0,
                      "network_action_max": 0, "application_launch_max": 0, "ui_action_max": 0,
                      "authentication_action_max": 0, "mutation_max": 0}}
    c0p["expires_at_utc"] = expires_at_utc
    fixture = {**common, "schema_version": FIXTURE_SCHEMA, "fixture_alias": "epic-phone-001-fixture-001",
               "synthetic_test_only": True, "not_real_user": True, "values_local_only": True, "revoked": False,
               "authority_validity": "current_epic_run_until_completion_or_revocation",
               "allowed_scope": ["synthetic_session_create", "read_only_navigation", "safe_logout"],
               "forbidden_scope": ["payment", "subscription", "entitlement", "profile", "account", "paid_session", "external_or_qr_traversal"],
               "expires_at_utc": expires_at_utc}
    target = {**common, "schema_version": TARGET_SCHEMA, "target_alias": "phone-current-001",
              "build_alias": "task058-selected-phone-full-001", "target_authorized": True,
              "build_authorized": True, "launch_allowed": False, "mutation_allowed": False,
              "passport_purpose": "authorization_only", "task058a_row03_evidence_status": "unknown",
              "current_freshness_evidence": False, "runtime_evidence": False, "expires_at_utc": expires_at_utc}
    cleanup = {**common, "schema_version": CLEANUP_SCHEMA, "run_root": RUN_REL.as_posix(),
               "soft_bytes_max": 50331648, "hard_bytes_max": 67108864,
               "passport_purpose": "policy_readiness_only",
               "execution_evidence": False, "redaction_default": True, "direct_capture_no_echo": True,
               "cleanup_sequence": ["target_only_force_stop", "home", "post_kill_checkpoint", "capture_shutdown"],
               "forbidden_action_count": 0,
               "retention_expires_at_utc": retention_expires_at_utc}
    return [c0p, fixture, target, cleanup]


def build_candidate(*, repository_head: str, source_bindings: list[dict[str, Any]], controller_sha256: str,
                    issued_at_utc: str, expires_at_utc: str, authority_expires_at_utc: str,
                    retention_expires_at_utc: str, no_mutator_expires_at_utc: str,
                    no_mutator_status: str) -> dict[str, Any]:
    payloads = build_authority_payloads(repository_head=repository_head, controller_sha256=controller_sha256,
                                        issued_at_utc=issued_at_utc, expires_at_utc=authority_expires_at_utc,
                                        retention_expires_at_utc=retention_expires_at_utc)
    artifacts = []
    for path, value in zip(ARTIFACT_PATHS, payloads):
        data = canonical_bytes(value)
        if len(data) > MAX_SINGLE: raise RenewalError("artifact_size_invalid")
        artifacts.append({"bytes": len(data), "canonical_json": value, "path": path.as_posix(), "sha256": _sha(data)})
    return {"schema_version": CANDIDATE_SCHEMA, "epic_id": EPIC_ID, "run_id": RUN_ID,
            "contour_id": CONTOUR_ID, "renewal_id": RENEWAL_ID, "authority_set_id": AUTHORITY_SET_ID,
            "prep_attempt_id": PREP_ATTEMPT_ID, "security_alias": SECURITY_ALIAS,
            "classification": CLASSIFICATION, "scope_qualifier": SCOPE,
            "execution_status": "planned_literal_security_go_required_not_run",
            "repository_head": repository_head, "source_bindings": source_bindings,
            "owner_no_mutator_authority": {"alias": NO_MUTATOR_ALIAS,
                                            "expires_at_utc": no_mutator_expires_at_utc,
                                            "scope": NO_MUTATOR_SCOPE, "status": no_mutator_status},
            "issued_at_utc": issued_at_utc, "expires_at_utc": expires_at_utc,
            "marker_path": MARKER_REL.as_posix(), "set_root": SET_ROOT_REL.as_posix(),
            "artifacts": artifacts, "budget": dict(BUDGET),
            "failure_policy": "marker_first_partial_preserved_no_retry_no_cleanup_no_reuse",
            "literal_go_format": GO_PREFIX + "<64_lowercase_plan_sha256>"}


def build_plan(candidate_data: bytes, *, repository_head: str, source_bindings: list[dict[str, Any]],
               gitignore_binding: dict[str, Any], issued_at_utc: str, expires_at_utc: str,
               no_mutator_expires_at_utc: str, no_mutator_status: str) -> dict[str, Any]:
    _validate_head(repository_head)
    return {"schema_version": PLAN_SCHEMA, "epic_id": EPIC_ID, "run_id": RUN_ID,
            "contour_id": CONTOUR_ID, "renewal_id": RENEWAL_ID, "authority_set_id": AUTHORITY_SET_ID,
            "prep_attempt_id": PREP_ATTEMPT_ID, "security_alias": SECURITY_ALIAS,
            "classification": CLASSIFICATION, "scope_qualifier": SCOPE,
            "repository_head": repository_head, "candidate_path": CANDIDATE_REL.as_posix(),
            "owner_no_mutator_authority": {"alias": NO_MUTATOR_ALIAS,
                                            "expires_at_utc": no_mutator_expires_at_utc,
                                            "scope": NO_MUTATOR_SCOPE, "status": no_mutator_status},
            "candidate_bytes": len(candidate_data), "candidate_sha256": _sha(candidate_data),
            "plan_path": PLAN_REL.as_posix(), "source_bindings": source_bindings,
            "gitignore_binding": gitignore_binding, "marker_path": MARKER_REL.as_posix(),
            "set_root": SET_ROOT_REL.as_posix(), "artifact_paths": [p.as_posix() for p in ARTIFACT_PATHS],
            "result_path": RESULT_REL.as_posix(), "issued_at_utc": issued_at_utc,
            "expires_at_utc": expires_at_utc, "budget": dict(BUDGET),
            "literal_go_format": GO_PREFIX + "<64_lowercase_plan_sha256>",
            "failure_policy": "marker_first_partial_preserved_no_retry_no_cleanup_no_reuse"}


def _safe_chain(path: Path, *, missing_leaf: bool = False) -> None:
    root = REPO_ROOT.absolute(); absolute = path.absolute()
    _fixed_local(root); _fixed_local(absolute)
    root_info = root.lstat()
    if stat.S_ISLNK(root_info.st_mode) or getattr(root_info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE:
        raise RenewalError("repository_root_reparse")
    try: relative = absolute.relative_to(root)
    except ValueError as exc: raise RenewalError("path_outside_repository") from exc
    cursor = root
    for index, part in enumerate(relative.parts):
        cursor /= part; leaf = index == len(relative.parts) - 1
        try: info = cursor.lstat()
        except FileNotFoundError:
            if leaf and missing_leaf: return
            raise RenewalError("path_missing")
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE:
            raise RenewalError("path_reparse")


def _fixed_local(path: Path) -> None:
    text = str(path)
    if os.name != "nt" or not path.is_absolute() or not path.drive or text.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")):
        raise RenewalError("windows_fixed_local_drive_required")
    import ctypes
    if ctypes.windll.kernel32.GetDriveTypeW(path.anchor) != 3: raise RenewalError("windows_fixed_local_drive_required")


def _safe_absolute_chain(path: Path) -> None:
    absolute = path.absolute(); _fixed_local(absolute); cursor = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        cursor /= part
        info = cursor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE:
            raise RenewalError("git_metadata_reparse")


def _track_git_path(path: Path, budget: dict[str, Any]) -> None:
    budget["targets"].add(str(path.absolute()))
    if len(budget["targets"]) > BUDGET["metadata_path_target_max"]: raise RenewalError("git_metadata_path_budget_exhausted")


def _probe_optional_git_path(path: Path, budget: dict[str, Any]) -> bool:
    absolute = path.absolute(); _fixed_local(absolute); cursor = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        cursor /= part; _track_git_path(cursor, budget)
        try: info = cursor.lstat()
        except FileNotFoundError: return False
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE:
            raise RenewalError("git_metadata_reparse")
    return True


def _read_metadata(path: Path, budget: dict[str, Any], maximum: int = 4096) -> bytes:
    _track_git_path(path, budget)
    budget["content_reads"] += 1
    if budget["content_reads"] > BUDGET["git_metadata_content_read_max"]: raise RenewalError("git_metadata_content_budget_exhausted")
    _safe_absolute_chain(path); before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum: raise RenewalError("git_metadata_invalid")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); data = os.read(fd, maximum + 1); after = os.fstat(fd)
    finally: os.close(fd)
    ident = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != ident or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != ident or len(data) != before.st_size):
        raise RenewalError("git_metadata_identity_invalid")
    return data


def _actual_repository_head() -> tuple[str, int, int]:
    budget: dict[str, Any] = {"content_reads": 0, "targets": set()}
    marker = REPO_ROOT / ".git"; _track_git_path(marker, budget); _safe_absolute_chain(marker); info = marker.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise RenewalError("git_marker_reparse")
    if stat.S_ISDIR(info.st_mode):
        gitdir = marker
    elif stat.S_ISREG(info.st_mode):
        raw = _read_metadata(marker, budget).decode("utf-8", errors="strict").strip()
        if not raw.startswith("gitdir: "): raise RenewalError("gitdir_contract_invalid")
        value = raw[8:]
        if value.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")): raise RenewalError("gitdir_contract_invalid")
        gitdir = Path(value) if Path(value).is_absolute() else REPO_ROOT / value
        gitdir = Path(os.path.abspath(gitdir)); _track_git_path(gitdir, budget); _safe_absolute_chain(gitdir)
    else: raise RenewalError("git_marker_type_invalid")
    common = gitdir
    _track_git_path(gitdir / "commondir", budget)
    try: commondir_info = (gitdir / "commondir").lstat()
    except FileNotFoundError: commondir_info = None
    if commondir_info is not None:
        raw_common = _read_metadata(gitdir / "commondir", budget).decode("utf-8", errors="strict").strip()
        if not raw_common or raw_common.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")): raise RenewalError("commondir_contract_invalid")
        common = Path(raw_common) if Path(raw_common).is_absolute() else gitdir / raw_common
        common = Path(os.path.abspath(common)); _track_git_path(common, budget); _safe_absolute_chain(common)
    head = _read_metadata(gitdir / "HEAD", budget).decode("ascii", errors="strict").strip()
    if len(head) == 40 and all(ch in HEX40 for ch in head): return head, budget["content_reads"], len(budget["targets"])
    if not head.startswith("ref: "): raise RenewalError("git_head_invalid")
    ref = head[5:]
    if not ref.startswith("refs/") or "\\" in ref or ":" in ref or any(part in ("", ".", "..") for part in ref.split("/")):
        raise RenewalError("git_ref_invalid")
    loose = common.joinpath(*ref.split("/"))
    if _probe_optional_git_path(loose, budget):
        value = _read_metadata(loose, budget).decode("ascii", errors="strict").strip()
        if len(value) == 40 and all(ch in HEX40 for ch in value): return value, budget["content_reads"], len(budget["targets"])
        raise RenewalError("git_loose_ref_invalid")
    packed = _read_metadata(common / "packed-refs", budget, 32768).decode("ascii", errors="strict")
    matches = []
    for line in packed.splitlines():
        if not line or line.startswith(("#", "^")): continue
        parts = line.split(" ")
        if len(parts) != 2: raise RenewalError("packed_refs_invalid")
        if parts[1] == ref: matches.append(parts[0])
    if len(matches) != 1 or len(matches[0]) != 40 or any(ch not in HEX40 for ch in matches[0]): raise RenewalError("packed_ref_missing_or_ambiguous")
    return matches[0], budget["content_reads"], len(budget["targets"])


def _read_fixed(path: Path, binding: Mapping[str, Any], maximum: int) -> bytes:
    if (type(binding) is not dict or set(binding) != {"bytes", "path", "sha256"} or
            binding["path"] != path.relative_to(REPO_ROOT).as_posix() or type(binding["bytes"]) is not int or
            not 0 < binding["bytes"] <= maximum or type(binding["sha256"]) is not str or len(binding["sha256"]) != 64):
        raise RenewalError("binding_invalid")
    _safe_chain(path); before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size != binding["bytes"]: raise RenewalError("binding_identity_invalid")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); data = os.read(fd, binding["bytes"] + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or
            len(data) != binding["bytes"] or _sha(data) != binding["sha256"]): raise RenewalError("binding_identity_invalid")
    return data


def _read_public_once(path: Path, maximum: int) -> bytes:
    _safe_chain(path); before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum: raise RenewalError("public_input_invalid")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); data = os.read(fd, maximum + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or len(data) != before.st_size):
        raise RenewalError("public_input_identity_invalid")
    return data


def _check_deadline(deadline_ns: int) -> None:
    if time.monotonic_ns() >= deadline_ns: raise RenewalError("wall_clock_budget_exhausted")


def _write_new(path: Path, data: bytes, deadline_ns: int) -> None:
    _check_deadline(deadline_ns)
    if not data or len(data) > MAX_SINGLE: raise RenewalError("created_file_size_invalid")
    _safe_chain(path.parent); _safe_chain(path, missing_leaf=True)
    _check_deadline(deadline_ns)
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags, 0o600)
    try:
        view = memoryview(data); offset = 0
        while offset < len(data):
            _check_deadline(deadline_ns)
            written = os.write(fd, view[offset:])
            if written <= 0: raise RenewalError("write_failed")
            offset += written
        os.fsync(fd); _check_deadline(deadline_ns); os.lseek(fd, 0, os.SEEK_SET)
        if os.read(fd, len(data) + 1) != data: raise RenewalError("readback_failed")
        _check_deadline(deadline_ns)
    finally: os.close(fd)


def _validate_plan(plan: Mapping[str, Any], candidate: Mapping[str, Any], raw_plan: bytes, now: datetime) -> None:
    expected = build_plan(canonical_bytes(candidate), repository_head=plan["repository_head"],
                          source_bindings=plan["source_bindings"], gitignore_binding=plan["gitignore_binding"],
                          issued_at_utc=plan["issued_at_utc"], expires_at_utc=plan["expires_at_utc"],
                          no_mutator_expires_at_utc=plan["owner_no_mutator_authority"]["expires_at_utc"],
                          no_mutator_status=plan["owner_no_mutator_authority"]["status"])
    if not _exact(plan, expected): raise RenewalError("plan_contract_drift")
    expected_candidate = build_candidate(repository_head=plan["repository_head"], source_bindings=plan["source_bindings"],
                                         controller_sha256=next(x["sha256"] for x in plan["source_bindings"] if x["path"] == CONTROLLER_REL.as_posix()),
                                         issued_at_utc=candidate["issued_at_utc"], expires_at_utc=candidate["expires_at_utc"],
                                         authority_expires_at_utc=candidate["artifacts"][1]["canonical_json"]["expires_at_utc"],
                                         retention_expires_at_utc=candidate["artifacts"][3]["canonical_json"]["retention_expires_at_utc"],
                                         no_mutator_expires_at_utc=candidate["owner_no_mutator_authority"]["expires_at_utc"],
                                         no_mutator_status=candidate["owner_no_mutator_authority"]["status"])
    if not _exact(candidate, expected_candidate): raise RenewalError("candidate_contract_drift")
    if len(plan["source_bindings"]) != 6 or [x.get("path") for x in plan["source_bindings"]] != [p.as_posix() for p in SOURCE_PATHS]:
        raise RenewalError("source_binding_set_invalid")
    issued, expires = _utc(plan["issued_at_utc"], "issued"), _utc(plan["expires_at_utc"], "expires")
    if expires <= issued or expires - issued > timedelta(minutes=10) or not issued <= now < expires:
        raise RenewalError("plan_expired")
    candidate_issued = _utc(candidate["issued_at_utc"], "candidate_issued")
    candidate_expires = _utc(candidate["expires_at_utc"], "candidate_expires")
    if (candidate_expires <= candidate_issued or candidate_expires - candidate_issued > timedelta(minutes=10) or
            not candidate_issued <= now < candidate_expires):
        raise RenewalError("candidate_time_contract_invalid")
    if (plan["owner_no_mutator_authority"] != candidate["owner_no_mutator_authority"] or
            plan["owner_no_mutator_authority"] != {"alias": NO_MUTATOR_ALIAS,
                                                    "expires_at_utc": plan["owner_no_mutator_authority"]["expires_at_utc"],
                                                    "scope": NO_MUTATOR_SCOPE, "status": "accepted_by_owner"}):
        raise RenewalError("owner_no_mutator_authority_required")
    if os.environ.get(GO_ENV) != GO_PREFIX + _sha(raw_plan): raise RenewalError("literal_go_invalid")


def execute(now: datetime | None = None) -> Mapping[str, Any]:
    deadline_ns = globals().get(DEADLINE_NS_GLOBAL); bootstrap_wall = globals().get(BOOTSTRAP_WALL_GLOBAL)
    if (type(deadline_ns) is not int or type(bootstrap_wall) is not datetime or bootstrap_wall.tzinfo is None or
            globals().get(LOADER_GO_READ_GLOBAL) != 1 or globals().get(LOADER_SOURCE_READ_GLOBAL) != 1):
        raise RenewalError("loader_process_envelope_required")
    mono_now = time.monotonic_ns(); current = now or datetime.now(UTC)
    if not mono_now < deadline_ns <= mono_now + 300_000_000_000: raise RenewalError("process_deadline_invalid")
    inherited_plan = globals().get("__authority_renewal_plan_bytes__")
    if inherited_plan is None:
        plan_data = _read_public_once(REPO_ROOT / PLAN_REL, MAX_PLAN)
    elif type(inherited_plan) is bytes and 0 < len(inherited_plan) <= MAX_PLAN:
        plan_data = inherited_plan
    else:
        raise RenewalError("loader_plan_same_buffer_invalid")
    plan = _strict_json(plan_data, "plan")
    candidate_binding = {"path": CANDIDATE_REL.as_posix(), "bytes": plan.get("candidate_bytes"), "sha256": plan.get("candidate_sha256")}
    candidate_data = _read_fixed(REPO_ROOT / CANDIDATE_REL, candidate_binding, MAX_PLAN)
    candidate = _strict_json(candidate_data, "candidate")
    _validate_plan(plan, candidate, plan_data, current)
    remaining_seconds = (deadline_ns - mono_now + 999_999_999) // 1_000_000_000
    required_until = max(_utc(plan["expires_at_utc"], "expires"), current + timedelta(seconds=remaining_seconds + 1),
                         bootstrap_wall + timedelta(seconds=301))
    if _utc(plan["expires_at_utc"], "expires") < required_until:
        raise RenewalError("plan_execution_coverage_invalid")
    if _utc(candidate["expires_at_utc"], "candidate_expires") < required_until:
        raise RenewalError("candidate_execution_coverage_invalid")
    if _utc(plan["owner_no_mutator_authority"]["expires_at_utc"], "no_mutator_expiry") < required_until:
        raise RenewalError("owner_no_mutator_coverage_invalid")
    for index, item in enumerate(candidate["artifacts"]):
        payload = item["canonical_json"]
        issued = _utc(payload["issued_at_utc"], "artifact_issued")
        expiry_key = "retention_expires_at_utc" if index == 3 else "expires_at_utc"
        expiry = _utc(payload[expiry_key], "artifact_expiry")
        maximum = timedelta(hours=24) if index == 3 else timedelta(minutes=10)
        if not issued <= current < expiry or expiry <= issued or expiry - issued > maximum or expiry < required_until:
            raise RenewalError("artifact_time_contract_invalid")
    _check_deadline(deadline_ns)
    for path, binding in zip(SOURCE_PATHS, plan["source_bindings"]): _read_fixed(REPO_ROOT / path, binding, 1024 * 1024)
    gitignore = _read_fixed(REPO_ROOT / GITIGNORE_REL, plan["gitignore_binding"], 1024 * 1024)
    if b".qa_local/" not in gitignore.splitlines(): raise RenewalError("gitignore_contract_invalid")
    _safe_chain(REPO_ROOT / RUN_REL)
    _safe_chain(REPO_ROOT / SET_PARENT_REL)
    if not stat.S_ISDIR((REPO_ROOT / SET_PARENT_REL).lstat().st_mode):
        raise RenewalError("authority_set_parent_invalid")
    _safe_chain(REPO_ROOT / SET_ROOT_REL, missing_leaf=True)
    if (REPO_ROOT / MARKER_REL).exists() or (REPO_ROOT / SET_ROOT_REL).exists():
        raise RenewalError("renewal_already_consumed")
    marker = canonical_bytes({"schema_version": ATTEMPT_SCHEMA, "epic_id": EPIC_ID, "run_id": RUN_ID,
                              "contour_id": CONTOUR_ID, "renewal_id": RENEWAL_ID,
                              "authority_set_id": AUTHORITY_SET_ID, "plan_sha256": _sha(plan_data),
                              "attempt_state": "started_partial_preserved"})
    actual_head, git_content_reads, git_path_targets = _actual_repository_head()
    if actual_head != plan["repository_head"]: raise RenewalError("repository_head_binding_invalid")
    _write_new(REPO_ROOT / MARKER_REL, marker, deadline_ns)
    _check_deadline(deadline_ns); os.mkdir(REPO_ROOT / SET_ROOT_REL)
    created, total = [], len(marker)
    for item in candidate["artifacts"]:
        data = canonical_bytes(item["canonical_json"]); total += len(data)
        if total > MAX_TOTAL: raise RenewalError("total_created_bytes_invalid")
        path = Path(item["path"])
        if path not in ARTIFACT_PATHS or len(data) != item["bytes"] or _sha(data) != item["sha256"]: raise RenewalError("artifact_binding_invalid")
        _write_new(REPO_ROOT / path, data, deadline_ns); created.append({"path_alias": path.name, "bytes_category": "within_8192", "sha256": item["sha256"]})
    result = {"schema_version": RESULT_SCHEMA, "status": "authority_set_materialized", "epic_id": EPIC_ID,
              "run_id": RUN_ID, "contour_id": CONTOUR_ID, "renewal_id": RENEWAL_ID,
              "authority_set_id": AUTHORITY_SET_ID, "prep_attempt_id": PREP_ATTEMPT_ID,
              "created_artifact_count": 4, "directory_created_count": 1, "file_created_count": 6,
              "readback_count": 6, "all_secret_serial_device_app_network_runtime_auth_ui_counters": 0,
              "gitignore_content_read_count": 1, "git_metadata_content_read_count": git_content_reads,
              "git_metadata_path_target_count": git_path_targets, "go_env_read_count": 2,
              "full_envelope_source_read_count": 7, "old_authority_content_read_count": 0,
              "artifacts": created}
    result_data = canonical_bytes(result); total += len(result_data)
    if total > MAX_TOTAL: raise RenewalError("total_created_bytes_invalid")
    _write_new(REPO_ROOT / RESULT_REL, result_data, deadline_ns)
    return result


def main() -> int:
    try: result = execute()
    except BaseException: return 2
    print(json.dumps({"schema_version": RESULT_SCHEMA, "status": result["status"], "created_artifact_count": 4,
                      "directory_created_count": 1, "file_created_count": 6,
                      "all_forbidden_counters": 0}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__": sys.exit(main())

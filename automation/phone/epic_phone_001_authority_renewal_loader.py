#!/usr/bin/env python3
"""No-pyc fixed loader for the authority-renewal executor."""

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


RUN_ID = "epic-phone-001-20260816-r01"
CONTOUR_ID = "epic-phone-001-authority-renewal"
RENEWAL_ID = "authority-renewal-001"
AUTHORITY_SET_ID = "c0p-authority-003"
PREP_ATTEMPT_ID = "c0p-prep-003"
SECURITY_ALIAS = "epic-phone-001-security-c0p-003"
PLAN_SCHEMA = "epic-phone-001-authority-renewal-plan-v1"
PLAN_REL = Path("docs/qa/phone/epic-phone-001-authority-renewal-plan.json")
EXECUTOR_REL = Path("automation/phone/epic_phone_001_authority_renewal.py")
GO_ENV = "EPIC_PHONE_001_AUTHORITY_RENEWAL_GO"
GO_PREFIX = f"GO_EPIC_PHONE_001_AUTHORITY_RENEWAL__{RUN_ID}__"
REPARSE_ATTRIBUTE = 0x400
NO_MUTATOR_SCOPE = {
    "ancestors": "all_lexical_ancestors_of_every_listed_or_resolved_path",
    "git_metadata": [".git_marker", "resolved_local_gitdir", "optional_resolved_local_commondir",
                     "gitdir_HEAD", "exact_active_loose_ref_or_packed_refs"],
    "new_outputs": [
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-renewal-001-attempt.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/c0p-plan.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/fixture-authority-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/target-build-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/evidence-cleanup-passport.local.json",
        ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/authority-renewal-result.local.json",
    ],
    "public_inputs": ["docs/qa/phone/epic-phone-001-authority-renewal-candidate.json",
                      "docs/qa/phone/epic-phone-001-authority-renewal-plan.json"],
    "repository_inputs": ["six_exact_bound_sources", ".gitignore"],
}
MAX_PLAN = 49152
MAX_SOURCE = 1024 * 1024
HEX40 = set("0123456789abcdef")
SOURCE_PATHS = [
    "automation/phone/epic_phone_001_authority_renewal.py",
    "automation/phone/epic_phone_001_authority_renewal_loader.py",
    "automation/phone/epic_phone_001_c0p_prep.py",
    "automation/phone/epic_phone_001_runtime_controller.py",
    "automation/phone/epic_phone_001_fixture_interactive_provision.py",
    "automation/phone/epic_phone_001_owner_local_fixture_loader.py",
]
ARTIFACT_PATHS = NO_MUTATOR_SCOPE["new_outputs"][3:7]
BUDGET = {
    "application_action_max": 0, "authentication_action_max": 0, "candidate_read_max": 1,
    "child_subprocess_max": 0, "concurrency_max": 1, "created_file_readback_max": 6,
    "device_action_max": 0, "directory_create_max": 2, "execution_max": 1, "file_create_max": 6,
    "host_process_max": 1, "metadata_path_target_max": 32, "network_action_max": 0,
    "git_metadata_content_read_max": 4, "gitignore_content_read_max": 1, "go_env_read_max": 2,
    "old_authority_content_read_max": 0, "overwrite_append_delete_rename_max": 0,
    "plan_read_max": 1, "retry_max": 0, "runtime_action_max": 0, "secret_read_max": 0,
    "serial_read_max": 0, "single_file_bytes_max": 8192, "subprocess_max": 1,
    "total_created_bytes_max": 49152, "executor_tracked_source_read_max": 6,
    "loader_executor_source_read_max": 1, "full_envelope_source_read_max": 7,
    "ui_action_max": 0, "wall_clock_seconds_max": 300,
}
ROOT_KEYS = {
    "artifact_paths", "authority_set_id", "budget", "candidate_bytes", "candidate_path", "candidate_sha256",
    "classification", "contour_id", "epic_id", "expires_at_utc", "failure_policy", "gitignore_binding",
    "issued_at_utc", "literal_go_format", "marker_path", "plan_path", "prep_attempt_id", "renewal_id",
    "repository_head", "result_path", "run_id", "schema_version", "scope_qualifier", "security_alias",
    "set_root", "source_bindings", "owner_no_mutator_authority",
}


def _safe_chain(root: Path, path: Path):
    root = root.absolute(); absolute = path.absolute()
    for value in (root, absolute):
        text = str(value)
        if os.name != "nt" or not value.is_absolute() or not value.drive or text.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")):
            raise ValueError
        import ctypes
        if ctypes.windll.kernel32.GetDriveTypeW(value.anchor) != 3: raise ValueError
    try: relative = absolute.relative_to(root)
    except ValueError as exc: raise ValueError from exc
    cursor = root
    root_info = cursor.lstat()
    if stat.S_ISLNK(root_info.st_mode) or getattr(root_info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError
    for part in relative.parts:
        cursor /= part; info = cursor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE_ATTRIBUTE: raise ValueError


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _exact(left, right):
    if type(left) is not type(right): return False
    if type(right) is dict: return set(left) == set(right) and all(_exact(left[key], right[key]) for key in right)
    if type(right) is list: return len(left) == len(right) and all(_exact(a, b) for a, b in zip(left, right))
    return left == right


def _binding(value, path):
    return (type(value) is dict and set(value) == {"bytes", "path", "sha256"} and value.get("path") == path and
            type(value.get("bytes")) is int and 0 < value["bytes"] <= MAX_SOURCE and
            type(value.get("sha256")) is str and len(value["sha256"]) == 64 and
            all(ch in "0123456789abcdef" for ch in value["sha256"]))


def _check_deadline(deadline_ns):
    if type(deadline_ns) is not int or time.monotonic_ns() >= deadline_ns: raise ValueError


def _parse_utc(value):
    if type(value) is not str or not value.endswith("Z"): raise ValueError
    result = datetime.fromisoformat(value[:-1] + "+00:00")
    if result.utcoffset() != timedelta(0): raise ValueError
    return result


def _plan(root: Path, wall: datetime):
    path = root / PLAN_REL; _safe_chain(root, path); before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or getattr(before, "st_file_attributes", 0) & REPARSE_ATTRIBUTE or not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_PLAN:
        raise ValueError
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); raw = os.read(fd, MAX_PLAN + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or len(raw) != before.st_size): raise ValueError
    def hook(items):
        out, norms = {}, set()
        for key, value in items:
            norm = unicodedata.normalize("NFC", key)
            if key in out or norm in norms: raise ValueError
            out[key] = value; norms.add(norm)
        return out
    plan = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=hook)
    if type(plan) is not dict or set(plan) != ROOT_KEYS or _canonical(plan) != raw: raise ValueError
    fixed = {"schema_version": PLAN_SCHEMA, "epic_id": "EPIC-PHONE-001", "run_id": RUN_ID,
             "contour_id": CONTOUR_ID, "renewal_id": RENEWAL_ID, "authority_set_id": AUTHORITY_SET_ID,
             "prep_attempt_id": PREP_ATTEMPT_ID, "security_alias": SECURITY_ALIAS, "classification": "PROD_SAFE",
             "scope_qualifier": "ZERO_SECRET_ZERO_DEVICE_CREATE_NEW_VERSIONED_AUTHORITY_RENEWAL",
             "plan_path": PLAN_REL.as_posix(),
             "marker_path": ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-renewal-001-attempt.local.json",
             "set_root": ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003",
             "result_path": ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/authority-renewal-result.local.json"}
    if any(type(plan.get(k)) is not type(v) or plan.get(k) != v for k, v in fixed.items()): raise ValueError
    authority = plan.get("owner_no_mutator_authority")
    expected_authority = {"alias": "epic-phone-001-owner-authority-renewal-no-mutator-001",
                          "expires_at_utc": authority.get("expires_at_utc") if type(authority) is dict else None,
                          "scope": NO_MUTATOR_SCOPE, "status": "accepted_by_owner"}
    if not _exact(authority, expected_authority): raise ValueError
    issued, expires, authority_expires = (_parse_utc(plan.get("issued_at_utc")), _parse_utc(plan.get("expires_at_utc")),
                                          _parse_utc(authority["expires_at_utc"]))
    if not issued <= wall < expires or expires <= issued or expires - issued > timedelta(minutes=10): raise ValueError
    if expires < wall + timedelta(seconds=301) or authority_expires < wall + timedelta(seconds=301): raise ValueError
    if (not _exact(plan.get("budget"), BUDGET) or plan.get("candidate_path") != "docs/qa/phone/epic-phone-001-authority-renewal-candidate.json" or
            type(plan.get("candidate_bytes")) is not int or not 0 < plan["candidate_bytes"] <= MAX_PLAN or
            type(plan.get("candidate_sha256")) is not str or len(plan["candidate_sha256"]) != 64 or
            plan.get("artifact_paths") != ARTIFACT_PATHS or
            plan.get("literal_go_format") != GO_PREFIX + "<64_lowercase_plan_sha256>" or
            plan.get("failure_policy") != "marker_first_partial_preserved_no_retry_no_cleanup_no_reuse"):
        raise ValueError
    if type(plan.get("source_bindings")) is not list or len(plan["source_bindings"]) != 6 or any(
            not _binding(item, path) for item, path in zip(plan["source_bindings"], SOURCE_PATHS)):
        raise ValueError
    if not _binding(plan.get("gitignore_binding"), ".gitignore"): raise ValueError
    head = plan.get("repository_head")
    if type(head) is not str or len(head) != 40 or any(ch not in HEX40 for ch in head): raise ValueError
    first = plan["source_bindings"][0]
    if os.environ.get(GO_ENV) != GO_PREFIX + hashlib.sha256(raw).hexdigest(): raise ValueError
    return plan, first, raw


def _load(root: Path, binding):
    path = root / EXECUTOR_REL; _safe_chain(root, path); before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or getattr(before, "st_file_attributes", 0) & REPARSE_ATTRIBUTE or not stat.S_ISREG(before.st_mode) or before.st_size != binding["bytes"]: raise ValueError
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try: opened = os.fstat(fd); source = os.read(fd, binding["bytes"] + 1); after = os.fstat(fd)
    finally: os.close(fd)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity or
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity or len(source) != binding["bytes"] or
            hashlib.sha256(source).hexdigest() != binding["sha256"]): raise ValueError
    return source


def main() -> int:
    try:
        mono_start = time.monotonic_ns(); wall_start = datetime.now(UTC); deadline_ns = mono_start + 300_000_000_000
        _check_deadline(deadline_ns)
        root = Path.cwd().absolute(); plan, binding, raw_plan = _plan(root, wall_start); _check_deadline(deadline_ns)
        source = _load(root, binding); _check_deadline(deadline_ns)
        sys.dont_write_bytecode = True
        namespace = {"__name__": "__authority_renewal_executor__", "__file__": str(root / EXECUTOR_REL), "__package__": None,
                     "__authority_renewal_plan_bytes__": raw_plan}
        namespace["__authority_renewal_deadline_monotonic_ns__"] = deadline_ns
        namespace["__authority_renewal_bootstrap_wall_utc__"] = wall_start
        namespace["__authority_renewal_loader_go_env_read_count__"] = 1
        namespace["__authority_renewal_loader_source_read_count__"] = 1
        exec(compile(source, str(root / EXECUTOR_REL), "exec", dont_inherit=True), namespace, namespace); _check_deadline(deadline_ns)
        entry = namespace.get("main")
        if not callable(entry): return 2
        result = entry(); _check_deadline(deadline_ns)
        return result if type(result) is int and result in (0, 2) else 2
    except BaseException: return 2


if __name__ == "__main__": sys.exit(main())

"""Fail-closed authority for the TASK-041 portable official export.

The tool is repository-only and performs static filesystem, Git-index and ZIP
checks.  It never reads ignored local evidence, APKs, devices or runtime state.
An official archive contains exactly the Git-tracked regular files plus one
generated ``official-export-index.json`` member.  The embedded index is the
portable hash/size/file-set authority when ``.git`` is absent.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import stat
import struct
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SCHEMA_VERSION = "official-export-index-v1"
TASK_INDEX_SCHEMA_VERSION = "task041-055-index-v1"
INDEX_NAME = "official-export-index.json"
TASK_INDEX_PATH = Path("docs/qa/epics/task041_055_task_index.json")
OPAQUE_SURFACE_PATH = Path("docs/qa/epics/opaque_surface_task_traceability.csv")
TASK_RANGE = tuple(f"TASK-{number:03d}" for number in range(41, 56))
TASK_SCENARIO_TOTAL = 307
MAX_ZIP_MEMBERS = 10_000
MAX_ZIP_ENTRY_BYTES = 64 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 512 * 1024 * 1024
MAX_ZIP_COMPRESSION_RATIO = 200
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
WINDOWS_FORBIDDEN_CHARS = frozenset('<>:"|?*')
INDEX_FIELDS = {"schema_version", "algorithm", "index_path", "file_count", "files"}
FILE_FIELDS = {"path", "size", "sha256"}
TASK_INDEX_FIELDS = {"schema_version", "epic_id", "task_count", "scenario_count", "tasks"}
TASK_FIELDS = {
    "task_id",
    "title",
    "task_spec_path",
    "prompt_path",
    "scenario_catalog_path",
    "dependencies",
    "next_task",
    "production_safety_classification",
    "scenario_count",
    "p0_count",
}
PRESERVED_EXACT_PATHS = (
    "docs/approvals/local_paths_policy.md",
    "docs/approvals/task005_apk_bundle_contract.md",
    "docs/approvals/device_inventory.public_safe.review.json",
)
PRESERVED_HISTORY_PREFIXES = ("tasks/", "docs/qa/reports/")
SCENARIO_HEADERS = (
    "scenario_id",
    "priority",
    "surface_ids",
    "lane",
    "category",
    "title",
    "preconditions",
    "steps",
    "expected_oracle",
    "negative_or_boundary",
    "automation_target",
    "evidence_required",
    "safety_class",
    "blocking_rule",
)
STATIC_SCENARIO_EVIDENCE = "runner_log+ledger+hash_bound_static_artifact"
VISUAL_SCENARIO_EVIDENCE = "screenshot+ui_tree+runner_log+ledger"
OPAQUE_SURFACE_HEADERS = (
    "surface_id",
    "risk",
    "category",
    "public_safe_description",
    "applicable_families",
    "primary_tasks",
    "runtime_oracle",
    "evidence_status",
    "scenario_ids",
    "scenario_count",
)
CANONICAL_TASK_SPEC_PATHS = {
    "TASK-041": "tasks/TASK_041_qa_only_epic_integration_portable_export.md",
    "TASK-042": "tasks/TASK_042_local_runtime_preflight.md",
    "TASK-043": "tasks/TASK_043_source_informed_runtime_coverage_map.md",
    "TASK-044": "tasks/TASK_044_tpv13_reference_lane_oracle_closure.md",
    "TASK-045": "tasks/TASK_045_paired_tv_phone_virtual_gamepad_e2e.md",
    "TASK-046": "tasks/TASK_046_yandextv_representative_lane.md",
    "TASK-047": "tasks/TASK_047_sberbox_representative_lane.md",
    "TASK-048": "tasks/TASK_048_aosp_launcher_system_cluster_runtime.md",
    "TASK-049": "tasks/TASK_049_cross_family_transition_state_closure.md",
    "TASK-050": "tasks/TASK_050_install_update_persistence_recovery_matrix.md",
    "TASK-051": "tasks/TASK_051_network_api_transport_runtime.md",
    "TASK-052": "tasks/TASK_052_input_gamepad_lifecycle_coverage.md",
    "TASK-053": "tasks/TASK_053_device_equivalence_compatibility_usability.md",
    "TASK-054": "tasks/TASK_054_stability_performance_soak.md",
    "TASK-055": "tasks/TASK_055_unified_multi_apk_release_gate.md",
}


@dataclass(frozen=True)
class ExportEntry:
    path: str
    size: int
    sha256: str


class ExportIndexError(Exception):
    """Controlled public-safe failure carrying only a stable reason code."""

    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def _fail(condition: bool, reason: str) -> None:
    if condition:
        raise ExportIndexError(reason)


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _portable_path(raw_path: Any, *, allow_index: bool = False) -> tuple[str, str]:
    _fail(not isinstance(raw_path, str) or not raw_path, "PATH_INVALID")
    _fail(CONTROL_RE.search(raw_path) is not None, "PATH_CONTROL_CHARACTER")
    _fail("\\" in raw_path, "PATH_BACKSLASH")
    _fail("%" in raw_path, "PATH_ENCODED_OR_PERCENT")
    _fail("?" in raw_path or "#" in raw_path, "PATH_QUERY_OR_FRAGMENT")
    _fail(raw_path.startswith(("/", "//")) or re.match(r"^[A-Za-z]:/", raw_path) is not None, "PATH_ABSOLUTE")
    _fail(any(char in WINDOWS_FORBIDDEN_CHARS for char in raw_path), "PATH_WINDOWS_FORBIDDEN_CHARACTER")
    _fail(unicodedata.normalize("NFC", raw_path) != raw_path, "PATH_NOT_NFC")
    parts = raw_path.split("/")
    _fail(any(part in {"", ".", ".."} for part in parts), "PATH_TRAVERSAL_OR_AMBIGUOUS")
    _fail(any(part.casefold() == ".git" for part in parts), "PATH_VCS_METADATA")
    for part in parts:
        _fail(part != part.rstrip(" ."), "PATH_TRAILING_DOT_OR_SPACE")
        stem = part.split(".", 1)[0].casefold()
        _fail(stem in WINDOWS_RESERVED, "PATH_RESERVED_NAME")
    normalized = "/".join(parts)
    _fail(not allow_index and normalized == INDEX_NAME, "PATH_INDEX_SELF_ENTRY")
    return normalized, unicodedata.normalize("NFC", normalized).casefold()


def _parse_index_bytes(content: bytes) -> list[ExportEntry]:
    _fail(len(content) > 32 * 1024 * 1024, "INDEX_TOO_LARGE")
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ExportIndexError("INDEX_MALFORMED") from None
    _fail(not isinstance(payload, dict) or set(payload) != INDEX_FIELDS, "INDEX_SCHEMA_INVALID")
    _fail(payload.get("schema_version") != SCHEMA_VERSION, "INDEX_SCHEMA_VERSION_INVALID")
    _fail(payload.get("algorithm") != "sha256", "INDEX_ALGORITHM_INVALID")
    _fail(payload.get("index_path") != INDEX_NAME, "INDEX_PATH_INVALID")
    files = payload.get("files")
    _fail(not isinstance(files, list) or not files, "INDEX_FILES_INVALID")
    _fail(type(payload.get("file_count")) is not int or payload["file_count"] != len(files), "INDEX_COUNT_MISMATCH")
    entries: list[ExportEntry] = []
    normalized_keys: set[str] = set()
    previous_path = ""
    for item in files:
        _fail(not isinstance(item, dict) or set(item) != FILE_FIELDS, "INDEX_FILE_SCHEMA_INVALID")
        path, collision_key = _portable_path(item.get("path"))
        _fail(collision_key in normalized_keys, "INDEX_NORMALIZED_PATH_COLLISION")
        normalized_keys.add(collision_key)
        _fail(previous_path and path <= previous_path, "INDEX_FILES_NOT_SORTED")
        previous_path = path
        size = item.get("size")
        digest = item.get("sha256")
        _fail(type(size) is not int or size < 0, "INDEX_FILE_SIZE_INVALID")
        _fail(not isinstance(digest, str) or HASH_RE.fullmatch(digest) is None, "INDEX_FILE_HASH_INVALID")
        entries.append(ExportEntry(path=path, size=size, sha256=digest))
    return entries


def _index_bytes(entries: Iterable[ExportEntry]) -> bytes:
    ordered = sorted(entries, key=lambda entry: entry.path)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": "sha256",
        "index_path": INDEX_NAME,
        "file_count": len(ordered),
        "files": [entry.__dict__ for entry in ordered],
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _git(root: Path, args: list[str]) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={root.as_posix()}", *args],
            cwd=root,
            check=False,
            capture_output=True,
        )
    except OSError:
        raise ExportIndexError("GIT_UNAVAILABLE") from None
    _fail(result.returncode != 0, "GIT_COMMAND_FAILED")
    return result.stdout


def _git_status(root: Path, args: list[str]) -> int:
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={root.as_posix()}", *args],
            cwd=root,
            check=False,
            capture_output=True,
        )
    except OSError:
        raise ExportIndexError("GIT_UNAVAILABLE") from None
    return result.returncode


def _assert_export_worktree_ready(root: Path) -> None:
    status = _git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    _fail(bool(status), "GIT_WORKTREE_NOT_CLEAN")


def _tracked_git_entries(root: Path) -> list[tuple[str, str]]:
    raw = _git(root, ["ls-files", "--stage", "-z"])
    _fail(not raw, "GIT_TRACKED_SET_EMPTY")
    entries: list[tuple[str, str]] = []
    keys: set[str] = set()
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_id, stage = metadata.decode("ascii").split(" ")
            decoded = raw_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            raise ExportIndexError("GIT_INDEX_RECORD_INVALID") from None
        _fail(stage != "0", "GIT_INDEX_UNMERGED")
        _fail(mode not in {"100644", "100755"}, "GIT_INDEX_NONREGULAR_ENTRY")
        if decoded == INDEX_NAME:
            continue
        path, key = _portable_path(decoded)
        _fail(key in keys, "GIT_NORMALIZED_PATH_COLLISION")
        keys.add(key)
        entries.append((path, object_id))
    _fail(not entries, "GIT_TRACKED_SET_EMPTY")
    return sorted(entries)


def _tracked_paths(root: Path) -> list[str]:
    return [path for path, _ in _tracked_git_entries(root)]


def _regular_file_bytes(root: Path, repo_path: str) -> bytes:
    _portable_path(repo_path)
    root = root.resolve(strict=True)
    candidate = root.joinpath(*PurePosixPath(repo_path).parts)
    current = root
    for part in PurePosixPath(repo_path).parts:
        current = current / part
        try:
            _fail(current.is_symlink(), "TREE_SYMLINK_REJECTED")
        except OSError:
            raise ExportIndexError("TREE_METADATA_ERROR") from None
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        raise ExportIndexError("TREE_PATH_UNAVAILABLE") from None
    _fail(not resolved.is_file(), "TREE_NONREGULAR_ENTRY")
    try:
        return resolved.read_bytes()
    except OSError:
        raise ExportIndexError("TREE_READ_ERROR") from None


def _path_is_reparse(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _contained_regular_file(root: Path, repo_path: str | Path, reason: str) -> Path:
    root = root.resolve(strict=True)
    normalized, _ = _portable_path(Path(repo_path).as_posix())
    candidate = root.joinpath(*PurePosixPath(normalized).parts)
    current = root
    for part in PurePosixPath(normalized).parts:
        current = current / part
        _fail(_path_is_reparse(current), reason)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        raise ExportIndexError(reason) from None
    _fail(not resolved.is_file(), reason)
    return resolved


def build_git_index(root: Path) -> tuple[bytes, list[ExportEntry]]:
    root = root.resolve(strict=True)
    _assert_export_worktree_ready(root)
    entries: list[ExportEntry] = []
    for repo_path, object_id in _tracked_git_entries(root):
        content = _git(root, ["cat-file", "blob", object_id])
        entries.append(ExportEntry(repo_path, len(content), _sha256_bytes(content)))
    return _index_bytes(entries), entries


def _canonical_index_path(root: Path, requested: Path | None) -> Path:
    root = root.resolve(strict=True)
    expected = root / INDEX_NAME
    candidate = expected if requested is None else requested
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        raise ExportIndexError("INDEX_PATH_OUTSIDE_ROOT") from None
    _fail(resolved != expected, "INDEX_PATH_OUTSIDE_ROOT")
    return expected


def _tree_files(root: Path) -> dict[str, Path]:
    root = root.resolve(strict=True)
    _fail(root.is_symlink(), "TREE_ROOT_SYMLINK_REJECTED")
    found: dict[str, Path] = {}
    keys: set[str] = set()
    for current_root, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_root)
        kept_dirs: list[str] = []
        for name in sorted(dir_names):
            path = current / name
            relative = path.relative_to(root).as_posix()
            if relative == ".git":
                raise ExportIndexError("TREE_VCS_METADATA_PRESENT")
            _fail(_path_is_reparse(path), "TREE_SYMLINK_REJECTED")
            kept_dirs.append(name)
        dir_names[:] = kept_dirs
        for name in sorted(file_names):
            path = current / name
            relative = path.relative_to(root).as_posix()
            _fail(relative == ".git", "TREE_VCS_METADATA_PRESENT")
            normalized, key = _portable_path(relative, allow_index=True)
            _fail(key in keys, "TREE_NORMALIZED_PATH_COLLISION")
            keys.add(key)
            _fail(_path_is_reparse(path), "TREE_SYMLINK_REJECTED")
            _fail(not path.is_file(), "TREE_NONREGULAR_ENTRY")
            found[normalized] = path
    return found


def validate_tree(root: Path, index_path: Path | None = None) -> list[ExportEntry]:
    root = root.resolve(strict=True)
    index_path = _canonical_index_path(root, index_path)
    _fail(not index_path.exists() or not index_path.is_file() or index_path.is_symlink(), "INDEX_MISSING")
    try:
        entries = _parse_index_bytes(index_path.read_bytes())
    except OSError:
        raise ExportIndexError("INDEX_UNREADABLE") from None
    actual = _tree_files(root)
    expected_paths = {entry.path for entry in entries}
    actual_paths = set(actual) - {INDEX_NAME}
    _fail(actual_paths - expected_paths != set(), "TREE_EXTRA_FILE")
    _fail(expected_paths - actual_paths != set(), "TREE_MISSING_FILE")
    for entry in entries:
        try:
            content = actual[entry.path].read_bytes()
        except OSError:
            raise ExportIndexError("TREE_READ_ERROR") from None
        _fail(len(content) != entry.size, "TREE_SIZE_MISMATCH")
        _fail(_sha256_bytes(content) != entry.sha256, "TREE_HASH_MISMATCH")
    return entries


def validated_portable_paths(root: Path) -> list[Path]:
    """Return exact index-governed paths only after full portable validation.

    This is the sole no-Git discovery authority for other repository tools.
    It intentionally performs no permissive directory fallback.
    """

    root = root.resolve(strict=True)
    entries = validate_tree(root, root / INDEX_NAME)
    return [Path(entry.path) for entry in entries]


def _zip_member_is_symlink(info: zipfile.ZipInfo) -> bool:
    return stat.S_IFMT((info.external_attr >> 16) & 0xFFFF) == stat.S_IFLNK


def _zip_member_is_nonregular(info: zipfile.ZipInfo) -> bool:
    unix_type = stat.S_IFMT((info.external_attr >> 16) & 0xFFFF)
    return unix_type not in {0, stat.S_IFREG}


def _zip_member_has_reparse_metadata(info: zipfile.ZipInfo) -> bool:
    return bool(info.external_attr & 0x400)


def _raw_local_zip_name(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    try:
        if archive.fp is None:
            raise OSError
        archive.fp.seek(info.header_offset)
        header = archive.fp.read(30)
        if len(header) != 30:
            raise OSError
        signature, *values = struct.unpack("<IHHHHHIIIHH", header)
        if signature != 0x04034B50:
            raise OSError
        name_length = values[-2]
        raw_name = archive.fp.read(name_length)
        if len(raw_name) != name_length:
            raise OSError
        encoding = "utf-8" if info.flag_bits & 0x800 else "cp437"
        return raw_name.decode(encoding)
    except (OSError, UnicodeDecodeError, struct.error):
        raise ExportIndexError("ZIP_LOCAL_HEADER_INVALID") from None


def validate_zip(zip_path: Path) -> None:
    try:
        archive = zipfile.ZipFile(zip_path, "r")
    except (OSError, zipfile.BadZipFile):
        raise ExportIndexError("ZIP_MALFORMED") from None
    with archive:
        infos = archive.infolist()
        _fail(not infos, "ZIP_EMPTY")
        _fail(len(infos) > MAX_ZIP_MEMBERS, "ZIP_MEMBER_LIMIT_EXCEEDED")
        members: dict[str, zipfile.ZipInfo] = {}
        keys: set[str] = set()
        total_uncompressed = 0
        for info in infos:
            raw_name = _raw_local_zip_name(archive, info)
            _portable_path(raw_name, allow_index=True)
            _fail(raw_name != info.filename, "ZIP_RAW_NAME_MISMATCH")
            path, key = _portable_path(info.filename, allow_index=True)
            _fail(key in keys, "ZIP_NORMALIZED_PATH_COLLISION")
            keys.add(key)
            _fail(info.is_dir(), "ZIP_DIRECTORY_ENTRY_UNEXPECTED")
            _fail(_zip_member_is_symlink(info), "ZIP_SYMLINK_REJECTED")
            _fail(_zip_member_is_nonregular(info), "ZIP_NONREGULAR_ENTRY_REJECTED")
            _fail(_zip_member_has_reparse_metadata(info), "ZIP_REPARSE_ENTRY_REJECTED")
            _fail(bool(info.flag_bits & 0x1), "ZIP_ENCRYPTED_ENTRY_REJECTED")
            _fail(info.file_size < 0 or info.file_size > MAX_ZIP_ENTRY_BYTES, "ZIP_ENTRY_SIZE_LIMIT_EXCEEDED")
            total_uncompressed += info.file_size
            _fail(total_uncompressed > MAX_ZIP_TOTAL_BYTES, "ZIP_TOTAL_SIZE_LIMIT_EXCEEDED")
            if info.file_size:
                _fail(info.compress_size <= 0, "ZIP_COMPRESSION_METADATA_INVALID")
                _fail(
                    info.file_size > info.compress_size * MAX_ZIP_COMPRESSION_RATIO,
                    "ZIP_COMPRESSION_RATIO_LIMIT_EXCEEDED",
                )
            members[path] = info
        _fail(INDEX_NAME not in members, "INDEX_MISSING")
        try:
            index_content = archive.read(members[INDEX_NAME])
        except (OSError, RuntimeError, zipfile.BadZipFile):
            raise ExportIndexError("INDEX_UNREADABLE") from None
        entries = _parse_index_bytes(index_content)
        expected_paths = {entry.path for entry in entries}
        actual_paths = set(members) - {INDEX_NAME}
        _fail(actual_paths - expected_paths != set(), "ZIP_EXTRA_FILE")
        _fail(expected_paths - actual_paths != set(), "ZIP_MISSING_FILE")
        for entry in entries:
            info = members[entry.path]
            _fail(info.file_size != entry.size, "ZIP_SIZE_MISMATCH")
            try:
                content = archive.read(info)
            except (OSError, RuntimeError, zipfile.BadZipFile):
                raise ExportIndexError("ZIP_READ_ERROR") from None
            _fail(len(content) != entry.size, "ZIP_SIZE_MISMATCH")
            _fail(_sha256_bytes(content) != entry.sha256, "ZIP_HASH_MISMATCH")


def create_zip(root: Path, output: Path) -> None:
    root = root.resolve(strict=True)
    try:
        output_resolved = output.resolve(strict=False)
        output_resolved.relative_to(root)
    except ValueError:
        pass
    except (OSError, RuntimeError):
        raise ExportIndexError("ZIP_OUTPUT_PATH_INVALID") from None
    else:
        raise ExportIndexError("ZIP_OUTPUT_INSIDE_ROOT")
    _fail(output.exists() or output.is_symlink(), "ZIP_OUTPUT_EXISTS")
    index_content, entries = build_git_index(root)
    tracked_object_ids = dict(_tracked_git_entries(root))
    temporary_path: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        _fail(_path_is_reparse(output.parent), "ZIP_OUTPUT_PATH_INVALID")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.",
            suffix=".task041.tmp",
            dir=output.parent,
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for entry in entries:
                object_id = tracked_object_ids[entry.path]
                content = _git(root, ["cat-file", "blob", object_id])
                info = zipfile.ZipInfo(entry.path, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, content)
            index_info = zipfile.ZipInfo(INDEX_NAME, date_time=(1980, 1, 1, 0, 0, 0))
            index_info.compress_type = zipfile.ZIP_DEFLATED
            index_info.create_system = 3
            index_info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(index_info, index_content)
        validate_zip(temporary_path)
        _publish_no_clobber(temporary_path, output, "ZIP_OUTPUT_EXISTS", "ZIP_WRITE_ERROR")
    except ExportIndexError:
        raise
    except OSError:
        raise ExportIndexError("ZIP_WRITE_ERROR") from None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def _publish_no_clobber(
    temporary_path: Path,
    output: Path,
    exists_reason: str,
    failure_reason: str,
) -> None:
    try:
        os.link(temporary_path, output)
    except FileExistsError:
        raise ExportIndexError(exists_reason) from None
    except OSError:
        raise ExportIndexError(failure_reason) from None


def write_git_index(root: Path, requested: Path | None = None) -> None:
    root = root.resolve(strict=True)
    target = _canonical_index_path(root, requested)
    _fail(target.exists() or target.is_symlink(), "INDEX_OUTPUT_EXISTS")
    content, _ = build_git_index(root)
    temporary_path: Path | None = None
    descriptor: int | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".task041.tmp",
            dir=target.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        parsed = _parse_index_bytes(temporary_path.read_bytes())
        _fail(_index_bytes(parsed) != content, "INDEX_SELF_VALIDATION_FAILED")
        _publish_no_clobber(temporary_path, target, "INDEX_OUTPUT_EXISTS", "INDEX_WRITE_ERROR")
    except ExportIndexError:
        raise
    except OSError:
        raise ExportIndexError("INDEX_WRITE_ERROR") from None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def check_preservation(root: Path, base_ref: str) -> None:
    root = root.resolve(strict=True)
    _fail(not isinstance(base_ref, str) or re.fullmatch(r"[0-9a-f]{40}", base_ref) is None, "BASE_REF_INVALID")
    base_paths_raw = _git(root, ["ls-tree", "-r", "-z", "--name-only", base_ref])
    try:
        base_paths = {item.decode("utf-8") for item in base_paths_raw.split(b"\0") if item}
    except UnicodeDecodeError:
        raise ExportIndexError("BASE_PATH_NOT_UTF8") from None
    preserved_history = {
        path
        for path in base_paths
        if path.startswith("docs/qa/reports/")
        or (path.startswith("tasks/TASK_") and re.match(r"tasks/TASK_(?:0[0-3][0-9]|040)(?:\D|$)", path))
    }
    _fail(not preserved_history, "BASE_HISTORY_SET_EMPTY")
    for repo_path in preserved_history:
        _fail(not (root / PurePosixPath(repo_path)).is_file(), "HISTORY_FILE_REMOVED")
        if repo_path != "docs/qa/reports/report-manifest.json":
            changed = _git_status(root, ["diff", "--no-ext-diff", "--quiet", base_ref, "--", repo_path])
            _fail(changed not in {0, 1}, "GIT_COMMAND_FAILED")
            _fail(changed == 1, "HISTORY_FILE_CHANGED")
    for repo_path in PRESERVED_EXACT_PATHS:
        _fail(repo_path not in base_paths, "BASE_CONTRACT_MISSING")
        changed = _git_status(root, ["diff", "--no-ext-diff", "--quiet", base_ref, "--", repo_path])
        _fail(changed not in {0, 1}, "GIT_COMMAND_FAILED")
        _fail(changed == 1, "PRESERVED_CONTRACT_CHANGED")
    tracked = set(_tracked_paths(root))
    _fail(any(path == ".qa_local" or path.startswith(".qa_local/") for path in tracked), "LOCAL_ONLY_PATH_TRACKED")


def _read_json_object(path: Path, malformed_reason: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ExportIndexError(malformed_reason) from None
    _fail(not isinstance(value, dict), malformed_reason)
    return value


def _canonical_task_index_path(root: Path, requested: Path | None) -> Path:
    if requested is not None and (requested.is_absolute() or requested.as_posix() != TASK_INDEX_PATH.as_posix()):
        raise ExportIndexError("TASK_INDEX_PATH_INVALID")
    return _contained_regular_file(root, TASK_INDEX_PATH, "TASK_INDEX_PATH_INVALID")


def validate_epic(root: Path, task_index_path: Path | None = None) -> None:
    root = root.resolve(strict=True)
    path = _canonical_task_index_path(root, task_index_path)
    payload = _read_json_object(path, "TASK_INDEX_MALFORMED")
    _fail(set(payload) != TASK_INDEX_FIELDS, "TASK_INDEX_SCHEMA_INVALID")
    _fail(payload.get("schema_version") != TASK_INDEX_SCHEMA_VERSION, "TASK_INDEX_VERSION_INVALID")
    _fail(payload.get("epic_id") != "EPIC-QA-041-055", "TASK_INDEX_EPIC_INVALID")
    tasks = payload.get("tasks")
    _fail(not isinstance(tasks, list) or len(tasks) != 15 or payload.get("task_count") != 15, "TASK_INDEX_COUNT_INVALID")
    _fail(payload.get("scenario_count") != TASK_SCENARIO_TOTAL, "TASK_INDEX_SCENARIO_TOTAL_INVALID")
    by_id: dict[str, dict[str, Any]] = {}
    mapped_paths: dict[str, set[str]] = {
        "task_spec_path": set(),
        "prompt_path": set(),
        "scenario_catalog_path": set(),
    }
    total_scenarios = 0
    for item in tasks:
        _fail(not isinstance(item, dict) or set(item) != TASK_FIELDS, "TASK_INDEX_ENTRY_SCHEMA_INVALID")
        task_id = item.get("task_id")
        _fail(task_id not in TASK_RANGE or task_id in by_id, "TASK_INDEX_TASK_ID_INVALID")
        by_id[task_id] = item
        task_number = int(task_id[-3:])
        expected_safety = "PROD_SAFE" if task_number in {41, 43, 55} else "PROD_CONDITIONAL"
        _fail(
            item.get("production_safety_classification") != expected_safety,
            "TASK_INDEX_SAFETY_CLASSIFICATION_INVALID",
        )
        dependencies = item.get("dependencies")
        _fail(not isinstance(dependencies, list) or any(dep not in TASK_RANGE for dep in dependencies), "TASK_INDEX_DEPENDENCY_INVALID")
        task_digits = task_id[-3:]
        expected_paths = {
            "task_spec_path": CANONICAL_TASK_SPEC_PATHS[task_id],
            "prompt_path": f"docs/qa/epics/prompts/task{task_digits}_codex_prompt.md",
            "scenario_catalog_path": f"docs/qa/epics/scenarios/task{task_digits}_scenarios.csv",
        }
        for field in ("task_spec_path", "prompt_path", "scenario_catalog_path"):
            repo_path, _ = _portable_path(item.get(field))
            _fail(repo_path != expected_paths[field], "TASK_INDEX_CANONICAL_PATH_MISMATCH")
            _fail(repo_path in mapped_paths[field], "TASK_INDEX_PATH_NOT_UNIQUE")
            mapped_paths[field].add(repo_path)
            _contained_regular_file(root, repo_path, "TASK_INDEX_REFERENCED_FILE_UNSAFE")
        _fail(type(item.get("scenario_count")) is not int or item["scenario_count"] <= 0, "TASK_INDEX_SCENARIO_COUNT_INVALID")
        _fail(type(item.get("p0_count")) is not int or item["p0_count"] <= 0, "TASK_INDEX_P0_COUNT_INVALID")
        total_scenarios += item["scenario_count"]
        try:
            catalog_path = _contained_regular_file(
                root,
                item["scenario_catalog_path"],
                "TASK_INDEX_REFERENCED_FILE_UNSAFE",
            )
            with catalog_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                _fail(tuple(reader.fieldnames or ()) != SCENARIO_HEADERS, "SCENARIO_CATALOG_HEADERS_INVALID")
                rows = list(reader)
        except (OSError, UnicodeDecodeError, csv.Error):
            raise ExportIndexError("SCENARIO_CATALOG_UNREADABLE") from None
        _fail(len(rows) != item["scenario_count"], "SCENARIO_CATALOG_COUNT_MISMATCH")
        scenario_ids = [row.get("scenario_id", "") for row in rows]
        expected_ids = [f"QA-{task_digits}-{number:03d}" for number in range(1, len(rows) + 1)]
        _fail(scenario_ids != expected_ids, "SCENARIO_ID_SEQUENCE_INVALID")
        _fail(
            any(any(not isinstance(row.get(field), str) or not row[field].strip() for field in SCENARIO_HEADERS) for row in rows),
            "SCENARIO_REQUIRED_FIELD_EMPTY",
        )
        _fail(sum(row.get("priority") == "P0" for row in rows) != item["p0_count"], "SCENARIO_P0_COUNT_MISMATCH")
        if task_number in {41, 43, 55}:
            _fail(any(row.get("safety_class") != "PROD_SAFE" for row in rows), "STATIC_TASK_SAFETY_INVALID")
            _fail(
                any(row.get("evidence_required") != STATIC_SCENARIO_EVIDENCE for row in rows),
                "STATIC_TASK_EVIDENCE_INVALID",
            )
        else:
            _fail(
                any(row.get("safety_class") != "PROD_CONDITIONAL" for row in rows),
                "RUNTIME_TASK_SAFETY_INVALID",
            )
            _fail(
                any(row.get("evidence_required") != VISUAL_SCENARIO_EVIDENCE for row in rows),
                "RUNTIME_TASK_EVIDENCE_INVALID",
            )
    _fail(set(by_id) != set(TASK_RANGE) or total_scenarios != TASK_SCENARIO_TOTAL, "TASK_INDEX_TASK_SET_INVALID")
    for number, task_id in enumerate(TASK_RANGE):
        item = by_id[task_id]
        expected_next = TASK_RANGE[number + 1] if number + 1 < len(TASK_RANGE) else None
        _fail(item.get("next_task") != expected_next, "TASK_INDEX_NEXT_TASK_INVALID")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        _fail(task_id in visiting, "TASK_INDEX_DEPENDENCY_CYCLE")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in by_id[task_id]["dependencies"]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in TASK_RANGE:
        visit(task_id)

    opaque_path = _contained_regular_file(root, OPAQUE_SURFACE_PATH, "OPAQUE_SURFACE_REGISTRY_UNSAFE")
    try:
        with opaque_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            _fail(tuple(reader.fieldnames or ()) != OPAQUE_SURFACE_HEADERS, "OPAQUE_SURFACE_HEADERS_INVALID")
            opaque_rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error):
        raise ExportIndexError("OPAQUE_SURFACE_REGISTRY_UNREADABLE") from None
    _fail(len(opaque_rows) != 55, "OPAQUE_SURFACE_COUNT_INVALID")
    _fail(
        len({row.get("surface_id") for row in opaque_rows}) != 55,
        "OPAQUE_SURFACE_ID_NOT_UNIQUE",
    )
    _fail(
        any(row.get("evidence_status") != "hypothesis" for row in opaque_rows),
        "OPAQUE_SURFACE_EVIDENCE_STATUS_INVALID",
    )


def _run(action: str, args: argparse.Namespace) -> None:
    if action == "build-index":
        write_git_index(args.root, args.index)
    elif action == "validate-tree":
        validate_tree(args.root, args.index)
    elif action == "create-zip":
        create_zip(args.root, args.output)
    elif action == "validate-zip":
        validate_zip(args.zip)
    elif action == "check-preservation":
        check_preservation(args.root, args.base_ref)
    elif action == "validate-epic":
        validate_epic(args.root, args.task_index)
    else:  # pragma: no cover - argparse guarantees the subcommand.
        raise ExportIndexError("ACTION_INVALID")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create and validate a portable official QA export.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    build = subparsers.add_parser("build-index")
    build.add_argument("--root", type=Path, default=Path("."))
    build.add_argument("--index", type=Path, default=Path(INDEX_NAME))
    tree = subparsers.add_parser("validate-tree")
    tree.add_argument("--root", type=Path, required=True)
    tree.add_argument("--index", type=Path)
    create = subparsers.add_parser("create-zip")
    create.add_argument("--root", type=Path, default=Path("."))
    create.add_argument("--output", type=Path, required=True)
    zip_parser = subparsers.add_parser("validate-zip")
    zip_parser.add_argument("--zip", type=Path, required=True)
    preserve = subparsers.add_parser("check-preservation")
    preserve.add_argument("--root", type=Path, default=Path("."))
    preserve.add_argument("--base-ref", required=True)
    epic = subparsers.add_parser("validate-epic")
    epic.add_argument("--root", type=Path, default=Path("."))
    epic.add_argument("--task-index", type=Path)
    args = parser.parse_args(argv)
    try:
        _run(args.action, args)
    except ExportIndexError as exc:
        sys.stdout.write(f"official_export_index=fail\nreason={exc.reason_code}\n")
        return 2
    sys.stdout.write(f"official_export_index=pass\naction={args.action}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

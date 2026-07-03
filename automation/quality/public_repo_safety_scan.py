"""Fail-closed public repository safety scan for tracked artifact paths.

The scan is local/static only. It does not inspect ignored `.qa_local/`
evidence, run Android tooling, read APK contents, contact a network service or
print matched secret-like values. Findings identify paths and rule ids only.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FORBIDDEN_PATH_PREFIXES = (
    ".qa_local/",
    "qa_reverse_analysis/",
    "docs/context/reverse-analysis/raw/",
    "safe_archives/",
)

FORBIDDEN_EXTENSIONS = {
    ".7z",
    ".aab",
    ".apk",
    ".apks",
    ".dex",
    ".jks",
    ".jar",
    ".key",
    ".keystore",
    ".log",
    ".mkv",
    ".mov",
    ".mp4",
    ".p12",
    ".pem",
    ".rar",
    ".so",
    ".webm",
    ".xml",
    ".xapk",
    ".zip",
}

FORBIDDEN_FILENAMES = {
    "google-services.json",
    "local.properties",
}

RAW_EVIDENCE_NAME_PREFIXES = (
    "logcat",
    "uiautomator",
    "screenrecord",
    "screenshot",
    "raw_adb",
    "ui_dump",
    "window_dump",
)

TREE_EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".qa_local",
    ".ruff_cache",
    "__pycache__",
}

TREE_EXCLUDED_FILE_NAMES = {
    "qa_reverse_analysis_documents.zip",
}


@dataclass(frozen=True)
class SafetyFinding:
    rule_id: str
    path: str
    reason: str


class GitTrackedScanUnavailable(RuntimeError):
    """Raised when git tracked-file discovery cannot be used."""


def _normalize_repo_path(path: Path | str) -> str:
    normalized = str(path).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    while normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def _tracked_files(root: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "-c", f"safe.directory={root.as_posix()}", "ls-files", "-z"],
            cwd=root,
            capture_output=True,
            text=False,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitTrackedScanUnavailable("git executable is unavailable") from exc
    if completed.returncode != 0:
        raise GitTrackedScanUnavailable("root is not a git checkout or git ls-files failed")
    return [Path(raw.decode("utf-8")) for raw in completed.stdout.split(b"\0") if raw]


def _tree_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for current_root, dir_names, file_names in os.walk(root):
        filtered_dir_names: list[str] = []
        for name in dir_names:
            candidate = Path(current_root).relative_to(root) / name
            repo_path = _normalize_repo_path(candidate)
            if name in TREE_EXCLUDED_DIRECTORIES:
                continue
            if any(repo_path == prefix.rstrip("/") or repo_path.startswith(prefix) for prefix in FORBIDDEN_PATH_PREFIXES):
                continue
            filtered_dir_names.append(name)
        dir_names[:] = filtered_dir_names
        for file_name in file_names:
            if file_name in TREE_EXCLUDED_FILE_NAMES:
                continue
            paths.append(Path(current_root).relative_to(root) / file_name)
    return sorted(paths)


def scan_repo_paths(paths: Iterable[Path | str]) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    for path in paths:
        repo_path = _normalize_repo_path(path)
        lower_path = repo_path.lower()
        path_obj = Path(repo_path)
        name = path_obj.name.lower()
        stem = path_obj.stem.lower()
        suffix = path_obj.suffix.lower()

        if any(lower_path.startswith(prefix) for prefix in FORBIDDEN_PATH_PREFIXES):
            findings.append(
                SafetyFinding(
                    "PUBLIC_PATH_FORBIDDEN_PREFIX",
                    repo_path,
                    "tracked path is under a raw/local-only artifact directory",
                )
            )
        if suffix in FORBIDDEN_EXTENSIONS:
            findings.append(
                SafetyFinding(
                    "PUBLIC_PATH_FORBIDDEN_EXTENSION",
                    repo_path,
                    "tracked path has an APK/raw evidence/archive/secret material extension",
                )
            )
        if name in FORBIDDEN_FILENAMES or name == ".env" or name.endswith(".env"):
            findings.append(
                SafetyFinding(
                    "PUBLIC_PATH_FORBIDDEN_FILENAME",
                    repo_path,
                    "tracked path has a local config, secret or signing filename",
                )
            )
        if suffix == ".png" and stem.startswith(RAW_EVIDENCE_NAME_PREFIXES):
            findings.append(
                SafetyFinding(
                    "PUBLIC_PATH_RAW_SCREENSHOT_NAME",
                    repo_path,
                    "tracked path looks like a raw screenshot artifact",
                )
            )
        if suffix == ".txt" and stem.startswith("logcat"):
            findings.append(
                SafetyFinding(
                    "PUBLIC_PATH_RAW_LOGCAT_NAME",
                    repo_path,
                    "tracked path looks like a raw logcat artifact",
                )
            )
    return findings


def _paths_for_mode(root: Path, mode: str) -> list[Path]:
    if mode == "tracked":
        return _tracked_files(root)
    if mode == "tree":
        return _tree_files(root)
    try:
        return _tracked_files(root)
    except GitTrackedScanUnavailable:
        return _tree_files(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan public repository paths for forbidden raw artifacts.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--mode",
        choices=("auto", "tracked", "tree"),
        default="auto",
        help="auto uses git tracked files and falls back to a local tree scan outside git.",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        paths = _paths_for_mode(root, args.mode)
    except GitTrackedScanUnavailable as exc:
        sys.stdout.write(f"public_repo_safety=blocked\nreason={exc}\n")
        return 2

    findings = scan_repo_paths(paths)
    if findings:
        for finding in findings:
            sys.stdout.write(f"{finding.rule_id}\t{finding.path}\t{finding.reason}\n")
        sys.stdout.write(f"public_repo_safety=fail\nscanned_files={len(paths)}\nfindings={len(findings)}\n")
        return 1

    sys.stdout.write(f"public_repo_safety=pass\nscanned_files={len(paths)}\nfindings=0\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

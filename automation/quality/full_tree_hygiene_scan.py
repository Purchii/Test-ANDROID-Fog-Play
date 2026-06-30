"""Scan tracked text files for whitespace and EOF hygiene issues.

This tool is local-only and performs no Android, device, APK, network or
production interaction. It intentionally scans tracked files instead of only
the current diff so historical whitespace issues cannot hide behind a clean
`git diff --check`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


BINARY_EXTENSIONS = {
    ".7z",
    ".aab",
    ".apk",
    ".apks",
    ".bin",
    ".bmp",
    ".class",
    ".dex",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".keystore",
    ".mov",
    ".mp4",
    ".pdf",
    ".png",
    ".pyd",
    ".pyc",
    ".pyo",
    ".so",
    ".webm",
    ".xapk",
    ".zip",
}

CACHE_AND_BUILD_DIRECTORIES = {
    ".cache",
    ".coverage",
    ".eggs",
    ".gradle",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "out",
    "target",
}

PUBLIC_SAFE_EXCLUDED_DIRECTORIES = {
    ".git",
    ".qa_local",
    *CACHE_AND_BUILD_DIRECTORIES,
}


class GitTrackedScanUnavailable(RuntimeError):
    """Raised when git tracked-file discovery cannot be used."""


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
    return [root / raw.decode("utf-8") for raw in completed.stdout.split(b"\0") if raw]


def _looks_binary(path: Path) -> bool:
    return path.suffix.lower() in BINARY_EXTENSIONS


def _public_safe_tree_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [
            name
            for name in dir_names
            if name not in PUBLIC_SAFE_EXCLUDED_DIRECTORIES
            and not name.endswith((".egg-info", ".dist-info"))
        ]
        for file_name in file_names:
            path = Path(current_root) / file_name
            if not _looks_binary(path):
                paths.append(path)
    return sorted(paths)


def _scan_file(path: Path) -> list[str]:
    if _looks_binary(path):
        return []
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [f"{path}: unable to read file: {exc}"]
    if b"\0" in data:
        return []

    issues: list[str] = []
    if data and not data.endswith(b"\n"):
        issues.append(f"{path}: missing final newline")

    lines = data.splitlines(keepends=True)
    for index, raw_line in enumerate(lines, start=1):
        content = raw_line.rstrip(b"\r\n")
        if content.endswith((b" ", b"\t")):
            issues.append(f"{path}:{index}: trailing whitespace")

    if len(lines) >= 2 and lines[-1].rstrip(b"\r\n") == b"":
        issues.append(f"{path}: blank line at EOF")

    return issues


def scan_paths(paths: Iterable[Path]) -> list[str]:
    issues: list[str] = []
    for path in paths:
        if path.is_file():
            issues.extend(_scan_file(path))
    return issues


def _paths_for_mode(root: Path, mode: str) -> list[Path]:
    if mode == "tracked":
        return _tracked_files(root)
    if mode == "public-safe-tree":
        return _public_safe_tree_files(root)

    try:
        return _tracked_files(root)
    except GitTrackedScanUnavailable:
        return _public_safe_tree_files(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan tracked text files for whitespace and EOF hygiene.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--mode",
        choices=("auto", "tracked", "public-safe-tree"),
        default="auto",
        help=(
            "Scan mode. auto uses git tracked files when available and falls back "
            "to a public-safe tree scan outside git checkouts."
        ),
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        paths = _paths_for_mode(root, args.mode)
    except GitTrackedScanUnavailable as exc:
        sys.stdout.write(f"full_tree_hygiene=blocked\nreason={exc}\n")
        return 2

    issues = scan_paths(paths)
    if issues:
        sys.stdout.write("\n".join(str(issue) for issue in issues) + "\n")
        return 1
    sys.stdout.write("full_tree_hygiene=pass\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Static Markdown link and public-reference sanity checks.

This TASK-018 guard is repository-local and public-safe. It reads tracked
Markdown files by default, validates local Markdown links and public
repo-relative file references, and never crawls external URLs or ignored local
evidence trees.
"""

from __future__ import annotations

import argparse
import posixpath
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit


MARKDOWN_LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
REFERENCE_DEFINITION_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(\S+)")
INLINE_REPO_PATH_RE = re.compile(
    r"`((?:AGENTS|CODEX_ANDROID_QA_PROJECT_TZ|README|pyproject)\.[A-Za-z0-9]+|"
    r"(?:automation|docs|tasks|tests)/[^`\s]+)`"
)

EXTERNAL_SCHEMES = {"http", "https", "mailto"}
PUBLIC_REFERENCE_PREFIXES = ("automation/", "docs/", "tasks/", "tests/")
FORBIDDEN_TARGET_PREFIXES = (
    ".qa_local/",
    "qa_reverse_analysis/",
    "docs/context/reverse-analysis/raw/",
    "safe_archives/",
)
FORBIDDEN_TARGET_EXTENSIONS = {
    ".7z",
    ".aab",
    ".apk",
    ".apks",
    ".dex",
    ".jks",
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
    ".xapk",
    ".zip",
}
FORBIDDEN_TARGET_FILENAMES = {
    ".env",
    "google-services.json",
    "local.properties",
}


@dataclass(frozen=True)
class DocsFinding:
    rule_id: str
    source_path: str
    line: int
    target: str
    reason: str


class GitTrackedScanUnavailable(RuntimeError):
    """Raised when git tracked-file discovery cannot be used."""


def _normalize_repo_path(path: str | Path) -> str:
    normalized = str(path).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    while normalized.startswith("/"):
        normalized = normalized[1:]
    return posixpath.normpath(normalized) if normalized else "."


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


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _is_external_target(target: str) -> bool:
    scheme = _url_scheme(target)
    return scheme in EXTERNAL_SCHEMES


def _url_scheme(target: str) -> str:
    decoded = unquote(target).replace("\\", "/")
    scheme = urlsplit(decoded).scheme.lower()
    if scheme and len(scheme) == 1 and re.match(r"^[A-Za-z]:/", decoded):
        return ""
    return scheme


def _has_forbidden_target_shape(target: str) -> bool:
    decoded = unquote(target).replace("\\", "/")
    lower = decoded.lower()
    normalized = _normalize_repo_path(decoded.split("#", 1)[0])
    path_obj = Path(normalized)
    scheme = _url_scheme(target)
    if scheme and scheme not in EXTERNAL_SCHEMES:
        return True
    if any(lower.startswith(prefix) or lower.startswith(f"./{prefix}") for prefix in FORBIDDEN_TARGET_PREFIXES):
        return True
    if path_obj.suffix.lower() in FORBIDDEN_TARGET_EXTENSIONS:
        return True
    if path_obj.name.lower() in FORBIDDEN_TARGET_FILENAMES or path_obj.name.lower().endswith(".env"):
        return True
    return False


def _target_label(target: str) -> str:
    if _is_external_target(target):
        return "[external-link-not-crawled]"
    if _has_forbidden_target_shape(target):
        return "[forbidden-local-target]"
    if "?" in target or "=" in target or _url_scheme(target):
        return "[query-or-url-like-target]"
    return target


def _looks_absolute_or_traversal(target: str) -> bool:
    decoded = unquote(target).replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", decoded):
        return True
    if decoded.startswith("//") or decoded.startswith("/"):
        return True
    parts = [part for part in decoded.split("#", 1)[0].split("/") if part]
    return any(part == ".." for part in parts)


def _resolve_target(source_path: str, target: str) -> str:
    path_part = unquote(target.split("#", 1)[0]).replace("\\", "/")
    if path_part == "":
        return source_path
    if path_part.startswith("./") or path_part.startswith("../"):
        base_dir = posixpath.dirname(source_path)
        return _normalize_repo_path(posixpath.join(base_dir, path_part))
    return _normalize_repo_path(path_part)


def _github_anchor_base(heading: str) -> str:
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"\[[^\]]+\]\(([^)]+)\)", "", heading)
    heading = heading.strip().lower()
    normalized = unicodedata.normalize("NFKD", heading)
    chars: list[str] = []
    previous_dash = False
    for char in normalized:
        category = unicodedata.category(char)
        if category.startswith("M"):
            continue
        if char.isalnum() or char in {"_", "-"}:
            chars.append(char)
            previous_dash = False
        elif char.isspace():
            if not previous_dash:
                chars.append("-")
                previous_dash = True
    return "".join(chars).strip("-")


def anchors_for_markdown(text: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = _github_anchor_base(match.group(2))
        if not base:
            continue
        duplicate_count = counts.get(base, 0)
        counts[base] = duplicate_count + 1
        anchors.add(base if duplicate_count == 0 else f"{base}-{duplicate_count}")
    return anchors


def _is_public_inline_reference(target: str) -> bool:
    if "*" in target or target.endswith("/"):
        return False
    normalized = _normalize_repo_path(target)
    if normalized in {"AGENTS.md", "CODEX_ANDROID_QA_PROJECT_TZ.md", "README.md", "pyproject.toml"}:
        return True
    return normalized.startswith(PUBLIC_REFERENCE_PREFIXES)


def scan_markdown_paths(root: Path, paths: Iterable[Path | str]) -> list[DocsFinding]:
    markdown_paths = [
        Path(path)
        for path in paths
        if _normalize_repo_path(path).lower().endswith(".md")
        and not any(_normalize_repo_path(path).lower().startswith(prefix) for prefix in FORBIDDEN_TARGET_PREFIXES)
    ]
    tracked_or_given = {_normalize_repo_path(path) for path in paths}
    text_by_path: dict[str, str] = {}
    anchors_by_path: dict[str, set[str]] = {}
    findings: list[DocsFinding] = []

    for path in markdown_paths:
        repo_path = _normalize_repo_path(path)
        try:
            text = (root / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            findings.append(DocsFinding("DOCS_READ_ERROR", repo_path, 1, repo_path, f"unable to read file: {exc}"))
            continue
        text_by_path[repo_path] = text
        anchors_by_path[repo_path] = anchors_for_markdown(text)

    for source_path, text in text_by_path.items():
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = next(group for group in match.groups() if group is not None)
            line = _line_for_offset(text, match.start())
            findings.extend(_scan_target(source_path, line, target, tracked_or_given, anchors_by_path, is_link=True))

        for line_index, line_text in enumerate(text.splitlines(), start=1):
            reference_definition = REFERENCE_DEFINITION_RE.match(line_text)
            if reference_definition:
                findings.extend(
                    _scan_target(
                        source_path,
                        line_index,
                        reference_definition.group(1),
                        tracked_or_given,
                        anchors_by_path,
                        is_link=True,
                    )
                )

        for match in INLINE_REPO_PATH_RE.finditer(text):
            target = match.group(1).rstrip(".,;:")
            if not _is_public_inline_reference(target):
                continue
            line = _line_for_offset(text, match.start())
            findings.extend(_scan_target(source_path, line, target, tracked_or_given, anchors_by_path, is_link=False))

    return findings


def _scan_target(
    source_path: str,
    line: int,
    target: str,
    known_paths: set[str],
    anchors_by_path: dict[str, set[str]],
    *,
    is_link: bool,
) -> list[DocsFinding]:
    findings: list[DocsFinding] = []
    if _is_external_target(target):
        return findings
    if target.startswith("#"):
        target_path = source_path
        anchor = unquote(target[1:])
    else:
        target_path = _resolve_target(source_path, target)
        anchor = unquote(target.split("#", 1)[1]) if "#" in target else ""

    if _looks_absolute_or_traversal(target):
        findings.append(
            DocsFinding(
                "DOCS_UNSAFE_TARGET_PATH",
                source_path,
                line,
                "[unsafe-local-target]",
                "target uses absolute path, Windows/UNC path or path traversal",
            )
        )
        return findings

    if is_link and _has_forbidden_target_shape(target):
        findings.append(
            DocsFinding(
                "DOCS_FORBIDDEN_LINK_TARGET",
                source_path,
                line,
                "[forbidden-local-target]",
                "Markdown link points to local-only, raw, package or secret-like material",
            )
        )
        return findings

    if target_path not in known_paths:
        findings.append(
            DocsFinding(
                "DOCS_MISSING_TARGET",
                source_path,
                line,
                _target_label(target),
                "local Markdown link or public repo-relative reference points to a missing tracked file",
            )
        )
        return findings

    if anchor:
        normalized_anchor = anchor.strip().lower()
        if target_path.lower().endswith(".md") and normalized_anchor not in anchors_by_path.get(target_path, set()):
            findings.append(
                DocsFinding(
                    "DOCS_MISSING_ANCHOR",
                    source_path,
                    line,
                    f"{target_path}#[anchor]",
                    "local Markdown anchor was not found in the target document",
                )
            )

    return findings


def _paths_for_mode(root: Path, mode: str) -> list[Path]:
    if mode == "tracked":
        return _tracked_files(root)
    if mode == "explicit":
        raise GitTrackedScanUnavailable("explicit mode requires --path arguments")
    try:
        return _tracked_files(root)
    except GitTrackedScanUnavailable:
        return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate public Markdown links and repo-relative doc references.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--mode",
        choices=("auto", "tracked", "explicit"),
        default="auto",
        help="auto/tracked use git tracked files; explicit scans only --path values.",
    )
    parser.add_argument("--path", action="append", default=[], help="Explicit repo-relative path to include.")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        if args.mode == "explicit":
            if not args.path:
                raise GitTrackedScanUnavailable("explicit mode requires --path arguments")
            paths = [Path(_normalize_repo_path(path)) for path in args.path]
        else:
            paths = _paths_for_mode(root, args.mode)
    except GitTrackedScanUnavailable as exc:
        sys.stdout.write(f"docs_consistency_link_sanity=blocked\nreason={exc}\n")
        return 2

    findings = scan_markdown_paths(root, paths)
    if findings:
        for finding in findings:
            sys.stdout.write(
                f"{finding.rule_id}\t{finding.source_path}:{finding.line}\t{finding.target}\t{finding.reason}\n"
            )
        sys.stdout.write(
            f"docs_consistency_link_sanity=fail\nscanned_files={len(paths)}\nfindings={len(findings)}\n"
        )
        return 1

    sys.stdout.write(f"docs_consistency_link_sanity=pass\nscanned_files={len(paths)}\nfindings=0\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


INVALID_SCAN_SOURCE = "[invalid-scan-path]"
INVALID_SCAN_TARGET = "[invalid-scan-path]"


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
    except OSError as exc:
        raise GitTrackedScanUnavailable("DOCS_GIT_DISCOVERY_UNAVAILABLE") from exc
    if completed.returncode != 0:
        raise GitTrackedScanUnavailable("DOCS_GIT_DISCOVERY_FAILED")
    try:
        return [Path(raw.decode("utf-8")) for raw in completed.stdout.split(b"\0") if raw]
    except UnicodeDecodeError as exc:
        raise GitTrackedScanUnavailable("DOCS_GIT_DISCOVERY_INVALID_OUTPUT") from exc


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


def _decode_path_for_validation(raw_path: str) -> str:
    decoded = raw_path
    for _ in range(3):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return decoded.replace("\\", "/")


def _scan_path_reason(raw_path: str) -> str | None:
    if not raw_path or raw_path == ".":
        return "DOCS_SCAN_PATH_EMPTY_OR_DOT"
    if any(ord(char) < 32 or ord(char) == 127 for char in raw_path):
        return "DOCS_SCAN_PATH_CONTROL_CHARACTER"
    if "?" in raw_path or "#" in raw_path:
        return "DOCS_SCAN_PATH_QUERY_OR_FRAGMENT"
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw_path):
        return "DOCS_SCAN_PATH_SCHEME_OR_DRIVE"

    decoded = _decode_path_for_validation(raw_path)
    if any(ord(char) < 32 or ord(char) == 127 for char in decoded):
        return "DOCS_SCAN_PATH_CONTROL_CHARACTER"
    if "?" in decoded or "#" in decoded:
        return "DOCS_SCAN_PATH_QUERY_OR_FRAGMENT"
    if decoded.startswith("/") or decoded.startswith("//") or re.match(r"^[A-Za-z]:/", decoded):
        return "DOCS_SCAN_PATH_ABSOLUTE"
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", decoded):
        return "DOCS_SCAN_PATH_SCHEME_OR_DRIVE"

    parts = decoded.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return "DOCS_SCAN_PATH_TRAVERSAL_OR_AMBIGUOUS"
    normalized = _normalize_repo_path(decoded)
    lower = normalized.lower()
    if any(lower.startswith(prefix) for prefix in FORBIDDEN_TARGET_PREFIXES):
        return "DOCS_SCAN_PATH_FORBIDDEN_PREFIX"
    if _has_forbidden_target_shape(decoded):
        return "DOCS_SCAN_PATH_FORBIDDEN_SHAPE"
    if not lower.endswith(".md"):
        return "DOCS_SCAN_PATH_NOT_MARKDOWN"
    return None


def _validate_markdown_scan_paths(root: Path, paths: Iterable[Path | str]) -> tuple[list[Path], list[DocsFinding]]:
    validated: list[Path] = []
    findings: list[DocsFinding] = []
    try:
        root_resolved = root.resolve()
    except (OSError, RuntimeError, ValueError):
        return [], [
            DocsFinding(
                "DOCS_UNSAFE_SCAN_PATH",
                INVALID_SCAN_SOURCE,
                1,
                INVALID_SCAN_TARGET,
                "DOCS_ROOT_INVALID",
            )
        ]

    for path in paths:
        raw_path = str(path)
        reason = _scan_path_reason(raw_path)
        if reason is None:
            repo_path = raw_path.replace("\\", "/")
            candidate = root / Path(repo_path)
            try:
                resolved = candidate.resolve(strict=False)
                resolved.relative_to(root_resolved)
            except (OSError, RuntimeError, ValueError):
                reason = "DOCS_SCAN_PATH_ROOT_ESCAPE"
            else:
                current = root
                try:
                    for part in Path(repo_path).parts:
                        current = current / part
                        if current.is_symlink():
                            reason = "DOCS_SCAN_PATH_SYMLINK"
                            break
                    if reason is None and (not candidate.exists() or not candidate.is_file()):
                        reason = "DOCS_SCAN_PATH_MISSING_OR_NONREGULAR"
                except OSError:
                    reason = "DOCS_SCAN_PATH_METADATA_ERROR"

        if reason is not None:
            findings.append(DocsFinding("DOCS_UNSAFE_SCAN_PATH", INVALID_SCAN_SOURCE, 1, INVALID_SCAN_TARGET, reason))
        else:
            validated.append(Path(_normalize_repo_path(repo_path)))

    if findings:
        return [], findings
    return validated, []


def _scan_markdown_paths(
    root: Path,
    paths: Iterable[Path | str],
    *,
    known_paths: Iterable[Path | str] | None = None,
) -> tuple[list[DocsFinding], int]:
    path_list = list(paths)
    markdown_paths, validation_findings = _validate_markdown_scan_paths(root, path_list)
    if validation_findings:
        return validation_findings, 0

    tracked_or_given = {
        _normalize_repo_path(path) for path in (known_paths if known_paths is not None else path_list)
    }
    text_by_path: dict[str, str] = {}
    anchors_by_path: dict[str, set[str]] = {}
    findings: list[DocsFinding] = []

    for path in markdown_paths:
        repo_path = _normalize_repo_path(path)
        try:
            text = (root / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(
                DocsFinding("DOCS_READ_ERROR", repo_path, 1, "[unreadable-markdown]", "DOCS_READ_ERROR")
            )
            continue
        except OSError:
            findings.append(
                DocsFinding("DOCS_READ_ERROR", repo_path, 1, "[unreadable-markdown]", "DOCS_READ_ERROR")
            )
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

    return findings, len(markdown_paths)


def scan_markdown_paths(root: Path, paths: Iterable[Path | str]) -> list[DocsFinding]:
    findings, _ = _scan_markdown_paths(root, paths)
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
        raise GitTrackedScanUnavailable("DOCS_EXPLICIT_PATH_REQUIRED")
    return _tracked_files(root)


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

    try:
        root = args.root.resolve()
    except (OSError, RuntimeError, ValueError):
        sys.stdout.write("docs_consistency_link_sanity=blocked\nreason=DOCS_ROOT_INVALID\n")
        return 2
    try:
        if args.mode == "explicit":
            if not args.path:
                raise GitTrackedScanUnavailable("DOCS_EXPLICIT_PATH_REQUIRED")
            paths = list(args.path)
            known_paths: Iterable[Path | str] | None = None
        else:
            tracked_paths = _paths_for_mode(root, args.mode)
            paths = [path for path in tracked_paths if str(path).lower().endswith(".md")]
            known_paths = tracked_paths
    except GitTrackedScanUnavailable as exc:
        sys.stdout.write(f"docs_consistency_link_sanity=blocked\nreason={exc.reason_code}\n")
        return 2

    findings, scanned_files = _scan_markdown_paths(root, paths, known_paths=known_paths)
    if not findings and scanned_files == 0:
        sys.stdout.write("docs_consistency_link_sanity=blocked\nreason=DOCS_NO_ELIGIBLE_MARKDOWN\nscanned_files=0\n")
        return 2
    if findings:
        for finding in findings:
            sys.stdout.write(
                f"{finding.rule_id}\t{finding.source_path}:{finding.line}\t{finding.target}\t{finding.reason}\n"
            )
        sys.stdout.write(
            f"docs_consistency_link_sanity=fail\nscanned_files={scanned_files}\nfindings={len(findings)}\n"
        )
        return 1

    sys.stdout.write(f"docs_consistency_link_sanity=pass\nscanned_files={scanned_files}\nfindings=0\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

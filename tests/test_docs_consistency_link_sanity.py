from pathlib import Path

import pytest

from automation.quality.docs_consistency_link_sanity import main, scan_markdown_paths
from automation.quality.official_export_index import INDEX_NAME, ExportEntry, _index_bytes, _sha256_bytes


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_official_index(root: Path) -> None:
    entries = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file() and candidate.name != INDEX_NAME):
        content = path.read_bytes()
        entries.append(ExportEntry(path.relative_to(root).as_posix(), len(content), _sha256_bytes(content)))
    (root / INDEX_NAME).write_bytes(_index_bytes(entries))


def test_docs_sanity_accepts_valid_internal_links_and_duplicate_anchors(tmp_path):
    write(
        tmp_path / "docs" / "guide.md",
        "# Overview\n\n## Details\n\n## Details\n\n",
    )
    write(
        tmp_path / "README.md",
        "[overview](docs/guide.md#overview)\n"
        "[first details](docs/guide.md#details)\n"
        "[second details](docs/guide.md#details-1)\n"
        "`docs/guide.md`\n",
    )

    findings = scan_markdown_paths(tmp_path, [Path("README.md"), Path("docs/guide.md")])

    assert findings == []


def test_docs_sanity_reports_missing_file_and_anchor(tmp_path):
    write(tmp_path / "README.md", "# Root\n[missing](docs/missing.md)\n[bad anchor](#missing)\n")

    findings = scan_markdown_paths(tmp_path, [Path("README.md")])
    ids = {finding.rule_id for finding in findings}

    assert "DOCS_MISSING_TARGET" in ids
    assert "DOCS_MISSING_ANCHOR" in ids


def test_docs_sanity_blocks_forbidden_link_targets_without_echoing_raw_path(tmp_path, capsys):
    write(
        tmp_path / "README.md",
        "# Root\n"
        "[local evidence](.qa_local/evidence/task-020/raw.xml)\n"
        "[apk](builds/product-under-test.apk)\n"
        "Literal `.qa_local/evidence/task-020/` policy text is allowed.\n",
    )

    result = main(["--root", str(tmp_path), "--mode", "explicit", "--path", "README.md"])
    output = capsys.readouterr().out

    assert result == 1
    assert "DOCS_FORBIDDEN_LINK_TARGET" in output
    assert "[forbidden-local-target]" in output
    assert ".qa_local/evidence/task-020/raw.xml" not in output
    assert "product-under-test.apk" not in output


def test_docs_sanity_blocks_absolute_windows_unc_and_encoded_traversal(tmp_path):
    write(
        tmp_path / "README.md",
        "# Root\n"
        "[windows](C:/Users/example/secret.md)\n"
        "[unc](//server/share/secret.md)\n"
        "[encoded](docs/%2e%2e/secrets.md)\n",
    )

    findings = scan_markdown_paths(tmp_path, [Path("README.md")])

    assert {finding.rule_id for finding in findings} == {"DOCS_UNSAFE_TARGET_PATH"}
    assert all(finding.target == "[unsafe-local-target]" for finding in findings)


def test_docs_sanity_does_not_crawl_external_links(tmp_path, monkeypatch):
    write(tmp_path / "README.md", "# Root\n[external](https://example.invalid/private?token=value)\n")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("external checks must not run")

    monkeypatch.setattr("automation.quality.docs_consistency_link_sanity.subprocess.run", fail_if_called)

    findings = scan_markdown_paths(tmp_path, [Path("README.md")])

    assert findings == []


def test_docs_sanity_reports_inline_public_missing_reference(tmp_path):
    write(tmp_path / "README.md", "# Root\nSee `docs/missing.md`.\n")

    findings = scan_markdown_paths(tmp_path, [Path("README.md")])

    assert len(findings) == 1
    assert findings[0].rule_id == "DOCS_MISSING_TARGET"


def test_docs_sanity_sanitizes_url_like_and_query_targets(tmp_path, capsys):
    write(
        tmp_path / "README.md",
        "# Root\n"
        "[deeplink](fogplay://private/path?token=raw-secret-value)\n"
        "[query](docs/missing.md?token=raw-secret-value)\n",
    )

    result = main(["--root", str(tmp_path), "--mode", "explicit", "--path", "README.md"])
    output = capsys.readouterr().out

    assert result == 1
    assert "DOCS_FORBIDDEN_LINK_TARGET" in output
    assert "DOCS_MISSING_TARGET" in output
    assert "[forbidden-local-target]" in output
    assert "[query-or-url-like-target]" in output
    assert "fogplay://private/path" not in output
    assert "raw-secret-value" not in output


def test_docs_sanity_checks_reference_style_link_definitions(tmp_path):
    write(tmp_path / "docs" / "guide.md", "# Guide\n\n## Target\n")
    write(
        tmp_path / "README.md",
        "# Root\n"
        "[ok][ok-ref]\n"
        "[bad][bad-ref]\n\n"
        "[ok-ref]: docs/guide.md#target\n"
        "[bad-ref]: docs/guide.md#missing\n",
    )

    findings = scan_markdown_paths(tmp_path, [Path("README.md"), Path("docs/guide.md")])

    assert len(findings) == 1
    assert findings[0].rule_id == "DOCS_MISSING_ANCHOR"


@pytest.mark.parametrize("mode", ["auto", "tracked"])
def test_docs_sanity_git_failure_is_sanitized_blocked(tmp_path, monkeypatch, capsys, mode):
    class FailedGit:
        returncode = 128
        stdout = b""
        stderr = b"fatal: raw/private/path"

    monkeypatch.setattr("automation.quality.docs_consistency_link_sanity.subprocess.run", lambda *a, **k: FailedGit())

    result = main(["--root", str(tmp_path), "--mode", mode])
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == "docs_consistency_link_sanity=blocked\nreason=DOCS_GIT_DISCOVERY_FAILED\n"
    assert captured.err == ""
    assert "raw/private/path" not in captured.out


def test_docs_sanity_auto_git_exception_is_sanitized_blocked(tmp_path, monkeypatch, capsys):
    def raise_private_error(*args, **kwargs):
        raise OSError("private absolute root and executable path")

    monkeypatch.setattr("automation.quality.docs_consistency_link_sanity.subprocess.run", raise_private_error)

    result = main(["--root", str(tmp_path), "--mode", "auto"])
    captured = capsys.readouterr()

    assert result == 2
    assert "reason=DOCS_GIT_DISCOVERY_UNAVAILABLE" in captured.out
    assert "private absolute root" not in captured.out
    assert captured.err == ""


def test_docs_sanity_no_git_uses_only_validated_official_index(tmp_path, monkeypatch, capsys):
    write(tmp_path / "README.md", "# Root\n[guide](docs/guide.md)\n")
    write(tmp_path / "docs/guide.md", "# Guide\n")
    write_official_index(tmp_path)

    class FailedGit:
        returncode = 128
        stdout = b""
        stderr = b"not a git repository"

    monkeypatch.setattr("automation.quality.docs_consistency_link_sanity.subprocess.run", lambda *a, **k: FailedGit())
    result = main(["--root", str(tmp_path), "--mode", "tracked"])
    captured = capsys.readouterr()

    assert result == 0
    assert "docs_consistency_link_sanity=pass" in captured.out
    assert "scanned_files=2" in captured.out
    assert captured.err == ""


def test_docs_sanity_no_git_stale_official_index_blocks(tmp_path, monkeypatch, capsys):
    write(tmp_path / "README.md", "# Root\n")
    write_official_index(tmp_path)
    write(tmp_path / "README.md", "# Changed root\n")

    class FailedGit:
        returncode = 128
        stdout = b""
        stderr = b"not a git repository"

    monkeypatch.setattr("automation.quality.docs_consistency_link_sanity.subprocess.run", lambda *a, **k: FailedGit())
    result = main(["--root", str(tmp_path), "--mode", "auto"])
    captured = capsys.readouterr()

    assert result == 2
    assert "reason=DOCS_PORTABLE_INDEX_INVALID_TREE_" in captured.out
    assert "=pass" not in captured.out
    assert captured.err == ""


def test_docs_sanity_invalid_git_output_is_sanitized_blocked(tmp_path, monkeypatch, capsys):
    class InvalidGitOutput:
        returncode = 0
        stdout = b"docs/\xff.md\0"
        stderr = b""

    monkeypatch.setattr(
        "automation.quality.docs_consistency_link_sanity.subprocess.run",
        lambda *a, **k: InvalidGitOutput(),
    )

    result = main(["--root", str(tmp_path), "--mode", "tracked"])
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == "docs_consistency_link_sanity=blocked\nreason=DOCS_GIT_DISCOVERY_INVALID_OUTPUT\n"
    assert captured.err == ""


def test_docs_sanity_blocks_when_git_has_no_eligible_markdown(tmp_path, monkeypatch, capsys):
    class SuccessfulGit:
        returncode = 0
        stdout = b"pyproject.toml\0"
        stderr = b""

    monkeypatch.setattr("automation.quality.docs_consistency_link_sanity.subprocess.run", lambda *a, **k: SuccessfulGit())

    result = main(["--root", str(tmp_path), "--mode", "tracked"])
    output = capsys.readouterr().out

    assert result == 2
    assert "reason=DOCS_NO_ELIGIBLE_MARKDOWN" in output
    assert "scanned_files=0" in output
    assert "=pass" not in output


def test_docs_sanity_scanned_files_counts_only_validated_markdown(tmp_path, monkeypatch, capsys):
    write(tmp_path / "README.md", "# Root\n")

    class SuccessfulGit:
        returncode = 0
        stdout = b"README.md\0pyproject.toml\0"
        stderr = b""

    monkeypatch.setattr("automation.quality.docs_consistency_link_sanity.subprocess.run", lambda *a, **k: SuccessfulGit())

    result = main(["--root", str(tmp_path), "--mode", "tracked"])
    output = capsys.readouterr().out

    assert result == 0
    assert "scanned_files=1" in output


def test_docs_sanity_rejects_adversarial_scan_paths_before_any_content_read(tmp_path, monkeypatch, capsys):
    write(tmp_path / "README.md", "# must not be read\n")
    raw_secret = "raw-secret-value"
    unsafe_paths = [
        "",
        ".",
        "/absolute/private.md",
        "C:/private/drive.md",
        "//server/private/share.md",
        "docs/../private.md",
        "docs\\..\\private.md",
        "docs/%2e%2e/private.md",
        "docs/%252e%252e/private.md",
        f"docs/guide.md?token={raw_secret}",
        "docs/guide.md#fragment",
        "file:docs/guide.md",
        ".qa_local/private.md",
        "docs/not-markdown.txt",
        "docs/missing.md",
    ]

    def fail_if_read(*args, **kwargs):
        raise AssertionError("no content read is allowed before all paths validate")

    monkeypatch.setattr(Path, "read_text", fail_if_read)
    argv = ["--root", str(tmp_path), "--mode", "explicit", "--path", "README.md"]
    for unsafe_path in unsafe_paths:
        argv.extend(["--path", unsafe_path])

    result = main(argv)
    captured = capsys.readouterr()

    assert result == 1
    assert "DOCS_UNSAFE_SCAN_PATH" in captured.out
    assert "[invalid-scan-path]" in captured.out
    assert raw_secret not in captured.out
    assert "absolute/private" not in captured.out
    assert captured.err == ""


def test_docs_sanity_rejects_directory_and_symlink_without_reading(tmp_path, monkeypatch):
    write(tmp_path / "README.md", "# Root\n")
    (tmp_path / "docs.md").mkdir()
    symlink_path = tmp_path / "linked.md"
    try:
        symlink_path.symlink_to(tmp_path / "README.md")
    except OSError:
        symlink_path = None

    paths = [Path("README.md"), Path("docs.md")]
    if symlink_path is not None:
        paths.append(Path("linked.md"))

    def fail_if_read(*args, **kwargs):
        raise AssertionError("no content read is allowed for a rejected scan set")

    monkeypatch.setattr(Path, "read_text", fail_if_read)
    findings = scan_markdown_paths(tmp_path, paths)

    assert findings
    assert {finding.rule_id for finding in findings} == {"DOCS_UNSAFE_SCAN_PATH"}


def test_docs_sanity_deterministically_rejects_symlink_before_read(tmp_path, monkeypatch):
    write(tmp_path / "README.md", "# Root\n")
    write(tmp_path / "linked.md", "# Sentinel that must not be read\n")
    original_is_symlink = Path.is_symlink

    def report_linked_path_as_symlink(path):
        if path.name == "linked.md":
            return True
        return original_is_symlink(path)

    def fail_if_read(*args, **kwargs):
        raise AssertionError("a rejected symlink scan set must not be read")

    monkeypatch.setattr(Path, "is_symlink", report_linked_path_as_symlink)
    monkeypatch.setattr(Path, "read_text", fail_if_read)

    findings = scan_markdown_paths(tmp_path, [Path("README.md"), Path("linked.md")])

    assert findings
    assert {finding.rule_id for finding in findings} == {"DOCS_UNSAFE_SCAN_PATH"}
    assert {finding.reason for finding in findings} == {"DOCS_SCAN_PATH_SYMLINK"}
    assert {finding.target for finding in findings} == {"[invalid-scan-path]"}


def test_docs_sanity_second_root_resolution_failure_is_sanitized(tmp_path, monkeypatch, capsys):
    write(tmp_path / "README.md", "# Root\n")
    original_resolve = Path.resolve
    root_resolve_calls = 0

    def fail_second_root_resolve(path, *args, **kwargs):
        nonlocal root_resolve_calls
        if path == tmp_path:
            root_resolve_calls += 1
            if root_resolve_calls == 2:
                raise OSError("RAW_PRIVATE_ROOT_MARKER")
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fail_second_root_resolve)

    result = main(["--root", str(tmp_path), "--mode", "explicit", "--path", "README.md"])
    captured = capsys.readouterr()

    assert result == 1
    assert "DOCS_ROOT_INVALID" in captured.out
    assert "[invalid-scan-path]" in captured.out
    assert "RAW_PRIVATE_ROOT_MARKER" not in captured.out
    assert str(tmp_path) not in captured.out
    assert captured.err == ""


def test_docs_sanity_initial_root_value_error_is_sanitized(tmp_path, monkeypatch, capsys):
    raw_root = "RAW_PRIVATE_ROOT_MARKER"

    def reject_root(*args, **kwargs):
        raise ValueError(raw_root)

    monkeypatch.setattr(Path, "resolve", reject_root)

    result = main(["--root", str(tmp_path), "--mode", "explicit", "--path", "README.md"])
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == "docs_consistency_link_sanity=blocked\nreason=DOCS_ROOT_INVALID\n"
    assert raw_root not in captured.out
    assert str(tmp_path) not in captured.out
    assert captured.err == ""


def test_docs_sanity_reads_literal_percent_encoded_filename(tmp_path):
    write(tmp_path / "docs" / "literal%20name.md", "# Literal percent filename\n")
    write(tmp_path / "docs" / "literal name.md", "[must not be read](missing.md)\n")

    findings = scan_markdown_paths(tmp_path, [Path("docs/literal%20name.md")])

    assert findings == []


def test_docs_sanity_read_error_does_not_echo_exception_or_absolute_root(tmp_path, monkeypatch, capsys):
    write(tmp_path / "README.md", "# Root\n")

    def raise_private_error(*args, **kwargs):
        raise OSError(f"failed at {tmp_path} with raw-secret-value")

    monkeypatch.setattr(Path, "read_text", raise_private_error)

    result = main(["--root", str(tmp_path), "--mode", "explicit", "--path", "README.md"])
    captured = capsys.readouterr()

    assert result == 1
    assert "DOCS_READ_ERROR" in captured.out
    assert "[unreadable-markdown]" in captured.out
    assert str(tmp_path) not in captured.out
    assert "raw-secret-value" not in captured.out
    assert captured.err == ""

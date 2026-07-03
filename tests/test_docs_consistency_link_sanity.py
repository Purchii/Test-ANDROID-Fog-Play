from pathlib import Path

from automation.quality.docs_consistency_link_sanity import main, scan_markdown_paths


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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

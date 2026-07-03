from pathlib import Path

from automation.quality.public_repo_safety_scan import main, scan_repo_paths


def finding_ids(paths):
    return {finding.rule_id for finding in scan_repo_paths(paths)}


def test_public_repo_scan_accepts_public_safe_docs_and_examples():
    findings = scan_repo_paths(
        [
            Path("README.md"),
            Path("docs/approvals/qa_user.env.example"),
            Path("docs/qa/reports/task024_native_post_auth_regression.summary.json"),
            Path("tests/test_public_repo_safety_scan.py"),
        ]
    )

    assert findings == []


def test_public_repo_scan_blocks_tracked_local_only_prefixes():
    for path in [
        ".qa_local/evidence/task-020/raw.xml",
        "./.qa_local/evidence/task-020/raw.xml",
        "qa_reverse_analysis/raw/manifest.txt",
        "docs/context/reverse-analysis/raw/private.md",
        "safe_archives/task024.zip",
    ]:
        assert "PUBLIC_PATH_FORBIDDEN_PREFIX" in finding_ids([path])


def test_public_repo_scan_blocks_apk_raw_media_archives_and_signing_material():
    ids = finding_ids(
        [
            "builds/app-under-test.apk",
            "raw/logcat.txt.log",
            "captures/screenrecord.mp4",
            "archives/reverse-analysis.zip",
            "signing/release.keystore",
            "libs/native.so",
            "raw/uiautomator.xml",
        ]
    )

    assert "PUBLIC_PATH_FORBIDDEN_EXTENSION" in ids


def test_public_repo_scan_blocks_local_config_and_secret_filenames():
    for path in ["google-services.json", "local.properties", ".env", "./.env", "runtime.env"]:
        assert "PUBLIC_PATH_FORBIDDEN_FILENAME" in finding_ids([path])


def test_public_repo_scan_blocks_screenshot_like_png_names():
    ids = finding_ids(["docs/qa/screenshots/screenshot_auth.png", "logs/logcat-auth.txt"])

    assert "PUBLIC_PATH_RAW_SCREENSHOT_NAME" in ids
    assert "PUBLIC_PATH_RAW_LOGCAT_NAME" in ids


def test_tree_mode_excludes_ignored_local_evidence_and_reports_no_contents(tmp_path, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "safe.md").write_text("safe\n", encoding="utf-8")
    (tmp_path / ".qa_local" / "evidence").mkdir(parents=True)
    (tmp_path / ".qa_local" / "evidence" / "raw.xml").write_text(
        "local-only evidence path must not be printed\n",
        encoding="utf-8",
    )
    (tmp_path / "qa_reverse_analysis").mkdir()
    (tmp_path / "qa_reverse_analysis" / "raw_manifest.txt").write_text(
        "local reverse analysis must not be printed\n",
        encoding="utf-8",
    )
    (tmp_path / "safe_archives").mkdir()
    (tmp_path / "safe_archives" / "archive.zip").write_text(
        "local archive must not be printed\n",
        encoding="utf-8",
    )
    (tmp_path / "qa_reverse_analysis_documents.zip").write_text(
        "local zip must not be printed\n",
        encoding="utf-8",
    )
    (tmp_path / "capture.log").write_text("raw secret-like contents are not printed\n", encoding="utf-8")

    result = main(["--root", str(tmp_path), "--mode", "tree"])
    output = capsys.readouterr().out

    assert result == 1
    assert "PUBLIC_PATH_FORBIDDEN_EXTENSION" in output
    assert "capture.log" in output
    assert ".qa_local" not in output
    assert "qa_reverse_analysis" not in output
    assert "safe_archives" not in output
    assert "qa_reverse_analysis_documents.zip" not in output
    assert "local-only evidence path must not be printed" not in output
    assert "local reverse analysis must not be printed" not in output
    assert "local archive must not be printed" not in output
    assert "local zip must not be printed" not in output
    assert "raw secret-like contents are not printed" not in output

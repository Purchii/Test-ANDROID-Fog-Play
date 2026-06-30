from pathlib import Path

from automation.quality.full_tree_hygiene_scan import main, scan_paths


def test_hygiene_scan_accepts_clean_text_file(tmp_path):
    path = tmp_path / "clean.md"
    path.write_text("line one\nline two\n", encoding="utf-8")

    assert scan_paths([path]) == []


def test_hygiene_scan_reports_missing_final_newline(tmp_path):
    path = tmp_path / "missing-final-newline.md"
    path.write_text("line one", encoding="utf-8")

    issues = scan_paths([path])

    assert any("missing final newline" in issue for issue in issues)


def test_hygiene_scan_reports_trailing_whitespace(tmp_path):
    path = tmp_path / "trailing.md"
    path.write_text("line one \n", encoding="utf-8")

    issues = scan_paths([path])

    assert any("trailing whitespace" in issue for issue in issues)


def test_hygiene_scan_reports_blank_line_at_eof(tmp_path):
    path = tmp_path / "blank-eof.md"
    path.write_text("line one\n\n", encoding="utf-8")

    issues = scan_paths([path])

    assert any("blank line at EOF" in issue for issue in issues)


def test_auto_mode_falls_back_to_public_safe_tree_when_git_is_unavailable(tmp_path, monkeypatch, capsys):
    def raise_no_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr("automation.quality.full_tree_hygiene_scan.subprocess.run", raise_no_git)
    (tmp_path / "clean.md").write_text("line one\n", encoding="utf-8")

    result = main(["--root", str(tmp_path), "--mode", "auto"])

    assert result == 0
    assert capsys.readouterr().out == "full_tree_hygiene=pass\n"


def test_public_safe_tree_mode_ignores_local_cache_and_build_directories(tmp_path, capsys):
    for directory in [".git", ".qa_local", "__pycache__", ".pytest_cache", "build", "dist"]:
        ignored_dir = tmp_path / directory
        ignored_dir.mkdir()
        (ignored_dir / "bad.md").write_text("bad whitespace \n\n", encoding="utf-8")
    (tmp_path / "clean.md").write_text("line one\n", encoding="utf-8")

    result = main(["--root", str(tmp_path), "--mode", "public-safe-tree"])

    assert result == 0
    assert capsys.readouterr().out == "full_tree_hygiene=pass\n"


def test_auto_fallback_reports_whitespace_missing_newline_and_blank_eof(
    tmp_path, monkeypatch, capsys
):
    def raise_no_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr("automation.quality.full_tree_hygiene_scan.subprocess.run", raise_no_git)
    (tmp_path / "trailing.md").write_text("line one \n", encoding="utf-8")
    (tmp_path / "missing-newline.md").write_text("line one", encoding="utf-8")
    (tmp_path / "blank-eof.md").write_text("line one\n\n", encoding="utf-8")

    result = main(["--root", str(tmp_path), "--mode", "auto"])
    output = capsys.readouterr().out

    assert result == 1
    assert "trailing.md:1: trailing whitespace" in output
    assert "missing-newline.md: missing final newline" in output
    assert "blank-eof.md: blank line at EOF" in output

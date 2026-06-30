from pathlib import Path

from automation.quality.full_tree_hygiene_scan import scan_paths


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

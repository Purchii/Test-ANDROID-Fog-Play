import copy
import json
import os
import stat
import subprocess
import zipfile
from pathlib import Path

import pytest

from automation.quality import official_export_index as subject


def _entry(path: str, content: bytes) -> subject.ExportEntry:
    return subject.ExportEntry(path, len(content), subject._sha256_bytes(content))


def _write_tree(root: Path, files: dict[str, bytes], *, index_entries=None) -> Path:
    for repo_path, content in files.items():
        path = root / repo_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    entries = index_entries or [_entry(path, content) for path, content in sorted(files.items())]
    index = root / subject.INDEX_NAME
    index.write_bytes(subject._index_bytes(entries))
    return index


def _write_zip(path: Path, files: dict[str, bytes], *, index_entries=None, extra_infos=()) -> None:
    entries = index_entries or [_entry(name, content) for name, content in sorted(files.items())]
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
        archive.writestr(subject.INDEX_NAME, subject._index_bytes(entries))
        for info, content in extra_infos:
            archive.writestr(info, content)


def _assert_reason(reason: str, call, *args) -> None:
    with pytest.raises(subject.ExportIndexError) as caught:
        call(*args)
    assert caught.value.reason_code == reason


def test_portable_tree_validates_without_git(tmp_path):
    files = {"README.md": b"safe\n", "automation/check.py": b"print('ok')\n"}
    _write_tree(tmp_path, files)

    subject.validate_tree(tmp_path)


def test_portable_tree_missing_index_fails_closed(tmp_path):
    (tmp_path / "README.md").write_text("safe", encoding="utf-8")

    _assert_reason("INDEX_MISSING", subject.validate_tree, tmp_path)


def test_portable_tree_rejects_stale_hash_and_size(tmp_path):
    _write_tree(tmp_path, {"README.md": b"before"})
    (tmp_path / "README.md").write_bytes(b"after-longer")

    _assert_reason("TREE_SIZE_MISMATCH", subject.validate_tree, tmp_path)


def test_portable_tree_rejects_unindexed_extra_file(tmp_path):
    _write_tree(tmp_path, {"README.md": b"safe"})
    (tmp_path / "extra.txt").write_text("unexpected", encoding="utf-8")

    _assert_reason("TREE_EXTRA_FILE", subject.validate_tree, tmp_path)


def test_malformed_index_is_controlled(tmp_path):
    (tmp_path / subject.INDEX_NAME).write_text("{", encoding="utf-8")

    _assert_reason("INDEX_MALFORMED", subject.validate_tree, tmp_path)


@pytest.mark.parametrize(
    ("bad_path", "reason"),
    [
        ("../escape.txt", "PATH_TRAVERSAL_OR_AMBIGUOUS"),
        ("/absolute.txt", "PATH_ABSOLUTE"),
        ("C:/drive.txt", "PATH_ABSOLUTE"),
        ("line\nfeed.txt", "PATH_CONTROL_CHARACTER"),
        ("encoded%2fescape.txt", "PATH_ENCODED_OR_PERCENT"),
        ("back\\slash.txt", "PATH_BACKSLASH"),
    ],
)
def test_index_rejects_unsafe_paths_before_filesystem_access(tmp_path, bad_path, reason):
    index = {
        "schema_version": subject.SCHEMA_VERSION,
        "algorithm": "sha256",
        "index_path": subject.INDEX_NAME,
        "file_count": 1,
        "files": [{"path": bad_path, "size": 0, "sha256": "0" * 64}],
    }
    (tmp_path / subject.INDEX_NAME).write_text(json.dumps(index), encoding="utf-8")

    _assert_reason(reason, subject.validate_tree, tmp_path)


def test_index_rejects_normalized_collision(tmp_path):
    entries = [_entry("Readme.md", b"one"), _entry("README.md", b"two")]
    (tmp_path / subject.INDEX_NAME).write_bytes(subject._index_bytes(entries))

    _assert_reason("INDEX_NORMALIZED_PATH_COLLISION", subject.validate_tree, tmp_path)


def test_index_rejects_unknown_schema_fields(tmp_path):
    payload = json.loads(subject._index_bytes([_entry("README.md", b"safe")]))
    payload["unexpected"] = True
    (tmp_path / subject.INDEX_NAME).write_text(json.dumps(payload), encoding="utf-8")

    _assert_reason("INDEX_SCHEMA_INVALID", subject.validate_tree, tmp_path)


def test_zip_validates_without_git_or_extraction(tmp_path):
    archive = tmp_path / "official.zip"
    _write_zip(archive, {"README.md": b"safe", "tests/test_safe.py": b"def test_safe(): pass\n"})

    subject.validate_zip(archive)


def test_zip_rejects_missing_index(tmp_path):
    archive = tmp_path / "missing.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("README.md", b"safe")

    _assert_reason("INDEX_MISSING", subject.validate_zip, archive)


def test_zip_rejects_stale_hash(tmp_path):
    archive = tmp_path / "stale.zip"
    expected = [_entry("README.md", b"before")]
    _write_zip(archive, {"README.md": b"after!"}, index_entries=expected)

    _assert_reason("ZIP_HASH_MISMATCH", subject.validate_zip, archive)


def test_zip_rejects_unindexed_extra_file(tmp_path):
    archive = tmp_path / "extra.zip"
    expected = [_entry("README.md", b"safe")]
    _write_zip(archive, {"README.md": b"safe", "extra.txt": b"unexpected"}, index_entries=expected)

    _assert_reason("ZIP_EXTRA_FILE", subject.validate_zip, archive)


def test_zip_rejects_normalized_member_collision(tmp_path):
    archive = tmp_path / "collision.zip"
    expected = [_entry("README.md", b"safe")]
    _write_zip(archive, {"README.md": b"safe", "Readme.md": b"duplicate"}, index_entries=expected)

    _assert_reason("ZIP_NORMALIZED_PATH_COLLISION", subject.validate_zip, archive)


@pytest.mark.parametrize("member", ["../escape.txt", "/absolute.txt", "C:/drive.txt"])
def test_zip_rejects_unsafe_member_names(tmp_path, member):
    archive = tmp_path / "unsafe.zip"
    expected = [_entry("README.md", b"safe")]
    _write_zip(archive, {"README.md": b"safe", member: b"unsafe"}, index_entries=expected)

    with pytest.raises(subject.ExportIndexError) as caught:
        subject.validate_zip(archive)
    assert caught.value.reason_code.startswith("PATH_")


def test_zip_rejects_raw_backslash_member_name(tmp_path):
    archive = tmp_path / "unsafe-backslash.zip"
    expected = [_entry("README.md", b"safe")]
    _write_zip(archive, {"README.md": b"safe", "bad/path.txt": b"unsafe"}, index_entries=expected)
    raw = archive.read_bytes().replace(b"bad/path.txt", b"bad\\path.txt")
    archive.write_bytes(raw)

    _assert_reason("PATH_BACKSLASH", subject.validate_zip, archive)


def test_zip_rejects_symlink_member(tmp_path):
    archive = tmp_path / "symlink.zip"
    symlink = zipfile.ZipInfo("unsafe-link")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
    _write_zip(
        archive,
        {"README.md": b"safe"},
        extra_infos=[(symlink, b"../outside")],
    )

    _assert_reason("ZIP_SYMLINK_REJECTED", subject.validate_zip, archive)


def test_zip_member_count_is_bounded_before_reads(tmp_path, monkeypatch):
    archive = tmp_path / "members.zip"
    _write_zip(archive, {"README.md": b"safe"})
    monkeypatch.setattr(subject, "MAX_ZIP_MEMBERS", 1)

    _assert_reason("ZIP_MEMBER_LIMIT_EXCEEDED", subject.validate_zip, archive)


def test_zip_entry_size_is_bounded_before_reads(tmp_path, monkeypatch):
    archive = tmp_path / "entry-size.zip"
    _write_zip(archive, {"README.md": b"safe"})
    monkeypatch.setattr(subject, "MAX_ZIP_ENTRY_BYTES", 3)

    _assert_reason("ZIP_ENTRY_SIZE_LIMIT_EXCEEDED", subject.validate_zip, archive)


def test_zip_total_uncompressed_size_is_bounded_before_reads(tmp_path, monkeypatch):
    archive = tmp_path / "total-size.zip"
    _write_zip(archive, {"a.txt": b"aaa", "b.txt": b"bbb"})
    monkeypatch.setattr(subject, "MAX_ZIP_TOTAL_BYTES", 5)

    _assert_reason("ZIP_TOTAL_SIZE_LIMIT_EXCEEDED", subject.validate_zip, archive)


def test_zip_compression_ratio_is_bounded_before_reads(tmp_path, monkeypatch):
    archive = tmp_path / "ratio.zip"
    content = b"0" * 4096
    entries = [_entry("compressible.txt", content)]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr("compressible.txt", content)
        output.writestr(subject.INDEX_NAME, subject._index_bytes(entries))
    monkeypatch.setattr(subject, "MAX_ZIP_COMPRESSION_RATIO", 2)

    _assert_reason("ZIP_COMPRESSION_RATIO_LIMIT_EXCEEDED", subject.validate_zip, archive)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _init_git_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "qa@example.invalid")
    _git(root, "config", "user.name", "QA")


def test_create_zip_uses_git_tracked_set_and_does_not_self_hash(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    (repo / "README.md").write_text("tracked\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-qm", "tracked baseline")
    archive = tmp_path / "official.zip"

    subject.create_zip(repo, archive)
    subject.validate_zip(archive)

    with zipfile.ZipFile(archive) as exported:
        names = set(exported.namelist())
        payload = json.loads(exported.read(subject.INDEX_NAME))
    assert names == {"README.md", subject.INDEX_NAME}
    assert all(item["path"] != subject.INDEX_NAME for item in payload["files"])


def test_create_zip_requires_clean_fully_tracked_public_tree(tmp_path):
    _init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("tracked\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    (tmp_path / "untracked.txt").write_text("not governed\n", encoding="utf-8")

    _assert_reason("GIT_WORKTREE_NOT_CLEAN", subject.create_zip, tmp_path, tmp_path.parent / "export.zip")


def test_create_zip_rejects_output_inside_repository(tmp_path):
    _init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("tracked\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-qm", "baseline")

    _assert_reason("ZIP_OUTPUT_INSIDE_ROOT", subject.create_zip, tmp_path, tmp_path / "export.zip")


def test_export_uses_git_blob_bytes_for_crlf_portability(tmp_path):
    _init_git_repo(tmp_path)
    (tmp_path / ".gitattributes").write_text("*.txt text eol=lf\n", encoding="utf-8")
    (tmp_path / "portable.txt").write_bytes(b"line-one\r\nline-two\r\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "baseline")
    _git(tmp_path, "checkout", "--", "portable.txt")
    archive = tmp_path.parent / "portable.zip"

    subject.create_zip(tmp_path, archive)

    committed = subprocess.run(
        ["git", "show", "HEAD:portable.txt"], cwd=tmp_path, check=True, capture_output=True
    ).stdout
    with zipfile.ZipFile(archive) as exported:
        assert exported.read("portable.txt") == committed == b"line-one\nline-two\n"


def test_build_and_validate_index_path_must_be_canonical_inside_root(tmp_path):
    _init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("tracked\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-qm", "baseline")

    _assert_reason(
        "INDEX_PATH_OUTSIDE_ROOT",
        subject._canonical_index_path,
        tmp_path,
        tmp_path.parent / "outside-index.json",
    )


def _create_preservation_repo(root: Path) -> str:
    _init_git_repo(root)
    files = {
        "tasks/TASK_000_history.md": "history\n",
        "tasks/TASK_040_history.md": "history\n",
        "docs/qa/reports/task039.summary.json": "{}\n",
        "docs/qa/reports/report-manifest.json": "{}\n",
        "docs/approvals/local_paths_policy.md": "five local paths\n",
        "docs/approvals/task005_apk_bundle_contract.md": "five apk contract\n",
        "docs/approvals/device_inventory.public_safe.review.json": "{}\n",
    }
    for repo_path, content in files.items():
        path = root / repo_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "base")
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def test_base_ref_preservation_passes_for_additive_changes(tmp_path):
    base_sha = _create_preservation_repo(tmp_path)
    (tmp_path / "tasks/TASK_041_new.md").write_text("new\n", encoding="utf-8")
    _git(tmp_path, "add", ".")

    subject.check_preservation(tmp_path, base_sha)


def test_base_ref_preservation_rejects_history_deletion(tmp_path):
    base_sha = _create_preservation_repo(tmp_path)
    os.remove(tmp_path / "tasks/TASK_000_history.md")

    _assert_reason("HISTORY_FILE_REMOVED", subject.check_preservation, tmp_path, base_sha)


def test_base_ref_preservation_rejects_history_content_change(tmp_path):
    base_sha = _create_preservation_repo(tmp_path)
    (tmp_path / "tasks/TASK_000_history.md").write_text("rewritten\n", encoding="utf-8")

    _assert_reason("HISTORY_FILE_CHANGED", subject.check_preservation, tmp_path, base_sha)


def test_base_ref_allows_report_manifest_authority_refresh(tmp_path):
    base_sha = _create_preservation_repo(tmp_path)
    manifest = tmp_path / "docs/qa/reports/report-manifest.json"
    manifest.write_text("{\"updated\": true}\n", encoding="utf-8")

    subject.check_preservation(tmp_path, base_sha)


def test_base_ref_preservation_rejects_five_apk_contract_change(tmp_path):
    base_sha = _create_preservation_repo(tmp_path)
    (tmp_path / "docs/approvals/task005_apk_bundle_contract.md").write_text("changed\n", encoding="utf-8")

    _assert_reason("PRESERVED_CONTRACT_CHANGED", subject.check_preservation, tmp_path, base_sha)


def test_base_ref_preservation_rejects_tracked_local_only_path(tmp_path):
    base_sha = _create_preservation_repo(tmp_path)
    local = tmp_path / ".qa_local/evidence/raw.txt"
    local.parent.mkdir(parents=True)
    local.write_text("raw", encoding="utf-8")
    _git(tmp_path, "add", "-f", ".qa_local/evidence/raw.txt")

    _assert_reason("LOCAL_ONLY_PATH_TRACKED", subject.check_preservation, tmp_path, base_sha)


def test_base_ref_must_be_exact_full_lowercase_sha(tmp_path):
    _create_preservation_repo(tmp_path)

    _assert_reason("BASE_REF_INVALID", subject.check_preservation, tmp_path, "HEAD")


def test_canonical_epic_index_and_all_catalogs_validate():
    subject.validate_epic(Path.cwd())


def test_epic_index_rejects_dependency_cycle(tmp_path):
    canonical = json.loads(subject.TASK_INDEX_PATH.read_text(encoding="utf-8"))
    broken = copy.deepcopy(canonical)
    broken["tasks"][0]["dependencies"] = ["TASK-055"]
    index = tmp_path / "cycle.json"
    index.write_text(json.dumps(broken), encoding="utf-8")

    _assert_reason("TASK_INDEX_DEPENDENCY_CYCLE", subject.validate_epic, Path.cwd(), index)


def test_cli_failure_is_public_safe_and_stderr_empty(tmp_path, capsys):
    result = subject.main(["validate-tree", "--root", str(tmp_path)])
    captured = capsys.readouterr()

    assert result == 2
    assert captured.err == ""
    assert captured.out == "official_export_index=fail\nreason=INDEX_MISSING\n"

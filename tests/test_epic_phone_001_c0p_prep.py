from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import py_compile
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from automation.phone import epic_phone_001_c0p_prep as prep


HEAD = "1" * 40


def _utc(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, now: datetime) -> tuple[dict, str]:
    monkeypatch.setattr(prep, "REPO_ROOT", tmp_path)
    controller_source = Path("automation/phone/epic_phone_001_runtime_controller.py").read_bytes()
    executor_source = Path("automation/phone/epic_phone_001_c0p_prep.py").read_bytes()
    _write(tmp_path / prep.CONTROLLER_REL, controller_source)
    _write(tmp_path / prep.EXECUTOR_REL, executor_source)
    gitignore = b".qa_local/\n"
    _write(tmp_path / ".gitignore", gitignore)
    _write(tmp_path / ".git/HEAD", b"ref: refs/heads/qa/epic\n")
    _write(tmp_path / ".git/refs/heads/qa/epic", (HEAD + "\n").encode())
    controller_sha = hashlib.sha256(controller_source).hexdigest()
    executor_sha = hashlib.sha256(executor_source).hexdigest()
    candidate = prep.build_candidate(
        repository_head=HEAD,
        controller_source_sha256=controller_sha,
        executor_source_sha256=executor_sha,
        issued_at_utc=_utc(now - timedelta(minutes=1)),
        expires_at_utc=_utc(now + timedelta(minutes=10)),
        passport_expires_at_utc=_utc(now + timedelta(minutes=90)),
        retention_expires_at_utc=_utc(now + timedelta(hours=23)),
    )
    data = prep.canonical_bytes(candidate)
    _write(tmp_path / prep.CANDIDATE_REL, data)
    plan = prep.build_prep_plan(
        data,
        repository_head=HEAD,
        controller_source_sha256=controller_sha,
        executor_source_sha256=executor_sha,
        gitignore_sha256=hashlib.sha256(gitignore).hexdigest(),
        issued_at_utc=_utc(now - timedelta(minutes=1)),
        expires_at_utc=_utc(now + timedelta(minutes=10)),
    )
    plan_data = prep.canonical_bytes(plan)
    _write(tmp_path / prep.PREP_PLAN_REL, plan_data)
    (tmp_path / ".qa_local/evidence").mkdir(parents=True)
    token = prep.GO_PREFIX + hashlib.sha256(plan_data).hexdigest()
    return candidate, token


def _rebind_plan(tmp_path: Path, now: datetime) -> str:
    candidate_data = (tmp_path / prep.CANDIDATE_REL).read_bytes()
    controller_sha = hashlib.sha256((tmp_path / prep.CONTROLLER_REL).read_bytes()).hexdigest()
    executor_sha = hashlib.sha256((tmp_path / prep.EXECUTOR_REL).read_bytes()).hexdigest()
    gitignore_sha = hashlib.sha256((tmp_path / ".gitignore").read_bytes()).hexdigest()
    plan = prep.build_prep_plan(
        candidate_data,
        repository_head=HEAD,
        controller_source_sha256=controller_sha,
        executor_source_sha256=executor_sha,
        gitignore_sha256=gitignore_sha,
        issued_at_utc=_utc(now - timedelta(minutes=1)),
        expires_at_utc=_utc(now + timedelta(minutes=10)),
    )
    data = prep.canonical_bytes(plan)
    (tmp_path / prep.PREP_PLAN_REL).write_bytes(data)
    return prep.GO_PREFIX + hashlib.sha256(data).hexdigest()


def _rewrite_artifact(candidate: dict, index: int) -> None:
    payload = prep.canonical_bytes(candidate["artifacts"][index]["canonical_json"])
    candidate["artifacts"][index]["bytes"] = len(payload)
    candidate["artifacts"][index]["sha256"] = hashlib.sha256(payload).hexdigest()


def _write_candidate_and_rebind(tmp_path: Path, candidate: dict, now: datetime) -> str:
    (tmp_path / prep.CANDIDATE_REL).write_bytes(prep.canonical_bytes(candidate))
    return _rebind_plan(tmp_path, now)


def test_validate_only_does_not_touch_local_or_environment(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(prep, "REPO_ROOT", tmp_path)
    monkeypatch.delenv(prep.GO_ENV, raising=False)
    assert prep.main(["--validate-only"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["execution_requires_literal_security_go"] is True
    assert output["prep_attempt_id"] == "c0p-prep-005"
    assert output["secret_read_max"] == 0
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_unified_prep_budget_counts_host_and_both_public_inputs():
    assert prep.PREP_ATTEMPT_ID == "c0p-prep-005"
    assert prep.AUTHORITY_SET_ROOT_REL.as_posix().endswith("authority-sets/c0p-authority-005")
    assert prep.BUDGET["execution_max"] == 1
    assert prep.BUDGET["subprocess_max"] == 1
    assert prep.BUDGET["host_process_max"] == 1
    assert prep.BUDGET["child_subprocess_max"] == 0
    assert prep.BUDGET["candidate_read_max"] == 1
    assert prep.BUDGET["prep_plan_read_max"] == 1
    assert prep.BUDGET["metadata_path_target_max"] == 32


def test_consumed_attempt_identity_cannot_be_rebound_as_fresh(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    candidate, _token = _repo(tmp_path, monkeypatch, now)
    candidate["prep_attempt_id"] = "c0p-prep-003"
    token = _write_candidate_and_rebind(tmp_path, candidate, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    with pytest.raises(prep.PrepError, match="candidate_fixed_binding_invalid"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_legacy_missing_attempt_identity_candidate_and_plan_are_rejected(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    candidate, _token = _repo(tmp_path, monkeypatch, now)
    fresh_candidate = json.loads(json.dumps(candidate))
    candidate.pop("prep_attempt_id")
    token = _write_candidate_and_rebind(tmp_path, candidate, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    with pytest.raises(prep.PrepError, match="candidate_keyset_invalid"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()

    (tmp_path / prep.CANDIDATE_REL).write_bytes(prep.canonical_bytes(fresh_candidate))
    _rebind_plan(tmp_path, now)
    plan_path = tmp_path / prep.PREP_PLAN_REL
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan.pop("prep_attempt_id")
    data = prep.canonical_bytes(plan)
    plan_path.write_bytes(data)
    monkeypatch.setenv(prep.GO_ENV, prep.GO_PREFIX + hashlib.sha256(data).hexdigest())
    with pytest.raises(prep.PrepError, match="prep_plan_keyset_invalid"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_success_materializes_exact_four_files_without_child_process(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    candidate, token = _repo(tmp_path, monkeypatch, now)
    plan = json.loads((tmp_path / prep.PREP_PLAN_REL).read_text(encoding="utf-8"))
    assert candidate["schema_version"].endswith("-v2")
    assert plan["schema_version"].endswith("-v2")
    assert candidate["prep_attempt_id"] == plan["prep_attempt_id"] == "c0p-prep-005"
    assert candidate["public_aggregate_contract"]["prep_attempt_id"] == "c0p-prep-005"
    assert candidate["attempt_root"] == prep.ATTEMPT_ROOT_REL.as_posix()
    assert candidate["durable_attempt_marker"] == "exclusive_attempt_root_creation_first_mutation"
    assert candidate["failure_policy"].startswith("leave_partial_attempt_root")
    monkeypatch.setenv(prep.GO_ENV, token)
    result = prep.execute_prep(now)
    assert result["status"] == "superseded_validate_only"
    assert result["superseded_by_contour"] == "epic-phone-001-authority-renewal"
    execute_source = Path(prep.__file__).read_text("utf-8").split("def execute_prep", 1)[1].split("def dry_run", 1)[0]
    assert 'open("xb")' not in execute_source and "_mkdir_new_or_existing(" not in execute_source
    assert result["schema_version"].endswith("-v2")
    assert result["prep_attempt_id"] == "c0p-prep-005"
    assert result["directory_target_count"] == 9
    assert result["directory_created_count"] == 0
    assert result["file_created_count"] == 0
    assert result["subprocess_count"] == 1
    assert result["host_process_count"] == 1
    assert result["child_subprocess_count"] == 0
    assert all(result[key] == 0 for key in (
        "secret_read_count", "device_action_count", "application_action_count",
        "network_action_count", "authentication_action_count", "runtime_action_count",
    ))
    assert all(not (tmp_path / artifact["path"]).exists() for artifact in candidate["artifacts"])


def test_literal_go_is_checked_before_local_mutation(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, prep.GO_PREFIX + "0" * 64)
    with pytest.raises(prep.PrepError, match="literal_security_go_invalid"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


@pytest.mark.parametrize("offset", [timedelta(minutes=-20), timedelta(minutes=20)])
def test_stale_or_future_candidate_fails_before_mutation(tmp_path, monkeypatch, offset):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    candidate, _ = _repo(tmp_path, monkeypatch, now)
    candidate["issued_at_utc"] = _utc(now + offset)
    candidate["expires_at_utc"] = _utc(now + offset + timedelta(minutes=5))
    data = prep.canonical_bytes(candidate)
    (tmp_path / prep.CANDIDATE_REL).write_bytes(data)
    monkeypatch.setenv(prep.GO_ENV, _rebind_plan(tmp_path, now))
    with pytest.raises(prep.PrepError, match="candidate_ttl_invalid"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_candidate_duplicate_key_and_oversize_are_rejected():
    with pytest.raises(prep.PrepError, match="candidate_duplicate_key"):
        prep._strict_json(b'{"a":1,"a":2}', "candidate", 100)
    with pytest.raises(prep.PrepError, match="candidate_size_invalid"):
        prep._strict_json(b"x" * 101, "candidate", 100)
    with pytest.raises(prep.PrepError, match="candidate_duplicate_key"):
        prep._strict_json('{"é":1,"e\\u0301":2}'.encode(), "candidate", 100)


def test_noncanonical_candidate_and_plan_are_rejected(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    candidate = json.loads((tmp_path / prep.CANDIDATE_REL).read_text(encoding="utf-8"))
    (tmp_path / prep.CANDIDATE_REL).write_text(json.dumps(candidate, indent=2), encoding="utf-8")
    with pytest.raises(prep.PrepError, match="candidate_not_canonical"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()
    candidate_data = prep.canonical_bytes(candidate)
    (tmp_path / prep.CANDIDATE_REL).write_bytes(candidate_data)
    plan = json.loads((tmp_path / prep.PREP_PLAN_REL).read_text(encoding="utf-8"))
    (tmp_path / prep.PREP_PLAN_REL).write_text(json.dumps(plan, indent=2), encoding="utf-8")
    with pytest.raises(prep.PrepError, match="prep_plan_not_canonical"):
        prep.execute_prep(now)


def test_stale_plan_and_boolean_type_drift_fail_before_mutation(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, _token = _repo(tmp_path, monkeypatch, now)
    plan = json.loads((tmp_path / prep.PREP_PLAN_REL).read_text(encoding="utf-8"))
    plan["issued_at_utc"] = _utc(now - timedelta(hours=1))
    plan["expires_at_utc"] = _utc(now - timedelta(minutes=1))
    data = prep.canonical_bytes(plan)
    (tmp_path / prep.PREP_PLAN_REL).write_bytes(data)
    monkeypatch.setenv(prep.GO_ENV, prep.GO_PREFIX + hashlib.sha256(data).hexdigest())
    with pytest.raises(prep.PrepError, match="prep_plan_ttl_invalid"):
        prep.execute_prep(now)
    plan["issued_at_utc"] = _utc(now - timedelta(minutes=1))
    plan["expires_at_utc"] = _utc(now + timedelta(minutes=5))
    plan["budget"]["execution_max"] = True
    data = prep.canonical_bytes(plan)
    (tmp_path / prep.PREP_PLAN_REL).write_bytes(data)
    monkeypatch.setenv(prep.GO_ENV, prep.GO_PREFIX + hashlib.sha256(data).hexdigest())
    with pytest.raises(prep.PrepError, match="prep_plan_fixed_binding_invalid"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_gitignore_hash_drift_with_rule_still_present_fails(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    (tmp_path / ".gitignore").write_bytes(b".qa_local/\nextra-safe-rule/\n")
    monkeypatch.setenv(prep.GO_ENV, token)
    with pytest.raises(prep.PrepError, match="gitignore_hash_drift"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_fixed_input_ancestor_reparse_and_lexical_escape_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(prep, "REPO_ROOT", tmp_path)
    inside = tmp_path / "docs/qa/phone/input.json"
    _write(inside, b"{}")
    original = prep.Path.is_symlink
    monkeypatch.setattr(prep.Path, "is_symlink", lambda path: path == tmp_path / "docs" or original(path))
    with pytest.raises(prep.PrepError, match="ancestor_reparse"):
        prep._safe_fixed_file(inside, "input", 100)
    monkeypatch.setattr(prep.Path, "is_symlink", original)
    with pytest.raises(prep.PrepError, match="outside_repository|lexical_escape"):
        prep._relative_fixed(tmp_path.parent / "escape.json", "input")


def test_source_contains_no_secret_or_child_process_interface():
    source = Path("automation/phone/epic_phone_001_c0p_prep.py").read_text(encoding="utf-8")
    assert "qa_user.env" not in source
    assert "serial_alias_map" not in source
    assert "import subprocess" not in source
    assert "shell=True" not in source


def test_controller_loader_executes_exact_source_bytes_not_ignored_pyc(tmp_path, monkeypatch):
    monkeypatch.setattr(prep, "REPO_ROOT", tmp_path)
    source = tmp_path / prep.CONTROLLER_REL
    _write(source, b"X = 'EVIL'\n")
    original = source.stat()
    cache = Path(importlib.util.cache_from_source(str(source)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    py_compile.compile(str(source), cfile=str(cache), doraise=True)
    source.write_bytes(b"X = 'SAFE'\n")
    os.utime(source, (original.st_atime, original.st_mtime))
    assert source.stat().st_size == original.st_size
    assert prep._load_controller(hashlib.sha256(source.read_bytes()).hexdigest()).X == "SAFE"


def test_controller_swap_after_binding_cannot_execute_unbound_bytes(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    original_binding = prep._validate_pre_mutation_bindings

    def bind_then_swap(*args, **kwargs):
        original_binding(*args, **kwargs)
        source = tmp_path / prep.CONTROLLER_REL
        source.write_bytes(b"#" * len(source.read_bytes()))

    monkeypatch.setattr(prep, "_validate_pre_mutation_bindings", bind_then_swap)
    with pytest.raises(prep.PrepError, match="controller_executed_source_drift"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_git_directory_reparse_attribute_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(prep, "REPO_ROOT", tmp_path)
    _write(tmp_path / ".git/HEAD", (HEAD + "\n").encode())
    original = Path.lstat

    class ReparseStat:
        def __init__(self, base):
            self.st_mode = base.st_mode
            self.st_file_attributes = prep.REPARSE_ATTRIBUTE | 0x10

    def fake_lstat(path):
        base = original(path)
        return ReparseStat(base) if path == tmp_path / ".git" else base

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(prep.PrepError, match="git_pointer_reparse"):
        prep._read_repository_head()


@pytest.mark.skipif(os.name != "nt", reason="Windows UNC/device namespace contract")
def test_unc_git_metadata_path_is_rejected_before_first_stat(monkeypatch):
    calls = {"count": 0}

    def forbidden_lstat(_path):
        calls["count"] += 1
        raise AssertionError("UNC path must not be touched")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(prep.PrepError, match="remote_or_device_namespace"):
        prep._reject_absolute_reparse_chain(Path(r"\\server\share\repo\.git"), "git_directory")
    assert calls["count"] == 0


def test_detached_and_strict_packed_head_parsing(tmp_path, monkeypatch):
    monkeypatch.setattr(prep, "REPO_ROOT", tmp_path)
    _write(tmp_path / ".git/HEAD", (HEAD + "\n").encode())
    assert prep._read_repository_head() == HEAD
    (tmp_path / ".git/HEAD").write_text("ref: refs/heads/qa/epic\n", encoding="utf-8")
    _write(tmp_path / ".git/packed-refs", (HEAD + " refs/heads/qa/epic\n").encode())
    assert prep._read_repository_head() == HEAD
    (tmp_path / ".git/packed-refs").write_text(
        HEAD + " extra refs/heads/qa/epic\n", encoding="utf-8"
    )
    with pytest.raises(prep.PrepError, match="git_packed_ref_line_invalid"):
        prep._read_repository_head()
    (tmp_path / ".git/packed-refs").write_text(
        HEAD + " refs/heads/qa/epic\n" + "2" * 40 + " refs/heads/qa/epic\n",
        encoding="utf-8",
    )
    with pytest.raises(prep.PrepError, match="git_ref_not_unique"):
        prep._read_repository_head()


def test_linked_worktree_head_is_bounded_to_common_git_metadata(tmp_path, monkeypatch):
    worktree = tmp_path / "worktree"
    common = tmp_path / "main/.git"
    gitdir = common / "worktrees/epic"
    worktree.mkdir(parents=True)
    monkeypatch.setattr(prep, "REPO_ROOT", worktree)
    _write(worktree / ".git", ("gitdir: " + str(gitdir) + "\n").encode())
    _write(gitdir / "commondir", b"../..\n")
    _write(gitdir / "gitdir", (str(worktree / ".git") + "\n").encode())
    _write(gitdir / "HEAD", b"ref: refs/heads/qa/epic\n")
    _write(common / "refs/heads/qa/epic", (HEAD + "\n").encode())
    assert prep._read_repository_head() == HEAD


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("head", "repository_head_drift"),
        ("controller", "controller_source_drift"),
        ("executor", "executor_source_drift"),
        ("gitignore", "ignored_root_contract_missing"),
    ],
)
def test_binding_drift_fails_before_mutation(tmp_path, monkeypatch, mutation, reason):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    if mutation == "head":
        (tmp_path / ".git/refs/heads/qa/epic").write_text("2" * 40 + "\n", encoding="utf-8")
    elif mutation == "controller":
        (tmp_path / prep.CONTROLLER_REL).write_bytes(b"drift")
    elif mutation == "executor":
        (tmp_path / prep.EXECUTOR_REL).write_bytes(b"drift")
    else:
        (tmp_path / ".gitignore").write_text("other/\n", encoding="utf-8")
    with pytest.raises(prep.PrepError, match=reason):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_candidate_payload_drift_invalidates_literal_go(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    candidate, token = _repo(tmp_path, monkeypatch, now)
    candidate["artifacts"][0]["sha256"] = "0" * 64
    (tmp_path / prep.CANDIDATE_REL).write_bytes(prep.canonical_bytes(candidate))
    _rebind_plan(tmp_path, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    with pytest.raises(prep.PrepError, match="literal_security_go_invalid"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_artifact_hash_drift_fails_even_with_candidate_bound_go(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    candidate, _token = _repo(tmp_path, monkeypatch, now)
    candidate["artifacts"][0]["sha256"] = "0" * 64
    data = prep.canonical_bytes(candidate)
    (tmp_path / prep.CANDIDATE_REL).write_bytes(data)
    monkeypatch.setenv(prep.GO_ENV, _rebind_plan(tmp_path, now))
    with pytest.raises(prep.PrepError, match="artifact_bytes_hash_invalid"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_c0p_plan_boolean_integer_type_drift_is_rejected(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    candidate, _token = _repo(tmp_path, monkeypatch, now)
    candidate["artifacts"][0]["canonical_json"]["budget"]["retry_max"] = False
    _rewrite_artifact(candidate, 0)
    monkeypatch.setenv(prep.GO_ENV, _write_candidate_and_rebind(tmp_path, candidate, now))
    with pytest.raises(prep.PrepError, match="c0p_plan_contract_drift"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


@pytest.mark.parametrize(
    ("artifact_index", "issued_offset", "expiry_offset", "reason"),
    [
        (1, timedelta(minutes=1), timedelta(minutes=30), "fixture_passport_ttl_invalid"),
        (2, timedelta(minutes=-20), timedelta(minutes=-1), "target_build_passport_ttl_invalid"),
        (2, timedelta(minutes=1), timedelta(minutes=30), "target_build_passport_ttl_invalid"),
    ],
)
def test_fixture_and_target_passport_current_ttl_is_enforced(
    tmp_path, monkeypatch, artifact_index, issued_offset, expiry_offset, reason
):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    candidate, _token = _repo(tmp_path, monkeypatch, now)
    passport = candidate["artifacts"][artifact_index]["canonical_json"]
    passport["issued_at_utc"] = _utc(now + issued_offset)
    passport["expires_at_utc"] = _utc(now + expiry_offset)
    _rewrite_artifact(candidate, artifact_index)
    monkeypatch.setenv(prep.GO_ENV, _write_candidate_and_rebind(tmp_path, candidate, now))
    with pytest.raises(prep.PrepError, match=reason):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_reparse_ancestor_fails_before_run_root(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    original = Path.lstat

    class ReparseStat:
        def __init__(self, base):
            self.st_mode = base.st_mode
            self.st_file_attributes = prep.REPARSE_ATTRIBUTE | 0x10

    def fake_lstat(path):
        base = original(path)
        return ReparseStat(base) if path == tmp_path / ".qa_local" else base

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(prep.PrepError, match="fixed_ancestor_not_plain_directory"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.RUN_ROOT_REL).exists()


def test_git_commondir_reparse_is_rejected_before_read(tmp_path, monkeypatch):
    worktree = tmp_path / "worktree"
    common = tmp_path / "main/.git"
    gitdir = common / "worktrees/epic"
    worktree.mkdir(parents=True)
    monkeypatch.setattr(prep, "REPO_ROOT", worktree)
    _write(worktree / ".git", ("gitdir: " + str(gitdir) + "\n").encode())
    _write(gitdir / "commondir", b"../..\n")
    original_lstat = Path.lstat
    original_read = Path.read_bytes

    class ReparseStat:
        def __init__(self, base):
            self.st_mode = base.st_mode
            self.st_file_attributes = prep.REPARSE_ATTRIBUTE

    def fake_lstat(path):
        base = original_lstat(path)
        return ReparseStat(base) if path == gitdir / "commondir" else base

    def forbid_read(path):
        if path == gitdir / "commondir":
            raise AssertionError("reparse commondir must not be read")
        return original_read(path)

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    monkeypatch.setattr(Path, "read_bytes", forbid_read)
    with pytest.raises(prep.PrepError, match="git_commondir_not_plain_file"):
        prep._read_repository_head()


def test_loose_ref_reparse_ancestor_is_rejected_before_final_stat(tmp_path, monkeypatch):
    monkeypatch.setattr(prep, "REPO_ROOT", tmp_path)
    _write(tmp_path / ".git/HEAD", b"ref: refs/heads/qa/epic\n")
    _write(tmp_path / ".git/refs/heads/qa/epic", (HEAD + "\n").encode())
    original = Path.lstat
    final = tmp_path / ".git/refs/heads/qa/epic"
    final_touched = {"value": False}

    class ReparseStat:
        def __init__(self, base):
            self.st_mode = base.st_mode
            self.st_file_attributes = prep.REPARSE_ATTRIBUTE | 0x10

    def fake_lstat(path):
        if path == final:
            final_touched["value"] = True
            raise AssertionError("final loose ref must not be touched through reparse ancestor")
        base = original(path)
        return ReparseStat(base) if path == tmp_path / ".git/refs" else base

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(prep.PrepError, match="git_loose_ref_git_metadata_reparse"):
        prep._read_repository_head()
    assert final_touched["value"] is False


def test_preexisting_run_root_is_a_consumed_attempt(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    (tmp_path / prep.RUN_ROOT_REL).mkdir(parents=True)
    monkeypatch.setenv(prep.GO_ENV, token)
    with pytest.raises(prep.PrepError, match="prep_attempt_root_already_consumed"):
        prep.execute_prep(now)


def test_capacity_gate_fails_before_local_mutation(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    monkeypatch.setattr(prep.shutil, "disk_usage", lambda _path: shutil._ntuple_diskusage(1, 1, 0))
    with pytest.raises(prep.PrepError, match="local_capacity_insufficient"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_wall_clock_budget_fails_before_attempt_mutation(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    values = iter((0.0, 301.0))
    monkeypatch.setattr(prep.time, "monotonic", lambda: next(values, 301.0))
    with pytest.raises(prep.PrepError, match="wall_clock_budget_exhausted"):
        prep.execute_prep(now)
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_final_readback_cannot_overrun_wall_clock_and_return_prepared(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    last_path = tmp_path / prep.EVIDENCE_CLEANUP_PASSPORT_REL
    slow_read_completed = {"value": False}
    original_read = Path.read_bytes

    def bounded_read(path):
        value = original_read(path)
        if path == last_path:
            slow_read_completed["value"] = True
        return value

    monkeypatch.setattr(Path, "read_bytes", bounded_read)
    monkeypatch.setattr(
        prep.time, "monotonic", lambda: 301.0 if slow_read_completed["value"] else 0.0
    )
    assert prep.execute_prep(now)["status"] == "superseded_validate_only"
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_shared_parents_missing_fails_before_any_mutation(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    shutil.rmtree(tmp_path / ".qa_local")
    monkeypatch.setenv(prep.GO_ENV, token)
    with pytest.raises(prep.PrepError, match="shared_ignored_parent_missing"):
        prep.execute_prep(now)
    assert not (tmp_path / ".qa_local").exists()


def test_interruption_after_first_mutation_consumes_attempt(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    original = prep._mkdir_new_or_existing

    def interrupt_run_root(path):
        if path == tmp_path / prep.RUN_ROOT_REL:
            raise KeyboardInterrupt()
        return original(path)

    monkeypatch.setattr(prep, "_mkdir_new_or_existing", interrupt_run_root)
    assert prep.execute_prep(now)["status"] == "superseded_validate_only"
    assert not (tmp_path / prep.ATTEMPT_ROOT_REL).exists()


def test_preexisting_output_file_is_a_consumed_attempt(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    _write(tmp_path / prep.C0P_PLAN_REL, b"preexisting")
    monkeypatch.setenv(prep.GO_ENV, token)
    with pytest.raises(prep.PrepError, match="prep_attempt_root_already_consumed"):
        prep.execute_prep(now)


def test_partial_failure_leaves_durable_run_root_and_forbids_retry(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    original_open = Path.open
    calls = {"count": 0}

    def fail_first_artifact(path, *args, **kwargs):
        if args and args[0] == "xb":
            calls["count"] += 1
            raise OSError("sensitive local path")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_first_artifact)
    assert prep.execute_prep(now)["status"] == "superseded_validate_only"
    assert calls["count"] == 0
    assert not (tmp_path / prep.RUN_ROOT_REL).exists()


def test_interruption_after_attempt_creation_leaves_root_and_forbids_retry(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _candidate, token = _repo(tmp_path, monkeypatch, now)
    monkeypatch.setenv(prep.GO_ENV, token)
    original_open = Path.open

    def interrupt_first_artifact(path, *args, **kwargs):
        if args and args[0] == "xb":
            raise KeyboardInterrupt()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", interrupt_first_artifact)
    assert prep.execute_prep(now)["status"] == "superseded_validate_only"
    assert not (tmp_path / prep.RUN_ROOT_REL).exists()


def test_interrupt_and_oserror_are_redacted(capsys, monkeypatch):
    monkeypatch.setattr(prep, "execute_prep", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    assert prep.main(["--execute"]) == 130
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "operation_interrupted_fail_closed\n"
    monkeypatch.setattr(prep, "execute_prep", lambda: (_ for _ in ()).throw(OSError("C:/private/value")))
    assert prep.main(["--execute"]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "local_io_error_fail_closed\n"
    assert "private" not in captured.err and "Traceback" not in captured.err


def test_executor_imports_no_subprocess_module():
    source = Path("automation/phone/epic_phone_001_c0p_prep.py").read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "os.system" not in source
    assert "Popen(" not in source

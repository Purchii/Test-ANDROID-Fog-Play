from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from automation.phone import epic_phone_001_authority_renewal as renewal
from automation.phone import epic_phone_001_authority_renewal_loader as loader
from automation.phone import epic_phone_001_runtime_controller as controller


NOW = datetime(2026, 8, 18, 8, 0, tzinfo=UTC)


def stamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)


def setup_contract(tmp_path: Path, monkeypatch):
    tmp_path.mkdir(parents=True, exist_ok=True); root = tmp_path / "repo"; root.mkdir()
    monkeypatch.setattr(renewal, "REPO_ROOT", root)
    source_bindings = []
    for index, path in enumerate(renewal.SOURCE_PATHS):
        data = f"source-{index}".encode(); write(root / path, data)
        source_bindings.append({"path": path.as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    gitignore = b".qa_local/\n"; write(root / renewal.GITIGNORE_REL, gitignore)
    (root / renewal.SET_PARENT_REL / "c0p-authority-003").mkdir(parents=True)
    write(root / renewal.SET_PARENT_REL / "c0p-authority-003/history.local.json", b"generation003-preserved")
    head = "a" * 40
    issued, plan_expiry = stamp(NOW - timedelta(seconds=5)), stamp(NOW + timedelta(minutes=7))
    authority_expiry, retention = stamp(NOW + timedelta(minutes=8)), stamp(NOW + timedelta(minutes=9))
    candidate = renewal.build_candidate(repository_head=head, source_bindings=source_bindings,
                                         controller_sha256=source_bindings[3]["sha256"], issued_at_utc=issued,
                                         expires_at_utc=plan_expiry, authority_expires_at_utc=authority_expiry,
                                         retention_expires_at_utc=retention,
                                         no_mutator_expires_at_utc=authority_expiry, no_mutator_status="accepted_by_owner")
    candidate_data = renewal.canonical_bytes(candidate); write(root / renewal.CANDIDATE_REL, candidate_data)
    git_binding = {"path": renewal.GITIGNORE_REL.as_posix(), "bytes": len(gitignore), "sha256": hashlib.sha256(gitignore).hexdigest()}
    plan = renewal.build_plan(candidate_data, repository_head=head, source_bindings=source_bindings,
                              gitignore_binding=git_binding, issued_at_utc=issued, expires_at_utc=plan_expiry,
                              no_mutator_expires_at_utc=authority_expiry, no_mutator_status="accepted_by_owner")
    plan_data = renewal.canonical_bytes(plan); write(root / renewal.PLAN_REL, plan_data)
    monkeypatch.setenv(renewal.GO_ENV, renewal.GO_PREFIX + hashlib.sha256(plan_data).hexdigest())
    write(root / ".git/HEAD", (head + "\n").encode())
    monkeypatch.setitem(renewal.__dict__, renewal.DEADLINE_NS_GLOBAL, time.monotonic_ns() + 300_000_000_000)
    monkeypatch.setitem(renewal.__dict__, renewal.BOOTSTRAP_WALL_GLOBAL, NOW)
    monkeypatch.setitem(renewal.__dict__, renewal.LOADER_GO_READ_GLOBAL, 1)
    monkeypatch.setitem(renewal.__dict__, renewal.LOADER_SOURCE_READ_GLOBAL, 1)
    return root, candidate, plan, plan_data


def test_exact_ids_paths_schemas_and_zero_impact_budget():
    assert renewal.CONTOUR_ID == "epic-phone-001-authority-renewal"
    assert renewal.RENEWAL_ID == "authority-renewal-002"
    assert renewal.AUTHORITY_SET_ID == "c0p-authority-004"
    assert renewal.PREP_ATTEMPT_ID == "c0p-prep-004"
    assert renewal.SECURITY_ALIAS == "epic-phone-001-security-c0p-004"
    assert renewal.NO_MUTATOR_ALIAS == "epic-phone-001-owner-authority-renewal-no-mutator-002"
    assert renewal.SET_ROOT_REL.as_posix().endswith("authority-sets/c0p-authority-004")
    assert renewal.MARKER_REL.name == "authority-renewal-002-attempt.local.json"
    assert (renewal.CANDIDATE_SCHEMA, renewal.PLAN_SCHEMA, renewal.ATTEMPT_SCHEMA, renewal.RESULT_SCHEMA) == (
        "epic-phone-001-authority-renewal-candidate-v1", "epic-phone-001-authority-renewal-plan-v1",
        "epic-phone-001-authority-renewal-attempt-v1", "epic-phone-001-authority-renewal-result-v1")
    for key in ("secret_read_max", "serial_read_max", "device_action_max", "application_action_max",
                "network_action_max", "runtime_action_max", "authentication_action_max", "ui_action_max"):
        assert renewal.BUDGET[key] == 0
    with pytest.raises(renewal.RenewalError, match="windows_fixed_local_drive_required"):
        renewal._fixed_local(Path(r"\\server\share\repo"))


def test_candidate_preserves_target_authorization_only_and_task058a_unknown():
    payloads = renewal.build_authority_payloads(repository_head="a" * 40, controller_sha256="b" * 64,
                                                issued_at_utc=stamp(NOW), expires_at_utc=stamp(NOW + timedelta(minutes=8)),
                                                retention_expires_at_utc=stamp(NOW + timedelta(minutes=9)))
    assert [item["schema_version"] for item in payloads] == [renewal.C0P_SCHEMA, renewal.FIXTURE_SCHEMA, renewal.TARGET_SCHEMA, renewal.CLEANUP_SCHEMA]
    target = payloads[2]
    assert target["passport_purpose"] == "authorization_only"
    assert target["task058a_row03_evidence_status"] == "unknown"
    assert target["current_freshness_evidence"] is target["runtime_evidence"] is False
    assert payloads[0] == controller.c0p_plan("a" * 40, "b" * 64, stamp(NOW), stamp(NOW + timedelta(minutes=8)))
    assert payloads[0]["passport_aliases"] == {
        "fixture_authority": "epic-phone-001-fixture-authority-004",
        "target_build": "epic-phone-001-target-build-004",
        "evidence_cleanup": "epic-phone-001-evidence-cleanup-004",
    }
    controller._validate_fixture_passport(payloads[1])
    controller._validate_target_build_passport(payloads[2])
    controller._validate_evidence_cleanup_passport(payloads[3])


def test_final_head_placeholder_and_old_generation_are_rejected():
    with pytest.raises(renewal.RenewalError, match="final_repository_head_required"):
        renewal.build_authority_payloads(repository_head=renewal.REPOSITORY_HEAD_PLACEHOLDER, controller_sha256="b" * 64,
                                         issued_at_utc=stamp(NOW), expires_at_utc=stamp(NOW + timedelta(minutes=8)),
                                         retention_expires_at_utc=stamp(NOW + timedelta(minutes=9)))
    assert all("c0p-authority-004" in path.as_posix() for path in renewal.ARTIFACT_PATHS)
    assert all(path.parent == renewal.SET_ROOT_REL for path in renewal.ARTIFACT_PATHS)


def test_success_create_new_six_files_one_dir_and_category_result(tmp_path, monkeypatch):
    root, _, _, _ = setup_contract(tmp_path, monkeypatch)
    result = renewal.execute(NOW)
    assert result["status"] == "authority_set_materialized"
    assert (root / renewal.MARKER_REL).is_file() and (root / renewal.RESULT_REL).is_file()
    assert all((root / path).is_file() for path in renewal.ARTIFACT_PATHS)
    assert result["file_created_count"] == 6 and result["directory_created_count"] == 1
    assert result["all_secret_serial_device_app_network_runtime_auth_ui_counters"] == 0
    assert result["gitignore_content_read_count"] == 1
    assert result["git_metadata_content_read_count"] == 1
    assert 0 < result["git_metadata_path_target_count"] <= renewal.BUDGET["metadata_path_target_max"]
    assert result["go_env_read_count"] == 2 and result["full_envelope_source_read_count"] == 7
    assert renewal.NO_MUTATOR_SCOPE == loader.NO_MUTATOR_SCOPE
    assert renewal.CANDIDATE_REL.as_posix() in renewal.NO_MUTATOR_SCOPE["public_inputs"]
    assert renewal.PLAN_REL.as_posix() in renewal.NO_MUTATOR_SCOPE["public_inputs"]
    assert "gitdir_HEAD" in renewal.NO_MUTATOR_SCOPE["git_metadata"]
    assert renewal.RESULT_REL.as_posix() in renewal.NO_MUTATOR_SCOPE["new_outputs"]
    assert renewal.SET_PARENT_REL.as_posix() not in renewal.NO_MUTATOR_SCOPE["new_outputs"]
    absolute_deadline = 10_000
    delayed_samples = iter((9_000, 10_001))
    with monkeypatch.context() as deadline_patch:
        deadline_patch.setattr(renewal.time, "monotonic_ns", lambda: next(delayed_samples))
        renewal._check_deadline(absolute_deadline)
        with pytest.raises(renewal.RenewalError, match="wall_clock_budget_exhausted"):
            renewal._check_deadline(absolute_deadline)
    short_root, short_candidate, short_plan, _ = setup_contract(tmp_path / "short", monkeypatch)
    bindings = short_plan["source_bindings"]; short_expiry = stamp(NOW + timedelta(minutes=6))
    rebuilt = renewal.build_candidate(repository_head="a" * 40, source_bindings=bindings,
                                      controller_sha256=bindings[3]["sha256"], issued_at_utc=stamp(NOW - timedelta(seconds=5)),
                                      expires_at_utc=short_plan["expires_at_utc"], authority_expires_at_utc=short_expiry,
                                      retention_expires_at_utc=stamp(NOW + timedelta(minutes=9)),
                                      no_mutator_expires_at_utc=stamp(NOW + timedelta(minutes=8)), no_mutator_status="accepted_by_owner")
    rebuilt_data = renewal.canonical_bytes(rebuilt); write(short_root / renewal.CANDIDATE_REL, rebuilt_data)
    rebuilt_plan = renewal.build_plan(rebuilt_data, repository_head="a" * 40, source_bindings=bindings,
                                       gitignore_binding=short_plan["gitignore_binding"], issued_at_utc=short_plan["issued_at_utc"],
                                       expires_at_utc=short_plan["expires_at_utc"], no_mutator_expires_at_utc=stamp(NOW + timedelta(minutes=8)),
                                       no_mutator_status="accepted_by_owner")
    rebuilt_plan_data = renewal.canonical_bytes(rebuilt_plan); write(short_root / renewal.PLAN_REL, rebuilt_plan_data)
    monkeypatch.setenv(renewal.GO_ENV, renewal.GO_PREFIX + hashlib.sha256(rebuilt_plan_data).hexdigest())
    with pytest.raises(renewal.RenewalError, match="artifact_time_contract_invalid"):
        renewal.execute(NOW)
    assert not (short_root / renewal.MARKER_REL).exists()


def test_existing_generation003_is_never_opened_or_mutated_and_does_not_block_generation004(tmp_path, monkeypatch):
    root, _, _, _ = setup_contract(tmp_path, monkeypatch)
    old_root = root / renewal.SET_PARENT_REL / "c0p-authority-003"
    old_marker = root / renewal.RUN_REL / "authority-renewal-001-attempt.local.json"
    write(old_marker, b"generation003-consumed")

    def snapshot():
        return [(".", old_root.lstat().st_size, old_root.lstat().st_mtime_ns, None)] + [
            (path.relative_to(old_root).as_posix(), path.lstat().st_size, path.lstat().st_mtime_ns,
             path.read_bytes() if path.is_file() else None)
            for path in sorted(old_root.rglob("*"))
        ]

    before = snapshot()
    real_open = renewal.os.open

    def reject_old_content_read(path, *args, **kwargs):
        candidate = Path(path).absolute()
        if candidate == old_marker.absolute() or candidate == old_root.absolute() or old_root.absolute() in candidate.parents:
            raise AssertionError("old_generation_content_read")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(renewal.os, "open", reject_old_content_read)
    result = renewal.execute(NOW)
    assert result["old_authority_content_read_count"] == 0
    assert result["directory_created_count"] == 1
    assert snapshot() == before
    assert old_marker.read_bytes() == b"generation003-consumed"
    assert (root / renewal.SET_ROOT_REL).is_dir()


def test_existing_authority_sets_parent_is_required_before_marker(tmp_path, monkeypatch):
    root, _, _, _ = setup_contract(tmp_path, monkeypatch)
    real_lstat = Path.lstat

    def missing_parent(path):
        if Path(path) == root / renewal.SET_PARENT_REL:
            raise FileNotFoundError
        return real_lstat(path)

    with monkeypatch.context() as missing_patch:
        missing_patch.setattr(Path, "lstat", missing_parent)
        with pytest.raises(renewal.RenewalError, match="path_missing"):
            renewal.execute(NOW)
    assert not (root / renewal.MARKER_REL).exists()

    root, _, _, _ = setup_contract(tmp_path / "wrong-type", monkeypatch)
    regular_info = real_lstat(root / ".git/HEAD")

    def regular_parent(path):
        if Path(path) == root / renewal.SET_PARENT_REL:
            return regular_info
        return real_lstat(path)

    with monkeypatch.context() as type_patch:
        type_patch.setattr(Path, "lstat", regular_parent)
        with pytest.raises(renewal.RenewalError, match="authority_set_parent_invalid"):
            renewal.execute(NOW)
    assert not (root / renewal.MARKER_REL).exists()


def test_marker_is_first_mutation_and_partial_is_preserved(tmp_path, monkeypatch):
    root, _, _, _ = setup_contract(tmp_path, monkeypatch)
    real_mkdir = renewal.os.mkdir
    def fail_first_directory(path):
        if Path(path) == root / renewal.SET_ROOT_REL: raise OSError("injected")
        return real_mkdir(path)
    monkeypatch.setattr(renewal.os, "mkdir", fail_first_directory)
    with pytest.raises(OSError, match="injected"): renewal.execute(NOW)
    assert (root / renewal.MARKER_REL).is_file()
    assert (root / renewal.SET_PARENT_REL).is_dir()
    assert not (root / renewal.SET_ROOT_REL).exists()
    delayed_leaf = root / "deadline-preflight.local.json"
    with monkeypatch.context() as delayed:
        samples = iter((100, 200))
        delayed.setattr(renewal.time, "monotonic_ns", lambda: next(samples))
        with pytest.raises(renewal.RenewalError, match="wall_clock_budget_exhausted"):
            renewal._write_new(delayed_leaf, b"{}", 150)
    assert not delayed_leaf.exists()


def test_replay_and_preexisting_versioned_root_fail_before_new_write(tmp_path, monkeypatch):
    root, _, _, _ = setup_contract(tmp_path, monkeypatch)
    write(root / renewal.MARKER_REL, b"consumed")
    with pytest.raises(renewal.RenewalError, match="renewal_already_consumed"): renewal.execute(NOW)
    mismatch_root, _, _, _ = setup_contract(tmp_path / "head", monkeypatch)
    write(mismatch_root / ".git/HEAD", ("b" * 40 + "\n").encode())
    with pytest.raises(renewal.RenewalError, match="repository_head_binding_invalid"): renewal.execute(NOW)
    assert not (mismatch_root / renewal.MARKER_REL).exists()
    loose_root, _, _, _ = setup_contract(tmp_path / "loose", monkeypatch)
    write(loose_root / ".git/HEAD", b"ref: refs/heads/main\n"); write(loose_root / ".git/refs/heads/main", ("a" * 40 + "\n").encode())
    assert renewal._actual_repository_head()[0] == "a" * 40
    packed_root, _, _, _ = setup_contract(tmp_path / "packed", monkeypatch)
    write(packed_root / ".git/HEAD", b"ref: refs/heads/main\n"); write(packed_root / ".git/packed-refs", ("# pack-refs\n" + "a" * 40 + " refs/heads/main\n").encode())
    assert renewal._actual_repository_head()[0] == "a" * 40
    linked_root, _, _, _ = setup_contract(tmp_path / "linked", monkeypatch)
    import shutil
    shutil.rmtree(linked_root / ".git")
    gitdir = linked_root.parent / "git-meta/worktrees/w1"; common = linked_root.parent / "git-meta"
    write(linked_root / ".git", f"gitdir: {gitdir}\n".encode()); write(gitdir / "HEAD", b"ref: refs/heads/main\n")
    write(gitdir / "commondir", b"../..\n"); write(common / "refs/heads/main", ("a" * 40 + "\n").encode())
    assert renewal._actual_repository_head()[0] == "a" * 40


def test_optional_loose_ref_probe_stops_at_first_missing_component_and_rejects_intermediate_reparse(
    tmp_path, monkeypatch
):
    root, _, _, _ = setup_contract(tmp_path, monkeypatch)
    write(root / ".git/HEAD", b"ref: refs/heads/main\n")
    write(root / ".git/packed-refs", ("a" * 40 + " refs/heads/main\n").encode())
    (root / ".git/refs").mkdir()
    refs = root / ".git/refs"; heads = refs / "heads"; loose = heads / "main"
    real_lstat = Path.lstat; observed = []

    def missing_first(path):
        candidate = Path(path)
        if candidate in (refs, heads, loose): observed.append(candidate)
        if candidate == refs: raise FileNotFoundError
        if candidate in (heads, loose): raise AssertionError("probe_continued_after_missing_component")
        return real_lstat(path)

    with monkeypatch.context() as missing_patch:
        missing_patch.setattr(Path, "lstat", missing_first)
        assert renewal._actual_repository_head()[0] == "a" * 40
    assert observed == [refs]
    assert not (root / renewal.MARKER_REL).exists()

    def intermediate_reparse(path):
        if Path(path) == heads:
            return SimpleNamespace(st_mode=0, st_file_attributes=renewal.REPARSE_ATTRIBUTE)
        return real_lstat(path)

    with monkeypatch.context() as reparse_patch:
        reparse_patch.setattr(Path, "lstat", intermediate_reparse)
        with pytest.raises(renewal.RenewalError, match="git_metadata_reparse"):
            renewal.execute(NOW)
    assert not (root / renewal.MARKER_REL).exists()


@pytest.mark.parametrize("mutation", [
    lambda plan: plan.update(renewal_id="authority-renewal-001"),
    lambda plan: plan.update(authority_set_id="c0p-authority-003"),
    lambda plan: plan.update(prep_attempt_id="c0p-prep-003"),
    lambda plan: plan.update(security_alias="epic-phone-001-security-c0p-003"),
    lambda plan: plan["owner_no_mutator_authority"].update(alias="epic-phone-001-owner-authority-renewal-no-mutator-001"),
    lambda plan: plan["budget"].update(secret_read_max=1),
    lambda plan: plan["artifact_paths"].__setitem__(0, ".qa_local/evidence/epic-phone-001/epic-phone-001-20260816-r01/authority-sets/c0p-authority-003/c0p-plan.local.json"),
])
def test_plan_drift_old_ids_paths_and_nonzero_forbidden_budget_fail(tmp_path, monkeypatch, mutation):
    root, candidate, plan, _ = setup_contract(tmp_path, monkeypatch); mutation(plan)
    data = renewal.canonical_bytes(plan); write(root / renewal.PLAN_REL, data)
    monkeypatch.setenv(renewal.GO_ENV, renewal.GO_PREFIX + hashlib.sha256(data).hexdigest())
    with pytest.raises(renewal.RenewalError, match="plan_contract_drift"): renewal.execute(NOW)
    assert not (root / renewal.MARKER_REL).exists()


def test_no_literal_go_no_self_go_and_no_public_candidate_plan_generation(tmp_path, monkeypatch):
    root, _, _, _ = setup_contract(tmp_path, monkeypatch); monkeypatch.delenv(renewal.GO_ENV)
    with pytest.raises(renewal.RenewalError, match="literal_go_invalid"): renewal.execute(NOW)
    assert not (root / renewal.MARKER_REL).exists()
    source = Path(renewal.__file__).read_text("utf-8")
    assert "os.environ[GO_ENV]" not in source and "write_stdin" not in source
    root, candidate, plan, _ = setup_contract(tmp_path / "owner", monkeypatch)
    candidate["owner_no_mutator_authority"]["status"] = "owner_acceptance_required"
    candidate_data = renewal.canonical_bytes(candidate); write(root / renewal.CANDIDATE_REL, candidate_data)
    plan["owner_no_mutator_authority"]["status"] = "owner_acceptance_required"
    plan["candidate_bytes"], plan["candidate_sha256"] = len(candidate_data), hashlib.sha256(candidate_data).hexdigest()
    plan_data = renewal.canonical_bytes(plan); write(root / renewal.PLAN_REL, plan_data)
    monkeypatch.setenv(renewal.GO_ENV, renewal.GO_PREFIX + hashlib.sha256(plan_data).hexdigest())
    with pytest.raises(renewal.RenewalError, match="owner_no_mutator_authority_required"): renewal.execute(NOW)
    assert not (root / renewal.MARKER_REL).exists()


def test_loader_rejects_old_identity_and_systemexit(tmp_path, monkeypatch):
    root, _, plan, plan_data = setup_contract(tmp_path, monkeypatch)
    monkeypatch.chdir(root); monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(plan_data).hexdigest())
    loaded, binding, raw_loaded = loader._plan(root, NOW)
    assert loaded["authority_set_id"] == "c0p-authority-004" and binding["path"] == renewal.EXECUTOR_REL.as_posix()
    assert raw_loaded == plan_data
    plan["renewal_id"] = "authority-renewal-001"; bad = renewal.canonical_bytes(plan); write(root / renewal.PLAN_REL, bad)
    monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(bad).hexdigest())
    with pytest.raises(ValueError): loader._plan(root, NOW)
    plan["renewal_id"] = renewal.RENEWAL_ID
    plan["owner_no_mutator_authority"]["alias"] = "epic-phone-001-owner-authority-renewal-no-mutator-001"
    old_alias = renewal.canonical_bytes(plan); write(root / renewal.PLAN_REL, old_alias)
    monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(old_alias).hexdigest())
    with pytest.raises(ValueError): loader._plan(root, NOW)
    plan["owner_no_mutator_authority"]["alias"] = renewal.NO_MUTATOR_ALIAS
    plan["owner_no_mutator_authority"]["status"] = "accepted_by_owner"
    plan["budget"]["runtime_action_max"] = False
    nested_bool_drift = renewal.canonical_bytes(plan); write(root / renewal.PLAN_REL, nested_bool_drift)
    monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(nested_bool_drift).hexdigest())
    with pytest.raises(ValueError): loader._plan(root, NOW)
    plan["renewal_id"] = renewal.RENEWAL_ID
    plan["owner_no_mutator_authority"]["status"] = "owner_acceptance_required"
    pending = renewal.canonical_bytes(plan); write(root / renewal.PLAN_REL, pending)
    monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(pending).hexdigest())
    with pytest.raises(ValueError): loader._plan(root, NOW)
    monkeypatch.setattr(loader, "_plan", lambda *args: ({}, {"bytes": 1, "path": renewal.EXECUTOR_REL.as_posix(), "sha256": "a" * 64}, b"{}"))
    monkeypatch.setattr(loader, "_load", lambda *args: (
        b"def main():\n return 0 if isinstance(__authority_renewal_deadline_monotonic_ns__,int) "
        b"and __authority_renewal_bootstrap_wall_utc__.tzinfo is not None and __authority_renewal_plan_bytes__==b'{}' "
        b"and __authority_renewal_loader_go_env_read_count__==1 and __authority_renewal_loader_source_read_count__==1 else 2\n"))
    assert loader.main() == 0
    with monkeypatch.context() as delayed:
        samples = iter((1, 300_000_000_001))
        delayed.setattr(loader.time, "monotonic_ns", lambda: next(samples))
        assert loader.main() == 2
    monkeypatch.setattr(loader, "_load", lambda *args: b"raise SystemExit(0)\n")
    assert loader.main() == 2


def test_loader_reparse_gate_and_no_repo_import_fail_closed(tmp_path, monkeypatch):
    root, _, _, plan_data = setup_contract(tmp_path, monkeypatch)
    monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(plan_data).hexdigest())
    monkeypatch.setattr(loader, "_safe_chain", lambda *args: (_ for _ in ()).throw(ValueError()))
    with pytest.raises(ValueError): loader._plan(root, NOW)
    source = Path(loader.__file__).read_text("utf-8")
    assert "automation.phone" not in source and "dont_write_bytecode = True" in source


def test_budget_exact_materialization_envelope():
    assert renewal.BUDGET == {
        "application_action_max": 0, "authentication_action_max": 0, "candidate_read_max": 1,
        "child_subprocess_max": 0, "concurrency_max": 1, "created_file_readback_max": 6,
        "device_action_max": 0, "directory_create_max": 1, "execution_max": 1, "file_create_max": 6,
        "host_process_max": 1, "metadata_path_target_max": 32, "network_action_max": 0,
        "git_metadata_content_read_max": 4, "gitignore_content_read_max": 1, "go_env_read_max": 2,
        "old_authority_content_read_max": 0, "overwrite_append_delete_rename_max": 0,
        "plan_read_max": 1, "retry_max": 0, "runtime_action_max": 0, "secret_read_max": 0,
        "serial_read_max": 0, "single_file_bytes_max": 8192, "subprocess_max": 1,
        "total_created_bytes_max": 49152, "executor_tracked_source_read_max": 6,
        "loader_executor_source_read_max": 1, "full_envelope_source_read_max": 7, "ui_action_max": 0,
        "wall_clock_seconds_max": 300,
    }

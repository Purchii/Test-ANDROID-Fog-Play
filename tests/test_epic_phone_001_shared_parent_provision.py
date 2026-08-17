from __future__ import annotations

import hashlib
import json
import os
import stat
from types import SimpleNamespace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import automation.phone.epic_phone_001_shared_parent_provision as provision


def _utc(value: datetime) -> str:
    return value.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _repo(tmp_path: Path, monkeypatch, now: datetime, state: str = "both_absent"):
    monkeypatch.setattr(provision, "REPO_ROOT", tmp_path)
    executor = b"fixed executor"
    controller = b"fixed controller"
    gitignore = b".qa_local/\n"
    head_reader = b'def _read_repository_head():\n    return "' + b"a" * 40 + b'"\n'
    executor_path = tmp_path / "executor.py"
    controller_path = tmp_path / provision.CONTROLLER_REL
    gitignore_path = tmp_path / provision.GITIGNORE_REL
    head_reader_path = tmp_path / provision.HEAD_READER_REL
    _write(executor_path, executor)
    _write(controller_path, controller)
    _write(gitignore_path, gitignore)
    _write(head_reader_path, head_reader)
    monkeypatch.setattr(provision, "__file__", str(executor_path))
    if state == "qa_local_present_evidence_absent":
        (tmp_path / ".qa_local").mkdir()
    plan = provision.build_plan(
        repository_head="a" * 40,
        executor_sha256=hashlib.sha256(executor).hexdigest(),
        controller_sha256=hashlib.sha256(controller).hexdigest(),
        head_reader_sha256=hashlib.sha256(head_reader).hexdigest(),
        gitignore_sha256=hashlib.sha256(gitignore).hexdigest(),
        expected_initial_state=state,
        issued_at_utc=_utc(now - timedelta(seconds=10)),
        expires_at_utc=_utc(now + timedelta(minutes=5)),
    )
    data = provision.canonical_bytes(plan)
    monkeypatch.setenv(provision.PLAN_ENV, data.decode())
    monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(data).hexdigest())
    return plan


@pytest.mark.parametrize("state,created,preexisting", [
    ("both_absent", 2, 0),
    ("qa_local_present_evidence_absent", 1, 1),
])
def test_exact_initial_states_prepare_only_fixed_directories(tmp_path, monkeypatch, state, created, preexisting):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    plan = _repo(tmp_path, monkeypatch, now, state)
    result = provision.execute(now)
    assert result["created_directory_count"] == created
    assert result["preexisting_safe_directory_count"] == preexisting
    assert (tmp_path / ".qa_local").is_dir()
    assert (tmp_path / ".qa_local/evidence").is_dir()
    assert not any(path.is_file() for path in (tmp_path / ".qa_local").rglob("*"))
    assert set(result) == {
        "application_action_count", "authentication_action_count",
        "child_subprocess_count", "contour_id", "created_directory_count",
        "device_action_count", "epic_id", "file_create_count",
        "host_executor_invocation_count", "network_action_count",
        "preexisting_safe_directory_count", "run_id", "runtime_action_count",
        "secret_read_count", "serial_map_read_count", "status",
        "subprocess_count",
    }
    assert result["runtime_action_count"] == result["serial_map_read_count"] == 0
    assert plan["budget"]["runtime_action_max"] == 0
    assert set(plan["budget"]) == {
        "application_action_max", "authentication_action_max",
        "child_subprocess_max", "concurrency_max", "content_bytes_write_max",
        "device_action_max", "directory_create_max", "directory_target_count",
        "execution_max", "file_create_max", "git_metadata_read_max",
        "go_env_read_max", "host_process_max", "local_metadata_operation_max",
        "network_action_max", "overwrite_append_delete_rename_max",
        "plan_env_read_max", "retry_max", "runtime_action_max",
        "secret_read_max", "serial_map_read_max", "source_metadata_operation_max",
        "source_read_max", "subprocess_max", "token_or_result_write_max",
        "wall_clock_minutes_max",
    }


def test_initial_state_mismatch_and_both_present_fail_without_mutation(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _repo(tmp_path, monkeypatch, now)
    (tmp_path / ".qa_local").mkdir()
    with pytest.raises(provision.ProvisionError, match="initial_state_mismatch"):
        provision.execute(now)
    (tmp_path / ".qa_local/evidence").mkdir()
    with pytest.raises(provision.ProvisionError, match="shared_parents_already_present"):
        provision.execute(now)


def test_missing_go_and_noncanonical_plan_fail_before_mutation(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    plan = _repo(tmp_path, monkeypatch, now)
    monkeypatch.delenv(provision.GO_ENV)
    with pytest.raises(provision.ProvisionError, match="literal_security_go_invalid"):
        provision.execute(now)
    monkeypatch.setenv(provision.PLAN_ENV, json.dumps(plan, indent=2))
    with pytest.raises(provision.ProvisionError, match="plan_not_canonical"):
        provision.execute(now)
    assert not (tmp_path / ".qa_local").exists()


def test_ttl_hash_ignore_and_bool_integer_drift_fail_closed(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    plan = _repo(tmp_path, monkeypatch, now)
    for mutate, reason in (
        (lambda p: p.update(expires_at_utc=_utc(now + timedelta(minutes=11))), "plan_ttl_invalid"),
        (lambda p: p.update(gitignore_sha256="b" * 64), "gitignore_hash_mismatch"),
        (lambda p: p["budget"].update(retry_max=False), "plan_contract_invalid"),
    ):
        changed = json.loads(json.dumps(plan))
        mutate(changed)
        data = provision.canonical_bytes(changed)
        monkeypatch.setenv(provision.PLAN_ENV, data.decode())
        monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(data).hexdigest())
        with pytest.raises(provision.ProvisionError, match=reason):
            provision.execute(now)
    assert not (tmp_path / ".qa_local").exists()


def test_reparse_or_non_directory_parent_rejected_before_create(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _repo(tmp_path, monkeypatch, now)
    (tmp_path / ".qa_local").write_text("not a directory", encoding="utf-8")
    with pytest.raises(provision.ProvisionError, match="fixed_path_not_directory"):
        provision.execute(now)


def test_reparse_attribute_and_unc_are_rejected_before_follow_stat(tmp_path, monkeypatch):
    metadata = {"source_count": 0, "target_count": 0, "cache": {}}
    reparse = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=provision.REPARSE_ATTRIBUTE)
    monkeypatch.setattr(provision, "_counted_lstat", lambda *_args, **_kwargs: reparse)
    with pytest.raises(provision.ProvisionError, match="fixed_path_reparse"):
        provision._plain_dir_info(tmp_path / ".qa_local", metadata)

    monkeypatch.setattr(provision, "REPO_ROOT", Path(r"\\server\share\repo"))
    monkeypatch.setattr(Path, "lstat", lambda _path: (_ for _ in ()).throw(AssertionError("follow-stat")))
    with pytest.raises(provision.ProvisionError, match="fixed_path_namespace_invalid"):
        provision._classify({"source_count": 0, "target_count": 0, "cache": {}})


def test_bound_source_rejects_reparse_ancestor_before_open(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    plan = _repo(tmp_path, monkeypatch, now)
    original_lstat = Path.lstat
    original_open = Path.open

    def marked_lstat(path):
        info = original_lstat(path)
        if path == tmp_path / "automation":
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_size=info.st_size,
                st_file_attributes=provision.REPARSE_ATTRIBUTE,
            )
        return info

    opened = {"controller": False}

    def guarded_open(path, *args, **kwargs):
        if path == tmp_path / provision.CONTROLLER_REL:
            opened["controller"] = True
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", marked_lstat)
    monkeypatch.setattr(Path, "open", guarded_open)
    with pytest.raises(provision.ProvisionError, match="controller_source_reparse"):
        provision.execute(now)
    assert opened["controller"] is False
    assert plan["repository_head_authority"] == "security_attested_current_head"


def test_duplicate_key_and_metadata_budget_fail_closed(tmp_path, monkeypatch):
    with pytest.raises(provision.ProvisionError, match="plan_duplicate_key"):
        provision._strict_json(b'{"a":1,"a":2}')
    monkeypatch.setattr(Path, "lstat", lambda _path: (_ for _ in ()).throw(AssertionError("lstat")))
    with pytest.raises(provision.ProvisionError, match="target_metadata_budget_exhausted"):
        provision._counted_lstat(
            tmp_path, {"source_count": 0, "target_count": 12, "cache": {}},
            kind="target",
        )


def test_current_head_mismatch_and_reader_failure_fail_before_mutation(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    plan = _repo(tmp_path, monkeypatch, now)
    plan["repository_head"] = "b" * 40
    data = provision.canonical_bytes(plan)
    monkeypatch.setenv(provision.PLAN_ENV, data.decode())
    monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(data).hexdigest())
    with pytest.raises(provision.ProvisionError, match="repository_head_drift"):
        provision.execute(now)
    assert not (tmp_path / ".qa_local").exists()

    with pytest.raises(provision.ProvisionError, match="current_head_read_failed"):
        provision._current_head(b"def _read_repository_head():\n    raise RuntimeError('no git')\n")


@pytest.mark.parametrize(
    "state,swap_call",
    [("both_absent", 3), ("qa_local_present_evidence_absent", 2)],
)
def test_fresh_parent_checkpoint_rejects_swap_before_evidence_create(
    tmp_path, monkeypatch, state, swap_call
):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _repo(tmp_path, monkeypatch, now, state)
    original_lstat = Path.lstat
    calls = {"qa": 0}

    def swapped(path):
        if path == tmp_path / ".qa_local":
            calls["qa"] += 1
            if calls["qa"] == swap_call:
                base = original_lstat(path)
                return SimpleNamespace(
                    st_mode=base.st_mode,
                    st_size=base.st_size,
                    st_file_attributes=provision.REPARSE_ATTRIBUTE,
                )
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", swapped)
    with pytest.raises(provision.ProvisionError, match="fixed_path_reparse"):
        provision.execute(now)
    assert not (tmp_path / ".qa_local/evidence").exists()


def test_deep_json_is_fixed_public_error(monkeypatch, capsys):
    deep = "[" * 3000 + "0" + "]" * 3000
    monkeypatch.setenv(provision.PLAN_ENV, deep)
    monkeypatch.setenv(provision.GO_ENV, "unused")
    assert provision.main(["--execute"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "plan_json_depth_invalid\n"
    assert "Traceback" not in captured.err


def test_deep_dynamic_field_is_fixed_public_error(tmp_path, monkeypatch, capsys):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    plan = _repo(tmp_path, monkeypatch, now)
    nested: object = "x"
    for _ in range(1500):
        nested = [nested]
    plan["repository_head"] = nested
    data = provision.canonical_bytes(plan)
    monkeypatch.setenv(provision.PLAN_ENV, data.decode())
    monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(data).hexdigest())
    assert provision.main(["--execute"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "plan_contract_depth_invalid\n"
    assert "Traceback" not in captured.err


def test_lone_surrogate_is_fixed_public_error(monkeypatch, capsys):
    monkeypatch.setenv(provision.PLAN_ENV, '{"x":"\\ud800"}')
    monkeypatch.setenv(provision.GO_ENV, "unused")
    assert provision.main(["--execute"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "plan_unicode_scalar_invalid\n"
    assert "Traceback" not in captured.err


def test_surrogate_in_plan_environment_is_fixed_public_error(monkeypatch, capsys):
    monkeypatch.setenv(provision.PLAN_ENV, "\ud800")
    monkeypatch.setenv(provision.GO_ENV, "unused")
    assert provision.main(["--execute"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "plan_env_encoding_invalid\n"
    assert "Traceback" not in captured.err


def test_oversized_integer_is_fixed_public_error(monkeypatch, capsys):
    monkeypatch.setenv(provision.PLAN_ENV, '{"x":' + "1" * 5000 + "}")
    monkeypatch.setenv(provision.GO_ENV, "unused")
    assert provision.main(["--execute"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "plan_json_invalid\n"
    assert "Traceback" not in captured.err


def test_collision_after_classification_stops_and_does_not_retry(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _repo(tmp_path, monkeypatch, now)
    original = Path.mkdir
    calls = {"count": 0}

    def collide(path, *args, **kwargs):
        if path == tmp_path / ".qa_local":
            calls["count"] += 1
            raise FileExistsError()
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", collide)
    with pytest.raises(provision.ProvisionError, match="fixed_directory_collision"):
        provision.execute(now)
    assert calls["count"] == 1


def test_interruption_after_first_create_leaves_durable_parent(tmp_path, monkeypatch):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _repo(tmp_path, monkeypatch, now)
    original = Path.mkdir

    def interrupt(path, *args, **kwargs):
        if path == tmp_path / ".qa_local/evidence":
            raise KeyboardInterrupt()
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", interrupt)
    with pytest.raises(KeyboardInterrupt):
        provision.execute(now)
    assert (tmp_path / ".qa_local").is_dir()
    assert not (tmp_path / ".qa_local/evidence").exists()


def test_deadline_and_cli_errors_are_public_safe(tmp_path, monkeypatch, capsys):
    now = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    _repo(tmp_path, monkeypatch, now)
    values = iter((0.0, 121.0))
    monkeypatch.setattr(provision.time, "monotonic", lambda: next(values, 121.0))
    with pytest.raises(provision.ProvisionError, match="wall_clock_budget_exhausted"):
        provision.execute(now)
    monkeypatch.setattr(provision, "execute", lambda: (_ for _ in ()).throw(OSError("C:/private/value")))
    assert provision.main(["--execute"]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "local_io_error_fail_closed\n"
    assert "private" not in captured.err and "Traceback" not in captured.err
    monkeypatch.setattr(provision, "execute", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    assert provision.main(["--execute"]) == 130
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "operation_interrupted_fail_closed\n"


def test_validate_only_is_fixed_and_has_no_local_access(monkeypatch, capsys):
    monkeypatch.setattr(provision, "_classify", lambda _counter: (_ for _ in ()).throw(AssertionError("local")))
    assert provision.main(["--validate-only"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["execution_requires_literal_security_go"] is True
    assert result["secret_device_app_network_auth_runtime_max"] == 0
    assert result["fixed_directory_targets"] == [".qa_local", ".qa_local/evidence"]

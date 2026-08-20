from __future__ import annotations

import hashlib
import inspect
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import automation.phone.epic_phone_001_fixture_interactive_provision as provision
import automation.phone.epic_phone_001_owner_local_fixture_loader as loader
import automation.phone.epic_phone_001_authority_renewal as renewal
import automation.phone.epic_phone_001_c0p_prep as prep
import automation.phone.epic_phone_001_runtime_controller as controller


def _stamp(value: datetime) -> str:
    return value.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)


def _setup(tmp_path: Path, monkeypatch, *, parent_state: str = "present"):
    now = datetime(2026, 8, 18, 4, 30, tzinfo=UTC); tmp_path.mkdir(parents=True, exist_ok=True); root = tmp_path / "repo"; root.mkdir()
    monkeypatch.setattr(provision, "REPO_ROOT", root)
    monkeypatch.setattr(provision, "_fixed_drive", lambda path: None)
    monkeypatch.setattr(provision.time, "monotonic_ns", lambda: 1_000_000_000)
    monkeypatch.setattr(provision, "_utc_now", lambda: now)
    monkeypatch.setattr(provision, "_preflight_real_console", lambda: None)
    monkeypatch.setitem(provision.__dict__, provision.LOADER_GIT_CHECK_GLOBAL, 1)
    monkeypatch.setitem(provision.__dict__, provision.LOADER_GIT_CONTENT_GLOBAL, 1)
    monkeypatch.setitem(provision.__dict__, provision.LOADER_GIT_PATH_GLOBAL, 3)
    sources = {
        provision.EXECUTOR_REL: b"fixed executor", provision.LOADER_REL: b"fixed loader",
        provision.CONTROLLER_REL: b"fixed controller", provision.GITIGNORE_REL: b".qa_local/\n",
    }
    for index, (relative, _) in enumerate(provision.WORKSPACE_ALLOWLIST_CONTRACT):
        sources.setdefault(Path(relative), f"workspace-{index}".encode())
    for path, data in sources.items(): _write(root / path, data)
    _write(root / ".git/HEAD", ("a" * 40 + "\n").encode())
    (root / provision.RUN_REL).mkdir(parents=True)
    if parent_state == "present": (root / provision.DESTINATION_REL.parent).mkdir(parents=True)
    expiry = _stamp(now + timedelta(minutes=8))
    artifacts = renewal.build_authority_payloads(
        repository_head="a" * 40, controller_sha256=hashlib.sha256(sources[provision.CONTROLLER_REL]).hexdigest(),
        issued_at_utc=_stamp(now - timedelta(seconds=5)), expires_at_utc=expiry,
        retention_expires_at_utc=expiry)
    artifact_contracts = (
        ("epic-phone-001-security-c0p-005", "execution_status", "planned_separate_literal_go_required_not_run", "expires_at_utc", expiry),
        ("epic-phone-001-fixture-001", "revoked", False, "expires_at_utc", expiry),
        ("phone-current-001", "target_authorized", True, "expires_at_utc", expiry),
        ("policy_readiness_only", "execution_evidence", False, "retention_expires_at_utc", expiry),
    )
    authority = []
    for path, artifact, contract in zip(provision.AUTHORITY_PATHS, artifacts, artifact_contracts):
        data = provision.canonical_bytes(artifact); _write(root / path, data)
        alias, status_field, status_value, expiry_field, expiry_value = contract
        authority.append({"alias": alias, "bytes": len(data), "embedded_expiry_field": expiry_field,
                          "embedded_expiry_value": expiry_value, "embedded_status_field": status_field,
                          "embedded_status_value": status_value, "path": path.as_posix(),
                          "schema_version": artifact["schema_version"], "sha256": hashlib.sha256(data).hexdigest()})
    workspace = []
    for relative, status in provision.WORKSPACE_ALLOWLIST_CONTRACT:
        data = sources[Path(relative)]
        workspace.append({"bytes": len(data), "path": relative, "sha256": hashlib.sha256(data).hexdigest(), "status": status})
    loader_data = sources[provision.LOADER_REL]
    bootstrap = provision.build_inline_bootstrap(loader_bytes=len(loader_data), loader_sha256=hashlib.sha256(loader_data).hexdigest())
    plan = provision.build_plan(
        executor_bytes=len(sources[provision.EXECUTOR_REL]), executor_sha256=hashlib.sha256(sources[provision.EXECUTOR_REL]).hexdigest(),
        loader_bytes=len(loader_data), loader_sha256=hashlib.sha256(loader_data).hexdigest(),
        inline_bootstrap_bytes=len(bootstrap), inline_bootstrap_sha256=hashlib.sha256(bootstrap).hexdigest(),
        controller_bytes=len(sources[provision.CONTROLLER_REL]), controller_sha256=hashlib.sha256(sources[provision.CONTROLLER_REL]).hexdigest(),
        gitignore_bytes=len(sources[provision.GITIGNORE_REL]), gitignore_sha256=hashlib.sha256(sources[provision.GITIGNORE_REL]).hexdigest(),
        workspace_allowlist=workspace, authority_artifacts=authority, expected_secret_parent_state=parent_state,
        fixture_authority_expires_at_utc=_stamp(now + timedelta(minutes=8)),
        owner_console_expires_at_utc=_stamp(now + timedelta(minutes=8)),
        no_mutator_expires_at_utc=_stamp(now + timedelta(minutes=8)),
        no_mutator_authority_status="confirmed_by_owner",
        cooperative_timeout_expires_at_utc=_stamp(now + timedelta(minutes=8)),
        cooperative_timeout_acceptance_status="accepted_by_owner",
        repository_head="a" * 40,
        issued_at_utc=_stamp(now - timedelta(seconds=5)), expires_at_utc=_stamp(now + timedelta(minutes=5)),
    )
    raw = provision.canonical_bytes(plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode("utf-8")); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    real_fixed_input = provision._read_fixed_input
    def fixed_input(relative, label, maximum=provision.MAX_PLAN):
        if relative == provision.PROVISION_PLAN_REL:
            return os.environ[provision.PLAN_ENV].encode("utf-8")
        if relative == provision.PROVISION_GO_REL:
            plan_raw = os.environ[provision.PLAN_ENV].encode("utf-8")
            current_plan = json.loads(plan_raw)
            go = provision.build_security_go(plan_sha256=hashlib.sha256(plan_raw).hexdigest(),
                                              issued_at_utc=current_plan["issued_at_utc"],
                                              expires_at_utc=current_plan["expires_at_utc"])
            go["literal_go"] = os.environ.get(provision.GO_ENV)
            return provision.canonical_bytes(go)
        return real_fixed_input(relative, label, maximum)
    monkeypatch.setattr(provision, "_read_fixed_input", fixed_input)
    monkeypatch.setenv(provision.BOOTSTRAP_WALL_ENV, _stamp(now)); monkeypatch.setenv(provision.DEADLINE_ENV, str(121_000_000_000))
    monkeypatch.setattr(provision, "_verify_path_acl", lambda path, **kwargs: None)
    return SimpleNamespace(now=now, root=root, plan=plan, bootstrap=bootstrap)


def test_exact_security_literals_and_bootstrap_never_parses_plan():
    bootstrap = provision.build_inline_bootstrap(loader_bytes=10, loader_sha256="a" * 64)
    assert provision.CONTOUR_ID == "epic-phone-001-owner-local-fixture-provision"
    assert provision.SCHEMA == "epic-phone-001-owner-local-fixture-provision-plan-v1"
    assert provision.MARKER_REL.name == "fixture-owner-provision-003-attempt.local.json"
    assert provision.RESULT_REL.name == "fixture-owner-provision-003-result.local.json"
    assert provision.AUTHORITY_SET_REL.as_posix().endswith("authority-sets/c0p-authority-005")
    assert provision.FIXTURE_AUTHORITY_ALIAS == "epic-phone-001-fixture-authority-owner-provision-003"
    assert provision.OWNER_CONSOLE_ALIAS == "epic-phone-001-owner-local-console-entry-003"
    assert provision.NO_MUTATOR_ALIAS == "epic-phone-001-owner-local-provision-no-mutator-003"
    assert provision.COOPERATIVE_TIMEOUT_ALIAS == "epic-phone-001-owner-cooperative-timeout-acceptance-003"
    assert provision.NO_MUTATOR_SCOPE == loader.NO_MUTATOR_SCOPE
    assert "exact_active_loose_ref_or_packed_refs" in provision.NO_MUTATOR_SCOPE["git_metadata"]
    assert provision.GO_PREFIX == "GO_EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION__epic-phone-001-20260816-r01__"
    assert provision.PLAN_ENV.encode() not in bootstrap
    assert b"print(" not in bootstrap
    assert b"='provision'" in bootstrap
    readiness_bootstrap = provision.build_readiness_inline_bootstrap(loader_bytes=10, loader_sha256="a" * 64)
    assert b"='readiness'" in readiness_bootstrap and b"='provision'" not in readiness_bootstrap
    assert provision.PLAN_ENV not in inspect.getsource(provision._read_plan)
    assert provision.GO_ENV not in inspect.getsource(provision._read_plan)
    assert loader.PLAN_ENV not in inspect.getsource(loader._plan)
    assert loader.GO_ENV not in inspect.getsource(loader._plan)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda plan: plan.update(security_alias="epic-phone-001-security-owner-local-fixture-provision-001"),
        lambda plan: plan.update(security_alias="epic-phone-001-security-owner-local-fixture-provision-002"),
        lambda plan: plan["authority_objects"]["fixture_authority"].update(
            alias="epic-phone-001-fixture-authority-owner-provision-001"
        ),
        lambda plan: plan["authority_objects"]["owner_local_console_entry"].update(
            alias="epic-phone-001-owner-local-console-entry-001"
        ),
        lambda plan: plan["authority_objects"]["provision_no_mutator_window"].update(
            alias="epic-phone-001-owner-local-provision-no-mutator-001"
        ),
        lambda plan: plan["authority_objects"]["cooperative_timeout_acceptance"].update(
            alias="epic-phone-001-owner-cooperative-timeout-acceptance-001"
        ),
    ],
)
def test_consumed_provision_aliases_fail_before_marker(tmp_path, monkeypatch, mutation):
    fx = _setup(tmp_path, monkeypatch)
    mutation(fx.plan)
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode())
    monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="plan_contract_invalid"):
        provision.execute(fx.now)
    assert not (fx.root / provision.MARKER_REL).exists()
    _loader_env(fx, monkeypatch, fx.plan)
    with pytest.raises(ValueError):
        loader._plan()


def test_success_marker_before_input_exact_payload_and_aggregate(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch); events = []; inputs = [bytearray(b"0123456789"), bytearray(b"0042")]
    monkeypatch.setitem(provision.__dict__, provision.LOADER_GIT_CHECK_GLOBAL, 1)
    monkeypatch.setitem(provision.__dict__, provision.LOADER_GIT_CONTENT_GLOBAL, 1)
    monkeypatch.setitem(provision.__dict__, provision.LOADER_GIT_PATH_GLOBAL, 3)
    def marker(path, payload, deadline, **kwargs): events.append((path.name, bytes(payload), False)); _write(path, bytes(payload))
    def secure(path, payload, deadline): events.append((path.name, bytes(payload), True)); _write(path, bytes(payload))
    def console(*args):
        assert (fx.root / provision.MARKER_REL).is_file(); events.append(("input", b"", False)); return inputs.pop(0)
    monkeypatch.setattr(provision, "_protected_write_new", marker); monkeypatch.setattr(provision, "_secure_write_new", secure); monkeypatch.setattr(provision, "_read_console_digits", console)
    result = provision.execute(fx.now)
    expected = b"EPIC_PHONE_001_PHONE_SUFFIX=0123456789\nEPIC_PHONE_001_OTP=0042\n"
    assert (fx.root / provision.DESTINATION_REL).read_bytes() == expected
    assert events[0][0] == provision.MARKER_REL.name and events[1][0] == "input"
    assert ("qa_user.env", expected, True) in events
    assert events[-1][0] == provision.RESULT_REL.name
    assert {key: result[key] for key in fx.plan["aggregate_contract"]} == fx.plan["aggregate_contract"] == provision._aggregate(0)
    assert result["git_head_validation_count"] == 2
    assert 0 < result["git_metadata_content_read_count"] <= provision.BUDGET["git_metadata_content_read_max"]
    assert 0 < result["git_metadata_path_target_count"] <= provision.BUDGET["git_metadata_path_target_max"]
    terminal = json.loads((fx.root / provision.RESULT_REL).read_text("utf-8"))
    assert terminal["terminal_state"] == "fixture_provisioned"
    assert terminal["attempt_id"] == "fixture-owner-provision-003"
    assert terminal["result_alias"] == "epic-phone-001-owner-local-fixture-provision-result-003"
    serialized = json.dumps(terminal, sort_keys=True)
    assert "0123456789" not in serialized and "0042" not in serialized
    assert "EPIC_PHONE_001_PHONE_SUFFIX" not in serialized and "EPIC_PHONE_001_OTP" not in serialized


def test_absent_parent_is_created_once_before_destination(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch, parent_state="absent"); created = []
    monkeypatch.setattr(provision, "_secure_mkdir", lambda path, deadline: (path.mkdir(), created.append(path)))
    monkeypatch.setattr(provision, "_protected_write_new", lambda path, payload, deadline, **kwargs: _write(path, bytes(payload)))
    monkeypatch.setattr(provision, "_secure_write_new", lambda path, payload, deadline: _write(path, bytes(payload)))
    answers = iter((bytearray(b"0123456789"), bytearray(b"1234")))
    monkeypatch.setattr(provision, "_read_console_digits", lambda *args: next(answers))
    result = provision.execute(fx.now)
    assert {key: result[key] for key in provision._aggregate(1)} == provision._aggregate(1)
    assert result["git_head_validation_count"] == 2
    assert created == [fx.root / provision.DESTINATION_REL.parent]


@pytest.mark.parametrize("mutation,reason", [
    (lambda plan: plan.update(extra=0), "plan_contract_invalid"),
    (lambda plan: plan["budget"].update(runtime_action_max=False), "plan_contract_invalid"),
    (lambda plan: plan.update(expires_at_utc=plan["issued_at_utc"]), "security_go_expired"),
])
def test_plan_exact_type_extra_and_ttl_fail_before_marker(tmp_path, monkeypatch, mutation, reason):
    fx = _setup(tmp_path, monkeypatch); mutation(fx.plan); raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match=reason): provision.execute(fx.now)
    assert not (fx.root / provision.MARKER_REL).exists()


def test_go_source_authority_and_replay_fail_before_console(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch); monkeypatch.setenv(provision.GO_ENV, "wrong")
    with pytest.raises(provision.ProvisionError, match="security_go_contract_invalid"): provision.execute(fx.now)
    fx = _setup(tmp_path / "source", monkeypatch); (fx.root / provision.CONTROLLER_REL).write_bytes(b"drift")
    with pytest.raises(provision.ProvisionError, match="bound_identity_invalid"): provision.execute(fx.now)
    fx = _setup(tmp_path / "replay", monkeypatch); _write(fx.root / provision.MARKER_REL, b"used")
    with pytest.raises(provision.ProvisionError, match="attempt_consumed"): provision.execute(fx.now)


def test_input_contract_uses_getwch_polling_without_echo_mode_mutation():
    source = Path(provision.__file__).read_text("utf-8")
    assert "msvcrt.getwch()" in source and "msvcrt.kbhit()" in source
    assert "SetConsoleMode" not in source and "getpass" not in source
    assert 'not "0" <= char <= "9"' in source


def test_input_and_payload_buffers_zeroed_on_destination_failure(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch); phone = bytearray(b"0123456789"); otp = bytearray(b"1234")
    answers = iter((phone, otp)); monkeypatch.setattr(provision, "_read_console_digits", lambda *args: next(answers))
    calls = 0
    monkeypatch.setattr(provision, "_protected_write_new", lambda path, payload, deadline, **kwargs: _write(path, bytes(payload)))
    def fail_destination(path, payload, deadline):
        nonlocal calls; calls += 1
        raise provision.ProvisionError("write_failed")
    monkeypatch.setattr(provision, "_secure_write_new", fail_destination)
    with pytest.raises(provision.ProvisionError, match="write_failed"): provision.execute(fx.now)
    assert phone == bytearray(10) and otp == bytearray(4)


def test_forbidden_actions_and_public_output_are_category_only(tmp_path, monkeypatch, capsys):
    fx = _setup(tmp_path, monkeypatch)
    assert fx.plan["budget"]["subprocess_max"] == fx.plan["budget"]["network_action_max"] == 0
    assert fx.plan["budget"]["device_action_max"] == fx.plan["budget"]["runtime_action_max"] == 0
    monkeypatch.setattr(provision, "execute", lambda: provision._aggregate(0))
    assert provision.main() == 0
    stdout = capsys.readouterr().out
    assert stdout == ""
    monkeypatch.setattr(provision, "execute", lambda: (_ for _ in ()).throw(provision.ProvisionError("blocked")))
    assert provision.main() == 2 and capsys.readouterr().out == ""


def test_loader_rejects_extra_plan_and_executor_systemexit(monkeypatch, tmp_path):
    fx = _setup(tmp_path, monkeypatch)
    class FixedDateTime:
        fromisoformat = staticmethod(datetime.fromisoformat)
        now = staticmethod(lambda tz: fx.now)
    monkeypatch.setattr(loader, "datetime", FixedDateTime); monkeypatch.setattr(loader.time, "monotonic_ns", lambda: 1_000_000_000)
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(loader.PLAN_ENV, raw.decode()); monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    monkeypatch.setenv(loader.BOOTSTRAP_WALL_ENV, _stamp(fx.now)); monkeypatch.setenv(loader.DEADLINE_ENV, str(121_000_000_000))
    _loader_env(fx, monkeypatch, fx.plan)
    assert loader._plan()[0]["schema_version"] == provision.SCHEMA
    extra = dict(fx.plan); extra["extra"] = 0; raw = provision.canonical_bytes(extra)
    monkeypatch.setenv(loader.PLAN_ENV, raw.decode()); monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError): loader._plan()
    monkeypatch.setattr(loader, "_plan", lambda: ({"repository_head": "a" * 40, "executor_bytes": 1, "executor_sha256": "a" * 64}, "b" * 64))
    monkeypatch.setattr(loader, "_load_executor", lambda *args: b"raise SystemExit(0)\n")
    assert loader.main() == 2


@pytest.mark.parametrize("shape,expected_content_reads", [
    ("detached", 1), ("loose", 2), ("packed", 2), ("worktree", 4),
])
def test_git_head_reader_accepts_detached_loose_packed_and_worktree(
    tmp_path, monkeypatch, shape, expected_content_reads
):
    fx = _setup(tmp_path, monkeypatch)
    git = fx.root / ".git"
    if shape == "loose":
        _write(git / "HEAD", b"ref: refs/heads/main\n")
        _write(git / "refs/heads/main", ("a" * 40 + "\n").encode())
    elif shape == "packed":
        _write(git / "HEAD", b"ref: refs/heads/main\n")
        _write(git / "packed-refs", ("# pack-refs\n" + "a" * 40 + " refs/heads/main\n").encode())
    elif shape == "worktree":
        common = fx.root / "git-common"
        git.rename(common)
        gitdir = common / "worktrees/w1"
        _write(git, f"gitdir: {gitdir}\n".encode())
        _write(gitdir / "HEAD", b"ref: refs/heads/main\n")
        _write(gitdir / "commondir", b"../..\n")
        _write(common / "refs/heads/main", ("a" * 40 + "\n").encode())
    assert provision._actual_repository_head(fx.root)[:2] == ("a" * 40, expected_content_reads)
    assert loader._actual_repository_head(fx.root)[:2] == ("a" * 40, expected_content_reads)


def test_executor_and_loader_reject_git_head_drift_before_marker_or_executor(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    _write(fx.root / ".git/HEAD", ("b" * 40 + "\n").encode())
    with pytest.raises(provision.ProvisionError, match="repository_head_binding_invalid"):
        provision.execute(fx.now)
    assert not (fx.root / provision.MARKER_REL).exists()
    _loader_env(fx, monkeypatch, fx.plan)
    monkeypatch.chdir(fx.root)
    monkeypatch.setattr(loader, "_load_executor", lambda *args: (_ for _ in ()).throw(AssertionError("executor_loaded")))
    assert loader.main() == 2
    assert not (fx.root / provision.MARKER_REL).exists()


def test_executor_rejects_missing_loader_git_attestation_before_marker(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    monkeypatch.delitem(provision.__dict__, provision.LOADER_GIT_CHECK_GLOBAL, raising=False)
    monkeypatch.delitem(provision.__dict__, provision.LOADER_GIT_CONTENT_GLOBAL, raising=False)
    monkeypatch.delitem(provision.__dict__, provision.LOADER_GIT_PATH_GLOBAL, raising=False)
    with pytest.raises(provision.ProvisionError, match="loader_git_counter_invalid"):
        provision.execute(fx.now)
    assert not (fx.root / provision.MARKER_REL).exists()

def test_git_head_reader_rejects_reparse_gate_and_unc(monkeypatch, tmp_path):
    fx = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(provision, "_safe_absolute_chain", lambda *args: (_ for _ in ()).throw(provision.ProvisionError("git_metadata_reparse")))
    with pytest.raises(provision.ProvisionError, match="git_metadata_reparse"):
        provision._actual_repository_head(fx.root)
    with pytest.raises(ValueError):
        loader._fixed_drive(Path(r"\\server\share\repo"))


def test_optional_loose_ref_component_probe_is_bounded_and_fail_closed_before_marker_or_executor(
    tmp_path, monkeypatch
):
    fx = _setup(tmp_path, monkeypatch)
    _write(fx.root / ".git/HEAD", b"ref: refs/heads/main\n")
    _write(fx.root / ".git/packed-refs", ("a" * 40 + " refs/heads/main\n").encode())
    (fx.root / ".git/refs").mkdir()
    refs = fx.root / ".git/refs"; heads = refs / "heads"; loose = heads / "main"
    real_lstat = Path.lstat; observed = []

    def missing_first(path):
        candidate = Path(path)
        if candidate in (refs, heads, loose): observed.append(candidate)
        if candidate == refs: raise FileNotFoundError
        if candidate in (heads, loose): raise AssertionError("probe_continued_after_missing_component")
        return real_lstat(path)

    with monkeypatch.context() as missing_patch:
        missing_patch.setattr(Path, "lstat", missing_first)
        assert provision._actual_repository_head(fx.root)[0] == "a" * 40
        assert loader._actual_repository_head(fx.root)[0] == "a" * 40
    assert observed == [refs, refs]
    assert not (fx.root / provision.MARKER_REL).exists()

    def intermediate_reparse(path):
        if Path(path) == heads:
            return SimpleNamespace(st_mode=0, st_file_attributes=provision.REPARSE_ATTRIBUTE)
        return real_lstat(path)

    with monkeypatch.context() as reparse_patch:
        reparse_patch.setattr(Path, "lstat", intermediate_reparse)
        with pytest.raises(provision.ProvisionError, match="git_metadata_reparse"):
            provision.execute(fx.now)
        _loader_env(fx, reparse_patch, fx.plan)
        reparse_patch.chdir(fx.root)
        reparse_patch.setattr(loader, "_load_executor", lambda *args: (_ for _ in ()).throw(AssertionError("executor_loaded")))
        assert loader.main() == 2
    assert not (fx.root / provision.MARKER_REL).exists()


def test_loader_binds_head_and_injects_exact_git_counters_before_executor(monkeypatch):
    plan = {"repository_head": "a" * 40, "executor_bytes": 1, "executor_sha256": "b" * 64}
    monkeypatch.setattr(loader, "_plan", lambda: (plan, "c" * 64))
    monkeypatch.setattr(loader, "_actual_repository_head", lambda root: ("a" * 40, 2, 5))
    source = (
        b"def main():\n"
        b" return 0 if __owner_fixture_loader_git_head_validation_count__==1 "
        b"and __owner_fixture_loader_git_metadata_content_read_count__==2 "
        b"and __owner_fixture_loader_git_metadata_path_target_count__==5 else 2\n"
    )
    monkeypatch.setattr(loader, "_load_executor", lambda *args: source)
    monkeypatch.setattr(loader, "_provision_attempt_consumed", lambda digest: False)
    monkeypatch.setenv(loader.READINESS_MODE_ENV, "provision")
    monkeypatch.setenv(loader.DEADLINE_ENV, "999999999999999999")
    success = provision.canonical_bytes(provision._terminal_result(
        "c" * 64, terminal_state="fixture_provisioned", exit_category="success",
        directory_created=0, execution_stage="terminal_result_finalization")) + b"\n"
    monkeypatch.setattr(loader, "_load_fixed_input", lambda *args: success)
    assert loader.main() == 0
    monkeypatch.setattr(loader, "_actual_repository_head", lambda root: ("b" * 40, 1, 3))
    monkeypatch.setattr(loader, "_load_executor", lambda *args: (_ for _ in ()).throw(AssertionError("executor_loaded")))
    assert loader.main() == 2
    assert loader.BUDGET["subprocess_max"] == 0


def test_acl_createfile_same_handle_flush_readback_and_protected_check_are_mandatory():
    source = Path(provision.__file__).read_text("utf-8")
    for token in ("CreateFileW", "CREATE", "WriteFile", "FlushFileBuffers", "SetFilePointerEx", "ReadFile", "GetSecurityInfo", "GetSecurityDescriptorControl"):
        assert token in source
    assert "0x1000" in source and "D:P(A;;FA;;;" in source


def _loader_env(fx, monkeypatch, plan):
    class FixedDateTime:
        fromisoformat = staticmethod(datetime.fromisoformat)
        now = staticmethod(lambda tz: fx.now)
    monkeypatch.setattr(loader, "datetime", FixedDateTime); monkeypatch.setattr(loader.time, "monotonic_ns", lambda: 1_000_000_000)
    raw = provision.canonical_bytes(plan)
    monkeypatch.setenv(loader.PLAN_ENV, raw.decode()); monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    real_load = loader._load_fixed_input
    def fixed_input(path, maximum):
        if str(path).endswith(loader.PLAN_REL.replace("/", os.sep)):
            return os.environ[loader.PLAN_ENV].encode("utf-8")
        if str(path).endswith(loader.SECURITY_GO_REL.replace("/", os.sep)):
            plan_raw = os.environ[loader.PLAN_ENV].encode("utf-8")
            current_plan = json.loads(plan_raw)
            go = provision.build_security_go(plan_sha256=hashlib.sha256(plan_raw).hexdigest(),
                                              issued_at_utc=current_plan["issued_at_utc"],
                                              expires_at_utc=current_plan["expires_at_utc"])
            go["literal_go"] = os.environ.get(loader.GO_ENV)
            return provision.canonical_bytes(go)
        return real_load(path, maximum)
    monkeypatch.setattr(loader, "_load_fixed_input", fixed_input)
    monkeypatch.setenv(loader.BOOTSTRAP_WALL_ENV, _stamp(fx.now)); monkeypatch.setenv(loader.DEADLINE_ENV, str(121_000_000_000))


@pytest.mark.parametrize("mutate", [
    lambda plan: plan["budget"].update(runtime_action_max=False),
    lambda plan: plan["aggregate_contract"].update(runtime_action_count=False),
    lambda plan: plan["authority_objects"]["fixture_authority"].update(status="unknown"),
    lambda plan: plan["authority_artifacts"][1].update(embedded_status_value=True),
    lambda plan: plan["workspace_allowlist"].append({"path": "docs\\escape", "status": "??", "bytes": 1, "sha256": "a" * 64}),
])
def test_anomaly056_loader_exact_rejects_nested_plan_drift(tmp_path, monkeypatch, mutate):
    fx = _setup(tmp_path, monkeypatch); mutate(fx.plan); _loader_env(fx, monkeypatch, fx.plan)
    with pytest.raises(ValueError): loader._plan()


@pytest.mark.parametrize("bad_path", ["../escape", "./escape", "C:/escape", "/absolute", "a\\b", "a:b"])
def test_anomaly056_workspace_path_rejected_before_join(tmp_path, monkeypatch, bad_path):
    fx = _setup(tmp_path, monkeypatch); fx.plan["workspace_allowlist"].append(
        {"path": bad_path, "status": "??", "bytes": 1, "sha256": "a" * 64})
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="workspace_allowlist_invalid"): provision.execute(fx.now)


def test_anomaly056_authority_wrapper_cannot_relabel_embedded_expiry_or_status(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    fx.plan["authority_artifacts"][1]["embedded_expiry_value"] = _stamp(fx.now + timedelta(minutes=7))
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="authority_cross_binding_invalid"): provision.execute(fx.now)
    mutations = (
        (0, lambda value: value.update(repository_head="b" * 40)),
        (0, lambda value: value.update(controller_source_sha256=True)),
        (0, lambda value: value["value_handling"].update(print=0)),
        (0, lambda value: value["budget"].update(network_action_max=False)),
        (0, lambda value: value["budget"].update(secret_source_read_max=True)),
        (1, lambda value: value.pop("allowed_scope")),
        (1, lambda value: value.update(synthetic_test_only=1)),
        (2, lambda value: value.update(task058a_row03_evidence_status="confirmed")),
        (3, lambda value: value.update(forbidden_action_count=False)),
        (3, lambda value: value.update(soft_bytes_max=True)),
        (3, lambda value: value.update(cleanup_sequence=False)),
    )
    for number, (index, mutate) in enumerate(mutations):
        case = _setup(tmp_path / f"semantic-{number}", monkeypatch)
        artifact_path = case.root / provision.AUTHORITY_PATHS[index]
        artifact = json.loads(artifact_path.read_text("utf-8")); mutate(artifact)
        data = provision.canonical_bytes(artifact); _write(artifact_path, data)
        case.plan["authority_artifacts"][index].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        plan_data = provision.canonical_bytes(case.plan)
        monkeypatch.setenv(provision.PLAN_ENV, plan_data.decode())
        monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(plan_data).hexdigest())
        with pytest.raises(provision.ProvisionError, match="authority_v2_semantic_invalid"):
            provision.execute(case.now)
        assert not (case.root / provision.MARKER_REL).exists()


def test_anomaly057_failed_console_input_zeroes_internal_buffer_and_backspace_overwrites(monkeypatch):
    instances = []
    class TrackingBytearray(bytearray):
        def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); instances.append(self)
    chars = iter(("1", "2", "\b", "x"))
    fake = SimpleNamespace(kbhit=lambda: True, getwch=lambda: next(chars))
    monkeypatch.setattr(provision, "bytearray", TrackingBytearray, raising=False)
    monkeypatch.setattr(provision, "_real_console_api", lambda: fake)
    monkeypatch.setattr(provision.time, "monotonic_ns", lambda: 1)
    with pytest.raises(provision.ProvisionError, match="input_contract_invalid"):
        provision._read_console_digits(4, 8, 100, [0], "Prompt: ")
    assert instances and instances[0] == bytearray(b"\0")


def test_anomaly057_secret_write_uses_mutable_view_and_all_readback_paths_zero():
    source = Path(provision.__file__).read_text("utf-8")
    assert "from_buffer(payload)" in source
    assert "payload[offset:]" not in source
    assert "from_buffer_copy(payload[offset:])" not in source
    assert "if isinstance(readback, bytearray)" in source
    assert "result[-1] = 0" in source


def test_anomaly058_console_preflight_marker_first_mutation_then_optional_directory(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch, parent_state="absent"); events = []
    monkeypatch.setattr(provision, "_preflight_real_console", lambda: events.append("console"))
    monkeypatch.setattr(provision, "_protected_write_new", lambda path, payload, deadline, **kwargs: (events.append("marker"), _write(path, bytes(payload))))
    monkeypatch.setattr(provision, "_secure_mkdir", lambda path, deadline: (events.append("mkdir"), path.mkdir()))
    monkeypatch.setattr(provision, "_verify_path_acl", lambda path, **kwargs: None)
    answers = iter((bytearray(b"0123456789"), bytearray(b"1234")))
    monkeypatch.setattr(provision, "_read_console_digits", lambda *args: next(answers))
    monkeypatch.setattr(provision, "_secure_write_new", lambda path, payload, deadline: events.append("destination"))
    provision.execute(fx.now)
    assert events[:3] == ["console", "marker", "mkdir"] and "destination" in events
    assert events[-1] == "marker"  # durable terminal result is the final create-new write


def test_anomaly058_acl_marker_and_deadline_contract_are_exact():
    source = Path(provision.__file__).read_text("utf-8")
    assert "_protected_write_new(marker" in source
    assert "for kind in ((22,) if exact_secret else (22, 26))" in source
    assert "acl_exact_ace_count_invalid" in source and "acl_required_principal_missing" in source
    assert source.count("_check_deadline(deadline_ns)") >= 12
    assert provision.BUDGET["acl_create_max"] == 4 and provision.BUDGET["acl_check_max"] == 6
    assert provision.BUDGET["console_prompt_write_max"] == 2
    assert provision.BUDGET["console_separator_write_max"] == 2
    assert provision.BUDGET["bootstrap_env_write_max"] == 3


def test_anomaly059_secret_parent_uses_exact_current_user_and_system_acl(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch); checks = []
    monkeypatch.setattr(provision, "_verify_path_acl", lambda path, **kwargs: checks.append((path, kwargs["exact_secret"])))
    monkeypatch.setattr(provision, "_protected_write_new", lambda path, payload, deadline, **kwargs: _write(path, bytes(payload)))
    answers = iter((bytearray(b"0123456789"), bytearray(b"1234")))
    monkeypatch.setattr(provision, "_read_console_digits", lambda *args: next(answers))
    monkeypatch.setattr(provision, "_secure_write_new", lambda path, payload, deadline: None)
    provision.execute(fx.now)
    assert checks == [(fx.root / provision.RUN_REL, False), (fx.root / provision.DESTINATION_REL.parent, True)]
    source = inspect.getsource(provision._verify_handle_acl)
    assert "info.AceCount != 2" in source and "acl_owner_invalid" in source
    assert "for kind in ((22,) if exact_secret else (22, 26))" in source
    assert "header[1] != 0 or mask != 0x001F01FF" in source
    assert "acl_exact_order_invalid" in source and "acl_exact_type_invalid" in source


def test_anomaly060_destination_acl_is_exactly_checked_before_and_after_secret_write():
    source = inspect.getsource(provision._protected_write_new)
    first = source.index("_verify_handle_acl(handle, exact_secret=True)")
    write = source.index("_write_flush_readback(handle, payload, deadline_ns)")
    second = source.index("_verify_handle_acl(handle, exact_secret=True)", first + 1)
    assert first < write < second
    handle_source = inspect.getsource(provision._new_file_handle)
    assert "0xC0000000, 0, security_attributes, CREATE_NEW, 0x80000080" in handle_source


def test_anomaly061_embedded_authority_expiry_covers_plan_and_runtime(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    short = _stamp(fx.now + timedelta(seconds=90))
    artifact = dict(fx.plan["authority_artifacts"][1])
    artifact = renewal.build_authority_payloads(
        repository_head="a" * 40, controller_sha256=fx.plan["controller_sha256"],
        issued_at_utc=_stamp(fx.now - timedelta(seconds=5)), expires_at_utc=short,
        retention_expires_at_utc=_stamp(fx.now + timedelta(minutes=8)))[1]
    data = provision.canonical_bytes(artifact); _write(fx.root / provision.AUTHORITY_PATHS[1], data)
    fx.plan["authority_artifacts"][1].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), embedded_expiry_value=short)
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="authority_cross_binding_invalid"):
        provision.execute(fx.now)
    _loader_env(fx, monkeypatch, fx.plan)
    with pytest.raises(ValueError): loader._plan()


def test_anomaly062_deadline_brackets_console_and_acl_and_budget_is_explicit():
    execute_source = inspect.getsource(provision.execute)
    input_source = inspect.getsource(provision._read_console_digits)
    assert "_check_deadline(operation_deadline_ns); _preflight_real_console(); _check_deadline(operation_deadline_ns)" in execute_source
    assert "_check_deadline(deadline_ns)\n    msvcrt = _real_console_api()\n    _check_deadline(deadline_ns)" in input_source
    assert execute_source.count("_verify_path_acl") == 3
    assert provision.BUDGET["console_api_validation_max"] == 3


def test_anomaly063_marker_protected_owner_authority_and_cooperative_timeout(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    fx.plan["authority_objects"]["provision_no_mutator_window"]["status"] = "owner_confirmation_required"
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="owner_no_mutator_authority_required"):
        provision.execute(fx.now)
    source = inspect.getsource(provision.execute)
    assert "_protected_provision_write_new(marker, marker_payload, operation_deadline_ns," in source
    assert provision.BUDGET["acl_create_max"] == 4 and provision.BUDGET["acl_check_max"] == 6
    assert provision.TIMEOUT_CONTRACT == loader.TIMEOUT_CONTRACT
    assert provision.TIMEOUT_CONTRACT["hard_kill_guarantee"] is False
    assert provision.TIMEOUT_CONTRACT["blocking_winapi_preemption"] == "not_claimed"
    assert "write_stdin" not in Path(provision.__file__).read_text("utf-8")


def test_anomaly065_plan_and_all_authorities_cover_truncated_wall_guard(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    fx.plan["expires_at_utc"] = _stamp(fx.now + timedelta(seconds=120))
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="plan_runtime_coverage_invalid"):
        provision.execute(fx.now)
    _loader_env(fx, monkeypatch, fx.plan)
    with pytest.raises(ValueError): loader._plan()
    assert provision.TIMEOUT_CONTRACT["authority_coverage_guard_seconds"] == 1
    assert provision.TIMEOUT_CONTRACT["owner_acceptance_window_seconds_min"] == 121


def test_anomaly066_bound_source_budget_covers_bootstrap_loader_executor_and_four_executor_reads(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    assert provision.BUDGET["bound_source_content_read_full_envelope_max"] == 6
    assert loader.BUDGET["bound_source_content_read_full_envelope_max"] == 6
    assert "bound_source_content_read_max" not in provision.BUDGET
    fx.plan["budget"]["bound_source_content_read_full_envelope_max"] = 5
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="plan_contract_invalid"):
        provision.execute(fx.now)
    _loader_env(fx, monkeypatch, fx.plan)
    with pytest.raises(ValueError): loader._plan()


def test_anomaly067_cooperative_timeout_requires_fresh_external_owner_acceptance(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    acceptance = fx.plan["authority_objects"]["cooperative_timeout_acceptance"]
    assert acceptance["status"] == "accepted_by_owner"
    assert acceptance["scope"] == provision.TIMEOUT_CONTRACT["owner_acceptance_scope"]
    acceptance["status"] = "owner_acceptance_required"
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="owner_cooperative_timeout_acceptance_required"):
        provision.execute(fx.now)
    _loader_env(fx, monkeypatch, fx.plan)
    with pytest.raises(ValueError): loader._plan()
    assert provision.TIMEOUT_CONTRACT["hard_kill_guarantee"] is False
    assert provision.TIMEOUT_CONTRACT["blocking_winapi_preemption"] == "not_claimed"


def test_anomaly069_executor_bootstrap_delay_uses_validation_time_and_ceil_remaining(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    fx.plan["expires_at_utc"] = _stamp(fx.now + timedelta(seconds=120))
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    monkeypatch.setenv(provision.BOOTSTRAP_WALL_ENV, _stamp(fx.now - timedelta(seconds=2)))
    monkeypatch.setenv(provision.DEADLINE_ENV, "120500000000")  # 119.5s remains at validation.
    with pytest.raises(provision.ProvisionError, match="plan_runtime_coverage_invalid"):
        provision.execute(fx.now)
    assert provision.TIMEOUT_CONTRACT["authority_coverage_basis"] == "validation_utc_plus_ceil_monotonic_remaining_plus_guard"


def test_anomaly069_loader_bootstrap_delay_uses_validation_time_and_ceil_remaining(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    fx.plan["expires_at_utc"] = _stamp(fx.now + timedelta(seconds=120))
    _loader_env(fx, monkeypatch, fx.plan)
    monkeypatch.setenv(loader.BOOTSTRAP_WALL_ENV, _stamp(fx.now - timedelta(seconds=2)))
    monkeypatch.setenv(loader.DEADLINE_ENV, "120500000000")  # 119.5s remains at validation.
    with pytest.raises(ValueError): loader._plan()
    assert loader.TIMEOUT_CONTRACT["authority_coverage_basis"] == "validation_utc_plus_ceil_monotonic_remaining_plus_guard"


def test_anomaly070_executor_fresh_wall_covers_intra_validation_pause_and_rejects_backward_clock(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    fx.plan["expires_at_utc"] = _stamp(fx.now + timedelta(seconds=122))
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(provision, "_utc_now", lambda: fx.now + timedelta(seconds=2))
    with pytest.raises(provision.ProvisionError, match="plan_runtime_coverage_invalid"):
        provision.execute(fx.now)
    monkeypatch.setattr(provision, "_utc_now", lambda: fx.now - timedelta(seconds=1))
    with pytest.raises(provision.ProvisionError, match="deadline_invalid"):
        provision.execute(fx.now)


def test_anomaly070_loader_fresh_wall_covers_intra_validation_pause_and_rejects_backward_clock(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch)
    fx.plan["expires_at_utc"] = _stamp(fx.now + timedelta(seconds=122))
    _loader_env(fx, monkeypatch, fx.plan)
    class PausedDateTime:
        fromisoformat = staticmethod(datetime.fromisoformat)
        values = iter((fx.now, fx.now + timedelta(seconds=2)))
        now = staticmethod(lambda tz: next(PausedDateTime.values))
    monkeypatch.setattr(loader, "datetime", PausedDateTime)
    with pytest.raises(ValueError): loader._plan()
    class BackwardDateTime:
        fromisoformat = staticmethod(datetime.fromisoformat)
        values = iter((fx.now, fx.now - timedelta(seconds=1)))
        now = staticmethod(lambda tz: next(BackwardDateTime.values))
    monkeypatch.setattr(loader, "datetime", BackwardDateTime)
    with pytest.raises(ValueError): loader._plan()
    assert loader.TIMEOUT_CONTRACT["clock_continuity_policy"] == "fresh_wall_not_before_initial_and_monotonic_non_decreasing"


def test_generation005_fixed_file_observability_and_readiness_contracts_are_exact():
    bootstrap = provision.build_readiness_inline_bootstrap(loader_bytes=10, loader_sha256="a" * 64)
    assert provision.READINESS_MODE_ENV.encode() in bootstrap
    plan = provision.build_readiness_plan(
        executor_bytes=11, executor_sha256="b" * 64, loader_bytes=10, loader_sha256="a" * 64,
        inline_bootstrap_bytes=len(bootstrap), inline_bootstrap_sha256=hashlib.sha256(bootstrap).hexdigest(),
        repository_head="c" * 40, issued_at_utc="2026-08-20T10:00:00Z",
        expires_at_utc="2026-08-20T10:05:00Z")
    assert plan["contour_id"] == "epic-phone-001-owner-local-console-readiness"
    assert plan["attempt_id"] == "owner-local-console-readiness-001"
    assert plan["security_alias"] == "epic-phone-001-security-owner-local-console-readiness-001"
    assert plan["budget"]["secret_read_max"] == plan["budget"]["authority_artifact_read_max"] == 0
    assert plan["plan_relative_path"].endswith("owner-local-console-readiness-001-plan.local.json")
    assert provision.PROVISION_PLAN_REL.name == "fixture-owner-provision-003-plan.local.json"
    assert provision.PROVISION_GO_REL.name == "security-go-owner-local-fixture-provision-003.local.json"


@pytest.mark.parametrize("console_ready,expected_state,expected_exit", [(True, "ready", 0), (False, "blocked", 2)])
def test_readiness_success_and_failure_are_durable_redacted_and_zero_secret(
    tmp_path, monkeypatch, console_ready, expected_state, expected_exit
):
    root = tmp_path / ("ready" if console_ready else "blocked")
    (root / provision.RUN_REL).mkdir(parents=True)
    monkeypatch.setattr(provision, "REPO_ROOT", root)
    monkeypatch.setattr(provision, "_fixed_drive", lambda path: None)
    monkeypatch.setattr(provision, "_safe_chain", lambda path, **kwargs: None)
    monkeypatch.setattr(provision, "_protected_write_new",
                        lambda path, payload, deadline, **kwargs: _write(path, bytes(payload)))
    monkeypatch.setattr(provision.time, "monotonic_ns", lambda: 1)
    monkeypatch.setenv(provision.DEADLINE_ENV, "10000000000")
    if console_ready:
        monkeypatch.setattr(provision, "_preflight_real_console", lambda: None)
    else:
        monkeypatch.setattr(provision, "_preflight_real_console",
                            lambda: (_ for _ in ()).throw(provision.ProvisionError("real_console_required")))
    assert provision.readiness_main({}, "d" * 64) == expected_exit
    result = json.loads((root / provision.READINESS_RESULT_REL).read_text("utf-8"))
    assert result["terminal_state"] == expected_state
    assert result["aggregate_counters"]["secret_read_count"] == 0
    assert set(result) == {"schema_version", "epic_id", "run_id", "contour_id", "attempt_id", "result_alias",
                           "plan_sha256", "terminal_state", "exit_category", "aggregate_counters"}
    assert "value" not in json.dumps(result).lower() and "length" not in json.dumps(result).lower()


def test_loader_pre_executor_failure_records_fixed_result_without_stdout(monkeypatch, capsys):
    plan = {"repository_head": "a" * 40, "executor_bytes": 1, "executor_sha256": "b" * 64}
    monkeypatch.setenv(loader.READINESS_MODE_ENV, "provision")
    monkeypatch.setenv(loader.DEADLINE_ENV, "999999999999999999")
    monkeypatch.setattr(loader, "_plan", lambda: (plan, "e" * 64))
    monkeypatch.setattr(loader, "_actual_repository_head", lambda root: ("a" * 40, 1, 3))
    monkeypatch.setattr(loader, "_load_executor", lambda *args: (_ for _ in ()).throw(ValueError()))
    monkeypatch.setattr(loader, "_provision_attempt_consumed", lambda digest: False)
    recorded = []
    monkeypatch.setattr(loader, "_write_blocked_result", lambda digest: recorded.append(digest))
    assert loader.main() == 2
    assert recorded == ["e" * 64]
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("mode", [None, "unexpected", "readiness"])
def test_loader_never_infers_provision_from_missing_invalid_or_inherited_readiness_mode(monkeypatch, mode):
    if mode is None: monkeypatch.delenv(loader.READINESS_MODE_ENV, raising=False)
    else: monkeypatch.setenv(loader.READINESS_MODE_ENV, mode)
    provision_called = []
    monkeypatch.setattr(loader, "_plan", lambda: provision_called.append(True))
    if mode == "readiness": monkeypatch.setattr(loader, "_readiness_plan", lambda: (_ for _ in ()).throw(ValueError()))
    assert loader.main() == 2 and provision_called == []


def test_preexisting_result_without_marker_consumes_before_console_or_destination(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch); events = []
    raw_plan = provision.canonical_bytes(fx.plan); digest = hashlib.sha256(raw_plan).hexdigest()
    prior = provision.canonical_bytes(provision._terminal_result(
        digest, terminal_state="blocked_before_attempt", exit_category="blocked",
        directory_created=0, execution_stage="pre_attempt", marker_created=0)) + b"\n"
    _write(fx.root / provision.RESULT_REL, prior)
    monkeypatch.setattr(provision, "_preflight_real_console", lambda: events.append("console"))
    monkeypatch.setattr(provision, "_secure_write_new", lambda *args: events.append("destination"))
    with pytest.raises(provision.ProvisionError, match="attempt_consumed"):
        provision.execute(fx.now)
    assert events == [] and not (fx.root / provision.MARKER_REL).exists()
    assert (fx.root / provision.RESULT_REL).read_bytes() == prior


def test_loader_executor_return_two_creates_durable_blocked_result_without_stdout(tmp_path, monkeypatch, capsys):
    root = tmp_path / "loader-return-two"; (root / Path(loader.RESULT_REL).parent).mkdir(parents=True)
    monkeypatch.chdir(root); monkeypatch.setenv(loader.READINESS_MODE_ENV, "provision")
    monkeypatch.setenv(loader.DEADLINE_ENV, "999999999999999999")
    plan = {"repository_head": "a" * 40, "executor_bytes": 1, "executor_sha256": "b" * 64}
    monkeypatch.setattr(loader, "_plan", lambda: (plan, "f" * 64))
    monkeypatch.setattr(loader, "_actual_repository_head", lambda root: ("a" * 40, 1, 3))
    monkeypatch.setattr(loader, "_load_executor", lambda *args: b"def main(): return 2\n")
    assert loader.main() == 2 and capsys.readouterr().out == ""
    result = json.loads((root / loader.RESULT_REL).read_text("utf-8"))
    assert result["terminal_state"] == "blocked_before_attempt"
    assert result["execution_stage"] == "pre_attempt"
    assert result["aggregate_counters"]["marker_file_created_count"] == 0


def test_loader_post_marker_partial_state_uses_unknown_not_false_zero(tmp_path, monkeypatch):
    root = tmp_path / "partial"; (root / Path(loader.RESULT_REL).parent).mkdir(parents=True)
    monkeypatch.chdir(root); monkeypatch.setenv(loader.DEADLINE_ENV, "999999999999999999")
    _write(root / loader.PROVISION_MARKER_REL, b"consumed\n")
    loader._write_blocked_result("a" * 64)
    result = json.loads((root / loader.RESULT_REL).read_text("utf-8"))
    assert result["terminal_state"] == "blocked_after_attempt"
    assert result["execution_stage"] == "unknown_after_marker"
    assert result["aggregate_counters"]["destination_directory_created_count"] == "unknown"


@pytest.mark.parametrize("consumed_kind", ["marker", "result"])
def test_loader_preexisting_marker_or_result_never_executes_again(tmp_path, monkeypatch, consumed_kind):
    root = tmp_path / consumed_kind; (root / Path(loader.RESULT_REL).parent).mkdir(parents=True)
    monkeypatch.chdir(root); monkeypatch.setenv(loader.READINESS_MODE_ENV, "provision")
    plan = {"repository_head": "a" * 40, "executor_bytes": 1, "executor_sha256": "b" * 64}
    digest = "c" * 64
    if consumed_kind == "marker":
        _write(root / loader.PROVISION_MARKER_REL, b"prior\n")
    else:
        prior = provision.canonical_bytes(provision._terminal_result(
            digest, terminal_state="blocked_before_attempt", exit_category="blocked",
            directory_created=0, execution_stage="pre_attempt", marker_created=0)) + b"\n"
        _write(root / loader.RESULT_REL, prior)
    monkeypatch.setattr(loader, "_plan", lambda: (plan, digest))
    monkeypatch.setattr(loader, "_actual_repository_head", lambda root: ("a" * 40, 1, 3))
    monkeypatch.setattr(loader, "_load_executor", lambda *args: (_ for _ in ()).throw(AssertionError("replayed")))
    assert loader.main() == 2
    assert not (root / loader.RESULT_REL).exists() if consumed_kind == "marker" else (root / loader.RESULT_REL).exists()


def test_inherited_readiness_marker_never_creates_new_result(tmp_path, monkeypatch):
    root = tmp_path / "readiness-replay"; (root / provision.RUN_REL).mkdir(parents=True)
    _write(root / provision.READINESS_MARKER_REL, b"prior\n")
    monkeypatch.setattr(provision, "REPO_ROOT", root); monkeypatch.setattr(provision, "_fixed_drive", lambda path: None)
    monkeypatch.setattr(provision, "_safe_chain", lambda path, **kwargs: None)
    monkeypatch.setattr(provision.time, "monotonic_ns", lambda: 1)
    monkeypatch.setenv(provision.DEADLINE_ENV, "10000000000")
    writes = []; monkeypatch.setattr(provision, "_protected_write_new", lambda *args, **kwargs: writes.append(args[0]))
    assert provision.readiness_main({}, "b" * 64) == 2
    assert writes == [] and not (root / provision.READINESS_RESULT_REL).exists()


def test_finalization_reserve_schemas_budgets_and_expectation_builders_are_exact():
    assert provision.AGGREGATE_SCHEMA != provision.TERMINAL_RESULT_SCHEMA
    assert provision.RESULT_FINALIZATION_RESERVE_SECONDS == 5
    assert provision.TIMEOUT_CONTRACT["result_finalization_reserve_seconds"] == 5
    assert provision.BUDGET["result_finalization_reserve_seconds"] == 5
    exact_terminal_io_budget = {
        "protected_marker_file_readback_max": 1,
        "protected_terminal_result_file_readback_max": 1,
        "loader_terminal_result_content_read_max": 2,
        "loader_terminal_result_validation_max": 2,
    }
    assert {key: provision.BUDGET[key] for key in exact_terminal_io_budget} == exact_terminal_io_budget
    assert {key: loader.BUDGET[key] for key in exact_terminal_io_budget} == exact_terminal_io_budget
    assert provision.BUDGET == loader.BUDGET
    readiness_budget = provision.build_readiness_plan(
        executor_bytes=1, executor_sha256="a" * 64, loader_bytes=1, loader_sha256="b" * 64,
        inline_bootstrap_bytes=1, inline_bootstrap_sha256="c" * 64, repository_head="d" * 40,
        issued_at_utc="2026-08-20T10:00:00Z", expires_at_utc="2026-08-20T10:05:00Z")["budget"]
    assert {key: readiness_budget[key] for key in ("acl_create_max", "acl_check_max", "created_file_readback_max")} == {
        "acl_create_max": 2, "acl_check_max": 2, "created_file_readback_max": 2}
    for builder in (provision.build_security_go, provision.build_readiness_security_go):
        source = inspect.getsource(builder)
        assert "expect" in (builder.__doc__ or "").lower()
        assert not any(token in source for token in ("open(", "write(", "os.open", "Path("))


def _mutate_terminal_forbidden_counter(value):
    value["aggregate_counters"]["application_action_count"] = 999


def _mutate_terminal_marker_zero(value):
    value["aggregate_counters"]["marker_file_created_count"] = 0


def _mutate_terminal_directory_above_one(value):
    value["aggregate_counters"]["destination_directory_created_count"] = 2


def _mutate_terminal_garbage_category(value):
    value["exit_category"] = "garbage"


def _mutate_terminal_garbage_stage(value):
    value["execution_stage"] = "garbage"


def _mutate_terminal_boolean_counter(value):
    value["aggregate_counters"]["destination_directory_created_count"] = True


TERMINAL_CROSS_FIELD_MUTATIONS = (
    _mutate_terminal_forbidden_counter,
    _mutate_terminal_marker_zero,
    _mutate_terminal_directory_above_one,
    _mutate_terminal_garbage_category,
    _mutate_terminal_garbage_stage,
    _mutate_terminal_boolean_counter,
)


@pytest.mark.parametrize("mutate", TERMINAL_CROSS_FIELD_MUTATIONS)
def test_loader_terminal_result_cross_fields_fail_closed(mutate):
    digest = "a" * 64
    value = provision._terminal_result(
        digest, terminal_state="fixture_provisioned", exit_category="success",
        directory_created=1, execution_stage="terminal_result_finalization")
    mutate(value)
    with pytest.raises(ValueError):
        loader._validate_terminal_result(provision.canonical_bytes(value) + b"\n", digest)


@pytest.mark.parametrize("mutate", TERMINAL_CROSS_FIELD_MUTATIONS)
def test_loader_cannot_return_zero_for_invalid_terminal_cross_fields(monkeypatch, mutate):
    digest = "b" * 64
    plan = {"repository_head": "a" * 40, "executor_bytes": 1, "executor_sha256": "c" * 64}
    value = provision._terminal_result(
        digest, terminal_state="fixture_provisioned", exit_category="success",
        directory_created=0, execution_stage="terminal_result_finalization")
    mutate(value)
    invalid = provision.canonical_bytes(value) + b"\n"
    monkeypatch.setenv(loader.READINESS_MODE_ENV, "provision")
    monkeypatch.setenv(loader.DEADLINE_ENV, "999999999999999999")
    monkeypatch.setattr(loader, "_plan", lambda: (plan, digest))
    monkeypatch.setattr(loader, "_actual_repository_head", lambda root: ("a" * 40, 1, 3))
    monkeypatch.setattr(loader, "_provision_attempt_consumed", lambda plan_sha: False)
    monkeypatch.setattr(loader, "_load_executor", lambda *args: b"def main(): return 0\n")
    monkeypatch.setattr(loader, "_load_fixed_input", lambda *args: invalid)
    monkeypatch.setattr(loader, "_write_blocked_result", lambda plan_sha: None)
    assert loader.main() == 2


def test_terminal_contract_state_rules_and_loader_io_budget_are_exact(monkeypatch):
    contract = provision.terminal_result_contract()
    assert contract == loader._terminal_result_contract()
    assert contract["exit_category_by_terminal_state"] == {
        "blocked_after_attempt": "blocked", "blocked_before_attempt": "blocked",
        "fixture_provisioned": "success"}
    assert contract["execution_stages_by_terminal_state"]["blocked_before_attempt"] == ["pre_attempt"]
    assert contract["execution_stages_by_terminal_state"]["fixture_provisioned"] == ["terminal_result_finalization"]
    assert set(contract["always_exact_zero_counters"]) == {
        "application_action_count", "authentication_action_count", "device_action_count",
        "network_action_count", "runtime_action_count", "subprocess_count", "ui_action_count"}
    digest = "d" * 64
    raw = provision.canonical_bytes(provision._terminal_result(
        digest, terminal_state="fixture_provisioned", exit_category="success",
        directory_created=0, execution_stage="terminal_result_finalization")) + b"\n"
    monkeypatch.setattr(loader, "_load_fixed_input", lambda *args: raw)
    loader._ACTIVE_TERMINAL_IO_BUDGET = {"content_reads": 0, "validations": 0}
    try:
        loader._load_and_validate_terminal_result(Path("ignored"), digest)
        loader._load_and_validate_terminal_result(Path("ignored"), digest)
        with pytest.raises(ValueError):
            loader._load_and_validate_terminal_result(Path("ignored"), digest)
        assert loader._ACTIVE_TERMINAL_IO_BUDGET == {"content_reads": 3, "validations": 2}
    finally:
        loader._ACTIVE_TERMINAL_IO_BUDGET = None


def test_protected_marker_and_terminal_readbacks_have_one_attempt_each(monkeypatch):
    calls = []
    monkeypatch.setattr(provision, "_protected_write_new", lambda *args, **kwargs: calls.append(args[0]))
    counters = {"marker": 0, "terminal_result": 0}
    provision._protected_provision_write_new(Path("marker"), b"m", 1, counters, "marker")
    provision._protected_provision_write_new(Path("result"), b"r", 1, counters, "terminal_result")
    with pytest.raises(provision.ProvisionError, match="protected_readback_budget_exhausted"):
        provision._protected_provision_write_new(Path("result-2"), b"r", 1, counters, "terminal_result")
    assert calls == [Path("marker"), Path("result")]


def test_generation004_immediate_predecessor_is_rejected_and_not_read(tmp_path, monkeypatch):
    assert renewal.BUDGET["old_authority_content_read_max"] == 0
    assert all("c0p-authority-005" in path.as_posix() for path in renewal.ARTIFACT_PATHS)
    assert controller.AUTHORITY_SET_ID == "c0p-authority-005" and prep.PREP_ATTEMPT_ID == "c0p-prep-005"
    assert provision.AUTHORITY_SET_REL.as_posix().endswith("c0p-authority-005")
    fx = _setup(tmp_path, monkeypatch)
    fx.plan["authority_artifacts"][0]["alias"] = "epic-phone-001-security-c0p-004"
    raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode())
    monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match="authority_cross_binding_invalid"):
        provision.execute(fx.now)
    assert not (fx.root / provision.MARKER_REL).exists()

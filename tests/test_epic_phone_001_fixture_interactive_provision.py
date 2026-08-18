from __future__ import annotations

import hashlib
import inspect
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import automation.phone.epic_phone_001_fixture_interactive_provision as provision
import automation.phone.epic_phone_001_owner_local_fixture_loader as loader
import automation.phone.epic_phone_001_authority_renewal as renewal


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
    sources = {
        provision.EXECUTOR_REL: b"fixed executor", provision.LOADER_REL: b"fixed loader",
        provision.CONTROLLER_REL: b"fixed controller", provision.GITIGNORE_REL: b".qa_local/\n",
    }
    for index, (relative, _) in enumerate(provision.WORKSPACE_ALLOWLIST_CONTRACT):
        sources.setdefault(Path(relative), f"workspace-{index}".encode())
    for path, data in sources.items(): _write(root / path, data)
    (root / provision.RUN_REL).mkdir(parents=True)
    if parent_state == "present": (root / provision.DESTINATION_REL.parent).mkdir(parents=True)
    expiry = _stamp(now + timedelta(minutes=8))
    artifacts = renewal.build_authority_payloads(
        repository_head="a" * 40, controller_sha256=hashlib.sha256(sources[provision.CONTROLLER_REL]).hexdigest(),
        issued_at_utc=_stamp(now - timedelta(seconds=5)), expires_at_utc=expiry,
        retention_expires_at_utc=expiry)
    artifact_contracts = (
        ("epic-phone-001-security-c0p-003", "execution_status", "planned_separate_literal_go_required_not_run", "expires_at_utc", expiry),
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
    monkeypatch.setenv(provision.BOOTSTRAP_WALL_ENV, _stamp(now)); monkeypatch.setenv(provision.DEADLINE_ENV, str(121_000_000_000))
    monkeypatch.setattr(provision, "_verify_path_acl", lambda path, **kwargs: None)
    return SimpleNamespace(now=now, root=root, plan=plan, bootstrap=bootstrap)


def test_exact_security_literals_and_bootstrap_never_parses_plan():
    bootstrap = provision.build_inline_bootstrap(loader_bytes=10, loader_sha256="a" * 64)
    assert provision.CONTOUR_ID == "epic-phone-001-owner-local-fixture-provision"
    assert provision.SCHEMA == "epic-phone-001-owner-local-fixture-provision-plan-v1"
    assert provision.MARKER_REL.name == "fixture-owner-provision-attempt.local.json"
    assert provision.GO_PREFIX == "GO_EPIC_PHONE_001_OWNER_LOCAL_FIXTURE_PROVISION__epic-phone-001-20260816-r01__"
    assert provision.PLAN_ENV.encode() not in bootstrap
    assert bootstrap.count(b'print(\'{"status":"blocked"}\')') == 1


def test_success_marker_before_input_exact_payload_and_aggregate(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch); events = []; inputs = [bytearray(b"0123456789"), bytearray(b"0042")]
    def marker(path, payload, deadline, **kwargs): events.append((path.name, bytes(payload), False)); _write(path, bytes(payload))
    def secure(path, payload, deadline): events.append((path.name, bytes(payload), True)); _write(path, bytes(payload))
    def console(*args):
        assert (fx.root / provision.MARKER_REL).is_file(); events.append(("input", b"", False)); return inputs.pop(0)
    monkeypatch.setattr(provision, "_protected_write_new", marker); monkeypatch.setattr(provision, "_secure_write_new", secure); monkeypatch.setattr(provision, "_read_console_digits", console)
    result = provision.execute(fx.now)
    expected = b"EPIC_PHONE_001_PHONE_SUFFIX=0123456789\nEPIC_PHONE_001_OTP=0042\n"
    assert (fx.root / provision.DESTINATION_REL).read_bytes() == expected
    assert events[0][0] == provision.MARKER_REL.name and events[1][0] == "input"
    assert events[-1] == ("qa_user.env", expected, True)
    assert result == fx.plan["aggregate_contract"] == provision._aggregate(0)


def test_absent_parent_is_created_once_before_destination(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch, parent_state="absent"); created = []
    monkeypatch.setattr(provision, "_secure_mkdir", lambda path, deadline: (path.mkdir(), created.append(path)))
    monkeypatch.setattr(provision, "_protected_write_new", lambda path, payload, deadline, **kwargs: _write(path, bytes(payload)))
    monkeypatch.setattr(provision, "_secure_write_new", lambda path, payload, deadline: _write(path, bytes(payload)))
    answers = iter((bytearray(b"0123456789"), bytearray(b"1234")))
    monkeypatch.setattr(provision, "_read_console_digits", lambda *args: next(answers))
    assert provision.execute(fx.now) == provision._aggregate(1)
    assert created == [fx.root / provision.DESTINATION_REL.parent]


@pytest.mark.parametrize("mutation,reason", [
    (lambda plan: plan.update(extra=0), "plan_contract_invalid"),
    (lambda plan: plan["budget"].update(runtime_action_max=False), "plan_contract_invalid"),
    (lambda plan: plan.update(expires_at_utc=plan["issued_at_utc"]), "plan_or_authority_expired"),
])
def test_plan_exact_type_extra_and_ttl_fail_before_marker(tmp_path, monkeypatch, mutation, reason):
    fx = _setup(tmp_path, monkeypatch); mutation(fx.plan); raw = provision.canonical_bytes(fx.plan)
    monkeypatch.setenv(provision.PLAN_ENV, raw.decode()); monkeypatch.setenv(provision.GO_ENV, provision.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(provision.ProvisionError, match=reason): provision.execute(fx.now)
    assert not (fx.root / provision.MARKER_REL).exists()


def test_go_source_authority_and_replay_fail_before_console(tmp_path, monkeypatch):
    fx = _setup(tmp_path, monkeypatch); monkeypatch.setenv(provision.GO_ENV, "wrong")
    with pytest.raises(provision.ProvisionError, match="literal_go_invalid"): provision.execute(fx.now)
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
    assert "PHONE_SUFFIX" not in stdout and "OTP" not in stdout and str(tmp_path) not in stdout
    assert json.loads(stdout)["status"] == "fixture_provisioned"
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
    assert loader._plan()["schema_version"] == provision.SCHEMA
    extra = dict(fx.plan); extra["extra"] = 0; raw = provision.canonical_bytes(extra)
    monkeypatch.setenv(loader.PLAN_ENV, raw.decode()); monkeypatch.setenv(loader.GO_ENV, loader.GO_PREFIX + hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError): loader._plan()
    monkeypatch.setattr(loader, "_plan", lambda: {"executor_bytes": 1, "executor_sha256": "a" * 64})
    monkeypatch.setattr(loader, "_load_executor", lambda *args: b"raise SystemExit(0)\n")
    assert loader.main() == 2


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
    assert events[:3] == ["console", "marker", "mkdir"] and events[-1] == "destination"


def test_anomaly058_acl_marker_and_deadline_contract_are_exact():
    source = Path(provision.__file__).read_text("utf-8")
    assert "_protected_write_new(marker" in source
    assert "for kind in ((22,) if exact_secret else (22, 26))" in source
    assert "acl_exact_ace_count_invalid" in source and "acl_required_principal_missing" in source
    assert source.count("_check_deadline(deadline_ns)") >= 12
    assert provision.BUDGET["acl_create_max"] == 3 and provision.BUDGET["acl_check_max"] == 5
    assert provision.BUDGET["console_prompt_write_max"] == 2
    assert provision.BUDGET["console_separator_write_max"] == 2
    assert provision.BUDGET["bootstrap_env_write_max"] == 2


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
    assert "_check_deadline(deadline_ns); _preflight_real_console(); _check_deadline(deadline_ns)" in execute_source
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
    assert "_protected_write_new(marker, marker_payload, deadline_ns, verify_before_write=False)" in source
    assert provision.BUDGET["acl_create_max"] == 3 and provision.BUDGET["acl_check_max"] == 5
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

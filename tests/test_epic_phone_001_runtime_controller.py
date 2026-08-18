from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from automation.phone import epic_phone_001_runtime_controller as controller


NOW = datetime(2026, 8, 16, 14, 0, tzinfo=UTC)
ISSUED = "2026-08-16T13:55:00Z"
EXPIRES = "2026-08-16T14:04:00Z"
RETENTION_EXPIRES = "2026-08-17T15:00:00Z"
C0P_EXPIRES = "2026-08-16T14:20:00Z"


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _fixture():
    return {
        "schema_version": controller.FIXTURE_PASSPORT_SCHEMA,
        "epic_id": controller.EPIC_ID,
        "run_id": controller.RUN_ID,
        "authority_set_id": controller.AUTHORITY_SET_ID,
        "renewal_id": controller.AUTHORITY_RENEWAL_ID,
        "prep_attempt_id": controller.C0P_PREP_ATTEMPT_ID,
        "fixture_alias": controller.FIXTURE_ALIAS,
        "synthetic_test_only": True,
        "not_real_user": True,
        "values_local_only": True,
        "revoked": False,
        "authority_validity": "current_epic_run_until_completion_or_revocation",
        "allowed_scope": ["synthetic_session_create", "read_only_navigation", "safe_logout"],
        "forbidden_scope": ["payment", "subscription", "entitlement", "profile", "account", "paid_session", "external_or_qr_traversal"],
        "issued_at_utc": ISSUED,
        "expires_at_utc": EXPIRES,
    }


def _target():
    return {
        "schema_version": controller.TARGET_BUILD_PASSPORT_SCHEMA,
        "epic_id": controller.EPIC_ID,
        "run_id": controller.RUN_ID,
        "authority_set_id": controller.AUTHORITY_SET_ID,
        "renewal_id": controller.AUTHORITY_RENEWAL_ID,
        "prep_attempt_id": controller.C0P_PREP_ATTEMPT_ID,
        "target_alias": controller.TARGET_ALIAS,
        "build_alias": controller.BUILD_ALIAS,
        "target_authorized": True,
        "build_authorized": True,
        "launch_allowed": False,
        "mutation_allowed": False,
        "passport_purpose": "authorization_only",
        "current_freshness_evidence": False,
        "runtime_evidence": False,
        "task058a_row03_evidence_status": "unknown",
        "issued_at_utc": ISSUED,
        "expires_at_utc": EXPIRES,
    }


def _cleanup():
    return {
        "schema_version": controller.EVIDENCE_CLEANUP_PASSPORT_SCHEMA,
        "epic_id": controller.EPIC_ID,
        "run_id": controller.RUN_ID,
        "authority_set_id": controller.AUTHORITY_SET_ID,
        "renewal_id": controller.AUTHORITY_RENEWAL_ID,
        "prep_attempt_id": controller.C0P_PREP_ATTEMPT_ID,
        "issued_at_utc": ISSUED,
        "run_root": controller.RUN_ROOT_REL.as_posix(),
        "soft_bytes_max": 48 * 1024 * 1024,
        "hard_bytes_max": 64 * 1024 * 1024,
        "redaction_default": True,
        "direct_capture_no_echo": True,
        "cleanup_sequence": ["target_only_force_stop", "home", "post_kill_checkpoint", "capture_shutdown"],
        "forbidden_action_count": 0,
        "passport_purpose": "policy_readiness_only",
        "execution_evidence": False,
        "retention_expires_at_utc": RETENTION_EXPIRES,
    }


def _c0p_result():
    source_hash = controller._controller_source_sha256()
    binding = {
        "repository_head": "a" * 40,
        "controller_source_sha256": source_hash,
        "c0p_plan_sha256": "b" * 64,
        "expires_at_utc": C0P_EXPIRES,
    }
    return controller._build_c0p_result(binding, executed_at=datetime(2026, 8, 16, 13, 59, tzinfo=UTC))


def _go(plan, fixture, target, cleanup, c0p_result):
    digest = controller.plan_sha256(plan)
    return {
        "schema_version": controller.SECURITY_GO_SCHEMA,
        "literal_token": controller.expected_go_token(digest),
        "epic_id": controller.EPIC_ID,
        "run_id": controller.RUN_ID,
        "contour_id": controller.CONTOUR_ID,
        "plan_sha256": digest,
        "target_alias": controller.TARGET_ALIAS,
        "build_alias": controller.BUILD_ALIAS,
        "fixture_alias": controller.FIXTURE_ALIAS,
        "security_alias": controller.C1_SECURITY_ALIAS,
        "passport_sha256": {
            "fixture_authority": controller._sha256_bytes(_bytes(fixture)),
            "target_build": controller._sha256_bytes(_bytes(target)),
            "evidence_cleanup": controller._sha256_bytes(_bytes(cleanup)),
        },
        "passport_aliases": {
            "fixture_authority": controller.FIXTURE_PASSPORT_ALIAS,
            "target_build": controller.TARGET_BUILD_PASSPORT_ALIAS,
            "evidence_cleanup": controller.EVIDENCE_CLEANUP_PASSPORT_ALIAS,
        },
        "passport_expires_at_utc": {
            "fixture_authority": EXPIRES,
            "target_build": EXPIRES,
            "evidence_cleanup": RETENTION_EXPIRES,
        },
        "issued_at_utc": ISSUED,
        "expires_at_utc": EXPIRES,
        "budget": dict(controller.C1_BUDGET),
        "c0p_result_path": controller.C0P_RESULT_REL.as_posix(),
        "c0p_result_sha256": controller._sha256_bytes(controller.canonical_plan_bytes(c0p_result)),
    }


def _c0p_go(plan, fixture, target, cleanup, source_hash):
    digest = controller.plan_sha256(plan)
    return {
        "schema_version": controller.C0P_SECURITY_GO_SCHEMA,
        "literal_token": controller.expected_c0p_go_token(digest),
        "epic_id": controller.EPIC_ID,
        "run_id": controller.RUN_ID,
        "contour_id": controller.C0P_CONTOUR_ID,
        "c0p_plan_sha256": digest,
        "repository_head": "a" * 40,
        "controller_source_sha256": source_hash,
        "target_alias": controller.TARGET_ALIAS,
        "build_alias": controller.BUILD_ALIAS,
        "fixture_alias": controller.FIXTURE_ALIAS,
        "passport_aliases": {
            "fixture_authority": controller.FIXTURE_PASSPORT_ALIAS,
            "target_build": controller.TARGET_BUILD_PASSPORT_ALIAS,
            "evidence_cleanup": controller.EVIDENCE_CLEANUP_PASSPORT_ALIAS,
        },
        "security_alias": controller.C0P_SECURITY_ALIAS,
        "passport_sha256": {
            "fixture_authority": controller._sha256_bytes(_bytes(fixture)),
            "target_build": controller._sha256_bytes(_bytes(target)),
            "evidence_cleanup": controller._sha256_bytes(_bytes(cleanup)),
        },
        "passport_expires_at_utc": {
            "fixture_authority": fixture["expires_at_utc"],
            "target_build": target["expires_at_utc"],
            "evidence_cleanup": cleanup["retention_expires_at_utc"],
        },
        "issued_at_utc": ISSUED,
        "expires_at_utc": C0P_EXPIRES,
        "result_path": controller.C0P_RESULT_REL.as_posix(),
        "attempt_marker_path": controller.C0P_ATTEMPT_REL.as_posix(),
        "attempt_marker_schema": controller.C0P_ATTEMPT_SCHEMA,
        "budget": dict(controller.C0P_BUDGET),
    }


def _prepare_c0p_temp_repo(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    source_hash = "d" * 64
    plan = controller.c0p_plan("a" * 40, source_hash, ISSUED, EXPIRES)
    fixture, target, cleanup = _fixture(), _target(), _cleanup()
    go = _c0p_go(plan, fixture, target, cleanup, source_hash)
    payloads = {
        controller.C0P_PLAN_REL: plan,
        controller.FIXTURE_PASSPORT_REL: fixture,
        controller.TARGET_BUILD_PASSPORT_REL: target,
        controller.EVIDENCE_CLEANUP_PASSPORT_REL: cleanup,
        controller.SECURITY_GO_C0P_REL: go,
    }
    for relative, value in payloads.items():
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(controller.canonical_plan_bytes(value))
    secret = repo / controller.SECRET_SOURCE_REL
    secret.parent.mkdir(parents=True, exist_ok=True)
    secret.write_bytes(
        b"EPIC_PHONE_001_PHONE_SUFFIX=1234567890\nEPIC_PHONE_001_OTP=123456\n"
    )
    (repo / controller.PUBLIC_SAFE_REL).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(controller, "REPO_ROOT", repo)
    monkeypatch.setattr(controller, "_controller_source_sha256", lambda: source_hash)
    return repo


def _validate(plan=None, fixture=None, target=None, cleanup=None, c0p_result=None, go=None):
    plan = plan or controller.controller_plan()
    fixture = fixture or _fixture()
    target = target or _target()
    cleanup = cleanup or _cleanup()
    c0p_result = c0p_result or _c0p_result()
    c0p_result_bytes = controller.canonical_plan_bytes(c0p_result)
    go = go or _go(plan, fixture, target, cleanup, c0p_result)
    return controller.validate_preflight_payloads(
        plan,
        fixture,
        _bytes(fixture),
        target,
        _bytes(target),
        cleanup,
        _bytes(cleanup),
        c0p_result,
        c0p_result_bytes,
        go,
        now=NOW,
    )


def test_fixed_epic_run_contour_aliases_and_paths_are_exact():
    assert controller.EPIC_ID == "EPIC-PHONE-001"
    assert controller.RUN_ID == "epic-phone-001-20260816-r01"
    assert controller.CONTOUR_ID == "epic-phone-001-c1-launch-free-readiness"
    assert controller.TARGET_ALIAS == "phone-current-001"
    assert controller.BUILD_ALIAS == "task058-selected-phone-full-001"
    assert controller.FIXTURE_ALIAS == "epic-phone-001-fixture-001"
    assert controller.AUTHORITY_SET_ID == "c0p-authority-004"
    assert controller.AUTHORITY_RENEWAL_ID == "authority-renewal-002"
    assert controller.C0P_PREP_ATTEMPT_ID == "c0p-prep-004"
    assert controller.FIXTURE_PASSPORT_ALIAS == "epic-phone-001-fixture-authority-004"
    assert controller.TARGET_BUILD_PASSPORT_ALIAS == "epic-phone-001-target-build-004"
    assert controller.EVIDENCE_CLEANUP_PASSPORT_ALIAS == "epic-phone-001-evidence-cleanup-004"
    assert controller.C0P_SECURITY_ALIAS == "epic-phone-001-security-c0p-004"
    assert controller.AUTHORITY_SET_ROOT_REL.as_posix().endswith("authority-sets/c0p-authority-004")
    assert controller.C1_SECURITY_ALIAS == "epic-phone-001-security-c1-001"
    assert controller.SECRET_SOURCE_REL.as_posix() == ".qa_local/secrets/qa_user.env"
    assert controller.SERIAL_ALIAS_MAP_REL.as_posix() == ".qa_local/devices/serial_alias_map.json"
    assert controller.PLAN_REL.name == "controller-plan.local.json"
    assert controller.SECURITY_GO_C1_REL.name == "security-go-c1.local.json"
    assert {controller.RAW_REL.name, controller.CHECKPOINTS_REL.name, controller.PUBLIC_SAFE_REL.name} == {"raw", "checkpoints", "public-safe"}


def test_c0p_is_a_separate_fixed_token_contour_with_guarded_interface():
    plan = controller.c0p_plan("a" * 40, "b" * 64, ISSUED, EXPIRES)
    assert plan["contour_id"] == "epic-phone-001-c0p-local-presence"
    assert plan["security_alias"] == "epic-phone-001-security-c0p-004"
    assert plan["fixed_plan_path"].endswith("/c0p-plan.local.json")
    assert plan["fixed_token_path"].endswith("/security-go-c0p.local.json")
    assert plan["public_result_allowlist"] == [
        "required_field_count",
        "required_fields_present",
        "unexpected_fields_absent",
        "phone_format_policy_pass",
        "otp_format_policy_pass",
    ]
    assert set(plan["value_handling"].values()) == {False, True}
    assert plan["controller_execution_interface_present"] is True
    digest = controller.plan_sha256(plan)
    assert controller.expected_c0p_go_token(digest) == f"GO_EPIC_PHONE_001_C0P_LOCAL_PRESENCE__{controller.RUN_ID}__{digest}"


@pytest.mark.parametrize(
    "payload_factory,field,consumed_value,validator",
    [
        (_fixture, "authority_set_id", "c0p-authority-003", controller._validate_fixture_passport),
        (_target, "renewal_id", "authority-renewal-001", controller._validate_target_build_passport),
        (_cleanup, "prep_attempt_id", "c0p-prep-003", controller._validate_evidence_cleanup_passport),
    ],
)
def test_consumed_generation_passports_cannot_be_mixed_into_generation004(
    payload_factory, field, consumed_value, validator
):
    payload = payload_factory()
    payload[field] = consumed_value
    with pytest.raises(controller.ContractError, match="passport_binding_invalid"):
        validator(payload)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda plan: plan.update(security_alias="epic-phone-001-security-c0p-003"),
        lambda plan: plan["passport_aliases"].update(fixture_authority="epic-phone-001-fixture-authority-003"),
        lambda plan: plan["passport_aliases"].update(target_build="epic-phone-001-target-build-003"),
        lambda plan: plan["passport_aliases"].update(evidence_cleanup="epic-phone-001-evidence-cleanup-003"),
    ],
)
def test_consumed_security_or_passport_alias_cannot_be_mixed_into_generation004(mutation):
    plan = controller.c0p_plan("a" * 40, "b" * 64, ISSUED, EXPIRES)
    mutation(plan)
    with pytest.raises(controller.ContractError, match="c0p_plan_contract_drift"):
        controller._validate_c0p_plan(plan, "b" * 64)


def test_c0p_secret_parser_emits_only_exact_approved_aggregate():
    secret = (
        b"# synthetic local fixture\n\n"
        b"EPIC_PHONE_001_PHONE_SUFFIX=1234567890\n"
        b"EPIC_PHONE_001_OTP=123456\n"
    )
    result = controller._parse_c0p_secret(secret)
    assert result == {
        "required_field_count": 2,
        "required_fields_present": True,
        "unexpected_fields_absent": True,
        "phone_format_policy_pass": True,
        "otp_format_policy_pass": True,
    }
    serialized = json.dumps(result, sort_keys=True)
    assert "1234567890" not in serialized
    assert "123456" not in serialized
    assert "PHONE_SUFFIX" not in serialized
    assert "EPIC_PHONE_001_OTP" not in serialized


@pytest.mark.parametrize(
    "secret",
    [
        b"EPIC_PHONE_001_PHONE_SUFFIX=1234567890\n",
        b"EPIC_PHONE_001_PHONE_SUFFIX=1234567890\nEPIC_PHONE_001_PHONE_SUFFIX=1234567890\nEPIC_PHONE_001_OTP=1234\n",
        b"EPIC_PHONE_001_PHONE_SUFFIX=1234567890\nEPIC_PHONE_001_OTP=1234\nUNEXPECTED=1\n",
        b"export EPIC_PHONE_001_PHONE_SUFFIX=1234567890\nEPIC_PHONE_001_OTP=1234\n",
        b"EPIC_PHONE_001_PHONE_SUFFIX=123456789\nEPIC_PHONE_001_OTP=1234\n",
        b"EPIC_PHONE_001_PHONE_SUFFIX=1234567890\nEPIC_PHONE_001_OTP=123\n",
        "EPIC_PHONE_001_PHONE_SUFFIX=1234567890\nEPIC_PHONE_001_OTP=12é4\n".encode(),
    ],
)
def test_c0p_missing_duplicate_unknown_export_format_or_nonascii_fails(secret):
    with pytest.raises(controller.ContractError):
        controller._parse_c0p_secret(secret)


def test_c0p_cli_requires_allow_before_any_local_read(monkeypatch, capsys):
    called = False

    def forbidden_call():
        nonlocal called
        called = True
        raise AssertionError("must not run")

    monkeypatch.setattr(controller, "preflight_c0p", forbidden_call)
    assert controller.main(["--preflight-c0p"]) == 1
    assert called is False
    assert "requires_explicit_allow_flag" in capsys.readouterr().err


def test_c0p_invalid_authority_stops_before_secret_read(monkeypatch):
    monkeypatch.setattr(controller, "_controller_source_sha256", lambda: "a" * 64)
    monkeypatch.setattr(controller, "_read_small_json", lambda *args, **kwargs: ({}, b"{}"))
    monkeypatch.setattr(
        controller,
        "_validate_c0p_authority_payloads",
        lambda *args, **kwargs: (_ for _ in ()).throw(controller.ContractError("invalid_token")),
    )
    secret_read = False

    def forbidden_secret(*args, **kwargs):
        nonlocal secret_read
        secret_read = True
        raise AssertionError("secret read")

    monkeypatch.setattr(controller, "_read_small_bytes", forbidden_secret)
    with pytest.raises(controller.ContractError, match="invalid_token"):
        controller.preflight_c0p(now=NOW)
    assert secret_read is False


def test_c0p_existing_result_stops_before_secret_read(monkeypatch):
    monkeypatch.setattr(controller, "_controller_source_sha256", lambda: "a" * 64)
    monkeypatch.setattr(controller, "_read_small_json", lambda *args, **kwargs: ({}, b"{}"))
    monkeypatch.setattr(
        controller,
        "_validate_c0p_authority_payloads",
        lambda *args, **kwargs: {
            "repository_head": "a" * 40,
            "controller_source_sha256": "a" * 64,
            "c0p_plan_sha256": "b" * 64,
            "expires_at_utc": C0P_EXPIRES,
            "security_go_sha256": "c" * 64,
        },
    )
    monkeypatch.setattr(
        controller,
        "_assert_c0p_one_shot_paths_clear",
        lambda: (_ for _ in ()).throw(controller.ContractError("one_shot_result_exists")),
    )
    monkeypatch.setattr(controller, "_write_c0p_attempt_marker", lambda *args: None)
    secret_read = False

    def forbidden_secret(*args, **kwargs):
        nonlocal secret_read
        secret_read = True
        raise AssertionError("secret read")

    monkeypatch.setattr(controller, "_read_small_bytes", forbidden_secret)
    with pytest.raises(controller.ContractError, match="one_shot_result_exists"):
        controller.preflight_c0p(now=NOW)
    assert secret_read is False


def test_c0p_exact_plan_passports_and_literal_token_validate_in_memory():
    source_hash = controller._controller_source_sha256()
    plan = controller.c0p_plan("a" * 40, source_hash, ISSUED, EXPIRES)
    plan_bytes = controller.canonical_plan_bytes(plan)
    fixture, target, cleanup = _fixture(), _target(), _cleanup()
    go = _c0p_go(plan, fixture, target, cleanup, source_hash)
    binding = controller._validate_c0p_authority_payloads(
        plan, plan_bytes, fixture, _bytes(fixture), target, _bytes(target),
        cleanup, _bytes(cleanup), go, source_sha256=source_hash, now=NOW
    )
    assert binding["repository_head"] == "a" * 40
    mutated = copy.deepcopy(go)
    mutated["repository_head"] = "b" * 40
    with pytest.raises(controller.ContractError, match="binding_invalid"):
        controller._validate_c0p_authority_payloads(
            plan, plan_bytes, fixture, _bytes(fixture), target, _bytes(target),
            cleanup, _bytes(cleanup), mutated, source_sha256=source_hash, now=NOW
        )


def test_fixed_ignored_file_rejects_escape_and_link_or_reparse(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    ignored = repo / ".qa_local"
    ignored.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(controller, "REPO_ROOT", repo)
    with pytest.raises(controller.ContractError, match="outside_repository"):
        controller._assert_fixed_ignored_file(outside, "test")
    link = ignored / "link.json"
    link.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(controller, "_is_reparse_or_link", lambda path: path == link)
    with pytest.raises(controller.ContractError, match="link_or_reparse_forbidden"):
        controller._assert_fixed_ignored_file(link, "test")


def test_fixed_ignored_dir_rejects_dotdot_escape_after_resolution(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    (repo / ".qa_local").mkdir(parents=True)
    outside = repo / "outside"
    outside.mkdir()
    monkeypatch.setattr(controller, "REPO_ROOT", repo)
    escaped = repo / ".qa_local" / ".." / "outside"
    with pytest.raises(controller.ContractError, match="outside_fixed_ignored_root"):
        controller._assert_fixed_ignored_dir(escaped, "test")


def test_canonical_hash_is_nfc_sorted_minified_and_rejects_normalized_duplicate_keys():
    left = {"z": "e\u0301", "a": [True, 1]}
    right = {"a": [True, 1], "z": "é"}
    assert controller.canonical_plan_bytes(left) == b'{"a":[true,1],"z":"\xc3\xa9"}'
    assert controller.plan_sha256(left) == controller.plan_sha256(right)
    with pytest.raises(controller.ContractError, match="duplicate_nfc_key"):
        controller.canonical_plan_bytes({"é": 1, "e\u0301": 2})
    with pytest.raises(controller.ContractError, match="float_forbidden"):
        controller.canonical_plan_bytes({"a": 1.5})


def test_plan_is_exact_and_any_mutation_fails_closed():
    plan = controller.controller_plan()
    controller.validate_plan(plan)
    mutated = copy.deepcopy(plan)
    mutated["budget"]["retry_max"] = 1
    with pytest.raises(controller.ContractError, match="controller_plan_drift"):
        controller.validate_plan(mutated)


def test_c1_budget_is_exact_launch_free_zero_retry_and_bounded():
    assert controller.C1_BUDGET == {
        "controller_external_exec_max": 1,
        "retry_max": 0,
        "wall_clock_minutes_max": 10,
        "command_timeout_seconds": 20,
        "application_launch_max": 0,
        "ui_action_max": 0,
        "authentication_action_max": 0,
        "credential_read_or_entry_max": 0,
        "mutation_max": 0,
        "selector_snapshot_max": 3,
        "target_only_read_only_metadata_query_max": 8,
        "raw_sink_hard_bytes_max": 64 * 1024 * 1024,
        "raw_sink_soft_bytes_max": 48 * 1024 * 1024,
    }


def test_every_future_contour_has_enough_triplets_and_c2_no_longer_has_12():
    contours = controller.future_contours()
    for contour in contours:
        assert contour["checkpoint_triplet_max"] >= contour["state_changing_action_max"] + 1
        assert contour["minimum_checkpoint_rule"] == "N_plus_1_with_validated_adjacent_sharing"
    c2 = next(row for row in contours if "c2-" in row["id"])
    assert c2["state_changing_action_max"] == 41
    assert c2["checkpoint_triplet_max"] == 42


def test_global_c4_aggregate_and_c7_budgets_are_exact():
    assert controller.GLOBAL_BUDGET == {
        "concurrency_max": 1,
        "state_changing_action_max": 340,
        "checkpoint_triplet_max": 349,
        "launch_or_relaunch_max": 8,
        "runtime_minutes_max": 180,
        "local_only_qr_decode_max": 20,
        "raw_sink_bytes_max": 1024 * 1024 * 1024,
    }
    contours = controller.future_contours()
    c4 = next(row for row in contours if "c4-" in row["id"])
    assert (c4["slice_count_max"], c4["aggregate_state_changing_action_max"], c4["aggregate_checkpoint_triplet_max"]) == (2, 120, 122)
    c7 = next(row for row in contours if "c7-" in row["id"])
    assert (c7["state_changing_action_max"], c7["checkpoint_triplet_max"]) == (3, 4)


def test_checkpoint_anomaly_and_kill_switch_contracts_are_fail_closed():
    plan = controller.controller_plan()
    assert plan["checkpoint_contract"]["C1-000"]["semantics"] == "mandatory_pre_execution_gate"
    assert plan["checkpoint_contract"]["C1-999"]["cannot_be_omitted_on_failure"] is True
    assert plan["anomaly_contract"]["record_before_continue_or_recovery"] is True
    assert plan["kill_switch"]["sequence"] == ["target_only_force_stop", "home", "post_kill_checkpoint", "capture_shutdown"]
    assert plan["kill_switch"]["invalidates_security_token"] is True


def test_owner_authority_is_category_only_and_does_not_record_constant_otp():
    authority = controller.controller_plan()["owner_authority"]
    assert authority["synthetic_test_only"] is True
    assert authority["not_real_user"] is True
    assert authority["billing_payment_subscription_entitlement_impact_allowed"] is False
    assert authority["constant_otp_value_recorded"] is False
    assert authority["values_local_only_and_redacted"] is True


def test_valid_in_memory_c1_authority_payload_is_only_ready_for_external_executor():
    result = _validate()
    assert result["status"] == "ready_for_separately_authorized_external_c1_executor"
    assert result["fixture_presence"] == "confirmed_by_current_c0p_result"
    assert result["plan_binding_valid"] is True
    assert result["subprocess_started"] is result["device_action"] is result["c1_executed"] is False


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda go, fixture, target, cleanup: go.update(literal_token="GO_FAKE"), "security_go_c1_binding_invalid"),
        (lambda go, fixture, target, cleanup: go.update(target_alias="wrong"), "security_go_c1_binding_invalid"),
        (lambda go, fixture, target, cleanup: go["budget"].update(retry_max=1), "security_go_c1_binding_invalid"),
        (lambda go, fixture, target, cleanup: fixture.update(synthetic_test_only=False), "fixture_passport_binding_invalid"),
        (lambda go, fixture, target, cleanup: fixture.update(synthetic_test_only=1), "fixture_passport_binding_invalid"),
        (lambda go, fixture, target, cleanup: target.update(launch_allowed=True), "target_build_passport_binding_invalid"),
        (lambda go, fixture, target, cleanup: cleanup.update(hard_bytes_max=1), "evidence_cleanup_passport_binding_invalid"),
    ],
)
def test_adversarial_binding_and_scope_mutations_fail(mutation, message):
    plan = controller.controller_plan()
    fixture, target, cleanup = _fixture(), _target(), _cleanup()
    c0p_result = _c0p_result()
    go = _go(plan, fixture, target, cleanup, c0p_result)
    mutation(go, fixture, target, cleanup)
    with pytest.raises(controller.ContractError, match=message):
        _validate(plan, fixture, target, cleanup, c0p_result, go)


def test_expired_or_future_security_go_fails():
    plan = controller.controller_plan()
    fixture, target, cleanup = _fixture(), _target(), _cleanup()
    c0p_result = _c0p_result()
    expired = _go(plan, fixture, target, cleanup, c0p_result)
    expired["expires_at_utc"] = "2026-08-16T13:59:59Z"
    with pytest.raises(controller.ContractError, match="not_current"):
        _validate(plan, fixture, target, cleanup, c0p_result, expired)
    future = _go(plan, fixture, target, cleanup, c0p_result)
    future["issued_at_utc"] = "2026-08-16T14:00:01Z"
    with pytest.raises(controller.ContractError, match="not_current"):
        _validate(plan, fixture, target, cleanup, c0p_result, future)


def test_overlong_c1_go_and_future_passports_fail_in_c1_and_c0p():
    plan = controller.controller_plan()
    fixture, target, cleanup = _fixture(), _target(), _cleanup()
    c0p_result = _c0p_result()
    overlong = _go(plan, fixture, target, cleanup, c0p_result)
    overlong["issued_at_utc"] = "2026-08-16T13:00:00Z"
    with pytest.raises(controller.ContractError, match="validity_exceeds_30_minutes"):
        _validate(plan, fixture, target, cleanup, c0p_result, overlong)

    for passport_name in ("fixture", "target"):
        future_fixture, future_target = _fixture(), _target()
        selected = future_fixture if passport_name == "fixture" else future_target
        selected["issued_at_utc"] = "2026-08-16T14:01:00Z"
        c1_go = _go(plan, future_fixture, future_target, cleanup, c0p_result)
        with pytest.raises(controller.ContractError, match="issued_in_future"):
            _validate(plan, future_fixture, future_target, cleanup, c0p_result, c1_go)

        source_hash = controller._controller_source_sha256()
        c0p = controller.c0p_plan("a" * 40, source_hash, ISSUED, EXPIRES)
        c0p_go = _c0p_go(c0p, future_fixture, future_target, cleanup, source_hash)
        with pytest.raises(controller.ContractError, match="issued_in_future"):
            controller._validate_c0p_authority_payloads(
                c0p,
                controller.canonical_plan_bytes(c0p),
                future_fixture,
                _bytes(future_fixture),
                future_target,
                _bytes(future_target),
                cleanup,
                _bytes(cleanup),
                c0p_go,
                source_sha256=source_hash,
                now=NOW,
            )


def test_c0p_success_writes_canonical_one_shot_files_and_exact_public_projection(monkeypatch, tmp_path, capsys):
    repo = _prepare_c0p_temp_repo(monkeypatch, tmp_path)
    projection = controller.preflight_c0p(now=NOW)
    assert projection == {
        "required_field_count": 2,
        "required_fields_present": True,
        "unexpected_fields_absent": True,
        "phone_format_policy_pass": True,
        "otp_format_policy_pass": True,
    }
    marker_bytes = (repo / controller.C0P_ATTEMPT_REL).read_bytes()
    result_bytes = (repo / controller.C0P_RESULT_REL).read_bytes()
    assert marker_bytes == controller.canonical_plan_bytes(json.loads(marker_bytes))
    assert result_bytes == controller.canonical_plan_bytes(json.loads(result_bytes))
    with pytest.raises(controller.ContractError, match="c0p_one_shot_path_already_exists"):
        controller.preflight_c0p(now=NOW)
    monkeypatch.setattr(controller, "preflight_c0p", lambda: projection)
    assert controller.main(["--preflight-c0p", "--allow-prod-conditional-c0p"]) == 0
    public_output = json.loads(capsys.readouterr().out)
    assert public_output == projection


@pytest.mark.parametrize("failure_point", ["parser", "result_validation", "result_write", "interruption"])
def test_c0p_failure_after_marker_is_durably_one_shot_before_second_secret_read(monkeypatch, tmp_path, failure_point):
    repo = _prepare_c0p_temp_repo(monkeypatch, tmp_path)
    original_read = controller._read_small_bytes
    secret_reads = 0

    def counted_read(*args, **kwargs):
        nonlocal secret_reads
        secret_reads += 1
        return original_read(*args, **kwargs)

    monkeypatch.setattr(controller, "_read_small_bytes", counted_read)
    if failure_point == "parser":
        monkeypatch.setattr(controller, "_parse_c0p_secret", lambda *args: (_ for _ in ()).throw(controller.ContractError("parser_failed")))
    elif failure_point == "result_validation":
        monkeypatch.setattr(controller, "_validate_c0p_result", lambda *args, **kwargs: (_ for _ in ()).throw(controller.ContractError("result_validation_failed")))
    elif failure_point == "result_write":
        monkeypatch.setattr(controller, "_write_c0p_result", lambda *args: (_ for _ in ()).throw(controller.ContractError("result_write_failed")))
    else:
        monkeypatch.setattr(controller, "_parse_c0p_secret", lambda *args: (_ for _ in ()).throw(KeyboardInterrupt("simulated_interruption")))

    with pytest.raises((controller.ContractError, KeyboardInterrupt)):
        controller.preflight_c0p(now=NOW)
    assert (repo / controller.C0P_ATTEMPT_REL).is_file()
    assert secret_reads == 1
    with pytest.raises(controller.ContractError, match="c0p_one_shot_path_already_exists"):
        controller.preflight_c0p(now=NOW)
    assert secret_reads == 1


def test_c0p_cli_keyboard_interrupt_is_public_safe_and_marker_stays_one_shot(monkeypatch, tmp_path, capsys):
    repo = _prepare_c0p_temp_repo(monkeypatch, tmp_path)
    original_preflight = controller.preflight_c0p
    original_parse = controller._parse_c0p_secret
    monkeypatch.setattr(
        controller,
        "_parse_c0p_secret",
        lambda *args: (_ for _ in ()).throw(KeyboardInterrupt("must_not_be_printed")),
    )
    monkeypatch.setattr(controller, "preflight_c0p", lambda: original_preflight(now=NOW))
    assert controller.main(["--preflight-c0p", "--allow-prod-conditional-c0p"]) == 130
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "EPIC-PHONE-001 runtime controller: FAIL (operation_interrupted_fail_closed)\n"
    assert "Traceback" not in captured.err
    assert str(repo) not in captured.err
    assert "must_not_be_printed" not in captured.err
    assert (repo / controller.C0P_ATTEMPT_REL).is_file()

    monkeypatch.setattr(controller, "_parse_c0p_secret", original_parse)
    assert controller.main(["--preflight-c0p", "--allow-prod-conditional-c0p"]) == 1
    second = capsys.readouterr()
    assert "c0p_one_shot_path_already_exists" in second.err
    assert "Traceback" not in second.err


def test_cli_oserror_is_reduced_to_fixed_public_safe_reason(monkeypatch, capsys):
    sensitive = "C:\\private\\secret-path\\qa_user.env"
    monkeypatch.setattr(
        controller,
        "preflight_c0p",
        lambda: (_ for _ in ()).throw(OSError(sensitive)),
    )
    assert controller.main(["--preflight-c0p", "--allow-prod-conditional-c0p"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "EPIC-PHONE-001 runtime controller: FAIL (local_io_error_fail_closed)\n"
    assert sensitive not in captured.err
    assert "Traceback" not in captured.err


def test_cli_default_modes_do_not_call_preflight_or_read_ignored_storage(monkeypatch, capsys):
    monkeypatch.setattr(controller, "preflight_c1", lambda: (_ for _ in ()).throw(AssertionError("local read")))
    assert controller.main(["--validate-only"]) == 0
    validate_result = json.loads(capsys.readouterr().out)
    assert validate_result["ignored_storage_read"] is False
    assert controller.main(["--dry-run"]) == 0
    dry_result = json.loads(capsys.readouterr().out)
    assert dry_result["ignored_storage_read"] is False
    assert dry_result["secret_presence_checked"] is False
    assert dry_result["plan_contract_valid"] is True
    assert dry_result["c0p_guarded_interface_present"] is True
    assert "plan" not in dry_result
    assert "plan_sha256" not in dry_result


def test_c1_preflight_requires_literal_allow_flag_before_any_local_read(monkeypatch, capsys):
    called = False

    def forbidden_call():
        nonlocal called
        called = True
        raise AssertionError("must not run")

    monkeypatch.setattr(controller, "preflight_c1", forbidden_call)
    assert controller.main(["--preflight-c1"]) == 1
    assert called is False
    assert "requires_explicit_allow_flag" in capsys.readouterr().err


def test_allow_flag_is_rejected_outside_c1_preflight(capsys):
    assert controller.main(["--dry-run", "--allow-prod-conditional-c1"]) == 1
    assert "valid_only_with_preflight_c1" in capsys.readouterr().err


def test_controller_source_has_no_subprocess_executor_or_environment_secret_read():
    source = Path(controller.__file__).read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "os.environ" not in source
    assert "os.getenv" not in source
    assert "shell=True" not in source
    assert "adb " not in source.lower()


def test_go_token_rejects_uppercase_short_or_nonhex_hash():
    for invalid in ("a" * 63, "A" * 64, "g" * 64):
        with pytest.raises(controller.ContractError):
            controller.expected_go_token(invalid)

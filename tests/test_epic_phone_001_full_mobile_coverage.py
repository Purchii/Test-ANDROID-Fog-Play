from __future__ import annotations

import copy
import json
from datetime import UTC, datetime, timedelta

import pytest

from automation.phone import epic_phone_001_full_mobile_coverage as sut


def test_crosswalk_is_exact_43_rows_once_and_lossless():
    source = sut._load_crosswalk()
    rows = sut.coverage_rows()
    assert len(source) == len(rows) == 43
    assert tuple(row["source_row_id"] for row in rows) == sut.EXPECTED_IDS
    assert len({(row["source_task"], row["source_row_id"]) for row in rows}) == 43
    for original, projected in zip(source, rows):
        assert all(projected[key] == value for key, value in original.items())


def test_only_exact_tracked_task058a_rows_are_inherited():
    assert sut._task058a_inheritance_valid() is True
    covered = [row for row in sut.coverage_rows() if row["terminal_status"] == "covered"]
    assert {row["source_row_id"] for row in covered} == sut.INHERITED_IDS
    assert all(row["evidence_status"] == "confirmed" for row in covered)
    assert all(row["modality_complete"] == "true" for row in covered)
    assert all(row["cleanup_status"] == "confirmed" for row in covered)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("task_id",), "TASK-999"),
        (("run_id",), "unrelated-run"),
        (("execution_status",), "pass"),
        (("payload", "readiness_observed_pass_count"), 7),
        (("payload", "readiness_blocked_count"), 0),
        (("payload", "go_runtime"), True),
        (("payload", "launch_count"), 0),
        (("payload", "runtime_checkpoint_count"), 0),
        (("payload", "first_launch_restored"), True),
    ],
)
def test_task058a_inheritance_rejects_identity_and_semantic_drift(path, value):
    summary = json.loads(sut.TASK058A_SUMMARY.read_text(encoding="utf-8"))
    target = summary
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert sut._task058a_inheritance_payload_valid(summary, sut.TASK058A_SCENARIOS.read_bytes()) is False


def test_task058a_inheritance_rejects_future_authority_timestamp():
    summary = json.loads(sut.TASK058A_SUMMARY.read_text(encoding="utf-8"))
    future = datetime.now(UTC) + timedelta(days=1)
    summary["generated_at_utc"] = future.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    assert sut._task058a_inheritance_payload_valid(summary, sut.TASK058A_SCENARIOS.read_bytes()) is False


def test_remaining_required_phone_rows_are_terminal_external_blocks():
    rows = sut.coverage_rows()
    remaining = [
        row for row in rows
        if row["phone_applicability"] == "phone_required" and row["source_row_id"] not in sut.INHERITED_IDS
    ]
    assert remaining
    assert all(row["terminal_status"] == "blocked_by_external_state" for row in remaining)
    assert all(row["evidence_status"] == "unknown" for row in remaining)
    assert all(row["reason_code"] == "synthetic_fixture_classification_absent_and_no_literal_runtime_go" for row in remaining)
    assert all(row["epic_release_effect"] == "blocks_release" for row in remaining)


def test_deferred_and_audit_rows_preserve_crosswalk_semantics():
    source = {row["source_row_id"]: row for row in sut._load_crosswalk()}
    projected = {row["source_row_id"]: row for row in sut.coverage_rows()}
    assert set(sut.DEFERRED_IDS) == {
        "phone-coverage-021", "phone-coverage-022", "phone-coverage-023",
        "phone-coverage-024", "phone-coverage-026", "A001", "A016",
    }
    for row_id in sut.DEFERRED_IDS:
        assert projected[row_id]["terminal_status"] == source[row_id]["current_status"]
        assert projected[row_id]["epic_release_effect"] == source[row_id]["release_effect"]
    assert projected["A001"]["terminal_status"] == "blocked_by_tooling"
    assert projected["A001"]["modality_complete"] == "false"


def test_readiness_preserves_row03_unknown_consumed_first_launch_and_security_verdict():
    rows = sut.readiness_rows()
    assert len(rows) == 7
    assert rows[2]["authority_id"] == "epic-readiness-03"
    assert rows[2]["evidence_status"] == "unknown"
    assert rows[2]["reason_code"] == "current_row03_unknown_owner_override_not_reusable"
    assert rows[4]["reason_code"] == "synthetic_fixture_classification_absent"
    assert rows[5]["terminal_status"] == "consumed_not_restorable"
    assert all(row["security_verdict"] == sut.SECURITY_VERDICT for row in rows)


def test_all_runtime_stages_are_blocked_and_repository_stage_only_closes_ledger():
    rows = sut.stage_rows()
    assert len(rows) == 6
    assert all(row["runtime_action_count"] == "0" for row in rows)
    assert all(row["terminal_status"] == "blocked_by_external_state" for row in rows[:5])
    assert rows[5]["terminal_status"] == "closed_by_ledger"
    assert all(row["release_effect"] == "blocks_release" for row in rows)


def test_unified_budget_is_zero_and_contains_checkpoint_and_kill_switch_contracts():
    rows = sut.budget_rows()
    assert len(rows) == 10
    assert {row["budget_kind"] for row in rows} == {"action", "evidence_resource", "time_resource"}
    assert all(row["maximum"] == row["actual"] == "0" for row in rows)
    assert all(
        row["checkpoint_before_every_action"] == "required_for_conditional_action_or_not_applicable_if_forbidden"
        for row in rows if row["budget_kind"] == "action"
    )
    assert all(
        row["checkpoint_before_every_action"] == "passive_prerequisite_exempt_from_recursive_checkpoint"
        for row in rows if row["budget_kind"] == "evidence_resource"
    )
    assert next(row for row in rows if row["budget_kind"] == "time_resource")["checkpoint_before_every_action"] == "not_an_action"
    assert all(row["kill_switch"] == "target_only_force_stop_then_home_then_capture_shutdown" for row in rows)
    assert {row["classification"] for row in rows} == {"PROD_CONDITIONAL", "PROD_FORBIDDEN"}


def test_zero_action_cleanup_and_empty_runtime_anomaly_ledger_are_explicit():
    assert sut.anomaly_rows() == []
    cleanup = sut.cleanup_rows()[0]
    assert cleanup["device_cleanup_required"] == "false_no_device_actions"
    assert cleanup["target_force_stop"] == cleanup["home"] == cleanup["capture_shutdown"] == "not_run"
    assert cleanup["forbidden_action_count"] == "0"
    assert cleanup["evidence_status"] == "confirmed"


def test_summary_blocks_release_and_has_all_zero_action_counters():
    summary = json.loads(sut.expected_bundle()[sut.REPORT_OUTPUT])
    payload = summary["payload"]
    assert summary["execution_status"] == "closed_by_ledger"
    assert summary["coverage_status"] == "partial_blocked"
    assert summary["release_effect"] == "blocks_release"
    assert payload["crosswalk_row_count"] == 43
    assert payload["covered_row_count"] == 3
    assert payload["required_phone_blocked_count"] == 33
    assert payload["deferred_or_audit_row_count"] == 7
    assert payload["inherited_task058a_row_count"] == 3
    assert payload["current_row03_unknown"] is True
    assert payload["clean_first_launch_consumed"] is True
    assert payload["security_verdict"] == sut.SECURITY_VERDICT
    for key in (
        "action_count", "device_action_count", "application_action_count",
        "auth_entry_action_count", "credential_value_access_count",
        "forbidden_action_count", "anomaly_count",
    ):
        assert payload[key] == 0


def test_expected_bundle_is_deterministic_and_valid():
    first = sut.expected_bundle()
    second = sut.expected_bundle()
    assert first == second
    sut.validate_bundle(first)


def test_epic_timestamp_is_not_future_and_follows_inherited_authority():
    summary = json.loads(sut.expected_bundle()[sut.REPORT_OUTPUT])
    epic_at = datetime.fromisoformat(summary["generated_at_utc"].replace("Z", "+00:00"))
    inherited_at = datetime.fromisoformat(sut.task058a_contract.GENERATED_AT.replace("Z", "+00:00"))
    assert inherited_at <= epic_at <= datetime.now(UTC)


def test_bundle_drift_fails_closed():
    bundle = sut.expected_bundle()
    changed = copy.deepcopy(bundle)
    changed[sut.COVERAGE_OUTPUT] += b"unexpected\n"
    with pytest.raises(sut.ContractError, match="bundle_content_drift"):
        sut.validate_bundle(changed)


def test_inheritance_failure_blocks_all_required_rows(monkeypatch):
    monkeypatch.setattr(sut, "_task058a_inheritance_valid", lambda: False)
    rows = sut.coverage_rows()
    inherited = [row for row in rows if row["source_row_id"] in sut.INHERITED_IDS]
    assert all(row["terminal_status"] == "blocked_by_external_state" for row in inherited)
    assert all(row["evidence_status"] == "unknown" for row in inherited)


def test_cli_is_fixed_path_only():
    assert sut.main(["--validate-only"]) == 0
    with pytest.raises(SystemExit):
        sut.main(["--validate-report", "--input", "elsewhere.json"])


def test_source_has_no_device_subprocess_or_arbitrary_input_capability():
    text = sut.Path(sut.__file__).read_text(encoding="utf-8")
    assert "import subprocess" not in text
    assert "adb" not in text.lower()
    assert "adapter-input" not in text
    assert ".qa_local" not in text

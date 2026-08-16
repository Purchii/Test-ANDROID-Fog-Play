from __future__ import annotations

import copy
import json

import pytest

from automation.phone import task058a_phone_launch_readiness_pre_auth_continuation as sut


def test_readiness_is_exact_six_of_seven_under_literal_owner_override():
    rows = sut.baseline_readiness_rows()
    assert len(rows) == 7
    assert [row["authority_id"] for row in rows] == list(sut.AUTHORITY_IDS)
    assert sum(row["terminal_status"] == "observed_pass" for row in rows) == 6
    assert all(row["reviewer_gate"] == "GO_RUNTIME_OWNER_OVERRIDE" for row in rows)
    waived = rows[2]
    assert waived == {
        "authority_id": sut.AUTHORITY_IDS[2],
        "subject_alias": "phone-current-001",
        "freshness": "fresh_current_run",
        "evidence_status": "unknown",
        "evidence_ids": "task058a-owner-override-authority",
        "reviewer_gate": "GO_RUNTIME_OWNER_OVERRIDE",
        "expires_at": sut.EXPIRES_AT,
        "terminal_status": "blocked_by_external_state",
        "reason_code": "selector_unrelated_delta_waived_owner_override",
        "release_effect": "blocks_release",
    }


def test_rows_01_02_and_04_through_07_have_exact_confirmed_authority_shape():
    rows = sut.baseline_readiness_rows()
    assert "task058a-owner-team-confirmation" in rows[0]["evidence_ids"]
    assert "task058a-retained-machine-authority" in rows[1]["evidence_ids"]
    assert "task058a-current-opening-package-observation" in rows[0]["evidence_ids"]
    assert rows[3]["reason_code"] == "zero_reinstall_uninstall_reset_retry"
    assert rows[4]["reason_code"] == "pre_auth_no_real_session_confirmed"
    assert rows[5]["reason_code"] == "clean_first_launch_consumed_once_not_restored"
    assert rows[6]["reason_code"] == "evidence_budget_cleanup_reviewed_owner_override"
    assert all(rows[index]["evidence_status"] == "confirmed" for index in (0, 1, 3, 4, 5, 6))


def test_three_passports_are_observed_and_reviewed_under_override():
    rows = sut.baseline_passport_rows()
    assert [row["passport_type"] for row in rows] == list(sut.PASSPORT_TYPES)
    assert all(row["task_id"] == sut.TASK_ID and row["run_id"] == sut.RUN_ID for row in rows)
    assert all(row["observation_status"] == "observed_confirmed" for row in rows)
    assert all(row["evidence_status"] == "confirmed" for row in rows)
    assert all(row["reviewer_gate"] == "GO_RUNTIME_OWNER_OVERRIDE" for row in rows)
    assert all(row["terminal_status"] == "observed_pass" for row in rows)


def test_projection_records_collector_block_without_retry_mutation_launch_or_delta_claim():
    collector = sut.baseline_projection()["collector"]
    assert collector == {
        "execution_status": "blocked_artifact_metadata_ambiguity",
        "native_stdout_stderr_direct_capture": True,
        "retry_count": 0,
        "mutation_count": 0,
        "launch_count": 0,
        "unrelated_package_delta_count": None,
    }


def test_runtime_scenarios_cover_three_inherited_rows_losslessly():
    rows = sut.baseline_scenario_rows()
    assert [row["source_crosswalk_id"] for row in rows[:3]] == ["phone-coverage-001", "phone-coverage-017", "A002"]
    assert all(row["status"] == "covered" for row in rows[:3])
    assert all(row["evidence_status"] == "confirmed" for row in rows[:3])
    assert rows[2]["from_checkpoint_id"] == "task058a-checkpoint-001"
    assert rows[2]["to_checkpoint_id"] == "task058a-checkpoint-002"
    assert rows[2]["screenshot_id"] == "task058a-screenshot-pair-001-002"


def test_discovered_auth_boundary_and_visual_xml_mismatch_are_first_class():
    rows = sut.baseline_scenario_rows()
    boundary, anomaly = rows[3:]
    assert boundary["status"] == "blocked_by_boundary"
    assert boundary["reason_code"] == "authentication_boundary_not_followed"
    assert anomaly["status"] == "covered"
    assert anomaly["state_category"] == "visual_overlay_anomaly"
    assert anomaly["reason_code"] == "partial_green_left_edge_overlay_absent_from_ui_tree"
    assert anomaly["screenshot_id"] != "none" and anomaly["ui_tree_id"] != "none"


def test_cleanup_records_one_launch_zero_actions_and_no_restore():
    row = sut.baseline_cleanup_rows()[0]
    assert row["target_force_stop"] == row["home"] == row["capture_shutdown"] == "confirmed"
    assert row["launch_count"] == "1"
    assert row["safe_pre_auth_action_count"] == row["forbidden_action_count"] == "0"
    assert row["first_launch_restored"] == "not_claimed"
    assert row["reviewer_gate"] == "GO_RUNTIME_OWNER_OVERRIDE"
    assert row["terminal_status"] == "observed_pass"


def test_actual_projection_and_bundle_validate():
    projection = sut.baseline_projection()
    sut.validate_projection(projection)
    sut.validate_bundle(sut.expected_bundle())


def test_summary_distinguishes_override_coverage_pass_from_release_block():
    summary = json.loads(sut.expected_bundle()[sut.REPORT_OUTPUT])
    payload = summary["payload"]
    assert payload["readiness_observed_pass_count"] == 6
    assert payload["readiness_blocked_count"] == 1
    assert payload["security_gate"] == "GO_RUNTIME_OWNER_OVERRIDE"
    assert payload["go_runtime"] is False
    assert payload["go_runtime_owner_override"] is True
    assert payload["launch_count"] == 1
    assert payload["safe_pre_auth_action_count"] == payload["forbidden_action_count"] == 0
    assert payload["runtime_checkpoint_count"] == 2
    assert payload["inherited_scenario_covered_count"] == 3
    assert payload["authentication_boundary_count"] == 1
    assert payload["visual_xml_mismatch_anomaly_count"] == 1
    assert summary["coverage_status"] == "covered"
    assert summary["execution_status"] == "partial_blocked"
    assert summary["release_effect"] == "blocks_release"
    assert summary["blocked_reasons"] == ["selector_unrelated_delta_waived_owner_override_blocks_release"]


def test_legacy_go_runtime_and_false_seven_of_seven_are_rejected():
    projection = copy.deepcopy(sut.baseline_projection())
    projection["security_gate"] = "GO_RUNTIME"
    with pytest.raises(sut.ContractError, match="security_gate_invalid"):
        sut.validate_projection(projection)
    projection = copy.deepcopy(sut.baseline_projection())
    projection["readiness"][2].update(
        evidence_status="confirmed", terminal_status="observed_pass",
        release_effect="candidate_evidence",
    )
    with pytest.raises(sut.ContractError, match="readiness_exact"):
        sut.validate_projection(projection)


def test_owner_override_row03_cannot_be_promoted_or_reworded():
    for field, value in (("reason_code", "waived"), ("evidence_status", "confirmed"), ("evidence_ids", "other-authority")):
        projection = copy.deepcopy(sut.baseline_projection())
        projection["readiness"][2][field] = value
        with pytest.raises(sut.ContractError, match="readiness_exact"):
            sut.validate_projection(projection)


def test_runtime_budget_and_modality_guards_remain_fail_closed():
    projection = copy.deepcopy(sut.baseline_projection())
    projection["cleanup"][0]["launch_count"] = "2"
    with pytest.raises(sut.ContractError, match="cleanup_exact"):
        sut.validate_projection(projection)
    projection = copy.deepcopy(sut.baseline_projection())
    projection["scenarios"][0]["screenshot_id"] = "none"
    with pytest.raises(sut.ContractError, match="scenario_exact"):
        sut.validate_projection(projection)


@pytest.mark.parametrize(
    ("ledger", "row", "field", "value", "error"),
    [
        ("readiness", 0, "freshness", "historical", "readiness_exact"),
        ("readiness", 0, "reason_code", "other_reason", "readiness_exact"),
        ("passports", 0, "action_budget", "launch_2", "passport_exact"),
        ("passports", 1, "retention_redaction", "none", "passport_exact"),
        ("passports", 2, "kill_switch", "none", "passport_exact"),
        ("scenarios", 0, "reachable", "false", "scenario_exact"),
        ("scenarios", 1, "row_id", "task058a-scenario-001", "scenario_exact"),
        ("scenarios", 2, "action_category", "observe_only", "scenario_exact"),
        ("scenarios", 3, "screenshot_id", "none", "scenario_exact"),
        ("cleanup", 0, "target_force_stop", "blocked", "cleanup_exact"),
        ("cleanup", 0, "reviewer_gate", "NO_GO", "cleanup_exact"),
        ("cleanup", 0, "launch_count", "0", "cleanup_exact"),
    ],
)
def test_completed_projection_rejects_any_reviewed_ledger_drift(ledger, row, field, value, error):
    projection = copy.deepcopy(sut.baseline_projection())
    projection[ledger][row][field] = value
    with pytest.raises(sut.ContractError, match=error):
        sut.validate_projection(projection)


def test_first_launch_restore_claim_remains_forbidden():
    projection = copy.deepcopy(sut.baseline_projection())
    projection["cleanup"][0]["first_launch_restored"] = "confirmed"
    with pytest.raises(sut.ContractError, match="cleanup_exact"):
        sut.validate_projection(projection)


@pytest.mark.parametrize(
    "unsafe",
    [r"C:\private\raw.txt", ".qa_local/task058a/raw", "a" * 64, "https://private.example/value", "private.application.package"],
)
def test_public_values_reject_raw_shaped_content(unsafe):
    with pytest.raises(sut.ContractError, match="unsafe_public_value"):
        sut._safe(unsafe, "synthetic")


def test_cli_is_fixed_path_only():
    assert sut.main(["--validate-only"]) == 0
    with pytest.raises(SystemExit):
        sut.main(["--validate-report", "--input", "elsewhere.json"])

from __future__ import annotations

import copy
import json

import pytest

from automation.phone import task058_phone_first_launch_pre_auth_coverage as sut


def test_exact_seven_readiness_rows_are_non_inferential():
    rows = sut.readiness_rows()
    assert len(rows) == 7
    assert [row["row_id"] for row in rows] == [
        "task057-authority-01-canonical-phone-full",
        "task057-authority-02-installed-compatibility",
        "task057-authority-03-current-phone-selector",
        "task057-authority-04-downgrade-safety",
        "task057-authority-05-synthetic-session",
        "task057-authority-06-clean-first-launch",
        "task057-authority-07-evidence-cleanup-security",
    ]
    assert [row["subject_alias"] for row in rows] == [
        "task058-selected-phone-full-001", "installed-phone-full-build",
        "phone-current-001", "ordinary-downgrade-guard",
        "synthetic-session-passport", "clean-first-launch-fixture",
        "evidence-cleanup-passport",
    ]
    assert sum(row["terminal_status"] == "observed_pass" for row in rows) == 2
    assert sum(row["terminal_status"].startswith("blocked_by_") for row in rows) == 5
    assert rows[4]["reason_code"] == "synthetic_session_passport_absent"
    assert rows[5]["reason_code"] == "clean_first_launch_fixture_passport_absent"
    assert rows[6]["reason_code"] == "runtime_evidence_cleanup_passport_absent"
    assert [row["reviewer_gate"] for row in rows[4:]] == ["BLOCK_RUNTIME"] * 3
    assert [row["evidence_ids"] for row in rows[4:]] == ["none"] * 3
    assert rows[0]["evidence_ids"].split(";") == [
        "task058-candidate-integrity",
        "task058-candidate-provenance",
        "task058-candidate-signing",
        "task058-candidate-version",
        "task058-candidate-min-sdk",
        "task058-candidate-target-sdk",
        "task058-candidate-abi",
        "task058-candidate-install-compatibility",
    ]


def test_package_budget_and_hard_stop_are_exact():
    rows = sut.action_rows()
    counts = {row["action_alias"]: (int(row["intended_count"]), int(row["observed_count"])) for row in rows}
    assert counts["target_uninstall"] == (1, 1)
    assert counts["target_absence"] == (1, 1)
    assert counts["ordinary_install"] == (1, 1)
    assert counts["retry"] == (0, 0)
    assert counts["launch_navigation"] == (0, 0)
    assert counts["installed_candidate_equivalence"] == (1, 0)
    assert counts["unrelated_package_delta"] == (1, 0)


def test_exact_three_inherited_scenarios_close_blocked_not_covered():
    rows = sut.scenario_rows()
    assert [row["source_crosswalk_id"] for row in rows] == ["phone-coverage-001", "phone-coverage-017", "A002"]
    assert all(row["status"] == "blocked_by_external_state" for row in rows)
    assert all(row["release_effect"] == "blocks_release" for row in rows)
    assert all(row["screenshot_id"] == row["ui_tree_id"] == row["log_marker_id"] == "none" for row in rows)


def test_a002_is_losslessly_terminal_in_transition_ledger():
    screens = sut.screen_state_rows()
    transitions = sut.transition_rows()
    assert [row["source_crosswalk_id"] for row in screens] == ["phone-coverage-001", "phone-coverage-017"]
    assert len(transitions) == 1
    row = transitions[0]
    assert row["source_crosswalk_id"] == "A002"
    assert row["status"] == "blocked_by_external_state"
    assert row["from_checkpoint_id"] != row["to_checkpoint_id"]
    assert row["screenshot_id"] == row["ui_tree_id"] == row["log_marker_id"] == "none"


def test_summary_never_claims_runtime_or_coverage():
    bundle = sut.expected_bundle()
    summary = json.loads(bundle[sut.REPORT_OUTPUT])
    payload = summary["payload"]
    assert summary["execution_status"] == "blocked"
    assert summary["coverage_status"] == "blocked"
    assert summary["release_effect"] == "blocks_release"
    assert payload["go_runtime"] is False
    assert payload["launch_count"] == 0
    assert payload["runtime_checkpoint_count"] == 0
    assert payload["covered_scenario_count"] == 0
    assert payload["blocked_scenario_count"] == 3
    assert payload["anomaly_count"] == len(sut.anomaly_rows())
    assert payload["uninstall_count"] == 1
    assert payload["ordinary_install_count"] == 1


def test_all_eleven_process_anomalies_are_retained():
    rows = sut.anomaly_rows()
    assert [row["row_id"] for row in rows] == [f"TASK058-PROCESS-ANOMALY-{n:03d}" for n in range(1, 12)]
    assert all(row["evidence_status"] == "confirmed" for row in rows)
    assert all(row["product_impact"] == "none" for row in rows)


def test_local_temp_cleanup_is_confirmed_without_runtime_cleanup_claim():
    row = sut.cleanup_rows()[0]
    assert row["local_temp_cleanup"] == "confirmed_removed"
    assert row["runtime_cleanup"] == "not_run_security_block_runtime"
    assert row["package_end_state"] == "install_success_package_present_equivalence_unverified"


def test_owner_actions_require_fresh_non_reinstall_validation_and_all_runtime_passports():
    summary = json.loads(sut.expected_bundle()[sut.REPORT_OUTPUT])
    assert summary["unknowns"][-2:] == [
        {"id": "task058-owner-action-01", "evidence_status": "unknown", "reason_code": "fresh_launch_free_postinstall_validation_authority_and_security_plan_required_without_reinstall"},
        {"id": "task058-owner-action-02", "evidence_status": "unknown", "reason_code": "three_runtime_passports_and_new_security_go_runtime_required"},
    ]


def test_expected_bundle_validates_and_disk_bundle_matches():
    sut.validate_bundle(sut.expected_bundle())
    sut.validate_bundle(sut.disk_bundle())


def test_summary_tampering_fails_closed():
    bundle = dict(sut.expected_bundle())
    summary = json.loads(bundle[sut.REPORT_OUTPUT])
    summary["payload"]["go_runtime"] = True
    bundle[sut.REPORT_OUTPUT] = sut._json_bytes(summary)
    with pytest.raises(sut.ContractError, match="summary_semantic_or_hash_drift"):
        sut.validate_bundle(bundle)


def test_readiness_tampering_fails_closed():
    bundle = dict(sut.expected_bundle())
    rows = copy.deepcopy(sut.readiness_rows())
    rows[4]["terminal_status"] = "observed_pass"
    bundle[sut.LEDGERS["readiness"]] = sut._csv_bytes(sut.READINESS_HEADERS, rows)
    with pytest.raises(sut.ContractError):
        sut.validate_bundle(bundle)


@pytest.mark.parametrize(
    "unsafe",
    [r"C:\\private\\candidate.apk", ".qa_local/evidence/raw", "a" * 64, "private.application.package", "https://private.example/value"],
)
def test_public_values_reject_raw_shaped_data(unsafe):
    with pytest.raises(sut.ContractError):
        sut._safe(unsafe, "synthetic")


def test_cli_is_fixed_path_repository_only():
    assert sut.main(["--validate-only"]) == 0
    assert sut.main(["--validate-report"]) == 0
    with pytest.raises(SystemExit):
        sut.main(["--validate-only", "--input", "elsewhere"])

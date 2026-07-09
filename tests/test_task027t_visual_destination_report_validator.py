import json

from automation.native_regression.validate_task027t_visual_destination_report import (
    main,
    validate_report,
    validate_report_shape,
)


REPORT_PATH = "docs/qa/reports/task027t_continue_visual_destination_screen_coverage.summary.json"


def _valid_report():
    with open(REPORT_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def test_validator_accepts_task027t_blocked_preflight_report():
    assert validate_report_shape(_valid_report()) == []


def test_validator_rejects_destination_covered_without_visual_proof():
    report = _valid_report()
    row = report["target_destination_ledger"][0]
    row["coverage_status"] = "covered"
    row["evidence_status"] = "confirmed"
    row["visual_destination_proof"] = False
    row["runtime_evidence_collected"] = True
    row["evidence_ids"] = ["rt027t-cp001-journal"]

    errors = validate_report_shape(report)

    assert any("cannot be covered without visual_destination_proof=true" in error for error in errors)


def test_validator_rejects_destination_covered_without_fresh_task027t_evidence():
    report = _valid_report()
    report["runtime_execution_status"] = "partial"
    row = report["target_destination_ledger"][0]
    row["coverage_status"] = "covered"
    row["evidence_status"] = "confirmed"
    row["visual_destination_proof"] = True
    row["runtime_evidence_collected"] = True
    row["evidence_ids"] = []

    errors = validate_report_shape(report)

    assert any("cannot be covered without fresh TASK-027T evidence IDs" in error for error in errors)


def test_validator_rejects_destination_covered_with_wrong_fresh_task027t_evidence():
    report = _valid_report()
    row = report["target_destination_ledger"][0]
    row["coverage_status"] = "covered"
    row["evidence_status"] = "confirmed"
    row["visual_destination_proof"] = True
    row["runtime_evidence_collected"] = True
    row["evidence_ids"] = ["rt027t-cp001-post-launch"]

    errors = validate_report_shape(report)

    assert any("cannot be covered without destination-specific TASK-027T visual evidence" in error for error in errors)


def test_validator_rejects_prior_task_evidence_as_task027t_visual_proof():
    report = _valid_report()
    report["runtime_execution_status"] = "partial"
    row = report["target_destination_ledger"][0]
    row["coverage_status"] = "covered"
    row["evidence_status"] = "confirmed"
    row["visual_destination_proof"] = True
    row["runtime_evidence_collected"] = True
    row["evidence_ids"] = ["rt027s-cp086-loader-timeout-after-2min"]

    errors = validate_report_shape(report)

    assert any("unsupported TASK-027T evidence id" in error for error in errors)
    assert any("cannot be covered without fresh TASK-027T evidence IDs" in error for error in errors)


def test_validator_rejects_runtime_blocked_with_evidence_ids():
    report = _valid_report()
    report["run_status"] = "blocked"
    report["runtime_execution_status"] = "blocked"
    report["target_destination_ledger"][0]["evidence_ids"] = ["rt027t-cp001-journal"]

    errors = validate_report_shape(report)

    assert "target_destination_ledger[0].evidence_ids must be empty while runtime is not run or blocked." in errors


def test_validator_rejects_runtime_blocked_with_destination_claim():
    report = _valid_report()
    report["run_status"] = "blocked"
    report["runtime_execution_status"] = "blocked"
    report["target_destination_ledger"][0]["coverage_status"] = "covered"
    report["target_destination_ledger"][0]["visual_destination_proof"] = True
    report["target_destination_ledger"][0]["runtime_evidence_collected"] = True

    errors = validate_report_shape(report)

    assert (
        "target_destination_ledger[0].visual_destination_proof must be false while runtime is not run or blocked."
        in errors
    )
    assert (
        "target_destination_ledger[0].runtime_evidence_collected must be false while runtime is not run or blocked."
        in errors
    )
    assert any("coverage_status must be not-run or blocked while runtime is not run or blocked" in error for error in errors)


def test_validator_rejects_missing_preflight_blocker_for_missing_lane_status():
    report = _valid_report()
    report["run_status"] = "blocked_missing_local_selected_lane"
    report["runtime_execution_status"] = "blocked"
    report["preflight_blockers"] = []

    errors = validate_report_shape(report)

    assert "preflight_blockers must be a non-empty list for missing-lane blocker." in errors


def test_validator_rejects_missing_local_lane_flag_drift():
    report = _valid_report()
    report["run_status"] = "blocked_missing_local_selected_lane"
    report["runtime_execution_status"] = "blocked"
    report["runtime_scope"]["local_selected_lane_material_present"] = True

    errors = validate_report_shape(report)

    assert "runtime_scope.local_selected_lane_material_present must be false for missing-lane blocker." in errors


def test_validator_rejects_qr_navigation_followed():
    report = _valid_report()
    report["target_destination_ledger"][1]["qr_navigation_followed"] = True

    errors = validate_report_shape(report)

    assert "target_destination_ledger[1].qr_navigation_followed must be false." in errors


def test_validator_rejects_covered_qr_without_local_only_decode():
    report = _valid_report()
    row = report["target_destination_ledger"][1]
    row["coverage_status"] = "covered"
    row["evidence_status"] = "confirmed"
    row["visual_destination_proof"] = True
    row["runtime_evidence_collected"] = True
    row["evidence_ids"] = ["rt027t-cp013-steam-topup-qr-after-center"]
    row["qr_decode_status"] = "not_run"

    errors = validate_report_shape(report)

    assert any("cannot be covered without local_only_decoded QR metadata" in error for error in errors)


def test_validator_rejects_qr_decode_with_wrong_destination_evidence():
    report = _valid_report()
    row = report["target_destination_ledger"][1]
    row["coverage_status"] = "covered"
    row["evidence_status"] = "confirmed"
    row["visual_destination_proof"] = True
    row["runtime_evidence_collected"] = True
    row["evidence_ids"] = ["rt027t-cp015-feedback-qr-after-center"]
    row["qr_decode_status"] = "local_only_decoded"

    errors = validate_report_shape(report)

    assert any("cannot be covered without destination-specific TASK-027T visual evidence" in error for error in errors)
    assert any("qr_decode_status cannot be local_only_decoded without destination-specific TASK-027T visual evidence" in error for error in errors)


def test_validator_rejects_app_shell_loader_gate_marked_covered():
    report = _valid_report()
    loader_gate = report["route_gate_ledger"][1]
    loader_gate["coverage_status"] = "covered"
    loader_gate["runtime_evidence_collected"] = True
    loader_gate["evidence_ids"] = ["rt027t-cp011-after-grid-dpad-left"]

    errors = validate_report_shape(report)

    assert "route_gate_ledger app_shell_loader_after_launcher_entry must not be marked covered." in errors


def test_validator_rejects_loader_counted_as_catalog_or_destination():
    report = _valid_report()
    report["coverage_claims"]["app_shell_loader_counts_as_catalog"] = True
    report["coverage_claims"]["app_shell_loader_counts_as_destination"] = True

    errors = validate_report_shape(report)

    assert "coverage_claims.app_shell_loader_counts_as_catalog must be false." in errors
    assert "coverage_claims.app_shell_loader_counts_as_destination must be false." in errors


def test_validator_rejects_prior_reports_counted_as_visual_proof():
    report = _valid_report()
    report["coverage_claims"]["prior_task027r_or_task027s_evidence_counts_as_task027t_visual_proof"] = True

    errors = validate_report_shape(report)

    assert "coverage_claims.prior_task027r_or_task027s_evidence_counts_as_task027t_visual_proof must be false." in errors


def test_validator_rejects_runtime_executed_claim_while_blocked():
    report = _valid_report()
    report["run_status"] = "blocked"
    report["runtime_execution_status"] = "blocked"
    report["coverage_claims"]["runtime_executed"] = True
    report["coverage_claims"]["loaded_actionable_app_state_reconfirmed"] = True

    errors = validate_report_shape(report)

    assert "coverage_claims.runtime_executed cannot be true when runtime_execution_status is not_run or blocked." in errors
    assert (
        "coverage_claims.loaded_actionable_app_state_reconfirmed cannot be true when runtime_execution_status is not_run or blocked."
        in errors
    )


def test_validator_rejects_top_level_covered_without_all_destinations_covered():
    report = _valid_report()
    report["run_status"] = "covered"
    report["runtime_execution_status"] = "covered"
    report["runtime_scope"]["runtime_performed"] = True
    report["runtime_scope"]["local_selected_lane_material_present"] = True
    report["runtime_scope"]["adb_or_device_commands_performed"] = True
    report["checkpoint_modality_audit"]["runtime_checkpoints_captured"] = True
    report["checkpoint_modality_audit"]["screenshot_visual_inspection"] = "confirmed_local_only"
    report["checkpoint_modality_audit"]["xml_capture"] = "confirmed_local_only"
    report["coverage_claims"]["runtime_executed"] = True
    report["coverage_claims"]["loaded_actionable_app_state_reconfirmed"] = True
    report["target_destination_ledger"][0]["coverage_status"] = "blocked_by_tooling"
    report["target_destination_ledger"][0]["visual_destination_proof"] = False
    report["target_destination_ledger"][0]["runtime_evidence_collected"] = False
    report["target_destination_ledger"][0]["evidence_ids"] = []
    report["coverage_claims"]["session_journal_visually_covered"] = False

    errors = validate_report_shape(report)

    assert any("runtime_execution_status covered requires covered destination rows" in error for error in errors)


def test_validator_rejects_partial_runtime_with_top_level_covered():
    report = _valid_report()
    report["run_status"] = "covered"
    report["runtime_execution_status"] = "partial"
    report["runtime_scope"]["runtime_performed"] = True
    report["runtime_scope"]["local_selected_lane_material_present"] = True
    report["runtime_scope"]["adb_or_device_commands_performed"] = True

    errors = validate_report_shape(report)

    assert "run_status covered requires runtime_execution_status covered." in errors
    assert "run_status covered cannot be paired with runtime_execution_status partial." in errors


def test_validator_rejects_missing_lane_status_with_covered_runtime():
    report = _valid_report()
    report["run_status"] = "blocked_missing_local_selected_lane"
    report["runtime_execution_status"] = "covered"

    errors = validate_report_shape(report)

    assert "run_status blocked_missing_local_selected_lane requires runtime_execution_status blocked." in errors


def test_validator_rejects_missing_task027s_source_report():
    report = _valid_report()
    report["source_reports"] = [row for row in report["source_reports"] if row["task_id"] != "TASK-027S"]

    errors = validate_report_shape(report)

    assert any("source_reports missing required task references" in error for error in errors)


def test_validator_rejects_missing_loader_gate_exclusions():
    report = _valid_report()
    loader_gate = report["route_gate_ledger"][1]
    loader_gate["must_not_classify_as"] = ["covered_destination"]

    errors = validate_report_shape(report)

    assert any("must_not_classify_as missing session_journal_empty" in error for error in errors)
    assert any("must_not_classify_as missing steam_topup_qr" in error for error in errors)
    assert any("must_not_classify_as missing feedback_qr" in error for error in errors)


def test_validator_rejects_raw_local_path_or_artifact_reference():
    report = _valid_report()
    drive_prefix = "C:" + "\\\\"
    local_marker = "." + "qa_local"
    artifact_name = "raw" + ".png"
    report["debug_note"] = f"{drive_prefix}synthetic\\\\{local_marker}\\\\evidence\\\\{artifact_name}"

    errors = validate_report_shape(report)

    assert any("raw local path" in error for error in errors)
    assert any("raw artifact reference" in error for error in errors)


def test_validator_cli_accepts_task027t_report(capsys):
    exit_code = main(["--report", REPORT_PATH])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "pass"


def test_validator_rejects_missing_file(tmp_path):
    assert validate_report(tmp_path / "missing.json") == ["Report file was not found."]

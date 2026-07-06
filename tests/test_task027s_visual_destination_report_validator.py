import copy
import json

from automation.native_regression.validate_task027s_visual_destination_report import (
    main,
    validate_report,
    validate_report_shape,
)


def _valid_report():
    with open("docs/qa/reports/task027s_visual_destination_screen_coverage.summary.json", encoding="utf-8") as handle:
        return json.load(handle)


def test_validator_accepts_task027s_report():
    assert validate_report_shape(_valid_report()) == []


def test_validator_rejects_destination_covered_without_visual_proof():
    report = _valid_report()
    report["target_destination_ledger"][0]["coverage_status"] = "covered"
    report["target_destination_ledger"][0]["visual_destination_proof"] = False

    errors = validate_report_shape(report)

    assert any("cannot be covered without visual_destination_proof=true" in error for error in errors)


def test_validator_rejects_qr_navigation_followed():
    report = _valid_report()
    report["target_destination_ledger"][1]["qr_navigation_followed"] = True

    errors = validate_report_shape(report)

    assert "target_destination_ledger[1].qr_navigation_followed must be false." in errors


def test_validator_rejects_loader_counted_as_catalog_or_destination():
    report = _valid_report()
    report["coverage_claims"]["app_shell_loader_counts_as_catalog"] = True
    report["coverage_claims"]["app_shell_loader_counts_as_destination"] = True

    errors = validate_report_shape(report)

    assert "coverage_claims.app_shell_loader_counts_as_catalog must be false." in errors
    assert "coverage_claims.app_shell_loader_counts_as_destination must be false." in errors


def test_validator_rejects_missing_loader_detection_target():
    report = _valid_report()
    report["state_detection_targets"] = []

    errors = validate_report_shape(report)

    assert any("state_detection_targets missing required aliases" in error for error in errors)


def test_validator_rejects_detection_target_without_destination_exclusions():
    report = _valid_report()
    report["state_detection_targets"][0]["must_not_classify_as"] = ["covered_destination"]

    errors = validate_report_shape(report)

    assert any("must_not_classify_as missing session_journal_empty" in error for error in errors)
    assert any("must_not_classify_as missing steam_topup_qr" in error for error in errors)
    assert any("must_not_classify_as missing feedback_qr" in error for error in errors)


def test_validator_rejects_loader_timeout_policy_drift():
    report = _valid_report()
    report["state_detection_targets"][0]["timeout_policy_seconds"] = 180
    report["checkpoint_modality_audit"]["timeout_policy_seconds_for_app_shell_loader"] = 180

    errors = validate_report_shape(report)

    assert any("timeout_policy_seconds must be 120" in error for error in errors)
    assert "checkpoint_modality_audit.timeout_policy_seconds_for_app_shell_loader must be 120." in errors


def test_validator_rejects_missing_launcher_entry_surface():
    report = _valid_report()
    report["entry_surface_ledger"] = [
        row
        for row in report["entry_surface_ledger"]
        if row["entry_surface"] != "google_tv_launcher_apps_row_or_recommendations"
    ]

    errors = validate_report_shape(report)

    assert any("entry_surface_ledger missing required surfaces" in error for error in errors)


def test_validator_rejects_missing_new_anomaly_records():
    report = _valid_report()
    report["anomaly_records"] = [
        row for row in report["anomaly_records"] if row["anomaly_id"] != "ANOM-027S-004"
    ]

    errors = validate_report_shape(report)

    assert any("anomaly_records missing required anomalies" in error for error in errors)


def test_validator_rejects_loader_entry_marked_expected_catalog():
    report = _valid_report()
    report["entry_surface_ledger"][0]["entered_expected_catalog"] = True

    errors = validate_report_shape(report)

    assert "entry_surface_ledger[0].entered_expected_catalog must be false for app shell loader." in errors


def test_validator_rejects_raw_local_path_or_artifact_reference():
    report = _valid_report()
    drive_prefix = "C:" + "\\\\"
    local_marker = "." + "qa_local"
    artifact_name = "raw" + ".png"
    report["debug_note"] = f"{drive_prefix}synthetic\\\\{local_marker}\\\\evidence\\\\{artifact_name}"

    errors = validate_report_shape(report)

    assert any("raw local path" in error for error in errors)
    assert any("raw artifact reference" in error for error in errors)


def test_validator_rejects_unknown_evidence_id_shape():
    report = _valid_report()
    report["target_destination_ledger"][0]["evidence_ids"] = ["rt027s-raw-screenshot-1"]

    errors = validate_report_shape(report)

    assert any("unsupported TASK-027S evidence id" in error for error in errors)


def test_validator_cli_accepts_task027s_report(capsys):
    exit_code = main(["--report", "docs/qa/reports/task027s_visual_destination_screen_coverage.summary.json"])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "pass"


def test_validator_rejects_missing_file(tmp_path):
    assert validate_report(tmp_path / "missing.json") == ["Report file was not found."]

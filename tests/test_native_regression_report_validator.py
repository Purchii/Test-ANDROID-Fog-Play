import json
import subprocess
import sys

from automation.native_regression.validate_native_regression_report import main, validate_report


def _valid_report():
    return {
        "schema_version": "task024-native-regression-summary-v1",
        "task_id": "TASK-024",
        "run_status": "blocked",
        "runtime_execution_status": "not_run",
        "runtime_lane": {
            "device_alias": "tv-tpv-013",
            "runtime_profile_alias": "tv-tpv-a12-013",
            "build_alias": "task-005-local-apk-001",
            "synthetic_user_alias": "qa-user-phone-001",
        },
        "regression_cases": [
            {
                "case_id": f"NR-{index:03d}",
                "status": "not_run",
                "evidence_status": "unknown",
                "reason": "runtime not executed",
            }
            for index in range(1, 11)
        ],
        "session_persistence_checkpoints": [],
        "boundary_ledger": [],
        "known_anomalies_rechecked": [],
        "new_anomalies": [],
        "public_safety": {
            "raw_phone_otp_public": False,
            "raw_device_identifiers_public": False,
            "raw_screenshots_public": False,
            "raw_xml_public": False,
            "raw_logs_public": False,
            "payment_webview_stream_entered": False,
            "profile_account_mutation_entered": False,
        },
        "coverage_claims": {
            "exhaustive_app_navigation": False,
            "complete_dynamic_value_inventory": False,
            "payment_or_stream_covered": False,
            "selected_lane_native_regression_only": True,
        },
        "dynamic_data_policy": {
            "assert_fixed_game_titles": False,
            "assert_fixed_server_rows": False,
            "assert_fixed_prices": False,
            "assert_raw_qr_targets": False,
        },
    }


def test_validator_accepts_public_safe_blocked_summary(tmp_path):
    report_path = tmp_path / "task024_report.json"
    report_path.write_text(json.dumps(_valid_report()), encoding="utf-8")

    assert validate_report(report_path) == []


def test_validator_rejects_missing_file(tmp_path):
    assert validate_report(tmp_path / "missing.json") == ["Report file was not found."]


def test_validator_rejects_malformed_json(tmp_path):
    report_path = tmp_path / "bad.json"
    report_path.write_text("{bad-json", encoding="utf-8")

    errors = validate_report(report_path)

    assert any("not valid JSON" in error for error in errors)


def test_validator_rejects_unsafe_public_safety_flags(tmp_path):
    report = _valid_report()
    report["public_safety"]["payment_webview_stream_entered"] = True
    report_path = tmp_path / "task024_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    errors = validate_report(report_path)

    assert "public_safety.payment_webview_stream_entered must be false." in errors


def test_cli_returns_zero_for_valid_report(tmp_path, capsys):
    report_path = tmp_path / "task024_report.json"
    report_path.write_text(json.dumps(_valid_report()), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "pass"


def test_cli_returns_one_for_invalid_report(tmp_path, capsys):
    report = _valid_report()
    report["coverage_claims"]["payment_or_stream_covered"] = True
    report_path = tmp_path / "task024_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "fail"
    assert result["errors"]


def test_validator_script_direct_invocation_works(tmp_path):
    report_path = tmp_path / "task024_report.json"
    report_path.write_text(json.dumps(_valid_report()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "automation/native_regression/validate_native_regression_report.py",
            "--report",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result["validation_status"] == "pass"

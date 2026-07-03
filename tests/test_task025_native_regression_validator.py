import json

from automation.native_regression.validate_task025_native_regression_report import main, validate_report


def _valid_runtime_pass_report():
    return {
        "schema_version": "task025-native-regression-summary-v1",
        "task_id": "TASK-025",
        "mode": "BOUNDED_AUTONOMOUS",
        "execution_mode": "physical_selected_lane_runtime",
        "run_status": "pass",
        "overall_status": "pass",
        "runtime_execution_status": "pass",
        "physical_device_available": True,
        "physical_device_status": "available",
        "apk_install_status": "pass",
        "app_launch_status": "pass",
        "task025b_runtime_status": "ready_after_refreshed_approval",
        "runtime_lane": {
            "device_alias": "tv-tpv-013",
            "runtime_profile_alias": "tv-tpv-a12-013",
            "build_alias": "task-005-local-apk-001",
            "synthetic_user_alias": "qa-user-phone-001",
        },
        "phase_gates": {
            "phase_a_no_device_readiness": "pass",
            "phase_b_schema_validator": "pass",
            "phase_c_runtime": "pass",
        },
        "regression_cases": [
            {
                "case_id": f"NR-{index:03d}",
                "status": "pass",
                "evidence_status": "confirmed",
                "evidence_ids": [f"evidence-nr-{index:03d}"],
                "boundary_entered": False,
                "boundary_evidence_confirmed": index in {8, 9} or None,
            }
            for index in range(1, 11)
        ],
        "session_persistence_checkpoints": [
            {
                "checkpoint_id": "home_foreground_session",
                "status": "pass",
                "evidence_status": "confirmed",
                "evidence_ids": ["evidence-session-home"],
            }
        ],
        "boundary_ledger": [
            {
                "boundary_id": "payment_boundary_classified_not_entered",
                "status": "classified_not_entered",
                "entered": False,
                "evidence_status": "confirmed",
                "evidence_ids": ["evidence-boundary-payment"],
            }
        ],
        "known_anomalies_rechecked": [
            {
                "anomaly_id": "known-search-recovery",
                "category": "search_recovery",
                "status": "not_reproduced",
                "evidence_status": "confirmed",
            }
        ],
        "new_anomalies": [],
        "public_safety": {
            "raw_phone_otp_public": False,
            "raw_device_identifiers_public": False,
            "raw_screenshots_public": False,
            "raw_xml_public": False,
            "raw_logs_public": False,
            "raw_runtime_evidence_public": False,
            "payment_webview_stream_entered": False,
            "profile_account_mutation_entered": False,
            "adb_runtime_invoked": False,
            "apk_install_invoked": False,
            "app_launch_invoked": False,
        },
        "coverage_claims": {
            "exhaustive_app_navigation": False,
            "complete_dynamic_value_inventory": False,
            "payment_or_stream_covered": False,
            "webview_covered": False,
            "broad_compatibility_covered": False,
            "selected_lane_native_regression_only": True,
            "fake_synthetic_tests_are_runtime_evidence": False,
        },
        "dynamic_data_policy": {
            "assert_fixed_game_titles": False,
            "assert_fixed_server_rows": False,
            "assert_fixed_prices": False,
            "assert_raw_qr_targets": False,
        },
    }


def _blocked_no_device_report():
    report = _valid_runtime_pass_report()
    report.update(
        {
            "task_id": "TASK-025A",
            "execution_mode": "no_device_readiness",
            "run_status": "blocked",
            "overall_status": "blocked",
            "runtime_execution_status": "not_run",
            "physical_device_available": False,
            "physical_device_status": "unavailable",
            "apk_install_status": "not_run",
            "app_launch_status": "not_run",
            "task025b_runtime_status": "deferred",
            "phase_gates": {
                "phase_a_no_device_readiness": "pass",
                "phase_b_schema_validator": "pass",
                "phase_c_runtime": "not_run",
            },
            "regression_cases": [
                {
                    "case_id": f"NR-{index:03d}",
                    "status": "not_run",
                    "evidence_status": "unknown",
                    "reason": "physical device unavailable; runtime deferred",
                }
                for index in range(1, 11)
            ],
            "session_persistence_checkpoints": [],
            "boundary_ledger": [],
            "known_anomalies_rechecked": [],
            "new_anomalies": [],
        }
    )
    return report


def _errors_for(report, tmp_path):
    report_path = tmp_path / "task025.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return validate_report(report_path)


def test_validator_accepts_blocked_no_device_report(tmp_path):
    assert _errors_for(_blocked_no_device_report(), tmp_path) == []


def test_validator_rejects_missing_file(tmp_path):
    assert validate_report(tmp_path / "missing.json") == ["Report file was not found."]


def test_validator_rejects_malformed_json(tmp_path):
    report_path = tmp_path / "bad.json"
    report_path.write_text("{bad-json", encoding="utf-8")

    errors = validate_report(report_path)

    assert any("not valid JSON" in error for error in errors)


def test_validator_rejects_pass_with_empty_session_checkpoints(tmp_path):
    report = _valid_runtime_pass_report()
    report["session_persistence_checkpoints"] = []

    errors = _errors_for(report, tmp_path)

    assert "runtime pass requires non-empty session_persistence_checkpoints." in errors


def test_validator_rejects_runtime_pass_when_physical_device_unavailable(tmp_path):
    report = _valid_runtime_pass_report()
    report["physical_device_available"] = False

    errors = _errors_for(report, tmp_path)

    assert "run_status must be blocked when physical_device_available=false." in " ".join(errors)
    assert "runtime_execution_status must be not_run when physical_device_available=false." in " ".join(errors)


def test_validator_rejects_task025a_runtime_pass_shape(tmp_path):
    report = _valid_runtime_pass_report()
    report["task_id"] = "TASK-025A"

    errors = _errors_for(report, tmp_path)

    assert "TASK-025A reports must use no-device or synthetic contract execution mode." in errors
    assert "run_status must be blocked for TASK-025A reports." in errors
    assert "runtime_execution_status must be not_run for TASK-025A reports." in errors
    assert "physical_device_available must be False for TASK-025A reports." in errors
    assert "physical_device_status must be unavailable for TASK-025A reports." in errors
    assert "apk_install_status must be not_run for TASK-025A reports." in errors
    assert "app_launch_status must be not_run for TASK-025A reports." in errors
    assert "task025b_runtime_status must be deferred for TASK-025A reports." in errors


def test_validator_rejects_nr009_pass_with_empty_boundary_ledger(tmp_path):
    report = _valid_runtime_pass_report()
    report["boundary_ledger"] = []

    errors = _errors_for(report, tmp_path)

    assert "boundary-sensitive runtime pass requires non-empty boundary_ledger." in errors
    assert any("NR-009 pass requires confirmed boundary_ledger evidence" in error for error in errors)


def test_validator_rejects_boundary_sensitive_pass_without_confirmed_boundary_evidence(tmp_path):
    report = _valid_runtime_pass_report()
    for case in report["regression_cases"]:
        if case["case_id"] in {"NR-008", "NR-009"}:
            case["boundary_evidence_confirmed"] = False

    errors = _errors_for(report, tmp_path)

    assert any("NR-008 pass requires boundary_evidence_confirmed=true" in error for error in errors)
    assert any("NR-009 pass requires boundary_evidence_confirmed=true" in error for error in errors)


def test_validator_rejects_duplicate_evidence_ids_inside_case(tmp_path):
    report = _valid_runtime_pass_report()
    report["regression_cases"][0]["evidence_ids"] = ["evidence-duplicate", "evidence-duplicate"]

    errors = _errors_for(report, tmp_path)

    assert any("contains a duplicate evidence id" in error for error in errors)


def test_validator_rejects_duplicate_evidence_ids_across_ledgers(tmp_path):
    report = _valid_runtime_pass_report()
    report["session_persistence_checkpoints"][0]["evidence_ids"] = report["boundary_ledger"][0]["evidence_ids"]

    errors = _errors_for(report, tmp_path)

    assert any("evidence id is duplicated across report ledgers" in error for error in errors)


def test_validator_rejects_malformed_known_anomaly(tmp_path):
    report = _valid_runtime_pass_report()
    report["known_anomalies_rechecked"] = [{"category": "search"}]

    errors = _errors_for(report, tmp_path)

    assert "known_anomalies_rechecked[0].anomaly_id is required." in errors
    assert "known_anomalies_rechecked[0].status is required." in errors
    assert "known_anomalies_rechecked[0].evidence_status is required." in errors


def test_validator_rejects_malformed_new_anomaly(tmp_path):
    report = _valid_runtime_pass_report()
    report["new_anomalies"] = [{"anomaly_id": "new-001"}]

    errors = _errors_for(report, tmp_path)

    assert "new_anomalies[0].category is required." in errors
    assert "new_anomalies[0].severity is required." in errors
    assert "new_anomalies[0].evidence_status is required." in errors


def test_validator_rejects_phase_c_runtime_pass_while_runtime_not_run(tmp_path):
    report = _blocked_no_device_report()
    report["phase_gates"]["phase_c_runtime"] = "pass"

    errors = _errors_for(report, tmp_path)

    assert "phase_gates.phase_c_runtime=pass requires runtime_execution_status=pass." in errors


def test_validator_rejects_exhaustive_payment_stream_and_webview_claims(tmp_path):
    report = _valid_runtime_pass_report()
    report["coverage_claims"]["exhaustive_app_navigation"] = True
    report["coverage_claims"]["payment_or_stream_covered"] = True
    report["coverage_claims"]["webview_covered"] = True

    errors = _errors_for(report, tmp_path)

    assert "coverage_claims.exhaustive_app_navigation must be false." in errors
    assert "coverage_claims.payment_or_stream_covered must be false." in errors
    assert "coverage_claims.webview_covered must be false." in errors


def test_validator_rejects_raw_public_values_paths_and_artifacts(tmp_path):
    report = _valid_runtime_pass_report()
    report["notes"] = "https://example.invalid/path .qa_local/evidence/task-025/raw.xml +79990000000 token=secret"

    errors = _errors_for(report, tmp_path)

    assert any("URL-like" in error for error in errors)
    assert any("raw local path" in error for error in errors)
    assert any("phone-like" in error for error in errors)
    assert any("secret-like" in error for error in errors)
    assert any("raw artifact path" in error for error in errors)


def test_validator_rejects_synthetic_report_as_runtime_pass(tmp_path):
    report = _valid_runtime_pass_report()
    report["execution_mode"] = "no_device_synthetic_contract_test"

    errors = _errors_for(report, tmp_path)

    assert "runtime pass requires execution_mode=physical_selected_lane_runtime." in errors
    assert "synthetic contract tests must not produce runtime pass reports." in errors


def test_cli_returns_zero_for_valid_report(tmp_path, capsys):
    report_path = tmp_path / "task025_report.json"
    report_path.write_text(json.dumps(_blocked_no_device_report()), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "pass"


def test_cli_returns_one_for_invalid_report(tmp_path, capsys):
    report = _blocked_no_device_report()
    report["runtime_execution_status"] = "pass"
    report_path = tmp_path / "task025_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "fail"
    assert result["errors"]


def test_validator_cli_entrypoint_in_process_works(tmp_path, capsys):
    report_path = tmp_path / "task025_report.json"
    report_path.write_text(json.dumps(_blocked_no_device_report()), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "pass"

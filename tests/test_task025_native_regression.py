import ast
import json
import os
from pathlib import Path

from automation.native_regression.run_task025_selected_lane_regression import (
    REQUIRED_CASE_IDS,
    SyntheticRuntimeDriver,
    main,
    synthetic_contract_report,
    validate_output_path,
    validate_report_shape,
    validate_suite,
)


def _suite():
    return {
        "schema_version": "task025-native-regression-suite-v1",
        "task_id": "TASK-025",
        "runtime_execution_status": "not_run",
        "runtime_lane": {
            "device_alias": "tv-tpv-013",
            "runtime_profile_alias": "tv-tpv-a12-013",
            "build_alias": "task-005-local-apk-001",
            "synthetic_user_alias": "qa-user-phone-001",
        },
        "dynamic_data_policy": {
            "assert_fixed_game_titles": False,
            "assert_fixed_server_rows": False,
            "assert_fixed_prices": False,
            "assert_raw_qr_targets": False,
        },
        "cases": [
            {
                "case_id": case_id,
                "title": f"{case_id} case",
                "boundary_sensitive": case_id in {"NR-008", "NR-009"},
            }
            for case_id in sorted(REQUIRED_CASE_IDS)
        ],
    }


def _write_suite(tmp_path):
    suite_path = tmp_path / "suite.json"
    suite_path.write_text(json.dumps(_suite()), encoding="utf-8")
    return suite_path


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
                "case_id": case_id,
                "status": "pass",
                "evidence_status": "confirmed",
                "evidence_ids": [f"evidence-{case_id.lower()}"],
                "boundary_entered": False,
                "boundary_evidence_confirmed": case_id in {"NR-008", "NR-009"} or None,
            }
            for case_id in sorted(REQUIRED_CASE_IDS)
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


def test_default_command_blocks_and_does_not_require_device_or_runtime(tmp_path, capsys):
    suite_path = _write_suite(tmp_path)

    exit_code = main(["--suite", str(suite_path)])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["run_status"] == "blocked"
    assert report["runtime_execution_status"] == "not_run"
    assert report["physical_device_available"] is False
    assert report["physical_device_status"] == "unavailable"
    assert report["apk_install_status"] == "not_run"
    assert report["app_launch_status"] == "not_run"
    assert report["task025b_runtime_status"] == "deferred"
    assert {case["case_id"] for case in report["regression_cases"]} == REQUIRED_CASE_IDS


def test_default_runner_does_not_call_shell(monkeypatch, tmp_path, capsys):
    suite_path = _write_suite(tmp_path)

    def fail_system(*args, **kwargs):
        raise AssertionError("shell commands must not be called by TASK-025A default runner")

    monkeypatch.setattr(os, "system", fail_system)

    assert main(["--suite", str(suite_path)]) == 0
    assert json.loads(capsys.readouterr().out)["runtime_execution_status"] == "not_run"


def test_task025_scripts_do_not_import_process_or_shell_modules():
    forbidden_imports = {"sub" + "process", "os"}
    for path in (
        Path("automation/native_regression/run_task025_selected_lane_regression.py"),
        Path("automation/native_regression/validate_task025_native_regression_report.py"),
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not (imported & forbidden_imports)


def test_output_paths_are_constrained_to_public_reports():
    assert validate_output_path("docs/qa/reports/task025.json")
    assert not validate_output_path("docs/qa/private/task025.json")
    assert not validate_output_path(".qa_local/evidence/task-025/report.json")
    assert not validate_output_path("C:/tmp/task025.json")
    assert not validate_output_path("../task025.json")


def test_suite_requires_task025_schema_and_required_cases():
    suite = _suite()
    suite["schema_version"] = "task024-native-regression-suite-v1"
    suite["cases"] = suite["cases"][:-1]
    suite["cases"][-1]["boundary_sensitive"] = False

    errors = validate_suite(suite)

    assert "suite.schema_version must be task025-native-regression-suite-v1." in errors
    assert any("missing required cases" in error for error in errors)
    assert any("boundary_sensitive must be true" in error for error in errors)


def test_no_device_template_report_passes_validation(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    suite_path = _write_suite(tmp_path)
    output_path = tmp_path / "docs" / "qa" / "reports" / "task025.json"

    assert main(["--suite", str(suite_path), "--public-output", str(output_path.relative_to(tmp_path))]) == 0
    report = json.loads(capsys.readouterr().out)

    assert validate_report_shape(report) == []


def test_synthetic_contract_mode_is_not_runtime_evidence(tmp_path, capsys):
    suite_path = _write_suite(tmp_path)

    assert main(["--suite", str(suite_path), "--synthetic-contract-test"]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["execution_mode"] == "no_device_synthetic_contract_test"
    assert report["synthetic_contract"]["contract_status"] == "pass"
    assert report["runtime_execution_status"] == "not_run"
    assert report["coverage_claims"]["fake_synthetic_tests_are_runtime_evidence"] is False
    assert validate_report_shape(report) == []


def test_synthetic_driver_contract_records_expected_action_boundary():
    driver = SyntheticRuntimeDriver()

    report = synthetic_contract_report(driver)

    assert "launch_app" in driver.action_log
    assert "classify_boundary" in driver.action_log
    assert report["synthetic_contract"]["boundary_category"] == "payment/subscription/purchase"
    assert report["run_status"] == "blocked"


def test_valid_future_runtime_pass_shape_is_possible_after_device_returns():
    report = _valid_runtime_pass_report()

    assert validate_report_shape(report) == []

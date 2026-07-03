import json

from automation.native_regression.run_native_regression_probe import (
    REQUIRED_CASE_IDS,
    main,
    validate_output_path,
    validate_report_shape,
    validate_suite,
)


def _suite():
    return {
        "schema_version": "task024-native-regression-suite-v1",
        "task_id": "TASK-024",
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
        "cases": [{"case_id": case_id, "title": f"{case_id} case"} for case_id in sorted(REQUIRED_CASE_IDS)],
    }


def _valid_report():
    return {
        "schema_version": "task024-native-regression-summary-v1",
        "task_id": "TASK-024",
        "run_status": "partial",
        "runtime_execution_status": "partial",
        "runtime_lane": {
            "device_alias": "tv-tpv-013",
            "runtime_profile_alias": "tv-tpv-a12-013",
            "build_alias": "task-005-local-apk-001",
            "synthetic_user_alias": "qa-user-phone-001",
        },
        "regression_cases": [
            {
                "case_id": case_id,
                "status": "pass",
                "evidence_status": "confirmed",
                "evidence_ids": [f"task024:{case_id.lower()}"],
                "boundary_entered": False,
            }
            for case_id in sorted(REQUIRED_CASE_IDS)
        ],
        "session_persistence_checkpoints": [
            {
                "checkpoint_id": "session_home_foreground",
                "status": "pass",
                "evidence_status": "confirmed",
                "evidence_ids": ["task024:session_home_foreground"],
            }
        ],
        "boundary_ledger": [
            {
                "boundary_id": "payment_qr_boundary",
                "status": "blocked_by_boundary",
                "entered": False,
                "evidence_status": "confirmed",
                "evidence_ids": ["TASK-022:073"],
            }
        ],
        "known_anomalies_rechecked": [
            {
                "alias": "search_back_and_route_recovery_trap",
                "status": "known_anomaly",
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


def test_default_command_blocks_and_does_not_require_runtime(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["runtime_execution_status"] == "not_run"
    assert len(report["regression_cases"]) == 10


def test_output_paths_are_constrained_to_task024_families():
    assert validate_output_path(".qa_local/evidence/task-024/run/report.json")
    assert validate_output_path("docs/qa/reports/task024.json", public_output=True)
    assert not validate_output_path(".qa_local/evidence/task-023/run/report.json")
    assert not validate_output_path(".qa_local/secrets/qa_user.env")
    assert not validate_output_path(".qa_local/apks/task-005/app.apk")
    assert not validate_output_path("docs/qa/private/task024.json", public_output=True)
    assert not validate_output_path("C:/tmp/task024.json")
    assert not validate_output_path("../escape.json")


def test_invalid_raw_with_valid_public_is_atomic_no_write(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    suite_path = tmp_path / "suite.json"
    suite_path.write_text(json.dumps(_suite()), encoding="utf-8")
    public_output = "docs/qa/reports/task024_probe.json"
    raw_output = ".qa_local/evidence/task-023/probe.json"

    exit_code = main(["--suite", str(suite_path), "--public-output", public_output, "--raw-output", raw_output])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert "raw output path must stay under .qa_local/evidence/task-024/" in report["blocked_reasons"]
    assert not (tmp_path / public_output).exists()
    assert not (tmp_path / raw_output).exists()


def test_invalid_public_with_valid_raw_is_atomic_no_write(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    suite_path = tmp_path / "suite.json"
    suite_path.write_text(json.dumps(_suite()), encoding="utf-8")
    public_output = "docs/qa/private/task024_probe.json"
    raw_output = ".qa_local/evidence/task-024/probe.json"

    exit_code = main(["--suite", str(suite_path), "--public-output", public_output, "--raw-output", raw_output])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert "public output path must stay under docs/qa/reports/*.json" in report["blocked_reasons"]
    assert not (tmp_path / public_output).exists()
    assert not (tmp_path / raw_output).exists()


def test_suite_requires_all_cases_and_dynamic_policy_false():
    suite = _suite()
    suite["cases"].pop()
    suite["dynamic_data_policy"]["assert_fixed_server_rows"] = True

    errors = validate_suite(suite)

    assert any("missing required cases" in error for error in errors)
    assert "suite.dynamic_data_policy.assert_fixed_server_rows must be false." in errors


def test_valid_report_passes_shape_validation():
    assert validate_report_shape(_valid_report()) == []


def test_report_rejects_missing_required_case_reason_for_not_run():
    report = _valid_report()
    report["regression_cases"] = report["regression_cases"][:-1]
    report["regression_cases"][0] = {
        "case_id": "NR-001",
        "status": "not_run",
        "evidence_status": "unknown",
    }

    errors = validate_report_shape(report)

    assert any("missing required cases" in error for error in errors)
    assert "regression_cases[0].reason is required for not_run." in errors


def test_report_rejects_raw_values_dynamic_dumps_and_unsafe_claims():
    report = _valid_report()
    report["notes"] = "server_alias=raw-title-001 price=999 https://example.invalid/path .qa_local/evidence/task-024/raw.xml"
    report["public_safety"]["raw_xml_public"] = True
    report["coverage_claims"]["exhaustive_app_navigation"] = True
    report["dynamic_data_policy"]["assert_fixed_game_titles"] = True

    errors = validate_report_shape(report)

    assert any("fixed dynamic-value dump" in error for error in errors)
    assert any("URL-like" in error for error in errors)
    assert any("raw local path" in error for error in errors)
    assert "public_safety.raw_xml_public must be false." in errors
    assert "coverage_claims.exhaustive_app_navigation must be false." in errors
    assert "dynamic_data_policy.assert_fixed_game_titles must be false." in errors


def test_report_rejects_boundary_entered_or_pass_result():
    report = _valid_report()
    report["regression_cases"][0]["boundary_entered"] = True
    report["boundary_ledger"][0]["entered"] = True
    report["boundary_ledger"][0]["result"] = "pass"

    errors = validate_report_shape(report)

    assert "regression_cases[0].boundary_entered must not be true." in errors
    assert "boundary_ledger[0].entered must be false." in errors
    assert "boundary_ledger[0].result must not be pass." in errors


def test_report_rejects_pass_without_confirmed_evidence():
    report = _valid_report()
    report["regression_cases"][0]["evidence_status"] = "unknown"

    errors = validate_report_shape(report)

    assert "regression_cases[0].evidence_status must be confirmed for pass." in errors


def test_report_rejects_inconsistent_aggregate_statuses():
    report = _valid_report()
    report["run_status"] = "pass"
    report["runtime_execution_status"] = "not_run"

    errors = validate_report_shape(report)

    assert "run_status pass variants require runtime_execution_status=pass." in errors
    assert "runtime_execution_status=not_run requires run_status=blocked." in errors


def test_report_rejects_boundary_without_confirmed_identity_or_evidence():
    report = _valid_report()
    report["boundary_ledger"][0].pop("boundary_id")
    report["boundary_ledger"][0].pop("evidence_status")

    errors = validate_report_shape(report)

    assert "boundary_ledger[0].boundary_id is required." in errors
    assert "boundary_ledger[0].evidence_status must be confirmed." in errors


def test_report_rejects_pass_aggregate_with_blocked_case():
    report = _valid_report()
    report["run_status"] = "pass"
    report["runtime_execution_status"] = "pass"
    report["regression_cases"][0] = {
        "case_id": "NR-001",
        "status": "blocked",
        "evidence_status": "unknown",
        "reason": "blocked fixture",
    }

    errors = validate_report_shape(report)

    assert "run_status=pass cannot include regression_cases[0].status=blocked." in errors


def test_report_rejects_session_checkpoint_pass_without_confirmed_evidence():
    report = _valid_report()
    report["session_persistence_checkpoints"][0]["evidence_status"] = "unknown"
    report["session_persistence_checkpoints"][0].pop("evidence_ids")

    errors = validate_report_shape(report)

    assert "session_persistence_checkpoints[0].evidence_status must be confirmed for pass." in errors
    assert "session_persistence_checkpoints[0].evidence_ids are required for pass." in errors


def test_report_rejects_boundary_with_invalid_evidence_status():
    report = _valid_report()
    report["boundary_ledger"][0]["evidence_status"] = "garbage"

    errors = validate_report_shape(report)

    assert "boundary_ledger[0].evidence_status must be confirmed." in errors

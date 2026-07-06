import json

from automation.native_regression.validate_task027_transition_graph_report import (
    FORBIDDEN_BOUNDARY_CATEGORIES,
    REQUIRED_SCREEN_FAMILIES,
    REQUIRED_TASK025B_ANOMALIES,
    REQUIRED_TRANSITION_FAMILIES,
    main,
    validate_report,
    validate_report_shape,
)


def _valid_report():
    return {
        "schema_version": "task027-full-app-transition-graph-summary-v1",
        "task_id": "TASK-027",
        "mode": "NON_AUTONOMOUS",
        "run_status": "blocked_preflight_pending",
        "runtime_execution_status": "not_run",
        "execution_mode": "preflight_contract_only",
        "runtime_lane": {
            "device_alias": "tv-tpv-013",
            "runtime_profile_alias": "tv-tpv-a12-013",
            "build_alias": "task-005-local-apk-television-full",
            "synthetic_user_alias": "qa-user-phone-001",
        },
        "source_reports": [
            {"task_id": "TASK-025B", "public_ref": "task025b_selected_lane_physical_runtime.summary.json"},
            {"task_id": "TASK-020", "public_ref": "task020_full_screen_inventory.summary.json"},
            {"task_id": "TASK-023", "public_ref": "task023_full_data_screen_inventory.summary.json"},
        ],
        "preflight_ledger": {
            "status": "pending_runtime_confirmation",
            "physical_device_available": "pending",
            "selected_device_authorized": "pending",
            "selected_aliases_refreshed": "pending",
            "apk_presence_confirmed": "pending",
            "apk_hash_recorded_local_only": "pending",
            "synthetic_user_env_confirmed": "pending",
            "evidence_storage_approved": "pending",
            "cleanup_policy_confirmed": "pending",
            "qa_reviewer_a_approval": "pending",
            "qa_reviewer_b_approval": "pending",
            "security_prod_safety_approval": "pending",
        },
        "transition_graph_closure_ledger": [
            {
                "transition_id": f"TR-027-{index:03d}",
                "transition_family": family,
                "from_screen_family": "planned_source_family",
                "to_screen_family": "planned_target_family",
                "trigger_category": "planned_safe_action",
                "observed_transition_category": "pending_preflight",
                "closure_status": "blocked_by_tooling",
                "evidence_status": "unknown",
                "evidence_ids": [],
                "source_report_refs": ["TASK-025B"],
                "boundary_ids": [],
                "anomaly_ids": [],
                "recovery_policy": "Back, Home, cancel, force-stop and relaunch only.",
                "public_safe_note": "Planned row; no runtime evidence claimed.",
                "test_design_implication": "Requires physical checkpoint evidence before closure.",
            }
            for index, family in enumerate(sorted(REQUIRED_TRANSITION_FAMILIES), start=1)
        ],
        "screen_family_closure_ledger": [
            {
                "screen_family": family,
                "coverage_status": "blocked_by_tooling",
                "evidence_status": "unknown",
                "evidence_ids": [],
            }
            for family in sorted(REQUIRED_SCREEN_FAMILIES)
        ],
        "boundary_ledger": [
            {
                "boundary_id": "BND-027-PLANNED-001",
                "boundary_category": "payment/subscription/purchase",
                "status": "blocked_by_boundary",
                "entered": False,
                "navigation_followed": False,
                "external_action": "not_performed",
                "evidence_status": "unknown",
                "evidence_ids": [],
            }
        ],
        "anomaly_records": [
            {
                "anomaly_id": anomaly_id,
                "category": "known_task025b_anomaly",
                "trigger_action": "planned recheck",
                "expected_result": "safe transition or terminal classification",
                "observed_result": "pending TASK-027 runtime",
                "evidence_status": "unknown",
                "evidence_ids": [],
                "likely_or_hypothesis_cause": "pending recheck",
                "recovery_action": "force-stop and relaunch if safe navigation recovery fails",
                "recovered": "pending",
                "regression_case_ids": [],
                "test_design_implication": "Known TASK-025B anomaly must not be hidden by graph closure.",
            }
            for anomaly_id in sorted(REQUIRED_TASK025B_ANOMALIES)
        ],
        "public_safety": {
            "raw_phone_otp_public": False,
            "raw_device_identifiers_public": False,
            "raw_apk_hash_public": False,
            "raw_apk_filename_public": False,
            "raw_qr_targets_public": False,
            "raw_screenshots_public": False,
            "raw_xml_public": False,
            "raw_logs_public": False,
            "raw_video_public": False,
            "raw_runtime_evidence_public": False,
            "private_routes_or_endpoints_public": False,
            "payment_webview_stream_entered": False,
            "profile_account_mutation_entered": False,
            "external_qr_or_browser_opened": False,
            "steam_account_mutation_performed": False,
            "network_offline_manipulation_performed": False,
        },
        "coverage_claims": {
            "full_reachable_transition_graph_closed": False,
            "complete_dynamic_value_inventory": False,
            "complete_game_title_enumeration": False,
            "complete_server_row_enumeration": False,
            "payment_or_stream_covered": False,
            "webview_external_traversal_covered": False,
            "broad_compatibility_covered": False,
            "task025b_partial_counts_as_full_graph": False,
            "task026b_no_device_contract_counts_as_runtime_evidence": False,
        },
        "dynamic_data_policy": {
            "assert_fixed_game_titles": False,
            "assert_fixed_server_rows": False,
            "assert_fixed_server_aliases": False,
            "assert_fixed_prices": False,
            "assert_fixed_hardware_rows": False,
            "assert_raw_qr_targets": False,
            "assert_categories_and_transition_invariants_only": True,
        },
        "boundary_guard_categories": list(FORBIDDEN_BOUNDARY_CATEGORIES),
        "unverified_areas": [
            "physical runtime preflight",
            "full reachable transition graph",
            "Search recovery recheck",
            "Settings Gamepad safe-entry recheck",
            "NR-008 game-detail server-list recheck",
        ],
    }


def test_validator_accepts_preflight_pending_report():
    assert validate_report_shape(_valid_report()) == []


def test_validator_rejects_missing_required_transition_family():
    report = _valid_report()
    report["transition_graph_closure_ledger"] = report["transition_graph_closure_ledger"][:-1]

    errors = validate_report_shape(report)

    assert any("transition_graph_closure_ledger missing required families" in error for error in errors)


def test_validator_rejects_missing_required_screen_family():
    report = _valid_report()
    report["screen_family_closure_ledger"] = report["screen_family_closure_ledger"][:-1]

    errors = validate_report_shape(report)

    assert any("screen_family_closure_ledger missing required families" in error for error in errors)


def test_validator_rejects_task025b_partial_as_full_graph_claim():
    report = _valid_report()
    report["coverage_claims"]["task025b_partial_counts_as_full_graph"] = True

    errors = validate_report_shape(report)

    assert "coverage_claims.task025b_partial_counts_as_full_graph must be false." in errors


def test_validator_rejects_incomplete_preflight_ledger():
    report = _valid_report()
    report["preflight_ledger"] = {"status": "pending_runtime_confirmation"}

    errors = validate_report_shape(report)

    assert any("preflight_ledger missing required fields" in error for error in errors)


def test_validator_rejects_confirmed_preflight_with_pending_gate():
    report = _valid_report()
    report["run_status"] = "partial"
    report["preflight_ledger"] = {
        key: "confirmed"
        for key in (
            "physical_device_available",
            "selected_device_authorized",
            "selected_aliases_refreshed",
            "apk_presence_confirmed",
            "apk_hash_recorded_local_only",
            "synthetic_user_env_confirmed",
            "evidence_storage_approved",
            "cleanup_policy_confirmed",
            "qa_reviewer_a_approval",
            "qa_reviewer_b_approval",
            "security_prod_safety_approval",
        )
    }
    report["preflight_ledger"]["status"] = "confirmed_for_task027"
    report["preflight_ledger"]["apk_presence_confirmed"] = "pending"

    errors = validate_report_shape(report)

    assert "preflight_ledger.apk_presence_confirmed must be confirmed or approved when preflight is confirmed." in errors


def test_validator_rejects_fixed_dynamic_values_and_raw_targets():
    report = _valid_report()
    report["notes"] = "game_title=Example server_count=250 https://example.invalid/qr?token=fake"

    errors = validate_report_shape(report)

    assert any("fixed dynamic-value dump" in error for error in errors)
    assert any("URL-like" in error for error in errors)


def test_validator_rejects_boundary_entry():
    report = _valid_report()
    report["boundary_ledger"][0]["entered"] = True
    report["boundary_ledger"][0]["navigation_followed"] = True
    report["boundary_ledger"][0]["external_action"] = "performed"

    errors = validate_report_shape(report)

    assert "boundary_ledger[0].entered must be false." in errors
    assert "boundary_ledger[0].navigation_followed must be false." in errors
    assert "boundary_ledger[0].external_action must be not_performed." in errors


def test_validator_rejects_missing_known_task025b_anomaly():
    report = _valid_report()
    report["anomaly_records"] = report["anomaly_records"][:2]

    errors = validate_report_shape(report)

    assert any("anomaly_records missing required TASK-025B anomalies" in error for error in errors)


def test_validator_rejects_full_graph_closed_without_physical_runtime():
    report = _valid_report()
    report["run_status"] = "full_graph_closed"
    report["coverage_claims"]["full_reachable_transition_graph_closed"] = True

    errors = validate_report_shape(report)

    assert "full_graph_closed requires physical_selected_lane_runtime execution." in errors
    assert any("evidence_ids are required for full graph closure" in error for error in errors)


def test_validator_cli_accepts_template_report(capsys):
    exit_code = main(["--report", "docs/qa/reports/task027_full_app_transition_graph_physical_runtime.summary.json"])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "pass"


def test_validator_rejects_missing_file(tmp_path):
    assert validate_report(tmp_path / "missing.json") == ["Report file was not found."]

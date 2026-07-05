import copy

import pytest

from automation.native_regression.run_task025_selected_lane_regression import (
    REQUIRED_CASE_IDS,
    SyntheticRuntimeDriver,
    default_blocked_report,
    synthetic_contract_report,
    validate_report_shape,
)


BOUNDARY_GUARDS = [
    "payment/subscription/purchase",
    "WebView/browser/external QR traversal",
    "stream/WebRTC/media playback/game session start",
    "Steam/account connection",
    "profile/account mutation",
    "network/offline manipulation",
]


def _future_physical_pass_report():
    boundary_id = "payment_boundary_classified_not_entered"
    return {
        "schema_version": "task025-native-regression-summary-v1",
        "task_id": "TASK-025",
        "mode": "BOUNDED_AUTONOMOUS",
        "execution_mode": "physical_selected_lane_runtime",
        "run_status": "pass",
        "overall_status": "pass",
        "runtime_execution_status": "pass",
        "runtime_evidence_ids": ["evidence-runtime-top"],
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
        "task025b_preflight": {
            "preflight_status": "confirmed_for_task025b",
            "physical_device_available": True,
            "refreshed_owner_approvals": True,
            "selected_device_authorized": True,
            "apk_presence_confirmed": True,
            "apk_hash_recorded_local_only": True,
            "synthetic_user_env_confirmed": True,
            "evidence_capture_approval": True,
            "cleanup_policy_confirmed": True,
            "runtime_evidence_required_for_pass": True,
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
                "execution_mode": "physical_selected_lane_runtime",
                "counts_as_runtime_evidence": True,
                "evidence_ids": [f"evidence-{case_id.lower()}"],
                "boundary_entered": False,
                "boundary_evidence_confirmed": case_id in {"NR-008", "NR-009"} or None,
                "boundary_ids": [boundary_id] if case_id in {"NR-008", "NR-009"} else [],
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
                "boundary_id": boundary_id,
                "boundary_category": "payment/subscription/purchase",
                "status": "classified_not_entered",
                "entered": False,
                "navigation_followed": False,
                "external_action": "not_performed",
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
                "trigger_action": "future physical runtime rechecks search recovery",
                "expected_result": "search recovery remains safe",
                "observed_result": "not reproduced in this fixture",
                "test_design_implication": "keep search recovery as a regression oracle",
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
            "synthetic_contract_tests_are_runtime_evidence": False,
        },
        "dynamic_data_policy": {
            "assert_fixed_game_titles": False,
            "assert_fixed_server_rows": False,
            "assert_fixed_prices": False,
            "assert_raw_qr_targets": False,
        },
        "boundary_guard_categories": BOUNDARY_GUARDS,
    }


def _errors_after(mutator):
    report = _future_physical_pass_report()
    mutator(report)
    return validate_report_shape(report)


def test_task026a_default_no_device_report_has_deferred_preflight_and_no_runtime_evidence():
    report = default_blocked_report()

    assert report["task025b_preflight"]["preflight_status"] == "deferred_no_device"
    assert report["task025b_preflight"]["physical_device_available"] is False
    assert report["runtime_evidence_ids"] == []
    assert validate_report_shape(report) == []


@pytest.mark.parametrize(
    "field",
    [
        "physical_device_available",
        "refreshed_owner_approvals",
        "selected_device_authorized",
        "apk_presence_confirmed",
        "apk_hash_recorded_local_only",
        "synthetic_user_env_confirmed",
        "evidence_capture_approval",
        "cleanup_policy_confirmed",
    ],
)
def test_task026a_no_device_preflight_cannot_be_marked_ready(field):
    report = default_blocked_report()
    report["task025b_preflight"][field] = True

    errors = validate_report_shape(report)

    assert f"task025b_preflight.{field} must be false for no-device readiness reports." in errors


def test_task026a_runtime_pass_requires_confirmed_task025b_preflight():
    errors = _errors_after(lambda report: report["task025b_preflight"].update({"refreshed_owner_approvals": False}))

    assert "runtime evidence claims require task025b_preflight.refreshed_owner_approvals=true." in errors


def test_task026a_runtime_pass_cannot_keep_task025b_deferred():
    errors = _errors_after(lambda report: report.update({"task025b_runtime_status": "deferred"}))

    assert "runtime evidence claims require task025b_runtime_status=ready_after_refreshed_approval." in errors


def test_task026a_runtime_pass_requires_phase_c_runtime_pass():
    errors = _errors_after(lambda report: report["phase_gates"].update({"phase_c_runtime": "blocked"}))

    assert "runtime evidence claims require phase_gates.phase_c_runtime=pass." in errors


def test_task026a_runtime_pass_requires_top_level_runtime_evidence_ids():
    errors = _errors_after(lambda report: report.update({"runtime_evidence_ids": []}))

    assert "runtime evidence claims require non-empty runtime_evidence_ids." in errors


@pytest.mark.parametrize(
    "case_mutation, expected",
    [
        (
            lambda case: case.pop("execution_mode"),
            "regression_cases[0].execution_mode must be physical_selected_lane_runtime for pass.",
        ),
        (
            lambda case: case.update({"counts_as_runtime_evidence": False}),
            "regression_cases[0].counts_as_runtime_evidence must be true for pass.",
        ),
        (
            lambda case: case.update({"evidence_status": "likely"}),
            "regression_cases[0].evidence_status must be confirmed for pass.",
        ),
    ],
)
def test_task026a_passed_cases_need_physical_runtime_evidence_contract(case_mutation, expected):
    errors = _errors_after(lambda report: case_mutation(report["regression_cases"][0]))

    assert expected in errors


def test_task026a_boundary_sensitive_cases_must_link_to_specific_boundary_ledger_ids():
    def mutate(report):
        for case in report["regression_cases"]:
            if case["case_id"] == "NR-008":
                case["boundary_ids"] = ["unrelated-boundary"]

    errors = _errors_after(mutate)

    assert any("NR-008 boundary_ids must reference boundary_ledger entries" in error for error in errors)


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (
            lambda boundary: boundary.update({"boundary_category": "stream/session started"}),
            "boundary_ledger[0].boundary_category must be a guarded boundary category.",
        ),
        (
            lambda boundary: boundary.update({"navigation_followed": True}),
            "boundary_ledger[0].navigation_followed must be false when present.",
        ),
        (
            lambda boundary: boundary.update({"external_action": "performed"}),
            "boundary_ledger[0].external_action must not be performed.",
        ),
    ],
)
def test_task026a_boundary_ledger_blocks_boundary_overclaim(mutator, expected):
    errors = _errors_after(lambda report: mutator(report["boundary_ledger"][0]))

    assert expected in errors


def test_task026a_guard_category_allowlist_is_required():
    errors = _errors_after(lambda report: report.update({"boundary_guard_categories": BOUNDARY_GUARDS[:-1]}))

    assert "boundary_guard_categories must match the TASK-025 forbidden boundary category allowlist." in errors


def test_task026a_synthetic_contract_section_cannot_be_runtime_evidence():
    report = synthetic_contract_report(SyntheticRuntimeDriver())
    report["synthetic_contract"]["counts_as_runtime_evidence"] = True

    errors = validate_report_shape(report)

    assert "synthetic_contract.counts_as_runtime_evidence must be false." in errors


def test_task026a_synthetic_contract_requires_synthetic_only_reference():
    report = synthetic_contract_report(SyntheticRuntimeDriver())
    report["synthetic_contract"]["synthetic_ref"] = "runtime-evidence-001"

    errors = validate_report_shape(report)

    assert "synthetic_contract.synthetic_ref must be a synthetic-only reference." in errors


def test_task026a_anomalies_require_runtime_design_context():
    def mutate(report):
        report["known_anomalies_rechecked"][0] = {
            "anomaly_id": "known-search-recovery",
            "category": "search_recovery",
            "status": "reproduced",
            "evidence_status": "confirmed",
        }

    errors = _errors_after(mutate)

    assert "known_anomalies_rechecked[0].trigger_action is required." in errors
    assert "known_anomalies_rechecked[0].test_design_implication is required." in errors


@pytest.mark.parametrize(
    "field",
    [
        "payment_webview_stream_entered",
        "profile_account_mutation_entered",
        "raw_runtime_evidence_public",
    ],
)
def test_task026a_public_safety_flags_fail_closed(field):
    errors = _errors_after(lambda report: report["public_safety"].update({field: True}))

    assert f"public_safety.{field} must be false." in errors


def test_task026a_raw_public_values_paths_qr_targets_and_fixed_dynamic_values_are_rejected():
    report = _future_physical_pass_report()
    report["unsafe_notes"] = (
        "https://example.invalid/qr?token=fake .qa_local/evidence/task-025/raw.xml "
        "game_title=FixedName server_alias=server-001"
    )

    errors = validate_report_shape(report)

    assert any("URL-like value" in error for error in errors)
    assert any("raw local path" in error for error in errors)
    assert any("raw artifact path" in error for error in errors)
    assert any("fixed dynamic-value dump" in error for error in errors)


def test_task026a_no_device_report_rejects_hidden_runtime_evidence_ids():
    report = default_blocked_report()
    report["runtime_evidence_ids"] = ["evidence-runtime-hidden"]

    errors = validate_report_shape(report)

    assert "runtime_evidence_ids must be empty for no-device readiness reports." in errors


def test_task026a_no_device_report_requires_runtime_evidence_ids_field():
    report = default_blocked_report()
    report.pop("runtime_evidence_ids")

    errors = validate_report_shape(report)

    assert "runtime_evidence_ids is required." in errors
    assert "runtime_evidence_ids must be a list." in errors


def test_task026a_physical_device_available_must_be_boolean_and_cannot_hide_runtime_evidence():
    report = default_blocked_report()
    report["task_id"] = "TASK-025"
    report["physical_device_available"] = "false"
    report["runtime_evidence_ids"] = ["hidden-runtime-evidence"]

    errors = validate_report_shape(report)

    assert "physical_device_available must be boolean." in errors
    assert "runtime evidence claims require physical_device_available=true." not in errors
    assert "runtime_evidence_ids must be empty when runtime is not run or report is blocked." in errors


def test_task026a_runtime_evidence_ids_must_be_list():
    report = default_blocked_report()
    report["runtime_evidence_ids"] = "evidence-runtime-hidden"

    errors = validate_report_shape(report)

    assert "runtime_evidence_ids must be a list." in errors
    assert "runtime_evidence_ids must be empty for no-device readiness reports." in errors


def test_task026a_blocked_report_cannot_keep_runtime_evidence_ids_even_when_task025_shape_is_malformed():
    report = default_blocked_report()
    report["task_id"] = "TASK-025"
    report["physical_device_available"] = "false"
    report["run_status"] = "blocked"
    report["runtime_execution_status"] = "not_run"
    report["runtime_evidence_ids"] = ["hidden-runtime-evidence"]

    errors = validate_report_shape(report)

    assert "physical_device_available must be boolean." in errors
    assert "runtime_evidence_ids must be empty when runtime is not run or report is blocked." in errors


def test_task026a_partial_runtime_claim_requires_preflight_and_runtime_evidence():
    report = _future_physical_pass_report()
    report["run_status"] = "partial"
    report["overall_status"] = "partial"
    report["runtime_execution_status"] = "pass"
    report["runtime_evidence_ids"] = []
    report["task025b_preflight"]["refreshed_owner_approvals"] = False

    errors = validate_report_shape(report)

    assert "runtime evidence claims require non-empty runtime_evidence_ids." in errors
    assert "runtime evidence claims require task025b_preflight.refreshed_owner_approvals=true." in errors


def test_task026a_partial_runtime_claim_requires_phase_c_runtime_pass():
    report = _future_physical_pass_report()
    report["run_status"] = "partial"
    report["overall_status"] = "partial"
    report["runtime_execution_status"] = "partial"
    report["phase_gates"]["phase_c_runtime"] = "blocked"

    errors = validate_report_shape(report)

    assert "runtime evidence claims require phase_gates.phase_c_runtime=pass." in errors


def test_task026a_passed_case_claim_triggers_top_level_runtime_requirements():
    report = default_blocked_report()
    report["task_id"] = "TASK-025"
    report["regression_cases"][0].update(
        {
            "status": "pass",
            "evidence_status": "confirmed",
            "execution_mode": "physical_selected_lane_runtime",
            "counts_as_runtime_evidence": True,
            "evidence_ids": ["evidence-nr-001"],
            "boundary_entered": False,
        }
    )

    errors = validate_report_shape(report)

    assert "runtime evidence claims require physical_device_available=true." in errors
    assert "runtime evidence claims require non-empty runtime_evidence_ids." in errors
    assert "runtime evidence claims require task025b_preflight.preflight_status=confirmed_for_task025b." in errors


def test_task026a_future_physical_pass_fixture_is_only_schema_contract_not_task026a_runtime_evidence():
    report = _future_physical_pass_report()
    cloned = copy.deepcopy(report)

    assert validate_report_shape(cloned) == []
    assert cloned["execution_mode"] == "physical_selected_lane_runtime"
    assert cloned["task025b_preflight"]["preflight_status"] == "confirmed_for_task025b"

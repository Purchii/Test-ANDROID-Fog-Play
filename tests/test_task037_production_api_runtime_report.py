import copy
import json
from pathlib import Path

from automation.api_layer_contract.validate_task037_production_api_runtime_report import (
    main,
    validate_public_report,
)


def _valid_report():
    return {
        "task_id": "TASK-037",
        "schema_version": "task037-production-api-runtime-exploratory-v1",
        "tool_name": "validate_task037_production_api_runtime_report",
        "mode": "BOUNDED_AUTONOMOUS",
        "production_safety_classification": "PROD_CONDITIONAL_LIVE_READ_ONLY_SAFE_LANE",
        "overall_status": "partial_read_only_covered",
        "evidence_status": "confirmed",
        "runtime_execution_status": "partial_runtime_correlated",
        "live_api_execution_status": "partial_read_only_covered",
        "safe_lane": {
            "environment": "production",
            "target_alias": "task037-approved-tv-target",
            "target_raw_value_public": False,
            "synthetic_user_allowed": True,
            "raw_secret_values_public": False,
            "allowed_api_scope": [
                "config",
                "catalog",
                "reference_dictionary",
                "available_status",
                "synthetic_profile_status",
                "synthetic_entitlement_status",
                "auth_session_bootstrap",
            ],
            "blocked_actions": [
                "stream_start",
                "order",
                "payment",
                "profile_account_mutation",
                "device_binding_mutation",
                "destructive_revoke_update_delete",
            ],
        },
        "budget": {
            "concurrency": 1,
            "retry_cap": 3,
            "total_live_request_count": 2,
            "total_retry_count": 0,
            "load_or_fuzz_loop_performed": False,
        },
        "preflight": {
            "owner_safe_lane_recorded": True,
            "synthetic_secret_preflight": {
                "status": "confirmed",
                "evidence_status": "confirmed",
                "raw_values_printed": False,
            },
            "target_preflight": {
                "status": "confirmed",
                "evidence_status": "confirmed",
                "raw_values_printed": False,
            },
            "raw_evidence_storage_preflight": {
                "status": "confirmed",
                "evidence_status": "confirmed",
                "raw_values_printed": False,
            },
            "redaction_preflight": {
                "status": "confirmed",
                "evidence_status": "confirmed",
                "raw_values_printed": False,
            },
            "forbidden_action_guard_preflight": {
                "status": "confirmed",
                "evidence_status": "confirmed",
                "raw_values_printed": False,
            },
        },
        "coverage_summary": {
            "counts_by_api_category": {"config": 1, "catalog": 1},
            "counts_by_runtime_category": {"app_launch": 1},
            "counts_by_execution_status": {"covered": 3},
        },
        "api_coverage_ledger": [
            {
                "category": "config",
                "execution_status": "covered",
                "evidence_status": "confirmed",
                "evidence_ids": ["rt037-api-config-read"],
                "request_count": 1,
                "retry_count": 0,
                "mutation_performed": False,
                "raw_values_public": False,
            },
            {
                "category": "catalog",
                "execution_status": "covered",
                "evidence_status": "confirmed",
                "evidence_ids": ["rt037-api-catalog-read"],
                "request_count": 1,
                "retry_count": 0,
                "mutation_performed": False,
                "raw_values_public": False,
            },
        ],
        "runtime_coverage_ledger": [
            {
                "category": "app_launch",
                "execution_status": "covered",
                "evidence_status": "confirmed",
                "evidence_ids": ["rt037-runtime-app-launch"],
                "screen_alias": "post_auth_catalog_surface",
                "state_category": "runtime_app_surface",
                "focus_action_category": "launcher_entry",
                "risk_hypothesis_note": "app reached a public-safe catalog alias",
                "raw_values_public": False,
            }
        ],
        "boundary_ledger": [
            {
                "category": "payment",
                "execution_status": "blocked_by_boundary",
                "action_performed": False,
                "navigation_followed": False,
                "evidence_ids": ["rt037-boundary-payment"],
            }
        ],
        "anomaly_ledger": [
            {
                "anomaly_id": "ANOM-037-001",
                "public_safe_alias": "status_oracle_unavailable",
                "trigger_action": "read-only runtime correlation",
                "expected_result": "stable status",
                "observed_result": "status oracle unavailable",
                "evidence_status": "unknown",
                "likely_or_hypothesis_cause": "status oracle requires a future public-safe direct API invocation path",
                "evidence_ids": ["rt037-runtime-app-launch"],
            }
        ],
        "public_safety": {
            "raw_endpoints_public": False,
            "raw_urls_public": False,
            "raw_headers_public": False,
            "raw_payloads_public": False,
            "raw_cookies_public": False,
            "raw_tokens_or_sessions_public": False,
            "raw_qr_targets_public": False,
            "raw_device_identifiers_public": False,
            "raw_local_paths_public": False,
            "raw_secrets_public": False,
            "real_user_data_public": False,
            "mutation_performed": False,
            "stream_or_session_started": False,
            "order_or_payment_performed": False,
            "device_binding_mutated": False,
            "tls_or_security_bypass_performed": False,
            "apk_modified_or_decompiled": False,
        },
        "blocked_reasons": [],
        "unverified_areas": ["state-change oracle"],
    }


def test_task037_valid_public_report_passes():
    assert validate_public_report(_valid_report()) == []


def test_task037_rejects_raw_endpoint_like_text():
    report = _valid_report()
    # Synthetic-only leak fixture: built from pieces so the public test file
    # does not carry a real-looking endpoint literal.
    report["api_coverage_ledger"][0]["note"] = "debug " + "/" + "api" + "/private/config"

    errors = validate_public_report(report)

    assert any("raw/private evidence-like text" in error for error in errors)


def test_task037_rejects_raw_device_address_like_text():
    report = _valid_report()
    # Synthetic-only leak fixture: reserved documentation-range address.
    report["safe_lane"]["target_alias"] = "192.0.2.10:5555"

    errors = validate_public_report(report)

    assert "safe_lane.target_alias must be task037-approved-tv-target." in errors
    assert any("raw/private evidence-like text" in error for error in errors)


def test_task037_rejects_raw_endpoint_like_key_text():
    report = _valid_report()
    report["coverage_summary"]["counts_by_api_category"] = {
        "/" + "api" + "/private/config": 1,
    }

    errors = validate_public_report(report)

    assert any("raw/private evidence-like key text" in error for error in errors)


def test_task037_rejects_mutation_overclaim():
    report = _valid_report()
    report["api_coverage_ledger"][0]["mutation_performed"] = True
    report["public_safety"]["mutation_performed"] = True

    errors = validate_public_report(report)

    assert "api_coverage_ledger[0].mutation_performed must be false." in errors
    assert "public_safety.mutation_performed must be false." in errors


def test_task037_rejects_boundary_action_performed():
    report = _valid_report()
    report["boundary_ledger"][0]["action_performed"] = True

    errors = validate_public_report(report)

    assert "boundary_ledger[0].action_performed must be false." in errors


def test_task037_rejects_budget_drift():
    report = _valid_report()
    report["budget"]["concurrency"] = 2
    report["budget"]["total_retry_count"] = 4

    errors = validate_public_report(report)

    assert "budget.concurrency must be 1." in errors
    assert "budget.total_retry_count must be an integer from 0 to 3." in errors


def test_task037_rejects_partial_live_claim_without_covered_api_row():
    report = _valid_report()
    for row in report["api_coverage_ledger"]:
        row["execution_status"] = "not_run"

    errors = validate_public_report(report)

    assert "live_api_execution_status partial_read_only_covered requires at least one covered API row." in errors


def test_task037_rejects_pass_when_direct_api_not_run_or_unverified():
    report = _valid_report()
    report["overall_status"] = "pass_read_only_safe_lane"
    report["live_api_execution_status"] = "not_run"
    report["unverified_areas"] = ["direct live API behavior"]

    errors = validate_public_report(report)

    assert (
        "overall_status pass_read_only_safe_lane requires live_api_execution_status partial_read_only_covered."
        in errors
    )
    assert "overall_status pass_read_only_safe_lane requires empty unverified_areas." in errors


def test_task037_rejects_pass_with_unknown_api_evidence_or_zero_requests():
    report = _valid_report()
    report["overall_status"] = "pass_read_only_safe_lane"
    report["unverified_areas"] = []
    for row in report["api_coverage_ledger"]:
        row["execution_status"] = "covered"
        row["evidence_status"] = "unknown"
        row["request_count"] = 0
    report["budget"]["total_live_request_count"] = 0

    errors = validate_public_report(report)

    assert "overall_status pass_read_only_safe_lane requires every API row evidence_status to be confirmed." in errors
    assert "overall_status pass_read_only_safe_lane requires every API row request_count to be positive." in errors


def test_task037_rejects_pass_when_budget_request_total_mismatches_api_rows():
    report = _valid_report()
    report["overall_status"] = "pass_read_only_safe_lane"
    report["unverified_areas"] = []
    for row in report["api_coverage_ledger"]:
        row["execution_status"] = "covered"
        row["evidence_status"] = "confirmed"
        row["request_count"] = 1
    report["budget"]["total_live_request_count"] = 1

    errors = validate_public_report(report)

    assert (
        "overall_status pass_read_only_safe_lane requires budget.total_live_request_count to equal API row request_count sum."
        in errors
    )


def test_task037_runtime_rows_require_checkpoint_fields():
    report = _valid_report()
    report["runtime_coverage_ledger"][0].pop("screen_alias")

    errors = validate_public_report(report)

    assert any("missing runtime checkpoint fields" in error for error in errors)


def test_task037_rejects_raw_values_printed_in_preflight():
    report = _valid_report()
    report["preflight"]["synthetic_secret_preflight"]["raw_values_printed"] = True

    errors = validate_public_report(report)

    assert "preflight.synthetic_secret_preflight.raw_values_printed must be false." in errors


def test_task037_rejects_covered_api_row_without_evidence_ids():
    report = _valid_report()
    report["api_coverage_ledger"][0]["evidence_ids"] = []

    errors = validate_public_report(report)

    assert "api_coverage_ledger[0].evidence_ids must contain at least one evidence id." in errors


def test_task037_rejects_covered_runtime_row_without_evidence_ids():
    report = _valid_report()
    report["runtime_coverage_ledger"][0]["evidence_ids"] = []

    errors = validate_public_report(report)

    assert "runtime_coverage_ledger[0].evidence_ids must contain at least one evidence id." in errors


def test_task037_rejects_anomaly_without_required_public_safe_fields():
    report = _valid_report()
    report["anomaly_ledger"][0].pop("public_safe_alias")
    report["anomaly_ledger"][0].pop("likely_or_hypothesis_cause")

    errors = validate_public_report(report)

    assert any("missing required fields" in error for error in errors)


def test_task037_committed_public_report_fixture_is_valid():
    report_path = Path("docs/qa/reports/task037_production_api_runtime_exploratory.summary.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert validate_public_report(report) == []


def test_task037_cli_returns_success_for_valid_report(tmp_path, capsys):
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_valid_report()), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 0
    assert "TASK-037 public report validation passed." in capsys.readouterr().out


def test_task037_cli_returns_failure_for_invalid_report(tmp_path):
    report = copy.deepcopy(_valid_report())
    report["public_safety"]["raw_tokens_or_sessions_public"] = True
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 1

import json
import subprocess
import sys

import pytest

from automation.quality.synthetic_redaction_corpus import (
    EXPECTED_VALIDATOR_COVERAGE,
    REQUIRED_CATEGORIES,
    iter_specimens,
    main,
    public_summary,
    release_gate_metadata_for_specimen,
    sanitized_device_inventory_payload_for_specimen,
    specimen_by_id,
    specimen_ids,
    validator_findings_for_specimen,
    webview_payment_metadata_for_specimen,
)
from automation.native_regression.validate_native_regression_report import validate_report as validate_native_regression_report
from automation.post_auth_navigation.validate_post_auth_navigation_report import validate_report as validate_post_auth_report
from automation.reporting.generate_release_gate_report import build_report as build_release_gate_report
from automation.webview_payment_safe_runner.generate_webview_payment_safe_report import (
    build_report as build_webview_payment_report,
)


EXPECTED_CATEGORIES = {
    "credential_like",
    "token_like",
    "url_endpoint_like",
    "route_deeplink_like",
    "local_apk_path_like",
    "hash_like",
    "device_identifier_like",
    "phone_otp_like",
    "payment_account_like",
    "qr_payload_like",
    "raw_evidence_reference_like",
}


def _assert_raw_absent(raw_value: str, text: str, specimen_id: str) -> None:
    if raw_value in text:
        raise AssertionError(f"{specimen_id} raw specimen leaked")


def _assert_sensitive_fragments_absent(specimen, text: str) -> None:
    _assert_raw_absent(specimen.value, text, specimen.specimen_id)
    for fragment in specimen.sensitive_fragments:
        _assert_raw_absent(fragment, text, specimen.specimen_id)


def _assert_no_raw_value_field(payload):
    if isinstance(payload, dict):
        if "value" in payload:
            raise AssertionError("public summary exposed a raw value field")
        for child in payload.values():
            _assert_no_raw_value_field(child)
    elif isinstance(payload, list):
        for child in payload:
            _assert_no_raw_value_field(child)


def _task020_report_with_specimen(raw_value: str):
    return {
        "schema_version": "task-020-post-auth-navigation-v1",
        "task_id": "TASK-020",
        "coverage_status": "sampled_bounded_runtime_coverage",
        "runtime_execution_status": "partial",
        "target": {
            "device_alias": "tv-tpv-013",
            "runtime_profile_alias": "tv-tpv-a12-013",
            "build_alias": "task-005-local-apk-001",
            "synthetic_user_alias": "qa-user-phone-001",
        },
        "resource_budget": {"max_screens": 1, "max_transition_edges": 1},
        "screens_observed": [
            {"screen_alias": "post_auth_home_unknown", "state_category": "post_auth_shell"}
        ],
        "transitions_observed": [],
        "boundaries_observed": [],
        "session_persistence_results": {
            "root_home_foreground": {"result": "pass"},
            "root_force_stop_relaunch": {"result": "pass"},
        },
        "public_safety": {
            "raw_phone_otp_committed": False,
            "raw_device_identifiers_committed": False,
            "raw_evidence_committed": False,
            "payment_webview_stream_profile_mutation_entered": False,
        },
        "synthetic_probe": raw_value,
    }


def _task024_report_with_specimen(raw_value: str):
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
        "synthetic_probe": raw_value,
    }


def test_corpus_covers_required_synthetic_classes():
    assert REQUIRED_CATEGORIES == EXPECTED_CATEGORIES
    assert {specimen.category for specimen in iter_specimens()} == EXPECTED_CATEGORIES
    assert len(specimen_ids()) == len(set(specimen_ids()))


def test_corpus_entries_have_explicit_synthetic_public_safe_provenance():
    for specimen in iter_specimens():
        assert specimen.synthetic is True, specimen.specimen_id
        assert specimen.public_safe is True, specimen.specimen_id
        assert specimen.provenance == "fabricated_task017_canary", specimen.specimen_id


def test_public_summary_never_exposes_raw_specimen_values():
    summary = public_summary()
    summary_text = json.dumps(summary, sort_keys=True)

    _assert_no_raw_value_field(summary)
    for item in summary["specimens"]:
        assert item["synthetic"] is True
        assert item["public_safe"] is True
        assert item["provenance"] == "fabricated_task017_canary"
    for specimen in iter_specimens():
        _assert_sensitive_fragments_absent(specimen, summary_text)


@pytest.mark.parametrize("specimen_id", specimen_ids())
def test_existing_public_safety_validators_catch_synthetic_specimens(specimen_id):
    specimen = specimen_by_id(specimen_id)
    findings_by_tool = validator_findings_for_specimen(specimen)
    all_findings = tuple(finding for findings in findings_by_tool.values() for finding in findings)
    findings_text = " ".join(all_findings)

    assert all_findings, specimen_id
    assert any(term in findings_text for term in specimen.expected_finding_terms), specimen_id
    _assert_sensitive_fragments_absent(specimen, findings_text)


def test_static_validator_coverage_matrix_matches_expected_synthetic_scope():
    observed = {
        "post_auth_navigation": [],
        "native_regression": [],
        "device_inventory": [],
    }
    for specimen in iter_specimens():
        findings = validator_findings_for_specimen(specimen)
        for tool_name in observed:
            if findings[tool_name]:
                observed[tool_name].append(specimen.specimen_id)

    assert {key: tuple(value) for key, value in observed.items()} == EXPECTED_VALIDATOR_COVERAGE


@pytest.mark.parametrize("specimen_id", specimen_ids())
def test_task020_report_validator_rejects_synthetic_specimens_without_echoing_values(tmp_path, specimen_id):
    specimen = specimen_by_id(specimen_id)
    report_path = tmp_path / f"{specimen.specimen_id}-task020.json"
    report_path.write_text(json.dumps(_task020_report_with_specimen(specimen.value)), encoding="utf-8")

    errors = validate_post_auth_report(report_path)
    error_text = " ".join(errors)

    assert errors, specimen_id
    _assert_sensitive_fragments_absent(specimen, error_text)


@pytest.mark.parametrize(
    "specimen_id",
    EXPECTED_VALIDATOR_COVERAGE["native_regression"],
)
def test_task024_report_validator_rejects_covered_synthetic_specimens_without_echoing_values(tmp_path, specimen_id):
    specimen = specimen_by_id(specimen_id)
    report_path = tmp_path / f"{specimen.specimen_id}-task024.json"
    report_path.write_text(json.dumps(_task024_report_with_specimen(specimen.value)), encoding="utf-8")

    errors = validate_native_regression_report(report_path)
    error_text = " ".join(errors)

    assert errors, specimen_id
    _assert_sensitive_fragments_absent(specimen, error_text)


@pytest.mark.parametrize(
    "specimen_id",
    tuple(specimen.specimen_id for specimen in iter_specimens() if specimen.webview_payment_redaction_expected),
)
def test_webview_payment_report_redacts_expected_synthetic_specimens(tmp_path, specimen_id):
    specimen = specimen_by_id(specimen_id)
    metadata_path = tmp_path / f"{specimen.specimen_id}-webview-payment.json"
    metadata_path.write_text(json.dumps(webview_payment_metadata_for_specimen(specimen)), encoding="utf-8")

    report = build_webview_payment_report(metadata_path)
    serialized = json.dumps(report, sort_keys=True)

    assert report["redaction_status"] == "redacted", specimen_id
    _assert_sensitive_fragments_absent(specimen, serialized)


@pytest.mark.parametrize(
    "specimen_id",
    tuple(specimen.specimen_id for specimen in iter_specimens() if specimen.release_gate_redaction_expected),
)
def test_release_gate_report_redacts_expected_synthetic_specimens(tmp_path, specimen_id):
    specimen = specimen_by_id(specimen_id)
    metadata_path = tmp_path / f"{specimen.specimen_id}.json"
    metadata_path.write_text(json.dumps(release_gate_metadata_for_specimen(specimen)), encoding="utf-8")

    report = build_release_gate_report(metadata_path)
    serialized = json.dumps(report, sort_keys=True)

    assert report["redaction_status"] == "redacted", specimen_id
    _assert_sensitive_fragments_absent(specimen, serialized)


@pytest.mark.parametrize(
    "specimen_id",
    tuple(specimen.specimen_id for specimen in iter_specimens() if specimen.device_inventory_redaction_expected),
)
def test_device_inventory_public_sanitizer_redacts_expected_synthetic_specimens(specimen_id):
    specimen = specimen_by_id(specimen_id)
    sanitized, redacted = sanitized_device_inventory_payload_for_specimen(specimen)
    serialized = json.dumps(sanitized, sort_keys=True)

    assert redacted is True, specimen_id
    _assert_sensitive_fragments_absent(specimen, serialized)


def test_cli_outputs_ids_and_categories_only(capsys):
    exit_code = main(["--json"])

    assert exit_code == 0
    output = capsys.readouterr().out
    loaded = json.loads(output)
    assert loaded["specimen_count"] == len(specimen_ids())
    _assert_no_raw_value_field(loaded)
    for specimen in iter_specimens():
        _assert_sensitive_fragments_absent(specimen, output)


def test_script_direct_invocation_outputs_ids_and_categories_only():
    completed = subprocess.run(
        [sys.executable, "automation/quality/synthetic_redaction_corpus.py", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    loaded = json.loads(completed.stdout)
    _assert_no_raw_value_field(loaded)
    for specimen in iter_specimens():
        _assert_sensitive_fragments_absent(specimen, completed.stdout)

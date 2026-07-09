import copy
import json

from automation.api_layer_contract.validate_task033_api_redaction_prod_safety_guards import (
    build_report,
    main,
    validate_public_report,
)


def _valid_report():
    report = build_report(generated_at_utc="2026-07-09T00:00:00Z")
    assert report["overall_status"] == "pass"
    assert validate_public_report(report) == []
    return report


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _source_paths(tmp_path):
    task028 = {
        "task_id": "TASK-028",
        "overall_status": "pass",
        "evidence_status": "likely",
        "runtime_execution_status": "not_run",
        "live_api_execution_status": "not_run",
        "coverage_summary": {
            "counts_by_layer": {"security": 8},
            "counts_by_test_type": {"security_redaction": 8},
            "counts_by_automation_target": {"log_artifact_scanner_or_guard_test": 8},
        },
    }
    task036 = {
        "task_id": "TASK-036",
        "overall_status": "partial_blocked",
        "evidence_status": "likely_with_blockers",
        "runtime_execution_status": "not_run",
        "live_api_execution_status": "not_run",
        "coverage_area_ledger": [
            {
                "area": "api_redaction_prod_safety_guards",
                "source_task": "TASK-033",
                "known_security_rows": 8,
                "known_redaction_tests": 8,
                "status": "tracked_summary_validated_synthetic_guard_tests_required",
            }
        ],
    }
    task028_path = tmp_path / "task028.summary.json"
    task036_path = tmp_path / "task036.summary.json"
    _write_json(task028_path, task028)
    _write_json(task036_path, task036)
    return task028_path, task036_path


def test_task033_builds_valid_synthetic_guard_report():
    report = _valid_report()

    assert report["production_safety_classification"] == "PROD_SAFE_OFFLINE_STATIC_AND_SYNTHETIC_ONLY"
    assert report["runtime_execution_status"] == "not_run"
    assert report["live_api_execution_status"] == "not_run"
    assert report["coverage_summary"]["guard_count"] == 10
    assert report["source_summary"]["known_security_rows"] == 8
    assert report["source_summary"]["known_redaction_tests"] == 8
    assert (
        report["source_summary"]["source_reports"]["task036"]["task033_ledger_status"]
        == "tracked_summary_validated_synthetic_guard_tests_required"
    )
    assert report["public_safety"]["synthetic_specimens_only"] is True
    assert report["public_safety"]["live_budget_zero"] is True


def test_task033_accepts_minimal_public_safe_source_summaries(tmp_path):
    task028_path, task036_path = _source_paths(tmp_path)

    report = build_report(
        task028_report_path=task028_path,
        task036_report_path=task036_path,
        generated_at_utc="2026-07-09T00:00:00Z",
    )

    assert report["overall_status"] == "pass"
    assert validate_public_report(report) == []


def test_task033_blocks_source_summary_count_mismatch(tmp_path):
    task028_path, task036_path = _source_paths(tmp_path)
    task028 = json.loads(task028_path.read_text(encoding="utf-8"))
    task028["coverage_summary"]["counts_by_layer"]["security"] = 7
    task028_path.write_text(json.dumps(task028), encoding="utf-8")

    report = build_report(
        task028_report_path=task028_path,
        task036_report_path=task036_path,
        generated_at_utc="2026-07-09T00:00:00Z",
    )

    assert report["overall_status"] == "blocked"
    assert "task028_security_row_count_invalid" in report["blocked_reasons"]


def test_task033_blocks_source_summary_live_api_overclaim(tmp_path):
    task028_path, task036_path = _source_paths(tmp_path)
    task036 = json.loads(task036_path.read_text(encoding="utf-8"))
    task036["live_api_execution_status"] = "partial_read_only_covered"
    task036_path.write_text(json.dumps(task036), encoding="utf-8")

    report = build_report(
        task028_report_path=task028_path,
        task036_report_path=task036_path,
        generated_at_utc="2026-07-09T00:00:00Z",
    )

    assert report["overall_status"] == "blocked"
    assert "task036_live_api_status_must_be_not_run" in report["blocked_reasons"]


def test_task033_rejects_raw_nested_url_endpoint_value():
    report = _valid_report()
    report["guard_ledger"][0]["debug_note"] = "synthetic leak " + "https" + "://" + "example.invalid" + "/" + "api" + "/private"

    errors = validate_public_report(report)

    assert any("raw/private evidence-like text" in error for error in errors)


def test_task033_rejects_raw_private_key_text():
    report = _valid_report()
    report["coverage_summary"]["counts_by_guard_category"] = {
        "/" + "api" + "/private": 1,
    }

    errors = validate_public_report(report)

    assert any("raw/private evidence-like key text" in error or "contains_raw_private_key_text" in error for error in errors)


def test_task033_rejects_raw_local_path_leak():
    report = _valid_report()
    report["redaction_specimen_suite"]["note"] = "artifact " + "C:" + "\\" + "Users" + "\\" + "tester" + "\\" + "raw.log"

    errors = validate_public_report(report)

    assert any("raw/private evidence-like text" in error for error in errors)


def test_task033_rejects_unsafe_live_and_runtime_statuses():
    report = _valid_report()
    report["live_api_execution_status"] = "covered"
    report["android_runtime_status"] = "pass"

    errors = validate_public_report(report)

    assert "live_api_execution_status_must_be_not_run" in errors
    assert "android_runtime_status_must_be_not_run" in errors


def test_task033_rejects_unsafe_public_safety_boolean():
    report = _valid_report()
    report["public_safety"]["raw_tokens_or_sessions_public"] = True

    errors = validate_public_report(report)

    assert "public_safety_raw_tokens_or_sessions_public_must_be_false" in errors


def test_task033_rejects_missing_required_field():
    report = _valid_report()
    del report["production_safety_boundary"]

    errors = validate_public_report(report)

    assert "report_missing_required_fields:production_safety_boundary" in errors


def test_task033_rejects_unknown_top_level_field():
    report = _valid_report()
    report["debug_extra"] = "synthetic alias only"

    errors = validate_public_report(report)

    assert "report_unknown_fields:debug_extra" in errors


def test_task033_rejects_unknown_nested_fields():
    report = _valid_report()
    report["guard_ledger"][0]["debug_extra"] = "synthetic alias only"
    report["redaction_specimen_suite"]["debug_extra"] = "synthetic alias only"
    report["source_summary"]["debug_extra"] = "synthetic alias only"
    report["source_summary"]["source_reports"]["task028"]["debug_extra"] = "synthetic alias only"
    report["coverage_summary"]["debug_extra"] = 1
    report["production_safety_boundary"]["debug_extra"] = "synthetic alias only"

    errors = validate_public_report(report)

    assert "guard_ledger[0]_unknown_fields:debug_extra" in errors
    assert "redaction_specimen_suite_unknown_fields:debug_extra" in errors
    assert "source_summary_unknown_fields:debug_extra" in errors
    assert "source_summary_task028_unknown_fields:debug_extra" in errors
    assert "coverage_summary_unknown_fields:debug_extra" in errors
    assert "production_safety_boundary_unknown_fields:debug_extra" in errors


def test_task033_rejects_hidden_nested_runtime_overclaim_fields():
    report = _valid_report()
    report["production_safety_boundary"]["session_execution_status"] = "pass"
    report["production_safety_boundary"]["apk_install_status"] = "pass"
    report["production_safety_boundary"]["adb_execution_status"] = "pass"
    report["production_safety_boundary"]["payment_status"] = "pass"

    errors = validate_public_report(report)

    assert (
        "production_safety_boundary_unknown_fields:"
        "adb_execution_status,apk_install_status,payment_status,session_execution_status"
    ) in errors


def test_task033_rejects_pass_with_blockers():
    report = _valid_report()
    report["blocked_reasons"] = ["blocked_missing_synthetic_specimens_file"]

    errors = validate_public_report(report)

    assert "pass_report_must_have_empty_blocked_reasons" in errors


def test_task033_rejects_live_budget_drift():
    report = _valid_report()
    report["production_safety_boundary"]["live_request_count"] = 1
    report["production_safety_boundary"]["retry_count"] = 1
    report["production_safety_boundary"]["concurrency"] = 1

    errors = validate_public_report(report)

    assert "production_safety_boundary_live_request_count_must_be_zero" in errors
    assert "production_safety_boundary_retry_count_must_be_zero" in errors
    assert "production_safety_boundary_concurrency_must_be_zero" in errors


def test_task033_rejects_guard_not_marked_synthetic_only():
    report = _valid_report()
    report["guard_ledger"][0]["synthetic_only"] = False

    errors = validate_public_report(report)

    assert "guard_ledger[0]_synthetic_only_must_be_true" in errors


def test_task033_rejects_missing_guard_category():
    report = _valid_report()
    report["guard_ledger"] = [
        row for row in report["guard_ledger"] if row["category"] != "qr_target"
    ]
    report["coverage_summary"]["guard_count"] -= 1
    del report["coverage_summary"]["counts_by_guard_category"]["qr_target"]

    errors = validate_public_report(report)

    assert any("qr_target" in error for error in errors)


def test_task033_rejects_coverage_count_drift():
    report = _valid_report()
    report["coverage_summary"]["counts_by_validation_status"]["pass"] += 1

    errors = validate_public_report(report)

    assert "coverage_summary_counts_by_validation_status_total_mismatch" in errors


def test_task033_missing_external_specimens_is_controlled_partial_blocked(tmp_path):
    report = build_report(tmp_path / "missing-specimens.json", generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "partial_blocked"
    assert report["blocked_reasons"] == ["blocked_missing_synthetic_specimens_file"]
    assert validate_public_report(report) == []


def test_task033_blocks_malformed_external_specimen_file(tmp_path):
    specimen_path = tmp_path / "specimens.json"
    specimen_path.write_text("{bad", encoding="utf-8")

    report = build_report(specimen_path, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "synthetic_specimens_json_malformed" in report["blocked_reasons"]


def test_task033_cli_writes_valid_report(tmp_path, capsys):
    output_path = tmp_path / "task033.summary.json"

    exit_code = main(["--report", str(output_path)])

    cli_result = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert cli_result["validation_status"] == "pass"
    assert written["overall_status"] == "pass"
    assert validate_public_report(written) == []


def test_task033_cli_missing_specimens_defaults_nonzero_partial_blocked(tmp_path, capsys):
    output_path = tmp_path / "task033.summary.json"

    exit_code = main(["--specimens", str(tmp_path / "missing.json"), "--report", str(output_path)])

    cli_result = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert cli_result["validation_status"] == "partial_blocked"
    assert written["overall_status"] == "partial_blocked"


def test_task033_cli_allows_partial_blocked_zero_exit_when_explicit(tmp_path, capsys):
    exit_code = main(
        [
            "--specimens",
            str(tmp_path / "missing.json"),
            "--allow-partial-blocked-exit-zero",
        ]
    )

    cli_result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert cli_result["validation_status"] == "partial_blocked"


def test_task033_external_specimens_use_synthetic_aliases_only(tmp_path):
    valid = _valid_report()
    specimen_path = tmp_path / "specimens.json"
    specimen_path.write_text(json.dumps({"specimens": copy.deepcopy(valid["guard_ledger"])}), encoding="utf-8")

    report = build_report(specimen_path, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "pass"
    assert report["redaction_specimen_suite"]["specimen_source"] == "external_fabricated_synthetic_specimens"
    assert validate_public_report(report) == []


def test_task033_external_specimens_reject_unknown_extra_fields_before_projection(tmp_path):
    valid = _valid_report()
    specimens = copy.deepcopy(valid["guard_ledger"])
    specimens[0]["debug_extra"] = "synthetic alias only"
    specimen_path = tmp_path / "specimens.json"
    specimen_path.write_text(json.dumps({"specimens": specimens}), encoding="utf-8")

    report = build_report(specimen_path, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "synthetic_specimens[0]_unknown_fields:debug_extra" in report["blocked_reasons"]


def test_task033_external_specimens_reject_raw_extra_fields_before_projection(tmp_path):
    valid = _valid_report()
    specimens = copy.deepcopy(valid["guard_ledger"])
    specimens[0]["debug_extra"] = "https" + "://" + "example.invalid" + "/" + "api" + "/private"
    specimen_path = tmp_path / "specimens.json"
    specimen_path.write_text(json.dumps({"specimens": specimens}), encoding="utf-8")

    report = build_report(specimen_path, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "synthetic_specimens[0]_unknown_fields:debug_extra" in report["blocked_reasons"]
    assert any("raw/private evidence-like text" in reason for reason in report["blocked_reasons"])

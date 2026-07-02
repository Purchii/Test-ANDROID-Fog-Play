import json
import subprocess
import sys

from automation.post_auth_navigation.validate_post_auth_navigation_report import main, validate_report


def _valid_report():
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
        "resource_budget": {"max_screens": 40, "max_transition_edges": 160},
        "screens_observed": [
            {"screen_alias": "post_auth_home_unknown", "state_category": "post_auth_shell"}
        ],
        "transitions_observed": [
            {
                "transition_alias": "transition_boundary_payment_001",
                "from_screen_alias": "post_auth_home_unknown",
                "to_screen_alias": "payment_boundary_001",
                "trigger_category": "payment_subscription_purchase",
                "boundary_type": "payment_subscription_purchase",
                "result": "blocked_by_boundary",
            }
        ],
        "boundaries_observed": [
            {
                "boundary_alias": "payment_boundary_001",
                "boundary_type": "payment_subscription_purchase",
                "action_taken": "not_entered",
                "result": "blocked_by_boundary",
            }
        ],
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
    }


def test_validator_accepts_alias_only_summary(tmp_path):
    report_path = tmp_path / "task020_report.json"
    report_path.write_text(json.dumps(_valid_report()), encoding="utf-8")

    assert validate_report(report_path) == []


def test_validator_rejects_missing_file(tmp_path):
    errors = validate_report(tmp_path / "missing.json")

    assert errors == ["Report file was not found."]


def test_validator_rejects_malformed_json(tmp_path):
    report_path = tmp_path / "bad.json"
    report_path.write_text("{bad-json", encoding="utf-8")

    errors = validate_report(report_path)

    assert any("not valid JSON" in error for error in errors)


def test_validator_rejects_raw_artifact_paths(tmp_path):
    report = _valid_report()
    report["artifact_ref"] = ".qa_local/evidence/task-020/run/raw.xml"
    report_path = tmp_path / "task020_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    errors = validate_report(report_path)

    assert any("raw local path" in error for error in errors)


def test_validator_rejects_unsafe_public_safety_flags(tmp_path):
    report = _valid_report()
    report["public_safety"]["raw_evidence_committed"] = True
    report_path = tmp_path / "task020_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    errors = validate_report(report_path)

    assert "public_safety.raw_evidence_committed must be false." in errors


def test_cli_returns_zero_for_valid_report(tmp_path, capsys):
    report_path = tmp_path / "task020_report.json"
    report_path.write_text(json.dumps(_valid_report()), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "pass"


def test_cli_returns_one_for_invalid_report(tmp_path, capsys):
    report = _valid_report()
    report["runtime_execution_status"] = "done"
    report_path = tmp_path / "task020_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    exit_code = main(["--report", str(report_path)])

    assert exit_code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "fail"
    assert result["errors"]


def test_validator_script_direct_invocation_works(tmp_path):
    report_path = tmp_path / "task020_report.json"
    report_path.write_text(json.dumps(_valid_report()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "automation/post_auth_navigation/validate_post_auth_navigation_report.py",
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

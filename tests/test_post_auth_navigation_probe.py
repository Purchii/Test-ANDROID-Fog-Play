import json
import os

import pytest

from automation.post_auth_navigation.run_post_auth_navigation_probe import (
    RAW_EVIDENCE_ROOT,
    detect_boundary,
    is_safe_alias,
    main,
    validate_output_path,
    validate_report_shape,
)


def _valid_report():
    return {
        "schema_version": "task-020-post-auth-navigation-v1",
        "task_id": "TASK-020",
        "coverage_status": "sampled_bounded_runtime_coverage",
        "runtime_execution_status": "pass",
        "target": {
            "device_alias": "tv-tpv-013",
            "runtime_profile_alias": "tv-tpv-a12-013",
            "build_alias": "task-005-local-apk-001",
            "synthetic_user_alias": "qa-user-phone-001",
        },
        "resource_budget": {"max_screens": 40},
        "screens_observed": [
            {
                "screen_alias": "post_auth_home_unknown",
                "state_category": "post_auth_shell",
                "focus_status": "pass",
            }
        ],
        "transitions_observed": [
            {
                "transition_alias": "transition_home_catalog_001",
                "from_screen_alias": "post_auth_home_unknown",
                "to_screen_alias": "native_catalog_or_list_001",
                "trigger_category": "dpad_select_safe_native",
                "result": "pass",
                "evidence_status": "confirmed",
            }
        ],
        "states_observed": ["post_auth_shell", "catalog_or_list"],
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


def test_default_command_blocks_and_does_not_require_runtime(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["runtime_execution_status"] == "not_run"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["blocked_reasons"] == ["--allow-runtime was not provided"]


def test_allow_runtime_without_input_still_blocks(capsys):
    exit_code = main(["--allow-runtime"])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["runtime_execution_status"] == "not_run"
    assert report["production_safety_classification"] == "PROD_CONDITIONAL"


def test_output_paths_are_constrained_to_task020_families():
    assert validate_output_path(".qa_local/evidence/task-020/run/report.json")
    assert validate_output_path(".qa_local/evidence/task-020/run/deep/report.json")
    assert validate_output_path("docs/qa/reports/task020.json", public_summary=True)
    assert not validate_output_path(".qa_local/evidence/task-019/run/report.json")
    assert not validate_output_path(".qa_local/devices/raw_adb_devices.json")
    assert not validate_output_path(".qa_local/secrets/qa_user.env")
    assert not validate_output_path(".qa_local/apks/task-005/app.apk")
    assert not validate_output_path("C:/tmp/task020.json")
    assert not validate_output_path("docs/qa/private/task020.json", public_summary=True)
    assert not validate_output_path("../escape.json")
    assert not validate_output_path(".qa_local/evidence/task-020/../task-019/report.json")


def test_boundary_detection_is_conservative():
    assert detect_boundary("Open payment checkout") == "payment_subscription_purchase"
    assert detect_boundary("Оплатить подписка") == "payment_subscription_purchase"
    assert detect_boundary("Open WebView redirect") == "webview_redirect_browser"
    assert detect_boundary("start game stream playback") == "stream_webrtc_media_playback"
    assert detect_boundary("profile edit") == "profile_account_mutation"
    assert detect_boundary("safe catalog item") is None


def test_public_safe_alias_rejects_raw_values():
    assert is_safe_alias("native_catalog_or_list_001")
    assert not is_safe_alias("https://private.example/path")
    assert not is_safe_alias(".qa_local/evidence/task-020/raw.xml")
    assert not is_safe_alias("otp_token_001")
    assert not is_safe_alias("screen with spaces")


def test_valid_alias_only_report_passes_shape_validation():
    assert validate_report_shape(_valid_report()) == []


def test_report_validation_rejects_raw_values_and_identifiers():
    report = _valid_report()
    report["screens_observed"][0]["notes"] = "phone +79990000000"
    report["transitions_observed"][0]["to_screen_alias"] = "https://private.example/path"
    report["target"]["device_alias"] = "tv-other-001"

    errors = validate_report_shape(report)

    assert any("phone-like" in error for error in errors)
    assert any("to_screen_alias is not public-safe" in error for error in errors)
    assert "target.device_alias must be tv-tpv-013." in errors


@pytest.mark.parametrize(
    ("field_value", "expected"),
    [
        (r".qa_local\evidence\task-020\run\raw.xml", "raw local path"),
        ("OTP 123456", "OTP-like value"),
        ("account_id=qa-user-raw-001", "raw account identifier"),
        ("a" * 64, "raw hash-like value"),
    ],
)
def test_report_validation_rejects_qa_a_false_pass_cases(field_value, expected):
    report = _valid_report()
    report["screens_observed"][0]["notes"] = field_value

    errors = validate_report_shape(report)

    assert any(expected in error for error in errors)


def test_report_validation_requires_exact_schema_version():
    report = _valid_report()
    report["schema_version"] = "wrong-version"

    errors = validate_report_shape(report)

    assert "schema_version must be task-020-post-auth-navigation-v1." in errors


def test_boundary_transition_cannot_pass():
    report = _valid_report()
    report["transitions_observed"][0]["trigger_category"] = "payment checkout"
    report["transitions_observed"][0]["result"] = "pass"

    errors = validate_report_shape(report)

    assert any("boundary trigger must be blocked_by_boundary" in error for error in errors)


def test_session_checkpoint_not_run_requires_reason():
    report = _valid_report()
    report["session_persistence_results"]["root_home_foreground"] = {"result": "not_run"}

    errors = validate_report_shape(report)

    assert "session_persistence_results.root_home_foreground.reason is required when not_run." in errors


def test_public_summary_and_raw_output_are_written(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    public_path = "docs/qa/reports/task020_unit_probe_output.json"
    raw_path = ".qa_local/evidence/task-020/unit-run/probe.json"

    exit_code = main(["--public-summary", public_path, "--raw-output", raw_path])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert (tmp_path / public_path).exists()
    assert (tmp_path / raw_path).exists()


def test_invalid_output_paths_block_without_writing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    invalid_public_path = "docs/qa/private/task020_unit_probe_output.json"
    invalid_raw_path = ".qa_local/evidence/task-019/unit-run/probe.json"

    exit_code = main(["--public-summary", invalid_public_path, "--raw-output", invalid_raw_path])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert "raw output path must stay under .qa_local/evidence/task-020/" in report["blocked_reasons"]
    assert not (tmp_path / invalid_public_path).exists()
    assert not (tmp_path / invalid_raw_path).exists()


def test_invalid_raw_output_blocks_valid_public_write(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    public_path = "docs/qa/reports/task020_unit_probe_output.json"
    invalid_raw_path = ".qa_local/evidence/task-019/unit-run/probe.json"

    exit_code = main(["--public-summary", public_path, "--raw-output", invalid_raw_path])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert not (tmp_path / public_path).exists()
    assert not (tmp_path / invalid_raw_path).exists()


def test_invalid_public_output_blocks_valid_raw_write(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    invalid_public_path = "docs/qa/private/task020_unit_probe_output.json"
    raw_path = ".qa_local/evidence/task-020/unit-run/probe.json"

    exit_code = main(["--public-summary", invalid_public_path, "--raw-output", raw_path])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert not (tmp_path / invalid_public_path).exists()
    assert not (tmp_path / raw_path).exists()


def test_output_path_rejects_symlink_escape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / RAW_EVIDENCE_ROOT
    root.mkdir(parents=True)
    link = root / "escape"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable in this environment")

    assert not validate_output_path(link / "report.json")

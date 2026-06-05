import json

from automation.manual_runtime_maps.generate_map_report import build_report, main


def _complete_metadata():
    return {
        "approved_build": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved build metadata placeholder for unit test.",
        },
        "approved_target": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved target metadata placeholder for unit test.",
        },
        "approved_config": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved config metadata placeholder for unit test.",
        },
        "redaction_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved redaction policy placeholder for unit test.",
        },
        "synthetic_fixture_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved synthetic fixture policy placeholder for unit test.",
        },
        "evidence_storage": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved ignored evidence storage placeholder for unit test.",
        },
        "cleanup_rollback": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved cleanup and rollback placeholder for unit test.",
        },
    }


def test_missing_metadata_generates_blocked_map_report():
    report = build_report()

    assert report["task_id"] == "TASK-004"
    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["prerequisites"]["approved_build"]["present"] is False
    assert report["prerequisites"]["approved_target"]["present"] is False
    assert report["prerequisites"]["approved_config"]["present"] is False
    assert report["prerequisites"]["redaction_policy"]["present"] is False
    assert report["prerequisites"]["synthetic_fixture_policy"]["present"] is False
    assert report["prerequisites"]["evidence_storage"]["present"] is False
    assert report["prerequisites"]["cleanup_rollback"]["present"] is False
    assert report["blocked_reasons"]


def test_partial_metadata_without_runtime_map_prerequisites_stays_blocked(tmp_path):
    metadata = _complete_metadata()
    metadata.pop("synthetic_fixture_policy")
    metadata.pop("evidence_storage")
    metadata.pop("cleanup_rollback")
    metadata_path = tmp_path / "map_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert "synthetic_fixture_policy is not approved or not present." in report["blocked_reasons"]
    assert "evidence_storage is not approved or not present." in report["blocked_reasons"]
    assert "cleanup_rollback is not approved or not present." in report["blocked_reasons"]


def test_complete_metadata_generates_not_run_templates_without_pass(tmp_path):
    metadata_path = tmp_path / "map_metadata.json"
    metadata_path.write_text(json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    expected_categories = {
        "first_screen",
        "screen_inventory",
        "transitions",
        "initial_focus",
        "d_pad_directions",
        "focus_traps",
        "back_home",
        "accessibility_localization",
        "redacted_evidence",
    }
    screen_categories = {item["category"] for item in report["screen_map_sections"]}
    focus_categories = {item["category"] for item in report["focus_map_checks"]}

    assert report["overall_status"] == "not_run"
    assert report["evidence_status"] == "unknown"
    assert report["blocked_reasons"] == []
    assert screen_categories == expected_categories
    assert focus_categories == expected_categories
    assert all(item["result"] == "not_run" for item in report["screen_map_sections"])
    assert all(item["evidence_status"] == "unknown" for item in report["screen_map_sections"])
    assert all(item["result"] == "not_run" for item in report["focus_map_checks"])
    assert all(item["evidence_status"] == "unknown" for item in report["focus_map_checks"])
    assert '"pass"' not in json.dumps(report)


def test_cli_prints_map_report_to_stdout(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["screen_map_sections"]
    assert report["focus_map_checks"]


def test_cli_writes_map_report_to_output_path(tmp_path):
    output_path = tmp_path / "map_report.json"

    exit_code = main(["--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert report["verification"][0]["classification"] == "PROD_SAFE"
    assert report["verification"][0]["result"] == "not_run"


def test_malformed_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "map_metadata.json"
    metadata_path.write_text("{not-json", encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert any("not valid JSON" in reason for reason in report["blocked_reasons"])


def test_invalid_evidence_status_normalizes_to_unknown_and_blocks_not_run(tmp_path):
    metadata = _complete_metadata()
    metadata["approved_build"]["evidence_status"] = "verified"
    metadata_path = tmp_path / "map_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["prerequisites"]["approved_build"]["evidence_status"] == "unknown"
    assert "approved_build does not have confirmed evidence." in report["blocked_reasons"]
    assert all(item["evidence_status"] == "unknown" for item in report["screen_map_sections"])
    assert all(item["result"] != "pass" for item in report["focus_map_checks"])


def test_metadata_with_utf8_bom_is_supported(tmp_path):
    metadata_path = tmp_path / "map_metadata.json"
    metadata_path.write_text("\ufeff" + json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    assert "not valid JSON" not in " ".join(report["blocked_reasons"])
    assert report["overall_status"] == "not_run"
    assert report["prerequisites"]["approved_build"]["present"] is True


def test_metadata_notes_and_artifacts_are_redacted(tmp_path):
    secret_pair = "api_key" + "=" + "abc123"
    private_url = "http" + "s://" + "private.example/path"
    private_email = "user" + "@" + "example.com"
    private_windows_path = "C:" + "\\Users\\qa\\private"
    private_unix_path = "/" + "home/qa/private/log.txt"
    session_pair = "session" + "=" + "secret-value"
    authorization_pair = "authorization: Bearer " + "auth-secret"
    long_value = "A" * 40
    metadata = _complete_metadata()
    metadata["approved_build"]["note"] = (
        f"{private_windows_path} {secret_pair} {authorization_pair} {private_url} {private_email} {long_value}"
    )
    metadata["artifacts"] = [
        {
            "name": "manual map raw reference",
            "reference": f"{private_unix_path} {session_pair}",
            "evidence_status": "verified",
        }
    ]
    metadata_path = tmp_path / "map_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    serialized = json.dumps(report)

    assert report["redaction_status"] == "redacted"
    assert "abc123" not in serialized
    assert "secret-value" not in serialized
    assert "auth-secret" not in serialized
    assert "private.example" not in serialized
    assert "user@example.com" not in serialized
    assert ("C:" + "\\Users\\qa") not in serialized
    assert ("/" + "home/qa") not in serialized
    assert long_value not in serialized
    assert report["artifacts"][0]["evidence_status"] == "unknown"
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_URL]" in serialized
    assert "[REDACTED_EMAIL]" in serialized
    assert "[REDACTED_PATH]" in serialized
    assert "[REDACTED_OPAQUE_VALUE]" in serialized

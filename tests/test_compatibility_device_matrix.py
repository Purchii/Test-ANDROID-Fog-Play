import json

from automation.compatibility_device_matrix.generate_compatibility_device_matrix_report import build_report, main


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
        "device_inventory_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved device inventory policy placeholder for unit test.",
        },
        "matrix_scope": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved matrix scope placeholder for unit test.",
        },
        "compatibility_criteria": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved compatibility criteria placeholder for unit test.",
        },
        "redaction_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved redaction policy placeholder for unit test.",
        },
        "evidence_storage": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved ignored evidence storage placeholder for unit test.",
        },
        "fixture_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved fixture policy placeholder for unit test.",
        },
        "security_review": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved security review placeholder for unit test.",
        },
        "qa_review": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved QA review placeholder for unit test.",
        },
    }


def test_missing_metadata_generates_blocked_compatibility_report():
    report = build_report()

    assert report["task_id"] == "TASK-009"
    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["prerequisites"]["approved_build"]["present"] is False
    assert report["prerequisites"]["device_inventory_policy"]["present"] is False
    assert report["prerequisites"]["matrix_scope"]["present"] is False
    assert report["prerequisites"]["compatibility_criteria"]["present"] is False
    assert report["prerequisites"]["security_review"]["present"] is False
    assert report["prerequisites"]["qa_review"]["present"] is False
    assert report["blocked_reasons"]


def test_malformed_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "compatibility_metadata.json"
    metadata_path.write_text("{not-json", encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert any("not valid JSON" in reason for reason in report["blocked_reasons"])


def test_non_object_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "compatibility_metadata.json"
    metadata_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("must be a JSON object" in reason for reason in report["blocked_reasons"])


def test_partial_or_non_confirmed_metadata_stays_blocked(tmp_path):
    metadata = _complete_metadata()
    metadata.pop("matrix_scope")
    metadata["compatibility_criteria"]["present"] = False
    metadata["qa_review"]["evidence_status"] = "likely"
    metadata_path = tmp_path / "compatibility_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert "matrix_scope is not approved or not present." in report["blocked_reasons"]
    assert "compatibility_criteria is not approved or not present." in report["blocked_reasons"]
    assert "qa_review does not have confirmed evidence." in report["blocked_reasons"]


def test_invalid_evidence_status_normalizes_to_unknown_and_blocks(tmp_path):
    metadata = _complete_metadata()
    metadata["approved_build"]["evidence_status"] = "verified"
    metadata_path = tmp_path / "compatibility_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["prerequisites"]["approved_build"]["evidence_status"] == "unknown"
    assert "approved_build does not have confirmed evidence." in report["blocked_reasons"]
    assert all(item["evidence_status"] == "unknown" for item in report["planned_compatibility_checks"])
    assert all(item["result"] != "pass" for item in report["planned_compatibility_checks"])


def test_complete_confirmed_metadata_generates_not_run_plan_without_pass(tmp_path):
    metadata_path = tmp_path / "compatibility_metadata.json"
    metadata_path.write_text(json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    expected_categories = {
        "os_api_band",
        "form_factor",
        "performance_class",
        "display_output",
        "input_focus",
        "network_class",
        "locale_accessibility",
        "webview_webrtc_surface",
        "install_update_path",
        "redacted_evidence",
    }
    categories = {item["category"] for item in report["planned_compatibility_checks"]}

    assert report["overall_status"] == "not_run"
    assert report["evidence_status"] == "unknown"
    assert report["blocked_reasons"] == []
    assert categories == expected_categories
    assert all(item["result"] == "not_run" for item in report["planned_compatibility_checks"])
    assert all(item["evidence_status"] == "unknown" for item in report["planned_compatibility_checks"])
    assert report["device_profiles"][0]["alias"] == "device-template-001"
    assert '"pass"' not in json.dumps(report)


def test_cli_prints_compatibility_report_to_stdout(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["planned_compatibility_checks"]


def test_cli_writes_compatibility_report_to_output_path(tmp_path):
    output_path = tmp_path / "compatibility_report.json"

    exit_code = main(["--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert report["verification"][0]["classification"] == "PROD_SAFE"
    assert report["verification"][0]["result"] == "not_run"


def test_metadata_with_utf8_bom_is_supported(tmp_path):
    metadata_path = tmp_path / "compatibility_metadata.json"
    metadata_path.write_text("\ufeff" + json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    assert "not valid JSON" not in " ".join(report["blocked_reasons"])
    assert report["overall_status"] == "not_run"
    assert report["prerequisites"]["approved_build"]["present"] is True


def test_metadata_notes_profiles_and_artifacts_are_redacted(tmp_path):
    secret_pair = "api_key" + "=" + "abc123"
    private_url = "http" + "s://" + "private.example/path"
    private_email = "user" + "@" + "example.com"
    private_windows_path = "C:" + "\\Users\\qa\\private"
    private_unix_path = "/" + "home/qa/private/log.txt"
    session_pair = "session" + "=" + "secret-value"
    cookie_pair = "cookie" + "=" + "secret-cookie"
    authorization_pair = "authorization: Bearer " + "auth-secret"
    serial_pair = "serial" + "=" + "DEVICE123456"
    android_id_pair = "android_id" + "=" + "ANDROID123456"
    long_value = "A" * 40
    metadata = _complete_metadata()
    metadata["approved_build"]["note"] = (
        f"{private_windows_path} {secret_pair} {authorization_pair} {private_url} {private_email} {long_value}"
    )
    metadata["device_profiles"] = [
        {
            "alias": f"device-public-001 {serial_pair}",
            "target_category": "android_tv",
            "os_api_band": "api_31_33",
            "form_factor": "tv_panel",
            "display_class": "full_hd",
            "input_class": "dpad_remote",
            "network_class": "standard",
            "locale_class": "primary_locale",
            "evidence_status": "verified",
            "notes": f"{android_id_pair} {session_pair}",
        }
    ]
    metadata["artifacts"] = [
        {
            "name": "compatibility raw reference",
            "reference": f"{private_unix_path} {cookie_pair}",
            "evidence_status": "verified",
        }
    ]
    metadata_path = tmp_path / "compatibility_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    serialized = json.dumps(report)

    assert report["redaction_status"] == "redacted"
    assert "abc123" not in serialized
    assert "secret-value" not in serialized
    assert "secret-cookie" not in serialized
    assert "auth-secret" not in serialized
    assert "private.example" not in serialized
    assert "user@example.com" not in serialized
    assert "DEVICE123456" not in serialized
    assert "ANDROID123456" not in serialized
    assert ("C:" + "\\Users\\qa") not in serialized
    assert ("/" + "home/qa") not in serialized
    assert long_value not in serialized
    assert report["device_profiles"][0]["evidence_status"] == "unknown"
    assert report["artifacts"][0]["evidence_status"] == "unknown"
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_URL]" in serialized
    assert "[REDACTED_EMAIL]" in serialized
    assert "[REDACTED_PATH]" in serialized
    assert "[REDACTED_DEVICE_ID]" in serialized
    assert "[REDACTED_OPAQUE_VALUE]" in serialized

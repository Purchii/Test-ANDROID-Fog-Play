import json

from automation.webview_payment_safe_runner.generate_webview_payment_safe_report import (
    REQUIRED_PREREQUISITES,
    build_report,
    main,
)


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
        "webview_fixture_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved WebView scope placeholder for unit test.",
        },
        "payment_staging_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved staging-only non-real-payment fixture policy placeholder for unit test.",
        },
        "synthetic_user_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved synthetic account policy placeholder for unit test.",
        },
        "resource_budget": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved navigation scope placeholder for unit test.",
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
        "cleanup_rollback": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved cleanup and rollback placeholder for unit test.",
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


def test_missing_metadata_generates_blocked_webview_payment_report():
    report = build_report()

    assert report["task_id"] == "TASK-008"
    assert report["mode"] == "NON_AUTONOMOUS"
    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["prerequisites"]["approved_build"]["present"] is False
    assert report["prerequisites"]["webview_fixture_policy"]["present"] is False
    assert report["prerequisites"]["payment_staging_policy"]["present"] is False
    assert report["prerequisites"]["security_review"]["present"] is False
    assert report["prerequisites"]["qa_review"]["present"] is False
    assert report["blocked_reasons"]


def test_malformed_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "webview_payment_metadata.json"
    metadata_path.write_text("{not-json", encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert any("not valid JSON" in reason for reason in report["blocked_reasons"])


def test_missing_metadata_path_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "missing_webview_payment_metadata.json"

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("metadata file was not found" in reason for reason in report["blocked_reasons"])


def test_non_object_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "webview_payment_metadata.json"
    metadata_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("must be a JSON object" in reason for reason in report["blocked_reasons"])


def test_partial_or_non_confirmed_metadata_stays_blocked(tmp_path):
    metadata = _complete_metadata()
    metadata.pop("payment_staging_policy")
    metadata["webview_fixture_policy"]["present"] = False
    metadata["qa_review"]["evidence_status"] = "likely"
    metadata_path = tmp_path / "webview_payment_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert "payment_staging_policy is not approved or not present." in report["blocked_reasons"]
    assert "webview_fixture_policy is not approved or not present." in report["blocked_reasons"]
    assert "qa_review does not have confirmed evidence." in report["blocked_reasons"]


def test_invalid_evidence_status_normalizes_to_unknown_and_blocks(tmp_path):
    metadata = _complete_metadata()
    metadata["approved_build"]["evidence_status"] = "verified"
    metadata_path = tmp_path / "webview_payment_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["prerequisites"]["approved_build"]["evidence_status"] == "unknown"
    assert "approved_build does not have confirmed evidence." in report["blocked_reasons"]
    assert all(item["evidence_status"] == "unknown" for item in report["planned_webview_payment_checks"])
    assert all(item["result"] != "pass" for item in report["planned_webview_payment_checks"])


def test_complete_confirmed_metadata_generates_not_run_plan_without_pass(tmp_path):
    metadata_path = tmp_path / "webview_payment_metadata.json"
    metadata_path.write_text(json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    expected_categories = {
        "webview_render_guard",
        "webview_navigation_boundary",
        "webview_session_cookie_boundary",
        "webview_offline_error_state",
        "payment_cancel",
        "payment_failure",
        "payment_pending_resume",
        "payment_duplicate_return",
        "payment_success_return",
        "redacted_web_payment_evidence",
    }
    categories = {item["category"] for item in report["planned_webview_payment_checks"]}

    assert report["overall_status"] == "not_run"
    assert report["evidence_status"] == "unknown"
    assert report["blocked_reasons"] == []
    assert categories == expected_categories
    assert all(item["result"] == "not_run" for item in report["planned_webview_payment_checks"])
    assert all(item["evidence_status"] == "unknown" for item in report["planned_webview_payment_checks"])
    assert report["flow_aliases"][0]["alias"] == "webview-payment-template-001"
    assert '"pass"' not in json.dumps(report)


def test_required_prerequisites_match_task_contract():
    assert REQUIRED_PREREQUISITES == (
        "approved_build",
        "approved_target",
        "approved_config",
        "webview_fixture_policy",
        "payment_staging_policy",
        "synthetic_user_policy",
        "resource_budget",
        "redaction_policy",
        "evidence_storage",
        "cleanup_rollback",
        "security_review",
        "qa_review",
    )


def test_cli_prints_webview_payment_report_to_stdout(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["planned_webview_payment_checks"]


def test_cli_writes_webview_payment_report_to_output_path(tmp_path):
    output_path = tmp_path / "webview_payment_report.json"

    exit_code = main(["--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert report["verification"][0]["classification"] == "PROD_SAFE"
    assert report["verification"][0]["result"] == "not_run"


def test_cli_complete_confirmed_metadata_outputs_not_run(tmp_path, capsys):
    metadata_path = tmp_path / "webview_payment_metadata.json"
    metadata_path.write_text(json.dumps(_complete_metadata()), encoding="utf-8")

    exit_code = main(["--metadata", str(metadata_path)])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "not_run"
    assert report["blocked_reasons"] == []
    assert all(item["result"] == "not_run" for item in report["planned_webview_payment_checks"])


def test_metadata_with_utf8_bom_is_supported(tmp_path):
    metadata_path = tmp_path / "webview_payment_metadata.json"
    metadata_path.write_text("\ufeff" + json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    assert "not valid JSON" not in " ".join(report["blocked_reasons"])
    assert report["overall_status"] == "not_run"
    assert report["prerequisites"]["approved_build"]["present"] is True


def test_metadata_notes_flows_and_artifacts_are_redacted(tmp_path):
    secret_pair = "api_key" + "=" + "abc123"
    private_url = "http" + "s://" + "private" + ".example/path"
    private_email = "user" + "@" + "example" + ".com"
    private_windows_path = "C:" + "\\Users\\qa\\private"
    private_unix_path = "/" + "home/qa/private/log.txt"
    session_pair = "session" + "=" + "secret" + "-value"
    cookie_pair = "cookie" + "=" + "secret" + "-cookie"
    authorization_pair = "authorization: Bearer " + "auth" + "-secret"
    payment_token_pair = "payment" + "_token" + "=" + "pay" + "-secret-token"
    payment_number = ("4" + "111 ") * 3 + "4" + "111"
    long_value = "A" * 40
    metadata = _complete_metadata()
    metadata["approved_build"]["note"] = (
        f"{private_windows_path} {secret_pair} {authorization_pair} {private_url} {private_email} {long_value}"
    )
    metadata["payment_staging_policy"]["note"] = f"{payment_token_pair} card_number={payment_number}"
    metadata["flow_aliases"] = [
        {
            "alias": f"checkout alias {payment_number}",
            "surface_category": "webview_payment",
            "fixture_category": f"staging_fixture {payment_token_pair}",
            "allowed_scope": "plan_only",
            "evidence_status": "verified",
            "notes": f"{session_pair} {private_url}",
        }
    ]
    metadata["artifacts"] = [
        {
            "name": "webview payment raw reference",
            "reference": f"{private_unix_path} {cookie_pair}",
            "evidence_status": "verified",
        }
    ]
    metadata_path = tmp_path / "webview_payment_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    serialized = json.dumps(report)

    assert report["redaction_status"] == "redacted"
    assert "abc123" not in serialized
    assert ("secret" + "-value") not in serialized
    assert ("secret" + "-cookie") not in serialized
    assert ("auth" + "-secret") not in serialized
    assert ("pay" + "-secret-token") not in serialized
    assert ("4" + "111") not in serialized
    assert ("private" + ".example") not in serialized
    assert ("user" + "@" + "example" + ".com") not in serialized
    assert ("C:" + "\\Users\\qa") not in serialized
    assert ("/" + "home/qa") not in serialized
    assert long_value not in serialized
    assert report["flow_aliases"][0]["evidence_status"] == "unknown"
    assert report["artifacts"][0]["evidence_status"] == "unknown"
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_PAYMENT]" in serialized
    assert "[REDACTED_PAYMENT_NUMBER]" in serialized
    assert "[REDACTED_URL]" in serialized
    assert "[REDACTED_EMAIL]" in serialized
    assert "[REDACTED_PATH]" in serialized
    assert "[REDACTED_OPAQUE_VALUE]" in serialized

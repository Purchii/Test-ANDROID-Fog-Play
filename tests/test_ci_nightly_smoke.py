import json

from automation.ci_nightly_smoke.generate_ci_nightly_smoke_report import (
    REQUIRED_PREREQUISITES,
    build_report,
    main,
)


def _complete_metadata():
    return {
        "approved_static_ci_scope": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved static CI scope placeholder for unit test.",
        },
        "approved_schedule_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved schedule policy placeholder for unit test.",
        },
        "repository_safety_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved repository safety policy placeholder for unit test.",
        },
        "resource_budget": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved CI/nightly resource budget placeholder for unit test.",
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
        "artifact_retention_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved artifact retention policy placeholder for unit test.",
        },
        "dependency_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved dependency policy placeholder for unit test.",
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


def test_missing_metadata_generates_blocked_ci_nightly_report():
    report = build_report()

    assert report["task_id"] == "TASK-010"
    assert report["mode"] == "BOUNDED_AUTONOMOUS"
    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["prerequisites"]["approved_static_ci_scope"]["present"] is False
    assert report["prerequisites"]["approved_schedule_policy"]["present"] is False
    assert report["prerequisites"]["repository_safety_policy"]["present"] is False
    assert report["prerequisites"]["security_review"]["present"] is False
    assert report["prerequisites"]["qa_review"]["present"] is False
    assert report["blocked_reasons"]


def test_missing_metadata_path_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "missing_ci_nightly_metadata.json"

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("metadata file was not found" in reason for reason in report["blocked_reasons"])


def test_malformed_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "ci_nightly_metadata.json"
    metadata_path.write_text("{not-json", encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert any("not valid JSON" in reason for reason in report["blocked_reasons"])


def test_non_object_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "ci_nightly_metadata.json"
    metadata_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("must be a JSON object" in reason for reason in report["blocked_reasons"])


def test_partial_or_non_confirmed_metadata_stays_blocked(tmp_path):
    metadata = _complete_metadata()
    metadata.pop("artifact_retention_policy")
    metadata["dependency_policy"]["present"] = False
    metadata["qa_review"]["evidence_status"] = "likely"
    metadata_path = tmp_path / "ci_nightly_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert "artifact_retention_policy is not approved or not present." in report["blocked_reasons"]
    assert "dependency_policy is not approved or not present." in report["blocked_reasons"]
    assert "qa_review does not have confirmed evidence." in report["blocked_reasons"]


def test_invalid_evidence_status_normalizes_to_unknown_and_blocks(tmp_path):
    metadata = _complete_metadata()
    metadata["approved_static_ci_scope"]["evidence_status"] = "verified"
    metadata_path = tmp_path / "ci_nightly_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["prerequisites"]["approved_static_ci_scope"]["evidence_status"] == "unknown"
    assert "approved_static_ci_scope does not have confirmed evidence." in report["blocked_reasons"]
    assert all(item["evidence_status"] == "unknown" for item in report["planned_ci_nightly_checks"])
    assert all(item["result"] != "pass" for item in report["planned_ci_nightly_checks"])


def test_complete_confirmed_metadata_generates_not_run_plan_without_pass(tmp_path):
    metadata_path = tmp_path / "ci_nightly_metadata.json"
    metadata_path.write_text(json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    expected_categories = {
        "repository_hygiene",
        "python_unit_tests",
        "python_compileall",
        "release_gate_dry_run",
        "runtime_blocked_report_dry_run",
        "network_offline_plan_dry_run",
        "webview_payment_plan_dry_run",
        "compatibility_matrix_plan_dry_run",
        "public_safety_scan",
        "redacted_summary_publish",
    }
    categories = {item["category"] for item in report["planned_ci_nightly_checks"]}

    assert report["overall_status"] == "not_run"
    assert report["evidence_status"] == "unknown"
    assert report["blocked_reasons"] == []
    assert categories == expected_categories
    assert all(item["result"] == "not_run" for item in report["planned_ci_nightly_checks"])
    assert all(item["evidence_status"] == "unknown" for item in report["planned_ci_nightly_checks"])
    assert report["ci_jobs"][0]["alias"] == "ci-nightly-template-001"
    assert '"pass"' not in json.dumps(report)


def test_required_prerequisites_match_task_contract():
    assert REQUIRED_PREREQUISITES == (
        "approved_static_ci_scope",
        "approved_schedule_policy",
        "repository_safety_policy",
        "resource_budget",
        "redaction_policy",
        "evidence_storage",
        "artifact_retention_policy",
        "dependency_policy",
        "security_review",
        "qa_review",
    )


def test_cli_prints_ci_nightly_report_to_stdout(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["planned_ci_nightly_checks"]


def test_cli_writes_ci_nightly_report_to_output_path(tmp_path):
    output_path = tmp_path / "ci_nightly_report.json"

    exit_code = main(["--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert report["verification"][0]["classification"] == "PROD_SAFE"
    assert report["verification"][0]["result"] == "not_run"


def test_cli_complete_confirmed_metadata_outputs_not_run(tmp_path, capsys):
    metadata_path = tmp_path / "ci_nightly_metadata.json"
    metadata_path.write_text(json.dumps(_complete_metadata()), encoding="utf-8")

    exit_code = main(["--metadata", str(metadata_path)])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "not_run"
    assert report["blocked_reasons"] == []
    assert all(item["result"] == "not_run" for item in report["planned_ci_nightly_checks"])


def test_metadata_with_utf8_bom_is_supported(tmp_path):
    metadata_path = tmp_path / "ci_nightly_metadata.json"
    metadata_path.write_text("\ufeff" + json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    assert "not valid JSON" not in " ".join(report["blocked_reasons"])
    assert report["overall_status"] == "not_run"
    assert report["prerequisites"]["approved_static_ci_scope"]["present"] is True


def test_metadata_notes_ci_jobs_and_artifacts_are_redacted(tmp_path):
    secret_pair = "api_key" + "=" + "abc123"
    private_url = "http" + "s://" + "private.example/path"
    private_email = "user" + "@" + "example.com"
    private_windows_path = "C:" + "\\Users\\qa\\private"
    private_unix_path = "/" + "home/qa/private/log.txt"
    session_pair = "session" + "=" + "secret-value"
    cookie_pair = "cookie" + "=" + "secret-cookie"
    authorization_pair = "authorization: Bearer " + "auth-secret"
    ci_token_pair = "GITHUB_TOKEN" + "=" + "ghs_secret_ci_token"
    runner_token_pair = "runner_token" + "=" + "runner-secret"
    long_value = "A" * 40
    metadata = _complete_metadata()
    metadata["approved_static_ci_scope"]["note"] = (
        f"{private_windows_path} {secret_pair} {authorization_pair} {private_url} {private_email} {long_value}"
    )
    metadata["approved_schedule_policy"]["note"] = f"{ci_token_pair} {runner_token_pair}"
    metadata["ci_jobs"] = [
        {
            "alias": f"nightly public alias {ci_token_pair}",
            "job_category": f"python_unit_tests {runner_token_pair}",
            "trigger_category": "nightly_timer",
            "runner_category": "public_safe_runner",
            "evidence_status": "verified",
            "notes": f"{session_pair} {private_url}",
        }
    ]
    metadata["artifacts"] = [
        {
            "name": "ci raw reference",
            "reference": f"{private_unix_path} {cookie_pair}",
            "evidence_status": "verified",
        }
    ]
    metadata_path = tmp_path / "ci_nightly_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    serialized = json.dumps(report)

    assert report["redaction_status"] == "redacted"
    assert "abc123" not in serialized
    assert "secret-value" not in serialized
    assert "secret-cookie" not in serialized
    assert "auth-secret" not in serialized
    assert "ghs_secret_ci_token" not in serialized
    assert "runner-secret" not in serialized
    assert "private.example" not in serialized
    assert "user@example.com" not in serialized
    assert ("C:" + "\\Users\\qa") not in serialized
    assert ("/" + "home/qa") not in serialized
    assert long_value not in serialized
    assert report["ci_jobs"][0]["evidence_status"] == "unknown"
    assert report["artifacts"][0]["evidence_status"] == "unknown"
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_CI_TOKEN]" in serialized
    assert "[REDACTED_URL]" in serialized
    assert "[REDACTED_EMAIL]" in serialized
    assert "[REDACTED_PATH]" in serialized
    assert "[REDACTED_OPAQUE_VALUE]" in serialized

import json

from automation.reporting.generate_release_gate_report import DEFAULT_RELEASE_GATES, build_report, main


def _confirmed_prerequisites():
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
    }


def _confirmed_pass_gates():
    return {
        gate["name"]: {
            "status": "pass",
            "evidence_status": "confirmed",
            "note": f"Confirmed public-safe {gate['name']} gate metadata.",
            "artifacts": [
                {
                    "name": f"{gate['name']}-summary",
                    "reference": f"public-safe/{gate['name']}.json",
                    "evidence_status": "confirmed",
                }
            ],
        }
        for gate in DEFAULT_RELEASE_GATES
    }


def test_missing_metadata_generates_blocked_release_gate_report():
    report = build_report()

    assert report["task_id"] == "TASK-003"
    assert report["overall_status"] == "blocked"
    assert report["release_decision"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["blocked_reasons"]
    assert {gate["name"] for gate in report["release_gates"]} >= {
        "prerequisites",
        "runtime_startup",
        "first_focus",
        "exported_component_guards",
        "auth_session_guard",
        "redacted_evidence",
    }


def test_network_offline_recovery_gate_is_runtime_dependent_r1():
    gate = next(gate for gate in DEFAULT_RELEASE_GATES if gate["name"] == "network_offline_recovery")

    assert gate["id"] == "RG-007"
    assert gate["risk_level"] == "R1"
    assert gate["runtime_dependent"] is True


def test_compatibility_device_matrix_gate_is_runtime_dependent_r1():
    gate = next(gate for gate in DEFAULT_RELEASE_GATES if gate["name"] == "compatibility_device_matrix")

    assert gate["id"] == "RG-008"
    assert gate["risk_level"] == "R1"
    assert gate["runtime_dependent"] is True


def test_webview_payment_safe_boundary_gate_is_runtime_dependent_r1():
    gate = next(gate for gate in DEFAULT_RELEASE_GATES if gate["name"] == "webview_payment_safe_boundary")

    assert gate["id"] == "RG-009"
    assert gate["risk_level"] == "R1"
    assert gate["runtime_dependent"] is True


def test_complete_confirmed_pass_metadata_allows_release_pass(tmp_path):
    metadata = {
        "evidence_status": "confirmed",
        "prerequisites": _confirmed_prerequisites(),
        "release_gates": _confirmed_pass_gates(),
        "review": {
            "qa_reviewer_a": "approved",
            "qa_reviewer_b": "approved",
            "security_prod_safety_reviewer": "approved",
            "docs_scribe": "approved",
        },
    }
    metadata_path = tmp_path / "release_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "pass"
    assert report["release_decision"] == "pass"
    assert report["evidence_status"] == "confirmed"
    assert report["blocked_reasons"] == []
    assert all(gate["status"] == "pass" for gate in report["release_gates"])
    assert all(gate["evidence_status"] == "confirmed" for gate in report["release_gates"])


def test_complete_not_run_metadata_does_not_fake_runtime_pass(tmp_path):
    metadata = {
        "prerequisites": _confirmed_prerequisites(),
        "release_gates": {
            name: {
                "status": "not_run",
                "evidence_status": "unknown",
                "note": "Runtime evidence intentionally not provided.",
            }
            for name in _confirmed_pass_gates()
        },
    }
    metadata_path = tmp_path / "release_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["release_decision"] == "blocked"
    assert any(gate["name"] == "runtime_startup" and gate["status"] == "not_run" for gate in report["release_gates"])
    assert any("runtime_startup gate is not_run" in reason for reason in report["blocked_reasons"])
    assert not any(gate["status"] == "pass" for gate in report["release_gates"])


def test_malformed_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "release_metadata.json"
    metadata_path.write_text("{not-json", encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("not valid JSON" in reason for reason in report["blocked_reasons"])


def test_non_object_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "release_metadata.json"
    metadata_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("must be a JSON object" in reason for reason in report["blocked_reasons"])


def test_invalid_evidence_status_normalizes_to_unknown_and_blocks_pass(tmp_path):
    gates = _confirmed_pass_gates()
    gates["runtime_startup"]["evidence_status"] = "verified"
    metadata = {
        "prerequisites": _confirmed_prerequisites(),
        "release_gates": gates,
    }
    metadata_path = tmp_path / "release_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    runtime_gate = next(gate for gate in report["release_gates"] if gate["name"] == "runtime_startup")

    assert runtime_gate["evidence_status"] == "unknown"
    assert runtime_gate["status"] == "blocked"
    assert report["release_decision"] == "blocked"
    assert any("runtime_startup requested pass without confirmed evidence" in reason for reason in report["blocked_reasons"])


def test_notes_and_artifact_references_are_redacted(tmp_path):
    secret_pair = "token" + "=" + "abc123"
    private_url = "http" + "s://" + "private.example/path"
    private_email = "user" + "@" + "example.com"
    private_windows_path = "C:" + "\\Users\\qa\\private"
    private_unix_path = "/" + "home/qa/private/log.txt"
    session_pair = "session" + "=" + "secret-value"
    cookie_pair = "cookie" + "=" + "secret"
    long_value = "A" * 40
    gates = _confirmed_pass_gates()
    gates["runtime_startup"]["note"] = f"{private_windows_path} {secret_pair} {private_url} {private_email} {long_value}"
    gates["runtime_startup"]["artifacts"] = [
        {
            "name": "startup raw reference",
            "reference": f"{private_unix_path} {session_pair}",
            "evidence_status": "confirmed",
        }
    ]
    metadata = {
        "prerequisites": _confirmed_prerequisites(),
        "release_gates": gates,
        "artifacts": [
            {
                "name": "external report",
                "reference": f"{private_url} {cookie_pair}",
                "evidence_status": "confirmed",
            }
        ],
    }
    metadata_path = tmp_path / "release_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    serialized = json.dumps(report)

    assert report["redaction_status"] == "redacted"
    assert "abc123" not in serialized
    assert "private.example" not in serialized
    assert "user@example.com" not in serialized
    assert ("C:" + "\\Users\\qa") not in serialized
    assert ("/" + "home/qa") not in serialized
    assert long_value not in serialized
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_PATH]" in serialized
    assert "[REDACTED_URL]" in serialized
    assert "[REDACTED_EMAIL]" in serialized
    assert "[REDACTED_OPAQUE_VALUE]" in serialized


def test_metadata_derived_risks_unknowns_verification_and_review_are_redacted(tmp_path):
    metadata = {
        "prerequisites": _confirmed_prerequisites(),
        "release_gates": _confirmed_pass_gates(),
        "risks": [
            {
                "id": "token=abc123",
                "level": "High",
                "evidence_status": "likely",
                "summary": {"nested": "session=secret-value"},
            }
        ],
        "unknowns": [
            {
                "id": "https://private.example/path",
                "evidence_status": "unknown",
                "question": "Contact user@example.com",
            }
        ],
        "verification": [
            {
                "name": "C:\\Users\\qa\\private\\report.txt",
                "evidence_status": "confirmed",
                "note": "api_key=abc123",
            }
        ],
        "review": {
            "qa_reviewer_a": "approved session=secret-value",
            "qa_reviewer_b": "approved",
            "security_prod_safety_reviewer": "approved",
            "docs_scribe": "approved",
        },
    }
    metadata_path = tmp_path / "release_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    serialized = json.dumps(report)

    assert report["overall_status"] == "pass"
    assert report["redaction_status"] == "redacted"
    assert "abc123" not in serialized
    assert "secret-value" not in serialized
    assert "private.example" not in serialized
    assert "user@example.com" not in serialized
    assert "C:\\Users\\qa" not in serialized
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_URL]" in serialized
    assert "[REDACTED_EMAIL]" in serialized
    assert "[REDACTED_PATH]" in serialized


def test_cli_prints_release_report_to_stdout(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["release_gates"]


def test_cli_writes_release_report_to_output_path(tmp_path):
    output_path = tmp_path / "release_gate_report.json"

    exit_code = main(["--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert report["verification"][0]["classification"] == "PROD_SAFE"

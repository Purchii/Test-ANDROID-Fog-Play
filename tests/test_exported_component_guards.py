import json

from automation.exported_component_guards.generate_guard_report import build_report, main


def test_missing_metadata_generates_blocked_guard_report():
    report = build_report()

    assert report["task_id"] == "TASK-002"
    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["prerequisites"]["approved_build"]["present"] is False
    assert report["prerequisites"]["approved_target"]["present"] is False
    assert report["prerequisites"]["approved_config"]["present"] is False
    assert report["prerequisites"]["approved_guard_scope"]["present"] is False
    assert report["blocked_reasons"]


def test_complete_metadata_generates_not_run_plan_without_pass(tmp_path):
    metadata = {
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
        "approved_guard_scope": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved category-level guard scope placeholder for unit test.",
        },
    }
    metadata_path = tmp_path / "guard_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "not_run"
    assert report["evidence_status"] == "unknown"
    assert report["blocked_reasons"] == []
    assert all(case["result"] == "not_run" for case in report["guard_cases"])
    assert all(case["runtime_execution"] == "blocked_until_approved_task" for case in report["guard_cases"])
    assert "runtime guard execution belongs to a future approved task" in " ".join(report["execution_notes"])
    assert '"pass"' not in json.dumps(report)


def test_cli_writes_guard_report(tmp_path):
    output_path = tmp_path / "guard_report.json"

    exit_code = main(["--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert report["verification"][0]["classification"] == "PROD_SAFE"
    assert report["verification"][0]["result"] == "not_run"


def test_cli_prints_guard_report_to_stdout(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["guard_cases"]
    assert all(case["result"] == "not_run" for case in report["guard_cases"])


def test_guard_metadata_notes_are_redacted(tmp_path):
    secret_pair = "api_key" + "=" + "abc123"
    private_url = "http" + "s://" + "private.example/path"
    private_email = "user" + "@" + "example.com"
    metadata = {
        "approved_build": {
            "present": True,
            "evidence_status": "confirmed",
            "note": f"path=C:\\Users\\qa\\private {secret_pair} {private_url} {private_email}",
        },
        "approved_target": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Public-safe target note.",
        },
        "approved_config": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Public-safe config note.",
        },
        "approved_guard_scope": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Public-safe guard scope note.",
        },
    }
    metadata_path = tmp_path / "guard_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    notes = " ".join(value["note"] for value in report["prerequisites"].values())

    assert report["redaction_status"] == "redacted"
    assert "abc123" not in notes
    assert "private.example" not in notes
    assert "user@example.com" not in notes
    assert "C:\\Users\\qa" not in notes
    assert "[REDACTED_SECRET]" in notes


def test_malformed_guard_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "guard_metadata.json"
    metadata_path.write_text("{not-json", encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("not valid JSON" in reason for reason in report["blocked_reasons"])


def test_invalid_evidence_status_normalizes_to_unknown_without_runtime_pass(tmp_path):
    metadata = {
        "approved_build": {
            "present": True,
            "evidence_status": "verified",
            "note": "Public-safe build note.",
        },
        "approved_target": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Public-safe target note.",
        },
        "approved_config": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Public-safe config note.",
        },
        "approved_guard_scope": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Public-safe guard scope note.",
        },
    }
    metadata_path = tmp_path / "guard_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "not_run"
    assert report["prerequisites"]["approved_build"]["evidence_status"] == "unknown"
    assert all(case["result"] != "pass" for case in report["guard_cases"])
    assert all(item["result"] != "pass" for item in report["verification"])


def test_guard_metadata_with_utf8_bom_is_supported(tmp_path):
    metadata = {
        "approved_guard_scope": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Public-safe guard scope note.",
        }
    }
    metadata_path = tmp_path / "guard_metadata.json"
    metadata_path.write_text("\ufeff" + json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert "not valid JSON" not in " ".join(report["blocked_reasons"])
    assert report["prerequisites"]["approved_guard_scope"]["present"] is True

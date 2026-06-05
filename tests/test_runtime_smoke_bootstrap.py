import json

from automation.runtime_smoke_bootstrap.generate_blocked_report import build_report, main


def test_missing_metadata_generates_blocked_report():
    report = build_report()

    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["prerequisites"]["approved_build"]["present"] is False
    assert report["prerequisites"]["approved_target"]["present"] is False
    assert report["prerequisites"]["approved_config"]["present"] is False
    assert report["blocked_reasons"]


def test_complete_metadata_still_fails_closed_for_task_001(tmp_path):
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
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert "never executes runtime checks" in " ".join(report["blocked_reasons"])


def test_cli_writes_blocked_report(tmp_path):
    output_path = tmp_path / "blocked_report.json"

    exit_code = main(["--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert report["verification"][0]["classification"] == "PROD_SAFE"


def test_metadata_notes_are_redacted(tmp_path):
    secret_pair = "token" + "=" + "abc123"
    private_url = "http" + "s://" + "private.example/path"
    private_email = "user" + "@" + "example.com"
    session_pair = "session" + "=" + "secret-value"
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
            "note": session_pair,
        },
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)
    notes = " ".join(value["note"] for value in report["prerequisites"].values())

    assert report["redaction_status"] == "redacted"
    assert "abc123" not in notes
    assert "private.example" not in notes
    assert "user@example.com" not in notes
    assert "C:\\Users\\qa" not in notes
    assert "[REDACTED_SECRET]" in notes


def test_metadata_with_utf8_bom_is_supported(tmp_path):
    metadata = {
        "approved_build": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Public-safe build note.",
        }
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text("\ufeff" + json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert "not valid JSON" not in " ".join(report["blocked_reasons"])
    assert report["prerequisites"]["approved_build"]["present"] is True

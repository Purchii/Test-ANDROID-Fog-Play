import json

from automation.navigation_transition_map.generate_navigation_transition_report import (
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
        "navigation_scope": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved navigation scope placeholder for unit test.",
        },
        "screen_alias_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved public-safe screen alias policy placeholder for unit test.",
        },
        "input_event_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved D-pad and Back input event policy placeholder for unit test.",
        },
        "fixture_policy": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved fixture policy placeholder for unit test.",
        },
        "resource_budget": {
            "present": True,
            "evidence_status": "confirmed",
            "note": "Approved transition resource budget placeholder for unit test.",
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


def test_missing_metadata_generates_blocked_navigation_transition_report():
    report = build_report()

    assert report["task_id"] == "TASK-011"
    assert report["mode"] == "BOUNDED_AUTONOMOUS"
    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert report["production_safety_classification"] == "PROD_SAFE"
    assert report["prerequisites"]["approved_build"]["present"] is False
    assert report["prerequisites"]["approved_target"]["present"] is False
    assert report["prerequisites"]["navigation_scope"]["present"] is False
    assert report["prerequisites"]["screen_alias_policy"]["present"] is False
    assert report["prerequisites"]["input_event_policy"]["present"] is False
    assert report["prerequisites"]["resource_budget"]["present"] is False
    assert report["prerequisites"]["security_review"]["present"] is False
    assert report["prerequisites"]["qa_review"]["present"] is False
    assert report["blocked_reasons"]


def test_missing_metadata_path_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "missing_navigation_metadata.json"

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("metadata file was not found" in reason for reason in report["blocked_reasons"])


def test_malformed_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "navigation_metadata.json"
    metadata_path.write_text("{not-json", encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["evidence_status"] == "unknown"
    assert any("not valid JSON" in reason for reason in report["blocked_reasons"])


def test_non_object_metadata_generates_blocked_report(tmp_path):
    metadata_path = tmp_path / "navigation_metadata.json"
    metadata_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert any("must be a JSON object" in reason for reason in report["blocked_reasons"])


def test_partial_or_non_confirmed_metadata_stays_blocked(tmp_path):
    metadata = _complete_metadata()
    metadata.pop("navigation_scope")
    metadata["screen_alias_policy"]["present"] = False
    metadata["qa_review"]["evidence_status"] = "likely"
    metadata_path = tmp_path / "navigation_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert "navigation_scope is not approved or not present." in report["blocked_reasons"]
    assert "screen_alias_policy is not approved or not present." in report["blocked_reasons"]
    assert "qa_review does not have confirmed evidence." in report["blocked_reasons"]


def test_invalid_evidence_status_normalizes_to_unknown_and_blocks(tmp_path):
    metadata = _complete_metadata()
    metadata["approved_build"]["evidence_status"] = "verified"
    metadata_path = tmp_path / "navigation_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    report = build_report(metadata_path)

    assert report["overall_status"] == "blocked"
    assert report["prerequisites"]["approved_build"]["evidence_status"] == "unknown"
    assert "approved_build does not have confirmed evidence." in report["blocked_reasons"]
    assert all(item["evidence_status"] == "unknown" for item in report["planned_transitions"])
    assert all(item["result"] != "pass" for item in report["planned_transitions"])


def test_complete_confirmed_metadata_generates_not_run_plan_without_pass(tmp_path):
    metadata_path = tmp_path / "navigation_metadata.json"
    metadata_path.write_text(json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    expected_categories = {
        "startup_to_first_screen",
        "home_to_catalog",
        "catalog_to_detail",
        "detail_to_playback",
        "playback_controls",
        "back_navigation",
        "home_resume",
        "auth_required_boundary",
        "search_navigation",
        "webview_or_hybrid_boundary",
        "error_empty_state",
        "redacted_transition_evidence",
    }
    expected_guidance_categories = {
        "efficient_intuitive_entry",
        "axis_based_traversal",
        "four_way_dpad_select",
        "select_semantics",
        "clear_focus_path",
        "predictable_back_no_infinite_loop",
        "home_semantics",
        "predictable_navigation_boundary",
        "intuitive_recovery",
        "public_safe_evidence",
    }
    categories = {item["category"] for item in report["planned_transitions"]}
    guidance_categories = {item["design_guideline_category"] for item in report["planned_transitions"]}

    assert report["overall_status"] == "not_run"
    assert report["evidence_status"] == "unknown"
    assert report["blocked_reasons"] == []
    assert categories == expected_categories
    assert guidance_categories == expected_guidance_categories
    assert report["design_guidance_references"]
    assert all(
        item["applies_as"] == "public_design_guideline_reference_only"
        for item in report["design_guidance_references"]
    )
    assert all(item["result"] == "not_run" for item in report["planned_transitions"])
    assert all(item["evidence_status"] == "unknown" for item in report["planned_transitions"])
    assert report["screen_aliases"][0]["alias"] == "screen-template-001"
    assert report["transition_edges"][0]["alias"] == "transition-template-001"
    assert '"pass"' not in json.dumps(report)


def test_required_prerequisites_match_task_contract():
    assert REQUIRED_PREREQUISITES == (
        "approved_build",
        "approved_target",
        "approved_config",
        "navigation_scope",
        "screen_alias_policy",
        "input_event_policy",
        "fixture_policy",
        "resource_budget",
        "redaction_policy",
        "evidence_storage",
        "cleanup_rollback",
        "security_review",
        "qa_review",
    )


def test_cli_prints_navigation_transition_report_to_stdout(capsys):
    exit_code = main([])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "blocked"
    assert report["planned_transitions"]


def test_cli_writes_navigation_transition_report_to_output_path(tmp_path):
    output_path = tmp_path / "navigation_report.json"

    exit_code = main(["--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "blocked"
    assert report["verification"][0]["classification"] == "PROD_SAFE"
    assert report["verification"][0]["result"] == "not_run"


def test_cli_complete_confirmed_metadata_outputs_not_run(tmp_path, capsys):
    metadata_path = tmp_path / "navigation_metadata.json"
    metadata_path.write_text(json.dumps(_complete_metadata()), encoding="utf-8")

    exit_code = main(["--metadata", str(metadata_path)])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall_status"] == "not_run"
    assert report["blocked_reasons"] == []
    assert all(item["result"] == "not_run" for item in report["planned_transitions"])


def test_metadata_with_utf8_bom_is_supported(tmp_path):
    metadata_path = tmp_path / "navigation_metadata.json"
    metadata_path.write_text("\ufeff" + json.dumps(_complete_metadata()), encoding="utf-8")

    report = build_report(metadata_path)

    assert "not valid JSON" not in " ".join(report["blocked_reasons"])
    assert report["overall_status"] == "not_run"
    assert report["prerequisites"]["approved_build"]["present"] is True


def test_metadata_notes_aliases_edges_and_artifacts_are_redacted(tmp_path):
    secret_pair = "api_key" + "=" + "abc123"
    private_url = "http" + "s://" + "private.example/path"
    private_email = "user" + "@" + "example.com"
    private_windows_path = "C:" + "\\Users\\qa\\private"
    private_unix_path = "/" + "home/qa/private/log.txt"
    session_pair = "session" + "=" + "secret-value"
    cookie_pair = "cookie" + "=" + "secret-cookie"
    authorization_pair = "authorization: Bearer " + "auth-secret"
    long_value = "A" * 40
    metadata = _complete_metadata()
    metadata["approved_build"]["note"] = (
        f"{private_windows_path} {secret_pair} {authorization_pair} {private_url} {private_email} {long_value}"
    )
    metadata["screen_aliases"] = [
        {
            "alias": f"home_alias {private_url}",
            "screen_category": "home",
            "entry_category": "startup",
            "exit_category": "catalog",
            "evidence_status": "verified",
            "notes": f"{session_pair} {private_email}",
        }
    ]
    metadata["transition_edges"] = [
        {
            "alias": f"home_to_catalog {cookie_pair}",
            "from_screen_alias": "home_alias",
            "to_screen_alias": "catalog_alias",
            "trigger_category": f"d_pad_select {authorization_pair}",
            "risk_level": "R1",
            "evidence_status": "verified",
            "notes": f"{secret_pair} {long_value}",
        }
    ]
    metadata["artifacts"] = [
        {
            "name": "navigation raw reference",
            "reference": f"{private_unix_path} {cookie_pair}",
            "evidence_status": "verified",
        }
    ]
    metadata_path = tmp_path / "navigation_metadata.json"
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
    assert ("C:" + "\\Users\\qa") not in serialized
    assert ("/" + "home/qa") not in serialized
    assert long_value not in serialized
    assert report["screen_aliases"][0]["evidence_status"] == "unknown"
    assert report["transition_edges"][0]["evidence_status"] == "unknown"
    assert report["artifacts"][0]["evidence_status"] == "unknown"
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_URL]" in serialized
    assert "[REDACTED_EMAIL]" in serialized
    assert "[REDACTED_PATH]" in serialized
    assert "[REDACTED_OPAQUE_VALUE]" in serialized

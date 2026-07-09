import csv
import json

from automation.api_layer_contract.validate_task028_api_layer_contract import build_report as build_task028_report
from automation.api_layer_contract.validate_task029_rest_schema_fixture_contracts import build_report as build_task029_report
from automation.api_layer_contract.validate_task030_rest_negative_cache_sequences import build_report as build_task030_report
from automation.api_layer_contract.validate_task031_stomp_protocol_contracts import build_report as build_task031_report
from automation.api_layer_contract.validate_task032_datachannel_gamepad_contracts import (
    build_report,
    main,
    validate_public_report,
)
from automation.api_layer_contract.validate_task036_api_layer_exhaustive_coverage import build_report as build_task036_report


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_pack(tmp_path):
    root = tmp_path / "api_pack"
    (root / "docs").mkdir(parents=True)
    (root / "specs").mkdir()
    (root / "fixtures").mkdir()
    (root / "schemas").mkdir()
    (root / "templates").mkdir()
    (root / "VALIDATION_RESULT.txt").write_text("validation=pass\n", encoding="utf-8")
    (root / "templates" / "deferred_runtime_lane.md").write_text("deferred\n", encoding="utf-8")
    (root / "specs" / "api_inventory.yaml").write_text(
        "\n".join(
            [
                "items:",
                "  - id: REST_CONFIG_GET",
                "    type: rest",
                "  - id: REST_AUTH_REFRESH",
                "    type: rest",
                "  - id: REST_SEQUENCE_ITEM",
                "    type: rest",
                "  - id: WS_SIG_OFFER_IN",
                "    type: stomp_signaling_message",
                "  - id: DEVICE_STOMP_PAIRING",
                "    type: device_stomp_message",
                "  - id: DC_PING_MESSAGE",
                "    type: datachannel_message",
                "  - id: DC_BAD_FIELDS",
                "    type: datachannel_message",
                "  - id: GAMEPAD_MAPPING_UNKNOWN",
                "    type: datachannel_message",
                "  - id: RUNTIME_OPTIONAL_ONE",
                "    type: runtime_optional",
                "  - id: RUNTIME_OPTIONAL_TWO",
                "    type: runtime_optional",
                "  - id: RUNTIME_OPTIONAL_THREE",
                "    type: runtime_optional",
                "  - id: RUNTIME_OPTIONAL_FOUR",
                "    type: runtime_optional",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(root / "fixtures" / "rest" / "rest_config_get__ok.json", {"enabled": True})
    _write_json(root / "fixtures" / "rest" / "rest_config_get__bad.json", {"error": {"code": "invalid"}})
    _write_json(root / "fixtures" / "rest" / "rest_auth_refresh__401.json", {"error": {"code": "auth"}})
    _write_json(root / "fixtures" / "rest" / "rest_config_get__500.json", {"error": {"code": "server"}})
    _write_json(root / "fixtures" / "sequences" / "rest_config_cache.sequence.json", [{"state": "miss"}, {"state": "hit"}])
    _write_json(root / "fixtures" / "stomp_signaling" / "offer__ok.json", {"message_alias": "offer"})
    _write_json(root / "fixtures" / "stomp_device" / "pairing__ok.json", {"message_alias": "pairing"})
    _write_json(root / "fixtures" / "datachannel" / "ping__ok.json", {"message_alias": "ping"})
    _write_json(root / "fixtures" / "datachannel" / "bad_fields.json", {"message_alias": "bad-fields"})
    _write_json(root / "fixtures" / "gamepad" / "mapping_unknown.json", {"message_alias": "mapping-unknown"})
    _write_json(
        root / "schemas" / "rest" / "client_config_response.schema.json",
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "ClientConfig", "type": "object"},
    )
    _write_json(
        root / "schemas" / "protocol" / "datachannel_message.schema.json",
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "DataChannel", "type": "object"},
    )

    rows = [
        _row("TVAPI-REST_CONFIG_GET-POS-001", "config", "rest", "REST_CONFIG_GET", "positive_schema", "fixture_schema_test", "fixtures/rest/rest_config_get__ok.json"),
        _row("TVAPI-REST_CONFIG_GET-NEG-001", "config", "rest", "REST_CONFIG_GET", "negative_malformed_json", "fixture_schema_negative_test", "fixtures/rest/rest_config_get__bad.json"),
        _row("TVAPI-REST_AUTH_REFRESH-NEG-AUTH", "auth", "rest", "REST_AUTH_REFRESH", "negative_auth", "mock_http_test", "fixtures/rest/rest_auth_refresh__401.json", "P0"),
        _row("TVAPI-REST_CONFIG_GET-SERVER-ERROR", "config", "rest", "REST_CONFIG_GET", "negative_server_error", "mock_http_test", "fixtures/rest/rest_config_get__500.json"),
        _row("TVAPI-REST_CONFIG_GET-CACHE", "config", "state_machine_sequence", "REST_SEQUENCE_ITEM", "cache_behavior", "mock_http_sequence_test", "fixtures/sequences/rest_config_cache.sequence.json"),
        _row("TVAPI-WS_SIG_OFFER_IN-POS-001", "stomp_signaling", "protocol", "WS_SIG_OFFER_IN", "positive_protocol_schema", "protocol_fixture_test", "fixtures/stomp_signaling/offer__ok.json", "P0"),
        _row("TVAPI-DEVICE_STOMP_PAIRING-POS-001", "inter_device_communication", "protocol", "DEVICE_STOMP_PAIRING", "positive_protocol_schema", "protocol_fixture_test", "fixtures/stomp_device/pairing__ok.json"),
        _row("TVAPI-DC_PING_MESSAGE-POS-001", "stream_control", "protocol", "DC_PING_MESSAGE", "positive_protocol_schema", "protocol_fixture_test", "fixtures/datachannel/ping__ok.json"),
        _row("TVAPI-DC_BAD_FIELDS-NEG-001", "stream_control", "protocol", "DC_BAD_FIELDS", "negative_invalid_fields", "protocol_negative_test", "fixtures/datachannel/bad_fields.json"),
        _row("TVAPI-GAMEPAD_MAPPING_UNKNOWN-POS-001", "gamepad", "protocol", "GAMEPAD_MAPPING_UNKNOWN", "positive_protocol_schema", "protocol_fixture_test", "fixtures/gamepad/mapping_unknown.json"),
    ]
    for index in range(1, 5):
        rows.append(
            _row(
                f"TVAPI-RUNTIME-OPTIONAL-{index}",
                "runtime",
                "runtime_optional",
                f"RUNTIME_OPTIONAL_{index}",
                "explicit_deferred",
                "deferred_with_reason",
                "templates/deferred_runtime_lane.md",
                "P2",
                "deferred_not_blocking_this_run",
            )
        )
    with (root / "specs" / "test_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return root


def _row(test_id, domain, layer, item, test_type, target, fixture, priority="P1", status="ready_or_fixture_only"):
    return {
        "test_id": test_id,
        "domain": domain,
        "layer": layer,
        "item": item,
        "test_type": test_type,
        "priority": priority,
        "title": "contract fixture validates offline",
        "automation_target": target,
        "fixture_or_sequence": fixture,
        "parallelization": "independent_api_layer",
        "status": status,
    }


def _write_source_summaries(tmp_path, pack_root):
    task028_summary = build_task028_report(pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    task028_path = tmp_path / "task028.summary.json"
    task028_path.write_text(json.dumps(task028_summary), encoding="utf-8")
    task036_summary = build_task036_report(task028_path, pack_root=pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    task036_path = tmp_path / "task036.summary.json"
    task036_path.write_text(json.dumps(task036_summary), encoding="utf-8")
    task029_summary = build_task029_report(task028_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    task029_path = tmp_path / "task029.summary.json"
    task029_path.write_text(json.dumps(task029_summary), encoding="utf-8")
    task030_summary = build_task030_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    task030_path = tmp_path / "task030.summary.json"
    task030_path.write_text(json.dumps(task030_summary), encoding="utf-8")
    task031_summary = build_task031_report(task028_path, task030_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    task031_path = tmp_path / "task031.summary.json"
    task031_path.write_text(json.dumps(task031_summary), encoding="utf-8")
    return task028_path, task031_path, task036_path


def test_task032_passes_with_synthetic_pack_and_counts_datachannel_gamepad_rows(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "pass"
    assert report["pack_contract"]["task032_matrix_rows"] == 3
    assert report["pack_contract"]["datachannel_rows"] == 2
    assert report["pack_contract"]["gamepad_rows"] == 1
    assert report["pack_contract"]["protocol_negative_rows"] == 1
    assert report["live_api_execution_status"] == "not_run"
    assert report["offline_execution_boundary"]["webrtc_datachannel_connections"] == "not_run"
    assert validate_public_report(report) == []


def test_task032_missing_pack_is_controlled_partial_blocker(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)

    report = build_report(task028_path, task031_path, task036_path, tmp_path / "missing", generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "partial_blocked"
    assert report["pack_contract"]["status"] == "blocked_missing_local_quarantine_pack"
    assert report["blocked_reasons"] == ["blocked_missing_local_quarantine_pack"]
    assert validate_public_report(report) == []


def test_task032_blocks_missing_datachannel_or_gamepad_rows(tmp_path):
    pack_root = _make_pack(tmp_path)
    matrix_path = pack_root / "specs" / "test_matrix.csv"
    rows = list(csv.DictReader(matrix_path.open(encoding="utf-8", newline="")))
    rows = [row for row in rows if not row["fixture_or_sequence"].startswith("fixtures/gamepad/")]
    with matrix_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task032_gamepad_rows_missing" in report["blocked_reasons"]


def test_task032_blocks_malformed_protocol_fixture_json(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    (pack_root / "fixtures" / "datachannel" / "ping__ok.json").write_text("{bad", encoding="utf-8")

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task032_fixture_json_malformed" in report["blocked_reasons"]


def test_task032_blocks_invalid_protocol_fixture_shape(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    _write_json(pack_root / "fixtures" / "gamepad" / "mapping_unknown.json", [])

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task032_protocol_fixture_shape_invalid" in report["blocked_reasons"]


def test_task032_blocks_unapproved_fixture_reference_group_even_when_summaries_match(tmp_path):
    pack_root = _make_pack(tmp_path)
    matrix_path = pack_root / "specs" / "test_matrix.csv"
    text = matrix_path.read_text(encoding="utf-8")
    matrix_path.write_text(text.replace("fixtures/gamepad/mapping_unknown.json", "fixtures/rest/rest_config_get__ok.json"), encoding="utf-8")
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task032_fixture_reference_unapproved_group" in report["blocked_reasons"]


def test_task032_blocks_source_summary_count_mismatch(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    task028_summary = json.loads(task028_path.read_text(encoding="utf-8"))
    task028_summary["coverage_summary"]["fixture_groups"]["datachannel"] += 1
    task028_path.write_text(json.dumps(task028_summary), encoding="utf-8")

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert (
        "pack_datachannel_count_mismatch_with_task028" in report["blocked_reasons"]
        or "task031_task032_out_of_scope_total_mismatch" in report["blocked_reasons"]
    )


def test_task032_blocks_task031_scope_reconciliation_mismatch(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    task031_summary = json.loads(task031_path.read_text(encoding="utf-8"))
    task031_summary["pack_contract"]["task032_out_of_scope_protocol_rows"] = 0
    task031_path.write_text(json.dumps(task031_summary), encoding="utf-8")

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task031_task032_out_of_scope_total_mismatch" in report["blocked_reasons"]


def test_task032_blocks_task036_ledger_status_mismatch(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    task036_summary = json.loads(task036_path.read_text(encoding="utf-8"))
    for area in task036_summary["coverage_area_ledger"]:
        if area["source_task"] == "TASK-032":
            area["status"] = "wrong_status"
    task036_path.write_text(json.dumps(task036_summary), encoding="utf-8")

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task036_task032_ledger_status_invalid" in report["blocked_reasons"]


def test_task032_blocks_non_protocol_fixture_group_row_from_false_pass(tmp_path):
    pack_root = _make_pack(tmp_path)
    matrix_path = pack_root / "specs" / "test_matrix.csv"
    rows = list(csv.DictReader(matrix_path.open(encoding="utf-8", newline="")))
    rows.append(
        _row(
            "TVAPI-DC-SECURITY-ROW",
            "security",
            "security",
            "DC_SECURITY_ROW",
            "security_redaction",
            "log_artifact_scanner_or_guard_test",
            "fixtures/datachannel/ping__ok.json",
        )
    )
    with matrix_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)

    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert (
        "pack_datachannel_count_mismatch_with_task028" in report["blocked_reasons"]
        or "task031_task032_out_of_scope_total_mismatch" in report["blocked_reasons"]
    )


def test_task032_public_report_rejects_raw_api_like_text(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["unsafe_note"] = "debug wss://example.invalid/socket"

    errors = validate_public_report(report)

    assert any("raw API/private/local evidence-like text" in error for error in errors)


def test_task032_public_report_rejects_unknown_fields(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["unsafe_extra"] = "controller mapping payload alias"

    errors = validate_public_report(report)

    assert "report_unknown_fields:unsafe_extra" in errors


def test_task032_public_report_rejects_pass_with_blockers(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["blocked_reasons"] = ["blocked_missing_local_quarantine_pack"]

    errors = validate_public_report(report)

    assert "pass_report_must_have_empty_blocked_reasons" in errors


def test_task032_public_report_rejects_pass_with_blocked_pack_contract(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["pack_contract"]["status"] = "blocked_pack_contract_validation_failed"

    errors = validate_public_report(report)

    assert "pass_report_pack_contract_must_pass" in errors


def test_task032_public_report_rejects_missing_pack_contract(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    del report["pack_contract"]

    errors = validate_public_report(report)

    assert "report_missing_required_fields:pack_contract" in errors


def test_task032_public_report_rejects_live_datachannel_claim(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["public_safety"]["datachannel_webrtc_connections_performed"] = True

    errors = validate_public_report(report)

    assert "public_safety_datachannel_webrtc_connections_performed_must_be_false" in errors


def test_task032_public_report_rejects_gamepad_runtime_claim(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["offline_execution_boundary"]["gamepad_runtime_input_or_pairing"] = "pass"

    errors = validate_public_report(report)

    assert "offline_execution_boundary_contains_executed_action" in errors


def test_task032_public_report_rejects_android_runtime_overclaim(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task031_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["android_runtime_status"] = "pass"

    errors = validate_public_report(report)

    assert "android_runtime_status_must_be_not_run" in errors


def test_task032_cli_writes_missing_pack_report_with_nonzero_exit(tmp_path, capsys):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    output_path = tmp_path / "task032.summary.json"

    exit_code = main(
        [
            "--task028-report",
            str(task028_path),
            "--task031-report",
            str(task031_path),
            "--task036-report",
            str(task036_path),
            "--pack-root",
            str(tmp_path / "missing"),
            "--report",
            str(output_path),
        ]
    )

    cli_result = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert cli_result["validation_status"] == "partial_blocked"
    assert written["pack_contract"]["status"] == "blocked_missing_local_quarantine_pack"


def test_task032_cli_allows_partial_blocked_zero_exit_when_explicit(tmp_path, capsys):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)

    exit_code = main(
        [
            "--task028-report",
            str(task028_path),
            "--task031-report",
            str(task031_path),
            "--task036-report",
            str(task036_path),
            "--pack-root",
            str(tmp_path / "missing"),
            "--allow-partial-blocked-exit-zero",
        ]
    )

    cli_result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert cli_result["validation_status"] == "partial_blocked"


def test_task032_cli_returns_nonzero_for_blocked_pack(tmp_path, capsys):
    pack_root = _make_pack(tmp_path)
    task028_path, task031_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    (pack_root / "fixtures" / "datachannel" / "ping__ok.json").write_text("{bad", encoding="utf-8")

    exit_code = main(
        [
            "--task028-report",
            str(task028_path),
            "--task031-report",
            str(task031_path),
            "--task036-report",
            str(task036_path),
            "--pack-root",
            str(pack_root),
        ]
    )

    cli_result = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert cli_result["validation_status"] == "blocked"

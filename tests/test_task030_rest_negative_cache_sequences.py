import csv
import json

from automation.api_layer_contract.validate_task028_api_layer_contract import build_report as build_task028_report
from automation.api_layer_contract.validate_task029_rest_schema_fixture_contracts import build_report as build_task029_report
from automation.api_layer_contract.validate_task036_api_layer_exhaustive_coverage import build_report as build_task036_report
from automation.api_layer_contract.validate_task030_rest_negative_cache_sequences import (
    build_report,
    main,
    validate_public_report,
)


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
    _write_json(root / "fixtures" / "stomp_signaling" / "offer__ok.json", {"message": "offer"})
    _write_json(root / "fixtures" / "stomp_device" / "pairing__ok.json", {"content": "Pairing"})
    _write_json(root / "fixtures" / "datachannel" / "ping__ok.json", {"message": "ping"})
    _write_json(root / "fixtures" / "gamepad" / "mapping_unknown.json", {"gamepad": {}})
    _write_json(
        root / "schemas" / "rest" / "client_config_response.schema.json",
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "ClientConfig", "type": "object"},
    )
    _write_json(
        root / "schemas" / "protocol" / "datachannel_message.schema.json",
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "DataChannel", "type": "object"},
    )

    rows = [
        {
            "test_id": "TVAPI-REST_CONFIG_GET-POS-001",
            "domain": "config",
            "layer": "rest",
            "item": "REST_CONFIG_GET",
            "test_type": "positive_schema",
            "priority": "P1",
            "title": "config happy path response validates against schema",
            "automation_target": "fixture_schema_test",
            "fixture_or_sequence": "fixtures/rest/rest_config_get__ok.json",
            "parallelization": "independent_api_layer",
            "status": "ready_or_fixture_only",
        },
        {
            "test_id": "TVAPI-REST_CONFIG_GET-NEG-001",
            "domain": "config",
            "layer": "rest",
            "item": "REST_CONFIG_GET",
            "test_type": "negative_malformed_json",
            "priority": "P1",
            "title": "config malformed response rejects",
            "automation_target": "fixture_schema_negative_test",
            "fixture_or_sequence": "fixtures/rest/rest_config_get__bad.json",
            "parallelization": "independent_api_layer",
            "status": "ready_or_fixture_only",
        },
        {
            "test_id": "TVAPI-REST_AUTH_REFRESH-NEG-AUTH",
            "domain": "auth",
            "layer": "rest",
            "item": "REST_AUTH_REFRESH",
            "test_type": "negative_auth",
            "priority": "P0",
            "title": "auth failure handled by mocked transport",
            "automation_target": "mock_http_test",
            "fixture_or_sequence": "fixtures/rest/rest_auth_refresh__401.json",
            "parallelization": "independent_api_layer",
            "status": "ready_or_fixture_only",
        },
        {
            "test_id": "TVAPI-REST_CONFIG_GET-SERVER-ERROR",
            "domain": "config",
            "layer": "rest",
            "item": "REST_CONFIG_GET",
            "test_type": "negative_server_error",
            "priority": "P1",
            "title": "server error handled by mocked transport",
            "automation_target": "mock_http_test",
            "fixture_or_sequence": "fixtures/rest/rest_config_get__500.json",
            "parallelization": "independent_api_layer",
            "status": "ready_or_fixture_only",
        },
        {
            "test_id": "TVAPI-REST_CONFIG_GET-CACHE",
            "domain": "config",
            "layer": "state_machine_sequence",
            "item": "REST_SEQUENCE_ITEM",
            "test_type": "cache_behavior",
            "priority": "P1",
            "title": "cache sequence remains deterministic",
            "automation_target": "mock_http_sequence_test",
            "fixture_or_sequence": "fixtures/sequences/rest_config_cache.sequence.json",
            "parallelization": "independent_api_layer",
            "status": "ready_or_fixture_only",
        },
        {
            "test_id": "TVAPI-WS_SIG_OFFER_IN-POS-001",
            "domain": "stomp_signaling",
            "layer": "protocol",
            "item": "WS_SIG_OFFER_IN",
            "test_type": "positive_protocol_schema",
            "priority": "P0",
            "title": "offer protocol fixture validates",
            "automation_target": "protocol_fixture_test",
            "fixture_or_sequence": "fixtures/stomp_signaling/offer__ok.json",
            "parallelization": "independent_api_layer",
            "status": "ready_or_fixture_only",
        },
        {
            "test_id": "TVAPI-DEVICE_STOMP_PAIRING-POS-001",
            "domain": "inter_device_communication",
            "layer": "protocol",
            "item": "DEVICE_STOMP_PAIRING",
            "test_type": "positive_protocol_schema",
            "priority": "P1",
            "title": "device pairing protocol fixture validates",
            "automation_target": "protocol_fixture_test",
            "fixture_or_sequence": "fixtures/stomp_device/pairing__ok.json",
            "parallelization": "independent_api_layer",
            "status": "ready_or_fixture_only",
        },
        {
            "test_id": "TVAPI-DC_PING_MESSAGE-POS-001",
            "domain": "stream_control",
            "layer": "protocol",
            "item": "DC_PING_MESSAGE",
            "test_type": "positive_protocol_schema",
            "priority": "P1",
            "title": "datachannel ping fixture validates",
            "automation_target": "protocol_fixture_test",
            "fixture_or_sequence": "fixtures/datachannel/ping__ok.json",
            "parallelization": "independent_api_layer",
            "status": "ready_or_fixture_only",
        },
    ]
    for index, item in enumerate(
        ["RUNTIME_OPTIONAL_ONE", "RUNTIME_OPTIONAL_TWO", "RUNTIME_OPTIONAL_THREE", "RUNTIME_OPTIONAL_FOUR"],
        start=1,
    ):
        rows.append(
            {
                "test_id": f"TVAPI-RUNTIME-OPTIONAL-{index}",
                "domain": "runtime",
                "layer": "runtime_optional",
                "item": item,
                "test_type": "explicit_deferred",
                "priority": "P2",
                "title": "live API lane is deferred to a separate approved task",
                "automation_target": "deferred_with_reason",
                "fixture_or_sequence": "templates/deferred_runtime_lane.md",
                "parallelization": "independent_api_layer",
                "status": "deferred_not_blocking_this_run",
            }
        )
    with (root / "specs" / "test_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return root


def _write_source_summaries(tmp_path, pack_root):
    task028_summary = build_task028_report(pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    task028_path = tmp_path / "task028.summary.json"
    task028_path.write_text(json.dumps(task028_summary), encoding="utf-8")
    task036_summary = build_task036_report(
        task028_path,
        pack_root=pack_root,
        generated_at_utc="2026-07-09T00:00:00Z",
    )
    task036_path = tmp_path / "task036.summary.json"
    task036_path.write_text(json.dumps(task036_summary), encoding="utf-8")
    task029_summary = build_task029_report(
        task028_path,
        task036_path,
        pack_root,
        generated_at_utc="2026-07-09T00:00:00Z",
    )
    task029_path = tmp_path / "task029.summary.json"
    task029_path.write_text(json.dumps(task029_summary), encoding="utf-8")
    return task028_path, task029_path, task036_path


def test_task030_passes_with_synthetic_pack_and_source_summaries(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)

    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "pass"
    assert report["pack_contract"]["status"] == "pass"
    assert report["pack_contract"]["task030_matrix_rows"] == 3
    assert report["pack_contract"]["mock_http_test_rows"] == 2
    assert report["pack_contract"]["mock_http_sequence_rows"] == 1
    assert report["pack_contract"]["state_machine_sequence_rows"] == 1
    assert report["pack_contract"]["cache_behavior_rows"] == 1
    assert report["pack_contract"]["fixture_groups_checked"] == {"rest": 2, "sequences": 1}
    assert report["live_api_execution_status"] == "not_run"
    assert report["public_safety"]["mocked_transport_only"] is True
    assert validate_public_report(report) == []


def test_task030_missing_pack_is_controlled_partial_blocker(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)

    report = build_report(task028_path, task029_path, task036_path, tmp_path / "missing", generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "partial_blocked"
    assert report["pack_contract"]["status"] == "blocked_missing_local_quarantine_pack"
    assert report["blocked_reasons"] == ["blocked_missing_local_quarantine_pack"]
    assert validate_public_report(report) == []


def test_task030_blocks_malformed_mock_fixture_json(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    (pack_root / "fixtures" / "rest" / "rest_auth_refresh__401.json").write_text("{bad", encoding="utf-8")

    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task030_fixture_json_malformed" in report["blocked_reasons"]


def test_task030_blocks_invalid_sequence_fixture_shape(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    _write_json(pack_root / "fixtures" / "sequences" / "rest_config_cache.sequence.json", {"state": "single"})

    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task030_sequence_fixture_shape_invalid" in report["blocked_reasons"]


def test_task030_cache_behavior_requires_sequence_like_fixture_shape(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    matrix_path = pack_root / "specs" / "test_matrix.csv"
    text = matrix_path.read_text(encoding="utf-8")
    matrix_path.write_text(
        text.replace("fixtures/sequences/rest_config_cache.sequence.json", "fixtures/rest/rest_config_get__ok.json"),
        encoding="utf-8",
    )

    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task030_sequence_fixture_shape_invalid" in report["blocked_reasons"]


def test_task030_accepts_virtual_time_sequence_fixture_shape(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    _write_json(
        pack_root / "fixtures" / "sequences" / "rest_config_cache.sequence.json",
        {
            "fixture_id": "sequence-fixture-001",
            "virtual_time": "synthetic",
            "poll_interval_seconds": 5,
            "timeout_seconds": 30,
            "expected_terminal_state": "timeout",
        },
    )

    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "pass"
    assert report["pack_contract"]["fixture_shape_counts"] == {"object": 2, "sequence_virtual_time": 1}


def test_task030_blocks_unapproved_fixture_reference_group(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    matrix_path = pack_root / "specs" / "test_matrix.csv"
    text = matrix_path.read_text(encoding="utf-8")
    matrix_path.write_text(text.replace("fixtures/rest/rest_auth_refresh__401.json", "fixtures/stomp_device/pairing__ok.json"), encoding="utf-8")

    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task030_fixture_reference_unapproved_group" in report["blocked_reasons"]


def test_task030_blocks_source_summary_count_mismatch(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    task028_summary = json.loads(task028_path.read_text(encoding="utf-8"))
    task028_summary["coverage_summary"]["counts_by_automation_target"]["mock_http_test"] += 1
    task028_path.write_text(json.dumps(task028_summary), encoding="utf-8")

    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert "task028_counts_by_automation_target_total_mismatch" in report["blocked_reasons"]


def test_task030_public_report_rejects_raw_api_like_text(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["unsafe_note"] = "debug /api/private/resource"

    errors = validate_public_report(report)

    assert any("raw API/private/local evidence-like text" in error for error in errors)


def test_task030_public_report_rejects_live_network_claim(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["public_safety"]["live_network_calls_performed"] = True

    errors = validate_public_report(report)

    assert "public_safety_live_network_calls_performed_must_be_false" in errors


def test_task030_public_report_rejects_android_runtime_overclaim(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    report = build_report(task028_path, task029_path, task036_path, pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    report["android_runtime_status"] = "pass"

    errors = validate_public_report(report)

    assert "android_runtime_status_must_be_not_run" in errors


def test_task030_cli_writes_report_for_missing_pack_with_zero_exit(tmp_path, capsys):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    output_path = tmp_path / "task030.summary.json"

    exit_code = main(
        [
            "--task028-report",
            str(task028_path),
            "--task029-report",
            str(task029_path),
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
    assert exit_code == 0
    assert cli_result["validation_status"] == "partial_blocked"
    assert written["pack_contract"]["status"] == "blocked_missing_local_quarantine_pack"


def test_task030_cli_returns_nonzero_for_blocked_pack(tmp_path, capsys):
    pack_root = _make_pack(tmp_path)
    task028_path, task029_path, task036_path = _write_source_summaries(tmp_path, pack_root)
    (pack_root / "fixtures" / "sequences" / "rest_config_cache.sequence.json").write_text("{bad", encoding="utf-8")

    exit_code = main(
        [
            "--task028-report",
            str(task028_path),
            "--task029-report",
            str(task029_path),
            "--task036-report",
            str(task036_path),
            "--pack-root",
            str(pack_root),
        ]
    )

    cli_result = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert cli_result["validation_status"] == "blocked"

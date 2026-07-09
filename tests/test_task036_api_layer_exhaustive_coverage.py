import csv
import json

from automation.api_layer_contract.validate_task028_api_layer_contract import build_report as build_task028_report
from automation.api_layer_contract.validate_task036_api_layer_exhaustive_coverage import (
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
                "  - id: WS_SIG_OFFER_IN",
                "    type: stomp_signaling_message",
                "  - id: DEVICE_STOMP_PAIRING",
                "    type: device_stomp_message",
                "  - id: DC_PING_MESSAGE",
                "    type: datachannel_message",
                "  - id: GAMEPAD_MAPPING_GET",
                "    type: rest",
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
    _write_json(root / "fixtures" / "sequences" / "rest_config_cache.json", [{"enabled": True}])
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
            "test_id": "TVAPI-REST_CONFIG_GET-CACHE",
            "domain": "config",
            "layer": "state_machine_sequence",
            "item": "REST_CONFIG_GET",
            "test_type": "cache_behavior",
            "priority": "P1",
            "title": "cache sequence remains deterministic",
            "automation_target": "mock_http_sequence_test",
            "fixture_or_sequence": "fixtures/sequences/rest_config_cache.json",
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
        {
            "test_id": "TVAPI-GAMEPAD_MAPPING_GET-EDGE",
            "domain": "gamepad",
            "layer": "rest",
            "item": "GAMEPAD_MAPPING_GET",
            "test_type": "negative_edge_case",
            "priority": "P1",
            "title": "unknown controller mapping is handled",
            "automation_target": "mock_or_fixture_test",
            "fixture_or_sequence": "fixtures/gamepad/mapping_unknown.json",
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


def _write_task028_summary(tmp_path, summary):
    path = tmp_path / "task028.summary.json"
    path.write_text(json.dumps(summary), encoding="utf-8")
    return path


def test_task036_validates_task028_summary_and_blocks_live_gate(tmp_path):
    task028_summary = build_task028_report(_make_pack(tmp_path), generated_at_utc="2026-07-09T00:00:00Z")
    summary_path = _write_task028_summary(tmp_path, task028_summary)

    report = build_report(summary_path, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "partial_blocked"
    assert report["local_pack_crosscheck"]["status"] == "blocked_pack_root_not_provided"
    assert report["runtime_execution_status"] == "not_run"
    assert report["live_api_execution_status"] == "not_run"
    assert report["source_summary"]["matrix_rows"] == 10
    assert report["exploratory_evidence_intake_gate"]["status"] == "blocked_missing_prod_conditional_prerequisites"
    assert validate_public_report(report) == []


def test_task036_missing_pack_is_controlled_partial_blocker(tmp_path):
    task028_summary = build_task028_report(_make_pack(tmp_path), generated_at_utc="2026-07-09T00:00:00Z")
    summary_path = _write_task028_summary(tmp_path, task028_summary)

    report = build_report(summary_path, pack_root=tmp_path / "missing-pack", generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "partial_blocked"
    assert report["local_pack_crosscheck"]["status"] == "blocked_missing_local_quarantine_pack"
    assert "local quarantine API pack is not available in this worktree." in report["blocked_reasons"]
    assert validate_public_report(report) == []


def test_task036_pack_crosscheck_passes_when_pack_matches_summary(tmp_path):
    pack_root = _make_pack(tmp_path)
    task028_summary = build_task028_report(pack_root, generated_at_utc="2026-07-09T00:00:00Z")
    summary_path = _write_task028_summary(tmp_path, task028_summary)

    report = build_report(summary_path, pack_root=pack_root, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "pass"
    assert report["local_pack_crosscheck"]["status"] == "pass"
    assert report["blocked_reasons"] == []


def test_task036_blocks_inconsistent_task028_count_totals(tmp_path):
    task028_summary = build_task028_report(_make_pack(tmp_path), generated_at_utc="2026-07-09T00:00:00Z")
    task028_summary["coverage_summary"]["counts_by_layer"]["rest"] += 1
    summary_path = _write_task028_summary(tmp_path, task028_summary)

    report = build_report(summary_path, generated_at_utc="2026-07-09T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert any("counts_by_layer total must equal matrix_rows" in reason for reason in report["blocked_reasons"])


def test_task036_public_report_rejects_live_network_claim(tmp_path):
    task028_summary = build_task028_report(_make_pack(tmp_path), generated_at_utc="2026-07-09T00:00:00Z")
    report = build_report(_write_task028_summary(tmp_path, task028_summary), generated_at_utc="2026-07-09T00:00:00Z")
    report["public_safety"]["live_network_calls_performed"] = True

    errors = validate_public_report(report)

    assert "public_safety.live_network_calls_performed must be false." in errors


def test_task036_public_report_rejects_missing_live_and_runtime_status_fields(tmp_path):
    task028_summary = build_task028_report(_make_pack(tmp_path), generated_at_utc="2026-07-09T00:00:00Z")
    report = build_report(_write_task028_summary(tmp_path, task028_summary), generated_at_utc="2026-07-09T00:00:00Z")
    report.pop("runtime_execution_status")
    report.pop("live_api_execution_status")

    errors = validate_public_report(report)

    assert "report missing required fields: ['live_api_execution_status', 'runtime_execution_status']." in errors


def test_task036_public_report_rejects_raw_api_like_text(tmp_path):
    task028_summary = build_task028_report(_make_pack(tmp_path), generated_at_utc="2026-07-09T00:00:00Z")
    report = build_report(_write_task028_summary(tmp_path, task028_summary), generated_at_utc="2026-07-09T00:00:00Z")
    report["unsafe_note"] = "debug /api/private/resource"

    errors = validate_public_report(report)

    assert any("raw API/private/local evidence-like text" in error for error in errors)


def test_task036_cli_writes_report_and_returns_zero_for_controlled_pack_blocker(tmp_path, capsys):
    task028_summary = build_task028_report(_make_pack(tmp_path), generated_at_utc="2026-07-09T00:00:00Z")
    summary_path = _write_task028_summary(tmp_path, task028_summary)
    output_path = tmp_path / "task036.summary.json"

    exit_code = main(["--task028-report", str(summary_path), "--pack-root", str(tmp_path / "missing"), "--report", str(output_path)])

    assert exit_code == 0
    cli_result = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert cli_result["validation_status"] == "partial_blocked"
    assert written["local_pack_crosscheck"]["status"] == "blocked_missing_local_quarantine_pack"


def test_task036_cli_returns_nonzero_for_invalid_task028_arithmetic(tmp_path, capsys):
    task028_summary = build_task028_report(_make_pack(tmp_path), generated_at_utc="2026-07-09T00:00:00Z")
    task028_summary["coverage_summary"]["counts_by_layer"]["rest"] += 1
    summary_path = _write_task028_summary(tmp_path, task028_summary)

    exit_code = main(["--task028-report", str(summary_path), "--pack-root", str(tmp_path / "missing")])

    assert exit_code == 1
    cli_result = json.loads(capsys.readouterr().out)
    assert cli_result["validation_status"] == "blocked"

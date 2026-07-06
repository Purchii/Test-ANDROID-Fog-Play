import csv
import json

from automation.api_layer_contract.validate_task028_api_layer_contract import (
    FOLLOW_UP_TASKS,
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


def test_build_report_accepts_synthetic_pack(tmp_path):
    report = build_report(_make_pack(tmp_path), generated_at_utc="2026-07-06T00:00:00Z")

    assert report["overall_status"] == "pass"
    assert report["runtime_execution_status"] == "not_run"
    assert report["live_api_execution_status"] == "not_run"
    assert report["archive_intake"]["matrix_rows"] == 10
    assert report["archive_intake"]["fixture_json_files"] == 6
    assert report["archive_intake"]["schema_json_files"] == 2
    assert report["coverage_summary"]["counts_by_status"]["deferred_not_blocking_this_run"] == 4
    assert report["public_safety"]["raw_endpoints_public"] is False
    assert validate_public_report(report) == []


def test_build_report_blocks_missing_fixture_reference(tmp_path):
    root = _make_pack(tmp_path)
    matrix_path = root / "specs" / "test_matrix.csv"
    text = matrix_path.read_text(encoding="utf-8")
    matrix_path.write_text(text.replace("fixtures/rest/rest_config_get__ok.json", "fixtures/rest/missing.json"), encoding="utf-8")

    report = build_report(root, generated_at_utc="2026-07-06T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert any("invalid pack reference" in reason for reason in report["blocked_reasons"])


def test_build_report_blocks_missing_required_file_without_traceback(tmp_path):
    root = _make_pack(tmp_path)
    (root / "specs" / "api_inventory.yaml").unlink()

    report = build_report(root, generated_at_utc="2026-07-06T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert report["runtime_execution_status"] == "not_run"
    assert report["live_api_execution_status"] == "not_run"
    assert "required pack file specs/api_inventory.yaml is missing." in report["blocked_reasons"]


def test_build_report_blocks_fixture_reference_traversal(tmp_path):
    root = _make_pack(tmp_path)
    matrix_path = root / "specs" / "test_matrix.csv"
    text = matrix_path.read_text(encoding="utf-8")
    matrix_path.write_text(text.replace("fixtures/rest/rest_config_get__ok.json", "../outside.json"), encoding="utf-8")

    report = build_report(root, generated_at_utc="2026-07-06T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert any("must stay under fixtures" in reason for reason in report["blocked_reasons"])


def test_build_report_blocks_absolute_fixture_reference(tmp_path):
    root = _make_pack(tmp_path)
    external_fixture = tmp_path / "external.json"
    external_fixture.write_text("{}", encoding="utf-8")
    matrix_path = root / "specs" / "test_matrix.csv"
    text = matrix_path.read_text(encoding="utf-8")
    matrix_path.write_text(text.replace("fixtures/rest/rest_config_get__ok.json", str(external_fixture)), encoding="utf-8")

    report = build_report(root, generated_at_utc="2026-07-06T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert any("must use POSIX separators" in reason or "must be relative" in reason for reason in report["blocked_reasons"])


def test_build_report_blocks_deferred_template_traversal(tmp_path):
    root = _make_pack(tmp_path)
    matrix_path = root / "specs" / "test_matrix.csv"
    text = matrix_path.read_text(encoding="utf-8")
    matrix_path.write_text(text.replace("templates/deferred_runtime_lane.md", "../deferred.md", 1), encoding="utf-8")

    report = build_report(root, generated_at_utc="2026-07-06T00:00:00Z")

    assert report["overall_status"] == "blocked"
    assert any("deferred template reference" in reason for reason in report["blocked_reasons"])


def test_public_report_rejects_raw_url_or_endpoint_values(tmp_path):
    report = build_report(_make_pack(tmp_path), generated_at_utc="2026-07-06T00:00:00Z")
    report["leaky_note"] = "GET /api/private/example/ https://example.invalid/token"

    errors = validate_public_report(report)

    assert any("raw URL or endpoint-like value" in error for error in errors)


def test_public_report_rejects_live_network_claim(tmp_path):
    report = build_report(_make_pack(tmp_path), generated_at_utc="2026-07-06T00:00:00Z")
    report["public_safety"]["live_network_calls_performed"] = True

    errors = validate_public_report(report)

    assert "public_safety.live_network_calls_performed must be false." in errors


def test_follow_up_decomposition_contains_conditional_live_gate():
    assert any(task["task_id"] == "TASK-034" for task in FOLLOW_UP_TASKS)
    assert [task for task in FOLLOW_UP_TASKS if task["task_id"] == "TASK-034"][0][
        "production_safety_classification"
    ] == "PROD_CONDITIONAL"


def test_cli_writes_public_safe_report(tmp_path, capsys):
    report_path = tmp_path / "report.json"
    exit_code = main(["--pack-root", str(_make_pack(tmp_path)), "--report", str(report_path)])

    assert exit_code == 0
    cli_result = json.loads(capsys.readouterr().out)
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert cli_result["validation_status"] == "pass"
    assert written["overall_status"] == "pass"
    assert validate_public_report(written) == []

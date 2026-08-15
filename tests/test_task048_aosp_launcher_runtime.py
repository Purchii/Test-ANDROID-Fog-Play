from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from automation.system_lane import task048_aosp_launcher_runtime as task048


def _bundle() -> dict[Path, bytes]:
    return dict(task048.build_bundle())


def _rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"), newline="")))


def _rewrite_csv(bundle: dict[Path, bytes], index: int, **changes: str) -> None:
    rows = _rows(bundle[task048.SCENARIO_OUTPUT])
    rows[index].update(changes)
    bundle[task048.SCENARIO_OUTPUT] = task048._csv_bytes(task048.SCENARIO_HEADERS, rows)
    report = json.loads(bundle[task048.REPORT_OUTPUT])
    for artifact in report["artifacts"]:
        if artifact["reference"] == task048._repo_ref(task048.SCENARIO_OUTPUT):
            artifact["sha256"] = hashlib.sha256(bundle[task048.SCENARIO_OUTPUT]).hexdigest()
    bundle[task048.REPORT_OUTPUT] = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()


def _rewrite_report(bundle: dict[Path, bytes], mutate) -> None:
    report = json.loads(bundle[task048.REPORT_OUTPUT])
    mutate(report)
    bundle[task048.REPORT_OUTPUT] = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()


def test_catalog_is_exact_19_rows_with_15_p0() -> None:
    rows = task048.load_catalog()
    assert [row["scenario_id"] for row in rows] == list(task048.EXPECTED_IDS)
    assert sum(row["priority"] == "P0" for row in rows) == 15
    assert sum(row["priority"] == "P1" for row in rows) == 4


def test_tracked_contracts_confirm_stick_is_missing_without_local_runtime() -> None:
    facts = task048.validate_static_contracts()
    assert facts["approved_stick_mapping_state"] == "missing"
    assert facts["physical_stick_availability"] == "unknown"
    assert facts["runtime_gate"] == "BLOCK_RUNTIME"
    assert facts["scenario_count"] == 19


def test_task042_unknown_mapping_authority_is_required(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = json.loads(task048.TASK042_REPORT.read_text(encoding="utf-8"))
    report["payload"]["fogplay_stick_actual_target"]["actual_alias_status"] = "known"
    changed = tmp_path / "task042.summary.json"
    changed.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(task048, "TASK042_REPORT", changed)
    with pytest.raises(task048.ContractError, match="task042_stick_authority_changed"):
        task048.validate_static_contracts()


def test_inventory_alias_substring_cannot_promote_stick_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = json.loads(task048.PUBLIC_DEVICE_INVENTORY.read_text(encoding="utf-8"))
    inventory["devices"].append({"device_alias": "generic-streaming-stick-014"})
    changed = tmp_path / "inventory.json"
    changed.write_text(json.dumps(inventory), encoding="utf-8")
    monkeypatch.setattr(task048, "PUBLIC_DEVICE_INVENTORY", changed)
    facts = task048.validate_static_contracts()
    assert facts["approved_stick_mapping_state"] == "missing"
    assert facts["physical_stick_availability"] == "unknown"


@pytest.mark.parametrize("attribute", ["CATALOG", "TASK042_REPORT"])
def test_invalid_utf8_fixed_input_fails_with_basename_only_reason(
    attribute: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    changed = tmp_path / f"invalid-{attribute.casefold()}.json"
    changed.write_bytes(b"\xff")
    monkeypatch.setattr(task048, attribute, changed)
    assert task048.main(["--validate-only"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked"
    assert payload["reason"] == f"tracked_contract_read_failed:{changed.name}"
    assert str(tmp_path) not in payload["reason"]


def test_blocked_baseline_terminally_classifies_all_rows() -> None:
    bundle = _bundle()
    rows = _rows(bundle[task048.SCENARIO_OUTPUT])
    assert len(rows) == 19
    assert {row["scenario_status"] for row in rows} <= task048.TERMINAL_STATUSES
    assert sum(row["scenario_status"] == "blocked_by_device" for row in rows) == 17
    assert sum(row["scenario_status"] == "blocked_by_product_boundary" for row in rows) == 1
    assert sum(row["scenario_status"] == "observed_pass" for row in rows) == 1


def test_every_scenario_has_zero_runtime_and_zero_product_coverage() -> None:
    rows = _rows(_bundle()[task048.SCENARIO_OUTPUT])
    assert {row["runtime_executed"] for row in rows} == {"false"}
    assert {row["product_coverage_counted"] for row in rows} == {"false"}
    assert all(row["evidence_type"] == "static_contract" for row in rows)


def test_qa048_014_stops_at_component_boundary() -> None:
    rows = {row["scenario_id"]: row for row in _rows(_bundle()[task048.SCENARIO_OUTPUT])}
    boundary = rows["QA-048-014"]
    assert boundary["scenario_status"] == "blocked_by_product_boundary"
    assert boundary["primary_blocker"] == "approved_public_component_contract_missing"
    assert "not attempted" in boundary["justification"]


def test_qa048_019_pass_is_static_closure_only() -> None:
    rows = {row["scenario_id"]: row for row in _rows(_bundle()[task048.SCENARIO_OUTPUT])}
    closure = rows["QA-048-019"]
    assert closure["scenario_status"] == "observed_pass"
    assert closure["evidence_status"] == "confirmed"
    assert closure["runtime_executed"] == "false"
    assert closure["product_coverage_counted"] == "false"
    assert "no product or release PASS" in closure["justification"]


def test_launcher_mapping_and_aosp_contract_are_distinct_authorities() -> None:
    rows = {row["authority_id"]: row for row in _rows(_bundle()[task048.AUTHORITY_OUTPUT])}
    aosp = rows["task048-aosp-full-artifact"]
    launcher = rows["task048-launcher-system-cluster"]
    assert aosp["main_five_apk_member"] == "true"
    assert aosp["static_state"] == "contract_declared_not_inspected"
    assert launcher["main_five_apk_member"] == "false"
    assert launcher["static_state"] == "mapping_missing"
    assert aosp["launcher_contour_separate"] == launcher["launcher_contour_separate"] == "true"


def test_generic_device_substitution_is_denied_everywhere() -> None:
    rows = _rows(_bundle()[task048.AUTHORITY_OUTPUT])
    assert {row["generic_substitution_allowed"] for row in rows} == {"false"}


def test_summary_blocks_runtime_coverage_and_release() -> None:
    report = json.loads(_bundle()[task048.REPORT_OUTPUT])
    assert report["execution_status"] == "blocked"
    assert report["coverage_status"] == "blocked"
    assert report["release_effect"] == "blocks_release"
    assert report["payload"]["runtime_action_count"] == 0
    assert report["payload"]["product_coverage_count"] == 0
    assert report["payload"]["release_pass_claimed"] is False


def test_missing_scenario_row_fails_closed() -> None:
    bundle = _bundle()
    rows = _rows(bundle[task048.SCENARIO_OUTPUT])[:-1]
    bundle[task048.SCENARIO_OUTPUT] = task048._csv_bytes(task048.SCENARIO_HEADERS, rows)
    with pytest.raises(task048.ContractError, match="scenario_ledger_missing_or_reordered_rows"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_status_drift_fails_even_with_matching_artifact_hash() -> None:
    bundle = _bundle()
    _rewrite_csv(bundle, 0, scenario_status="observed_pass")
    with pytest.raises(task048.ContractError, match="scenario_status_drift"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_fake_runtime_evidence_fails_even_with_matching_artifact_hash() -> None:
    bundle = _bundle()
    _rewrite_csv(bundle, 0, runtime_executed="true", evidence_type="physical_runtime", evidence_status="confirmed")
    with pytest.raises(task048.ContractError, match="repository_only_runtime_or_coverage_overclaim"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_fake_product_coverage_fails_even_with_matching_artifact_hash() -> None:
    bundle = _bundle()
    _rewrite_csv(bundle, 0, product_coverage_counted="true")
    with pytest.raises(task048.ContractError, match="repository_only_runtime_or_coverage_overclaim"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


@pytest.mark.parametrize(
    "changes",
    [
        {"evidence_type": "physical_runtime"},
        {"evidence_status": "confirmed"},
        {"primary_blocker": ""},
        {"secondary_blockers": ""},
        {"justification": "Runtime was observed and passed."},
    ],
)
def test_rebound_hash_cannot_hide_scenario_semantic_drift(changes: dict[str, str]) -> None:
    bundle = _bundle()
    _rewrite_csv(bundle, 0, **changes)
    with pytest.raises(task048.ContractError, match="scenario_ledger_semantic_drift"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_qa048_019_cannot_claim_physical_runtime() -> None:
    bundle = _bundle()
    _rewrite_csv(bundle, 18, evidence_type="physical_runtime")
    with pytest.raises(task048.ContractError, match="scenario_ledger_semantic_drift"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_summary_status_overclaim_fails_closed() -> None:
    bundle = _bundle()
    _rewrite_report(bundle, lambda report: report.update(execution_status="pass"))
    with pytest.raises(task048.ContractError, match="summary_blocked_authority_drift"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda report: report["payload"].update(actual_stick_mapping_state="ready"),
        lambda report: report["payload"].update(physical_stick_availability="ready"),
        lambda report: report["payload"].update(launcher_mapping_state="ready"),
        lambda report: report["payload"].update(aosp_artifact_state="verified_runtime"),
        lambda report: report["payload"].update(runtime_gate="GO"),
        lambda report: report["provenance"].update(adb_or_device_action=True),
        lambda report: report["provenance"].update(apk_read=True),
        lambda report: report["provenance"].update(runtime_evidence_published=True),
        lambda report: report["review"].update(qa_reviewer_a="go"),
        lambda report: report.update(blocked_reasons=[]),
        lambda report: report.update(unknowns=[]),
        lambda report: report.update(risks=[]),
        lambda report: report["artifacts"].append(dict(report["artifacts"][0])),
        lambda report: report["verification"][2].update(status="pass", evidence_status="confirmed", result_count=19),
    ],
)
def test_summary_semantic_drift_fails_closed(mutate) -> None:
    bundle = _bundle()
    _rewrite_report(bundle, mutate)
    with pytest.raises(task048.ContractError, match="summary_semantic_drift"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


@pytest.mark.parametrize(
    "unsafe",
    [
        "https://invalid.example/test",
        "C:\\Users\\example\\artifact",
        "192.0.2.10",
        ".qa_local/evidence/task-048/raw.json",
        "/tmp/raw/evidence.json",
        "file:///tmp/raw",
        "intent://unsafe",
        "market://unsafe",
        "mailto:test@example.invalid",
        "com.example/.MainActivity",
        "sha256:" + "a" * 64,
        "2001:db8::1",
    ],
)
def test_unsafe_public_value_is_rejected(unsafe: str) -> None:
    bundle = _bundle()
    _rewrite_report(bundle, lambda report: report.update(target_alias=unsafe))
    with pytest.raises(task048.ContractError, match="unsafe_public_value"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


@pytest.mark.parametrize("unsafe", ["a" * 64, "example.private.package"])
def test_unsafe_public_identifier_is_rejected(unsafe: str) -> None:
    bundle = _bundle()
    _rewrite_report(bundle, lambda report: report.update(target_alias=unsafe))
    with pytest.raises(task048.ContractError, match="unsafe_public_identifier"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_forbidden_public_key_is_rejected() -> None:
    bundle = _bundle()
    _rewrite_report(bundle, lambda report: report["payload"].update(adb_serial="synthetic-value"))
    with pytest.raises(task048.ContractError, match="forbidden_public_key"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_cross_family_catalog_lane_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    text = task048.CATALOG.read_text(encoding="utf-8").replace("FogPlay Stick", "generic TV", 1)
    changed = tmp_path / "task048_scenarios.csv"
    changed.write_text(text, encoding="utf-8")
    monkeypatch.setattr(task048, "CATALOG", changed)
    with pytest.raises(task048.ContractError, match="cross_family_lane_rejected"):
        task048.load_catalog()


def test_artifact_hash_tamper_is_rejected() -> None:
    bundle = _bundle()
    bundle[task048.AUTHORITY_OUTPUT] += b"\n"
    with pytest.raises(task048.ContractError, match="summary_artifact_hash_or_reference_drift"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_duplicate_json_key_is_rejected() -> None:
    bundle = _bundle()
    text = bundle[task048.REPORT_OUTPUT].decode("utf-8")
    text = text.replace('"task_id": "TASK-048",', '"task_id": "TASK-048",\n  "task_id": "TASK-048",', 1)
    bundle[task048.REPORT_OUTPUT] = text.encode("utf-8")
    with pytest.raises(task048.ContractError, match="duplicate_json_key:task_id"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_extra_csv_cell_is_rejected() -> None:
    bundle = _bundle()
    lines = bundle[task048.SCENARIO_OUTPUT].decode("utf-8").splitlines()
    lines[1] += ",unexpected"
    bundle[task048.SCENARIO_OUTPUT] = ("\n".join(lines) + "\n").encode("utf-8")
    with pytest.raises(task048.ContractError, match="csv_extra_cells"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_invalid_utf8_csv_is_a_stable_contract_error() -> None:
    bundle = _bundle()
    bundle[task048.SCENARIO_OUTPUT] = b"\xff"
    with pytest.raises(task048.ContractError, match="csv_invalid_utf8"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_invalid_utf8_json_is_a_stable_contract_error() -> None:
    bundle = _bundle()
    bundle[task048.REPORT_OUTPUT] = b"\xff"
    with pytest.raises(task048.ContractError, match="json_invalid"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_launcher_cluster_cannot_be_moved_into_main_five_apk_contract() -> None:
    bundle = _bundle()
    rows = _rows(bundle[task048.AUTHORITY_OUTPUT])
    rows[2]["main_five_apk_member"] = "true"
    bundle[task048.AUTHORITY_OUTPUT] = task048._csv_bytes(task048.AUTHORITY_HEADERS, rows)
    with pytest.raises(task048.ContractError, match="authority_ledger_semantic_drift"):
        task048.validate_bundle(bundle, validate_disk_artifacts=False)


def test_validate_only_and_preflight_do_not_publish(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(task048, "_atomic_publish", lambda _bundle: pytest.fail("write attempted"))
    assert task048.main(["--validate-only"]) == 0
    validate_payload = json.loads(capsys.readouterr().out)
    assert validate_payload["status"] == "pass"
    assert task048.main(["--preflight"]) == 0
    preflight_payload = json.loads(capsys.readouterr().out)
    assert preflight_payload["status"] == "blocked_by_device"
    assert preflight_payload["runtime_gate"] == "BLOCK_RUNTIME"


def test_publish_rolls_back_if_a_replace_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = [tmp_path / f"artifact-{index}.txt" for index in range(3)]
    for index, path in enumerate(paths):
        path.write_bytes(f"old-{index}".encode())
    bundle = {path: f"new-{index}".encode() for index, path in enumerate(paths)}
    real_replace = task048.os.replace
    calls = 0

    def fail_second_replace(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic replace failure")
        real_replace(source, destination)

    monkeypatch.setattr(task048.os, "replace", fail_second_replace)
    with pytest.raises(task048.ContractError, match="static_bundle_publish_failed"):
        task048._atomic_publish(bundle)
    assert [path.read_bytes() for path in paths] == [b"old-0", b"old-1", b"old-2"]
    assert not list(tmp_path.glob("*.task048.*"))


def test_publish_preserves_backup_if_rollback_replace_also_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = [tmp_path / f"artifact-{index}.txt" for index in range(3)]
    for index, path in enumerate(paths):
        path.write_bytes(f"old-{index}".encode())
    bundle = {path: f"new-{index}".encode() for index, path in enumerate(paths)}
    real_replace = task048.os.replace
    calls = 0

    def fail_publish_and_rollback(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls in {2, 3}:
            raise OSError("synthetic double failure")
        real_replace(source, destination)

    monkeypatch.setattr(task048.os, "replace", fail_publish_and_rollback)
    with pytest.raises(task048.ContractError, match="static_bundle_publish_rollback_failed"):
        task048._atomic_publish(bundle)
    backup = paths[0].with_name(f".{paths[0].name}.task048.rollback")
    assert backup.read_bytes() == b"old-0"


def test_cli_rejects_path_override() -> None:
    with pytest.raises(SystemExit):
        task048.main(["--validate-only", "--adapter-input", "anything"])


def test_tracked_report_bundle_validates() -> None:
    task048.validate_bundle(task048._tracked_bundle(), validate_disk_artifacts=True)

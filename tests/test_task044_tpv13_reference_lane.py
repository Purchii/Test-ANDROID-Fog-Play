from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path

import pytest

from automation.native_regression import task044_tpv13_reference_lane as subject


def contract_and_adapter() -> tuple[list[dict[str, str]], dict[str, object]]:
    catalog = subject.load_contract()
    return catalog, subject._initial_adapter(catalog)


def passing_attempt(scenario_id: str) -> dict[str, object]:
    oracle = subject.SCENARIO_PASS_ORACLES[scenario_id]
    boundary = {
        "applicable": scenario_id in subject.BOUNDARY_RECOVERY_SCENARIOS,
        "observed": scenario_id in subject.BOUNDARY_RECOVERY_SCENARIOS,
        "external_action_performed": False,
        "primary_back_recovery_outcome": "pass" if scenario_id in subject.BOUNDARY_RECOVERY_SCENARIOS else "not_applicable",
        "fallback_recovery_method": "none",
        "fallback_recovery_outcome": "not_required",
    }
    privacy = {
        "applicable": scenario_id == "QA-044-028",
        "bounded_log_summary_present": scenario_id == "QA-044-028",
        "public_output_scan": "pass" if scenario_id == "QA-044-028" else "not_required",
        "raw_sensitive_values_present": False,
    }
    crash = {
        "applicable": scenario_id == "QA-044-029",
        "scan_performed": scenario_id == "QA-044-029",
        "result": "clear" if scenario_id == "QA-044-029" else "not_required",
    }
    suffix = scenario_id[-3:]
    return {
        "attempt_id": f"attempt-{suffix}-1",
        "started_at_utc": "2026-08-14T10:00:00Z",
        "completed_at_utc": "2026-08-14T10:01:00Z",
        "pre_state_alias": "stable-state",
        "action_category": oracle["actions"][0],
        "observed_state_alias": oracle["observed"],
        "oracle_result": "pass",
        "evidence_type": "physical_runtime",
        "evidence_status": "confirmed",
        "modalities": {
            "screenshot": {"evidence_id": f"shot-{suffix}", "captured_at_utc": "2026-08-14T10:00:30Z", "visual_inspection": True},
            "ui_tree": {"evidence_id": f"tree-{suffix}", "captured_at_utc": "2026-08-14T10:00:31Z"},
            "runner_log": {"evidence_id": f"log-{suffix}", "captured_at_utc": "2026-08-14T10:00:32Z"},
        },
        "cleanup_result": "pass",
        "recovery_attempt": False,
        "recovery_of_attempt_id": "none",
        "dynamic_assertion_policy": "structure_and_category_only",
        "fixed_dynamic_values_used": False,
        "boundary": boundary,
        "privacy": privacy,
        "crash_anr": crash,
        "inventory_event": {
            "screen_alias": f"screen-{suffix}",
            "state_category": oracle["state"],
            "focus_category": oracle["focus"],
            "risk_note_code": "bounded_oracle_checkpoint",
            "recurrence_status": "first_observation",
            "prior_screen_alias": "none",
            "recurrence_match": "not_applicable",
        },
    }


def runtime_anomaly(scenario_id: str, attempt_id: str, classification: str) -> dict[str, object]:
    suffix = scenario_id[-3:]
    return {
        "anomaly_id": f"runtime-{suffix}-{attempt_id}",
        "anomaly_alias": f"scenario-{suffix}-failure",
        "category": "runtime_failure",
        "classification": classification,
        "evidence_status": "confirmed",
        "scenario_id": scenario_id,
        "attempt_id": attempt_id,
        "trigger_category": "scenario_action",
        "expected_result_category": "scenario_oracle_pass",
        "observed_result_category": "scenario_oracle_not_satisfied",
        "public_safe_screen_alias": f"screen-{suffix}",
        "cause_evidence_status": "hypothesis",
        "cause_category": "runtime_or_tooling_condition",
        "test_design_implication": "retain_first_failure_and_triage",
        "first_failure_retained": True,
        "reason_code": f"scenario_{suffix}_failure_recorded",
    }


def ready_adapter() -> tuple[list[dict[str, str]], dict[str, object]]:
    catalog, adapter = contract_and_adapter()
    adapter["runtime_preflight"].update({  # type: ignore[union-attr]
        "status": "READY", "adb_authorized": True, "artifact_present": True,
        "synthetic_fixture_ready": True, "ignored_evidence_storage_ready": True,
        "cleanup_rollback_ready": True, "reviewer_gate": True,
    })
    for entry in adapter["scenarios"]:  # type: ignore[index]
        attempt = passing_attempt(entry["scenario_id"])
        entry["attempts"] = [attempt]
        if entry["scenario_id"] == "QA-044-031":
            entry["attempts"] = []
            for cycle in range(1, 4):
                cycle_attempt = copy.deepcopy(attempt)
                cycle_attempt["attempt_id"] = f"attempt-031-cycle-{cycle}"
                cycle_attempt["action_category"] = f"repeatability_cycle_{cycle}"
                for modality in cycle_attempt["modalities"].values():
                    modality["evidence_id"] += f"-cycle-{cycle}"
                entry["attempts"].append(cycle_attempt)
    for anomaly in adapter["known_anomaly_rechecks"]:  # type: ignore[index]
        anomaly["classification"] = "resolved"
        anomaly["evidence_status"] = "confirmed"
        anomaly["first_failure_retained"] = True
        anomaly["reason_code"] = "fresh_recheck_resolved"
        anomaly["observed_result_category"] = "expected_result_observed"
        anomaly["public_safe_screen_alias"] = "recheck-screen"
        anomaly["cause_evidence_status"] = "hypothesis"
        anomaly["cause_category"] = "historical_condition_not_reproduced"
    adapter["generated_at_utc"] = "2026-08-14T10:01:30Z"
    return catalog, adapter


def report_from_bundle(bundle: dict[Path, bytes]) -> dict[str, object]:
    return json.loads(bundle[subject.REPORT_OUTPUT])


def test_exact_catalog_selector_reconciliation() -> None:
    rows = subject.load_contract()
    assert len(rows) == 32
    assert sum(row["priority"] == "P0" for row in rows) == 29
    assert sum(row["priority"] == "P1" for row in rows) == 3
    assert {row["lane"] for row in rows} == {"tv-tpv-013"}


def test_validate_only_has_no_file_or_subprocess_access(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(Path, "read_text", lambda *_a, **_k: pytest.fail("file read"))
    monkeypatch.setattr(Path, "write_text", lambda *_a, **_k: pytest.fail("file write"))
    monkeypatch.setattr(subject, "_atomic_publish", lambda *_a, **_k: pytest.fail("publish"))
    assert subject.main(["--validate-only"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["file_io"] == "not_run"
    assert result["subprocesses"] == "not_run"
    assert "subprocess" not in subject.__dict__


def test_initial_bundle_is_public_safe_blocked_and_not_runtime_pass() -> None:
    catalog, adapter = contract_and_adapter()
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "blocked"
    assert report["coverage_status"] == "blocked"
    assert report["payload"]["task_status"] == "blocked"
    assert report["payload"]["runtime_actions_not_run"] is True
    assert report["payload"]["phone_never_substitutes_tv"] is True
    assert report["payload"]["scenario_summary"]["status_counts"] == {"executable_not_run": 32}


def test_fresh_physical_visual_oracle_can_produce_pass() -> None:
    catalog, adapter = ready_adapter()
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "pass"
    assert report["coverage_status"] == "covered"
    assert report["evidence_status"] == "confirmed"
    assert report["payload"]["scenario_summary"]["status_counts"] == {"observed_pass": 32}


def test_generic_action_and_state_cannot_produce_pass() -> None:
    catalog, adapter = ready_adapter()
    attempt = adapter["scenarios"][0]["attempts"][0]  # type: ignore[index]
    attempt["action_category"] = "bounded-action"
    attempt["observed_state_alias"] = "expected-state"
    adapter["runtime_anomalies"] = [runtime_anomaly("QA-044-001", attempt["attempt_id"], "observed_fail")]
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "fail"
    assert report["payload"]["scenario_summary"]["status_counts"]["observed_fail"] == 1


def test_repeatability_requires_exactly_three_planned_non_recovery_cycles() -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][30]["attempts"] = adapter["scenarios"][30]["attempts"][:2]  # type: ignore[index]
    attempt_id = adapter["scenarios"][30]["attempts"][0]["attempt_id"]  # type: ignore[index]
    adapter["runtime_anomalies"] = [runtime_anomaly("QA-044-031", attempt_id, "observed_fail")]
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "fail"
    assert report["payload"]["scenario_summary"]["status_counts"]["observed_fail"] == 1


def test_repeatability_requires_exact_cycle_action_aliases() -> None:
    catalog, adapter = ready_adapter()
    attempt = adapter["scenarios"][30]["attempts"][1]  # type: ignore[index]
    attempt["action_category"] = "repeatability_cycle_generic"
    adapter["runtime_anomalies"] = [runtime_anomaly("QA-044-031", attempt["attempt_id"], "observed_fail")]
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "fail"


def test_checkpoint_ledger_has_one_row_per_attempt_and_all_three_cycles() -> None:
    catalog, adapter = ready_adapter()
    outputs = subject.build_bundle(adapter, catalog)
    rows = list(csv.DictReader(io.StringIO(outputs[subject.CHECKPOINT_LEDGER_OUTPUT].decode())))
    assert len(rows) == 34
    repeatability = [row for row in rows if row["scenario_id"] == "QA-044-031"]
    assert [row["attempt_index"] for row in repeatability] == ["1", "2", "3"]
    assert [row["action_category"] for row in repeatability] == [
        "repeatability_cycle_1", "repeatability_cycle_2", "repeatability_cycle_3"
    ]
    assert all(row["recovery_attempt"] == "false" and row["recovery_of_attempt_id"] == "none" for row in repeatability)


@pytest.mark.parametrize("evidence_type", ["paired_physical_runtime", "avd_tooling_runtime", "synthetic_offline", "mapped_only"])
def test_non_reference_evidence_type_cannot_pass(evidence_type: str) -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][0]["attempts"][0]["evidence_type"] = evidence_type  # type: ignore[index]
    attempt_id = adapter["scenarios"][0]["attempts"][0]["attempt_id"]  # type: ignore[index]
    adapter["runtime_anomalies"] = [runtime_anomaly("QA-044-001", attempt_id, "tooling_defect")]
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "fail"
    assert report["payload"]["scenario_summary"]["status_counts"].get("tooling_defect") == 1


def test_phone_or_cross_family_cannot_substitute_for_tv() -> None:
    catalog, adapter = ready_adapter()
    adapter["target"]["form_factor"] = "phone"  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="ADAPTER_SCHEMA_INSTANCE_INVALID|PHONE_OR_CROSS_LANE_SUBSTITUTION_FORBIDDEN"):
        subject.build_bundle(adapter, catalog)
    _, adapter = ready_adapter()
    adapter["build_ref"]["apk_family"] = "phone-full"  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="ADAPTER_SCHEMA_INSTANCE_INVALID|CROSS_FAMILY_BUILD_FORBIDDEN"):
        subject.build_bundle(adapter, catalog)


def test_retry_and_recovery_never_become_clean_pass() -> None:
    catalog, adapter = ready_adapter()
    first = copy.deepcopy(adapter["scenarios"][0]["attempts"][0])  # type: ignore[index]
    first["attempt_id"] = "attempt-001-first"
    first["oracle_result"] = "fail"
    recovered = copy.deepcopy(first)
    recovered["attempt_id"] = "attempt-001-recovery"
    recovered["oracle_result"] = "pass"
    recovered["recovery_attempt"] = True
    recovered["recovery_of_attempt_id"] = "attempt-001-first"
    for modality in recovered["modalities"].values():
        modality["evidence_id"] += "-recovery"
    adapter["scenarios"][0]["attempts"] = [first, recovered]  # type: ignore[index]
    adapter["runtime_anomalies"] = [runtime_anomaly("QA-044-001", "attempt-001-first", "observed_fail")]
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "fail"
    assert report["payload"]["scenario_summary"]["status_counts"]["observed_fail"] == 1


def test_runtime_failure_requires_attempt_linked_anomaly() -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][0]["attempts"][0]["oracle_result"] = "fail"  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="RUNTIME_ANOMALY_SCENARIO_COVERAGE_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_runtime_anomaly_is_separate_and_exported() -> None:
    catalog, adapter = ready_adapter()
    attempt = adapter["scenarios"][0]["attempts"][0]  # type: ignore[index]
    attempt["oracle_result"] = "fail"
    adapter["runtime_anomalies"] = [runtime_anomaly("QA-044-001", attempt["attempt_id"], "observed_fail")]
    outputs = subject.build_bundle(adapter, catalog)
    report = report_from_bundle(outputs)
    assert len(report["payload"]["known_anomaly_rechecks"]) == 3
    assert len(report["payload"]["runtime_anomalies"]) == 1
    ledger = list(csv.DictReader(io.StringIO(outputs[subject.ANOMALY_LEDGER_OUTPUT].decode())))
    assert [row["record_type"] for row in ledger].count("known_recheck") == 3
    assert [row["record_type"] for row in ledger].count("runtime_anomaly") == 1


def test_unclosed_known_anomaly_prevents_pass() -> None:
    catalog, adapter = ready_adapter()
    adapter["known_anomaly_rechecks"][0]["classification"] = "not_run"  # type: ignore[index]
    adapter["known_anomaly_rechecks"][0]["evidence_status"] = "unknown"  # type: ignore[index]
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "partial_blocked"
    assert report["payload"]["product_runtime_coverage_claim"] is False


@pytest.mark.parametrize("blocker", sorted(subject.BLOCKED_STATUSES))
def test_every_blocked_status_is_preserved_and_cannot_pass(blocker: str) -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][0]["blocker"] = {  # type: ignore[index]
        "status": blocker,
        "reason_code": subject.SCENARIO_BLOCKER_REASON_CODES["QA-044-001"],
    }
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    assert report["execution_status"] == "partial_blocked"
    assert report["payload"]["scenario_summary"]["status_counts"][blocker] == 1


def test_blocker_reason_is_exact_and_scenario_specific() -> None:
    assert subject.SCENARIO_BLOCKER_REASON_CODES["QA-044-013"] == "tooling_input_unsupported"
    assert subject.SCENARIO_BLOCKER_REASON_CODES["QA-044-024"] == "partial_family_home_return_not_executed"
    catalog, adapter = ready_adapter()
    adapter["scenarios"][12]["blocker"] = {"status": "blocked_by_oracle", "reason_code": "partial_family_home_return_not_executed"}  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="BLOCKER_REASON_CODE_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_stale_modality_is_rejected() -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][0]["attempts"][0]["modalities"]["screenshot"]["captured_at_utc"] = "2026-08-14T09:59:00Z"  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="EVIDENCE_STALE_OR_OUTSIDE_ATTEMPT"):
        subject.build_bundle(adapter, catalog)


def test_prior_run_evidence_is_not_fresh() -> None:
    catalog, adapter = ready_adapter()
    adapter["generated_at_utc"] = "2026-08-16T10:01:30Z"
    with pytest.raises(subject.ContractError, match="RUN_EVIDENCE_NOT_FRESH"):
        subject.build_bundle(adapter, catalog)


def test_missing_visual_inspection_is_rejected() -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][0]["attempts"][0]["modalities"]["screenshot"]["visual_inspection"] = False  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="ADAPTER_SCHEMA_INSTANCE_INVALID|VISUAL_INSPECTION_MISSING"):
        subject.build_bundle(adapter, catalog)


def test_dynamic_fixed_values_are_rejected() -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][8]["attempts"][0]["fixed_dynamic_values_used"] = True  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="ADAPTER_SCHEMA_INSTANCE_INVALID|DYNAMIC_DATA_ASSERTION_UNSAFE"):
        subject.build_bundle(adapter, catalog)


def test_boundary_external_action_is_rejected() -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][20]["attempts"][0]["boundary"]["external_action_performed"] = True  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="ADAPTER_SCHEMA_INSTANCE_INVALID|BOUNDARY_SAFETY_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_boundary_force_stop_fallback_does_not_erase_failed_back() -> None:
    catalog, adapter = ready_adapter()
    attempt = adapter["scenarios"][20]["attempts"][0]  # type: ignore[index]
    attempt["boundary"].update({
        "primary_back_recovery_outcome": "fail",
        "fallback_recovery_method": "force_stop_relaunch",
        "fallback_recovery_outcome": "pass",
    })
    adapter["runtime_anomalies"] = [runtime_anomaly("QA-044-021", attempt["attempt_id"], "observed_fail")]
    outputs = subject.build_bundle(adapter, catalog)
    report = report_from_bundle(outputs)
    assert report["execution_status"] == "fail"
    scenario_rows = list(csv.DictReader(io.StringIO(outputs[subject.SCENARIO_LEDGER_OUTPUT].decode())))
    assert scenario_rows[20]["boundary_safely_held"] == "false"


@pytest.mark.parametrize(("field", "value"), [("pre_state_alias", "79991234567"), ("screen_alias", "accountValue123")])
def test_attempt_derived_checkpoint_values_are_redaction_checked(field: str, value: str) -> None:
    catalog, adapter = ready_adapter()
    attempt = adapter["scenarios"][0]["attempts"][0]  # type: ignore[index]
    if field == "screen_alias":
        attempt["inventory_event"][field] = value
    else:
        attempt[field] = value
    with pytest.raises(subject.ContractError, match="PUBLIC_VALUE_FORBIDDEN"):
        subject.build_bundle(adapter, catalog)


def test_preflight_authority_digest_is_exact_bound() -> None:
    catalog, adapter = contract_and_adapter()
    adapter["runtime_preflight"]["authority_report_sha256"] = "0" * 64  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="PREFLIGHT_AUTHORITY_LINK_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_defect_requires_tracked_reference_and_failed_reproduction_attempt() -> None:
    catalog, adapter = ready_adapter()
    attempt = adapter["scenarios"][3]["attempts"][0]  # type: ignore[index]
    defect_path = subject.REPO_ROOT / "docs/qa/defects/task044_loader_timeout_after_ambient_recovery.md"
    adapter["scenarios"][3]["defect"] = {  # type: ignore[index]
        "defect_alias": "TASK044-DEFECT-LOADER-001",
        "reference": "docs/qa/defects/task044_loader_timeout_after_ambient_recovery.md",
        "sha256": hashlib.sha256(defect_path.read_bytes()).hexdigest(),
        "reproduction_attempt_ids": [attempt["attempt_id"]],
    }
    with pytest.raises(subject.ContractError, match="DEFECT_REPRODUCTION_LINK_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_confirmed_defect_is_linked_to_failed_attempt_and_runtime_anomaly() -> None:
    catalog, adapter = ready_adapter()
    attempt = adapter["scenarios"][3]["attempts"][0]  # type: ignore[index]
    attempt["oracle_result"] = "fail"
    defect_path = subject.REPO_ROOT / "docs/qa/defects/task044_loader_timeout_after_ambient_recovery.md"
    adapter["scenarios"][3]["defect"] = {  # type: ignore[index]
        "defect_alias": "TASK044-DEFECT-LOADER-001",
        "reference": "docs/qa/defects/task044_loader_timeout_after_ambient_recovery.md",
        "sha256": hashlib.sha256(defect_path.read_bytes()).hexdigest(),
        "reproduction_attempt_ids": [attempt["attempt_id"]],
    }
    adapter["runtime_anomalies"] = [runtime_anomaly("QA-044-004", attempt["attempt_id"], "confirmed_defect")]
    report = report_from_bundle(subject.build_bundle(adapter, catalog))
    failure = report["payload"]["outcome_aggregates"]["confirmed_failures"][0]
    assert failure["defect_alias"] == "TASK044-DEFECT-LOADER-001"
    assert failure["defect_reference"].startswith("docs/qa/defects/task044_")


def test_malformed_32_empty_scenarios_fail_authoritative_contract() -> None:
    catalog, adapter = contract_and_adapter()
    adapter["scenarios"] = [{} for _ in range(32)]
    with pytest.raises(subject.ContractError, match="ADAPTER_SCHEMA_INSTANCE_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_oracle_schema_is_full_content_pinned_and_used() -> None:
    assert hashlib.sha256(subject.ORACLE_SCHEMA.read_bytes()).hexdigest() == subject.ORACLE_SCHEMA_SHA256
    subject._validate_oracle_schema()


def test_log_privacy_and_crash_oracles_are_mandatory() -> None:
    catalog, adapter = ready_adapter()
    adapter["scenarios"][27]["attempts"][0]["privacy"]["bounded_log_summary_present"] = False  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="PRIVACY_LOG_ORACLE_INVALID"):
        subject.build_bundle(adapter, catalog)
    _, adapter = ready_adapter()
    adapter["scenarios"][28]["attempts"][0]["crash_anr"]["scan_performed"] = False  # type: ignore[index]
    with pytest.raises(subject.ContractError, match="CRASH_ANR_ORACLE_MISSING"):
        subject.build_bundle(adapter, catalog)


def test_preflight_requires_typed_input_and_never_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    catalog, adapter = contract_and_adapter()
    path = tmp_path / ".qa_local" / "evidence" / "task-044" / "adapter.json"
    path.parent.mkdir(parents=True)
    monkeypatch.setattr(subject, "LOCAL_ADAPTER_ROOT", path.parent)
    path.write_text(json.dumps(adapter), encoding="utf-8")
    monkeypatch.setattr(subject, "_atomic_publish", lambda *_a, **_k: pytest.fail("publish"))
    assert subject.main(["--preflight", "--adapter-input", str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["writes"] == "not_run"
    assert result["runtime_actions"] == "not_run"


def test_execute_requires_explicit_ingest_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _, adapter = contract_and_adapter()
    path = tmp_path / ".qa_local" / "evidence" / "task-044" / "adapter.json"
    path.parent.mkdir(parents=True)
    monkeypatch.setattr(subject, "LOCAL_ADAPTER_ROOT", path.parent)
    path.write_text(json.dumps(adapter), encoding="utf-8")
    assert subject.main(["--execute", "--adapter-input", str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["reason_code"] == "PROD_CONDITIONAL_INGEST_GATE_REQUIRED"


def test_rebound_artifact_hash_cannot_hide_semantic_ledger_tamper() -> None:
    catalog, adapter = contract_and_adapter()
    outputs = subject.build_bundle(adapter, catalog)
    mutated = dict(outputs)
    ledger = mutated[subject.SCENARIO_LEDGER_OUTPUT].replace(b"QA-044-001", b"QA-044-999", 1)
    mutated[subject.SCENARIO_LEDGER_OUTPUT] = ledger
    report = json.loads(mutated[subject.REPORT_OUTPUT])
    for artifact in report["artifacts"]:
        if artifact["kind"] == "scenario_ledger":
            artifact["sha256"] = subject._sha(ledger)
    mutated[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    with pytest.raises(subject.ContractError, match="BUNDLE_LEDGER_SCENARIO_SET_INVALID"):
        subject.validate_bundle(mutated, catalog=catalog)


def test_rebound_hash_cannot_hide_checkpoint_false_pass() -> None:
    catalog, adapter = ready_adapter()
    outputs = subject.build_bundle(adapter, catalog)
    mutated = dict(outputs)
    checkpoints = mutated[subject.CHECKPOINT_LEDGER_OUTPUT].replace(b",true,true,true,fresh,", b",false,true,true,fresh,", 1)
    mutated[subject.CHECKPOINT_LEDGER_OUTPUT] = checkpoints
    report = json.loads(mutated[subject.REPORT_OUTPUT])
    for artifact in report["artifacts"]:
        if artifact["kind"] == "checkpoint_ledger":
            artifact["sha256"] = subject._sha(checkpoints)
    mutated[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    with pytest.raises(subject.ContractError, match="BUNDLE_CHECKPOINT_FALSE_PASS"):
        subject.validate_bundle(mutated, catalog=catalog)


def test_false_pass_report_tamper_is_rejected_even_with_valid_json() -> None:
    catalog, adapter = contract_and_adapter()
    outputs = subject.build_bundle(adapter, catalog)
    mutated = dict(outputs)
    report = json.loads(mutated[subject.REPORT_OUTPUT])
    report["execution_status"] = "pass"
    mutated[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    with pytest.raises(subject.ContractError, match="REPORT_FALSE_PASS"):
        subject.validate_bundle(mutated, catalog=catalog)


def test_malformed_cli_input_has_public_safe_generic_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / ".qa_local" / "evidence" / "task-044" / "adapter.json"
    path.parent.mkdir(parents=True)
    monkeypatch.setattr(subject, "LOCAL_ADAPTER_ROOT", path.parent)
    path.write_text('{"schema_version":"task044-runtime-adapter-v1","run_id":[]}', encoding="utf-8")
    assert subject.main(["--preflight", "--adapter-input", str(path)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["validation_status"] == "blocked"
    assert "traceback" not in json.dumps(result).lower()


def test_adapter_outside_canonical_task_root_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    canonical_root = tmp_path / ".qa_local" / "evidence" / "task-044"
    canonical_root.mkdir(parents=True)
    monkeypatch.setattr(subject, "LOCAL_ADAPTER_ROOT", canonical_root)
    outside = tmp_path / "adapter.json"
    outside.write_text("{}", encoding="utf-8")

    with pytest.raises(subject.ContractError, match="ADAPTER_INPUT_TYPE_INVALID"):
        subject._load_adapter(outside)


def test_atomic_publish_rolls_back_all_targets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = [tmp_path / name for name in ("report.json", "scenarios.csv", "checkpoints.csv", "anomalies.csv")]
    for constant, path in zip(
        ("REPORT_OUTPUT", "SCENARIO_LEDGER_OUTPUT", "CHECKPOINT_LEDGER_OUTPUT", "ANOMALY_LEDGER_OUTPUT"),
        paths,
        strict=True,
    ):
        monkeypatch.setattr(subject, constant, path)
        path.write_bytes(b"OLD")
    real_replace = os.replace
    calls = 0

    def fail_third(source: os.PathLike[str] | str, target: os.PathLike[str] | str) -> None:
        nonlocal calls
        if ".backup." not in str(source):
            calls += 1
            if calls == 3:
                raise OSError("injected")
        real_replace(source, target)

    monkeypatch.setattr(subject.os, "replace", fail_third)
    with pytest.raises(subject.ContractError, match="OUTPUT_ATOMIC_PUBLISH_FAILED"):
        subject._atomic_publish({path: b"NEW" for path in paths})
    assert {path.read_bytes() for path in paths} == {b"OLD"}
    assert not list(tmp_path.glob("*.tmp"))


def test_initial_bundle_validates_in_memory_without_overwriting_physical_report() -> None:
    catalog, adapter = contract_and_adapter()
    subject.validate_bundle(subject.build_bundle(adapter, catalog), catalog=catalog)


def test_checked_physical_bundle_validates() -> None:
    assert subject.main(["--validate-report"]) == 0

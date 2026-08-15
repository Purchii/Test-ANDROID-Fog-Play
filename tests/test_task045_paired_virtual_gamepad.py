from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path

import pytest

from automation.gamepad import task045_paired_virtual_gamepad as subject


def baseline() -> tuple[list[dict[str, str]], dict[str, object]]:
    return subject.load_contract(), subject._baseline_adapter()


def add_independent_pass(adapter: dict[str, object], scenario_id: str) -> None:
    adapter["generated_at_utc"] = "2026-08-15T10:02:00Z"
    adapter["runtime_preflight"]["phone"].update(
        status="READY",
        adb_authorized=True,
        artifact_present=True,
        family_confirmed=True,
        owner_declared_available=True,
        reason_code="approved_phone_realme_independent_lane_ready",
    )
    action, observed = subject.PASS_ORACLES[scenario_id]
    attempt_id = f"attempt-{scenario_id.lower()}-1"
    cleanup_id = f"cleanup-{scenario_id.lower()}-1"
    boundary_id = f"boundary-{scenario_id.lower()}-1"
    attempt = {
        "attempt_id": attempt_id,
        "started_at_utc": "2026-08-15T10:00:00Z",
        "completed_at_utc": "2026-08-15T10:00:05Z",
        "lane_scope": "phone_independent",
        "phone_alias": "phone-realme-001",
        "phone_apk_family": "phone-full",
        "tv_alias": "tv-tpv-013",
        "tv_apk_family": "television-full",
        "pre_state_alias": "phone_disconnected",
        "action_category": action,
        "observed_state_alias": observed,
        "oracle_result": "pass",
        "evidence_type": "physical_runtime",
        "evidence_status": "confirmed",
        "paired_state_observed": False,
        "modalities": {
            "screenshot": {"evidence_id": f"shot-{scenario_id.lower()}-1", "captured_at_utc": "2026-08-15T10:00:02Z", "visual_inspection": True},
            "ui_tree": {"evidence_id": f"tree-{scenario_id.lower()}-1", "captured_at_utc": "2026-08-15T10:00:03Z"},
            "runner_log": {"evidence_id": f"log-{scenario_id.lower()}-1", "captured_at_utc": "2026-08-15T10:00:04Z"},
        },
        "recovery_attempt": False,
        "recovery_of_attempt_id": "none",
        "cleanup_id": cleanup_id,
        "boundary_id": boundary_id,
    }
    scenario = adapter["scenarios"][int(scenario_id[-3:]) - 1]
    scenario["blocker"] = None
    scenario["attempts"] = [attempt]
    adapter["cleanup"].append({
        "cleanup_id": cleanup_id,
        "scenario_id": scenario_id,
        "attempt_id": attempt_id,
        "action_category": "return_to_safe_phone_state",
        "result": "pass",
        "kill_switch_ready": True,
        "rollback_verified": True,
        "evidence_status": "confirmed",
    })
    adapter["boundaries"].append({
        "boundary_id": boundary_id,
        "scenario_id": scenario_id,
        "attempt_id": attempt_id,
        "category": "none",
        "reached": False,
        "external_action_performed": False,
        "qr_traversed": False,
        "mutation_performed": False,
        "recovery_result": "not_required",
        "evidence_status": "confirmed",
    })
    adapter["paired_timeline"].append({
        "event_id": f"event-{scenario_id.lower()}-1",
        "scenario_id": scenario_id,
        "observed_at_utc": "2026-08-15T10:00:03Z",
        "side": "phone",
        "state_alias": observed,
        "attempt_id": attempt_id,
        "evidence_ids": [f"shot-{scenario_id.lower()}-1", f"tree-{scenario_id.lower()}-1"],
    })


def report_from(bundle: dict[Path, bytes]) -> dict[str, object]:
    return json.loads(bundle[subject.REPORT_OUTPUT])


def scenario_rows(bundle: dict[Path, bytes]) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(bundle[subject.SCENARIO_LEDGER_OUTPUT].decode())))


def test_exact_catalog_is_22_rows_20_p0_2_p1() -> None:
    catalog = subject.load_contract()
    assert [row["scenario_id"] for row in catalog] == list(subject.EXPECTED_IDS)
    assert sum(row["priority"] == "P0" for row in catalog) == 20
    assert sum(row["priority"] == "P1" for row in catalog) == 2


def test_validate_only_has_no_file_access(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(Path, "read_text", lambda *_args, **_kwargs: pytest.fail("read forbidden"))
    monkeypatch.setattr(Path, "read_bytes", lambda *_args, **_kwargs: pytest.fail("read forbidden"))
    assert subject.main(["--validate-only"]) == 0
    assert json.loads(capsys.readouterr().out)["runtime_access"] is False


def test_blocked_baseline_is_terminal_partial_and_blocks_release() -> None:
    catalog, adapter = baseline()
    bundle = subject.build_bundle(adapter, catalog)
    report = report_from(bundle)
    rows = scenario_rows(bundle)
    assert report["coverage_status"] == "partial_blocked"
    assert report["release_effect"] == "blocks_release"
    assert all(row["scenario_status"] in subject.TERMINAL_STATUSES for row in rows)
    assert rows[-1]["scenario_id"] == "QA-045-022"
    assert rows[-1]["scenario_status"] == "blocked_by_oracle"
    assert rows[-1]["evidence_type"] == "static_contract"


def test_missing_tv_blocks_every_paired_or_connected_row() -> None:
    catalog, adapter = baseline()
    rows = scenario_rows(subject.build_bundle(adapter, catalog))
    for row in rows:
        if row["scenario_id"] in subject.PAIRED_REQUIRED_SCENARIOS:
            assert row["scenario_status"] == "blocked_by_device"
            assert row["reason_code"] == "paired_tv_unavailable"


@pytest.mark.parametrize("scenario_id", ["QA-045-006", "QA-045-009"])
def test_only_approved_independent_phone_scenarios_can_pass(scenario_id: str) -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, scenario_id)
    rows = scenario_rows(subject.build_bundle(adapter, catalog))
    row = rows[int(scenario_id[-3:]) - 1]
    assert row["scenario_status"] == "observed_pass"
    assert row["evidence_type"] == "physical_runtime"


@pytest.mark.parametrize("scenario_id", ["QA-045-012", "QA-045-013"])
def test_auxiliary_disconnected_phone_cannot_satisfy_connected_lifecycle(scenario_id: str) -> None:
    catalog, adapter = baseline()
    scenario = adapter["scenarios"][int(scenario_id[-3:]) - 1]
    scenario["blocker"] = None
    source = copy.deepcopy(adapter)
    add_independent_pass(source, "QA-045-006")
    adapter["generated_at_utc"] = source["generated_at_utc"]
    attempt = copy.deepcopy(source["scenarios"][5]["attempts"][0])
    attempt["attempt_id"] = f"attempt-{scenario_id.lower()}-1"
    attempt["action_category"], attempt["observed_state_alias"] = subject.PASS_ORACLES[scenario_id]
    scenario["attempts"] = [attempt]
    with pytest.raises(subject.ContractError, match="PAIRED_PHONE_LANE_NOT_APPROVED|PAIRED_EVIDENCE_REQUIRED"):
        subject.build_bundle(adapter, catalog)


def test_realme_deviation_is_independent_only() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    subject.build_bundle(adapter, catalog)
    attempt = adapter["scenarios"][5]["attempts"][0]
    attempt["phone_alias"] = "phone-unknown-999"
    with pytest.raises(subject.ContractError, match="PHONE_TARGET_SUBSTITUTION|SCHEMA_INSTANCE_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_cross_family_phone_evidence_is_rejected() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["scenarios"][5]["attempts"][0]["phone_apk_family"] = "television-full"
    with pytest.raises(subject.ContractError, match="PHONE_TARGET_SUBSTITUTION|SCHEMA_INSTANCE_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_stale_visual_evidence_is_rejected() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["scenarios"][5]["attempts"][0]["modalities"]["screenshot"]["captured_at_utc"] = "2026-08-14T10:00:02Z"
    with pytest.raises(subject.ContractError, match="EVIDENCE_FRESHNESS_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_missing_visual_inspection_is_rejected() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-009")
    adapter["scenarios"][8]["attempts"][0]["modalities"]["screenshot"]["visual_inspection"] = False
    with pytest.raises(subject.ContractError, match="VISUAL_INSPECTION_REQUIRED|SCHEMA_INSTANCE_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_recovery_cannot_become_clean_pass() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    scenario = adapter["scenarios"][5]
    first = scenario["attempts"][0]
    first["oracle_result"] = "fail"
    first["observed_state_alias"] = "unexpected_phone_state"
    adapter["anomalies"].append({
        "anomaly_id": "anomaly-qa045-006-1", "scenario_id": "QA-045-006",
        "attempt_id": first["attempt_id"], "trigger_category": "launch_without_tv",
        "expected_result_category": "no_phantom_tv", "observed_result_category": "unexpected_state",
        "public_safe_screen_alias": "phone_unexpected", "classification": "observed_fail",
        "evidence_status": "confirmed", "cause_evidence_status": "hypothesis",
        "cause_category": "runtime_state", "test_design_implication": "retain_first_failure",
        "first_failure_retained": True, "reason_code": "first_failure",
    })
    second = copy.deepcopy(first)
    second["attempt_id"] = "attempt-qa-045-006-2"
    second["started_at_utc"] = "2026-08-15T10:01:00Z"
    second["completed_at_utc"] = "2026-08-15T10:01:05Z"
    second["oracle_result"] = "pass"
    second["observed_state_alias"] = subject.PASS_ORACLES["QA-045-006"][1]
    second["recovery_attempt"] = True
    second["recovery_of_attempt_id"] = first["attempt_id"]
    second["cleanup_id"] = "cleanup-qa-045-006-2"
    second["boundary_id"] = "boundary-qa-045-006-2"
    for index, modality in enumerate(second["modalities"].values(), start=2):
        modality["evidence_id"] += "-recovery"
        modality["captured_at_utc"] = f"2026-08-15T10:01:0{index}Z"
    scenario["attempts"].append(second)
    adapter["cleanup"].append({**adapter["cleanup"][0], "cleanup_id": second["cleanup_id"], "attempt_id": second["attempt_id"]})
    adapter["boundaries"].append({
        **adapter["boundaries"][0],
        "boundary_id": second["boundary_id"],
        "attempt_id": second["attempt_id"],
    })
    adapter["paired_timeline"].append({
        **adapter["paired_timeline"][0],
        "event_id": "event-qa045-006-2",
        "attempt_id": second["attempt_id"],
        "observed_at_utc": "2026-08-15T10:01:03Z",
        "evidence_ids": [second["modalities"]["screenshot"]["evidence_id"], second["modalities"]["ui_tree"]["evidence_id"]],
    })
    rows = scenario_rows(subject.build_bundle(adapter, catalog))
    assert rows[5]["scenario_status"] == "observed_fail"
    assert rows[5]["first_failure_retained"] == "true"


def test_failed_attempt_requires_immediate_anomaly_record() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["scenarios"][5]["attempts"][0]["oracle_result"] = "fail"
    with pytest.raises(subject.ContractError, match="FAILED_ATTEMPT_ANOMALY_MISSING"):
        subject.build_bundle(adapter, catalog)


def test_forbidden_payment_or_qr_action_is_rejected() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["boundaries"][0]["qr_traversed"] = True
    with pytest.raises(subject.ContractError, match="FORBIDDEN_BOUNDARY_ACTION|SCHEMA_INSTANCE_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_connected_phone_coverage_cannot_be_marked_covered_without_tv() -> None:
    catalog, adapter = baseline()
    connected = next(row for row in adapter["phone_coverage"] if row["requires_connected_pair"])
    adapter["inventory_evidence_ids"].append("shot-connected")
    connected.update(status="covered", evidence_status="confirmed", evidence_ids=["shot-connected"], discovered=True)
    adapter["runtime_preflight"]["inventory_discovered_branch_count"] = 1
    with pytest.raises(subject.ContractError, match="DISCONNECTED_PHONE_CANNOT_COVER_CONNECTED_BRANCH"):
        subject.build_bundle(adapter, catalog)


def test_incomplete_phone_coverage_ledger_is_rejected() -> None:
    catalog, adapter = baseline()
    adapter["runtime_preflight"]["inventory_declaration_complete"] = True
    with pytest.raises(subject.ContractError, match="INVENTORY_CORE_DECLARATION_MISMATCH"):
        subject.build_bundle(adapter, catalog)


def test_static_closure_cannot_pass_before_prior_terminal() -> None:
    catalog, adapter = baseline()
    adapter["scenarios"][0]["blocker"] = None
    with pytest.raises(subject.ContractError, match="MISSING_TV_MUST_BLOCK_PAIRED_ROW"):
        subject.build_bundle(adapter, catalog)


def test_static_closure_rejects_runtime_attempt_or_blocker() -> None:
    catalog, adapter = baseline()
    adapter["scenarios"][-1]["blocker"] = None
    with pytest.raises(subject.ContractError, match="STATIC_CLOSURE_INPUT_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_raw_identifier_like_value_is_rejected() -> None:
    catalog, adapter = baseline()
    adapter["run_id"] = "serial=123456789012"
    with pytest.raises(subject.ContractError):
        subject.build_bundle(adapter, catalog)


def test_report_tamper_cannot_hide_missing_tv_false_pass() -> None:
    catalog, adapter = baseline()
    bundle = subject.build_bundle(adapter, catalog)
    rows = scenario_rows(bundle)
    rows[0]["scenario_status"] = "observed_pass"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=subject.SCENARIO_LEDGER_HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    bundle[subject.SCENARIO_LEDGER_OUTPUT] = stream.getvalue().encode()
    report = report_from(bundle)
    artifact = next(item for item in report["artifacts"] if item["reference"] == subject._repo_reference(subject.SCENARIO_LEDGER_OUTPUT))
    artifact["sha256"] = subject._sha(bundle[subject.SCENARIO_LEDGER_OUTPUT])
    bundle[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    report["payload"]["scenario_summary"]["status_counts"]["blocked_by_device"] -= 1
    report["payload"]["scenario_summary"]["status_counts"]["observed_pass"] = 1
    bundle[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    with pytest.raises(subject.ContractError, match="REPORT_SUMMARY_RECONCILIATION_INVALID|REPORT_MISSING_TV_FALSE_PASS"):
        subject.validate_bundle(bundle, catalog=catalog)


def test_report_cannot_claim_pass_while_phone_coverage_is_blocked() -> None:
    catalog, adapter = baseline()
    bundle = subject.build_bundle(adapter, catalog)
    report = report_from(bundle)
    report["coverage_status"] = "covered"
    report["release_effect"] = "candidate_evidence"
    bundle[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    with pytest.raises(subject.ContractError, match="REPORT_COVERAGE_RECONCILIATION_INVALID"):
        subject.validate_bundle(bundle, catalog=catalog)


def test_preflight_requires_canonical_local_adapter_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "adapter.json"
    path.write_text(json.dumps(subject._baseline_adapter()), encoding="utf-8")
    assert subject.main(["--preflight", "--adapter-input", str(path)]) == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "ADAPTER_INPUT_PATH_INVALID"


def test_execute_requires_explicit_ingest_gate(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["--execute"]) == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "EXECUTE_GATE_REQUIRED"


def test_blocked_baseline_bundle_validates_in_memory() -> None:
    catalog, adapter = baseline()
    bundle = subject.build_bundle(adapter, catalog)
    subject.validate_bundle(bundle, catalog=catalog)
    assert len(bundle) == 6


def runtime_adapter() -> tuple[list[dict[str, str]], dict[str, object]]:
    source = subject._load_runtime_coverage_source()
    return subject.load_contract(), subject._adapter_from_runtime_coverage_source(source)


def test_runtime_source_yields_dynamic_closed_phone_ledger_without_paired_claim() -> None:
    catalog, adapter = runtime_adapter()
    bundle = subject.build_bundle(adapter, catalog)
    report = report_from(bundle)
    rows = scenario_rows(bundle)
    assert report["schema_version"] == "evidence-report-envelope-v2"
    assert report["production_safety_classification"] == "PROD_CONDITIONAL_PHONE_INDEPENDENT"
    assert "synthetic_session_fixture_not_verified" in report["blocked_reasons"]
    assert any(risk["id"] == "TASK045-RISK-002" for risk in report["risks"])
    assert report["payload"]["phone_inventory"] == {
        "closure": True,
        "branch_count": 26,
        "discovered_branch_count": 21,
        "approved_reachable_branch_count": 21,
    }
    assert report["payload"]["scenario_summary"]["status_counts"] == {
        "blocked_by_device": 19,
        "blocked_by_oracle": 2,
        "observed_pass": 1,
    }
    assert report["payload"]["paired_claim"] == "not_established"
    assert report["coverage_status"] == "partial_blocked"
    assert report["release_effect"] == "blocks_release"
    assert rows[-1]["scenario_status"] == "observed_pass"


def test_installed_newer_build_provenance_stays_separate_from_canonical_lane() -> None:
    catalog, adapter = runtime_adapter()
    report = report_from(subject.build_bundle(adapter, catalog))
    provenance = report["payload"]["build_provenance"]
    assert provenance["installed_lane_alias"] == "task045-phone-full-installed-newer-001"
    assert provenance["canonical_install_outcome"] == "blocked_version_downgrade"
    assert provenance["canonical_execution_outcome"] == "not_run"
    assert provenance["compatibility_evidence_status"] == "unknown"


@pytest.mark.parametrize("changes", [
    {"alias": "task045-phone-full-canonical-candidate"},
    {
        "alias": "task045-phone-full-canonical-candidate",
        "installed_lane_alias": "task045-phone-full-canonical-candidate",
    },
    {"canonical_bundle_alias": "task045-phone-full-installed-newer-001"},
])
def test_build_provenance_rejects_alias_substitution_or_lane_collapse(changes: dict[str, str]) -> None:
    catalog, adapter = runtime_adapter()
    adapter["build_ref"].update(changes)
    with pytest.raises(subject.ContractError, match="BUILD_PROVENANCE_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_runtime_source_build_alias_is_pinned_to_installed_newer_lane() -> None:
    source = copy.deepcopy(subject._load_runtime_coverage_source())
    source["build_set_alias"] = "task045-phone-full-canonical-candidate"
    with pytest.raises(subject.ContractError, match="COVERAGE_SOURCE_PROVENANCE_INVALID"):
        subject._adapter_from_runtime_coverage_source(source)


def test_runtime_anomaly_ledger_preserves_specific_first_failure_details() -> None:
    catalog, adapter = runtime_adapter()
    bundle = subject.build_bundle(adapter, catalog)
    rows = list(csv.DictReader(io.StringIO(bundle[subject.ANOMALY_OUTPUT].decode())))
    by_id = {row["anomaly_id"]: row for row in rows}
    assert len(rows) == len(adapter["inventory_anomalies"])
    assert by_id["TASK045-RUNTIME-ANOMALY-001"]["cause_category"] == "environment_build_state_mismatch"
    assert by_id["TASK045-RUNTIME-ANOMALY-001"]["observed_result_category"] == "version_downgrade_rejected"
    for anomaly_id in ("TASK045-RUNTIME-ANOMALY-002", "TASK045-RUNTIME-ANOMALY-004"):
        assert "partial_render" in by_id[anomaly_id]["observed_result_category"]
        assert "screenshot_xml_mismatch" in by_id[anomaly_id]["reason_code"]
    assert by_id["TASK045-RUNTIME-ANOMALY-003"]["reason_code"] == "external_keyboard_privacy_boundary"
    assert by_id["TASK045-PROCESS-ANOMALY-004"]["reason_code"] == "adb_pull_stderr_helper_failure"
    assert by_id["TASK045-PROCESS-ANOMALY-005"]["reason_code"] == "out_of_display_scroll_coordinates"
    assert by_id["TASK045-PROCESS-ANOMALY-006"]["reason_code"] == "null_pid_log_helper_gap"
    assert all(row["first_failure_retained"] == "true" for row in rows)


def test_adapter_schema_is_applied_to_entire_instance() -> None:
    catalog, adapter = baseline()
    adapter["unexpected_top_level"] = False
    with pytest.raises(subject.ContractError, match=r"SCHEMA_INSTANCE_INVALID:\$"):
        subject.build_bundle(adapter, catalog)


def test_only_primary_plus_one_recovery_is_allowed() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    scenario = adapter["scenarios"][5]
    scenario["attempts"].extend(copy.deepcopy(scenario["attempts"][0]) for _ in range(2))
    with pytest.raises(subject.ContractError, match="SCHEMA_INSTANCE_INVALID|ATTEMPT_BUDGET_EXCEEDED"):
        subject.build_bundle(adapter, catalog)


def test_observed_pass_requires_confirmed_fresh_evidence() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["scenarios"][5]["attempts"][0]["evidence_status"] = "likely"
    with pytest.raises(subject.ContractError, match="PASS_REQUIRES_CONFIRMED_EVIDENCE"):
        subject.build_bundle(adapter, catalog)


def test_observed_pass_requires_confirmed_successful_cleanup() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["cleanup"][0]["evidence_status"] = "likely"
    with pytest.raises(subject.ContractError, match="PASS_REQUIRES_CONFIRMED_CLEANUP"):
        subject.build_bundle(adapter, catalog)


def test_runtime_failure_has_precedence_over_static_blocker() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    scenario = adapter["scenarios"][5]
    attempt = scenario["attempts"][0]
    attempt["oracle_result"] = "fail"
    attempt["observed_state_alias"] = "unexpected_phone_state"
    scenario["blocker"] = {"status": "blocked_by_oracle", "reason_code": "secondary_static_blocker"}
    adapter["anomalies"].append({
        "anomaly_id": "anomaly-runtime-precedence", "scenario_id": "QA-045-006",
        "attempt_id": attempt["attempt_id"], "trigger_category": "launch_without_tv",
        "expected_result_category": "explicit_no_tv_state", "observed_result_category": "unexpected_phone_state",
        "public_safe_screen_alias": "phone_unexpected", "classification": "observed_fail",
        "evidence_status": "confirmed", "cause_evidence_status": "hypothesis",
        "cause_category": "runtime_state", "test_design_implication": "retain_first_failure",
        "first_failure_retained": True, "reason_code": "first_runtime_failure",
    })
    rows = scenario_rows(subject.build_bundle(adapter, catalog))
    assert rows[5]["scenario_status"] == "observed_fail"
    assert rows[5]["reason_code"] == "first_runtime_failure_retained"


def test_boundary_must_link_to_its_exact_attempt_and_scenario() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["boundaries"][0]["attempt_id"] = "attempt-nonexistent"
    with pytest.raises(subject.ContractError, match="BOUNDARY_LINK_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_hash_like_public_alias_is_rejected() -> None:
    catalog, adapter = baseline()
    adapter["run_id"] = "abcdef0123456789abcdef01"
    with pytest.raises(subject.ContractError, match="SAFE_ID_HASH_OR_RAW_IDENTIFIER_LIKE"):
        subject.build_bundle(adapter, catalog)


def test_dynamic_extra_out_of_scope_branch_is_supported() -> None:
    source = copy.deepcopy(subject._load_runtime_coverage_source())
    source["coverage"].append({
        "branch_alias": "phone-future-approved-catalog-surface",
        "status": "not_run_out_of_scope",
        "evidence_ids": [],
        "reason_code": "not_authorized_by_task045_catalog",
    })
    adapter = subject._adapter_from_runtime_coverage_source(source)
    report = report_from(subject.build_bundle(adapter, subject.load_contract()))
    assert report["payload"]["phone_inventory"]["branch_count"] == 27
    assert report["payload"]["phone_inventory"]["closure"] is True


def test_reachable_approved_branch_cannot_be_classified_out_of_scope() -> None:
    catalog, adapter = runtime_adapter()
    row = next(item for item in adapter["phone_coverage"] if item["status"] == "not_run_out_of_scope")
    row.update(approved_scope=True, declared_reachable=True)
    adapter["runtime_preflight"]["inventory_approved_reachable_branch_count"] += 1
    with pytest.raises(subject.ContractError, match="REACHABLE_APPROVED_BRANCH_NOT_TERMINAL"):
        subject.build_bundle(adapter, catalog)


def test_runtime_inventory_evidence_registry_is_exact_and_cleanup_confirmed() -> None:
    catalog, adapter = runtime_adapter()
    referenced = {evidence_id for row in adapter["phone_coverage"] for evidence_id in row["evidence_ids"]}
    assert referenced == set(adapter["inventory_evidence_ids"])
    report = report_from(subject.build_bundle(adapter, catalog))
    assert report["payload"]["inventory_cleanup_confirmed"] is True


def test_truncated_runtime_source_cannot_claim_full_inventory_closure() -> None:
    source = copy.deepcopy(subject._load_runtime_coverage_source())
    source["coverage"] = source["coverage"][:1]
    adapter = subject._adapter_from_runtime_coverage_source(source)
    assert adapter["runtime_preflight"]["inventory_declaration_complete"] is False
    assert adapter["scenarios"][-1]["blocker"] == {
        "status": "blocked_by_oracle",
        "reason_code": "phone_inventory_declaration_incomplete",
    }
    bundle = subject.build_bundle(adapter, subject.load_contract())
    assert report_from(bundle)["payload"]["phone_inventory"]["closure"] is False
    assert scenario_rows(bundle)[-1]["scenario_status"] == "blocked_by_oracle"


@pytest.mark.parametrize("required_flag", [
    "target_app_force_stopped", "home_restored", "existing_session_preserved",
])
def test_incomplete_inventory_cleanup_blocks_static_closure(required_flag: str) -> None:
    source = copy.deepcopy(subject._load_runtime_coverage_source())
    source["cleanup"][required_flag] = False
    adapter = subject._adapter_from_runtime_coverage_source(source)
    bundle = subject.build_bundle(adapter, subject.load_contract())
    report = report_from(bundle)
    assert report["payload"]["inventory_cleanup_confirmed"] is False
    assert report["payload"]["phone_inventory"]["closure"] is False
    assert scenario_rows(bundle)[-1]["reason_code"] == "phone_inventory_cleanup_incomplete"


def test_tampered_public_cleanup_cannot_coexist_with_static_closure_pass() -> None:
    catalog, adapter = runtime_adapter()
    bundle = subject.build_bundle(adapter, catalog)
    cleanup_rows = list(csv.DictReader(io.StringIO(bundle[subject.CLEANUP_OUTPUT].decode())))
    cleanup_rows[0].update(
        target_app_force_stopped="false", home_restored="false",
        existing_session_preserved="false", kill_switch_ready="false",
        rollback_verified="false", result="not_run",
    )
    bundle[subject.CLEANUP_OUTPUT] = subject._csv_bytes(subject.CLEANUP_HEADERS, cleanup_rows)
    report = report_from(bundle)
    cleanup_artifact = next(
        item for item in report["artifacts"]
        if item["reference"] == subject._repo_reference(subject.CLEANUP_OUTPUT)
    )
    cleanup_artifact["sha256"] = subject._sha(bundle[subject.CLEANUP_OUTPUT])
    report["payload"]["inventory_cleanup_confirmed"] = False
    bundle[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    with pytest.raises(subject.ContractError, match="REPORT_INVENTORY_CLOSURE_WITHOUT_CLEANUP"):
        subject.validate_bundle(bundle, catalog=catalog)


def test_generated_run_time_must_be_bound_to_attempt_and_modalities() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["generated_at_utc"] = "2030-08-15T10:02:00Z"
    with pytest.raises(subject.ContractError, match="RUN_EVIDENCE_FRESHNESS_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_generated_run_time_must_be_bound_to_timeline() -> None:
    catalog, adapter = baseline()
    add_independent_pass(adapter, "QA-045-006")
    adapter["paired_timeline"][0]["observed_at_utc"] = "2030-08-15T10:00:03Z"
    with pytest.raises(subject.ContractError, match="RUN_TIMELINE_FRESHNESS_INVALID"):
        subject.build_bundle(adapter, catalog)


def test_unverified_session_cannot_yield_session_dependent_coverage() -> None:
    catalog, adapter = runtime_adapter()
    assert adapter["runtime_preflight"]["session_provenance"] == "unknown_not_verified"
    assert adapter["runtime_preflight"]["session_dependent_evidence_eligible"] is False
    for row in adapter["phone_coverage"]:
        if row["branch_alias"] in subject.SESSION_DEPENDENT_BRANCHES:
            assert row["status"] == "blocked_by_external_state"
            assert row["reason_code"] == "synthetic_session_fixture_not_verified"
    row = next(
        item for item in adapter["phone_coverage"]
        if item["branch_alias"] in subject.SESSION_DEPENDENT_BRANCHES
    )
    row["status"] = "covered"
    with pytest.raises(subject.ContractError, match="UNVERIFIED_SESSION_CANNOT_YIELD_COVERAGE"):
        subject.build_bundle(adapter, catalog)

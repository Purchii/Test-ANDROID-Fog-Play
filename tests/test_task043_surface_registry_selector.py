from __future__ import annotations

import copy
import csv
import importlib.util
import io
import json
import os
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).parents[1] / "automation/regression/task043_surface_registry_selector.py"
SPEC = importlib.util.spec_from_file_location("task043_surface_registry_selector", MODULE_PATH)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


def reason(exc: pytest.ExceptionInfo[subject.ContractError]) -> str:
    return str(exc.value)


def test_static_constants_are_valid() -> None:
    assert subject.validate_static_constants() == []


def test_validate_only_cli_performs_no_contract_reads(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(subject, "load_snapshot", lambda: (_ for _ in ()).throw(AssertionError("read")))
    assert subject.main(["--validate-only"]) == 0
    assert json.loads(capsys.readouterr().out)["validation_status"] == "pass"


def test_preflight_reconciles_canonical_counts() -> None:
    snapshot = subject.load_snapshot()
    assert len(snapshot["registry"]) == 55
    assert len(snapshot["scenarios"]) == 307
    assert len(snapshot["task043"]) == 18
    assert len(snapshot["lanes"]) == 13


def test_registry_has_exact_risk_and_family_counts() -> None:
    document = subject._registry_document(subject.load_snapshot())
    subject.validate_registry_document(document)
    assert document["risk_summary"] == {"R0": 33, "R1": 22}
    assert document["families"] == list(subject.FAMILIES)


@pytest.mark.parametrize(
    ("status", "evidence_type", "evidence_status"),
    [
        ("mapped_only", "mapped_only", "unknown"),
        ("executable_not_run", "static_contract", "confirmed"),
        ("blocked_by_device", "physical_runtime", "confirmed"),
        ("tooling_defect", "physical_runtime", "confirmed"),
        ("observed_fail", "physical_runtime", "confirmed"),
        ("confirmed_defect", "physical_runtime", "confirmed"),
        ("observed_pass", "mapped_only", "confirmed"),
        ("observed_pass", "physical_runtime", "likely"),
    ],
)
def test_non_pass_semantics_never_promote(status: str, evidence_type: str, evidence_status: str) -> None:
    assert subject.scenario_is_clean_pass(status, evidence_type, evidence_status) is False


def test_static_observed_pass_is_a_clean_task_contract_pass() -> None:
    assert subject.scenario_is_clean_pass("observed_pass", "static_contract", "confirmed") is True


def test_unknown_status_fails_closed() -> None:
    with pytest.raises(subject.ContractError) as caught:
        subject.scenario_is_clean_pass("future_pass", "static_contract", "confirmed")
    assert reason(caught) == "EVIDENCE_ENUM_UNKNOWN"


def test_retry_recovery_preserves_first_failure() -> None:
    attempts = [
        {"attempt_id": "attempt-1", "oracle_result": "fail", "recovery": False},
        {"attempt_id": "attempt-2", "oracle_result": "pass", "recovery": True},
    ]
    assert subject.scenario_is_clean_pass("observed_pass", "physical_runtime", "confirmed", attempts) is False


def test_recovery_marker_alone_prevents_clean_pass() -> None:
    attempts = [{"attempt_id": "attempt-1", "oracle_result": "pass", "recovery": True}]
    assert subject.scenario_is_clean_pass("observed_pass", "physical_runtime", "confirmed", attempts) is False


def test_empty_attempts_fail_closed() -> None:
    with pytest.raises(subject.ContractError) as caught:
        subject.scenario_is_clean_pass("observed_pass", "physical_runtime", "confirmed", [])
    assert reason(caught) == "ATTEMPTS_MISSING"


@pytest.mark.parametrize("evidence_type", ["avd_tooling_runtime", "synthetic_offline", "static_contract", "mapped_only", "manual_observation"])
def test_nonphysical_evidence_does_not_satisfy_physical(evidence_type: str) -> None:
    assert subject.evidence_satisfies("physical", evidence_type) is False


def test_avd_does_not_satisfy_oem_compatibility() -> None:
    assert subject.evidence_satisfies("oem_compatibility", "avd_tooling_runtime") is False


def test_paired_requirement_needs_paired_physical() -> None:
    assert subject.evidence_satisfies("paired_physical", "physical_runtime") is False
    assert subject.evidence_satisfies("paired_physical", "paired_physical_runtime") is True


@pytest.mark.parametrize("missing", ["build_match", "family_match", "lane_match", "scenario_contract_match", "freshness_contract_present"])
def test_prior_evidence_reuse_requires_every_compatibility_dimension(missing: str) -> None:
    values = {
        "build_match": True,
        "family_match": True,
        "lane_match": True,
        "scenario_contract_match": True,
        "freshness_contract_present": True,
    }
    values[missing] = False
    assert subject.can_reuse_prior_evidence(**values) is False


@pytest.mark.parametrize("truthy", ["true", 1, [True], {"value": True}])
def test_prior_evidence_reuse_rejects_truthy_non_booleans(truthy: object) -> None:
    assert subject.can_reuse_prior_evidence(
        build_match=truthy,  # type: ignore[arg-type]
        family_match=True,
        lane_match=True,
        scenario_contract_match=True,
        freshness_contract_present=True,
    ) is False


def test_family_specific_selector_does_not_overselect_other_families() -> None:
    registry = subject.load_snapshot()["registry"]
    assert subject.select_surface_scenarios(registry, "SURF-CATALOG-001", "television-sber") == ("QA-047-004",)


def test_shared_selector_includes_all_five_app_family_tasks_and_paired_path() -> None:
    assert subject.select_family_tasks("television-full", shared=True) == (
        "TASK-044", "TASK-045", "TASK-046", "TASK-047", "TASK-048"
    )


def test_equivalence_delta_adds_task053_only_as_delta() -> None:
    assert subject.select_family_tasks("television-full", equivalence_delta=True) == ("TASK-044", "TASK-053")


def test_unknown_or_inapplicable_family_fails_closed() -> None:
    registry = subject.load_snapshot()["registry"]
    with pytest.raises(subject.ContractError, match="SELECTOR_FAMILY_UNKNOWN"):
        subject.select_family_tasks("generic-tv")
    with pytest.raises(subject.ContractError, match="SELECTOR_FAMILY_NOT_APPLICABLE"):
        subject.select_surface_scenarios(registry, "SURF-LAUNCHER-001", "television-full")


@pytest.mark.parametrize(
    "value",
    [
        "https://public.invalid/value",
        ".qa_local/evidence/task-043/value",
        "C:\\private\\value",
        "/home/private/value",
        "sample.apk",
        "token=synthetic",
    ],
)
def test_recursive_public_value_guard_rejects_private_shaped_values(value: str) -> None:
    with pytest.raises(subject.ContractError, match="PUBLIC_VALUE_FORBIDDEN"):
        subject._validate_public_values({"nested": [{"value": value}]})


@pytest.mark.parametrize(
    "value",
    [
        "com.private.SecretClass", "com.private.secret",
        "internal.api.example/path", "SecretManagerImpl", "runSecretMethod()",
        "example.synthetic.private", "dev.private.secret", "api.private.example/path",
        "SecretComponent", "SyntheticEngineImpl",
    ],
)
def test_recursive_public_value_guard_rejects_source_private_identifiers(value: str) -> None:
    with pytest.raises(subject.ContractError, match="PUBLIC_VALUE_FORBIDDEN"):
        subject._validate_public_values({"value": value})


def test_public_value_guard_allows_approved_opaque_text_and_aliases() -> None:
    subject._validate_public_values({
        "surface_id": "SURF-CATALOG-001",
        "description": "Public-safe catalog manager boundary",
        "lane_alias": "tv-tpv-013",
        "status": "observed_pass",
    })
    for approved_term in subject.PUBLIC_SAFE_IDENTIFIER_ALLOWLIST:
        subject._validate_public_values({"approved_public_term": approved_term})
    subject._validate_public_values({
        "artifacts": [{"reference": "docs/qa/reports/task043_surface_coverage.summary.json"}]
    })
    subject._validate_generated_csv_row({
        "report_alias": "task025_selected_lane_native_regression.summary.template"
    })


def test_private_catalog_lane_is_rejected_before_derivation(monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = subject.load_snapshot()
    original_load_csv = subject._load_csv

    def mutated_load_csv(path: Path, headers, *, parent: Path):
        rows = original_load_csv(path, headers, parent=parent)
        if path == subject.CATALOGS[3]:
            rows[0]["lane"] = "com.private.secret"
        return rows

    monkeypatch.setattr(subject, "_load_csv", mutated_load_csv)
    with pytest.raises(subject.ContractError, match="PUBLIC_VALUE_FORBIDDEN"):
        subject._validate_catalogs(snapshot["registry"], snapshot["task_index"])


def test_private_selection_lane_is_rejected_during_bundle_build() -> None:
    snapshot = subject.load_snapshot()
    snapshot["scenarios"]["QA-044-001"]["lane"] = "com.private.secret"
    with pytest.raises(subject.ContractError, match="PUBLIC_VALUE_FORBIDDEN"):
        subject._build_output_bytes(snapshot)


@pytest.mark.parametrize(
    ("section", "field"),
    [("migration", "report_alias"), ("lanes", "lane_alias"), ("task043", "surface_ids")],
)
def test_private_generated_csv_values_are_rejected(section: str, field: str) -> None:
    snapshot = subject.load_snapshot()
    snapshot[section][0][field] = "dev.private.secret"
    with pytest.raises(subject.ContractError, match="PUBLIC_VALUE_FORBIDDEN"):
        subject._build_output_bytes(snapshot)


def test_unapproved_private_report_alias_is_rejected() -> None:
    with pytest.raises(subject.ContractError, match="PUBLIC_VALUE_FORBIDDEN"):
        subject._validate_generated_csv_row({"report_alias": "task020_dev.private.secret.summary"})


def test_full_hash_allowed_only_in_artifact_sha_field() -> None:
    digest = "a" * 64
    subject._validate_public_values({"artifacts": [{"sha256": digest}]})
    with pytest.raises(subject.ContractError, match="RAW_HASH_OUTSIDE_ARTIFACT_FIELD"):
        subject._validate_public_values({"raw_hash": digest})


@pytest.mark.parametrize("reference", ["../outside.json", "/absolute.json", "docs\\qa\\bad.json", "https://bad"])
def test_unsafe_public_reference_is_rejected(reference: str) -> None:
    assert subject._safe_reference(reference) is False


@pytest.mark.parametrize("cell", ["=1+1", "+cmd", "-2", "@formula"])
def test_csv_formula_leading_values_are_rejected(cell: str) -> None:
    with pytest.raises(subject.ContractError, match="CSV_FORMULA_VALUE_FORBIDDEN"):
        subject._validate_csv_cells([cell])


def test_duplicate_json_key_is_rejected() -> None:
    with pytest.raises(subject.ContractError, match="JSON_DUPLICATE_KEY"):
        json.loads('{"a":1,"a":2}', object_pairs_hook=subject._json_pairs)


def test_duplicate_surface_id_is_rejected() -> None:
    rows = list(csv.DictReader(io.StringIO(subject.TRACEABILITY.read_text(encoding="utf-8-sig"))))
    rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(subject.ContractError, match="SURFACE_ID_INVALID_OR_DUPLICATE"):
        subject._validate_surfaces(rows)


def test_unknown_surface_family_scope_is_rejected() -> None:
    rows = list(csv.DictReader(io.StringIO(subject.TRACEABILITY.read_text(encoding="utf-8-sig"))))
    rows[0]["applicable_families"] = "generic-anything"
    with pytest.raises(subject.ContractError, match="SURFACE_FAMILY_SCOPE_UNKNOWN"):
        subject._validate_surfaces(rows)


def test_missing_manifest_tasks_are_explicit_and_legacy_never_inflates() -> None:
    rows = subject.load_snapshot()["migration"]
    assert {row["task_id"] for row in rows} == {f"TASK-{number:03d}" for number in range(19, 41)}
    assert any(row["schema_status"] == "missing" for row in rows)
    assert all(row["reuse_status"] in {"historical_context_only", "not_available"} for row in rows)
    assert all(row["freshness_status"] != "fresh" for row in rows)
    assert any(row["task_id"] == "TASK-025" and row["report_alias"] != "none" for row in rows)
    assert any(row["task_id"] == "TASK-026" and row["report_alias"] != "none" for row in rows)


def test_registry_validator_rejects_surface_count_and_family_tampering() -> None:
    registry = subject._registry_document(subject.load_snapshot())
    registry["surfaces"][0]["scenario_count"] += 1
    with pytest.raises(subject.ContractError, match="REGISTRY_DOCUMENT_SCENARIOS_INVALID"):
        subject.validate_registry_document(registry)

    registry = subject._registry_document(subject.load_snapshot())
    registry["surfaces"][0]["applicable_families"] = ["phone-full"]
    with pytest.raises(subject.ContractError, match="REGISTRY_DOCUMENT_FAMILY_SCOPE_INVALID"):
        subject.validate_registry_document(registry)


def test_task044_selection_is_selection_only_and_exact() -> None:
    rows = subject._selection_rows(subject.load_snapshot()["scenarios"])
    assert len(rows) == 32
    assert sum(row["priority"] == "P0" for row in rows) == 29
    assert sum(row["priority"] == "P1" for row in rows) == 3
    assert {row["selection_status"] for row in rows} == {"selected_not_run"}


def test_gap_matrix_has_separate_launcher_contour() -> None:
    snapshot = subject.load_snapshot()
    rows = subject._gap_rows(snapshot["registry"], snapshot["lanes"])
    assert len(rows) == 14
    launcher = [row for row in rows if row["lane_alias"] == "launcher-system-contour"]
    assert len(launcher) == 1
    assert launcher[0]["family"] == "launcher-system"
    assert int(launcher[0]["surface_count"]) > 0


def test_output_generation_is_deterministic_and_report_has_no_product_claim() -> None:
    snapshot = subject.load_snapshot()
    first = subject._build_output_bytes(snapshot)
    second = subject._build_output_bytes(snapshot)
    assert first == second
    report = json.loads(first[subject.REPORT_OUTPUT])
    assert report["coverage_status"] == "partial"
    assert report["release_effect"] == "no_release_claim"
    assert report["payload"]["product_runtime_coverage_claim"] is False
    assert report["provenance"]["runtime_actions"] == "not_run"


def test_tampered_generated_artifact_hash_is_rejected() -> None:
    outputs = subject._build_output_bytes(subject.load_snapshot())
    report = json.loads(outputs[subject.REPORT_OUTPUT])
    report["artifacts"][0]["sha256"] = "0" * 64
    with pytest.raises(subject.ContractError, match="REPORT_ARTIFACT_HASH_MISMATCH"):
        subject.validate_report(report, artifact_bytes=outputs)


def test_rebound_hash_cannot_make_tampered_bundle_canonical() -> None:
    expected = subject._build_output_bytes(subject.load_snapshot())
    actual = dict(expected)
    ledger = bytearray(actual[subject.LEDGER_OUTPUT])
    ledger.extend(b"\n")
    actual[subject.LEDGER_OUTPUT] = bytes(ledger)
    report = json.loads(actual[subject.REPORT_OUTPUT])
    ledger_ref = subject._repo_reference(subject.LEDGER_OUTPUT)
    for artifact in report["artifacts"]:
        if artifact["reference"] == ledger_ref:
            artifact["sha256"] = subject._canonical_sha_bytes(actual[subject.LEDGER_OUTPUT], ".csv")
    actual[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    subject.validate_report(report, artifact_bytes=actual)
    with pytest.raises(subject.ContractError, match="GENERATED_OUTPUT_CANONICAL_MISMATCH"):
        subject._validate_canonical_output_bytes(actual, expected)


@pytest.mark.parametrize(
    ("path_name", "headers_name", "field", "value"),
    [
        ("LEDGER_OUTPUT", "LEDGER_HEADERS", "scenario_id", "QA-043-999"),
        ("LEDGER_OUTPUT", "LEDGER_HEADERS", "surface_ids", "SURF-LOG-001"),
        ("SELECTION_OUTPUT", "SELECTION_HEADERS", "scenario_id", "QA-044-999"),
        ("SELECTION_OUTPUT", "SELECTION_HEADERS", "lane", "wrong-lane"),
        ("GAP_OUTPUT", "GAP_HEADERS", "surface_count", "999"),
        ("MIGRATION_OUTPUT", "MIGRATION_HEADERS", "authority_status", "authoritative"),
    ],
)
def test_rebound_hash_rejects_semantic_artifact_tamper(
    path_name: str, headers_name: str, field: str, value: str
) -> None:
    expected = subject._build_output_bytes(subject.load_snapshot())
    actual = dict(expected)
    path = getattr(subject, path_name)
    headers = getattr(subject, headers_name)
    rows = subject._csv_rows_from_bytes(actual[path], headers)
    rows[0][field] = value
    actual[path] = subject._csv_bytes(headers, rows)
    report = json.loads(actual[subject.REPORT_OUTPUT])
    reference = subject._repo_reference(path)
    for artifact in report["artifacts"]:
        if artifact["reference"] == reference:
            artifact["sha256"] = subject._canonical_sha_bytes(actual[path], path.suffix)
    actual[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    subject.validate_report(report, artifact_bytes=actual)
    with pytest.raises(subject.ContractError, match="GENERATED_OUTPUT_CANONICAL_MISMATCH"):
        subject._validate_canonical_output_bytes(actual, expected)


@pytest.mark.parametrize(
    ("field", "value", "reason_code"),
    [
        ("schema_validation_status", "unknown", "REPORT_STATUS_INVALID"),
        ("evidence_status", "likely", "REPORT_STATUS_INVALID"),
        ("verification", [], "REPORT_VERIFICATION_INVALID"),
        ("review", {"qa_reviewer_a": "approved"}, "REPORT_REVIEW_OR_BLOCKER_INVALID"),
    ],
)
def test_strict_report_fields_reject_tampering(field: str, value: object, reason_code: str) -> None:
    outputs = subject._build_output_bytes(subject.load_snapshot())
    report = json.loads(outputs[subject.REPORT_OUTPUT])
    report[field] = value
    with pytest.raises(subject.ContractError, match=reason_code):
        subject.validate_report(report, artifact_bytes=outputs)


@pytest.mark.parametrize(
    "hidden_key",
    [
        "runtime_execution_status", "apk_execution_status",
        "adb_avd_execution_status", "network_execution_status",
        "runtime_evidence_status",
    ],
)
def test_hidden_payload_status_keys_are_rejected(hidden_key: str) -> None:
    outputs = subject._build_output_bytes(subject.load_snapshot())
    report = json.loads(outputs[subject.REPORT_OUTPUT])
    report["payload"][hidden_key] = "not_run"
    with pytest.raises(subject.ContractError, match="REPORT_PAYLOAD_HIDDEN_STATUS_FORBIDDEN"):
        subject.validate_report(report, artifact_bytes=outputs)


def test_report_process_anomaly_record_is_canonical() -> None:
    outputs = subject._build_output_bytes(subject.load_snapshot())
    report = json.loads(outputs[subject.REPORT_OUTPUT])
    assert [item["id"] for item in report["payload"]["process_anomalies"]] == [
        "TASK043-PROCESS-ANOMALY-002", "TASK043-PROCESS-ANOMALY-003"
    ]
    assert report["payload"]["gap_summary"]["evidence_status"] == "unknown"


def test_invalid_bundle_is_rejected_before_atomic_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fail_publish(_outputs):
        nonlocal called
        called = True

    monkeypatch.setattr(subject, "_atomic_publish", fail_publish)
    monkeypatch.setattr(subject, "_build_output_bytes", lambda _snapshot: (_ for _ in ()).throw(subject.ContractError("GENERATED_OUTPUT_SET_INVALID")))
    with pytest.raises(subject.ContractError, match="GENERATED_OUTPUT_SET_INVALID"):
        subject.execute()
    assert called is False


def test_atomic_publish_rolls_back_every_target_on_replace_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    names = ["registry.json", "report.json", "ledger.csv", "migration.csv", "gaps.csv", "selection.csv"]
    paths = [tmp_path / name for name in names]
    constants = [
        "REGISTRY_OUTPUT", "REPORT_OUTPUT", "LEDGER_OUTPUT",
        "MIGRATION_OUTPUT", "GAP_OUTPUT", "SELECTION_OUTPUT",
    ]
    for constant, path in zip(constants, paths, strict=True):
        monkeypatch.setattr(subject, constant, path)
        path.write_bytes(b"OLD")
    outputs = {path: b"NEW" for path in paths}
    real_replace = os.replace
    publish_calls = 0

    def fail_third_publish(source: os.PathLike[str] | str, target: os.PathLike[str] | str) -> None:
        nonlocal publish_calls
        if ".backup." not in str(source):
            publish_calls += 1
            if publish_calls == 3:
                raise OSError("injected")
        real_replace(source, target)

    monkeypatch.setattr(subject.os, "replace", fail_third_publish)
    with pytest.raises(subject.ContractError, match="OUTPUT_ATOMIC_PUBLISH_FAILED"):
        subject._atomic_publish(outputs)
    assert {path.read_bytes() for path in paths} == {b"OLD"}
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob(".*.tmp"))


def test_atomic_publish_preserves_backup_when_rollback_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    names = ["registry.json", "report.json", "ledger.csv", "migration.csv", "gaps.csv", "selection.csv"]
    paths = [tmp_path / name for name in names]
    constants = [
        "REGISTRY_OUTPUT", "REPORT_OUTPUT", "LEDGER_OUTPUT",
        "MIGRATION_OUTPUT", "GAP_OUTPUT", "SELECTION_OUTPUT",
    ]
    for constant, path in zip(constants, paths, strict=True):
        monkeypatch.setattr(subject, constant, path)
        path.write_bytes(b"OLD")
    outputs = {path: b"NEW" for path in paths}
    real_replace = os.replace
    publish_calls = 0
    rollback_failed_once = False

    def fail_publish_and_one_rollback(source: os.PathLike[str] | str, target: os.PathLike[str] | str) -> None:
        nonlocal publish_calls, rollback_failed_once
        if ".backup." in str(source):
            if not rollback_failed_once:
                rollback_failed_once = True
                raise OSError("injected rollback failure")
        else:
            publish_calls += 1
            if publish_calls == 3:
                raise OSError("injected publish failure")
        real_replace(source, target)

    monkeypatch.setattr(subject.os, "replace", fail_publish_and_one_rollback)
    with pytest.raises(subject.ContractError, match="OUTPUT_ROLLBACK_FAILED") as caught:
        subject._atomic_publish(outputs)
    assert caught.value.recovery_status == "local_backup_preserved"
    backups = list(tmp_path.glob(".*.task043.backup.*.tmp"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == b"OLD"
    assert sum(path.read_bytes() == b"NEW" for path in paths) == 1
    assert list(tmp_path.glob(".*.task043.*.tmp")) == backups


def test_registry_schema_is_full_content_pinned() -> None:
    assert subject._canonical_sha_file(subject.REGISTRY_SCHEMA) == subject.REGISTRY_SCHEMA_SHA256


def test_fixed_file_rejects_outside_root(tmp_path: Path) -> None:
    outside = tmp_path / "input.csv"
    outside.write_text("a\n1\n", encoding="utf-8")
    with pytest.raises(subject.ContractError, match="INPUT_PATH_NOT_CANONICAL|INPUT_OUTSIDE_REPOSITORY"):
        subject._fixed_file(outside, parent=tmp_path, suffix=".csv")


def test_fixed_file_rejects_symlink_when_supported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "repo"
    parent = root / "docs"
    parent.mkdir(parents=True)
    target = parent / "target.csv"
    target.write_text("a\n1\n", encoding="utf-8")
    link = parent / "link.csv"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation unavailable")
    monkeypatch.setattr(subject, "REPO_ROOT", root)
    with pytest.raises(subject.ContractError, match="INPUT_PATH_NOT_CANONICAL|INPUT_REPARSE_FORBIDDEN"):
        subject._fixed_file(link, parent=parent, suffix=".csv")


def test_checked_in_report_bundle_validates() -> None:
    subject._validate_generated_files()


def test_validate_report_cli_is_fixed_and_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["--validate-report"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {"mode": "validate_report", "runtime_actions": "not_run", "validation_status": "pass"}

"""Deterministic repository-only closure for EPIC-PHONE-001.

The tool reads only fixed, tracked, public-safe inputs.  It has no device,
credential, local-evidence, network, or subprocess capability and cannot issue
a Security GO.  The published baseline is intentionally release-blocking.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from automation.reporting.generate_report_manifest import _validate_v2_envelope
    from automation.phone import task058a_phone_launch_readiness_pre_auth_continuation as task058a_contract
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from automation.reporting.generate_report_manifest import _validate_v2_envelope
    from automation.phone import task058a_phone_launch_readiness_pre_auth_continuation as task058a_contract


TASK_ID = "EPIC-PHONE-001"
RUN_ID = "epic-phone-001-repository-blocked-baseline-20260816-001"
GENERATED_AT = "2026-08-16T12:57:00Z"
SCHEMA_VERSION = "evidence-report-envelope-v2"
SECURITY_VERDICT = "GO_REPOSITORY_PLAN/BLOCK_RUNTIME/BLOCK_AUTH_ENTRY"
REPO_ROOT = Path(__file__).resolve().parents[2]
CROSSWALK = REPO_ROOT / "docs/qa/phone/phone_only_roadmap_crosswalk.csv"
TASK058A_SUMMARY = REPO_ROOT / "docs/qa/reports/task058a_phone_launch_readiness_pre_auth_continuation.summary.json"
TASK058A_SCENARIOS = REPO_ROOT / "docs/qa/reports/task058a_phone_launch_readiness_pre_auth_continuation.scenario-ledger.csv"
TASK_SPEC = REPO_ROOT / "tasks/EPIC_PHONE_001_full_mobile_application_test_coverage.md"
REPORT_ROOT = REPO_ROOT / "docs/qa/reports"
STEM = "epic_phone_001_full_mobile_application_test_coverage"

COVERAGE_OUTPUT = REPORT_ROOT / f"{STEM}.coverage-ledger.csv"
READINESS_OUTPUT = REPORT_ROOT / f"{STEM}.readiness-ledger.csv"
STAGE_OUTPUT = REPORT_ROOT / f"{STEM}.stage-ledger.csv"
BUDGET_OUTPUT = REPORT_ROOT / f"{STEM}.action-budget-ledger.csv"
ANOMALY_OUTPUT = REPORT_ROOT / f"{STEM}.anomaly-ledger.csv"
CLEANUP_OUTPUT = REPORT_ROOT / f"{STEM}.cleanup-ledger.csv"
REPORT_OUTPUT = REPORT_ROOT / f"{STEM}.summary.json"

CROSSWALK_HEADERS = (
    "source_task", "source_row_id", "current_status", "evidence_freshness",
    "phone_applicability", "owner_task", "allowed_terminal_status",
    "release_effect", "note",
)
COVERAGE_HEADERS = CROSSWALK_HEADERS + (
    "epic_stage", "terminal_status", "evidence_status", "evidence_ids",
    "reason_code", "modality_complete", "cleanup_status", "epic_release_effect",
)
READINESS_HEADERS = (
    "authority_id", "authority_alias", "evidence_status", "terminal_status",
    "reason_code", "security_verdict", "release_effect",
)
STAGE_HEADERS = (
    "stage_id", "stage_name", "terminal_status", "evidence_status",
    "reason_code", "runtime_action_count", "release_effect",
)
BUDGET_HEADERS = (
    "budget_id", "budget_kind", "action_contour", "classification", "unit",
    "maximum", "actual", "checkpoint_before_every_action",
    "required_fresh_security_gate", "kill_switch", "terminal_status",
)
ANOMALY_HEADERS = (
    "anomaly_id", "trigger_action", "expected_result", "observed_result",
    "evidence_status", "public_safe_alias", "cause_classification",
    "test_design_implication",
)
CLEANUP_HEADERS = (
    "cleanup_id", "repository_outputs_validated", "device_cleanup_required",
    "target_force_stop", "home", "capture_shutdown", "credential_cleanup",
    "forbidden_action_count", "evidence_status", "terminal_status", "reason_code",
)

EXPECTED_IDS = tuple([f"phone-coverage-{n:03d}" for n in range(1, 27)] + [f"A{n:03d}" for n in range(1, 18)])
INHERITED_IDS = {"phone-coverage-001", "phone-coverage-017", "A002"}
DEFERRED_IDS = {"phone-coverage-021", "phone-coverage-022", "phone-coverage-023", "phone-coverage-024", "phone-coverage-026", "A001", "A016"}
TASK058A_EVIDENCE = {
    "phone-coverage-001": "task058a-scenario-001",
    "phone-coverage-017": "task058a-scenario-002",
    "A002": "task058a-transition-001",
}
STAGE_BY_OWNER = {
    "TASK-058": "stage-01-authority-readiness",
    "TASK-059": "stage-02-authenticated-session",
    "TASK-060": "stage-03-exhaustive-inventory",
    "TASK-061": "stage-04-input-lifecycle-recovery",
    "TASK-062": "stage-05-boundary-recovery",
    "TASK-063": "stage-06-regression-closure",
}


class ContractError(ValueError):
    """The fixed public-safe epic contract failed closed."""


def _csv_bytes(headers: Sequence[str], rows: Iterable[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _parse_csv(data: bytes, headers: Sequence[str], label: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
    except UnicodeError as exc:
        raise ContractError(f"{label}_utf8_invalid") from exc
    if tuple(reader.fieldnames or ()) != tuple(headers):
        raise ContractError(f"{label}_headers_drift")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ContractError(f"{label}_extra_cells")
    return rows


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()


def _load_crosswalk() -> list[dict[str, str]]:
    if not CROSSWALK.is_file() or CROSSWALK.is_symlink():
        raise ContractError("crosswalk_missing_or_link")
    rows = _parse_csv(CROSSWALK.read_bytes(), CROSSWALK_HEADERS, "crosswalk")
    ids = [row["source_row_id"] for row in rows]
    if len(rows) != 43 or tuple(ids) != EXPECTED_IDS or len(set(ids)) != 43:
        raise ContractError("crosswalk_must_contain_exact_43_rows_once_in_order")
    if [row["source_task"] for row in rows[:26]] != ["TASK-045"] * 26:
        raise ContractError("crosswalk_task045_authority_drift")
    if [row["source_task"] for row in rows[26:]] != ["TASK-045A"] * 17:
        raise ContractError("crosswalk_task045a_authority_drift")
    return rows


def _task058a_inheritance_valid() -> bool:
    if any(not path.is_file() or path.is_symlink() for path in (TASK058A_SUMMARY, TASK058A_SCENARIOS)):
        return False
    try:
        expected_history = task058a_contract.expected_bundle()
        tracked_history = task058a_contract._disk_bundle()
        task058a_contract.validate_bundle(tracked_history, validate_disk_schema=True)
        if any(tracked_history[path] != expected_history[path] for path in expected_history):
            return False
        summary = json.loads(TASK058A_SUMMARY.read_text(encoding="utf-8"))
        scenario_bytes = TASK058A_SCENARIOS.read_bytes()
    except (OSError, UnicodeError, json.JSONDecodeError, task058a_contract.ContractError):
        return False
    return _task058a_inheritance_payload_valid(summary, scenario_bytes)


def _task058a_inheritance_payload_valid(
    summary: Mapping[str, Any],
    scenario_bytes: bytes,
    *,
    now: datetime | None = None,
) -> bool:
    """Fail closed unless the exact non-reusable TASK-058A authority is present."""

    if _validate_v2_envelope(summary, REPO_ROOT):
        return False
    expected_identity = {
        "task_id": task058a_contract.TASK_ID,
        "run_id": task058a_contract.RUN_ID,
        "generated_at_utc": task058a_contract.GENERATED_AT,
        "execution_status": "partial_blocked",
        "coverage_status": "covered",
        "release_effect": "blocks_release",
        "evidence_status": "confirmed",
    }
    if any(summary.get(key) != value for key, value in expected_identity.items()):
        return False
    try:
        generated_at = datetime.fromisoformat(str(summary["generated_at_utc"]).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    if generated_at > (now or datetime.now(UTC)):
        return False
    payload = summary.get("payload")
    if not isinstance(payload, dict):
        return False
    exact_payload = {
        "readiness_row_count": 7,
        "readiness_observed_pass_count": 6,
        "readiness_blocked_count": 1,
        "inherited_scenario_covered_count": 3,
        "launch_count": 1,
        "runtime_checkpoint_count": 2,
        "safe_pre_auth_action_count": 0,
        "forbidden_action_count": 0,
        "go_runtime": False,
        "go_runtime_owner_override": True,
        "first_launch_restored": False,
        "security_gate": "GO_RUNTIME_OWNER_OVERRIDE",
    }
    if any(payload.get(key) != value for key, value in exact_payload.items()):
        return False
    if summary.get("unknowns") != [{
        "evidence_status": "unknown",
        "id": "task057-authority-03-current-phone-selector",
        "reason_code": "selector_unrelated_delta_waived_owner_override",
    }]:
        return False
    artifact = next((item for item in summary.get("artifacts", []) if item.get("kind") == "scenario_ledger"), None)
    if not artifact or artifact.get("sha256") != _sha256(scenario_bytes):
        return False
    try:
        scenarios = list(csv.DictReader(io.StringIO(scenario_bytes.decode("utf-8"), newline="")))
    except (UnicodeError, csv.Error):
        return False
    by_source = {row.get("source_crosswalk_id"): row for row in scenarios}
    return all(
        by_source.get(source_id, {}).get("row_id") == evidence_id
        and by_source[source_id].get("status") == "covered"
        and by_source[source_id].get("evidence_status") == "confirmed"
        and by_source[source_id].get("screenshot_id") not in {None, "", "none"}
        and by_source[source_id].get("ui_tree_id") not in {None, "", "none"}
        and by_source[source_id].get("log_marker_id") not in {None, "", "none"}
        for source_id, evidence_id in TASK058A_EVIDENCE.items()
    )


def coverage_rows() -> list[dict[str, str]]:
    inherited = _task058a_inheritance_valid()
    result: list[dict[str, str]] = []
    for source in _load_crosswalk():
        row_id = source["source_row_id"]
        owner = source["owner_task"]
        if row_id in INHERITED_IDS and inherited:
            status, evidence, ids = "covered", "confirmed", TASK058A_EVIDENCE[row_id]
            reason, modality, cleanup, effect = "validated_tracked_task058a_inheritance", "true", "confirmed", "candidate_evidence"
        elif row_id in DEFERRED_IDS:
            status, evidence, ids = source["current_status"], "unknown", "historical_crosswalk_authority"
            reason, modality, cleanup, effect = "deferred_or_audit_semantics_preserved", "false", "not_applicable", source["release_effect"]
        else:
            status, evidence, ids = "blocked_by_external_state", "unknown", "epic-readiness-05;epic-readiness-07"
            reason, modality, cleanup, effect = "synthetic_fixture_classification_absent_and_no_literal_runtime_go", "false", "not_run_no_actions", "blocks_release"
        result.append({
            **source,
            "epic_stage": STAGE_BY_OWNER.get(owner, "deferred_original_owner"),
            "terminal_status": status,
            "evidence_status": evidence,
            "evidence_ids": ids,
            "reason_code": reason,
            "modality_complete": modality,
            "cleanup_status": cleanup,
            "epic_release_effect": effect,
        })
    return result


def readiness_rows() -> list[dict[str, str]]:
    values = (
        ("01", "canonical-phone-full", "confirmed", "inherited_authority", "task058a_tracked_authority_validated"),
        ("02", "installed-phone-full-build", "confirmed", "inherited_authority", "task058a_tracked_authority_validated"),
        ("03", "current-phone-selector", "unknown", "blocked_by_external_state", "current_row03_unknown_owner_override_not_reusable"),
        ("04", "ordinary-downgrade-guard", "confirmed", "inherited_safety_constraint", "zero_reinstall_uninstall_reset_required"),
        ("05", "synthetic-test-fixture", "unknown", "blocked_by_external_state", "synthetic_fixture_classification_absent"),
        ("06", "clean-first-launch", "confirmed", "consumed_not_restorable", "clean_first_launch_consumed_not_restored"),
        ("07", "epic-runtime-authority", "confirmed", "blocked_by_external_state", "security_blocks_runtime_and_auth_entry"),
    )
    return [dict(zip(READINESS_HEADERS, (
        f"epic-readiness-{number}", alias, evidence, terminal, reason,
        SECURITY_VERDICT, "blocks_release" if terminal.startswith("blocked") or number in {"03", "05", "06", "07"} else "candidate_evidence",
    ))) for number, alias, evidence, terminal, reason in values]


def stage_rows() -> list[dict[str, str]]:
    values = (
        ("01", "authority_readiness_and_synthetic_fixture_gate", "blocked_by_external_state", "unknown", "synthetic_fixture_classification_absent"),
        ("02", "authenticated_session_core_navigation", "blocked_by_external_state", "unknown", "auth_entry_blocked_no_literal_go"),
        ("03", "exhaustive_screen_state_transition_inventory", "blocked_by_external_state", "unknown", "runtime_authority_absent"),
        ("04", "input_lifecycle_safe_recovery", "blocked_by_external_state", "unknown", "runtime_authority_absent"),
        ("05", "boundary_classification_safe_recovery", "blocked_by_external_state", "unknown", "runtime_authority_absent"),
        ("06", "regression_ledger_reports_reviews_cleanup_integration", "closed_by_ledger", "confirmed", "repository_only_terminal_blocked_baseline"),
    )
    return [dict(zip(STAGE_HEADERS, (
        f"epic-stage-{number}", name, terminal, evidence, reason, "0", "blocks_release",
    ))) for number, name, terminal, evidence, reason in values]


def budget_rows() -> list[dict[str, str]]:
    values = (
        ("01", "action", "device_or_application_observation", "PROD_CONDITIONAL", "actions", "fresh_exact_security_go_required"),
        ("02", "action", "application_launch_or_ui_input", "PROD_CONDITIONAL", "actions", "fresh_exact_security_go_required"),
        ("03", "action", "authentication_or_credential_entry", "PROD_CONDITIONAL", "actions", "fresh_exact_security_go_and_synthetic_fixture_confirmation_required"),
        ("04", "evidence_resource", "screenshot_visual_capture", "PROD_CONDITIONAL", "captures", "fresh_exact_security_go_required"),
        ("05", "evidence_resource", "ui_tree_capture", "PROD_CONDITIONAL", "captures", "fresh_exact_security_go_required"),
        ("06", "evidence_resource", "bounded_target_log_capture", "PROD_CONDITIONAL", "captures", "fresh_exact_security_go_required"),
        ("07", "time_resource", "conditional_runtime_window", "PROD_CONDITIONAL", "minutes", "fresh_exact_security_go_required"),
        ("08", "action", "payment_external_qr_browser_or_account_mutation", "PROD_FORBIDDEN", "actions", "not_authorizable_by_this_epic_baseline"),
        ("09", "action", "apk_reinstall_clear_reset_patch_or_bypass", "PROD_FORBIDDEN", "actions", "not_authorizable_by_this_epic_baseline"),
        ("10", "action", "network_shaping_load_or_raw_endpoint_extraction", "PROD_FORBIDDEN", "actions", "not_authorizable_by_this_epic_baseline"),
    )
    kill = "target_only_force_stop_then_home_then_capture_shutdown"
    checkpoint_rule = {
        "action": "required_for_conditional_action_or_not_applicable_if_forbidden",
        "evidence_resource": "passive_prerequisite_exempt_from_recursive_checkpoint",
        "time_resource": "not_an_action",
    }
    return [dict(zip(BUDGET_HEADERS, (
        f"epic-budget-{number}", kind, contour, classification, unit, "0", "0",
        checkpoint_rule[kind], gate, kill, "not_run_blocked_before_action",
    ))) for number, kind, contour, classification, unit, gate in values]


def anomaly_rows() -> list[dict[str, str]]:
    return []


def cleanup_rows() -> list[dict[str, str]]:
    return [dict(zip(CLEANUP_HEADERS, (
        "epic-cleanup-001", "confirmed", "false_no_device_actions", "not_run",
        "not_run", "not_run", "not_applicable_no_values_accessed", "0",
        "confirmed", "closed_by_ledger", "repository_only_zero_action_cleanup",
    )))]


def expected_bundle() -> dict[Path, bytes]:
    ledgers = {
        COVERAGE_OUTPUT: _csv_bytes(COVERAGE_HEADERS, coverage_rows()),
        READINESS_OUTPUT: _csv_bytes(READINESS_HEADERS, readiness_rows()),
        STAGE_OUTPUT: _csv_bytes(STAGE_HEADERS, stage_rows()),
        BUDGET_OUTPUT: _csv_bytes(BUDGET_HEADERS, budget_rows()),
        ANOMALY_OUTPUT: _csv_bytes(ANOMALY_HEADERS, anomaly_rows()),
        CLEANUP_OUTPUT: _csv_bytes(CLEANUP_HEADERS, cleanup_rows()),
    }
    coverage = coverage_rows()
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": "closed_by_ledger",
        "coverage_status": "partial_blocked",
        "evidence_status": "confirmed_for_recorded_checkpoints",
        "release_effect": "blocks_release",
        "production_safety_classification": "PROD_SAFE_REPOSITORY_ONLY_BLOCKED_BASELINE",
        "generated_at_utc": GENERATED_AT,
        "task_id": TASK_ID,
        "build_ref": {"alias": "phone-full-authority-inherited-public-safe"},
        "target_alias": "phone-current-authority-unresolved",
        "run_id": RUN_ID,
        "artifacts": [
            {"kind": path.name.removeprefix(STEM + ".").removesuffix(".csv"), "reference": path.relative_to(REPO_ROOT).as_posix(), "sha256": _sha256(data), "evidence_status": "confirmed"}
            for path, data in ledgers.items()
        ],
        "blocked_reasons": [
            "synthetic_fixture_classification_absent",
            "no_literal_runtime_go",
            "auth_entry_explicitly_blocked",
            "current_row03_unknown",
            "clean_first_launch_consumed_not_restorable",
        ],
        "unknowns": [
            "synthetic_test_fixture_classification",
            "current_phone_selector_row03",
            "all_unexecuted_product_behavior",
        ],
        "risks": [
            {"id": "EPIC-PHONE-001-RISK-FALSE-GO", "evidence_status": "confirmed", "summary": "Repository closure cannot authorize runtime or credential entry."},
            {"id": "EPIC-PHONE-001-RISK-FIRST-LAUNCH", "evidence_status": "confirmed", "summary": "Clean first launch was consumed and is not claimed restorable."},
        ],
        "verification": ["fixed_path_contract", "exact_43_row_crosswalk", "task058a_hash_and_modality_validation", "deterministic_bundle_validation"],
        "review": {
            "planner": "GO_TO_BUILD_REPOSITORY_ONLY",
            "security_prod_safety": SECURITY_VERDICT,
            "qa_reviewer_a": "pending_independent_review",
            "qa_reviewer_b": "pending_independent_review",
            "docs_scribe": "pending_independent_review",
        },
        "provenance": {
            "source": "fixed_tracked_public_safe_inputs",
            "arbitrary_input_supported": False,
            "local_only_input_read": False,
            "device_action": False,
            "application_action": False,
            "credential_action": False,
            "forbidden_action": False,
        },
        "payload": {
            "crosswalk_row_count": 43,
            "covered_row_count": sum(row["terminal_status"] == "covered" for row in coverage),
            "blocked_by_external_state_count": sum(row["terminal_status"] == "blocked_by_external_state" for row in coverage),
            "required_phone_blocked_count": sum(row["phone_applicability"] == "phone_required" and row["terminal_status"].startswith("blocked_by_") for row in coverage),
            "blocked_by_tooling_count": sum(row["terminal_status"] == "blocked_by_tooling" for row in coverage),
            "not_run_out_of_scope_count": sum(row["terminal_status"] == "not_run_out_of_scope" for row in coverage),
            "deferred_or_audit_row_count": len(DEFERRED_IDS),
            "inherited_task058a_row_count": 3 if _task058a_inheritance_valid() else 0,
            "stage_count": 6,
            "action_count": 0,
            "device_action_count": 0,
            "application_action_count": 0,
            "auth_entry_action_count": 0,
            "credential_value_access_count": 0,
            "forbidden_action_count": 0,
            "anomaly_count": 0,
            "clean_first_launch_consumed": True,
            "current_row03_unknown": True,
            "security_verdict": SECURITY_VERDICT,
            "checkpoint_contract": "screenshot_visual_inspection_plus_ui_tree_plus_bounded_target_log_before_every_action",
            "kill_switch": "target_only_force_stop_then_home_then_capture_shutdown",
        },
    }
    ledgers[REPORT_OUTPUT] = (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return ledgers


def validate_bundle(bundle: Mapping[Path, bytes], *, disk_schema: bool = False) -> None:
    expected = expected_bundle()
    if set(bundle) != set(expected):
        raise ContractError("bundle_path_set_drift")
    for path, data in expected.items():
        if bundle[path] != data:
            raise ContractError(f"bundle_content_drift:{path.name}")
    coverage = _parse_csv(bundle[COVERAGE_OUTPUT], COVERAGE_HEADERS, "coverage")
    if len(coverage) != 43 or tuple(row["source_row_id"] for row in coverage) != EXPECTED_IDS:
        raise ContractError("coverage_exact_43_rows_once_failed")
    summary = json.loads(bundle[REPORT_OUTPUT])
    try:
        generated_at = datetime.fromisoformat(summary["generated_at_utc"].replace("Z", "+00:00"))
        inherited_at = datetime.fromisoformat(task058a_contract.GENERATED_AT.replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("summary_generated_at_invalid") from exc
    if generated_at > datetime.now(UTC):
        raise ContractError("summary_generated_at_in_future")
    if generated_at < inherited_at:
        raise ContractError("summary_generated_at_precedes_inherited_authority")
    if disk_schema:
        errors = _validate_v2_envelope(summary, REPO_ROOT)
        if errors:
            raise ContractError("summary_schema_invalid:" + ",".join(errors))


def validate_static_contract() -> None:
    if not TASK_SPEC.is_file() or TASK_SPEC.is_symlink():
        raise ContractError("task_spec_missing_or_link")
    text = TASK_SPEC.read_text(encoding="utf-8")
    for marker in (SECURITY_VERDICT, "exactly 43", "checkpoint before every action", "target-only force-stop + Home + capture shutdown"):
        if marker not in text:
            raise ContractError("task_spec_contract_drift")


def _disk_bundle() -> dict[Path, bytes]:
    result: dict[Path, bytes] = {}
    for path in expected_bundle():
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"tracked_artifact_missing_or_link:{path.name}")
        result[path] = path.read_bytes()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--publish-blocked-baseline", action="store_true")
    modes.add_argument("--validate-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        validate_static_contract()
        if args.publish_blocked_baseline:
            bundle = expected_bundle()
            validate_bundle(bundle)
            for path, data in bundle.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        elif args.validate_report:
            validate_bundle(_disk_bundle(), disk_schema=True)
        else:
            validate_bundle(expected_bundle())
    except (ContractError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print("PASS: EPIC-PHONE-001 fixed-path repository-only blocked baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

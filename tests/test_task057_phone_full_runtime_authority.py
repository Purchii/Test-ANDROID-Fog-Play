from __future__ import annotations

import copy
import json
from datetime import datetime, timezone

import pytest

from automation.runtime_authority import task057_phone_full_runtime_authority as sut


NOW_TEXT = "2026-08-15T12:00:00Z"
NOW = datetime(2026, 8, 15, 12, tzinfo=timezone.utc)
FUTURE = "2026-08-16T12:00:00Z"


def authority_bytes(rows):
    return sut._csv_bytes(sut.AUTHORITY_HEADERS, rows)


def cleanup_bytes(rows):
    return sut._csv_bytes(sut.CLEANUP_HEADERS, rows)


def ready_rows():
    rows = copy.deepcopy(sut.baseline_authority_rows())
    for row in rows:
        row.update(
            current_status=sut.PASS_CURRENT_STATUS[row["authority_id"]],
            freshness="fresh_current_run",
            evidence_status="confirmed",
            evidence_ids=";".join(sut.PASS_EVIDENCE_IDS[row["authority_id"]]),
            reviewer_gate="GO_RUNTIME",
            expires_at=FUTURE,
            terminal_status="observed_pass",
            release_effect="candidate_evidence",
            reason_code=sut.PASS_CURRENT_STATUS[row["authority_id"]],
        )
    rows[2]["subject_alias"] = "phone-current-001"
    return rows


def ready_cleanup():
    row = copy.deepcopy(sut.baseline_cleanup_rows()[0])
    row.update(
        current_status="evidence_cleanup_security_ready",
        freshness="fresh_current_run",
        evidence_status="confirmed",
        evidence_ids=";".join(sut.PASS_CLEANUP_EVIDENCE_IDS),
        retention_redaction="confirmed_local_only_redacted_public",
        action_budget="bounded_runtime_budget_current",
        kill_switch="confirmed_runtime_current",
        cleanup_rollback="runtime_cleanup_rollback_current",
        mutation_check="confirmed_unchanged",
        reviewer_gate="GO_RUNTIME",
        expires_at=FUTURE,
        terminal_status="observed_pass",
        release_effect="candidate_evidence",
        reason_code="evidence_cleanup_security_ready",
    )
    return [row]


def test_current_observations_are_exactly_seven_independent_rows():
    rows = sut.baseline_authority_rows()
    assert len(rows) == 7
    assert [row["authority_id"] for row in rows] == list(sut.EXPECTED_AUTHORITY_IDS)
    assert sum(row["terminal_status"] == "observed_pass" for row in rows) == 2
    assert rows[2]["subject_alias"] == "phone-current-001"
    assert rows[3]["reason_code"] == "downgrade_rejection_preserved_no_bypass"


def test_current_sanitized_blockers_and_evidence_are_preserved_exactly():
    rows = sut.baseline_authority_rows()
    assert rows[0]["evidence_ids"] == "task057-apk-presence;task057-apk-integrity;task057-apk-metadata"
    assert rows[0]["reason_code"] == "candidate_min_sdk_metadata_not_emitted"
    assert rows[1]["terminal_status"] == "blocked_by_external_state"
    assert rows[1]["reason_code"] == "installed_signing_certificate_mismatch"
    assert rows[4]["reason_code"] == "synthetic_session_passport_absent"
    assert rows[5]["reason_code"] == "clean_first_launch_fixture_absent"
    assert rows[6]["reason_code"] == "evidence_cleanup_passport_absent_security_block_runtime"
    cleanup = sut.baseline_cleanup_rows()[0]
    assert cleanup["cleanup_rollback"] == "confirmed_no_mutation"
    assert cleanup["mutation_check"] == "confirmed_unchanged"
    assert cleanup["kill_switch"] == "confirmed_metadata_only"
    assert cleanup["reviewer_gate"] == "BLOCK_RUNTIME"


def test_current_summary_fails_closed_without_product_runtime_claims():
    bundle = sut.build_baseline_bundle()
    sut.validate_bundle(bundle)
    summary = json.loads(bundle[sut.REPORT_OUTPUT])
    assert summary["execution_status"] == "blocked"
    assert summary["payload"]["readiness_decision"] == "BLOCK_RUNTIME"
    assert summary["payload"]["runtime_action_count_by_generator"] == 0
    assert summary["payload"]["product_runtime_action_count"] == 0
    assert summary["payload"]["product_navigation_executed"] is False
    assert summary["provenance"]["adb_or_device_action"] is True
    assert summary["provenance"]["apk_read"] is True
    assert summary["production_safety_classification"] == "PROD_CONDITIONAL_READ_ONLY_METADATA"


def test_individual_nonsecurity_row_can_pass_under_metadata_conditional_gate():
    rows = ready_rows()
    rows[0]["reviewer_gate"] = "GO_METADATA_CONDITIONAL"
    assert all(sut.validate_authority_rows(rows, NOW))


def test_row_seven_requires_security_go_runtime_not_metadata_gate():
    rows = ready_rows()
    rows[6]["reviewer_gate"] = "GO_METADATA_CONDITIONAL"
    with pytest.raises(sut.ContractError, match="authority_false_pass"):
        sut.validate_authority_rows(rows, NOW)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reordered"])
def test_missing_duplicate_or_merged_authority_rows_are_rejected(mutation):
    rows = sut.baseline_authority_rows()
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    else:
        rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(sut.ContractError):
        sut.validate_authority_rows(rows, NOW)


def test_one_row_cannot_infer_or_promote_another():
    rows = ready_rows()
    rows[5] = sut.baseline_authority_rows()[5]
    summary = sut.build_summary(authority_bytes(rows), cleanup_bytes(ready_cleanup()), NOW_TEXT)
    assert summary["execution_status"] == "blocked"
    assert summary["payload"]["blocked_row_count"] == 1


def test_shared_generic_evidence_cannot_satisfy_independent_rows():
    rows = ready_rows()
    for row in rows:
        row["evidence_ids"] = "task057-shared-evidence"
    with pytest.raises(sut.ContractError, match="authority_false_pass"):
        sut.validate_authority_rows(rows, NOW)


def test_all_seven_fresh_rows_and_cleanup_with_security_go_allow_go_runtime():
    summary = sut.build_summary(authority_bytes(ready_rows()), cleanup_bytes(ready_cleanup()), NOW_TEXT)
    assert summary["execution_status"] == "pass"
    assert summary["payload"]["authority_row_count"] == 7
    assert summary["payload"]["go_runtime"] is True
    assert summary["payload"]["security_gate"] == "GO_RUNTIME"
    assert summary["release_effect"] == "candidate_evidence"


def test_security_block_cannot_be_labeled_observed_pass():
    rows = ready_rows()
    rows[0]["reviewer_gate"] = "BLOCK_RUNTIME"
    with pytest.raises(sut.ContractError, match="authority_false_pass"):
        sut.validate_authority_rows(rows, NOW)


def test_blocker_reason_cannot_be_labeled_observed_pass():
    rows = ready_rows()
    rows[0]["reason_code"] = "synthetic_session_passport_absent"
    with pytest.raises(sut.ContractError, match="authority_false_pass"):
        sut.validate_authority_rows(rows, NOW)


def test_expired_authority_cannot_be_labeled_observed_pass():
    rows = ready_rows()
    rows[1]["expires_at"] = "2026-08-15T11:59:59Z"
    with pytest.raises(sut.ContractError, match="authority_false_pass"):
        sut.validate_authority_rows(rows, NOW)


def test_current_phone_selector_requires_fresh_public_safe_phone_alias():
    rows = ready_rows()
    rows[2]["subject_alias"] = "current-phone-selector"
    with pytest.raises(sut.ContractError, match="authority_false_pass"):
        sut.validate_authority_rows(rows, NOW)


def test_historical_phone_alias_cannot_substitute_for_neutral_current_mapping():
    rows = ready_rows()
    rows[2]["subject_alias"] = "phone-realme-001"
    with pytest.raises(sut.ContractError, match="authority_false_pass"):
        sut.validate_authority_rows(rows, NOW)


def test_cleanup_passport_is_independent_and_required():
    summary = sut.build_summary(
        authority_bytes(ready_rows()), cleanup_bytes(sut.baseline_cleanup_rows()), NOW_TEXT
    )
    assert summary["execution_status"] == "blocked"
    assert summary["payload"]["blocked_row_count"] == 0
    assert summary["payload"]["cleanup_passport_status"] == "blocked"


def test_metadata_only_budget_cannot_satisfy_runtime_cleanup_authority():
    cleanup = ready_cleanup()
    cleanup[0]["action_budget"] = "bounded_read_only_metadata_only"
    with pytest.raises(sut.ContractError, match="cleanup_false_pass"):
        sut.validate_cleanup_rows(cleanup, NOW)


def test_metadata_only_kill_switch_and_cleanup_cannot_satisfy_runtime_authority():
    cleanup = ready_cleanup()
    cleanup[0]["kill_switch"] = "confirmed_metadata_only"
    cleanup[0]["cleanup_rollback"] = "confirmed_no_mutation"
    with pytest.raises(sut.ContractError, match="cleanup_false_pass"):
        sut.validate_cleanup_rows(cleanup, NOW)


@pytest.mark.parametrize(
    "unsafe_value",
    [
        r"C:\\private\\artifact.apk",
        "https://private.example/value",
        "192.0.2.10",
        ".qa_local/evidence/raw.json",
        "a" * 64,
        "private.application.package",
    ],
)
def test_public_ledger_rejects_raw_or_private_looking_values(unsafe_value):
    rows = sut.baseline_authority_rows()
    rows[0]["reason_code"] = unsafe_value
    with pytest.raises(sut.ContractError, match="unsafe_public_value"):
        sut.validate_authority_rows(rows, NOW)


def test_summary_hash_drift_is_rejected():
    bundle = sut.build_baseline_bundle()
    changed = dict(bundle)
    changed[sut.AUTHORITY_OUTPUT] += b"\n"
    with pytest.raises(sut.ContractError):
        sut.validate_bundle(changed)


def test_duplicate_summary_json_key_is_rejected():
    bundle = sut.build_baseline_bundle()
    changed = dict(bundle)
    changed[sut.REPORT_OUTPUT] = bundle[sut.REPORT_OUTPUT].replace(
        b'"task_id": "TASK-057",', b'"task_id": "TASK-057",\n  "task_id": "TASK-057",'
    )
    with pytest.raises(sut.ContractError, match="duplicate_json_key"):
        sut.validate_bundle(changed)


def test_cli_has_no_path_override_and_static_validation_passes():
    assert sut.main(["--validate-only"]) == 0
    with pytest.raises(SystemExit):
        sut.main(["--validate-report", "--input", "elsewhere.json"])

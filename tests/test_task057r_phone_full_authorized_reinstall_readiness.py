from __future__ import annotations

import copy
import json

import pytest

from automation.runtime_authority import task057r_phone_full_authorized_reinstall_readiness as sut


def _authority_bytes(rows):
    return sut._csv_bytes(sut.AUTHORITY_HEADERS, rows)


def _action_bytes(rows):
    return sut._csv_bytes(sut.ACTION_HEADERS, rows)


def _cleanup_bytes(rows):
    return sut._csv_bytes(sut.CLEANUP_HEADERS, rows)


def test_exact_task057_seven_rows_are_revalidated_without_merging():
    rows = sut.authority_rows()
    assert len(rows) == 7
    assert [row["authority_id"] for row in rows] == list(sut.EXPECTED_AUTHORITY_IDS)
    assert sum(row["terminal_status"] == "observed_pass" for row in rows) == 4
    assert sum(row["terminal_status"] == "blocked_by_fixture" for row in rows) == 3
    sut.validate_authority_rows(rows)


def test_bounded_reinstall_success_does_not_create_go_runtime():
    summary = sut.build_summary(
        _authority_bytes(sut.authority_rows()),
        _action_bytes(sut.action_rows()),
        _cleanup_bytes(sut.cleanup_rows()),
    )
    assert summary["payload"]["bounded_reinstall_status"] == "observed_pass"
    assert summary["payload"]["readiness_observed_pass_count"] == 4
    assert summary["payload"]["readiness_blocked_count"] == 3
    assert summary["payload"]["go_runtime"] is False
    assert summary["payload"]["security_gate"] == "BLOCK_RUNTIME"
    assert summary["payload"]["security_plan_go_pre_action"] is True
    assert summary["payload"]["security_plan_go_phase_order"] < summary["payload"]["uninstall_phase_order"]
    assert summary["payload"]["reinstall_kill_switch"] == "confirmed_stop_no_retry_on_drift_or_failure"
    assert summary["payload"]["reinstall_failure_recovery"] == "requires_new_owner_authority_after_uninstall_or_install_failure"
    assert summary["payload"]["reinstall_contingency_status"] == "confirmed_unused"
    assert summary["execution_status"] == "blocked"
    assert summary["release_effect"] == "blocks_release"


def test_reinstall_action_ledger_records_exact_bounded_counts():
    rows = sut.action_rows()
    sut.validate_action_rows(rows)
    assert len({row["evidence_ids"] for row in rows}) == len(rows)
    counts = {row["action_alias"]: int(row["observed_count"]) for row in rows}
    assert counts["uninstall"] == 1
    assert counts["ordinary-install"] == 1
    assert counts["midstate-absence"] == 1
    assert counts["unrelated-package-delta"] == 0
    assert counts["launch-navigation"] == 0
    assert counts["task058"] == 0


def test_security_plan_go_is_a_distinct_pre_action_row_before_uninstall():
    rows = sut.action_rows()
    security = next(row for row in rows if row["action_alias"] == "security-plan-go")
    uninstall = next(row for row in rows if row["action_alias"] == "uninstall")
    assert security["phase"] == "pre-action"
    assert int(security["phase_order"]) < int(uninstall["phase_order"])
    assert security["evidence_ids"] == "task057r-security-plan-go"


@pytest.mark.parametrize("mutation", ["missing", "wrong_phase", "after_uninstall"])
def test_security_plan_go_missing_or_wrong_phase_order_fails_closed(mutation):
    rows = copy.deepcopy(sut.action_rows())
    index = next(index for index, row in enumerate(rows) if row["action_alias"] == "security-plan-go")
    if mutation == "missing":
        rows.pop(index)
    elif mutation == "wrong_phase":
        rows[index]["phase"] = "package-mutation"
    else:
        rows[index]["phase_order"] = "50"
    with pytest.raises(sut.ContractError):
        sut.validate_action_rows(rows)


def test_reinstall_contingency_is_distinct_from_runtime_kill_switch_and_data_loss():
    action = next(row for row in sut.action_rows() if row["action_alias"] == "one-shot-contingency")
    cleanup = sut.cleanup_rows()[0]
    assert action["phase"] == "pre-action"
    assert action["current_status"] == "stop_no_retry_contingency_confirmed"
    assert cleanup["reinstall_kill_switch"] == "confirmed_stop_no_retry_on_drift_or_failure"
    assert cleanup["reinstall_failure_recovery"] == "requires_new_owner_authority_after_uninstall_or_install_failure"
    assert cleanup["reinstall_contingency_status"] == "confirmed_unused"
    assert cleanup["cleanup_rollback"] == "not_claimed_for_accepted_target_data_loss"
    assert cleanup["runtime_kill_switch"] == "absent"


@pytest.mark.parametrize(
    ("alias", "count"),
    [
        ("uninstall", "0"),
        ("uninstall", "2"),
        ("ordinary-install", "0"),
        ("ordinary-install", "2"),
        ("unrelated-package-delta", "1"),
        ("launch-navigation", "1"),
        ("task058", "1"),
    ],
)
def test_action_budget_or_scope_drift_fails_closed(alias, count):
    rows = copy.deepcopy(sut.action_rows())
    next(row for row in rows if row["action_alias"] == alias)["observed_count"] = count
    with pytest.raises(sut.ContractError, match="action_semantic_drift"):
        sut.validate_action_rows(rows)


def test_installed_compatibility_requires_fresh_exact_postinstall_equivalence():
    rows = copy.deepcopy(sut.authority_rows())
    rows[1]["evidence_ids"] = "task057r-install-observation"
    with pytest.raises(sut.ContractError, match="authority_semantic_drift"):
        sut.validate_authority_rows(rows)


def test_candidate_row_cannot_reuse_task057_or_generic_evidence():
    rows = copy.deepcopy(sut.authority_rows())
    rows[0]["evidence_ids"] = "task057r-reinstall-action-ledger"
    with pytest.raises(sut.ContractError, match="authority_semantic_drift"):
        sut.validate_authority_rows(rows)


@pytest.mark.parametrize(
    "missing_evidence",
    [
        "task057r-candidate-integrity",
        "task057r-candidate-provenance",
        "task057r-candidate-signing",
        "task057r-candidate-version",
        "task057r-candidate-min-sdk",
        "task057r-candidate-target-sdk",
        "task057r-candidate-abi",
        "task057r-candidate-install-compatibility",
    ],
)
def test_candidate_row_requires_every_install_metadata_category(missing_evidence):
    rows = copy.deepcopy(sut.authority_rows())
    evidence = rows[0]["evidence_ids"].split(";")
    evidence.remove(missing_evidence)
    rows[0]["evidence_ids"] = ";".join(evidence)
    with pytest.raises(sut.ContractError, match="authority_semantic_drift"):
        sut.validate_authority_rows(rows)


@pytest.mark.parametrize("index", [4, 5, 6])
def test_install_success_cannot_promote_independent_fixture_rows(index):
    rows = copy.deepcopy(sut.authority_rows())
    rows[index].update(
        evidence_status="confirmed",
        evidence_ids="task057r-install-observation",
        reviewer_gate="GO_RUNTIME",
        expires_at="2026-08-17T23:59:59Z",
        terminal_status="observed_pass",
        release_effect="candidate_evidence",
    )
    with pytest.raises(sut.ContractError, match="authority_semantic_drift"):
        sut.validate_authority_rows(rows)


def test_empty_session_after_uninstall_is_not_a_synthetic_passport():
    assert sut.authority_rows()[4]["reason_code"] == "synthetic_session_passport_absent"
    assert sut.authority_rows()[4]["terminal_status"] == "blocked_by_fixture"


def test_successful_reinstall_is_not_clean_first_launch_fixture_authority():
    row = sut.authority_rows()[5]
    assert row["terminal_status"] == "blocked_by_fixture"
    assert row["reason_code"] == "reinstall_success_does_not_establish_clean_first_launch_fixture"


def test_cleanup_records_accepted_loss_without_restoration_or_rollback_claim():
    row = sut.cleanup_rows()[0]
    sut.validate_cleanup_rows([row])
    assert row["target_data_loss"] == "owner_authorized_accepted_not_restored"
    assert row["cleanup_rollback"] == "not_claimed_for_accepted_target_data_loss"
    assert row["reinstall_kill_switch"] == "confirmed_stop_no_retry_on_drift_or_failure"
    assert row["reinstall_failure_recovery"] == "requires_new_owner_authority_after_uninstall_or_install_failure"
    assert row["reinstall_contingency_status"] == "confirmed_unused"
    assert row["runtime_kill_switch"] == "absent"
    assert row["reviewer_gate"] == "BLOCK_RUNTIME"
    assert row["terminal_status"] == "blocked_by_fixture"


def test_process_anomalies_preserve_pre_mutation_failures_and_builder_validation_failure():
    anomalies = sut.build_summary(
        _authority_bytes(sut.authority_rows()),
        _action_bytes(sut.action_rows()),
        _cleanup_bytes(sut.cleanup_rows()),
    )["payload"]["anomalies"]
    assert len(anomalies) == 4
    assert all(item["evidence_status"] == "confirmed" for item in anomalies)
    assert all(item["phase"] == "before_mutation" for item in anomalies[:3])
    assert anomalies[3]["phase"] == "repository_validation_after_device_action"
    assert all(item["product_impact"] == "none" for item in anomalies)


@pytest.mark.parametrize(
    "unsafe_value",
    [
        r"C:\private\candidate.apk",
        "https://private.example/value",
        "192.0.2.10",
        ".qa_local/evidence/raw.json",
        "a" * 64,
        "private.application.package",
    ],
)
def test_public_ledgers_reject_raw_or_private_looking_values(unsafe_value):
    with pytest.raises(sut.ContractError, match="unsafe_public_value"):
        sut._assert_public_safe(unsafe_value, "synthetic-test-field")


def test_summary_hash_or_semantic_drift_is_rejected():
    bundle = sut.build_bundle()
    changed = dict(bundle)
    summary = json.loads(changed[sut.REPORT_OUTPUT])
    summary["payload"]["go_runtime"] = True
    changed[sut.REPORT_OUTPUT] = sut._json_bytes(summary)
    with pytest.raises(sut.ContractError, match="summary_semantic_or_hash_drift"):
        sut.validate_bundle(changed)


def test_duplicate_summary_key_is_rejected():
    bundle = sut.build_bundle()
    changed = dict(bundle)
    changed[sut.REPORT_OUTPUT] = bundle[sut.REPORT_OUTPUT].replace(
        b'"task_id": "TASK-057R",',
        b'"task_id": "TASK-057R",\n  "task_id": "TASK-057R",',
    )
    with pytest.raises(sut.ContractError, match="duplicate_json_key"):
        sut.validate_bundle(changed)


def test_bundle_paths_are_task057r_and_do_not_overlap_task057():
    paths = {path.name for path in sut.build_bundle()}
    assert len(paths) == 4
    assert all(name.startswith("task057r_") for name in paths)
    assert all(not name.startswith("task057_") for name in paths)


def test_cli_is_fixed_path_repository_only_and_rejects_overrides():
    assert sut.main(["--validate-only"]) == 0
    with pytest.raises(SystemExit):
        sut.main(["--validate-report", "--input", "elsewhere.json"])

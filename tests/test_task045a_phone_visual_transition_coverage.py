from __future__ import annotations

import copy
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from automation.gamepad import task045a_phone_visual_transition_coverage as subject


def baseline() -> dict[str, object]:
    return copy.deepcopy(subject._baseline_adapter())


def by_scenario(adapter: dict[str, object], group: str, scenario_id: str) -> dict[str, object]:
    return next(row for row in adapter[group] if row["scenario_id"] == scenario_id)


def cover(adapter: dict[str, object], scenario_id: str) -> None:
    scenario = by_scenario(adapter, "scenarios", scenario_id)
    node = by_scenario(adapter, "screen_states", scenario_id)
    transition = by_scenario(adapter, "transitions", scenario_id)
    branch = by_scenario(adapter, "branch_closure", scenario_id)
    pre_ids = [f"fresh-{scenario_id.lower()}-pre-shot", f"fresh-{scenario_id.lower()}-pre-tree", f"fresh-{scenario_id.lower()}-pre-log"]
    post_ids = [f"fresh-{scenario_id.lower()}-post-shot", f"fresh-{scenario_id.lower()}-post-tree", f"fresh-{scenario_id.lower()}-post-log"]
    ids = pre_ids + post_ids
    scenario.update(status="covered", evidence_status="confirmed", evidence_ids=ids, reason_code="fresh_eligible_coverage")
    node.update(
        observed=True,
        evidence_origin="fresh_task045a",
        audit_only=False,
        counts_as_product_coverage=True,
        status="covered",
        evidence_status="confirmed",
        evidence_ids=pre_ids,
        modalities={
            "screenshot": {"evidence_id": pre_ids[0], "captured_at_utc": "2026-08-15T00:59:57Z", "visual_inspection": True},
            "ui_tree": {"evidence_id": pre_ids[1], "captured_at_utc": "2026-08-15T00:59:58Z"},
            "runner_log": {"evidence_id": pre_ids[2], "captured_at_utc": "2026-08-15T00:59:59Z"},
        },
        recurrence_status="first_observation",
        reason_code="fresh_eligible_coverage",
    )
    post = copy.deepcopy(node)
    post.update(
        node_id=f"{node['node_id']}-post",
        state_alias=f"{node['state_alias']}-post",
        evidence_ids=post_ids,
        modalities={
            "screenshot": {"evidence_id": post_ids[0], "captured_at_utc": "2026-08-15T00:59:57Z", "visual_inspection": True},
            "ui_tree": {"evidence_id": post_ids[1], "captured_at_utc": "2026-08-15T00:59:58Z"},
            "runner_log": {"evidence_id": post_ids[2], "captured_at_utc": "2026-08-15T00:59:59Z"},
        },
    )
    adapter["screen_states"].append(post)
    transition.update(from_node_id=node["node_id"], to_node_id=post["node_id"], attempt_index=1)
    transition.update(status="covered", evidence_status="confirmed", evidence_ids=ids, reason_code="fresh_eligible_coverage")
    branch.update(
        status="covered", evidence_status="confirmed", evidence_ids=ids,
        screen_node_ids=[node["node_id"], post["node_id"]], reason_code="fresh_eligible_coverage",
    )
    adapter["evidence_registry"] = sorted(subject._all_evidence_ids(adapter))


def prove_session(adapter: dict[str, object]) -> None:
    adapter["lane_preflight"].update(
        active_session_provenance="approved_synthetic_fixture",
        session_passport_status="proven",
    )


def test_catalog_is_exact_a001_through_a017() -> None:
    rows = subject.load_contract()
    assert [row["scenario_id"] for row in rows] == list(subject.EXPECTED_IDS)
    assert all(row["priority"] == "P0" for row in rows)


def test_blocked_baseline_is_strict_and_builds_v2_bundle() -> None:
    adapter = baseline()
    subject.validate_adapter(adapter)
    bundle = subject.build_bundle(adapter, subject.load_contract())
    subject.validate_bundle(bundle)
    report = json.loads(bundle[subject.REPORT_OUTPUT])
    assert report["task_id"] == "TASK-045A"
    assert report["coverage_status"] == "blocked"
    assert report["execution_status"] == "blocked"
    assert report["release_effect"] == "blocks_release"
    assert report["payload"]["full_visual_transition_coverage"] is False
    assert report["payload"]["counts_as_paired_evidence"] is False


def test_quarantined_audit_counts_are_category_only_and_ineligible() -> None:
    prior = baseline()["prior_audit"]
    assert prior == {
        "source_task": "TASK-045",
        "png_count": 20,
        "xml_count": 19,
        "bounded_log_count": 19,
        "incomplete_checkpoint_alias": "prior-audit-cp001",
        "audit_only": True,
        "counts_as_product_coverage": False,
        "session_provenance": "unknown_not_verified",
    }


def test_cp001_incomplete_audit_cannot_be_covered() -> None:
    adapter = baseline()
    row = by_scenario(adapter, "screen_states", "A001")
    row.update(status="covered", counts_as_product_coverage=True)
    with pytest.raises(subject.ContractError, match="QUARANTINED_EVIDENCE_CANNOT_COVER"):
        subject.validate_adapter(adapter)


def test_unknown_session_blocks_every_session_dependent_branch() -> None:
    adapter = baseline()
    assert adapter["lane_preflight"]["active_session_provenance"] == "unknown_not_verified"
    for scenario_id in subject.SESSION_DEPENDENT_IDS:
        for group in ("scenarios", "screen_states", "transitions", "branch_closure"):
            row = by_scenario(adapter, group, scenario_id)
            assert row["status"] == "blocked_by_external_state"
            assert row["reason_code"] == "active_session_provenance_unknown"


def test_unverified_session_cannot_cover_screen() -> None:
    adapter = baseline()
    cover(adapter, "A003")
    with pytest.raises(subject.ContractError, match="UNVERIFIED_SESSION_CANNOT_COVER_SCREEN"):
        subject.validate_adapter(adapter)


def test_session_passport_enum_relation_is_fail_closed() -> None:
    adapter = baseline()
    adapter["lane_preflight"]["session_passport_status"] = "proven"
    with pytest.raises(subject.ContractError, match="SESSION_PASSPORT_RELATION_INVALID"):
        subject.validate_adapter(adapter)


def test_fresh_session_independent_coverage_requires_visual_triplet() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    subject.validate_adapter(adapter)
    by_scenario(adapter, "screen_states", "A011")["modalities"]["ui_tree"] = None
    with pytest.raises(subject.ContractError, match="FRESH_MODALITIES_REQUIRED"):
        subject.validate_adapter(adapter)


def test_visual_inspection_is_mandatory() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "screen_states", "A011")["modalities"]["screenshot"]["visual_inspection"] = False
    with pytest.raises(subject.ContractError, match="VISUAL_INSPECTION_REQUIRED"):
        subject.validate_adapter(adapter)


def test_stale_modality_is_rejected() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "screen_states", "A011")["modalities"]["runner_log"]["captured_at_utc"] = "2026-08-13T00:00:00Z"
    with pytest.raises(subject.ContractError, match="MODALITY_FRESHNESS_INVALID"):
        subject.validate_adapter(adapter)


def test_missing_tv_cannot_cover_paired_node() -> None:
    adapter = baseline()
    cover(adapter, "A016")
    with pytest.raises(subject.ContractError, match="NON_PHONE_SCREEN_CANNOT_COVER|PAIRED_SCREEN_CANNOT_COUNT_AS_PHONE_COVERAGE"):
        subject.validate_adapter(adapter)


def test_tv_or_external_surface_can_never_count_as_phone_coverage() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "screen_states", "A011")["surface_side"] = "external_blocker"
    with pytest.raises(subject.ContractError, match="NON_PHONE_SCREEN_CANNOT_COVER"):
        subject.validate_adapter(adapter)


def test_tv_layout_or_state_alias_is_rejected_even_when_side_is_mislabeled_phone() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "screen_states", "A011")["screen_alias"] = "television-full-layout"
    with pytest.raises(subject.ContractError, match="NON_PHONE_SCREEN_ALIAS_INVALID|PUBLIC_IDENTIFIER_PACKAGE_LIKE"):
        subject.validate_adapter(adapter)


def test_tv_or_paired_edge_can_never_count_as_phone_coverage() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "transitions", "A011")["edge_scope"] = "external_blocker"
    with pytest.raises(subject.ContractError, match="NON_PHONE_EDGE_CANNOT_COVER"):
        subject.validate_adapter(adapter)


def test_tv_edge_alias_is_rejected_even_when_scope_is_mislabeled_phone() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "transitions", "A011")["action_category"] = "paired-tv-edge"
    with pytest.raises(subject.ContractError, match="NON_PHONE_EDGE_ALIAS_INVALID"):
        subject.validate_adapter(adapter)


def test_foreign_tv_evidence_cannot_be_added_to_phone_checkpoint() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    node = by_scenario(adapter, "screen_states", "A011")
    node["evidence_ids"].append("tv-side-evidence")
    adapter["evidence_registry"] = sorted(subject._all_evidence_ids(adapter))
    with pytest.raises(subject.ContractError, match="NON_PHONE_EVIDENCE_ID_INVALID"):
        subject.validate_adapter(adapter)


def test_transition_requires_exact_nodes() -> None:
    adapter = baseline()
    by_scenario(adapter, "transitions", "A011")["to_node_id"] = "node-does-not-exist"
    with pytest.raises(subject.ContractError, match="TRANSITION_NODE_LINK_INVALID"):
        subject.validate_adapter(adapter)


def test_recovery_requires_retained_first_failure() -> None:
    adapter = baseline()
    original = by_scenario(adapter, "transitions", "A011")
    original["first_failure_retained"] = False
    recovery = copy.deepcopy(original)
    recovery.update(
        transition_id="transition-a011-recovery",
        recovery_attempt=True,
        recovery_of_transition_id=original["transition_id"],
        attempt_index=2,
    )
    adapter["transitions"].append(recovery)
    with pytest.raises(subject.ContractError, match="FIRST_FAILURE_NOT_RETAINED"):
        subject.validate_adapter(adapter)


def test_xml_visual_mismatch_requires_immediate_anomaly() -> None:
    adapter = baseline()
    by_scenario(adapter, "screen_states", "A011")["xml_visual_match"] = "confirmed_mismatch"
    with pytest.raises(subject.ContractError, match="XML_VISUAL_MISMATCH_REQUIRES_ANOMALY"):
        subject.validate_adapter(adapter)


def test_reachable_approved_branch_cannot_be_out_of_scope() -> None:
    adapter = baseline()
    by_scenario(adapter, "branch_closure", "A011")["status"] = "not_run_out_of_scope"
    with pytest.raises(subject.ContractError, match="REACHABLE_APPROVED_BRANCH_OUT_OF_SCOPE_INVALID"):
        subject.validate_adapter(adapter)


def test_long_list_coverage_requires_initial_and_later_segments() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A004")
    with pytest.raises(subject.ContractError, match="LONG_LIST_SEGMENTS_INCOMPLETE"):
        subject.validate_adapter(adapter)


def test_menu_coverage_requires_expanded_and_collapsed_states() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A005")
    with pytest.raises(subject.ContractError, match="MENU_STATES_INCOMPLETE"):
        subject.validate_adapter(adapter)


def test_evidence_registry_must_be_exact() -> None:
    adapter = baseline()
    adapter["evidence_registry"].append("unreferenced-evidence")
    with pytest.raises(subject.ContractError, match="EVIDENCE_REGISTRY_MISMATCH"):
        subject.validate_adapter(adapter)


def test_boundary_mutation_is_forbidden() -> None:
    adapter = baseline()
    adapter["boundaries"][0]["payment_or_session_started"] = True
    with pytest.raises(subject.ContractError, match="FORBIDDEN_BOUNDARY_ACTION_RECORDED"):
        subject.validate_adapter(adapter)


def test_cleanup_covered_requires_force_stop_home_and_preserved_session() -> None:
    adapter = baseline()
    adapter["cleanup"].update(status="covered", evidence_status="confirmed")
    with pytest.raises(subject.ContractError, match="CLEANUP_COVERAGE_INVALID"):
        subject.validate_adapter(adapter)


def test_required_process_anomaly_preserves_historical_suite_failure() -> None:
    anomaly = baseline()["anomalies"][0]
    assert anomaly["anomaly_id"] == "TASK045A-PROCESS-001"
    assert anomaly["observed_result_category"] == "seventeen_failures_missing_ignored_source"
    assert anomaly["first_failure_retained"] is True


def test_required_process_anomaly_cannot_be_removed() -> None:
    adapter = baseline()
    adapter["anomalies"] = []
    with pytest.raises(subject.ContractError, match="SCHEMA_INSTANCE_INVALID|REQUIRED_PROCESS_ANOMALY_MISSING"):
        subject.validate_adapter(adapter)


def test_schema_rejects_unknown_top_level_fields() -> None:
    adapter = baseline()
    adapter["unexpected"] = False
    with pytest.raises(subject.ContractError, match=r"SCHEMA_INSTANCE_INVALID:\$"):
        subject.validate_adapter(adapter)


def test_public_output_rejects_url_like_state_alias() -> None:
    adapter = baseline()
    by_scenario(adapter, "screen_states", "A011")["state_alias"] = "https://invalid.example"
    with pytest.raises((subject.ContractError, subject.shared.ContractError)):
        subject.validate_adapter(adapter)


@pytest.mark.parametrize("alias", ["com.vendor.privateapp", "a" * 64])
def test_public_build_alias_rejects_package_or_hash_like_values(alias: str) -> None:
    adapter = baseline()
    adapter["build_ref"]["alias"] = alias
    with pytest.raises(subject.ContractError, match="PUBLIC_IDENTIFIER_(?:PACKAGE|HASH)_LIKE"):
        subject.validate_adapter(adapter)


@pytest.mark.parametrize(
    "alias",
    ["phone-tv-layout", "phone.television.layout", "phone_paired_state", "phone-cross-device-edge"],
)
def test_phone_coverage_rejects_embedded_tv_or_paired_aliases(alias: str) -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "screen_states", "A011")["screen_alias"] = alias
    with pytest.raises(subject.ContractError, match="NON_PHONE_SCREEN_ALIAS_INVALID|PUBLIC_IDENTIFIER_PACKAGE_LIKE"):
        subject.validate_adapter(adapter)


def test_blocked_terminal_branch_requires_evidence_ids() -> None:
    adapter = baseline()
    by_scenario(adapter, "branch_closure", "A011")["evidence_ids"] = []
    with pytest.raises(subject.ContractError, match="SCHEMA_INSTANCE_INVALID|BRANCH_EVIDENCE_RECONCILIATION_INVALID"):
        subject.validate_adapter(adapter)


def test_branch_must_link_every_discovered_node_and_edge() -> None:
    adapter = baseline()
    extra_node = copy.deepcopy(by_scenario(adapter, "screen_states", "A011"))
    extra_node["node_id"] = "node-a011-extra"
    adapter["screen_states"].append(extra_node)
    with pytest.raises(subject.ContractError, match="BRANCH_GRAPH_RECONCILIATION_INVALID"):
        subject.validate_adapter(adapter)


def test_scenario_and_branch_status_must_match() -> None:
    adapter = baseline()
    by_scenario(adapter, "scenarios", "A011")["status"] = "blocked_by_tooling"
    with pytest.raises(subject.ContractError, match="SCENARIO_BRANCH_STATUS_MISMATCH"):
        subject.validate_adapter(adapter)


def test_go_requires_confirmed_task_build_compatibility() -> None:
    adapter = baseline()
    adapter["lane_preflight"].update(
        runtime_gate="GO", phone_status="READY", reviewer_gate=True,
        ignored_evidence_storage_ready=True,
        active_session_provenance="approved_synthetic_fixture", session_passport_status="proven",
    )
    with pytest.raises(subject.ContractError, match="RUNTIME_GO_PREFLIGHT_INVALID"):
        subject.validate_adapter(adapter)


def test_transition_boundary_reference_must_exist() -> None:
    adapter = baseline()
    by_scenario(adapter, "transitions", "A015")["boundary_id"] = "boundary-does-not-exist"
    with pytest.raises(subject.ContractError, match="TRANSITION_BOUNDARY_LINK_INVALID"):
        subject.validate_adapter(adapter)


def test_transition_must_link_nodes_from_its_own_scenario() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    foreign = by_scenario(adapter, "screen_states", "A012")["node_id"]
    edge = by_scenario(adapter, "transitions", "A011")
    edge.update(from_node_id=foreign, to_node_id=foreign)
    with pytest.raises(subject.ContractError, match="TRANSITION_SCENARIO_LINK_INVALID"):
        subject.validate_adapter(adapter)


def test_covered_transition_requires_exact_pre_post_checkpoint_evidence() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "transitions", "A011")["evidence_ids"] = ["fresh-a011-pre-shot"]
    adapter["evidence_registry"] = sorted(subject._all_evidence_ids(adapter))
    with pytest.raises(subject.ContractError, match="TRANSITION_CHECKPOINT_EVIDENCE_INCOMPLETE"):
        subject.validate_adapter(adapter)


def test_go_adapter_freshness_is_bound_to_validation_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = baseline()
    adapter["build_ref"]["compatibility_status"] = "confirmed_for_task045a"
    adapter["lane_preflight"].update(
        runtime_gate="GO", phone_status="READY", reviewer_gate=True,
        ignored_evidence_storage_ready=True,
        active_session_provenance="approved_synthetic_fixture", session_passport_status="proven",
    )
    monkeypatch.setattr(subject, "_now_utc", lambda: datetime(2026, 8, 17, tzinfo=timezone.utc))
    with pytest.raises(subject.ContractError, match="RUNTIME_ADAPTER_FRESHNESS_INVALID"):
        subject.validate_adapter(adapter)


def test_naive_search_overlay_self_loop_cannot_cover() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A006")
    with pytest.raises(subject.ContractError, match="SEARCH_OVERLAY_RECOVERY_INCOMPLETE"):
        subject.validate_adapter(adapter)


def test_naive_lifecycle_branch_without_recurrence_cannot_cover() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A013")
    with pytest.raises(subject.ContractError, match="LIFECYCLE_RECURRENCE_INCOMPLETE"):
        subject.validate_adapter(adapter)


def test_naive_payment_boundary_branch_without_capture_recovery_cannot_cover() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A015")
    with pytest.raises(subject.ContractError, match="BOUNDARY_CAPTURE_RECOVERY_INCOMPLETE"):
        subject.validate_adapter(adapter)


def test_covered_transition_requires_positive_attempt_index() -> None:
    adapter = baseline()
    cover(adapter, "A011")
    by_scenario(adapter, "transitions", "A011")["attempt_index"] = 0
    with pytest.raises(subject.ContractError, match="COVERED_TRANSITION_ATTEMPT_INVALID"):
        subject.validate_adapter(adapter)


def test_combined_account_route_label_cannot_replace_four_distinct_states() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A008")
    for node in [item for item in adapter["screen_states"] if item["scenario_id"] == "A008"]:
        node["state_category"] = "profile-settings-help-legal-shell"
    with pytest.raises(subject.ContractError, match="READ_ONLY_ACCOUNT_ROUTES_INCOMPLETE"):
        subject.validate_adapter(adapter)


def test_disconnected_required_search_node_cannot_satisfy_branch() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A006")
    source = by_scenario(adapter, "screen_states", "A006")
    extra = copy.deepcopy(source)
    extra.update(
        node_id="node-a006-disconnected-overlay", state_alias="search-overlay",
        overlay_category="app_overlay", recurrence_status="recurrence", prior_node_id=source["node_id"],
    )
    adapter["screen_states"].append(extra)
    branch = by_scenario(adapter, "branch_closure", "A006")
    branch["screen_node_ids"].append(extra["node_id"])
    adapter["evidence_registry"] = sorted(subject._all_evidence_ids(adapter))
    with pytest.raises(subject.ContractError, match="COVERED_BRANCH_DISCONNECTED_NODE"):
        subject.validate_adapter(adapter)


def test_local_adapter_symlink_escape_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    local_root = tmp_path / "local"
    local_root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(baseline()), encoding="utf-8")
    link = local_root / "runtime-adapter.local.json"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    monkeypatch.setattr(subject, "LOCAL_ROOT", local_root)
    monkeypatch.setattr(subject, "LOCAL_ADAPTER", link)
    with pytest.raises(subject.ContractError, match="ADAPTER_PATH_INVALID"):
        subject._load_adapter(link)


def test_local_adapter_reparse_point_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    local_root = tmp_path / "local"
    local_root.mkdir()
    adapter_path = local_root / "runtime-adapter.local.json"
    adapter_path.write_text(json.dumps(baseline()), encoding="utf-8")
    monkeypatch.setattr(subject, "LOCAL_ROOT", local_root)
    monkeypatch.setattr(subject, "LOCAL_ADAPTER", adapter_path)
    monkeypatch.setattr(subject, "_is_reparse_point", lambda _path: True)
    with pytest.raises(subject.ContractError, match="ADAPTER_PATH_INVALID"):
        subject._load_adapter(adapter_path)


def test_session_passport_must_bind_run_phone_build_lane_freshness_and_reviewer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = baseline()
    local_root = tmp_path / "local"
    local_root.mkdir()
    passport_path = local_root / "synthetic-session-passport.local.json"
    passport = {
        "schema_version": "task045a-synthetic-session-passport-v1",
        "task_id": "TASK-045A",
        "run_id": adapter["run_id"],
        "fixture_alias": "task045a-synthetic-fixture",
        "provenance": "approved_synthetic_fixture",
        "task_authoritative": True,
        "evidence_status": "confirmed",
        "raw_values_published": False,
        "phone_alias": adapter["lane_preflight"]["phone_alias"],
        "build_alias": "wrong-build-alias",
        "lane_alias": "phone-full-visual-transition-lane",
        "confirmed_at_utc": "2026-08-15T00:55:00Z",
        "expires_at_utc": "2026-08-15T01:05:00Z",
        "authority_evidence_id": "task045a-session-authority-review",
        "reviewer_decision": "GO",
    }
    passport_path.write_text(json.dumps(passport), encoding="utf-8")
    monkeypatch.setattr(subject, "LOCAL_ROOT", local_root)
    monkeypatch.setattr(subject, "LOCAL_SESSION_PASSPORT", passport_path)
    with pytest.raises(subject.ContractError, match="SESSION_PASSPORT_NOT_PROVEN"):
        subject._validate_session_passport(passport_path, adapter)


def _rehash(bundle: dict[Path, bytes], path: Path) -> None:
    report = json.loads(bundle[subject.REPORT_OUTPUT])
    artifact = next(row for row in report["artifacts"] if row["reference"] == subject._repo_ref(path))
    artifact["sha256"] = subject.shared._sha(bundle[path])
    bundle[subject.REPORT_OUTPUT] = subject._json_bytes(report)


def test_report_rejects_hash_consistent_forbidden_cleanup_state() -> None:
    bundle = subject.build_bundle(baseline(), subject.load_contract())
    text = bundle[subject.CLEANUP_OUTPUT].decode("utf-8").replace(
        "false,false,false,false,false,confirmed", "true,false,false,false,false,confirmed", 1
    )
    bundle[subject.CLEANUP_OUTPUT] = text.encode("utf-8")
    _rehash(bundle, subject.CLEANUP_OUTPUT)
    with pytest.raises(subject.ContractError, match="REPORT_FORBIDDEN_CLEANUP_STATE"):
        subject.validate_bundle(bundle)


@pytest.mark.parametrize("unsafe_alias", ["com.vendor.privateapp", "https://private.invalid/path"])
def test_report_rejects_hash_consistent_unsafe_blocked_screen_alias(unsafe_alias: str) -> None:
    bundle = subject.build_bundle(baseline(), subject.load_contract())
    rows = list(csv.DictReader(io.StringIO(bundle[subject.SCREEN_OUTPUT].decode("utf-8"))))
    rows[0]["screen_alias"] = unsafe_alias
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=subject.SCREEN_HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    bundle[subject.SCREEN_OUTPUT] = stream.getvalue().encode("utf-8")
    _rehash(bundle, subject.SCREEN_OUTPUT)
    with pytest.raises((subject.ContractError, subject.shared.ContractError)):
        subject.validate_bundle(bundle)


def test_report_rejects_covered_count_and_full_coverage_false_pass() -> None:
    bundle = subject.build_bundle(baseline(), subject.load_contract())
    report = json.loads(bundle[subject.REPORT_OUTPUT])
    report["payload"]["covered_counts"].update(screens=999, transitions=999)
    report["payload"]["full_visual_transition_coverage"] = True
    bundle[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    with pytest.raises(subject.ContractError, match="REPORT_COVERED_COUNTS_INVALID|REPORT_FULL_COVERAGE_FLAG_INVALID"):
        subject.validate_bundle(bundle)


def test_report_rejects_hash_consistent_long_list_semantic_tamper() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A004")
    nodes = [item for item in adapter["screen_states"] if item["scenario_id"] == "A004"]
    nodes[0]["long_list_segment"] = "initial"
    nodes[1]["long_list_segment"] = "later"
    subject.validate_adapter(adapter)
    bundle = subject.build_bundle(adapter, subject.load_contract())
    rows = list(csv.DictReader(io.StringIO(bundle[subject.SCREEN_OUTPUT].decode("utf-8"))))
    for row in rows:
        if row["scenario_id"] == "A004":
            row["long_list_segment"] = "none"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=subject.SCREEN_HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    bundle[subject.SCREEN_OUTPUT] = stream.getvalue().encode("utf-8")
    _rehash(bundle, subject.SCREEN_OUTPUT)
    with pytest.raises(subject.ContractError, match="REPORT_LONG_LIST_SEGMENTS_INCOMPLETE"):
        subject.validate_bundle(bundle)


def test_report_rejects_hash_consistent_distinct_account_route_tamper() -> None:
    adapter = baseline()
    prove_session(adapter)
    cover(adapter, "A008")
    nodes = [item for item in adapter["screen_states"] if item["scenario_id"] == "A008"]
    nodes[0]["state_category"] = "profile"
    nodes[1]["state_category"] = "settings"
    all_ids = list(nodes[0]["evidence_ids"] + nodes[1]["evidence_ids"])
    edge = by_scenario(adapter, "transitions", "A008")
    branch = by_scenario(adapter, "branch_closure", "A008")
    for category in ("help", "legal"):
        ids = [f"fresh-a008-{category}-shot", f"fresh-a008-{category}-tree", f"fresh-a008-{category}-log"]
        node = copy.deepcopy(nodes[1])
        node.update(
            node_id=f"node-a008-{category}", state_alias=f"account-{category}", state_category=category,
            evidence_ids=ids,
            modalities={
                "screenshot": {"evidence_id": ids[0], "captured_at_utc": "2026-08-15T00:59:57Z", "visual_inspection": True},
                "ui_tree": {"evidence_id": ids[1], "captured_at_utc": "2026-08-15T00:59:58Z"},
                "runner_log": {"evidence_id": ids[2], "captured_at_utc": "2026-08-15T00:59:59Z"},
            },
        )
        adapter["screen_states"].append(node)
        route_edge = copy.deepcopy(edge)
        route_edge.update(
            transition_id=f"transition-a008-{category}", to_node_id=node["node_id"],
            evidence_ids=list(nodes[0]["evidence_ids"] + ids),
        )
        adapter["transitions"].append(route_edge)
        branch["screen_node_ids"].append(node["node_id"])
        branch["transition_ids"].append(route_edge["transition_id"])
        all_ids.extend(ids)
    by_scenario(adapter, "scenarios", "A008")["evidence_ids"] = all_ids
    branch["evidence_ids"] = all_ids
    adapter["evidence_registry"] = sorted(subject._all_evidence_ids(adapter))
    subject.validate_adapter(adapter)
    bundle = subject.build_bundle(adapter, subject.load_contract())
    rows = list(csv.DictReader(io.StringIO(bundle[subject.SCREEN_OUTPUT].decode("utf-8"))))
    for row in rows:
        if row["scenario_id"] == "A008" and row["state_category"] in {"help", "legal"}:
            row["state_category"] = "profile"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=subject.SCREEN_HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    bundle[subject.SCREEN_OUTPUT] = stream.getvalue().encode("utf-8")
    _rehash(bundle, subject.SCREEN_OUTPUT)
    with pytest.raises(subject.ContractError, match="REPORT_READ_ONLY_ACCOUNT_ROUTES_INCOMPLETE"):
        subject.validate_bundle(bundle)


def test_report_rejects_hash_consistent_nonterminal_status_enum() -> None:
    bundle = subject.build_bundle(baseline(), subject.load_contract())
    for path, headers in (
        (subject.SCENARIO_OUTPUT, subject.SCENARIO_HEADERS),
        (subject.SCREEN_OUTPUT, subject.SCREEN_HEADERS),
        (subject.TRANSITION_OUTPUT, subject.TRANSITION_HEADERS),
        (subject.BRANCH_OUTPUT, subject.BRANCH_HEADERS),
    ):
        rows = list(csv.DictReader(io.StringIO(bundle[path].decode("utf-8"))))
        for row in rows:
            if row["scenario_id"] == "A011":
                row["status"] = "banana"
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        bundle[path] = stream.getvalue().encode("utf-8")
        _rehash(bundle, path)
    with pytest.raises(subject.ContractError, match="REPORT_TERMINAL_STATUS_INVALID"):
        subject.validate_bundle(bundle)


def test_every_terminal_ledger_publishes_public_safe_evidence_ids() -> None:
    bundle = subject.build_bundle(baseline(), subject.load_contract())
    for path in (
        subject.SCENARIO_OUTPUT, subject.SCREEN_OUTPUT, subject.TRANSITION_OUTPUT,
        subject.BRANCH_OUTPUT, subject.ANOMALY_OUTPUT, subject.BOUNDARY_OUTPUT,
        subject.CLEANUP_OUTPUT,
    ):
        rows = list(csv.DictReader(io.StringIO(bundle[path].decode("utf-8"))))
        assert rows and all(row["evidence_ids"] for row in rows)


def test_validate_only_has_no_runtime_or_writes(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["--validate-only"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {"mode": "validate_only", "runtime_access": False, "status": "pass", "task_id": "TASK-045A", "writes": False}


def test_preflight_requires_canonical_ignored_adapter(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    candidate = tmp_path / "adapter.json"
    candidate.write_text(json.dumps(baseline()), encoding="utf-8")
    assert subject.main(["--preflight", "--adapter-input", str(candidate)]) == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "ADAPTER_PATH_INVALID"


def test_execute_requires_explicit_adapter_passport_and_allow_flag(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["--execute"]) == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "EXECUTE_GATE_REQUIRED"


def test_report_hash_tamper_is_rejected() -> None:
    bundle = subject.build_bundle(baseline(), subject.load_contract())
    bundle[subject.SCREEN_OUTPUT] += b"tamper\n"
    with pytest.raises(subject.ContractError, match="REPORT_ARTIFACT_HASH_INVALID"):
        subject.validate_bundle(bundle)


def test_report_cannot_hide_unknown_session_covered_branch() -> None:
    bundle = subject.build_bundle(baseline(), subject.load_contract())
    text = bundle[subject.BRANCH_OUTPUT].decode("utf-8")
    text = text.replace(
        "branch-003,A003,phone_independent,true,true,blocked_by_external_state",
        "branch-003,A003,phone_independent,true,true,covered",
        1,
    )
    bundle[subject.BRANCH_OUTPUT] = text.encode("utf-8")
    report = json.loads(bundle[subject.REPORT_OUTPUT])
    artifact = next(row for row in report["artifacts"] if row["reference"] == subject._repo_ref(subject.BRANCH_OUTPUT))
    artifact["sha256"] = subject.shared._sha(bundle[subject.BRANCH_OUTPUT])
    bundle[subject.REPORT_OUTPUT] = subject._json_bytes(report)
    with pytest.raises(subject.ContractError, match="REPORT_UNKNOWN_SESSION_FALSE_PASS"):
        subject.validate_bundle(bundle)


def test_tracked_report_bundle_validates() -> None:
    if not subject.REPORT_OUTPUT.exists():
        pytest.skip("tracked TASK-045A blocked baseline not materialized yet")
    subject.validate_bundle(subject._tracked_bundle())

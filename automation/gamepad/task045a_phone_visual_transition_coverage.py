"""Static-only TASK-045A Phone Full visual-transition evidence authority.

The runner never invokes ADB, an APK, an Android device, the target app, a
network service, a QR target or another external application.  It validates a
strict ignored adapter and publishes only category-level public-safe ledgers.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import stat
import tempfile
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_IMPORT_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_IMPORT_ROOT))

from automation.gamepad import task045_paired_virtual_gamepad as shared


TASK_ID = "TASK-045A"
SCHEMA_VERSION = "task045a-phone-visual-transition-adapter-v1"
SCENARIO_VERSION = "task045a-phone-visual-transition-scenarios-v1"
REPORT_SCHEMA_VERSION = "evidence-report-envelope-v2"
PRODUCTION_SAFETY = "PROD_SAFE_STATIC_BLOCKED_BASELINE"

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = REPO_ROOT / "docs/qa/epics/scenarios/task045a_phone_visual_transition_branches.csv"
ADAPTER_SCHEMA = REPO_ROOT / "docs/qa/schemas/task045a-phone-visual-transition-adapter-v1.schema.json"
REPORT_ENVELOPE_SCHEMA = REPO_ROOT / "docs/qa/schemas/evidence-report-envelope-v2.schema.json"
REPORT_OUTPUT = REPO_ROOT / "docs/qa/reports/task045a_phone_visual_transition_coverage.summary.json"
SCENARIO_OUTPUT = REPO_ROOT / "docs/qa/reports/task045a_phone_visual_transition_coverage.scenario-ledger.csv"
SCREEN_OUTPUT = REPO_ROOT / "docs/qa/reports/task045a_phone_visual_transition_coverage.screen-state-ledger.csv"
TRANSITION_OUTPUT = REPO_ROOT / "docs/qa/reports/task045a_phone_visual_transition_coverage.transition-ledger.csv"
BRANCH_OUTPUT = REPO_ROOT / "docs/qa/reports/task045a_phone_visual_transition_coverage.branch-closure-ledger.csv"
ANOMALY_OUTPUT = REPO_ROOT / "docs/qa/reports/task045a_phone_visual_transition_coverage.anomaly-ledger.csv"
BOUNDARY_OUTPUT = REPO_ROOT / "docs/qa/reports/task045a_phone_visual_transition_coverage.boundary-ledger.csv"
CLEANUP_OUTPUT = REPO_ROOT / "docs/qa/reports/task045a_phone_visual_transition_coverage.cleanup-ledger.csv"

LOCAL_ROOT = REPO_ROOT / ".qa_local/evidence/task-045a"
LOCAL_ADAPTER = LOCAL_ROOT / "runtime-adapter.local.json"
LOCAL_SESSION_PASSPORT = LOCAL_ROOT / "synthetic-session-passport.local.json"

EXPECTED_IDS = tuple(f"A{index:03d}" for index in range(1, 18))
SESSION_DEPENDENT_IDS = frozenset({
    "A002", "A003", "A004", "A005", "A006", "A007", "A008",
    "A009", "A010", "A013", "A014", "A015",
})
PAIRED_IDS = frozenset({"A016"})
COVERAGE_STATUSES = {
    "covered", "blocked_by_boundary", "blocked_by_tooling",
    "blocked_by_external_state", "not_run_out_of_scope",
}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
MAX_EVIDENCE_AGE = timedelta(hours=24)
MAX_CLOCK_SKEW = timedelta(minutes=5)
NON_PHONE_PREFIX_RE = re.compile(r"^(?:tv|television|paired|cross-device)[_.:-]", re.IGNORECASE)
PACKAGE_LIKE_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9_]*\.)+[A-Za-z][A-Za-z0-9_]*$")
HASH_LIKE_RE = re.compile(r"^[0-9A-Fa-f]{32,}$")

SCENARIO_HEADERS = (
    "scenario_id", "priority", "branch_alias", "session_scope", "requires_tv",
    "status", "evidence_status", "evidence_count", "evidence_ids", "reason_code",
)
SCREEN_HEADERS = (
    "node_id", "scenario_id", "screen_alias", "state_alias", "state_category",
    "session_scope", "surface_side", "observed", "evidence_origin", "audit_only",
    "counts_as_product_coverage", "status", "evidence_status", "evidence_count", "evidence_ids",
    "screenshot_present", "visual_inspection", "ui_tree_present", "runner_log_present",
    "recurrence_status", "prior_node_id", "long_list_segment", "menu_state",
    "overlay_category", "xml_visual_match", "reason_code",
)
TRANSITION_HEADERS = (
    "transition_id", "scenario_id", "from_node_id", "to_node_id", "action_category",
    "session_scope", "edge_scope", "requires_tv", "attempt_index", "recovery_attempt",
    "recovery_of_transition_id", "status", "evidence_status", "evidence_count", "evidence_ids",
    "first_failure_retained", "boundary_id", "anomaly_id", "reason_code",
)
BRANCH_HEADERS = (
    "branch_id", "scenario_id", "coverage_scope", "approved_scope", "declared_reachable", "status",
    "screen_node_count", "transition_count", "evidence_status", "evidence_count", "evidence_ids",
    "reason_code",
)
ANOMALY_HEADERS = (
    "anomaly_id", "classification", "trigger_category", "expected_result_category",
    "observed_result_category", "public_safe_screen_alias", "evidence_status",
    "cause_evidence_status", "cause_category", "test_design_implication",
    "first_failure_retained", "evidence_count", "evidence_ids", "reason_code",
)
BOUNDARY_HEADERS = (
    "boundary_id", "category", "status", "external_action_performed",
    "payment_or_session_started", "account_mutated", "network_changed", "qr_traversed",
    "evidence_status", "evidence_count", "evidence_ids", "reason_code",
)
CLEANUP_HEADERS = (
    "cleanup_id", "status", "target_app_force_stopped", "home_restored",
    "existing_session_preserved", "external_app_opened", "payment_or_session_started",
    "account_mutated", "network_changed", "paired_state_observed", "evidence_status",
    "evidence_count", "evidence_ids", "reason_code",
)


class ContractError(Exception):
    """Fail-closed public contract error."""


def _is_reparse_point(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _fixed(path: Path, *, suffix: str) -> Path:
    absolute = path.absolute()
    try:
        resolved = path.resolve(strict=True)
        root = REPO_ROOT.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractError("FIXED_INPUT_MISSING") from exc
    if (
        resolved != absolute or not resolved.is_relative_to(root)
        or resolved.suffix.lower() != suffix or resolved.is_symlink()
        or _is_reparse_point(absolute)
    ):
        raise ContractError("FIXED_INPUT_INVALID")
    return resolved


def _fixed_local_input(path: Path, expected: Path, *, code: str) -> Path:
    absolute = path.absolute()
    if absolute != expected.absolute():
        raise ContractError(code)
    try:
        resolved = path.resolve(strict=True)
        root = LOCAL_ROOT.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractError(code) from exc
    if (
        resolved != absolute or not resolved.is_relative_to(root)
        or resolved.suffix.lower() != ".json" or resolved.is_symlink()
        or _is_reparse_point(absolute)
    ):
        raise ContractError(code)
    return resolved


def _safe_public_identifiers(value: Any, *, key: str = "") -> None:
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            _safe_public_identifiers(child, key=str(child_key))
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            _safe_public_identifiers(child, key=key)
        return
    if not isinstance(value, str):
        return
    lowered = key.lower()
    is_public_identifier = (
        lowered == "alias" or lowered.endswith("_alias")
        or lowered.endswith("_id") or lowered.endswith("_ids")
    )
    if is_public_identifier and PACKAGE_LIKE_RE.fullmatch(value):
        raise ContractError("PUBLIC_IDENTIFIER_PACKAGE_LIKE")
    if is_public_identifier and HASH_LIKE_RE.fullmatch(value):
        raise ContractError("PUBLIC_IDENTIFIER_HASH_LIKE")


def _repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ContractError("PUBLIC_REFERENCE_OUTSIDE_REPOSITORY") from exc


def _utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractError("TIMESTAMP_INVALID")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ContractError("TIMESTAMP_INVALID") from exc


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _read_json(path: Path) -> dict[str, Any]:
    fixed = _fixed(path, suffix=".json")
    return _read_fixed_json(fixed)


def _read_fixed_json(fixed: Path) -> dict[str, Any]:
    try:
        value = json.loads(fixed.read_text(encoding="utf-8"), object_pairs_hook=shared._json_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError, shared.ContractError) as exc:
        raise ContractError("JSON_INPUT_INVALID") from exc
    if not isinstance(value, dict):
        raise ContractError("JSON_INPUT_INVALID")
    return value


def load_contract() -> list[dict[str, str]]:
    fixed = _fixed(CATALOG, suffix=".csv")
    try:
        rows = list(csv.DictReader(io.StringIO(fixed.read_text(encoding="utf-8"))))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ContractError("SCENARIO_CONTRACT_INVALID") from exc
    expected_headers = {
        "scenario_id", "priority", "branch_alias", "screen_family", "transition_family",
        "session_scope", "approved_scope", "requires_tv", "boundary_category",
        "evidence_requirement",
    }
    if not rows or set(rows[0]) != expected_headers:
        raise ContractError("SCENARIO_CONTRACT_INVALID")
    if tuple(row["scenario_id"] for row in rows) != EXPECTED_IDS:
        raise ContractError("SCENARIO_IDS_INVALID")
    if any(row["priority"] != "P0" or row["approved_scope"] != "true" for row in rows):
        raise ContractError("SCENARIO_SCOPE_INVALID")
    for row in rows:
        shared._safe_public_value(row)
    return rows


def _load_schema() -> dict[str, Any]:
    schema = _read_json(ADAPTER_SCHEMA)
    if (
        schema.get("$id") != _repo_ref(ADAPTER_SCHEMA)
        or schema.get("additionalProperties") is not False
        or schema.get("properties", {}).get("scenarios", {}).get("minItems") != 17
    ):
        raise ContractError("ADAPTER_SCHEMA_INVALID")
    return schema


def _validate_schema_instance(instance: Any, schema: Mapping[str, Any]) -> None:
    try:
        shared._validate_schema_instance(instance, schema, root=schema)
    except shared.ContractError as exc:
        raise ContractError(str(exc)) from exc


def _all_evidence_ids(adapter: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()
    for group in ("scenarios", "screen_states", "transitions", "branch_closure", "anomalies", "boundaries"):
        for row in adapter[group]:
            values.update(row["evidence_ids"])
    values.update(adapter["cleanup"]["evidence_ids"])
    return values


def _reject_non_phone_identifier(value: Any, code: str) -> None:
    if not isinstance(value, str):
        raise ContractError(code)
    normalized = (
        value.lower().replace("no-tv", "").replace("no_tv", "")
        .replace("no.television", "").replace("no_television", "")
    )
    tokens = {token for token in re.split(r"[_.:-]+", normalized) if token}
    if NON_PHONE_PREFIX_RE.search(value) or "cross-device" in normalized or tokens.intersection({"tv", "television", "paired"}):
        raise ContractError(code)


def _validate_fresh_modalities(row: Mapping[str, Any], generated: datetime) -> None:
    modalities = row["modalities"]
    if not isinstance(modalities, dict) or set(modalities) != {"screenshot", "ui_tree", "runner_log"}:
        raise ContractError("FRESH_MODALITIES_INVALID")
    if any(not isinstance(modalities[key], dict) for key in modalities):
        raise ContractError("FRESH_MODALITIES_REQUIRED")
    if modalities["screenshot"].get("visual_inspection") is not True:
        raise ContractError("VISUAL_INSPECTION_REQUIRED")
    ids: set[str] = set()
    for modality in modalities.values():
        evidence_id = modality.get("evidence_id")
        captured = _utc(modality.get("captured_at_utc"))
        if not isinstance(evidence_id, str) or evidence_id in ids:
            raise ContractError("MODALITY_EVIDENCE_ID_INVALID")
        ids.add(evidence_id)
        if captured > generated + MAX_CLOCK_SKEW or generated - captured > MAX_EVIDENCE_AGE:
            raise ContractError("MODALITY_FRESHNESS_INVALID")
    if not ids.issubset(set(row["evidence_ids"])):
        raise ContractError("MODALITY_EVIDENCE_REGISTRY_INVALID")


def validate_adapter(adapter: Mapping[str, Any]) -> None:
    schema = _load_schema()
    _validate_schema_instance(adapter, schema)
    shared._safe_public_value(adapter)
    _safe_public_identifiers(adapter)

    if adapter["task_id"] != TASK_ID or adapter["schema_version"] != SCHEMA_VERSION:
        raise ContractError("ADAPTER_VERSION_INVALID")
    if adapter["scenario_contract_version"] != SCENARIO_VERSION:
        raise ContractError("SCENARIO_VERSION_INVALID")
    generated = _utc(adapter["generated_at_utc"])
    preflight = adapter["lane_preflight"]
    session_proven = (
        preflight["active_session_provenance"] == "approved_synthetic_fixture"
        and preflight["session_passport_status"] == "proven"
    )
    if (
        preflight["active_session_provenance"] == "approved_synthetic_fixture"
    ) != (preflight["session_passport_status"] == "proven"):
        raise ContractError("SESSION_PASSPORT_RELATION_INVALID")
    if preflight["runtime_gate"] == "GO" and not (
        preflight["reviewer_gate"] and preflight["phone_status"] == "READY"
        and preflight["ignored_evidence_storage_ready"] and session_proven
        and adapter["build_ref"]["compatibility_status"] == "confirmed_for_task045a"
    ):
        raise ContractError("RUNTIME_GO_PREFLIGHT_INVALID")
    if preflight["runtime_gate"] == "GO" and (
        generated > _now_utc() + MAX_CLOCK_SKEW or _now_utc() - generated > MAX_EVIDENCE_AGE
    ):
        raise ContractError("RUNTIME_ADAPTER_FRESHNESS_INVALID")

    prior = adapter["prior_audit"]
    if prior["audit_only"] is not True or prior["counts_as_product_coverage"] is not False:
        raise ContractError("PRIOR_AUDIT_ELIGIBILITY_INVALID")

    scenario_ids = [row["scenario_id"] for row in adapter["scenarios"]]
    if tuple(scenario_ids) != EXPECTED_IDS or len(set(scenario_ids)) != 17:
        raise ContractError("SCENARIO_RECONCILIATION_INVALID")

    nodes = {row["node_id"]: row for row in adapter["screen_states"]}
    if len(nodes) != len(adapter["screen_states"]):
        raise ContractError("SCREEN_NODE_DUPLICATE")
    if set(row["scenario_id"] for row in nodes.values()) != set(EXPECTED_IDS):
        raise ContractError("SCREEN_SCENARIO_COVERAGE_INCOMPLETE")
    for row in nodes.values():
        scenario_id = row["scenario_id"]
        if not row["evidence_ids"]:
            raise ContractError("SCREEN_EVIDENCE_REQUIRED")
        if row["evidence_origin"] == "quarantined_task045_audit" and not (
            row["audit_only"] is True and row["counts_as_product_coverage"] is False
        ):
            raise ContractError("QUARANTINED_EVIDENCE_CANNOT_COVER")
        if row["audit_only"] and row["counts_as_product_coverage"]:
            raise ContractError("AUDIT_ONLY_CANNOT_COVER")
        if row["status"] == "covered":
            if not (
                row["observed"] is True
                and row["surface_side"] == "phone"
                and row["evidence_origin"] == "fresh_task045a"
                and row["audit_only"] is False
                and row["counts_as_product_coverage"] is True
                and row["evidence_status"] == "confirmed"
            ):
                raise ContractError("NON_PHONE_SCREEN_CANNOT_COVER")
            if row["session_scope"] == "paired_only":
                raise ContractError("PAIRED_SCREEN_CANNOT_COUNT_AS_PHONE_COVERAGE")
            for key in ("screen_alias", "state_alias", "state_category"):
                _reject_non_phone_identifier(row[key], "NON_PHONE_SCREEN_ALIAS_INVALID")
            for evidence_id in row["evidence_ids"]:
                _reject_non_phone_identifier(evidence_id, "NON_PHONE_EVIDENCE_ID_INVALID")
            if scenario_id in SESSION_DEPENDENT_IDS and not session_proven:
                raise ContractError("UNVERIFIED_SESSION_CANNOT_COVER_SCREEN")
            if scenario_id in PAIRED_IDS and preflight["tv_status"] != "READY":
                raise ContractError("MISSING_TV_CANNOT_COVER_SCREEN")
            _validate_fresh_modalities(row, generated)
            modality_ids = {item["evidence_id"] for item in row["modalities"].values()}
            if set(row["evidence_ids"]) != modality_ids:
                raise ContractError("NON_PHONE_EVIDENCE_SUBSTITUTION_INVALID")
        if row["xml_visual_match"] == "confirmed_mismatch" and not any(
            anomaly["public_safe_screen_alias"] == row["screen_alias"]
            for anomaly in adapter["anomalies"]
        ):
            raise ContractError("XML_VISUAL_MISMATCH_REQUIRES_ANOMALY")
        if row["recurrence_status"] == "recurrence" and row["prior_node_id"] not in nodes:
            raise ContractError("RECURRENCE_LINK_INVALID")

    transitions = {row["transition_id"]: row for row in adapter["transitions"]}
    if len(transitions) != len(adapter["transitions"]):
        raise ContractError("TRANSITION_DUPLICATE")
    if set(row["scenario_id"] for row in transitions.values()) != set(EXPECTED_IDS):
        raise ContractError("TRANSITION_SCENARIO_COVERAGE_INCOMPLETE")
    boundary_ids = {row["boundary_id"] for row in adapter["boundaries"]}
    anomaly_ids = {row["anomaly_id"] for row in adapter["anomalies"]}
    edge_attempts: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for row in transitions.values():
        if not row["evidence_ids"]:
            raise ContractError("TRANSITION_EVIDENCE_REQUIRED")
        if row["from_node_id"] not in nodes or row["to_node_id"] not in nodes:
            raise ContractError("TRANSITION_NODE_LINK_INVALID")
        if (
            nodes[row["from_node_id"]]["scenario_id"] != row["scenario_id"]
            or nodes[row["to_node_id"]]["scenario_id"] != row["scenario_id"]
        ):
            raise ContractError("TRANSITION_SCENARIO_LINK_INVALID")
        if row["boundary_id"] != "none" and row["boundary_id"] not in boundary_ids:
            raise ContractError("TRANSITION_BOUNDARY_LINK_INVALID")
        if row["anomaly_id"] != "none" and row["anomaly_id"] not in anomaly_ids:
            raise ContractError("TRANSITION_ANOMALY_LINK_INVALID")
        edge_attempts.setdefault((row["from_node_id"], row["to_node_id"], row["action_category"]), []).append(row)
        if row["status"] == "covered":
            if row["edge_scope"] != "phone_independent" or row["requires_tv"] or row["session_scope"] == "paired_only":
                raise ContractError("NON_PHONE_EDGE_CANNOT_COVER")
            _reject_non_phone_identifier(row["action_category"], "NON_PHONE_EDGE_ALIAS_INVALID")
            for evidence_id in row["evidence_ids"]:
                _reject_non_phone_identifier(evidence_id, "NON_PHONE_EVIDENCE_ID_INVALID")
            if nodes[row["from_node_id"]]["status"] != "covered" or nodes[row["to_node_id"]]["status"] != "covered":
                raise ContractError("COVERED_TRANSITION_REQUIRES_COVERED_NODES")
            if row["evidence_status"] != "confirmed" or not row["evidence_ids"]:
                raise ContractError("COVERED_TRANSITION_EVIDENCE_INVALID")
            if row["from_node_id"] == row["to_node_id"]:
                raise ContractError("COVERED_TRANSITION_SELF_LOOP_INVALID")
            if row["attempt_index"] < 1:
                raise ContractError("COVERED_TRANSITION_ATTEMPT_INVALID")
            if row["scenario_id"] in SESSION_DEPENDENT_IDS and not session_proven:
                raise ContractError("UNVERIFIED_SESSION_CANNOT_COVER_TRANSITION")
            if row["requires_tv"] and preflight["tv_status"] != "READY":
                raise ContractError("MISSING_TV_CANNOT_COVER_TRANSITION")
            linked_evidence = set(nodes[row["from_node_id"]]["evidence_ids"]) | set(nodes[row["to_node_id"]]["evidence_ids"])
            if set(row["evidence_ids"]) != linked_evidence:
                raise ContractError("TRANSITION_CHECKPOINT_EVIDENCE_INCOMPLETE")
        if row["recovery_attempt"]:
            prior_id = row["recovery_of_transition_id"]
            if prior_id not in transitions or prior_id == row["transition_id"]:
                raise ContractError("TRANSITION_RECOVERY_LINK_INVALID")
            if not transitions[prior_id]["first_failure_retained"]:
                raise ContractError("FIRST_FAILURE_NOT_RETAINED")
        elif row["recovery_of_transition_id"] != "none":
            raise ContractError("TRANSITION_RECOVERY_LINK_INVALID")
    for attempts in edge_attempts.values():
        if len(attempts) > 2 or len({row["attempt_index"] for row in attempts}) != len(attempts):
            raise ContractError("TRANSITION_ATTEMPT_BUDGET_EXCEEDED")
        if sum(bool(row["recovery_attempt"]) for row in attempts) > 1:
            raise ContractError("TRANSITION_RECOVERY_BUDGET_EXCEEDED")

    branches = {row["scenario_id"]: row for row in adapter["branch_closure"]}
    if set(branches) != set(EXPECTED_IDS) or len(branches) != 17:
        raise ContractError("BRANCH_CLOSURE_RECONCILIATION_INVALID")
    for scenario_id, row in branches.items():
        if row["approved_scope"] and row["declared_reachable"] and row["status"] == "not_run_out_of_scope":
            raise ContractError("REACHABLE_APPROVED_BRANCH_OUT_OF_SCOPE_INVALID")
        if any(node_id not in nodes for node_id in row["screen_node_ids"]):
            raise ContractError("BRANCH_SCREEN_LINK_INVALID")
        if any(transition_id not in transitions for transition_id in row["transition_ids"]):
            raise ContractError("BRANCH_TRANSITION_LINK_INVALID")
        scenario_node_ids = {node_id for node_id, item in nodes.items() if item["scenario_id"] == scenario_id}
        scenario_transition_ids = {transition_id for transition_id, item in transitions.items() if item["scenario_id"] == scenario_id}
        if set(row["screen_node_ids"]) != scenario_node_ids or set(row["transition_ids"]) != scenario_transition_ids:
            raise ContractError("BRANCH_GRAPH_RECONCILIATION_INVALID")
        scenario = next(item for item in adapter["scenarios"] if item["scenario_id"] == scenario_id)
        if scenario["status"] != row["status"]:
            raise ContractError("SCENARIO_BRANCH_STATUS_MISMATCH")
        linked_evidence = {
            evidence_id for node_id in scenario_node_ids for evidence_id in nodes[node_id]["evidence_ids"]
        } | {
            evidence_id for transition_id in scenario_transition_ids for evidence_id in transitions[transition_id]["evidence_ids"]
        }
        if not linked_evidence or set(row["evidence_ids"]) != linked_evidence or set(scenario["evidence_ids"]) != linked_evidence:
            raise ContractError("BRANCH_EVIDENCE_RECONCILIATION_INVALID")
        if row["status"] == "covered":
            if row["coverage_scope"] != "phone_independent" or scenario_id in PAIRED_IDS:
                raise ContractError("NON_PHONE_BRANCH_CANNOT_COVER")
            if not all(nodes[node_id]["status"] == "covered" for node_id in row["screen_node_ids"]):
                raise ContractError("BRANCH_COVERED_WITH_BLOCKED_SCREEN")
            if not all(transitions[item]["status"] == "covered" for item in row["transition_ids"]):
                raise ContractError("BRANCH_COVERED_WITH_BLOCKED_TRANSITION")
            if row["evidence_status"] != "confirmed" or not row["evidence_ids"]:
                raise ContractError("BRANCH_COVERAGE_EVIDENCE_INVALID")
            if any(transitions[item]["from_node_id"] == transitions[item]["to_node_id"] for item in row["transition_ids"]):
                raise ContractError("COVERED_BRANCH_SELF_LOOP_INVALID")
            endpoints = {
                node_id
                for transition_id in row["transition_ids"]
                for node_id in (transitions[transition_id]["from_node_id"], transitions[transition_id]["to_node_id"])
            }
            if endpoints != scenario_node_ids:
                raise ContractError("COVERED_BRANCH_DISCONNECTED_NODE")
            adjacency = {node_id: set() for node_id in scenario_node_ids}
            indegree = {node_id: 0 for node_id in scenario_node_ids}
            for transition_id in row["transition_ids"]:
                edge = transitions[transition_id]
                adjacency[edge["from_node_id"]].add(edge["to_node_id"])
                indegree[edge["to_node_id"]] += 1
            starts = [node_id for node_id, degree in indegree.items() if degree == 0] or [next(iter(scenario_node_ids))]
            def reachable(start: str) -> set[str]:
                seen: set[str] = set()
                pending = [start]
                while pending:
                    current = pending.pop()
                    if current in seen:
                        continue
                    seen.add(current)
                    pending.extend(adjacency[current] - seen)
                return seen
            if not any(reachable(start) == scenario_node_ids for start in starts):
                raise ContractError("COVERED_BRANCH_DIRECTED_GRAPH_DISCONNECTED")
        if scenario_id in SESSION_DEPENDENT_IDS and not session_proven and row["status"] == "covered":
            raise ContractError("UNVERIFIED_SESSION_CANNOT_COVER_BRANCH")

    for scenario_id, required_segments in {"A004": {"initial", "later"}, "A007": {"initial", "later"}}.items():
        if branches[scenario_id]["status"] == "covered":
            found = {nodes[item]["long_list_segment"] for item in branches[scenario_id]["screen_node_ids"]}
            if not required_segments.issubset(found):
                raise ContractError("LONG_LIST_SEGMENTS_INCOMPLETE")
    if branches["A005"]["status"] == "covered":
        found_menu = {nodes[item]["menu_state"] for item in branches["A005"]["screen_node_ids"]}
        if not {"expanded", "collapsed"}.issubset(found_menu):
            raise ContractError("MENU_STATES_INCOMPLETE")
    if branches["A006"]["status"] == "covered":
        branch_nodes = [nodes[item] for item in branches["A006"]["screen_node_ids"]]
        overlay_ids = {item["node_id"] for item in branch_nodes if item["overlay_category"] != "none"}
        recovered_ids = {
            item["node_id"] for item in branch_nodes
            if item["recurrence_status"] == "recurrence" and item["prior_node_id"] in branches["A006"]["screen_node_ids"]
        }
        branch_edges = [transitions[item] for item in branches["A006"]["transition_ids"]]
        overlay_entries = [edge for edge in branch_edges if edge["to_node_id"] in overlay_ids]
        recovery_edges = [edge for edge in branch_edges if edge["from_node_id"] in overlay_ids and edge["to_node_id"] in recovered_ids]
        if (
            len(branch_nodes) < 3 or not overlay_entries or not recovery_edges
            or not any(edge["recovery_attempt"] and edge["recovery_of_transition_id"] in {item["transition_id"] for item in overlay_entries} for edge in recovery_edges)
        ):
            raise ContractError("SEARCH_OVERLAY_RECOVERY_INCOMPLETE")
    if branches["A008"]["status"] == "covered":
        route_categories = {nodes[item]["state_category"] for item in branches["A008"]["screen_node_ids"]}
        if not {"profile", "settings", "help", "legal"}.issubset(route_categories):
            raise ContractError("READ_ONLY_ACCOUNT_ROUTES_INCOMPLETE")
    if branches["A013"]["status"] == "covered":
        recurrence_ids = {
            item for item in branches["A013"]["screen_node_ids"]
            if nodes[item]["recurrence_status"] == "recurrence"
            and nodes[item]["prior_node_id"] in branches["A013"]["screen_node_ids"]
        }
        if not recurrence_ids or not any(
            transitions[item]["to_node_id"] in recurrence_ids
            and transitions[item]["action_category"] == "background_foreground_recurrence"
            for item in branches["A013"]["transition_ids"]
        ):
            raise ContractError("LIFECYCLE_RECURRENCE_INCOMPLETE")
    if branches["A014"]["status"] == "covered":
        if len(branches["A014"]["screen_node_ids"]) < 2 or not any(
            transitions[item]["action_category"] == "force_stop_relaunch"
            for item in branches["A014"]["transition_ids"]
        ):
            raise ContractError("FORCE_STOP_RELAUNCH_CHECKPOINTS_INCOMPLETE")
    if branches["A015"]["status"] == "covered":
        branch_nodes = [nodes[item] for item in branches["A015"]["screen_node_ids"]]
        branch_transitions = [transitions[item] for item in branches["A015"]["transition_ids"]]
        boundary_node_ids = {item["node_id"] for item in branch_nodes if item["state_category"] == "boundary"}
        recovered_node_ids = {item["node_id"] for item in branch_nodes if item["recurrence_status"] == "recurrence"}
        boundary_entries = [edge for edge in branch_transitions if edge["to_node_id"] in boundary_node_ids and edge["boundary_id"] in boundary_ids]
        boundary_recoveries = [edge for edge in branch_transitions if edge["from_node_id"] in boundary_node_ids and edge["to_node_id"] in recovered_node_ids]
        if (
            len(branch_nodes) < 3
            or not boundary_entries or not boundary_recoveries
            or not any(edge["recovery_attempt"] and edge["recovery_of_transition_id"] in {item["transition_id"] for item in boundary_entries} for edge in boundary_recoveries)
        ):
            raise ContractError("BOUNDARY_CAPTURE_RECOVERY_INCOMPLETE")

    if not any(row["anomaly_id"] == "TASK045A-PROCESS-001" for row in adapter["anomalies"]):
        raise ContractError("REQUIRED_PROCESS_ANOMALY_MISSING")
    if any(not row["first_failure_retained"] for row in adapter["anomalies"]):
        raise ContractError("ANOMALY_FIRST_FAILURE_NOT_RETAINED")
    for row in adapter["boundaries"]:
        if any(row[key] for key in (
            "external_action_performed", "payment_or_session_started", "account_mutated",
            "network_changed", "qr_traversed",
        )):
            raise ContractError("FORBIDDEN_BOUNDARY_ACTION_RECORDED")
    cleanup = adapter["cleanup"]
    if any(cleanup[key] for key in (
        "external_app_opened", "payment_or_session_started", "account_mutated",
        "network_changed", "paired_state_observed",
    )):
        raise ContractError("FORBIDDEN_CLEANUP_STATE_RECORDED")
    if cleanup["status"] == "covered" and not (
        cleanup["target_app_force_stopped"] and cleanup["home_restored"]
        and cleanup["existing_session_preserved"] and cleanup["evidence_status"] == "confirmed"
        and cleanup["evidence_ids"]
    ):
        raise ContractError("CLEANUP_COVERAGE_INVALID")

    referenced = _all_evidence_ids(adapter)
    if referenced != set(adapter["evidence_registry"]):
        raise ContractError("EVIDENCE_REGISTRY_MISMATCH")


def _scenario_rows(adapter: Mapping[str, Any], catalog: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    by_id = {row["scenario_id"]: row for row in adapter["scenarios"]}
    return [{
        "scenario_id": item["scenario_id"],
        "priority": item["priority"],
        "branch_alias": item["branch_alias"],
        "session_scope": item["session_scope"],
        "requires_tv": item["requires_tv"],
        "status": by_id[item["scenario_id"]]["status"],
        "evidence_status": by_id[item["scenario_id"]]["evidence_status"],
        "evidence_count": len(by_id[item["scenario_id"]]["evidence_ids"]),
        "evidence_ids": ";".join(by_id[item["scenario_id"]]["evidence_ids"]),
        "reason_code": by_id[item["scenario_id"]]["reason_code"],
    } for item in catalog]


def _screen_rows(adapter: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in adapter["screen_states"]:
        modalities = item["modalities"]
        shot = modalities["screenshot"]
        rows.append({
            **{key: item[key] for key in (
                "node_id", "scenario_id", "screen_alias", "state_alias", "state_category",
                "session_scope", "surface_side", "observed", "evidence_origin", "audit_only",
                "counts_as_product_coverage", "status", "evidence_status",
            )},
            "evidence_count": len(item["evidence_ids"]),
            "evidence_ids": ";".join(item["evidence_ids"]),
            "screenshot_present": shot is not None,
            "visual_inspection": bool(shot and shot.get("visual_inspection") is True),
            "ui_tree_present": modalities["ui_tree"] is not None,
            "runner_log_present": modalities["runner_log"] is not None,
            **{key: item[key] for key in (
                "recurrence_status", "prior_node_id", "long_list_segment", "menu_state",
                "overlay_category", "xml_visual_match", "reason_code",
            )},
        })
    return rows


def _transition_rows(adapter: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{
        **{key: item[key] for key in TRANSITION_HEADERS if key not in {"evidence_count", "evidence_ids"}},
        "evidence_count": len(item["evidence_ids"]),
        "evidence_ids": ";".join(item["evidence_ids"]),
    } for item in adapter["transitions"]]


def _branch_rows(adapter: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{
        "branch_id": item["branch_id"], "scenario_id": item["scenario_id"],
        "coverage_scope": item["coverage_scope"],
        "approved_scope": item["approved_scope"], "declared_reachable": item["declared_reachable"],
        "status": item["status"], "screen_node_count": len(item["screen_node_ids"]),
        "transition_count": len(item["transition_ids"]), "evidence_status": item["evidence_status"],
        "evidence_count": len(item["evidence_ids"]), "evidence_ids": ";".join(item["evidence_ids"]),
        "reason_code": item["reason_code"],
    } for item in adapter["branch_closure"]]


def _anomaly_rows(adapter: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{
        **{key: item[key] for key in ANOMALY_HEADERS if key not in {"evidence_count", "evidence_ids"}},
        "evidence_count": len(item["evidence_ids"]),
        "evidence_ids": ";".join(item["evidence_ids"]),
    } for item in adapter["anomalies"]]


def _boundary_rows(adapter: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{
        **{key: item[key] for key in BOUNDARY_HEADERS if key not in {"evidence_count", "evidence_ids"}},
        "evidence_count": len(item["evidence_ids"]),
        "evidence_ids": ";".join(item["evidence_ids"]),
    } for item in adapter["boundaries"]]


def _cleanup_rows(adapter: Mapping[str, Any]) -> list[dict[str, Any]]:
    item = adapter["cleanup"]
    return [{
        **{key: item[key] for key in CLEANUP_HEADERS if key not in {"evidence_count", "evidence_ids"}},
        "evidence_count": len(item["evidence_ids"]),
        "evidence_ids": ";".join(item["evidence_ids"]),
    }]


def _csv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    return shared._csv_bytes(headers, rows)


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return shared._json_bytes(value)


def _overall(adapter: Mapping[str, Any]) -> str:
    statuses = [row["status"] for row in adapter["branch_closure"] if row["approved_scope"]]
    if statuses and all(value == "covered" for value in statuses) and adapter["cleanup"]["status"] == "covered":
        return "covered"
    if any(value == "covered" for value in statuses):
        return "partial_blocked"
    return "blocked"


def build_bundle(adapter: Mapping[str, Any], catalog: Sequence[Mapping[str, str]]) -> dict[Path, bytes]:
    validate_adapter(adapter)
    scenario_rows = _scenario_rows(adapter, catalog)
    screen_rows = _screen_rows(adapter)
    transition_rows = _transition_rows(adapter)
    branch_rows = _branch_rows(adapter)
    anomaly_rows = _anomaly_rows(adapter)
    boundary_rows = _boundary_rows(adapter)
    cleanup_rows = _cleanup_rows(adapter)
    ledger_outputs = {
        SCENARIO_OUTPUT: _csv_bytes(SCENARIO_HEADERS, scenario_rows),
        SCREEN_OUTPUT: _csv_bytes(SCREEN_HEADERS, screen_rows),
        TRANSITION_OUTPUT: _csv_bytes(TRANSITION_HEADERS, transition_rows),
        BRANCH_OUTPUT: _csv_bytes(BRANCH_HEADERS, branch_rows),
        ANOMALY_OUTPUT: _csv_bytes(ANOMALY_HEADERS, anomaly_rows),
        BOUNDARY_OUTPUT: _csv_bytes(BOUNDARY_HEADERS, boundary_rows),
        CLEANUP_OUTPUT: _csv_bytes(CLEANUP_HEADERS, cleanup_rows),
    }
    overall = _overall(adapter)
    blocked_reasons = sorted({
        row["reason_code"] for group in (
            adapter["scenarios"], adapter["screen_states"], adapter["transitions"],
            adapter["branch_closure"], adapter["boundaries"],
        ) for row in group if row["status"] != "covered"
    } | ({adapter["cleanup"]["reason_code"]} if adapter["cleanup"]["status"] != "covered" else set()))
    artifacts = [{
        "kind": kind,
        "reference": _repo_ref(path),
        "sha256": shared._sha(content),
        "evidence_status": "confirmed",
    } for kind, (path, content) in zip(
        ("scenario_ledger", "screen_state_ledger", "transition_ledger", "branch_closure_ledger",
         "anomaly_ledger", "boundary_ledger", "cleanup_ledger"),
        ledger_outputs.items(),
    )]
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "build_ref": {"alias": adapter["build_ref"]["alias"]},
        "target_alias": "phone-full-visual-transition-lane",
        "run_id": adapter["run_id"],
        "generated_at_utc": adapter["generated_at_utc"],
        "production_safety_classification": PRODUCTION_SAFETY if adapter["lane_preflight"]["runtime_gate"] == "BLOCK_RUNTIME" else "PROD_CONDITIONAL_PHONE_VISUAL_RUNTIME_INGEST",
        "execution_status": "blocked" if overall == "blocked" else overall,
        "coverage_status": overall,
        "evidence_status": "confirmed" if overall == "blocked" else "confirmed_for_recorded_checkpoints",
        "release_effect": "candidate_evidence" if overall == "covered" else "blocks_release",
        "schema_validation_status": "pass",
        "blocked_reasons": blocked_reasons,
        "unknowns": [
            {"id": "TASK045A-UNKNOWN-SESSION", "evidence_status": "unknown", "reason_code": "active_session_provenance_unknown"},
            {"id": "TASK045A-UNKNOWN-TV", "evidence_status": "unknown", "reason_code": "missing_tv_no_paired_evidence"},
        ],
        "risks": [
            {"id": "TASK045A-RISK-001", "evidence_status": "confirmed", "summary": "Quarantined TASK-045 evidence is audit-only and cannot establish product coverage."},
            {"id": "TASK045A-RISK-002", "evidence_status": "confirmed", "summary": "Unknown active-session provenance blocks session-dependent Phone Full nodes and edges."},
            {"id": "TASK045A-RISK-003", "evidence_status": "confirmed", "summary": "Missing TV keeps paired-only coverage blocked and prevents paired evidence."},
        ],
        "verification": [
            {"check": "scenario_reconciliation", "status": "pass", "result_count": len(scenario_rows), "evidence_status": "confirmed"},
            {"check": "screen_state_ledger_validation", "status": "pass", "result_count": len(screen_rows), "evidence_status": "confirmed"},
            {"check": "transition_ledger_validation", "status": "pass", "result_count": len(transition_rows), "evidence_status": "confirmed"},
            {"check": "branch_closure_validation", "status": "pass", "result_count": len(branch_rows), "evidence_status": "confirmed"},
        ],
        "artifacts": artifacts,
        "review": {
            "qa_reviewer_a": "go_no_open_r0_r1",
            "qa_reviewer_b": "go_no_open_r0_r1",
            "security_prod_safety_reviewer": "go_static_closure_runtime_blocked",
            "docs_scribe": "go_no_open_r0_r1",
        },
        "provenance": {
            "adapter_input_published": False,
            "adapter_schema": _repo_ref(ADAPTER_SCHEMA),
            "adapter_schema_sha256": shared._sha(ADAPTER_SCHEMA.read_bytes()),
            "scenario_contract": _repo_ref(CATALOG),
            "scenario_contract_version": SCENARIO_VERSION,
            "prior_task045_raw_evidence_published": False,
            "session_passport_published": False,
        },
        "payload": {
            "runtime_gate": adapter["lane_preflight"]["runtime_gate"],
            "active_session_provenance": adapter["lane_preflight"]["active_session_provenance"],
            "session_passport_evidence": adapter["lane_preflight"]["session_passport_status"],
            "tv_status": adapter["lane_preflight"]["tv_status"],
            "graph_ledger_terminal": all(row["status"] in COVERAGE_STATUSES for row in adapter["branch_closure"]),
            "full_visual_transition_coverage": overall == "covered",
            "counts_as_paired_evidence": False,
            "evidence_registry": sorted(adapter["evidence_registry"]),
            "prior_audit": dict(adapter["prior_audit"]),
            "row_counts": {
                "scenario_ledger": len(scenario_rows), "screen_state_ledger": len(screen_rows),
                "transition_ledger": len(transition_rows), "branch_closure_ledger": len(branch_rows),
                "anomaly_ledger": len(anomaly_rows), "boundary_ledger": len(boundary_rows),
                "cleanup_ledger": len(cleanup_rows),
            },
            "covered_counts": {
                "screens": sum(row["status"] == "covered" for row in adapter["screen_states"]),
                "transitions": sum(row["status"] == "covered" for row in adapter["transitions"]),
                "branches": sum(row["status"] == "covered" for row in adapter["branch_closure"]),
            },
            "boundary_guards": {
                "real_payment_performed": any(row["payment_or_session_started"] for row in adapter["boundaries"]),
                "paid_session_started": any(row["payment_or_session_started"] for row in adapter["boundaries"]),
                "account_mutation_performed": any(row["account_mutated"] for row in adapter["boundaries"]),
                "qr_or_browser_traversal_performed": any(row["qr_traversed"] or row["external_action_performed"] for row in adapter["boundaries"]),
                "network_changed": any(row["network_changed"] for row in adapter["boundaries"]),
            },
            "cleanup_guards": {
                key: adapter["cleanup"][key] for key in (
                    "target_app_force_stopped", "home_restored", "existing_session_preserved",
                    "external_app_opened", "payment_or_session_started", "account_mutated",
                    "network_changed", "paired_state_observed",
                )
            },
        },
    }
    report_schema = _read_json(REPORT_ENVELOPE_SCHEMA)
    _validate_schema_instance(report, report_schema)
    shared._safe_public_value(report)
    _safe_public_identifiers(report)
    return {**ledger_outputs, REPORT_OUTPUT: _json_bytes(report)}


def validate_bundle(outputs: Mapping[Path, bytes]) -> None:
    expected = {SCENARIO_OUTPUT, SCREEN_OUTPUT, TRANSITION_OUTPUT, BRANCH_OUTPUT, ANOMALY_OUTPUT, BOUNDARY_OUTPUT, CLEANUP_OUTPUT, REPORT_OUTPUT}
    if set(outputs) != expected:
        raise ContractError("REPORT_BUNDLE_INCOMPLETE")
    try:
        report = json.loads(outputs[REPORT_OUTPUT])
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("REPORT_JSON_INVALID") from exc
    report_schema = _read_json(REPORT_ENVELOPE_SCHEMA)
    _validate_schema_instance(report, report_schema)
    if report["task_id"] != TASK_ID or report["schema_validation_status"] != "pass":
        raise ContractError("REPORT_IDENTITY_INVALID")
    if report["coverage_status"] == "covered" and report["release_effect"] != "candidate_evidence":
        raise ContractError("REPORT_RELEASE_EFFECT_INVALID")
    if report["coverage_status"] != "covered" and report["release_effect"] != "blocks_release":
        raise ContractError("REPORT_RELEASE_EFFECT_INVALID")
    artifacts = {row["reference"]: row for row in report["artifacts"]}
    for path in expected - {REPORT_OUTPUT}:
        reference = _repo_ref(path)
        if reference not in artifacts or artifacts[reference]["sha256"] != shared._sha(outputs[path]):
            raise ContractError("REPORT_ARTIFACT_HASH_INVALID")
    parsed: dict[Path, list[dict[str, str]]] = {}
    for path, headers in (
        (SCENARIO_OUTPUT, SCENARIO_HEADERS), (SCREEN_OUTPUT, SCREEN_HEADERS),
        (TRANSITION_OUTPUT, TRANSITION_HEADERS), (BRANCH_OUTPUT, BRANCH_HEADERS),
        (ANOMALY_OUTPUT, ANOMALY_HEADERS), (BOUNDARY_OUTPUT, BOUNDARY_HEADERS),
        (CLEANUP_OUTPUT, CLEANUP_HEADERS),
    ):
        rows = list(csv.DictReader(io.StringIO(outputs[path].decode("utf-8"))))
        if not rows or tuple(rows[0]) != headers:
            raise ContractError("REPORT_LEDGER_INVALID")
        try:
            shared._safe_public_value(rows)
            _safe_public_identifiers(rows)
        except shared.ContractError as exc:
            raise ContractError("REPORT_PUBLIC_SAFETY_INVALID") from exc
        parsed[path] = rows
    ledger_evidence: set[str] = set()
    boolean_fields = {
        "requires_tv", "observed", "audit_only", "counts_as_product_coverage",
        "screenshot_present", "visual_inspection", "ui_tree_present", "runner_log_present",
        "recovery_attempt", "first_failure_retained", "approved_scope", "declared_reachable",
        "external_action_performed", "payment_or_session_started", "account_mutated",
        "network_changed", "qr_traversed", "target_app_force_stopped", "home_restored",
        "existing_session_preserved", "external_app_opened", "paired_state_observed",
    }
    integer_fields = {"evidence_count", "attempt_index", "screen_node_count", "transition_count"}
    for rows in parsed.values():
        for row in rows:
            if "status" in row and row["status"] not in COVERAGE_STATUSES:
                raise ContractError("REPORT_TERMINAL_STATUS_INVALID")
            if "evidence_status" in row and row["evidence_status"] not in EVIDENCE_STATUSES:
                raise ContractError("REPORT_EVIDENCE_STATUS_INVALID")
            if "cause_evidence_status" in row and row["cause_evidence_status"] not in EVIDENCE_STATUSES:
                raise ContractError("REPORT_CAUSE_EVIDENCE_STATUS_INVALID")
            if any(row[key] not in {"true", "false"} for key in boolean_fields.intersection(row)):
                raise ContractError("REPORT_BOOLEAN_ENUM_INVALID")
            for key in integer_fields.intersection(row):
                try:
                    if int(row[key]) < 0 or str(int(row[key])) != row[key]:
                        raise ValueError
                except ValueError as exc:
                    raise ContractError("REPORT_INTEGER_ENUM_INVALID") from exc
            try:
                count = int(row["evidence_count"])
            except (KeyError, ValueError) as exc:
                raise ContractError("REPORT_EVIDENCE_COUNT_INVALID") from exc
            evidence_ids = [] if not row["evidence_ids"] else row["evidence_ids"].split(";")
            if count != len(evidence_ids) or count < 1 or len(set(evidence_ids)) != len(evidence_ids):
                raise ContractError("REPORT_EVIDENCE_IDS_INVALID")
            _safe_public_identifiers({"evidence_ids": evidence_ids})
            ledger_evidence.update(evidence_ids)
    expected_counts = {
        "scenario_ledger": len(parsed[SCENARIO_OUTPUT]),
        "screen_state_ledger": len(parsed[SCREEN_OUTPUT]),
        "transition_ledger": len(parsed[TRANSITION_OUTPUT]),
        "branch_closure_ledger": len(parsed[BRANCH_OUTPUT]),
        "anomaly_ledger": len(parsed[ANOMALY_OUTPUT]),
        "boundary_ledger": len(parsed[BOUNDARY_OUTPUT]),
        "cleanup_ledger": len(parsed[CLEANUP_OUTPUT]),
    }
    if report["payload"]["row_counts"] != expected_counts:
        raise ContractError("REPORT_ROW_COUNTS_INVALID")
    if set(report["payload"].get("evidence_registry", [])) != ledger_evidence:
        raise ContractError("REPORT_EVIDENCE_REGISTRY_INVALID")
    if tuple(row["scenario_id"] for row in parsed[SCENARIO_OUTPUT]) != EXPECTED_IDS:
        raise ContractError("REPORT_SCENARIO_RECONCILIATION_INVALID")
    if {row["scenario_id"] for row in parsed[BRANCH_OUTPUT]} != set(EXPECTED_IDS):
        raise ContractError("REPORT_BRANCH_RECONCILIATION_INVALID")
    graph_terminal = all(row["status"] in COVERAGE_STATUSES for row in parsed[BRANCH_OUTPUT])
    if report["payload"].get("graph_ledger_terminal") is not graph_terminal:
        raise ContractError("REPORT_GRAPH_TERMINAL_FLAG_INVALID")
    scenario_rows = {row["scenario_id"]: row for row in parsed[SCENARIO_OUTPUT]}
    branch_rows = {row["scenario_id"]: row for row in parsed[BRANCH_OUTPUT]}
    if len(branch_rows) != len(EXPECTED_IDS):
        raise ContractError("REPORT_BRANCH_RECONCILIATION_INVALID")
    if report["payload"]["prior_audit"]["counts_as_product_coverage"] is not False:
        raise ContractError("REPORT_AUDIT_FALSE_PASS")
    audit_rows = [row for row in parsed[SCREEN_OUTPUT] if row["evidence_origin"] == "quarantined_task045_audit"]
    if not audit_rows or any(row["audit_only"] != "true" or row["counts_as_product_coverage"] != "false" for row in audit_rows):
        raise ContractError("REPORT_AUDIT_FALSE_PASS")
    if report["payload"]["active_session_provenance"] == "unknown_not_verified":
        session_ids = set(SESSION_DEPENDENT_IDS)
        for path in (SCENARIO_OUTPUT, SCREEN_OUTPUT, TRANSITION_OUTPUT, BRANCH_OUTPUT):
            if any(row["scenario_id"] in session_ids and row["status"] == "covered" for row in parsed[path]):
                raise ContractError("REPORT_UNKNOWN_SESSION_FALSE_PASS")
    if any(row["scenario_id"] in PAIRED_IDS and row["status"] == "covered" for row in parsed[BRANCH_OUTPUT]):
        raise ContractError("REPORT_MISSING_TV_FALSE_PASS")
    screen_by_id = {row["node_id"]: row for row in parsed[SCREEN_OUTPUT]}
    if len(screen_by_id) != len(parsed[SCREEN_OUTPUT]) or set(row["scenario_id"] for row in parsed[SCREEN_OUTPUT]) != set(EXPECTED_IDS):
        raise ContractError("REPORT_SCREEN_RECONCILIATION_INVALID")
    for row in parsed[SCREEN_OUTPUT]:
        if row["status"] == "covered":
            if not (
                row["observed"] == "true" and row["surface_side"] == "phone"
                and row["evidence_origin"] == "fresh_task045a" and row["audit_only"] == "false"
                and row["counts_as_product_coverage"] == "true" and row["evidence_status"] == "confirmed"
                and row["screenshot_present"] == "true" and row["visual_inspection"] == "true"
                and row["ui_tree_present"] == "true" and row["runner_log_present"] == "true"
            ):
                raise ContractError("REPORT_COVERED_SCREEN_MODALITIES_INVALID")
            for key in ("screen_alias", "state_alias", "state_category"):
                _reject_non_phone_identifier(row[key], "REPORT_NON_PHONE_SCREEN_ALIAS")
    transition_by_id = {row["transition_id"]: row for row in parsed[TRANSITION_OUTPUT]}
    if len(transition_by_id) != len(parsed[TRANSITION_OUTPUT]) or set(row["scenario_id"] for row in parsed[TRANSITION_OUTPUT]) != set(EXPECTED_IDS):
        raise ContractError("REPORT_TRANSITION_RECONCILIATION_INVALID")
    report_edge_attempts: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    known_boundary_ids = {row["boundary_id"] for row in parsed[BOUNDARY_OUTPUT]}
    known_anomaly_ids = {row["anomaly_id"] for row in parsed[ANOMALY_OUTPUT]}
    for row in parsed[TRANSITION_OUTPUT]:
        if row["from_node_id"] not in screen_by_id or row["to_node_id"] not in screen_by_id:
            raise ContractError("REPORT_TRANSITION_NODE_LINK_INVALID")
        if (
            screen_by_id[row["from_node_id"]]["scenario_id"] != row["scenario_id"]
            or screen_by_id[row["to_node_id"]]["scenario_id"] != row["scenario_id"]
        ):
            raise ContractError("REPORT_TRANSITION_SCENARIO_LINK_INVALID")
        if row["boundary_id"] != "none" and row["boundary_id"] not in known_boundary_ids:
            raise ContractError("REPORT_TRANSITION_BOUNDARY_LINK_INVALID")
        if row["anomaly_id"] != "none" and row["anomaly_id"] not in known_anomaly_ids:
            raise ContractError("REPORT_TRANSITION_ANOMALY_LINK_INVALID")
        report_edge_attempts.setdefault((row["from_node_id"], row["to_node_id"], row["action_category"]), []).append(row)
        if row["status"] == "covered" and (
            row["from_node_id"] == row["to_node_id"] or row["edge_scope"] != "phone_independent"
            or row["requires_tv"] != "false" or row["evidence_status"] != "confirmed"
            or int(row["attempt_index"]) < 1
            or screen_by_id[row["from_node_id"]]["status"] != "covered"
            or screen_by_id[row["to_node_id"]]["status"] != "covered"
        ):
            raise ContractError("REPORT_COVERED_TRANSITION_INVALID")
        if row["status"] == "covered":
            _reject_non_phone_identifier(row["action_category"], "REPORT_NON_PHONE_EDGE_ALIAS")
            endpoint_ids = set(screen_by_id[row["from_node_id"]]["evidence_ids"].split(";")) | set(
                screen_by_id[row["to_node_id"]]["evidence_ids"].split(";")
            )
            if set(row["evidence_ids"].split(";")) != endpoint_ids:
                raise ContractError("REPORT_TRANSITION_EVIDENCE_INCOMPLETE")
        if row["recovery_attempt"] == "true":
            prior = transition_by_id.get(row["recovery_of_transition_id"])
            if prior is None or prior["transition_id"] == row["transition_id"] or prior["first_failure_retained"] != "true":
                raise ContractError("REPORT_TRANSITION_RECOVERY_LINK_INVALID")
        elif row["recovery_of_transition_id"] != "none":
            raise ContractError("REPORT_TRANSITION_RECOVERY_LINK_INVALID")
    for attempts in report_edge_attempts.values():
        try:
            indexes = [int(row["attempt_index"]) for row in attempts]
        except ValueError as exc:
            raise ContractError("REPORT_TRANSITION_ATTEMPT_INVALID") from exc
        if len(attempts) > 2 or len(set(indexes)) != len(indexes):
            raise ContractError("REPORT_TRANSITION_ATTEMPT_BUDGET_EXCEEDED")
        if sum(row["recovery_attempt"] == "true" for row in attempts) > 1:
            raise ContractError("REPORT_TRANSITION_RECOVERY_BUDGET_EXCEEDED")
    for scenario_id in EXPECTED_IDS:
        branch = branch_rows[scenario_id]
        scenario = scenario_rows[scenario_id]
        scenario_nodes = [row for row in parsed[SCREEN_OUTPUT] if row["scenario_id"] == scenario_id]
        scenario_transitions = [row for row in parsed[TRANSITION_OUTPUT] if row["scenario_id"] == scenario_id]
        linked_ids = {
            evidence_id
            for item in scenario_nodes + scenario_transitions
            for evidence_id in item["evidence_ids"].split(";")
        }
        if (
            scenario["status"] != branch["status"]
            or int(branch["screen_node_count"]) != len(scenario_nodes)
            or int(branch["transition_count"]) != len(scenario_transitions)
            or set(branch["evidence_ids"].split(";")) != linked_ids
            or set(scenario["evidence_ids"].split(";")) != linked_ids
        ):
            raise ContractError("REPORT_GRAPH_RECONCILIATION_INVALID")
        if branch["status"] == "covered" and any(
            item["status"] != "covered" for item in scenario_nodes + scenario_transitions
        ):
            raise ContractError("REPORT_BRANCH_FALSE_PASS")
        if branch["status"] == "covered":
            node_ids = {item["node_id"] for item in scenario_nodes}
            endpoints = {
                node_id
                for edge in scenario_transitions
                for node_id in (edge["from_node_id"], edge["to_node_id"])
            }
            if endpoints != node_ids:
                raise ContractError("REPORT_COVERED_BRANCH_DISCONNECTED_NODE")
            adjacency = {node_id: set() for node_id in node_ids}
            indegree = {node_id: 0 for node_id in node_ids}
            for edge in scenario_transitions:
                adjacency[edge["from_node_id"]].add(edge["to_node_id"])
                indegree[edge["to_node_id"]] += 1
            starts = [node_id for node_id, degree in indegree.items() if degree == 0] or [next(iter(node_ids))]
            def report_reachable(start: str) -> set[str]:
                seen: set[str] = set()
                pending = [start]
                while pending:
                    current = pending.pop()
                    if current in seen:
                        continue
                    seen.add(current)
                    pending.extend(adjacency[current] - seen)
                return seen
            if not any(report_reachable(start) == node_ids for start in starts):
                raise ContractError("REPORT_COVERED_BRANCH_DIRECTED_GRAPH_DISCONNECTED")
            if scenario_id in {"A004", "A007"} and not {"initial", "later"}.issubset(
                {item["long_list_segment"] for item in scenario_nodes}
            ):
                raise ContractError("REPORT_LONG_LIST_SEGMENTS_INCOMPLETE")
            if scenario_id == "A005" and not {"expanded", "collapsed"}.issubset(
                {item["menu_state"] for item in scenario_nodes}
            ):
                raise ContractError("REPORT_MENU_STATES_INCOMPLETE")
            if scenario_id == "A006":
                overlay_ids = {item["node_id"] for item in scenario_nodes if item["overlay_category"] != "none"}
                recovered_ids = {
                    item["node_id"] for item in scenario_nodes
                    if item["recurrence_status"] == "recurrence" and item["prior_node_id"] in node_ids
                }
                overlay_entries = [edge for edge in scenario_transitions if edge["to_node_id"] in overlay_ids]
                recovery_edges = [edge for edge in scenario_transitions if edge["from_node_id"] in overlay_ids and edge["to_node_id"] in recovered_ids]
                if (
                    len(scenario_nodes) < 3 or not overlay_entries or not recovery_edges
                    or not any(edge["recovery_attempt"] == "true" and edge["recovery_of_transition_id"] in {item["transition_id"] for item in overlay_entries} for edge in recovery_edges)
                ):
                    raise ContractError("REPORT_SEARCH_OVERLAY_RECOVERY_INCOMPLETE")
            if scenario_id == "A008" and not {"profile", "settings", "help", "legal"}.issubset(
                {item["state_category"] for item in scenario_nodes}
            ):
                raise ContractError("REPORT_READ_ONLY_ACCOUNT_ROUTES_INCOMPLETE")
            if scenario_id == "A013":
                recurrence_ids = {
                    item["node_id"] for item in scenario_nodes
                    if item["recurrence_status"] == "recurrence" and item["prior_node_id"] in node_ids
                }
                if not recurrence_ids or not any(
                    edge["to_node_id"] in recurrence_ids and edge["action_category"] == "background_foreground_recurrence"
                    for edge in scenario_transitions
                ):
                    raise ContractError("REPORT_LIFECYCLE_RECURRENCE_INCOMPLETE")
            if scenario_id == "A014" and (
                len(scenario_nodes) < 2 or not any(edge["action_category"] == "force_stop_relaunch" for edge in scenario_transitions)
            ):
                raise ContractError("REPORT_FORCE_STOP_RELAUNCH_INCOMPLETE")
            if scenario_id == "A015":
                known_boundaries = {item["boundary_id"] for item in parsed[BOUNDARY_OUTPUT]}
                boundary_nodes = {item["node_id"] for item in scenario_nodes if item["state_category"] == "boundary"}
                recovered_nodes = {item["node_id"] for item in scenario_nodes if item["recurrence_status"] == "recurrence"}
                entries = [edge for edge in scenario_transitions if edge["to_node_id"] in boundary_nodes and edge["boundary_id"] in known_boundaries]
                recoveries = [edge for edge in scenario_transitions if edge["from_node_id"] in boundary_nodes and edge["to_node_id"] in recovered_nodes]
                if (
                    len(scenario_nodes) < 3 or not entries or not recoveries
                    or not any(edge["recovery_attempt"] == "true" and edge["recovery_of_transition_id"] in {item["transition_id"] for item in entries} for edge in recoveries)
                ):
                    raise ContractError("REPORT_BOUNDARY_CAPTURE_RECOVERY_INCOMPLETE")
    if not any(row["anomaly_id"] == "TASK045A-PROCESS-001" and row["first_failure_retained"] == "true" for row in parsed[ANOMALY_OUTPUT]):
        raise ContractError("REPORT_REQUIRED_PROCESS_ANOMALY_MISSING")
    if any(row[key] != "false" for row in parsed[BOUNDARY_OUTPUT] for key in (
        "external_action_performed", "payment_or_session_started", "account_mutated",
        "network_changed", "qr_traversed",
    )):
        raise ContractError("REPORT_FORBIDDEN_BOUNDARY_ACTION")
    if len(parsed[CLEANUP_OUTPUT]) != 1:
        raise ContractError("REPORT_CLEANUP_RECONCILIATION_INVALID")
    cleanup = parsed[CLEANUP_OUTPUT][0]
    cleanup_bool_keys = (
        "target_app_force_stopped", "home_restored", "existing_session_preserved",
        "external_app_opened", "payment_or_session_started", "account_mutated",
        "network_changed", "paired_state_observed",
    )
    if any(cleanup[key] not in {"true", "false"} for key in cleanup_bool_keys):
        raise ContractError("REPORT_CLEANUP_BOOLEAN_INVALID")
    if any(cleanup[key] != "false" for key in (
        "external_app_opened", "payment_or_session_started", "account_mutated",
        "network_changed", "paired_state_observed",
    )):
        raise ContractError("REPORT_FORBIDDEN_CLEANUP_STATE")
    if cleanup["status"] == "covered" and not (
        cleanup["target_app_force_stopped"] == "true" and cleanup["home_restored"] == "true"
        and cleanup["existing_session_preserved"] == "true" and cleanup["evidence_status"] == "confirmed"
    ):
        raise ContractError("REPORT_CLEANUP_COVERAGE_INVALID")
    cleanup_claims = {key: cleanup[key] == "true" for key in cleanup_bool_keys}
    if report["payload"].get("cleanup_guards") != cleanup_claims:
        raise ContractError("REPORT_CLEANUP_SUMMARY_MISMATCH")
    if any(report["payload"].get("boundary_guards", {}).values()):
        raise ContractError("REPORT_BOUNDARY_GUARD_FALSE_PASS")
    branch_covered = sum(row["status"] == "covered" for row in parsed[BRANCH_OUTPUT])
    screen_covered = sum(row["status"] == "covered" for row in parsed[SCREEN_OUTPUT])
    transition_covered = sum(row["status"] == "covered" for row in parsed[TRANSITION_OUTPUT])
    if report["payload"]["covered_counts"] != {
        "branches": branch_covered, "screens": screen_covered, "transitions": transition_covered,
    }:
        raise ContractError("REPORT_COVERED_COUNTS_INVALID")
    expected_coverage = "covered" if branch_covered == len(parsed[BRANCH_OUTPUT]) and parsed[CLEANUP_OUTPUT][0]["status"] == "covered" else ("partial_blocked" if branch_covered else "blocked")
    if report["coverage_status"] != expected_coverage:
        raise ContractError("REPORT_COVERAGE_STATUS_INVALID")
    if report["payload"]["full_visual_transition_coverage"] is not (expected_coverage == "covered"):
        raise ContractError("REPORT_FULL_COVERAGE_FLAG_INVALID")
    shared._safe_public_value(report)
    _safe_public_identifiers(report)


def _atomic_publish(outputs: Mapping[Path, bytes]) -> None:
    staged: dict[Path, Path] = {}
    try:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
            staged_path = Path(raw)
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            staged[path] = staged_path
        for path, staged_path in staged.items():
            os.replace(staged_path, path)
    finally:
        for staged_path in staged.values():
            staged_path.unlink(missing_ok=True)


def _baseline_adapter() -> dict[str, Any]:
    catalog = load_contract()
    marker = {
        "audit": "audit-task045-quarantine-category-summary",
        "cp001": "audit-task045-cp001-incomplete",
        "security": "static-security-block-runtime",
        "session": "static-session-provenance-unknown",
        "tv": "static-missing-tv",
        "boundary": "static-boundary-guard",
        "anomaly": "static-process-anomaly-task045-suite",
        "cleanup": "static-cleanup-not-run",
    }
    scenarios = []
    screens = []
    transitions = []
    branches = []
    for index, item in enumerate(catalog, start=1):
        scenario_id = item["scenario_id"]
        session_scope = item["session_scope"]
        if scenario_id == "A001":
            status, reason, ids = "blocked_by_tooling", "quarantined_audit_cp001_incomplete", [marker["audit"], marker["cp001"]]
            origin, observed, audit_only = "quarantined_task045_audit", True, True
        elif scenario_id == "A016":
            status, reason, ids = "blocked_by_external_state", "missing_tv_no_paired_evidence", [marker["tv"]]
            origin, observed, audit_only = "static_blocker", False, False
        elif scenario_id == "A017":
            status, reason, ids = "blocked_by_external_state", "runtime_blocked_cleanup_not_run", [marker["security"], marker["cleanup"]]
            origin, observed, audit_only = "static_blocker", False, False
        elif scenario_id in SESSION_DEPENDENT_IDS:
            status, reason, ids = "blocked_by_external_state", "active_session_provenance_unknown", [marker["session"]]
            origin, observed, audit_only = "static_blocker", False, False
        else:
            status, reason, ids = "blocked_by_external_state", "security_runtime_gate_blocked", [marker["security"]]
            origin, observed, audit_only = "static_blocker", False, False
        node_id = f"node-{scenario_id.lower()}-blocked"
        transition_id = f"transition-{scenario_id.lower()}-blocked"
        scenarios.append({"scenario_id": scenario_id, "status": status, "evidence_status": "confirmed", "evidence_ids": ids, "reason_code": reason})
        screens.append({
            "node_id": node_id, "scenario_id": scenario_id,
            "screen_alias": item["screen_family"], "state_alias": f"{item['branch_alias']}-blocked",
            "state_category": "audit_quarantine" if scenario_id == "A001" else "not_observed_runtime_blocked",
            "session_scope": session_scope,
            "surface_side": "audit" if scenario_id == "A001" else ("external_blocker" if scenario_id == "A016" else "phone"),
            "observed": observed, "evidence_origin": origin,
            "audit_only": audit_only, "counts_as_product_coverage": False, "status": status,
            "evidence_status": "confirmed", "evidence_ids": ids,
            "modalities": {"screenshot": None, "ui_tree": None, "runner_log": None},
            "recurrence_status": "first_observation" if observed else "not_observed",
            "prior_node_id": "none", "long_list_segment": "none", "menu_state": "none",
            "overlay_category": "unknown" if scenario_id == "A001" else "none",
            "xml_visual_match": "not_compared", "reason_code": reason,
        })
        transitions.append({
            "transition_id": transition_id, "scenario_id": scenario_id,
            "from_node_id": node_id, "to_node_id": node_id,
            "action_category": item["transition_family"], "session_scope": session_scope,
            "edge_scope": "audit" if scenario_id == "A001" else ("external_blocker" if scenario_id == "A016" else "phone_independent"),
            "requires_tv": item["requires_tv"] == "true", "attempt_index": 0,
            "recovery_attempt": False, "recovery_of_transition_id": "none", "status": status,
            "evidence_status": "confirmed", "evidence_ids": ids, "first_failure_retained": True,
            "boundary_id": "boundary-payment-session" if scenario_id == "A015" else "none",
            "anomaly_id": "TASK045A-PROCESS-001" if scenario_id == "A001" else "none",
            "reason_code": reason,
        })
        branches.append({
            "branch_id": f"branch-{index:03d}", "scenario_id": scenario_id,
            "coverage_scope": "audit" if scenario_id == "A001" else ("external_blocker" if scenario_id == "A016" else "phone_independent"),
            "approved_scope": True, "declared_reachable": scenario_id not in {"A015", "A016"},
            "status": status, "screen_node_ids": [node_id], "transition_ids": [transition_id],
            "evidence_status": "confirmed", "evidence_ids": ids, "reason_code": reason,
        })
    boundaries = [
        {"boundary_id": "boundary-payment-session", "category": "payment_or_session", "status": "blocked_by_boundary", "reason_code": "payment_or_session_not_started"},
        {"boundary_id": "boundary-account-profile", "category": "account_or_profile", "status": "blocked_by_boundary", "reason_code": "account_profile_not_mutated"},
        {"boundary_id": "boundary-qr-external", "category": "qr_browser_external", "status": "blocked_by_boundary", "reason_code": "qr_external_not_traversed"},
        {"boundary_id": "boundary-network-lock", "category": "network_or_lock", "status": "not_run_out_of_scope", "reason_code": "network_lock_actions_not_authorized"},
        {"boundary_id": "boundary-paired-tv", "category": "paired_tv", "status": "blocked_by_external_state", "reason_code": "missing_tv_no_paired_evidence"},
    ]
    for row in boundaries:
        row.update({
            "external_action_performed": False, "payment_or_session_started": False,
            "account_mutated": False, "network_changed": False, "qr_traversed": False,
            "evidence_status": "confirmed",
            "evidence_ids": [marker["tv"] if row["category"] == "paired_tv" else marker["boundary"]],
        })
    return {
        "schema_version": SCHEMA_VERSION, "task_id": TASK_ID,
        "scenario_contract_version": SCENARIO_VERSION,
        "run_id": "task045a-static-blocked-baseline", "generated_at_utc": "2026-08-15T01:00:00Z",
        "build_ref": {"alias": "task045a-phone-full-lane", "apk_family": "phone-full", "compatibility_status": "unknown_not_verified", "raw_identity_published": False},
        "lane_preflight": {
            "runtime_gate": "BLOCK_RUNTIME", "phone_alias": "phone-full-approved-lane",
            "phone_status": "BLOCKED", "tv_status": "BLOCKED_MISSING_TV",
            "active_session_provenance": "unknown_not_verified", "session_passport_status": "missing",
            "ignored_evidence_storage_ready": False, "reviewer_gate": False,
        },
        "prior_audit": {
            "source_task": "TASK-045", "png_count": 20, "xml_count": 19,
            "bounded_log_count": 19, "incomplete_checkpoint_alias": "prior-audit-cp001",
            "audit_only": True, "counts_as_product_coverage": False,
            "session_provenance": "unknown_not_verified",
        },
        "scenarios": scenarios, "screen_states": screens, "transitions": transitions,
        "branch_closure": branches,
        "anomalies": [{
            "anomaly_id": "TASK045A-PROCESS-001", "classification": "process_anomaly",
            "trigger_category": "clean_worktree_task045_focused_suite_baseline",
            "expected_result_category": "historical_focused_suite_static_pass",
            "observed_result_category": "seventeen_failures_missing_ignored_source",
            "public_safe_screen_alias": "repository_test_baseline", "evidence_status": "confirmed",
            "cause_evidence_status": "confirmed", "cause_category": "ignored_task045_source_unavailable",
            "test_design_implication": "keep_task045_closed_and_build_separate_task045a_authority",
            "first_failure_retained": True, "evidence_ids": [marker["anomaly"]],
            "reason_code": "historical_task045_focused_suite_requires_ignored_source",
        }],
        "boundaries": boundaries,
        "cleanup": {
            "cleanup_id": "cleanup-static-blocked", "status": "blocked_by_external_state",
            "target_app_force_stopped": False, "home_restored": False,
            "existing_session_preserved": True, "external_app_opened": False,
            "payment_or_session_started": False, "account_mutated": False,
            "network_changed": False, "paired_state_observed": False,
            "evidence_status": "confirmed", "evidence_ids": [marker["security"], marker["cleanup"]],
            "reason_code": "runtime_blocked_cleanup_not_run",
        },
        "evidence_registry": sorted(set(marker.values())),
    }


def _validate_session_passport(path: Path, adapter: Mapping[str, Any]) -> None:
    fixed = _fixed_local_input(path, LOCAL_SESSION_PASSPORT, code="SESSION_PASSPORT_PATH_INVALID")
    passport = _read_fixed_json(fixed)
    required = {
        "schema_version", "task_id", "run_id", "fixture_alias", "provenance",
        "task_authoritative", "evidence_status", "raw_values_published",
        "phone_alias", "build_alias", "lane_alias", "confirmed_at_utc", "expires_at_utc",
        "authority_evidence_id", "reviewer_decision",
    }
    if set(passport) != required:
        raise ContractError("SESSION_PASSPORT_SHAPE_INVALID")
    if not (
        passport["schema_version"] == "task045a-synthetic-session-passport-v1"
        and passport["task_id"] == TASK_ID and passport["run_id"] == adapter["run_id"]
        and passport["provenance"] == "approved_synthetic_fixture"
        and passport["task_authoritative"] is True and passport["evidence_status"] == "confirmed"
        and passport["raw_values_published"] is False
        and passport["phone_alias"] == adapter["lane_preflight"]["phone_alias"]
        and passport["build_alias"] == adapter["build_ref"]["alias"]
        and passport["lane_alias"] == "phone-full-visual-transition-lane"
        and passport["reviewer_decision"] == "GO"
        and passport["authority_evidence_id"].startswith("task045a-session-authority-")
    ):
        raise ContractError("SESSION_PASSPORT_NOT_PROVEN")
    confirmed = _utc(passport["confirmed_at_utc"])
    expires = _utc(passport["expires_at_utc"])
    generated = _utc(adapter["generated_at_utc"])
    now = _now_utc()
    if not (
        confirmed <= generated <= expires and expires - confirmed <= MAX_EVIDENCE_AGE
        and confirmed <= now <= expires + MAX_CLOCK_SKEW and now - confirmed <= MAX_EVIDENCE_AGE
    ):
        raise ContractError("SESSION_PASSPORT_FRESHNESS_INVALID")
    shared._safe_public_value(passport)
    _safe_public_identifiers(passport)


def _load_adapter(path: Path) -> dict[str, Any]:
    fixed = _fixed_local_input(path, LOCAL_ADAPTER, code="ADAPTER_PATH_INVALID")
    adapter = _read_fixed_json(fixed)
    validate_adapter(adapter)
    return adapter


def _tracked_bundle() -> dict[Path, bytes]:
    paths = (SCENARIO_OUTPUT, SCREEN_OUTPUT, TRANSITION_OUTPUT, BRANCH_OUTPUT, ANOMALY_OUTPUT, BOUNDARY_OUTPUT, CLEANUP_OUTPUT, REPORT_OUTPUT)
    try:
        return {path: _fixed(path, suffix=path.suffix).read_bytes() for path in paths}
    except OSError as exc:
        raise ContractError("TRACKED_BUNDLE_MISSING") from exc


def _emit(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-045A public-safe visual-transition evidence.")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--publish-blocked-baseline", action="store_true")
    modes.add_argument("--validate-report", action="store_true")
    parser.add_argument("--adapter-input", type=Path)
    parser.add_argument("--session-passport", type=Path)
    parser.add_argument("--allow-prod-conditional-ingest", action="store_true")
    args = parser.parse_args(argv)
    try:
        catalog = load_contract()
        _load_schema()
        if args.validate_only:
            validate_adapter(_baseline_adapter())
            _emit({"task_id": TASK_ID, "mode": "validate_only", "status": "pass", "runtime_access": False, "writes": False})
            return 0
        if args.preflight:
            if args.adapter_input is None:
                raise ContractError("ADAPTER_INPUT_REQUIRED")
            adapter = _load_adapter(args.adapter_input)
            _emit({"task_id": TASK_ID, "mode": "preflight", "status": "pass", "coverage_status": _overall(adapter), "runtime_access": False, "writes": False})
            return 0
        if args.execute:
            if args.adapter_input is None or args.session_passport is None or not args.allow_prod_conditional_ingest:
                raise ContractError("EXECUTE_GATE_REQUIRED")
            adapter = _load_adapter(args.adapter_input)
            preflight = adapter["lane_preflight"]
            if not (
                preflight["runtime_gate"] == "GO" and preflight["reviewer_gate"] is True
                and preflight["active_session_provenance"] == "approved_synthetic_fixture"
                and preflight["session_passport_status"] == "proven"
            ):
                raise ContractError("EXECUTE_RUNTIME_GATE_NOT_PROVEN")
            _validate_session_passport(args.session_passport, adapter)
            outputs = build_bundle(adapter, catalog)
            validate_bundle(outputs)
            _atomic_publish(outputs)
            _emit({"task_id": TASK_ID, "mode": "execute", "status": "pass", "published_artifacts": len(outputs), "device_actions": False})
            return 0
        if args.publish_blocked_baseline:
            outputs = build_bundle(_baseline_adapter(), catalog)
            validate_bundle(outputs)
            _atomic_publish(outputs)
            _emit({"task_id": TASK_ID, "mode": "publish_blocked_baseline", "status": "pass", "published_artifacts": len(outputs), "device_actions": False})
            return 0
        outputs = _tracked_bundle()
        validate_bundle(outputs)
        _emit({"task_id": TASK_ID, "mode": "validate_report", "status": "pass", "artifacts": len(outputs), "runtime_access": False, "writes": False})
        return 0
    except (ContractError, shared.ContractError) as exc:
        _emit({"task_id": TASK_ID, "status": "blocked", "reason_code": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

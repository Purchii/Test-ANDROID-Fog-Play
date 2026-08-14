"""Fail-closed TASK-044 television reference-lane evidence adapter.

This module does not contain device commands.  Runtime control belongs to a
local-only adapter; this code validates its typed result and derives a
public-safe, atomic report bundle.  The validate-only mode deliberately does
not read files, create processes, access the network, or write output.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


TASK_ID = "TASK-044"
ADAPTER_SCHEMA_VERSION = "task044-runtime-adapter-v1"
ORACLE_SCHEMA_VERSION = "task044-reference-lane-oracle-v1"
REPORT_SCHEMA_VERSION = "evidence-report-envelope-v2"
SAFETY_CLASS = "PROD_CONDITIONAL_BOUNDED_RUNTIME"
SCENARIO_CONTRACT_VERSION = "task044-scenarios-v1"
LANE_ALIAS = "tv-tpv-013"
PROFILE_ALIAS = "tv-tpv-a12-013"
APK_FAMILY = "television-full"
REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = REPO_ROOT / "docs/qa/epics/scenarios/task044_scenarios.csv"
SELECTION = REPO_ROOT / "docs/qa/reports/task043_task044_selection.csv"
ORACLE_SCHEMA = REPO_ROOT / "docs/qa/schemas/task044-reference-lane-oracle-v1.schema.json"
ORACLE_SCHEMA_SHA256 = "1cb29ec9aabf162b4c376d58f78901c9a1672616b75e1fa6aaf7c99de4609271"
TASK042_AUTHORITY = REPO_ROOT / "docs/qa/reports/task042_local_runtime_preflight.summary.json"
DEVICE_REVIEW_AUTHORITY = REPO_ROOT / "docs/approvals/device_inventory.public_safe.review.json"
REPORT_OUTPUT = REPO_ROOT / "docs/qa/reports/task044_tpv13_reference_lane.summary.json"
SCENARIO_LEDGER_OUTPUT = REPO_ROOT / "docs/qa/reports/task044_tpv13_reference_lane.scenario-ledger.csv"
CHECKPOINT_LEDGER_OUTPUT = REPO_ROOT / "docs/qa/reports/task044_tpv13_reference_lane.checkpoint-ledger.csv"
ANOMALY_LEDGER_OUTPUT = REPO_ROOT / "docs/qa/reports/task044_tpv13_reference_lane.anomaly-ledger.csv"
LOCAL_ADAPTER_ROOT = REPO_ROOT / ".qa_local" / "evidence" / "task-044"

CATALOG_HEADERS = (
    "scenario_id", "priority", "surface_ids", "lane", "category", "title",
    "preconditions", "steps", "expected_oracle", "negative_or_boundary",
    "automation_target", "evidence_required", "safety_class", "blocking_rule",
)
SELECTION_HEADERS = (
    "scenario_id", "priority", "surface_ids", "lane", "selection_status",
    "evidence_status", "reason_code",
)
SCENARIO_LEDGER_HEADERS = (
    "scenario_id", "priority", "surface_ids", "category", "scenario_status",
    "evidence_type", "evidence_status", "attempt_count", "reason_code",
    "fresh_visual_pair", "retry_or_recovery_seen", "boundary_safely_held",
    "defect_alias", "defect_reference",
)
CHECKPOINT_LEDGER_HEADERS = (
    "scenario_id", "attempt_id", "attempt_index", "recovery_attempt",
    "recovery_of_attempt_id", "pre_state_alias", "action_category",
    "observed_state_alias", "screen_alias", "state_category", "focus_category",
    "recurrence_status", "prior_screen_alias", "risk_note_code",
    "screenshot_present", "ui_tree_present", "visual_inspection_present",
    "freshness_status", "oracle_result", "cleanup_status",
    "dynamic_assertion_policy",
)
ANOMALY_LEDGER_HEADERS = (
    "record_type", "anomaly_id", "anomaly_alias", "category",
    "classification", "evidence_status", "scenario_id", "attempt_id",
    "trigger_category", "expected_result_category",
    "observed_result_category", "public_safe_screen_alias",
    "cause_evidence_status", "cause_category", "test_design_implication",
    "first_failure_retained", "reason_code",
)

SCENARIO_STATUSES = {
    "observed_pass", "observed_fail", "confirmed_defect", "tooling_defect",
    "executable_not_run", "blocked_by_device", "blocked_by_fixture",
    "blocked_by_oracle", "blocked_by_product_boundary",
    "blocked_by_external_state", "not_applicable", "mapped_only",
}
BLOCKED_STATUSES = {status for status in SCENARIO_STATUSES if status.startswith("blocked_")}
NON_PASS_STATUSES = SCENARIO_STATUSES - {"observed_pass"}
TERMINAL_STATUSES = SCENARIO_STATUSES - {"executable_not_run", "mapped_only"}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
EVIDENCE_TYPES = {
    "physical_runtime", "paired_physical_runtime", "avd_tooling_runtime",
    "synthetic_offline", "static_contract", "manual_observation", "mapped_only",
}
ORACLE_RESULTS = {"pass", "fail", "blocked", "not_observed"}
KNOWN_ANOMALIES = {
    "loader_not_catalog", "search_keyboard_trap", "settings_logout_route",
}
BOUNDARY_RECOVERY_SCENARIOS = {"QA-044-021", "QA-044-022", "QA-044-023"}
ANOMALY_CLASSIFICATIONS = {
    "resolved", "observed_fail", "confirmed_defect", "tooling_defect",
    "blocked_by_oracle", "blocked_by_external_state", "not_run",
}
RUNTIME_ANOMALY_CLASSIFICATIONS = {"observed_fail", "confirmed_defect", "tooling_defect"}

# A clean pass is semantic, not merely a successful generic adapter action.
# Each scenario has an exact action sequence and public-safe state/focus oracle.
SCENARIO_PASS_ORACLES: dict[str, dict[str, Any]] = {
    "QA-044-001": {"actions": ("verify_reference_apk_intake",), "observed": "reference_apk_launchable", "state": "intake", "focus": "not_applicable"},
    "QA-044-002": {"actions": ("force_stop_cold_launch",), "observed": "actionable_shell_reached", "state": "startup", "focus": "actionable_focus"},
    "QA-044-003": {"actions": ("warm_foreground_launch",), "observed": "restored_actionable_shell", "state": "startup", "focus": "restored_focus"},
    "QA-044-004": {"actions": ("bounded_loader_classification",), "observed": "loader_not_misclassified", "state": "negative", "focus": "classification_recorded"},
    "QA-044-005": {"actions": ("observe_existing_synthetic_session",), "observed": "post_auth_shell", "state": "auth", "focus": "actionable_focus"},
    "QA-044-006": {"actions": ("home_foreground_session_restore",), "observed": "session_restored", "state": "session", "focus": "restored_focus"},
    "QA-044-007": {"actions": ("force_stop_session_restore",), "observed": "session_outcome_observed", "state": "session", "focus": "focus_classified"},
    "QA-044-008": {"actions": ("catalog_actionability_probe",), "observed": "actionable_catalog", "state": "catalog", "focus": "actionable_focus"},
    "QA-044-009": {"actions": ("dynamic_rail_traversal",), "observed": "rail_boundaries_recorded", "state": "catalog", "focus": "focus_movement_recorded"},
    "QA-044-010": {"actions": ("grid_focus_acquisition",), "observed": "grid_focus_acquired", "state": "focus", "focus": "focus_visible"},
    "QA-044-011": {"actions": ("noop_focus_loss_compare",), "observed": "focus_outcome_classified", "state": "negative", "focus": "focus_classified"},
    "QA-044-012": {"actions": ("open_search_keyboard",), "observed": "search_keyboard_visible", "state": "search", "focus": "keyboard_focus"},
    "QA-044-013": {"actions": ("input_safe_unicode_query",), "observed": "query_state_classified", "state": "search", "focus": "input_focus"},
    "QA-044-014": {"actions": ("search_back_escape",), "observed": "keyboard_closed_focus_returned", "state": "negative", "focus": "focus_returned"},
    "QA-044-015": {"actions": ("search_force_stop_fallback",), "observed": "first_failure_and_recovery_recorded", "state": "recovery", "focus": "restored_focus"},
    "QA-044-016": {"actions": ("open_settings_root",), "observed": "settings_root", "state": "settings", "focus": "settings_focus"},
    "QA-044-017": {"actions": ("settings_gamepad_navigation",), "observed": "gamepad_destination", "state": "settings", "focus": "gamepad_focus"},
    "QA-044-018": {"actions": ("logout_cancel_boundary",), "observed": "logout_cancelled_without_mutation", "state": "settings", "focus": "cancel_focus"},
    "QA-044-019": {"actions": ("open_game_detail",), "observed": "game_detail", "state": "detail", "focus": "detail_focus"},
    "QA-044-020": {"actions": ("open_server_list",), "observed": "server_list", "state": "detail", "focus": "server_list_focus"},
    "QA-044-021": {"actions": ("observe_session_boundary_and_back",), "observed": "boundary_back_recovered", "state": "boundary", "focus": "focus_restored"},
    "QA-044-022": {"actions": ("capture_qr_boundary_and_back",), "observed": "qr_boundary_back_recovered", "state": "boundary", "focus": "focus_restored"},
    "QA-044-023": {"actions": ("back_family_navigation",), "observed": "parent_behavior_classified", "state": "navigation", "focus": "focus_classified"},
    "QA-044-024": {"actions": ("home_foreground_family_restore",), "observed": "family_state_restoration_classified", "state": "lifecycle", "focus": "focus_classified"},
    "QA-044-025": {"actions": ("process_kill_relaunch",), "observed": "process_restoration_classified", "state": "lifecycle", "focus": "focus_classified"},
    "QA-044-026": {"actions": ("ambient_wake_recovery",), "observed": "app_focus_restored", "state": "system", "focus": "actionable_focus"},
    "QA-044-027": {"actions": ("invoke_safe_deeplink",), "observed": "safe_route_classified", "state": "deeplink", "focus": "focus_classified"},
    "QA-044-028": {"actions": ("bounded_log_privacy_scan",), "observed": "public_log_summary_safe", "state": "privacy", "focus": "not_applicable"},
    "QA-044-029": {"actions": ("bounded_crash_anr_scan",), "observed": "crash_anr_result_classified", "state": "stability", "focus": "not_applicable"},
    "QA-044-030": {"actions": ("screenshot_tree_compare",), "observed": "modality_consistency_classified", "state": "evidence", "focus": "focus_classified"},
    "QA-044-031": {"actions": ("repeatability_cycle_1", "repeatability_cycle_2", "repeatability_cycle_3"), "observed": "repeatability_cycle_recorded", "state": "repeatability", "focus": "restored_focus"},
    "QA-044-032": {"actions": ("validate_terminal_ledger",), "observed": "terminal_ledger_valid", "state": "closure", "focus": "not_applicable"},
}

SCENARIO_BLOCKER_REASON_CODES = {
    scenario_id: f"qa044_{scenario_id[-3:]}_runtime_prerequisite_unavailable"
    for scenario_id in SCENARIO_PASS_ORACLES
}
SCENARIO_BLOCKER_REASON_CODES.update({
    "QA-044-013": "tooling_input_unsupported",
    "QA-044-024": "partial_family_home_return_not_executed",
})
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
SCENARIO_ID_RE = re.compile(r"^QA-044-[0-9]{3}$")
FORMULA_PREFIXES = ("=", "+", "-", "@")
FORBIDDEN_PUBLIC_PATTERNS = (
    re.compile(r"(?i)(?:https?|wss?)://"),
    re.compile(r"(?i)(?:^|[\\/])\.qa_local(?:[\\/]|$)"),
    re.compile(r"(?i)^[a-z]:[\\/]"),
    re.compile(r"(?i)^/(?:home|users|private|var)/"),
    re.compile(r"(?i)\b(?:serial|imei|android_id|token|cookie|password|otp|endpoint|ip)\s*[:=]"),
    re.compile(r"(?<![A-Za-z0-9])\d{10,}(?![A-Za-z0-9])"),
    re.compile(r"(?i)^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"),
    re.compile(r"^(?:account|user|email|phone|session|device|serial|token)[A-Z0-9][A-Za-z0-9_-]*$"),
)


class ContractError(Exception):
    """Public-safe validation failure."""

    def __init__(self, reason_code: str, *, recovery_status: str | None = None) -> None:
        super().__init__(reason_code)
        self.recovery_status = recovery_status


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractError("TIMESTAMP_INVALID")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise ContractError("TIMESTAMP_INVALID") from None
    if parsed.tzinfo is None:
        raise ContractError("TIMESTAMP_INVALID")
    return parsed.astimezone(timezone.utc)


def _fixed_file(path: Path, *, suffix: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
        root = REPO_ROOT.resolve(strict=True)
    except OSError:
        raise ContractError("INPUT_MISSING") from None
    if resolved != path.absolute() or not resolved.is_relative_to(root):
        raise ContractError("INPUT_PATH_NOT_CANONICAL")
    if resolved.suffix.lower() != suffix or resolved.is_symlink():
        raise ContractError("INPUT_TYPE_INVALID")
    return resolved


def _read_csv(path: Path, headers: Sequence[str]) -> list[dict[str, str]]:
    fixed = _fixed_file(path, suffix=".csv")
    try:
        text = fixed.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        raise ContractError("INPUT_UNREADABLE") from None
    reader = csv.DictReader(io.StringIO(text))
    if tuple(reader.fieldnames or ()) != tuple(headers):
        raise ContractError("CSV_HEADERS_INVALID")
    rows = list(reader)
    if not rows or any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ContractError("CSV_ROWS_INVALID")
    return rows


def _authority_sha256(path: Path) -> str:
    return hashlib.sha256(_fixed_file(path, suffix=".json").read_bytes()).hexdigest()


def _validate_public_authority_inputs() -> None:
    for path in (TASK042_AUTHORITY, DEVICE_REVIEW_AUTHORITY):
        fixed = _fixed_file(path, suffix=".json")
        try:
            value = json.loads(fixed.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise ContractError("PREFLIGHT_AUTHORITY_UNREADABLE") from None
        if not isinstance(value, dict):
            raise ContractError("PREFLIGHT_AUTHORITY_INVALID")
    task042 = json.loads(TASK042_AUTHORITY.read_text(encoding="utf-8"))
    review = json.loads(DEVICE_REVIEW_AUTHORITY.read_text(encoding="utf-8"))
    if TASK042_AUTHORITY.name != "task042_local_runtime_preflight.summary.json":
        raise ContractError("PREFLIGHT_AUTHORITY_INVALID")
    devices = review.get("devices")
    if not isinstance(devices, list) or not any(
        item.get("device_alias") == LANE_ALIAS
        and item.get("runtime_profile_alias") == PROFILE_ALIAS
        and item.get("form_factor") == "tv"
        for item in devices if isinstance(item, dict)
    ):
        raise ContractError("DEVICE_AUTHORITY_LANE_MISSING")
    if task042.get("task_id") != "TASK-042":
        raise ContractError("PREFLIGHT_AUTHORITY_INVALID")


def _load_oracle_schema() -> dict[str, Any]:
    fixed = _fixed_file(ORACLE_SCHEMA, suffix=".json")
    try:
        raw = fixed.read_bytes()
        schema = json.loads(raw, object_pairs_hook=_json_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ContractError("ORACLE_SCHEMA_UNREADABLE") from None
    if hashlib.sha256(raw).hexdigest() != ORACLE_SCHEMA_SHA256:
        raise ContractError("ORACLE_SCHEMA_DIGEST_INVALID")
    if (
        not isinstance(schema, dict)
        or schema.get("$id") != _repo_reference(ORACLE_SCHEMA)
        or set(schema.get("required", [])) != {
            "schema_version", "run_id", "generated_at_utc", "build_ref", "target",
            "scenario_contract_version", "runtime_preflight", "known_anomaly_rechecks",
            "runtime_anomalies", "scenarios",
        }
        or schema.get("properties", {}).get("scenarios", {}).get("minItems") != 32
        or schema.get("properties", {}).get("scenarios", {}).get("items") != {"$ref": "#/$defs/scenario"}
        or schema.get("$defs", {}).get("scenario", {}).get("additionalProperties") is not False
        or schema.get("$defs", {}).get("attempt", {}).get("additionalProperties") is not False
    ):
        raise ContractError("ORACLE_SCHEMA_CONTRACT_INVALID")
    return schema


def _validate_schema_instance(
    instance: Any, schema: Mapping[str, Any], *, root: Mapping[str, Any], path: str = "$"
) -> None:
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            raise ContractError("ORACLE_SCHEMA_REFERENCE_INVALID")
        target: Any = root
        for part in reference[2:].split("/"):
            if not isinstance(target, dict) or part not in target:
                raise ContractError("ORACLE_SCHEMA_REFERENCE_INVALID")
            target = target[part]
        _validate_schema_instance(instance, target, root=root, path=path)
        return
    for branch in schema.get("allOf", []):
        _validate_schema_instance(instance, branch, root=root, path=path)
    if "const" in schema and instance != schema["const"]:
        raise ContractError("ADAPTER_SCHEMA_INSTANCE_INVALID")
    if "enum" in schema and instance not in schema["enum"]:
        raise ContractError("ADAPTER_SCHEMA_INSTANCE_INVALID")
    expected_type = schema.get("type")
    if expected_type is not None:
        names = expected_type if isinstance(expected_type, list) else [expected_type]
        matches = any(
            (name == "object" and isinstance(instance, dict))
            or (name == "array" and isinstance(instance, list))
            or (name == "string" and isinstance(instance, str))
            or (name == "boolean" and isinstance(instance, bool))
            or (name == "null" and instance is None)
            for name in names
        )
        if not matches:
            raise ContractError("ADAPTER_SCHEMA_INSTANCE_INVALID")
    if instance is None:
        return
    if isinstance(instance, dict):
        required = schema.get("required", [])
        if not isinstance(required, list) or any(key not in instance for key in required):
            raise ContractError("ADAPTER_SCHEMA_INSTANCE_INVALID")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ContractError("ORACLE_SCHEMA_CONTRACT_INVALID")
        if schema.get("additionalProperties") is False and set(instance) - set(properties):
            raise ContractError("ADAPTER_SCHEMA_INSTANCE_INVALID")
        for key, value in instance.items():
            if key in properties:
                _validate_schema_instance(value, properties[key], root=root, path=f"{path}.{key}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0) or len(instance) > schema.get("maxItems", len(instance)):
            raise ContractError("ADAPTER_SCHEMA_INSTANCE_INVALID")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, value in enumerate(instance):
                _validate_schema_instance(value, item_schema, root=root, path=f"{path}[{index}]")
    if isinstance(instance, str) and "pattern" in schema:
        try:
            matched = re.fullmatch(schema["pattern"], instance)
        except (re.error, TypeError):
            raise ContractError("ORACLE_SCHEMA_CONTRACT_INVALID") from None
        if matched is None:
            raise ContractError("ADAPTER_SCHEMA_INSTANCE_INVALID")


def _validate_oracle_schema() -> None:
    _load_oracle_schema()


def _validate_adapter_against_schema(adapter: Mapping[str, Any]) -> None:
    schema = _load_oracle_schema()
    _validate_schema_instance(adapter, schema, root=schema)


def validate_static_constants() -> list[str]:
    errors: list[str] = []
    if TASK_ID != "TASK-044" or LANE_ALIAS != "tv-tpv-013":
        errors.append("IMMUTABLE_IDENTITY_INVALID")
    if SCENARIO_STATUSES != {
        "observed_pass", "observed_fail", "confirmed_defect", "tooling_defect",
        "executable_not_run", "blocked_by_device", "blocked_by_fixture",
        "blocked_by_oracle", "blocked_by_product_boundary",
        "blocked_by_external_state", "not_applicable", "mapped_only",
    }:
        errors.append("STATUS_CONTRACT_INVALID")
    if not {"screenshot", "ui_tree"}.issubset({"screenshot", "ui_tree", "runner_log", "ledger"}):
        errors.append("VISUAL_MODALITY_CONTRACT_INVALID")
    expected_ids = {f"QA-044-{index:03d}" for index in range(1, 33)}
    if set(SCENARIO_PASS_ORACLES) != expected_ids or set(SCENARIO_BLOCKER_REASON_CODES) != expected_ids:
        errors.append("SCENARIO_SEMANTIC_CONTRACT_INVALID")
    if SCENARIO_PASS_ORACLES["QA-044-031"]["actions"] != (
        "repeatability_cycle_1", "repeatability_cycle_2", "repeatability_cycle_3"
    ):
        errors.append("REPEATABILITY_ACTION_CONTRACT_INVALID")
    return errors


def load_contract() -> list[dict[str, str]]:
    _validate_public_authority_inputs()
    _validate_oracle_schema()
    catalog = _read_csv(CATALOG, CATALOG_HEADERS)
    selection = _read_csv(SELECTION, SELECTION_HEADERS)
    if len(catalog) != 32 or len(selection) != 32:
        raise ContractError("SCENARIO_COUNT_INVALID")
    if Counter(row["priority"] for row in catalog) != Counter({"P0": 29, "P1": 3}):
        raise ContractError("PRIORITY_RECONCILIATION_INVALID")
    catalog_ids = [row["scenario_id"] for row in catalog]
    if catalog_ids != [f"QA-044-{index:03d}" for index in range(1, 33)]:
        raise ContractError("SCENARIO_ID_SEQUENCE_INVALID")
    if len(catalog_ids) != len(set(catalog_ids)):
        raise ContractError("SCENARIO_ID_DUPLICATE")
    selection_by_id = {row["scenario_id"]: row for row in selection}
    if len(selection_by_id) != 32 or set(selection_by_id) != set(catalog_ids):
        raise ContractError("SELECTION_SET_INVALID")
    for row in catalog:
        selected = selection_by_id[row["scenario_id"]]
        if (
            not SCENARIO_ID_RE.fullmatch(row["scenario_id"])
            or row["lane"] != LANE_ALIAS
            or row["priority"] not in {"P0", "P1"}
            or row["automation_target"] != "automate"
            or row["evidence_required"] != "screenshot+ui_tree+runner_log+ledger"
            or row["safety_class"] != "PROD_CONDITIONAL"
            or selected != {
                "scenario_id": row["scenario_id"], "priority": row["priority"],
                "surface_ids": row["surface_ids"], "lane": row["lane"],
                "selection_status": "selected_not_run", "evidence_status": "hypothesis",
                "reason_code": "task044_reference_lane_contract",
            }
        ):
            raise ContractError("CATALOG_SELECTION_RECONCILIATION_INVALID")
    categories = {row["category"] for row in catalog}
    if not {"boundary", "privacy", "stability", "evidence"}.issubset(categories):
        raise ContractError("MANDATORY_CATEGORY_MISSING")
    return catalog


def _strict_keys(value: Mapping[str, Any], required: set[str], code: str) -> None:
    if set(value) != required:
        raise ContractError(code)


def _safe_public_value(value: Any, *, key: str = "") -> None:
    if isinstance(value, dict):
        for child_key, child in value.items():
            _safe_public_value(child, key=child_key)
    elif isinstance(value, list):
        for child in value:
            _safe_public_value(child, key=key)
    elif isinstance(value, str):
        if key == "sha256" and HASH_RE.fullmatch(value):
            return
        if HASH_RE.fullmatch(value):
            raise ContractError("RAW_HASH_OUTSIDE_ARTIFACT_FIELD")
        if any(pattern.search(value) for pattern in FORBIDDEN_PUBLIC_PATTERNS):
            raise ContractError("PUBLIC_VALUE_FORBIDDEN")


def _load_adapter(path: Path) -> dict[str, Any]:
    # The path itself stays local-only and is never copied into output.
    try:
        candidate = path.absolute()
        resolved = path.resolve(strict=True)
        canonical_root = LOCAL_ADAPTER_ROOT.resolve(strict=True)
        if (
            resolved != candidate
            or not resolved.is_file()
            or path.suffix.lower() != ".json"
            or not resolved.is_relative_to(canonical_root)
        ):
            raise ContractError("ADAPTER_INPUT_TYPE_INVALID")
        current = candidate
        while True:
            attributes = getattr(current.lstat(), "st_file_attributes", 0)
            if current.is_symlink() or attributes & 0x400:
                raise ContractError("ADAPTER_INPUT_TYPE_INVALID")
            if current == canonical_root:
                break
            current = current.parent
        data = json.loads(resolved.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ContractError("ADAPTER_INPUT_UNREADABLE") from None
    if not isinstance(data, dict):
        raise ContractError("ADAPTER_INPUT_INVALID")
    return data


def _validate_adapter_header(adapter: Mapping[str, Any]) -> None:
    _strict_keys(adapter, {
        "schema_version", "run_id", "generated_at_utc", "build_ref",
        "target", "scenario_contract_version", "runtime_preflight",
        "known_anomaly_rechecks", "runtime_anomalies", "scenarios",
    }, "ADAPTER_FIELDS_INVALID")
    if adapter["schema_version"] != ADAPTER_SCHEMA_VERSION:
        raise ContractError("ADAPTER_SCHEMA_INVALID")
    if not isinstance(adapter["run_id"], str) or not SAFE_ID_RE.fullmatch(adapter["run_id"]):
        raise ContractError("RUN_ID_INVALID")
    _utc(adapter["generated_at_utc"])
    build = adapter["build_ref"]
    if not isinstance(build, dict):
        raise ContractError("BUILD_REF_INVALID")
    _strict_keys(build, {"alias", "apk_family"}, "BUILD_REF_INVALID")
    if not SAFE_ID_RE.fullmatch(str(build["alias"])) or build["apk_family"] != APK_FAMILY:
        raise ContractError("CROSS_FAMILY_BUILD_FORBIDDEN")
    target = adapter["target"]
    if not isinstance(target, dict):
        raise ContractError("TARGET_INVALID")
    _strict_keys(target, {"lane_alias", "profile_alias", "form_factor", "physical"}, "TARGET_INVALID")
    if target != {
        "lane_alias": LANE_ALIAS, "profile_alias": PROFILE_ALIAS,
        "form_factor": "tv", "physical": True,
    }:
        raise ContractError("PHONE_OR_CROSS_LANE_SUBSTITUTION_FORBIDDEN")
    if adapter["scenario_contract_version"] != SCENARIO_CONTRACT_VERSION:
        raise ContractError("SCENARIO_CONTRACT_VERSION_INVALID")
    preflight = adapter["runtime_preflight"]
    if not isinstance(preflight, dict):
        raise ContractError("PREFLIGHT_INVALID")
    _strict_keys(preflight, {
        "status", "adb_authorized", "artifact_present", "synthetic_fixture_ready",
        "ignored_evidence_storage_ready", "cleanup_rollback_ready", "reviewer_gate",
        "authority_task_id", "authority_report_reference", "authority_report_sha256",
        "device_review_reference", "device_review_sha256",
    }, "PREFLIGHT_INVALID")
    boolean_fields = {
        "adb_authorized", "artifact_present", "synthetic_fixture_ready",
        "ignored_evidence_storage_ready", "cleanup_rollback_ready", "reviewer_gate",
    }
    if any(not isinstance(preflight[field], bool) for field in boolean_fields):
        raise ContractError("PREFLIGHT_BOOLEAN_INVALID")
    if (
        preflight["authority_task_id"] != "TASK-042"
        or preflight["authority_report_reference"] != _repo_reference(TASK042_AUTHORITY)
        or preflight["authority_report_sha256"] != _authority_sha256(TASK042_AUTHORITY)
        or preflight["device_review_reference"] != _repo_reference(DEVICE_REVIEW_AUTHORITY)
        or preflight["device_review_sha256"] != _authority_sha256(DEVICE_REVIEW_AUTHORITY)
    ):
        raise ContractError("PREFLIGHT_AUTHORITY_LINK_INVALID")
    expected_ready = all(preflight[field] for field in boolean_fields)
    if preflight["status"] != ("READY" if expected_ready else "BLOCKED"):
        raise ContractError("PREFLIGHT_STATUS_INCONSISTENT")


def _validate_attempt(attempt: Mapping[str, Any], *, scenario_id: str) -> None:
    _strict_keys(attempt, {
        "attempt_id", "started_at_utc", "completed_at_utc", "pre_state_alias",
        "action_category", "observed_state_alias", "oracle_result", "evidence_type",
        "evidence_status", "modalities", "cleanup_result", "recovery_attempt",
        "recovery_of_attempt_id",
        "dynamic_assertion_policy", "fixed_dynamic_values_used", "boundary",
        "privacy", "crash_anr", "inventory_event",
    }, "ATTEMPT_FIELDS_INVALID")
    if not isinstance(attempt["attempt_id"], str) or not SAFE_ID_RE.fullmatch(attempt["attempt_id"]):
        raise ContractError("ATTEMPT_ID_INVALID")
    started = _utc(attempt["started_at_utc"])
    completed = _utc(attempt["completed_at_utc"])
    if completed < started:
        raise ContractError("ATTEMPT_TIME_INVALID")
    for field in ("pre_state_alias", "action_category", "observed_state_alias"):
        if not isinstance(attempt[field], str) or not SAFE_ID_RE.fullmatch(attempt[field]):
            raise ContractError("ATTEMPT_ALIAS_INVALID")
    if attempt["oracle_result"] not in ORACLE_RESULTS or attempt["evidence_type"] not in EVIDENCE_TYPES:
        raise ContractError("ATTEMPT_ENUM_INVALID")
    if attempt["evidence_status"] not in EVIDENCE_STATUSES:
        raise ContractError("ATTEMPT_EVIDENCE_STATUS_INVALID")
    if attempt["cleanup_result"] not in {"pass", "fail", "not_required"}:
        raise ContractError("CLEANUP_RESULT_INVALID")
    if not isinstance(attempt["recovery_attempt"], bool):
        raise ContractError("RECOVERY_FLAG_INVALID")
    if (
        not isinstance(attempt["recovery_of_attempt_id"], str)
        or not SAFE_ID_RE.fullmatch(attempt["recovery_of_attempt_id"])
        or (attempt["recovery_attempt"] is False and attempt["recovery_of_attempt_id"] != "none")
        or (attempt["recovery_attempt"] is True and attempt["recovery_of_attempt_id"] == "none")
    ):
        raise ContractError("RECOVERY_RELATION_INVALID")
    if attempt["dynamic_assertion_policy"] != "structure_and_category_only" or attempt["fixed_dynamic_values_used"] is not False:
        raise ContractError("DYNAMIC_DATA_ASSERTION_UNSAFE")
    modalities = attempt["modalities"]
    if not isinstance(modalities, dict):
        raise ContractError("MODALITIES_INVALID")
    _strict_keys(modalities, {"screenshot", "ui_tree", "runner_log"}, "MODALITIES_INVALID")
    for name in ("screenshot", "ui_tree", "runner_log"):
        item = modalities[name]
        if not isinstance(item, dict):
            raise ContractError("MODALITY_INVALID")
        required = {"evidence_id", "captured_at_utc"}
        if name == "screenshot":
            required.add("visual_inspection")
        _strict_keys(item, required, "MODALITY_FIELDS_INVALID")
        if not isinstance(item["evidence_id"], str) or not SAFE_ID_RE.fullmatch(item["evidence_id"]):
            raise ContractError("EVIDENCE_ID_INVALID")
        captured = _utc(item["captured_at_utc"])
        if captured < started or captured > completed:
            raise ContractError("EVIDENCE_STALE_OR_OUTSIDE_ATTEMPT")
        if name == "screenshot" and item["visual_inspection"] is not True:
            raise ContractError("VISUAL_INSPECTION_MISSING")
    for name, required in (
        ("boundary", {
            "applicable", "observed", "external_action_performed",
            "primary_back_recovery_outcome", "fallback_recovery_method",
            "fallback_recovery_outcome",
        }),
        ("privacy", {"applicable", "bounded_log_summary_present", "public_output_scan", "raw_sensitive_values_present"}),
        ("crash_anr", {"applicable", "scan_performed", "result"}),
    ):
        item = attempt[name]
        if not isinstance(item, dict):
            raise ContractError(f"{name.upper()}_CONTRACT_INVALID")
        _strict_keys(item, required, f"{name.upper()}_CONTRACT_INVALID")
    boundary = attempt["boundary"]
    if scenario_id in BOUNDARY_RECOVERY_SCENARIOS:
        if (
            boundary["applicable"] is not True
            or boundary["observed"] is not True
            or boundary["external_action_performed"] is not False
            or boundary["primary_back_recovery_outcome"] not in {"pass", "fail"}
            or boundary["fallback_recovery_method"] not in {"none", "force_stop_relaunch"}
            or boundary["fallback_recovery_outcome"] not in {"not_required", "pass", "fail"}
            or (
                boundary["primary_back_recovery_outcome"] == "pass"
                and (boundary["fallback_recovery_method"] != "none" or boundary["fallback_recovery_outcome"] != "not_required")
            )
            or (
                boundary["primary_back_recovery_outcome"] == "fail"
                and boundary["fallback_recovery_method"] != "force_stop_relaunch"
            )
        ):
            raise ContractError("BOUNDARY_SAFETY_INVALID")
    elif (
        boundary["applicable"] not in {True, False}
        or boundary["external_action_performed"] is not False
        or boundary["primary_back_recovery_outcome"] != "not_applicable"
        or boundary["fallback_recovery_method"] != "none"
        or boundary["fallback_recovery_outcome"] != "not_required"
    ):
        raise ContractError("BOUNDARY_SAFETY_INVALID")
    privacy = attempt["privacy"]
    if scenario_id == "QA-044-028" and privacy != {
        "applicable": True, "bounded_log_summary_present": True,
        "public_output_scan": "pass", "raw_sensitive_values_present": False,
    }:
        raise ContractError("PRIVACY_LOG_ORACLE_INVALID")
    if privacy["raw_sensitive_values_present"] is not False:
        raise ContractError("PUBLIC_PRIVACY_FAILURE")
    crash = attempt["crash_anr"]
    if scenario_id == "QA-044-029" and (
        crash["applicable"] is not True or crash["scan_performed"] is not True
        or crash["result"] not in {"clear", "signal_classified"}
    ):
        raise ContractError("CRASH_ANR_ORACLE_MISSING")
    inventory = attempt["inventory_event"]
    if not isinstance(inventory, dict):
        raise ContractError("INVENTORY_EVENT_INVALID")
    _strict_keys(inventory, {
        "screen_alias", "state_category", "focus_category", "risk_note_code",
        "recurrence_status", "prior_screen_alias", "recurrence_match",
    }, "INVENTORY_EVENT_INVALID")
    for field in ("screen_alias", "state_category", "focus_category", "risk_note_code", "prior_screen_alias"):
        if not isinstance(inventory[field], str) or not SAFE_ID_RE.fullmatch(inventory[field]):
            raise ContractError("INVENTORY_EVENT_VALUE_INVALID")
    if inventory["recurrence_status"] not in {"first_observation", "recurrence"}:
        raise ContractError("INVENTORY_RECURRENCE_INVALID")
    if inventory["recurrence_match"] not in {"not_applicable", "matched", "changed"}:
        raise ContractError("INVENTORY_RECURRENCE_INVALID")
    if (
        (inventory["recurrence_status"] == "first_observation" and (
            inventory["prior_screen_alias"] != "none" or inventory["recurrence_match"] != "not_applicable"
        ))
        or (inventory["recurrence_status"] == "recurrence" and inventory["prior_screen_alias"] == "none")
    ):
        raise ContractError("INVENTORY_RECURRENCE_INVALID")


def _clean_pass(
    attempts: Sequence[Mapping[str, Any]], preflight_ready: bool, scenario_id: str
) -> bool:
    oracle = SCENARIO_PASS_ORACLES[scenario_id]
    if not preflight_ready or len(attempts) != len(oracle["actions"]):
        return False
    return tuple(attempt["action_category"] for attempt in attempts) == oracle["actions"] and all(
        attempt["oracle_result"] == "pass"
        and attempt["evidence_type"] == "physical_runtime"
        and attempt["evidence_status"] == "confirmed"
        and attempt["cleanup_result"] in {"pass", "not_required"}
        and attempt["recovery_attempt"] is False
        and attempt["recovery_of_attempt_id"] == "none"
        and attempt["observed_state_alias"] == oracle["observed"]
        and attempt["inventory_event"]["state_category"] == oracle["state"]
        and attempt["inventory_event"]["focus_category"] == oracle["focus"]
        and (
            scenario_id not in BOUNDARY_RECOVERY_SCENARIOS
            or (
                attempt["boundary"]["primary_back_recovery_outcome"] == "pass"
                and attempt["boundary"]["fallback_recovery_method"] == "none"
                and attempt["boundary"]["fallback_recovery_outcome"] == "not_required"
            )
        )
        for attempt in attempts
    )


def _derive_scenario(
    row: Mapping[str, str], entry: Mapping[str, Any], *, preflight_ready: bool
) -> dict[str, Any]:
    _strict_keys(entry, {"scenario_id", "attempts", "blocker", "defect"}, "SCENARIO_ENTRY_FIELDS_INVALID")
    if entry["scenario_id"] != row["scenario_id"] or not isinstance(entry["attempts"], list):
        raise ContractError("SCENARIO_ENTRY_INVALID")
    blocker = entry["blocker"]
    if blocker is not None:
        if not isinstance(blocker, dict):
            raise ContractError("BLOCKER_INVALID")
        _strict_keys(blocker, {"status", "reason_code"}, "BLOCKER_INVALID")
        if (
            blocker["status"] not in BLOCKED_STATUSES
            or blocker["reason_code"] != SCENARIO_BLOCKER_REASON_CODES[row["scenario_id"]]
        ):
            raise ContractError("BLOCKER_REASON_CODE_INVALID")
    attempts = entry["attempts"]
    for attempt in attempts:
        if not isinstance(attempt, dict):
            raise ContractError("ATTEMPT_INVALID")
        _validate_attempt(attempt, scenario_id=row["scenario_id"])
    attempt_positions = {attempt["attempt_id"]: index for index, attempt in enumerate(attempts)}
    if len(attempt_positions) != len(attempts):
        raise ContractError("ATTEMPT_ID_DUPLICATE")
    for index, attempt in enumerate(attempts):
        relation = attempt["recovery_of_attempt_id"]
        if attempt["recovery_attempt"] and (
            relation not in attempt_positions or attempt_positions[relation] >= index
        ):
            raise ContractError("RECOVERY_RELATION_INVALID")
    defect = entry["defect"]
    if defect is not None:
        if not isinstance(defect, dict):
            raise ContractError("DEFECT_REFERENCE_INVALID")
        _strict_keys(defect, {
            "defect_alias", "reference", "sha256", "reproduction_attempt_ids",
        }, "DEFECT_REFERENCE_INVALID")
        reference = defect["reference"]
        if (
            not isinstance(reference, str)
            or not reference.startswith("docs/qa/defects/task044_")
            or not reference.endswith(".md")
            or not isinstance(defect["defect_alias"], str)
            or not SAFE_ID_RE.fullmatch(defect["defect_alias"])
            or not isinstance(defect["sha256"], str)
            or not HASH_RE.fullmatch(defect["sha256"])
            or not isinstance(defect["reproduction_attempt_ids"], list)
            or not defect["reproduction_attempt_ids"]
        ):
            raise ContractError("DEFECT_REFERENCE_INVALID")
        defect_path = REPO_ROOT / PurePosixPath(reference)
        fixed_defect = _fixed_file(defect_path, suffix=".md")
        defect_text = fixed_defect.read_text(encoding="utf-8")
        reproduction_ids = defect["reproduction_attempt_ids"]
        if (
            hashlib.sha256(fixed_defect.read_bytes()).hexdigest() != defect["sha256"]
            or f"`{defect['defect_alias']}`" not in defect_text
            or "`tv-tpv-013`" not in defect_text
            or "`television-full`" not in defect_text
            or len(set(reproduction_ids)) != len(reproduction_ids)
            or any(
                attempt_id not in attempt_positions
                or attempts[attempt_positions[attempt_id]]["oracle_result"] != "fail"
                for attempt_id in reproduction_ids
            )
        ):
            raise ContractError("DEFECT_REPRODUCTION_LINK_INVALID")
    if blocker is not None:
        status = blocker["status"]
        reason = blocker["reason_code"]
    elif not attempts:
        status = "executable_not_run"
        reason = "runtime_not_run"
    elif defect is not None:
        status = "confirmed_defect"
        reason = "confirmed_runtime_defect"
    elif _clean_pass(attempts, preflight_ready, row["scenario_id"]):
        status = "observed_pass"
        reason = "fresh_physical_visual_oracle_pass"
    elif any(attempt["evidence_type"] != "physical_runtime" for attempt in attempts):
        status = "tooling_defect"
        reason = "physical_runtime_evidence_required"
    else:
        status = "observed_fail"
        reason = "retry_recovery_stale_or_oracle_failure_retained"
    evidence_type = attempts[-1]["evidence_type"] if attempts else "mapped_only"
    evidence_status = "confirmed" if attempts and all(item["evidence_status"] == "confirmed" for item in attempts) else "unknown"
    fresh_pair = bool(attempts and all(
        set(item["modalities"]) == {"screenshot", "ui_tree", "runner_log"}
        and item["modalities"]["screenshot"]["visual_inspection"] is True
        for item in attempts
    ))
    boundary_held = all(
        item["boundary"]["external_action_performed"] is False
        and (
            row["scenario_id"] not in BOUNDARY_RECOVERY_SCENARIOS
            or item["boundary"]["primary_back_recovery_outcome"] == "pass"
        )
        for item in attempts
    ) if attempts else True
    return {
        "scenario_id": row["scenario_id"], "priority": row["priority"],
        "surface_ids": row["surface_ids"], "category": row["category"],
        "scenario_status": status, "evidence_type": evidence_type,
        "evidence_status": evidence_status, "attempt_count": len(attempts),
        "reason_code": reason, "fresh_visual_pair": fresh_pair,
        "retry_or_recovery_seen": (
            (len(attempts) > 1 and row["scenario_id"] != "QA-044-031")
            or any(item["recovery_attempt"] for item in attempts)
        ),
        "boundary_safely_held": boundary_held, "attempts": attempts,
        "defect_alias": defect["defect_alias"] if defect else "none",
        "defect_reference": defect["reference"] if defect else "none",
    }


def validate_and_derive(adapter: Mapping[str, Any], catalog: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    _validate_adapter_against_schema(adapter)
    _validate_adapter_header(adapter)
    scenarios = adapter["scenarios"]
    if not isinstance(scenarios, list) or len(scenarios) != 32:
        raise ContractError("ADAPTER_SCENARIO_COUNT_INVALID")
    by_id = {entry.get("scenario_id"): entry for entry in scenarios if isinstance(entry, dict)}
    if len(by_id) != 32 or set(by_id) != {row["scenario_id"] for row in catalog}:
        raise ContractError("ADAPTER_SCENARIO_SET_INVALID")
    preflight_ready = adapter["runtime_preflight"]["status"] == "READY"
    derived = [_derive_scenario(row, by_id[row["scenario_id"]], preflight_ready=preflight_ready) for row in catalog]
    generated = _utc(adapter["generated_at_utc"])
    seen_attempt_ids: set[str] = set()
    seen_evidence_ids: set[str] = set()
    for row in derived:
        for attempt in row["attempts"]:
            completed = _utc(attempt["completed_at_utc"])
            if generated < completed or (generated - completed).total_seconds() > 86400:
                raise ContractError("RUN_EVIDENCE_NOT_FRESH")
            if attempt["attempt_id"] in seen_attempt_ids:
                raise ContractError("ATTEMPT_ID_DUPLICATE")
            seen_attempt_ids.add(attempt["attempt_id"])
            for modality in attempt["modalities"].values():
                if modality["evidence_id"] in seen_evidence_ids:
                    raise ContractError("EVIDENCE_ID_DUPLICATE")
                seen_evidence_ids.add(modality["evidence_id"])
    anomaly_rows = adapter["known_anomaly_rechecks"]
    if not isinstance(anomaly_rows, list) or len(anomaly_rows) != 3:
        raise ContractError("KNOWN_ANOMALY_SET_INVALID")
    seen: set[str] = set()
    for item in anomaly_rows:
        if not isinstance(item, dict):
            raise ContractError("KNOWN_ANOMALY_INVALID")
        _strict_keys(item, {
            "anomaly_alias", "category", "classification", "evidence_status",
            "scenario_id", "trigger_category", "expected_result_category",
            "observed_result_category", "public_safe_screen_alias",
            "cause_evidence_status", "cause_category", "test_design_implication",
            "first_failure_retained", "reason_code",
        }, "KNOWN_ANOMALY_FIELDS_INVALID")
        if (
            item["anomaly_alias"] in seen or item["anomaly_alias"] not in KNOWN_ANOMALIES
            or item["classification"] not in ANOMALY_CLASSIFICATIONS
            or item["evidence_status"] not in EVIDENCE_STATUSES
            or item["cause_evidence_status"] not in {"likely", "hypothesis", "unknown"}
            or item["scenario_id"] not in by_id
            or not isinstance(item["first_failure_retained"], bool)
            or any(not isinstance(item[field], str) or not SAFE_ID_RE.fullmatch(item[field]) for field in (
                "category", "trigger_category", "expected_result_category",
                "observed_result_category", "public_safe_screen_alias", "cause_category",
                "test_design_implication", "reason_code",
            ))
        ):
            raise ContractError("KNOWN_ANOMALY_INVALID")
        if item["classification"] == "resolved" and (
            item["evidence_status"] != "confirmed"
            or item["observed_result_category"] == "not_run"
            or item["first_failure_retained"] is not True
        ):
            raise ContractError("KNOWN_ANOMALY_RESOLUTION_INVALID")
        seen.add(item["anomaly_alias"])
    if seen != KNOWN_ANOMALIES:
        raise ContractError("KNOWN_ANOMALY_SET_INVALID")

    runtime_anomalies = adapter["runtime_anomalies"]
    if not isinstance(runtime_anomalies, list):
        raise ContractError("RUNTIME_ANOMALIES_INVALID")
    derived_by_id = {row["scenario_id"]: row for row in derived}
    attempt_owner = {
        attempt["attempt_id"]: row["scenario_id"]
        for row in derived
        for attempt in row["attempts"]
    }
    seen_runtime_ids: set[str] = set()
    covered_scenarios: set[str] = set()
    covered_failed_attempts: set[str] = set()
    runtime_fields = {
        "anomaly_id", "anomaly_alias", "category", "classification",
        "evidence_status", "scenario_id", "attempt_id", "trigger_category",
        "expected_result_category", "observed_result_category",
        "public_safe_screen_alias", "cause_evidence_status", "cause_category",
        "test_design_implication", "first_failure_retained", "reason_code",
    }
    for item in runtime_anomalies:
        if not isinstance(item, dict):
            raise ContractError("RUNTIME_ANOMALY_INVALID")
        _strict_keys(item, runtime_fields, "RUNTIME_ANOMALY_FIELDS_INVALID")
        scenario_id = item["scenario_id"]
        if (
            not isinstance(item["anomaly_id"], str)
            or not SAFE_ID_RE.fullmatch(item["anomaly_id"])
            or item["anomaly_id"] in seen_runtime_ids
            or item["classification"] not in RUNTIME_ANOMALY_CLASSIFICATIONS
            or item["evidence_status"] != "confirmed"
            or item["cause_evidence_status"] not in {"likely", "hypothesis", "unknown"}
            or scenario_id not in derived_by_id
            or item["classification"] != derived_by_id[scenario_id]["scenario_status"]
            or item["attempt_id"] not in attempt_owner
            or attempt_owner[item["attempt_id"]] != scenario_id
            or item["first_failure_retained"] is not True
            or any(not isinstance(item[field], str) or not SAFE_ID_RE.fullmatch(item[field]) for field in (
                "anomaly_alias", "category", "attempt_id", "trigger_category",
                "expected_result_category", "observed_result_category",
                "public_safe_screen_alias", "cause_category",
                "test_design_implication", "reason_code",
            ))
        ):
            raise ContractError("RUNTIME_ANOMALY_INVALID")
        seen_runtime_ids.add(item["anomaly_id"])
        covered_scenarios.add(scenario_id)
        covered_failed_attempts.add(item["attempt_id"])
    required_failure_scenarios = {
        row["scenario_id"] for row in derived
        if row["scenario_status"] in RUNTIME_ANOMALY_CLASSIFICATIONS
    }
    required_failed_attempts = {
        attempt["attempt_id"] for row in derived for attempt in row["attempts"]
        if attempt["oracle_result"] == "fail"
    }
    if covered_scenarios != required_failure_scenarios:
        raise ContractError("RUNTIME_ANOMALY_SCENARIO_COVERAGE_INVALID")
    if not required_failed_attempts.issubset(covered_failed_attempts):
        raise ContractError("RUNTIME_ANOMALY_ATTEMPT_COVERAGE_INVALID")
    _safe_public_value({
        "run_id": adapter["run_id"], "build_ref": adapter["build_ref"],
        "target": adapter["target"], "derived": [{k: v for k, v in row.items() if k != "attempts"} for row in derived],
        "attempts": [attempt for row in derived for attempt in row["attempts"]],
        "known_anomalies": anomaly_rows, "runtime_anomalies": runtime_anomalies,
    })
    return {
        "scenario_rows": derived, "known_anomaly_rows": anomaly_rows,
        "runtime_anomaly_rows": runtime_anomalies,
    }


def _csv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        values = {header: str(row.get(header, "")).lower() if isinstance(row.get(header), bool) else row.get(header, "") for header in headers}
        if any(str(value).startswith(FORMULA_PREFIXES) for value in values.values()):
            raise ContractError("CSV_FORMULA_VALUE_FORBIDDEN")
        writer.writerow(values)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _repo_reference(path: Path) -> str:
    return PurePosixPath(path.relative_to(REPO_ROOT)).as_posix()


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _checkpoint_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        attempts = row["attempts"]
        for index, attempt in enumerate(attempts, start=1):
            inventory = attempt["inventory_event"]
            result.append({
                "scenario_id": row["scenario_id"], "attempt_id": attempt["attempt_id"],
                "attempt_index": index, "recovery_attempt": attempt["recovery_attempt"],
                "recovery_of_attempt_id": attempt["recovery_of_attempt_id"],
                "pre_state_alias": attempt["pre_state_alias"],
                "action_category": attempt["action_category"],
                "observed_state_alias": attempt["observed_state_alias"],
                "screen_alias": inventory["screen_alias"],
                "state_category": inventory["state_category"],
                "focus_category": inventory["focus_category"],
                "recurrence_status": inventory["recurrence_status"],
                "prior_screen_alias": inventory["prior_screen_alias"],
                "risk_note_code": inventory["risk_note_code"],
                "screenshot_present": "screenshot" in attempt["modalities"],
                "ui_tree_present": "ui_tree" in attempt["modalities"],
                "visual_inspection_present": attempt["modalities"]["screenshot"]["visual_inspection"],
                "freshness_status": "fresh",
                "oracle_result": attempt["oracle_result"],
                "cleanup_status": attempt["cleanup_result"],
                "dynamic_assertion_policy": attempt["dynamic_assertion_policy"],
            })
    return result


def _initial_adapter(catalog: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    return {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "run_id": "task044-initial-not-run",
        "generated_at_utc": "2026-08-14T00:00:00Z",
        "build_ref": {"alias": "television-full-local-build", "apk_family": APK_FAMILY},
        "target": {"lane_alias": LANE_ALIAS, "profile_alias": PROFILE_ALIAS, "form_factor": "tv", "physical": True},
        "scenario_contract_version": SCENARIO_CONTRACT_VERSION,
        "runtime_preflight": {
            "status": "BLOCKED", "adb_authorized": False, "artifact_present": False,
            "synthetic_fixture_ready": False, "ignored_evidence_storage_ready": False,
            "cleanup_rollback_ready": False, "reviewer_gate": False,
            "authority_task_id": "TASK-042",
            "authority_report_reference": _repo_reference(TASK042_AUTHORITY),
            "authority_report_sha256": _authority_sha256(TASK042_AUTHORITY),
            "device_review_reference": _repo_reference(DEVICE_REVIEW_AUTHORITY),
            "device_review_sha256": _authority_sha256(DEVICE_REVIEW_AUTHORITY),
        },
        "known_anomaly_rechecks": [
            {"anomaly_alias": "loader_not_catalog", "category": "loader", "classification": "not_run", "evidence_status": "unknown", "scenario_id": "QA-044-004", "trigger_category": "launch", "expected_result_category": "actionable_catalog", "observed_result_category": "not_run", "public_safe_screen_alias": "not_observed", "cause_evidence_status": "unknown", "cause_category": "unknown", "test_design_implication": "bounded_loader_recheck_required", "first_failure_retained": False, "reason_code": "runtime_not_run"},
            {"anomaly_alias": "search_keyboard_trap", "category": "search", "classification": "not_run", "evidence_status": "unknown", "scenario_id": "QA-044-014", "trigger_category": "search_back", "expected_result_category": "focus_return", "observed_result_category": "not_run", "public_safe_screen_alias": "not_observed", "cause_evidence_status": "unknown", "cause_category": "unknown", "test_design_implication": "back_escape_recheck_required", "first_failure_retained": False, "reason_code": "runtime_not_run"},
            {"anomaly_alias": "settings_logout_route", "category": "settings", "classification": "not_run", "evidence_status": "unknown", "scenario_id": "QA-044-018", "trigger_category": "settings_navigation", "expected_result_category": "gamepad_destination", "observed_result_category": "not_run", "public_safe_screen_alias": "not_observed", "cause_evidence_status": "unknown", "cause_category": "unknown", "test_design_implication": "semantic_focus_recheck_required", "first_failure_retained": False, "reason_code": "runtime_not_run"},
        ],
        "runtime_anomalies": [],
        "scenarios": [{"scenario_id": row["scenario_id"], "attempts": [], "blocker": None, "defect": None} for row in catalog],
    }


def _anomaly_ledger_rows(derived: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in derived["known_anomaly_rows"]:
        rows.append({
            "record_type": "known_recheck",
            "anomaly_id": f"known-{item['anomaly_alias']}",
            "attempt_id": "none",
            **item,
        })
    for item in derived["runtime_anomaly_rows"]:
        rows.append({"record_type": "runtime_anomaly", **item})
    return rows


def build_bundle(adapter: Mapping[str, Any], catalog: Sequence[Mapping[str, str]]) -> dict[Path, bytes]:
    derived = validate_and_derive(adapter, catalog)
    rows = derived["scenario_rows"]
    public_rows = [{k: v for k, v in row.items() if k != "attempts"} for row in rows]
    ledger = _csv_bytes(SCENARIO_LEDGER_HEADERS, public_rows)
    checkpoint_rows = _checkpoint_rows(rows)
    _safe_public_value({"checkpoint_rows": checkpoint_rows})
    checkpoints = _csv_bytes(CHECKPOINT_LEDGER_HEADERS, checkpoint_rows)
    anomaly_ledger_rows = _anomaly_ledger_rows(derived)
    _safe_public_value({"anomaly_ledger_rows": anomaly_ledger_rows})
    anomalies = _csv_bytes(ANOMALY_LEDGER_HEADERS, anomaly_ledger_rows)
    status_counts = Counter(row["scenario_status"] for row in rows)
    anomaly_closed = all(
        item["classification"] == "resolved" and item["evidence_status"] == "confirmed"
        for item in derived["known_anomaly_rows"]
    )
    all_pass = status_counts == Counter({"observed_pass": 32}) and anomaly_closed
    any_attempt = any(row["attempt_count"] for row in rows)
    has_failure = any(row["scenario_status"] in {"observed_fail", "confirmed_defect", "tooling_defect"} for row in rows)
    task_status = "completed" if all_pass else ("failed" if has_failure else ("partial" if any_attempt else "blocked"))
    execution_status = "pass" if all_pass else ("fail" if has_failure else ("partial_blocked" if any_attempt else "blocked"))
    coverage_status = "covered" if all_pass else ("partial_blocked" if any_attempt else "blocked")
    confirmed_failures = [
        {
            "scenario_id": row["scenario_id"], "scenario_status": row["scenario_status"],
            "reason_code": row["reason_code"], "evidence_status": row["evidence_status"],
            "defect_alias": row["defect_alias"], "defect_reference": row["defect_reference"],
        }
        for row in rows if row["scenario_status"] in RUNTIME_ANOMALY_CLASSIFICATIONS
    ]
    blockers = [
        {
            "scenario_id": row["scenario_id"], "scenario_status": row["scenario_status"],
            "reason_code": row["reason_code"], "evidence_status": row["evidence_status"],
        }
        for row in rows if row["scenario_status"] in BLOCKED_STATUSES
    ]
    unresolved = [
        {
            "scenario_id": row["scenario_id"], "scenario_status": row["scenario_status"],
            "reason_code": row["reason_code"], "evidence_status": row["evidence_status"],
        }
        for row in rows if row["scenario_status"] in {"executable_not_run", "mapped_only"}
        or row["evidence_status"] == "unknown"
    ]
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": execution_status,
        "coverage_status": coverage_status,
        "evidence_status": "confirmed" if all_pass else "unknown",
        "release_effect": "candidate_evidence" if all_pass else "blocks_release",
        "production_safety_classification": SAFETY_CLASS,
        "generated_at_utc": adapter["generated_at_utc"],
        "task_id": TASK_ID,
        "build_ref": {"alias": adapter["build_ref"]["alias"]},
        "target_alias": LANE_ALIAS,
        "run_id": adapter["run_id"],
        "artifacts": [
            {"reference": _repo_reference(SCENARIO_LEDGER_OUTPUT), "sha256": _sha(ledger), "kind": "scenario_ledger", "evidence_status": "confirmed"},
            {"reference": _repo_reference(CHECKPOINT_LEDGER_OUTPUT), "sha256": _sha(checkpoints), "kind": "checkpoint_ledger", "evidence_status": "confirmed"},
            {"reference": _repo_reference(ANOMALY_LEDGER_OUTPUT), "sha256": _sha(anomalies), "kind": "anomaly_ledger", "evidence_status": "confirmed"},
        ],
        "blocked_reasons": sorted({item["reason_code"] for item in blockers + unresolved}),
        "unknowns": [
            {"id": f"TASK044-UNKNOWN-{item['scenario_id'][-3:]}", **item}
            for item in unresolved
        ],
        "risks": [{"id": "TASK044-RISK-001", "evidence_status": "confirmed", "summary": "Phone, stale, retry, recovery, blocked, mapped, and cross-family evidence cannot produce PASS."}],
        "verification": [
            {"check": "catalog_selector_reconciliation", "status": "pass", "evidence_status": "confirmed", "result_count": 32},
            {"check": "p0_p1_reconciliation", "status": "pass", "evidence_status": "confirmed", "result_count": "29/3"},
            {"check": "atomic_bundle_validation", "status": "pass", "evidence_status": "confirmed", "result_count": 4},
        ],
        "review": {"qa_reviewer_a": "pending", "qa_reviewer_b": "pending", "security_prod_safety_reviewer": "pending", "docs_scribe": "pending"},
        "provenance": {
            "oracle_schema_version": ORACLE_SCHEMA_VERSION,
            "oracle_schema_validation_status": "pass",
            "scenario_contract_version": SCENARIO_CONTRACT_VERSION,
            "runtime_actions": "not_run" if not any_attempt else "reported_by_local_only_adapter",
            "adapter_input_published": False,
            "preflight_authority": {
                "task_id": "TASK-042",
                "artifacts": [
                    {"kind": "task042_report", "reference": adapter["runtime_preflight"]["authority_report_reference"], "sha256": adapter["runtime_preflight"]["authority_report_sha256"]},
                    {"kind": "device_review", "reference": adapter["runtime_preflight"]["device_review_reference"], "sha256": adapter["runtime_preflight"]["device_review_sha256"]},
                ],
            },
        },
        "payload": {
            "task_status": task_status,
            "scenario_summary": {"total": 32, "P0": 29, "P1": 3, "status_counts": dict(sorted(status_counts.items()))},
            "mandatory_oracles": {"boundary": True, "log_privacy": True, "crash_anr": True, "screenshot_and_ui_tree": True, "dynamic_data_category_only": True},
            "known_anomaly_rechecks": derived["known_anomaly_rows"],
            "runtime_anomalies": derived["runtime_anomaly_rows"],
            "outcome_aggregates": {
                "confirmed_failures": confirmed_failures,
                "blockers": blockers,
                "unknowns": unresolved,
            },
            "phone_never_substitutes_tv": True,
            "runtime_actions_not_run": not any_attempt,
            "product_runtime_coverage_claim": all_pass,
        },
    }
    outputs = {
        REPORT_OUTPUT: _json_bytes(report), SCENARIO_LEDGER_OUTPUT: ledger,
        CHECKPOINT_LEDGER_OUTPUT: checkpoints, ANOMALY_LEDGER_OUTPUT: anomalies,
    }
    validate_bundle(outputs, catalog=catalog)
    return outputs


def validate_report(report: Mapping[str, Any], *, outputs: Mapping[Path, bytes] | None = None) -> None:
    required = {
        "schema_version", "schema_validation_status", "execution_status", "coverage_status",
        "evidence_status", "release_effect", "production_safety_classification",
        "generated_at_utc", "task_id", "build_ref", "target_alias", "run_id",
        "artifacts", "blocked_reasons", "unknowns", "risks", "verification",
        "review", "provenance", "payload",
    }
    _strict_keys(report, required, "REPORT_FIELDS_INVALID")
    if report["schema_version"] != REPORT_SCHEMA_VERSION or report["schema_validation_status"] != "pass":
        raise ContractError("REPORT_SCHEMA_INVALID")
    if report["task_id"] != TASK_ID or report["target_alias"] != LANE_ALIAS:
        raise ContractError("REPORT_IDENTITY_INVALID")
    _utc(report["generated_at_utc"])
    if (
        not isinstance(report["build_ref"], dict)
        or set(report["build_ref"]) != {"alias"}
        or not isinstance(report["build_ref"]["alias"], str)
        or not SAFE_ID_RE.fullmatch(report["build_ref"]["alias"])
        or not isinstance(report["run_id"], str)
        or not SAFE_ID_RE.fullmatch(report["run_id"])
    ):
        raise ContractError("REPORT_PROVENANCE_INVALID")
    if report["execution_status"] not in {"pass", "fail", "blocked", "partial_blocked"}:
        raise ContractError("REPORT_EXECUTION_STATUS_INVALID")
    provenance = report["provenance"]
    expected_authority = {
        "task_id": "TASK-042",
        "artifacts": [
            {"kind": "task042_report", "reference": _repo_reference(TASK042_AUTHORITY), "sha256": _authority_sha256(TASK042_AUTHORITY)},
            {"kind": "device_review", "reference": _repo_reference(DEVICE_REVIEW_AUTHORITY), "sha256": _authority_sha256(DEVICE_REVIEW_AUTHORITY)},
        ],
    }
    if (
        not isinstance(provenance, dict)
        or provenance.get("preflight_authority") != expected_authority
        or provenance.get("oracle_schema_validation_status") != "pass"
        or provenance.get("oracle_schema_version") != ORACLE_SCHEMA_VERSION
    ):
        raise ContractError("REPORT_PREFLIGHT_AUTHORITY_INVALID")
    payload = report["payload"]
    if not isinstance(payload, dict) or payload.get("phone_never_substitutes_tv") is not True:
        raise ContractError("REPORT_LANE_SAFETY_INVALID")
    summary = payload.get("scenario_summary", {})
    if summary.get("total") != 32 or summary.get("P0") != 29 or summary.get("P1") != 3:
        raise ContractError("REPORT_RECONCILIATION_INVALID")
    if payload.get("mandatory_oracles") != {
        "boundary": True, "crash_anr": True, "dynamic_data_category_only": True,
        "log_privacy": True, "screenshot_and_ui_tree": True,
    }:
        raise ContractError("REPORT_MANDATORY_ORACLES_INVALID")
    if (
        not isinstance(payload.get("known_anomaly_rechecks"), list)
        or len(payload["known_anomaly_rechecks"]) != 3
        or not isinstance(payload.get("runtime_anomalies"), list)
        or not isinstance(payload.get("outcome_aggregates"), dict)
        or set(payload["outcome_aggregates"]) != {"confirmed_failures", "blockers", "unknowns"}
    ):
        raise ContractError("REPORT_OUTCOME_AGGREGATES_INVALID")
    if report["execution_status"] == "pass":
        if (
            payload.get("task_status") != "completed"
            or summary.get("status_counts") != {"observed_pass": 32}
            or payload.get("product_runtime_coverage_claim") is not True
            or payload.get("runtime_actions_not_run") is not False
            or report["evidence_status"] != "confirmed"
        ):
            raise ContractError("REPORT_FALSE_PASS")
    artifacts = report["artifacts"]
    expected = {SCENARIO_LEDGER_OUTPUT, CHECKPOINT_LEDGER_OUTPUT, ANOMALY_LEDGER_OUTPUT}
    if not isinstance(artifacts, list) or len(artifacts) != 3:
        raise ContractError("REPORT_ARTIFACTS_INVALID")
    seen: set[Path] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ContractError("REPORT_ARTIFACT_INVALID")
        _strict_keys(artifact, {"reference", "sha256", "kind", "evidence_status"}, "REPORT_ARTIFACT_FIELDS_INVALID")
        if artifact["evidence_status"] != "confirmed":
            raise ContractError("REPORT_ARTIFACT_EVIDENCE_INVALID")
        try:
            path = REPO_ROOT / PurePosixPath(artifact["reference"])
        except TypeError:
            raise ContractError("REPORT_ARTIFACT_REFERENCE_INVALID") from None
        if path not in expected or path in seen or not HASH_RE.fullmatch(str(artifact["sha256"])):
            raise ContractError("REPORT_ARTIFACT_REFERENCE_INVALID")
        seen.add(path)
        content = outputs[path] if outputs is not None and path in outputs else _fixed_file(path, suffix=path.suffix).read_bytes()
        if _sha(content) != artifact["sha256"]:
            raise ContractError("REPORT_ARTIFACT_HASH_MISMATCH")
    if seen != expected:
        raise ContractError("REPORT_ARTIFACT_SET_INVALID")
    _safe_public_value(report)


def validate_bundle(outputs: Mapping[Path, bytes], *, catalog: Sequence[Mapping[str, str]] | None = None) -> None:
    expected = {REPORT_OUTPUT, SCENARIO_LEDGER_OUTPUT, CHECKPOINT_LEDGER_OUTPUT, ANOMALY_LEDGER_OUTPUT}
    if set(outputs) != expected:
        raise ContractError("BUNDLE_OUTPUT_SET_INVALID")
    try:
        report = json.loads(outputs[REPORT_OUTPUT], object_pairs_hook=_json_pairs)
    except (UnicodeError, json.JSONDecodeError):
        raise ContractError("REPORT_JSON_INVALID") from None
    validate_report(report, outputs=outputs)
    def read_rows(path: Path, headers: Sequence[str]) -> list[dict[str, str]]:
        try:
            reader = csv.DictReader(io.StringIO(outputs[path].decode("utf-8")))
        except UnicodeError:
            raise ContractError("BUNDLE_LEDGER_ENCODING_INVALID") from None
        if tuple(reader.fieldnames or ()) != tuple(headers):
            raise ContractError("BUNDLE_LEDGER_HEADERS_INVALID")
        result = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in result):
            raise ContractError("BUNDLE_LEDGER_ROWS_INVALID")
        return result

    rows = read_rows(SCENARIO_LEDGER_OUTPUT, SCENARIO_LEDGER_HEADERS)
    checkpoints = read_rows(CHECKPOINT_LEDGER_OUTPUT, CHECKPOINT_LEDGER_HEADERS)
    anomaly_rows = read_rows(ANOMALY_LEDGER_OUTPUT, ANOMALY_LEDGER_HEADERS)
    if len(rows) != 32 or len(anomaly_rows) < 3:
        raise ContractError("BUNDLE_LEDGER_COUNT_INVALID")
    contract = list(catalog) if catalog is not None else load_contract()
    ids = [row["scenario_id"] for row in contract]
    if [row["scenario_id"] for row in rows] != ids:
        raise ContractError("BUNDLE_LEDGER_SCENARIO_SET_INVALID")
    for actual, expected in zip(rows, contract, strict=True):
        if (
            actual["priority"] != expected["priority"]
            or actual["surface_ids"] != expected["surface_ids"]
            or actual["category"] != expected["category"]
            or actual["scenario_status"] not in SCENARIO_STATUSES
            or actual["evidence_type"] not in EVIDENCE_TYPES
            or actual["evidence_status"] not in EVIDENCE_STATUSES
            or (
                actual["scenario_status"] == "confirmed_defect"
                and (actual["defect_alias"] == "none" or not actual["defect_reference"].startswith("docs/qa/defects/task044_"))
            )
            or (
                actual["scenario_status"] != "confirmed_defect"
                and (actual["defect_alias"] != "none" or actual["defect_reference"] != "none")
            )
        ):
            raise ContractError("BUNDLE_LEDGER_CONTRACT_MISMATCH")
    status_counts = Counter(row["scenario_status"] for row in rows)
    if report["payload"]["scenario_summary"]["status_counts"] != dict(sorted(status_counts.items())):
        raise ContractError("BUNDLE_REPORT_LEDGER_MISMATCH")
    try:
        has_attempt = any(int(row["attempt_count"]) > 0 for row in rows)
        expected_checkpoint_count = sum(int(row["attempt_count"]) for row in rows)
    except ValueError:
        raise ContractError("BUNDLE_ATTEMPT_COUNT_INVALID") from None
    if len(checkpoints) != expected_checkpoint_count:
        raise ContractError("BUNDLE_CHECKPOINT_COUNT_INVALID")
    checkpoint_counts = Counter(row["scenario_id"] for row in checkpoints)
    for row in rows:
        if checkpoint_counts[row["scenario_id"]] != int(row["attempt_count"]):
            raise ContractError("BUNDLE_CHECKPOINT_SCENARIO_COUNT_INVALID")
    for scenario_id, scenario_checkpoints in {
        scenario_id: [row for row in checkpoints if row["scenario_id"] == scenario_id]
        for scenario_id in ids
    }.items():
        for index, checkpoint in enumerate(scenario_checkpoints, start=1):
            if checkpoint["attempt_index"] != str(index):
                raise ContractError("BUNDLE_CHECKPOINT_INDEX_INVALID")
            if checkpoint["recovery_attempt"] == "false" and checkpoint["recovery_of_attempt_id"] != "none":
                raise ContractError("BUNDLE_CHECKPOINT_RECOVERY_RELATION_INVALID")
    has_failure = any(row["scenario_status"] in {"observed_fail", "confirmed_defect", "tooling_defect"} for row in rows)
    known_ledger_rows = [row for row in anomaly_rows if row["record_type"] == "known_recheck"]
    runtime_ledger_rows = [row for row in anomaly_rows if row["record_type"] == "runtime_anomaly"]
    if len(known_ledger_rows) != 3 or len(runtime_ledger_rows) != len(report["payload"]["runtime_anomalies"]):
        raise ContractError("BUNDLE_ANOMALY_LEDGER_COUNT_INVALID")
    anomaly_closed = all(
        row["classification"] == "resolved" and row["evidence_status"] == "confirmed"
        for row in known_ledger_rows
    )
    scenario_all_pass = status_counts == Counter({"observed_pass": 32})
    expected_execution = "pass" if scenario_all_pass and anomaly_closed else ("fail" if has_failure else ("partial_blocked" if has_attempt else "blocked"))
    if report["execution_status"] != expected_execution:
        raise ContractError("BUNDLE_EXECUTION_STATUS_MISMATCH")
    expected_task_status = "completed" if expected_execution == "pass" else ("failed" if expected_execution == "fail" else ("partial" if has_attempt else "blocked"))
    if report["payload"].get("task_status") != expected_task_status:
        raise ContractError("BUNDLE_TASK_STATUS_MISMATCH")
    public_known_anomalies = [
        {
            "anomaly_alias": row["anomaly_alias"], "category": row["category"],
            "classification": row["classification"], "evidence_status": row["evidence_status"],
            "scenario_id": row["scenario_id"],
            "trigger_category": row["trigger_category"],
            "expected_result_category": row["expected_result_category"],
            "observed_result_category": row["observed_result_category"],
            "public_safe_screen_alias": row["public_safe_screen_alias"],
            "cause_evidence_status": row["cause_evidence_status"],
            "cause_category": row["cause_category"],
            "test_design_implication": row["test_design_implication"],
            "first_failure_retained": row["first_failure_retained"] == "true",
            "reason_code": row["reason_code"],
        }
        for row in known_ledger_rows
    ]
    public_runtime_anomalies = [
        {
            "anomaly_id": row["anomaly_id"], "anomaly_alias": row["anomaly_alias"],
            "category": row["category"], "classification": row["classification"],
            "evidence_status": row["evidence_status"], "scenario_id": row["scenario_id"],
            "attempt_id": row["attempt_id"], "trigger_category": row["trigger_category"],
            "expected_result_category": row["expected_result_category"],
            "observed_result_category": row["observed_result_category"],
            "public_safe_screen_alias": row["public_safe_screen_alias"],
            "cause_evidence_status": row["cause_evidence_status"],
            "cause_category": row["cause_category"],
            "test_design_implication": row["test_design_implication"],
            "first_failure_retained": row["first_failure_retained"] == "true",
            "reason_code": row["reason_code"],
        }
        for row in runtime_ledger_rows
    ]
    if report["payload"]["known_anomaly_rechecks"] != public_known_anomalies:
        raise ContractError("BUNDLE_ANOMALY_LEDGER_MISMATCH")
    if report["payload"]["runtime_anomalies"] != public_runtime_anomalies:
        raise ContractError("BUNDLE_RUNTIME_ANOMALY_LEDGER_MISMATCH")
    expected_failures = [
        {"scenario_id": row["scenario_id"], "scenario_status": row["scenario_status"], "reason_code": row["reason_code"], "evidence_status": row["evidence_status"], "defect_alias": row["defect_alias"], "defect_reference": row["defect_reference"]}
        for row in rows if row["scenario_status"] in RUNTIME_ANOMALY_CLASSIFICATIONS
    ]
    expected_blockers = [
        {"scenario_id": row["scenario_id"], "scenario_status": row["scenario_status"], "reason_code": row["reason_code"], "evidence_status": row["evidence_status"]}
        for row in rows if row["scenario_status"] in BLOCKED_STATUSES
    ]
    expected_unknowns = [
        {"scenario_id": row["scenario_id"], "scenario_status": row["scenario_status"], "reason_code": row["reason_code"], "evidence_status": row["evidence_status"]}
        for row in rows if row["scenario_status"] in {"executable_not_run", "mapped_only"} or row["evidence_status"] == "unknown"
    ]
    if report["payload"]["outcome_aggregates"] != {
        "confirmed_failures": expected_failures, "blockers": expected_blockers,
        "unknowns": expected_unknowns,
    }:
        raise ContractError("BUNDLE_OUTCOME_AGGREGATES_MISMATCH")
    if report["blocked_reasons"] != sorted({item["reason_code"] for item in expected_blockers + expected_unknowns}):
        raise ContractError("BUNDLE_BLOCKED_REASONS_MISMATCH")
    if report["execution_status"] == "pass" and any(
        row["scenario_status"] != "observed_pass"
        or row["evidence_type"] != "physical_runtime"
        or row["evidence_status"] != "confirmed"
        or row["fresh_visual_pair"] != "true"
        or row["retry_or_recovery_seen"] != "false"
        for row in rows
    ):
        raise ContractError("BUNDLE_FALSE_PASS")
    if report["execution_status"] == "pass" and any(
        row["screenshot_present"] != "true"
        or row["ui_tree_present"] != "true"
        or row["visual_inspection_present"] != "true"
        or row["freshness_status"] != "fresh"
        for row in checkpoints
    ):
        raise ContractError("BUNDLE_CHECKPOINT_FALSE_PASS")


def _atomic_publish(outputs: Mapping[Path, bytes]) -> None:
    allowed = {REPORT_OUTPUT, SCENARIO_LEDGER_OUTPUT, CHECKPOINT_LEDGER_OUTPUT, ANOMALY_LEDGER_OUTPUT}
    if set(outputs) != allowed:
        raise ContractError("OUTPUT_NOT_ALLOWLISTED")
    staged: list[tuple[Path, Path]] = []
    backups: dict[Path, Path | None] = {}
    published: list[Path] = []
    preserved: set[Path] = set()
    try:
        for target, content in outputs.items():
            target.parent.mkdir(parents=False, exist_ok=True)
            descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.task044.", suffix=".tmp", dir=target.parent)
            temp = Path(name)
            staged.append((temp, target))
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        for _, target in staged:
            if target.exists():
                descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.task044.backup.", suffix=".tmp", dir=target.parent)
                backup = Path(name)
                backups[target] = backup
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(target.read_bytes())
                    handle.flush()
                    os.fsync(handle.fileno())
            else:
                backups[target] = None
        for temp, target in staged:
            os.replace(temp, target)
            published.append(target)
    except ContractError:
        raise
    except OSError:
        rollback_failed = False
        for target in reversed(published):
            backup = backups.get(target)
            try:
                if backup is None:
                    target.unlink(missing_ok=True)
                else:
                    os.replace(backup, target)
                    backups[target] = None
            except OSError:
                rollback_failed = True
                if backup is not None:
                    preserved.add(backup)
        if rollback_failed:
            raise ContractError("OUTPUT_ROLLBACK_FAILED", recovery_status="local_backup_preserved") from None
        raise ContractError("OUTPUT_ATOMIC_PUBLISH_FAILED") from None
    finally:
        for temp, _ in staged:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
        for backup in backups.values():
            try:
                if backup is not None and backup not in preserved:
                    backup.unlink(missing_ok=True)
            except OSError:
                pass


def publish_bundle(outputs: Mapping[Path, bytes], *, catalog: Sequence[Mapping[str, str]]) -> None:
    validate_bundle(outputs, catalog=catalog)
    _atomic_publish(outputs)
    actual = {path: path.read_bytes() for path in outputs}
    if actual != dict(outputs):
        raise ContractError("PUBLISHED_BUNDLE_MISMATCH")
    validate_bundle(actual, catalog=catalog)


def _emit(value: Mapping[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TASK-044 fail-closed local-only runtime evidence adapter")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true", help="Validate immutable constants; no file, process, network, or device access.")
    modes.add_argument("--preflight", action="store_true", help="Validate tracked contracts and typed local-only adapter; no writes or device actions.")
    modes.add_argument("--execute", action="store_true", help="Ingest an approved typed local-only adapter and atomically publish the public-safe bundle.")
    modes.add_argument("--validate-report", action="store_true", help="Validate the fixed tracked public-safe bundle; no writes or device actions.")
    parser.add_argument("--adapter-input", type=Path, help="Ignored local-only JSON adapter result; its path and raw contents are never published.")
    parser.add_argument("--allow-prod-conditional-ingest", action="store_true", help="Required explicit gate for --execute; permits ingest only, not device control.")
    args = parser.parse_args(argv)
    try:
        if args.validate_only:
            if args.adapter_input is not None or args.allow_prod_conditional_ingest:
                raise ContractError("VALIDATE_ONLY_EXTRA_FLAG_FORBIDDEN")
            errors = validate_static_constants()
            if errors:
                raise ContractError(errors[0])
            result = {"task_id": TASK_ID, "mode": "validate_only", "validation_status": "pass", "runtime_actions": "not_run", "file_io": "not_run", "subprocesses": "not_run"}
        elif args.validate_report:
            if args.adapter_input is not None or args.allow_prod_conditional_ingest:
                raise ContractError("VALIDATE_REPORT_EXTRA_FLAG_FORBIDDEN")
            catalog = load_contract()
            outputs = {path: _fixed_file(path, suffix=path.suffix).read_bytes() for path in (REPORT_OUTPUT, SCENARIO_LEDGER_OUTPUT, CHECKPOINT_LEDGER_OUTPUT, ANOMALY_LEDGER_OUTPUT)}
            validate_bundle(outputs, catalog=catalog)
            result = {"task_id": TASK_ID, "mode": "validate_report", "validation_status": "pass", "runtime_actions": "not_run"}
        else:
            if args.adapter_input is None:
                raise ContractError("ADAPTER_INPUT_REQUIRED")
            catalog = load_contract()
            adapter = _load_adapter(args.adapter_input)
            outputs = build_bundle(adapter, catalog)
            if args.preflight:
                if args.allow_prod_conditional_ingest:
                    raise ContractError("PREFLIGHT_EXECUTION_FLAG_FORBIDDEN")
                result = {"task_id": TASK_ID, "mode": "preflight", "validation_status": "pass", "scenario_count": 32, "p0_count": 29, "p1_count": 3, "runtime_actions": "not_run", "writes": "not_run", "phone_never_substitutes_tv": True}
            else:
                if not args.allow_prod_conditional_ingest:
                    raise ContractError("PROD_CONDITIONAL_INGEST_GATE_REQUIRED")
                publish_bundle(outputs, catalog=catalog)
                report = json.loads(outputs[REPORT_OUTPUT])
                result = {"task_id": TASK_ID, "mode": "execute", "validation_status": "pass", "execution_status": report["execution_status"], "runtime_actions": "reported_by_local_only_adapter", "device_commands": "not_run", "phone_never_substitutes_tv": True}
        _emit(result)
        return 0
    except ContractError as exc:
        result: dict[str, Any] = {"task_id": TASK_ID, "validation_status": "blocked", "reason_code": str(exc), "runtime_actions": "not_run"}
        if exc.recovery_status:
            result["recovery_status"] = exc.recovery_status
        _emit(result)
        return 1
    except Exception:
        _emit({
            "task_id": TASK_ID, "validation_status": "blocked",
            "reason_code": "INTERNAL_VALIDATION_ERROR", "runtime_actions": "not_run",
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

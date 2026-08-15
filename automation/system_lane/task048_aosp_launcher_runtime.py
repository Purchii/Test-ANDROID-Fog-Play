"""TASK-048 repository-only AOSP/launcher system-lane authority.

This module deliberately has no Android runtime implementation.  The current
Security decision is ``GO_REPOSITORY_ONLY / BLOCK_RUNTIME`` and the exact
FogPlay Stick approved mapping is absent and physical availability remains
unknown in authoritative tracked dependency evidence.  All CLI modes read
tracked public-safe contracts only; no mode reads ``.qa_local``,
starts a subprocess, contacts ADB, reads an APK, or controls a device.
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
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from automation.reporting.generate_report_manifest import _validate_v2_envelope
except ModuleNotFoundError:  # Direct ``python automation/...py`` execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from automation.reporting.generate_report_manifest import _validate_v2_envelope


TASK_ID = "TASK-048"
REPORT_SCHEMA_VERSION = "evidence-report-envelope-v2"
PRODUCTION_SAFETY = "PROD_SAFE_REPOSITORY_ONLY_BLOCKED_RUNTIME"
SECURITY_DECISION = "GO_REPOSITORY_ONLY_BLOCK_RUNTIME"
RUN_ID = "task048-repository-only-blocked-runtime-001"
GENERATED_AT = "2026-08-15T00:00:00Z"

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = REPO_ROOT / "docs/qa/epics/scenarios/task048_scenarios.csv"
TASK_SPEC = REPO_ROOT / "tasks/TASK_048_aosp_launcher_system_cluster_runtime.md"
STATUS_CONTRACT = REPO_ROOT / "docs/qa/epics/task041_055_status_evidence_contract.md"
DEPENDENCY_MAP = REPO_ROOT / "docs/qa/epics/task041_055_dependency_map.md"
APK_CONTRACT = REPO_ROOT / "docs/approvals/task005_apk_bundle_contract.md"
PUBLIC_DEVICE_INVENTORY = REPO_ROOT / "docs/approvals/device_inventory.public_safe.review.json"
TASK042_REPORT = REPO_ROOT / "docs/qa/reports/task042_local_runtime_preflight.summary.json"
REPORT_SCHEMA = REPO_ROOT / "docs/qa/schemas/evidence-report-envelope-v2.schema.json"

REPORT_OUTPUT = REPO_ROOT / "docs/qa/reports/task048_aosp_launcher_runtime.summary.json"
SCENARIO_OUTPUT = REPO_ROOT / "docs/qa/reports/task048_aosp_launcher_runtime.scenario-ledger.csv"
AUTHORITY_OUTPUT = REPO_ROOT / "docs/qa/reports/task048_aosp_launcher_runtime.authority-ledger.csv"

EXPECTED_IDS = tuple(f"QA-048-{index:03d}" for index in range(1, 20))
EXPECTED_HEADERS = (
    "scenario_id",
    "priority",
    "surface_ids",
    "lane",
    "category",
    "title",
    "preconditions",
    "steps",
    "expected_oracle",
    "negative_or_boundary",
    "automation_target",
    "evidence_required",
    "safety_class",
    "blocking_rule",
)
TERMINAL_STATUSES = {
    "observed_pass",
    "observed_fail",
    "confirmed_defect",
    "tooling_defect",
    "executable_not_run",
    "blocked_by_device",
    "blocked_by_fixture",
    "blocked_by_oracle",
    "blocked_by_product_boundary",
    "blocked_by_external_state",
    "not_applicable",
    "mapped_only",
}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}

SCENARIO_HEADERS = (
    "scenario_id",
    "priority",
    "surface_ids",
    "lane",
    "category",
    "scenario_status",
    "evidence_type",
    "evidence_status",
    "primary_blocker",
    "secondary_blockers",
    "justification",
    "runtime_executed",
    "product_coverage_counted",
)
AUTHORITY_HEADERS = (
    "authority_id",
    "authority_kind",
    "static_state",
    "scenario_status",
    "evidence_status",
    "claim_scope",
    "main_five_apk_member",
    "launcher_contour_separate",
    "generic_substitution_allowed",
    "reason_code",
)

FORBIDDEN_PUBLIC_KEYS = {
    "absolute_path",
    "account",
    "adb_serial",
    "android_id",
    "endpoint",
    "full_build_fingerprint",
    "imei",
    "ip",
    "mac",
    "package_id",
    "raw_hash",
    "raw_path",
    "raw_serial",
    "token",
}
FORBIDDEN_PUBLIC_PATTERNS = (
    re.compile(r"(?i)(?:^|[\s\"'])[a-z]:[\\/]"),
    re.compile(r"\\\\[^\\\s]+\\"),
    re.compile(r"(?i)(?:^|[\s\"'])/(?!/)[^\s,;]+"),
    re.compile(r"(?i)\b(?:https?|wss?|file|intent|market|mailto):"),
    re.compile(r"(?<![\w-])(?:\d{1,3}\.){3}\d{1,3}(?![\w-])"),
    re.compile(r"(?i)(?<![\w:])(?:[0-9a-f]{0,4}:){2,}[0-9a-f:]{0,4}(?![\w:])"),
    re.compile(r"(?i)(?:^|[\\/])\.qa_local(?:[\\/]|$)"),
    re.compile(r"(?i)\b(?:[a-z][a-z0-9_]*\.)+[a-z][a-z0-9_]*(?:/[.a-z][a-z0-9_.$]*)"),
    re.compile(r"(?i)\b(?:sha(?:1|224|256|384|512)|md5):[0-9a-f]{16,}\b"),
)
HASH_LIKE_RE = re.compile(r"^[0-9a-fA-F]{32,}$")
PACKAGE_LIKE_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9_]*\.)+[A-Za-z][A-Za-z0-9_]*$")


class ContractError(ValueError):
    """A stable public-safe contract failed closed."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ContractError(f"duplicate_json_key:{key}")
        value[key] = child
    return value


def _json_loads(value: str | bytes) -> Any:
    try:
        return json.loads(value, object_pairs_hook=_reject_duplicate_json_keys)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ContractError("json_invalid") from exc


def _is_reparse(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return True
    return path.is_symlink() or bool(attributes & 0x400)


def _read_fixed_text(path: Path) -> str:
    if not path.is_file() or _is_reparse(path):
        raise ContractError(f"tracked_contract_missing_or_not_regular:{path.name}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ContractError(f"tracked_contract_read_failed:{path.name}") from exc


def _read_fixed_json(path: Path) -> dict[str, Any]:
    try:
        value = _json_loads(_read_fixed_text(path))
    except json.JSONDecodeError as exc:
        raise ContractError(f"tracked_json_invalid:{path.name}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"tracked_json_not_object:{path.name}")
    return value


def load_catalog() -> list[dict[str, str]]:
    text = _read_fixed_text(CATALOG)
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != EXPECTED_HEADERS:
        raise ContractError("scenario_catalog_headers_drift")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ContractError("scenario_catalog_extra_cells")
    if [row["scenario_id"] for row in rows] != list(EXPECTED_IDS):
        raise ContractError("scenario_catalog_requires_exact_qa048_001_through_019")
    if sum(row["priority"] == "P0" for row in rows) != 15 or sum(row["priority"] == "P1" for row in rows) != 4:
        raise ContractError("scenario_catalog_priority_count_drift")
    for row in rows:
        if row["lane"] != "FogPlay Stick":
            raise ContractError(f"cross_family_lane_rejected:{row['scenario_id']}")
        if row["automation_target"] != "automate":
            raise ContractError(f"scenario_automation_target_drift:{row['scenario_id']}")
        if row["safety_class"] != "PROD_CONDITIONAL":
            raise ContractError(f"scenario_safety_class_drift:{row['scenario_id']}")
        if row["blocking_rule"] != "classify; continue independent scenarios":
            raise ContractError(f"scenario_blocking_rule_drift:{row['scenario_id']}")
        if row["negative_or_boundary"] not in {"yes", "no"}:
            raise ContractError(f"scenario_boundary_flag_invalid:{row['scenario_id']}")
    if rows[13]["scenario_id"] != "QA-048-014" or rows[13]["negative_or_boundary"] != "yes":
        raise ContractError("qa048_014_boundary_contract_drift")
    return rows


def validate_static_contracts() -> dict[str, Any]:
    """Validate tracked inputs only and prove why runtime stays blocked."""

    catalog = load_catalog()
    task_text = _read_fixed_text(TASK_SPEC)
    status_text = _read_fixed_text(STATUS_CONTRACT)
    dependency_text = _read_fixed_text(DEPENDENCY_MAP)
    apk_text = _read_fixed_text(APK_CONTRACT)
    schema = _read_fixed_json(REPORT_SCHEMA)
    inventory = _read_fixed_json(PUBLIC_DEVICE_INVENTORY)
    task042_report = _read_fixed_json(TASK042_REPORT)

    required_task_phrases = (
        "qa/task-048-aosp-launcher-system-cluster-runtime",
        "blocked_by_device",
        "launcher cluster remains separate from main five-APK contract",
    )
    if any(phrase not in task_text for phrase in required_task_phrases):
        raise ContractError("task_spec_required_boundary_drift")
    if "blocked_by_device" not in status_text or "observed_pass" not in status_text:
        raise ContractError("status_evidence_contract_drift")
    if "target отсутствует" not in dependency_text or "продолжить TASK-049" not in dependency_text:
        raise ContractError("task048_optional_lane_dependency_rule_drift")

    expected_apk_names = re.findall(r"`(fogplay-tv-[^`]+\.apk)`", apk_text)
    if len(expected_apk_names) != 5 or len(set(expected_apk_names)) != 5:
        raise ContractError("main_five_apk_contract_drift")
    if "fogplay-tv-aosp-full-production-release.apk" not in expected_apk_names:
        raise ContractError("aosp_full_contract_entry_missing")
    if "launcher" in " ".join(expected_apk_names).casefold():
        raise ContractError("launcher_contour_must_not_join_main_five_apk_contract")

    devices = inventory.get("devices")
    if not isinstance(devices, list) or not devices:
        raise ContractError("public_device_inventory_empty_or_invalid")
    aliases: list[str] = []
    for item in devices:
        if not isinstance(item, dict) or not isinstance(item.get("device_alias"), str):
            raise ContractError("public_device_inventory_alias_invalid")
        aliases.append(item["device_alias"])
    if len(aliases) != len(set(aliases)):
        raise ContractError("public_device_inventory_alias_duplicate")
    task042_payload = task042_report.get("payload")
    stick_authority = task042_payload.get("fogplay_stick_actual_target") if isinstance(task042_payload, dict) else None
    required_stick_authority = {
        "actual_alias_status": "unknown",
        "blocker": "actual_stick_mapping_missing",
        "current_status": "MISSING",
        "evidence_status": "unknown",
        "generic_substitution_allowed": False,
        "scenario_status": "blocked_by_device",
        "selected_device_alias": None,
        "selector_key": "fogplay_stick_actual_target",
    }
    if stick_authority != required_stick_authority:
        raise ContractError("task042_stick_authority_changed_requires_fresh_security_review")

    required_schema_fields = set(schema.get("required", []))
    if schema.get("title") != "Evidence Report Envelope v2" or "task_id" not in required_schema_fields:
        raise ContractError("evidence_report_envelope_v2_contract_drift")

    return {
        "scenario_count": len(catalog),
        "p0_count": sum(row["priority"] == "P0" for row in catalog),
        "p1_count": sum(row["priority"] == "P1" for row in catalog),
        "tracked_device_count": len(aliases),
        "approved_stick_mapping_state": "missing",
        "physical_stick_availability": "unknown",
        "runtime_gate": "BLOCK_RUNTIME",
    }


def _scenario_classification(scenario_id: str) -> tuple[str, str, str, str, str]:
    if scenario_id == "QA-048-014":
        return (
            "blocked_by_product_boundary",
            "unknown",
            "approved_public_component_contract_missing",
            "actual_stick_mapping_missing",
            "No approved public-safe component contract exists; unauthorized or malformed invocation was not attempted.",
        )
    if scenario_id == "QA-048-019":
        return (
            "observed_pass",
            "confirmed",
            "",
            "runtime_lane_remains_blocked",
            "The repository-only authority terminally reconciles all 19 rows; this is static closure only and grants no product or release PASS.",
        )
    secondary = {
        "QA-048-001": "authoritative_target_mapping_missing",
        "QA-048-002": "launcher_component_mapping_missing",
        "QA-048-003": "aosp_artifact_not_inspected_repository_only",
        "QA-048-004": "reboot_not_authorized_without_exact_target",
        "QA-048-005": "home_ownership_not_observed",
        "QA-048-006": "launcher_focus_not_observed",
        "QA-048-007": "launcher_windows_not_observed",
        "QA-048-008": "aosp_launcher_transition_not_observed",
        "QA-048-009": "launcher_return_transition_not_observed",
        "QA-048-010": "process_recovery_not_authorized_without_exact_target",
        "QA-048-011": "setup_fixture_and_safe_route_not_verified",
        "QA-048-012": "setup_reentry_not_observed",
        "QA-048-013": "launcher_service_mapping_missing",
        "QA-048-015": "ambient_wake_recovery_not_observed",
        "QA-048-016": "service_restart_not_authorized_without_exact_target",
        "QA-048-017": "runtime_log_evidence_absent",
        "QA-048-018": "crash_anr_signal_evidence_absent",
    }[scenario_id]
    return (
        "blocked_by_device",
        "unknown",
        "actual_stick_mapping_missing",
        secondary,
        "The approved exact FogPlay Stick mapping is absent and physical availability remains unknown; no generic TV, phone, AVD, historical profile, plan, or static artifact substitutes for runtime evidence.",
    )


def build_scenario_rows(catalog: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in catalog:
        status, evidence, primary, secondary, justification = _scenario_classification(source["scenario_id"])
        rows.append(
            {
                "scenario_id": source["scenario_id"],
                "priority": source["priority"],
                "surface_ids": source["surface_ids"],
                "lane": source["lane"],
                "category": source["category"],
                "scenario_status": status,
                "evidence_type": "static_contract",
                "evidence_status": evidence,
                "primary_blocker": primary,
                "secondary_blockers": secondary,
                "justification": justification,
                "runtime_executed": "false",
                "product_coverage_counted": "false",
            }
        )
    return rows


def build_authority_rows() -> list[dict[str, str]]:
    return [
        {
            "authority_id": "task048-actual-stick-target",
            "authority_kind": "physical_target",
            "static_state": "approved_mapping_missing_physical_state_unknown",
            "scenario_status": "blocked_by_device",
            "evidence_status": "confirmed",
            "claim_scope": "approved_mapping_absence_only",
            "main_five_apk_member": "false",
            "launcher_contour_separate": "true",
            "generic_substitution_allowed": "false",
            "reason_code": "actual_stick_mapping_missing",
        },
        {
            "authority_id": "task048-aosp-full-artifact",
            "authority_kind": "apk_contract_entry",
            "static_state": "contract_declared_not_inspected",
            "scenario_status": "blocked_by_device",
            "evidence_status": "unknown",
            "claim_scope": "tracked_bundle_shape_only",
            "main_five_apk_member": "true",
            "launcher_contour_separate": "true",
            "generic_substitution_allowed": "false",
            "reason_code": "repository_only_no_apk_read",
        },
        {
            "authority_id": "task048-launcher-system-cluster",
            "authority_kind": "launcher_contour",
            "static_state": "mapping_missing",
            "scenario_status": "blocked_by_fixture",
            "evidence_status": "unknown",
            "claim_scope": "separate_system_cluster",
            "main_five_apk_member": "false",
            "launcher_contour_separate": "true",
            "generic_substitution_allowed": "false",
            "reason_code": "launcher_component_mapping_missing",
        },
        {
            "authority_id": "task048-component-boundary",
            "authority_kind": "security_boundary",
            "static_state": "invocation_forbidden",
            "scenario_status": "blocked_by_product_boundary",
            "evidence_status": "confirmed",
            "claim_scope": "qa048_014_static_guard",
            "main_five_apk_member": "false",
            "launcher_contour_separate": "true",
            "generic_substitution_allowed": "false",
            "reason_code": "approved_public_component_contract_missing",
        },
        {
            "authority_id": "task048-terminal-ledger",
            "authority_kind": "repository_closure",
            "static_state": "terminal_19_of_19",
            "scenario_status": "observed_pass",
            "evidence_status": "confirmed",
            "claim_scope": "static_reconciliation_only",
            "main_five_apk_member": "false",
            "launcher_contour_separate": "true",
            "generic_substitution_allowed": "false",
            "reason_code": "no_product_or_release_pass",
        },
    ]


def _csv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(headers), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _repo_ref(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _validate_public_value(value: Any, *, key: str = "") -> None:
    if key.casefold() in FORBIDDEN_PUBLIC_KEYS:
        raise ContractError(f"forbidden_public_key:{key}")
    if isinstance(value, dict):
        for child_key, child in value.items():
            _validate_public_value(child, key=str(child_key))
    elif isinstance(value, list):
        for child in value:
            _validate_public_value(child, key=key)
    elif isinstance(value, str) and key != "sha256":
        if any(pattern.search(value) for pattern in FORBIDDEN_PUBLIC_PATTERNS):
            raise ContractError(f"unsafe_public_value:{key}")
        if HASH_LIKE_RE.fullmatch(value) or PACKAGE_LIKE_RE.fullmatch(value):
            raise ContractError(f"unsafe_public_identifier:{key}")


def _report(scenario_bytes: bytes, authority_bytes: bytes) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": "blocked",
        "coverage_status": "blocked",
        "evidence_status": "confirmed",
        "release_effect": "blocks_release",
        "production_safety_classification": PRODUCTION_SAFETY,
        "generated_at_utc": GENERATED_AT,
        "task_id": TASK_ID,
        "build_ref": {"alias": "task048-aosp-launcher-static-authority"},
        "target_alias": "fogplay-stick-required-target",
        "run_id": RUN_ID,
        "artifacts": [
            {
                "kind": "scenario_ledger",
                "reference": _repo_ref(SCENARIO_OUTPUT),
                "sha256": _sha256(scenario_bytes),
                "evidence_status": "confirmed",
            },
            {
                "kind": "authority_ledger",
                "reference": _repo_ref(AUTHORITY_OUTPUT),
                "sha256": _sha256(authority_bytes),
                "evidence_status": "confirmed",
            },
        ],
        "blocked_reasons": [
            "actual_stick_mapping_missing",
            "aosp_artifact_not_inspected_repository_only",
            "launcher_component_mapping_missing",
            "runtime_fixture_not_verified",
            "security_runtime_gate_blocked",
        ],
        "unknowns": [
            {
                "id": "TASK048-UNKNOWN-AOSP-COMPATIBILITY",
                "evidence_status": "unknown",
                "reason_code": "actual_build_target_compatibility_not_verified",
            },
            {
                "id": "TASK048-UNKNOWN-LAUNCHER-MAPPING",
                "evidence_status": "unknown",
                "reason_code": "launcher_component_mapping_missing",
            },
        ],
        "risks": [
            {
                "id": "TASK048-RISK-FALSE-PASS",
                "evidence_status": "confirmed",
                "summary": "Static contracts, generic devices, phones, AVDs, historical profiles, and blocked rows cannot establish AOSP or launcher product coverage.",
            },
            {
                "id": "TASK048-RISK-UNAUTHORIZED-IPC",
                "evidence_status": "confirmed",
                "summary": "QA-048-014 remains at the product-safety boundary because no approved public component contract exists.",
            },
        ],
        "verification": [
            {"check": "tracked_contract_validation", "status": "pass", "evidence_status": "confirmed"},
            {"check": "scenario_terminal_reconciliation", "status": "pass", "evidence_status": "confirmed", "result_count": 19},
            {"check": "physical_runtime", "status": "blocked", "evidence_status": "unknown", "result_count": 0},
            {"check": "product_coverage", "status": "blocked", "evidence_status": "unknown", "result_count": 0},
        ],
        "review": {
            "security_prod_safety_reviewer": "go_repository_only_block_runtime",
            "qa_reviewer_a": "pending_independent_review",
            "qa_reviewer_b": "pending_independent_review",
            "docs_scribe": "pending_independent_review",
        },
        "provenance": {
            "source": "tracked_public_safe_contracts_only",
            "local_only_input_read": False,
            "apk_read": False,
            "adb_or_device_action": False,
            "runtime_evidence_published": False,
            "scenario_contract": "docs/qa/epics/scenarios/task048_scenarios.csv",
        },
        "payload": {
            "runtime_gate": "BLOCK_RUNTIME",
            "security_decision": SECURITY_DECISION,
            "actual_stick_mapping_state": "missing",
            "physical_stick_availability": "unknown",
            "launcher_mapping_state": "missing",
            "aosp_artifact_state": "not_inspected_repository_only",
            "launcher_cluster_is_separate_from_main_five_apks": True,
            "generic_tv_phone_or_avd_substitution_allowed": False,
            "runtime_action_count": 0,
            "product_coverage_count": 0,
            "release_pass_claimed": False,
            "scenario_counts": {
                "total": 19,
                "p0": 15,
                "p1": 4,
                "blocked_by_device": 17,
                "blocked_by_product_boundary": 1,
                "static_closure_observed_pass": 1,
            },
            "qa048_019_claim_scope": "static_terminal_ledger_only",
        },
    }


def build_bundle() -> dict[Path, bytes]:
    validate_static_contracts()
    catalog = load_catalog()
    scenario_bytes = _csv_bytes(SCENARIO_HEADERS, build_scenario_rows(catalog))
    authority_bytes = _csv_bytes(AUTHORITY_HEADERS, build_authority_rows())
    report = _report(scenario_bytes, authority_bytes)
    report_bytes = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    bundle = {SCENARIO_OUTPUT: scenario_bytes, AUTHORITY_OUTPUT: authority_bytes, REPORT_OUTPUT: report_bytes}
    validate_bundle(bundle, validate_disk_artifacts=False)
    return bundle


def _parse_csv_bytes(value: bytes) -> tuple[list[str], list[dict[str, str]]]:
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("csv_invalid_utf8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)
    if any(None in row for row in rows):
        raise ContractError("csv_extra_cells")
    return list(reader.fieldnames or []), rows


def validate_bundle(bundle: Mapping[Path, bytes], *, validate_disk_artifacts: bool) -> None:
    if set(bundle) != {SCENARIO_OUTPUT, AUTHORITY_OUTPUT, REPORT_OUTPUT}:
        raise ContractError("report_bundle_file_set_drift")
    scenario_headers, scenarios = _parse_csv_bytes(bundle[SCENARIO_OUTPUT])
    authority_headers, authorities = _parse_csv_bytes(bundle[AUTHORITY_OUTPUT])
    if tuple(scenario_headers) != SCENARIO_HEADERS:
        raise ContractError("scenario_ledger_headers_drift")
    if tuple(authority_headers) != AUTHORITY_HEADERS:
        raise ContractError("authority_ledger_headers_drift")
    if [row["scenario_id"] for row in scenarios] != list(EXPECTED_IDS):
        raise ContractError("scenario_ledger_missing_or_reordered_rows")
    if len(authorities) != 5 or len({row["authority_id"] for row in authorities}) != 5:
        raise ContractError("authority_ledger_row_set_drift")
    if authorities != build_authority_rows():
        raise ContractError("authority_ledger_semantic_drift")

    expected_catalog = load_catalog()
    for source, row in zip(expected_catalog, scenarios, strict=True):
        for key in ("scenario_id", "priority", "surface_ids", "lane", "category"):
            if row[key] != source[key]:
                raise ContractError(f"scenario_ledger_catalog_drift:{source['scenario_id']}:{key}")
        if row["scenario_status"] not in TERMINAL_STATUSES:
            raise ContractError(f"scenario_status_not_terminal:{row['scenario_id']}")
        if row["evidence_status"] not in EVIDENCE_STATUSES:
            raise ContractError(f"scenario_evidence_status_invalid:{row['scenario_id']}")
        if row["runtime_executed"] != "false" or row["product_coverage_counted"] != "false":
            raise ContractError(f"repository_only_runtime_or_coverage_overclaim:{row['scenario_id']}")
        expected_status = _scenario_classification(row["scenario_id"])[0]
        if row["scenario_status"] != expected_status:
            raise ContractError(f"scenario_status_drift:{row['scenario_id']}")
        if row["scenario_id"] != "QA-048-019" and row["scenario_status"] == "observed_pass":
            raise ContractError(f"runtime_false_pass:{row['scenario_id']}")
    if scenarios[-1]["justification"].find("static closure only") < 0:
        raise ContractError("qa048_019_static_scope_missing")
    if scenarios != build_scenario_rows(expected_catalog):
        raise ContractError("scenario_ledger_semantic_drift")

    report = _json_loads(bundle[REPORT_OUTPUT])
    if not isinstance(report, dict):
        raise ContractError("summary_not_object")
    _validate_public_value(report)
    for raw in (scenarios, authorities):
        _validate_public_value(raw)
    payload = report.get("payload", {})
    counts = payload.get("scenario_counts", {}) if isinstance(payload, dict) else {}
    actual_counts = {
        "total": len(scenarios),
        "p0": sum(row["priority"] == "P0" for row in scenarios),
        "p1": sum(row["priority"] == "P1" for row in scenarios),
        "blocked_by_device": sum(row["scenario_status"] == "blocked_by_device" for row in scenarios),
        "blocked_by_product_boundary": sum(row["scenario_status"] == "blocked_by_product_boundary" for row in scenarios),
        "static_closure_observed_pass": sum(row["scenario_id"] == "QA-048-019" and row["scenario_status"] == "observed_pass" for row in scenarios),
    }
    if counts != actual_counts:
        raise ContractError("summary_scenario_counts_drift")
    required_report_values = {
        "task_id": TASK_ID,
        "execution_status": "blocked",
        "coverage_status": "blocked",
        "release_effect": "blocks_release",
        "production_safety_classification": PRODUCTION_SAFETY,
    }
    if any(report.get(key) != value for key, value in required_report_values.items()):
        raise ContractError("summary_blocked_authority_drift")
    if not isinstance(payload, dict) or any(
        payload.get(key) != value
        for key, value in {
            "runtime_action_count": 0,
            "product_coverage_count": 0,
            "release_pass_claimed": False,
            "launcher_cluster_is_separate_from_main_five_apks": True,
            "generic_tv_phone_or_avd_substitution_allowed": False,
        }.items()
    ):
        raise ContractError("summary_runtime_or_release_overclaim")
    artifact_map = {item["reference"]: item["sha256"] for item in report.get("artifacts", []) if isinstance(item, dict)}
    expected_hashes = {
        _repo_ref(SCENARIO_OUTPUT): _sha256(bundle[SCENARIO_OUTPUT]),
        _repo_ref(AUTHORITY_OUTPUT): _sha256(bundle[AUTHORITY_OUTPUT]),
    }
    if artifact_map != expected_hashes:
        raise ContractError("summary_artifact_hash_or_reference_drift")
    expected_report = _report(bundle[SCENARIO_OUTPUT], bundle[AUTHORITY_OUTPUT])
    if report != expected_report:
        raise ContractError("summary_semantic_drift")
    if validate_disk_artifacts:
        errors = _validate_v2_envelope(report, REPO_ROOT)
        if errors:
            raise ContractError("v2_envelope_invalid:" + "|".join(errors))


def _atomic_publish(bundle: Mapping[Path, bytes]) -> None:
    temporary: list[tuple[Path, Path]] = []
    originals: dict[Path, bytes | None] = {}
    published: list[Path] = []
    rollback_failed = False
    try:
        for path, value in bundle.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[path] = path.read_bytes() if path.exists() else None
            temp = path.with_name(f".{path.name}.task048.tmp")
            temp.write_bytes(value)
            temporary.append((temp, path))
        for temp, path in temporary:
            os.replace(temp, path)
            published.append(path)
    except OSError:
        rollback_errors: list[str] = []
        for path in reversed(published):
            try:
                original = originals[path]
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    rollback = path.with_name(f".{path.name}.task048.rollback")
                    rollback.write_bytes(original)
                    os.replace(rollback, path)
            except OSError:
                rollback_errors.append(path.name)
        if rollback_errors:
            rollback_failed = True
            raise ContractError("static_bundle_publish_rollback_failed:" + ",".join(rollback_errors))
        raise ContractError("static_bundle_publish_failed")
    finally:
        for temp, _ in temporary:
            if temp.exists():
                temp.unlink()
        if not rollback_failed:
            for _, path in temporary:
                rollback = path.with_name(f".{path.name}.task048.rollback")
                if rollback.exists():
                    rollback.unlink()


def _tracked_bundle() -> dict[Path, bytes]:
    bundle: dict[Path, bytes] = {}
    for path in (SCENARIO_OUTPUT, AUTHORITY_OUTPUT, REPORT_OUTPUT):
        if not path.is_file() or _is_reparse(path):
            raise ContractError(f"tracked_report_artifact_missing_or_not_regular:{path.name}")
        try:
            bundle[path] = path.read_bytes()
        except OSError as exc:
            raise ContractError(f"tracked_report_artifact_read_failed:{path.name}") from exc
    return bundle


def _emit(**values: Any) -> None:
    print(json.dumps({"task_id": TASK_ID, **values}, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true", help="validate fixed tracked contracts only")
    modes.add_argument("--preflight", action="store_true", help="confirm repository-only BLOCK_RUNTIME readiness")
    modes.add_argument("--execute", action="store_true", help="publish the fixed static blocked authority bundle")
    modes.add_argument("--validate-report", action="store_true", help="validate the tracked static authority bundle")
    args = parser.parse_args(argv)
    try:
        if args.validate_only:
            facts = validate_static_contracts()
            _emit(mode="validate-only", status="pass", **facts)
        elif args.preflight:
            facts = validate_static_contracts()
            _emit(mode="preflight", status="blocked_by_device", repository_ready=True, **facts)
        elif args.execute:
            bundle = build_bundle()
            _atomic_publish(bundle)
            validate_bundle(_tracked_bundle(), validate_disk_artifacts=True)
            _emit(mode="execute", status="static_closure_published_runtime_blocked", scenario_count=19, runtime_action_count=0)
        else:
            validate_static_contracts()
            validate_bundle(_tracked_bundle(), validate_disk_artifacts=True)
            _emit(mode="validate-report", status="pass", scenario_count=19, runtime_action_count=0)
    except (ContractError, json.JSONDecodeError, OSError) as exc:
        _emit(mode="error", status="blocked", reason=str(exc))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate a public-safe TASK-027 transition graph report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "task027-full-app-transition-graph-summary-v1"
TASK_ID = "TASK-027"

ALLOWED_RUN_STATUSES = {"blocked_preflight_pending", "partial", "full_graph_closed", "blocked", "fail"}
ALLOWED_RUNTIME_STATUSES = {"not_run", "partial", "closed_by_ledger", "blocked", "fail"}
ALLOWED_EXECUTION_MODES = {"preflight_contract_only", "physical_selected_lane_runtime"}
ALLOWED_CLOSURE_STATUSES = {
    "covered",
    "blocked_by_boundary",
    "blocked_by_tooling",
    "blocked_by_external_state",
    "not_run_out_of_scope",
}
ALLOWED_EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
ALLOWED_BOUNDARY_STATUSES = {"classified_not_entered", "blocked_by_boundary", "not_run_out_of_scope"}

FORBIDDEN_BOUNDARY_CATEGORIES = (
    "payment/subscription/purchase",
    "WebView/browser/external QR traversal",
    "stream/WebRTC/media playback/game session start",
    "Steam/account connection",
    "profile/account mutation",
    "network/offline manipulation",
)

REQUIRED_TRANSITION_FAMILIES = {
    "launch_recovery_to_catalog",
    "catalog_rail_focus_and_long_scroll",
    "search_input_no_results_and_recovery",
    "settings_gamepad_safe_entry",
    "game_card_to_detail",
    "detail_server_list_sampling",
    "boundary_qr_classification_and_recovery",
    "session_persistence_home_foreground",
    "force_stop_relaunch_recovery",
    "external_system_ambient_recovery",
}
REQUIRED_SCREEN_FAMILIES = {
    "app_launch_splash_loader",
    "external_tv_screensaver_or_system_overlay",
    "post_auth_games_catalog_top",
    "games_catalog_long_scroll_and_bottom",
    "catalog_banner_qr",
    "search_empty_keyboard_or_no_results",
    "session_journal_empty",
    "left_navigation_rail_expanded_collapsed_focus_states",
    "settings_root",
    "settings_promo_codes",
    "settings_gamepad_setup",
    "logout_confirmation_boundary",
    "game_detail_pricing_server_boundary",
    "server_card_dynamic_list",
    "steam_topup_qr",
    "feedback_qr",
    "connect_device_gate",
    "payment_checkout_or_payment_qr",
    "stream_or_paid_game_session",
    "profile_or_account_mutation_boundary",
    "network_offline_webview_payment_external_traversal",
}
REQUIRED_TASK025B_ANOMALIES = {"ANOM-025B-001", "ANOM-025B-002", "ANOM-025B-003"}
REQUIRED_PREFLIGHT_FIELDS = {
    "status",
    "physical_device_available",
    "selected_device_authorized",
    "selected_aliases_refreshed",
    "apk_presence_confirmed",
    "apk_hash_recorded_local_only",
    "synthetic_user_env_confirmed",
    "evidence_storage_approved",
    "cleanup_policy_confirmed",
    "qa_reviewer_a_approval",
    "qa_reviewer_b_approval",
    "security_prod_safety_approval",
}
PREFLIGHT_STATUSES = {"pending_runtime_confirmation", "confirmed_for_task027", "blocked_preflight_failed"}

FALSE_PUBLIC_SAFETY_FLAGS = {
    "raw_phone_otp_public",
    "raw_device_identifiers_public",
    "raw_apk_hash_public",
    "raw_apk_filename_public",
    "raw_qr_targets_public",
    "raw_screenshots_public",
    "raw_xml_public",
    "raw_logs_public",
    "raw_video_public",
    "raw_runtime_evidence_public",
    "private_routes_or_endpoints_public",
    "payment_webview_stream_entered",
    "profile_account_mutation_entered",
    "external_qr_or_browser_opened",
    "steam_account_mutation_performed",
    "network_offline_manipulation_performed",
}

FALSE_COVERAGE_CLAIMS = {
    "full_reachable_transition_graph_closed",
    "complete_dynamic_value_inventory",
    "complete_game_title_enumeration",
    "complete_server_row_enumeration",
    "payment_or_stream_covered",
    "webview_external_traversal_covered",
    "broad_compatibility_covered",
    "task025b_partial_counts_as_full_graph",
    "task026b_no_device_contract_counts_as_runtime_evidence",
}

URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
LOCAL_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<![\w+])\+?\d[\d\s().-]{8,}\d(?!\w)")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
ANDROID_ID_RE = re.compile(r"\b[0-9a-fA-F]{16}\b")
HEX_HASH_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
SECRET_PAIR_RE = re.compile(
    r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|bearer|otp)\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)
RAW_ARTIFACT_RE = re.compile(r"\.(?:png|jpg|jpeg|webp|mp4|mov|log|txt|xml|apk|aab|apks|xapk)(?:\b|$)", re.IGNORECASE)
PRIVATE_ROUTE_RE = re.compile(r"\b(?:deeplink|endpoint|header|payload|activity|package|class)\s*[:=]", re.IGNORECASE)
FIXED_VALUE_DUMP_RE = re.compile(
    r"\b(?:game_title|server_alias|server_count|ping_ms|gpu|cpu|tariff|price|qr_target|account_label)\s*[:=]",
    re.IGNORECASE,
)


def _public_safety_findings(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(_public_safety_findings(child, f"{path}.{key}"))
        return findings
    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_public_safety_findings(child, f"{path}[{index}]"))
        return findings
    if not isinstance(value, str) or not value:
        return findings
    if URL_RE.search(value):
        findings.append(f"{path} contains a URL-like value.")
    if LOCAL_PATH_RE.search(value):
        findings.append(f"{path} contains a raw local path.")
    if PHONE_RE.search(value):
        findings.append(f"{path} contains a phone-like value.")
    if IP_RE.search(value):
        findings.append(f"{path} contains an IP-like value.")
    if MAC_RE.search(value):
        findings.append(f"{path} contains a MAC-like value.")
    if ANDROID_ID_RE.search(value):
        findings.append(f"{path} contains an Android-ID-like value.")
    if HEX_HASH_RE.search(value):
        findings.append(f"{path} contains a hash-like value.")
    if SECRET_PAIR_RE.search(value):
        findings.append(f"{path} contains a secret-like key/value.")
    if RAW_ARTIFACT_RE.search(value):
        findings.append(f"{path} contains a raw artifact path.")
    if PRIVATE_ROUTE_RE.search(value):
        findings.append(f"{path} contains private route/internal metadata.")
    if FIXED_VALUE_DUMP_RE.search(value):
        findings.append(f"{path} contains a fixed dynamic-value dump.")
    return findings


def _require_object(value: Any, field_name: str) -> list[str]:
    return [] if isinstance(value, dict) else [f"{field_name} must be an object."]


def _validate_public_safety(flags: Any) -> list[str]:
    if not isinstance(flags, dict):
        return ["public_safety must be an object."]
    return [f"public_safety.{key} must be false." for key in sorted(FALSE_PUBLIC_SAFETY_FLAGS) if flags.get(key) is not False]


def _validate_coverage_claims(report: dict[str, Any]) -> list[str]:
    claims = report.get("coverage_claims")
    if not isinstance(claims, dict):
        return ["coverage_claims must be an object."]
    reasons = [f"coverage_claims.{key} must be false." for key in sorted(FALSE_COVERAGE_CLAIMS) if claims.get(key) is not False]
    if report.get("run_status") == "full_graph_closed":
        if claims.get("full_reachable_transition_graph_closed") is not True:
            reasons.append("coverage_claims.full_reachable_transition_graph_closed must be true for full_graph_closed.")
        reasons = [reason for reason in reasons if reason != "coverage_claims.full_reachable_transition_graph_closed must be false."]
    return reasons


def _validate_dynamic_policy(policy: Any) -> list[str]:
    if not isinstance(policy, dict):
        return ["dynamic_data_policy must be an object."]
    reasons: list[str] = []
    for key in (
        "assert_fixed_game_titles",
        "assert_fixed_server_rows",
        "assert_fixed_server_aliases",
        "assert_fixed_prices",
        "assert_fixed_hardware_rows",
        "assert_raw_qr_targets",
    ):
        if policy.get(key) is not False:
            reasons.append(f"dynamic_data_policy.{key} must be false.")
    if not policy.get("assert_categories_and_transition_invariants_only"):
        reasons.append("dynamic_data_policy.assert_categories_and_transition_invariants_only must be true.")
    return reasons


def _validate_preflight_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("preflight_ledger")
    if not isinstance(ledger, dict):
        return ["preflight_ledger must be an object."]
    reasons: list[str] = []
    missing = sorted(REQUIRED_PREFLIGHT_FIELDS - set(ledger))
    if missing:
        reasons.append(f"preflight_ledger missing required fields: {missing}.")
    status = ledger.get("status")
    if status not in PREFLIGHT_STATUSES:
        reasons.append("preflight_ledger.status is not recognized.")
    if report.get("run_status") == "blocked_preflight_pending":
        for key in sorted(REQUIRED_PREFLIGHT_FIELDS - {"status"}):
            if key in ledger and ledger.get(key) != "pending":
                reasons.append(f"preflight_ledger.{key} must be pending while run_status=blocked_preflight_pending.")
    if status == "confirmed_for_task027":
        for key in sorted(REQUIRED_PREFLIGHT_FIELDS - {"status"}):
            value = ledger.get(key)
            allowed = {True, "confirmed", "approved"}
            if value not in allowed:
                reasons.append(f"preflight_ledger.{key} must be confirmed or approved when preflight is confirmed.")
    if report.get("execution_mode") == "physical_selected_lane_runtime" and status != "confirmed_for_task027":
        reasons.append("physical_selected_lane_runtime requires preflight_ledger.status=confirmed_for_task027.")
    return reasons


def _validate_transition_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("transition_graph_closure_ledger")
    if not isinstance(ledger, list):
        return ["transition_graph_closure_ledger must be a list."]
    reasons: list[str] = []
    seen_ids: set[str] = set()
    families: set[str] = set()
    full_closed = report.get("run_status") == "full_graph_closed"
    for index, row in enumerate(ledger):
        if not isinstance(row, dict):
            reasons.append(f"transition_graph_closure_ledger[{index}] must be an object.")
            continue
        transition_id = row.get("transition_id")
        if not isinstance(transition_id, str) or not transition_id.strip():
            reasons.append(f"transition_graph_closure_ledger[{index}].transition_id is required.")
        elif transition_id in seen_ids:
            reasons.append(f"transition_graph_closure_ledger[{index}].transition_id is duplicated.")
        else:
            seen_ids.add(transition_id)
        family = row.get("transition_family")
        if isinstance(family, str):
            families.add(family)
        else:
            reasons.append(f"transition_graph_closure_ledger[{index}].transition_family is required.")
        if row.get("closure_status") not in ALLOWED_CLOSURE_STATUSES:
            reasons.append(f"transition_graph_closure_ledger[{index}].closure_status is not allowed.")
        evidence_status = row.get("evidence_status")
        if evidence_status not in ALLOWED_EVIDENCE_STATUSES:
            reasons.append(f"transition_graph_closure_ledger[{index}].evidence_status is not recognized.")
        evidence_ids = row.get("evidence_ids")
        if evidence_ids is not None and not isinstance(evidence_ids, list):
            reasons.append(f"transition_graph_closure_ledger[{index}].evidence_ids must be a list.")
        if row.get("closure_status") == "covered":
            if evidence_status != "confirmed":
                reasons.append(f"transition_graph_closure_ledger[{index}].evidence_status must be confirmed for covered.")
            if not evidence_ids:
                reasons.append(f"transition_graph_closure_ledger[{index}].evidence_ids are required for covered.")
        if full_closed and row.get("closure_status") != "not_run_out_of_scope":
            if evidence_status != "confirmed":
                reasons.append(f"transition_graph_closure_ledger[{index}].evidence_status must be confirmed for full graph closure.")
            if not evidence_ids:
                reasons.append(f"transition_graph_closure_ledger[{index}].evidence_ids are required for full graph closure.")
        for key in (
            "from_screen_family",
            "to_screen_family",
            "trigger_category",
            "observed_transition_category",
            "recovery_policy",
            "public_safe_note",
            "test_design_implication",
        ):
            if not row.get(key):
                reasons.append(f"transition_graph_closure_ledger[{index}].{key} is required.")
    missing = sorted(REQUIRED_TRANSITION_FAMILIES - families)
    if missing:
        reasons.append(f"transition_graph_closure_ledger missing required families: {missing}.")
    return reasons


def _validate_screen_family_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("screen_family_closure_ledger")
    if not isinstance(ledger, list):
        return ["screen_family_closure_ledger must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(ledger):
        if not isinstance(row, dict):
            reasons.append(f"screen_family_closure_ledger[{index}] must be an object.")
            continue
        family = row.get("screen_family")
        if not isinstance(family, str) or not family.strip():
            reasons.append(f"screen_family_closure_ledger[{index}].screen_family is required.")
        elif family in seen:
            reasons.append(f"screen_family_closure_ledger[{index}].screen_family is duplicated.")
        else:
            seen.add(family)
        if row.get("coverage_status") not in ALLOWED_CLOSURE_STATUSES:
            reasons.append(f"screen_family_closure_ledger[{index}].coverage_status is not allowed.")
        if row.get("evidence_status") not in ALLOWED_EVIDENCE_STATUSES:
            reasons.append(f"screen_family_closure_ledger[{index}].evidence_status is not recognized.")
        if report.get("run_status") == "full_graph_closed" and row.get("coverage_status") != "not_run_out_of_scope":
            if row.get("evidence_status") != "confirmed":
                reasons.append(f"screen_family_closure_ledger[{index}].evidence_status must be confirmed for full graph closure.")
            if not row.get("evidence_ids"):
                reasons.append(f"screen_family_closure_ledger[{index}].evidence_ids are required for full graph closure.")
    missing = sorted(REQUIRED_SCREEN_FAMILIES - seen)
    if missing:
        reasons.append(f"screen_family_closure_ledger missing required families: {missing}.")
    return reasons


def _validate_boundary_ledger(report: dict[str, Any]) -> list[str]:
    boundaries = report.get("boundary_ledger")
    if not isinstance(boundaries, list):
        return ["boundary_ledger must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    for index, boundary in enumerate(boundaries):
        if not isinstance(boundary, dict):
            reasons.append(f"boundary_ledger[{index}] must be an object.")
            continue
        boundary_id = boundary.get("boundary_id")
        if not isinstance(boundary_id, str) or not boundary_id.strip():
            reasons.append(f"boundary_ledger[{index}].boundary_id is required.")
        elif boundary_id in seen:
            reasons.append(f"boundary_ledger[{index}].boundary_id is duplicated.")
        else:
            seen.add(boundary_id)
        if boundary.get("boundary_category") not in FORBIDDEN_BOUNDARY_CATEGORIES:
            reasons.append(f"boundary_ledger[{index}].boundary_category must be a guarded boundary category.")
        if boundary.get("status") not in ALLOWED_BOUNDARY_STATUSES:
            reasons.append(f"boundary_ledger[{index}].status must be boundary-safe.")
        if boundary.get("entered") is not False:
            reasons.append(f"boundary_ledger[{index}].entered must be false.")
        if boundary.get("navigation_followed") is not False:
            reasons.append(f"boundary_ledger[{index}].navigation_followed must be false.")
        if boundary.get("external_action") != "not_performed":
            reasons.append(f"boundary_ledger[{index}].external_action must be not_performed.")
    return reasons


def _validate_anomalies(report: dict[str, Any]) -> list[str]:
    anomalies = report.get("anomaly_records")
    if not isinstance(anomalies, list):
        return ["anomaly_records must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    for index, anomaly in enumerate(anomalies):
        if not isinstance(anomaly, dict):
            reasons.append(f"anomaly_records[{index}] must be an object.")
            continue
        anomaly_id = anomaly.get("anomaly_id")
        if not isinstance(anomaly_id, str) or not anomaly_id.strip():
            reasons.append(f"anomaly_records[{index}].anomaly_id is required.")
        elif anomaly_id in seen:
            reasons.append(f"anomaly_records[{index}].anomaly_id is duplicated.")
        else:
            seen.add(anomaly_id)
        for key in (
            "category",
            "trigger_action",
            "expected_result",
            "observed_result",
            "evidence_status",
            "likely_or_hypothesis_cause",
            "recovery_action",
            "test_design_implication",
        ):
            if not anomaly.get(key):
                reasons.append(f"anomaly_records[{index}].{key} is required.")
        if anomaly.get("evidence_status") not in ALLOWED_EVIDENCE_STATUSES:
            reasons.append(f"anomaly_records[{index}].evidence_status is not recognized.")
    missing = sorted(REQUIRED_TASK025B_ANOMALIES - seen)
    if missing:
        reasons.append(f"anomaly_records missing required TASK-025B anomalies: {missing}.")
    return reasons


def _validate_evidence_id_shape(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for ledger_name in ("transition_graph_closure_ledger", "screen_family_closure_ledger", "boundary_ledger", "anomaly_records"):
        ledger = report.get(ledger_name)
        if not isinstance(ledger, list):
            continue
        for index, row in enumerate(ledger):
            if not isinstance(row, dict) or "evidence_ids" not in row:
                continue
            evidence_ids = row.get("evidence_ids")
            if not isinstance(evidence_ids, list):
                reasons.append(f"{ledger_name}[{index}].evidence_ids must be a list.")
                continue
            local_seen: set[str] = set()
            for evidence_id in evidence_ids:
                if not isinstance(evidence_id, str) or not evidence_id.strip():
                    reasons.append(f"{ledger_name}[{index}].evidence_ids contains an invalid evidence id.")
                elif evidence_id in local_seen:
                    reasons.append(f"{ledger_name}[{index}].evidence_ids contains a duplicate evidence id.")
                local_seen.add(evidence_id)
    return reasons


def validate_report_shape(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for field_name in (
        "schema_version",
        "task_id",
        "mode",
        "run_status",
        "runtime_execution_status",
        "execution_mode",
        "runtime_lane",
        "source_reports",
        "preflight_ledger",
        "transition_graph_closure_ledger",
        "screen_family_closure_ledger",
        "boundary_ledger",
        "anomaly_records",
        "public_safety",
        "coverage_claims",
        "dynamic_data_policy",
        "boundary_guard_categories",
        "unverified_areas",
    ):
        if field_name not in report:
            reasons.append(f"{field_name} is required.")
    if report.get("schema_version") != SCHEMA_VERSION:
        reasons.append(f"schema_version must be {SCHEMA_VERSION}.")
    if report.get("task_id") != TASK_ID:
        reasons.append("task_id must be TASK-027.")
    if report.get("mode") != "NON_AUTONOMOUS":
        reasons.append("mode must be NON_AUTONOMOUS.")
    if report.get("run_status") not in ALLOWED_RUN_STATUSES:
        reasons.append("run_status is not recognized.")
    if report.get("runtime_execution_status") not in ALLOWED_RUNTIME_STATUSES:
        reasons.append("runtime_execution_status is not recognized.")
    if report.get("execution_mode") not in ALLOWED_EXECUTION_MODES:
        reasons.append("execution_mode is not recognized.")
    if report.get("run_status") == "full_graph_closed" and report.get("execution_mode") != "physical_selected_lane_runtime":
        reasons.append("full_graph_closed requires physical_selected_lane_runtime execution.")
    if report.get("run_status") == "blocked_preflight_pending" and report.get("runtime_execution_status") != "not_run":
        reasons.append("blocked_preflight_pending requires runtime_execution_status=not_run.")
    if report.get("boundary_guard_categories") != list(FORBIDDEN_BOUNDARY_CATEGORIES):
        reasons.append("boundary_guard_categories must match the guarded boundary allowlist.")
    if not isinstance(report.get("source_reports"), list) or not report.get("source_reports"):
        reasons.append("source_reports must be a non-empty list.")
    if not isinstance(report.get("unverified_areas"), list):
        reasons.append("unverified_areas must be a list.")

    reasons.extend(_require_object(report.get("runtime_lane"), "runtime_lane"))
    reasons.extend(_validate_preflight_ledger(report))
    reasons.extend(_public_safety_findings(report))
    reasons.extend(_validate_public_safety(report.get("public_safety")))
    reasons.extend(_validate_coverage_claims(report))
    reasons.extend(_validate_dynamic_policy(report.get("dynamic_data_policy")))
    reasons.extend(_validate_transition_ledger(report))
    reasons.extend(_validate_screen_family_ledger(report))
    reasons.extend(_validate_boundary_ledger(report))
    reasons.extend(_validate_anomalies(report))
    reasons.extend(_validate_evidence_id_shape(report))
    return sorted(set(reasons))


def validate_report(path: Path) -> list[str]:
    if not path.exists():
        return ["Report file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return [f"Report file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return ["Report must be a JSON object."]
    return validate_report_shape(loaded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate public-safe TASK-027 transition graph report JSON.")
    parser.add_argument("--report", type=Path, required=True, help="Path to a public-safe TASK-027 report JSON.")
    args = parser.parse_args(argv)

    errors = validate_report(args.report)
    result = {
        "report": args.report.as_posix(),
        "validation_status": "pass" if not errors else "fail",
        "errors": errors,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

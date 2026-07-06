"""Validate the public-safe TASK-027T visual destination coverage report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "task027t-continue-visual-destination-screen-coverage-v1"
TASK_ID = "TASK-027T"

REQUIRED_TARGETS = {
    "session_journal_empty",
    "steam_topup_qr",
    "feedback_qr",
}
QR_TARGETS = {"steam_topup_qr", "feedback_qr"}
DESTINATION_VISUAL_PROOF_EVIDENCE_IDS = {
    "session_journal_empty": {"rt027t-cp011-after-grid-dpad-left"},
    "steam_topup_qr": {"rt027t-cp013-steam-topup-qr-after-center"},
    "feedback_qr": {"rt027t-cp015-feedback-qr-after-center"},
}
REQUIRED_SOURCE_TASKS = {"TASK-027R", "TASK-027S"}
REQUIRED_ROUTE_GATES = {
    "loaded_actionable_app_state_before_destination_assertions",
    "app_shell_loader_after_launcher_entry",
    "fresh_task027t_visual_evidence_required",
}
REQUIRED_BOUNDARY_CATEGORIES = {
    "payment/subscription/purchase",
    "WebView/browser/external QR traversal",
    "stream/WebRTC/media playback/game session start",
    "Steam/account connection",
    "profile/account mutation",
    "network/offline manipulation",
}

ALLOWED_RUN_STATUSES = {
    "not_run_pending_runtime_evidence",
    "blocked_missing_local_selected_lane",
    "blocked_pending_runtime_evidence",
    "partial",
    "blocked",
    "covered",
}
ALLOWED_RUNTIME_STATUSES = {"not_run", "blocked", "partial", "covered"}
ALLOWED_EXECUTION_MODES = {
    "no_runtime_public_safe_skeleton",
    "physical_selected_lane_runtime_preflight_blocked",
    "physical_selected_lane_runtime",
}
ALLOWED_COVERAGE_STATUSES = {
    "not_run_pending_runtime_evidence",
    "blocked_pending_runtime_evidence",
    "blocked_by_missing_local_selected_lane",
    "blocked_by_app_shell_loader",
    "blocked_by_prior_rail_input_blocker",
    "blocked_by_tooling",
    "blocked_by_boundary",
    "not_run_out_of_scope",
    "covered",
}
ALLOWED_EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
ALLOWED_QR_DECODE_STATUSES = {"not_run", "not_reached", "local_only_decoded", "blocked_by_tooling"}

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
    "app_shell_loader_counts_as_catalog",
    "app_shell_loader_counts_as_destination",
    "prior_task027r_or_task027s_evidence_counts_as_task027t_visual_proof",
    "qr_navigation_followed",
    "payment_or_stream_covered",
    "profile_or_account_mutation_covered",
    "network_offline_covered",
}

TASK027T_EVIDENCE_ID_RE = re.compile(r"^rt027t-cp\d{3}(?:-[a-z0-9-]+)?$")
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
LOCAL_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<![\w+])\+?\d[\d\s().-]{8,}\d(?!\w)")
HEX_HASH_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
SECRET_PAIR_RE = re.compile(
    r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|bearer|otp)\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)
RAW_ARTIFACT_RE = re.compile(r"\.(?:png|jpg|jpeg|webp|mp4|mov|log|txt|xml|apk|aab|apks|xapk|zip)(?:\b|$)", re.IGNORECASE)
PRIVATE_ROUTE_RE = re.compile(r"\b(?:deeplink|endpoint|header|payload|activity|package|class|component)\s*[:=]", re.IGNORECASE)


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
    if HEX_HASH_RE.search(value):
        findings.append(f"{path} contains a hash-like value.")
    if SECRET_PAIR_RE.search(value):
        findings.append(f"{path} contains a secret-like key/value.")
    if RAW_ARTIFACT_RE.search(value):
        findings.append(f"{path} contains a raw artifact reference.")
    if PRIVATE_ROUTE_RE.search(value):
        findings.append(f"{path} contains private route/internal metadata.")
    return findings


def _validate_public_safety(report: dict[str, Any]) -> list[str]:
    flags = report.get("public_safety")
    if not isinstance(flags, dict):
        return ["public_safety must be an object."]
    return [f"public_safety.{key} must be false." for key in sorted(FALSE_PUBLIC_SAFETY_FLAGS) if flags.get(key) is not False]


def _validate_coverage_claims(report: dict[str, Any]) -> list[str]:
    claims = report.get("coverage_claims")
    if not isinstance(claims, dict):
        return ["coverage_claims must be an object."]

    reasons = [f"coverage_claims.{key} must be false." for key in sorted(FALSE_COVERAGE_CLAIMS) if claims.get(key) is not False]
    if claims.get("runtime_executed") is True and report.get("runtime_execution_status") in {"not_run", "blocked"}:
        reasons.append("coverage_claims.runtime_executed cannot be true when runtime_execution_status is not_run or blocked.")
    if claims.get("loaded_actionable_app_state_reconfirmed") is True and report.get("runtime_execution_status") in {
        "not_run",
        "blocked",
    }:
        reasons.append(
            "coverage_claims.loaded_actionable_app_state_reconfirmed cannot be true when runtime_execution_status is not_run or blocked."
        )
    if claims.get("qr_target_decoded") is True:
        qr_rows = [
            row
            for row in report.get("target_destination_ledger", [])
            if isinstance(row, dict) and row.get("screen_family") in {"steam_topup_qr", "feedback_qr"}
        ]
        missing_decoded = [
            row.get("screen_family")
            for row in qr_rows
            if row.get("coverage_status") == "covered" and row.get("qr_decode_status") != "local_only_decoded"
        ]
        if missing_decoded:
            reasons.append(f"coverage_claims.qr_target_decoded cannot be true without local_only_decoded QR rows for: {missing_decoded}.")
        if not any(row.get("qr_decode_status") == "local_only_decoded" for row in qr_rows):
            reasons.append("coverage_claims.qr_target_decoded cannot be true without a local_only_decoded QR destination row.")
    destination_claims = {
        "session_journal_visually_covered": "session_journal_empty",
        "steam_topup_qr_visually_covered": "steam_topup_qr",
        "feedback_qr_visually_covered": "feedback_qr",
    }
    rows = {
        row.get("screen_family"): row
        for row in report.get("target_destination_ledger", [])
        if isinstance(row, dict) and isinstance(row.get("screen_family"), str)
    }
    for claim_key, family in destination_claims.items():
        row = rows.get(family)
        if claims.get(claim_key) is True:
            if not isinstance(row, dict) or row.get("coverage_status") != "covered" or row.get("visual_destination_proof") is not True:
                reasons.append(f"coverage_claims.{claim_key} cannot be true without a covered {family} destination row.")
            elif not _has_destination_visual_proof_evidence(row):
                reasons.append(f"coverage_claims.{claim_key} cannot be true without destination-specific TASK-027T visual evidence.")
            elif family in QR_TARGETS and row.get("qr_decode_status") != "local_only_decoded":
                reasons.append(f"coverage_claims.{claim_key} cannot be true without local_only_decoded QR metadata.")
        elif isinstance(row, dict) and row.get("coverage_status") == "covered":
            reasons.append(f"coverage_claims.{claim_key} must be true when {family} is covered.")
    return reasons


def _validate_evidence_ids(rows: list[dict[str, Any]], path: str) -> list[str]:
    reasons: list[str] = []
    for index, row in enumerate(rows):
        evidence_ids = row.get("evidence_ids")
        if not isinstance(evidence_ids, list):
            reasons.append(f"{path}[{index}].evidence_ids must be a list.")
            continue
        seen: set[str] = set()
        for evidence_id in evidence_ids:
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                reasons.append(f"{path}[{index}].evidence_ids contains an invalid evidence id.")
            elif not TASK027T_EVIDENCE_ID_RE.fullmatch(evidence_id):
                reasons.append(f"{path}[{index}].evidence_ids contains an unsupported TASK-027T evidence id.")
            elif evidence_id in seen:
                reasons.append(f"{path}[{index}].evidence_ids contains a duplicate evidence id.")
            seen.add(evidence_id)
    return reasons


def _has_task027t_evidence(row: dict[str, Any]) -> bool:
    evidence_ids = row.get("evidence_ids")
    return isinstance(evidence_ids, list) and any(isinstance(item, str) and TASK027T_EVIDENCE_ID_RE.fullmatch(item) for item in evidence_ids)


def _has_destination_visual_proof_evidence(row: dict[str, Any]) -> bool:
    family = row.get("screen_family")
    required_ids = DESTINATION_VISUAL_PROOF_EVIDENCE_IDS.get(family)
    evidence_ids = row.get("evidence_ids")
    if not required_ids or not isinstance(evidence_ids, list):
        return False
    return any(isinstance(item, str) and item in required_ids for item in evidence_ids)


def _validate_runtime_scope(report: dict[str, Any]) -> list[str]:
    scope = report.get("runtime_scope")
    if not isinstance(scope, dict):
        return ["runtime_scope must be an object."]
    reasons: list[str] = []
    if report.get("runtime_execution_status") == "not_run":
        for key in ("runtime_performed", "adb_or_device_commands_performed", "ignored_local_evidence_inspected"):
            if scope.get(key) is not False:
                reasons.append(f"runtime_scope.{key} must be false while runtime_execution_status is not_run.")
        if scope.get("runtime_approval_required_before_execution") is not True:
            reasons.append("runtime_scope.runtime_approval_required_before_execution must be true while runtime is not run.")
    if report.get("runtime_execution_status") == "blocked":
        for key in ("runtime_performed", "adb_or_device_commands_performed", "ignored_local_evidence_inspected"):
            if scope.get(key) is not False:
                reasons.append(f"runtime_scope.{key} must be false while runtime_execution_status is blocked.")
        if report.get("run_status") == "blocked_missing_local_selected_lane":
            if scope.get("selected_lane_approval_reviewed") is not True:
                reasons.append("runtime_scope.selected_lane_approval_reviewed must be true for missing-lane blocker.")
            if scope.get("lane_unchanged_from_task027s") is not True:
                reasons.append("runtime_scope.lane_unchanged_from_task027s must be true for TASK-027T.")
            if scope.get("local_selected_lane_material_present") is not False:
                reasons.append("runtime_scope.local_selected_lane_material_present must be false for missing-lane blocker.")
    if report.get("runtime_execution_status") in {"partial", "covered"}:
        for key in ("runtime_performed", "selected_lane_approval_reviewed", "lane_unchanged_from_task027s"):
            if scope.get(key) is not True:
                reasons.append(f"runtime_scope.{key} must be true when runtime_execution_status is partial or covered.")
        if scope.get("local_selected_lane_material_present") is not True:
            reasons.append(
                "runtime_scope.local_selected_lane_material_present must be true when runtime_execution_status is partial or covered."
            )
        if scope.get("adb_or_device_commands_performed") is not True:
            reasons.append("runtime_scope.adb_or_device_commands_performed must be true when runtime executed.")
    return reasons


def _validate_preflight_blockers(report: dict[str, Any]) -> list[str]:
    blockers = report.get("preflight_blockers")
    if report.get("run_status") != "blocked_missing_local_selected_lane":
        return []
    if not isinstance(blockers, list) or not blockers:
        return ["preflight_blockers must be a non-empty list for missing-lane blocker."]
    reasons: list[str] = []
    categories = set()
    for index, row in enumerate(blockers):
        if not isinstance(row, dict):
            reasons.append(f"preflight_blockers[{index}] must be an object.")
            continue
        category = row.get("blocker_category")
        if isinstance(category, str):
            categories.add(category)
        else:
            reasons.append(f"preflight_blockers[{index}].blocker_category is required.")
        if row.get("evidence_status") != "confirmed":
            reasons.append(f"preflight_blockers[{index}].evidence_status must be confirmed.")
        for key in ("observed_result", "expected_result", "test_design_implication"):
            if not row.get(key):
                reasons.append(f"preflight_blockers[{index}].{key} is required.")
    if "missing_local_selected_lane_material" not in categories:
        reasons.append("preflight_blockers must include missing_local_selected_lane_material.")
    return reasons


def _validate_source_reports(report: dict[str, Any]) -> list[str]:
    source_reports = report.get("source_reports")
    if not isinstance(source_reports, list) or not source_reports:
        return ["source_reports must be a non-empty list."]
    seen = {row.get("task_id") for row in source_reports if isinstance(row, dict)}
    missing = sorted(REQUIRED_SOURCE_TASKS - seen)
    return [f"source_reports missing required task references: {missing}."] if missing else []


def _validate_target_destination_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("target_destination_ledger")
    if not isinstance(ledger, list):
        return ["target_destination_ledger must be a list."]

    reasons: list[str] = []
    families: set[str] = set()
    runtime_not_run = report.get("runtime_execution_status") == "not_run"
    runtime_blocked = report.get("runtime_execution_status") == "blocked"

    for index, row in enumerate(ledger):
        if not isinstance(row, dict):
            reasons.append(f"target_destination_ledger[{index}] must be an object.")
            continue
        family = row.get("screen_family")
        if isinstance(family, str):
            families.add(family)
        else:
            reasons.append(f"target_destination_ledger[{index}].screen_family is required.")
        status = row.get("coverage_status")
        if status not in ALLOWED_COVERAGE_STATUSES:
            reasons.append(f"target_destination_ledger[{index}].coverage_status is not allowed.")
        evidence_status = row.get("evidence_status")
        if evidence_status not in ALLOWED_EVIDENCE_STATUSES:
            reasons.append(f"target_destination_ledger[{index}].evidence_status is not recognized.")
        if status == "covered":
            if row.get("visual_destination_proof") is not True:
                reasons.append(f"target_destination_ledger[{index}] cannot be covered without visual_destination_proof=true.")
            if row.get("runtime_evidence_collected") is not True:
                reasons.append(f"target_destination_ledger[{index}] cannot be covered without runtime_evidence_collected=true.")
            if evidence_status != "confirmed":
                reasons.append(f"target_destination_ledger[{index}] cannot be covered unless evidence_status is confirmed.")
            if not _has_task027t_evidence(row):
                reasons.append(f"target_destination_ledger[{index}] cannot be covered without fresh TASK-027T evidence IDs.")
            if family in DESTINATION_VISUAL_PROOF_EVIDENCE_IDS and not _has_destination_visual_proof_evidence(row):
                reasons.append(
                    f"target_destination_ledger[{index}] cannot be covered without destination-specific TASK-027T visual evidence."
                )
            if family in QR_TARGETS and row.get("qr_decode_status") != "local_only_decoded":
                reasons.append(f"target_destination_ledger[{index}] cannot be covered without local_only_decoded QR metadata.")
        if runtime_not_run or runtime_blocked:
            if row.get("visual_destination_proof") is not False:
                reasons.append(
                    f"target_destination_ledger[{index}].visual_destination_proof must be false while runtime is not run or blocked."
                )
            if row.get("runtime_evidence_collected") is not False:
                reasons.append(
                    f"target_destination_ledger[{index}].runtime_evidence_collected must be false while runtime is not run or blocked."
                )
            if row.get("evidence_ids"):
                reasons.append(f"target_destination_ledger[{index}].evidence_ids must be empty while runtime is not run or blocked.")
            if runtime_not_run and evidence_status != "unknown":
                reasons.append(f"target_destination_ledger[{index}].evidence_status must be unknown while runtime is not run.")
            if runtime_blocked and evidence_status != "confirmed":
                reasons.append(f"target_destination_ledger[{index}].evidence_status must be confirmed while runtime is blocked.")
            allowed_unexecuted_statuses = {
                "not_run_pending_runtime_evidence",
                "blocked_pending_runtime_evidence",
                "blocked_by_missing_local_selected_lane",
            }
            if status not in allowed_unexecuted_statuses:
                reasons.append(
                    f"target_destination_ledger[{index}].coverage_status must be not-run or blocked while runtime is not run or blocked."
                )
        if family in QR_TARGETS:
            if row.get("qr_navigation_followed") is not False:
                reasons.append(f"target_destination_ledger[{index}].qr_navigation_followed must be false.")
            if row.get("qr_decode_status") not in ALLOWED_QR_DECODE_STATUSES:
                reasons.append(f"target_destination_ledger[{index}].qr_decode_status is not allowed.")
            if row.get("qr_decode_status") == "local_only_decoded" and not _has_task027t_evidence(row):
                reasons.append(
                    f"target_destination_ledger[{index}].qr_decode_status cannot be local_only_decoded without TASK-027T evidence."
                )
            if row.get("qr_decode_status") == "local_only_decoded" and not _has_destination_visual_proof_evidence(row):
                reasons.append(
                    f"target_destination_ledger[{index}].qr_decode_status cannot be local_only_decoded without destination-specific TASK-027T visual evidence."
                )

    missing = sorted(REQUIRED_TARGETS - families)
    if missing:
        reasons.append(f"target_destination_ledger missing required targets: {missing}.")
    reasons.extend(_validate_evidence_ids([row for row in ledger if isinstance(row, dict)], "target_destination_ledger"))
    return reasons


def _validate_route_gate_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("route_gate_ledger")
    if not isinstance(ledger, list):
        return ["route_gate_ledger must be a list."]

    reasons: list[str] = []
    aliases: set[str] = set()
    runtime_not_run = report.get("runtime_execution_status") == "not_run"
    runtime_blocked = report.get("runtime_execution_status") == "blocked"

    for index, row in enumerate(ledger):
        if not isinstance(row, dict):
            reasons.append(f"route_gate_ledger[{index}] must be an object.")
            continue
        alias = row.get("gate_alias")
        if isinstance(alias, str):
            aliases.add(alias)
        else:
            reasons.append(f"route_gate_ledger[{index}].gate_alias is required.")
        if row.get("coverage_status") not in ALLOWED_COVERAGE_STATUSES:
            reasons.append(f"route_gate_ledger[{index}].coverage_status is not allowed.")
        if row.get("evidence_status") not in ALLOWED_EVIDENCE_STATUSES:
            reasons.append(f"route_gate_ledger[{index}].evidence_status is not recognized.")
        if (runtime_not_run or runtime_blocked) and row.get("runtime_evidence_collected") is not False:
            reasons.append(
                f"route_gate_ledger[{index}].runtime_evidence_collected must be false while runtime is not run or blocked."
            )
        if alias == "app_shell_loader_after_launcher_entry":
            if row.get("coverage_status") == "covered":
                reasons.append("route_gate_ledger app_shell_loader_after_launcher_entry must not be marked covered.")
            forbidden = set(row.get("must_not_classify_as", [])) if isinstance(row.get("must_not_classify_as"), list) else set()
            for required_forbidden in (
                "post_auth_games_catalog_top",
                "session_journal_empty",
                "steam_topup_qr",
                "feedback_qr",
                "covered_destination",
            ):
                if required_forbidden not in forbidden:
                    reasons.append(f"route_gate_ledger[{index}].must_not_classify_as missing {required_forbidden}.")
            if row.get("timeout_policy_seconds") != 120:
                reasons.append(f"route_gate_ledger[{index}].timeout_policy_seconds must be 120 for app shell loader.")

    missing = sorted(REQUIRED_ROUTE_GATES - aliases)
    if missing:
        reasons.append(f"route_gate_ledger missing required gates: {missing}.")
    reasons.extend(_validate_evidence_ids([row for row in ledger if isinstance(row, dict)], "route_gate_ledger"))
    return reasons


def _validate_planned_runtime_boundaries(report: dict[str, Any]) -> list[str]:
    boundaries = report.get("planned_runtime_boundaries")
    if not isinstance(boundaries, list):
        return ["planned_runtime_boundaries must be a list."]

    reasons: list[str] = []
    categories: set[str] = set()
    for index, row in enumerate(boundaries):
        if not isinstance(row, dict):
            reasons.append(f"planned_runtime_boundaries[{index}] must be an object.")
            continue
        category = row.get("boundary_category")
        if isinstance(category, str):
            categories.add(category)
        else:
            reasons.append(f"planned_runtime_boundaries[{index}].boundary_category is required.")
        for bool_key in ("entered", "navigation_followed"):
            if row.get(bool_key) is not False:
                reasons.append(f"planned_runtime_boundaries[{index}].{bool_key} must be false.")
        if row.get("external_action") != "not_performed":
            reasons.append(f"planned_runtime_boundaries[{index}].external_action must be not_performed.")
        if row.get("status") not in {"not_run_out_of_scope", "blocked_by_boundary"}:
            reasons.append(f"planned_runtime_boundaries[{index}].status must be not_run_out_of_scope or blocked_by_boundary.")
        if row.get("evidence_status") not in ALLOWED_EVIDENCE_STATUSES:
            reasons.append(f"planned_runtime_boundaries[{index}].evidence_status is not recognized.")

    missing = sorted(REQUIRED_BOUNDARY_CATEGORIES - categories)
    if missing:
        reasons.append(f"planned_runtime_boundaries missing required categories: {missing}.")
    return reasons


def _validate_modality_audit(report: dict[str, Any]) -> list[str]:
    audit = report.get("checkpoint_modality_audit")
    if not isinstance(audit, dict):
        return ["checkpoint_modality_audit must be an object."]
    reasons: list[str] = []
    if audit.get("raw_artifacts_public") is not False:
        reasons.append("checkpoint_modality_audit.raw_artifacts_public must be false.")
    if audit.get("timeout_policy_seconds_for_app_shell_loader") != 120:
        reasons.append("checkpoint_modality_audit.timeout_policy_seconds_for_app_shell_loader must be 120.")
    if report.get("runtime_execution_status") == "not_run":
        if audit.get("runtime_checkpoints_captured") is not False:
            reasons.append("checkpoint_modality_audit.runtime_checkpoints_captured must be false while runtime is not run.")
        if audit.get("screenshot_visual_inspection") != "not_run":
            reasons.append("checkpoint_modality_audit.screenshot_visual_inspection must be not_run while runtime is not run.")
        if audit.get("xml_capture") != "not_run":
            reasons.append("checkpoint_modality_audit.xml_capture must be not_run while runtime is not run.")
        if audit.get("local_only_diagnostics_collected") is not False:
            reasons.append("checkpoint_modality_audit.local_only_diagnostics_collected must be false while runtime is not run.")
    if report.get("runtime_execution_status") == "blocked":
        if audit.get("runtime_checkpoints_captured") is not False:
            reasons.append("checkpoint_modality_audit.runtime_checkpoints_captured must be false while runtime is blocked.")
        if audit.get("screenshot_visual_inspection") != "blocked_before_capture":
            reasons.append(
                "checkpoint_modality_audit.screenshot_visual_inspection must be blocked_before_capture while runtime is blocked."
            )
        if audit.get("xml_capture") != "blocked_before_capture":
            reasons.append("checkpoint_modality_audit.xml_capture must be blocked_before_capture while runtime is blocked.")
        if audit.get("local_only_diagnostics_collected") is not False:
            reasons.append("checkpoint_modality_audit.local_only_diagnostics_collected must be false while runtime is blocked.")
    if report.get("runtime_execution_status") in {"partial", "covered"}:
        if audit.get("runtime_checkpoints_captured") is not True:
            reasons.append("checkpoint_modality_audit.runtime_checkpoints_captured must be true when runtime executed.")
        if not str(audit.get("screenshot_visual_inspection", "")).startswith("confirmed"):
            reasons.append("checkpoint_modality_audit.screenshot_visual_inspection must be confirmed when runtime executed.")
        if not str(audit.get("xml_capture", "")).startswith("confirmed"):
            reasons.append("checkpoint_modality_audit.xml_capture must be confirmed when runtime executed.")
    return reasons


def _validate_top_level_status_consistency(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    run_status = report.get("run_status")
    runtime_status = report.get("runtime_execution_status")
    if run_status == "blocked_missing_local_selected_lane" and runtime_status != "blocked":
        reasons.append("run_status blocked_missing_local_selected_lane requires runtime_execution_status blocked.")
    if run_status == "covered" and runtime_status != "covered":
        reasons.append("run_status covered requires runtime_execution_status covered.")
    if runtime_status == "covered":
        rows = [
            row
            for row in report.get("target_destination_ledger", [])
            if isinstance(row, dict) and row.get("screen_family") in REQUIRED_TARGETS
        ]
        covered = {
            row.get("screen_family")
            for row in rows
            if row.get("coverage_status") == "covered"
            and row.get("visual_destination_proof") is True
            and row.get("runtime_evidence_collected") is True
            and row.get("evidence_status") == "confirmed"
            and _has_destination_visual_proof_evidence(row)
            and (row.get("screen_family") not in QR_TARGETS or row.get("qr_decode_status") == "local_only_decoded")
        }
        missing = sorted(REQUIRED_TARGETS - covered)
        if missing:
            reasons.append(f"runtime_execution_status covered requires covered destination rows for: {missing}.")
        claims = report.get("coverage_claims")
        if isinstance(claims, dict):
            for key in (
                "runtime_executed",
                "loaded_actionable_app_state_reconfirmed",
                "session_journal_visually_covered",
                "steam_topup_qr_visually_covered",
                "feedback_qr_visually_covered",
            ):
                if claims.get(key) is not True:
                    reasons.append(f"coverage_claims.{key} must be true when runtime_execution_status is covered.")
    if runtime_status == "partial" and run_status == "covered":
        reasons.append("run_status covered cannot be paired with runtime_execution_status partial.")
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
        "runtime_scope",
        "preflight_blockers",
        "source_reports",
        "target_destination_ledger",
        "route_gate_ledger",
        "planned_runtime_boundaries",
        "checkpoint_modality_audit",
        "public_safety",
        "coverage_claims",
        "unverified_areas",
    ):
        if field_name not in report:
            reasons.append(f"{field_name} is required.")
    if report.get("schema_version") != SCHEMA_VERSION:
        reasons.append(f"schema_version must be {SCHEMA_VERSION}.")
    if report.get("task_id") != TASK_ID:
        reasons.append(f"task_id must be {TASK_ID}.")
    if report.get("mode") != "NON_AUTONOMOUS":
        reasons.append("mode must be NON_AUTONOMOUS.")
    if report.get("run_status") not in ALLOWED_RUN_STATUSES:
        reasons.append("run_status is not recognized.")
    if report.get("runtime_execution_status") not in ALLOWED_RUNTIME_STATUSES:
        reasons.append("runtime_execution_status is not recognized.")
    if report.get("execution_mode") not in ALLOWED_EXECUTION_MODES:
        reasons.append("execution_mode is not recognized.")
    if not isinstance(report.get("unverified_areas"), list) or not report.get("unverified_areas"):
        reasons.append("unverified_areas must be a non-empty list.")

    reasons.extend(_public_safety_findings(report))
    reasons.extend(_validate_runtime_scope(report))
    reasons.extend(_validate_preflight_blockers(report))
    reasons.extend(_validate_top_level_status_consistency(report))
    reasons.extend(_validate_source_reports(report))
    reasons.extend(_validate_public_safety(report))
    reasons.extend(_validate_coverage_claims(report))
    reasons.extend(_validate_target_destination_ledger(report))
    reasons.extend(_validate_route_gate_ledger(report))
    reasons.extend(_validate_planned_runtime_boundaries(report))
    reasons.extend(_validate_modality_audit(report))
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
    parser = argparse.ArgumentParser(description="Validate public-safe TASK-027T visual destination report JSON.")
    parser.add_argument("--report", type=Path, required=True, help="Path to a public-safe TASK-027T report JSON.")
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

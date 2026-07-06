"""Validate the public-safe TASK-027S visual destination coverage report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "task027s-visual-destination-screen-coverage-v1"
TASK_ID = "TASK-027S"

REQUIRED_TARGETS = {
    "session_journal_empty",
    "steam_topup_qr",
    "feedback_qr",
}
REQUIRED_ENTRY_SURFACES = {
    "google_tv_launcher_apps_row_or_recommendations",
    "explicit_component_launch_oracle",
    "leanback_package_launch_oracle",
}
REQUIRED_STATE_ALIASES = {"app_shell_loader_after_launcher_entry"}
REQUIRED_ANOMALIES = {
    "ANOM-027S-001",
    "ANOM-027S-002",
    "ANOM-027S-003",
    "ANOM-027S-004",
}

ALLOWED_RUN_STATUSES = {"blocked_by_app_shell_loader", "partial", "blocked", "covered"}
ALLOWED_RUNTIME_STATUSES = {"blocked", "partial", "not_run"}
ALLOWED_EXECUTION_MODES = {"physical_selected_lane_runtime"}
ALLOWED_COVERAGE_STATUSES = {
    "covered",
    "covered_as_entry_surface",
    "blocked_by_tooling",
    "blocked_by_app_shell_loader_and_prior_rail_input_blocker",
    "blocked_by_boundary",
    "not_run_out_of_scope",
}
ALLOWED_EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}

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
    "session_journal_visually_covered",
    "steam_topup_qr_visually_covered",
    "feedback_qr_visually_covered",
    "app_shell_loader_counts_as_catalog",
    "app_shell_loader_counts_as_destination",
    "qr_target_decoded",
    "qr_navigation_followed",
    "payment_or_stream_covered",
    "profile_or_account_mutation_covered",
    "network_offline_covered",
}

ALLOWED_EVIDENCE_ID_RE = re.compile(r"^rt027s-cp\d{3}(?:-[a-z0-9-]+)?$|^rt027r-cp\d{3}[a-z]?$")
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
    if claims.get("launcher_entry_surface_covered") is not True:
        reasons.append("coverage_claims.launcher_entry_surface_covered must be true.")
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
            elif not ALLOWED_EVIDENCE_ID_RE.fullmatch(evidence_id):
                reasons.append(f"{path}[{index}].evidence_ids contains an unsupported TASK-027S evidence id.")
            elif evidence_id in seen:
                reasons.append(f"{path}[{index}].evidence_ids contains a duplicate evidence id.")
            seen.add(evidence_id)
    return reasons


def _validate_target_destination_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("target_destination_ledger")
    if not isinstance(ledger, list):
        return ["target_destination_ledger must be a list."]
    reasons: list[str] = []
    families: set[str] = set()
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
        if row.get("evidence_status") not in ALLOWED_EVIDENCE_STATUSES:
            reasons.append(f"target_destination_ledger[{index}].evidence_status is not recognized.")
        if status == "covered" and row.get("visual_destination_proof") is not True:
            reasons.append(f"target_destination_ledger[{index}] cannot be covered without visual_destination_proof=true.")
        if family in REQUIRED_TARGETS and row.get("visual_destination_proof") is True and status != "covered":
            reasons.append(f"target_destination_ledger[{index}] has visual proof but is not marked covered.")
        if family in {"steam_topup_qr", "feedback_qr"} and row.get("qr_navigation_followed") is not False:
            reasons.append(f"target_destination_ledger[{index}].qr_navigation_followed must be false.")
    missing = sorted(REQUIRED_TARGETS - families)
    if missing:
        reasons.append(f"target_destination_ledger missing required targets: {missing}.")
    reasons.extend(_validate_evidence_ids([row for row in ledger if isinstance(row, dict)], "target_destination_ledger"))
    return reasons


def _validate_entry_surface_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("entry_surface_ledger")
    if not isinstance(ledger, list):
        return ["entry_surface_ledger must be a list."]
    reasons: list[str] = []
    surfaces: set[str] = set()
    for index, row in enumerate(ledger):
        if not isinstance(row, dict):
            reasons.append(f"entry_surface_ledger[{index}] must be an object.")
            continue
        surface = row.get("entry_surface")
        if isinstance(surface, str):
            surfaces.add(surface)
        else:
            reasons.append(f"entry_surface_ledger[{index}].entry_surface is required.")
        if row.get("coverage_status") not in ALLOWED_COVERAGE_STATUSES:
            reasons.append(f"entry_surface_ledger[{index}].coverage_status is not allowed.")
        if row.get("evidence_status") not in ALLOWED_EVIDENCE_STATUSES:
            reasons.append(f"entry_surface_ledger[{index}].evidence_status is not recognized.")
        if row.get("resulting_state") == "app_shell_loader_after_launcher_entry" and row.get("entered_expected_catalog") is not False:
            reasons.append(f"entry_surface_ledger[{index}].entered_expected_catalog must be false for app shell loader.")
    missing = sorted(REQUIRED_ENTRY_SURFACES - surfaces)
    if missing:
        reasons.append(f"entry_surface_ledger missing required surfaces: {missing}.")
    reasons.extend(_validate_evidence_ids([row for row in ledger if isinstance(row, dict)], "entry_surface_ledger"))
    return reasons


def _validate_state_detection_targets(report: dict[str, Any]) -> list[str]:
    targets = report.get("state_detection_targets")
    if not isinstance(targets, list):
        return ["state_detection_targets must be a list."]
    reasons: list[str] = []
    aliases: set[str] = set()
    for index, row in enumerate(targets):
        if not isinstance(row, dict):
            reasons.append(f"state_detection_targets[{index}] must be an object.")
            continue
        alias = row.get("state_alias")
        if isinstance(alias, str):
            aliases.add(alias)
        else:
            reasons.append(f"state_detection_targets[{index}].state_alias is required.")
        forbidden = set(row.get("must_not_classify_as", [])) if isinstance(row.get("must_not_classify_as"), list) else set()
        for required_forbidden in (
            "post_auth_games_catalog_top",
            "session_journal_empty",
            "steam_topup_qr",
            "feedback_qr",
            "covered_destination",
        ):
            if required_forbidden not in forbidden:
                reasons.append(f"state_detection_targets[{index}].must_not_classify_as missing {required_forbidden}.")
        if row.get("evidence_status") != "confirmed":
            reasons.append(f"state_detection_targets[{index}].evidence_status must be confirmed.")
        if alias == "app_shell_loader_after_launcher_entry" and row.get("timeout_policy_seconds") != 120:
            reasons.append(
                f"state_detection_targets[{index}].timeout_policy_seconds must be 120 for app shell loader."
            )
    missing = sorted(REQUIRED_STATE_ALIASES - aliases)
    if missing:
        reasons.append(f"state_detection_targets missing required aliases: {missing}.")
    reasons.extend(_validate_evidence_ids([row for row in targets if isinstance(row, dict)], "state_detection_targets"))
    return reasons


def _validate_anomalies(report: dict[str, Any]) -> list[str]:
    anomalies = report.get("anomaly_records")
    if not isinstance(anomalies, list):
        return ["anomaly_records must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(anomalies):
        if not isinstance(row, dict):
            reasons.append(f"anomaly_records[{index}] must be an object.")
            continue
        anomaly_id = row.get("anomaly_id")
        if isinstance(anomaly_id, str):
            seen.add(anomaly_id)
        else:
            reasons.append(f"anomaly_records[{index}].anomaly_id is required.")
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
            if not row.get(key):
                reasons.append(f"anomaly_records[{index}].{key} is required.")
        if row.get("evidence_status") != "confirmed":
            reasons.append(f"anomaly_records[{index}].evidence_status must be confirmed.")
    missing = sorted(REQUIRED_ANOMALIES - seen)
    if missing:
        reasons.append(f"anomaly_records missing required anomalies: {missing}.")
    reasons.extend(_validate_evidence_ids([row for row in anomalies if isinstance(row, dict)], "anomaly_records"))
    return reasons


def _validate_modality_audit(report: dict[str, Any]) -> list[str]:
    audit = report.get("checkpoint_modality_audit")
    if not isinstance(audit, dict):
        return ["checkpoint_modality_audit must be an object."]
    reasons: list[str] = []
    if not str(audit.get("screenshot_visual_inspection", "")).startswith("confirmed"):
        reasons.append("checkpoint_modality_audit.screenshot_visual_inspection must be confirmed.")
    if not str(audit.get("xml_capture", "")).startswith("confirmed"):
        reasons.append("checkpoint_modality_audit.xml_capture must be confirmed.")
    if audit.get("raw_artifacts_public") is not False:
        reasons.append("checkpoint_modality_audit.raw_artifacts_public must be false.")
    if audit.get("timeout_policy_seconds_for_app_shell_loader") != 120:
        reasons.append("checkpoint_modality_audit.timeout_policy_seconds_for_app_shell_loader must be 120.")
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
        "target_destination_ledger",
        "entry_surface_ledger",
        "state_detection_targets",
        "anomaly_records",
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
    if not isinstance(report.get("runtime_lane"), dict):
        reasons.append("runtime_lane must be an object.")
    elif report["runtime_lane"].get("lane_unchanged_from_task027r") is not True:
        reasons.append("runtime_lane.lane_unchanged_from_task027r must be true.")
    if not isinstance(report.get("source_reports"), list) or not report.get("source_reports"):
        reasons.append("source_reports must be a non-empty list.")
    if not isinstance(report.get("unverified_areas"), list):
        reasons.append("unverified_areas must be a list.")

    reasons.extend(_public_safety_findings(report))
    reasons.extend(_validate_public_safety(report))
    reasons.extend(_validate_coverage_claims(report))
    reasons.extend(_validate_target_destination_ledger(report))
    reasons.extend(_validate_entry_surface_ledger(report))
    reasons.extend(_validate_state_detection_targets(report))
    reasons.extend(_validate_anomalies(report))
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
    parser = argparse.ArgumentParser(description="Validate public-safe TASK-027S visual destination report JSON.")
    parser.add_argument("--report", type=Path, required=True, help="Path to a public-safe TASK-027S report JSON.")
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

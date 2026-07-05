"""TASK-025 selected-lane native regression no-device runner.

TASK-025A is intentionally no-device. The default runner creates a blocked
public-safe readiness report and does not call ADB, install APKs, launch the
app, read local secrets, or capture runtime evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


SCHEMA_VERSION = "task025-native-regression-summary-v1"
SUITE_SCHEMA_VERSION = "task025-native-regression-suite-v1"
TASK_ID = "TASK-025A"
MODE = "BOUNDED_AUTONOMOUS"
DEFAULT_SUITE = Path("docs/qa/native-regression/task025_selected_lane_native_regression_suite.json")
DEFAULT_TEMPLATE = Path("docs/qa/reports/task025_selected_lane_native_regression.summary.template.json")
PUBLIC_REPORT_ROOT = Path("docs/qa/reports")
NO_DEVICE_EXECUTION_MODE = "no_device_readiness"
SYNTHETIC_EXECUTION_MODE = "no_device_synthetic_contract_test"
PHYSICAL_RUNTIME_EXECUTION_MODE = "physical_selected_lane_runtime"

TARGET_ALIASES = {
    "device_alias": "tv-tpv-013",
    "runtime_profile_alias": "tv-tpv-a12-013",
    "build_alias": "task-005-local-apk-001",
    "synthetic_user_alias": "qa-user-phone-001",
}

REQUIRED_CASE_IDS = {f"NR-{index:03d}" for index in range(1, 11)}
BOUNDARY_SENSITIVE_CASE_IDS = {"NR-008", "NR-009"}

RUN_STATUSES = {"pass", "pass_with_known_anomalies", "partial", "blocked", "fail"}
RUNTIME_STATUSES = {"pass", "partial", "blocked", "not_run", "fail"}
PHYSICAL_DEVICE_STATUSES = {"available", "unavailable", "unknown"}
INSTALL_LAUNCH_STATUSES = {"pass", "blocked", "not_run", "fail"}
TASK025B_STATUSES = {"deferred", "blocked", "ready_after_refreshed_approval"}
TASK025B_PREFLIGHT_STATUSES = {"deferred_no_device", "blocked_missing_approval", "confirmed_for_task025b"}
CASE_STATUSES = {"pass", "fail", "blocked", "blocked_by_boundary", "not_run", "known_anomaly"}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
BOUNDARY_STATUSES = {"blocked_by_boundary", "not_run_out_of_scope", "blocked", "classified_not_entered"}
EXECUTION_MODES = {
    NO_DEVICE_EXECUTION_MODE,
    PHYSICAL_RUNTIME_EXECUTION_MODE,
    SYNTHETIC_EXECUTION_MODE,
}

FALSE_PUBLIC_SAFETY_FLAGS = {
    "raw_phone_otp_public",
    "raw_device_identifiers_public",
    "raw_screenshots_public",
    "raw_xml_public",
    "raw_logs_public",
    "raw_runtime_evidence_public",
    "payment_webview_stream_entered",
    "profile_account_mutation_entered",
    "adb_runtime_invoked",
    "apk_install_invoked",
    "app_launch_invoked",
}

FALSE_COVERAGE_CLAIMS = {
    "exhaustive_app_navigation",
    "complete_dynamic_value_inventory",
    "payment_or_stream_covered",
    "webview_covered",
    "broad_compatibility_covered",
}

FORBIDDEN_BOUNDARY_CATEGORIES = (
    "payment/subscription/purchase",
    "WebView/browser/external QR traversal",
    "stream/WebRTC/media playback/game session start",
    "Steam/account connection",
    "profile/account mutation",
    "network/offline manipulation",
)

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


class RuntimeDriver(Protocol):
    """Future physical runtime boundary. TASK-025A uses only synthetic fakes."""

    def launch_app(self) -> None: ...

    def ensure_authorized_session(self) -> None: ...

    def classify_screen(self) -> str: ...

    def classify_boundary(self) -> str: ...

    def press_dpad(self, direction: str) -> None: ...

    def press_ok(self) -> None: ...

    def press_back(self) -> None: ...

    def press_home(self) -> None: ...

    def foreground_app(self) -> None: ...

    def force_stop_relaunch(self) -> None: ...

    def assert_focus_present(self) -> None: ...

    def assert_session_preserved(self) -> None: ...

    def record_public_safe_evidence_ref(self, category: str) -> str: ...


@dataclass
class SyntheticRuntimeDriver:
    """In-memory fake used by unit tests only; it never creates runtime evidence."""

    screens: list[str] = field(default_factory=lambda: ["post_auth_catalog_root"])
    boundary_category: str = "payment/subscription/purchase"
    action_log: list[str] = field(default_factory=list)

    def _record(self, action: str) -> None:
        self.action_log.append(action)

    def launch_app(self) -> None:
        self._record("launch_app")

    def ensure_authorized_session(self) -> None:
        self._record("ensure_authorized_session")

    def classify_screen(self) -> str:
        self._record("classify_screen")
        return self.screens[-1]

    def classify_boundary(self) -> str:
        self._record("classify_boundary")
        return self.boundary_category

    def press_dpad(self, direction: str) -> None:
        self._record(f"press_dpad:{direction}")

    def press_ok(self) -> None:
        self._record("press_ok")

    def press_back(self) -> None:
        self._record("press_back")

    def press_home(self) -> None:
        self._record("press_home")

    def foreground_app(self) -> None:
        self._record("foreground_app")

    def force_stop_relaunch(self) -> None:
        self._record("force_stop_relaunch")

    def assert_focus_present(self) -> None:
        self._record("assert_focus_present")

    def assert_session_preserved(self) -> None:
        self._record("assert_session_preserved")

    def record_public_safe_evidence_ref(self, category: str) -> str:
        self._record(f"record_public_safe_evidence_ref:{category}")
        return f"synthetic-only:{category}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def public_safety_findings(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(public_safety_findings(child, f"{path}.{key}"))
        return findings
    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(public_safety_findings(child, f"{path}[{index}]"))
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


def default_blocked_report(reason: str = "physical device unavailable; runtime deferred") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "task_id": TASK_ID,
        "mode": MODE,
        "execution_mode": NO_DEVICE_EXECUTION_MODE,
        "run_status": "blocked",
        "overall_status": "blocked",
        "runtime_execution_status": "not_run",
        "physical_device_available": False,
        "physical_device_status": "unavailable",
        "apk_install_status": "not_run",
        "app_launch_status": "not_run",
        "task025b_runtime_status": "deferred",
        "runtime_lane": TARGET_ALIASES,
        "selected_lane": TARGET_ALIASES,
        "blocked_reasons": [reason],
        "runtime_evidence_ids": [],
        "task025b_preflight": {
            "preflight_status": "deferred_no_device",
            "physical_device_available": False,
            "refreshed_owner_approvals": False,
            "selected_device_authorized": False,
            "apk_presence_confirmed": False,
            "apk_hash_recorded_local_only": False,
            "synthetic_user_env_confirmed": False,
            "evidence_capture_approval": False,
            "cleanup_policy_confirmed": False,
            "runtime_evidence_required_for_pass": True,
        },
        "phase_gates": {
            "phase_a_no_device_readiness": "pass",
            "phase_b_schema_validator": "pass",
            "phase_c_runtime": "not_run",
        },
        "regression_cases": [
            {
                "case_id": case_id,
                "status": "not_run",
                "evidence_status": "unknown",
                "execution_mode": NO_DEVICE_EXECUTION_MODE,
                "counts_as_runtime_evidence": False,
                "reason": reason,
            }
            for case_id in sorted(REQUIRED_CASE_IDS)
        ],
        "synthetic_contract_tests": [],
        "session_persistence_checkpoints": [],
        "boundary_ledger": [],
        "known_anomalies_rechecked": [],
        "new_anomalies": [],
        "public_safety": {
            "raw_phone_otp_public": False,
            "raw_device_identifiers_public": False,
            "raw_screenshots_public": False,
            "raw_xml_public": False,
            "raw_logs_public": False,
            "raw_runtime_evidence_public": False,
            "payment_webview_stream_entered": False,
            "profile_account_mutation_entered": False,
            "adb_runtime_invoked": False,
            "apk_install_invoked": False,
            "app_launch_invoked": False,
        },
        "coverage_claims": {
            "exhaustive_app_navigation": False,
            "complete_dynamic_value_inventory": False,
            "payment_or_stream_covered": False,
            "webview_covered": False,
            "broad_compatibility_covered": False,
            "selected_lane_native_regression_only": True,
            "fake_synthetic_tests_are_runtime_evidence": False,
            "synthetic_contract_tests_are_runtime_evidence": False,
        },
        "dynamic_data_policy": {
            "assert_fixed_game_titles": False,
            "assert_fixed_server_rows": False,
            "assert_fixed_prices": False,
            "assert_raw_qr_targets": False,
        },
        "boundary_guard_categories": list(FORBIDDEN_BOUNDARY_CATEGORIES),
    }


def synthetic_contract_report(driver: RuntimeDriver) -> dict[str, Any]:
    driver.launch_app()
    driver.ensure_authorized_session()
    screen = driver.classify_screen()
    driver.assert_focus_present()
    driver.press_dpad("down")
    driver.press_back()
    driver.press_home()
    driver.foreground_app()
    driver.assert_session_preserved()
    driver.force_stop_relaunch()
    boundary = driver.classify_boundary()
    synthetic_ref = driver.record_public_safe_evidence_ref("contract-only")
    report = default_blocked_report("synthetic contract test only; physical runtime not executed")
    report["execution_mode"] = SYNTHETIC_EXECUTION_MODE
    report["synthetic_contract"] = {
        "contract_status": "pass",
        "screen_alias": screen,
        "boundary_category": boundary,
        "synthetic_ref": synthetic_ref,
        "counts_as_runtime_evidence": False,
    }
    report["synthetic_contract_tests"] = [
        {
            "contract_id": "SYN-001",
            "title": "selected-lane no-device contract",
            "status": "pass",
            "evidence_status": "confirmed",
            "execution_mode": SYNTHETIC_EXECUTION_MODE,
            "counts_as_runtime_evidence": False,
            "runtime_evidence_ids": [],
            "reason": "In-memory fake contract only; no app/device/APK runtime evidence was produced.",
        }
    ]
    return report


def build_report(*, include_synthetic_contract_tests: bool = False) -> dict[str, Any]:
    if include_synthetic_contract_tests:
        return synthetic_contract_report(SyntheticRuntimeDriver())
    return default_blocked_report()


def validate_output_path(path: str | Path) -> bool:
    normalized = Path(path)
    if normalized.is_absolute() or ".." in normalized.parts:
        return False
    expected_parts = ("docs", "qa", "reports")
    if normalized.parts[: len(expected_parts)] != expected_parts:
        return False
    return normalized.suffix == ".json"


def validate_public_output_path(path: str | Path) -> bool:
    return validate_output_path(path)


def load_json_object(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return None, [f"{path.as_posix()} was not found."]
    except json.JSONDecodeError as exc:
        return None, [f"{path.as_posix()} is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return None, [f"{path.as_posix()} must contain a JSON object."]
    return loaded, []


def validate_suite(suite: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if suite.get("schema_version") != SUITE_SCHEMA_VERSION:
        reasons.append(f"suite.schema_version must be {SUITE_SCHEMA_VERSION}.")
    if suite.get("task_id") != "TASK-025":
        reasons.append("suite.task_id must be TASK-025.")
    if suite.get("runtime_lane") != TARGET_ALIASES:
        reasons.append("suite.runtime_lane must match the selected TASK-025 lane aliases.")
    if suite.get("runtime_execution_status") != "not_run":
        reasons.append("suite.runtime_execution_status must be not_run for TASK-025A.")
    policy = suite.get("dynamic_data_policy")
    if not isinstance(policy, dict):
        reasons.append("suite.dynamic_data_policy must be an object.")
    else:
        for key in ("assert_fixed_game_titles", "assert_fixed_server_rows", "assert_fixed_prices", "assert_raw_qr_targets"):
            if policy.get(key) is not False:
                reasons.append(f"suite.dynamic_data_policy.{key} must be false.")
    cases = suite.get("cases")
    if not isinstance(cases, list):
        return sorted(set(reasons + ["suite.cases must be a list."]))
    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            reasons.append(f"suite.cases[{index}] must be an object.")
            continue
        case_id = case.get("case_id")
        if case_id in seen:
            reasons.append(f"suite.cases[{index}].case_id is duplicated.")
        if not isinstance(case_id, str) or case_id not in REQUIRED_CASE_IDS:
            reasons.append(f"suite.cases[{index}].case_id is not recognized.")
        else:
            seen.add(case_id)
        if not isinstance(case.get("title"), str) or not case["title"].strip():
            reasons.append(f"suite.cases[{index}].title is required.")
        if case_id in BOUNDARY_SENSITIVE_CASE_IDS and case.get("boundary_sensitive") is not True:
            reasons.append(f"suite.cases[{index}].boundary_sensitive must be true.")
    missing = sorted(REQUIRED_CASE_IDS - seen)
    if missing:
        reasons.append(f"suite is missing required cases: {missing}.")
    return sorted(set(reasons))


def validate_report_shape(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    required = (
        "schema_version",
        "task_id",
        "execution_mode",
        "run_status",
        "overall_status",
        "runtime_execution_status",
        "physical_device_available",
        "physical_device_status",
        "apk_install_status",
        "app_launch_status",
        "task025b_runtime_status",
        "runtime_evidence_ids",
        "runtime_lane",
        "task025b_preflight",
        "phase_gates",
        "regression_cases",
        "session_persistence_checkpoints",
        "boundary_ledger",
        "known_anomalies_rechecked",
        "new_anomalies",
        "public_safety",
        "coverage_claims",
        "dynamic_data_policy",
        "boundary_guard_categories",
    )
    for field_name in required:
        if field_name not in report:
            reasons.append(f"{field_name} is required.")
    if report.get("schema_version") != SCHEMA_VERSION:
        reasons.append(f"schema_version must be {SCHEMA_VERSION}.")
    if report.get("task_id") not in {"TASK-025", "TASK-025A"}:
        reasons.append("task_id must be TASK-025 or TASK-025A.")
    if report.get("execution_mode") not in EXECUTION_MODES:
        reasons.append("execution_mode must be recognized.")
    if report.get("runtime_lane") != TARGET_ALIASES:
        reasons.append("runtime_lane must match the selected TASK-025 lane aliases.")
    if report.get("selected_lane") is not None and report.get("selected_lane") != TARGET_ALIASES:
        reasons.append("selected_lane must match the selected TASK-025 lane aliases.")
    if report.get("run_status") not in RUN_STATUSES:
        reasons.append("run_status must be recognized.")
    if report.get("overall_status") not in RUN_STATUSES:
        reasons.append("overall_status must be recognized.")
    if report.get("runtime_execution_status") not in RUNTIME_STATUSES:
        reasons.append("runtime_execution_status must be recognized.")
    if not isinstance(report.get("physical_device_available"), bool):
        reasons.append("physical_device_available must be boolean.")
    if report.get("physical_device_status") not in PHYSICAL_DEVICE_STATUSES:
        reasons.append("physical_device_status must be recognized.")
    if report.get("apk_install_status") not in INSTALL_LAUNCH_STATUSES:
        reasons.append("apk_install_status must be recognized.")
    if report.get("app_launch_status") not in INSTALL_LAUNCH_STATUSES:
        reasons.append("app_launch_status must be recognized.")
    if report.get("task025b_runtime_status") not in TASK025B_STATUSES:
        reasons.append("task025b_runtime_status must be recognized.")
    if not isinstance(report.get("runtime_evidence_ids"), list):
        reasons.append("runtime_evidence_ids must be a list.")

    reasons.extend(public_safety_findings(report))
    reasons.extend(_validate_no_device_contract(report))
    reasons.extend(_validate_task025b_preflight(report))
    reasons.extend(_validate_phase_gates(report))
    reasons.extend(_validate_regression_cases(report))
    reasons.extend(_validate_synthetic_contract_section(report))
    reasons.extend(_validate_synthetic_contract_tests(report.get("synthetic_contract_tests", [])))
    reasons.extend(_validate_session_checkpoints(report))
    reasons.extend(_validate_boundary_ledger(report))
    reasons.extend(_validate_anomaly_list(report.get("known_anomalies_rechecked"), "known_anomalies_rechecked"))
    reasons.extend(_validate_anomaly_list(report.get("new_anomalies"), "new_anomalies"))
    reasons.extend(_validate_public_safety(report.get("public_safety")))
    reasons.extend(_validate_coverage_claims(report.get("coverage_claims")))
    reasons.extend(_validate_dynamic_data_policy(report.get("dynamic_data_policy")))
    reasons.extend(_validate_boundary_guard_categories(report.get("boundary_guard_categories")))
    reasons.extend(_validate_evidence_id_uniqueness(report))
    return sorted(set(reasons))


def _has_runtime_evidence_claim(report: dict[str, Any]) -> bool:
    if report.get("run_status") in {"pass", "pass_with_known_anomalies"}:
        return True
    if report.get("runtime_execution_status") in {"pass", "partial"}:
        return True
    cases = report.get("regression_cases")
    if isinstance(cases, list) and any(isinstance(case, dict) and case.get("status") == "pass" for case in cases):
        return True
    return False


def _validate_no_device_contract(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    task025a = report.get("task_id") == "TASK-025A"
    no_device = report.get("physical_device_available") is False
    synthetic = report.get("execution_mode") == SYNTHETIC_EXECUTION_MODE
    if task025a and report.get("execution_mode") not in {NO_DEVICE_EXECUTION_MODE, SYNTHETIC_EXECUTION_MODE}:
        reasons.append("TASK-025A reports must use no-device or synthetic contract execution mode.")
    if task025a or no_device:
        expected = {
            "run_status": "blocked",
            "overall_status": "blocked",
            "runtime_execution_status": "not_run",
            "physical_device_available": False,
            "physical_device_status": "unavailable",
            "apk_install_status": "not_run",
            "app_launch_status": "not_run",
            "task025b_runtime_status": "deferred",
        }
        for key, value in expected.items():
            if report.get(key) != value:
                suffix = " for TASK-025A reports." if task025a else " when physical_device_available=false."
                reasons.append(f"{key} must be {value}{suffix}")
        if report.get("runtime_evidence_ids") != []:
            reasons.append("runtime_evidence_ids must be empty for no-device readiness reports.")
    if report.get("runtime_execution_status") == "not_run" or report.get("run_status") == "blocked":
        if report.get("runtime_evidence_ids") != []:
            reasons.append("runtime_evidence_ids must be empty when runtime is not run or report is blocked.")
    if synthetic and report.get("runtime_execution_status") != "not_run":
        reasons.append("synthetic contract tests must keep runtime_execution_status=not_run.")
    if synthetic and report.get("run_status") in {"pass", "pass_with_known_anomalies"}:
        reasons.append("synthetic contract tests must not produce runtime pass reports.")
    if _has_runtime_evidence_claim(report):
        if report.get("execution_mode") != PHYSICAL_RUNTIME_EXECUTION_MODE:
            reasons.append("runtime evidence claims require execution_mode=physical_selected_lane_runtime.")
        if report.get("physical_device_available") is not True:
            reasons.append("runtime evidence claims require physical_device_available=true.")
        if report.get("physical_device_status") != "available":
            reasons.append("runtime evidence claims require physical_device_status=available.")
        if report.get("runtime_execution_status") not in {"pass", "partial"}:
            reasons.append("runtime evidence claims require runtime_execution_status=pass or partial.")
        if report.get("apk_install_status") != "pass":
            reasons.append("runtime evidence claims require apk_install_status=pass.")
        if report.get("app_launch_status") != "pass":
            reasons.append("runtime evidence claims require app_launch_status=pass.")
        if report.get("task025b_runtime_status") != "ready_after_refreshed_approval":
            reasons.append("runtime evidence claims require task025b_runtime_status=ready_after_refreshed_approval.")
        if not report.get("runtime_evidence_ids"):
            reasons.append("runtime evidence claims require non-empty runtime_evidence_ids.")
    return reasons


def _validate_task025b_preflight(report: dict[str, Any]) -> list[str]:
    preflight = report.get("task025b_preflight")
    if not isinstance(preflight, dict):
        return ["task025b_preflight must be an object."]
    reasons: list[str] = []
    status = preflight.get("preflight_status")
    if status not in TASK025B_PREFLIGHT_STATUSES:
        reasons.append("task025b_preflight.preflight_status must be recognized.")
    boolean_fields = (
        "physical_device_available",
        "refreshed_owner_approvals",
        "selected_device_authorized",
        "apk_presence_confirmed",
        "apk_hash_recorded_local_only",
        "synthetic_user_env_confirmed",
        "evidence_capture_approval",
        "cleanup_policy_confirmed",
        "runtime_evidence_required_for_pass",
    )
    for key in boolean_fields:
        if not isinstance(preflight.get(key), bool):
            reasons.append(f"task025b_preflight.{key} must be boolean.")

    no_device = report.get("physical_device_available") is False or report.get("task_id") == "TASK-025A"
    if no_device or report.get("execution_mode") == SYNTHETIC_EXECUTION_MODE:
        expected_false = (
            "physical_device_available",
            "refreshed_owner_approvals",
            "selected_device_authorized",
            "apk_presence_confirmed",
            "apk_hash_recorded_local_only",
            "synthetic_user_env_confirmed",
            "evidence_capture_approval",
            "cleanup_policy_confirmed",
        )
        for key in expected_false:
            if preflight.get(key) is not False:
                reasons.append(f"task025b_preflight.{key} must be false for no-device readiness reports.")
        if status != "deferred_no_device":
            reasons.append("task025b_preflight.preflight_status must be deferred_no_device for no-device readiness reports.")

    if _has_runtime_evidence_claim(report):
        required_true = (
            "physical_device_available",
            "refreshed_owner_approvals",
            "selected_device_authorized",
            "apk_presence_confirmed",
            "apk_hash_recorded_local_only",
            "synthetic_user_env_confirmed",
            "evidence_capture_approval",
            "cleanup_policy_confirmed",
            "runtime_evidence_required_for_pass",
        )
        for key in required_true:
            if preflight.get(key) is not True:
                reasons.append(f"runtime evidence claims require task025b_preflight.{key}=true.")
        if status != "confirmed_for_task025b":
            reasons.append("runtime evidence claims require task025b_preflight.preflight_status=confirmed_for_task025b.")
    return reasons


def _validate_phase_gates(report: dict[str, Any]) -> list[str]:
    gates = report.get("phase_gates")
    if not isinstance(gates, dict):
        return ["phase_gates must be an object."]
    reasons: list[str] = []
    if gates.get("phase_c_runtime") == "pass" and report.get("runtime_execution_status") != "pass":
        reasons.append("phase_gates.phase_c_runtime=pass requires runtime_execution_status=pass.")
    if report.get("runtime_execution_status") == "not_run" and gates.get("phase_c_runtime") not in {"not_run", "blocked"}:
        reasons.append("phase_gates.phase_c_runtime must be not_run or blocked when runtime_execution_status=not_run.")
    if _has_runtime_evidence_claim(report) and gates.get("phase_c_runtime") != "pass":
        reasons.append("runtime evidence claims require phase_gates.phase_c_runtime=pass.")
    return reasons


def _validate_regression_cases(report: dict[str, Any]) -> list[str]:
    cases = report.get("regression_cases")
    if not isinstance(cases, list):
        return ["regression_cases must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    boundary_ledger = report.get("boundary_ledger")
    has_boundary_evidence = isinstance(boundary_ledger, list) and bool(boundary_ledger)
    boundary_ids = {
        boundary.get("boundary_id")
        for boundary in boundary_ledger
        if isinstance(boundary, dict) and isinstance(boundary.get("boundary_id"), str)
    }
    run_status = report.get("run_status")
    no_device = report.get("physical_device_available") is False
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            reasons.append(f"regression_cases[{index}] must be an object.")
            continue
        case_id = case.get("case_id")
        if case_id in seen:
            reasons.append(f"regression_cases[{index}].case_id is duplicated.")
        if case_id in REQUIRED_CASE_IDS:
            seen.add(case_id)
        else:
            reasons.append(f"regression_cases[{index}].case_id is not recognized.")
        status = case.get("status")
        if status not in CASE_STATUSES:
            reasons.append(f"regression_cases[{index}].status is not recognized.")
        if case.get("evidence_status") not in EVIDENCE_STATUSES:
            reasons.append(f"regression_cases[{index}].evidence_status is not recognized.")
        if no_device and status not in {"not_run", "blocked"}:
            reasons.append(f"regression_cases[{index}].status must be not_run or blocked for no-device reports.")
        if status == "pass":
            if case.get("execution_mode") != PHYSICAL_RUNTIME_EXECUTION_MODE:
                reasons.append(f"regression_cases[{index}].execution_mode must be physical_selected_lane_runtime for pass.")
            if case.get("counts_as_runtime_evidence") is not True:
                reasons.append(f"regression_cases[{index}].counts_as_runtime_evidence must be true for pass.")
            if case.get("execution_mode") == NO_DEVICE_EXECUTION_MODE:
                reasons.append(f"regression_cases[{index}] no-device execution cannot pass a runtime regression case.")
            if case.get("execution_mode") == SYNTHETIC_EXECUTION_MODE:
                reasons.append(f"regression_cases[{index}] synthetic contract pass cannot count as runtime regression pass.")
            if case.get("evidence_status") != "confirmed":
                reasons.append(f"regression_cases[{index}].evidence_status must be confirmed for pass.")
            if not case.get("evidence_ids"):
                reasons.append(f"regression_cases[{index}].evidence_ids are required for pass.")
            if case_id in BOUNDARY_SENSITIVE_CASE_IDS and not has_boundary_evidence:
                reasons.append(f"regression_cases[{index}] {case_id} pass requires confirmed boundary_ledger evidence.")
            if case_id in BOUNDARY_SENSITIVE_CASE_IDS:
                linked_boundary_ids = case.get("boundary_ids")
                if not isinstance(linked_boundary_ids, list) or not linked_boundary_ids:
                    reasons.append(f"regression_cases[{index}] {case_id} pass requires boundary_ids linked to boundary_ledger.")
                elif not all(isinstance(boundary_id, str) and boundary_id in boundary_ids for boundary_id in linked_boundary_ids):
                    reasons.append(f"regression_cases[{index}] {case_id} boundary_ids must reference boundary_ledger entries.")
        if case_id in BOUNDARY_SENSITIVE_CASE_IDS and status == "pass" and case.get("boundary_evidence_confirmed") is not True:
            reasons.append(f"regression_cases[{index}] {case_id} pass requires boundary_evidence_confirmed=true.")
        if status in {"blocked", "blocked_by_boundary", "not_run", "fail", "known_anomaly"} and not case.get("reason"):
            reasons.append(f"regression_cases[{index}].reason is required for {status}.")
        if case.get("boundary_entered") is True:
            reasons.append(f"regression_cases[{index}].boundary_entered must not be true.")
        if run_status in {"pass", "pass_with_known_anomalies"} and status in {"blocked", "blocked_by_boundary", "not_run", "fail"}:
            reasons.append(f"run_status={run_status} cannot include regression_cases[{index}].status={status}.")
        if run_status == "pass" and status == "known_anomaly":
            reasons.append(f"run_status=pass cannot include regression_cases[{index}].status=known_anomaly.")
    missing = sorted(REQUIRED_CASE_IDS - seen)
    if missing:
        reasons.append(f"regression_cases missing required cases: {missing}.")
    return reasons


def _validate_synthetic_contract_tests(tests: Any) -> list[str]:
    if not isinstance(tests, list):
        return ["synthetic_contract_tests must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    for index, test in enumerate(tests):
        if not isinstance(test, dict):
            reasons.append(f"synthetic_contract_tests[{index}] must be an object.")
            continue
        contract_id = test.get("contract_id")
        if not isinstance(contract_id, str) or not contract_id.strip():
            reasons.append(f"synthetic_contract_tests[{index}].contract_id is required.")
        elif contract_id in seen:
            reasons.append(f"synthetic_contract_tests[{index}].contract_id is duplicated.")
        else:
            seen.add(contract_id)
        if test.get("execution_mode") != SYNTHETIC_EXECUTION_MODE:
            reasons.append(f"synthetic_contract_tests[{index}].execution_mode must be {SYNTHETIC_EXECUTION_MODE}.")
        if test.get("counts_as_runtime_evidence") is not False:
            reasons.append(f"synthetic_contract_tests[{index}].counts_as_runtime_evidence must be false.")
        if test.get("runtime_evidence_ids") not in ([], None):
            reasons.append(f"synthetic_contract_tests[{index}].runtime_evidence_ids must be empty.")
        if test.get("status") not in CASE_STATUSES:
            reasons.append(f"synthetic_contract_tests[{index}].status is not recognized.")
        if test.get("evidence_status") not in EVIDENCE_STATUSES:
            reasons.append(f"synthetic_contract_tests[{index}].evidence_status is not recognized.")
    return reasons


def _validate_synthetic_contract_section(report: dict[str, Any]) -> list[str]:
    section = report.get("synthetic_contract")
    if report.get("execution_mode") != SYNTHETIC_EXECUTION_MODE:
        return []
    if not isinstance(section, dict):
        return ["synthetic_contract must be an object for synthetic contract execution."]
    reasons: list[str] = []
    if section.get("contract_status") not in CASE_STATUSES:
        reasons.append("synthetic_contract.contract_status must be recognized.")
    if not isinstance(section.get("screen_alias"), str) or not section.get("screen_alias", "").strip():
        reasons.append("synthetic_contract.screen_alias is required.")
    if section.get("boundary_category") not in FORBIDDEN_BOUNDARY_CATEGORIES:
        reasons.append("synthetic_contract.boundary_category must be a guarded boundary category.")
    if not isinstance(section.get("synthetic_ref"), str) or not section.get("synthetic_ref", "").startswith("synthetic-only:"):
        reasons.append("synthetic_contract.synthetic_ref must be a synthetic-only reference.")
    if section.get("counts_as_runtime_evidence") is not False:
        reasons.append("synthetic_contract.counts_as_runtime_evidence must be false.")
    return reasons


def _validate_session_checkpoints(report: dict[str, Any]) -> list[str]:
    checkpoints = report.get("session_persistence_checkpoints")
    if not isinstance(checkpoints, list):
        return ["session_persistence_checkpoints must be a list."]
    reasons: list[str] = []
    if report.get("run_status") in {"pass", "pass_with_known_anomalies"} and not checkpoints:
        reasons.append("runtime pass requires non-empty session_persistence_checkpoints.")
    seen: set[str] = set()
    for index, checkpoint in enumerate(checkpoints):
        if not isinstance(checkpoint, dict):
            reasons.append(f"session_persistence_checkpoints[{index}] must be an object.")
            continue
        checkpoint_id = checkpoint.get("checkpoint_id")
        if not isinstance(checkpoint_id, str) or not checkpoint_id.strip():
            reasons.append(f"session_persistence_checkpoints[{index}].checkpoint_id is required.")
        elif checkpoint_id in seen:
            reasons.append(f"session_persistence_checkpoints[{index}].checkpoint_id is duplicated.")
        else:
            seen.add(checkpoint_id)
        status = checkpoint.get("status")
        if status not in CASE_STATUSES:
            reasons.append(f"session_persistence_checkpoints[{index}].status is not recognized.")
        if checkpoint.get("evidence_status") not in EVIDENCE_STATUSES:
            reasons.append(f"session_persistence_checkpoints[{index}].evidence_status is not recognized.")
        if status == "pass":
            if checkpoint.get("evidence_status") != "confirmed":
                reasons.append(f"session_persistence_checkpoints[{index}].evidence_status must be confirmed for pass.")
            if not checkpoint.get("evidence_ids"):
                reasons.append(f"session_persistence_checkpoints[{index}].evidence_ids are required for pass.")
        if status in {"blocked", "blocked_by_boundary", "not_run", "fail", "known_anomaly"} and not checkpoint.get("reason"):
            reasons.append(f"session_persistence_checkpoints[{index}].reason is required for {status}.")
    return reasons


def _validate_boundary_ledger(report: dict[str, Any]) -> list[str]:
    boundaries = report.get("boundary_ledger")
    if not isinstance(boundaries, list):
        return ["boundary_ledger must be a list."]
    reasons: list[str] = []
    if report.get("run_status") in {"pass", "pass_with_known_anomalies"}:
        case_statuses = {
            case.get("case_id"): case.get("status")
            for case in report.get("regression_cases", [])
            if isinstance(case, dict)
        }
        if any(case_statuses.get(case_id) == "pass" for case_id in BOUNDARY_SENSITIVE_CASE_IDS) and not boundaries:
            reasons.append("boundary-sensitive runtime pass requires non-empty boundary_ledger.")
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
        if boundary.get("status") not in BOUNDARY_STATUSES:
            reasons.append(f"boundary_ledger[{index}].status must be a boundary-safe terminal status.")
        if boundary.get("boundary_category") not in FORBIDDEN_BOUNDARY_CATEGORIES:
            reasons.append(f"boundary_ledger[{index}].boundary_category must be a guarded boundary category.")
        if boundary.get("evidence_status") != "confirmed":
            reasons.append(f"boundary_ledger[{index}].evidence_status must be confirmed.")
        if boundary.get("entered") is not False:
            reasons.append(f"boundary_ledger[{index}].entered must be false.")
        if boundary.get("navigation_followed") not in (None, False):
            reasons.append(f"boundary_ledger[{index}].navigation_followed must be false when present.")
        if boundary.get("external_action") == "performed":
            reasons.append(f"boundary_ledger[{index}].external_action must not be performed.")
        if boundary.get("result") == "pass":
            reasons.append(f"boundary_ledger[{index}].result must not be pass.")
        if not boundary.get("evidence_ids"):
            reasons.append(f"boundary_ledger[{index}].evidence_ids are required.")
    return reasons


def _validate_anomaly_list(items: Any, field_name: str) -> list[str]:
    if not isinstance(items, list):
        return [f"{field_name} must be a list."]
    reasons: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            reasons.append(f"{field_name}[{index}] must be an object.")
            continue
        required = ("anomaly_id", "category", "status", "evidence_status")
        if field_name == "new_anomalies":
            required = ("anomaly_id", "category", "severity", "evidence_status")
        for key in required:
            if not item.get(key):
                reasons.append(f"{field_name}[{index}].{key} is required.")
        if item.get("evidence_status") not in EVIDENCE_STATUSES:
            reasons.append(f"{field_name}[{index}].evidence_status is not recognized.")
        for key in ("trigger_action", "expected_result", "observed_result", "test_design_implication"):
            if not item.get(key):
                reasons.append(f"{field_name}[{index}].{key} is required.")
    return reasons


def _validate_public_safety(flags: Any) -> list[str]:
    if not isinstance(flags, dict):
        return ["public_safety must be an object."]
    reasons: list[str] = []
    for key in FALSE_PUBLIC_SAFETY_FLAGS:
        if flags.get(key) is not False:
            reasons.append(f"public_safety.{key} must be false.")
    return reasons


def _validate_coverage_claims(claims: Any) -> list[str]:
    if not isinstance(claims, dict):
        return ["coverage_claims must be an object."]
    reasons: list[str] = []
    for key in FALSE_COVERAGE_CLAIMS:
        if claims.get(key) is not False:
            reasons.append(f"coverage_claims.{key} must be false.")
    if claims.get("selected_lane_native_regression_only") is not True:
        reasons.append("coverage_claims.selected_lane_native_regression_only must be true.")
    if claims.get("fake_synthetic_tests_are_runtime_evidence") is not False:
        reasons.append("coverage_claims.fake_synthetic_tests_are_runtime_evidence must be false.")
    if "synthetic_contract_tests_are_runtime_evidence" in claims and claims.get("synthetic_contract_tests_are_runtime_evidence") is not False:
        reasons.append("coverage_claims.synthetic_contract_tests_are_runtime_evidence must be false.")
    return reasons


def _validate_dynamic_data_policy(policy: Any) -> list[str]:
    if not isinstance(policy, dict):
        return ["dynamic_data_policy must be an object."]
    reasons: list[str] = []
    for key in ("assert_fixed_game_titles", "assert_fixed_server_rows", "assert_fixed_prices", "assert_raw_qr_targets"):
        if policy.get(key) is not False:
            reasons.append(f"dynamic_data_policy.{key} must be false.")
    return reasons


def _validate_boundary_guard_categories(categories: Any) -> list[str]:
    if not isinstance(categories, list):
        return ["boundary_guard_categories must be a list."]
    if categories != list(FORBIDDEN_BOUNDARY_CATEGORIES):
        return ["boundary_guard_categories must match the TASK-025 forbidden boundary category allowlist."]
    return []


def _evidence_ids_from(items: Any, prefix: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if not isinstance(items, list):
        return found
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        evidence_ids = item.get("evidence_ids")
        if evidence_ids is None:
            continue
        if not isinstance(evidence_ids, list):
            found.append((f"{prefix}[{index}].evidence_ids", "<non-list>"))
            continue
        seen_local: set[str] = set()
        for evidence_id in evidence_ids:
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                found.append((f"{prefix}[{index}].evidence_ids", "<invalid>"))
                continue
            if evidence_id in seen_local:
                found.append((f"{prefix}[{index}].evidence_ids", f"<duplicate-local:{evidence_id}>"))
            seen_local.add(evidence_id)
            found.append((f"{prefix}[{index}].evidence_ids", evidence_id))
    return found


def _validate_evidence_id_uniqueness(report: dict[str, Any]) -> list[str]:
    entries: list[tuple[str, str]] = []
    entries.extend(_evidence_ids_from([{"evidence_ids": report.get("runtime_evidence_ids")}], "runtime_evidence_ids"))
    entries.extend(_evidence_ids_from(report.get("regression_cases"), "regression_cases"))
    entries.extend(_evidence_ids_from(report.get("session_persistence_checkpoints"), "session_persistence_checkpoints"))
    entries.extend(_evidence_ids_from(report.get("boundary_ledger"), "boundary_ledger"))
    reasons: list[str] = []
    seen: dict[str, str] = {}
    for location, evidence_id in entries:
        if evidence_id == "<non-list>":
            reasons.append(f"{location} must be a list.")
            continue
        if evidence_id == "<invalid>":
            reasons.append(f"{location} contains an invalid evidence id.")
            continue
        if evidence_id.startswith("<duplicate-local:"):
            reasons.append(f"{location} contains a duplicate evidence id.")
            continue
        if evidence_id in seen:
            reasons.append(f"evidence id is duplicated across report ledgers: {evidence_id}.")
        else:
            seen[evidence_id] = location
    return reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TASK-025A selected-lane native regression no-device readiness gate.")
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE, help="TASK-025 suite definition JSON.")
    parser.add_argument("--public-output", type=Path, default=None, help="Optional public summary path under docs/qa/reports/*.json.")
    parser.add_argument(
        "--synthetic-contract-test",
        action="store_true",
        help="Use in-memory fake driver for contract tests only; still reports runtime not_run.",
    )
    parser.add_argument(
        "--include-synthetic-contract-tests",
        action="store_true",
        help="Alias for --synthetic-contract-test; synthetic checks remain non-runtime evidence.",
    )
    args = parser.parse_args(argv)

    suite, suite_load_errors = load_json_object(args.suite)
    suite_errors = suite_load_errors if suite is None else validate_suite(suite)
    public_output_valid = args.public_output is None or validate_output_path(args.public_output)

    if not public_output_valid:
        report = default_blocked_report("public output path must stay under docs/qa/reports/*.json")
    elif suite_errors:
        report = default_blocked_report("; ".join(suite_errors))
    elif args.synthetic_contract_test or args.include_synthetic_contract_tests:
        report = synthetic_contract_report(SyntheticRuntimeDriver())
    else:
        report = default_blocked_report()

    if args.public_output is not None and public_output_valid:
        args.public_output.parent.mkdir(parents=True, exist_ok=True)
        args.public_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

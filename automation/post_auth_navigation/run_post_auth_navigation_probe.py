"""Generate or validate TASK-020 post-auth navigation probe reports.

Default execution is intentionally fail-closed and performs no ADB, Android,
APK, network or production interaction. Runtime collection requires an explicit
future `--allow-runtime` call and still validates output/report boundaries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "task-020-post-auth-navigation-v1"
TASK_ID = "TASK-020"
MODE = "NON_AUTONOMOUS"
TOOL_NAME = "post_auth_navigation.post_auth_navigation_probe"
PRODUCTION_SAFE = "PROD_SAFE"
PRODUCTION_CONDITIONAL = "PROD_CONDITIONAL"
RAW_EVIDENCE_ROOT = Path(".qa_local/evidence/task-020")
PUBLIC_REPORT_ROOT = Path("docs/qa/reports")

STATUS_VALUES = {"pass", "fail", "blocked", "not_run", "not_observed", "unknown", "blocked_by_boundary"}
COVERAGE_STATUSES = {
    "sampled_bounded_runtime_coverage",
    "partial_budget_limited_coverage",
    "blocked",
    "not_run",
}
RUNTIME_EXECUTION_STATUSES = {"pass", "partial", "blocked", "not_run", "fail"}
BOUNDARY_TYPES = {
    "payment_subscription_purchase",
    "webview_redirect_browser",
    "stream_webrtc_media_playback",
    "profile_account_mutation",
    "network_offline_manipulation",
    "unknown_dangerous_boundary",
}
DEFAULT_BUDGET = {
    "max_runtime_duration_minutes": 90,
    "max_screens": 40,
    "max_transition_edges": 160,
    "max_actions_total": 500,
    "max_depth_from_post_auth_root": 6,
    "max_focus_moves_per_screen": 24,
    "max_selects_per_screen": 8,
    "max_back_recovery_attempts_per_screen": 4,
    "max_session_checkpoint_screens": 6,
    "max_revisits_per_screen_alias": 3,
}
TARGET_ALIASES = {
    "device_alias": "tv-tpv-013",
    "runtime_profile_alias": "tv-tpv-a12-013",
    "build_alias": "task-005-local-apk-001",
    "synthetic_user_alias": "qa-user-phone-001",
}

BOUNDARY_KEYWORDS = {
    "payment_subscription_purchase": (
        "pay",
        "payment",
        "purchase",
        "subscribe",
        "subscription",
        "billing",
        "checkout",
        "card",
        "wallet",
        "bank",
        "оплата",
        "оплатить",
        "купить",
        "подписка",
        "тариф",
        "карта",
        "банк",
        "счет",
    ),
    "webview_redirect_browser": (
        "webview",
        "browser",
        "redirect",
        "external",
        "url",
        "custom tab",
        "http://",
        "https://",
    ),
    "stream_webrtc_media_playback": (
        "stream",
        "webrtc",
        "playback",
        "player",
        "play",
        "start game",
        "launch game",
        "connect",
        "session start",
        "video",
        "media",
    ),
    "profile_account_mutation": (
        "profile edit",
        "edit profile",
        "delete account",
        "logout",
        "sign out",
        "reset",
        "remove",
        "account delete",
    ),
    "network_offline_manipulation": (
        "offline",
        "proxy",
        "packet",
        "vpn",
        "network reset",
        "airplane",
    ),
}

ALIAS_RE = re.compile(r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*$")
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
LOCAL_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<![\w+])\+?\d[\d\s().-]{8,}\d(?!\w)")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
IMEI_RE = re.compile(r"\b\d{15}\b")
ANDROID_ID_RE = re.compile(r"\b[0-9a-fA-F]{16}\b")
SECRET_PAIR_RE = re.compile(
    r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|bearer|otp)\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)
OTP_VALUE_RE = re.compile(r"\botp\b\s+\d{4,8}\b", re.IGNORECASE)
ACCOUNT_ID_RE = re.compile(r"\baccount[_-]?id\s*[:=]\s*[^\s,;]+", re.IGNORECASE)
HEX_HASH_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
RAW_ARTIFACT_RE = re.compile(r"\.(?:png|jpg|jpeg|webp|mp4|mov|log|txt|xml)$", re.IGNORECASE)
PRIVATE_ROUTE_RE = re.compile(r"(?:deeplink|endpoint|header|payload|activity|package|class)\s*[:=]", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_safe_alias(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value != value.strip() or not ALIAS_RE.fullmatch(value):
        return False
    lowered = value.lower()
    blocked_tokens = {
        "http",
        "https",
        "url",
        "endpoint",
        "deeplink",
        "serial",
        "imei",
        "mac",
        "androidid",
        "android_id",
        "otp",
        "token",
        "secret",
        "password",
        "cookie",
        "sessioncookie",
        "phone",
    }
    return not any(token in lowered for token in blocked_tokens)


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
    if IMEI_RE.search(value):
        findings.append(f"{path} contains an IMEI-like value.")
    if ANDROID_ID_RE.search(value):
        findings.append(f"{path} contains an Android-ID-like value.")
    if SECRET_PAIR_RE.search(value):
        findings.append(f"{path} contains a secret-like key/value.")
    if OTP_VALUE_RE.search(value):
        findings.append(f"{path} contains an OTP-like value.")
    if ACCOUNT_ID_RE.search(value):
        findings.append(f"{path} contains a raw account identifier.")
    if HEX_HASH_RE.search(value):
        findings.append(f"{path} contains a raw hash-like value.")
    if RAW_ARTIFACT_RE.search(value):
        findings.append(f"{path} contains a raw artifact path.")
    if PRIVATE_ROUTE_RE.search(value):
        findings.append(f"{path} contains private route/internal metadata.")
    return findings


def detect_boundary(text: Any) -> str | None:
    if not isinstance(text, str):
        return None
    lowered = text.lower()
    for boundary_type, keywords in BOUNDARY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return boundary_type
    return None


def validate_output_path(path: str | Path, *, public_summary: bool = False) -> bool:
    normalized = Path(path)
    if normalized.is_absolute() or ".." in normalized.parts:
        return False
    base = PUBLIC_REPORT_ROOT if public_summary else RAW_EVIDENCE_ROOT
    expected_parts = ("docs", "qa", "reports") if public_summary else (".qa_local", "evidence", "task-020")
    if normalized.parts[: len(expected_parts)] != expected_parts:
        return False
    if public_summary and normalized.suffix != ".json":
        return False

    # Pattern validation must work in clean public archives where .qa_local is
    # intentionally absent, while still rejecting existing symlink escapes.
    try:
        resolved_base = base.resolve(strict=False)
        candidate = base
        for part in normalized.parts[len(expected_parts) : -1]:
            candidate = candidate / part
            if candidate.exists():
                candidate.resolve(strict=True).relative_to(resolved_base)
    except (OSError, ValueError):
        return False
    return True


def default_blocked_report(reason: str = "--allow-runtime was not provided") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "task_id": TASK_ID,
        "mode": MODE,
        "tool_name": TOOL_NAME,
        "overall_status": "blocked",
        "runtime_execution_status": "not_run",
        "coverage_status": "not_run",
        "evidence_status": "unknown",
        "production_safety_classification": PRODUCTION_SAFE,
        "target": TARGET_ALIASES,
        "resource_budget": DEFAULT_BUDGET,
        "blocked_reasons": [reason],
        "screens_observed": [],
        "transitions_observed": [],
        "states_observed": [],
        "boundaries_observed": [],
        "session_persistence_results": {
            "root_home_foreground": {"result": "not_run", "reason": reason},
            "root_force_stop_relaunch": {"result": "not_run", "reason": reason},
        },
        "crash_anr_summary": {
            "status": "not_run",
            "evidence_status": "unknown",
        },
        "unknowns_frontier": [
            "Post-auth native navigation remains not_run until an approved runtime collection executes.",
        ],
        "public_safety": {
            "raw_phone_otp_committed": False,
            "raw_device_identifiers_committed": False,
            "raw_evidence_committed": False,
            "payment_webview_stream_profile_mutation_entered": False,
        },
        "forbidden_scope_not_run": [
            "payment",
            "webview_redirect",
            "stream_webrtc_media_playback",
            "profile_account_mutation",
            "network_offline_manipulation",
            "compatibility_matrix",
            "experience_qa_craft_audit",
        ],
        "verification": [
            {
                "name": "post-auth-navigation-default-gate",
                "classification": PRODUCTION_SAFE,
                "result": "pass",
                "evidence_status": "confirmed",
                "note": "Default command blocked before any runtime or ADB action.",
            }
        ],
    }


def validate_report_shape(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for field in (
        "schema_version",
        "task_id",
        "coverage_status",
        "runtime_execution_status",
        "target",
        "resource_budget",
        "screens_observed",
        "transitions_observed",
        "boundaries_observed",
        "session_persistence_results",
        "public_safety",
    ):
        if field not in report:
            reasons.append(f"{field} is required.")

    if report.get("task_id") != TASK_ID:
        reasons.append("task_id must be TASK-020.")
    if report.get("schema_version") != SCHEMA_VERSION:
        reasons.append(f"schema_version must be {SCHEMA_VERSION}.")
    if report.get("coverage_status") not in COVERAGE_STATUSES:
        reasons.append("coverage_status must be explicit and recognized.")
    if report.get("runtime_execution_status") not in RUNTIME_EXECUTION_STATUSES:
        reasons.append("runtime_execution_status must be explicit and recognized.")

    target = report.get("target")
    if isinstance(target, dict):
        for key, expected in TARGET_ALIASES.items():
            if target.get(key) != expected:
                reasons.append(f"target.{key} must be {expected}.")
    else:
        reasons.append("target must be an object.")

    reasons.extend(public_safety_findings(report))
    reasons.extend(_validate_screens(report.get("screens_observed")))
    reasons.extend(_validate_transitions(report.get("transitions_observed")))
    reasons.extend(_validate_boundaries(report.get("boundaries_observed")))
    reasons.extend(_validate_session_results(report.get("session_persistence_results")))
    reasons.extend(_validate_public_safety_flags(report.get("public_safety")))
    return sorted(set(reasons))


def _validate_screens(screens: Any) -> list[str]:
    if not isinstance(screens, list):
        return ["screens_observed must be a list."]
    reasons: list[str] = []
    for index, screen in enumerate(screens):
        if not isinstance(screen, dict):
            reasons.append(f"screens_observed[{index}] must be an object.")
            continue
        alias = screen.get("screen_alias")
        if not is_safe_alias(alias):
            reasons.append(f"screens_observed[{index}].screen_alias is not public-safe.")
    return reasons


def _validate_transitions(transitions: Any) -> list[str]:
    if not isinstance(transitions, list):
        return ["transitions_observed must be a list."]
    reasons: list[str] = []
    for index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            reasons.append(f"transitions_observed[{index}] must be an object.")
            continue
        for field in ("transition_alias", "from_screen_alias", "to_screen_alias"):
            if not is_safe_alias(transition.get(field)):
                reasons.append(f"transitions_observed[{index}].{field} is not public-safe.")
        result = transition.get("result")
        if result not in STATUS_VALUES:
            reasons.append(f"transitions_observed[{index}].result is not recognized.")
        if detect_boundary(transition.get("trigger_category")) and result != "blocked_by_boundary":
            reasons.append(f"transitions_observed[{index}] boundary trigger must be blocked_by_boundary.")
        if transition.get("boundary_type") in BOUNDARY_TYPES and result == "pass":
            reasons.append(f"transitions_observed[{index}] boundary transition must not pass.")
    return reasons


def _validate_boundaries(boundaries: Any) -> list[str]:
    if not isinstance(boundaries, list):
        return ["boundaries_observed must be a list."]
    reasons: list[str] = []
    for index, boundary in enumerate(boundaries):
        if not isinstance(boundary, dict):
            reasons.append(f"boundaries_observed[{index}] must be an object.")
            continue
        if not is_safe_alias(boundary.get("boundary_alias")):
            reasons.append(f"boundaries_observed[{index}].boundary_alias is not public-safe.")
        if boundary.get("boundary_type") not in BOUNDARY_TYPES:
            reasons.append(f"boundaries_observed[{index}].boundary_type is not recognized.")
        if boundary.get("action_taken") != "not_entered":
            reasons.append(f"boundaries_observed[{index}].action_taken must be not_entered.")
        if boundary.get("result") != "blocked_by_boundary":
            reasons.append(f"boundaries_observed[{index}].result must be blocked_by_boundary.")
    return reasons


def _validate_session_results(results: Any) -> list[str]:
    if not isinstance(results, dict):
        return ["session_persistence_results must be an object."]
    reasons: list[str] = []
    for key in ("root_home_foreground", "root_force_stop_relaunch"):
        item = results.get(key)
        if not isinstance(item, dict):
            reasons.append(f"session_persistence_results.{key} is required.")
            continue
        result = item.get("result")
        if result not in STATUS_VALUES:
            reasons.append(f"session_persistence_results.{key}.result is not recognized.")
        if result == "not_run" and not item.get("reason"):
            reasons.append(f"session_persistence_results.{key}.reason is required when not_run.")
    return reasons


def _validate_public_safety_flags(flags: Any) -> list[str]:
    if not isinstance(flags, dict):
        return ["public_safety must be an object."]
    reasons: list[str] = []
    expected_false = (
        "raw_phone_otp_committed",
        "raw_device_identifiers_committed",
        "raw_evidence_committed",
        "payment_webview_stream_profile_mutation_entered",
    )
    for key in expected_false:
        if flags.get(key) is not False:
            reasons.append(f"public_safety.{key} must be false.")
    return reasons


def _load_report(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, ["Input report was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return None, [f"Input report is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return None, ["Input report must be a JSON object."]
    return loaded, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a fail-closed TASK-020 post-auth navigation probe gate.")
    parser.add_argument("--allow-runtime", action="store_true", help="Explicitly allow PROD_CONDITIONAL runtime collection.")
    parser.add_argument("--input-report", type=Path, default=None, help="Optional prebuilt public-safe report to validate/write.")
    parser.add_argument("--raw-output", type=Path, default=None, help="Local raw output path under .qa_local/evidence/task-020/.")
    parser.add_argument("--public-summary", type=Path, default=None, help="Public summary path under docs/qa/reports/*.json.")
    args = parser.parse_args(argv)

    raw_output_valid = args.raw_output is None or validate_output_path(args.raw_output, public_summary=False)
    public_summary_valid = args.public_summary is None or validate_output_path(args.public_summary, public_summary=True)

    if not raw_output_valid:
        report = default_blocked_report("raw output path must stay under .qa_local/evidence/task-020/")
    elif not public_summary_valid:
        report = default_blocked_report("public summary path must stay under docs/qa/reports/*.json")
    elif not args.allow_runtime:
        report = default_blocked_report()
    elif args.input_report is not None:
        loaded_report, load_errors = _load_report(args.input_report)
        if loaded_report is None:
            report = default_blocked_report("; ".join(load_errors))
        else:
            errors = validate_report_shape(loaded_report)
            report = loaded_report if not errors else default_blocked_report("; ".join(errors))
    else:
        report = default_blocked_report(
            "--allow-runtime was provided, but this Phase A gate has no approved runtime collector input."
        )
        report["production_safety_classification"] = PRODUCTION_CONDITIONAL

    output_paths_valid = raw_output_valid and public_summary_valid
    if args.public_summary is not None and output_paths_valid:
        args.public_summary.parent.mkdir(parents=True, exist_ok=True)
        args.public_summary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.raw_output is not None and output_paths_valid:
        args.raw_output.parent.mkdir(parents=True, exist_ok=True)
        args.raw_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

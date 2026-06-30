"""Validate public-safe approval metadata for future limited runtime work.

This tool performs no Android, APK, device, WebView, WebRTC, payment, network
or production interaction. It validates only structured approval metadata and
always reports runtime execution as not_run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "task-015-approval-validator-v1"
APPROVAL_METADATA_SCHEMA_VERSION = "task-015-approval-metadata-v1"
DEFAULT_TASK_ID = "TASK-005"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE"
RUNTIME_EXECUTION_STATUS = "not_run"

REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "task_id",
    "scope_version",
    "approval_status",
    "approval_evidence_status",
    "expires_at",
    "approved_by_role",
    "approved_build_apk",
    "approved_targets",
    "runtime_execution",
    "synthetic_qa_user",
    "fixtures",
    "evidence_capture",
    "cleanup_rollback",
    "required_reviews",
)
APPROVAL_STATUSES = {"approved", "pending", "blocked", "revoked"}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
FIXTURE_STATUSES = {"approved", "out_of_scope", "pending", "blocked"}
REVIEW_STATUSES = {"approved", "confirmed", "pending", "blocked", "rejected"}
PASSING_REVIEW_STATUSES = {"approved", "confirmed"}
APPROVED_BY_ROLES = {"project_owner", "qa_lead", "security_prod_safety_reviewer"}
REQUIRED_REVIEWERS = (
    "qa_reviewer_a",
    "qa_reviewer_b",
    "security_prod_safety_reviewer",
    "docs_scribe",
)
TASK_005_ALLOWED_RUNTIME_SCOPE = {
    "install",
    "launch",
    "first_visible_state",
    "synthetic_login_if_required",
    "initial_focus",
    "minimal_dpad_navigation",
    "back_home",
    "background_foreground",
    "force_stop_relaunch",
    "clear_cache_if_preapproved",
    "clear_app_data_before_after_clean_state",
    "crash_anr_logcat_observation",
    "redacted_evidence_summary",
}
TASK_005_REQUIRED_RUNTIME_SCOPE = {
    "install",
    "launch",
    "first_visible_state",
    "initial_focus",
    "minimal_dpad_navigation",
    "back_home",
    "background_foreground",
    "force_stop_relaunch",
    "crash_anr_logcat_observation",
    "redacted_evidence_summary",
}
BUILD_ALLOWED_ACTIONS = {"install", "launch", "observe"}
BUILD_REQUIRED_FORBIDDEN_ACTIONS = {
    "commit",
    "upload",
    "archive",
    "decompile",
    "patch",
    "resign",
    "extract_private_endpoints",
    "extract_secrets",
}
FORBIDDEN_SCOPE_TERMS = {
    "stream",
    "webrtc",
    "media",
    "media_playback",
    "video",
    "video_playback",
    "playback",
    "player",
    "cloud_stream",
    "game_stream",
    "webview",
    "browser",
    "custom_tab",
    "url_load",
    "redirect",
    "redirect_flow",
    "payment",
    "purchase",
    "subscription",
    "billing",
    "checkout",
    "card",
    "wallet",
    "bank",
    "transaction",
    "invoice",
    "receipt",
    "profile_mutation",
    "profile_update",
    "account_mutation",
    "destructive_account_action",
    "real_user_data_changes",
    "production_mutation",
    "security_bypass",
    "decompilation",
    "patching",
    "resigning",
}
FIXTURE_SCOPE_TERMS = {
    "stream_fixture": {"stream", "webrtc", "media", "media_playback", "video", "video_playback", "playback", "player", "cloud_stream", "game_stream"},
    "webview_fixture": {"webview", "browser", "custom_tab", "url_load", "redirect", "redirect_flow"},
    "payment_staging_fixture": {"payment", "subscription", "purchase", "billing", "checkout", "card", "wallet", "bank", "transaction", "invoice", "receipt"},
}
EXPECTED_FIXTURE_STATUSES = {
    "stream_fixture": "out_of_scope",
    "webview_fixture": "out_of_scope",
    "payment_staging_fixture": "out_of_scope",
}
EVIDENCE_CAPTURE_STATUSES = {
    "approved_local_redacted_summary_only",
    "pending_explicit_owner_confirmation",
    "blocked",
}
EVIDENCE_CAPTURE_IMAGE_LOG_VALUES = {
    "yes_local_only_redacted_summary",
    "no",
    "pending",
    "blocked",
}
EVIDENCE_CAPTURE_VIDEO_VALUES = {
    "no_by_default",
    "yes_local_only_redacted_summary",
    "no",
    "pending",
    "blocked",
}
AUTH_MODES = {
    "synthetic_login_if_required",
    "auth_out_of_scope",
    "no_auth_required",
}
CLEANUP_ALLOWED_LEVELS = {
    "C1_background_foreground",
    "C2_force_stop_relaunch",
    "C3_clear_cache",
    "C4_clear_app_data",
}
TARGET_ALLOWED_CATEGORIES = {
    "physical_android_tv",
    "google_tv",
    "android_stb",
    "aosp_stb",
    "android_phone_secondary",
}
TARGET_CATEGORY_TO_STRUCTURED = {
    "physical_android_tv": "android_tv",
    "google_tv": "google_tv",
    "android_stb": "android_stb",
    "aosp_stb": "aosp_stb",
    "android_phone_secondary": "android_phone_secondary",
}
STRUCTURED_TARGET_CATEGORIES = {
    "android_tv",
    "google_tv",
    "android_stb",
    "aosp_stb",
    "android_phone_secondary",
}
TV_STB_TARGET_CATEGORIES = {"android_tv", "google_tv", "android_stb", "aosp_stb"}
TV_STB_FORM_FACTORS = {"tv", "stb"}
TARGET_PRIORITIES = {"P0", "P1", "P2"}
YES_NO_UNKNOWN = {"yes", "no", "unknown"}
CLASSIFICATION_CONFIDENCES = {"manual_confirmed", "manual_review", "heuristic", "unknown"}
DEVICE_ALIAS_RE = re.compile(r"^(tv|stb|phone|tablet|emulator|unknown)-[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{3}$")
RUNTIME_PROFILE_ALIAS_RE = re.compile(
    r"^(tv|stb|phone|tablet|emulator|unknown)-[a-z0-9]+(?:-[a-z0-9]+)*-a[0-9]{1,2}-[0-9]{3}$"
)
BUILD_ALIAS_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{3}$")
BLOCKED_ALIAS_LABELS = {
    "oleg",
    "home",
    "livingroom",
    "living-room",
    "living_room",
    "bedroom",
    "office",
    "kitchen",
    "personal",
    "private",
}
RESERVED_ALIAS_TOKENS = {
    "serial",
    "serialnumber",
    "serial-number",
    "serial_number",
    "imei",
    "imsi",
    "mac",
    "macaddress",
    "mac-address",
    "mac_address",
    "androidid",
    "android-id",
    "android_id",
    "google-account",
    "google_account",
    "account",
    "phone",
    "otp",
    "token",
    "secret",
    "password",
    "cookie",
    "session",
    *BLOCKED_ALIAS_LABELS,
}
BUILD_RESERVED_ALIAS_TOKENS = {
    "secret",
    "token",
    "password",
    "cookie",
    "session",
    "serial",
    "serialnumber",
    "serial-number",
    "serial_number",
    "imei",
    "mac",
    "macaddress",
    "mac-address",
    "mac_address",
    "androidid",
    "android-id",
    "android_id",
    "phone",
}
BLOCKED_ALIAS_PATTERN = re.compile(
    r"\b(?:oleg|living\s*[-_ ]?\s*room|home|bedroom|office|kitchen|personal|private)\b"
)
FINGERPRINT_LIKE_RE = re.compile(r"[a-z0-9_.-]+/[a-z0-9_.-]+/[a-z0-9_.-]+:[0-9]", re.IGNORECASE)
FORBIDDEN_IDENTIFIER_KEYS = {
    "serial",
    "serial_number",
    "imei",
    "imsi",
    "mac",
    "mac_address",
    "android_id",
    "google_account",
    "device_id",
    "personal_device_identifier",
}

PHONE_RE = re.compile(r"(?<![\w+])\+?\d[\d\s().-]{8,}\d(?!\w)")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
IMEI_RE = re.compile(r"\b\d{15}\b")
ANDROID_ID_RE = re.compile(r"\b[0-9a-fA-F]{16}\b")
URL_RE = re.compile(r"https?://[^\s)]+", re.IGNORECASE)
WINDOWS_USER_PATH_RE = re.compile(r"\b[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE)
UNIX_USER_PATH_RE = re.compile(r"(?<!\w)/(?:home|Users|private)/[^\s,;]+", re.IGNORECASE)
SECRET_PAIR_RE = re.compile(
    r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|bearer)\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_metadata(path: Path | None) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return {}, ["Approval metadata file was not provided."]
    if not path.exists():
        return {}, ["Approval metadata file was not found."]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"Approval metadata file is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return {}, ["Approval metadata must be a JSON object."]
    return loaded, []


def _as_lower(value: Any) -> str:
    return value.strip().lower() if isinstance(value, str) else ""


def _normalize_enum(value: Any, allowed: set[str], default: str = "unknown") -> str:
    lowered = _as_lower(value)
    return lowered if lowered in allowed else default


def _parse_expiration(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        if raw.endswith("Z"):
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _is_expired(value: Any, now: datetime) -> bool:
    parsed = _parse_expiration(value)
    if parsed is None:
        return True
    return parsed < now


def _stringify_scope(raw_scope: Any) -> list[str]:
    if isinstance(raw_scope, list):
        return [str(item).strip() for item in raw_scope if str(item).strip()]
    if isinstance(raw_scope, str) and raw_scope.strip():
        return [raw_scope.strip()]
    return []


def _contains_scope_term(scope_item: str, term: str) -> bool:
    normalized_item = scope_item.lower().replace("-", "_").replace(" ", "_")
    normalized_term = term.lower().replace("-", "_").replace(" ", "_")
    return normalized_term in normalized_item


def _path_is_local_ignored(path_value: Any) -> bool:
    if not isinstance(path_value, str):
        return False
    normalized = path_value.replace("\\", "/").strip()
    if not normalized.startswith(".qa_local/"):
        return False
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    return parts[:1] == [".qa_local"] and ".." not in parts


def _iter_json(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    items = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            items.extend(_iter_json(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(_iter_json(child, f"{path}[{index}]"))
    return items


def _is_policy_identifier_list(path: str) -> bool:
    return path.endswith(".forbidden_identifiers") or ".forbidden_identifiers[" in path


def _is_safe_otp_policy(path: str, value: Any) -> bool:
    lowered_path = path.lower()
    return lowered_path.endswith("raw_otp_allowed_in_public_docs") and value is False


def _scan_for_forbidden_public_values(metadata: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for path, value in _iter_json(metadata):
        lowered_path = path.lower()
        key_name = lowered_path.rsplit(".", maxsplit=1)[-1]

        if key_name in FORBIDDEN_IDENTIFIER_KEYS and not _is_policy_identifier_list(path):
            reasons.append(f"Forbidden device identifier field is present at {path}.")

        if _is_safe_otp_policy(path, value):
            continue

        if "otp" in key_name and isinstance(value, str) and value.strip() and not value.strip().startswith("<"):
            reasons.append(f"OTP-like public value is present at {path}.")

        if not isinstance(value, str):
            continue

        if _is_policy_identifier_list(path):
            continue

        text = value.strip()
        if not text or text.startswith("<"):
            continue

        if PHONE_RE.search(text) and sum(char.isdigit() for char in text) >= 10:
            reasons.append(f"Phone-like public value is present at {path}.")
        if MAC_RE.search(text):
            reasons.append(f"MAC-like public value is present at {path}.")
        if IMEI_RE.search(text):
            reasons.append(f"IMEI-like public value is present at {path}.")
        if ANDROID_ID_RE.search(text) and "sha256" not in lowered_path:
            reasons.append(f"Android-ID-like public value is present at {path}.")
        if URL_RE.search(text):
            reasons.append(f"Raw URL-like public value is present at {path}.")
        if WINDOWS_USER_PATH_RE.search(text) or UNIX_USER_PATH_RE.search(text):
            reasons.append(f"Raw user-specific path is present at {path}.")
        if SECRET_PAIR_RE.search(text):
            reasons.append(f"Secret-like public value is present at {path}.")
        if "google" in lowered_path and "account" in lowered_path:
            reasons.append(f"Google account identifier field is present at {path}.")

    return sorted(set(reasons))


def _validate_required_fields(metadata: dict[str, Any]) -> list[str]:
    return [f"Required field {field} is missing." for field in REQUIRED_TOP_LEVEL_FIELDS if field not in metadata]


def _validate_identity(metadata: dict[str, Any]) -> list[str]:
    reasons = []
    if metadata.get("schema_version") != APPROVAL_METADATA_SCHEMA_VERSION:
        reasons.append(f"schema_version must be {APPROVAL_METADATA_SCHEMA_VERSION}.")
    if metadata.get("task_id") != DEFAULT_TASK_ID:
        reasons.append(f"task_id must be {DEFAULT_TASK_ID}.")
    return reasons


def _validate_approved_by_role(metadata: dict[str, Any]) -> list[str]:
    role = _as_lower(metadata.get("approved_by_role"))
    if role not in APPROVED_BY_ROLES:
        return ["approved_by_role must be non-empty and one of project_owner, qa_lead, security_prod_safety_reviewer."]
    return []


def _validate_build(metadata: dict[str, Any]) -> list[str]:
    reasons = []
    build = metadata.get("approved_build_apk")
    if not isinstance(build, dict):
        return ["approved_build_apk must be an object."]
    if build.get("approved") is not True:
        reasons.append("approved_build_apk.approved must be true for TASK-005 runtime approval.")
    build_alias = build.get("build_alias")
    if (
        not isinstance(build_alias, str)
        or BUILD_ALIAS_RE.fullmatch(build_alias.strip()) is None
        or _build_alias_has_forbidden_content(build_alias)
    ):
        reasons.append("approved_build_apk.build_alias must be a non-empty public-safe build alias.")
    if build.get("storage_policy") != "local_ignored_path_only":
        reasons.append("approved_build_apk.storage_policy must be local_ignored_path_only.")
    if not _path_is_local_ignored(build.get("expected_local_path_pattern")):
        reasons.append("approved_build_apk.expected_local_path_pattern must stay under .qa_local/.")
    if build.get("sha256_required") is not True:
        reasons.append("approved_build_apk.sha256_required must be true.")
    if build.get("sha256_public_value_allowed") is not False:
        reasons.append("approved_build_apk.sha256_public_value_allowed must be false.")

    allowed_actions = build.get("allowed_actions")
    if not isinstance(allowed_actions, list) or not allowed_actions:
        reasons.append("approved_build_apk.allowed_actions must be a non-empty list.")
    else:
        normalized_allowed_actions = {str(action) for action in allowed_actions}
        unsupported_allowed = sorted(normalized_allowed_actions - BUILD_ALLOWED_ACTIONS)
        if unsupported_allowed:
            reasons.append(f"approved_build_apk.allowed_actions contains unsupported actions: {unsupported_allowed}.")
        missing_allowed = sorted(BUILD_ALLOWED_ACTIONS - normalized_allowed_actions)
        if missing_allowed:
            reasons.append(f"approved_build_apk.allowed_actions is missing required actions: {missing_allowed}.")

    forbidden_actions = build.get("forbidden_actions")
    if not isinstance(forbidden_actions, list) or not forbidden_actions:
        reasons.append("approved_build_apk.forbidden_actions must be a non-empty list.")
    else:
        missing_forbidden = sorted(BUILD_REQUIRED_FORBIDDEN_ACTIONS - {str(action) for action in forbidden_actions})
        if missing_forbidden:
            reasons.append(f"approved_build_apk.forbidden_actions is missing required actions: {missing_forbidden}.")
    return reasons


def _alias_tokens(alias: str) -> set[str]:
    normalized = alias.strip().lower()
    parts = [part for part in re.split(r"[-_\s]+", normalized) if part]
    tokens = set(parts)
    for start in range(len(parts)):
        for end in range(start + 2, min(len(parts), start + 4) + 1):
            joined = "".join(parts[start:end])
            tokens.add(joined)
            tokens.add("-".join(parts[start:end]))
            tokens.add("_".join(parts[start:end]))
    return tokens


def _alias_form_factor(alias: str) -> str:
    return alias.strip().lower().split("-", maxsplit=1)[0]


def _alias_index(alias: str) -> str:
    return alias.strip().lower().rsplit("-", maxsplit=1)[-1]


def _device_alias_prefix(alias: str) -> str:
    return alias.strip().lower().rsplit("-", maxsplit=1)[0]


def _runtime_alias_parts(alias: str) -> tuple[str, int | None, str] | None:
    normalized = alias.strip().lower()
    match = re.fullmatch(r"(.+)-a([0-9]{1,2})-([0-9]{3})", normalized)
    if match is None:
        return None
    return match.group(1), int(match.group(2)), match.group(3)


def _tokens_without_allowed_phone(alias: str, form_factor: Any = None) -> set[str]:
    tokens = _alias_tokens(alias)
    parts = [part for part in re.split(r"[-_\s]+", alias.strip().lower()) if part]
    if form_factor == "phone" and parts[:1] == ["phone"] and "phone" not in parts[1:]:
        tokens.discard("phone")
    return tokens


def _alias_has_forbidden_content(alias: Any, form_factor: Any = None) -> bool:
    if not isinstance(alias, str):
        return True
    normalized = alias.strip().lower()
    if not normalized:
        return True
    parts = [part for part in re.split(r"[-_\s]+", normalized) if part]
    if "phone" in parts and not (form_factor == "phone" and parts[:1] == ["phone"] and "phone" not in parts[1:]):
        return True
    if BLOCKED_ALIAS_PATTERN.search(normalized):
        return True
    if _tokens_without_allowed_phone(normalized, form_factor) & RESERVED_ALIAS_TOKENS:
        return True
    return bool(
        IP_RE.search(normalized)
        or MAC_RE.search(normalized)
        or IMEI_RE.search(normalized)
        or ANDROID_ID_RE.search(normalized)
        or FINGERPRINT_LIKE_RE.search(normalized)
    )


def _build_alias_has_forbidden_content(alias: Any) -> bool:
    if not isinstance(alias, str):
        return True
    normalized = alias.strip().lower()
    if not normalized:
        return True
    if _alias_tokens(normalized) & BUILD_RESERVED_ALIAS_TOKENS:
        return True
    return bool(
        IP_RE.search(normalized)
        or PHONE_RE.search(normalized)
        or MAC_RE.search(normalized)
        or IMEI_RE.search(normalized)
        or ANDROID_ID_RE.search(normalized)
        or FINGERPRINT_LIKE_RE.search(normalized)
    )


def _valid_device_alias(alias: Any, form_factor: Any = None) -> bool:
    return (
        isinstance(alias, str)
        and DEVICE_ALIAS_RE.fullmatch(alias.strip()) is not None
        and not _alias_has_forbidden_content(alias, form_factor)
    )


def _valid_runtime_profile_alias(alias: Any, form_factor: Any = None) -> bool:
    return (
        isinstance(alias, str)
        and RUNTIME_PROFILE_ALIAS_RE.fullmatch(alias.strip()) is not None
        and not _alias_has_forbidden_content(alias, form_factor)
    )


def _device_alias_matches_form_factor(alias: str, form_factor: str) -> bool:
    return _alias_form_factor(alias) == form_factor


def _runtime_alias_matches_device(device_alias: str, runtime_profile_alias: str, android_major: int) -> bool:
    parts = _runtime_alias_parts(runtime_profile_alias)
    if parts is None:
        return False
    runtime_prefix, runtime_major, runtime_index = parts
    return (
        runtime_prefix == _device_alias_prefix(device_alias)
        and runtime_index == _alias_index(device_alias)
        and runtime_major == android_major
    )


def _validate_targets(metadata: dict[str, Any]) -> list[str]:
    reasons = []
    targets = metadata.get("approved_targets")
    if not isinstance(targets, dict):
        return ["approved_targets must be an object."]
    if targets.get("approved") is not True:
        reasons.append("approved_targets.approved must be true.")
    if targets.get("device_aliases_required") is not True:
        reasons.append("approved_targets.device_aliases_required must be true.")
    categories = targets.get("allowed_categories")
    normalized_allowed_categories: set[str] = set()
    if not isinstance(categories, list) or not categories:
        reasons.append("approved_targets.allowed_categories must list approved target categories.")
    else:
        unsupported_categories = [str(category) for category in categories if str(category) not in TARGET_ALLOWED_CATEGORIES]
        if unsupported_categories:
            reasons.append(f"approved_targets.allowed_categories contains unsupported categories: {unsupported_categories}.")
        normalized_allowed_categories = {
            TARGET_CATEGORY_TO_STRUCTURED[str(category)]
            for category in categories
            if str(category) in TARGET_CATEGORY_TO_STRUCTURED
        }

    aliases = targets.get("device_aliases")
    if aliases is None and targets.get("device_aliases_required") is not True:
        aliases = targets.get("approved_device_aliases")
    listed_aliases: set[str] = set()
    if aliases is not None:
        if not isinstance(aliases, list) or not aliases:
            reasons.append("approved_targets.device_aliases must be a non-empty list when present.")
        else:
            for alias in aliases:
                if not _valid_device_alias(alias, form_factor="phone"):
                    reasons.append(f"approved_targets.device_aliases contains unsafe alias: {alias}.")
                if isinstance(alias, str):
                    listed_aliases.add(alias.strip())
            if len(listed_aliases) != len([alias for alias in aliases if isinstance(alias, str)]):
                reasons.append("approved_targets.device_aliases must not contain duplicates.")
    elif targets.get("device_aliases_required") is True:
        reasons.append("approved_targets.device_aliases must be present when device_aliases_required=true.")

    devices = targets.get("devices")
    if not isinstance(devices, list) or not devices:
        reasons.append("approved_targets.devices must include structured device targets.")
        return reasons

    has_actionable_p0_tv_stb_dpad = False
    structured_aliases: list[str] = []
    runtime_aliases: list[str] = []
    required_device_fields = {
        "device_alias",
        "runtime_profile_alias",
        "category",
        "priority",
        "form_factor",
        "input_method",
        "android_major",
        "api_level",
        "adb_available",
        "google_play_services",
        "classification_confidence",
        "manual_review_required",
        "forbidden_identifiers_excluded",
    }
    for index, device in enumerate(devices):
        if not isinstance(device, dict):
            reasons.append(f"approved_targets.devices[{index}] must be an object.")
            continue
        for field in sorted(required_device_fields - set(device)):
            reasons.append(f"approved_targets.devices[{index}].{field} is missing.")
        form_factor = device.get("form_factor")
        device_alias = device.get("device_alias")
        runtime_profile_alias = device.get("runtime_profile_alias")
        android_major = device.get("android_major")

        if not _valid_device_alias(device_alias, form_factor=form_factor):
            reasons.append(f"approved_targets.devices[{index}].device_alias is unsafe or invalid.")
        elif isinstance(device_alias, str):
            structured_aliases.append(device_alias.strip())
        if not _valid_runtime_profile_alias(runtime_profile_alias, form_factor=form_factor):
            reasons.append(f"approved_targets.devices[{index}].runtime_profile_alias is unsafe or invalid.")
        elif isinstance(runtime_profile_alias, str):
            runtime_aliases.append(runtime_profile_alias.strip())
        if device.get("category") not in STRUCTURED_TARGET_CATEGORIES:
            reasons.append(f"approved_targets.devices[{index}].category is unsupported.")
        elif normalized_allowed_categories and device.get("category") not in normalized_allowed_categories:
            reasons.append(
                f"approved_targets.devices[{index}].category is not allowed by approved_targets.allowed_categories."
            )
        if device.get("classification_confidence") == "manual_confirmed" and device.get("category") in TV_STB_TARGET_CATEGORIES:
            if form_factor not in TV_STB_FORM_FACTORS:
                reasons.append(
                    f"approved_targets.devices[{index}].form_factor must be tv or stb for manual-confirmed TV/STB targets."
                )
        if device.get("priority") not in TARGET_PRIORITIES:
            reasons.append(f"approved_targets.devices[{index}].priority is unsupported.")
        if device.get("form_factor") not in {"tv", "stb", "phone", "tablet", "emulator", "unknown"}:
            reasons.append(f"approved_targets.devices[{index}].form_factor is unsupported.")
        if device.get("input_method") not in {"dpad_remote", "touch", "keyboard_mouse", "unknown"}:
            reasons.append(f"approved_targets.devices[{index}].input_method is unsupported.")
        if not isinstance(device.get("android_major"), int) or device.get("android_major") < 1:
            reasons.append(f"approved_targets.devices[{index}].android_major must be a positive integer.")
        if not isinstance(device.get("api_level"), int) or device.get("api_level") < 1:
            reasons.append(f"approved_targets.devices[{index}].api_level must be a positive integer.")
        if device.get("adb_available") not in YES_NO_UNKNOWN:
            reasons.append(f"approved_targets.devices[{index}].adb_available is unsupported.")
        if device.get("google_play_services") not in YES_NO_UNKNOWN:
            reasons.append(f"approved_targets.devices[{index}].google_play_services is unsupported.")
        if device.get("classification_confidence") not in CLASSIFICATION_CONFIDENCES:
            reasons.append(f"approved_targets.devices[{index}].classification_confidence is unsupported.")
        if not isinstance(device.get("manual_review_required"), bool):
            reasons.append(f"approved_targets.devices[{index}].manual_review_required must be boolean.")
        if device.get("forbidden_identifiers_excluded") is not True:
            reasons.append(f"approved_targets.devices[{index}].forbidden_identifiers_excluded must be true.")

        if (
            isinstance(device_alias, str)
            and isinstance(runtime_profile_alias, str)
            and isinstance(android_major, int)
            and android_major > 0
            and not _runtime_alias_matches_device(device_alias, runtime_profile_alias, android_major)
        ):
            reasons.append(
                f"approved_targets.devices[{index}].runtime_profile_alias must preserve device_alias prefix/index and match android_major."
            )

        if (
            device.get("category") in TV_STB_TARGET_CATEGORIES
            and form_factor in TV_STB_FORM_FACTORS
            and device.get("classification_confidence") == "manual_confirmed"
            and isinstance(device_alias, str)
            and not _device_alias_matches_form_factor(device_alias, form_factor)
        ):
            reasons.append(
                f"approved_targets.devices[{index}].device_alias form-factor prefix must match structured form_factor."
            )

        if (
            device.get("priority") == "P0"
            and device.get("category") in TV_STB_TARGET_CATEGORIES
            and device.get("form_factor") in TV_STB_FORM_FACTORS
            and device.get("input_method") == "dpad_remote"
        ):
            if device.get("adb_available") != "yes":
                reasons.append(f"approved_targets.devices[{index}].adb_available must be yes for runtime approval.")
            if device.get("classification_confidence") != "manual_confirmed":
                reasons.append(
                    f"approved_targets.devices[{index}].classification_confidence must be manual_confirmed for runtime approval."
                )
            if device.get("manual_review_required") is not False:
                reasons.append(f"approved_targets.devices[{index}].manual_review_required must be false for runtime approval.")
            if (
                device.get("adb_available") == "yes"
                and device.get("classification_confidence") == "manual_confirmed"
                and device.get("manual_review_required") is False
                and device.get("forbidden_identifiers_excluded") is True
            ):
                has_actionable_p0_tv_stb_dpad = True

    if len(set(structured_aliases)) != len(structured_aliases):
        reasons.append("approved_targets.devices device_alias values must not contain duplicates.")
    if len(set(runtime_aliases)) != len(runtime_aliases):
        reasons.append("approved_targets.devices runtime_profile_alias values must not contain duplicates.")
    if listed_aliases:
        missing_from_structured = sorted(listed_aliases - set(structured_aliases))
        missing_from_list = sorted(set(structured_aliases) - listed_aliases)
        if missing_from_structured:
            reasons.append(f"approved_targets.device_aliases contains aliases missing from structured devices: {missing_from_structured}.")
        if missing_from_list:
            reasons.append(f"approved_targets.devices contains aliases missing from device_aliases: {missing_from_list}.")
    if not has_actionable_p0_tv_stb_dpad:
        reasons.append("TASK-005 approval requires at least one actionable P0 Android TV/STB D-pad target.")
    return reasons


def _validate_runtime_scope(metadata: dict[str, Any]) -> list[str]:
    reasons = []
    runtime = metadata.get("runtime_execution")
    if not isinstance(runtime, dict):
        return ["runtime_execution must be an object."]
    if metadata.get("task_id") == DEFAULT_TASK_ID and runtime.get("allowed") is not True:
        reasons.append("runtime_execution.allowed must be true for TASK-005 approval metadata.")

    allowed_scope = _stringify_scope(runtime.get("allowed_scope"))
    auth_mode = _as_lower(runtime.get("auth_mode"))
    if auth_mode not in AUTH_MODES:
        reasons.append("runtime_execution.auth_mode must be one of synthetic_login_if_required, auth_out_of_scope, no_auth_required.")
    if metadata.get("task_id") == DEFAULT_TASK_ID and not allowed_scope:
        reasons.append("runtime_execution.allowed_scope must be a non-empty list for TASK-005 approval metadata.")
    missing_core_scope = sorted(TASK_005_REQUIRED_RUNTIME_SCOPE - set(allowed_scope))
    if metadata.get("task_id") == DEFAULT_TASK_ID and missing_core_scope:
        reasons.append(f"runtime_execution.allowed_scope is missing required TASK-005 core items: {missing_core_scope}.")
    for item in allowed_scope:
        if item not in TASK_005_ALLOWED_RUNTIME_SCOPE:
            reasons.append(f"runtime_execution.allowed_scope contains unsupported item: {item}.")
    for item in allowed_scope:
        for term in FORBIDDEN_SCOPE_TERMS:
            if _contains_scope_term(item, term):
                reasons.append(f"runtime_execution.allowed_scope contains forbidden area: {item}.")

    synthetic_login_in_scope = "synthetic_login_if_required" in allowed_scope
    if synthetic_login_in_scope and auth_mode != "synthetic_login_if_required":
        reasons.append("runtime_execution.auth_mode must be synthetic_login_if_required when synthetic login is in scope.")
    if auth_mode == "synthetic_login_if_required" and not synthetic_login_in_scope:
        reasons.append("runtime_execution.auth_mode synthetic_login_if_required requires matching runtime scope.")

    fixtures = metadata.get("fixtures")
    if isinstance(fixtures, dict):
        for fixture_name, fixture_terms in FIXTURE_SCOPE_TERMS.items():
            status = _normalize_enum(fixtures.get(fixture_name), FIXTURE_STATUSES)
            if status == "out_of_scope":
                for item in allowed_scope:
                    if any(_contains_scope_term(item, term) for term in fixture_terms):
                        reasons.append(f"{fixture_name} is out_of_scope but runtime scope includes {item}.")
    return sorted(set(reasons))


def _validate_synthetic_user(metadata: dict[str, Any]) -> list[str]:
    reasons = []
    user = metadata.get("synthetic_qa_user")
    if not isinstance(user, dict):
        return ["synthetic_qa_user must be an object."]
    runtime = metadata.get("runtime_execution")
    allowed_scope = _stringify_scope(runtime.get("allowed_scope")) if isinstance(runtime, dict) else []
    auth_mode = _as_lower(runtime.get("auth_mode")) if isinstance(runtime, dict) else ""
    synthetic_login_in_scope = "synthetic_login_if_required" in allowed_scope
    if synthetic_login_in_scope and user.get("approved") is not True:
        reasons.append("synthetic_login_if_required requires synthetic_qa_user.approved=true.")
    if user.get("approved") is not True and synthetic_login_in_scope:
        reasons.append("synthetic_qa_user.approved=false requires runtime scope to omit synthetic_login_if_required.")
    if user.get("approved") is not True and auth_mode not in {"auth_out_of_scope", "no_auth_required"}:
        reasons.append("synthetic_qa_user.approved=false requires explicit auth_out_of_scope or no_auth_required auth_mode.")
    if user.get("approved") is True and user.get("alias") != "qa-user-phone-001":
        reasons.append("synthetic_qa_user.approved requires public alias qa-user-phone-001.")
    if user.get("approved") is True and user.get("raw_phone_allowed_in_public_docs") is not False:
        reasons.append("synthetic_qa_user raw phone must be forbidden in public docs.")
    if user.get("approved") is True and user.get("raw_otp_allowed_in_public_docs") is not False:
        reasons.append("synthetic_qa_user raw OTP must be forbidden in public docs.")
    local_secret_file = user.get("local_secret_file_pattern")
    if local_secret_file is not None and not _path_is_local_ignored(local_secret_file):
        reasons.append("synthetic_qa_user.local_secret_file_pattern must stay under .qa_local/.")
    return reasons


def _validate_fixtures(metadata: dict[str, Any]) -> list[str]:
    fixtures = metadata.get("fixtures")
    if not isinstance(fixtures, dict):
        return ["fixtures must be an object."]
    reasons = []
    for fixture_name, expected_status in EXPECTED_FIXTURE_STATUSES.items():
        status = _as_lower(fixtures.get(fixture_name))
        if status not in FIXTURE_STATUSES:
            reasons.append(f"fixtures.{fixture_name} must be one of approved, out_of_scope, pending, blocked.")
            continue
        if metadata.get("task_id") == DEFAULT_TASK_ID and status != expected_status:
            reasons.append(f"fixtures.{fixture_name} must be {expected_status} for current TASK-005 scope.")
    return reasons


def _validate_evidence_capture(metadata: dict[str, Any]) -> list[str]:
    reasons = []
    evidence = metadata.get("evidence_capture")
    if not isinstance(evidence, dict):
        return ["evidence_capture must be an object."]
    runtime = metadata.get("runtime_execution")
    allowed_scope = _stringify_scope(runtime.get("allowed_scope")) if isinstance(runtime, dict) else []
    status = _as_lower(evidence.get("status"))
    if status not in EVIDENCE_CAPTURE_STATUSES:
        reasons.append("evidence_capture.status must use an approved exact value.")
    elif status in {"pending_explicit_owner_confirmation", "blocked"}:
        reasons.append("evidence_capture.status must be explicit and non-pending for runtime approval.")
    if evidence.get("raw_storage_policy") != "local_ignored_path_only":
        reasons.append("evidence_capture.raw_storage_policy must be local_ignored_path_only.")
    if not _path_is_local_ignored(evidence.get("raw_storage_path_pattern")):
        reasons.append("evidence_capture.raw_storage_path_pattern must stay under .qa_local/.")
    if evidence.get("public_report_policy") != "redacted_summaries_only":
        reasons.append("evidence_capture.public_report_policy must be redacted_summaries_only.")
    for field in ("screenshots", "logs_logcat"):
        value = _as_lower(evidence.get(field))
        if value not in EVIDENCE_CAPTURE_IMAGE_LOG_VALUES:
            reasons.append(f"evidence_capture.{field} must use an approved exact value.")
        elif value in {"pending", "blocked"}:
            reasons.append(f"evidence_capture.{field} must be explicit and non-pending.")
    video_value = _as_lower(evidence.get("videos"))
    if video_value not in EVIDENCE_CAPTURE_VIDEO_VALUES:
        reasons.append("evidence_capture.videos must use an approved exact value.")
    elif video_value in {"pending", "blocked"}:
        reasons.append("evidence_capture.videos must be explicit and non-pending.")

    if (
        "crash_anr_logcat_observation" in allowed_scope
        and _as_lower(evidence.get("logs_logcat")) != "yes_local_only_redacted_summary"
    ):
        reasons.append(
            "crash_anr_logcat_observation requires evidence_capture.logs_logcat=yes_local_only_redacted_summary."
        )
    visual_scope = {"first_visible_state", "initial_focus", "minimal_dpad_navigation"}
    if visual_scope & set(allowed_scope) and not (
        _as_lower(evidence.get("screenshots")) == "yes_local_only_redacted_summary"
        or _as_lower(evidence.get("videos")) == "yes_local_only_redacted_summary"
    ):
        reasons.append(
            "first_visible_state/initial_focus/minimal_dpad_navigation require screenshots or videos as local redacted summaries."
        )
    return reasons


def _validate_cleanup(metadata: dict[str, Any]) -> list[str]:
    reasons = []
    cleanup = metadata.get("cleanup_rollback")
    if not isinstance(cleanup, dict):
        return ["cleanup_rollback must be an object."]
    if cleanup.get("approved") is not True:
        reasons.append("cleanup_rollback.approved must be true.")
    levels = cleanup.get("allowed_levels")
    if not isinstance(levels, list) or not levels:
        reasons.append("cleanup_rollback.allowed_levels must not be empty.")
        return reasons
    unsupported_levels = [str(level) for level in levels if str(level) not in CLEANUP_ALLOWED_LEVELS]
    if unsupported_levels:
        reasons.append(f"cleanup_rollback.allowed_levels contains unsupported levels: {unsupported_levels}.")
    if any("C5" in str(level) for level in levels):
        separate = cleanup.get("separate_approvals") or cleanup.get("separate_approved_levels") or []
        if not isinstance(separate, list) or not any("C5" in str(level) for level in separate):
            reasons.append("C5 uninstall/reinstall requires separate approval.")
    return reasons


def _validate_reviews(metadata: dict[str, Any]) -> list[str]:
    reasons = []
    reviews = metadata.get("required_reviews")
    if not isinstance(reviews, dict):
        return ["required_reviews must be an object."]
    for reviewer in REQUIRED_REVIEWERS:
        status = _normalize_enum(reviews.get(reviewer), REVIEW_STATUSES, default="pending")
        if status not in PASSING_REVIEW_STATUSES:
            reasons.append(f"required_reviews.{reviewer} must be approved or confirmed.")
    return reasons


def _normalized_summary(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": metadata.get("task_id", DEFAULT_TASK_ID),
        "scope_version": metadata.get("scope_version", "unknown"),
        "approval_status": _normalize_enum(metadata.get("approval_status"), APPROVAL_STATUSES, default="blocked"),
        "approval_evidence_status": _normalize_enum(
            metadata.get("approval_evidence_status"),
            EVIDENCE_STATUSES,
            default="unknown",
        ),
        "approved_build_alias": (
            metadata.get("approved_build_apk", {}).get("build_alias")
            if isinstance(metadata.get("approved_build_apk"), dict)
            else None
        ),
        "approved_device_aliases": _normalized_device_aliases(metadata),
        "runtime_scope": (
            _stringify_scope(metadata.get("runtime_execution", {}).get("allowed_scope"))
            if isinstance(metadata.get("runtime_execution"), dict)
            else []
        ),
        "fixture_statuses": metadata.get("fixtures") if isinstance(metadata.get("fixtures"), dict) else {},
        "required_reviews": metadata.get("required_reviews") if isinstance(metadata.get("required_reviews"), dict) else {},
    }


def _normalized_device_aliases(metadata: dict[str, Any]) -> list[str]:
    if not isinstance(metadata.get("approved_targets"), dict):
        return []
    aliases = metadata["approved_targets"].get("device_aliases")
    if aliases is None:
        aliases = metadata["approved_targets"].get("approved_device_aliases")
    if not isinstance(aliases, list):
        return []
    return [alias for alias in aliases if isinstance(alias, str) and alias.strip()]


def build_report(metadata_path: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    metadata, load_reasons = _load_metadata(metadata_path)
    blocked_reasons = list(load_reasons)

    if metadata:
        blocked_reasons.extend(_validate_required_fields(metadata))
        blocked_reasons.extend(_validate_identity(metadata))

        approval_status = _normalize_enum(metadata.get("approval_status"), APPROVAL_STATUSES, default="blocked")
        if approval_status != "approved":
            blocked_reasons.append("approval_status must be approved.")

        approval_evidence_status = _normalize_enum(
            metadata.get("approval_evidence_status"),
            EVIDENCE_STATUSES,
            default="unknown",
        )
        if approval_evidence_status != "confirmed":
            blocked_reasons.append("approval_evidence_status must be confirmed.")

        if _is_expired(metadata.get("expires_at"), now):
            blocked_reasons.append("expires_at must be valid and not expired.")

        blocked_reasons.extend(_validate_approved_by_role(metadata))
        blocked_reasons.extend(_validate_build(metadata))
        blocked_reasons.extend(_validate_targets(metadata))
        blocked_reasons.extend(_validate_runtime_scope(metadata))
        blocked_reasons.extend(_validate_synthetic_user(metadata))
        blocked_reasons.extend(_validate_fixtures(metadata))
        blocked_reasons.extend(_validate_evidence_capture(metadata))
        blocked_reasons.extend(_validate_cleanup(metadata))
        blocked_reasons.extend(_validate_reviews(metadata))
        blocked_reasons.extend(_scan_for_forbidden_public_values(metadata))

    blocked_reasons = sorted(set(blocked_reasons))
    approval_decision = "blocked" if blocked_reasons else "approved_for_limited_runtime"
    warnings = [
        "Approval validation does not run the app and cannot produce runtime pass/fail evidence.",
        "Runtime execution remains not_run until a separate approved TASK-005 run records evidence.",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "task_id": metadata.get("task_id", DEFAULT_TASK_ID) if metadata else DEFAULT_TASK_ID,
        "approval_decision": approval_decision,
        "runtime_execution_status": RUNTIME_EXECUTION_STATUS,
        "runtime_evidence_status": "unknown",
        "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
        "blocked_reasons": blocked_reasons,
        "warnings": warnings,
        "normalized_summary": _normalized_summary(metadata),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate public-safe approval metadata.")
    parser.add_argument("--metadata", type=Path, required=True, help="Approval metadata JSON file.")
    parser.add_argument("--output", type=Path, default=None, help="Optional output report JSON path.")
    args = parser.parse_args(argv)

    report = build_report(args.metadata)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

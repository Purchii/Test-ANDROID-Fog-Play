"""Generate a public-safe ADB device inventory preflight report.

The default command performs no ADB calls. With --allow-adb, this tool runs
only an explicit inventory allowlist and never installs, launches, captures
logs/screens/videos, or interacts with the application under test.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SCHEMA_VERSION = "task-016-adb-device-inventory-preflight-v1"
PUBLIC_SCHEMA_VERSION = "task-016-device-inventory-public-safe-v1"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_CONDITIONAL"
RUNTIME_EXECUTION_STATUS = "not_run"
APK_INSTALL_STATUS = "not_run"
APP_LAUNCH_STATUS = "not_run"

SAFE_GETPROP_FIELDS = (
    "ro.product.manufacturer",
    "ro.product.model",
    "ro.build.version.release",
    "ro.build.version.sdk",
    "ro.build.version.security_patch",
)

DEVICE_ALIAS_RE = re.compile(r"^(tv|stb|phone|tablet|emulator|unknown)-[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{3}$")
RUNTIME_PROFILE_ALIAS_RE = re.compile(
    r"^(tv|stb|phone|tablet|emulator|unknown)-[a-z0-9]+(?:-[a-z0-9]+)*-a[0-9]{1,2}-[0-9]{3}$"
)
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
IMEI_RE = re.compile(r"\b\d{15}\b")
ANDROID_ID_RE = re.compile(r"\b[0-9a-fA-F]{16}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<![\w+])\+?\d[\d\s().-]{8,}\d(?!\w)")
FINGERPRINT_RE = re.compile(r"\b[a-z0-9_.-]+/[a-z0-9_.-]+/[a-z0-9_.-]+:[0-9][^ \n\r\t]*", re.IGNORECASE)
OTP_RE = re.compile(r"\botp\s*[:=]\s*\S+", re.IGNORECASE)
SECRET_PAIR_RE = re.compile(
    r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|bearer)\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)
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
BLOCKED_LABEL_PATTERN = r"oleg|living\s*[-_ ]?\s*room|home|bedroom|office|kitchen|personal|private"
BLOCKED_PUBLIC_LABEL_RE = re.compile(rf"\b(?:{BLOCKED_LABEL_PATTERN})\b", re.IGNORECASE)
ALIAS_RE = DEVICE_ALIAS_RE
RUNTIME_ALIAS_RE = RUNTIME_PROFILE_ALIAS_RE

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_adb(argv: list[str], runner: Runner) -> tuple[str, int]:
    try:
        completed = runner(argv, capture_output=True, text=True, timeout=30, check=False)
    except OSError as exc:
        return str(exc), 127
    return completed.stdout.strip(), completed.returncode


def _load_json(path: Path | None, default: Any) -> Any:
    if path is None or not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _path_is_under_qa_local(path: Path | None) -> bool:
    if path is None:
        return True
    normalized = path.as_posix()
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    return parts[:1] == [".qa_local"] and ".." not in parts


def _local_only_path_errors(*paths: tuple[str, Path | None]) -> list[str]:
    return [
        f"{label} must stay under .qa_local/ because it may contain local-only identifiers."
        for label, path in paths
        if not _path_is_under_qa_local(path)
    ]


def _parse_adb_devices(output: str) -> list[dict[str, Any]]:
    devices = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("List of devices"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        details: dict[str, str] = {}
        for token in parts[2:]:
            if ":" in token:
                key, value = token.split(":", 1)
                details[key] = value
        devices.append({"serial": serial, "state": state, "details": details})
    return devices


def _safe_slug(value: str, default: str = "aosp") -> str:
    scrubbed = BLOCKED_PUBLIC_LABEL_RE.sub("", value.strip().lower())
    normalized = re.sub(r"[^a-z0-9]+", "-", scrubbed).strip("-")
    if not normalized:
        normalized = default
    for blocked in BLOCKED_ALIAS_LABELS:
        normalized = normalized.replace(blocked, "")
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized[:24] or default


def _android_major(release: str) -> int:
    match = re.search(r"\d+", release or "")
    return int(match.group(0)) if match else 0


def _api_level(value: str) -> int:
    try:
        return int(str(value).strip())
    except ValueError:
        return 0


def _detect_form_factor(features: list[str], manufacturer: str, model: str) -> tuple[str, str, str]:
    feature_text = "\n".join(features).lower()
    model_text = f"{manufacturer} {model}".lower()
    looks_stb = "box" in model_text or "stb" in model_text or "stick" in model_text or "dongle" in model_text
    if "android.software.leanback" in feature_text or "android.hardware.type.television" in feature_text:
        if looks_stb:
            return "stb", "android_tv", "dpad_remote"
        return "tv", "android_tv", "dpad_remote"
    if "tv" in model_text or looks_stb:
        return "stb", "android_stb", "dpad_remote"
    if "android.hardware.touchscreen" in feature_text:
        return "phone", "android_phone_secondary", "touch"
    return "stb", "aosp_stb", "dpad_remote"


def _screen_class(size_output: str) -> str:
    match = re.search(r"(\d+)x(\d+)", size_output)
    if not match:
        return "unknown"
    width, height = int(match.group(1)), int(match.group(2))
    longest = max(width, height)
    if longest >= 3800:
        return "4k_or_unknown"
    if longest >= 1900:
        return "fhd_or_unknown"
    if longest >= 1200:
        return "hd_or_unknown"
    return "mobile_or_unknown"


def _google_play_services_from_features(features: list[str]) -> str:
    text = "\n".join(features).lower()
    if "google" in text or "com.google.android.feature" in text:
        return "yes"
    return "unknown"


def _has_forbidden_public_value(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return False
    return bool(
        IP_RE.search(text)
        or MAC_RE.search(text)
        or IMEI_RE.search(text)
        or ANDROID_ID_RE.search(text)
        or EMAIL_RE.search(text)
        or (PHONE_RE.search(text) and sum(char.isdigit() for char in text) >= 10)
        or FINGERPRINT_RE.search(text)
        or OTP_RE.search(text)
        or SECRET_PAIR_RE.search(text)
        or BLOCKED_PUBLIC_LABEL_RE.search(text)
    )


def _sanitize_public_text(value: Any, known_raw_values: set[str] | None = None) -> tuple[str, bool]:
    text = str(value).strip() if value is not None else "unknown"
    original = text
    replacements = (
        (EMAIL_RE, "[REDACTED_EMAIL]"),
        (IP_RE, "[REDACTED_IP]"),
        (MAC_RE, "[REDACTED_DEVICE_ID]"),
        (IMEI_RE, "[REDACTED_DEVICE_ID]"),
        (ANDROID_ID_RE, "[REDACTED_DEVICE_ID]"),
        (FINGERPRINT_RE, "[REDACTED_FINGERPRINT]"),
        (OTP_RE, "otp=[REDACTED_OTP]"),
        (SECRET_PAIR_RE, r"\1=[REDACTED_SECRET]"),
    )
    for pattern, replacement in replacements:
        text = pattern.sub(replacement, text)
    text = BLOCKED_PUBLIC_LABEL_RE.sub("[REDACTED_LABEL]", text)
    if PHONE_RE.search(text) and sum(char.isdigit() for char in text) >= 10:
        text = PHONE_RE.sub("[REDACTED_PHONE]", text)
    for raw in sorted(known_raw_values or set(), key=len, reverse=True):
        if raw:
            text = text.replace(raw, "[REDACTED_DEVICE_ID]")
    return text or "unknown", text != original


def _sanitize_public_json(value: Any, known_raw_values: set[str] | None = None) -> tuple[Any, bool]:
    forbidden_keys = {"serial", "raw_serial", "ip", "mac", "imei", "android_id", "google_account", "fingerprint"}
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        redacted = False
        for key, child in value.items():
            if key.lower() in forbidden_keys:
                redacted = True
                continue
            sanitized_child, child_redacted = _sanitize_public_json(child, known_raw_values)
            sanitized[key] = sanitized_child
            redacted = redacted or child_redacted
        return sanitized, redacted
    if isinstance(value, list):
        sanitized_items = []
        redacted = False
        for child in value:
            sanitized_child, child_redacted = _sanitize_public_json(child, known_raw_values)
            sanitized_items.append(sanitized_child)
            redacted = redacted or child_redacted
        return sanitized_items, redacted
    if isinstance(value, str):
        return _sanitize_public_text(value, known_raw_values)
    return value, False


def _public_safety_findings(value: Any, known_raw_values: set[str] | None = None, path: str = "$") -> list[str]:
    forbidden_keys = {"serial", "raw_serial", "ip", "mac", "imei", "android_id", "google_account", "fingerprint"}
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in forbidden_keys:
                findings.append(f"Forbidden public identifier key at {path}.{key}.")
            findings.extend(_public_safety_findings(child, known_raw_values, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_public_safety_findings(child, known_raw_values, f"{path}[{index}]"))
    elif isinstance(value, str):
        sanitized, redacted = _sanitize_public_text(value, known_raw_values)
        if redacted or sanitized != value:
            findings.append(f"Forbidden public identifier-like value at {path}.")
    return sorted(set(findings))


def _public_payload_is_safe(payload: Any) -> bool:
    if isinstance(payload, dict):
        return all(_public_payload_is_safe(value) for value in payload.values())
    if isinstance(payload, list):
        return all(_public_payload_is_safe(value) for value in payload)
    return not _has_forbidden_public_value(payload)


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
    if BLOCKED_PUBLIC_LABEL_RE.search(normalized):
        return True
    if _tokens_without_allowed_phone(normalized, form_factor) & RESERVED_ALIAS_TOKENS:
        return True
    return bool(
        IP_RE.search(normalized)
        or MAC_RE.search(normalized)
        or IMEI_RE.search(normalized)
        or ANDROID_ID_RE.search(normalized)
        or FINGERPRINT_RE.search(normalized)
        or EMAIL_RE.search(normalized)
        or (PHONE_RE.search(normalized) and sum(char.isdigit() for char in normalized) >= 10)
        or OTP_RE.search(normalized)
        or SECRET_PAIR_RE.search(normalized)
    )


def _alias_map_entry(serial: str, raw: dict[str, Any], existing_map: dict[str, Any]) -> dict[str, str]:
    if isinstance(existing_map.get(serial), dict):
        entry = existing_map[serial]
        if isinstance(entry.get("device_alias"), str) and isinstance(entry.get("index"), str):
            return {"device_alias": entry["device_alias"], "index": entry["index"]}

    manufacturer = _safe_slug(raw.get("manufacturer", "aosp"))
    form_factor = raw.get("form_factor", "unknown")
    index = f"{len(existing_map) + 1:03d}"
    return {"device_alias": f"{form_factor}-{manufacturer}-{index}", "index": index}


def _runtime_profile_alias(device_alias: str, android_major: int, index: str) -> str:
    prefix = device_alias.rsplit("-", 1)[0]
    major = android_major if android_major > 0 else 0
    return f"{prefix}-a{major}-{index}"


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


def _collect_device(serial: str, runner: Runner) -> dict[str, Any]:
    props = {}
    for field in SAFE_GETPROP_FIELDS:
        stdout, returncode = _run_adb(["adb", "-s", serial, "shell", "getprop", field], runner)
        props[field] = stdout if returncode == 0 else ""
    size, _ = _run_adb(["adb", "-s", serial, "shell", "wm", "size"], runner)
    density, _ = _run_adb(["adb", "-s", serial, "shell", "wm", "density"], runner)
    features_output, _ = _run_adb(["adb", "-s", serial, "shell", "pm", "list", "features"], runner)
    features = [line.strip() for line in features_output.splitlines() if line.strip()]
    form_factor, category, input_method = _detect_form_factor(
        features,
        props.get("ro.product.manufacturer", ""),
        props.get("ro.product.model", ""),
    )
    return {
        "serial": serial,
        "manufacturer": props.get("ro.product.manufacturer", ""),
        "model": props.get("ro.product.model", ""),
        "android_release": props.get("ro.build.version.release", ""),
        "api_level": _api_level(props.get("ro.build.version.sdk", "")),
        "security_patch": props.get("ro.build.version.security_patch", ""),
        "wm_size": size,
        "wm_density": density,
        "features": features,
        "form_factor": form_factor,
        "category": category,
        "input_method": input_method,
        "google_play_services": _google_play_services_from_features(features),
        "screen_class": _screen_class(size),
    }


def _public_device(raw: dict[str, Any], alias_entry: dict[str, str]) -> dict[str, Any]:
    android_major = _android_major(raw.get("android_release", ""))
    category = raw.get("category", "aosp_stb")
    confidence = "heuristic"
    manual_review_required = True
    if category == "aosp_stb" or raw.get("google_play_services") == "unknown":
        confidence = "heuristic"
        manual_review_required = True
    return {
        "device_alias": alias_entry["device_alias"],
        "runtime_profile_alias": _runtime_profile_alias(alias_entry["device_alias"], android_major, alias_entry["index"]),
        "category": category,
        "priority": "P0" if category in {"android_tv", "google_tv", "android_stb", "aosp_stb"} else "P2",
        "form_factor": raw.get("form_factor", "unknown"),
        "input_method": raw.get("input_method", "unknown"),
        "android_major": android_major,
        "api_level": raw.get("api_level", 0),
        "screen_class": raw.get("screen_class", "unknown"),
        "google_play_services": raw.get("google_play_services", "unknown"),
        "adb_available": "yes",
        "classification_confidence": confidence,
        "manual_review_required": manual_review_required,
        "forbidden_identifiers_excluded": True,
        "runtime_execution_status": RUNTIME_EXECUTION_STATUS,
        "apk_install_status": APK_INSTALL_STATUS,
        "app_launch_status": APP_LAUNCH_STATUS,
    }


def build_report(
    *,
    allow_adb: bool = False,
    alias_map_path: Path | None = None,
    runner: Runner = subprocess.run,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    blocked_reasons: list[str] = []
    raw_payload: dict[str, Any] = {
        "schema_version": "task-016-raw-adb-device-inventory-local-v1",
        "generated_at_utc": _utc_now(),
        "devices": [],
    }
    alias_map = _load_json(alias_map_path, {})
    if not isinstance(alias_map, dict):
        alias_map = {}

    if not allow_adb:
        blocked_reasons.append("--allow-adb was not provided; ADB inventory was not run.")
        public_payload = _public_inventory([])
        report = _preflight_report("blocked", blocked_reasons, 0)
        return report, raw_payload, alias_map, public_payload

    devices_output, returncode = _run_adb(["adb", "devices", "-l"], runner)
    if returncode != 0:
        blocked_reasons.append("adb devices -l failed.")
        raw_payload["adb_devices_l_output"] = devices_output
        public_payload = _public_inventory([])
        report = _preflight_report("blocked", blocked_reasons + ["No authorized ADB devices were collected."], 0)
        return report, raw_payload, alias_map, public_payload
    adb_devices = _parse_adb_devices(devices_output)
    raw_payload["adb_devices_l_output"] = devices_output
    raw_payload["devices"] = adb_devices
    collected: list[dict[str, Any]] = []
    for device in adb_devices:
        if device.get("state") != "device":
            blocked_reasons.append(f"ADB target {device.get('state', 'unknown')} was skipped.")
            continue
        serial = str(device["serial"])
        raw_device = _collect_device(serial, runner)
        collected.append(raw_device)
        raw_payload.setdefault("collected_device_details", []).append(raw_device)
        alias_map[serial] = _alias_map_entry(serial, raw_device, alias_map)

    public_devices = [_public_device(raw_device, alias_map[str(raw_device["serial"])]) for raw_device in collected]
    public_payload = _public_inventory(public_devices)
    if not public_devices:
        blocked_reasons.append("No authorized ADB devices were collected.")
    if not _public_payload_is_safe(public_payload):
        blocked_reasons.append("Public-safe inventory sanitizer detected forbidden identifier-like values.")
        public_payload["devices"] = []
    if public_payload["devices"] and not _aliases_are_valid(public_payload):
        blocked_reasons.append("Public-safe inventory sanitizer detected unsafe alias-map values.")
        public_payload["devices"] = []

    status = "blocked" if blocked_reasons else "not_run"
    report = _preflight_report(status, blocked_reasons, len(public_payload["devices"]))
    return report, raw_payload, alias_map, public_payload


def _public_inventory(devices: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "source": "adb_inventory_sanitized_local_output",
        "runtime_execution_status": RUNTIME_EXECUTION_STATUS,
        "apk_install_status": APK_INSTALL_STATUS,
        "app_launch_status": APP_LAUNCH_STATUS,
        "devices": devices,
        "redaction_guarantees": {
            "adb_serial_excluded": True,
            "ip_excluded": True,
            "mac_excluded": True,
            "imei_excluded": True,
            "android_id_excluded": True,
            "google_account_excluded": True,
            "full_build_fingerprint_excluded": True,
            "phone_otp_excluded": True,
        },
    }


def build_inventory(
    *,
    allow_adb: bool = False,
    raw_output: Path = Path(".qa_local/devices/raw_adb_devices.json"),
    alias_map_path: Path = Path(".qa_local/devices/serial_alias_map.json"),
    public_output: Path = Path(".qa_local/devices/device_inventory.public_safe.generated.json"),
    report_path: Path = Path(".qa_local/devices/preflight_report.json"),
    write_files: bool = True,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    raw_output = Path(raw_output)
    alias_map_path = Path(alias_map_path)
    public_output = Path(public_output)
    report_path = Path(report_path)

    path_errors = _local_only_path_errors(
        ("--raw-output", raw_output),
        ("--alias-map", alias_map_path),
        ("--public-output", public_output),
        ("--report", report_path),
    )
    if allow_adb and path_errors:
        return _preflight_report("blocked", path_errors, 0)

    report, raw_payload, alias_map, public_payload = build_report(
        allow_adb=allow_adb,
        alias_map_path=alias_map_path,
        runner=runner,
    )

    known_raw_values = {str(device.get("serial")) for device in raw_payload.get("devices", []) if device.get("serial")}
    public_payload, redacted = _sanitize_public_json(public_payload, known_raw_values)
    findings = _public_safety_findings(public_payload, known_raw_values)
    public_payload["redaction_status"] = "redacted" if redacted else "not_applicable"
    public_payload["public_safety_findings"] = findings
    if findings:
        report["overall_status"] = "blocked"
        report["blocked_reasons"] = sorted(set(report["blocked_reasons"] + findings))
    if public_payload["devices"] and not _aliases_are_valid(public_payload):
        report["overall_status"] = "blocked"
        report["blocked_reasons"] = sorted(
            set(report["blocked_reasons"] + ["Generated aliases failed public-safe grammar validation."])
        )

    if write_files:
        _write_json(raw_output, raw_payload)
        _write_json(alias_map_path, alias_map)
        _write_json(public_output, public_payload)
        _write_json(report_path, report)
    return report


def _preflight_report(status: str, blocked_reasons: list[str], public_device_count: int) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "task_id": "TASK-016",
        "overall_status": status,
        "runtime_execution_status": RUNTIME_EXECUTION_STATUS,
        "apk_install_status": APK_INSTALL_STATUS,
        "app_launch_status": APP_LAUNCH_STATUS,
        "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
        "public_device_count": public_device_count,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "warnings": [
            "Inventory preflight does not install, launch, smoke test, capture logcat, screenshots, videos or app runtime evidence.",
            "Raw ADB serials and transport details are local-only under .qa_local/devices/.",
        ],
        "allowed_adb_commands": [
            "adb devices -l",
            *[f"adb -s <serial> shell getprop {field}" for field in SAFE_GETPROP_FIELDS],
            "adb -s <serial> shell wm size",
            "adb -s <serial> shell wm density",
            "adb -s <serial> shell pm list features",
        ],
        "forbidden_actions": [
            "adb install",
            "am start",
            "monkey",
            "logcat",
            "screenshots",
            "screenrecord",
            "apk_runtime_smoke",
            "webview",
            "webrtc_stream_media_playback",
            "payment_subscription_purchase",
            "account_profile_mutation",
            "security_bypass",
            "decompilation_patching_resigning",
        ],
    }


def _aliases_are_valid(public_payload: dict[str, Any]) -> bool:
    for device in public_payload.get("devices", []):
        device_alias = device.get("device_alias", "")
        runtime_profile_alias = device.get("runtime_profile_alias", "")
        form_factor = device.get("form_factor")
        android_major = device.get("android_major")
        if DEVICE_ALIAS_RE.fullmatch(device_alias) is None or _alias_has_forbidden_content(device_alias, form_factor):
            return False
        if RUNTIME_PROFILE_ALIAS_RE.fullmatch(runtime_profile_alias) is None or _alias_has_forbidden_content(
            runtime_profile_alias,
            form_factor,
        ):
            return False
        if isinstance(android_major, int) and android_major > 0 and not _runtime_alias_matches_device(
            device_alias,
            runtime_profile_alias,
            android_major,
        ):
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate TASK-016 ADB device inventory preflight.")
    parser.add_argument("--allow-adb", action="store_true", help="Run the approved ADB inventory allowlist.")
    parser.add_argument("--raw-output", type=Path, default=None, help="Local-only raw ADB inventory JSON output.")
    parser.add_argument("--alias-map", type=Path, default=None, help="Local-only serial to alias map JSON.")
    parser.add_argument("--public-output", type=Path, default=None, help="Public-safe generated inventory JSON output.")
    parser.add_argument("--report", type=Path, default=None, help="Local preflight report JSON output.")
    args = parser.parse_args(argv)

    report = build_inventory(
        allow_adb=args.allow_adb,
        raw_output=args.raw_output or Path(".qa_local/devices/raw_adb_devices.json"),
        alias_map_path=args.alias_map or Path(".qa_local/devices/serial_alias_map.json"),
        public_output=args.public_output or Path(".qa_local/devices/device_inventory.public_safe.generated.json"),
        report_path=args.report or Path(".qa_local/devices/preflight_report.json"),
        write_files=args.allow_adb
        or args.raw_output is not None
        or args.alias_map is not None
        or args.public_output is not None
        or args.report is not None,
    )
    public_payload = _load_json(args.public_output, _public_inventory([])) if args.public_output else _public_inventory([])
    if public_payload["devices"] and not _aliases_are_valid(public_payload):
        report["overall_status"] = "blocked"
        report["blocked_reasons"].append("Generated aliases failed public-safe grammar validation.")

    if args.report is None and args.public_output is None:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

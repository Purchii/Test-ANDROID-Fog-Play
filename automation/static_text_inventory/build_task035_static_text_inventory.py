"""Build TASK-035 static text inventory from local sanitized static inputs.

This tool is static/offline only. It may read ignored local reverse-analysis
artifacts, but it writes raw text values only to ignored local storage and emits
a public-safe summary with counts, hashes and categories only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "TASK-035"
SCHEMA_VERSION = "task035-static-text-inventory-v1"
TOOL_NAME = "build_task035_static_text_inventory"

DEFAULT_SOURCE = Path("qa_reverse_analysis/raw/apk_analysis_sanitized.json")
DEFAULT_LOCAL_INVENTORY = Path(".qa_local/static_text_inventory/task035_available_static_text_inventory.local.jsonl")
DEFAULT_REPORT = Path("docs/qa/reports/task035_static_text_inventory.summary.json")

FORBIDDEN_PUBLIC_FLAGS = {
    "raw_static_text_values_public",
    "raw_url_or_endpoint_values_public",
    "raw_token_secret_or_session_values_public",
    "raw_phone_otp_captcha_values_public",
    "raw_payment_account_values_public",
    "raw_device_identifier_values_public",
    "raw_local_paths_public",
    "apk_runtime_or_adb_execution_performed",
    "apk_patch_decompile_or_source_used",
    "live_backend_or_network_calls_performed",
}

URL_OR_DOMAIN_RE = re.compile(r"\b(?:https?|wss?)://|\b[a-z0-9-]+(?:\.[a-z0-9-]+)+\b", re.IGNORECASE)
SECRET_RE = re.compile(r"\b(?:authorization|bearer|cookie|session|token|secret|password|api[_-]?key|otp)\b", re.I)
PHONE_OTP_RE = re.compile(r"(?:\+?\d[\d ()-]{8,}\d|\b(?:otp|sms|captcha|code)\b)", re.I)
PAYMENT_RE = re.compile(r"\b(?:pay|payment|billing|bank|card|receipt|invoice|account|balance|₽|rub)\b", re.I)
DEVICE_RE = re.compile(r"\b(?:device|android[_ -]?id|serial|imei|imsi|mac|controller|gamepad)\b", re.I)
LOCAL_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])", re.I)
FORMAT_RE = re.compile(r"%(?:\d+\$)?[sdfoxXeEgG%]")
MOJIBAKE_RE = re.compile(r"(?:Ð|Ñ|Â|â)")
VECTOR_PATH_RE = re.compile(r"^M\d+(?:[.,\sA-Za-z0-9-]+)$")
UTC_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

ALLOWED_TOP_LEVEL_KEYS = {
    "blocked_reasons",
    "classification_summary",
    "coverage_contract",
    "evidence_status",
    "execution_boundaries",
    "follow_up_actions",
    "generated_at_utc",
    "mode",
    "overall_status",
    "production_safety_classification",
    "public_safety",
    "sample_hash_ledger",
    "schema_version",
    "source_artifact",
    "static_text_inventory",
    "task_id",
    "tool_name",
}
ALLOWED_SOURCE_ARTIFACT_KEYS = {
    "raw_values_public",
    "source_alias",
    "source_kind",
    "source_path_public",
    "source_path_tracked",
}
ALLOWED_EXECUTION_BOUNDARY_KEYS = {
    "adb_execution_status",
    "apk_patch_or_modification_status",
    "decompile_or_smali_status",
    "live_backend_or_network_status",
    "runtime_execution_status",
}
ALLOWED_STATIC_INVENTORY_KEYS = {
    "available_raw_sample_inventory_count",
    "coverage_status",
    "duplicate_sample_hashes",
    "full_raw_value_list_available_in_source",
    "likely_ui_string_total_from_source",
    "local_inventory_artifact_public_ref",
    "localization_qualifier_count",
    "localization_qualifiers_observed",
    "missing_raw_value_count",
    "raw_text_values_public",
    "resource_key_sample_count",
    "resource_type_count",
}
ALLOWED_CLASSIFICATION_SUMMARY_KEYS = {"category_counts", "length_buckets", "redaction_class_counts"}
ALLOWED_LEDGER_KEYS = {"categories", "inventory_id", "length_bucket", "redaction_classes", "sha256_prefix"}
ALLOWED_COVERAGE_CONTRACT_KEYS = {
    "accessibility_behavior_status",
    "blocked_scope",
    "complete_scope",
    "fixed_dynamic_value_oracles_allowed",
    "runtime_visibility_status",
    "translation_quality_status",
}
ALLOWED_FOLLOW_UP_ACTION_KEYS = {"action", "production_safety_classification", "task"}
EXPECTED_FOLLOW_UP_ACTIONS = {
    "owner_input_or_local_artifact": {
        "action": "provide an approved local-only full static string export if exact 19187-value raw coverage is required",
        "production_safety_classification": "PROD_SAFE_LOCAL_STATIC_ONLY",
    },
    "runtime_text_visibility_audit": {
        "action": "map static strings to visible runtime screens only in a separate approved runtime task",
        "production_safety_classification": "PROD_CONDITIONAL",
    },
}
ALLOWED_CATEGORIES = {
    "auth_phone_otp_captcha_like",
    "cyrillic",
    "device_or_controller_like",
    "empty",
    "format_placeholder",
    "latin",
    "local_path_like",
    "long_text",
    "mojibake_suspected",
    "multiline",
    "non_ascii",
    "payment_or_account_like",
    "plain_text",
    "secret_keyword_like",
    "url_or_domain_like",
    "vector_path_like",
}
ALLOWED_REDACTION_CLASSES = {
    "device_identifier_or_controller_like",
    "endpoint_or_domain_like",
    "local_path_like",
    "payment_account_like",
    "phone_otp_captcha_like",
    "public_summary_hash_only",
    "token_secret_or_session_like",
}
ALLOWED_LENGTH_BUCKETS = {"len_0", "len_1_16", "len_17_40", "len_41_80", "len_81_160", "len_gt_160"}
REQUIRED_MISSING_FULL_LIST_BLOCKER = "full_raw_static_text_value_list_missing_from_available_sanitized_source"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValueError("source artifact cannot be read") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("source artifact is not valid JSON") from exc
    if not isinstance(loaded, dict):
        raise ValueError("source artifact must be a JSON object")
    return loaded


def _resources(source: dict[str, Any]) -> dict[str, Any]:
    resources = source.get("resources")
    if not isinstance(resources, dict):
        raise ValueError("source artifact missing resources object")
    return resources


def classify_text(value: str) -> dict[str, Any]:
    categories: set[str] = set()
    redaction_classes: set[str] = set()
    if not value:
        categories.add("empty")
    if "\n" in value:
        categories.add("multiline")
    if len(value) >= 80:
        categories.add("long_text")
    if any(ord(char) > 127 for char in value):
        categories.add("non_ascii")
    if any("A" <= char <= "Z" or "a" <= char <= "z" for char in value):
        categories.add("latin")
    if any("\u0400" <= char <= "\u04ff" for char in value):
        categories.add("cyrillic")
    if MOJIBAKE_RE.search(value):
        categories.add("mojibake_suspected")
    if FORMAT_RE.search(value):
        categories.add("format_placeholder")
    if URL_OR_DOMAIN_RE.search(value):
        categories.add("url_or_domain_like")
        redaction_classes.add("endpoint_or_domain_like")
    if SECRET_RE.search(value):
        categories.add("secret_keyword_like")
        redaction_classes.add("token_secret_or_session_like")
    if PHONE_OTP_RE.search(value):
        categories.add("auth_phone_otp_captcha_like")
        redaction_classes.add("phone_otp_captcha_like")
    if PAYMENT_RE.search(value):
        categories.add("payment_or_account_like")
        redaction_classes.add("payment_account_like")
    if DEVICE_RE.search(value):
        categories.add("device_or_controller_like")
        redaction_classes.add("device_identifier_or_controller_like")
    if LOCAL_PATH_RE.search(value):
        categories.add("local_path_like")
        redaction_classes.add("local_path_like")
    if VECTOR_PATH_RE.match(value.strip()):
        categories.add("vector_path_like")
    if not categories:
        categories.add("plain_text")
    if not redaction_classes:
        redaction_classes.add("public_summary_hash_only")
    return {
        "categories": sorted(categories),
        "redaction_classes": sorted(redaction_classes),
        "length": len(value),
        "line_count": value.count("\n") + 1,
    }


def _bucket(length: int) -> str:
    if length == 0:
        return "len_0"
    if length <= 16:
        return "len_1_16"
    if length <= 40:
        return "len_17_40"
    if length <= 80:
        return "len_41_80"
    if length <= 160:
        return "len_81_160"
    return "len_gt_160"


def _inventory_records(sample_values: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    for index, value in enumerate(sample_values, start=1):
        if not isinstance(value, str):
            continue
        digest = _sha256_text(value)
        record_id = f"stxt-sample-{index:04d}-{digest[:12]}"
        classification = classify_text(value)
        records.append(
            {
                "inventory_id": record_id,
                "source_scope": "local_sanitized_reverse_analysis_sample",
                "source_index": index,
                "sha256": digest,
                "duplicate_hash": digest in seen_hashes,
                "raw_text": value,
                **classification,
            }
        )
        seen_hashes.add(digest)
    return records


def _write_local_inventory(path: Path, records: list[dict[str, Any]]) -> None:
    normalized_parts = tuple(part.replace("\\", "/") for part in path.parts)
    if ".qa_local" not in normalized_parts or any(part in {"..", ""} for part in normalized_parts):
        raise ValueError("local inventory path must stay under .qa_local/")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def build_report(source_path: Path, local_inventory_path: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    source = _load_json(source_path)
    resources = _resources(source)
    sample_values = resources.get("likely_ui_strings_sample")
    if not isinstance(sample_values, list):
        raise ValueError("resources.likely_ui_strings_sample must be a list")
    likely_count = resources.get("likely_ui_string_count")
    if not isinstance(likely_count, int) or likely_count < 0:
        raise ValueError("resources.likely_ui_string_count must be a non-negative integer")

    localization_qualifiers = resources.get("localization_qualifiers")
    resource_type_names = resources.get("resource_type_names")
    resource_key_samples = resources.get("resource_key_samples")
    if not isinstance(localization_qualifiers, list):
        localization_qualifiers = []
    if not isinstance(resource_type_names, list):
        resource_type_names = []
    if not isinstance(resource_key_samples, list):
        resource_key_samples = []

    records = _inventory_records([value for value in sample_values if isinstance(value, str)])
    _write_local_inventory(local_inventory_path, records)

    category_counts: Counter[str] = Counter()
    redaction_counts: Counter[str] = Counter()
    length_buckets: Counter[str] = Counter()
    duplicate_hashes = 0
    for record in records:
        category_counts.update(record["categories"])
        redaction_counts.update(record["redaction_classes"])
        length_buckets.update([_bucket(record["length"])])
        if record["duplicate_hash"]:
            duplicate_hashes += 1

    missing_raw_value_count = max(likely_count - len(records), 0)
    full_raw_list_available = likely_count == len(records)
    coverage_status = "complete_full_raw_values_available" if full_raw_list_available else "blocked_by_missing_full_static_text_values_source"

    public_safety = {key: False for key in sorted(FORBIDDEN_PUBLIC_FLAGS)}
    public_safety.update(
        {
            "public_report_contains_raw_text_values": False,
            "public_report_contains_hashes_counts_categories_only": True,
            "local_inventory_contains_raw_text_values": True,
            "local_inventory_storage": "ignored_local_only",
        }
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "mode": "BOUNDED_AUTONOMOUS",
        "tool_name": TOOL_NAME,
        "overall_status": "partial_blocked" if not full_raw_list_available else "pass",
        "evidence_status": "likely",
        "production_safety_classification": "PROD_SAFE_LOCAL_STATIC_ONLY",
        "source_artifact": {
            "source_alias": "apk-analysis-sanitized-local-raw-json",
            "source_path_public": "local_ignored_reverse_analysis_artifact",
            "source_path_tracked": False,
            "source_kind": "sanitized_static_reverse_analysis_json",
            "raw_values_public": False,
        },
        "execution_boundaries": {
            "runtime_execution_status": "not_run",
            "adb_execution_status": "not_run",
            "apk_patch_or_modification_status": "not_run",
            "decompile_or_smali_status": "not_run",
            "live_backend_or_network_status": "not_run",
        },
        "static_text_inventory": {
            "coverage_status": coverage_status,
            "likely_ui_string_total_from_source": likely_count,
            "available_raw_sample_inventory_count": len(records),
            "missing_raw_value_count": missing_raw_value_count,
            "full_raw_value_list_available_in_source": full_raw_list_available,
            "local_inventory_artifact_public_ref": "local_only_ignored_task035_available_inventory",
            "raw_text_values_public": False,
            "localization_qualifier_count": len(localization_qualifiers),
            "localization_qualifiers_observed": sorted(str(value) for value in localization_qualifiers),
            "resource_type_count": len(resource_type_names),
            "resource_key_sample_count": len(resource_key_samples),
            "duplicate_sample_hashes": duplicate_hashes,
        },
        "classification_summary": {
            "category_counts": dict(sorted(category_counts.items())),
            "redaction_class_counts": dict(sorted(redaction_counts.items())),
            "length_buckets": dict(sorted(length_buckets.items())),
        },
        "sample_hash_ledger": [
            {
                "inventory_id": record["inventory_id"],
                "sha256_prefix": record["sha256"][:16],
                "categories": record["categories"],
                "redaction_classes": record["redaction_classes"],
                "length_bucket": _bucket(record["length"]),
            }
            for record in records
        ],
        "coverage_contract": {
            "complete_scope": "all raw static text values available in the local sanitized source artifact were inventoried",
            "blocked_scope": "full raw list for likely_ui_string_total_from_source is absent from the available sanitized artifact",
            "runtime_visibility_status": "unknown_not_run",
            "translation_quality_status": "unknown_not_run",
            "accessibility_behavior_status": "unknown_not_run",
            "fixed_dynamic_value_oracles_allowed": False,
        },
        "public_safety": public_safety,
        "blocked_reasons": [] if full_raw_list_available else ["full_raw_static_text_value_list_missing_from_available_sanitized_source"],
        "follow_up_actions": [
            {
                "task": "owner_input_or_local_artifact",
                "action": "provide an approved local-only full static string export if exact 19187-value raw coverage is required",
                "production_safety_classification": "PROD_SAFE_LOCAL_STATIC_ONLY",
            },
            {
                "task": "runtime_text_visibility_audit",
                "action": "map static strings to visible runtime screens only in a separate approved runtime task",
                "production_safety_classification": "PROD_CONDITIONAL",
            },
        ],
    }


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
    if not isinstance(value, str):
        return findings
    if URL_OR_DOMAIN_RE.search(value):
        findings.append(f"{path} contains raw URL/domain-like value")
    if LOCAL_PATH_RE.search(value):
        findings.append(f"{path} contains raw local path-like value")
    if re.fullmatch(r"[a-fA-F0-9]{64}", value):
        findings.append(f"{path} contains full raw hash value")
    return findings


def validate_public_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(ALLOWED_TOP_LEVEL_KEYS - set(report))
    unknown = sorted(set(report) - ALLOWED_TOP_LEVEL_KEYS)
    if missing:
        errors.append(f"report missing required fields: {missing}")
    if unknown:
        errors.append(f"report contains unknown top-level fields: {unknown}")
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if report.get("task_id") != TASK_ID:
        errors.append("task_id must be TASK-035")
    if report.get("mode") != "BOUNDED_AUTONOMOUS":
        errors.append("mode must be BOUNDED_AUTONOMOUS")
    generated_at = report.get("generated_at_utc")
    if not isinstance(generated_at, str) or not UTC_TIMESTAMP_RE.fullmatch(generated_at):
        errors.append("generated_at_utc must be an ISO-8601 UTC timestamp")
    if report.get("tool_name") != TOOL_NAME:
        errors.append(f"tool_name must be {TOOL_NAME}")
    if report.get("evidence_status") != "likely":
        errors.append("evidence_status must be likely")
    if report.get("production_safety_classification") != "PROD_SAFE_LOCAL_STATIC_ONLY":
        errors.append("production_safety_classification must be PROD_SAFE_LOCAL_STATIC_ONLY")
    source_artifact = report.get("source_artifact")
    if not isinstance(source_artifact, dict):
        errors.append("source_artifact must be an object")
    else:
        unknown_source_keys = sorted(set(source_artifact) - ALLOWED_SOURCE_ARTIFACT_KEYS)
        missing_source_keys = sorted(ALLOWED_SOURCE_ARTIFACT_KEYS - set(source_artifact))
        if unknown_source_keys:
            errors.append(f"source_artifact contains unknown fields: {unknown_source_keys}")
        if missing_source_keys:
            errors.append(f"source_artifact missing required fields: {missing_source_keys}")
        expected_source = {
            "source_alias": "apk-analysis-sanitized-local-raw-json",
            "source_path_public": "local_ignored_reverse_analysis_artifact",
            "source_path_tracked": False,
            "source_kind": "sanitized_static_reverse_analysis_json",
            "raw_values_public": False,
        }
        for key, expected in expected_source.items():
            if source_artifact.get(key) != expected:
                errors.append(f"source_artifact.{key} must be {expected!r}")
    public_safety = report.get("public_safety")
    if not isinstance(public_safety, dict):
        errors.append("public_safety must be an object")
    else:
        required_public_safety = sorted(
            FORBIDDEN_PUBLIC_FLAGS
            | {
                "public_report_contains_raw_text_values",
                "public_report_contains_hashes_counts_categories_only",
                "local_inventory_contains_raw_text_values",
                "local_inventory_storage",
            }
        )
        missing_public_safety = sorted(set(required_public_safety) - set(public_safety))
        unknown_public_safety = sorted(set(public_safety) - set(required_public_safety))
        if missing_public_safety:
            errors.append(f"public_safety missing required fields: {missing_public_safety}")
        if unknown_public_safety:
            errors.append(f"public_safety contains unknown fields: {unknown_public_safety}")
        for flag in sorted(FORBIDDEN_PUBLIC_FLAGS):
            if public_safety.get(flag) is not False:
                errors.append(f"public_safety.{flag} must be false")
        if public_safety.get("public_report_contains_hashes_counts_categories_only") is not True:
            errors.append("public report must be hash/count/category only")
        if public_safety.get("public_report_contains_raw_text_values") is not False:
            errors.append("public report must not contain raw text values")
        if public_safety.get("local_inventory_contains_raw_text_values") is not True:
            errors.append("local inventory must be explicitly marked as raw-text-containing")
        if public_safety.get("local_inventory_storage") != "ignored_local_only":
            errors.append("public_safety.local_inventory_storage must be ignored_local_only")
    boundaries = report.get("execution_boundaries", {})
    if not isinstance(boundaries, dict):
        errors.append("execution_boundaries must be an object")
    else:
        missing_boundary_keys = sorted(ALLOWED_EXECUTION_BOUNDARY_KEYS - set(boundaries))
        unknown_boundary_keys = sorted(set(boundaries) - ALLOWED_EXECUTION_BOUNDARY_KEYS)
        if missing_boundary_keys:
            errors.append(f"execution_boundaries missing required fields: {missing_boundary_keys}")
        if unknown_boundary_keys:
            errors.append(f"execution_boundaries contains unknown fields: {unknown_boundary_keys}")
        for key, value in boundaries.items():
            if value != "not_run":
                errors.append(f"execution_boundaries.{key} must be not_run")
    inventory = report.get("static_text_inventory", {})
    sample_count = None
    missing_count = None
    if not isinstance(inventory, dict):
        errors.append("static_text_inventory must be an object")
    else:
        missing_inventory_keys = sorted(ALLOWED_STATIC_INVENTORY_KEYS - set(inventory))
        unknown_inventory_keys = sorted(set(inventory) - ALLOWED_STATIC_INVENTORY_KEYS)
        if missing_inventory_keys:
            errors.append(f"static_text_inventory missing required fields: {missing_inventory_keys}")
        if unknown_inventory_keys:
            errors.append(f"static_text_inventory contains unknown fields: {unknown_inventory_keys}")
        total = inventory.get("likely_ui_string_total_from_source")
        sample_count = inventory.get("available_raw_sample_inventory_count")
        missing_count = inventory.get("missing_raw_value_count")
        if not isinstance(total, int) or not isinstance(sample_count, int) or not isinstance(missing_count, int):
            errors.append("static_text_inventory count fields must be integers")
        elif total < 0 or sample_count < 0 or missing_count < 0:
            errors.append("static_text_inventory count fields must be non-negative")
        elif sample_count > total:
            errors.append("available_raw_sample_inventory_count must not exceed likely_ui_string_total_from_source")
        elif total != sample_count + missing_count:
            errors.append("static_text_inventory counts must reconcile")
        elif missing_count > 0:
            if report.get("overall_status") != "partial_blocked":
                errors.append("overall_status must be partial_blocked when raw full-list values are missing")
            if inventory.get("coverage_status") != "blocked_by_missing_full_static_text_values_source":
                errors.append("coverage_status must be blocked_by_missing_full_static_text_values_source when raw full-list values are missing")
            if inventory.get("full_raw_value_list_available_in_source") is not False:
                errors.append("full_raw_value_list_available_in_source must be false when raw full-list values are missing")
            if REQUIRED_MISSING_FULL_LIST_BLOCKER not in report.get("blocked_reasons", []):
                errors.append("blocked_reasons must include missing full static text value list blocker")
        elif missing_count == 0:
            if report.get("overall_status") != "pass":
                errors.append("overall_status must be pass when full raw values are available")
            if inventory.get("coverage_status") != "complete_full_raw_values_available":
                errors.append("coverage_status must be complete_full_raw_values_available when no raw values are missing")
            if inventory.get("full_raw_value_list_available_in_source") is not True:
                errors.append("full_raw_value_list_available_in_source must be true when no raw values are missing")
        if inventory.get("raw_text_values_public") is not False:
            errors.append("static_text_inventory.raw_text_values_public must be false")
        if inventory.get("local_inventory_artifact_public_ref") != "local_only_ignored_task035_available_inventory":
            errors.append("static_text_inventory.local_inventory_artifact_public_ref must be the approved local-only alias")
        secondary_count_keys = {
            "duplicate_sample_hashes",
            "localization_qualifier_count",
            "resource_key_sample_count",
            "resource_type_count",
        }
        for key in sorted(secondary_count_keys):
            if not isinstance(inventory.get(key), int) or inventory.get(key) < 0:
                errors.append(f"static_text_inventory.{key} must be a non-negative integer")
        qualifiers = inventory.get("localization_qualifiers_observed")
        if not isinstance(qualifiers, list):
            errors.append("static_text_inventory.localization_qualifiers_observed must be a list")
        elif not all(isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_-]{0,32}", item) for item in qualifiers):
            errors.append("static_text_inventory.localization_qualifiers_observed must contain only short public-safe qualifiers")
        elif isinstance(inventory.get("localization_qualifier_count"), int) and inventory["localization_qualifier_count"] != len(qualifiers):
            errors.append("static_text_inventory.localization_qualifier_count must match localization_qualifiers_observed length")
    blocked_reasons = report.get("blocked_reasons")
    if not isinstance(blocked_reasons, list) or not all(isinstance(item, str) for item in blocked_reasons):
        errors.append("blocked_reasons must be a list of strings")
    elif any(item not in {REQUIRED_MISSING_FULL_LIST_BLOCKER} for item in blocked_reasons):
        errors.append("blocked_reasons contains unsupported reason")

    ledger = report.get("sample_hash_ledger")
    if not isinstance(ledger, list):
        errors.append("sample_hash_ledger must be a list")
        ledger = []
    if isinstance(sample_count, int) and len(ledger) != sample_count:
        errors.append("sample_hash_ledger length must match available_raw_sample_inventory_count")
    ledger_category_counts: Counter[str] = Counter()
    ledger_redaction_counts: Counter[str] = Counter()
    ledger_length_buckets: Counter[str] = Counter()
    for item in ledger:
        if not isinstance(item, dict):
            errors.append("sample_hash_ledger entries must be objects")
            continue
        unknown_ledger_keys = sorted(set(item) - ALLOWED_LEDGER_KEYS)
        missing_ledger_keys = sorted(ALLOWED_LEDGER_KEYS - set(item))
        if unknown_ledger_keys:
            errors.append(f"sample_hash_ledger entries contain unknown fields: {unknown_ledger_keys}")
        if missing_ledger_keys:
            errors.append(f"sample_hash_ledger entries missing required fields: {missing_ledger_keys}")
        if "sha256" in item or "raw_text" in item:
            errors.append("sample_hash_ledger entries must not publish raw_text or full sha256")
        inventory_id = item.get("inventory_id")
        if not isinstance(inventory_id, str) or not re.fullmatch(r"stxt-sample-\d{4}-[a-f0-9]{12}", inventory_id):
            errors.append("sample_hash_ledger inventory_id must be a safe TASK-035 sample id")
        prefix = item.get("sha256_prefix")
        if not isinstance(prefix, str) or not re.fullmatch(r"[a-f0-9]{16}", prefix):
            errors.append("sample_hash_ledger sha256_prefix must be a 16-char hex prefix")
        categories = item.get("categories")
        if not isinstance(categories, list) or not all(isinstance(value, str) and value in ALLOWED_CATEGORIES for value in categories):
            errors.append("sample_hash_ledger categories must be known category slugs")
        else:
            ledger_category_counts.update(categories)
        redaction_classes = item.get("redaction_classes")
        if not isinstance(redaction_classes, list) or not all(isinstance(value, str) and value in ALLOWED_REDACTION_CLASSES for value in redaction_classes):
            errors.append("sample_hash_ledger redaction_classes must be known redaction class slugs")
        else:
            ledger_redaction_counts.update(redaction_classes)
        length_bucket = item.get("length_bucket")
        if not isinstance(length_bucket, str) or length_bucket not in ALLOWED_LENGTH_BUCKETS:
            errors.append("sample_hash_ledger length_bucket must be a known length bucket")
        else:
            ledger_length_buckets.update([length_bucket])
    classification_summary = report.get("classification_summary")
    if not isinstance(classification_summary, dict):
        errors.append("classification_summary must be an object")
    else:
        unknown_summary_keys = sorted(set(classification_summary) - ALLOWED_CLASSIFICATION_SUMMARY_KEYS)
        missing_summary_keys = sorted(ALLOWED_CLASSIFICATION_SUMMARY_KEYS - set(classification_summary))
        if unknown_summary_keys:
            errors.append(f"classification_summary contains unknown fields: {unknown_summary_keys}")
        if missing_summary_keys:
            errors.append(f"classification_summary missing required fields: {missing_summary_keys}")
        expected_summaries = {
            "category_counts": (ledger_category_counts, ALLOWED_CATEGORIES),
            "redaction_class_counts": (ledger_redaction_counts, ALLOWED_REDACTION_CLASSES),
            "length_buckets": (ledger_length_buckets, ALLOWED_LENGTH_BUCKETS),
        }
        for key, (expected_counts, allowed_keys) in expected_summaries.items():
            actual = classification_summary.get(key)
            if not isinstance(actual, dict) or not all(isinstance(name, str) and name in allowed_keys and isinstance(count, int) and count >= 0 for name, count in actual.items()):
                errors.append(f"classification_summary.{key} must be a known-count object")
            elif actual != dict(sorted(expected_counts.items())):
                errors.append(f"classification_summary.{key} must reconcile with sample_hash_ledger")
    coverage_contract = report.get("coverage_contract")
    if not isinstance(coverage_contract, dict):
        errors.append("coverage_contract must be an object")
    else:
        unknown_contract_keys = sorted(set(coverage_contract) - ALLOWED_COVERAGE_CONTRACT_KEYS)
        missing_contract_keys = sorted(ALLOWED_COVERAGE_CONTRACT_KEYS - set(coverage_contract))
        if unknown_contract_keys:
            errors.append(f"coverage_contract contains unknown fields: {unknown_contract_keys}")
        if missing_contract_keys:
            errors.append(f"coverage_contract missing required fields: {missing_contract_keys}")
        expected_contract = {
            "complete_scope": "all raw static text values available in the local sanitized source artifact were inventoried",
            "blocked_scope": "full raw list for likely_ui_string_total_from_source is absent from the available sanitized artifact",
            "runtime_visibility_status": "unknown_not_run",
            "translation_quality_status": "unknown_not_run",
            "accessibility_behavior_status": "unknown_not_run",
            "fixed_dynamic_value_oracles_allowed": False,
        }
        for key, expected in expected_contract.items():
            if coverage_contract.get(key) != expected:
                errors.append(f"coverage_contract.{key} must be {expected!r}")
    follow_up_actions = report.get("follow_up_actions")
    if not isinstance(follow_up_actions, list):
        errors.append("follow_up_actions must be a list")
    else:
        seen_follow_up_tasks: set[str] = set()
        for action in follow_up_actions:
            if not isinstance(action, dict):
                errors.append("follow_up_actions entries must be objects")
                continue
            unknown_action_keys = sorted(set(action) - ALLOWED_FOLLOW_UP_ACTION_KEYS)
            missing_action_keys = sorted(ALLOWED_FOLLOW_UP_ACTION_KEYS - set(action))
            if unknown_action_keys:
                errors.append(f"follow_up_actions entries contain unknown fields: {unknown_action_keys}")
            if missing_action_keys:
                errors.append(f"follow_up_actions entries missing required fields: {missing_action_keys}")
            task_name = action.get("task")
            if task_name not in EXPECTED_FOLLOW_UP_ACTIONS:
                errors.append("follow_up_actions task must be an approved TASK-035 follow-up slug")
                continue
            seen_follow_up_tasks.add(str(task_name))
            for key, expected in EXPECTED_FOLLOW_UP_ACTIONS[str(task_name)].items():
                if action.get(key) != expected:
                    errors.append(f"follow_up_actions.{task_name}.{key} must be {expected!r}")
        missing_follow_up_tasks = sorted(set(EXPECTED_FOLLOW_UP_ACTIONS) - seen_follow_up_tasks)
        if missing_follow_up_tasks:
            errors.append(f"follow_up_actions missing required tasks: {missing_follow_up_tasks}")
    errors.extend(_public_safety_findings(report))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build TASK-035 static text inventory summary.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--local-inventory", type=Path, default=DEFAULT_LOCAL_INVENTORY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--validate-only", action="store_true", help="Validate an existing public report instead of building.")
    args = parser.parse_args(argv)

    if args.validate_only:
        report = _load_json(args.report)
    else:
        report = build_report(args.source, args.local_inventory)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    errors = validate_public_report(report)
    result = {
        "validation_status": "pass" if not errors else "blocked",
        "report_path": args.report.as_posix(),
        "overall_status": report.get("overall_status"),
        "coverage_status": report.get("static_text_inventory", {}).get("coverage_status"),
        "likely_ui_string_total": report.get("static_text_inventory", {}).get("likely_ui_string_total_from_source"),
        "available_raw_sample_inventory_count": report.get("static_text_inventory", {}).get("available_raw_sample_inventory_count"),
        "blocked_reasons": sorted(set(report.get("blocked_reasons", []) + errors)),
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

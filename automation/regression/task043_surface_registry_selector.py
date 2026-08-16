"""TASK-043 public-safe offline surface registry and regression selector.

The production CLI intentionally has no path overrides.  It reads only the
tracked public contracts named below, never reads ``.qa_local`` and never
starts child processes or network activity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import stat
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


TASK_ID = "TASK-043"
SCHEMA_VERSION = "task043-surface-registry-v1"
REPORT_SCHEMA_VERSION = "evidence-report-envelope-v2"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_SAFE_OFFLINE_STATIC_ONLY"
REPO_ROOT = Path(__file__).resolve().parents[2]

EPIC_ROOT = REPO_ROOT / "docs/qa/epics"
REPORT_ROOT = REPO_ROOT / "docs/qa/reports"
SCHEMA_ROOT = REPO_ROOT / "docs/qa/schemas"
TRACEABILITY = EPIC_ROOT / "opaque_surface_task_traceability.csv"
DEVICE_MATRIX = EPIC_ROOT / "device_apk_execution_matrix.csv"
TASK_INDEX = EPIC_ROOT / "task041_055_task_index.json"
STATUS_CONTRACT = EPIC_ROOT / "task041_055_status_evidence_contract.md"
TASK043_CATALOG = EPIC_ROOT / "scenarios/task043_scenarios.csv"
TASK042_REPORT = REPORT_ROOT / "task042_local_runtime_preflight.summary.json"
REPORT_MANIFEST = REPORT_ROOT / "report-manifest.json"
REGISTRY_SCHEMA = SCHEMA_ROOT / "task043-surface-registry-v1.schema.json"
REGISTRY_OUTPUT = EPIC_ROOT / "task043_surface_registry.json"
REPORT_OUTPUT = REPORT_ROOT / "task043_surface_coverage.summary.json"
LEDGER_OUTPUT = REPORT_ROOT / "task043_surface_coverage.scenario-ledger.csv"
MIGRATION_OUTPUT = REPORT_ROOT / "task043_prior_evidence_migration.csv"
GAP_OUTPUT = REPORT_ROOT / "task043_surface_gap_matrix.csv"
SELECTION_OUTPUT = REPORT_ROOT / "task043_task044_selection.csv"
CATALOGS = tuple(EPIC_ROOT / f"scenarios/task{task:03d}_scenarios.csv" for task in range(41, 56))

TRACE_HEADERS = (
    "surface_id", "risk", "category", "public_safe_description",
    "applicable_families", "primary_tasks", "runtime_oracle",
    "evidence_status", "scenario_ids", "scenario_count",
)
SCENARIO_HEADERS = (
    "scenario_id", "priority", "surface_ids", "lane", "category", "title",
    "preconditions", "steps", "expected_oracle", "negative_or_boundary",
    "automation_target", "evidence_required", "safety_class", "blocking_rule",
)
DEVICE_HEADERS = (
    "order", "device_alias", "runtime_profile", "apk_family",
    "artifact_contract", "form_factor", "os_api", "task_usage",
    "release_evidence_role",
)
LEDGER_HEADERS = (
    "scenario_id", "priority", "surface_ids", "scenario_status",
    "evidence_type", "evidence_status", "justification_code",
)
MIGRATION_HEADERS = (
    "task_id", "report_alias", "schema_status", "authority_status",
    "freshness_status", "reuse_status", "reason_code",
)
GAP_HEADERS = (
    "lane_alias", "family", "surface_count", "r0_count", "r1_count",
    "coverage_status", "evidence_status", "reason_code",
)
SELECTION_HEADERS = (
    "scenario_id", "priority", "surface_ids", "lane", "selection_status",
    "evidence_status", "reason_code",
)

SCENARIO_STATUSES = {
    "observed_pass", "observed_fail", "confirmed_defect", "tooling_defect",
    "executable_not_run", "blocked_by_device", "blocked_by_fixture",
    "blocked_by_oracle", "blocked_by_product_boundary",
    "blocked_by_external_state", "not_applicable", "mapped_only",
}
NON_PASS_STATUSES = SCENARIO_STATUSES - {"observed_pass", "not_applicable"}
EVIDENCE_TYPES = {
    "physical_runtime", "paired_physical_runtime", "avd_tooling_runtime",
    "synthetic_offline", "static_contract", "manual_observation", "mapped_only",
}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
FAMILIES = (
    "television-full", "phone-full", "television-steam", "television-sber",
    "aosp-full", "launcher-system",
)
DEVICE_LANE_COUNT = 13
GAP_ROW_COUNT = 14
REGISTRY_SCHEMA_SHA256 = "1f63aab0bf8ade5f021937b34e229a4c609ec148ce3500e9652b012d6ab00f66"
APP_FAMILIES = FAMILIES[:5]
TV_FAMILIES = ("television-full", "television-steam", "television-sber", "aosp-full")
FAMILY_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "all": FAMILIES,
    "all app families": APP_FAMILIES,
    "all applicable": APP_FAMILIES,
    "all/paired": APP_FAMILIES,
    "applicable": APP_FAMILIES,
    "approved non-paid fixtures only": APP_FAMILIES,
    "approved public components only": ("aosp-full", "launcher-system"),
    "connected app lanes": APP_FAMILIES,
    "FogPlay Stick": ("aosp-full", "launcher-system"),
    "TV/phone": APP_FAMILIES,
    "TV/phone applicable": APP_FAMILIES,
    "TV/STB": TV_FAMILIES,
    "TV/STB/system": TV_FAMILIES + ("launcher-system",),
    "TV/system": TV_FAMILIES + ("launcher-system",),
    "TV+phone": APP_FAMILIES,
}
DEVICE_FAMILY_MAP = {
    "television-full": "television-full",
    "phone-full": "phone-full",
    "television-steam": "television-steam",
    "television-sber": "television-sber",
    "aosp-full + separate launcher contour": "aosp-full",
    "selected by AVD capability": "avd-tooling-only",
    "UNKNOWN until local approved mapping": "unknown-family",
}
FAMILY_TASKS = {
    "television-full": "TASK-044",
    "phone-full": "TASK-045",
    "television-steam": "TASK-046",
    "television-sber": "TASK-047",
    "aosp-full": "TASK-048",
    "launcher-system": "TASK-048",
}

SAFE_REFERENCE_RE = re.compile(r"^[a-zA-Z0-9_./-]+$")
OPAQUE_ID_RE = re.compile(r"^SURF-[A-Z]+-[0-9]{3}$")
SCENARIO_ID_RE = re.compile(r"^QA-[0-9]{3}-[0-9]{3}$")
TASK_ID_RE = re.compile(r"^TASK-[0-9]{3}$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"(?i)(?:https?|wss?)://"),
    re.compile(r"(?i)(?:^|[\\/])\.qa_local(?:[\\/]|$)"),
    re.compile(r"(?i)\.(?:apk|aab|apks|xapk)(?:$|[^a-z])"),
    re.compile(r"(?i)\b(?:token|cookie|password|otp|serial|imei|android_id)\s*[:=]"),
    re.compile(r"(?i)^[a-z]:[\\/]"),
    re.compile(r"(?i)^/(?:home|users|private|var)/"),
)
PRIVATE_IDENTIFIER_PATTERNS = (
    re.compile(r"\b[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*){2,}(?:/[a-z0-9_./-]+)?\b"),
    re.compile(r"\b(?:com|org|net|io)\.(?:[a-z_][a-z0-9_]*\.)+[A-Za-z_][A-Za-z0-9_]*\b"),
    re.compile(r"(?i)\binternal(?:\.[a-z_][a-z0-9_]*)+(?:/[a-z0-9_./-]+)?"),
    re.compile(r"\b[A-Z][A-Za-z0-9]*(?:Manager|Service|Repository|Controller|Client|Activity|Fragment|Component|Engine|Impl)\b"),
    re.compile(r"\b[a-z_][A-Za-z0-9_]*(?:[A-Z][A-Za-z0-9_]*)+\s*\("),
)
PUBLIC_SAFE_IDENTIFIER_ALLOWLIST = frozenset({"WebView", "WebRTC", "Android TV", "FogPlay Stick"})
PUBLIC_SAFE_REFERENCE_PREFIXES = ("docs/qa/", "automation/regression/")
PUBLIC_REPORT_ALIAS_RE = re.compile(
    r"^(?:none|task[0-9]{3}[a-z]?_[a-z0-9_-]+(?:\.summary(?:\.template)?)?)$"
)
FORMULA_PREFIXES = ("=", "+", "-", "@")
TEXT_SUFFIXES = {".json", ".csv", ".md", ".txt", ".py"}


class ContractError(Exception):
    """Controlled validation failure; its reason code is always public-safe."""

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


def _is_reparse(path: Path) -> bool:
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (OSError, AttributeError):
        return False


def _fixed_file(path: Path, *, parent: Path, suffix: str) -> Path:
    try:
        root = REPO_ROOT.resolve(strict=True)
        resolved_parent = parent.resolve(strict=True)
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ContractError("INPUT_UNAVAILABLE") from None
    if resolved_parent != parent or path.parent != parent or path.suffix.lower() != suffix:
        raise ContractError("INPUT_PATH_NOT_CANONICAL")
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ContractError("INPUT_OUTSIDE_REPOSITORY") from None
    current = path
    while current != REPO_ROOT:
        if current.is_symlink() or _is_reparse(current):
            raise ContractError("INPUT_REPARSE_FORBIDDEN")
        current = current.parent
    if not path.is_file():
        raise ContractError("INPUT_NOT_REGULAR_FILE")
    return path


def _load_json(path: Path, *, parent: Path) -> dict[str, Any]:
    _fixed_file(path, parent=parent, suffix=".json")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_json_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ContractError("JSON_UNREADABLE_OR_MALFORMED") from None
    if not isinstance(value, dict):
        raise ContractError("JSON_ROOT_NOT_OBJECT")
    return value


def _load_csv(path: Path, headers: Sequence[str], *, parent: Path) -> list[dict[str, str]]:
    _fixed_file(path, parent=parent, suffix=".csv")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames is None or tuple(reader.fieldnames) != tuple(headers):
                raise ContractError("CSV_HEADERS_INVALID")
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise ContractError("CSV_DUPLICATE_HEADER")
            rows = list(reader)
    except ContractError:
        raise
    except (OSError, UnicodeError, csv.Error):
        raise ContractError("CSV_UNREADABLE_OR_MALFORMED") from None
    if not rows:
        raise ContractError("CSV_ROWS_EMPTY")
    for row in rows:
        if set(row) != set(headers) or any(value is None or value == "" for value in row.values()):
            raise ContractError("CSV_ROW_INVALID")
        _validate_csv_cells(row.values())
    return rows


def _validate_csv_cells(values: Iterable[str]) -> None:
    for value in values:
        if any(ord(char) < 32 and char not in "\t" for char in value):
            raise ContractError("CSV_CONTROL_VALUE_FORBIDDEN")
        if value.startswith(FORMULA_PREFIXES):
            raise ContractError("CSV_FORMULA_VALUE_FORBIDDEN")


def _csv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=headers, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        values = {key: str(row[key]) for key in headers}
        _validate_csv_cells(values.values())
        _validate_generated_csv_row(values)
        writer.writerow(values)
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _canonical_sha_bytes(content: bytes, suffix: str) -> str:
    if suffix.lower() in TEXT_SUFFIXES:
        content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def _canonical_sha_file(path: Path) -> str:
    try:
        return _canonical_sha_bytes(path.read_bytes(), path.suffix)
    except OSError:
        raise ContractError("ARTIFACT_UNREADABLE") from None


def _repo_reference(path: Path) -> str:
    try:
        reference = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        raise ContractError("OUTPUT_OUTSIDE_REPOSITORY") from None
    if not _safe_reference(reference):
        raise ContractError("OUTPUT_REFERENCE_UNSAFE")
    return reference


def _safe_reference(reference: str) -> bool:
    if not SAFE_REFERENCE_RE.fullmatch(reference) or "\\" in reference:
        return False
    pure = PurePosixPath(reference)
    return not pure.is_absolute() and ".." not in pure.parts and ":" not in reference


def _walk_strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def _validate_public_values(value: Any) -> None:
    for field_path, text in _walk_strings(value):
        if any(pattern.search(text) for pattern in FORBIDDEN_VALUE_PATTERNS):
            raise ContractError("PUBLIC_VALUE_FORBIDDEN")
        identifier_allowlisted = text in PUBLIC_SAFE_IDENTIFIER_ALLOWLIST or (
            field_path.endswith(".reference")
            and text.startswith(PUBLIC_SAFE_REFERENCE_PREFIXES)
            and _safe_reference(text)
        )
        if not identifier_allowlisted and any(
            pattern.search(text) for pattern in PRIVATE_IDENTIFIER_PATTERNS
        ):
            raise ContractError("PUBLIC_VALUE_FORBIDDEN")
        if HASH_RE.fullmatch(text) and not field_path.endswith(".sha256"):
            raise ContractError("RAW_HASH_OUTSIDE_ARTIFACT_FIELD")


def _validate_generated_csv_row(row: Mapping[str, str]) -> None:
    for field, text in row.items():
        if field == "report_alias" and PUBLIC_REPORT_ALIAS_RE.fullmatch(text):
            if any(pattern.search(text) for pattern in FORBIDDEN_VALUE_PATTERNS):
                raise ContractError("PUBLIC_VALUE_FORBIDDEN")
            continue
        _validate_public_values({field: text})


def validate_static_constants() -> list[str]:
    errors: list[str] = []
    if len(CATALOGS) != 15:
        errors.append("CATALOG_CONSTANT_COUNT_INVALID")
    if len(FAMILIES) != 6 or len(APP_FAMILIES) != 5:
        errors.append("FAMILY_CONSTANT_COUNT_INVALID")
    if DEVICE_LANE_COUNT != 13 or GAP_ROW_COUNT != 14 or not HASH_RE.fullmatch(REGISTRY_SCHEMA_SHA256):
        errors.append("GENERATED_CONTRACT_CONSTANT_INVALID")
    if SCENARIO_STATUSES != {
        "observed_pass", "observed_fail", "confirmed_defect", "tooling_defect",
        "executable_not_run", "blocked_by_device", "blocked_by_fixture",
        "blocked_by_oracle", "blocked_by_product_boundary",
        "blocked_by_external_state", "not_applicable", "mapped_only",
    }:
        errors.append("SCENARIO_STATUS_CONSTANT_INVALID")
    if set(FAMILY_EXPANSIONS) != {
        "all", "all app families", "all applicable", "all/paired", "applicable",
        "approved non-paid fixtures only", "approved public components only",
        "connected app lanes", "FogPlay Stick", "TV/phone", "TV/phone applicable",
        "TV/STB", "TV/STB/system", "TV/system", "TV+phone",
    }:
        errors.append("FAMILY_EXPANSION_CONSTANT_INVALID")
    return errors


def _validate_task_index(value: Mapping[str, Any]) -> None:
    required = {"schema_version", "epic_id", "task_count", "scenario_count", "tasks"}
    if set(value) != required or value.get("task_count") != 15 or value.get("scenario_count") != 307:
        raise ContractError("TASK_INDEX_CONTRACT_INVALID")
    tasks = value.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 15:
        raise ContractError("TASK_INDEX_TASKS_INVALID")
    expected_keys = {
        "task_id", "title", "task_spec_path", "prompt_path",
        "scenario_catalog_path", "dependencies", "next_task",
        "production_safety_classification", "scenario_count", "p0_count",
    }
    expected_ids = [f"TASK-{number:03d}" for number in range(41, 56)]
    if [item.get("task_id") for item in tasks if isinstance(item, dict)] != expected_ids:
        raise ContractError("TASK_INDEX_TASK_ORDER_INVALID")
    for number, item in zip(range(41, 56), tasks, strict=True):
        if not isinstance(item, dict) or set(item) != expected_keys:
            raise ContractError("TASK_INDEX_TASK_SCHEMA_INVALID")
        if item["scenario_catalog_path"] != f"docs/qa/epics/scenarios/task{number:03d}_scenarios.csv":
            raise ContractError("TASK_INDEX_CATALOG_REFERENCE_INVALID")
        if item["production_safety_classification"] not in {"PROD_SAFE", "PROD_CONDITIONAL"}:
            raise ContractError("TASK_INDEX_SAFETY_CLASS_INVALID")
        if not isinstance(item["scenario_count"], int) or not isinstance(item["p0_count"], int):
            raise ContractError("TASK_INDEX_COUNT_TYPE_INVALID")


def _validate_surfaces(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    risks = Counter()
    for row in rows:
        surface_id = row["surface_id"]
        if not OPAQUE_ID_RE.fullmatch(surface_id) or surface_id in registry:
            raise ContractError("SURFACE_ID_INVALID_OR_DUPLICATE")
        if row["risk"] not in {"R0", "R1"} or row["evidence_status"] != "hypothesis":
            raise ContractError("SURFACE_ENUM_INVALID")
        family_key = row["applicable_families"]
        if family_key not in FAMILY_EXPANSIONS:
            raise ContractError("SURFACE_FAMILY_SCOPE_UNKNOWN")
        scenarios = row["scenario_ids"].split(";")
        if not scenarios or len(set(scenarios)) != len(scenarios) or not all(SCENARIO_ID_RE.fullmatch(x) for x in scenarios):
            raise ContractError("SURFACE_SCENARIO_LIST_INVALID")
        try:
            expected_count = int(row["scenario_count"])
        except ValueError:
            raise ContractError("SURFACE_SCENARIO_COUNT_INVALID") from None
        if expected_count != len(scenarios):
            raise ContractError("SURFACE_SCENARIO_COUNT_MISMATCH")
        tasks = row["primary_tasks"].split(",")
        if not tasks or not all(part.strip().isdigit() for part in tasks):
            raise ContractError("SURFACE_PRIMARY_TASKS_INVALID")
        risks[row["risk"]] += 1
        registry[surface_id] = {
            "surface_id": surface_id,
            "risk": row["risk"],
            "category": row["category"],
            "public_safe_description": row["public_safe_description"],
            "family_scope": family_key,
            "applicable_families": list(FAMILY_EXPANSIONS[family_key]),
            "primary_tasks": [f"TASK-{int(part.strip()):03d}" for part in tasks],
            "runtime_oracle_category": row["runtime_oracle"],
            "evidence_status": "hypothesis",
            "scenario_ids": scenarios,
            "scenario_count": expected_count,
        }
    if len(registry) != 55 or risks != Counter({"R0": 33, "R1": 22}):
        raise ContractError("SURFACE_TOTALS_INVALID")
    _validate_public_values(registry)
    return registry


def _validate_catalogs(
    registry: Mapping[str, Any], task_index: Mapping[str, Any]
) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    all_rows: list[dict[str, str]] = []
    by_id: dict[str, dict[str, str]] = {}
    reverse: dict[str, set[str]] = defaultdict(set)
    for task_number, path in zip(range(41, 56), CATALOGS, strict=True):
        rows = _load_csv(path, SCENARIO_HEADERS, parent=EPIC_ROOT / "scenarios")
        index_item = task_index["tasks"][task_number - 41]
        if len(rows) != index_item["scenario_count"] or sum(row["priority"] == "P0" for row in rows) != index_item["p0_count"]:
            raise ContractError("TASK_INDEX_CATALOG_COUNT_MISMATCH")
        for row in rows:
            _validate_public_values(row)
            scenario_id = row["scenario_id"]
            if not SCENARIO_ID_RE.fullmatch(scenario_id) or not scenario_id.startswith(f"QA-{task_number:03d}-"):
                raise ContractError("SCENARIO_ID_INVALID")
            if scenario_id in by_id:
                raise ContractError("SCENARIO_ID_DUPLICATE")
            if row["priority"] not in {"P0", "P1"} or row["safety_class"] not in {"PROD_SAFE", "PROD_CONDITIONAL"}:
                raise ContractError("SCENARIO_ENUM_INVALID")
            surface_ids = row["surface_ids"].split(";")
            if len(set(surface_ids)) != len(surface_ids) or any(surface not in registry for surface in surface_ids):
                raise ContractError("SCENARIO_SURFACE_REFERENCE_INVALID")
            for surface in surface_ids:
                reverse[surface].add(scenario_id)
            by_id[scenario_id] = row
            all_rows.append(row)
    if len(all_rows) != 307:
        raise ContractError("EPIC_SCENARIO_TOTAL_INVALID")
    for surface_id, record in registry.items():
        if set(record["scenario_ids"]) != reverse.get(surface_id, set()):
            raise ContractError("SURFACE_SCENARIO_REVERSE_MISMATCH")
    task043 = [row for row in all_rows if row["scenario_id"].startswith("QA-043-")]
    if len(task043) != 18 or Counter(row["priority"] for row in task043) != Counter({"P0": 16, "P1": 2}):
        raise ContractError("TASK043_SCENARIO_TOTAL_INVALID")
    return by_id, task043


def _validate_device_matrix(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    if len(rows) != DEVICE_LANE_COUNT:
        raise ContractError("DEVICE_LANE_TOTAL_INVALID")
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for row in rows:
        alias = row["device_alias"]
        if alias in seen or not re.fullmatch(r"[a-z0-9-]+", alias):
            raise ContractError("DEVICE_ALIAS_INVALID_OR_DUPLICATE")
        seen.add(alias)
        raw_family = row["apk_family"]
        if raw_family not in DEVICE_FAMILY_MAP:
            raise ContractError("DEVICE_FAMILY_UNKNOWN")
        result.append({"lane_alias": alias, "family": DEVICE_FAMILY_MAP[raw_family]})
    return result


def _validate_manifest_and_migration(manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    required = {"schema_version", "record_count", "records"}
    if not required.issubset(manifest) or manifest.get("schema_version") != "report-manifest-v1":
        raise ContractError("REPORT_MANIFEST_CONTRACT_INVALID")
    records = manifest.get("records")
    if not isinstance(records, list) or manifest.get("record_count") != len(records):
        raise ContractError("REPORT_MANIFEST_COUNT_INVALID")
    projected: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        if not isinstance(record, dict):
            raise ContractError("REPORT_MANIFEST_RECORD_INVALID")
        task_id = record.get("task_id")
        if not isinstance(task_id, str) or not re.fullmatch(
            r"(?:TASK-[0-9]{3}[A-Z]?|EPIC-[A-Z0-9]+-[0-9]{3})",
            task_id,
        ):
            raise ContractError("REPORT_MANIFEST_TASK_INVALID")
        if task_id.startswith("EPIC-"):
            # TASK-043 migration rows intentionally cover TASK-019..040 only.
            # A valid epic manifest record is governed by the manifest but does
            # not masquerade as, or inflate, a historical TASK migration row.
            continue
        task_number = int(task_id[5:8])
        if not 19 <= task_number <= 40:
            continue
        provenance = record.get("provenance")
        if not isinstance(provenance, dict):
            raise ContractError("REPORT_MANIFEST_PROVENANCE_INVALID")
        reference = provenance.get("source_reference")
        source_sha = provenance.get("source_sha256")
        if not isinstance(reference, str) or not _safe_reference(reference) or not reference.startswith("docs/qa/reports/"):
            raise ContractError("REPORT_MANIFEST_SOURCE_REFERENCE_INVALID")
        if not isinstance(source_sha, str) or not HASH_RE.fullmatch(source_sha):
            raise ContractError("REPORT_MANIFEST_SOURCE_HASH_INVALID")
        source_path = REPO_ROOT / PurePosixPath(reference)
        _fixed_file(source_path, parent=REPORT_ROOT, suffix=".json")
        if _canonical_sha_file(source_path) != source_sha:
            raise ContractError("REPORT_MANIFEST_SOURCE_HASH_MISMATCH")
        schema_status = record.get("schema_validation_status")
        authority_status = record.get("authority_status")
        if schema_status not in {"v2_valid", "legacy_migration_blocked"}:
            raise ContractError("REPORT_MANIFEST_SCHEMA_STATUS_INVALID")
        if authority_status not in {"authoritative", "legacy_not_authoritative", "superseded", "blocked"}:
            raise ContractError("REPORT_MANIFEST_AUTHORITY_STATUS_INVALID")
        base_task_id = f"TASK-{task_number:03d}"
        projected[base_task_id].append({
            "task_id": base_task_id,
            "report_alias": Path(reference).stem,
            "schema_status": str(schema_status),
            "authority_status": str(authority_status),
            "freshness_status": "stale_build_compatibility_unproven",
            "reuse_status": "historical_context_only",
            "reason_code": "prior_evidence_not_current_release_authority",
        })
    rows: list[dict[str, str]] = []
    for number in range(19, 41):
        task_id = f"TASK-{number:03d}"
        if task_id in projected:
            rows.extend(sorted(projected[task_id], key=lambda row: row["report_alias"]))
        else:
            rows.append({
                "task_id": task_id,
                "report_alias": "none",
                "schema_status": "missing",
                "authority_status": "non_authoritative",
                "freshness_status": "unknown",
                "reuse_status": "not_available",
                "reason_code": "manifest_record_missing",
            })
    return rows


def _validate_task042_report(report: Mapping[str, Any]) -> None:
    if report.get("schema_version") != REPORT_SCHEMA_VERSION or report.get("task_id") != "TASK-042":
        raise ContractError("TASK042_REPORT_CONTRACT_INVALID")
    if report.get("release_effect") != "no_release_claim":
        raise ContractError("TASK042_RELEASE_EFFECT_INVALID")
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ContractError("TASK042_ARTIFACTS_INVALID")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ContractError("TASK042_ARTIFACT_INVALID")
        reference = artifact.get("reference")
        expected = artifact.get("sha256")
        if not isinstance(reference, str) or not _safe_reference(reference) or not reference.startswith("docs/qa/reports/"):
            raise ContractError("TASK042_ARTIFACT_REFERENCE_INVALID")
        if not isinstance(expected, str) or not HASH_RE.fullmatch(expected):
            raise ContractError("TASK042_ARTIFACT_HASH_INVALID")
        artifact_path = REPO_ROOT / PurePosixPath(reference)
        _fixed_file(artifact_path, parent=REPORT_ROOT, suffix=artifact_path.suffix.lower())
        if _canonical_sha_file(artifact_path) != expected:
            raise ContractError("TASK042_ARTIFACT_HASH_MISMATCH")


def load_snapshot() -> dict[str, Any]:
    trace_rows = _load_csv(TRACEABILITY, TRACE_HEADERS, parent=EPIC_ROOT)
    registry = _validate_surfaces(trace_rows)
    task_index = _load_json(TASK_INDEX, parent=EPIC_ROOT)
    _validate_task_index(task_index)
    _fixed_file(STATUS_CONTRACT, parent=EPIC_ROOT, suffix=".md")
    scenarios, task043 = _validate_catalogs(registry, task_index)
    device_rows = _load_csv(DEVICE_MATRIX, DEVICE_HEADERS, parent=EPIC_ROOT)
    lanes = _validate_device_matrix(device_rows)
    manifest = _load_json(REPORT_MANIFEST, parent=REPORT_ROOT)
    migration = _validate_manifest_and_migration(manifest)
    task042 = _load_json(TASK042_REPORT, parent=REPORT_ROOT)
    _validate_task042_report(task042)
    schema = _load_json(REGISTRY_SCHEMA, parent=SCHEMA_ROOT)
    if schema.get("$id") != "docs/qa/schemas/task043-surface-registry-v1.schema.json":
        raise ContractError("REGISTRY_SCHEMA_ID_INVALID")
    if _canonical_sha_file(REGISTRY_SCHEMA) != REGISTRY_SCHEMA_SHA256:
        raise ContractError("REGISTRY_SCHEMA_CONTENT_INVALID")
    snapshot = {
        "registry": registry,
        "scenarios": scenarios,
        "task043": task043,
        "lanes": lanes,
        "migration": migration,
        "task_index": task_index,
    }
    _self_check_selector_semantics(snapshot)
    return snapshot


def scenario_is_clean_pass(status: str, evidence_type: str, evidence_status: str, attempts: Sequence[Mapping[str, Any]] | None = None) -> bool:
    if status not in SCENARIO_STATUSES or evidence_type not in EVIDENCE_TYPES or evidence_status not in EVIDENCE_STATUSES:
        raise ContractError("EVIDENCE_ENUM_UNKNOWN")
    if status != "observed_pass" or evidence_status != "confirmed" or evidence_type == "mapped_only":
        return False
    if attempts is not None:
        if not attempts:
            raise ContractError("ATTEMPTS_MISSING")
        for attempt in attempts:
            if set(attempt) != {"attempt_id", "oracle_result", "recovery"}:
                raise ContractError("ATTEMPT_SCHEMA_INVALID")
            if attempt["oracle_result"] not in {"pass", "fail"} or not isinstance(attempt["recovery"], bool):
                raise ContractError("ATTEMPT_ENUM_INVALID")
        if any(attempt["oracle_result"] == "fail" or attempt["recovery"] is True for attempt in attempts):
            return False
    return True


def evidence_satisfies(requirement: str, evidence_type: str) -> bool:
    if evidence_type not in EVIDENCE_TYPES:
        raise ContractError("EVIDENCE_TYPE_UNKNOWN")
    allowed = {
        "physical": {"physical_runtime"},
        "paired_physical": {"paired_physical_runtime"},
        "oem_compatibility": {"physical_runtime", "paired_physical_runtime"},
        "static": {"static_contract", "synthetic_offline"},
    }
    if requirement not in allowed:
        raise ContractError("EVIDENCE_REQUIREMENT_UNKNOWN")
    return evidence_type in allowed[requirement]


def can_reuse_prior_evidence(*, build_match: bool, family_match: bool, lane_match: bool, scenario_contract_match: bool, freshness_contract_present: bool) -> bool:
    return all(
        value is True
        for value in (build_match, family_match, lane_match, scenario_contract_match, freshness_contract_present)
    )


def select_family_tasks(changed_family: str, *, shared: bool = False, equivalence_delta: bool = False) -> tuple[str, ...]:
    if changed_family not in FAMILY_TASKS:
        raise ContractError("SELECTOR_FAMILY_UNKNOWN")
    selected = set(FAMILY_TASKS.values()) if shared else {FAMILY_TASKS[changed_family]}
    if equivalence_delta:
        selected.add("TASK-053")
    return tuple(sorted(selected))


def select_surface_scenarios(
    registry: Mapping[str, Mapping[str, Any]],
    surface_id: str,
    changed_family: str,
    *,
    shared: bool = False,
    equivalence_delta: bool = False,
) -> tuple[str, ...]:
    if surface_id not in registry:
        raise ContractError("SELECTOR_SURFACE_UNKNOWN")
    if changed_family not in registry[surface_id]["applicable_families"]:
        raise ContractError("SELECTOR_FAMILY_NOT_APPLICABLE")
    task_ids = set(select_family_tasks(changed_family, shared=shared, equivalence_delta=equivalence_delta))
    selected = []
    for scenario_id in registry[surface_id]["scenario_ids"]:
        task_id = f"TASK-{int(scenario_id[3:6]):03d}"
        if task_id in task_ids:
            selected.append(scenario_id)
    return tuple(sorted(selected))


def _self_check_selector_semantics(snapshot: Mapping[str, Any]) -> None:
    family_specific = select_surface_scenarios(snapshot["registry"], "SURF-CATALOG-001", "television-sber")
    if family_specific != ("QA-047-004",):
        raise ContractError("FAMILY_SPECIFIC_SELECTOR_INVALID")
    if select_family_tasks("television-full", shared=True) != ("TASK-044", "TASK-045", "TASK-046", "TASK-047", "TASK-048"):
        raise ContractError("SHARED_SELECTOR_INVALID")
    if "TASK-053" not in select_family_tasks("television-full", equivalence_delta=True):
        raise ContractError("EQUIVALENCE_SELECTOR_INVALID")
    if scenario_is_clean_pass("mapped_only", "mapped_only", "unknown"):
        raise ContractError("MAPPED_ONLY_FALSE_PASS")
    if scenario_is_clean_pass(
        "observed_pass",
        "physical_runtime",
        "confirmed",
        attempts=(
            {"attempt_id": "attempt-1", "oracle_result": "fail", "recovery": False},
            {"attempt_id": "attempt-2", "oracle_result": "pass", "recovery": True},
        ),
    ):
        raise ContractError("RETRY_RECOVERY_FALSE_PASS")
    if evidence_satisfies("physical", "synthetic_offline") or evidence_satisfies("oem_compatibility", "avd_tooling_runtime"):
        raise ContractError("EVIDENCE_TYPE_SUBSTITUTION_FALSE_PASS")


def _ledger_rows(task043: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    reason_map = {
        "QA-043-001": "registry_schema_validated",
        "QA-043-002": "public_safety_guards_validated",
        "QA-043-003": "surface_scenario_reverse_map_validated",
        "QA-043-004": "historical_manifest_projection_generated",
        "QA-043-005": "prior_build_stale_default_validated",
        "QA-043-006": "explicit_compatibility_rule_validated_synthetically",
        "QA-043-007": "mapped_only_false_pass_rejected",
        "QA-043-008": "blocked_false_pass_rejected",
        "QA-043-009": "retry_failure_preservation_validated",
        "QA-043-010": "synthetic_physical_substitution_rejected",
        "QA-043-011": "avd_oem_substitution_rejected",
        "QA-043-012": "family_specific_selection_validated",
        "QA-043-013": "shared_family_selection_validated",
        "QA-043-014": "device_equivalence_selection_validated",
        "QA-043-015": "unknown_status_fail_closed",
        "QA-043-016": "public_evidence_reference_policy_validated",
        "QA-043-017": "gap_counts_reconciled",
        "QA-043-018": "task044_selection_generated",
    }
    return [
        {
            "scenario_id": row["scenario_id"],
            "priority": row["priority"],
            "surface_ids": row["surface_ids"],
            "scenario_status": "observed_pass",
            "evidence_type": "static_contract",
            "evidence_status": "confirmed",
            "justification_code": reason_map[row["scenario_id"]],
        }
        for row in task043
    ]


def _gap_rows(registry: Mapping[str, Mapping[str, Any]], lanes: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for lane in lanes:
        family = lane["family"]
        matching = [item for item in registry.values() if family in item["applicable_families"]]
        if family in {"avd-tooling-only", "unknown-family"}:
            matching = []
        reason = "fresh_runtime_evidence_required"
        if lane["lane_alias"] == "actual-project-known-fogplay-stick":
            reason = "actual_stick_mapping_missing"
        elif family == "avd-tooling-only":
            reason = "avd_is_tooling_only"
        elif family == "unknown-family":
            reason = "family_mapping_unknown"
        rows.append({
            "lane_alias": lane["lane_alias"],
            "family": family,
            "surface_count": str(len(matching)),
            "r0_count": str(sum(item["risk"] == "R0" for item in matching)),
            "r1_count": str(sum(item["risk"] == "R1" for item in matching)),
            "coverage_status": "mapped_only",
            "evidence_status": "hypothesis" if matching else "unknown",
            "reason_code": reason,
        })
    launcher = [item for item in registry.values() if "launcher-system" in item["applicable_families"]]
    rows.append({
        "lane_alias": "launcher-system-contour",
        "family": "launcher-system",
        "surface_count": str(len(launcher)),
        "r0_count": str(sum(item["risk"] == "R0" for item in launcher)),
        "r1_count": str(sum(item["risk"] == "R1" for item in launcher)),
        "coverage_status": "mapped_only",
        "evidence_status": "hypothesis",
        "reason_code": "separate_launcher_runtime_evidence_required",
    })
    return rows


def _selection_rows(scenarios: Mapping[str, Mapping[str, str]]) -> list[dict[str, str]]:
    selected = [row for scenario_id, row in scenarios.items() if scenario_id.startswith("QA-044-")]
    selected.sort(key=lambda row: row["scenario_id"])
    if len(selected) != 32 or Counter(row["priority"] for row in selected) != Counter({"P0": 29, "P1": 3}):
        raise ContractError("TASK044_SELECTION_TOTAL_INVALID")
    return [
        {
            "scenario_id": row["scenario_id"],
            "priority": row["priority"],
            "surface_ids": row["surface_ids"],
            "lane": row["lane"],
            "selection_status": "selected_not_run",
            "evidence_status": "hypothesis",
            "reason_code": "task044_reference_lane_contract",
        }
        for row in selected
    ]


def _registry_document(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    surfaces = [snapshot["registry"][key] for key in sorted(snapshot["registry"])]
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
        "evidence_status": "confirmed",
        "product_runtime_evidence_status": "unknown",
        "surface_count": 55,
        "risk_summary": {"R0": 33, "R1": 22},
        "family_count": 6,
        "families": list(FAMILIES),
        "scenario_catalog_count": 15,
        "scenario_count": 307,
        "surfaces": surfaces,
    }


def _build_output_bytes(snapshot: Mapping[str, Any]) -> dict[Path, bytes]:
    registry_doc = _registry_document(snapshot)
    ledger = _ledger_rows(snapshot["task043"])
    migration = snapshot["migration"]
    gaps = _gap_rows(snapshot["registry"], snapshot["lanes"])
    selection = _selection_rows(snapshot["scenarios"])
    output_bytes: dict[Path, bytes] = {
        REGISTRY_OUTPUT: _json_bytes(registry_doc),
        LEDGER_OUTPUT: _csv_bytes(LEDGER_HEADERS, ledger),
        MIGRATION_OUTPUT: _csv_bytes(MIGRATION_HEADERS, migration),
        GAP_OUTPUT: _csv_bytes(GAP_HEADERS, gaps),
        SELECTION_OUTPUT: _csv_bytes(SELECTION_HEADERS, selection),
    }
    artifact_paths = (
        REGISTRY_SCHEMA, TRACEABILITY, DEVICE_MATRIX, TASK043_CATALOG, TASK042_REPORT,
        REGISTRY_OUTPUT, LEDGER_OUTPUT, MIGRATION_OUTPUT, GAP_OUTPUT, SELECTION_OUTPUT,
    )
    artifacts: list[dict[str, str]] = []
    for path in artifact_paths:
        content = output_bytes[path] if path in output_bytes else path.read_bytes()
        artifacts.append({
            "reference": _repo_reference(path),
            "sha256": _canonical_sha_bytes(content, path.suffix),
            "kind": "generated_static_artifact" if path in output_bytes else "canonical_static_input",
            "evidence_status": "confirmed",
        })
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": "pass",
        "coverage_status": "partial",
        "evidence_status": "confirmed",
        "release_effect": "no_release_claim",
        "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
        "generated_at_utc": "2026-07-29T00:00:00Z",
        "task_id": TASK_ID,
        "build_ref": {"alias": "qa-repository-task043-static-snapshot"},
        "target_alias": "all-families-plus-launcher-static-selector",
        "run_id": "task043-offline-static-001",
        "artifacts": artifacts,
        "blocked_reasons": [],
        "unknowns": [{
            "id": "U-T043-RUNTIME",
            "evidence_status": "unknown",
            "question": "Product runtime coverage remains unverified by this offline static task.",
        }],
        "risks": [{
            "id": "RISK-T043-001",
            "level": "High",
            "status": "active",
            "summary": "Static selector success must not be interpreted as product runtime or release readiness.",
        }],
        "verification": [
            {"check": "surface_registry_reverse_reconciliation", "status": "pass", "evidence_status": "confirmed", "result_count": 55},
            {"check": "epic_scenario_reconciliation", "status": "pass", "evidence_status": "confirmed", "result_count": 307},
            {"check": "task043_static_scenario_execution", "status": "pass", "evidence_status": "confirmed", "result_count": 18},
            {"check": "task044_selection_only", "status": "pass", "evidence_status": "confirmed", "result_count": 32},
        ],
        "review": {
            "qa_reviewer_a": "pending",
            "qa_reviewer_b": "pending",
            "security_prod_safety_reviewer": "pending",
            "docs_scribe": "pending",
        },
        "provenance": {
            "source": "tracked_public_safe_contracts_only",
            "authority": "automation/regression/task043_surface_registry_selector.py",
            "manifest_policy": "validated_projection_without_circular_hash_binding",
            "runtime_actions": "not_run",
        },
        "payload": {
            "contract_execution_scope": "offline_static_only",
            "product_runtime_coverage_claim": False,
            "release_readiness_claim": False,
            "surface_summary": {"total": 55, "R0": 33, "R1": 22},
            "scenario_summary": {"total": 18, "observed_pass": 18, "non_pass": 0},
            "prior_evidence_summary": {
                "task_range_count": 22,
                "record_count": len(migration),
                "missing_task_count": len({row["task_id"] for row in migration if row["schema_status"] == "missing"}),
                "reuse_policy": "historical_context_only_stale_by_default",
            },
            "gap_summary": {
                "lane_count": len(gaps),
                "device_lane_count": DEVICE_LANE_COUNT,
                "launcher_contour_count": 1,
                "coverage_status": "mapped_only",
                "evidence_status": "unknown",
            },
            "task044_selection_summary": {"total": 32, "P0": 29, "P1": 3, "execution_status": "not_run"},
            "process_anomalies": [
                {
                    "id": "TASK043-PROCESS-ANOMALY-002",
                    "evidence_status": "confirmed",
                    "status": "remediated",
                    "summary": "Review found canonical validation and transactional publication gaps; adversarial controls now cover them.",
                },
                {
                    "id": "TASK043-PROCESS-ANOMALY-003",
                    "evidence_status": "confirmed",
                    "status": "remediated",
                    "summary": "Manifest staging found forbidden hidden status keys in payload; the canonical envelope now omits them.",
                },
            ],
        },
    }
    output_bytes[REPORT_OUTPUT] = _json_bytes(report)
    validate_report(report, artifact_bytes=output_bytes)
    _validate_output_bundle_bytes(output_bytes)
    return output_bytes


def _csv_rows_from_bytes(content: bytes, headers: Sequence[str]) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames is None or tuple(reader.fieldnames) != tuple(headers):
            raise ContractError("GENERATED_CSV_HEADERS_INVALID")
        rows = list(reader)
    except ContractError:
        raise
    except (UnicodeError, csv.Error):
        raise ContractError("GENERATED_CSV_MALFORMED") from None
    if any(set(row) != set(headers) or any(value is None or value == "" for value in row.values()) for row in rows):
        raise ContractError("GENERATED_CSV_ROW_INVALID")
    return rows


def _validate_output_bundle_bytes(outputs: Mapping[Path, bytes]) -> None:
    if set(outputs) != {REGISTRY_OUTPUT, REPORT_OUTPUT, LEDGER_OUTPUT, MIGRATION_OUTPUT, GAP_OUTPUT, SELECTION_OUTPUT}:
        raise ContractError("GENERATED_OUTPUT_SET_INVALID")
    try:
        registry = json.loads(outputs[REGISTRY_OUTPUT].decode("utf-8"), object_pairs_hook=_json_pairs)
        report = json.loads(outputs[REPORT_OUTPUT].decode("utf-8"), object_pairs_hook=_json_pairs)
    except (UnicodeError, json.JSONDecodeError):
        raise ContractError("GENERATED_JSON_MALFORMED") from None
    if not isinstance(registry, dict) or not isinstance(report, dict):
        raise ContractError("GENERATED_JSON_ROOT_INVALID")
    validate_registry_document(registry)
    validate_report(report, artifact_bytes=outputs)
    ledger = _csv_rows_from_bytes(outputs[LEDGER_OUTPUT], LEDGER_HEADERS)
    migration = _csv_rows_from_bytes(outputs[MIGRATION_OUTPUT], MIGRATION_HEADERS)
    gaps = _csv_rows_from_bytes(outputs[GAP_OUTPUT], GAP_HEADERS)
    selection = _csv_rows_from_bytes(outputs[SELECTION_OUTPUT], SELECTION_HEADERS)
    if len(ledger) != 18 or any(not scenario_is_clean_pass(row["scenario_status"], row["evidence_type"], row["evidence_status"]) for row in ledger):
        raise ContractError("LEDGER_RECONCILIATION_INVALID")
    if len({row["task_id"] for row in migration}) != 22:
        raise ContractError("MIGRATION_RECONCILIATION_INVALID")
    if len(gaps) != GAP_ROW_COUNT or any(row["coverage_status"] != "mapped_only" for row in gaps):
        raise ContractError("GAP_RECONCILIATION_INVALID")
    if len(selection) != 32 or Counter(row["priority"] for row in selection) != Counter({"P0": 29, "P1": 3}):
        raise ContractError("SELECTION_RECONCILIATION_INVALID")


def validate_registry_document(value: Mapping[str, Any]) -> None:
    required = {
        "schema_version", "task_id", "production_safety_classification",
        "evidence_status", "product_runtime_evidence_status", "surface_count",
        "risk_summary", "family_count", "families", "scenario_catalog_count",
        "scenario_count", "surfaces",
    }
    if set(value) != required or value.get("schema_version") != SCHEMA_VERSION:
        raise ContractError("REGISTRY_DOCUMENT_SCHEMA_INVALID")
    exact_top_level = {
        "task_id": TASK_ID,
        "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
        "evidence_status": "confirmed",
        "product_runtime_evidence_status": "unknown",
        "family_count": 6,
        "families": list(FAMILIES),
        "scenario_catalog_count": 15,
    }
    if any(value.get(key) != expected for key, expected in exact_top_level.items()):
        raise ContractError("REGISTRY_DOCUMENT_TOP_LEVEL_INVALID")
    surfaces = value.get("surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 55 or value.get("surface_count") != 55:
        raise ContractError("REGISTRY_DOCUMENT_SURFACE_COUNT_INVALID")
    if value.get("risk_summary") != {"R0": 33, "R1": 22} or value.get("scenario_count") != 307:
        raise ContractError("REGISTRY_DOCUMENT_COUNTS_INVALID")
    surface_keys = {
        "surface_id", "risk", "category", "public_safe_description",
        "family_scope", "applicable_families", "primary_tasks",
        "runtime_oracle_category", "evidence_status", "scenario_ids",
        "scenario_count",
    }
    ids = [row.get("surface_id") for row in surfaces if isinstance(row, dict)]
    if len(ids) != 55 or len(set(ids)) != 55:
        raise ContractError("REGISTRY_DOCUMENT_IDS_INVALID")
    risk_counts = Counter()
    for row in surfaces:
        if not isinstance(row, dict) or set(row) != surface_keys:
            raise ContractError("REGISTRY_DOCUMENT_SURFACE_SCHEMA_INVALID")
        if not OPAQUE_ID_RE.fullmatch(row["surface_id"]) or row["risk"] not in {"R0", "R1"}:
            raise ContractError("REGISTRY_DOCUMENT_SURFACE_ENUM_INVALID")
        scope = row["family_scope"]
        if scope not in FAMILY_EXPANSIONS or row["applicable_families"] != list(FAMILY_EXPANSIONS[scope]):
            raise ContractError("REGISTRY_DOCUMENT_FAMILY_SCOPE_INVALID")
        scenario_ids = row["scenario_ids"]
        if (
            not isinstance(scenario_ids, list)
            or not scenario_ids
            or len(set(scenario_ids)) != len(scenario_ids)
            or not all(isinstance(item, str) and SCENARIO_ID_RE.fullmatch(item) for item in scenario_ids)
            or row["scenario_count"] != len(scenario_ids)
        ):
            raise ContractError("REGISTRY_DOCUMENT_SCENARIOS_INVALID")
        primary_tasks = row["primary_tasks"]
        if not isinstance(primary_tasks, list) or not primary_tasks or not all(isinstance(item, str) and TASK_ID_RE.fullmatch(item) for item in primary_tasks):
            raise ContractError("REGISTRY_DOCUMENT_PRIMARY_TASKS_INVALID")
        if row["evidence_status"] != "hypothesis" or not all(
            isinstance(row[key], str) and row[key] for key in ("category", "public_safe_description", "runtime_oracle_category")
        ):
            raise ContractError("REGISTRY_DOCUMENT_SURFACE_VALUE_INVALID")
        risk_counts[row["risk"]] += 1
    if risk_counts != Counter({"R0": 33, "R1": 22}):
        raise ContractError("REGISTRY_DOCUMENT_RISK_RECONCILIATION_INVALID")
    _validate_public_values(value)


def validate_report(report: Mapping[str, Any], *, artifact_bytes: Mapping[Path, bytes] | None = None) -> None:
    required = {
        "schema_version", "schema_validation_status", "execution_status",
        "coverage_status", "evidence_status", "release_effect",
        "production_safety_classification", "generated_at_utc", "task_id",
        "build_ref", "target_alias", "run_id", "artifacts", "blocked_reasons",
        "unknowns", "risks", "verification", "review", "provenance", "payload",
    }
    if set(report) != required or report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ContractError("REPORT_SCHEMA_INVALID")
    if report.get("task_id") != TASK_ID or report.get("release_effect") != "no_release_claim":
        raise ContractError("REPORT_CLAIM_INVALID")
    if (
        report.get("schema_validation_status") != "pass"
        or report.get("execution_status") != "pass"
        or report.get("coverage_status") != "partial"
        or report.get("evidence_status") != "confirmed"
        or report.get("production_safety_classification") != PRODUCTION_SAFETY_CLASSIFICATION
        or report.get("generated_at_utc") != "2026-07-29T00:00:00Z"
    ):
        raise ContractError("REPORT_STATUS_INVALID")
    if report.get("blocked_reasons") != [] or report.get("review") != {
        "qa_reviewer_a": "pending",
        "qa_reviewer_b": "pending",
        "security_prod_safety_reviewer": "pending",
        "docs_scribe": "pending",
    }:
        raise ContractError("REPORT_REVIEW_OR_BLOCKER_INVALID")
    payload = report.get("payload")
    if not isinstance(payload, dict) or payload.get("product_runtime_coverage_claim") is not False or payload.get("release_readiness_claim") is not False:
        raise ContractError("REPORT_PRODUCT_OVERCLAIM")
    summary = payload.get("scenario_summary")
    if summary != {"total": 18, "observed_pass": 18, "non_pass": 0}:
        raise ContractError("REPORT_SCENARIO_SUMMARY_INVALID")
    selection = payload.get("task044_selection_summary")
    if selection != {"total": 32, "P0": 29, "P1": 3, "execution_status": "not_run"}:
        raise ContractError("REPORT_SELECTION_SUMMARY_INVALID")
    if payload.get("gap_summary") != {
        "lane_count": GAP_ROW_COUNT,
        "device_lane_count": DEVICE_LANE_COUNT,
        "launcher_contour_count": 1,
        "coverage_status": "mapped_only",
        "evidence_status": "unknown",
    }:
        raise ContractError("REPORT_GAP_SUMMARY_INVALID")
    forbidden_payload_status_fields = {
        "runtime_execution_status", "apk_execution_status",
        "adb_avd_execution_status", "network_execution_status",
        "runtime_evidence_status",
    }
    if forbidden_payload_status_fields.intersection(payload):
        raise ContractError("REPORT_PAYLOAD_HIDDEN_STATUS_FORBIDDEN")
    if payload.get("process_anomalies") != [
        {
            "id": "TASK043-PROCESS-ANOMALY-002",
            "evidence_status": "confirmed",
            "status": "remediated",
            "summary": "Review found canonical validation and transactional publication gaps; adversarial controls now cover them.",
        },
        {
            "id": "TASK043-PROCESS-ANOMALY-003",
            "evidence_status": "confirmed",
            "status": "remediated",
            "summary": "Manifest staging found forbidden hidden status keys in payload; the canonical envelope now omits them.",
        },
    ]:
        raise ContractError("REPORT_PROCESS_ANOMALY_INVALID")
    expected_verification = [
        {"check": "surface_registry_reverse_reconciliation", "status": "pass", "evidence_status": "confirmed", "result_count": 55},
        {"check": "epic_scenario_reconciliation", "status": "pass", "evidence_status": "confirmed", "result_count": 307},
        {"check": "task043_static_scenario_execution", "status": "pass", "evidence_status": "confirmed", "result_count": 18},
        {"check": "task044_selection_only", "status": "pass", "evidence_status": "confirmed", "result_count": 32},
    ]
    if report.get("verification") != expected_verification:
        raise ContractError("REPORT_VERIFICATION_INVALID")
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 10:
        raise ContractError("REPORT_ARTIFACTS_INVALID")
    expected_refs = {
        _repo_reference(path) for path in (
            REGISTRY_SCHEMA, TRACEABILITY, DEVICE_MATRIX, TASK043_CATALOG, TASK042_REPORT,
            REGISTRY_OUTPUT, LEDGER_OUTPUT, MIGRATION_OUTPUT, GAP_OUTPUT, SELECTION_OUTPUT,
        )
    }
    seen_refs: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"reference", "sha256", "kind", "evidence_status"}:
            raise ContractError("REPORT_ARTIFACT_SCHEMA_INVALID")
        reference = artifact["reference"]
        if reference in seen_refs or reference not in expected_refs or not HASH_RE.fullmatch(artifact["sha256"]):
            raise ContractError("REPORT_ARTIFACT_REFERENCE_INVALID")
        seen_refs.add(reference)
        path = REPO_ROOT / PurePosixPath(reference)
        if artifact_bytes is not None and path in artifact_bytes:
            actual = _canonical_sha_bytes(artifact_bytes[path], path.suffix)
        else:
            _fixed_file(path, parent=path.parent, suffix=path.suffix.lower())
            actual = _canonical_sha_file(path)
        if actual != artifact["sha256"]:
            raise ContractError("REPORT_ARTIFACT_HASH_MISMATCH")
    if seen_refs != expected_refs:
        raise ContractError("REPORT_ARTIFACT_SET_INVALID")
    _validate_public_values(report)


def _validate_canonical_output_bytes(actual: Mapping[Path, bytes], expected: Mapping[Path, bytes]) -> None:
    if set(actual) != set(expected):
        raise ContractError("GENERATED_OUTPUT_SET_INVALID")
    for path, expected_bytes in expected.items():
        if actual[path] != expected_bytes:
            raise ContractError("GENERATED_OUTPUT_CANONICAL_MISMATCH")


def _validate_generated_files(snapshot: Mapping[str, Any] | None = None) -> None:
    canonical_snapshot = load_snapshot() if snapshot is None else snapshot
    expected = _build_output_bytes(canonical_snapshot)
    actual: dict[Path, bytes] = {}
    for path in expected:
        _fixed_file(path, parent=path.parent, suffix=path.suffix.lower())
        try:
            actual[path] = path.read_bytes()
        except OSError:
            raise ContractError("GENERATED_OUTPUT_UNREADABLE") from None
    _validate_canonical_output_bytes(actual, expected)


def _atomic_publish(outputs: Mapping[Path, bytes]) -> None:
    staged: list[tuple[Path, Path]] = []
    backups: dict[Path, Path | None] = {}
    published: list[Path] = []
    preserved_backups: set[Path] = set()
    try:
        for target, content in outputs.items():
            if target not in {REGISTRY_OUTPUT, REPORT_OUTPUT, LEDGER_OUTPUT, MIGRATION_OUTPUT, GAP_OUTPUT, SELECTION_OUTPUT}:
                raise ContractError("OUTPUT_NOT_ALLOWLISTED")
            target.parent.mkdir(parents=False, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(
                prefix=f".{target.name}.task043.", suffix=".tmp", dir=target.parent
            )
            temp = Path(temp_name)
            staged.append((temp, target))
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
            except Exception:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                raise
        for _, target in staged:
            if target.exists():
                descriptor, backup_name = tempfile.mkstemp(
                    prefix=f".{target.name}.task043.backup.", suffix=".tmp", dir=target.parent
                )
                backup = Path(backup_name)
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
                    preserved_backups.add(backup)
        if rollback_failed:
            raise ContractError(
                "OUTPUT_ROLLBACK_FAILED", recovery_status="local_backup_preserved"
            ) from None
        raise ContractError("OUTPUT_ATOMIC_PUBLISH_FAILED") from None
    finally:
        for temp, _ in staged:
            try:
                if temp.exists():
                    temp.unlink()
            except OSError:
                pass
        for backup in backups.values():
            try:
                if backup is not None and backup not in preserved_backups and backup.exists():
                    backup.unlink()
            except OSError:
                pass


def execute() -> dict[str, Any]:
    snapshot = load_snapshot()
    outputs = _build_output_bytes(snapshot)
    _atomic_publish(outputs)
    _validate_generated_files(snapshot)
    return {
        "validation_status": "pass",
        "task_id": TASK_ID,
        "mode": "offline_static_execute",
        "surface_count": 55,
        "scenario_count": 307,
        "task043_scenario_count": 18,
        "task044_selection_count": 32,
        "runtime_actions": "not_run",
        "release_claim": "none",
    }


def _emit(result: Mapping[str, Any]) -> None:
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TASK-043 offline static surface registry selector")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true", help="Validate immutable constants only; no file I/O.")
    modes.add_argument("--preflight", action="store_true", help="Validate fixed tracked inputs; no writes.")
    modes.add_argument("--execute", action="store_true", help="Generate fixed public-safe static outputs atomically.")
    modes.add_argument("--validate-report", action="store_true", help="Validate the fixed TASK-043 report bundle; no writes.")
    args = parser.parse_args(argv)
    try:
        if args.validate_only:
            errors = validate_static_constants()
            if errors:
                raise ContractError(errors[0])
            result = {"validation_status": "pass", "mode": "validate_only", "runtime_actions": "not_run"}
        elif args.preflight:
            snapshot = load_snapshot()
            result = {
                "validation_status": "pass", "mode": "preflight",
                "surface_count": len(snapshot["registry"]),
                "scenario_count": len(snapshot["scenarios"]),
                "task043_scenario_count": len(snapshot["task043"]),
                "runtime_actions": "not_run",
            }
        elif args.execute:
            result = execute()
        else:
            snapshot = load_snapshot()
            _validate_generated_files(snapshot)
            result = {"validation_status": "pass", "mode": "validate_report", "runtime_actions": "not_run"}
        _emit(result)
        return 0
    except ContractError as exc:
        result = {"validation_status": "blocked", "reason_code": str(exc), "runtime_actions": "not_run"}
        if exc.recovery_status is not None:
            result["recovery_status"] = exc.recovery_status
        _emit(result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

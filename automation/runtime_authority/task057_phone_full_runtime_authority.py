"""TASK-057 public-safe Phone Full readiness authority.

This module is deliberately repository-only.  It never reads ``.qa_local``,
APKs, Android tooling, ADB, device state, credentials, or product screens.  A
human orchestrator may place only sanitized, public-safe observations in the
tracked ledgers; this module then derives and validates the fail-closed public
summary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from automation.reporting.generate_report_manifest import _validate_v2_envelope
except ModuleNotFoundError:  # Direct ``python automation/...py`` execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from automation.reporting.generate_report_manifest import _validate_v2_envelope


TASK_ID = "TASK-057"
SCHEMA_VERSION = "evidence-report-envelope-v2"
PRODUCTION_SAFETY = "PROD_CONDITIONAL_READ_ONLY_METADATA"
BASELINE_GENERATED_AT = "2026-08-15T12:00:00Z"
BASELINE_RUN_ID = "task057-readiness-authority-blocked-001"

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_SPEC = REPO_ROOT / "tasks/TASK_057_phone_full_runtime_authority_gate.md"
AUTHORITY_OUTPUT = REPO_ROOT / "docs/qa/reports/task057_phone_full_runtime_authority.readiness-ledger.csv"
CLEANUP_OUTPUT = REPO_ROOT / "docs/qa/reports/task057_phone_full_runtime_authority.cleanup-ledger.csv"
REPORT_OUTPUT = REPO_ROOT / "docs/qa/reports/task057_phone_full_runtime_authority.summary.json"

AUTHORITY_HEADERS = (
    "authority_id",
    "subject_alias",
    "current_status",
    "freshness",
    "evidence_status",
    "evidence_ids",
    "reviewer_gate",
    "expires_at",
    "terminal_status",
    "release_effect",
    "reason_code",
)
CLEANUP_HEADERS = (
    "cleanup_id",
    "current_status",
    "freshness",
    "evidence_status",
    "evidence_ids",
    "retention_redaction",
    "action_budget",
    "kill_switch",
    "cleanup_rollback",
    "mutation_check",
    "reviewer_gate",
    "expires_at",
    "terminal_status",
    "release_effect",
    "reason_code",
)

AUTHORITY_CONTRACT = (
    (
        "task057-authority-01-canonical-phone-full",
        "main-apk-03",
        "presence_only_integrity_unknown",
        "canonical_phone_full_integrity_provenance_confirmed",
        "blocked_by_oracle",
    ),
    (
        "task057-authority-02-installed-compatibility",
        "installed-phone-full-build",
        "distinct_compatibility_unknown",
        "installed_canonical_compatibility_confirmed",
        "blocked_by_oracle",
    ),
    (
        "task057-authority-03-current-phone-selector",
        "current-phone-selector",
        "unresolved_historical_candidate_only",
        "current_phone_mapped_authorized_unchanged",
        "blocked_by_device",
    ),
    (
        "task057-authority-04-downgrade-safety",
        "ordinary-downgrade-guard",
        "rejected_no_bypass",
        "downgrade_rejection_preserved_no_bypass",
        "blocked_by_oracle",
    ),
    (
        "task057-authority-05-synthetic-session",
        "synthetic-session-passport",
        "policy_only_no_passport",
        "synthetic_session_passport_current",
        "blocked_by_fixture",
    ),
    (
        "task057-authority-06-clean-first-launch",
        "clean-first-launch-fixture",
        "unknown",
        "clean_first_launch_fixture_ready",
        "blocked_by_fixture",
    ),
    (
        "task057-authority-07-evidence-cleanup-security",
        "evidence-cleanup-passport",
        "unknown",
        "evidence_cleanup_security_ready",
        "blocked_by_fixture",
    ),
)
EXPECTED_AUTHORITY_IDS = tuple(item[0] for item in AUTHORITY_CONTRACT)
PASS_CURRENT_STATUS = {item[0]: item[3] for item in AUTHORITY_CONTRACT}
BASELINE_SUBJECT_ALIAS = {item[0]: item[1] for item in AUTHORITY_CONTRACT}
PASS_EVIDENCE_IDS = {
    EXPECTED_AUTHORITY_IDS[0]: (
        "task057-apk-presence",
        "task057-apk-integrity",
        "task057-apk-metadata",
        "task057-apk-compatibility",
    ),
    EXPECTED_AUTHORITY_IDS[1]: (
        "task057-installed-compatibility",
        "task057-installed-signing",
    ),
    EXPECTED_AUTHORITY_IDS[2]: (
        "task057-device-snapshot-open",
        "task057-device-snapshot-confirm",
        "task057-device-snapshot-cleanup",
    ),
    EXPECTED_AUTHORITY_IDS[3]: ("task057-metadata-action-ledger",),
    EXPECTED_AUTHORITY_IDS[4]: ("task057-synthetic-session-passport",),
    EXPECTED_AUTHORITY_IDS[5]: ("task057-clean-first-launch-fixture",),
    EXPECTED_AUTHORITY_IDS[6]: (
        "task057-evidence-cleanup-passport",
        "task057-runtime-action-budget",
        "task057-security-go-runtime",
    ),
}
PASS_CLEANUP_EVIDENCE_IDS = (
    "task057-evidence-cleanup-passport",
    "task057-runtime-action-budget",
    "task057-metadata-action-ledger",
    "task057-device-snapshot-cleanup",
    "task057-security-go-runtime",
)

FRESHNESS_VALUES = {"fresh_current_run", "stale_historical", "not_established"}
EVIDENCE_VALUES = {"confirmed", "likely", "hypothesis", "unknown"}
REVIEWER_GATES = {
    "GO_RUNTIME",
    "GO_METADATA_CONDITIONAL",
    "BLOCK_RUNTIME",
    "pending_security_review",
}
TERMINAL_VALUES = {
    "observed_pass",
    "blocked_by_device",
    "blocked_by_fixture",
    "blocked_by_oracle",
    "blocked_by_external_state",
}
RELEASE_EFFECTS = {"candidate_evidence", "blocks_release"}
SAFE_SLUG_RE = re.compile(r"^[a-z0-9]+(?:[a-z0-9_-]*[a-z0-9])?$")
EVIDENCE_ID_RE = re.compile(r"^task057-[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?$")
PHONE_ALIAS_RE = re.compile(r"^phone-current-[0-9]{3}$")
FORBIDDEN_PATTERNS = (
    re.compile(r"(?i)(?:^|[\s\"'])[a-z]:[\\/]"),
    re.compile(r"\\\\[^\\\s]+\\"),
    re.compile(r"(?i)\b(?:https?|wss?|file|intent|market|mailto):"),
    re.compile(r"(?<![\w-])(?:\d{1,3}\.){3}\d{1,3}(?![\w-])"),
    re.compile(r"(?i)(?:^|[\\/])\.qa_local(?:[\\/]|$)"),
    re.compile(r"(?i)\b(?:[a-z][a-z0-9_]*\.){2,}[a-z][a-z0-9_]*\b"),
    re.compile(r"(?i)\b[0-9a-f]{32,}\b"),
)


class ContractError(ValueError):
    """A public-safe TASK-057 contract failed closed."""


def _utc(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ContractError("timestamp_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ContractError("timestamp_invalid") from exc
    if parsed.tzinfo is None:
        raise ContractError("timestamp_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _now_utc_text() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _assert_public_safe(value: str, field: str) -> None:
    if any(pattern.search(value) for pattern in FORBIDDEN_PATTERNS):
        raise ContractError(f"unsafe_public_value:{field}")
    if "\r" in value or "\n" in value:
        raise ContractError(f"multiline_public_value:{field}")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ContractError(f"duplicate_json_key:{key}")
        value[key] = child
    return value


def _evidence_ids(value: str, *, allow_none: bool) -> tuple[str, ...]:
    if value == "none" and allow_none:
        return ()
    ids = tuple(value.split(";"))
    if not ids or any(not EVIDENCE_ID_RE.fullmatch(item) for item in ids) or len(set(ids)) != len(ids):
        raise ContractError("evidence_ids_invalid")
    return ids


def _csv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _parse_csv(data: bytes, headers: Sequence[str], label: str) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(f"{label}_utf8_invalid") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != tuple(headers):
        raise ContractError(f"{label}_headers_drift")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ContractError(f"{label}_extra_cells")
    return rows


def baseline_authority_rows() -> list[dict[str, str]]:
    rows = [
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[0],
            "subject_alias": "main-apk-03",
            "current_status": "candidate_metadata_incomplete",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057-apk-presence;task057-apk-integrity;task057-apk-metadata",
            "reviewer_gate": "GO_METADATA_CONDITIONAL",
            "expires_at": "2026-08-16T23:59:59Z",
            "terminal_status": "blocked_by_oracle",
            "release_effect": "blocks_release",
            "reason_code": "candidate_min_sdk_metadata_not_emitted",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[1],
            "subject_alias": "installed-phone-full-build",
            "current_status": "installed_canonical_incompatible",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057-installed-compatibility",
            "reviewer_gate": "GO_METADATA_CONDITIONAL",
            "expires_at": "2026-08-16T23:59:59Z",
            "terminal_status": "blocked_by_external_state",
            "release_effect": "blocks_release",
            "reason_code": "installed_signing_certificate_mismatch",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[2],
            "subject_alias": "phone-current-001",
            "current_status": PASS_CURRENT_STATUS[EXPECTED_AUTHORITY_IDS[2]],
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057-device-snapshot-open;task057-device-snapshot-confirm;task057-device-snapshot-cleanup",
            "reviewer_gate": "GO_METADATA_CONDITIONAL",
            "expires_at": "2026-08-16T23:59:59Z",
            "terminal_status": "observed_pass",
            "release_effect": "candidate_evidence",
            "reason_code": PASS_CURRENT_STATUS[EXPECTED_AUTHORITY_IDS[2]],
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[3],
            "subject_alias": "ordinary-downgrade-guard",
            "current_status": PASS_CURRENT_STATUS[EXPECTED_AUTHORITY_IDS[3]],
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057-metadata-action-ledger",
            "reviewer_gate": "GO_METADATA_CONDITIONAL",
            "expires_at": "2026-08-16T23:59:59Z",
            "terminal_status": "observed_pass",
            "release_effect": "candidate_evidence",
            "reason_code": PASS_CURRENT_STATUS[EXPECTED_AUTHORITY_IDS[3]],
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[4],
            "subject_alias": "synthetic-session-passport",
            "current_status": "synthetic_session_passport_absent",
            "freshness": "fresh_current_run",
            "evidence_status": "unknown",
            "evidence_ids": "none",
            "reviewer_gate": "BLOCK_RUNTIME",
            "expires_at": "not_set",
            "terminal_status": "blocked_by_fixture",
            "release_effect": "blocks_release",
            "reason_code": "synthetic_session_passport_absent",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[5],
            "subject_alias": "clean-first-launch-fixture",
            "current_status": "clean_first_launch_fixture_absent",
            "freshness": "fresh_current_run",
            "evidence_status": "unknown",
            "evidence_ids": "none",
            "reviewer_gate": "BLOCK_RUNTIME",
            "expires_at": "not_set",
            "terminal_status": "blocked_by_fixture",
            "release_effect": "blocks_release",
            "reason_code": "clean_first_launch_fixture_absent",
        },
        {
            "authority_id": EXPECTED_AUTHORITY_IDS[6],
            "subject_alias": "evidence-cleanup-passport",
            "current_status": "evidence_cleanup_passport_absent",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057-metadata-action-ledger;task057-device-snapshot-cleanup",
            "reviewer_gate": "BLOCK_RUNTIME",
            "expires_at": "not_set",
            "terminal_status": "blocked_by_fixture",
            "release_effect": "blocks_release",
            "reason_code": "evidence_cleanup_passport_absent_security_block_runtime",
        },
    ]
    return rows


def baseline_cleanup_rows() -> list[dict[str, str]]:
    return [
        {
            "cleanup_id": "task057-cleanup-passport",
            "current_status": "metadata_cleanup_confirmed_passport_absent",
            "freshness": "fresh_current_run",
            "evidence_status": "confirmed",
            "evidence_ids": "task057-metadata-action-ledger;task057-device-snapshot-cleanup",
            "retention_redaction": "confirmed_local_only_redacted_public",
            "action_budget": "bounded_read_only_metadata_only",
            "kill_switch": "confirmed_metadata_only",
            "cleanup_rollback": "confirmed_no_mutation",
            "mutation_check": "confirmed_unchanged",
            "reviewer_gate": "BLOCK_RUNTIME",
            "expires_at": "not_set",
            "terminal_status": "blocked_by_fixture",
            "release_effect": "blocks_release",
            "reason_code": "evidence_cleanup_passport_absent_security_block_runtime",
        }
    ]


def _row_passes(row: Mapping[str, str], generated_at: datetime) -> bool:
    authority_id = row["authority_id"]
    if authority_id not in PASS_CURRENT_STATUS:
        return False
    if authority_id == EXPECTED_AUTHORITY_IDS[2] and PHONE_ALIAS_RE.fullmatch(row["subject_alias"]) is None:
        return False
    if authority_id != EXPECTED_AUTHORITY_IDS[2] and row["subject_alias"] != BASELINE_SUBJECT_ALIAS[authority_id]:
        return False
    if row["current_status"] != PASS_CURRENT_STATUS[authority_id]:
        return False
    if row["reason_code"] != PASS_CURRENT_STATUS[authority_id]:
        return False
    if row["freshness"] != "fresh_current_run" or row["evidence_status"] != "confirmed":
        return False
    if _evidence_ids(row["evidence_ids"], allow_none=False) != PASS_EVIDENCE_IDS[authority_id]:
        return False
    allowed_gate = (
        row["reviewer_gate"] == "GO_RUNTIME"
        if authority_id == EXPECTED_AUTHORITY_IDS[6]
        else row["reviewer_gate"] in {"GO_METADATA_CONDITIONAL", "GO_RUNTIME"}
    )
    if not allowed_gate or row["expires_at"] == "not_set":
        return False
    if _utc(row["expires_at"]) <= generated_at:
        return False
    return row["terminal_status"] == "observed_pass" and row["release_effect"] == "candidate_evidence"


def validate_authority_rows(rows: Sequence[Mapping[str, str]], generated_at: datetime) -> list[bool]:
    if len(rows) != 7:
        raise ContractError("authority_ledger_requires_exactly_seven_rows")
    ids = [row.get("authority_id", "") for row in rows]
    if ids != list(EXPECTED_AUTHORITY_IDS) or len(set(ids)) != 7:
        raise ContractError("authority_ledger_missing_duplicate_merged_or_reordered_row")
    results: list[bool] = []
    for row in rows:
        for field in AUTHORITY_HEADERS:
            value = row.get(field)
            if not isinstance(value, str) or not value:
                raise ContractError(f"authority_field_missing:{row['authority_id']}:{field}")
            _assert_public_safe(value, f"{row['authority_id']}:{field}")
        if not SAFE_SLUG_RE.fullmatch(row["subject_alias"]):
            raise ContractError(f"subject_alias_invalid:{row['authority_id']}")
        if not SAFE_SLUG_RE.fullmatch(row["current_status"]):
            raise ContractError(f"current_status_invalid:{row['authority_id']}")
        if row["freshness"] not in FRESHNESS_VALUES:
            raise ContractError(f"freshness_invalid:{row['authority_id']}")
        if row["evidence_status"] not in EVIDENCE_VALUES:
            raise ContractError(f"evidence_status_invalid:{row['authority_id']}")
        _evidence_ids(row["evidence_ids"], allow_none=True)
        if row["reviewer_gate"] not in REVIEWER_GATES:
            raise ContractError(f"reviewer_gate_invalid:{row['authority_id']}")
        if row["expires_at"] != "not_set":
            _utc(row["expires_at"])
        if row["terminal_status"] not in TERMINAL_VALUES:
            raise ContractError(f"terminal_status_invalid:{row['authority_id']}")
        if row["release_effect"] not in RELEASE_EFFECTS:
            raise ContractError(f"release_effect_invalid:{row['authority_id']}")
        if not SAFE_SLUG_RE.fullmatch(row["reason_code"]):
            raise ContractError(f"reason_code_invalid:{row['authority_id']}")
        passed = _row_passes(row, generated_at)
        if row["terminal_status"] == "observed_pass" and not passed:
            raise ContractError(f"authority_false_pass:{row['authority_id']}")
        if not passed and row["release_effect"] != "blocks_release":
            raise ContractError(f"blocked_row_must_block_release:{row['authority_id']}")
        results.append(passed)
    return results


def _cleanup_passes(row: Mapping[str, str], generated_at: datetime) -> bool:
    exact = {
        "cleanup_id": "task057-cleanup-passport",
        "current_status": "evidence_cleanup_security_ready",
        "freshness": "fresh_current_run",
        "evidence_status": "confirmed",
        "retention_redaction": "confirmed_local_only_redacted_public",
        "action_budget": "bounded_runtime_budget_current",
        "kill_switch": "confirmed_runtime_current",
        "cleanup_rollback": "runtime_cleanup_rollback_current",
        "mutation_check": "confirmed_unchanged",
        "reviewer_gate": "GO_RUNTIME",
        "terminal_status": "observed_pass",
        "release_effect": "candidate_evidence",
        "reason_code": "evidence_cleanup_security_ready",
    }
    if any(row.get(key) != value for key, value in exact.items()):
        return False
    if _evidence_ids(row["evidence_ids"], allow_none=False) != PASS_CLEANUP_EVIDENCE_IDS:
        return False
    if row["expires_at"] == "not_set":
        return False
    return _utc(row["expires_at"]) > generated_at


def validate_cleanup_rows(rows: Sequence[Mapping[str, str]], generated_at: datetime) -> bool:
    if len(rows) != 1 or rows[0].get("cleanup_id") != "task057-cleanup-passport":
        raise ContractError("cleanup_ledger_requires_one_exact_row")
    row = rows[0]
    for field in CLEANUP_HEADERS:
        value = row.get(field)
        if not isinstance(value, str) or not value:
            raise ContractError(f"cleanup_field_missing:{field}")
        _assert_public_safe(value, f"cleanup:{field}")
    if row["freshness"] not in FRESHNESS_VALUES or row["evidence_status"] not in EVIDENCE_VALUES:
        raise ContractError("cleanup_freshness_or_evidence_invalid")
    _evidence_ids(row["evidence_ids"], allow_none=True)
    if row["reviewer_gate"] not in REVIEWER_GATES or row["terminal_status"] not in TERMINAL_VALUES:
        raise ContractError("cleanup_gate_or_terminal_invalid")
    if row["release_effect"] not in RELEASE_EFFECTS:
        raise ContractError("cleanup_release_effect_invalid")
    for field in ("current_status", "retention_redaction", "action_budget", "kill_switch", "cleanup_rollback", "mutation_check", "reason_code"):
        if not SAFE_SLUG_RE.fullmatch(row[field]):
            raise ContractError(f"cleanup_slug_invalid:{field}")
    if row["expires_at"] != "not_set":
        _utc(row["expires_at"])
    passed = _cleanup_passes(row, generated_at)
    if row["terminal_status"] == "observed_pass" and not passed:
        raise ContractError("cleanup_false_pass")
    if not passed and row["release_effect"] != "blocks_release":
        raise ContractError("blocked_cleanup_must_block_release")
    return passed


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_summary(authority_bytes: bytes, cleanup_bytes: bytes, generated_at_utc: str) -> dict[str, Any]:
    generated_at = _utc(generated_at_utc)
    authorities = _parse_csv(authority_bytes, AUTHORITY_HEADERS, "authority_ledger")
    cleanup = _parse_csv(cleanup_bytes, CLEANUP_HEADERS, "cleanup_ledger")
    pass_vector = validate_authority_rows(authorities, generated_at)
    cleanup_pass = validate_cleanup_rows(cleanup, generated_at)
    all_pass = all(pass_vector) and cleanup_pass
    selector = authorities[2]["subject_alias"]
    blocked_rows = [row for row, passed in zip(authorities, pass_vector) if not passed]
    if not cleanup_pass:
        blocked_reason_codes = [row["reason_code"] for row in blocked_rows] + [cleanup[0]["reason_code"]]
    else:
        blocked_reason_codes = [row["reason_code"] for row in blocked_rows]
    blocked_reason_codes = sorted(set(blocked_reason_codes))
    return {
        "artifacts": [
            {
                "evidence_status": "confirmed",
                "kind": "readiness_ledger",
                "reference": "docs/qa/reports/task057_phone_full_runtime_authority.readiness-ledger.csv",
                "sha256": _sha256(authority_bytes),
            },
            {
                "evidence_status": "confirmed",
                "kind": "cleanup_ledger",
                "reference": "docs/qa/reports/task057_phone_full_runtime_authority.cleanup-ledger.csv",
                "sha256": _sha256(cleanup_bytes),
            },
        ],
        "blocked_reasons": [] if all_pass else blocked_reason_codes,
        "build_ref": {"alias": "main-apk-03"},
        "coverage_status": "covered" if all_pass else "blocked",
        "evidence_status": "confirmed",
        "execution_status": "pass" if all_pass else "blocked",
        "generated_at_utc": generated_at_utc,
        "payload": {
            "authority_row_count": 7,
            "blocked_row_count": 7 - sum(pass_vector),
            "cleanup_passport_status": "observed_pass" if cleanup_pass else "blocked",
            "go_runtime": all_pass,
            "product_navigation_executed": False,
            "product_runtime_action_count": 0,
            "readiness_decision": "GO_RUNTIME" if all_pass else "BLOCK_RUNTIME",
            "runtime_action_count_by_generator": 0,
            "security_gate": "GO_RUNTIME" if all_pass else "BLOCK_RUNTIME",
        },
        "production_safety_classification": PRODUCTION_SAFETY,
        "provenance": {
            "adb_or_device_action": True,
            "apk_read": True,
            "bounded_metadata_actions_recorded": True,
            "local_only_input_read": True,
            "product_navigation": False,
            "source": "sanitized_task057_metadata_observations_and_tracked_public_safe_ledgers",
        },
        "release_effect": "candidate_evidence" if all_pass else "blocks_release",
        "review": {
            "docs_scribe": "pending_independent_review",
            "qa_reviewer_a": "pending_independent_review",
            "qa_reviewer_b": "pending_independent_review",
            "security_prod_safety_reviewer": "go_runtime" if all_pass else "block_runtime",
        },
        "risks": [
            {
                "evidence_status": "confirmed",
                "id": "TASK057-RISK-FALSE-PASS",
                "summary": "No readiness row may infer another; missing, stale, merged, unsafe, or non-confirmed authority blocks runtime.",
            },
            {
                "evidence_status": "confirmed",
                "id": "TASK057-RISK-DOWNGRADE-BYPASS",
                "summary": "Ordinary downgrade rejection must remain preserved; uninstall, clear-data, patching, and downgrade bypass remain forbidden.",
            },
        ],
        "run_id": BASELINE_RUN_ID if not all_pass else "task057-readiness-authority-go-runtime-001",
        "schema_validation_status": "pass",
        "schema_version": SCHEMA_VERSION,
        "target_alias": selector,
        "task_id": TASK_ID,
        "unknowns": [
            {
                "evidence_status": row["evidence_status"],
                "id": row["authority_id"],
                "reason_code": row["reason_code"],
            }
            for row in blocked_rows
        ],
        "verification": [
            {"check": "exact_seven_authority_rows", "evidence_status": "confirmed", "result_count": 7, "status": "pass"},
            {"check": "readiness_authority", "evidence_status": "confirmed", "result_count": sum(pass_vector), "status": "pass" if all_pass else "blocked"},
            {"check": "product_navigation", "evidence_status": "unknown", "result_count": 0, "status": "not_run"},
        ],
    }


def build_baseline_bundle() -> dict[Path, bytes]:
    authority = _csv_bytes(AUTHORITY_HEADERS, baseline_authority_rows())
    cleanup = _csv_bytes(CLEANUP_HEADERS, baseline_cleanup_rows())
    summary = _json_bytes(build_summary(authority, cleanup, BASELINE_GENERATED_AT))
    return {AUTHORITY_OUTPUT: authority, CLEANUP_OUTPUT: cleanup, REPORT_OUTPUT: summary}


def validate_bundle(
    bundle: Mapping[Path, bytes],
    *,
    validate_disk_schema: bool = False,
    validation_time: datetime | None = None,
) -> None:
    missing = {AUTHORITY_OUTPUT, CLEANUP_OUTPUT, REPORT_OUTPUT} - set(bundle)
    if missing:
        raise ContractError("report_bundle_missing_artifact")
    try:
        summary = json.loads(
            bundle[REPORT_OUTPUT].decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("summary_json_invalid") from exc
    if not isinstance(summary, dict):
        raise ContractError("summary_must_be_object")
    expected = build_summary(bundle[AUTHORITY_OUTPUT], bundle[CLEANUP_OUTPUT], summary.get("generated_at_utc", ""))
    if summary != expected:
        raise ContractError("summary_semantic_or_hash_drift")
    if summary["execution_status"] == "pass":
        current = validation_time or datetime.now(timezone.utc)
        authority_rows = _parse_csv(bundle[AUTHORITY_OUTPUT], AUTHORITY_HEADERS, "authority_ledger")
        cleanup_rows = _parse_csv(bundle[CLEANUP_OUTPUT], CLEANUP_HEADERS, "cleanup_ledger")
        if not all(validate_authority_rows(authority_rows, current)) or not validate_cleanup_rows(cleanup_rows, current):
            raise ContractError("go_runtime_authority_expired_or_not_current")
    if validate_disk_schema:
        errors = _validate_v2_envelope(summary, REPO_ROOT)
        if errors:
            raise ContractError("summary_v2_invalid:" + ",".join(errors))


def validate_static_contracts() -> None:
    if len(AUTHORITY_CONTRACT) != 7 or len(set(EXPECTED_AUTHORITY_IDS)) != 7:
        raise ContractError("internal_authority_contract_not_exactly_seven")
    text = TASK_SPEC.read_text(encoding="utf-8")
    for phrase in ("exactly seven", "main-apk-03", "current-phone-selector", "GO_RUNTIME", "downgrade rejection"):
        if phrase not in text:
            raise ContractError("task_spec_required_contract_drift")


def _disk_bundle() -> dict[Path, bytes]:
    bundle: dict[Path, bytes] = {}
    for path in (AUTHORITY_OUTPUT, CLEANUP_OUTPUT, REPORT_OUTPUT):
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"tracked_artifact_missing_or_link:{path.name}")
        bundle[path] = path.read_bytes()
    return bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true", help="validate fixed tracked contracts without writing")
    modes.add_argument("--write-baseline", action="store_true", help="write the fixed fail-closed tracked bundle")
    modes.add_argument("--generate-summary", action="store_true", help="derive summary from the fixed tracked sanitized ledgers")
    modes.add_argument("--validate-report", action="store_true", help="validate the fixed tracked report bundle")
    parser.add_argument("--generated-at-utc", help="explicit public UTC timestamp for summary generation")
    args = parser.parse_args(argv)
    try:
        validate_static_contracts()
        if args.generated_at_utc and not args.generate_summary:
            raise ContractError("generated_at_only_allowed_with_generate_summary")
        if args.write_baseline:
            for path, data in build_baseline_bundle().items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        elif args.generate_summary:
            authority = AUTHORITY_OUTPUT.read_bytes()
            cleanup = CLEANUP_OUTPUT.read_bytes()
            generated_at = args.generated_at_utc or _now_utc_text()
            REPORT_OUTPUT.write_bytes(_json_bytes(build_summary(authority, cleanup, generated_at)))
        elif args.validate_report:
            validate_bundle(_disk_bundle(), validate_disk_schema=True)
    except (ContractError, OSError, UnicodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print("PASS: TASK-057 public-safe readiness authority contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

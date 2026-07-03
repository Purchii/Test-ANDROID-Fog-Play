"""Synthetic-only specimens for public redaction and safety regression tests.

The values in this module are fabricated canaries. They intentionally resemble
private data classes that must never be published unredacted, but they are not
derived from runtime evidence, APKs, local secrets, endpoints or device state.
CLI output is category/id-only by design.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from automation.device_inventory.generate_adb_device_inventory import (
    _public_safety_findings as device_inventory_public_safety_findings,
)
from automation.device_inventory.generate_adb_device_inventory import (
    _sanitize_public_json as sanitize_device_inventory_public_json,
)
from automation.native_regression.run_native_regression_probe import (
    public_safety_findings as native_regression_public_safety_findings,
)
from automation.post_auth_navigation.run_post_auth_navigation_probe import (
    public_safety_findings as post_auth_public_safety_findings,
)


@dataclass(frozen=True)
class SyntheticSpecimen:
    """One fabricated sensitive-looking value and its expected public guard."""

    specimen_id: str
    category: str
    value: str
    expected_finding_terms: tuple[str, ...]
    sensitive_fragments: tuple[str, ...] = ()
    synthetic: bool = True
    public_safe: bool = True
    provenance: str = "fabricated_task017_canary"
    release_gate_redaction_expected: bool = False
    webview_payment_redaction_expected: bool = False
    device_inventory_redaction_expected: bool = False
    description: str = ""


SYNTHETIC_SPECIMENS: tuple[SyntheticSpecimen, ...] = (
    SyntheticSpecimen(
        specimen_id="SRC-001",
        category="credential_like",
        value="password=SYNTHETIC_ONLY_PASSWORD_123",
        expected_finding_terms=("secret-like",),
        sensitive_fragments=("SYNTHETIC_ONLY_PASSWORD_123",),
        release_gate_redaction_expected=True,
        webview_payment_redaction_expected=True,
        device_inventory_redaction_expected=True,
        description="Fabricated password-style key/value.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-002",
        category="token_like",
        value="authorization=Bearer_SYNTHETIC_ONLY_TOKEN_123",
        expected_finding_terms=("secret-like",),
        sensitive_fragments=("Bearer_SYNTHETIC_ONLY_TOKEN_123",),
        release_gate_redaction_expected=True,
        webview_payment_redaction_expected=True,
        device_inventory_redaction_expected=True,
        description="Fabricated bearer-token-style key/value.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-003",
        category="url_endpoint_like",
        value="https://synthetic.invalid/api/private/path?query=synthetic",
        expected_finding_terms=("URL-like",),
        sensitive_fragments=("synthetic.invalid",),
        release_gate_redaction_expected=True,
        webview_payment_redaction_expected=True,
        description="Fabricated URL/endpoint-like value under reserved .invalid.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-004",
        category="route_deeplink_like",
        value="deeplink=syntheticapp://private/route?payload=synthetic",
        expected_finding_terms=("private route",),
        sensitive_fragments=("syntheticapp://private/route",),
        description="Fabricated deeplink/internal-route key/value.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-005",
        category="local_apk_path_like",
        value=r"C:\Users\qa\private\task-005\synthetic-build.apk",
        expected_finding_terms=("raw local path", "raw artifact path"),
        sensitive_fragments=(r"C:\Users\qa", "synthetic-build.apk"),
        release_gate_redaction_expected=True,
        webview_payment_redaction_expected=True,
        description="Fabricated local APK path-like reference.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-006",
        category="hash_like",
        value="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        expected_finding_terms=("hash-like",),
        sensitive_fragments=("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",),
        release_gate_redaction_expected=True,
        webview_payment_redaction_expected=True,
        description="Fabricated SHA-256-like value.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-007",
        category="device_identifier_like",
        value="AA:BB:CC:DD:EE:FF",
        expected_finding_terms=("MAC-like", "identifier-like"),
        sensitive_fragments=("AA:BB:CC:DD:EE:FF",),
        device_inventory_redaction_expected=True,
        description="Fabricated MAC/device identifier-like value.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-008",
        category="phone_otp_like",
        value="+7 000 000-00-00 otp=123456",
        expected_finding_terms=("phone-like", "secret-like"),
        sensitive_fragments=("+7 000 000-00-00", "123456"),
        device_inventory_redaction_expected=True,
        description="Fabricated phone and OTP-like combined value.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-009",
        category="payment_account_like",
        value="account_id=acct_synthetic_0001 payment_token=pay_synthetic_0001",
        expected_finding_terms=("raw account identifier", "secret-like"),
        sensitive_fragments=("acct_synthetic_0001", "pay_synthetic_0001"),
        webview_payment_redaction_expected=True,
        description="Fabricated account/payment-token-style value.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-010",
        category="qr_payload_like",
        value="qr_target=https://synthetic.invalid/pay?token=synthetic_qr_token",
        expected_finding_terms=("URL-like", "fixed dynamic-value dump"),
        sensitive_fragments=("synthetic.invalid", "synthetic_qr_token"),
        release_gate_redaction_expected=True,
        webview_payment_redaction_expected=True,
        description="Fabricated QR payload-like value.",
    ),
    SyntheticSpecimen(
        specimen_id="SRC-011",
        category="raw_evidence_reference_like",
        value=".qa_local/evidence/task-020/run/screen.png",
        expected_finding_terms=("raw local path", "raw artifact path"),
        sensitive_fragments=(".qa_local/evidence", "screen.png"),
        description="Fabricated raw evidence artifact reference.",
    ),
)

REQUIRED_CATEGORIES = frozenset(specimen.category for specimen in SYNTHETIC_SPECIMENS)

EXPECTED_VALIDATOR_COVERAGE = {
    "post_auth_navigation": tuple(specimen.specimen_id for specimen in SYNTHETIC_SPECIMENS),
    "native_regression": (
        "SRC-001",
        "SRC-002",
        "SRC-003",
        "SRC-004",
        "SRC-005",
        "SRC-006",
        "SRC-007",
        "SRC-008",
        "SRC-010",
        "SRC-011",
    ),
    "device_inventory": (
        "SRC-001",
        "SRC-002",
        "SRC-003",
        "SRC-004",
        "SRC-005",
        "SRC-007",
        "SRC-008",
        "SRC-010",
    ),
}


def iter_specimens() -> tuple[SyntheticSpecimen, ...]:
    return SYNTHETIC_SPECIMENS


def specimen_ids() -> tuple[str, ...]:
    return tuple(specimen.specimen_id for specimen in SYNTHETIC_SPECIMENS)


def specimen_by_id(specimen_id: str) -> SyntheticSpecimen:
    for specimen in SYNTHETIC_SPECIMENS:
        if specimen.specimen_id == specimen_id:
            return specimen
    raise KeyError(f"Unknown synthetic redaction specimen id: {specimen_id}")


def public_summary() -> dict[str, Any]:
    """Return corpus metadata without raw specimen values."""

    return {
        "schema_version": "task-017-synthetic-redaction-corpus-v1",
        "source": "synthetic_only_public_safe_canaries",
        "runtime_execution_status": "not_run",
        "apk_inspection_status": "not_run",
        "raw_evidence_inspection_status": "not_run",
        "specimen_count": len(SYNTHETIC_SPECIMENS),
        "categories": sorted(REQUIRED_CATEGORIES),
        "specimens": [
            {
                "specimen_id": specimen.specimen_id,
                "category": specimen.category,
                "description": specimen.description,
                "synthetic": specimen.synthetic,
                "public_safe": specimen.public_safe,
                "provenance": specimen.provenance,
                "expected_finding_terms": list(specimen.expected_finding_terms),
                "sensitive_fragment_count": len(specimen.sensitive_fragments),
                "release_gate_redaction_expected": specimen.release_gate_redaction_expected,
                "webview_payment_redaction_expected": specimen.webview_payment_redaction_expected,
                "device_inventory_redaction_expected": specimen.device_inventory_redaction_expected,
            }
            for specimen in SYNTHETIC_SPECIMENS
        ],
    }


def release_gate_metadata_for_specimen(specimen: SyntheticSpecimen) -> dict[str, Any]:
    """Build metadata that feeds an existing public report redactor."""

    safe_note = f"Synthetic redaction corpus specimen {specimen.specimen_id}."
    return {
        "prerequisites": {
            "approved_build": {
                "present": True,
                "evidence_status": "confirmed",
                "note": safe_note,
            },
            "approved_target": {
                "present": True,
                "evidence_status": "confirmed",
                "note": specimen.value,
            },
            "approved_config": {
                "present": True,
                "evidence_status": "confirmed",
                "note": safe_note,
            },
            "redaction_policy": {
                "present": True,
                "evidence_status": "confirmed",
                "note": safe_note,
            },
            "synthetic_fixture_policy": {
                "present": True,
                "evidence_status": "confirmed",
                "note": safe_note,
            },
        },
        "release_gates": {
            "redacted_evidence": {
                "status": "pass",
                "evidence_status": "confirmed",
                "note": specimen.value,
                "artifacts": [
                    {
                        "name": f"{specimen.specimen_id}-artifact",
                        "reference": specimen.value,
                        "evidence_status": "confirmed",
                    }
                ],
            }
        },
        "risks": [
            {
                "id": specimen.specimen_id,
                "level": "High",
                "evidence_status": "confirmed",
                "summary": specimen.value,
            }
        ],
        "unknowns": [
            {
                "id": f"{specimen.specimen_id}-unknown",
                "evidence_status": "unknown",
                "question": specimen.value,
            }
        ],
        "verification": [
            {
                "name": specimen.specimen_id,
                "classification": "PROD_SAFE",
                "result": "pass",
                "evidence_status": "confirmed",
                "note": specimen.value,
            }
        ],
        "review": {
            "qa_reviewer_a": "approved",
            "qa_reviewer_b": "approved",
            "security_prod_safety_reviewer": "approved",
            "docs_scribe": "approved",
        },
    }


def webview_payment_metadata_for_specimen(specimen: SyntheticSpecimen) -> dict[str, Any]:
    """Build metadata that feeds the TASK-008 WebView/payment redactor."""

    safe_note = f"Synthetic redaction corpus specimen {specimen.specimen_id}."
    prerequisite = {
        "present": True,
        "evidence_status": "confirmed",
        "note": safe_note,
    }
    metadata = {
        "approved_build": prerequisite,
        "approved_target": prerequisite,
        "approved_config": prerequisite,
        "webview_fixture_policy": prerequisite,
        "payment_staging_policy": prerequisite,
        "synthetic_user_policy": prerequisite,
        "resource_budget": prerequisite,
        "redaction_policy": prerequisite,
        "evidence_storage": prerequisite,
        "cleanup_rollback": prerequisite,
        "security_review": prerequisite,
        "qa_review": prerequisite,
        "flow_aliases": [
            {
                "alias": f"webview-payment-template-{specimen.specimen_id.lower()}",
                "surface_category": "synthetic_redaction",
                "fixture_category": "synthetic_only",
                "allowed_scope": "plan_only",
                "evidence_status": "confirmed",
                "notes": specimen.value,
            }
        ],
        "artifacts": [
            {
                "name": f"{specimen.specimen_id}-artifact",
                "reference": specimen.value,
                "evidence_status": "confirmed",
            }
        ],
    }
    metadata["approved_target"] = {
        "present": True,
        "evidence_status": "confirmed",
        "note": specimen.value,
    }
    return metadata


def validator_findings_for_specimen(specimen: SyntheticSpecimen) -> dict[str, tuple[str, ...]]:
    payload = {"synthetic_specimen": specimen.value}
    return {
        "post_auth_navigation": tuple(post_auth_public_safety_findings(payload)),
        "native_regression": tuple(native_regression_public_safety_findings(payload)),
        "device_inventory": tuple(device_inventory_public_safety_findings(payload)),
    }


def sanitized_device_inventory_payload_for_specimen(specimen: SyntheticSpecimen) -> tuple[dict[str, Any], bool]:
    payload = {"synthetic_specimen": specimen.value}
    sanitized, redacted = sanitize_device_inventory_public_json(payload)
    if not isinstance(sanitized, dict):
        return {"synthetic_specimen": "unknown"}, True
    return sanitized, redacted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List TASK-017 synthetic redaction corpus ids and categories only.")
    parser.add_argument("--json", action="store_true", help="Emit the public corpus summary as JSON.")
    args = parser.parse_args(argv)

    summary = public_summary()
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for item in summary["specimens"]:
            print(f"{item['specimen_id']} {item['category']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
from pathlib import Path

from automation.static_text_inventory.build_task035_static_text_inventory import (
    build_report,
    classify_text,
    validate_public_report,
)


def _write_source(path: Path, strings: list[str], total: int | None = None) -> None:
    source = {
        "resources": {
            "likely_ui_string_count": total if total is not None else len(strings),
            "likely_ui_strings_sample": strings,
            "localization_qualifiers": [],
            "resource_key_samples": ["title", "button"],
            "resource_type_names": ["string", "plurals"],
        }
    }
    path.write_text(json.dumps(source), encoding="utf-8")


def test_build_report_keeps_raw_text_local_and_public_summary_sanitized(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(
        source,
        [
            "Login with a different number",
            "https://synthetic.invalid/private?token=secret",
            "Payment token is not displayed",
        ],
        total=5,
    )

    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    assert report["overall_status"] == "partial_blocked"
    assert report["static_text_inventory"]["likely_ui_string_total_from_source"] == 5
    assert report["static_text_inventory"]["available_raw_sample_inventory_count"] == 3
    assert report["static_text_inventory"]["missing_raw_value_count"] == 2
    assert report["static_text_inventory"]["coverage_status"] == "blocked_by_missing_full_static_text_values_source"
    assert report["public_safety"]["public_report_contains_raw_text_values"] is False
    assert validate_public_report(report) == []

    local_lines = local_inventory.read_text(encoding="utf-8").splitlines()
    assert len(local_lines) == 3
    assert "Login with a different number" in local_lines[0]

    public_payload = json.dumps(report, ensure_ascii=False)
    assert "Login with a different number" not in public_payload
    assert "synthetic.invalid" not in public_payload
    assert "Payment token is not displayed" not in public_payload


def test_public_report_can_pass_when_full_raw_values_are_available(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["One", "Two"])

    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    assert report["overall_status"] == "pass"
    assert report["static_text_inventory"]["coverage_status"] == "complete_full_raw_values_available"
    assert report["blocked_reasons"] == []
    assert validate_public_report(report) == []


def test_validate_public_report_blocks_raw_public_values_and_runtime_overclaim(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["One"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["sample_hash_ledger"][0]["raw_text"] = "should not be public"
    report["sample_hash_ledger"][0]["sha256"] = "a" * 64
    report["execution_boundaries"]["runtime_execution_status"] = "pass"
    report["public_safety"]["raw_static_text_values_public"] = True

    errors = validate_public_report(report)

    assert any("raw_static_text_values_public" in error for error in errors)
    assert any("runtime_execution_status" in error for error in errors)
    assert any("raw_text" in error for error in errors)
    assert any("full raw hash" in error for error in errors)


def test_validate_public_report_blocks_unknown_fields_and_plain_raw_text_outside_schema(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["Login with a different number"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["leaked_raw_string"] = "Login with a different number"
    report["source_artifact"]["notes"] = "Login with a different number"

    errors = validate_public_report(report)

    assert any("unknown top-level" in error for error in errors)
    assert any("source_artifact contains unknown" in error for error in errors)


def test_validate_public_report_blocks_missing_full_list_false_pass(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["One", "Two"], total=5)
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["overall_status"] = "pass"
    report["static_text_inventory"]["coverage_status"] = "complete_full_raw_values_available"
    report["static_text_inventory"]["full_raw_value_list_available_in_source"] = True
    report["blocked_reasons"] = []

    errors = validate_public_report(report)

    assert any("overall_status must be partial_blocked" in error for error in errors)
    assert any("coverage_status must be blocked_by_missing" in error for error in errors)
    assert any("full_raw_value_list_available_in_source must be false" in error for error in errors)
    assert any("blocked_reasons must include" in error for error in errors)


def test_validate_public_report_reconciles_ledger_and_classification_summary(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["One", "Two"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["sample_hash_ledger"] = []
    report["classification_summary"] = {
        "category_counts": {},
        "redaction_class_counts": {},
        "length_buckets": {},
    }

    errors = validate_public_report(report)

    assert any("sample_hash_ledger length must match" in error for error in errors)

    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")
    report["classification_summary"] = {
        "category_counts": {},
        "redaction_class_counts": {},
        "length_buckets": {},
    }

    errors = validate_public_report(report)

    assert any("classification_summary.category_counts must reconcile" in error for error in errors)
    assert any("classification_summary.redaction_class_counts must reconcile" in error for error in errors)
    assert any("classification_summary.length_buckets must reconcile" in error for error in errors)


def test_validate_public_report_blocks_source_raw_public_flag(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["One"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["source_artifact"]["raw_values_public"] = True

    errors = validate_public_report(report)

    assert any("source_artifact.raw_values_public" in error for error in errors)


def test_validate_public_report_blocks_negative_counts(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["One"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["static_text_inventory"]["likely_ui_string_total_from_source"] = -1
    report["static_text_inventory"]["available_raw_sample_inventory_count"] = 0
    report["static_text_inventory"]["missing_raw_value_count"] = -1

    errors = validate_public_report(report)

    assert any("count fields must be non-negative" in error for error in errors)


def test_validate_public_report_blocks_sample_count_greater_than_total(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["One", "Two"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["static_text_inventory"]["likely_ui_string_total_from_source"] = 1
    report["static_text_inventory"]["available_raw_sample_inventory_count"] = 2
    report["static_text_inventory"]["missing_raw_value_count"] = -1

    errors = validate_public_report(report)

    assert any("count fields must be non-negative" in error for error in errors)

    report["static_text_inventory"]["missing_raw_value_count"] = 0
    errors = validate_public_report(report)

    assert any("available_raw_sample_inventory_count must not exceed" in error for error in errors)


def test_validate_public_report_blocks_raw_text_in_allowed_follow_up_action_field(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["Login with a different number"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["follow_up_actions"][0]["action"] = "Login with a different number"

    errors = validate_public_report(report)

    assert any("follow_up_actions.owner_input_or_local_artifact.action must be" in error for error in errors)


def test_validate_public_report_blocks_plain_text_generated_timestamp(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["Login with a different number"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    report["generated_at_utc"] = "Login with a different number"

    errors = validate_public_report(report)

    assert any("generated_at_utc must be an ISO-8601 UTC timestamp" in error for error in errors)


def test_validate_public_report_blocks_negative_secondary_counts(tmp_path):
    source = tmp_path / "apk_analysis_sanitized.json"
    local_inventory = tmp_path / ".qa_local/static_text_inventory/task035.local.jsonl"
    _write_source(source, ["One"])
    report = build_report(source, local_inventory, generated_at_utc="2026-07-06T00:00:00Z")

    for key in (
        "duplicate_sample_hashes",
        "localization_qualifier_count",
        "resource_key_sample_count",
        "resource_type_count",
    ):
        candidate = json.loads(json.dumps(report))
        candidate["static_text_inventory"][key] = -1

        errors = validate_public_report(candidate)

        assert any(f"static_text_inventory.{key} must be a non-negative integer" in error for error in errors)


def test_classify_text_marks_high_risk_text_families():
    classification = classify_text("Pay by card at https://synthetic.invalid with otp=123456")

    assert "url_or_domain_like" in classification["categories"]
    assert "auth_phone_otp_captcha_like" in classification["categories"]
    assert "payment_or_account_like" in classification["categories"]
    assert "endpoint_or_domain_like" in classification["redaction_classes"]
    assert "phone_otp_captcha_like" in classification["redaction_classes"]

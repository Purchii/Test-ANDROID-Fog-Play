import json
from copy import deepcopy
from pathlib import Path

import pytest

from automation.approvals.validate_approval_metadata import build_report, main


def _happy_metadata():
    return {
        "schema_version": "task-015-approval-metadata-v1",
        "task_id": "TASK-005",
        "scope_version": "task-005-limited-runtime-smoke-v1",
        "approval_status": "approved",
        "approval_evidence_status": "confirmed",
        "expires_at": "2099-01-01",
        "approved_by_role": "project_owner",
        "approved_build_apk": {
            "approved": True,
            "build_alias": "task-005-local-apk-001",
            "storage_policy": "local_ignored_path_only",
            "expected_local_path_pattern": ".qa_local/apks/task-005/app-under-test.apk",
            "sha256_required": True,
            "sha256_public_value_allowed": False,
            "allowed_actions": ["install", "launch", "observe"],
            "forbidden_actions": [
                "commit",
                "upload",
                "archive",
                "decompile",
                "patch",
                "resign",
                "extract_private_endpoints",
                "extract_secrets",
            ],
        },
        "approved_targets": {
            "approved": True,
            "device_aliases": ["tv-tcl-001"],
            "allowed_categories": ["physical_android_tv", "android_stb"],
            "device_aliases_required": True,
            "devices": [
                {
                    "device_alias": "tv-tcl-001",
                    "runtime_profile_alias": "tv-tcl-a11-001",
                    "category": "android_tv",
                    "priority": "P0",
                    "form_factor": "tv",
                    "input_method": "dpad_remote",
                    "android_major": 11,
                    "api_level": 30,
                    "adb_available": "yes",
                    "google_play_services": "yes",
                    "classification_confidence": "manual_confirmed",
                    "manual_review_required": False,
                    "forbidden_identifiers_excluded": True,
                }
            ],
        },
        "runtime_execution": {
            "allowed": True,
            "auth_mode": "synthetic_login_if_required",
            "allowed_scope": [
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
            ],
            "forbidden_scope": [
                "payment",
                "subscription",
                "purchase",
                "stream",
                "webrtc",
                "media_playback",
                "webview",
                "redirect_flow",
                "production_mutation",
                "security_bypass",
                "decompilation",
                "patching",
                "resigning",
            ],
        },
        "synthetic_qa_user": {
            "approved": True,
            "alias": "qa-user-phone-001",
            "raw_phone_allowed_in_public_docs": False,
            "raw_otp_allowed_in_public_docs": False,
            "local_secret_file_pattern": ".qa_local/secrets/qa_user.env",
            "repo_allowed_file": "docs/approvals/qa_user.env.example",
            "allowed_auth_scope": ["login", "logout", "session_persistence"],
            "forbidden_account_actions": [
                "payment",
                "purchase",
                "profile_mutation",
                "destructive_account_action",
            ],
        },
        "fixtures": {
            "stream_fixture": "out_of_scope",
            "webview_fixture": "out_of_scope",
            "payment_staging_fixture": "out_of_scope",
        },
        "evidence_capture": {
            "status": "approved_local_redacted_summary_only",
            "screenshots": "yes_local_only_redacted_summary",
            "logs_logcat": "yes_local_only_redacted_summary",
            "videos": "no_by_default",
            "raw_storage_policy": "local_ignored_path_only",
            "raw_storage_path_pattern": ".qa_local/evidence/task-005/",
            "public_report_policy": "redacted_summaries_only",
            "retention_days": 7,
        },
        "cleanup_rollback": {
            "approved": True,
            "allowed_levels": [
                "C1_background_foreground",
                "C2_force_stop_relaunch",
                "C3_clear_cache",
                "C4_clear_app_data",
            ],
            "requires_separate_approval": ["C5_uninstall_reinstall"],
            "authorized_zone_scopes": [
                "force_stop_relaunch_with_auth_state_preserved",
                "background_foreground_without_force_stop",
            ],
            "clean_state_scope": "clear_app_data_before_scenario_and_record_precondition",
        },
        "required_reviews": {
            "qa_reviewer_a": "approved",
            "qa_reviewer_b": "confirmed",
            "security_prod_safety_reviewer": "approved",
            "docs_scribe": "confirmed",
        },
    }


def _write_metadata(tmp_path, metadata):
    path = tmp_path / "approval_metadata.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    return path


def _report_for(tmp_path, mutator=None):
    metadata = _happy_metadata()
    if mutator is not None:
        mutator(metadata)
    return build_report(_write_metadata(tmp_path, metadata))


def test_happy_path_approves_limited_runtime_but_runtime_remains_not_run(tmp_path):
    report = _report_for(tmp_path)

    assert report["approval_decision"] == "approved_for_limited_runtime"
    assert report["runtime_execution_status"] == "not_run"
    assert report["runtime_evidence_status"] == "unknown"
    assert report["blocked_reasons"] == []
    assert report["production_safety_classification"] == "PROD_SAFE"


def test_example_pending_metadata_is_blocked():
    report = build_report(Path("docs/approvals/approval_metadata.example.json"))

    assert report["approval_decision"] == "blocked"
    assert report["runtime_execution_status"] == "not_run"
    assert report["blocked_reasons"]


def test_evidence_policy_pending_blocks(tmp_path):
    report = _report_for(tmp_path, lambda metadata: metadata["evidence_capture"].update({"status": "pending"}))

    assert report["approval_decision"] == "blocked"
    assert any("evidence_capture.status" in reason for reason in report["blocked_reasons"])


def test_missing_reviewer_blocks(tmp_path):
    def mutate(metadata):
        del metadata["required_reviews"]["qa_reviewer_b"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("required_reviews.qa_reviewer_b" in reason for reason in report["blocked_reasons"])


def test_pending_security_reviewer_blocks(tmp_path):
    def mutate(metadata):
        metadata["required_reviews"]["security_prod_safety_reviewer"] = "pending"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("security_prod_safety_reviewer" in reason for reason in report["blocked_reasons"])


def test_expired_approval_blocks(tmp_path):
    report = _report_for(tmp_path, lambda metadata: metadata.update({"expires_at": "2020-01-01"}))

    assert report["approval_decision"] == "blocked"
    assert any("expires_at" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("status", ["unknown", "likely", "hypothesis"])
def test_non_confirmed_approval_evidence_blocks(tmp_path, status):
    report = _report_for(tmp_path, lambda metadata: metadata.update({"approval_evidence_status": status}))

    assert report["approval_decision"] == "blocked"
    assert any("approval_evidence_status" in reason for reason in report["blocked_reasons"])


def test_apk_path_outside_qa_local_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_build_apk"]["expected_local_path_pattern"] = "C:\\Users\\qa\\Downloads\\app.apk"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("expected_local_path_pattern" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "path",
    [
        ".qa_local/secrets/app-under-test.apk",
        ".qa_local/evidence/task-005/app.apk",
        ".qa_local/devices/app.apk",
        ".qa_local/apks/task-005/app-under-test.txt",
        ".qa_local/apks/task-005/app.apk.tmp.apk",
        ".qa_local/apks/task-005/*.apk",
        ".qa_local/apks/task-005/secrets/app-under-test.apk",
    ],
)
def test_apk_path_must_use_task005_apk_family_and_extension(tmp_path, path):
    def mutate(metadata):
        metadata["approved_build_apk"]["expected_local_path_pattern"] = path

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any(".qa_local/apks/task-005/" in reason for reason in report["blocked_reasons"])


def test_task005_apk_path_family_and_extension_passes(tmp_path):
    report = _report_for(
        tmp_path,
        lambda metadata: metadata["approved_build_apk"].update(
            {"expected_local_path_pattern": ".qa_local/apks/task-005/app-under-test.apk"}
        ),
    )

    assert report["approval_decision"] == "approved_for_limited_runtime"


@pytest.mark.parametrize("value", [None, "", "bad alias", "build"])
def test_missing_or_invalid_build_alias_blocks(tmp_path, value):
    def mutate(metadata):
        if value is None:
            del metadata["approved_build_apk"]["build_alias"]
        else:
            metadata["approved_build_apk"]["build_alias"] = value

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("approved_build_apk.build_alias" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "build_alias",
    [
        "task-005-secret-apk-001",
        "task-005-token-apk-001",
        "task-005-password-apk-001",
        "task-005-cookie-apk-001",
        "task-005-session-apk-001",
        "task-005-serial-apk-001",
        "task-005-imei-apk-001",
        "task-005-mac-apk-001",
        "task-005-androidid-apk-001",
        "task-005-phone-apk-001",
        "brand/product/device:14/build",
    ],
)
def test_semantically_unsafe_build_alias_blocks(tmp_path, build_alias):
    def mutate(metadata):
        metadata["approved_build_apk"]["build_alias"] = build_alias

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("approved_build_apk.build_alias" in reason for reason in report["blocked_reasons"])


def test_task_005_local_apk_build_alias_remains_valid(tmp_path):
    report = _report_for(tmp_path)

    assert report["approval_decision"] == "approved_for_limited_runtime"


@pytest.mark.parametrize(
    "build_alias",
    [
        "task-api-key-001",
        "task-apikey-001",
        "task-api_key-001",
        "task-extract-secrets-001",
        "task-extract_secrets-001",
        "task-extractsecrets-001",
        "task-private-endpoints-001",
        "task-private_endpoints-001",
        "task-privateendpoints-001",
    ],
)
def test_build_alias_compound_reserved_tokens_block(tmp_path, build_alias):
    def mutate(metadata):
        metadata["approved_build_apk"]["build_alias"] = build_alias

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("approved_build_apk.build_alias" in reason for reason in report["blocked_reasons"])


def test_nested_path_traversal_inside_qa_local_blocks(tmp_path):
    def mutate(metadata):
        metadata["evidence_capture"]["raw_storage_path_pattern"] = ".qa_local/evidence/../../outside"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("raw_storage_path_pattern" in reason for reason in report["blocked_reasons"])


def test_unexpected_schema_version_blocks(tmp_path):
    report = _report_for(tmp_path, lambda metadata: metadata.update({"schema_version": "unexpected-schema"}))

    assert report["approval_decision"] == "blocked"
    assert any("schema_version must be task-015-approval-metadata-v1" in reason for reason in report["blocked_reasons"])


def test_unexpected_task_id_blocks(tmp_path):
    report = _report_for(tmp_path, lambda metadata: metadata.update({"task_id": "TASK-999"}))

    assert report["approval_decision"] == "blocked"
    assert any("task_id must be TASK-005" in reason for reason in report["blocked_reasons"])


def test_unknown_top_level_field_blocks_approved_metadata(tmp_path):
    report = _report_for(tmp_path, lambda metadata: metadata.update({"comment": "reviewed"}))

    assert report["approval_decision"] == "blocked"
    assert any("metadata contains unsupported fields" in reason for reason in report["blocked_reasons"])


def test_unknown_fixture_field_blocks_approved_metadata(tmp_path):
    def mutate(metadata):
        metadata["fixtures"]["other_fixture"] = "approved"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("fixtures contains unsupported fields" in reason for reason in report["blocked_reasons"])


def test_unknown_required_reviewer_field_blocks_approved_metadata(tmp_path):
    def mutate(metadata):
        metadata["required_reviews"]["legal_reviewer"] = "rejected"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("required_reviews contains unsupported fields" in reason for reason in report["blocked_reasons"])


def test_raw_phone_number_in_metadata_blocks(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["phone"] = "+15551234567"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("Phone-like public value" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "mutator",
    [
        lambda metadata: metadata["approved_build_apk"].update(
            {"expected_local_path_pattern": ".qa_local/apks/192.168.0.1/app.apk"}
        ),
        lambda metadata: metadata["evidence_capture"].update(
            {"raw_storage_path_pattern": ".qa_local/evidence/192.168.0.1/"}
        ),
        lambda metadata: metadata["approved_targets"]["devices"][0].update({"model_family": "192.168.0.1"}),
    ],
)
def test_ip_like_values_in_approval_metadata_block(tmp_path, mutator):
    report = _report_for(tmp_path, mutator)

    assert report["approval_decision"] == "blocked"
    assert any("IP-like public value" in reason for reason in report["blocked_reasons"])


def test_otp_like_value_in_metadata_blocks(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["otp"] = "123456"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("OTP-like public value" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "key,value,expected",
    [
        ("serial", "ABC123", "Forbidden device identifier field"),
        ("imei", "123456789012345", "Forbidden device identifier field"),
        ("mac", "00:11:22:33:44:55", "Forbidden device identifier field"),
        ("android_id", "0123456789abcdef", "Forbidden device identifier field"),
    ],
)
def test_device_inventory_with_forbidden_identifier_blocks(tmp_path, key, value, expected):
    def mutate(metadata):
        metadata["approved_targets"]["devices"] = [{"alias": "tv-001", key: value}]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any(expected in reason for reason in report["blocked_reasons"])


def test_stream_out_of_scope_but_runtime_scope_includes_stream_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].append("stream_startup")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("stream_fixture is out_of_scope" in reason for reason in report["blocked_reasons"])


def test_webview_out_of_scope_but_runtime_scope_includes_webview_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].append("webview_redirect")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("webview_fixture is out_of_scope" in reason for reason in report["blocked_reasons"])


def test_payment_out_of_scope_but_runtime_scope_includes_purchase_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].append("purchase_restore")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("payment_staging_fixture is out_of_scope" in reason for reason in report["blocked_reasons"])


def test_c5_cleanup_without_separate_approval_blocks(tmp_path):
    def mutate(metadata):
        metadata["cleanup_rollback"]["allowed_levels"].append("C5_uninstall_reinstall")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("C5 uninstall/reinstall requires separate approval" in reason for reason in report["blocked_reasons"])


def test_invalid_fixture_status_blocks(tmp_path):
    def mutate(metadata):
        metadata["fixtures"]["stream_fixture"] = "maybe"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("fixtures.stream_fixture" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("status", ["approved", "pending", "blocked"])
def test_task_005_fixture_status_must_remain_out_of_scope(tmp_path, status):
    def mutate(metadata):
        metadata["fixtures"]["stream_fixture"] = status

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("fixtures.stream_fixture must be out_of_scope" in reason for reason in report["blocked_reasons"])


def test_invalid_evidence_capture_value_blocks(tmp_path):
    def mutate(metadata):
        metadata["evidence_capture"]["screenshots"] = "maybe"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("evidence_capture.screenshots" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("logs_logcat", "maybe"),
        ("videos", "maybe"),
        ("logs_logcat", "pending"),
        ("videos", "pending"),
    ],
)
def test_logs_and_video_evidence_values_block_when_invalid_or_pending(tmp_path, field, value):
    def mutate(metadata):
        metadata["evidence_capture"][field] = value

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any(f"evidence_capture.{field}" in reason for reason in report["blocked_reasons"])


def test_unknown_cleanup_level_blocks(tmp_path):
    def mutate(metadata):
        metadata["cleanup_rollback"]["allowed_levels"].append("C6_wipe_device")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("cleanup_rollback.allowed_levels" in reason for reason in report["blocked_reasons"])


def test_unknown_runtime_scope_blocks_even_without_known_forbidden_term(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].append("orientation_check")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("runtime_execution.allowed_scope contains unsupported item" in reason for reason in report["blocked_reasons"])


def test_profile_mutation_runtime_scope_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].append("profile_mutation")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("profile_mutation" in reason for reason in report["blocked_reasons"])


def test_empty_approved_by_role_blocks(tmp_path):
    report = _report_for(tmp_path, lambda metadata: metadata.update({"approved_by_role": ""}))

    assert report["approval_decision"] == "blocked"
    assert any("approved_by_role" in reason for reason in report["blocked_reasons"])


def test_invalid_approved_by_role_blocks(tmp_path):
    report = _report_for(tmp_path, lambda metadata: metadata.update({"approved_by_role": "release_manager"}))

    assert report["approval_decision"] == "blocked"
    assert any("approved_by_role" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("role", ["qa_lead", "security_prod_safety_reviewer"])
def test_allowed_non_owner_approved_by_roles_pass_happy_metadata(tmp_path, role):
    report = _report_for(tmp_path, lambda metadata: metadata.update({"approved_by_role": role}))

    assert report["approval_decision"] == "approved_for_limited_runtime"


def test_unsafe_device_alias_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0]["device_alias"] = "tv-oleg-livingroom-abc123"
        metadata["approved_targets"]["devices"][0]["runtime_profile_alias"] = "tv-oleg-livingroom-a11-abc123"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("device_alias" in reason for reason in report["blocked_reasons"])


def test_split_location_label_device_alias_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["device_aliases"] = ["tv-living-room-001"]
        metadata["approved_targets"]["devices"][0]["device_alias"] = "tv-living-room-001"
        metadata["approved_targets"]["devices"][0]["runtime_profile_alias"] = "tv-living-room-a11-001"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("device_alias" in reason for reason in report["blocked_reasons"])


def test_missing_allowed_categories_blocks(tmp_path):
    def mutate(metadata):
        del metadata["approved_targets"]["allowed_categories"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("approved_targets.allowed_categories" in reason for reason in report["blocked_reasons"])


def test_missing_runtime_profile_alias_blocks(tmp_path):
    def mutate(metadata):
        del metadata["approved_targets"]["devices"][0]["runtime_profile_alias"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("runtime_profile_alias" in reason for reason in report["blocked_reasons"])


def test_unsupported_structured_target_category_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0]["category"] = "smart_fridge"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("category is unsupported" in reason for reason in report["blocked_reasons"])


def test_target_without_forbidden_identifier_exclusion_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0]["forbidden_identifiers_excluded"] = False

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("forbidden_identifiers_excluded" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("field,value", [("network", "home-wifi"), ("room", "livingroom"), ("owner", "oleg")])
def test_unknown_public_device_fields_block(tmp_path, field, value):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0][field] = value

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("unsupported public metadata fields" in reason for reason in report["blocked_reasons"])


def test_synthetic_login_requires_approved_synthetic_user(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["approved"] = False

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("synthetic_login_if_required" in reason for reason in report["blocked_reasons"])


def test_synthetic_login_scope_requires_matching_auth_mode(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["auth_mode"] = "auth_out_of_scope"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("auth_mode must be synthetic_login_if_required" in reason for reason in report["blocked_reasons"])


def test_synthetic_auth_mode_requires_matching_scope(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].remove("synthetic_login_if_required")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("auth_mode synthetic_login_if_required requires matching runtime scope" in reason for reason in report["blocked_reasons"])


def test_missing_auth_mode_blocks(tmp_path):
    def mutate(metadata):
        del metadata["runtime_execution"]["auth_mode"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("runtime_execution.auth_mode" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("auth_mode", ["auth_out_of_scope", "no_auth_required"])
def test_unapproved_synthetic_user_requires_explicit_auth_out_of_scope_and_no_login_scope(tmp_path, auth_mode):
    def mutate(metadata):
        metadata["runtime_execution"]["auth_mode"] = auth_mode
        metadata["runtime_execution"]["allowed_scope"].remove("synthetic_login_if_required")
        metadata["synthetic_qa_user"]["approved"] = False

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "approved_for_limited_runtime"


def test_synthetic_user_approved_requires_local_secret_file_pattern(tmp_path):
    def mutate(metadata):
        del metadata["synthetic_qa_user"]["local_secret_file_pattern"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("local_secret_file_pattern" in reason for reason in report["blocked_reasons"])


def test_synthetic_user_approved_requires_repo_allowed_file(tmp_path):
    def mutate(metadata):
        del metadata["synthetic_qa_user"]["repo_allowed_file"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("repo_allowed_file" in reason for reason in report["blocked_reasons"])


def test_synthetic_user_repo_allowed_file_cannot_be_local_secret(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["repo_allowed_file"] = ".qa_local/secrets/qa_user.env"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("repo_allowed_file" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "path",
    [
        ".qa_local/apks/task-005/app.apk",
        ".qa_local/devices/raw_adb_devices.json",
        ".qa_local/secrets/qa_user.txt",
        ".qa_local/secrets/apks/qa_user.env",
        ".qa_local/secrets/devices/qa_user.env",
    ],
)
def test_synthetic_secret_path_must_use_secret_env_family(tmp_path, path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["local_secret_file_pattern"] = path

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any(".qa_local/secrets/" in reason for reason in report["blocked_reasons"])


def test_synthetic_secret_env_path_passes(tmp_path):
    report = _report_for(
        tmp_path,
        lambda metadata: metadata["synthetic_qa_user"].update(
            {"local_secret_file_pattern": ".qa_local/secrets/qa_user.env"}
        ),
    )

    assert report["approval_decision"] == "approved_for_limited_runtime"


def test_synthetic_user_safe_repo_allowed_file_passes(tmp_path):
    report = _report_for(
        tmp_path,
        lambda metadata: metadata["synthetic_qa_user"].update(
            {"repo_allowed_file": "docs/approvals/qa_user.env.example"}
        ),
    )

    assert report["approval_decision"] == "approved_for_limited_runtime"


@pytest.mark.parametrize("path", ["qa_user.env.example", "docs/secrets/qa_user.env.example"])
def test_synthetic_user_repo_allowed_file_must_use_exact_approved_template(tmp_path, path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["repo_allowed_file"] = path

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("repo_allowed_file" in reason for reason in report["blocked_reasons"])


def test_synthetic_allowed_auth_scope_blocks_payment(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["allowed_auth_scope"] = ["login", "payment"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("allowed_auth_scope" in reason and "payment" in reason for reason in report["blocked_reasons"])


def test_synthetic_login_requires_session_persistence_auth_scope(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["allowed_auth_scope"] = ["login"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("allowed_auth_scope" in reason and "session_persistence" in reason for reason in report["blocked_reasons"])


def test_synthetic_forbidden_account_actions_must_include_payment(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["forbidden_account_actions"].remove("payment")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("forbidden_account_actions" in reason and "payment" in reason for reason in report["blocked_reasons"])


def test_synthetic_forbidden_account_actions_block_typos(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["forbidden_account_actions"] = [
            "payment",
            "purchaze",
            "profile_mutation",
            "destructive_account_action",
        ]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("forbidden_account_actions" in reason and "purchaze" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("field", ["raw_phone_allowed_in_public_docs", "raw_otp_allowed_in_public_docs"])
def test_no_auth_metadata_still_blocks_raw_public_synthetic_flags(tmp_path, field):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].remove("synthetic_login_if_required")
        metadata["runtime_execution"]["auth_mode"] = "no_auth_required"
        metadata["synthetic_qa_user"]["approved"] = False
        metadata["synthetic_qa_user"][field] = True

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("public docs" in reason for reason in report["blocked_reasons"])


def test_phone_only_target_blocks_task_005(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["device_aliases"] = ["unknown-samsung-001"]
        metadata["approved_targets"]["allowed_categories"] = ["android_phone_secondary"]
        metadata["approved_targets"]["devices"] = [
            {
                "device_alias": "unknown-samsung-001",
                "runtime_profile_alias": "unknown-samsung-a14-001",
                "category": "android_phone_secondary",
                "priority": "P2",
                "form_factor": "phone",
                "input_method": "touch",
                "android_major": 14,
                "api_level": 34,
                "adb_available": "yes",
                "google_play_services": "yes",
                "classification_confidence": "manual_confirmed",
                "manual_review_required": False,
                "forbidden_identifiers_excluded": True,
            }
        ]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("actionable P0 Android TV/STB D-pad target" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("adb_available", ["no", "unknown"])
def test_p0_tv_stb_target_without_adb_available_yes_blocks(tmp_path, adb_available):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0]["adb_available"] = adb_available

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("adb_available must be yes" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("confidence", ["heuristic", "manual_review", "unknown"])
def test_p0_tv_stb_target_without_manual_confirmed_classification_blocks(tmp_path, confidence):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0]["classification_confidence"] = confidence

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("classification_confidence must be manual_confirmed" in reason for reason in report["blocked_reasons"])


def test_p0_tv_stb_target_with_manual_review_required_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0]["manual_review_required"] = True

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("manual_review_required must be false" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "device_alias,runtime_profile_alias",
    [
        ("tv-serial-001", "tv-serial-a11-001"),
        ("tv-google-account-001", "tv-google-account-a11-001"),
        ("tv-phone-001", "tv-phone-a11-001"),
        ("tv-otp-001", "tv-otp-a11-001"),
        ("tv-androidid-001", "tv-androidid-a11-001"),
        ("tv-token-001", "tv-token-a11-001"),
        ("tv-session-001", "tv-session-a11-001"),
    ],
)
def test_reserved_alias_tokens_block_device_aliases_and_runtime_profiles(tmp_path, device_alias, runtime_profile_alias):
    def mutate(metadata):
        metadata["approved_targets"]["device_aliases"] = [device_alias]
        metadata["approved_targets"]["devices"][0]["device_alias"] = device_alias
        metadata["approved_targets"]["devices"][0]["runtime_profile_alias"] = runtime_profile_alias

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("alias" in reason for reason in report["blocked_reasons"])


def test_phone_device_alias_allowed_only_as_phone_form_factor_prefix(tmp_path):
    def mutate(metadata):
        phone_device = deepcopy(metadata["approved_targets"]["devices"][0])
        phone_device.update(
            {
                "device_alias": "phone-samsung-001",
                "runtime_profile_alias": "phone-samsung-a14-001",
                "category": "android_phone_secondary",
                "priority": "P2",
                "form_factor": "phone",
                "input_method": "touch",
                "android_major": 14,
                "api_level": 34,
            }
        )
        metadata["approved_targets"]["device_aliases"].append("phone-samsung-001")
        metadata["approved_targets"]["allowed_categories"].append("android_phone_secondary")
        metadata["approved_targets"]["devices"].append(phone_device)

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "approved_for_limited_runtime"


@pytest.mark.parametrize(
    "device_alias,runtime_profile_alias,form_factor",
    [
        ("tv-phone-001", "tv-phone-a11-001", "tv"),
        ("phone-my-phone-001", "phone-my-phone-a14-001", "phone"),
        ("stb-phone-a12-001", "stb-phone-a12-001", "stb"),
        ("unknown-samsung-001", "unknown-samsung-a11-001", "tv"),
        ("stb-xiaomi-001", "stb-xiaomi-a11-001", "tv"),
    ],
)
def test_device_alias_form_factor_mismatch_or_embedded_phone_blocks(tmp_path, device_alias, runtime_profile_alias, form_factor):
    def mutate(metadata):
        metadata["approved_targets"]["device_aliases"] = [device_alias]
        metadata["approved_targets"]["devices"][0]["device_alias"] = device_alias
        metadata["approved_targets"]["devices"][0]["runtime_profile_alias"] = runtime_profile_alias
        metadata["approved_targets"]["devices"][0]["form_factor"] = form_factor

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("alias" in reason or "form-factor prefix" in reason for reason in report["blocked_reasons"])


def test_extra_manual_confirmed_tv_category_with_phone_form_factor_blocks(tmp_path):
    def mutate(metadata):
        extra_device = deepcopy(metadata["approved_targets"]["devices"][0])
        extra_device.update(
            {
                "device_alias": "tv-sony-002",
                "runtime_profile_alias": "tv-sony-a11-002",
                "category": "android_tv",
                "priority": "P1",
                "form_factor": "phone",
                "input_method": "touch",
            }
        )
        metadata["approved_targets"]["device_aliases"].append("tv-sony-002")
        metadata["approved_targets"]["devices"].append(extra_device)

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("form_factor must be tv or stb" in reason for reason in report["blocked_reasons"])


def test_stable_device_alias_must_not_contain_android_version_token(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["device_aliases"] = ["tv-tcl-a11-001"]
        metadata["approved_targets"]["devices"][0]["device_alias"] = "tv-tcl-a11-001"
        metadata["approved_targets"]["devices"][0]["runtime_profile_alias"] = "tv-tcl-a11-a11-001"
        metadata["approved_targets"]["devices"][0]["android_major"] = 11

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("device_alias" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "runtime_profile_alias,android_major",
    [
        ("tv-tcl-a12-001", 11),
        ("tv-sony-a11-001", 11),
        ("tv-tcl-a11-002", 11),
    ],
)
def test_runtime_profile_alias_must_match_device_alias_prefix_index_and_android_major(
    tmp_path,
    runtime_profile_alias,
    android_major,
):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0]["runtime_profile_alias"] = runtime_profile_alias
        metadata["approved_targets"]["devices"][0]["android_major"] = android_major

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("runtime_profile_alias must preserve" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("android_major,api_level", [(13, 30), (16, 30)])
def test_android_major_api_level_mismatch_blocks(tmp_path, android_major, api_level):
    def mutate(metadata):
        metadata["approved_targets"]["devices"][0]["android_major"] = android_major
        metadata["approved_targets"]["devices"][0]["api_level"] = api_level
        metadata["approved_targets"]["devices"][0]["runtime_profile_alias"] = f"tv-tcl-a{android_major}-001"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("Android major/API sanity map" in reason for reason in report["blocked_reasons"])


def test_empty_runtime_scope_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"] = []

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("allowed_scope must be a non-empty list" in reason for reason in report["blocked_reasons"])


def test_duplicate_runtime_scope_item_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].append("install")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("runtime_execution.allowed_scope must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_empty_runtime_forbidden_scope_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["forbidden_scope"] = []

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("runtime_execution.forbidden_scope must be a non-empty list" in reason for reason in report["blocked_reasons"])


def test_missing_required_runtime_forbidden_scope_term_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["forbidden_scope"].remove("payment")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("runtime_execution.forbidden_scope is missing required items" in reason for reason in report["blocked_reasons"])


def test_duplicate_runtime_forbidden_scope_item_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["forbidden_scope"].append("payment")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("runtime_execution.forbidden_scope must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_missing_core_runtime_scope_blocks(tmp_path):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"].remove("initial_focus")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("missing required TASK-005 core items" in reason for reason in report["blocked_reasons"])


def test_crash_anr_scope_requires_logcat_redacted_summary(tmp_path):
    def mutate(metadata):
        metadata["evidence_capture"]["logs_logcat"] = "no"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("crash_anr_logcat_observation requires" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("scope_item", ["first_visible_state", "initial_focus", "minimal_dpad_navigation"])
def test_visual_runtime_scope_requires_screenshot_or_video_redacted_summary(tmp_path, scope_item):
    def mutate(metadata):
        metadata["runtime_execution"]["allowed_scope"] = [
            item for item in metadata["runtime_execution"]["allowed_scope"] if item != "synthetic_login_if_required"
        ]
        metadata["runtime_execution"]["auth_mode"] = "auth_out_of_scope"
        metadata["synthetic_qa_user"]["approved"] = False
        metadata["evidence_capture"]["screenshots"] = "no"
        metadata["evidence_capture"]["videos"] = "no_by_default"
        assert scope_item in metadata["runtime_execution"]["allowed_scope"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("require screenshots or videos" in reason for reason in report["blocked_reasons"])


def test_visual_runtime_scope_accepts_video_redacted_summary_without_screenshots(tmp_path):
    def mutate(metadata):
        metadata["evidence_capture"]["screenshots"] = "no"
        metadata["evidence_capture"]["videos"] = "yes_local_only_redacted_summary"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "approved_for_limited_runtime"


def test_raw_evidence_public_report_policy_blocks(tmp_path):
    def mutate(metadata):
        metadata["evidence_capture"]["public_report_policy"] = "raw_evidence_allowed"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("public_report_policy" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "path",
    [
        ".qa_local/apks/task-005/",
        ".qa_local/secrets/",
        ".qa_local/devices/",
        ".qa_local/evidence/task-005/secrets/",
    ],
)
def test_evidence_path_must_use_task005_evidence_family(tmp_path, path):
    def mutate(metadata):
        metadata["evidence_capture"]["raw_storage_path_pattern"] = path

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any(".qa_local/evidence/task-005/" in reason for reason in report["blocked_reasons"])


def test_task005_evidence_path_passes(tmp_path):
    report = _report_for(
        tmp_path,
        lambda metadata: metadata["evidence_capture"].update(
            {"raw_storage_path_pattern": ".qa_local/evidence/task-005/"}
        ),
    )

    assert report["approval_decision"] == "approved_for_limited_runtime"


@pytest.mark.parametrize("retention_days", [None, 0, -1, 3650, "7", 7.5])
def test_evidence_retention_days_must_be_bounded_integer(tmp_path, retention_days):
    def mutate(metadata):
        metadata["evidence_capture"]["retention_days"] = retention_days

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("retention_days" in reason for reason in report["blocked_reasons"])


def test_evidence_retention_days_seven_passes(tmp_path):
    report = _report_for(tmp_path, lambda metadata: metadata["evidence_capture"].update({"retention_days": 7}))

    assert report["approval_decision"] == "approved_for_limited_runtime"


def test_apk_sha256_required_false_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_build_apk"]["sha256_required"] = False

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("sha256_required" in reason for reason in report["blocked_reasons"])


def test_apk_sha256_public_value_allowed_true_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_build_apk"]["sha256_public_value_allowed"] = True

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("sha256_public_value_allowed" in reason for reason in report["blocked_reasons"])


def test_apk_allowed_actions_containing_decompile_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_build_apk"]["allowed_actions"].append("decompile")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("allowed_actions" in reason and "decompile" in reason for reason in report["blocked_reasons"])


def test_duplicate_apk_allowed_action_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_build_apk"]["allowed_actions"].append("install")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("allowed_actions must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_duplicate_apk_forbidden_action_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_build_apk"]["forbidden_actions"].append("decompile")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("forbidden_actions must not contain duplicates" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("missing_action", ["install", "launch", "observe"])
def test_apk_allowed_actions_missing_required_action_blocks(tmp_path, missing_action):
    def mutate(metadata):
        metadata["approved_build_apk"]["allowed_actions"].remove(missing_action)

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("allowed_actions" in reason and missing_action in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize("missing_action", ["decompile", "extract_secrets"])
def test_apk_forbidden_actions_missing_critical_action_blocks(tmp_path, missing_action):
    def mutate(metadata):
        metadata["approved_build_apk"]["forbidden_actions"].remove(missing_action)

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("forbidden_actions" in reason and missing_action in reason for reason in report["blocked_reasons"])


def test_phone_only_allowed_categories_with_tv_device_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["allowed_categories"] = ["android_phone_secondary"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("category is not allowed" in reason for reason in report["blocked_reasons"])


def test_duplicate_allowed_category_blocks(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["allowed_categories"].append("physical_android_tv")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("allowed_categories must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_device_aliases_must_match_structured_devices(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["device_aliases"] = ["tv-sony-001"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("device_aliases contains aliases missing" in reason for reason in report["blocked_reasons"])


def test_empty_device_aliases_block_even_with_legacy_approved_device_aliases(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["device_aliases"] = []
        metadata["approved_targets"]["approved_device_aliases"] = ["tv-tcl-001"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("device_aliases must be a non-empty list" in reason for reason in report["blocked_reasons"])


def test_duplicate_device_aliases_block(tmp_path):
    def mutate(metadata):
        metadata["approved_targets"]["devices"].append(deepcopy(metadata["approved_targets"]["devices"][0]))

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("device_alias values must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_duplicate_cleanup_level_blocks(tmp_path):
    def mutate(metadata):
        metadata["cleanup_rollback"]["allowed_levels"].append("C1_background_foreground")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("cleanup_rollback.allowed_levels must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_duplicate_synthetic_allowed_auth_scope_blocks(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["allowed_auth_scope"].append("login")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("allowed_auth_scope must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_duplicate_synthetic_forbidden_account_actions_blocks(tmp_path):
    def mutate(metadata):
        metadata["synthetic_qa_user"]["forbidden_account_actions"].append("payment")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("forbidden_account_actions must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_duplicate_cleanup_requires_separate_approval_blocks(tmp_path):
    def mutate(metadata):
        metadata["cleanup_rollback"]["requires_separate_approval"].append("C5_uninstall_reinstall")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("requires_separate_approval must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_duplicate_cleanup_authorized_zone_scope_blocks(tmp_path):
    def mutate(metadata):
        metadata["cleanup_rollback"]["authorized_zone_scopes"].append(
            "force_stop_relaunch_with_auth_state_preserved"
        )

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("authorized_zone_scopes must not contain duplicates" in reason for reason in report["blocked_reasons"])


def test_missing_cleanup_requires_separate_approval_blocks(tmp_path):
    def mutate(metadata):
        del metadata["cleanup_rollback"]["requires_separate_approval"]

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("requires_separate_approval" in reason for reason in report["blocked_reasons"])


def test_empty_cleanup_requires_separate_approval_blocks(tmp_path):
    def mutate(metadata):
        metadata["cleanup_rollback"]["requires_separate_approval"] = []

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("requires_separate_approval" in reason for reason in report["blocked_reasons"])


def test_unknown_cleanup_authorized_zone_scope_blocks(tmp_path):
    def mutate(metadata):
        metadata["cleanup_rollback"]["authorized_zone_scopes"].append("wipe_device")

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("authorized_zone_scopes" in reason and "wipe_device" in reason for reason in report["blocked_reasons"])


def test_unknown_cleanup_clean_state_scope_blocks(tmp_path):
    def mutate(metadata):
        metadata["cleanup_rollback"]["clean_state_scope"] = "factory_reset"

    report = _report_for(tmp_path, mutate)

    assert report["approval_decision"] == "blocked"
    assert any("clean_state_scope" in reason for reason in report["blocked_reasons"])


def test_missing_metadata_path_blocks(tmp_path):
    report = build_report(tmp_path / "missing.json")

    assert report["approval_decision"] == "blocked"
    assert any("not found" in reason for reason in report["blocked_reasons"])


def test_malformed_metadata_blocks(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")

    report = build_report(path)

    assert report["approval_decision"] == "blocked"
    assert any("not valid JSON" in reason for reason in report["blocked_reasons"])


def test_non_object_metadata_blocks(tmp_path):
    path = tmp_path / "list.json"
    path.write_text(json.dumps(["not", "object"]), encoding="utf-8")

    report = build_report(path)

    assert report["approval_decision"] == "blocked"
    assert any("must be a JSON object" in reason for reason in report["blocked_reasons"])


def test_cli_writes_structured_report(tmp_path):
    output_path = tmp_path / "approval_validation_report.json"

    exit_code = main(["--metadata", str(_write_metadata(tmp_path, _happy_metadata())), "--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["approval_decision"] == "approved_for_limited_runtime"
    assert report["runtime_execution_status"] == "not_run"

import json
import subprocess
from pathlib import Path

import pytest

from automation.device_inventory.generate_adb_device_inventory import (
    build_inventory,
    build_public_safe_review_inventory,
    build_report,
    main,
)


class FakeAdb:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, argv, capture_output, text, timeout, check):
        self.calls.append(argv)
        key = tuple(argv)
        stdout = self.responses.get(key, "")
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")


def _responses(serial="ABC123", manufacturer="TCL", model="TV Pro", release="11", sdk="30", features=None):
    if features is None:
        features = ["feature:android.software.leanback", "feature:com.google.android.feature.GOOGLE_BUILD"]
    features_output = "\n".join(features)
    return {
        ("adb", "devices", "-l"): f"List of devices attached\n{serial} device product:x model:{model} device:x transport_id:1\n",
        ("adb", "-s", serial, "shell", "getprop", "ro.product.manufacturer"): manufacturer,
        ("adb", "-s", serial, "shell", "getprop", "ro.product.model"): model,
        ("adb", "-s", serial, "shell", "getprop", "ro.build.version.release"): release,
        ("adb", "-s", serial, "shell", "getprop", "ro.build.version.sdk"): sdk,
        ("adb", "-s", serial, "shell", "getprop", "ro.build.version.security_patch"): "2026-01-01",
        ("adb", "-s", serial, "shell", "wm", "size"): "Physical size: 3840x2160",
        ("adb", "-s", serial, "shell", "wm", "density"): "Physical density: 320",
        ("adb", "-s", serial, "shell", "pm", "list", "features"): features_output,
    }


def test_without_allow_adb_makes_no_adb_calls_and_blocks():
    fake = FakeAdb({})

    report, raw_payload, alias_map, public_payload = build_report(allow_adb=False, runner=fake)

    assert fake.calls == []
    assert report["overall_status"] == "blocked"
    assert report["runtime_execution_status"] == "not_run"
    assert report["apk_install_status"] == "not_run"
    assert report["app_launch_status"] == "not_run"
    assert raw_payload["devices"] == []
    assert alias_map == {}
    assert public_payload["devices"] == []


def test_missing_adb_binary_blocks_without_crash():
    def missing_adb(*_args, **_kwargs):
        raise FileNotFoundError("adb was not found")

    report, raw_payload, alias_map, public_payload = build_report(allow_adb=True, runner=missing_adb)

    assert report["overall_status"] == "blocked"
    assert any("adb devices -l failed" in reason for reason in report["blocked_reasons"])
    assert raw_payload["devices"] == []
    assert alias_map == {}
    assert public_payload["devices"] == []


def test_allow_adb_output_paths_must_stay_under_qa_local(tmp_path):
    fake = FakeAdb({})
    report = build_inventory(
        allow_adb=True,
        raw_output=Path(".qa_local/devices/raw_adb_devices.json"),
        alias_map_path=Path(".qa_local/devices/serial_alias_map.json"),
        public_output=tmp_path / "public.json",
        report_path=Path(".qa_local/devices/preflight_report.json"),
        write_files=False,
        runner=fake,
    )

    assert report["overall_status"] == "blocked"
    assert fake.calls == []
    assert any("--public-output must stay under .qa_local/devices/" in reason for reason in report["blocked_reasons"])


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"raw_output": Path("docs/raw_adb_devices.json")}, "--raw-output"),
        ({"alias_map_path": Path("docs/serial_alias_map.json")}, "--alias-map"),
        ({"public_output": Path("docs/approvals/device_inventory.generated.json")}, "--public-output"),
        ({"report_path": Path("docs/preflight_report.json")}, "--report"),
        ({"raw_output": Path(".qa_local/devices/192.168.0.1/raw.json")}, "--raw-output"),
    ],
)
def test_output_path_errors_block_before_adb_call(kwargs, expected):
    fake = FakeAdb(_responses(serial="ABC123"))
    defaults = {
        "raw_output": Path(".qa_local/devices/raw_adb_devices.json"),
        "alias_map_path": Path(".qa_local/devices/serial_alias_map.json"),
        "public_output": Path(".qa_local/devices/device_inventory.public_safe.generated.json"),
        "report_path": Path(".qa_local/devices/preflight_report.json"),
    }
    defaults.update(kwargs)

    report = build_inventory(allow_adb=True, write_files=False, runner=fake, **defaults)

    assert report["overall_status"] == "blocked"
    assert fake.calls == []
    assert any(expected in reason for reason in report["blocked_reasons"])


def test_default_cli_with_unsafe_output_path_blocks_before_adb_call():
    fake = FakeAdb({})

    report = build_inventory(
        allow_adb=False,
        raw_output=Path("docs/raw_adb_devices.json"),
        alias_map_path=Path(".qa_local/devices/serial_alias_map.json"),
        public_output=Path(".qa_local/devices/device_inventory.public_safe.generated.json"),
        report_path=Path(".qa_local/devices/preflight_report.json"),
        write_files=False,
        runner=fake,
    )

    assert report["overall_status"] == "blocked"
    assert fake.calls == []


def test_usb_serial_remains_local_only():
    fake = FakeAdb(_responses(serial="ABC123"))

    report, raw_payload, alias_map, public_payload = build_report(allow_adb=True, runner=fake)

    assert report["overall_status"] == "not_run"
    assert raw_payload["devices"][0]["serial"] == "ABC123"
    assert "ABC123" in alias_map
    assert "ABC123" not in json.dumps(public_payload)
    assert public_payload["devices"][0]["device_alias"].startswith("tv-tcl-")


def test_allow_adb_uses_only_inventory_command_allowlist():
    fake = FakeAdb(_responses(serial="ABC123"))

    build_report(allow_adb=True, runner=fake)

    assert fake.calls == [
        ["adb", "devices", "-l"],
        ["adb", "-s", "ABC123", "shell", "getprop", "ro.product.manufacturer"],
        ["adb", "-s", "ABC123", "shell", "getprop", "ro.product.model"],
        ["adb", "-s", "ABC123", "shell", "getprop", "ro.build.version.release"],
        ["adb", "-s", "ABC123", "shell", "getprop", "ro.build.version.sdk"],
        ["adb", "-s", "ABC123", "shell", "getprop", "ro.build.version.security_patch"],
        ["adb", "-s", "ABC123", "shell", "wm", "size"],
        ["adb", "-s", "ABC123", "shell", "wm", "density"],
        ["adb", "-s", "ABC123", "shell", "pm", "list", "features"],
    ]


def test_network_serial_ip_remains_local_only():
    serial = "192.168.1.44:5555"
    fake = FakeAdb(_responses(serial=serial, manufacturer="Xiaomi", model="Mi Box", release="12", sdk="31"))

    _report, raw_payload, alias_map, public_payload = build_report(allow_adb=True, runner=fake)

    assert raw_payload["devices"][0]["serial"] == serial
    assert serial in alias_map
    assert "192.168.1.44" not in json.dumps(public_payload)
    assert public_payload["redaction_guarantees"]["ip_excluded"] is True


def test_leanback_features_classify_tv():
    fake = FakeAdb(_responses(features=["feature:android.software.leanback"]))

    _report, _raw, _alias_map, public_payload = build_report(allow_adb=True, runner=fake)

    device = public_payload["devices"][0]
    assert device["category"] == "android_tv"
    assert device["form_factor"] == "tv"
    assert device["input_method"] == "dpad_remote"
    assert device["classification_confidence"] == "heuristic"
    assert device["manual_review_required"] is True


def test_touchscreen_only_classifies_phone_secondary():
    fake = FakeAdb(
        _responses(
            manufacturer="Samsung",
            model="Galaxy",
            release="14",
            sdk="34",
            features=["feature:android.hardware.touchscreen"],
        )
    )

    _report, _raw, _alias_map, public_payload = build_report(allow_adb=True, runner=fake)

    device = public_payload["devices"][0]
    assert device["category"] == "android_phone_secondary"
    assert device["device_alias"] == "phone-samsung-001"
    assert device["runtime_profile_alias"] == "phone-samsung-a14-001"
    assert device["priority"] == "P2"
    assert device["input_method"] == "touch"


def test_aosp_unknown_requires_manual_review():
    fake = FakeAdb(_responses(manufacturer="AOSP", model="Generic", release="10", sdk="29", features=[]))

    _report, _raw, _alias_map, public_payload = build_report(allow_adb=True, runner=fake)

    device = public_payload["devices"][0]
    assert device["category"] == "aosp_stb"
    assert device["manual_review_required"] is True
    assert device["google_play_services"] == "unknown"


def test_public_sanitizer_blocks_identifier_like_values(tmp_path):
    serial = "ABC123"
    alias_map = tmp_path / "serial_alias_map.json"
    alias_map.write_text(
        json.dumps({"ABC123": {"device_alias": "tv-192.168.1.5-001", "index": "001"}}),
        encoding="utf-8",
    )
    fake = FakeAdb(_responses(serial=serial, manufacturer="TCL", model="TV"))

    report, _raw, _alias_map, public_payload = build_report(allow_adb=True, alias_map_path=alias_map, runner=fake)

    assert report["overall_status"] == "blocked"
    assert any("sanitizer" in reason for reason in report["blocked_reasons"])
    assert public_payload["devices"] == []


@pytest.mark.parametrize(
    "unsafe_alias",
    [
        "tv-serial-001",
        "tv-phone-001",
        "tv-otp-001",
        "tv-androidid-001",
        "tv-google-account-001",
    ],
)
def test_existing_alias_map_reserved_tokens_block_public_inventory(tmp_path, unsafe_alias):
    alias_map = tmp_path / "serial_alias_map.json"
    alias_map.write_text(
        json.dumps({"ABC123": {"device_alias": unsafe_alias, "index": "001"}}),
        encoding="utf-8",
    )
    fake = FakeAdb(_responses(serial="ABC123", manufacturer="TCL", model="TV"))

    report, _raw, alias_map_payload, public_payload = build_report(allow_adb=True, alias_map_path=alias_map, runner=fake)

    assert alias_map_payload["ABC123"]["device_alias"] == unsafe_alias
    assert report["overall_status"] == "blocked"
    assert any("unsafe alias-map values" in reason for reason in report["blocked_reasons"])
    assert public_payload["devices"] == []


def test_existing_alias_map_phone_prefix_passes_for_phone_form_factor(tmp_path):
    alias_map = tmp_path / "serial_alias_map.json"
    alias_map.write_text(
        json.dumps({"ABC123": {"device_alias": "phone-samsung-001", "index": "001"}}),
        encoding="utf-8",
    )
    fake = FakeAdb(
        _responses(
            serial="ABC123",
            manufacturer="Samsung",
            model="Galaxy",
            release="14",
            sdk="34",
            features=["feature:android.hardware.touchscreen"],
        )
    )

    report, _raw, alias_map_payload, public_payload = build_report(allow_adb=True, alias_map_path=alias_map, runner=fake)

    assert report["overall_status"] == "not_run"
    assert alias_map_payload["ABC123"]["device_alias"] == "phone-samsung-001"
    assert public_payload["devices"][0]["device_alias"] == "phone-samsung-001"
    assert public_payload["devices"][0]["runtime_profile_alias"] == "phone-samsung-a14-001"


def test_existing_alias_map_runtime_profile_must_match_alias_index(tmp_path):
    alias_map = tmp_path / "serial_alias_map.json"
    alias_map.write_text(
        json.dumps({"ABC123": {"device_alias": "tv-tcl-002", "index": "001"}}),
        encoding="utf-8",
    )
    fake = FakeAdb(_responses(serial="ABC123", manufacturer="TCL", model="TV", release="11", sdk="30"))

    report, _raw, _alias_map_payload, public_payload = build_report(allow_adb=True, alias_map_path=alias_map, runner=fake)

    assert report["overall_status"] == "blocked"
    assert any("unsafe alias-map values" in reason for reason in report["blocked_reasons"])
    assert public_payload["devices"] == []


def test_existing_alias_map_safe_alias_passes_public_inventory(tmp_path):
    alias_map = tmp_path / "serial_alias_map.json"
    alias_map.write_text(
        json.dumps({"ABC123": {"device_alias": "tv-tcl-001", "index": "001"}}),
        encoding="utf-8",
    )
    fake = FakeAdb(_responses(serial="ABC123", manufacturer="TCL", model="TV", release="11", sdk="30"))

    report, _raw, alias_map_payload, public_payload = build_report(allow_adb=True, alias_map_path=alias_map, runner=fake)

    assert report["overall_status"] == "not_run"
    assert alias_map_payload["ABC123"]["device_alias"] == "tv-tcl-001"
    assert public_payload["devices"][0]["device_alias"] == "tv-tcl-001"
    assert public_payload["devices"][0]["runtime_profile_alias"] == "tv-tcl-a11-001"


def test_owner_and_location_labels_are_excluded_from_public_inventory():
    fake = FakeAdb(
        _responses(
            serial="ABC123",
            manufacturer="Oleg",
            model="Livingroom Private TV",
            release="11",
            sdk="30",
        )
    )

    report, raw_payload, _alias_map, public_payload = build_report(allow_adb=True, runner=fake)

    public_text = json.dumps(public_payload).lower()
    assert report["overall_status"] == "not_run"
    assert raw_payload["collected_device_details"][0]["manufacturer"] == "Oleg"
    assert "oleg" not in public_text
    assert "livingroom" not in public_text
    assert "private" not in public_text
    assert "manufacturer" not in public_text
    assert "model" not in public_text


def test_split_location_labels_are_removed_from_aliases():
    fake = FakeAdb(
        _responses(
            serial="ABC123",
            manufacturer="Living Room",
            model="TV",
            release="11",
            sdk="30",
        )
    )

    _report, _raw_payload, _alias_map, public_payload = build_report(allow_adb=True, runner=fake)

    public_text = json.dumps(public_payload).lower()
    device = public_payload["devices"][0]
    assert device["device_alias"] == "tv-aosp-001"
    assert device["runtime_profile_alias"] == "tv-aosp-a11-001"
    assert "living" not in public_text
    assert "room" not in public_text


def test_aliases_match_grammar():
    fake = FakeAdb(_responses(manufacturer="TCL", model="TV", release="11", sdk="30"))

    _report, _raw, _alias_map, public_payload = build_report(allow_adb=True, runner=fake)

    device = public_payload["devices"][0]
    assert device["device_alias"] == "tv-tcl-001"
    assert device["runtime_profile_alias"] == "tv-tcl-a11-001"


def test_android_update_preserves_device_alias_and_changes_runtime_profile(tmp_path):
    alias_map = tmp_path / "serial_alias_map.json"
    alias_map.write_text(json.dumps({"ABC123": {"device_alias": "stb-xiaomi-001", "index": "001"}}), encoding="utf-8")
    fake = FakeAdb(
        _responses(
            manufacturer="Xiaomi",
            model="Mi Box",
            release="13",
            sdk="33",
            features=["feature:android.hardware.hdmi.cec"],
        )
    )

    _report, _raw, alias_map_payload, public_payload = build_report(
        allow_adb=True,
        alias_map_path=alias_map,
        runner=fake,
    )

    device = public_payload["devices"][0]
    assert alias_map_payload["ABC123"]["device_alias"] == "stb-xiaomi-001"
    assert device["device_alias"] == "stb-xiaomi-001"
    assert device["runtime_profile_alias"] == "stb-xiaomi-a13-001"


def test_cli_writes_local_outputs_and_not_run_statuses(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw_output = Path(".qa_local/devices/raw_adb_devices.json")
    alias_map = Path(".qa_local/devices/serial_alias_map.json")
    public_output = Path(".qa_local/devices/device_inventory.public_safe.generated.json")
    report_output = Path(".qa_local/devices/preflight_report.json")

    exit_code = main(
        [
            "--raw-output",
            str(raw_output),
            "--alias-map",
            str(alias_map),
            "--public-output",
            str(public_output),
            "--report",
            str(report_output),
        ]
    )

    assert exit_code == 0
    report = json.loads(report_output.read_text(encoding="utf-8"))
    public_payload = json.loads(public_output.read_text(encoding="utf-8"))
    assert report["runtime_execution_status"] == "not_run"
    assert report["apk_install_status"] == "not_run"
    assert report["app_launch_status"] == "not_run"
    assert public_payload["runtime_execution_status"] == "not_run"
    assert public_payload["apk_install_status"] == "not_run"
    assert public_payload["app_launch_status"] == "not_run"


def _public_safe_inventory_payload():
    fake = FakeAdb(_responses(serial="ABC123", manufacturer="TCL", model="TV", release="11", sdk="30"))
    _report, _raw, _alias_map, public_payload = build_report(allow_adb=True, runner=fake)
    public_payload["redaction_status"] = "redacted"
    public_payload["public_safety_findings"] = []
    public_payload["public_device_count"] = len(public_payload["devices"])
    return public_payload


def test_owner_review_export_preserves_heuristic_manual_review_and_not_run_statuses():
    review_payload = build_public_safe_review_inventory(_public_safe_inventory_payload())

    assert review_payload["owner_review_boundary"] == "not approved for TASK-005 until owner/QA manual review"
    assert review_payload["runtime_execution_status"] == "not_run"
    assert review_payload["apk_install_status"] == "not_run"
    assert review_payload["app_launch_status"] == "not_run"
    assert review_payload["public_device_count"] == 1
    device = review_payload["devices"][0]
    assert device["classification_confidence"] == "heuristic"
    assert device["manual_review_required"] is True
    assert device["runtime_execution_status"] == "not_run"
    assert device["apk_install_status"] == "not_run"
    assert device["app_launch_status"] == "not_run"
    assert "ABC123" not in json.dumps(review_payload)
    assert ".qa_local" not in json.dumps(review_payload)


def test_owner_review_export_blocks_public_safety_findings():
    payload = _public_safe_inventory_payload()
    payload["public_safety_findings"] = ["Forbidden public identifier-like value at $.devices[0].device_alias."]

    with pytest.raises(ValueError, match="public_safety_findings"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_raw_source_metadata():
    payload = _public_safe_inventory_payload()
    payload["source"] = "raw_adb_inventory"

    with pytest.raises(ValueError, match="source"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_not_redacted_devices():
    payload = _public_safe_inventory_payload()
    payload["redaction_status"] = "not_redacted"

    with pytest.raises(ValueError, match="redaction_status"):
        build_public_safe_review_inventory(payload)


@pytest.mark.parametrize("generated_at", ["2099", "not-a-timestamp"])
def test_owner_review_export_blocks_invalid_generated_at_utc(generated_at):
    payload = _public_safe_inventory_payload()
    payload["generated_at_utc"] = generated_at

    with pytest.raises(ValueError, match="generated_at_utc"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_missing_public_device_count():
    payload = _public_safe_inventory_payload()
    del payload["public_device_count"]

    with pytest.raises(ValueError, match="public_device_count"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_empty_devices():
    payload = _public_safe_inventory_payload()
    payload["devices"] = []
    payload["public_device_count"] = 0
    payload["redaction_status"] = "not_applicable"

    with pytest.raises(ValueError, match="non-empty"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_missing_redaction_guarantees():
    payload = _public_safe_inventory_payload()
    payload["redaction_guarantees"] = {}

    with pytest.raises(ValueError, match="redaction_guarantees"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_missing_required_redaction_key():
    payload = _public_safe_inventory_payload()
    del payload["redaction_guarantees"]["ip_excluded"]

    with pytest.raises(ValueError, match="ip_excluded"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_runtime_status_drift():
    payload = _public_safe_inventory_payload()
    payload["devices"][0]["runtime_execution_status"] = "pass"

    with pytest.raises(ValueError, match="runtime_execution_status"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_does_not_allow_auto_manual_confirmed_promotion():
    payload = _public_safe_inventory_payload()
    payload["devices"][0]["classification_confidence"] = "manual_confirmed"
    payload["devices"][0]["manual_review_required"] = False

    with pytest.raises(ValueError, match="classification_confidence"):
        build_public_safe_review_inventory(payload)


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("device_alias", "bad alias", "device_alias"),
        ("runtime_profile_alias", "bad runtime", "runtime_profile_alias"),
    ],
)
def test_owner_review_export_blocks_malformed_aliases(field, value, match):
    payload = _public_safe_inventory_payload()
    payload["devices"][0][field] = value

    with pytest.raises(ValueError, match=match):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_stable_alias_with_android_version_token():
    payload = _public_safe_inventory_payload()
    payload["devices"][0]["device_alias"] = "tv-tcl-a11-001"
    payload["devices"][0]["runtime_profile_alias"] = "tv-tcl-a11-a11-001"
    payload["devices"][0]["android_major"] = 11
    payload["devices"][0]["api_level"] = 30

    with pytest.raises(ValueError, match="device_alias"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_duplicate_device_aliases():
    payload = _public_safe_inventory_payload()
    duplicate = dict(payload["devices"][0])
    duplicate["runtime_profile_alias"] = "tv-tcl-a11-002"
    payload["devices"].append(duplicate)

    with pytest.raises(ValueError, match="duplicate device_alias"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_public_device_count_mismatch():
    payload = _public_safe_inventory_payload()
    payload["public_device_count"] = 99

    with pytest.raises(ValueError, match="public_device_count"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_unknown_public_device_fields():
    payload = _public_safe_inventory_payload()
    payload["devices"][0]["owner_label"] = "review"

    with pytest.raises(ValueError, match="unsupported public fields"):
        build_public_safe_review_inventory(payload)


def test_owner_review_export_blocks_unknown_top_level_public_fields():
    payload = _public_safe_inventory_payload()
    payload["owner_label"] = "review"

    with pytest.raises(ValueError, match="unsupported top-level fields"):
        build_public_safe_review_inventory(payload)


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("category", "smart_fridge", "category"),
        ("priority", "P9", "priority"),
        ("form_factor", "watch", "form_factor"),
        ("input_method", "voice", "input_method"),
        ("adb_available", "maybe", "adb_available"),
        ("google_play_services", "maybe", "google_play_services"),
        ("screen_class", "home_livingroom", "screen_class"),
    ],
)
def test_owner_review_export_blocks_malformed_public_enums(field, value, match):
    payload = _public_safe_inventory_payload()
    payload["devices"][0][field] = value

    with pytest.raises(ValueError, match=match):
        build_public_safe_review_inventory(payload)

import json
import subprocess
from pathlib import Path

import pytest

from automation.device_inventory.generate_adb_device_inventory import build_inventory, build_report, main


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

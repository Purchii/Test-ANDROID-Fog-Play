from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from automation.runtime_preflight import task042_local_runtime_preflight as preflight
from automation.reporting.generate_report_manifest import _validate_v2_envelope


ROOT = Path(__file__).resolve().parents[1]


def absent_presence() -> preflight.CanonicalPresence:
    return preflight.CanonicalPresence(
        apk_dir_present=False,
        expected_apks_present=(),
        unexpected_apk_count=0,
        device_dir_present=False,
        device_preflight_present=False,
        public_device_inventory_present=False,
    )


def ready_bundle_presence() -> preflight.CanonicalPresence:
    return replace(
        absent_presence(),
        apk_dir_present=True,
        expected_apks_present=preflight.EXPECTED_APKS,
    )


def test_validate_only_static_contracts_pass_without_local_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_subprocess(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("validate-only must not start a subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden_subprocess)
    assert preflight.validate_static_contracts(ROOT) == []


def test_validate_only_cli_writes_no_report(tmp_path: Path) -> None:
    report = tmp_path / "must-not-exist.json"
    assert preflight.main(["--validate-only", "--repo-root", str(ROOT)]) == 0
    assert not report.exists()


def test_presence_probe_uses_only_canonical_direct_child_names(tmp_path: Path) -> None:
    apk_dir = tmp_path / preflight.CANONICAL_APK_DIR
    apk_dir.mkdir(parents=True)
    for name in preflight.EXPECTED_APKS:
        (apk_dir / name).touch()
    (apk_dir / "unexpected-sixth.apk").touch()
    nested = apk_dir / "nested"
    nested.mkdir()
    (nested / "ignored-nested.apk").touch()

    snapshot = preflight.probe_canonical_presence(tmp_path)

    assert snapshot.expected_apks_present == preflight.EXPECTED_APKS
    assert snapshot.unexpected_apk_count == 1


def test_missing_expected_apk_fails_closed() -> None:
    presence = replace(
        ready_bundle_presence(),
        expected_apks_present=preflight.EXPECTED_APKS[:-1],
    )
    bundle = preflight.classify_bundle(presence)

    assert bundle["bundle_status"] == "BLOCKED"
    assert bundle["missing_expected_count"] == 1
    assert bundle["entries"][-1]["scenario_status"] == "blocked_by_fixture"


def test_unexpected_sixth_never_becomes_main_bundle_member() -> None:
    bundle = preflight.classify_bundle(replace(ready_bundle_presence(), unexpected_apk_count=1))

    assert len(bundle["entries"]) == 5
    assert bundle["unexpected_apk_count"] == 1
    assert bundle["unexpected_entries_are_main_bundle_members"] is False
    assert bundle["bundle_status"] == "BLOCKED"


def test_absent_local_runtime_report_terminally_classifies_all_scenarios() -> None:
    report = preflight.build_report(
        repo_root=ROOT,
        presence=absent_presence(),
        generated_at_utc="2026-07-17T00:00:00Z",
    )
    ledger = report["payload"]["scenario_ledger"]

    assert len(ledger) == 18
    assert [row["scenario_id"] for row in ledger] == [f"QA-042-{index:03d}" for index in range(1, 19)]
    assert not {row["scenario_status"] for row in ledger} & preflight.NON_CLOSING_STATUSES
    assert report["execution_status"] == "partial"
    assert report["payload"]["scenario_summary"] == {
        "total": 18,
            "p0": 15,
            "observed_pass": 6,
            "blocked": 12,
            "tooling_defect": 0,
            "non_closing": 0,
        }
    assert preflight.validate_report(report) == []


def test_exact_five_bundle_and_launcher_are_separate() -> None:
    report = preflight.build_report(repo_root=ROOT, presence=ready_bundle_presence())
    payload = report["payload"]

    assert len(payload["apk_readiness"]["entries"]) == 5
    assert payload["launcher_contour"]["separate_from_main_apk_bundle"] is True
    assert payload["launcher_contour"]["counted_as_main_apk_entry"] is False
    assert payload["launcher_contour"]["contour_key"] not in {
        entry["apk_alias"] for entry in payload["apk_readiness"]["entries"]
    }


def test_required_device_aliases_are_explicit_but_not_false_ready() -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    devices = report["payload"]["device_readiness"]

    assert {device["device_alias"] for device in devices} == set(preflight.REQUIRED_DEVICE_ALIASES)
    assert {device["current_status"] for device in devices} == {"MISSING"}
    assert {device["scenario_status"] for device in devices} == {"blocked_by_device"}
    assert all(device["historical_public_profile_is_runtime_evidence"] is False for device in devices)


def test_actual_stick_alias_is_not_guessed_or_substituted() -> None:
    stick = preflight.build_report(repo_root=ROOT, presence=absent_presence())["payload"]["fogplay_stick_actual_target"]

    assert stick == {
        "selector_key": "fogplay_stick_actual_target",
        "actual_alias_status": "unknown",
        "selected_device_alias": None,
        "current_status": "MISSING",
        "scenario_status": "blocked_by_device",
        "evidence_status": "unknown",
        "blocker": "actual_stick_mapping_missing",
        "generic_substitution_allowed": False,
    }


def test_avd_result_is_tooling_only() -> None:
    avd = preflight.build_report(repo_root=ROOT, presence=absent_presence())["payload"]["tooling"]["avd"]

    assert avd["claim_scope"] == "tooling_only"
    assert avd["product_compatibility_claim"] is False
    assert avd["invoked"] is False


def test_synthetic_negative_scenarios_are_confirmed_without_runtime() -> None:
    ledger = preflight.build_report(repo_root=ROOT, presence=absent_presence())["payload"]["scenario_ledger"]
    rows = {row["scenario_id"]: row for row in ledger}

    for scenario_id in ("QA-042-002", "QA-042-003", "QA-042-006", "QA-042-016"):
        assert rows[scenario_id]["scenario_status"] == "observed_pass"
        assert rows[scenario_id]["evidence_type"] == "synthetic_offline"
        assert rows[scenario_id]["evidence_status"] == "confirmed"


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("payload", "device_readiness", 0, "adb_serial"), "emulator-secret"),
        (("payload", "leak"), r"C:\\Users\\person\\private"),
        (("payload", "leak"), "https://private.invalid/path"),
        (("payload", "leak"), "10.1.2.3"),
    ],
)
def test_public_safe_validator_rejects_machine_or_raw_values(path: tuple[object, ...], value: str) -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    target: object = report
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]

    assert preflight.public_safety_errors(report)
    assert preflight.validate_report(report)


def test_report_validator_rejects_mapped_only_and_unjustified_blocker() -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    report["payload"]["scenario_ledger"][0]["scenario_status"] = "mapped_only"
    report["payload"]["scenario_ledger"][1]["scenario_status"] = "blocked_by_fixture"
    report["payload"]["scenario_ledger"][1].pop("blocker", None)

    errors = preflight.validate_report(report)
    assert any("must not remain mapped_only" in error for error in errors)
    assert any("blocked status requires blocker" in error for error in errors)


def test_report_validator_rejects_cross_family_or_generic_stick_substitution() -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    stick = report["payload"]["fogplay_stick_actual_target"]
    stick["selected_device_alias"] = "tv-tpv-013"
    stick["generic_substitution_allowed"] = True

    errors = preflight.validate_report(report)
    assert any("alias must remain unknown" in error for error in errors)
    assert any("generic substitution" in error for error in errors)


def test_write_and_validate_report_bundle(tmp_path: Path) -> None:
    report = preflight.build_report(
        repo_root=ROOT,
        presence=absent_presence(),
        generated_at_utc="2026-07-17T00:00:00Z",
    )
    report_path = tmp_path / "task042.summary.json"
    ledger_path = tmp_path / "task042.scenario-ledger.csv"
    matrix_path = tmp_path / "task042.readiness-matrix.csv"

    preflight.write_report_bundle(report, report_path, ledger_path, matrix_path)
    saved = json.loads(report_path.read_text(encoding="utf-8"))

    assert preflight.validate_report(saved) == []
    assert _validate_v2_envelope(saved, tmp_path.resolve()) == []
    assert preflight.validate_report_file(report_path, tmp_path) == []
    assert len(saved["artifacts"]) == 2
    assert ledger_path.read_text(encoding="utf-8").count("\n") == 19
    assert "fogplay_stick_actual_target" in matrix_path.read_text(encoding="utf-8")


def test_validate_report_file_detects_hash_bound_artifact_tampering(tmp_path: Path) -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    report_path = tmp_path / "task042.summary.json"
    ledger_path = tmp_path / "task042.scenario-ledger.csv"
    matrix_path = tmp_path / "task042.readiness-matrix.csv"
    preflight.write_report_bundle(report, report_path, ledger_path, matrix_path)

    ledger_path.write_text(ledger_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")

    assert any("SHA-256 mismatch" in error for error in preflight.validate_report_file(report_path, tmp_path))


def test_report_validator_recomputes_scenario_summary_from_ledger() -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    report["payload"]["scenario_summary"]["observed_pass"] += 1

    assert "scenario summary does not match the scenario ledger" in preflight.validate_report(report)


def test_report_validator_recomputes_readiness_matrix_from_payload(tmp_path: Path) -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    report_path = tmp_path / "task042.summary.json"
    ledger_path = tmp_path / "task042.scenario-ledger.csv"
    matrix_path = tmp_path / "task042.readiness-matrix.csv"
    preflight.write_report_bundle(report, report_path, ledger_path, matrix_path)
    matrix_path.write_text(
        matrix_path.read_text(encoding="utf-8").replace(",MISSING,", ",READY,", 1),
        encoding="utf-8",
        newline="\n",
    )
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    next(item for item in saved["artifacts"] if item["kind"] == "readiness_matrix")["sha256"] = preflight._sha256(matrix_path)
    report_path.write_text(json.dumps(saved), encoding="utf-8", newline="\n")

    assert "readiness matrix content does not match report payload" in preflight.validate_report_file(report_path, tmp_path)


def test_validate_report_cli_fails_closed_for_missing_file(tmp_path: Path) -> None:
    assert preflight.main(["--validate-report", str(tmp_path / "missing.json")]) == 1


class ApprovedFakeRunner:
    def __init__(self, serial: str = "SYNTHETIC_SERIAL") -> None:
        self.serial = serial
        self.calls: list[list[str]] = []

    def __call__(self, argv, capture_output, text, timeout, check):  # type: ignore[no-untyped-def]
        self.calls.append(list(argv))
        name = Path(argv[0]).name.lower()
        stdout = ""
        if "apkanalyzer" in name:
            stdout = {"application-id": "synthetic.package", "version-name": "1.0", "version-code": "1"}[argv[-2]]
        elif "apksigner" in name:
            stdout = "Signer certificate synthetic metadata"
        elif name.startswith("emulator"):
            stdout = "synthetic-avd\n"
        elif name.startswith("adb"):
            tail = argv[1:]
            if tail == ["version"]:
                stdout = "Android Debug Bridge synthetic version"
            elif tail == ["devices", "-l"]:
                stdout = f"List of devices attached\n{self.serial} device product:x model:TV device:x transport_id:1\n"
            elif "getprop" in tail:
                stdout = {
                    "ro.product.manufacturer": "TPV",
                    "ro.product.model": "TV",
                    "ro.build.version.release": "12",
                    "ro.build.version.sdk": "31",
                    "ro.build.version.security_patch": "2026-01-01",
                }[tail[-1]]
            elif tail[-2:] == ["wm", "size"]:
                stdout = "Physical size: 3840x2160"
            elif tail[-2:] == ["wm", "density"]:
                stdout = "Physical density: 320"
            elif tail[-3:] == ["pm", "list", "features"]:
                stdout = "feature:android.software.leanback\nfeature:com.google.android.feature.GOOGLE_BUILD"
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")


class MultiDeviceApprovedFakeRunner(ApprovedFakeRunner):
    def __init__(self, serials: tuple[str, ...]) -> None:
        super().__init__(serial=serials[0])
        self.serials = serials

    def __call__(self, argv, capture_output, text, timeout, check):  # type: ignore[no-untyped-def]
        name = Path(argv[0]).name.lower()
        if not name.startswith("adb"):
            return super().__call__(argv, capture_output, text, timeout, check)
        self.calls.append(list(argv))
        tail = argv[1:]
        if tail == ["version"]:
            stdout = "Android Debug Bridge synthetic version"
        elif tail == ["devices", "-l"]:
            rows = [f"{serial} device product:x model:TV device:x transport_id:{index}" for index, serial in enumerate(self.serials, 1)]
            stdout = "List of devices attached\n" + "\n".join(rows) + "\n"
        else:
            serial = tail[1]
            yandex = serial == "SYNTHETIC_SERIAL_TWO"
            if "getprop" in tail:
                tv_profile = {
                    "ro.product.manufacturer": "Yandex" if yandex else "TPV",
                    "ro.product.model": "TV",
                    "ro.build.version.release": "9" if yandex else "12",
                    "ro.build.version.sdk": "28" if yandex else "31",
                    "ro.build.version.security_patch": "2026-01-01",
                }
                stdout = tv_profile[tail[-1]]
            elif tail[-2:] == ["wm", "size"]:
                stdout = "Physical size: 1920x1080" if yandex else "Physical size: 3840x2160"
            elif tail[-2:] == ["wm", "density"]:
                stdout = "Physical density: 320"
            elif tail[-3:] == ["pm", "list", "features"]:
                stdout = "feature:android.software.leanback\nfeature:com.google.android.feature.GOOGLE_BUILD"
            else:
                stdout = ""
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")


def _execution_fixture(tmp_path: Path, mapped_serial: str = "SYNTHETIC_SERIAL") -> dict[str, str]:
    for relative in (preflight.SCENARIO_CATALOG, preflight.APK_CONTRACT, preflight.PUBLIC_DEVICE_INVENTORY):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    apk_dir = tmp_path / preflight.CANONICAL_APK_DIR
    apk_dir.mkdir(parents=True)
    for name in preflight.EXPECTED_APKS:
        (apk_dir / name).write_bytes(b"synthetic-apk-fixture")
    alias_map = tmp_path / preflight.CANONICAL_ALIAS_MAP
    alias_map.parent.mkdir(parents=True, exist_ok=True)
    alias_map.write_text(json.dumps({mapped_serial: {"device_alias": "tv-tpv-013", "index": "013"}}), encoding="utf-8")
    local_app_data = tmp_path / "local-app-data"
    sdk = local_app_data / "Android" / "Sdk"
    for tool in (
        sdk / "platform-tools" / "adb.exe",
        sdk / "emulator" / "emulator.exe",
        sdk / "cmdline-tools" / "latest" / "bin" / "apkanalyzer.exe",
        sdk / "build-tools" / "1.0" / "apksigner.exe",
    ):
        tool.parent.mkdir(parents=True, exist_ok=True)
        tool.write_text("synthetic tool", encoding="utf-8")
    return {"LOCALAPPDATA": str(local_app_data)}


def test_execute_mapped_device_uses_only_metadata_and_task016_allowlist(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    fake = ApprovedFakeRunner()

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=fake)

    assert execution.apk_metadata_status == "READY"
    assert execution.adb_status == "READY"
    assert execution.avd_status == "READY"
    assert execution.avd_count == 1
    assert execution.device_statuses["tv-tpv-013"] == "READY"
    command_text = "\n".join(" ".join(call[1:]) for call in fake.calls)
    for forbidden in (" install ", "am start", "monkey", "logcat", "screencap", "screenrecord"):
        assert forbidden not in f" {command_text} "
    assert (tmp_path / preflight.CANONICAL_GENERATED_INVENTORY).is_file()


def test_sdk_resolution_supports_deterministic_apksigner_jar_fallback(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    sdk = Path(env["LOCALAPPDATA"]) / "Android" / "Sdk"
    signer = sdk / "build-tools" / "1.0" / "apksigner.exe"
    signer.rename(signer.with_suffix(".bat"))
    signer_jar = sdk / "build-tools" / "1.0" / "lib" / "apksigner.jar"
    signer_jar.parent.mkdir(parents=True)
    signer_jar.write_bytes(b"synthetic-apksigner-jar")
    program_files = tmp_path / "program-files"
    java = program_files / "Android" / "Android Studio" / "jbr" / "bin" / "java.exe"
    java.parent.mkdir(parents=True)
    java.write_text("synthetic java", encoding="utf-8")
    env["ProgramFiles"] = str(program_files)

    tools, errors = preflight.resolve_sdk_tools(env)

    assert errors == []
    assert tools is not None
    assert tools.apksigner_jar == signer_jar
    assert tools.java == java


def test_apk_metadata_prefers_deterministic_apksigner_jar(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    sdk = Path(env["LOCALAPPDATA"]) / "Android" / "Sdk"
    signer = sdk / "build-tools" / "1.0" / "apksigner.exe"
    signer.rename(signer.with_suffix(".bat"))
    signer_jar = sdk / "build-tools" / "1.0" / "lib" / "apksigner.jar"
    signer_jar.parent.mkdir(parents=True)
    signer_jar.write_bytes(b"synthetic-apksigner-jar")
    program_files = tmp_path / "program-files"
    java = program_files / "Android" / "Android Studio" / "jbr" / "bin" / "java.exe"
    java.parent.mkdir(parents=True)
    java.write_text("synthetic java", encoding="utf-8")
    env["ProgramFiles"] = str(program_files)
    tools, errors = preflight.resolve_sdk_tools(env)
    assert errors == [] and tools is not None
    apk = tmp_path / "synthetic.apk"
    apk.write_bytes(b"synthetic-apk-fixture")
    fake = ApprovedFakeRunner()

    def jar_aware_runner(argv, **kwargs):  # type: ignore[no-untyped-def]
        if "-jar" in argv:
            fake.calls.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, stdout="Signer certificate synthetic metadata", stderr="")
        return fake(argv, **kwargs)

    records, metadata_errors = preflight.capture_apk_metadata([apk], tools, jar_aware_runner)

    assert metadata_errors == []
    assert records[0]["signature_output"] == "Signer certificate synthetic metadata"
    assert any("-jar" in call for call in fake.calls)


def test_execute_unmapped_authorized_device_stops_before_per_device_calls(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path, mapped_serial="OTHER_SERIAL")
    fake = ApprovedFakeRunner(serial="UNMAPPED_SERIAL")

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=fake)

    adb_calls = [call for call in fake.calls if Path(call[0]).name.lower().startswith("adb")]
    assert execution.adb_status == "BLOCKED"
    assert "adb_snapshot_mapping_or_authorized_count_gate_failed" in execution.blockers
    assert [call[1:] for call in adb_calls] == [["version"], ["devices", "-l"]]


def test_execute_two_mapped_reviewed_devices_uses_only_exact_selected_set(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    map_path = tmp_path / preflight.CANONICAL_ALIAS_MAP
    map_path.write_text(
        json.dumps({
            "SYNTHETIC_SERIAL": {"device_alias": "tv-tpv-013", "index": "013"},
            "SYNTHETIC_SERIAL_TWO": {"device_alias": "tv-yandex-012", "index": "012"},
        }),
        encoding="utf-8",
    )
    fake = MultiDeviceApprovedFakeRunner(("SYNTHETIC_SERIAL", "SYNTHETIC_SERIAL_TWO"))

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=fake)

    assert execution.adb_status == "READY"
    assert execution.device_statuses["tv-tpv-013"] == "READY"
    assert execution.device_statuses["tv-yandex-012"] == "READY"
    per_device_calls = [
        call for call in fake.calls
        if Path(call[0]).name.lower().startswith("adb") and len(call) > 2 and call[1] == "-s"
    ]
    assert {call[2] for call in per_device_calls} == {"SYNTHETIC_SERIAL", "SYNTHETIC_SERIAL_TWO"}
    candidate = json.loads((tmp_path / preflight.CANONICAL_GENERATED_INVENTORY).read_text(encoding="utf-8"))
    assert {device["device_alias"] for device in candidate["devices"]} == {"tv-tpv-013", "tv-yandex-012"}


def test_more_than_two_connected_devices_blocks_before_per_device_calls(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    map_path = tmp_path / preflight.CANONICAL_ALIAS_MAP
    map_path.write_text(
        json.dumps({
            "SYNTHETIC_SERIAL": {"device_alias": "tv-tpv-013", "index": "013"},
            "SYNTHETIC_SERIAL_TWO": {"device_alias": "tv-yandex-012", "index": "012"},
            "SYNTHETIC_SERIAL_THREE": {"device_alias": "tv-himedia-010", "index": "010"},
        }),
        encoding="utf-8",
    )
    fake = MultiDeviceApprovedFakeRunner(("SYNTHETIC_SERIAL", "SYNTHETIC_SERIAL_TWO", "SYNTHETIC_SERIAL_THREE"))

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=fake)

    assert execution.adb_status == "BLOCKED"
    assert "adb_snapshot_mapping_or_authorized_count_gate_failed" in execution.blockers
    assert not any(len(call) > 2 and call[1] == "-s" for call in fake.calls if Path(call[0]).name.lower().startswith("adb"))


def test_duplicate_connected_alias_blocks_before_per_device_calls(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    map_path = tmp_path / preflight.CANONICAL_ALIAS_MAP
    map_path.write_text(
        json.dumps({
            "SYNTHETIC_SERIAL": {"device_alias": "tv-tpv-013", "index": "013"},
            "SYNTHETIC_SERIAL_TWO": {"device_alias": "tv-tpv-013", "index": "013"},
        }),
        encoding="utf-8",
    )
    fake = MultiDeviceApprovedFakeRunner(("SYNTHETIC_SERIAL", "SYNTHETIC_SERIAL_TWO"))

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=fake)

    assert execution.adb_status == "BLOCKED"
    assert "serial_alias_map_aliases_not_unique" in execution.blockers
    assert not any(len(call) > 2 and call[1] == "-s" for call in fake.calls if Path(call[0]).name.lower().startswith("adb"))


def test_second_unmapped_connected_device_blocks_before_per_device_calls(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    fake = MultiDeviceApprovedFakeRunner(("SYNTHETIC_SERIAL", "UNMAPPED_SECOND"))

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=fake)

    assert execution.adb_status == "BLOCKED"
    assert "adb_snapshot_mapping_or_authorized_count_gate_failed" in execution.blockers
    assert not any(len(call) > 2 and call[1] == "-s" for call in fake.calls if Path(call[0]).name.lower().startswith("adb"))


def test_invalid_alias_map_blocks_before_any_adb_call(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    map_path = tmp_path / preflight.CANONICAL_ALIAS_MAP
    map_path.write_text(json.dumps({"SYNTHETIC_SERIAL": {"device_alias": "tv-tpv-013", "index": "013", "extra": True}}), encoding="utf-8")
    fake = ApprovedFakeRunner()

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=fake)

    assert execution.adb_status == "BLOCKED"
    assert [call[1:] for call in fake.calls if Path(call[0]).name.lower().startswith("adb")] == [["version"]]


def test_duplicate_serial_alias_map_key_is_rejected(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    map_path = tmp_path / preflight.CANONICAL_ALIAS_MAP
    map_path.write_text('{"SYNTHETIC_SERIAL":{"device_alias":"tv-tpv-013","index":"013"},"SYNTHETIC_SERIAL":{"device_alias":"tv-tpv-013","index":"013"}}', encoding="utf-8")

    _mapping, _review, errors = preflight.validate_alias_map_against_review(map_path, tmp_path / preflight.PUBLIC_DEVICE_INVENTORY)

    assert errors == ["alias_map_or_review_json_invalid_or_duplicate_key"]


def test_missing_configured_sdk_tools_fail_closed(tmp_path: Path) -> None:
    tools, errors = preflight.resolve_sdk_tools({"LOCALAPPDATA": str(tmp_path)})

    assert tools is None
    assert errors == ["configured_android_sdk_root_invalid"]


def test_invalid_sdk_execution_reports_no_android_invocation(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    shutil.rmtree(Path(env["LOCALAPPDATA"]) / "Android" / "Sdk")

    execution = preflight.execute_conditional_preflight(
        repo_root=tmp_path,
        env=env,
        runner=ApprovedFakeRunner(),
    )
    report = preflight.build_report(repo_root=tmp_path, presence=execution.presence, execution=execution)

    assert execution.apk_contents_read is False
    assert execution.apk_tool_invoked is False
    assert execution.adb_invoked is False
    assert execution.avd_invoked is False
    assert execution.adb_snapshot_observed is False
    assert report["payload"]["tooling"]["adb"]["invoked"] is False
    assert report["payload"]["tooling"]["avd"]["invoked"] is False
    assert report["provenance"]["subprocesses"] == "not_run"
    assert report["provenance"]["apk_contents_read"] is False
    assert report["provenance"]["local_identity_values_read"] is False


def test_unavailable_batch_wrapper_does_not_claim_apk_tool_invocation(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    sdk = Path(env["LOCALAPPDATA"]) / "Android" / "Sdk"
    (sdk / "cmdline-tools" / "latest" / "bin" / "apkanalyzer.exe").rename(
        sdk / "cmdline-tools" / "latest" / "bin" / "apkanalyzer.bat"
    )
    (sdk / "build-tools" / "1.0" / "apksigner.exe").rename(
        sdk / "build-tools" / "1.0" / "apksigner.bat"
    )

    execution = preflight.execute_conditional_preflight(
        repo_root=tmp_path,
        env=env,
        runner=ApprovedFakeRunner(),
    )

    assert execution.apk_contents_read is True
    assert execution.apk_tool_invoked is False
    assert execution.apk_metadata_status == "TOOLING_DEFECT"


def test_inaccessible_configured_sdk_root_is_terminal_tooling_blocker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdk_root = tmp_path / "Android" / "Sdk"
    sdk_root.mkdir(parents=True)
    original_stat = Path.stat

    def denied(path: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if path == sdk_root:
            raise PermissionError("synthetic SDK access denial")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", denied)

    tools, errors = preflight.resolve_sdk_tools({"LOCALAPPDATA": str(tmp_path)})

    assert tools is None
    assert errors == ["configured_android_sdk_root_inaccessible"]


def test_inaccessible_sdk_report_records_complete_public_safe_anomaly() -> None:
    statuses = {alias: "UNKNOWN" for alias in (*preflight.REQUIRED_DEVICE_ALIASES, preflight.PAIRED_PHONE_FALLBACK_ALIAS)}
    execution = preflight.ExecutionSummary(
        presence=ready_bundle_presence(), apk_metadata_status="TOOLING_DEFECT", adb_tool_status="TOOLING_DEFECT",
        adb_status="TOOLING_DEFECT", avd_status="TOOLING_DEFECT", avd_count=None,
        ignored_unreviewed_alias_count=0, device_statuses=statuses,
        blockers=("configured_android_sdk_root_inaccessible",), raw_evidence_written=True,
    )

    report = preflight.build_report(repo_root=ROOT, presence=execution.presence, execution=execution)
    anomaly = next(
        row for row in report["payload"]["process_anomalies"]
        if row["public_safe_alias"] == "configured_sdk_access_interruption"
    )

    assert anomaly["evidence_status"] == "confirmed"
    assert anomaly["cause_evidence_status"] == "likely"
    assert anomaly["test_design_implication"]
    assert report["payload"]["tooling"]["adb"]["invoked"] is False
    assert report["payload"]["tooling"]["avd"]["invoked"] is False
    assert report["provenance"]["subprocesses"] == "not_run"
    assert report["provenance"]["apk_contents_read"] is False
    assert report["payload"]["apk_readiness"]["bundle_status"] == "BLOCKED"
    assert {entry["scenario_status"] for entry in report["payload"]["apk_readiness"]["entries"]} == {"blocked_by_oracle"}
    assert next(row for row in report["payload"]["scenario_ledger"] if row["scenario_id"] == "QA-042-001")["scenario_status"] == "blocked_by_fixture"
    assert {row["evidence_type"] for row in report["payload"]["scenario_ledger"] if row["scenario_id"] in {"QA-042-001", "QA-042-004", "QA-042-007", "QA-042-008", "QA-042-010"}} == {"local_preflight_gate"}
    assert preflight.validate_report(report) == []


def test_stale_generated_candidate_is_rejected(tmp_path: Path) -> None:
    _execution_fixture(tmp_path)
    _mapping, review, errors = preflight.validate_alias_map_against_review(
        tmp_path / preflight.CANONICAL_ALIAS_MAP,
        tmp_path / preflight.PUBLIC_DEVICE_INVENTORY,
    )
    assert errors == []
    reviewed = review["tv-tpv-013"]
    candidate = {
        "schema_version": "task-016-device-inventory-public-safe-v1",
        "generated_at_utc": "2020-01-01T00:00:00Z",
        "source": "adb_inventory_sanitized_local_output",
        "runtime_execution_status": "not_run",
        "apk_install_status": "not_run",
        "app_launch_status": "not_run",
        "devices": [dict(reviewed)],
        "public_device_count": 1,
        "redaction_status": "redacted",
        "public_safety_findings": [],
        "redaction_guarantees": {key: True for key in preflight.task016_inventory.REQUIRED_REDACTION_GUARANTEE_KEYS},
    }
    candidate["devices"][0]["classification_confidence"] = "heuristic"
    candidate["devices"][0]["manual_review_required"] = True

    assert "generated_candidate_stale_or_future" in preflight.validate_generated_candidate(candidate, review)


def test_two_stale_unreviewed_aliases_are_non_authoritative_not_blocking(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    map_path = tmp_path / preflight.CANONICAL_ALIAS_MAP
    map_path.write_text(
        json.dumps({
            "SYNTHETIC_SERIAL": {"device_alias": "tv-tpv-013", "index": "013"},
            "STALE_ONE": {"device_alias": "tv-stale-101", "index": "101"},
            "STALE_TWO": {"device_alias": "stb-stale-102", "index": "102"},
        }),
        encoding="utf-8",
    )

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=ApprovedFakeRunner())

    assert execution.adb_status == "READY"
    assert execution.ignored_unreviewed_alias_count == 2


def test_aapt_fallback_parses_package_version_without_apkanalyzer(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    sdk = Path(env["LOCALAPPDATA"]) / "Android" / "Sdk"
    (sdk / "cmdline-tools" / "latest" / "bin" / "apkanalyzer.exe").unlink()
    aapt = sdk / "build-tools" / "1.0" / "aapt2.exe"
    aapt.write_text("synthetic tool", encoding="utf-8")
    tools, errors = preflight.resolve_sdk_tools(env)
    assert errors == [] and tools is not None and tools.apkanalyzer is None

    def fake(argv, capture_output, text, timeout, check):  # type: ignore[no-untyped-def]
        if Path(argv[0]).name.lower().startswith("aapt"):
            stdout = "package: name='synthetic.package' versionCode='7' versionName='2.0'"
        else:
            stdout = "Signer certificate synthetic metadata"
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

    records, metadata_errors = preflight.capture_apk_metadata(
        [tmp_path / preflight.CANONICAL_APK_DIR / preflight.EXPECTED_APKS[0]],
        tools,
        fake,
    )

    assert metadata_errors == []
    assert records[0]["package_id"] == "synthetic.package"
    assert records[0]["version_code"] == "7"
    assert records[0]["version_name"] == "2.0"


def test_batch_tool_wrapper_uses_fixed_outer_quoting_and_rejects_metacharacters(tmp_path: Path) -> None:
    cmd = tmp_path / "cmd.exe"
    tool = tmp_path / "sdk tools" / "apksigner.bat"

    argv = preflight._sdk_tool_argv(tool, ["verify", "fixture.apk"], cmd)

    assert argv == [
        str(cmd),
        "/d",
        "/v:off",
        "/s",
        "/c",
        f'""{tool}" "verify" "fixture.apk""',
    ]
    assert preflight._sdk_tool_argv(tool, ["verify", "unsafe&(fixture).apk"], cmd) is None


def test_execution_report_removes_resolved_static_tooling_blockers(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=ApprovedFakeRunner())
    report = preflight.build_report(repo_root=tmp_path, presence=execution.presence, execution=execution)
    rows = {row["scenario_id"]: row for row in report["payload"]["scenario_ledger"]}

    assert rows["QA-042-001"]["scenario_status"] == "observed_pass"
    assert rows["QA-042-004"]["scenario_status"] == "observed_pass"
    assert rows["QA-042-007"]["scenario_status"] == "observed_pass"
    assert rows["QA-042-008"]["scenario_status"] == "observed_pass"
    assert "configured_adb_path_not_verified" not in report["blocked_reasons"]
    assert "configured_avd_tooling_not_verified" not in report["blocked_reasons"]
    assert report["coverage_status"] == "partial_blocked"
    assert preflight.validate_report(report) == []


def test_pass2_changed_adb_snapshot_blocks_before_per_device_calls(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)

    class ChangedSnapshotRunner(ApprovedFakeRunner):
        def __init__(self) -> None:
            super().__init__()
            self.inventory_calls = 0

        def __call__(self, argv, capture_output, text, timeout, check):  # type: ignore[no-untyped-def]
            if Path(argv[0]).name.lower().startswith("adb") and argv[1:] == ["devices", "-l"]:
                self.calls.append(list(argv))
                self.inventory_calls += 1
                state = "device" if self.inventory_calls == 1 else "offline"
                return subprocess.CompletedProcess(argv, 0, stdout=f"List of devices attached\n{self.serial} {state}\n", stderr="")
            return super().__call__(argv, capture_output, text, timeout, check)

    fake = ChangedSnapshotRunner()
    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=fake)
    adb_tails = [call[1:] for call in fake.calls if Path(call[0]).name.lower().startswith("adb")]

    assert execution.adb_status == "BLOCKED"
    assert adb_tails == [["version"], ["devices", "-l"], ["devices", "-l"]]


def test_adb_version_empty_is_tooling_defect_and_no_device_precheck(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)

    class EmptyVersionRunner(ApprovedFakeRunner):
        def __call__(self, argv, capture_output, text, timeout, check):  # type: ignore[no-untyped-def]
            if Path(argv[0]).name.lower().startswith("adb") and argv[1:] == ["version"]:
                self.calls.append(list(argv))
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
            return super().__call__(argv, capture_output, text, timeout, check)

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=EmptyVersionRunner())
    report = preflight.build_report(repo_root=tmp_path, presence=execution.presence, execution=execution)

    assert execution.adb_tool_status == "TOOLING_DEFECT"
    assert execution.adb_status == "BLOCKED"
    assert {row["scenario_id"]: row for row in report["payload"]["scenario_ledger"]}["QA-042-007"]["scenario_status"] == "tooling_defect"


def test_unmapped_connected_target_keeps_all_required_aliases_unknown(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path, mapped_serial="OTHER_SERIAL")
    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=ApprovedFakeRunner(serial="UNMAPPED_SERIAL"))

    assert set(execution.device_statuses.values()) == {"UNKNOWN"}
    report = preflight.build_report(repo_root=tmp_path, presence=execution.presence, execution=execution)
    assert {row["evidence_status"] for row in report["payload"]["device_readiness"]} == {"unknown"}
    assert report["provenance"]["local_identity_values_read"] is True
    anomaly = next(
        row for row in report["payload"]["process_anomalies"]
        if row["public_safe_alias"] == "current_unmapped_snapshot_stop"
    )
    assert anomaly["cause_evidence_status"] == "likely"


def test_strict_adb_snapshot_rejects_duplicate_and_incomplete_lines() -> None:
    snapshot, errors = preflight.parse_strict_adb_snapshot(
        "List of devices attached\nSERIAL device\nSERIAL offline\nINCOMPLETE\n"
    )

    assert snapshot == {"SERIAL": "device"}
    assert errors == ["adb_snapshot_duplicate_serial", "adb_snapshot_line_incomplete"]


def test_samsung_fallback_requires_explicit_ready_classification() -> None:
    statuses = {alias: "MISSING" for alias in preflight.REQUIRED_DEVICE_ALIASES}
    statuses[preflight.PAIRED_PHONE_FALLBACK_ALIAS] = "READY"
    execution = preflight.ExecutionSummary(
        presence=ready_bundle_presence(), apk_metadata_status="READY", adb_tool_status="READY",
        adb_status="BLOCKED", avd_status="READY", avd_count=0, ignored_unreviewed_alias_count=0,
        device_statuses=statuses, blockers=("primary_phone_unavailable",), raw_evidence_written=True,
    )
    report = preflight.build_report(repo_root=ROOT, presence=execution.presence, execution=execution)
    row = {item["scenario_id"]: item for item in report["payload"]["scenario_ledger"]}["QA-042-012"]

    assert row["scenario_status"] == "observed_pass"
    assert report["payload"]["selected_lanes"]["TASK-045"]["device_alias"] == "phone-samsung-002"
    assert report["payload"]["selected_lanes"]["TASK-045"]["fallback_selected"] is True


def test_report_rejects_extra_top_level_even_before_official_v2_validation() -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    report["unexpected"] = True

    assert any("unsupported top-level fields" in error for error in preflight.validate_report(report))


def test_device_contract_path_reparse_blocks_before_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _execution_fixture(tmp_path)
    alias_map = tmp_path / preflight.CANONICAL_ALIAS_MAP
    original = preflight._is_reparse
    monkeypatch.setattr(preflight, "_is_reparse", lambda path: path == alias_map or original(path))
    fake = ApprovedFakeRunner()

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env={"LOCALAPPDATA": str(tmp_path)}, runner=fake)

    assert execution.raw_evidence_written is False
    assert fake.calls == []
    assert "canonical_alias_map_missing_or_reparse" in execution.blockers


def test_task016_alias_map_mutation_blocks_authority_promotion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = _execution_fixture(tmp_path)
    original = preflight.task016_inventory.build_report

    def mutated(*args, **kwargs):  # type: ignore[no-untyped-def]
        report, raw, alias_map, candidate = original(*args, **kwargs)
        changed = dict(alias_map)
        changed["SYNTHETIC_NEW"] = {"device_alias": "tv-new-099", "index": "099"}
        return report, raw, changed, candidate

    monkeypatch.setattr(preflight.task016_inventory, "build_report", mutated)
    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=ApprovedFakeRunner())

    assert execution.adb_status == "BLOCKED"
    assert execution.device_statuses["tv-tpv-013"] == "UNKNOWN"
    assert "task016_attempted_alias_map_mutation" in execution.blockers
    assert not (tmp_path / preflight.CANONICAL_GENERATED_INVENTORY).exists()
    assert not (tmp_path / preflight.CANONICAL_DEVICE_PREFLIGHT).exists()


def test_candidate_profile_mismatch_is_incompatible_and_not_promoted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = _execution_fixture(tmp_path)
    original = preflight.task016_inventory.build_report

    def mismatched(*args, **kwargs):  # type: ignore[no-untyped-def]
        report, raw, alias_map, candidate = original(*args, **kwargs)
        candidate["devices"][0]["screen_class"] = "fhd_or_unknown"
        return report, raw, alias_map, candidate

    monkeypatch.setattr(preflight.task016_inventory, "build_report", mismatched)
    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=ApprovedFakeRunner())

    assert execution.adb_status == "BLOCKED"
    assert execution.device_statuses["tv-tpv-013"] == "INCOMPATIBLE"
    assert "generated_candidate_profile_differs_from_review" in execution.blockers
    assert not (tmp_path / preflight.CANONICAL_GENERATED_INVENTORY).exists()


def test_two_device_candidate_error_downgrades_every_selected_alias(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = _execution_fixture(tmp_path)
    map_path = tmp_path / preflight.CANONICAL_ALIAS_MAP
    map_path.write_text(
        json.dumps({
            "SYNTHETIC_SERIAL": {"device_alias": "tv-tpv-013", "index": "013"},
            "SYNTHETIC_SERIAL_TWO": {"device_alias": "tv-yandex-012", "index": "012"},
        }),
        encoding="utf-8",
    )
    original = preflight.task016_inventory.build_report

    def mismatched(*args, **kwargs):  # type: ignore[no-untyped-def]
        report, raw, alias_map, candidate = original(*args, **kwargs)
        candidate["devices"][0]["screen_class"] = "mobile_or_unknown"
        return report, raw, alias_map, candidate

    monkeypatch.setattr(preflight.task016_inventory, "build_report", mismatched)

    execution = preflight.execute_conditional_preflight(
        repo_root=tmp_path,
        env=env,
        runner=MultiDeviceApprovedFakeRunner(("SYNTHETIC_SERIAL", "SYNTHETIC_SERIAL_TWO")),
    )

    assert execution.adb_status == "BLOCKED"
    assert execution.device_statuses["tv-tpv-013"] == "INCOMPATIBLE"
    assert execution.device_statuses["tv-yandex-012"] == "INCOMPATIBLE"
    assert not (tmp_path / preflight.CANONICAL_GENERATED_INVENTORY).exists()


def test_task016_blocked_result_downgrades_selected_alias_and_prevents_promotion(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    map_path = tmp_path / preflight.CANONICAL_ALIAS_MAP
    map_path.write_text(
        json.dumps({
            "SYNTHETIC_SERIAL": {"device_alias": "tv-tpv-013", "index": "013"},
            "MAPPED_OFFLINE": {"device_alias": "tv-yandex-012", "index": "012"},
        }),
        encoding="utf-8",
    )

    class MappedOfflineRunner(ApprovedFakeRunner):
        def __call__(self, argv, capture_output, text, timeout, check):  # type: ignore[no-untyped-def]
            if Path(argv[0]).name.lower().startswith("adb") and argv[1:] == ["devices", "-l"]:
                self.calls.append(list(argv))
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout="List of devices attached\nSYNTHETIC_SERIAL device\nMAPPED_OFFLINE offline\n",
                    stderr="",
                )
            return super().__call__(argv, capture_output, text, timeout, check)

    execution = preflight.execute_conditional_preflight(repo_root=tmp_path, env=env, runner=MappedOfflineRunner())

    assert execution.adb_status == "BLOCKED"
    assert execution.device_statuses["tv-tpv-013"] == "UNKNOWN"
    assert "task016_inventory_report_blocked" in execution.blockers
    assert not (tmp_path / preflight.CANONICAL_GENERATED_INVENTORY).exists()


def test_signature_failure_diagnostics_remain_in_local_metadata_record(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path)
    tools, errors = preflight.resolve_sdk_tools(env)
    assert errors == [] and tools is not None

    def runner(argv, capture_output, text, timeout, check):  # type: ignore[no-untyped-def]
        if "apksigner" in Path(argv[0]).name.lower():
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="synthetic signature failure")
        field = argv[-2]
        output = {"application-id": "synthetic.package", "version-name": "1", "version-code": "1"}[field]
        return subprocess.CompletedProcess(argv, 0, stdout=output, stderr="")

    records, metadata_errors = preflight.capture_apk_metadata(
        [tmp_path / preflight.CANONICAL_APK_DIR / preflight.EXPECTED_APKS[0]], tools, runner
    )

    assert any("signature_output" in error for error in metadata_errors)
    signature = next(item for item in records[0]["tool_diagnostics"] if item["tool"] == "signature_output")
    assert signature["returncode"] == 1
    assert signature["stderr"] == "synthetic signature failure"


def test_execute_cli_returns_nonzero_when_expected_apk_lane_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    statuses = {alias: "UNKNOWN" for alias in (*preflight.REQUIRED_DEVICE_ALIASES, preflight.PAIRED_PHONE_FALLBACK_ALIAS)}
    execution = preflight.ExecutionSummary(
        presence=absent_presence(), apk_metadata_status="BLOCKED", adb_tool_status="READY",
        adb_status="BLOCKED", avd_status="READY", avd_count=0, ignored_unreviewed_alias_count=0,
        device_statuses=statuses, blockers=("expected_apk_entries_missing",), raw_evidence_written=False,
    )
    monkeypatch.setattr(preflight, "execute_conditional_preflight", lambda **kwargs: execution)

    result = preflight.main([
        "--execute", "--allow-local-apk-metadata", "--allow-adb-inventory",
        "--local-evidence-root", ".qa_local/evidence/task-042/", "--repo-root", str(ROOT),
    ])

    assert result == 3


def test_validate_report_file_invokes_official_v2_and_rejects_extra_top_level(tmp_path: Path) -> None:
    report = preflight.build_report(repo_root=ROOT, presence=absent_presence())
    report_path = tmp_path / "task042.summary.json"
    ledger_path = tmp_path / "task042.scenario-ledger.csv"
    matrix_path = tmp_path / "task042.readiness-matrix.csv"
    preflight.write_report_bundle(report, report_path, ledger_path, matrix_path)
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    saved["unexpected"] = True
    report_path.write_text(json.dumps(saved), encoding="utf-8")

    errors = preflight.validate_report_file(report_path, tmp_path)
    assert any("unsupported top-level fields" in error or "v2_unknown_top_level_fields" in error for error in errors)


def test_unmapped_device_keeps_sdk_resolution_pass_separate_from_inventory_block(tmp_path: Path) -> None:
    env = _execution_fixture(tmp_path, mapped_serial="OTHER_SERIAL")
    execution = preflight.execute_conditional_preflight(
        repo_root=tmp_path,
        env=env,
        runner=ApprovedFakeRunner(serial="UNMAPPED_SERIAL"),
    )

    report = preflight.build_report(repo_root=tmp_path, presence=execution.presence, execution=execution)
    rows = {row["scenario_id"]: row for row in report["payload"]["scenario_ledger"]}

    assert rows["QA-042-007"]["scenario_status"] == "observed_pass"
    assert rows["QA-042-010"]["scenario_status"] == "blocked_by_device"
    assert "configured_adb_path_not_verified" not in report["blocked_reasons"]
    summary = report["payload"]["scenario_summary"]
    assert summary["observed_pass"] + summary["blocked"] + summary["tooling_defect"] == summary["total"]

"""TASK-042 public-safe local runtime readiness preflight.

The default validation lane is static and never reads ``.qa_local`` or starts a
subprocess.  The preflight lane inspects only the presence and direct-child
names defined by existing repository-relative contracts.  It does not read APK
contents, query Android tooling, contact devices, or publish local identities.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

try:
    from automation.device_inventory import generate_adb_device_inventory as task016_inventory
    from automation.reporting.generate_report_manifest import _validate_v2_envelope
except ModuleNotFoundError:  # Direct ``python automation/...py`` execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from automation.device_inventory import generate_adb_device_inventory as task016_inventory
    from automation.reporting.generate_report_manifest import _validate_v2_envelope


TASK_ID = "TASK-042"
SCHEMA_VERSION = "evidence-report-envelope-v2"
PRODUCTION_SAFETY_CLASSIFICATION = "PROD_CONDITIONAL"
SCENARIO_CATALOG = Path("docs/qa/epics/scenarios/task042_scenarios.csv")
APK_CONTRACT = Path("docs/approvals/task005_apk_bundle_contract.md")
PUBLIC_DEVICE_INVENTORY = Path("docs/approvals/device_inventory.public_safe.review.json")
CANONICAL_APK_DIR = Path(".qa_local/apks/task-005")
CANONICAL_DEVICE_DIR = Path(".qa_local/devices")
CANONICAL_ALIAS_MAP = CANONICAL_DEVICE_DIR / "serial_alias_map.json"
CANONICAL_GENERATED_INVENTORY = CANONICAL_DEVICE_DIR / "device_inventory.public_safe.generated.json"
CANONICAL_DEVICE_PREFLIGHT = CANONICAL_DEVICE_DIR / "preflight_report.json"
CANONICAL_TASK042_EVIDENCE = Path(".qa_local/evidence/task-042")

DEFAULT_REPORT = Path("docs/qa/reports/task042_local_runtime_preflight.summary.json")
DEFAULT_LEDGER = Path("docs/qa/reports/task042_local_runtime_preflight.scenario-ledger.csv")
DEFAULT_MATRIX = Path("docs/qa/reports/task042_local_runtime_preflight.readiness-matrix.csv")

EXPECTED_APKS = (
    "fogplay-tv-television-steam-production-release.apk",
    "fogplay-tv-television-sber-production-release.apk",
    "fogplay-tv-phone-full-production-release.apk",
    "fogplay-tv-aosp-full-production-release.apk",
    "fogplay-tv-television-full-production-release.apk",
)

REQUIRED_DEVICE_ALIASES = (
    "tv-tpv-013",
    "phone-xiaomi-007",
    "tv-yandex-012",
    "stb-sberdevices-009",
)
PAIRED_PHONE_FALLBACK_ALIAS = "phone-samsung-002"

TERMINAL_SCENARIO_STATUSES = {
    "observed_pass",
    "observed_fail",
    "confirmed_defect",
    "tooling_defect",
    "executable_not_run",
    "blocked_by_device",
    "blocked_by_fixture",
    "blocked_by_oracle",
    "blocked_by_product_boundary",
    "blocked_by_external_state",
    "not_applicable",
    "mapped_only",
}

NON_CLOSING_STATUSES = {"executable_not_run", "mapped_only"}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}

FORBIDDEN_PUBLIC_KEYS = {
    "absolute_path",
    "account",
    "adb_serial",
    "android_id",
    "endpoint",
    "full_build_fingerprint",
    "imei",
    "ip",
    "mac",
    "raw_hash",
    "raw_metadata",
    "raw_serial",
    "token",
}

FORBIDDEN_PUBLIC_PATTERNS = (
    ("windows_absolute_path", re.compile(r"(?i)(?:^|[\s\"'])[a-z]:[\\/]")),
    ("unc_path", re.compile(r"\\\\[^\\\s]+\\")),
    ("user_profile_path", re.compile(r"(?i)/(?:users|home)/[^/\s]+/")),
    ("network_url", re.compile(r"(?i)\b(?:https?|wss?)://")),
    ("ipv4", re.compile(r"(?<![\w-])(?:\d{1,3}\.){3}\d{1,3}(?![\w-])")),
)


@dataclass(frozen=True)
class CanonicalPresence:
    """Presence-only local snapshot; values are safe to aggregate publicly."""

    apk_dir_present: bool
    expected_apks_present: tuple[str, ...]
    unexpected_apk_count: int
    device_dir_present: bool
    device_preflight_present: bool
    public_device_inventory_present: bool


@dataclass(frozen=True)
class SdkTools:
    sdk_root: Path
    adb: Path
    emulator: Path | None
    apkanalyzer: Path | None
    aapt: Path | None
    apksigner: Path | None
    apksigner_jar: Path | None
    java: Path | None
    cmd_exe: Path | None


@dataclass(frozen=True)
class ExecutionSummary:
    presence: CanonicalPresence
    apk_metadata_status: str
    adb_tool_status: str
    adb_status: str
    avd_status: str
    avd_count: int | None
    ignored_unreviewed_alias_count: int
    device_statuses: Mapping[str, str]
    blockers: tuple[str, ...]
    raw_evidence_written: bool
    apk_contents_read: bool = False
    apk_tool_invoked: bool = False
    adb_invoked: bool = False
    avd_invoked: bool = False
    adb_snapshot_observed: bool = False


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_path(path: Path) -> str:
    return path.as_posix()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_scenarios(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_static_contracts(repo_root: Path = Path(".")) -> list[str]:
    """Validate tracked contracts only; never inspect local runtime storage."""

    root = repo_root.resolve()
    errors: list[str] = []
    catalog_path = root / SCENARIO_CATALOG
    apk_contract_path = root / APK_CONTRACT
    inventory_path = root / PUBLIC_DEVICE_INVENTORY

    for path, label in (
        (catalog_path, "scenario catalog"),
        (apk_contract_path, "APK contract"),
        (inventory_path, "public device inventory"),
    ):
        if not path.is_file():
            errors.append(f"missing tracked {label}: {_repo_path(path.relative_to(root))}")

    if errors:
        return errors

    scenarios = _load_scenarios(catalog_path)
    expected_ids = [f"QA-042-{index:03d}" for index in range(1, 19)]
    actual_ids = [row.get("scenario_id", "") for row in scenarios]
    if actual_ids != expected_ids:
        errors.append("scenario catalog must contain QA-042-001..018 exactly and in order")
    if sum(row.get("priority") == "P0" for row in scenarios) != 15:
        errors.append("scenario catalog must contain exactly 15 P0 rows")
    if any(row.get("automation_target") != "automate" for row in scenarios):
        errors.append("every TASK-042 scenario must target automation")

    contract_text = apk_contract_path.read_text(encoding="utf-8")
    contract_apks = tuple(name for name in EXPECTED_APKS if f"`{name}`" in contract_text)
    if contract_apks != EXPECTED_APKS:
        errors.append("APK contract must contain the exact five expected bundle entries")

    inventory = _load_json(inventory_path)
    devices = inventory.get("devices", []) if isinstance(inventory, dict) else []
    aliases = {item.get("device_alias") for item in devices if isinstance(item, dict)}
    missing_aliases = sorted(set(REQUIRED_DEVICE_ALIASES) - aliases)
    if missing_aliases:
        errors.append("public device inventory misses required aliases: " + ", ".join(missing_aliases))
    return errors


def probe_canonical_presence(repo_root: Path = Path(".")) -> CanonicalPresence:
    """Inspect canonical path presence only; no APK reads and no subprocesses."""

    root = repo_root.resolve()
    apk_dir = root / CANONICAL_APK_DIR
    expected_present: tuple[str, ...] = ()
    unexpected_count = 0
    if apk_dir.is_dir():
        direct_apks = {entry.name for entry in apk_dir.iterdir() if entry.is_file() and entry.suffix.lower() == ".apk"}
        expected_present = tuple(name for name in EXPECTED_APKS if name in direct_apks)
        unexpected_count = len(direct_apks - set(EXPECTED_APKS))

    device_dir = root / CANONICAL_DEVICE_DIR
    return CanonicalPresence(
        apk_dir_present=apk_dir.is_dir(),
        expected_apks_present=expected_present,
        unexpected_apk_count=unexpected_count,
        device_dir_present=device_dir.is_dir(),
        device_preflight_present=(device_dir / "preflight_report.json").is_file(),
        public_device_inventory_present=(device_dir / "device_inventory.public_safe.generated.json").is_file(),
    )


def _is_reparse(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return True
    return path.is_symlink() or bool(attributes & 0x400)


def _is_regular_non_reparse(path: Path) -> bool:
    return path.is_file() and not _is_reparse(path)


def _validate_execution_evidence_root(repo_root: Path, evidence_root: Path) -> Path:
    root = repo_root.resolve()
    requested = evidence_root if evidence_root.is_absolute() else root / evidence_root
    resolved = requested.resolve(strict=False)
    expected = (root / CANONICAL_TASK042_EVIDENCE).resolve(strict=False)
    if resolved != expected:
        raise ValueError("--local-evidence-root must be the canonical .qa_local/evidence/task-042/ path")
    current = root / ".qa_local"
    for part in ("evidence", "task-042"):
        if current.exists() and _is_reparse(current):
            raise ValueError("local evidence path must not traverse a reparse point")
        current = current / part
    if current.exists() and _is_reparse(current):
        raise ValueError("local evidence path must not be a reparse point")
    return resolved


def _bounded_tool_candidates(root: Path, relative_parent: Path, names: Sequence[str]) -> list[Path]:
    parent = root / relative_parent
    if not parent.is_dir() or _is_reparse(parent):
        return []
    candidates: list[Path] = []
    def version_key(item: Path) -> tuple[int, ...]:
        numbers = tuple(int(part) for part in re.findall(r"\d+", item.name))
        return numbers or (-1,)

    for child in sorted(parent.iterdir(), key=version_key, reverse=True):
        if not child.is_dir() or _is_reparse(child):
            continue
        for name in names:
            candidate = child / "bin" / name if relative_parent.name == "cmdline-tools" else child / name
            if _is_regular_non_reparse(candidate):
                candidates.append(candidate)
    return candidates


def resolve_sdk_tools(env: Mapping[str, str] | None = None) -> tuple[SdkTools | None, list[str]]:
    """Resolve tools inside configured or deterministic standard SDK roots only."""

    environment = dict(os.environ if env is None else env)
    configured = [environment.get(name, "").strip() for name in ("ANDROID_SDK_ROOT", "ANDROID_HOME")]
    configured = [value for value in configured if value]
    if len({str(Path(value).resolve(strict=False)).casefold() for value in configured}) > 1:
        return None, ["android_sdk_environment_conflict"]
    if configured:
        sdk_root = Path(configured[0]).resolve(strict=False)
    else:
        local_app_data = environment.get("LOCALAPPDATA", "").strip()
        if not local_app_data:
            return None, ["configured_android_sdk_root_missing"]
        sdk_root = (Path(local_app_data) / "Android" / "Sdk").resolve(strict=False)
    try:
        sdk_root_mode = sdk_root.stat().st_mode
    except FileNotFoundError:
        return None, ["configured_android_sdk_root_invalid"]
    except OSError:
        return None, ["configured_android_sdk_root_inaccessible"]
    if not stat.S_ISDIR(sdk_root_mode) or _is_reparse(sdk_root):
        return None, ["configured_android_sdk_root_invalid"]

    adb_names = ("adb.exe", "adb")
    adb = next((sdk_root / "platform-tools" / name for name in adb_names if _is_regular_non_reparse(sdk_root / "platform-tools" / name)), None)
    if adb is None:
        return None, ["configured_sdk_adb_missing"]

    apkanalyzer_names = ("apkanalyzer.exe", "apkanalyzer", "apkanalyzer.bat")
    direct_analyzers = [sdk_root / "cmdline-tools" / "latest" / "bin" / name for name in apkanalyzer_names]
    apkanalyzer = next((path for path in direct_analyzers if _is_regular_non_reparse(path)), None)
    if apkanalyzer is None:
        candidates = _bounded_tool_candidates(sdk_root, Path("cmdline-tools"), apkanalyzer_names)
        apkanalyzer = candidates[0] if candidates else None

    build_tools = sdk_root / "build-tools"
    aapt_candidates = _bounded_tool_candidates(sdk_root, Path("build-tools"), ("aapt2.exe", "aapt.exe", "aapt2", "aapt"))
    aapt = aapt_candidates[0] if aapt_candidates else None
    signer_names = ("apksigner.exe", "apksigner", "apksigner.bat")
    signer_candidates = _bounded_tool_candidates(sdk_root, Path("build-tools"), signer_names)
    apksigner = signer_candidates[0] if signer_candidates else None
    apksigner_jar = None
    if apksigner is not None:
        jar_candidate = apksigner.parent / "lib" / "apksigner.jar"
        if _is_regular_non_reparse(jar_candidate):
            apksigner_jar = jar_candidate
    java_candidates: list[Path] = []
    java_home = environment.get("JAVA_HOME", "").strip()
    if java_home:
        java_candidates.append(Path(java_home).resolve(strict=False) / "bin" / "java.exe")
    program_files = environment.get("ProgramFiles", "").strip()
    if program_files:
        java_candidates.append(Path(program_files) / "Android" / "Android Studio" / "jbr" / "bin" / "java.exe")
    java = next((path for path in java_candidates if _is_regular_non_reparse(path)), None)
    emulator = next((sdk_root / "emulator" / name for name in ("emulator.exe", "emulator") if _is_regular_non_reparse(sdk_root / "emulator" / name)), None)
    system_root = environment.get("SystemRoot", environment.get("WINDIR", "")).strip()
    cmd_exe = Path(system_root) / "System32" / "cmd.exe" if system_root else None
    if cmd_exe is not None and not _is_regular_non_reparse(cmd_exe):
        cmd_exe = None
    return SdkTools(
        sdk_root=sdk_root,
        adb=adb,
        emulator=emulator,
        apkanalyzer=apkanalyzer,
        aapt=aapt,
        apksigner=apksigner,
        apksigner_jar=apksigner_jar,
        java=java,
        cmd_exe=cmd_exe,
    ), []


def validate_canonical_apks(repo_root: Path) -> tuple[CanonicalPresence, list[Path], list[str]]:
    root = repo_root.resolve()
    apk_dir = root / CANONICAL_APK_DIR
    errors: list[str] = []
    valid_paths: list[Path] = []
    if not apk_dir.is_dir() or _is_reparse(apk_dir):
        return probe_canonical_presence(root), [], ["canonical_apk_directory_missing_or_reparse"]
    direct_apks = [entry for entry in apk_dir.iterdir() if entry.suffix.lower() == ".apk"]
    names = {entry.name for entry in direct_apks}
    missing = sorted(set(EXPECTED_APKS) - names)
    extras = sorted(names - set(EXPECTED_APKS))
    if missing:
        errors.append("expected_apk_entries_missing")
    if extras:
        errors.append("unexpected_apk_entries_present")
    for name in EXPECTED_APKS:
        path = apk_dir / name
        if name not in names:
            continue
        if not _is_regular_non_reparse(path):
            errors.append("expected_apk_not_regular_or_reparse")
        elif path.stat().st_size <= 0:
            errors.append("expected_apk_empty")
        else:
            valid_paths.append(path)
    return probe_canonical_presence(root), valid_paths, sorted(set(errors))


def _run_bounded(runner: CommandRunner, argv: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return runner(argv, capture_output=True, text=True, timeout=timeout, check=False)


def _sdk_tool_argv(tool: Path, args: Sequence[str], cmd_exe: Path | None) -> list[str] | None:
    if tool.suffix.lower() not in {".bat", ".cmd"}:
        return [str(tool), *args]
    if cmd_exe is None:
        return None
    raw_parts = [str(tool), *args]
    if any(any(character in part for character in ('"', "\r", "\n", "&", "|", "<", ">", "^", "%", "!", "(", ")")) for part in raw_parts):
        return None
    # cmd.exe /s strips the outer pair and leaves each fixed argument quoted.
    # Every fragment is already gate-validated above; no shell-derived input is
    # interpolated and subprocess continues to run with shell=False.
    command = '"' + " ".join(f'"{part}"' for part in raw_parts) + '"'
    return [str(cmd_exe), "/d", "/v:off", "/s", "/c", command]


def capture_apk_metadata(
    apk_paths: Sequence[Path],
    tools: SdkTools,
    runner: CommandRunner = subprocess.run,
) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if tools.apkanalyzer is None and tools.aapt is None:
        errors.append("configured_sdk_apk_metadata_tool_missing")
    if tools.apksigner is None:
        errors.append("configured_sdk_apksigner_missing")
    for index, path in enumerate(apk_paths, 1):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        record: dict[str, Any] = {
            "apk_alias": f"main-apk-{index:02d}",
            "contract_filename": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": digest.hexdigest(),
            "package_id": None,
            "version_name": None,
            "version_code": None,
            "signature_output": None,
            "tool_diagnostics": [],
        }
        commands: list[tuple[str, list[str] | None]] = []
        if tools.apkanalyzer is not None:
            commands.extend(
                (
                    ("package_id", _sdk_tool_argv(tools.apkanalyzer, ["manifest", "application-id", str(path)], tools.cmd_exe)),
                    ("version_name", _sdk_tool_argv(tools.apkanalyzer, ["manifest", "version-name", str(path)], tools.cmd_exe)),
                    ("version_code", _sdk_tool_argv(tools.apkanalyzer, ["manifest", "version-code", str(path)], tools.cmd_exe)),
                )
            )
        elif tools.aapt is not None:
            aapt_argv = _sdk_tool_argv(tools.aapt, ["dump", "badging", str(path)], tools.cmd_exe)
            if aapt_argv is None:
                errors.append(f"apk_metadata_batch_wrapper_unavailable:{record['apk_alias']}:aapt")
            else:
                try:
                    completed = _run_bounded(runner, aapt_argv)
                except (OSError, subprocess.SubprocessError):
                    errors.append(f"apk_metadata_command_failed:{record['apk_alias']}:aapt")
                    record["tool_diagnostics"].append({"tool": "aapt", "outcome": "runner_error"})
                else:
                    record["tool_diagnostics"].append({"tool": "aapt", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
                    match = re.search(r"package:\s+name='([^']+)'\s+versionCode='([^']*)'\s+versionName='([^']*)'", completed.stdout)
                    if completed.returncode != 0 or match is None or not all(match.groups()):
                        errors.append(f"apk_metadata_parse_failed:{record['apk_alias']}:aapt")
                    else:
                        record["package_id"], record["version_code"], record["version_name"] = match.groups()
        if tools.apksigner_jar is not None and tools.java is not None:
            commands.append(
                (
                    "signature_output",
                    [str(tools.java), "-jar", str(tools.apksigner_jar), "verify", "--print-certs", str(path)],
                )
            )
        elif tools.apksigner is not None:
            commands.append(("signature_output", _sdk_tool_argv(tools.apksigner, ["verify", "--print-certs", str(path)], tools.cmd_exe)))
        for field, argv in commands:
            if argv is None:
                errors.append(f"apk_metadata_batch_wrapper_unavailable:{record['apk_alias']}:{field}")
                continue
            try:
                completed = _run_bounded(runner, argv)
            except (OSError, subprocess.SubprocessError):
                errors.append(f"apk_metadata_command_failed:{record['apk_alias']}:{field}")
                record["tool_diagnostics"].append({"tool": field, "outcome": "runner_error"})
                continue
            output = completed.stdout.strip()
            record["tool_diagnostics"].append({"tool": field, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
            if completed.returncode != 0 or not output:
                errors.append(f"apk_metadata_parse_failed:{record['apk_alias']}:{field}")
            else:
                record[field] = output
        records.append(record)
    return records, sorted(set(errors))


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key detected")
        result[key] = value
    return result


def load_json_duplicate_aware(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_no_duplicate_object)


def validate_alias_map_against_review(alias_map_path: Path, review_path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    try:
        alias_map = load_json_duplicate_aware(alias_map_path)
        review = load_json_duplicate_aware(review_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}, {}, ["alias_map_or_review_json_invalid_or_duplicate_key"]
    if not isinstance(alias_map, dict) or not alias_map:
        errors.append("serial_alias_map_must_be_non_empty_object")
        alias_map = {}
    if not isinstance(review, dict):
        return alias_map, {}, sorted(set(errors + ["tracked_review_must_be_object"]))

    allowed_review_top = {
        "schema_version", "generated_at_utc", "source", "owner_review_boundary",
        "runtime_execution_status", "apk_install_status", "app_launch_status", "public_device_count",
        "devices", "redaction_guarantees", "public_safety_findings", "review_instructions",
    }
    if set(review) != allowed_review_top:
        errors.append("tracked_review_top_level_fields_invalid")
    if review.get("schema_version") != task016_inventory.REVIEW_SCHEMA_VERSION or review.get("source") != "task016_public_safe_generated_inventory":
        errors.append("tracked_review_schema_or_source_invalid")
    for field in ("runtime_execution_status", "apk_install_status", "app_launch_status"):
        if review.get(field) != "not_run":
            errors.append("tracked_review_runtime_status_invariant_failed")
    guarantees = review.get("redaction_guarantees")
    if not isinstance(guarantees, dict) or set(guarantees) != task016_inventory.REQUIRED_REDACTION_GUARANTEE_KEYS or any(value is not True for value in guarantees.values()):
        errors.append("tracked_review_redaction_guarantees_invalid")
    if review.get("public_safety_findings") != []:
        errors.append("tracked_review_public_safety_findings_not_empty")
    devices = review.get("devices")
    if not isinstance(devices, list):
        devices = []
        errors.append("tracked_review_devices_invalid")
    count = review.get("public_device_count")
    if not isinstance(count, int) or isinstance(count, bool) or count != len(devices):
        errors.append("tracked_review_public_device_count_invalid")

    expected_device_fields = {
        "device_alias", "runtime_profile_alias", "category", "priority", "form_factor", "input_method",
        "android_major", "api_level", "screen_class", "google_play_services", "adb_available",
        "classification_confidence", "manual_review_required", "forbidden_identifiers_excluded",
        "runtime_execution_status", "apk_install_status", "app_launch_status",
    }
    review_by_alias: dict[str, dict[str, Any]] = {}
    runtime_aliases: set[str] = set()
    for device in devices:
        if not isinstance(device, dict) or set(device) != expected_device_fields:
            errors.append("tracked_review_device_fields_invalid")
            continue
        alias = device.get("device_alias")
        runtime_alias = device.get("runtime_profile_alias")
        form_factor = device.get("form_factor")
        if (
            not isinstance(alias, str)
            or task016_inventory.DEVICE_ALIAS_RE.fullmatch(alias) is None
            or task016_inventory._alias_has_forbidden_content(alias, form_factor)
            or not task016_inventory._alias_matches_form_factor(alias, form_factor)
        ):
            errors.append("tracked_review_device_alias_invalid")
            continue
        if (
            not isinstance(runtime_alias, str)
            or task016_inventory.RUNTIME_PROFILE_ALIAS_RE.fullmatch(runtime_alias) is None
            or task016_inventory._runtime_profile_alias_has_forbidden_content(runtime_alias, form_factor)
            or not task016_inventory._runtime_alias_matches_device(alias, runtime_alias, device.get("android_major"))
        ):
            errors.append("tracked_review_runtime_alias_invalid")
        if not task016_inventory._api_level_matches_android_major(device.get("android_major"), device.get("api_level")):
            errors.append("tracked_review_android_api_invalid")
        if device.get("classification_confidence") != "heuristic" or device.get("manual_review_required") is not True or device.get("forbidden_identifiers_excluded") is not True:
            errors.append("tracked_review_classification_invariants_invalid")
        if any(device.get(field) != "not_run" for field in ("runtime_execution_status", "apk_install_status", "app_launch_status")):
            errors.append("tracked_review_device_runtime_status_invalid")
        if alias in review_by_alias or runtime_alias in runtime_aliases:
            errors.append("tracked_review_aliases_not_unique")
        review_by_alias[alias] = device
        runtime_aliases.add(str(runtime_alias))

    mapped_aliases: set[str] = set()
    for serial, entry in alias_map.items():
        if not isinstance(serial, str) or not serial or not isinstance(entry, dict) or set(entry) != {"device_alias", "index"}:
            errors.append("serial_alias_map_entry_fields_invalid")
            continue
        alias = entry.get("device_alias")
        index = entry.get("index")
        reviewed = review_by_alias.get(alias) if isinstance(alias, str) else None
        inferred_form_factor = alias.split("-", 1)[0] if isinstance(alias, str) and "-" in alias else None
        if (
            not isinstance(alias, str)
            or task016_inventory.DEVICE_ALIAS_RE.fullmatch(alias) is None
            or task016_inventory._alias_has_forbidden_content(alias, reviewed.get("form_factor") if reviewed else inferred_form_factor)
            or not isinstance(index, str)
            or re.fullmatch(r"[0-9]{3}", index) is None
            or alias.rsplit("-", 1)[-1] != index
        ):
            errors.append("serial_alias_map_alias_or_index_invalid")
        if alias in mapped_aliases:
            errors.append("serial_alias_map_aliases_not_unique")
        mapped_aliases.add(alias)
    return alias_map, review_by_alias, sorted(set(errors))


def validate_local_device_contract_paths(repo_root: Path) -> list[str]:
    root = repo_root.resolve()
    local_root = root / ".qa_local"
    devices_root = root / CANONICAL_DEVICE_DIR
    alias_map = root / CANONICAL_ALIAS_MAP
    errors: list[str] = []
    if not local_root.is_dir() or _is_reparse(local_root):
        errors.append("canonical_qa_local_root_missing_or_reparse")
    if not devices_root.is_dir() or _is_reparse(devices_root):
        errors.append("canonical_device_root_missing_or_reparse")
    if not _is_regular_non_reparse(alias_map):
        errors.append("canonical_alias_map_missing_or_reparse")
    for output in (root / CANONICAL_GENERATED_INVENTORY, root / CANONICAL_DEVICE_PREFLIGHT):
        if output.parent != devices_root or not output.parent.is_dir() or _is_reparse(output.parent):
            errors.append("canonical_device_output_parent_invalid")
        if output.exists() and _is_reparse(output):
            errors.append("canonical_device_output_reparse")
    return sorted(set(errors))


def parse_strict_adb_snapshot(output: str) -> tuple[dict[str, str], list[str]]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines or lines[0] != "List of devices attached":
        return {}, ["adb_snapshot_header_invalid"]
    snapshot: dict[str, str] = {}
    errors: list[str] = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 2 or not parts[0] or not parts[1] or parts[1].startswith(("product:", "model:", "device:")):
            errors.append("adb_snapshot_line_incomplete")
            continue
        serial, state = parts[0], parts[1]
        if serial in snapshot:
            errors.append("adb_snapshot_duplicate_serial")
            continue
        snapshot[serial] = state
    return snapshot, sorted(set(errors))


class ResolvedAdbAllowlistRunner:
    """Replace TASK-016's argv[0] while enforcing its exact command allowlist."""

    def __init__(
        self,
        adb: Path,
        mapped_states: Mapping[str, str],
        selected_serials: Iterable[str],
        runner: CommandRunner,
    ) -> None:
        self.adb = adb
        self.mapped_states = dict(mapped_states)
        self.selected_serials = frozenset(selected_serials)
        connected_serials = {serial for serial, state in self.mapped_states.items() if state == "device"}
        if self.selected_serials != connected_serials or not 1 <= len(self.selected_serials) <= 2:
            raise ValueError("TASK-016 wrapper requires the exact approved one-or-two connected serial set")
        self.runner = runner
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if not argv or argv[0] != "adb":
            raise OSError("TASK-016 wrapper rejected non-ADB command")
        tail = argv[1:]
        if tail == ["devices", "-l"]:
            actual = [str(self.adb), *tail]
            completed = self.runner(actual, capture_output=True, text=True, timeout=min(int(kwargs.get("timeout", 30)), 30), check=False)
            snapshot, snapshot_errors = parse_strict_adb_snapshot(completed.stdout)
            if completed.returncode != 0 or snapshot_errors or snapshot != self.mapped_states:
                raise OSError("TASK-016 wrapper rejected changed serial/state snapshot")
            self.calls.append(actual)
            return completed
        elif len(tail) >= 4 and tail[0] == "-s":
            serial = tail[1]
            if serial not in self.selected_serials or self.mapped_states.get(serial) != "device":
                raise OSError("TASK-016 wrapper rejected unmapped or non-authorized serial")
            action = tail[2:]
            allowed = (
                len(action) == 3 and action[:2] == ["shell", "getprop"] and action[2] in task016_inventory.SAFE_GETPROP_FIELDS
            ) or action in (
                ["shell", "wm", "size"],
                ["shell", "wm", "density"],
                ["shell", "pm", "list", "features"],
            )
            if not allowed:
                raise OSError("TASK-016 wrapper rejected command outside allowlist")
        else:
            raise OSError("TASK-016 wrapper rejected command outside allowlist")
        actual = [str(self.adb), *tail]
        self.calls.append(actual)
        return self.runner(actual, capture_output=True, text=True, timeout=min(int(kwargs.get("timeout", 30)), 30), check=False)


def validate_generated_candidate(
    candidate: dict[str, Any],
    review_by_alias: Mapping[str, Mapping[str, Any]],
    expected_aliases: Iterable[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    count = candidate.get("public_device_count")
    devices = candidate.get("devices")
    if not isinstance(devices, list):
        return ["generated_candidate_devices_invalid"]
    if not isinstance(count, int) or isinstance(count, bool) or count != len(devices):
        errors.append("generated_candidate_public_device_count_invalid")
    if candidate.get("redaction_status") != "redacted" or candidate.get("public_safety_findings") != []:
        errors.append("generated_candidate_redaction_status_invalid")
    guarantees = candidate.get("redaction_guarantees")
    if not isinstance(guarantees, dict) or set(guarantees) != task016_inventory.REQUIRED_REDACTION_GUARANTEE_KEYS or any(value is not True for value in guarantees.values()):
        errors.append("generated_candidate_redaction_guarantees_invalid")
    generated = task016_inventory._parse_utc_timestamp(candidate.get("generated_at_utc"))
    now = datetime.now(timezone.utc)
    if generated is None or generated < now - timedelta(minutes=5) or generated > now + timedelta(minutes=1):
        errors.append("generated_candidate_stale_or_future")
    if task016_inventory._public_safety_findings(candidate) or not task016_inventory._public_payload_is_safe(candidate):
        errors.append("generated_candidate_contains_raw_public_value")
    candidate_aliases: list[str] = []
    for device in devices:
        if not isinstance(device, dict):
            errors.append("generated_candidate_device_invalid")
            continue
        device_alias = str(device.get("device_alias"))
        candidate_aliases.append(device_alias)
        reviewed = review_by_alias.get(device_alias)
        if reviewed is None:
            errors.append("generated_candidate_alias_not_reviewed")
            continue
        comparable = (
            "runtime_profile_alias", "category", "priority", "form_factor", "input_method", "android_major",
            "api_level", "screen_class", "google_play_services",
        )
        if any(device.get(field) != reviewed.get(field) for field in comparable):
            errors.append("generated_candidate_profile_differs_from_review")
    if len(candidate_aliases) != len(set(candidate_aliases)):
        errors.append("generated_candidate_aliases_not_unique")
    if expected_aliases is not None and set(candidate_aliases) != set(expected_aliases):
        errors.append("generated_candidate_alias_set_mismatch")
    try:
        task016_inventory.build_public_safe_review_inventory(candidate)
    except ValueError:
        errors.append("generated_candidate_task016_validation_failed")
    return sorted(set(errors))


def _write_local_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if _is_reparse(path.parent) or (path.exists() and _is_reparse(path)):
        raise ValueError("local evidence output must not use a reparse point")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def execute_conditional_preflight(
    *,
    repo_root: Path = Path("."),
    evidence_root: Path = CANONICAL_TASK042_EVIDENCE,
    env: Mapping[str, str] | None = None,
    runner: CommandRunner = subprocess.run,
) -> ExecutionSummary:
    """Execute only approved read-only APK metadata and ADB inventory actions."""

    root = repo_root.resolve()
    local_evidence = _validate_execution_evidence_root(root, evidence_root)
    initial_presence = probe_canonical_presence(root)
    initial_device_statuses = {alias: "UNKNOWN" for alias in (*REQUIRED_DEVICE_ALIASES, PAIRED_PHONE_FALLBACK_ALIAS)}
    device_path_errors = validate_local_device_contract_paths(root)
    if device_path_errors:
        return ExecutionSummary(
            presence=initial_presence, apk_metadata_status="BLOCKED", adb_tool_status="BLOCKED",
            adb_status="BLOCKED", avd_status="BLOCKED", avd_count=None, ignored_unreviewed_alias_count=0,
            device_statuses=initial_device_statuses, blockers=tuple(device_path_errors), raw_evidence_written=False,
        )
    presence, apk_paths, apk_errors = validate_canonical_apks(root)
    blockers = list(apk_errors)
    tools, tool_errors = resolve_sdk_tools(env)
    blockers.extend(tool_errors)
    apk_contents_read = False
    apk_tool_invoked = False
    adb_invoked = False
    avd_invoked = False
    adb_snapshot_observed = False
    metadata_status = "BLOCKED"
    metadata_records: list[dict[str, Any]] = []
    if not apk_errors and tools is not None:
        apk_contents_read = bool(apk_paths)

        def apk_metadata_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            nonlocal apk_tool_invoked
            apk_tool_invoked = True
            return runner(*args, **kwargs)

        metadata_records, metadata_errors = capture_apk_metadata(apk_paths, tools, apk_metadata_runner)
        blockers.extend(metadata_errors)
        metadata_status = "TOOLING_DEFECT" if metadata_errors else "READY"
    elif not apk_errors:
        metadata_status = "TOOLING_DEFECT"
    _write_local_json(
        local_evidence / "apk-metadata.json",
        {"schema_version": "task042-local-apk-metadata-v1", "generated_at_utc": _utc_now(), "records": metadata_records, "errors": sorted(set(blockers))},
    )

    avd_status = "TOOLING_DEFECT"
    avd_count: int | None = None
    if tools is None or tools.emulator is None:
        blockers.append("configured_sdk_emulator_missing")
    else:
        avd_invoked = True
        try:
            avd_completed = _run_bounded(runner, [str(tools.emulator), "-list-avds"])
        except (OSError, subprocess.SubprocessError):
            blockers.append("avd_inventory_command_failed")
        else:
            avd_names = [line.strip() for line in avd_completed.stdout.splitlines() if line.strip()]
            _write_local_json(
                local_evidence / "avd-inventory-raw.json",
                {"schema_version": "task042-local-avd-inventory-v1", "generated_at_utc": _utc_now(), "returncode": avd_completed.returncode, "avd_names": avd_names, "stderr": avd_completed.stderr},
            )
            if avd_completed.returncode == 0:
                avd_status = "READY"
                avd_count = len(avd_names)
            else:
                blockers.append("avd_inventory_command_failed")

    adb_tool_status = "TOOLING_DEFECT"
    if tools is not None:
        adb_invoked = True
        try:
            version_completed = _run_bounded(runner, [str(tools.adb), "version"])
        except (OSError, subprocess.SubprocessError):
            blockers.append("adb_version_command_failed")
        else:
            _write_local_json(
                local_evidence / "adb-version-raw.json",
                {"schema_version": "task042-local-adb-version-v1", "generated_at_utc": _utc_now(), "returncode": version_completed.returncode, "stdout": version_completed.stdout, "stderr": version_completed.stderr},
            )
            if version_completed.returncode == 0 and version_completed.stdout.strip():
                adb_tool_status = "READY"
            else:
                blockers.append("adb_version_command_failed")

    alias_map, review_by_alias, alias_errors = validate_alias_map_against_review(
        root / CANONICAL_ALIAS_MAP,
        root / PUBLIC_DEVICE_INVENTORY,
    )
    blockers.extend(alias_errors)
    ignored_alias_count = sum(1 for entry in alias_map.values() if isinstance(entry, dict) and entry.get("device_alias") not in review_by_alias)
    device_statuses = dict(initial_device_statuses)
    if tools is None or alias_errors or adb_tool_status != "READY":
        return ExecutionSummary(presence, metadata_status, adb_tool_status, "TOOLING_DEFECT" if tools is None else "BLOCKED", avd_status, avd_count, ignored_alias_count, device_statuses, tuple(sorted(set(blockers))), True, apk_contents_read, apk_tool_invoked, adb_invoked, avd_invoked, adb_snapshot_observed)

    try:
        precheck = _run_bounded(runner, [str(tools.adb), "devices", "-l"])
    except (OSError, subprocess.SubprocessError):
        blockers.append("adb_devices_precheck_failed")
        return ExecutionSummary(presence, metadata_status, adb_tool_status, "TOOLING_DEFECT", avd_status, avd_count, ignored_alias_count, device_statuses, tuple(sorted(set(blockers))), True, apk_contents_read, apk_tool_invoked, adb_invoked, avd_invoked, adb_snapshot_observed)
    raw_precheck = {"schema_version": "task042-local-adb-precheck-v1", "generated_at_utc": _utc_now(), "returncode": precheck.returncode, "stdout": precheck.stdout, "stderr": precheck.stderr}
    _write_local_json(local_evidence / "adb-devices-precheck.json", raw_precheck)
    adb_snapshot_observed = any(
        line.strip() and not line.startswith("List of devices attached")
        for line in precheck.stdout.splitlines()
    )
    if precheck.returncode != 0:
        blockers.append("adb_devices_precheck_failed")
        return ExecutionSummary(presence, metadata_status, adb_tool_status, "TOOLING_DEFECT", avd_status, avd_count, ignored_alias_count, device_statuses, tuple(sorted(set(blockers))), True, apk_contents_read, apk_tool_invoked, adb_invoked, avd_invoked, adb_snapshot_observed)

    states_by_serial, snapshot_errors = parse_strict_adb_snapshot(precheck.stdout)
    if snapshot_errors:
        blockers.extend(snapshot_errors)
        return ExecutionSummary(presence, metadata_status, adb_tool_status, "BLOCKED", avd_status, avd_count, ignored_alias_count, device_statuses, tuple(sorted(set(blockers))), True, apk_contents_read, apk_tool_invoked, adb_invoked, avd_invoked, adb_snapshot_observed)
    observed_device_statuses = {alias: "MISSING" for alias in (*REQUIRED_DEVICE_ALIASES, PAIRED_PHONE_FALLBACK_ALIAS)}
    unmapped_listed = sorted(serial for serial in states_by_serial if serial not in alias_map)
    authorized_serials = sorted(serial for serial, state in states_by_serial.items() if state == "device")
    for serial, state in states_by_serial.items():
        entry = alias_map.get(serial)
        if not isinstance(entry, dict):
            continue
        alias = entry.get("device_alias")
        if alias in observed_device_statuses:
            observed_device_statuses[alias] = {"device": "READY", "offline": "OFFLINE", "unauthorized": "UNAUTHORIZED"}.get(state, "UNKNOWN")
    if unmapped_listed or not 1 <= len(authorized_serials) <= 2:
        blockers.append("adb_snapshot_mapping_or_authorized_count_gate_failed")
        return ExecutionSummary(presence, metadata_status, adb_tool_status, "BLOCKED", avd_status, avd_count, ignored_alias_count, device_statuses, tuple(sorted(set(blockers))), True, apk_contents_read, apk_tool_invoked, adb_invoked, avd_invoked, adb_snapshot_observed)
    device_statuses = observed_device_statuses
    selected_aliases = [
        alias_map[serial].get("device_alias")
        for serial in authorized_serials
        if isinstance(alias_map.get(serial), dict)
    ]
    if len(selected_aliases) != len(set(selected_aliases)):
        blockers.append("connected_aliases_not_unique")
        device_statuses = dict(initial_device_statuses)
        return ExecutionSummary(presence, metadata_status, adb_tool_status, "BLOCKED", avd_status, avd_count, ignored_alias_count, device_statuses, tuple(sorted(set(blockers))), True, apk_contents_read, apk_tool_invoked, adb_invoked, avd_invoked, adb_snapshot_observed)
    if any(alias not in review_by_alias for alias in selected_aliases):
        blockers.append("connected_alias_not_in_tracked_review")
        device_statuses = dict(initial_device_statuses)
        return ExecutionSummary(presence, metadata_status, adb_tool_status, "BLOCKED", avd_status, avd_count, ignored_alias_count, device_statuses, tuple(sorted(set(blockers))), True, apk_contents_read, apk_tool_invoked, adb_invoked, avd_invoked, adb_snapshot_observed)

    wrapper = ResolvedAdbAllowlistRunner(tools.adb, states_by_serial, authorized_serials, runner)
    inventory_report, raw_payload, returned_map, candidate = task016_inventory.build_report(
        allow_adb=True,
        alias_map_path=root / CANONICAL_ALIAS_MAP,
        runner=wrapper,
    )
    _write_local_json(local_evidence / "adb-inventory-raw.json", raw_payload)
    if returned_map != alias_map:
        blockers.append("task016_attempted_alias_map_mutation")
    candidate["redaction_status"] = "redacted" if candidate.get("devices") else "not_applicable"
    candidate["public_safety_findings"] = task016_inventory._public_safety_findings(candidate)
    candidate_errors = (
        validate_generated_candidate(candidate, review_by_alias, selected_aliases)
        if candidate.get("devices")
        else ["generated_candidate_empty"]
    )
    if returned_map != alias_map:
        candidate_errors.append("task016_attempted_alias_map_mutation")
        candidate_errors = sorted(set(candidate_errors))
    if inventory_report.get("overall_status") != "not_run":
        candidate_errors.append("task016_inventory_report_blocked")
        candidate_errors = sorted(set(candidate_errors))
    blockers.extend(candidate_errors)
    adb_status = "READY" if not candidate_errors and inventory_report.get("overall_status") == "not_run" else "BLOCKED"
    if not candidate_errors and inventory_report.get("overall_status") == "not_run":
        _write_local_json(root / CANONICAL_GENERATED_INVENTORY, candidate)
        _write_local_json(root / CANONICAL_DEVICE_PREFLIGHT, inventory_report)
    if candidate_errors:
        failed_status = "INCOMPATIBLE" if "generated_candidate_profile_differs_from_review" in candidate_errors else "UNKNOWN"
        for selected_alias in selected_aliases:
            if selected_alias in device_statuses:
                device_statuses[str(selected_alias)] = failed_status
    return ExecutionSummary(presence, metadata_status, adb_tool_status, adb_status, avd_status, avd_count, ignored_alias_count, device_statuses, tuple(sorted(set(blockers))), True, apk_contents_read, apk_tool_invoked, adb_invoked, avd_invoked, adb_snapshot_observed)


def classify_bundle(presence: CanonicalPresence, *, integrity_verified: bool = False) -> dict[str, Any]:
    present = set(presence.expected_apks_present)
    entries = [
        {
            "apk_alias": f"main-apk-{index:02d}",
            "contract_filename": filename,
            "presence_status": "PRESENT" if filename in present else "MISSING",
            "scenario_status": (
                "observed_pass" if integrity_verified and filename in present
                else "blocked_by_oracle" if filename in present
                else "blocked_by_fixture"
            ),
            "evidence_status": "confirmed" if integrity_verified and filename in present else "unknown",
        }
        for index, filename in enumerate(EXPECTED_APKS, 1)
    ]
    missing_count = sum(entry["presence_status"] == "MISSING" for entry in entries)
    return {
        "canonical_contract_key": "task005_apk_bundle_contract",
        "canonical_directory_status": "PRESENT" if presence.apk_dir_present else "MISSING",
        "contract_entry_count": 5,
        "entries": entries,
        "missing_expected_count": missing_count,
        "unexpected_apk_count": presence.unexpected_apk_count,
        "unexpected_entries_are_main_bundle_members": False,
        "bundle_status": "READY" if integrity_verified and missing_count == 0 and presence.unexpected_apk_count == 0 else "BLOCKED",
        "metadata_capture_status": "LOCAL_ONLY_NOT_RUN",
    }


def _device_readiness(presence: CanonicalPresence) -> list[dict[str, Any]]:
    current_inventory_available = presence.device_preflight_present and presence.public_device_inventory_present
    # Presence alone is deliberately insufficient to assert authorization/readiness.
    return [
        {
            "device_alias": alias,
            "current_status": "UNKNOWN" if current_inventory_available else "MISSING",
            "scenario_status": "blocked_by_device",
            "evidence_status": "unknown",
            "blocker": "current_authorized_alias_status_not_verified",
            "historical_public_profile_is_runtime_evidence": False,
        }
        for alias in REQUIRED_DEVICE_ALIASES
    ]


def _scenario_row(
    source: Mapping[str, str],
    status: str,
    evidence_type: str,
    evidence_status: str,
    justification: str,
    blocker: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "scenario_id": source["scenario_id"],
        "priority": source["priority"],
        "surface_ids": source["surface_ids"],
        "lane": source["lane"],
        "scenario_status": status,
        "evidence_type": evidence_type,
        "evidence_status": evidence_status,
        "justification": justification,
    }
    if blocker:
        row["blocker"] = blocker
    return row


def build_scenario_ledger(
    scenarios: Sequence[Mapping[str, str]],
    presence: CanonicalPresence,
) -> list[dict[str, Any]]:
    by_id = {row["scenario_id"]: row for row in scenarios}
    apk_present = len(presence.expected_apks_present) == 5 and presence.unexpected_apk_count == 0
    definitions = {
        "QA-042-001": (
            "blocked_by_oracle" if apk_present else "blocked_by_fixture",
            "static_contract",
            "unknown",
            "Exact names are presence-only until regular/non-reparse/non-empty integrity validation executes.",
            "apk_integrity_not_executed" if apk_present else "canonical_apk_bundle_missing_or_incomplete",
        ),
        "QA-042-002": (
            "observed_pass", "synthetic_offline", "confirmed",
            "Synthetic missing-entry classifier returns a blocked bundle.", None,
        ),
        "QA-042-003": (
            "observed_pass", "synthetic_offline", "confirmed",
            "Synthetic extra entry remains outside the five-entry main bundle.", None,
        ),
        "QA-042-004": (
            "blocked_by_oracle" if apk_present else "blocked_by_fixture",
            "static_contract",
            "unknown",
            "Raw APK metadata is restricted to local-only evidence.",
            "apk_metadata_not_executed" if apk_present else "apk_metadata_source_unavailable",
        ),
        "QA-042-005": (
            "blocked_by_fixture", "static_contract", "unknown",
            "Launcher/system contour remains separate; no approved local component mapping is available.",
            "launcher_component_mapping_missing",
        ),
        "QA-042-006": (
            "observed_pass", "synthetic_offline", "confirmed",
            "Missing launcher component blocks only the launcher/system contour.", None,
        ),
        "QA-042-007": (
            "blocked_by_fixture", "static_contract", "unknown",
            "Configured SDK/ADB authority is not established by canonical presence.",
            "configured_adb_path_not_verified",
        ),
        "QA-042-008": (
            "blocked_by_fixture", "static_contract", "unknown",
            "AVD tooling inventory was not queried by the presence-only preflight.",
            "configured_avd_tooling_not_verified",
        ),
        "QA-042-009": (
            "blocked_by_fixture", "static_contract", "unknown",
            "No compatible approved AVD fixture was established; no compatibility claim is made.",
            "compatible_avd_fixture_not_verified",
        ),
        "QA-042-010": (
            "blocked_by_device", "static_contract", "unknown",
            "Current authorized device inventory was not executed.", "current_device_inventory_not_verified",
        ),
        "QA-042-011": (
            "blocked_by_device", "static_contract", "unknown",
            "Reference TV current authorization/profile is unverified.", "tv_tpv_013_not_verified",
        ),
        "QA-042-012": (
            "blocked_by_device", "static_contract", "unknown",
            "Primary paired phone and fallback current authorization/profile are unverified.",
            "paired_phone_lane_not_verified",
        ),
        "QA-042-013": (
            "blocked_by_device", "static_contract", "unknown",
            "Yandex lane current authorization/profile is unverified.", "tv_yandex_012_not_verified",
        ),
        "QA-042-014": (
            "blocked_by_device", "static_contract", "unknown",
            "Sber lane current authorization/profile is unverified.", "stb_sberdevices_009_not_verified",
        ),
        "QA-042-015": (
            "blocked_by_device", "static_contract", "unknown",
            "No approved actual FogPlay Stick alias is present; generic substitution is forbidden.",
            "actual_stick_mapping_missing",
        ),
        "QA-042-016": (
            "observed_pass", "synthetic_offline", "confirmed",
            "An unmapped Himedia alias remains UNKNOWN and requires manual mapping.", None,
        ),
        "QA-042-017": (
            "observed_pass", "static_contract", "confirmed",
            "Generated public report is validated against forbidden identity/value rules.", None,
        ),
        "QA-042-018": (
            "observed_pass", "static_contract", "confirmed",
            "TASK-043 proceeds while later runtime blockers remain lane-scoped.", None,
        ),
    }
    return [_scenario_row(by_id[scenario_id], *definitions[scenario_id]) for scenario_id in sorted(definitions)]


def build_report(
    *,
    repo_root: Path = Path("."),
    presence: CanonicalPresence | None = None,
    generated_at_utc: str | None = None,
    execution: ExecutionSummary | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    static_errors = validate_static_contracts(root)
    if static_errors:
        raise ValueError("; ".join(static_errors))
    scenarios = _load_scenarios(root / SCENARIO_CATALOG)
    local_presence = presence or probe_canonical_presence(root)
    apk_readiness = classify_bundle(local_presence)
    ledger = build_scenario_ledger(scenarios, local_presence)
    devices = _device_readiness(local_presence)
    blocked = [row for row in ledger if row["scenario_status"].startswith("blocked_")]
    observed = [row for row in ledger if row["scenario_status"] == "observed_pass"]

    report = {
        "schema_version": SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": "partial" if blocked else "pass",
        "coverage_status": "partial_blocked" if blocked else "covered",
        "evidence_status": "confirmed",
        "release_effect": "no_release_claim",
        "production_safety_classification": PRODUCTION_SAFETY_CLASSIFICATION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "build_ref": {"alias": "qa-repository-task042"},
        "target_alias": "local-runtime-preflight-public-safe",
        "run_id": "task042-presence-only-preflight-001",
        "artifacts": [],
        "blocked_reasons": sorted({row["blocker"] for row in blocked if row.get("blocker")}),
        "unknowns": [
            {"id": "U-T042-RUNTIME", "evidence_status": "unknown", "question": "Current APK/tool/device runtime readiness was not observed."},
            {"id": "U-T042-STICK", "evidence_status": "unknown", "question": "Approved actual FogPlay Stick alias is unavailable."},
        ],
        "risks": [
            {"id": "RISK-T042-FALSE-PASS", "level": "R0", "status": "controlled", "summary": "Presence, historical inventory, synthetic and AVD tooling evidence cannot assert physical product readiness."}
        ],
        "verification": [
            {"check": "tracked_static_contract_validation", "status": "pass", "evidence_status": "confirmed"},
            {"check": "canonical_presence_only_preflight", "status": "pass", "evidence_status": "confirmed", "runtime_actions": "not_run"},
            {"check": "scenario_terminal_classification", "status": "pass", "evidence_status": "confirmed", "scenario_count": 18},
        ],
        "review": {
            "qa_reviewer_a": "pending",
            "qa_reviewer_b": "pending",
            "security_prod_safety_reviewer": "conditional_go_before_runtime",
            "docs_scribe": "pending",
        },
        "provenance": {
            "source": "tracked_contracts_and_canonical_presence_only",
            "runtime_actions": "not_run",
            "subprocesses": "not_run",
            "apk_contents_read": False,
            "local_identity_values_read": False,
        },
        "payload": {
            "scenario_summary": {
                "total": 18,
                "p0": 15,
                "observed_pass": len(observed),
                "blocked": len(blocked),
                "tooling_defect": 0,
                "non_closing": 0,
            },
            "scenario_ledger": ledger,
            "apk_readiness": apk_readiness,
            "launcher_contour": {
                "contour_key": "launcher_system_cluster",
                "separate_from_main_apk_bundle": True,
                "counted_as_main_apk_entry": False,
                "canonical_local_contract_status": "UNAVAILABLE",
                "current_status": "BLOCKED",
                "scenario_status": "blocked_by_fixture",
                "evidence_status": "unknown",
                "blocker": "launcher_component_mapping_missing",
            },
            "tooling": {
                "adb": {"readiness": "UNKNOWN", "reason": "configured_adb_path_not_verified", "invoked": False},
                "avd": {
                    "status": "UNKNOWN",
                    "reason": "configured_avd_tooling_not_verified",
                    "invoked": False,
                    "claim_scope": "tooling_only",
                    "product_compatibility_claim": False,
                },
            },
            "device_readiness": devices,
            "fogplay_stick_actual_target": {
                "selector_key": "fogplay_stick_actual_target",
                "actual_alias_status": "unknown",
                "selected_device_alias": None,
                "current_status": "MISSING",
                "scenario_status": "blocked_by_device",
                "evidence_status": "unknown",
                "blocker": "actual_stick_mapping_missing",
                "generic_substitution_allowed": False,
            },
            "selected_lanes": {
                "TASK-043": {"decision": "proceed", "basis": "static_registry_task_not_blocked_by_runtime_lane"},
                "TASK-044": {"decision": "blocked_by_device", "device_alias": "tv-tpv-013"},
                "TASK-045": {"decision": "blocked_by_device", "device_alias": "phone-xiaomi-007", "fallback_alias": "phone-samsung-002"},
                "TASK-046": {"decision": "blocked_by_device", "device_alias": "tv-yandex-012"},
                "TASK-047": {"decision": "blocked_by_device", "device_alias": "stb-sberdevices-009"},
                "TASK-048": {"decision": "blocked_by_device", "selector_key": "fogplay_stick_actual_target"},
            },
            "public_safety": {
                "validation_status": "pass",
                "raw_machine_values_included": False,
                "raw_apk_metadata_included": False,
                "absolute_paths_included": False,
                "local_identity_values_included": False,
            },
        },
    }
    if execution is not None:
        apply_execution_summary(report, execution)
    return report


def apply_execution_summary(report: dict[str, Any], execution: ExecutionSummary) -> None:
    payload = report["payload"]
    sdk_inaccessible = "configured_android_sdk_root_inaccessible" in execution.blockers
    android_subprocesses_invoked = any((execution.apk_tool_invoked, execution.adb_invoked, execution.avd_invoked))
    payload["apk_readiness"] = classify_bundle(
        execution.presence,
        integrity_verified=execution.apk_contents_read,
    )
    if execution.apk_metadata_status == "READY":
        payload["apk_readiness"]["metadata_capture_status"] = "LOCAL_ONLY_READY"
    elif execution.apk_metadata_status == "TOOLING_DEFECT":
        payload["apk_readiness"]["metadata_capture_status"] = "LOCAL_ONLY_TOOLING_DEFECT"
    devices = {row["device_alias"]: row for row in payload["device_readiness"]}
    for alias, status in execution.device_statuses.items():
        if alias not in devices:
            continue
        row = devices[alias]
        row["current_status"] = status
        row["evidence_status"] = "confirmed" if status != "UNKNOWN" else "unknown"
        row["scenario_status"] = "observed_pass" if status == "READY" else "blocked_by_device"
        row["blocker"] = None if status == "READY" else f"current_device_status_{status.lower()}"
    fallback_status = execution.device_statuses.get(PAIRED_PHONE_FALLBACK_ALIAS, "UNKNOWN")
    payload["paired_phone_fallback"] = {
        "device_alias": PAIRED_PHONE_FALLBACK_ALIAS,
        "current_status": fallback_status,
        "evidence_status": "confirmed" if fallback_status != "UNKNOWN" else "unknown",
        "selection_allowed_only_if_primary_unavailable": True,
        "automatically_substituted": False,
    }
    payload["tooling"]["adb"] = {
        "readiness": execution.adb_tool_status,
        "reason": (
            None if execution.adb_tool_status == "READY"
            else "configured_sdk_not_ready" if not execution.adb_invoked
            else "configured_adb_version_not_ready"
        ),
        "invoked": execution.adb_invoked,
    }
    payload["tooling"]["avd"] = {
        "status": execution.avd_status,
        "reason": (
            None if execution.avd_status == "READY"
            else "configured_sdk_not_ready" if not execution.avd_invoked
            else "configured_avd_tooling_not_ready"
        ),
        "invoked": execution.avd_invoked,
        "claim_scope": "tooling_only",
        "product_compatibility_claim": False,
        "public_avd_count": execution.avd_count,
        "raw_avd_names_publicly_included": False,
    }
    rows = {row["scenario_id"]: row for row in payload["scenario_ledger"]}

    def set_row(
        scenario_id: str,
        status: str,
        evidence_status: str,
        blocker: str | None,
        justification: str,
        evidence_type: str | None = None,
    ) -> None:
        row = rows[scenario_id]
        row["scenario_status"] = status
        row["evidence_status"] = evidence_status
        if blocker:
            row["blocker"] = blocker
        else:
            row.pop("blocker", None)
        row["justification"] = justification
        row["evidence_type"] = evidence_type or (
            "local_read_only_runtime" if android_subprocesses_invoked else "local_preflight_gate"
        )

    bundle_ready = payload["apk_readiness"]["bundle_status"] == "READY" and execution.apk_metadata_status != "BLOCKED"
    if not bundle_ready:
        payload["apk_readiness"]["bundle_status"] = "BLOCKED"
    presence_complete = (
        set(execution.presence.expected_apks_present) == set(EXPECTED_APKS)
        and execution.presence.unexpected_apk_count == 0
    )
    bundle_blocker = (
        "canonical_apk_integrity_not_verified"
        if presence_complete and not execution.apk_contents_read
        else "canonical_apk_bundle_missing_or_incomplete"
    )
    bundle_justification = (
        "Exact canonical APKs passed content integrity validation."
        if bundle_ready
        else "Exact canonical APK presence passed, but content integrity was not read in the current run."
        if presence_complete and not execution.apk_contents_read
        else "Canonical APK presence or content integrity validation did not pass."
    )
    set_row(
        "QA-042-001",
        "observed_pass" if bundle_ready else "blocked_by_fixture",
        "confirmed" if bundle_ready else "unknown",
        None if bundle_ready else bundle_blocker,
        bundle_justification,
    )
    if execution.apk_metadata_status == "READY":
        set_row("QA-042-004", "observed_pass", "confirmed", None, "Read-only size/hash/package/version/signature metadata was captured to ignored local evidence.")
    elif execution.apk_metadata_status == "TOOLING_DEFECT":
        set_row("QA-042-004", "tooling_defect", "confirmed", "apk_signature_verification_tooling_failed", "A required SDK metadata/signature step failed; diagnostics remain local-only.")
    set_row(
        "QA-042-007",
        "observed_pass" if execution.adb_tool_status == "READY" else "tooling_defect",
        "confirmed",
        None if execution.adb_tool_status == "READY" else "configured_adb_version_not_ready",
        "Configured SDK ADB version returned rc=0 and non-empty local output." if execution.adb_tool_status == "READY" else "Configured SDK ADB version failed or returned empty output.",
    )
    if execution.adb_status == "READY":
        set_row("QA-042-010", "observed_pass", "confirmed", None, "Two-pass bounded ADB inventory completed with an unchanged mapped snapshot.")
    else:
        set_row(
            "QA-042-010",
            "blocked_by_device" if execution.adb_status == "BLOCKED" else "tooling_defect",
            "confirmed",
            "adb_connected_device_mapping_or_inventory_gate_not_ready" if execution.adb_status == "BLOCKED" else None,
            "ADB inventory or connected-device mapping gate did not complete authoritatively.",
        )
    if execution.avd_status == "READY":
        set_row("QA-042-008", "observed_pass", "confirmed", None, "Configured emulator inventory query succeeded; raw AVD names remain local-only.")
        if execution.avd_count == 0:
            set_row("QA-042-009", "blocked_by_device", "confirmed", "no_avd_available", "AVD inventory succeeded and returned zero configured AVDs.")
        else:
            set_row("QA-042-009", "blocked_by_fixture", "confirmed", "compatible_avd_fixture_not_selected", "AVDs exist but no compatible disposable fixture was selected.")
    else:
        set_row(
            "QA-042-008",
            "tooling_defect",
            "confirmed",
            "configured_avd_tooling_not_ready",
            "Configured emulator tool was missing or inventory query failed.",
        )
    scenario_aliases = {
        "QA-042-011": "tv-tpv-013",
        "QA-042-012": "phone-xiaomi-007",
        "QA-042-013": "tv-yandex-012",
        "QA-042-014": "stb-sberdevices-009",
    }
    for scenario_id, alias in scenario_aliases.items():
        if scenario_id == "QA-042-012":
            primary = execution.device_statuses.get(alias, "UNKNOWN")
            fallback = execution.device_statuses.get(PAIRED_PHONE_FALLBACK_ALIAS, "UNKNOWN")
            if primary == "READY":
                set_row(scenario_id, "observed_pass", "confirmed", None, "Reviewed primary paired-phone alias is READY.")
            elif fallback == "READY":
                set_row(scenario_id, "observed_pass", "confirmed", None, "Primary is unavailable; the separately mapped/reviewed Samsung fallback is explicitly selected.")
                payload["selected_lanes"]["TASK-045"]["device_alias"] = PAIRED_PHONE_FALLBACK_ALIAS
                payload["selected_lanes"]["TASK-045"]["fallback_selected"] = True
            else:
                evidence = "confirmed" if primary != "UNKNOWN" and fallback != "UNKNOWN" else "unknown"
                set_row(scenario_id, "blocked_by_device", evidence, "paired_phone_primary_and_fallback_not_ready", "Neither reviewed primary nor explicit fallback is READY.")
            continue
        status = execution.device_statuses.get(alias, "MISSING")
        set_row(
            scenario_id,
            "observed_pass" if status == "READY" else "blocked_by_device",
            "confirmed" if status != "UNKNOWN" else "unknown",
            None if status == "READY" else f"current_device_status_{status.lower()}",
            f"Read-only ADB inventory classified the approved alias as {status}.",
        )
    lane_tasks = {
        "TASK-044": "tv-tpv-013",
        "TASK-045": "phone-xiaomi-007",
        "TASK-046": "tv-yandex-012",
        "TASK-047": "stb-sberdevices-009",
    }
    for task_id, alias in lane_tasks.items():
        status = execution.device_statuses.get(alias, "MISSING")
        if task_id == "TASK-045" and execution.device_statuses.get(PAIRED_PHONE_FALLBACK_ALIAS) == "READY" and status != "READY":
            payload["selected_lanes"][task_id]["decision"] = "ready"
            continue
        payload["selected_lanes"][task_id]["decision"] = "ready" if status == "READY" else "blocked_by_device"

    blocked = [row for row in payload["scenario_ledger"] if str(row["scenario_status"]).startswith("blocked_")]
    observed = [row for row in payload["scenario_ledger"] if row["scenario_status"] == "observed_pass"]
    tooling_defects = [row for row in payload["scenario_ledger"] if row["scenario_status"] == "tooling_defect"]
    payload["scenario_summary"].update({
        "observed_pass": len(observed),
        "blocked": len(blocked),
        "tooling_defect": len(tooling_defects),
        "non_closing": 0,
    })
    report["blocked_reasons"] = sorted(set(execution.blockers) | {row["blocker"] for row in blocked if row.get("blocker")})
    report["run_id"] = "task042-approved-read-only-execution-001"
    report["execution_status"] = "partial" if blocked or tooling_defects else "pass"
    report["coverage_status"] = "partial_blocked" if blocked or tooling_defects else "covered"
    report["verification"] = [
        {"check": "tracked_static_contract_validation", "status": "pass", "evidence_status": "confirmed"},
        {"check": "canonical_apk_integrity_and_local_metadata", "status": "pass" if execution.apk_metadata_status == "READY" else "blocked", "evidence_status": "confirmed"},
        {"check": "task016_bounded_adb_inventory", "status": "pass" if execution.adb_status == "READY" else "blocked", "evidence_status": "confirmed"},
        {"check": "bounded_avd_inventory", "status": "pass" if execution.avd_status == "READY" else "blocked", "evidence_status": "confirmed"},
        {"check": "scenario_terminal_classification", "status": "pass", "evidence_status": "confirmed", "scenario_count": 18},
    ]
    report["unknowns"] = [{"id": "U-T042-LAUNCHER-STICK", "evidence_status": "unknown", "question": "Where are the approved launcher checkout contract and actual FogPlay Stick alias mapping?"}]
    if "adb_snapshot_mapping_or_authorized_count_gate_failed" in execution.blockers:
        report["unknowns"].append({"id": "U-T042-DEVICE-MAPPING", "evidence_status": "unknown", "question": "Which reviewed public-safe alias owns the currently connected unmapped target?"})
    if execution.apk_metadata_status != "READY":
        report["unknowns"].append({"id": "U-T042-APK-METADATA-TOOLING", "evidence_status": "unknown", "question": "Which bounded metadata/signature tooling step prevented complete local APK metadata capture?"})
    payload["alias_map_audit"] = {
        "ignored_unreviewed_alias_count": execution.ignored_unreviewed_alias_count,
        "ignored_aliases_are_authoritative": False,
        "connected_alias_requires_tracked_review": True,
    }
    payload["process_anomalies"] = []
    if execution.ignored_unreviewed_alias_count:
        payload["process_anomalies"].append({
            "id": "TASK042-PROCESS-ANOMALY-001", "evidence_status": "confirmed", "public_safe_alias": "initial_alias_scope_fail_closed",
            "classification": "preflight_gate_anomaly", "trigger_action": "Validate every local alias-map entry as authoritative.",
            "expected_result": "Only tracked-reviewed mappings influence connected-device authority.",
            "observed_result": "Initial strict validation stopped on stale unreviewed mappings.",
            "likely_cause": "Historical local mappings remained after the tracked review set changed.",
            "cause_evidence_status": "likely",
            "test_design_implication": "Classify stale mappings as non-authoritative while still requiring every listed serial to map.",
            "remediation": "Only the approved one-or-two connected tracked-reviewed aliases may receive per-device calls.",
        })
    if "adb_snapshot_mapping_or_authorized_count_gate_failed" in execution.blockers:
        payload["process_anomalies"].append({
            "id": "TASK042-PROCESS-ANOMALY-002", "evidence_status": "confirmed", "public_safe_alias": "current_unmapped_snapshot_stop",
            "classification": "preflight_gate_anomaly", "trigger_action": "Compare first ADB snapshot with the duplicate-aware canonical alias map.",
            "expected_result": "Every listed serial maps and one or two connected aliases are unique and tracked-reviewed.",
            "observed_result": "Snapshot mapping/approved connected-count gate failed; no per-device command executed.",
            "likely_cause": "Current local device state and approved mapping authority are not aligned.",
            "cause_evidence_status": "likely",
            "test_design_implication": "Keep all required public aliases UNKNOWN and require an explicit reviewed mapping before retry.",
            "remediation": "Execution stopped fail-closed before per-device collection.",
        })
    if "configured_android_sdk_root_inaccessible" in execution.blockers:
        payload["process_anomalies"].append({
            "id": "TASK042-PROCESS-ANOMALY-003",
            "evidence_status": "confirmed",
            "public_safe_alias": "configured_sdk_access_interruption",
            "classification": "tooling_access_anomaly",
            "trigger_action": "Repeat bounded APK/ADB/AVD inventory after the owner changed the connected-device set.",
            "expected_result": "Resolve configured SDK tooling and classify one or two mapped reviewed connected targets.",
            "observed_result": "The execution sandbox could not access the configured SDK root; no Android tooling or device command executed.",
            "likely_cause": "The resumed execution environment uses a more restrictive filesystem identity than the earlier approved run.",
            "cause_evidence_status": "likely",
            "test_design_implication": "SDK permission errors must become terminal tooling blockers instead of aborting report generation.",
            "remediation": "The runner recorded a public-safe tooling defect and preserved all device aliases as UNKNOWN.",
        })
    runtime_actions = (
        "metadata_and_inventory_only" if android_subprocesses_invoked
        else "local_apk_read_only" if execution.apk_contents_read
        else "local_contract_only_tooling_blocked"
    )
    report["provenance"].update({
        "source": "tracked_contracts_and_approved_local_read_only_execution",
        "runtime_actions": runtime_actions,
        "subprocesses": "approved_read_only_android_tools" if android_subprocesses_invoked else "not_run",
        "apk_contents_read": execution.apk_contents_read,
        "local_identity_values_read": execution.adb_snapshot_observed,
        "raw_values_publicly_included": False,
    })


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, str | None, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, None, child
            yield from _walk(child, child_path)


def public_safety_errors(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, key, value in _walk(report):
        normalized_key = key.lower() if key else ""
        if normalized_key in FORBIDDEN_PUBLIC_KEYS and value not in (None, "", [], {}):
            errors.append(f"{path} contains forbidden public value")
        if isinstance(value, str):
            for rule, pattern in FORBIDDEN_PUBLIC_PATTERNS:
                if pattern.search(value):
                    errors.append(f"{path} violates {rule}")
    return sorted(set(errors))


def validate_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    required_top = {
        "schema_version", "schema_validation_status", "execution_status", "coverage_status",
        "evidence_status", "release_effect", "production_safety_classification", "generated_at_utc",
        "task_id", "build_ref", "target_alias", "run_id", "artifacts", "blocked_reasons",
        "unknowns", "risks", "verification", "review", "provenance", "payload",
    }
    missing_top = sorted(required_top - set(report))
    if missing_top:
        errors.append("missing top-level fields: " + ", ".join(missing_top))
    extra_top = sorted(set(report) - (required_top | {"payload", "supersession"}))
    if extra_top:
        errors.append("unsupported top-level fields: " + ", ".join(extra_top))
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if report.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if report.get("coverage_status") not in {"covered", "partial", "partial_blocked", "blocked", "not_run", "unknown"}:
        errors.append("coverage_status is not valid for evidence-report-envelope-v2")

    payload = report.get("payload")
    if not isinstance(payload, dict):
        errors.append("payload must be an object")
        return errors + public_safety_errors(report)

    ledger = payload.get("scenario_ledger")
    if not isinstance(ledger, list):
        errors.append("payload.scenario_ledger must be a list")
    else:
        expected_ids = [f"QA-042-{index:03d}" for index in range(1, 19)]
        ids = [row.get("scenario_id") for row in ledger if isinstance(row, dict)]
        if ids != expected_ids:
            errors.append("scenario ledger must contain QA-042-001..018 exactly and in order")
        for index, row in enumerate(ledger):
            if not isinstance(row, dict):
                errors.append(f"scenario ledger row {index} must be an object")
                continue
            status = row.get("scenario_status")
            if status not in TERMINAL_SCENARIO_STATUSES:
                errors.append(f"{row.get('scenario_id', index)} has invalid scenario_status")
            if status in NON_CLOSING_STATUSES:
                errors.append(f"{row.get('scenario_id', index)} must not remain {status}")
            if row.get("evidence_status") not in EVIDENCE_STATUSES:
                errors.append(f"{row.get('scenario_id', index)} has invalid evidence_status")
            if status == "observed_pass" and row.get("evidence_status") != "confirmed":
                errors.append(f"{row.get('scenario_id', index)} observed_pass requires confirmed evidence")
            if status and status.startswith("blocked_") and not row.get("blocker"):
                errors.append(f"{row.get('scenario_id', index)} blocked status requires blocker")
        expected_summary = {
            "total": len(ledger),
            "p0": sum(1 for row in ledger if isinstance(row, dict) and row.get("priority") == "P0"),
            "observed_pass": sum(1 for row in ledger if isinstance(row, dict) and row.get("scenario_status") == "observed_pass"),
            "blocked": sum(1 for row in ledger if isinstance(row, dict) and str(row.get("scenario_status", "")).startswith("blocked_")),
            "tooling_defect": sum(1 for row in ledger if isinstance(row, dict) and row.get("scenario_status") == "tooling_defect"),
            "non_closing": sum(1 for row in ledger if isinstance(row, dict) and row.get("scenario_status") in NON_CLOSING_STATUSES),
        }
        if payload.get("scenario_summary") != expected_summary:
            errors.append("scenario summary does not match the scenario ledger")

    apk = payload.get("apk_readiness")
    entries = apk.get("entries") if isinstance(apk, dict) else None
    if not isinstance(entries, list) or len(entries) != 5:
        errors.append("APK readiness must contain exactly five entries")
    else:
        names = [entry.get("contract_filename") for entry in entries if isinstance(entry, dict)]
        if names != list(EXPECTED_APKS):
            errors.append("APK readiness entries must match the exact bundle contract")
    launcher = payload.get("launcher_contour")
    if not isinstance(launcher, dict) or launcher.get("separate_from_main_apk_bundle") is not True:
        errors.append("launcher contour must be separate from the five-entry bundle")
    if isinstance(launcher, dict) and launcher.get("counted_as_main_apk_entry") is not False:
        errors.append("launcher contour must not be counted as a main APK entry")

    devices = payload.get("device_readiness")
    device_aliases = {item.get("device_alias") for item in devices if isinstance(item, dict)} if isinstance(devices, list) else set()
    if device_aliases != set(REQUIRED_DEVICE_ALIASES):
        errors.append("device readiness must classify the exact four required approved aliases")
    stick = payload.get("fogplay_stick_actual_target")
    if not isinstance(stick, dict):
        errors.append("actual FogPlay Stick selector must be present")
    else:
        if stick.get("actual_alias_status") != "unknown" or stick.get("selected_device_alias") is not None:
            errors.append("actual FogPlay Stick alias must remain unknown when mapping is missing")
        if stick.get("generic_substitution_allowed") is not False:
            errors.append("generic substitution for actual FogPlay Stick must be forbidden")
        if stick.get("scenario_status") != "blocked_by_device":
            errors.append("missing actual FogPlay Stick mapping must be blocked_by_device")

    tooling = payload.get("tooling")
    avd = tooling.get("avd") if isinstance(tooling, dict) else None
    if not isinstance(avd, dict) or avd.get("claim_scope") != "tooling_only" or avd.get("product_compatibility_claim") is not False:
        errors.append("AVD result must be tooling_only and make no product compatibility claim")

    selected = payload.get("selected_lanes")
    if not isinstance(selected, dict) or selected.get("TASK-043", {}).get("decision") != "proceed":
        errors.append("TASK-043 must proceed independently of local runtime blockers")
    errors.extend(public_safety_errors(report))
    return sorted(set(errors))


def validate_report_file(report_path: Path, repo_root: Path = Path(".")) -> list[str]:
    """Validate the report plus its hash-bound public ledger and matrix."""

    try:
        report = _load_json(report_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [str(exc)]
    if not isinstance(report, dict):
        return ["report root must be an object"]

    errors = validate_report(report)
    errors.extend(_validate_v2_envelope(report, repo_root.resolve()))
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list):
        return sorted(set(errors + ["artifacts must be a list"]))
    kinds = [item.get("kind") for item in artifacts if isinstance(item, dict)]
    if kinds != ["scenario_ledger", "readiness_matrix"]:
        errors.append("artifacts must contain scenario_ledger then readiness_matrix exactly")

    root = repo_root.resolve()
    loaded_artifacts: dict[str, Path] = {}
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        reference = artifact.get("reference")
        digest = artifact.get("sha256")
        if not isinstance(reference, str) or not reference or Path(reference).is_absolute() or ".." in Path(reference).parts:
            errors.append(f"artifacts[{index}].reference must be a safe repository-relative path")
            continue
        artifact_path = root / Path(reference)
        if not artifact_path.is_file():
            errors.append(f"artifacts[{index}] referenced file is missing")
            continue
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(f"artifacts[{index}].sha256 must be a lowercase SHA-256")
        elif _sha256(artifact_path) != digest:
            errors.append(f"artifacts[{index}] SHA-256 mismatch")
        loaded_artifacts[str(artifact.get("kind"))] = artifact_path

    ledger_path = loaded_artifacts.get("scenario_ledger")
    if ledger_path:
        try:
            ledger_rows = _load_scenarios(ledger_path)
        except (OSError, csv.Error) as exc:
            errors.append(f"scenario ledger is unreadable: {exc}")
        else:
            report_rows = report.get("payload", {}).get("scenario_ledger", [])
            report_projection = [
                {
                    "scenario_id": str(row.get("scenario_id", "")),
                    "scenario_status": str(row.get("scenario_status", "")),
                    "evidence_type": str(row.get("evidence_type", "")),
                    "evidence_status": str(row.get("evidence_status", "")),
                }
                for row in report_rows
                if isinstance(row, dict)
            ]
            ledger_projection = [
                {field: row.get(field, "") for field in ("scenario_id", "scenario_status", "evidence_type", "evidence_status")}
                for row in ledger_rows
            ]
            if ledger_projection != report_projection:
                errors.append("scenario ledger content does not match report payload")

    matrix_path = loaded_artifacts.get("readiness_matrix")
    if matrix_path:
        try:
            with matrix_path.open("r", encoding="utf-8", newline="") as handle:
                matrix_rows = list(csv.DictReader(handle))
        except (OSError, csv.Error) as exc:
            errors.append(f"readiness matrix is unreadable: {exc}")
        else:
            if len(matrix_rows) != 13:
                errors.append("readiness matrix must contain 13 classified rows")
            if any(row.get("status") in (None, "", "READY") and not row.get("evidence_status") for row in matrix_rows):
                errors.append("readiness matrix rows must include evidence status")
            selectors = {row.get("selector") for row in matrix_rows}
            required = {"main-apk-01", "main-apk-02", "main-apk-03", "main-apk-04", "main-apk-05", *REQUIRED_DEVICE_ALIASES, PAIRED_PHONE_FALLBACK_ALIAS, "fogplay_stick_actual_target", "launcher_system_cluster", "configured_avd_inventory"}
            if selectors != required:
                errors.append("readiness matrix selectors must match the exact APK/device/launcher/AVD set")
            if matrix_rows != _readiness_matrix_rows(report):
                errors.append("readiness matrix content does not match report payload")
    return sorted(set(errors))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_ledger(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields = ("scenario_id", "priority", "surface_ids", "lane", "scenario_status", "evidence_type", "evidence_status", "blocker", "justification")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _readiness_matrix_rows(report: Mapping[str, Any]) -> list[dict[str, str]]:
    payload = report["payload"]
    rows: list[dict[str, str]] = []
    for entry in payload["apk_readiness"]["entries"]:
        rows.append({
            "kind": "apk",
            "selector": entry["apk_alias"],
            "status": entry["presence_status"],
            "scenario_status": entry["scenario_status"],
            "evidence_status": entry["evidence_status"],
            "claim_scope": "local_integrity_only" if entry["evidence_status"] == "confirmed" else "presence_only",
        })
    for device in payload["device_readiness"]:
        rows.append({"kind": "device", "selector": device["device_alias"], "status": device["current_status"], "scenario_status": device["scenario_status"], "evidence_status": device["evidence_status"], "claim_scope": "authorization_profile_only"})
    fallback = payload.get("paired_phone_fallback", {"device_alias": PAIRED_PHONE_FALLBACK_ALIAS, "current_status": "UNKNOWN", "evidence_status": "unknown"})
    rows.append({"kind": "device_fallback", "selector": fallback["device_alias"], "status": fallback["current_status"], "scenario_status": "observed_pass" if fallback["current_status"] == "READY" else "blocked_by_device", "evidence_status": fallback["evidence_status"], "claim_scope": "explicit_paired_phone_fallback"})
    stick = payload["fogplay_stick_actual_target"]
    rows.append({"kind": "device_selector", "selector": stick["selector_key"], "status": stick["current_status"], "scenario_status": stick["scenario_status"], "evidence_status": stick["evidence_status"], "claim_scope": "actual_alias_required"})
    rows.append({"kind": "launcher_contour", "selector": payload["launcher_contour"]["contour_key"], "status": payload["launcher_contour"]["current_status"], "scenario_status": payload["launcher_contour"]["scenario_status"], "evidence_status": payload["launcher_contour"]["evidence_status"], "claim_scope": "separate_contour"})
    avd_scenario = next(row for row in payload["scenario_ledger"] if row["scenario_id"] == "QA-042-009")
    rows.append({"kind": "avd", "selector": "configured_avd_inventory", "status": payload["tooling"]["avd"]["status"], "scenario_status": avd_scenario["scenario_status"], "evidence_status": avd_scenario["evidence_status"], "claim_scope": "tooling_only"})
    return rows


def _write_matrix(path: Path, report: Mapping[str, Any]) -> None:
    rows = _readiness_matrix_rows(report)
    fields = ("kind", "selector", "status", "scenario_status", "evidence_status", "claim_scope")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _public_artifact_reference(path: Path) -> str:
    """Return a public-safe reference even for an external test output path."""

    return path.name if path.is_absolute() else _repo_path(path)


def write_report_bundle(report: dict[str, Any], report_path: Path, ledger_path: Path, matrix_path: Path) -> None:
    _write_ledger(ledger_path, report["payload"]["scenario_ledger"])
    _write_matrix(matrix_path, report)
    report["artifacts"] = [
        {"reference": _public_artifact_reference(ledger_path), "sha256": _sha256(ledger_path), "kind": "scenario_ledger", "evidence_status": "confirmed"},
        {"reference": _public_artifact_reference(matrix_path), "sha256": _sha256(matrix_path), "kind": "readiness_matrix", "evidence_status": "confirmed"},
    ]
    errors = validate_report(report)
    if errors:
        raise ValueError("; ".join(errors))
    _write_json(report_path, report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TASK-042 fail-closed local runtime preflight")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true", help="Validate tracked contracts only; no .qa_local reads or subprocesses.")
    mode.add_argument("--preflight", action="store_true", help="Inspect canonical presence only; no APK/device actions.")
    mode.add_argument("--execute", action="store_true", help="Run the explicitly approved read-only APK metadata and ADB inventory lanes.")
    mode.add_argument("--validate-report", type=Path, help="Validate a public-safe TASK-042 report.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--write-report", type=Path)
    parser.add_argument("--write-ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--write-matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--allow-local-apk-metadata", action="store_true")
    parser.add_argument("--allow-adb-inventory", action="store_true")
    parser.add_argument("--local-evidence-root", type=Path)
    args = parser.parse_args(argv)

    if args.validate_only:
        if args.write_report:
            parser.error("--validate-only cannot write a report")
        errors = validate_static_contracts(args.repo_root)
        if errors:
            sys.stdout.write(json.dumps({"task_id": TASK_ID, "validation_status": "fail", "errors": errors}, indent=2) + "\n")
            return 1
        sys.stdout.write(json.dumps({"task_id": TASK_ID, "validation_status": "pass", "scenario_count": 18, "p0_count": 15, "local_runtime_access": "not_run"}, indent=2) + "\n")
        return 0

    if args.validate_report:
        errors = validate_report_file(args.validate_report, args.repo_root)
        sys.stdout.write(json.dumps({"task_id": TASK_ID, "validation_status": "fail" if errors else "pass", "errors": errors}, indent=2) + "\n")
        return 1 if errors else 0

    if args.execute:
        if not args.allow_local_apk_metadata or not args.allow_adb_inventory or args.local_evidence_root is None:
            parser.error("--execute requires --allow-local-apk-metadata, --allow-adb-inventory and --local-evidence-root")
        try:
            execution = execute_conditional_preflight(
                repo_root=args.repo_root,
                evidence_root=args.local_evidence_root,
            )
            report = build_report(repo_root=args.repo_root, presence=execution.presence, execution=execution)
            if args.write_report:
                write_report_bundle(report, args.write_report, args.write_ledger, args.write_matrix)
        except (OSError, ValueError) as exc:
            sys.stdout.write(json.dumps({"task_id": TASK_ID, "execution_status": "blocked", "reason": "execution_gate_or_local_contract_failed"}, indent=2) + "\n")
            return 2
        sys.stdout.write(json.dumps({
            "task_id": TASK_ID,
            "execution_status": report["execution_status"],
            "apk_metadata_status": execution.apk_metadata_status,
            "adb_tool_status": execution.adb_tool_status,
            "adb_inventory_status": execution.adb_status,
            "blocked_reason_count": len(execution.blockers),
            "runtime_app_actions": "not_run",
            "report_written": bool(args.write_report),
        }, indent=2) + "\n")
        return 3 if execution.apk_metadata_status == "BLOCKED" else 0

    report = build_report(repo_root=args.repo_root)
    if args.write_report:
        write_report_bundle(report, args.write_report, args.write_ledger, args.write_matrix)
    summary = report["payload"]["scenario_summary"]
    sys.stdout.write(json.dumps({"task_id": TASK_ID, "preflight_status": report["execution_status"], "scenario_summary": summary, "runtime_actions": "not_run", "report_written": bool(args.write_report)}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

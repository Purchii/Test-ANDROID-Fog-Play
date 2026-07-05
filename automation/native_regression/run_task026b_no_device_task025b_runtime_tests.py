"""TASK-026B no-device TASK-025B physical runtime test scenarios.

This module implements the future TASK-025B scenario contract without device
execution. It can prove sequencing with an in-memory fake driver, but it never
creates runtime evidence and never promotes TASK-025B to passed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from automation.native_regression.run_task025_selected_lane_regression import (
    FORBIDDEN_BOUNDARY_CATEGORIES,
    NO_DEVICE_EXECUTION_MODE,
    REQUIRED_CASE_IDS,
    SYNTHETIC_EXECUTION_MODE,
    SyntheticRuntimeDriver,
    RuntimeDriver,
    default_blocked_report,
    load_json_object,
    public_safety_findings,
    validate_output_path,
    validate_report_shape,
)


SCENARIO_SCHEMA_VERSION = "task025b-runtime-scenarios-v1"
TASK026B_REPORT_SCHEMA_VERSION = "task026b-task025b-runtime-tests-summary-v1"
DEFAULT_SCENARIOS = Path("docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json")
DEFAULT_TEMPLATE = Path("docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json")

ALLOWED_ACTIONS = {
    "launch_app",
    "ensure_authorized_session",
    "classify_screen",
    "assert_focus_present",
    "press_dpad",
    "press_back",
    "press_home",
    "foreground_app",
    "force_stop_relaunch",
    "assert_session_preserved",
    "classify_boundary",
    "record_public_safe_evidence_ref",
}
BOUNDARY_ACTIONS = {"classify_boundary", "record_public_safe_evidence_ref"}
FORBIDDEN_SCENARIO_ACTIONS = {
    "press_ok_on_boundary",
    "follow_qr",
    "open_webview",
    "start_stream",
    "start_payment",
    "mutate_profile",
    "toggle_network",
}


@dataclass
class ScenarioExecution:
    case_id: str
    status: str
    execution_mode: str
    counts_as_runtime_evidence: bool
    runtime_evidence_ids: list[str]
    action_log: list[str] = field(default_factory=list)
    guarded_boundaries: list[str] = field(default_factory=list)
    reason: str = "Synthetic sequencing only; physical TASK-025B runtime remains deferred."


def _scenario_steps(case: dict[str, Any]) -> list[dict[str, Any]]:
    steps = case.get("steps")
    if not isinstance(steps, list):
        return []
    return [step for step in steps if isinstance(step, dict)]


def validate_scenarios(scenarios: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if scenarios.get("schema_version") != SCENARIO_SCHEMA_VERSION:
        reasons.append(f"schema_version must be {SCENARIO_SCHEMA_VERSION}.")
    if scenarios.get("task_id") != "TASK-025B":
        reasons.append("task_id must be TASK-025B.")
    if scenarios.get("runtime_execution_status") != "not_run":
        reasons.append("runtime_execution_status must be not_run.")
    if scenarios.get("execution_policy") != "future_physical_runtime_gated":
        reasons.append("execution_policy must be future_physical_runtime_gated.")
    if scenarios.get("boundary_guard_categories") != list(FORBIDDEN_BOUNDARY_CATEGORIES):
        reasons.append("boundary_guard_categories must match the TASK-025 forbidden boundary category allowlist.")

    cases = scenarios.get("scenarios")
    if not isinstance(cases, list):
        return sorted(set(reasons + ["scenarios must be a list."]))

    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            reasons.append(f"scenarios[{index}] must be an object.")
            continue
        case_id = case.get("case_id")
        if case_id in seen:
            reasons.append(f"scenarios[{index}].case_id is duplicated.")
        if not isinstance(case_id, str) or case_id not in REQUIRED_CASE_IDS:
            reasons.append(f"scenarios[{index}].case_id is not recognized.")
        else:
            seen.add(case_id)
        if not isinstance(case.get("title"), str) or not case["title"].strip():
            reasons.append(f"scenarios[{index}].title is required.")
        if case.get("future_runtime_gate") != "requires_confirmed_task025b_preflight":
            reasons.append(f"scenarios[{index}].future_runtime_gate must require confirmed TASK-025B preflight.")
        if case.get("default_no_device_status") not in {"not_run", "blocked", "deferred"}:
            reasons.append(f"scenarios[{index}].default_no_device_status must be not_run, blocked or deferred.")

        boundary_policy = case.get("boundary_policy")
        if not isinstance(boundary_policy, dict):
            reasons.append(f"scenarios[{index}].boundary_policy must be an object.")
        else:
            if boundary_policy.get("boundary_actions") != "classify_only":
                reasons.append(f"scenarios[{index}].boundary_policy.boundary_actions must be classify_only.")
            if boundary_policy.get("boundary_entered") is not False:
                reasons.append(f"scenarios[{index}].boundary_policy.boundary_entered must be false.")
            forbidden_actions = boundary_policy.get("forbidden_actions")
            if not isinstance(forbidden_actions, list) or sorted(forbidden_actions) != sorted(FORBIDDEN_SCENARIO_ACTIONS):
                reasons.append(f"scenarios[{index}].boundary_policy.forbidden_actions must match the forbidden action allowlist.")

        steps = _scenario_steps(case)
        if not steps:
            reasons.append(f"scenarios[{index}].steps must be a non-empty list.")
        has_boundary_step = False
        for step_index, step in enumerate(steps):
            action = step.get("action")
            if action not in ALLOWED_ACTIONS:
                reasons.append(f"scenarios[{index}].steps[{step_index}].action is not allowed.")
            if action in FORBIDDEN_SCENARIO_ACTIONS:
                reasons.append(f"scenarios[{index}].steps[{step_index}].action is forbidden.")
            if action in BOUNDARY_ACTIONS:
                has_boundary_step = True
            if action == "press_ok":
                reasons.append(f"scenarios[{index}].steps[{step_index}].action is forbidden; use boundary classification instead.")
            if action == "press_dpad" and step.get("direction") not in {"up", "down", "left", "right"}:
                reasons.append(f"scenarios[{index}].steps[{step_index}].direction must be up/down/left/right.")
        if case_id in {"NR-008", "NR-009"} and not has_boundary_step:
            reasons.append(f"scenarios[{index}] {case_id} must include a boundary classification step.")

    missing = sorted(REQUIRED_CASE_IDS - seen)
    if missing:
        reasons.append(f"scenarios missing required cases: {missing}.")
    reasons.extend(public_safety_findings(scenarios))
    return sorted(set(reasons))


def _run_step(driver: RuntimeDriver, step: dict[str, Any]) -> str | None:
    action = step["action"]
    if action == "launch_app":
        driver.launch_app()
    elif action == "ensure_authorized_session":
        driver.ensure_authorized_session()
    elif action == "classify_screen":
        driver.classify_screen()
    elif action == "assert_focus_present":
        driver.assert_focus_present()
    elif action == "press_dpad":
        driver.press_dpad(step["direction"])
    elif action == "press_back":
        driver.press_back()
    elif action == "press_home":
        driver.press_home()
    elif action == "foreground_app":
        driver.foreground_app()
    elif action == "force_stop_relaunch":
        driver.force_stop_relaunch()
    elif action == "assert_session_preserved":
        driver.assert_session_preserved()
    elif action == "classify_boundary":
        return driver.classify_boundary()
    elif action == "record_public_safe_evidence_ref":
        driver.record_public_safe_evidence_ref("scenario-contract-only")
    return None


def run_synthetic_scenarios(scenarios: dict[str, Any], driver: SyntheticRuntimeDriver | None = None) -> list[dict[str, Any]]:
    fake_driver = driver or SyntheticRuntimeDriver()
    executions: list[dict[str, Any]] = []
    for case in scenarios["scenarios"]:
        before = len(fake_driver.action_log)
        guarded_boundaries: list[str] = []
        for step in _scenario_steps(case):
            boundary = _run_step(fake_driver, step)
            if boundary:
                guarded_boundaries.append(boundary)
        executions.append(
            {
                "case_id": case["case_id"],
                "status": "blocked",
                "execution_mode": SYNTHETIC_EXECUTION_MODE,
                "counts_as_runtime_evidence": False,
                "runtime_evidence_ids": [],
                "action_log": fake_driver.action_log[before:],
                "guarded_boundaries": guarded_boundaries,
                "reason": "Synthetic sequencing only; physical TASK-025B runtime remains deferred.",
            }
        )
    return executions


def build_report(scenarios: dict[str, Any], *, synthetic_sequencing_test: bool = False) -> dict[str, Any]:
    report = default_blocked_report("TASK-025B physical runtime scenarios implemented; execution deferred without device and approvals")
    report["task_id"] = "TASK-026B"
    report["task026b_report_schema_version"] = TASK026B_REPORT_SCHEMA_VERSION
    report["task026b_status"] = "implementation_ready_no_device"
    report["task025b_runtime_scenarios"] = {
        "schema_version": scenarios.get("schema_version"),
        "scenario_source": DEFAULT_SCENARIOS.as_posix(),
        "scenario_count": len(scenarios.get("scenarios", [])) if isinstance(scenarios.get("scenarios"), list) else 0,
        "default_no_device_status": "blocked_not_run_deferred",
        "future_runtime_gate": "requires_confirmed_task025b_preflight",
        "synthetic_sequencing_status": "not_run",
        "counts_as_runtime_evidence": False,
        "runtime_evidence_ids": [],
        "boundary_guard_categories": list(FORBIDDEN_BOUNDARY_CATEGORIES),
        "case_statuses": [
            {
                "case_id": case.get("case_id"),
                "status": "not_run",
                "execution_mode": NO_DEVICE_EXECUTION_MODE,
                "counts_as_runtime_evidence": False,
                "runtime_evidence_ids": [],
                "reason": "Scenario implemented for future TASK-025B; physical execution deferred.",
            }
            for case in scenarios.get("scenarios", [])
            if isinstance(case, dict)
        ],
        "synthetic_executions": [],
    }
    if synthetic_sequencing_test:
        report["execution_mode"] = SYNTHETIC_EXECUTION_MODE
        report["synthetic_contract"] = {
            "contract_status": "pass",
            "screen_alias": "task025b_scenario_contract",
            "boundary_category": "payment/subscription/purchase",
            "synthetic_ref": "synthetic-only:task025b-scenario-contract",
            "counts_as_runtime_evidence": False,
        }
        report["task025b_runtime_scenarios"]["synthetic_sequencing_status"] = "pass"
        report["task025b_runtime_scenarios"]["synthetic_executions"] = run_synthetic_scenarios(scenarios)
        report["synthetic_contract_tests"].append(
            {
                "contract_id": "SYN-026B",
                "title": "TASK-025B physical runtime scenario sequencing contract",
                "status": "pass",
                "evidence_status": "confirmed",
                "execution_mode": SYNTHETIC_EXECUTION_MODE,
                "counts_as_runtime_evidence": False,
                "runtime_evidence_ids": [],
                "reason": "In-memory fake scenario sequencing only; no app/device/APK runtime evidence was produced.",
            }
        )
    return report


def validate_task026b_report(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if report.get("task_id") != "TASK-026B":
        reasons.append("task_id must be TASK-026B for TASK-026B reports.")
    task025_compatible = dict(report)
    task025_compatible["task_id"] = "TASK-025A"
    reasons.extend(validate_report_shape(task025_compatible))
    section = report.get("task025b_runtime_scenarios")
    if not isinstance(section, dict):
        return sorted(set(reasons + ["task025b_runtime_scenarios must be an object."]))
    if report.get("task026b_report_schema_version") != TASK026B_REPORT_SCHEMA_VERSION:
        reasons.append(f"task026b_report_schema_version must be {TASK026B_REPORT_SCHEMA_VERSION}.")
    if report.get("task026b_status") != "implementation_ready_no_device":
        reasons.append("task026b_status must be implementation_ready_no_device.")
    if section.get("schema_version") != SCENARIO_SCHEMA_VERSION:
        reasons.append(f"task025b_runtime_scenarios.schema_version must be {SCENARIO_SCHEMA_VERSION}.")
    if section.get("scenario_count") != len(REQUIRED_CASE_IDS):
        reasons.append("task025b_runtime_scenarios.scenario_count must match required TASK-025B case count.")
    if section.get("default_no_device_status") != "blocked_not_run_deferred":
        reasons.append("task025b_runtime_scenarios.default_no_device_status must be blocked_not_run_deferred.")
    if section.get("synthetic_sequencing_status") not in {"not_run", "pass"}:
        reasons.append("task025b_runtime_scenarios.synthetic_sequencing_status must be not_run or pass.")
    if section.get("runtime_evidence_ids") != []:
        reasons.append("task025b_runtime_scenarios.runtime_evidence_ids must be empty.")
    if section.get("counts_as_runtime_evidence") is not False:
        reasons.append("task025b_runtime_scenarios.counts_as_runtime_evidence must be false.")
    if section.get("future_runtime_gate") != "requires_confirmed_task025b_preflight":
        reasons.append("task025b_runtime_scenarios.future_runtime_gate must require confirmed TASK-025B preflight.")
    if section.get("boundary_guard_categories") != list(FORBIDDEN_BOUNDARY_CATEGORIES):
        reasons.append("task025b_runtime_scenarios.boundary_guard_categories must match the forbidden boundary allowlist.")
    case_statuses = section.get("case_statuses")
    if not isinstance(case_statuses, list):
        reasons.append("task025b_runtime_scenarios.case_statuses must be a list.")
    else:
        seen: set[str] = set()
        for index, case in enumerate(case_statuses):
            if not isinstance(case, dict):
                reasons.append(f"task025b_runtime_scenarios.case_statuses[{index}] must be an object.")
                continue
            case_id = case.get("case_id")
            if case_id in seen:
                reasons.append(f"task025b_runtime_scenarios.case_statuses[{index}].case_id is duplicated.")
            if case_id in REQUIRED_CASE_IDS:
                seen.add(case_id)
            else:
                reasons.append(f"task025b_runtime_scenarios.case_statuses[{index}].case_id is not recognized.")
            if case.get("status") not in {"not_run", "blocked", "deferred"}:
                reasons.append(f"task025b_runtime_scenarios.case_statuses[{index}].status must remain not_run/blocked/deferred.")
            if case.get("counts_as_runtime_evidence") is not False:
                reasons.append(f"task025b_runtime_scenarios.case_statuses[{index}].counts_as_runtime_evidence must be false.")
            if case.get("runtime_evidence_ids") != []:
                reasons.append(f"task025b_runtime_scenarios.case_statuses[{index}].runtime_evidence_ids must be empty.")
        missing = sorted(REQUIRED_CASE_IDS - seen)
        if missing:
            reasons.append(f"task025b_runtime_scenarios.case_statuses missing required cases: {missing}.")
    executions = section.get("synthetic_executions")
    if not isinstance(executions, list):
        reasons.append("task025b_runtime_scenarios.synthetic_executions must be a list.")
    else:
        for index, execution in enumerate(executions):
            if not isinstance(execution, dict):
                reasons.append(f"task025b_runtime_scenarios.synthetic_executions[{index}] must be an object.")
                continue
            if execution.get("execution_mode") != SYNTHETIC_EXECUTION_MODE:
                reasons.append(f"task025b_runtime_scenarios.synthetic_executions[{index}].execution_mode must be synthetic.")
            if execution.get("status") != "blocked":
                reasons.append(f"task025b_runtime_scenarios.synthetic_executions[{index}].status must remain blocked.")
            if execution.get("counts_as_runtime_evidence") is not False:
                reasons.append(f"task025b_runtime_scenarios.synthetic_executions[{index}].counts_as_runtime_evidence must be false.")
            if execution.get("runtime_evidence_ids") != []:
                reasons.append(f"task025b_runtime_scenarios.synthetic_executions[{index}].runtime_evidence_ids must be empty.")
            action_log = execution.get("action_log")
            if not isinstance(action_log, list):
                reasons.append(f"task025b_runtime_scenarios.synthetic_executions[{index}].action_log must be a list.")
            else:
                for action_index, action in enumerate(action_log):
                    if not isinstance(action, str) or not _is_allowed_synthetic_action_log(action):
                        reasons.append(
                            f"task025b_runtime_scenarios.synthetic_executions[{index}].action_log[{action_index}] is not allowed."
                        )
            guarded_boundaries = execution.get("guarded_boundaries")
            if not isinstance(guarded_boundaries, list):
                reasons.append(f"task025b_runtime_scenarios.synthetic_executions[{index}].guarded_boundaries must be a list.")
            else:
                for boundary_index, boundary in enumerate(guarded_boundaries):
                    if boundary not in FORBIDDEN_BOUNDARY_CATEGORIES:
                        reasons.append(
                            f"task025b_runtime_scenarios.synthetic_executions[{index}].guarded_boundaries[{boundary_index}] must be a guarded boundary category."
                        )
    return sorted(set(reasons))


def _is_allowed_synthetic_action_log(action: str) -> bool:
    if action in {
        "launch_app",
        "ensure_authorized_session",
        "classify_screen",
        "assert_focus_present",
        "press_back",
        "press_home",
        "foreground_app",
        "force_stop_relaunch",
        "assert_session_preserved",
        "classify_boundary",
    }:
        return True
    if action in {"press_dpad:up", "press_dpad:down", "press_dpad:left", "press_dpad:right"}:
        return True
    return action == "record_public_safe_evidence_ref:scenario-contract-only"


def load_scenarios(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    scenarios, load_errors = load_json_object(path)
    if scenarios is None:
        return None, load_errors
    return scenarios, validate_scenarios(scenarios)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate TASK-026B no-device TASK-025B physical runtime test report.")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS, help="TASK-025B scenario contract JSON.")
    parser.add_argument("--public-output", type=Path, default=None, help="Optional public summary path under docs/qa/reports/*.json.")
    parser.add_argument(
        "--synthetic-sequencing-test",
        action="store_true",
        help="Run in-memory fake scenario sequencing only; still reports runtime not_run.",
    )
    args = parser.parse_args(argv)

    scenarios, errors = load_scenarios(args.scenarios)
    public_output_valid = args.public_output is None or validate_output_path(args.public_output)
    if not public_output_valid:
        scenarios = {"schema_version": SCENARIO_SCHEMA_VERSION, "scenarios": []}
        report = build_report(scenarios)
        report["blocked_reasons"] = ["public output path must stay under docs/qa/reports/*.json"]
    elif errors or scenarios is None:
        scenarios = {"schema_version": SCENARIO_SCHEMA_VERSION, "scenarios": []}
        report = build_report(scenarios)
        report["blocked_reasons"] = errors
    else:
        report = build_report(scenarios, synthetic_sequencing_test=args.synthetic_sequencing_test)

    if args.public_output is not None and public_output_valid:
        args.public_output.parent.mkdir(parents=True, exist_ok=True)
        args.public_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

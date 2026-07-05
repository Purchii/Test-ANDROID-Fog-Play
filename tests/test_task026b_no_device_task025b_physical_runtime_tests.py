import ast
import json
from pathlib import Path

from automation.native_regression.run_task026b_no_device_task025b_runtime_tests import (
    DEFAULT_SCENARIOS,
    FORBIDDEN_SCENARIO_ACTIONS,
    REQUIRED_CASE_IDS,
    SYNTHETIC_EXECUTION_MODE,
    build_report,
    load_scenarios,
    main,
    run_synthetic_scenarios,
    validate_scenarios,
    validate_task026b_report,
)
from automation.native_regression.validate_task026b_no_device_task025b_runtime_tests import main as validator_main


def _loaded_scenarios():
    scenarios, errors = load_scenarios(DEFAULT_SCENARIOS)
    assert scenarios is not None
    assert errors == []
    return scenarios


def test_task026b_scenario_contract_covers_all_task025b_cases_without_runtime_status():
    scenarios = _loaded_scenarios()

    assert scenarios["task_id"] == "TASK-025B"
    assert scenarios["runtime_execution_status"] == "not_run"
    assert {case["case_id"] for case in scenarios["scenarios"]} == REQUIRED_CASE_IDS
    assert all(case["default_no_device_status"] in {"not_run", "blocked", "deferred"} for case in scenarios["scenarios"])


def test_task026b_default_report_is_blocked_not_run_and_deferred(capsys):
    assert main([]) == 0

    report = json.loads(capsys.readouterr().out)

    assert report["run_status"] == "blocked"
    assert report["runtime_execution_status"] == "not_run"
    assert report["physical_device_status"] == "unavailable"
    assert report["apk_install_status"] == "not_run"
    assert report["app_launch_status"] == "not_run"
    assert report["task025b_runtime_status"] == "deferred"
    assert report["runtime_evidence_ids"] == []
    assert report["task025b_preflight"]["preflight_status"] == "deferred_no_device"
    assert report["task025b_runtime_scenarios"]["scenario_count"] == 10
    assert validate_task026b_report(report) == []


def test_task026b_public_output_path_writes_valid_blocked_report(tmp_path, monkeypatch, capsys):
    scenario_text = DEFAULT_SCENARIOS.read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    scenario_path = tmp_path / "scenarios.json"
    scenario_path.write_text(scenario_text, encoding="utf-8")
    output_path = Path("docs/qa/reports/task026b.json")

    assert main(["--scenarios", str(scenario_path), "--public-output", output_path.as_posix()]) == 0

    stdout_report = json.loads(capsys.readouterr().out)
    file_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report == file_report
    assert validate_task026b_report(file_report) == []


def test_task026b_rejects_public_output_outside_public_reports(capsys):
    assert main(["--public-output", ".qa_local/evidence/task026b/report.json"]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["blocked_reasons"] == ["public output path must stay under docs/qa/reports/*.json"]
    assert report["runtime_execution_status"] == "not_run"


def test_task026b_synthetic_sequencing_is_not_runtime_evidence(capsys):
    assert main(["--synthetic-sequencing-test"]) == 0

    report = json.loads(capsys.readouterr().out)
    section = report["task025b_runtime_scenarios"]

    assert report["execution_mode"] == SYNTHETIC_EXECUTION_MODE
    assert report["runtime_execution_status"] == "not_run"
    assert section["synthetic_sequencing_status"] == "pass"
    assert len(section["synthetic_executions"]) == 10
    assert all(execution["counts_as_runtime_evidence"] is False for execution in section["synthetic_executions"])
    assert all(execution["runtime_evidence_ids"] == [] for execution in section["synthetic_executions"])
    assert validate_task026b_report(report) == []


def test_task026b_fake_scenarios_record_boundary_classification_without_selecting():
    scenarios = _loaded_scenarios()
    executions = run_synthetic_scenarios(scenarios)
    boundary_executions = {item["case_id"]: item for item in executions if item["case_id"] in {"NR-008", "NR-009"}}

    assert set(boundary_executions) == {"NR-008", "NR-009"}
    assert all("classify_boundary" in item["action_log"] for item in boundary_executions.values())
    assert all(not any(action == "press_ok" for action in item["action_log"]) for item in executions)
    assert all(item["guarded_boundaries"] for item in boundary_executions.values())


def test_task026b_validator_rejects_scenario_runtime_evidence_claim():
    report = build_report(_loaded_scenarios(), synthetic_sequencing_test=True)
    report["task025b_runtime_scenarios"]["runtime_evidence_ids"] = ["runtime-evidence-hidden"]
    report["task025b_runtime_scenarios"]["case_statuses"][0]["status"] = "pass"
    report["task025b_runtime_scenarios"]["synthetic_executions"][0]["counts_as_runtime_evidence"] = True

    errors = validate_task026b_report(report)

    assert "task025b_runtime_scenarios.runtime_evidence_ids must be empty." in errors
    assert "task025b_runtime_scenarios.case_statuses[0].status must remain not_run/blocked/deferred." in errors
    assert "task025b_runtime_scenarios.synthetic_executions[0].counts_as_runtime_evidence must be false." in errors


def test_task026b_validator_requires_task026b_report_identity():
    report = build_report(_loaded_scenarios())
    report["task_id"] = "TASK-025A"

    errors = validate_task026b_report(report)

    assert "task_id must be TASK-026B for TASK-026B reports." in errors


def test_task026b_validator_rejects_wrong_section_schema_status_and_count():
    report = build_report(_loaded_scenarios())
    section = report["task025b_runtime_scenarios"]
    section["schema_version"] = "wrong-schema"
    section["scenario_count"] = 9
    section["default_no_device_status"] = "pass"
    section["synthetic_sequencing_status"] = "runtime_pass"

    errors = validate_task026b_report(report)

    assert "task025b_runtime_scenarios.schema_version must be task025b-runtime-scenarios-v1." in errors
    assert "task025b_runtime_scenarios.scenario_count must match required TASK-025B case count." in errors
    assert "task025b_runtime_scenarios.default_no_device_status must be blocked_not_run_deferred." in errors
    assert "task025b_runtime_scenarios.synthetic_sequencing_status must be not_run or pass." in errors


def test_task026b_validator_rejects_unsafe_synthetic_execution_details():
    report = build_report(_loaded_scenarios(), synthetic_sequencing_test=True)
    execution = report["task025b_runtime_scenarios"]["synthetic_executions"][0]
    execution["status"] = "pass"
    execution["action_log"].append("open_webview")
    execution["guarded_boundaries"] = ["unguarded/session-start"]

    errors = validate_task026b_report(report)

    assert "task025b_runtime_scenarios.synthetic_executions[0].status must remain blocked." in errors
    assert "task025b_runtime_scenarios.synthetic_executions[0].action_log[4] is not allowed." in errors
    assert (
        "task025b_runtime_scenarios.synthetic_executions[0].guarded_boundaries[0] must be a guarded boundary category."
        in errors
    )


def test_task026b_scenario_validator_rejects_boundary_entry_and_forbidden_action():
    scenarios = _loaded_scenarios()
    scenarios["scenarios"][7]["boundary_policy"]["boundary_entered"] = True
    scenarios["scenarios"][7]["steps"].append({"action": "press_ok"})

    errors = validate_scenarios(scenarios)

    assert "scenarios[7].boundary_policy.boundary_entered must be false." in errors
    assert "scenarios[7].steps[6].action is not allowed." in errors
    assert "scenarios[7].steps[6].action is forbidden; use boundary classification instead." in errors


def test_task026b_scenario_validator_rejects_missing_boundary_classification_for_sensitive_case():
    scenarios = _loaded_scenarios()
    scenarios["scenarios"][8]["steps"] = [{"action": "classify_screen"}]

    errors = validate_scenarios(scenarios)

    assert any("NR-009 must include a boundary classification step" in error for error in errors)


def test_task026b_scenario_validator_rejects_raw_public_values():
    scenarios = _loaded_scenarios()
    scenarios["notes"] = "https://example.invalid/qr?token=fake .qa_local/evidence/raw.xml +79990000000"

    errors = validate_scenarios(scenarios)

    assert any("URL-like value" in error for error in errors)
    assert any("raw local path" in error for error in errors)
    assert any("phone-like value" in error for error in errors)


def test_task026b_scenarios_use_exact_forbidden_boundary_actions_allowlist():
    scenarios = _loaded_scenarios()
    for case in scenarios["scenarios"]:
        assert sorted(case["boundary_policy"]["forbidden_actions"]) == sorted(FORBIDDEN_SCENARIO_ACTIONS)


def test_task026b_runner_does_not_import_process_shell_or_device_modules():
    forbidden_imports = {"sub" + "process", "os"}
    for path in (
        Path("automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py"),
        Path("automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py"),
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not (imported & forbidden_imports)


def test_task026b_validator_cli_accepts_scenarios_and_template_report(capsys):
    exit_code = validator_main(
        [
            "--scenarios",
            DEFAULT_SCENARIOS.as_posix(),
            "--report",
            "docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json",
        ]
    )

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {"validation_status": "pass", "errors": []}

# Codex execution prompt — TASK-041

Создай новый независимый Codex thread с названием:

```text
TASK-041 — QA-only epic integration, sanitized risk bridge and portable official export
```

Модель: `gpt-5.6-sol` (`5.6 Sol`), reasoning effort: `high`.

Режим: `BOUNDED_AUTONOMOUS`. Ветка:

```text
qa/task-041-qa-only-epic-integration-portable-export
```

База — актуальная remote default branch после verified integration зависимостей:
`epic pack integration`. Никогда не реализуй задачу непосредственно в default branch.

## Сначала прочитай

- `AGENTS.md`
- `CODEX_ANDROID_QA_PROJECT_TZ.md`
- `docs/codex/*.md`
- `docs/context/current-state.md`
- `docs/context/handoff/active-run.md`
- `docs/context/governance/decisions-log.md`
- `docs/context/governance/risk-register.md`
- `docs/context/engineering/quality-gates.md`
- `docs/context/engineering/verification-memory.md`
- `docs/tasks/backlog.md`
- `docs/approvals/local_paths_policy.md`
- `docs/approvals/task005_apk_bundle_contract.md`
- `docs/approvals/device_inventory.public_safe.review.json`

Затем прочитай:

```text
tasks/TASK_041_qa_only_epic_integration_portable_export.md
docs/qa/epics/EPIC_QA_TASK_041_055.md
docs/qa/epics/task041_055_status_evidence_contract.md
docs/qa/epics/task041_055_dependency_map.md
docs/qa/epics/scenarios/task041_scenarios.csv
docs/qa/epics/opaque_surface_task_traceability.csv
```

## Единственная bounded цель

Интегрировать полный QA-only epic TASK-041…055, исправить официальный ZIP без `.git`, сохранить существующие локальные контракты и добавить санитизированный opaque risk bridge без production source.

Не начинай TASK-042 в этом thread.


## Неизменяемые границы TASK-041

TASK-041 исполняется только как `PROD_SAFE` static repository task. Разрешены
tracked QA-файлы, локальные Python QA tests/validators и приложенный public-safe
epic archive. Не читать и не использовать `.qa_local`, APK/AAB, ADB, Android
SDK/AVD, устройства, runtime, WebView/WebRTC, live API/network, payment,
session/account state, production source/build, private dependencies, секреты,
endpoints или raw evidence. Доступность локального устройства или APK не
расширяет scope. Все TASK-041 scenarios подтверждаются только static
repository evidence; screenshot/UI-tree/runtime evidence не создаётся.


## Строгий multi-agent workflow

1. **Orchestrator** проверяет fresh thread, default branch, task branch и source
   of truth.
2. **Planner** читает весь scenario catalog, строит technical plan,
   scenario→automation→evidence→acceptance mapping и явно выделяет P0.
3. **Security/Prod-safety Reviewer** до implementation/runtime классифицирует
   каждую команду `PROD_SAFE / PROD_CONDITIONAL / PROD_FORBIDDEN`, проверяет
   blast radius, cleanup, rollback, kill switch и redaction.
4. **Builder** расширяет существующий framework, а не создаёт обходной harness.
5. **QA Reviewer A** проверяет functional completeness, state transitions,
   negative/boundary cases и dynamic-data assertions.
6. **QA Reviewer B** атакует false-pass: missing input, stale evidence,
   mapped-only, blocked, retry recovery, synthetic-vs-physical, cross-family
   evidence substitution, malformed schemas.
7. **Docs/Scribe** синхронизирует task, reports, manifest, backlog, current-state,
   active-run, decisions, risks и verification memory.
8. Orchestrator исправляет все R0/R1 findings в том же TASK и повторяет reviews.

Реальная multi-agent delegation обязательна. При недоступности инструментов
зафиксируй `MULTI_AGENT_BLOCKED_TOOL_UNAVAILABLE` и не симулируй роли.

## Обязательная реализация

- Реализовать все P0 rows из
  `docs/qa/epics/scenarios/task041_scenarios.csv`.
- Для P1 rows реализовать всё, что доступно в bounded scope; остаток должен иметь
  точную terminal classification и justification.
- Основной runner/validator: `automation/quality/official_export_index.py`.
- QA tests: `tests/test_official_export_index.py`.
- Authoritative tracked report: `docs/qa/reports/task041_epic_integration.summary.json`.
- Переиспользовать существующие schemas, local path contracts, aliases,
  `evidence-report-envelope-v2`, report manifest, release gate, redaction,
  transition/native/API/gamepad tooling.
- Добавить synthetic/adversarial tests до runtime там, где возможно.
- Любой missing input должен fail closed или дать честный blocked status.
- Не считать plan/template/existence evidence исполнением.
- Не удалять TASK-000…040 history.



## Acceptance

- full QA test suite is green in normal Git checkout
- official export unpacked without `.git` passes the same relevant checks
- missing/stale/malformed index, extra file, path traversal and unsafe symlink fail closed
- five-APK contract and `.qa_local` structure are unchanged
- no production source/private binaries/raw evidence enter the public-safe tree
- all fifteen task specs and scenario catalogs are discoverable and linked

## Проверка

Минимум:

```text
git status --short --branch
git diff --check
python -m pytest -q tests/test_official_export_index.py
python -m compileall -q automation tests
python -m pytest -q
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

Добавь и выполни task-specific validate-only/preflight/execute/report commands.
Если runtime lane blocked, tests/validators/docs/report generation всё равно
должны быть доведены до зелёного состояния, а report честно остаётся blocked или
partial.

## Integration и завершение

После final GO от обоих QA reviewers, Security/Prod-safety и Docs/Scribe:

1. commit/push task branch;
2. merge в фактическую default branch без force push;
3. повторить targeted и full verification на default;
4. push remote default;
5. обновить `active-run.md` и handoff;
6. создать ровно один fresh continuation thread:

```text
TASK-042 — Local APK, launcher, AVD and device runtime preflight
```

Финальный отчёт пользователю — на русском: что реализовано, что реально
исполнено, результаты проверок, anomalies/defects, blockers, residual risks,
commit/branch/default SHA и следующий thread.

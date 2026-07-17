# Codex execution prompt — TASK-055

Создай новый независимый Codex thread с названием:

```text
TASK-055 — Unified five-APK plus launcher regression selector and QA release gate
```

Модель: `gpt-5.6-sol` (`5.6 Sol`), reasoning effort: `high`.

Режим: `BOUNDED_AUTONOMOUS`. Ветка:

```text
qa/task-055-unified-multi-apk-release-gate
```

База — актуальная remote default branch после verified integration зависимостей:
`TASK-043, TASK-044, TASK-045, TASK-046, TASK-047, TASK-049, TASK-050, TASK-051, TASK-052, TASK-053, TASK-054`. Никогда не реализуй задачу непосредственно в default branch.

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
tasks/TASK_055_unified_multi_apk_release_gate.md
docs/qa/epics/EPIC_QA_TASK_041_055.md
docs/qa/epics/task041_055_status_evidence_contract.md
docs/qa/epics/task041_055_dependency_map.md
docs/qa/epics/scenarios/task055_scenarios.csv
docs/qa/epics/opaque_surface_task_traceability.csv
```

## Единственная bounded цель

Собрать единый fail-closed regression selector и evidence-backed QA release gate, показывающий реальную полноту по рискам, сценариям, устройствам и build set.

Не начинай TASK-NEXT в этом thread.


## Неизменяемые границы активного этапа

Работа ведётся полностью внутри независимого QA-контура по уже доступным APK,
локальным Android-инструментам, AVD, физическим устройствам, QA-автоматизации,
санитизированным контрактам и локальному evidence.

Разрешено:

- изменять QA-репозиторий, его Python-автоматизацию, схемы, валидаторы, runner'ы,
  отчёты, selectors, документацию и public-safe aliases;
- читать уже существующие локальные `.qa_local` artifacts через проектные
  repo-relative контракты;
- устанавливать и запускать готовые APK на утверждённых локальных AVD/устройствах;
- выполнять bounded black-box/system/UI/E2E проверки;
- использовать санитизированные source-informed risk IDs только как гипотезы и
  направления внешнего тестирования.

Запрещено:

- собирать production-приложение или воспроизводить Gradle/Android build;
- создавать или запускать unit/component/instrumentation tests внутри исходного
  Android-проекта;
- модифицировать production source, APK, подпись, manifest или binary;
- обращаться к программисту, ждать программистский отчёт или вводить
  программистский gate;
- запрашивать Artifactory, private Maven, credentials, keystore, build reports
  или дополнительные материалы;
- публиковать absolute paths, serials, IP, raw hashes, аккаунты, токены,
  endpoints, QR targets, screenshots, logs или иные local-only values;
- выполнять реальную оплату, покупку, изменение реального аккаунта,
  security/TLS bypass, нагрузочные или разрушительные действия.

Отсутствие конкретного устройства, fixture или безопасного runtime-oracle
блокирует только соответствующую строку сценария. Остальная работа продолжается.


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
  `docs/qa/epics/scenarios/task055_scenarios.csv`.
- Для P1 rows реализовать всё, что доступно в bounded scope; остаток должен иметь
  точную terminal classification и justification.
- Planned runner namespace: `automation/reporting/`; planned basename: `task055_unified_release_gate.py`.
- Planned test namespace: `tests/`; planned basename: `test_task055_unified_release_gate.py`.
- Planned report namespace: `docs/qa/reports/`; planned basename: `task055_unified_release_gate.summary.json`.
- Переиспользовать существующие schemas, local path contracts, aliases,
  `evidence-report-envelope-v2`, report manifest, release gate, redaction,
  transition/native/API/gamepad tooling.
- Добавить synthetic/adversarial tests до runtime там, где возможно.
- Любой missing input должен fail closed или дать честный blocked status.
- Не считать plan/template/existence evidence исполнением.
- Не удалять TASK-000…040 history.



## Acceptance

- all mandatory R0/R1 surfaces require fresh authoritative evidence
- five APK families are individually represented
- launcher contour is separately gated and never silently folded into five APKs
- missing mandatory device/lane blocks the applicable release claim
- mapped-only, retry recovery, prior-build and synthetic-only evidence cannot self-assert pass
- full QA suite, hygiene, public safety and docs checks pass

## Проверка

Минимум:

```text
git status --short --branch
git diff --check
python -m pytest -q tests/test_task055_unified_release_gate.py
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
final epic closure / next QA backlog selection
```

Финальный отчёт пользователю — на русском: что реализовано, что реально
исполнено, результаты проверок, anomalies/defects, blockers, residual risks,
commit/branch/default SHA и следующий thread.

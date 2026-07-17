# TASK-055 — Unified five-APK plus launcher regression selector and QA release gate

## Epic

`EPIC-QA-041-055 — Full independent QA coverage for ready MTC Fog Play APKs`

## Размер

`XL+`

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety classification

`PROD_SAFE`

## Ветка

```text
qa/task-055-unified-multi-apk-release-gate
```

## Зависимости

TASK-043, TASK-044, TASK-045, TASK-046, TASK-047, TASK-049, TASK-050, TASK-051, TASK-052, TASK-053, TASK-054

## Основные lanes

Five APK families plus separate launcher system contour

## Цель

Собрать единый fail-closed regression selector и evidence-backed QA release gate, показывающий реальную полноту по рискам, сценариям, устройствам и build set.


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


## Что уже переиспользовать

TASK-003 release gate; TASK-038 manifest; TASK-039 readiness generator; TASK-043 selector; TASK-044…054 evidence. extend authoritative fail-closed gate; no self-asserted pass

## In scope

- five-APK and launcher contour manifest/alias model
- risk/device/family/evidence-aware regression selection
- mandatory/conditional lane rules
- freshness, hash-bound provenance and reviewer approval
- blocked/not-run/mapped/recovery false-pass prevention
- human-readable and machine-readable release outputs
- delta/smoke/full regression profiles

## Обязательный сценарный каталог

```text
docs/qa/epics/scenarios/task055_scenarios.csv
```

Каталог содержит `24` сценариев, из них `23` P0. Основные
opaque surfaces: `SURF-RELEASE-001, SURF-RELEASE-002, SURF-LOG-001`.

Каждая P0-строка должна быть:

- автоматизирована и исполнена;
- либо автоматизирована и честно классифицирована конкретным локальным blocker;
- либо оставлена на разрешённой product boundary с evidence;
- но не может исчезнуть, стать `mapped_only` без причины или быть объявлена PASS
  из плана/шаблона/чужого устройства.

## Рекомендуемые точки реализации

```text
automation/reporting/task055_unified_release_gate.py
tests/test_task055_unified_release_gate.py
docs/qa/reports/task055_unified_release_gate.summary.json
```

Использовать существующие namespaces и schemas проекта, когда они уже покрывают
эту область. Не плодить параллельный framework при возможности расширить
действующий fail-closed runner/validator/report authority.

## Обязательные deliverables

- unified selector and release gate implementation
- release manifest and profile definitions
- adversarial gate tests
- public-safe readiness dashboard/report
- final epic closure and residual-risk register

## Out of scope

- declaring release pass from APK existence or smoke only
- requiring unavailable developer/build artifacts
- converting optional unavailable Stick into global pass




### Канонические статусы сценариев

- `observed_pass`
- `observed_fail`
- `confirmed_defect`
- `tooling_defect`
- `executable_not_run`
- `blocked_by_device`
- `blocked_by_fixture`
- `blocked_by_oracle`
- `blocked_by_product_boundary`
- `blocked_by_external_state`
- `not_applicable`
- `mapped_only`

`mapped_only`, `executable_not_run`, любой `blocked_*`, успешный recovery после
первичного сбоя и retry-pass никогда не преобразуются в исходный PASS.


## Evidence contract

- Сырые screenshot/XML/log/video/hash/serial/account данные — только в
  существующем ignored `.qa_local/evidence/...`.
- Tracked report — `evidence-report-envelope-v2` либо совместимый authoritative
  schema, уже принятый проектом.
- Каждый вывод имеет `confirmed`, `likely`, `hypothesis` или `unknown`.
- Runtime checkpoint включает visual inspection; UI tree используется совместно,
  но не вместо screenshot.
- Screenshot/XML mismatch, retry, recovery и recurrence записываются отдельно.
- Dynamic catalog titles, prices, row counts, ping/hardware values не являются
  стабильными fixed assertions.
- Evidence другого APK family/device/build set не подменяет требуемое evidence.

## Acceptance criteria

- all mandatory R0/R1 surfaces require fresh authoritative evidence
- five APK families are individually represented
- launcher contour is separately gated and never silently folded into five APKs
- missing mandatory device/lane blocks the applicable release claim
- mapped-only, retry recovery, prior-build and synthetic-only evidence cannot self-assert pass
- full QA suite, hygiene, public safety and docs checks pass

## Минимальная verification matrix

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

Codex должен добавить точные validate-only/preflight/execute/report команды
созданного runner'а в task file и `verification-memory.md`. Для runtime-команд
не печатать local-only values.

## Multi-agent acceptance

Обязательны реальные роли:

- Orchestrator;
- Planner;
- Builder;
- QA Reviewer A;
- QA Reviewer B;
- Security/Prod-safety Reviewer;
- Docs/Scribe.

Planner сначала формирует technical plan и scenario-to-deliverable mapping.
Security Reviewer утверждает runtime actions до исполнения. QA reviewers
независимо проверяют false-pass, negative cases, cleanup и evidence integrity.
Docs/Scribe сверяет task, backlog, current-state, active-run, decisions,
risk register и verification memory.

## Stop conditions

Остановить только опасное или конкретно заблокированное действие, если:

- потребовались real payment/account mutation/security bypass/destructive action;
- local-only value может попасть в tracked output;
- выбранное устройство/API/fixture отсутствует;
- отсутствует trustworthy oracle;
- runtime action не имеет cleanup/rollback;
- проверка требует production source/build/private dependency;
- unresolved R0/R1 reviewer finding остаётся после remediation.

При локальном blocker продолжить все независимые safe deliverables и сценарии.
Новый failing QA test, созданный в этом TASK, исправляется в этом же TASK.

## Handoff

После verified merge/push default branch создать ровно один fresh continuation
thread для `Нет; закрытие эпика и формирование остаточного QA backlog.`. Завершённый thread не реализует следующую независимую
задачу.

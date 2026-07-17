# TASK-052 — Remote, keyboard, physical/virtual gamepad and input lifecycle coverage

## Epic

`EPIC-QA-041-055 — Full independent QA coverage for ready MTC Fog Play APKs`

## Размер

`XL+`

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety classification

`PROD_CONDITIONAL`

## Ветка

```text
qa/task-052-input-gamepad-lifecycle-coverage
```

## Зависимости

TASK-044, TASK-045, TASK-049

## Основные lanes

TV/STB/phone pairs and approved physical input devices

## Цель

Закрыть D-pad, remote, keyboard, physical/virtual gamepad, hotplug, reconnect, focus routing and cleanup across applicable lanes.


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

TASK-004 focus templates; TASK-022 gamepad inventory; TASK-032 DataChannel/gamepad contracts; TASK-045 paired lane. separate physical, virtual and synthetic evidence

## In scope

- D-pad directions, Center, Back, Home, long/repeat behavior where safe
- TV keyboard open/close/escape
- physical gamepad paired/unpaired/hotplug/reconnect
- known/unknown/ambiguous controller behavior
- virtual gamepad controls and cross-device routing
- focus/input ownership across overlays/background/relaunch
- synthetic versus physical evidence separation

## Обязательный сценарный каталог

```text
docs/qa/epics/scenarios/task052_scenarios.csv
```

Каталог содержит `22` сценариев, из них `17` P0. Основные
opaque surfaces: `SURF-INPUT-001, SURF-SEARCH-002, SURF-INPUT-002, SURF-INPUT-003, SURF-INPUT-004, SURF-PAIR-002, SURF-FOCUS-002, SURF-LOG-001, SURF-RELEASE-001`.

Каждая P0-строка должна быть:

- автоматизирована и исполнена;
- либо автоматизирована и честно классифицирована конкретным локальным blocker;
- либо оставлена на разрешённой product boundary с evidence;
- но не может исчезнуть, стать `mapped_only` без причины или быть объявлена PASS
  из плана/шаблона/чужого устройства.

## Рекомендуемые точки реализации

```text
automation/input/task052_input_gamepad_lifecycle.py
tests/test_task052_input_gamepad_lifecycle.py
docs/qa/reports/task052_input_gamepad_lifecycle.summary.json
```

Использовать существующие namespaces и schemas проекта, когда они уже покрывают
эту область. Не плодить параллельный framework при возможности расширить
действующий fail-closed runner/validator/report authority.

## Обязательные deliverables

- input capability matrix
- physical and synthetic runner separation
- hotplug/reconnect/state ledger
- focus/input anomaly report
- input regression selector by device family

## Out of scope

- controller firmware modification
- OS-level privileged input injection as physical proof
- paid gameplay latency certification


## Локальный runtime gate

До первого ADB/APK/device action Codex обязан подтвердить только доступные внутри
QA-проекта условия: artifact presence по каноническому repo-relative контракту,
ADB authorization, выбранный synthetic fixture, ignored local evidence storage,
cleanup/rollback и reviewer approvals. Никаких внешних ответов не требуется.

Если локальный gate отсутствует, соответствующий сценарий получает точный
`blocked_*` status. Это не останавливает подготовку automation, validators,
synthetic tests, reports или исполнение других независимых сценариев.



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

- physical evidence is never inferred from synthetic keyevents
- unknown/ambiguous devices have explicit fallback classification
- hotplug and reconnect do not leave stale controls or focus
- keyboard escape trap is rechecked across applicable TV flavors
- cleanup leaves no paired/input state leakage

## Минимальная verification matrix

```text
git status --short --branch
git diff --check
python -m pytest -q tests/test_task052_input_gamepad_lifecycle.py
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
thread для `TASK-053`. Завершённый thread не реализует следующую независимую
задачу.

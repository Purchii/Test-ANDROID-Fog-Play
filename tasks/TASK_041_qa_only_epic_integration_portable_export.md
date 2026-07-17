# TASK-041 — QA-only epic integration, sanitized risk bridge and portable official export

## Epic

`EPIC-QA-041-055 — Full independent QA coverage for ready MTC Fog Play APKs`

## Размер

`XL`

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety classification

`PROD_SAFE`

## Ветка

```text
qa/task-041-qa-only-epic-integration-portable-export
```

## Зависимости

Нет; стартует после интеграции приложенного epic pack.

## Основные lanes

QA repository only; no APK/device/runtime actions

## Цель

Интегрировать полный QA-only epic TASK-041…055, исправить официальный ZIP без `.git`, сохранить существующие локальные контракты и добавить санитизированный opaque risk bridge без production source.


## Неизменяемые границы TASK-041

TASK-041 является строго статической repository-only задачей. Разрешены только
изменения tracked QA-документации, Python-автоматизации, схем, валидаторов,
public-safe отчётов и synthetic/adversarial тестов внутри repository, а также
чтение приложенного public-safe epic archive.

Запрещены любые чтение или действие с `.qa_local`, APK/AAB и другими бинарными
артефактами, ADB, Android SDK/AVD, физическими устройствами, runtime, WebView,
WebRTC, сетью/live API, payment/session/account flows, production source/build,
private dependencies, секретами, endpoints и raw evidence. Эти запреты
применяются даже если локальные APK или устройство доступны. Все сценарии
TASK-041 используют точный класс `PROD_SAFE` и только static repository
evidence; визуальное/runtime evidence для них не требуется и не создаётся.


## Что уже переиспользовать

AGENTS.md; TASK-038 report-manifest; TASK-039 release-readiness; TASK-040 docs checker; current backlog/current-state. extend fail-closed authorities; do not replace historical reports

## In scope

- официальный hash-bound export index и fail-closed ZIP-mode
- интеграция task files, epic docs, scenario catalogs, device/APK matrix
- public-safe opaque surface registry и traceability
- backlog/current-state/handoff/governance updates
- позитивные и adversarial tests QA-репозитория

## Обязательный сценарный каталог

```text
docs/qa/epics/scenarios/task041_scenarios.csv
```

Каталог содержит `18` сценариев, из них `16` P0. Основные
opaque surfaces: `SURF-RELEASE-001, SURF-LOG-001, SURF-RELEASE-002, SURF-INSTALL-001`.

Каждая P0-строка должна быть:

- автоматизирована и исполнена;
- либо автоматизирована и честно классифицирована конкретным локальным blocker;
- либо оставлена на разрешённой product boundary с evidence;
- но не может исчезнуть, стать `mapped_only` без причины или быть объявлена PASS
  из плана/шаблона/чужого устройства.

## Рекомендуемые точки реализации

```text
automation/quality/official_export_index.py
tests/test_official_export_index.py
docs/qa/reports/task041_epic_integration.summary.json
```

Использовать существующие namespaces и schemas проекта, когда они уже покрывают
эту область. Не плодить параллельный framework при возможности расширить
действующий fail-closed runner/validator/report authority.

## Обязательные deliverables

- tracked TASK-041…055 specifications and scenario catalogs
- validated official export index and ZIP portability tests
- epic status/dependency/evidence docs
- current-state, backlog and active-run handoff update
- one next fresh TASK-042 thread after verified integration

## Out of scope

- any `.qa_local`, APK, ADB, Android SDK/AVD, device or runtime read/action
- production source or build
- execution of TASK-042 or any later independent task




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

- TASK-041 использует только tracked static evidence: runner log без raw paths,
  canonical task index, hash/size-bound export index, scenario ledger и
  `evidence-report-envelope-v2`-compatible public report.
- Каждый вывод имеет `confirmed`, `likely`, `hypothesis` или `unknown`.
- Plan/template/file existence сами по себе не являются подтверждением
  исполнения; PASS требует успешного validator/test result.
- Missing, stale, malformed, extra, normalization-conflicting или unsafe entry
  всегда fail closed и не преобразуется в PASS.
- Screenshot, UI tree, runtime log, device/APK hash и `.qa_local` artifact не
  являются TASK-041 evidence и не читаются/не создаются.

Visual/runtime evidence rules из общего epic применяются только к будущим
TASK-042+ в их собственных fresh threads и не расширяют TASK-041.

## Acceptance criteria

- full QA test suite is green in normal Git checkout
- official export unpacked without `.git` passes the same relevant checks
- missing/stale/malformed index, extra file, path traversal and unsafe symlink fail closed
- five-APK contract and `.qa_local` structure are unchanged
- no production source/private binaries/raw evidence enter the public-safe tree
- all fifteen task specs and scenario catalogs are discoverable and linked

## Минимальная verification matrix

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
thread для `TASK-042`. Завершённый thread не реализует следующую независимую
задачу.

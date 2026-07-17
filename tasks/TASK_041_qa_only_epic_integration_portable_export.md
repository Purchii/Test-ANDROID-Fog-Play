# TASK-041 — QA-only epic integration, sanitized risk bridge and portable official export

## Epic

`EPIC-QA-041-055 — Full independent QA coverage for ready MTC Fog Play APKs`

## Размер

`XL`

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety classification

`PROD_SAFE` — repository-only static QA scope

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
чтение приложенного public-safe epic archive. После проверки containment,
manifest и checksum разрешена только свежая task-scoped ignored audit staging
area для содержимого этого archive и portable-export артефактов.

Запрещены чтение или действие с любыми существующими `.qa_local` APK/device/
evidence/secrets artifacts, APK/AAB и другими бинарными артефактами, ADB,
Android SDK/AVD, физическими устройствами, runtime, WebView, WebRTC, сетью/live
API, payment/session/account flows, production source/build, private
dependencies, секретами, endpoints и raw evidence. Эти запреты применяются
даже если локальные APK или устройство доступны. Все сценарии TASK-041
используют точный класс `PROD_SAFE` и только static repository evidence;
визуальное/runtime evidence для них не требуется и не создаётся.


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

- any existing `.qa_local` APK/device/evidence/secrets artifact, APK, ADB,
  Android SDK/AVD, device or runtime read/action; only fresh task-scoped ignored
  archive-audit/export staging is permitted after containment/hash validation
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

- TASK-041 использует только tracked static evidence: public-safe runner log
  `docs/qa/reports/task041_epic_integration.verification.md` без raw paths,
  canonical task index, hash/size-bound export index, scenario ledger и
  `evidence-report-envelope-v2`-compatible public report.
- Каждый вывод имеет `confirmed`, `likely`, `hypothesis` или `unknown`.
- Plan/template/file existence сами по себе не являются подтверждением
  исполнения; PASS требует успешного validator/test result.
- Missing, stale, malformed, extra, normalization-conflicting или unsafe entry
  всегда fail closed и не преобразуется в PASS.
- Screenshot, UI tree, runtime log, device/APK hash и существующие `.qa_local`
  APK/device/evidence/secrets artifacts не являются TASK-041 evidence и не
  читаются/не создаются. Свежая task-scoped ignored staging содержит только
  проверенный archive audit/export material и не расширяет evidence scope.

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

## Completed verification and lifecycle checkpoint — 2026-07-17

Evidence status: `confirmed` for the listed repository-only checks and lifecycle
closure.

- current Git checkout: 144 focused tests passed and 1 skipped; full suite 938
  passed and 2 skipped; compileall passed; docs checker passed with 170 files; both
  hygiene modes passed; public-safety scan passed with 322 files;
  `validate-epic` passed;
- official clean commit alias `qa-task041-final-pre-review` export: ZIP
  validation and unpacked tree validation without `.git` passed; full suite
  938 passed and 2 skipped; docs checker passed with 170 files; public hygiene
  passed; public-safety scan passed with 323 files; report-manifest validation
  passed with 25 records and
  explicit legacy migration blockers;
- process anomaly `TASK041-PROCESS-ANOMALY-001`: the first unpacked no-`.git`
  test attempt allowed pytest cache/bytecode inside the export tree; the strict
  index correctly rejected those extra files with `TREE_EXTRA_FILE`. A fresh
  export rerun disabled the cache provider and redirected bytecode outside the
  tree, then passed. No index rule or authority was weakened.
  Public-safe alias is `official_export_tree_extra_after_test_side_effect`;
  expected state was an index-identical tree, the likely cause was pytest/
  interpreter write side effects, and the test-design implication is to disable
  cache, externalize bytecode and validate the tree after every exported-tree
  check.
- process anomaly `TASK041-PROCESS-ANOMALY-002`: parallel focused/full pytest
  execution caused one temporary Git preservation fixture to fail `git add .`
  without stderr while the other suite remained active. Sequential reruns
  passed; the original failure remains a tooling-process anomaly. Public-safe
  alias is `parallel_temp_git_fixture_collision`; the likely cause is Windows
  Git/temp resource contention, and future Git-mutating suites run sequentially.
- only fresh task-scoped ignored archive audit/export staging was used after
  containment and hash validation; no existing `.qa_local` APK/device/evidence/
  secrets artifact was accessed.
- QA A, QA B, Security/Prod-safety and Docs/Scribe returned final `GO`;
  task branch and default `main` were pushed, `main`/`origin/main` aligned at
  public-safe alias `main-a34d075`, and exactly one fresh TASK-042 thread was
  accepted. `QA-041-018` is `observed_pass`; this thread did not execute TASK-042.

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

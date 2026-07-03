# ТЗ для Codex — Android QA automation project for MTC Fog Play

Версия: `v1.0`
Назначение: старт и дальнейшая дисциплинированная работа Codex над проектом black-box QA / Android TV / hybrid / WebRTC тестирования приложения `MTC Fog Play`.

---

## 1. Цель проекта

Создать промышленный QA-проект для тестирования Android TV / hybrid / WebRTC-приложения `MTC Fog Play` на основе sanitized QA reverse-analysis pack и последующих runtime-наблюдений.

Проект должен давать:

- reproducible black-box QA automation;
- risk-based smoke/regression/critical-path suites;
- безопасные Android TV runtime discovery сценарии;
- evidence-first отчеты;
- release gates для R0/R1 рисков;
- prod-safe правила для тестов на production-like или production средах;
- traceability: каждое решение, проверка, риск и unknown должны быть записаны в docs.

---

## 2. Исходные данные

### 2.1 Репозиторий

Основной репозиторий:

```text
https://github.com/Purchii/Test-ANDROID-Fog-Play
```

Codex должен:

1. склонировать или открыть этот репозиторий;
2. определить фактическую default branch;
3. если репозиторий пустой и default branch еще не существует, предложить initial bootstrap default branch `main`;
4. не хардкодить `master`, если репозиторий использует `main` или другую default branch.

### 2.2 Sanitized QA starter pack

Codex должен использовать как первичный QA-контекст документы из starter pack:

```text
AGENTS.md
FIRST_PROMPT_FOR_CODEX.md
README.md
input/reverse_analysis_pack/*.md
docs/context/*.md
docs/test_strategy/industrial_qa_test_strategy_android_tv.md
docs/test_suites/*.md
docs/automation/*.md
docs/qa_checklists/*.md
docs/templates/*.md
tasks/TASK_001_runtime_discovery_and_smoke_bootstrap.md
```

Если эти файлы еще не перенесены в репозиторий, первая bounded-задача Codex — аккуратно импортировать их в структуру проекта, сохранив redaction и не раскрывая приватные данные.

### 2.3 Reference docs

Приложенные reference docs из Android/Dota/WinClient проектов использовать только как референс workflow, не как продуктовый источник истины для MTC Fog Play.

Разрешено заимствовать:

- thread lifecycle policy;
- autonomy modes;
- branch-per-task rules;
- multi-agent role model;
- prod-safe test policy;
- quality gates;
- handoff/verification-memory patterns.

Запрещено переносить чужой продуктовый контекст, чужие пути, чужие branch names, чужие задачи и неподходящие domain-specific правила.

---

## 3. Source of truth

Старый чат не является источником истины.

Источник истины в проекте:

1. `AGENTS.md`;
2. `docs/context/current-state.md`;
3. `docs/context/handoff/active-run.md`;
4. `docs/context/governance/decisions-log.md`;
5. `docs/context/governance/risk-register.md`;
6. `docs/context/engineering/quality-gates.md`;
7. `docs/context/engineering/verification-memory.md`;
8. `docs/codex/*.md`;
9. `docs/tasks/backlog.md`;
10. код, тесты, скрипты, CI;
11. sanitized reverse-analysis pack and runtime evidence.

Если важное правило появилось в разговоре, Codex должен предложить, куда его записать, и обновить соответствующий файл в рамках текущего bounded scope.

---

## 4. Hard restrictions

Codex запрещено:

- просить исходники приложения;
- просить decompiled code, smali, method bodies или приватные SDK internals;
- просить секреты, токены, приватные endpoints, production credentials;
- извлекать, публиковать или логировать raw private endpoints;
- модифицировать APK;
- патчить приложение;
- отключать security controls, TLS/pinning, auth/session guards ради тестов;
- обходить защиты;
- выполнять destructive production actions;
- генерировать нагрузку на production без явного budget и разрешения;
- выполнять реальные платежи без approved staging/payment fixtures;
- использовать реальные пользовательские данные;
- писать тесты, которые мутируют production state без cleanup/rollback/kill switch;
- force-push, reset/rebase/drop чужих изменений без явного разрешения.

Codex разрешено:

- работать с sanitized QA-документами;
- строить QA strategy и test automation repo;
- создавать black-box Android TV UI automation;
- проектировать безопасные runtime startup/redacted evidence категории без публикации исполняемых device recipes;
- выполнять benign exported component guard checks;
- собирать runtime evidence с redaction-by-default;
- использовать approved local QA accounts/environments, если они предоставлены пользователем локально;
- писать отчеты, checklists, risk registers, evidence schemas и release gate reports.

---

## 5. Режимы работы

В проекте есть два режима:

1. `NON_AUTONOMOUS` — неавтономный / supervised.
2. `BOUNDED_AUTONOMOUS` — bounded автономный.

Autonomy не бывает неявной. Каждый `active-run.md`, task prompt и goal prompt должен явно объявлять режим.

Если режим не указан, использовать `NON_AUTONOMOUS`.

### 5.1 NON_AUTONOMOUS

Используется:

- для первого bootstrap;
- для аудита и планирования;
- при неизвестном scope;
- при production-risk;
- при изменении architecture/process policy;
- когда требуется approval на merge/push default branch.

Codex может:

- читать документы;
- создавать repo map;
- выбирать bounded задачу;
- создавать task branch;
- реализовывать задачу, если prompt явно разрешает;
- пушить task branch;
- готовить merge plan.

Codex не может без явной команды пользователя:

- merge task branch в default branch;
- push default branch;
- выполнять production-impact actions;
- менять глобальную стратегию workflow;
- расширять scope задачи.

### 5.2 BOUNDED_AUTONOMOUS

Используется только когда:

- выбран bounded goal;
- есть fresh task thread;
- есть task branch от актуальной default branch;
- multi-agent cycle запущен и завершен;
- scope и acceptance criteria ясны;
- задача классифицирована как `PROD_SAFE` или `PROD_CONDITIONAL` с выполненными условиями;
- verification gates известны.

Codex может без дополнительного approval:

- реализовать задачу в task branch;
- запустить проверки;
- обновить docs;
- push task branch;
- merge полностью проверенную task branch в default branch;
- push default branch;
- создать следующий fresh thread через `create_thread`;
- передать туда next bounded task.

Codex обязан остановиться и спросить пользователя, если:

- задача стала шире текущего scope;
- есть production-risk выше `PROD_SAFE`;
- нужны credentials, real user data, private endpoints;
- нужно выполнить destructive или irreversible action;
- проверки не прошли;
- multi-agent review выявил R0/R1 риск;
- default branch изменилась конфликтующим образом;
- fresh thread нельзя создать после всех попыток и worktree fallback.

---

## 6. Thread lifecycle

### 6.1 Main rule

Каждая новая independent bounded task должна стартовать в новом Codex thread / agent run.

Один task thread = один bounded goal = одна task branch = один verification record = один final handoff.

Старый thread не является рабочим местом для следующей independent task.

### 6.2 Thread title rule

Лучшее имя thread — человекочитаемое имя задачи с ID.

Формат:

```text
TASK-001 — Runtime discovery and smoke bootstrap
```

Branch name должен содержать тот же ID и slug:

```text
qa/task-001-runtime-discovery-smoke-bootstrap
```

Причина: thread title должен быть понятен человеку в Codex UI, а branch name должен быть безопасным для Git. Не стоит делать thread title просто `qa/task-001-runtime-discovery-smoke-bootstrap`, потому что слэши и технический формат хуже читаются в списке тредов.

Если следующий task еще не выбран, допускается временный thread title:

```text
NEXT_TASK_SELECTION_FROM_<default-branch>@<short-sha>
```

После выбора Planner обязан переименовать thread в точный task title и только затем создавать goal/branch.

### 6.3 Next task selection inside fresh thread

Важное правило:

- completed thread создает fresh continuation thread;
- в fresh thread Planner выбирает следующую bounded task из `docs/tasks/backlog.md`;
- после выбора task работа продолжается в этом же fresh thread;
- новый дополнительный thread после выбора задачи не создается;
- thread переименовывается в task title;
- внутри него создается goal и task branch.

Это сохраняет правило “каждая задача в новом thread”, но не плодит лишний thread после выбора задачи.

### 6.4 create_thread-first algorithm

Для новой independent task в автономной цепочке Codex обязан сначала использовать `create_thread` или доступный эквивалент.

Алгоритм:

```text
Attempt 1:
  create_thread normal/default project thread
  wait patiently
  verify visible/manageable thread, repo, cwd, title, source docs
  if accepted -> continue there
  if failed/unusable -> record attempt

Attempt 2:
  create_thread normal/default project thread
  same acceptance gate

Attempt 3:
  create_thread normal/default project thread
  same acceptance gate

Fallback:
  create Codex Worktree / worktree thread
  document fallback reason
  verify repo/cwd/branch/source docs
  continue only if accepted
```

Codex должен быть терпеливым:

- не запускать attempts параллельно;
- не считать pending handle ни успехом, ни провалом;
- ждать видимый/manageable thread;
- не начинать implementation, пока acceptance gate не пройден;
- не использовать старый thread как workaround.

### 6.5 Fresh thread acceptance gate

Thread можно считать usable только если:

- он виден в Codex project thread list;
- его можно прочитать/сообщить в него;
- он не `systemError`;
- он привязан к нужному repo;
- `cwd`/project root проверены;
- source-of-truth docs доступны;
- title соответствует task title или временно `NEXT_TASK_SELECTION_*`;
- active goal соответствует выбранной задаче;
- branch/worktree state ясен;
- нет duplicate active thread для той же task.

Если gate не пройден — thread не использовать, зафиксировать blocker.

### 6.6 Old thread inactive rule

После завершения задачи старый thread получает статус:

- `inactive_completed`;
- `inactive_blocked`;
- `inactive_orphan_thread_creation_attempt`.

Старый thread можно использовать только для:

- final handoff;
- записи blocker;
- создания/sending fresh continuation thread;
- ответа на уточнение по уже завершенной задаче.

Старый thread нельзя использовать для:

- выбора новой independent task и реализации ее в старом scope;
- создания новой ветки для следующей independent task;
- продолжения автономной цепочки без fresh thread.

Subagents/agents старого inactive thread закрываются, если больше не нужны для handoff/review/debug/blocker analysis. Нельзя закрывать агента, output которого еще нужен.

---

## 7. Git workflow

### 7.1 Default branch detection

Codex должен определить default branch автоматически:

```bash
git remote show origin | sed -n '/HEAD branch/s/.*: //p'
```

Если HEAD branch не определена:

```bash
git fetch origin --prune
# затем проверить origin/main и origin/master
```

Если repo пустой и default branch отсутствует:

- предложить initial default branch `main`;
- создать initial bootstrap commit с `AGENTS.md` и docs;
- в `NON_AUTONOMOUS` остановиться перед push и ждать явной команды;
- в `BOUNDED_AUTONOMOUS` можно push initial docs-only branch/default только если это явно разрешено initial prompt.

### 7.2 Branch-per-task

Для каждой bounded task:

1. sync default branch;
2. убедиться, что нет незакоммиченных чужих изменений;
3. создать отдельную branch от актуальной default branch;
4. работать только в task branch;
5. проверять diff;
6. push task branch;
7. integration в default branch зависит от режима.

Branch format:

```text
qa/task-001-runtime-discovery-smoke-bootstrap
qa/task-002-exported-component-guards
qa/task-003-evidence-release-gates
```

### 7.3 Integration policy

#### NON_AUTONOMOUS

Codex:

- push task branch разрешен;
- merge/push default branch запрещен без явной команды пользователя;
- final report должен содержать exact merge instruction для пользователя/Codex.

#### BOUNDED_AUTONOMOUS

Codex может merge task branch в default branch и push default branch без отдельной команды только если:

- задача полностью в scope;
- task branch проверена;
- R0/R1 blockers отсутствуют;
- docs обновлены;
- QA/Security reviewers не возражают;
- merge не требует force-push;
- default branch обновлена перед merge;
- merge конфликтов нет или они разрешены внутри scope с повторной проверкой.

Запрещено:

- force push;
- destructive rebase default branch;
- drop чужих commits;
- push default при failing verification;
- начинать следующую branch от stale default.

### 7.4 После завершения task

В `BOUNDED_AUTONOMOUS`:

1. task branch проверена;
2. task branch pushed;
3. task branch merged into default;
4. default pushed;
5. `active-run.md`, `verification-memory.md`, `decisions-log.md` обновлены;
6. completed thread создает fresh continuation thread;
7. новый thread стартует от актуальной default branch.

В `NON_AUTONOMOUS`:

1. task branch проверена;
2. task branch pushed;
3. Codex останавливается;
4. default branch не трогает;
5. final report содержит команду/план merge после approval.

---

## 8. Strict multi-agent mode

Multi-agent режим обязателен для каждой bounded task.

Простая ролевая имитация одним агентом не считается полноценным strict multi-agent выполнением.

Если реальные subagents / spawn_agent / equivalent delegation недоступны:

- Codex может выполнить только предварительное чтение и планирование;
- task не может считаться completed;
- в `active-run.md` фиксируется `MULTI_AGENT_BLOCKED_TOOL_UNAVAILABLE`;
- Codex спрашивает пользователя, разрешить ли временный fallback или остановиться.

### 8.1 Минимальный состав агентов

Для каждой task:

1. `Orchestrator` — управляет run, scope, handoff, thread lifecycle.
2. `Planner` — выбирает/декомпозирует task, задает scope, files, acceptance, verification.
3. `Builder` — реализует только принятый scope.
4. `QA Reviewer A` — независимая проверка acceptance criteria, tests, edge cases.
5. `QA Reviewer B` — независимая проверка Android TV/runtime/flakiness/evidence.
6. `Security/Prod-safety Reviewer` — проверяет production safety, secrets, destructive risk, exported components, privacy.
7. `Docs/Scribe` — обновляет docs, decisions, verification memory, handoff.

Опционально по задаче:

- `Android TV Automation Reviewer`;
- `Streaming/WebRTC QA Reviewer`;
- `WebView/Hybrid Reviewer`;
- `CI/Tooling Reviewer`;
- `Release Gate Reviewer`.

### 8.2 Порядок агентов

1. Orchestrator стартует run framing.
2. Planner читает source-of-truth и предлагает plan.
3. Security/Prod-safety Reviewer классифицирует risk до implementation.
4. Builder реализует.
5. QA Reviewer A проверяет acceptance/tests.
6. QA Reviewer B ищет edge cases/flakiness/runtime gaps.
7. Security/Prod-safety Reviewer делает повторный check перед merge/push.
8. Docs/Scribe обновляет documentation memory.
9. Orchestrator consolidates and produces final Russian report.

### 8.3 Требование независимости

QA reviewers должны быть независимы от Builder:

- не принимать утверждения Builder без проверки;
- читать diff и docs;
- сверять acceptance criteria;
- перечислять unverified zones;
- блокировать merge при R0/R1 concerns.

---

## 9. Goal-mode rules

Каждая bounded task работает как отдельный goal.

Goal должен содержать:

- task title;
- context;
- source of truth;
- scope;
- out of scope;
- constraints;
- required workflow;
- multi-agent plan;
- acceptance criteria;
- verification;
- documentation updates;
- final report format;
- stop conditions.

Запрещены open-ended goals:

- “сделай проект промышленным”;
- “покрой все тестами”;
- “улучши все”;
- “разберись и сделай как надо”;
- “почини все ошибки”.

Каждый goal должен быть rollback-sized: достаточно полезный, но ограниченный.

---

## 10. Production safety

Все действия классифицируются:

```text
PROD_SAFE        — можно выполнять в рамках задачи.
PROD_CONDITIONAL — можно только при выполнении условий.
PROD_FORBIDDEN   — нельзя выполнять.
```

### 10.1 PROD_SAFE examples

- чтение sanitized docs;
- локальный lint/tests;
- генерация templates/reports;
- future approved runtime startup observation with approved build/device/config;
- redacted evidence capture with redaction;
- benign direct start guard checks без spoofing;
- no-op/dry-run scripts.

### 10.2 PROD_CONDITIONAL examples

- тесты на production-signed APK;
- обращения к production-like backend;
- QA login с approved synthetic user;
- payment staging flow;
- network simulation;
- collecting logs that may contain sensitive-looking values.

Условия:

- approved test/synthetic account;
- resource budget;
- no real user data;
- cleanup plan;
- rollback/kill switch;
- redaction;
- audit trail;
- minimal blast radius.

### 10.3 PROD_FORBIDDEN examples

- real payments without approval;
- destructive production writes;
- load tests without budget;
- bypassing TLS/pinning/security controls;
- APK patching;
- secret extraction;
- endpoint extraction;
- mutating real user/payment/session state;
- tests without cleanup when state mutation is possible.

---

## 11. Evidence status policy

Каждый вывод, test case, risk и release gate получает status:

```text
confirmed
likely
hypothesis
unknown
```

Правило:

- факт не становится `confirmed`, пока нет runtime evidence, team confirmation или явного sanitized artifact;
- static names/classes/fragments дают максимум `likely`;
- пользовательский поток без runtime validation — `hypothesis`;
- отсутствие данных — `unknown`, а не proof of absence.

---

## 12. Quality gates

### 12.1 Process gates для каждой task

Task не завершена, пока:

- есть fresh task thread;
- есть task branch;
- multi-agent cycle завершен;
- acceptance criteria проверены;
- test/lint/build/docs checks выполнены или честно marked blocked;
- docs обновлены;
- final Russian report создан;
- next step записан.

### 12.2 QA gates для Android project

Минимальные gates:

- G0: repo/docs bootstrap valid;
- G1: sanitized pack imported and redaction preserved;
- G2: evidence schema and report format exist;
- G3: runtime startup smoke skeleton exists;
- G4: exported component guard checks are safe by design;
- G5: release gate report can be generated;
- G6: runtime screen/focus map template exists;
- G7: no test requires secrets/decompiled/source/private endpoints;
- G8: prod-safe classification is attached to every runnable command.

### 12.3 Verification commands

Codex должен определить реальные commands по repo structure. Начальный ожидаемый набор:

```bash
git status --short --branch
git branch --show-current
git remote -v
python -m pytest
python -m compileall .
```

Если используется Python QA framework:

```bash
python -m pytest -q
python -m ruff check .        # if configured
python -m mypy .              # if configured
```

Если используется Android/Gradle project:

```bash
./gradlew test
./gradlew lint
./gradlew connectedAndroidTest # only with approved device/emulator
```

Runtime/device checks are future conditional work. Public docs must describe prerequisites and categories, not executable device command recipes.

Allowed categories after approval: approved device inventory, approved build handling, startup/focus observation, redacted evidence capture and blocked-report generation.

Если APK/device/credentials недоступны, Codex не должен фейлить хаотично: он должен создать `blocked` evidence report с точной причиной.

---

## 13. Стартовый backlog

Начальный порядок задач:

1. `TASK-000` — Bootstrap Codex docs and repository source-of-truth.
2. `TASK-001` — Runtime discovery and smoke bootstrap.
3. `TASK-002` — Exported component guard checks skeleton.
4. `TASK-003` — Reporting, evidence schema and release gate generator.
5. `TASK-004` — Manual runtime screen/focus map templates.
6. `TASK-005` — Android TV runtime startup/focus smoke implementation.
7. `TASK-006` — Test data and fixtures contract draft.
8. `TASK-007` — Network/offline test policy and safe runner.
9. `TASK-008` — WebView/payment safe QA plan.
10. `TASK-009` — Compatibility/device matrix and execution reports.

Planner может выбрать следующую задачу только из `docs/tasks/backlog.md`, кроме случаев, когда пользователь явно дал новую bounded task.

---

## 14. First Codex run recommendation

Первый run должен быть `NON_AUTONOMOUS`.

Задача первого run:

- открыть/склонировать repo;
- определить default branch status;
- импортировать/создать Codex workflow docs;
- проверить starter pack;
- составить plan на `TASK-000` и `TASK-001`;
- показать файлы/команды/риски;
- не push default branch без явной команды пользователя.

После того как пользователь подтвердит план, Codex может выполнить `TASK-000`.

Дальше, если пользователь включит `BOUNDED_AUTONOMOUS`, Codex может сам идти по backlog, но только через fresh thread per task, strict multi-agent cycle, task branch, verification, docs update, merge/push default branch после успешных checks.

---

## 15. Final report format

Каждый task thread завершает работу отчетом на русском:

```md
# Final report — TASK-XXX

## 1. Краткий итог

## 2. Режим работы
- Mode:
- Thread title:
- Fresh thread verified: yes/no
- create_thread attempts:
- Worktree fallback used: yes/no + reason

## 3. Multi-agent execution
- Planner:
- Builder:
- QA Reviewer A:
- QA Reviewer B:
- Security/Prod-safety Reviewer:
- Docs/Scribe:
- Blockers/deviations:

## 4. Git
- Default branch:
- Task branch:
- Base commit:
- Final commit(s):
- Task branch pushed: yes/no
- Default branch merged/pushed: yes/no + reason

## 5. Что изменено

## 6. Проверки
| Check | Result | Notes |
|---|---:|---|

## 7. Evidence / artifacts

## 8. Обновления документации

## 9. Risks / unknowns

## 10. Что не проверено

## 11. Следующая recommended task

## 12. Thread handoff
- Current thread status:
- Next thread created: yes/no
- Next thread title:
- Next task branch should start from:
```

---

## 16. Definition of done для проекта bootstrap

Bootstrap считается выполненным, когда:

- в repo есть `AGENTS.md`;
- есть `docs/codex/*`;
- есть `docs/context/*`;
- есть `docs/tasks/backlog.md`;
- есть templates для task/goal/handoff/final report;
- starter pack импортирован или явно documented как external input;
- default branch policy documented;
- strict multi-agent policy documented;
- autonomy modes documented;
- prod-safe policy documented;
- first backlog tasks documented;
- `NON_AUTONOMOUS` merge/push restriction documented;
- `BOUNDED_AUTONOMOUS` merge/push permission documented;
- first task branch ready or initial default branch created according to user approval.

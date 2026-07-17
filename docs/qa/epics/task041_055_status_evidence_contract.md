# Status and evidence contract — TASK-041…055

## 1. Task status

- `completed` — все acceptance criteria выполнены, проверки зелёные, обязательные
  rows terminally classified, task integrated.
- `partial` — полезная реализация и evidence есть, но часть in-scope mandatory
  execution недоступна/не завершена; не эквивалентно pass.
- `blocked` — bounded objective невозможно доказать из-за конкретного local
  device/fixture/oracle/product boundary.
- `failed` — implementation/verification небезопасна или не проходит и не
  исправлена в том же task.

## 2. Scenario status

- `observed_pass` — ожидаемый oracle непосредственно наблюдён на применимой lane.
- `observed_fail` — наблюдаемый результат не соответствует oracle, но defect
  triage ещё не завершён.
- `confirmed_defect` — воспроизводимый product defect с evidence.
- `tooling_defect` — ненадёжный harness/oracle/evidence pipeline; product
  conclusion не допускается.
- `executable_not_run` — сценарий готов, но не запускался.
- `blocked_by_device` — требуемая device lane отсутствует/offline/unauthorized.
- `blocked_by_fixture` — отсутствует approved synthetic/local fixture.
- `blocked_by_oracle` — нет trustworthy способа отличить успех от no-op/loader.
- `blocked_by_product_boundary` — дальнейший шаг требует оплаты, реальной сессии,
  account mutation или другого запрещённого действия.
- `blocked_by_external_state` — изменчивое внешнее состояние не позволяет
  исполнить ветвь сейчас.
- `not_applicable` — доказанно неприменимо к данной family/device.
- `mapped_only` — risk→scenario mapping существует, execution evidence нет.

## 3. Evidence status

- `confirmed`
- `likely`
- `hypothesis`
- `unknown`

Статус scenario и evidence_status — разные поля. `observed_pass` требует
`confirmed` runtime evidence соответствующего типа.

## 4. Evidence type

- `physical_runtime`
- `paired_physical_runtime`
- `avd_tooling_runtime`
- `synthetic_offline`
- `static_contract`
- `manual_observation`
- `mapped_only`

Physical requirement нельзя удовлетворить `avd_tooling_runtime`,
`synthetic_offline` или `mapped_only`.

## 5. Attempt semantics

Каждая попытка имеет собственный record:

```text
attempt_id
started_at
pre_state
action
observed_state
oracle_result
evidence_ids
cleanup_result
```

Если attempt 1 failed, а attempt 2 passed:

```text
scenario_status != clean observed_pass
first_failure remains in anomaly/defect ledger
recovery_success is recorded separately
```

## 6. Recurrence semantics

Повторно увиденный loader/error/captcha/legal/QR/settings/ambient/empty state
является first-class event:

- prior alias/evidence;
- current trigger/path;
- совпавшие признаки;
- изменившиеся признаки;
- evidence status.

## 7. Build-set/freshness

Runtime evidence привязано к public-safe build-set alias, APK family, device
profile, scenario contract version и evidence timestamp. Raw hashes local-only.

Prior-build evidence:

- может использоваться для исторического контекста;
- может уменьшить selector scope только по explicit compatibility rule;
- не удовлетворяет mandatory release gate автоматически.

## 8. Visual evidence

UIAutomator/XML не является единственным oracle. Каждый runtime checkpoint
должен включать screenshot/visual inspection. Visual overlay, snackbar, focus
ring or blank state, отсутствующие в XML, остаются evidence.

## 9. Fail-closed rules

Никогда не считать PASS:

- отсутствующий input/report/artifact;
- пустой file list;
- skipped/disabled/quarantined test;
- `mapped_only`;
- `blocked_*`;
- `executable_not_run`;
- template/plan;
- AVD tooling smoke как OEM compatibility;
- synthetic keyevent как physical gamepad evidence;
- TPV result как Yandex/Sber/AOSP result;
- recovery после первого failure как отсутствие failure;
- наличие пяти APK как runtime readiness.

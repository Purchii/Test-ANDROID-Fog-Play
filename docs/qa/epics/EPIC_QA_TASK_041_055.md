# EPIC-QA-041-055 — independent runtime QA for five APK families and launcher contour

## Active scope

QA uses ready APK artifacts, existing `.qa_local` contracts, Android SDK/ADB/AVD,
available physical devices, current QA automation and sanitized opaque risk IDs.

No Android production build, source-level unit/component/instrumentation tests,
programmer handoff, private dependency access or external gate belongs to this
epic.

## Main artifacts

```text
docs/qa/epics/task041_055_status_evidence_contract.md
docs/qa/epics/task041_055_dependency_map.md
docs/qa/epics/device_apk_execution_matrix.csv
docs/qa/epics/opaque_surface_task_traceability.csv
docs/qa/epics/scenarios/task041_scenarios.csv
...
docs/qa/epics/scenarios/task055_scenarios.csv
```

## Tasks

| Task | Title | Dependencies | Scenarios |
|---|---|---|---:|
| TASK-041 | QA-only epic integration, sanitized risk bridge and portable official export | — | 18 |
| TASK-042 | Local APK, launcher, AVD and device runtime preflight | TASK-041 | 18 |
| TASK-043 | Sanitized source-informed runtime surface registry and regression selector | TASK-041, TASK-042 | 18 |
| TASK-044 | Television Full reference-lane oracle closure on TPV13 | TASK-042, TASK-043 | 32 |
| TASK-045 | Paired Television Full plus Phone Full virtual-gamepad E2E | TASK-044 | 22 |
| TASK-046 | Television Steam / YandexTV representative runtime lane | TASK-044 | 17 |
| TASK-047 | Television Sber / SberBox representative runtime lane | TASK-044 | 17 |
| TASK-048 | AOSP FogPlay Stick and launcher system-cluster runtime lane | TASK-042, TASK-043 | 19 |
| TASK-049 | Cross-family non-payment transition and state graph closure | TASK-044, TASK-045, TASK-046, TASK-047 | 24 |
| TASK-050 | Install, update, persistence, process-death and recovery matrix | TASK-044, TASK-046, TASK-047 | 20 |
| TASK-051 | Network, offline, cache, API/STOMP reconnect and fault-runtime coverage | TASK-044, TASK-045, TASK-049 | 20 |
| TASK-052 | Remote, keyboard, physical/virtual gamepad and input lifecycle coverage | TASK-044, TASK-045, TASK-049 | 22 |
| TASK-053 | Device equivalence, OS/OEM/display/localization usability matrix | TASK-046, TASK-047, TASK-049, TASK-052 | 18 |
| TASK-054 | Crash, ANR, startup, resource, performance and soak qualification | TASK-044, TASK-045, TASK-049, TASK-051, TASK-052, TASK-053 | 18 |
| TASK-055 | Unified five-APK plus launcher regression selector and QA release gate | TASK-043, TASK-044, TASK-045, TASK-046, TASK-047, TASK-049, TASK-050, TASK-051, TASK-052, TASK-053, TASK-054 | 24 |

## Runtime order

1. existing local AVD tooling sandbox;
2. `tv-tpv-013` reference/control;
3. `tv-tpv-013 + phone-xiaomi-007` paired lane;
4. `tv-yandex-012`;
5. `stb-sberdevices-009`;
6. actual project-known FogPlay Stick;
7. equivalence and OS/OEM boundaries.

## Completion

Total scenario inventory: `307`. Every row must end in a canonical
terminal status. No mapped/template/blocked/not-run/retry/synthetic evidence
may self-assert required physical/product PASS.

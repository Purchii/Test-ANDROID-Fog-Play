# EPIC-QA-041-055 handoff

## Active task after integration

```text
TASK-041 — QA-only epic integration, sanitized risk bridge and portable official export
branch: qa/task-041-qa-only-epic-integration-portable-export
mode: BOUNDED_AUTONOMOUS
```

## Scope freeze

- independent QA only;
- five ready APKs in existing local project structure;
- launcher/system cluster separate;
- Android Studio/SDK/ADB/AVD and devices already local;
- no unit/app compilation/build;
- no programmer handoff/gate;
- no private dependency request.

## Sequence

```text
041 → 042 → 043 → 044 → 045 → 046 → 047 → 048
→ 049 → 050 → 051 → 052 → 053 → 054 → 055
```

## First runtime lanes

```text
AVD tooling only
tv-tpv-013
tv-tpv-013 + phone-xiaomi-007
tv-yandex-012
stb-sberdevices-009
actual FogPlay Stick
```

## Inventory

- tasks: 15
- scenario rows: 307
- opaque surfaces: 55
- public-safe task specs: TASK-041 through TASK-055, with explicit paths in `docs/qa/epics/task041_055_task_index.json`
- scenario catalogs: `docs/qa/epics/scenarios/`

## Key rule

A local missing device/fixture/oracle blocks only the applicable scenario/lane.
It does not create an external wait state and does not stop safe independent work.

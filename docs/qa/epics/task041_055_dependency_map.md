# Dependency and continuation map

## Основной DAG

```text
TASK-041
└── TASK-042
    └── TASK-043
        ├── TASK-044
        │   ├── TASK-045
        │   ├── TASK-046
        │   └── TASK-047
        └── TASK-048
            │
TASK-044 + 045 + 046 + 047 (+ 048 when available)
└── TASK-049
    ├── TASK-050
    ├── TASK-051
    └── TASK-052
        └── TASK-053
            └── TASK-054
                └── TASK-055
```

## Исполняемая default-последовательность

```text
041 → 042 → 043 → 044 → 045 → 046 → 047 → 048
→ 049 → 050 → 051 → 052 → 053 → 054 → 055
```

## Optional lane semantics

`TASK-048` имеет особое правило:

- actual FogPlay Stick READY → выполнить runtime;
- target отсутствует → реализовать automation/validators/reports, записать
  `blocked_by_device`, продолжить TASK-049;
- TASK-055 блокирует только claim, требующий AOSP/launcher evidence, и сохраняет
  отдельные subclaims по остальным APK families.

Аналогично device-specific row в TASK-053 не останавливает остальные devices.

## Fresh thread lifecycle

После каждой задачи:

1. task branch verified;
2. merge/push actual default branch;
3. post-merge verification;
4. active-run and handoff update;
5. ровно один fresh continuation thread;
6. предыдущий thread inactive.

Никакой старый thread не реализует следующую задачу.

## Parallelism

Параллель разрешён только после явного Orchestrator решения:

- разные fresh threads;
- разные task branches/worktrees;
- нет shared mutable `.qa_local` device/session/evidence state;
- нет одновременного управления одним устройством;
- merge order определён заранее;
- каждый task имеет собственные reports и validators.

Без этих условий использовать последовательность.

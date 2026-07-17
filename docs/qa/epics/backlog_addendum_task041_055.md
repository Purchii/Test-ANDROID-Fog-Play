# Backlog addendum — EPIC-QA-041-055

TASK-041 is the first selected task after this overlay is integrated. All other
tasks are blocked only by explicit task dependencies or local lane readiness,
not by programmer/build prerequisites.

| Task | Title | Mode | Safety | Dependencies | Initial status | Branch |
|---|---|---|---|---|---|---|
| TASK-041 | QA-only epic integration, sanitized risk bridge and portable official export | BOUNDED_AUTONOMOUS | PROD_SAFE | none | selected | `qa/task-041-qa-only-epic-integration-portable-export` |
| TASK-042 | Local APK, launcher, AVD and device runtime preflight | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-041 | planned_blocked_by_dependency | `qa/task-042-local-runtime-preflight` |
| TASK-043 | Sanitized source-informed runtime surface registry and regression selector | BOUNDED_AUTONOMOUS | PROD_SAFE | TASK-041,TASK-042 | planned_blocked_by_dependency | `qa/task-043-source-informed-runtime-coverage-map` |
| TASK-044 | Television Full reference-lane oracle closure on TPV13 | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-042,TASK-043 | planned_blocked_by_dependency | `qa/task-044-tpv13-reference-lane-oracle-closure` |
| TASK-045 | Paired Television Full plus Phone Full virtual-gamepad E2E | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-044 | planned_blocked_by_dependency | `qa/task-045-paired-tv-phone-virtual-gamepad-e2e` |
| TASK-046 | Television Steam / YandexTV representative runtime lane | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-044 | planned_blocked_by_dependency | `qa/task-046-yandextv-representative-lane` |
| TASK-047 | Television Sber / SberBox representative runtime lane | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-044 | planned_blocked_by_dependency | `qa/task-047-sberbox-representative-lane` |
| TASK-048 | AOSP FogPlay Stick and launcher system-cluster runtime lane | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-042,TASK-043 | planned_blocked_by_dependency | `qa/task-048-aosp-launcher-system-cluster-runtime` |
| TASK-049 | Cross-family non-payment transition and state graph closure | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-044,TASK-045,TASK-046,TASK-047 | planned_blocked_by_dependency | `qa/task-049-cross-family-transition-state-closure` |
| TASK-050 | Install, update, persistence, process-death and recovery matrix | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-044,TASK-046,TASK-047 | planned_blocked_by_dependency | `qa/task-050-install-update-persistence-recovery-matrix` |
| TASK-051 | Network, offline, cache, API/STOMP reconnect and fault-runtime coverage | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-044,TASK-045,TASK-049 | planned_blocked_by_dependency | `qa/task-051-network-api-transport-runtime` |
| TASK-052 | Remote, keyboard, physical/virtual gamepad and input lifecycle coverage | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-044,TASK-045,TASK-049 | planned_blocked_by_dependency | `qa/task-052-input-gamepad-lifecycle-coverage` |
| TASK-053 | Device equivalence, OS/OEM/display/localization usability matrix | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-046,TASK-047,TASK-049,TASK-052 | planned_blocked_by_dependency | `qa/task-053-device-equivalence-compatibility-usability` |
| TASK-054 | Crash, ANR, startup, resource, performance and soak qualification | BOUNDED_AUTONOMOUS | PROD_CONDITIONAL | TASK-044,TASK-045,TASK-049,TASK-051,TASK-052,TASK-053 | planned_blocked_by_dependency | `qa/task-054-stability-performance-soak` |
| TASK-055 | Unified five-APK plus launcher regression selector and QA release gate | BOUNDED_AUTONOMOUS | PROD_SAFE | TASK-043,TASK-044,TASK-045,TASK-046,TASK-047,TASK-049,TASK-050,TASK-051,TASK-052,TASK-053,TASK-054 | planned_blocked_by_dependency | `qa/task-055-unified-multi-apk-release-gate` |

Planner should merge this block into `docs/tasks/backlog.md` without deleting
historical TASK-000…040 entries.

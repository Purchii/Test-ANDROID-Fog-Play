# Backlog — Android QA Codex bounded tasks

## P0 — workflow/source-of-truth bootstrap

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-000 | Bootstrap Codex docs and source-of-truth | BOUNDED_AUTONOMOUS | qa/task-000-bootstrap-codex-docs | completed |

## P1 — first QA foundation

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-001 | Runtime discovery and smoke bootstrap | BOUNDED_AUTONOMOUS with runtime execution blocked until fixtures approved | qa/task-001-runtime-discovery-smoke-bootstrap | completed |
| TASK-002 | Exported component guard checks skeleton | BOUNDED_AUTONOMOUS if TASK-001 done | qa/task-002-exported-component-guards | completed |
| TASK-003 | Reporting, evidence schema and release gate generator | BOUNDED_AUTONOMOUS if TASK-001 done | qa/task-003-evidence-release-gates | completed |
| TASK-004 | Manual runtime screen and TV focus map templates | BOUNDED_AUTONOMOUS | qa/task-004-runtime-screen-focus-map | completed |
| TASK-005 | Android TV install/launch/focus smoke implementation | BOUNDED_AUTONOMOUS with device/APK caveat | qa/task-005-android-tv-smoke | blocked until approved build/device/config/fixtures |

## P2 — fixtures-dependent QA

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-006 | Test data and fixtures contract draft | NON_AUTONOMOUS | qa/task-006-test-fixtures-contract | completed |
| TASK-007 | Network/offline policy and safe runner | BOUNDED_AUTONOMOUS after policy | qa/task-007-network-offline-policy | completed |
| TASK-008 | WebView/payment safe QA plan | NON_AUTONOMOUS | qa/task-008-webview-payment-safe-qa | completed |
| TASK-009 | Compatibility/device matrix and report format | BOUNDED_AUTONOMOUS | qa/task-009-device-matrix | completed |
| TASK-010 | CI/nightly smoke plan | NON_AUTONOMOUS then BOUNDED_AUTONOMOUS | qa/task-010-ci-nightly-smoke | planned |

## Selection rule

Planner selects the next task based on:

1. R0/R1 risk reduction;
2. dependency readiness;
3. ability to verify;
4. smallest useful rollback-sized branch;
5. no production safety blocker.

## Current selection note

After TASK-009, Planner and Security/Prod-safety evaluated TASK-008 and TASK-010. TASK-005 remains blocked because approved build/APK, Android TV target, runtime configuration, fixture approvals, redaction policy, evidence storage and cleanup/rollback are still `unknown`. TASK-008 was selected in `NON_AUTONOMOUS` mode because WebView/payment-safe planning is fixture and approval sensitive, and TASK-010 CI/nightly smoke planning should inherit an explicit WebView/payment safety boundary. Runtime/device/WebView/payment execution remains blocked until approved prerequisites are recorded.

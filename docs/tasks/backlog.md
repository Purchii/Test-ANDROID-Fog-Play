# Backlog - Android QA Codex bounded tasks

## P0 - workflow/source-of-truth bootstrap

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-000 | Bootstrap Codex docs and source-of-truth | BOUNDED_AUTONOMOUS | qa/task-000-bootstrap-codex-docs | completed |

## P1 - first QA foundation

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-001 | Runtime discovery and smoke bootstrap | BOUNDED_AUTONOMOUS with runtime execution blocked until fixtures approved | qa/task-001-runtime-discovery-smoke-bootstrap | completed |
| TASK-002 | Exported component guard checks skeleton | BOUNDED_AUTONOMOUS if TASK-001 done | qa/task-002-exported-component-guards | completed |
| TASK-003 | Reporting, evidence schema and release gate generator | BOUNDED_AUTONOMOUS if TASK-001 done | qa/task-003-evidence-release-gates | completed |
| TASK-004 | Manual runtime screen and TV focus map templates | BOUNDED_AUTONOMOUS | qa/task-004-runtime-screen-focus-map | completed |
| TASK-005 | Android TV install/launch/focus smoke implementation | BOUNDED_AUTONOMOUS with device/APK caveat | qa/task-005-android-tv-smoke | blocked until approved build/device/config/fixtures |

## P2 - fixtures-dependent QA

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-006 | Test data and fixtures contract draft | NON_AUTONOMOUS | qa/task-006-test-fixtures-contract | completed |
| TASK-007 | Network/offline policy and safe runner | BOUNDED_AUTONOMOUS after policy | qa/task-007-network-offline-policy | completed |
| TASK-008 | WebView/payment safe QA plan | NON_AUTONOMOUS | qa/task-008-webview-payment-safe-qa | completed |
| TASK-009 | Compatibility/device matrix and report format | BOUNDED_AUTONOMOUS | qa/task-009-device-matrix | completed |
| TASK-010 | CI/nightly smoke plan | BOUNDED_AUTONOMOUS for public-safe local planning only | qa/task-010-ci-nightly-smoke | completed |
| TASK-011 | Navigation transition map and coverage model | BOUNDED_AUTONOMOUS for public-safe local planning only | qa/task-011-navigation-transition-map | completed |

## P3 - safe autonomous planning before user-answer-dependent runtime work

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-012 | Safe task prioritization and approval-dependency map | BOUNDED_AUTONOMOUS for public-safe docs only | qa/task-012-safe-task-prioritization | completed |

## P4 - safe autonomous work without new user approvals

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-013 | Next-task selection blocker and safe backlog refresh | BOUNDED_AUTONOMOUS for public-safe docs only | qa/task-013-next-task-selection-safe-backlog-refresh | completed |
| TASK-014 | Public repository safety scan checklist and local guard plan | BOUNDED_AUTONOMOUS for public-safe docs/static checks only | qa/task-014-public-repo-safety-scan | proposed |
| TASK-015 | Approval metadata schema validator | BOUNDED_AUTONOMOUS for local fail-closed validation only | qa/task-015-approval-metadata-validator | completed |
| TASK-016 | Device/build inventory and runtime preflight draft | BOUNDED_AUTONOMOUS for public-safe docs/local validation only; execution blocked | qa/task-016-device-build-runtime-preflight | proposed |
| TASK-017 | Synthetic redaction policy test corpus | BOUNDED_AUTONOMOUS for synthetic local tests only | qa/task-017-redaction-policy-test-corpus | proposed |
| TASK-018 | Docs consistency and link sanity checks | BOUNDED_AUTONOMOUS for public-safe docs/static checks only | qa/task-018-docs-consistency-link-sanity | proposed |

## Selection rule

Planner selects the next task based on:

1. R0/R1 risk reduction;
2. dependency readiness;
3. ability to verify;
4. smallest useful rollback-sized branch;
5. no production safety blocker.

## Safe autonomous priority policy

Until approved runtime prerequisites are recorded with `evidence_status=confirmed`, autonomous continuation should prioritize public-safe planning, templates, local fail-closed generators, redaction tests, release-gate wiring and documentation tasks that do not require user secrets, private endpoints, APK handling, device execution, real accounts, real payments or production interaction.

Tasks that require user answers, approvals or external fixtures must stay blocked or proposed until those answers are recorded. This includes runtime smoke, real transition observation, WebView/payment execution, network/offline execution, compatibility execution, live CI scheduling and any task needing approved build/device/config/fixture metadata.

## Current selection note

After TASK-012 integration, a next-task selection checkpoint confirmed that no eligible unfinished public-safe task remained in the backlog. TASK-005 remains blocked because approved build/APK, Android TV target, runtime configuration, fixture approvals, redaction policy, evidence storage, cleanup/rollback, QA review and Security/Prod-safety review are still `unknown` or not confirmed.

Planner may continue autonomously with proposed P4 tasks only when the selected task is public-safe, bounded, verifiable locally and does not require user secrets, private endpoints, APK handling, device execution, real accounts, real payments or production interaction. Runtime/device/APK/WebView/WebRTC/payment/network/live CI execution remains blocked until approved prerequisites are recorded with `evidence_status=confirmed`.

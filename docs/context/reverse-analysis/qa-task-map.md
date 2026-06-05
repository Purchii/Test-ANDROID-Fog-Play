# QA task map from public-safe reverse-analysis context

## TASK-001 mapping

`TASK-001` is a planning/bootstrap task for runtime discovery and smoke bootstrap.

Allowed deliverables:

- smoke charter;
- runtime discovery checklist;
- prerequisites list for device, APK/build, QA accounts, staging payment fixtures and stream fixtures;
- evidence capture schema;
- blocked-report behavior for missing prerequisites;
- risk-priority mapping using `confirmed`, `likely`, `hypothesis`, `unknown`.

Not allowed in TASK-001:

- source or decompiled code analysis;
- APK patching or resigning;
- raw endpoint or secret extraction;
- real payment or production mutation;
- runtime/device execution unless a later task explicitly satisfies safety gates.

## Backlog seeds

| Candidate | Suggested task | Dependency |
|---|---|---|
| Runtime discovery checklist | TASK-001 | Bootstrap docs complete. |
| Exported surface guard plan | TASK-002 | TASK-001 risk map and safety policy. |
| Evidence schema and release gates | TASK-003 | TASK-001 report format decisions. |
| Manual screen/focus map | TASK-004 | Runtime discovery templates. |
| Android TV smoke execution | TASK-005 | Approved build/device/config and no safety blocker. |
| Fixtures contract | TASK-006 | Product/team answers for accounts, payments and streams. |

## Evidence discipline

Static names from sanitized material are planning inputs. They do not prove that a screen, route, endpoint or user journey works at runtime.

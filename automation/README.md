# Automation

This directory contains public-safe local QA tooling for the Android TV QA repository.

## Runtime Smoke Bootstrap

`automation/runtime_smoke_bootstrap/` contains the TASK-001 blocked-report generator. It is a local dry-run utility and does not interact with an Android device, app binary, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- complete metadata still does not execute runtime checks in TASK-001.

## Exported Component Guards

`automation/exported_component_guards/` contains the TASK-002 exported component guard skeleton generator. It is a local dry-run utility and does not interact with an Android device, app binary, network service, exported component or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing approved guard scope metadata -> `blocked`;
- complete metadata produces a `not_run` plan only and still does not execute runtime checks in TASK-002.

## Reporting and Release Gates

`automation/reporting/` contains the TASK-003 release gate report generator. It is a local dry-run utility and does not interact with an Android device, app binary, network service, WebView, WebRTC session or production environment.

The generator is designed to fail closed:

- missing release metadata -> `blocked`;
- malformed metadata -> `blocked`;
- runtime-dependent R0/R1 gates require `status=pass` and `evidence_status=confirmed`;
- blocked, failed, not-run or non-confirmed R0/R1 gates keep the release decision blocked;
- notes and artifact references are redacted before output.

## Safety Rules

Automation in this repository must not request or store:

- source or decompiled application code;
- secrets, tokens, cookies, sessions or credentials;
- private endpoint inventories;
- APK, AAB, DEX, native or signing artifacts;
- raw logs, screenshots or videos;
- real user data or real payment data.

Runtime/device execution belongs to a future approved task after prerequisites, redaction and review gates are satisfied.

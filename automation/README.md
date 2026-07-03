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

## Manual Runtime Maps

`automation/manual_runtime_maps/` contains the TASK-004 manual runtime screen/focus map report generator. It is a local dry-run utility and does not interact with an Android device, app binary, network service, WebView, WebRTC session or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing synthetic fixture policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- complete metadata produces `not_run` screen/focus map templates only and never claims runtime behavior passed in TASK-004;
- notes and artifact references are redacted before output.

## Network/Offline Safe Runner

`automation/network_offline_safe_runner/` contains the TASK-007 network/offline policy report generator. It is a local dry-run utility and does not interact with an Android device, app binary, backend, proxy, packet capture, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing network profile policy metadata -> `blocked`;
- missing resource budget metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` network/offline plan only and never claims runtime behavior passed in TASK-007;
- notes and artifact references are redacted before output.

## WebView/Payment Safe Runner

`automation/webview_payment_safe_runner/` contains the TASK-008 WebView/payment safe QA plan report generator. It is a local dry-run utility and does not interact with an Android device, app binary, WebView, browser, redirect target, payment flow, backend, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing WebView fixture policy metadata -> `blocked`;
- missing staging-only non-real-payment policy metadata -> `blocked`;
- missing synthetic user policy metadata -> `blocked`;
- missing resource budget metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` WebView/payment plan only and never claims runtime or payment behavior passed in TASK-008;
- notes, flow aliases and artifact references are redacted before output.

## Compatibility/Device Matrix

`automation/compatibility_device_matrix/` contains the TASK-009 compatibility/device matrix report generator. It is a local dry-run utility and does not interact with an Android device, app binary, WebView, WebRTC session, payment flow, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved device matrix policy metadata -> `blocked`;
- missing approved target class metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing synthetic fixture policy metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` compatibility matrix only and never claims runtime behavior passed in TASK-009;
- notes and artifact references are redacted before output.

## CI/Nightly Smoke

`automation/ci_nightly_smoke/` contains the TASK-010 CI/nightly smoke plan report generator. It is a local dry-run utility and does not create live CI schedules, access CI secrets, upload artifacts, install private dependencies, or interact with an Android device, app binary, WebView, WebRTC session, payment flow, network service or production environment.

The generator is designed to fail closed:

- missing approved static CI scope metadata -> `blocked`;
- missing approved schedule policy metadata -> `blocked`;
- missing repository safety policy metadata -> `blocked`;
- missing resource budget metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing artifact retention policy metadata -> `blocked`;
- missing dependency policy metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` CI/nightly plan only and never claims live CI, runtime or device behavior passed in TASK-010;
- notes, CI job aliases and artifact references are redacted before output.

## Navigation Transition Map

`automation/navigation_transition_map/` contains the TASK-011 navigation transition map report generator. It is a local dry-run utility and does not interact with an Android device, app binary, WebView, WebRTC session, payment flow, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing transition scope metadata -> `blocked`;
- missing screen alias policy metadata -> `blocked`;
- missing input event policy metadata -> `blocked`;
- missing fixture policy metadata -> `blocked`;
- missing resource budget metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` navigation transition plan only and never claims runtime transition behavior passed in TASK-011;
- notes, transition aliases and artifact references are redacted before output.

## Quality Guards

`automation/quality/` contains local static repository hygiene and public-safety
guards. These tools do not interact with Android devices, APKs, WebView,
WebRTC, payment flows, network services or production systems.

- `full_tree_hygiene_scan.py` scans tracked/public-safe text trees for
  whitespace, EOF and JSON BOM hygiene.
- `public_repo_safety_scan.py` scans tracked/public-repository paths for
  forbidden raw artifact families such as APKs, raw evidence, signing material,
  local config and local-only artifact directories. It reports only rule ids,
  paths and category-level reasons, never matched file contents.
- `synthetic_redaction_corpus.py` defines fabricated public-safe redaction test
  specimens for TASK-017. It is local/static only and must not be populated
  from real evidence, APKs, endpoints, QR targets, credentials or device data.

## Safety Rules

Automation in this repository must not request or store:

- source or decompiled application code;
- secrets, tokens, cookies, sessions or credentials;
- private endpoint inventories;
- APK, AAB, DEX, native or signing artifacts;
- raw logs, screenshots or videos;
- real user data or real payment data.

Runtime/device execution belongs to a future approved task after prerequisites, redaction and review gates are satisfied.

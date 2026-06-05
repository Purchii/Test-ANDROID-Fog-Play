# Testing strategy summary

## Principle

Use risk-based, evidence-first, black-box Android TV testing. Do not rely on source code, decompiled code, private endpoints or secrets.

## Test groups

- smoke;
- regression;
- critical path;
- exploratory;
- compatibility;
- WebView/hybrid;
- permissions/exported components;
- deeplinks/intent entry;
- network/offline;
- update/install/backup;
- accessibility/localization;
- security-oriented QA without bypass.

## First automation priority

1. Evidence schema and report writer.
2. runtime startup smoke skeleton.
3. Screenshot/redacted device logs redaction.
4. Initial focus/D-pad probe.
5. Direct `StreamActivity` guard skeleton.
6. Exported receiver benign guard skeleton.
7. Release gate summary.

## Do not start with

- full WebRTC E2E automation;
- real payment flows;
- private API contract tests;
- production load tests;
- security bypass testing;
- device matrix explosion before primary smoke is stable.

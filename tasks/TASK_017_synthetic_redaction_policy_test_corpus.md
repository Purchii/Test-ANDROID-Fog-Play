# TASK-017 - Synthetic redaction policy test corpus

## Task

Create a public-safe synthetic redaction policy test corpus and local checks
that exercise report validators and redactors against fabricated
sensitive-looking values.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-017 - Synthetic redaction policy test corpus
```

## Branch

```text
qa/task-017-redaction-policy-test-corpus
```

## Context

TASK-014 added a tracked-path public repository safety scan. That scan blocks
dangerous public file paths and artifact families, but it is intentionally not
a full content scanner or runtime validator.

TASK-017 complements it with a synthetic-only corpus for report validator and
redaction behavior. The corpus must never be built from `.qa_local`, APKs, raw
screenshots, logs, QR decode artifacts, private endpoints, credentials, device
identifiers, phone numbers or payment values.

## Production safety classification

TASK-017 is `PROD_SAFE` because it uses only fabricated repository-local data,
unit tests, static validation and documentation.

The following are `PROD_FORBIDDEN` in this task:

- ADB, APK read/install/launch, APK inspection or APK modification;
- runtime navigation, WebView, WebRTC, payment, stream, network/offline or live
  CI execution;
- traversal of ignored `.qa_local/` evidence roots;
- real secrets, tokens, cookies, sessions, credentials or private endpoints;
- real phone/OTP/device identifiers, QR targets, account values or payment
  values;
- publishing raw matched specimen values in command output.

## Scope

In scope:

- shared synthetic redaction corpus under `automation/quality/`;
- tests covering credential-like, token-like, URL/endpoint-like,
  route/deeplink-like, local/APK path-like, hash-like, device identifier-like,
  phone/OTP-like, payment/account-like, QR payload-like and raw evidence
  reference-like classes;
- tests proving relevant report validators reject or flag synthetic unsafe
  public report values;
- tests proving existing redactors remove synthetic sensitive-looking values
  from release/WebView-payment generated reports;
- source-of-truth documentation updates.

Out of scope:

- runtime evidence collection or replay;
- real local evidence inspection;
- broad pre-runtime approval hardening without a concrete synthetic corpus case;
- content scanning of ignored local artifacts;
- release, runtime or product-behavior claims.

## Acceptance criteria

- Every corpus entry is explicitly marked synthetic and public-safe.
- No corpus entry is copied from real local evidence or private product data.
- Corpus classes cover the sensitive-looking value families listed in scope.
- Tests fail closed when a validator/redactor misses a corpus class it is meant
  to cover.
- Test and CLI output use category/test ids, not raw specimen values.
- TASK-014 public repository safety scan and full-tree hygiene still pass.
- Source-of-truth docs state that TASK-017 does not approve or execute runtime,
  APK, WebView, WebRTC, payment, network or local raw evidence work.

## Verification

Required checks:

```bash
git status --short --branch
git diff --check
python -m pytest -q tests/test_synthetic_redaction_corpus.py tests/test_post_auth_navigation_report_validator.py tests/test_native_regression_report_validator.py tests/test_release_gate_report.py tests/test_webview_payment_safe_runner.py
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
```

Runtime/device/APK/WebView/WebRTC/browser/redirect/payment/backend/network/live
CI validation is not run for TASK-017.

## Stop conditions

Stop and ask for guidance if any requested change would require:

- real raw evidence, secrets, endpoints, QR targets, account/payment data or
  device identifiers;
- APK/device/runtime execution;
- executable production or Android command recipes;
- scanner output that prints raw matched specimen values;
- a failing check that cannot be fixed within the bounded task scope.

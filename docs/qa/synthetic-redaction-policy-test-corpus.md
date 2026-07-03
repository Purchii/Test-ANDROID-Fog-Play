# Synthetic redaction policy test corpus

Task: `TASK-017`

Production safety classification: `PROD_SAFE`

## Purpose

This corpus gives local validators and redactors fabricated sensitive-looking
inputs so they can be tested without touching real evidence, APKs, device
state, credentials, endpoints, accounts, payment data or QR targets.

It complements `docs/qa/public-repository-safety-scan.md`: TASK-014 blocks
dangerous tracked paths, while TASK-017 exercises content redaction and
public-report validation with synthetic values only.

## Corpus boundaries

Allowed:

- fabricated values with explicit `synthetic` provenance;
- reserved/example-style hostnames and aliases;
- local unit tests and static validation;
- category-level failure messages.

Forbidden:

- reading or copying `.qa_local/` raw evidence;
- APK read/install/launch or APK inspection;
- real secrets, phone/OTP values, device identifiers, QR targets, endpoints,
  account labels or payment data;
- WebView, WebRTC, payment, stream, network/offline or runtime execution;
- command output that prints raw matched specimen values.

## Required synthetic classes

The corpus must include at least one fabricated specimen for each class:

- credential-like key/value;
- token/session/cookie-like value;
- URL or endpoint-like value;
- route, deeplink or internal metadata-like value;
- local path and APK path-like value;
- hash-like value;
- device identifier-like value;
- phone and OTP-like value;
- payment and account-like value;
- QR payload-like value;
- raw screenshot, XML, log or video evidence reference-like value.

## Expected behavior

Validators should reject or flag unsafe public report values with
category-level reasons. Redactors should replace sensitive-looking substrings
with placeholders and avoid preserving raw specimens in generated public
reports.

Passing TASK-017 checks does not prove that real runtime evidence is safe. It
only proves that the synthetic corpus cases covered by the local tests are
handled by the exercised validators/redactors at command time.

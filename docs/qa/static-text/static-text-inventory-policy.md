# Static Text Inventory Policy

## Purpose

TASK-035 creates a public-safe static text coverage ledger without publishing
raw app strings. The ledger is designed for QA traceability, redaction review,
localization/accessibility planning and future runtime text visibility checks.

## Evidence status

Static reverse-analysis evidence is at most `likely` unless a later approved
runtime task confirms visibility or behavior on a device. TASK-035 does not
confirm screen reachability, translation quality, text truncation, TalkBack
behavior, payment behavior, backend behavior or dynamic catalog/server values.

## Raw value handling

Raw static text values must stay in ignored local storage:

```text
.qa_local/static_text_inventory/
```

Public artifacts may include:

- source aliases;
- counts;
- hash prefixes;
- length buckets;
- category counts;
- redaction class counts;
- coverage status;
- `not_run` / `unknown` runtime boundaries.

Public artifacts must not include:

- raw static text values;
- raw URLs, domains, endpoints, routes, deeplinks or query values;
- tokens, sessions, cookies, headers, OTP, captcha, phone, account or payment
  values;
- raw device identifiers;
- raw local paths, APK names or hashes;
- executable runtime, backend, API, payment or device recipes.

## Coverage statuses

`complete_full_raw_values_available` means the available sanitized source
contains a full raw static-text list and every value was inventoried locally.

`blocked_by_missing_full_static_text_values_source` means the source reports a
larger likely static text count than the raw values it exposes. In that case,
the task must inventory all available values and record the missing raw-value
count as a blocker for exact full-list coverage.

## TASK-035 source state

The current local sanitized reverse-analysis artifact reports `19187` likely UI
strings and exposes `160` raw sample strings. TASK-035 therefore provides full
coverage of the available sample values and a public-safe blocker for the
missing raw full list.

## Future work

Exact full raw-value coverage requires an approved local-only static string
export that does not require source code, decompiled code, smali, method bodies,
APK modification or public raw-value publication.

Runtime text visibility and truncation coverage requires a separate approved
runtime task with screenshots/visual inspection and redacted evidence.

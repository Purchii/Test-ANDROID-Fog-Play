# ADB Inventory Policy

Task: `TASK-015H/017C - Final scope-version/normalization polish + TASK-005 owner approval handoff finalization`

Production safety classification: `PROD_CONDITIONAL` for owner-approved local
ADB inventory only. Default CLI execution is `PROD_SAFE` and makes no ADB calls.

## Two-Phase Hard Gate

TASK-015D/016C Phase A is approval hardening. TASK-016C Phase B is blocked until
Phase A passes.

Phase B remains inventory-only even when approved. It cannot install, launch,
smoke test, collect runtime evidence or approve TASK-005.

## Allowed Scope

TASK-016C may run only inventory commands through
`automation/device_inventory/generate_adb_device_inventory.py --allow-adb`
after the Phase A hard gate passes and owner approval is present.

Allowed commands:

```text
adb devices -l
adb -s <serial> shell getprop ro.product.manufacturer
adb -s <serial> shell getprop ro.product.model
adb -s <serial> shell getprop ro.build.version.release
adb -s <serial> shell getprop ro.build.version.sdk
adb -s <serial> shell getprop ro.build.version.security_patch
adb -s <serial> shell wm size
adb -s <serial> shell wm density
adb -s <serial> shell pm list features
```

Forbidden in this task:

```text
adb install
am start
monkey
logcat
screenshots
screenrecord
APK runtime smoke
WebView
WebRTC
payment
account/profile mutation
decompile
patch
resign
security bypass
```

## Local Storage

Raw outputs and alias maps must stay ignored under `.qa_local/devices/`:

```text
.qa_local/devices/raw_adb_devices.json
.qa_local/devices/serial_alias_map.json
.qa_local/devices/preflight_report.json
.qa_local/devices/device_inventory.public_safe.generated.json
```

These files must not be committed.

TASK-016C output path validation must happen before any ADB invocation. Raw
output, alias map, generated public-safe inventory and preflight report paths
must all stay under `.qa_local/devices/`; absolute paths, `..`, repository docs
paths, `/tmp`-style public leakage and IP/identifier-like path segments block
the command before ADB is called.

Phone-category secondary devices may use public-safe aliases such as
`phone-samsung-001` and `phone-samsung-a14-001`. This does not make them
eligible P0 TASK-005 targets; TASK-005 still requires a manual-confirmed P0
Android TV/STB D-pad target.

## Manual Review Workflow

1. TASK-015D Phase A approval hardening passes.
2. TASK-016C collects raw local-only ADB inventory when owner approval is
   present and devices are visible.
3. TASK-016C generates public-safe inventory with heuristic classification and
   `manual_review_required: true`.
4. Owner/QA reviews aliases, categories, form factor, input method and target
   priority.
5. Approved TASK-005 metadata copies selected targets as `manual_confirmed` and
   `manual_review_required: false`.
6. Only then can the approval validator return `approved_for_limited_runtime`.

No TASK-016C output confirms app launch, first visible state, focus behavior,
WebView, WebRTC, payment or runtime smoke.

## TASK-015E/017 Owner-Review Export

After the Phase A gate passes, TASK-015E/017 may derive a committed owner-review
file from the ignored generated public-safe inventory only if:

- `public_safety_findings` is empty;
- all redaction guarantees are true;
- no raw ADB serial, IP, MAC, IMEI, Android ID, Google account, full
  fingerprint, phone, OTP, owner label or raw `.qa_local` path is present;
- runtime, APK install and app launch statuses are all `not_run`;
- every generated device remains `classification_confidence: heuristic`;
- every generated device remains `manual_review_required: true`.

The review export is owner-review material only. It is not TASK-005 approval and
must not mark devices `manual_confirmed`.

TASK-015F/017A hardens the owner-review export validator. Before export, the
tool must reject malformed stable or runtime aliases, stable aliases containing
Android-version tokens, runtime aliases that do not preserve stable alias
prefix/index and Android major, alias/form-factor mismatches, Android
major/API sanity mismatches, duplicate aliases, `public_device_count` mismatch,
unknown public device fields and any device that is not
heuristic/manual-review-required/not-run.

TASK-015G/017B additionally requires owner-review export validation to reject
missing or extra redaction guarantee keys, any redaction guarantee value other
than `true`, malformed category/priority/form-factor/input/ADB/Google Play
services/screen-class enum values and any auto-promotion to
`manual_confirmed`.

TASK-015H/017C additionally requires owner-review export validation to reject
generated inventory metadata that is not public-safe generated output:
unsupported source values such as `raw_adb_inventory`, non-redacted non-empty
device payloads, invalid or future-dated `generated_at_utc`, missing or
mismatched `public_device_count`, and empty device lists.

The owner handoff is recorded in:

```text
docs/approvals/task005_owner_device_review.md
```

# ADB Inventory Policy

Task: `TASK-015C/016B - Approval/device-inventory consistency polish and local ADB inventory readiness`

Production safety classification: `PROD_CONDITIONAL` for owner-approved local
ADB inventory only. Default CLI execution is `PROD_SAFE` and makes no ADB calls.

## Allowed Scope

TASK-016B may run only inventory commands through
`automation/device_inventory/generate_adb_device_inventory.py --allow-adb`.

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

Phone-category secondary devices may use public-safe aliases such as
`phone-samsung-001` and `phone-samsung-a14-001`. This does not make them
eligible P0 TASK-005 targets; TASK-005 still requires a manual-confirmed P0
Android TV/STB D-pad target.

## Manual Review Workflow

1. TASK-016B collects raw local-only ADB inventory when devices are visible.
2. TASK-016B generates public-safe inventory with heuristic classification.
3. Owner/QA reviews aliases, categories, form factor, input method and target
   priority.
4. Approved TASK-005 metadata copies selected targets as `manual_confirmed` and
   `manual_review_required: false`.
5. Only then can the approval validator return `approved_for_limited_runtime`.

No TASK-016B output confirms app launch, first visible state, focus behavior,
WebView, WebRTC, payment or runtime smoke.

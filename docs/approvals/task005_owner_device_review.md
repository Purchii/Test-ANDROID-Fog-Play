# TASK-005 Owner Device Review

Task: `TASK-015H/017C - Final scope-version/normalization polish + TASK-005 owner approval handoff finalization`

Status: `owner_review_required`

This guide is a public-safe handoff for manual owner/QA review only. It does
not approve TASK-005 runtime execution, APK install, app launch, logcat,
screenshots, videos, WebView, WebRTC, stream/media playback, payment,
subscription, purchase or production mutation.

After TASK-015H/017C, broad pre-runtime infrastructure hardening should stop
unless a new concrete false-pass is found. Owner/QA should move to selecting one
P0 TV/STB target, preparing local APK/hash and evidence approvals, filling real
approval metadata and opening a separate TASK-005 limited runtime smoke task.

Source inventory:

```text
docs/approvals/device_inventory.public_safe.review.json
```

## P0 TV/STB Candidates

| Device alias | Runtime profile alias | Form factor | Category | Android/API | Input | Google Play services | Screen class |
|---|---|---|---|---|---|---|---|
| `stb-sberdevices-009` | `stb-sberdevices-a13-009` | `stb` | `android_tv` | `13 / 33` | `dpad_remote` | `unknown` | `fhd_or_unknown` |
| `tv-himedia-010` | `tv-himedia-a13-010` | `tv` | `android_tv` | `13 / 33` | `dpad_remote` | `unknown` | `fhd_or_unknown` |
| `tv-tpv-005` | `tv-tpv-a11-005` | `tv` | `android_tv` | `11 / 30` | `dpad_remote` | `yes` | `fhd_or_unknown` |
| `tv-salutetv-011` | `tv-salutetv-a13-011` | `tv` | `android_tv` | `13 / 33` | `dpad_remote` | `unknown` | `fhd_or_unknown` |
| `tv-yandex-012` | `tv-yandex-a9-012` | `tv` | `android_tv` | `9 / 28` | `dpad_remote` | `yes` | `fhd_or_unknown` |
| `tv-tpv-013` | `tv-tpv-a12-013` | `tv` | `android_tv` | `12 / 31` | `dpad_remote` | `yes` | `4k_or_unknown` |

## Required Manual Review

Owner/QA must manually confirm all of the following before any selected target
can be copied into real TASK-005 approval metadata:

- form factor is actually TV/STB and not a phone/tablet/emulator;
- D-pad or remote input is stable enough for the limited smoke;
- `priority` should remain `P0` for the selected TASK-005 target;
- ADB stability is acceptable for the intended lab setup;
- alias does not reveal owner, room, serial, IP, account or other private data;
- Android major and API level are plausible for the target profile.

Generated inventory must not be copied blindly. Every exported device is still:

```text
classification_confidence: heuristic
manual_review_required: true
runtime_execution_status: not_run
apk_install_status: not_run
app_launch_status: not_run
```

No device in the review inventory is automatically marked
`manual_confirmed`. A selected target may become `manual_confirmed` only after
owner/QA review, and only in a future approval metadata update.

TASK-005 remains blocked until owner/QA also provides:

- local APK under `.qa_local/apks/task-005/app-under-test.apk`;
- local SHA-256 evidence record;
- explicit screenshots/logcat/video/retention approval;
- confirmed synthetic QA user local secret file;
- filled real approval metadata and required reviewer approvals;
- a separate limited TASK-005 runtime smoke task.

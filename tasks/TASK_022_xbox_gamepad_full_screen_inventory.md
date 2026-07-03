# TASK-022 - Xbox-like gamepad full screen inventory

## Task

Conduct a full screen-family inventory on the approved MTC Fog Play Android TV
lane using Xbox-like/gamepad-style ADB keyevents, then compare the result with
the prior TASK-020 D-pad full inventory.

## Mode

`NON_AUTONOMOUS`

## Branch

```text
qa/task-022-xbox-gamepad-screen-inventory
```

## Runtime lane

- `device_alias`: `tv-tpv-013`
- `runtime_profile_alias`: `tv-tpv-a12-013`
- `build_alias`: `task-005-local-apk-001`
- `synthetic_user_alias`: `qa-user-phone-001`
- `input_profile`: `adb_emulated_xbox_like_gamepad_keyevents`

## Production safety

- `PROD_SAFE`: docs, planning, local JSON validation, public-safe summaries,
  hygiene scans and diff review.
- `PROD_CONDITIONAL`: bounded Android TV runtime inventory on the approved lane
  using ADB-emulated gamepad keyevents, with local-only raw evidence and
  redaction-by-default.
- `PROD_FORBIDDEN`: payment, purchase, checkout completion, stream/session
  start, external QR/browser/WebView traversal, captcha solving/bypass, private
  endpoint extraction, proxy/packet capture/TLS bypass, APK modification,
  source/decompiled code access, raw evidence publication and real account
  mutation.

Physical controller pairing, reset, remap and detection mutation are not
approved by this task. TASK-022 samples ADB keyevents that emulate Xbox-like
buttons.

## Scope

In scope:

- safe use of `KEYCODE_BUTTON_A/B/X/Y`, `KEYCODE_BUTTON_START`,
  `KEYCODE_BUTTON_SELECT`, `KEYCODE_BUTTON_L1/R1`, D-pad directions and
  `DPAD_CENTER` where needed;
- checkpointed screen-family inventory with screenshot/visual inspection plus
  UIAutomator XML when available;
- recurrence tracking against TASK-020/TASK-021 public-safe aliases;
- bottom-right navigation hint inspection;
- game detail, tariff/server and connect-device boundary inspection without
  starting payment or a real stream/session;
- QR surfaces as local-only decoded evidence when needed, without opening any
  target;
- safe recovery through `BUTTON_B`/Back, Home/foreground and force-stop plus
  approved explicit relaunch helper if needed.

Out of scope:

- complete game-title data enumeration;
- broad compatibility or controller matrix;
- network/offline manipulation;
- payment/WebView/external traversal;
- physical controller setup mutation;
- profile/account mutation beyond approved synthetic auth/session continuity.

## Acceptance criteria

1. `docs/context/handoff/active-run.md` declares TASK-022 scope, mode, branch,
   runtime lane, safety classification, evidence storage and stop conditions.
2. Runtime checkpoints are stored locally under ignored
   `.qa_local/evidence/task-022/<run-id>/`.
3. Public-safe summary exists at
   `docs/qa/reports/task022_xbox_gamepad_full_screen_inventory.summary.json`.
4. Closure ledger classifies every approved safe reachable screen family/branch
   as `covered`, `blocked_by_boundary`, `blocked_by_tooling`,
   `blocked_by_external_state` or `not_run_out_of_scope`.
5. Differences from TASK-020 are explicit, especially bottom-right navigation
   hints and the screen after selecting a concrete game server.
6. No raw phone/OTP, device identifiers, QR targets, screenshots, XML, logs,
   videos, APK paths/hashes, server/tariff/payment values or private endpoints
   are committed or published.
7. Verification and multi-agent QA/Security review complete before final report.

## Stop conditions

Stop before payment, stream/session start, external QR/browser/WebView traversal,
captcha solving/bypass, physical gamepad reset/remap/pairing mutation, unclear
confirm target, unrecoverable focus trap, crash/ANR recurrence, raw-value
publication risk, failed cleanup/relaunch recovery or any need for secrets,
private endpoints, source/decompiled code or APK modification.

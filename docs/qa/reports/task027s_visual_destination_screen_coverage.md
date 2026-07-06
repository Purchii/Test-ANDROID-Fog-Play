# TASK-027S visual destination screen coverage

Mode: `NON_AUTONOMOUS`

Public-safe machine-readable report:
`docs/qa/reports/task027s_visual_destination_screen_coverage.summary.json`

## Result

TASK-027S did not visually cover the three unresolved TASK-027R rail
destinations. Session journal, Steam/top-up QR and feedback QR remain
`blocked_by_app_shell_loader_and_prior_rail_input_blocker` for this task.

TASK-027S did cover a new app entry surface category: Google TV launcher /
recommendations entry. Activating that visible entry did not reach a usable
catalog or any target destination. It reached a recurring anomalous app shell
loader state, now tracked as:

```text
app_shell_loader_after_launcher_entry
```

This state has the in-app rail visible, but the content area remains on a
spinner/loader and XML exposes no focused, clickable or scrollable target nodes
for the visible rail state. TASK-027S now uses a 120-second timeout for this
preloader condition: after the timeout, collect local-only diagnostics, record
the anomaly and move on. It must not be counted as catalog, session journal,
Steam/top-up QR, feedback QR or successful app entry.

## Evidence

Public-safe TASK-027S checkpoint IDs:

- `rt027s-cp057-launch-wait`;
- `rt027s-cp058-post-launch`;
- `rt027s-cp059-after-12-dpad-down`;
- `rt027s-cp060-after-30-dpad-down`;
- `rt027s-cp061-after-deep-dpad-left`;
- `rt027s-cp062-after-rail-dpad-down-1`;
- `rt027s-cp063-after-rail-dpad-down-2`;
- `rt027s-cp064-monkey-launch`;
- `rt027s-cp065-monkey-launch-wait`;
- `rt027s-cp066-launcher-recommendations-pre-entry`;
- `rt027s-cp067-after-visible-app-icon-entry`;
- `rt027s-cp068-after-entry-wait`;
- `rt027s-cp069-loader-rail-start`;
- `rt027s-cp073-after-wake-home`;
- `rt027s-cp074-after-entry-short-wait`;
- `rt027s-cp075-after-rail-down-to-journal-candidate`;
- `rt027s-cp076-after-journal-center`;
- `rt027s-cp077-after-rail-down-to-steam-candidate`;
- `rt027s-cp078-after-steam-center`;
- `rt027s-cp079-after-rail-down-to-feedback-candidate`;
- `rt027s-cp080-after-feedback-center`;
- `rt027s-cp081-loader-rail-before-icon-taps`;
- `rt027s-cp082-after-loader-journal-icon-tap`;
- `rt027s-cp083-after-loader-steam-icon-tap`;
- `rt027s-cp084-after-loader-feedback-icon-tap`;
- `rt027s-cp086-loader-timeout-after-2min`.

Local-only developer handoff archive for internal debugging was created under
ignored evidence storage. It contains screenshots, XML, app/process logcat when
available, crash-buffer capture, activity/window/input dumps and public-safe
repro notes. It must not be committed or published.

## Destination Ledger

| Destination | Status | Evidence status | Evidence IDs |
|---|---|---|---|
| Session journal | `blocked_by_app_shell_loader_and_prior_rail_input_blocker` | `confirmed` | `rt027s-cp076-after-journal-center`, `rt027s-cp082-after-loader-journal-icon-tap`, `rt027s-cp086-loader-timeout-after-2min`, prior TASK-027R no-destination checkpoints |
| Steam/top-up QR | `blocked_by_app_shell_loader_and_prior_rail_input_blocker` | `confirmed` | `rt027s-cp078-after-steam-center`, `rt027s-cp083-after-loader-steam-icon-tap`, `rt027s-cp086-loader-timeout-after-2min`, prior TASK-027R no-destination checkpoints |
| Feedback QR | `blocked_by_app_shell_loader_and_prior_rail_input_blocker` | `confirmed` | `rt027s-cp080-after-feedback-center`, `rt027s-cp084-after-loader-feedback-icon-tap`, `rt027s-cp086-loader-timeout-after-2min`, prior TASK-027R no-destination checkpoints |
| Google TV launcher/recommendation entry | `covered_as_entry_surface` | `confirmed` | `rt027s-cp066-launcher-recommendations-pre-entry`, `rt027s-cp067-after-visible-app-icon-entry`, `rt027s-cp086-loader-timeout-after-2min` |

## Anomaly

`ANOM-027S-001` records the frequent app shell loader after launcher entry.
Expected result was a loaded post-auth app destination. Observed result was
in-app shell rail plus persistent content loader through a 120-second timeout.
Likely/hypothesis causes: launcher-entry shell hydration or content bootstrap
stall, unresolved profile/session/entitlement bootstrap without a visible error
state, route host stuck in preloader, or rail focus/action registration waiting
for content bootstrap. The test implication is that future automation must
detect this state, collect diagnostics and stop or recover instead of promoting
it to catalog or destination coverage.

`ANOM-027S-003` records a TV/system ambient interruption during idle runtime and
keeps it out of app coverage. `ANOM-027S-004` records that bounded D-pad/center
and direct taps on visible rail icon regions from the loader did not reach
session journal, Steam/top-up QR or feedback QR destination screens.

## Boundaries

No payment, paid session, stream/WebRTC/media playback, external QR/browser
traversal, Steam/account mutation, profile/account mutation, network/offline
manipulation, captcha solving/bypass, APK modification or security bypass was
performed. Raw screenshots, XML, logs, APK hashes, package/component values,
device identifiers, account-like values and QR targets remain local-only.

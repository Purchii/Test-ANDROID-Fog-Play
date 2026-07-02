# Startup and Focus Smoke Charter

Task: `TASK-001 - Runtime discovery and smoke bootstrap`

Production safety classification: `PROD_SAFE` as a planning charter. Runtime execution is out of scope until approved build/device/config are available in a future task.

## Mission

Establish a minimal Android TV black-box smoke shape for startup and first-focus confidence without claiming runtime behavior before evidence exists.

## Scope

In scope:

- startup readiness categories;
- first visible state and focus expectations;
- redacted evidence requirements;
- blocked behavior when prerequisites are absent;
- release-gate signals for future execution.

Out of scope:

- runtime/device execution in TASK-001;
- source or decompiled inspection;
- private endpoint discovery;
- APK modification;
- bypasses or security control changes;
- real payments or real-user-impacting actions.

## Preconditions

The smoke is blocked until a task run records:

| Precondition | Required state | Current status |
|---|---|---:|
| Build | Approved QA build identifier and handling rules. | `unknown` |
| Target | Approved Android TV device or emulator target. | `unknown` |
| Configuration | Approved environment and fixture boundaries. | `unknown` |
| Evidence handling | Redaction policy and storage path. | `unknown` |
| Operator audit | Task branch, operator and timestamp. | `unknown` |

## Smoke Questions

Each question must be answered with evidence status `confirmed`, `likely`, `hypothesis` or `unknown`.

| ID | Question | Default status before runtime evidence |
|---|---|---:|
| SF-001 | Does the app reach a stable first visible state? | `unknown` |
| SF-002 | Is there a visible focus target suitable for TV remote navigation? | `unknown` |
| SF-003 | Can focus move away from the first target without a trap? | `unknown` |
| SF-004 | Does Back/Home behavior avoid crash, ANR or unrecoverable state? | `unknown` |
| SF-005 | Are auth/session-dependent areas guarded when fixtures are absent? | `unknown` |
| SF-006 | Are evidence artifacts redacted before being referenced? | `unknown` |

## Severity Guidance

| Signal | Suggested risk level | Evidence status rule |
|---|---:|---|
| App cannot reach first visible state. | R0 | `confirmed` only with approved runtime evidence. |
| No usable TV focus target on first screen. | R1 | `confirmed` only with approved runtime evidence. |
| Focus trap blocks startup navigation. | R1 | `confirmed` only with approved runtime evidence. |
| Protected flow opens without approved session state. | R0/R1 | `confirmed` only with approved runtime evidence and product/security review. |
| Evidence is not redacted. | R0/R1 | `confirmed` when raw private content is observed in a public/reportable path. |

## Report Expectations

The smoke report must include:

- `task_id`;
- `mode`;
- `production_safety_classification`;
- `overall_status`;
- `evidence_status`;
- prerequisite status;
- blocked reasons when applicable;
- redaction status;
- risks and unknowns;
- verification commands run;
- reviewer notes.

## TASK-001 Execution Rule

For TASK-001, the only runnable behavior is local report generation. If approved build, target or configuration are absent, the generator must produce a `blocked` report. It must not attempt runtime interaction or claim a pass.

## TASK-005 Limited Runtime Data Point

On 2026-07-02, a separate `NON_AUTONOMOUS` TASK-005 run executed the limited
startup/focus scope on the owner-selected target represented by `tv-tpv-013` /
`tv-tpv-a12-013`.

Confirmed for that one target/build:

- selected local APK presence and local-only hash record;
- ADB target identity match;
- ordinary install/update;
- launch to an auth/profile guard first visible state;
- initial focus with focusable UI;
- minimal directional D-pad movement;
- Back/Home and foreground relaunch;
- force-stop/relaunch;
- no observed crash/ANR signal in the captured summary.

Still not run:

- synthetic login, phone/OTP entry and profile/account mutation;
- WebView, redirect, WebRTC, stream/media playback and payment flows;
- network/offline execution;
- compatibility/device matrix coverage;
- broader device/build coverage.

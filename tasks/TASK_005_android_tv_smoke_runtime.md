# TASK-005 - Android TV limited runtime smoke on tv-tpv-013

## Task

Execute a narrow Android TV install/launch/focus smoke on the owner-selected
target represented by `tv-tpv-013` using the owner-selected local APK.

## Mode

`NON_AUTONOMOUS`

## Thread title

```text
TASK-005 - Android TV limited runtime smoke on tv-tpv-013
```

## Branch

```text
qa/task-005-android-tv-smoke-runtime
```

## Context

Earlier TASK-005 attempts were blocked because runtime prerequisites were not
available in the active checkout. This run used the normal local checkout,
where the owner-provided APK bundle exists under ignored `.qa_local/` storage.

The owner confirmed for this run:

- selected physical test target is represented publicly as `tv-tpv-013`;
- runtime profile alias is `tv-tpv-a12-013`;
- selected APK is represented publicly as `task-005-local-apk-001`;
- install-conflict cleanup is allowed only for this selected target and APK.

## Scope

In scope:

- local branch/default status;
- selected APK presence under `.qa_local/apks/task-005/`;
- local-only APK hash record;
- ADB tooling and target identity gate;
- selected APK install/update;
- app launch and first visible state;
- initial focus and minimal D-pad directional movement;
- Back/Home and foreground relaunch;
- force-stop/relaunch;
- crash/ANR logcat observation;
- redacted evidence summary.

Out of scope:

- WebView, redirect or private URL flows;
- WebRTC, stream, media playback or player flows;
- payment, subscription, purchase, billing or checkout flows;
- real user data, profile/account mutation or production mutation;
- source/decompiled code, smali or method bodies;
- APK patching, resigning or modification;
- TLS/pinning/security bypass, proxy or packet capture;
- raw evidence publication.

## Production Safety

Runtime execution is `PROD_CONDITIONAL` and is allowed only because the owner
provided run-specific approval for the selected local APK and selected physical
Android TV target.

Raw artifacts must remain ignored under:

```text
.qa_local/evidence/task-005/
```

Public docs and reports may include only public-safe aliases, status values,
redacted artifact references and category-level observations.

## Acceptance Criteria

- The task runs on a branch created from the detected default branch.
- The selected APK exists locally and is not committed.
- A local-only SHA-256 record exists but the hash value is not published.
- ADB tooling is present and the selected target identity matches
  `tv-tpv-013 / tv-tpv-a12-013`.
- Ordinary install/update succeeds, or the owner-approved conflict-only
  uninstall/install path is used.
- App launch reaches an observable first visible state.
- The first visible state is summarized with no raw screenshot in public docs.
- Initial focus and at least one minimal directional D-pad path are observed.
- Back/Home and foreground relaunch do not show crash/ANR evidence.
- Force-stop/relaunch returns to an app-visible state.
- Crash/ANR observation is recorded as a redacted summary only.
- WebView, WebRTC, stream/media playback, payment and production mutation remain
  `not_run`.

## Result

The 2026-07-02 run passed the limited scope:

- selected APK presence: `pass`, `confirmed`;
- target identity: `pass`, `confirmed`;
- install/update: `pass`, `confirmed`;
- launch/foreground: `pass`, `confirmed`;
- first visible state: auth/profile guard screen, `confirmed`;
- initial focus: one focused element with focusable UI, `confirmed`;
- minimal D-pad: down/right/up movement changed focus, `confirmed`;
- Back/Home/foreground: `pass`, `confirmed`;
- force-stop/relaunch: `pass`, `confirmed`;
- crash/ANR signal: `not_observed`, `confirmed`.

No synthetic login was attempted. No phone number, OTP or account data was
entered. No WebView, WebRTC, stream/media playback or payment route was entered.

## Verification

Required repository checks:

```text
git status --short --branch
git diff --check
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python -m pytest -q tests/test_approval_metadata_validator.py tests/test_runtime_smoke_bootstrap.py tests/test_full_tree_hygiene_scan.py
python -m compileall -q automation tests
```

Runtime evidence is local-only under `.qa_local/evidence/task-005/`.

## Stop Conditions

Stop if the task requires raw identifier publication, raw APK hash publication,
private endpoint capture, source/decompiled inspection, APK modification,
security bypass, real payments, WebView/WebRTC/stream playback, production
mutation, real user data, broader cleanup than approved or default branch
merge/push without explicit user command.

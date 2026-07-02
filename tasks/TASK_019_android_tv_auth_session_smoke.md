# TASK-019 - Android TV auth/session smoke on tv-tpv-013

## Task

Execute the first bounded auth/session smoke after the TASK-005 startup/focus
smoke on the owner-selected Android TV target represented publicly by
`tv-tpv-013` / `tv-tpv-a12-013`.

## Mode

`NON_AUTONOMOUS`

## Thread title

```text
TASK-019 - Android TV auth/session smoke on tv-tpv-013
```

## Branch

```text
qa/task-019-android-tv-auth-session-smoke
```

## Production safety

Repository checks, docs and validator tests are `PROD_SAFE`.

Runtime auth/session execution is `PROD_CONDITIONAL` and was run only after:

- Phase A repository checks passed;
- `.qa_local/secrets/qa_user.env` preflight passed without printing values;
- selected public-safe target/build aliases matched the prior TASK-005 lane;
- raw evidence stayed under ignored `.qa_local/evidence/task-019/`.

## Scope

In scope:

- selected target identity preflight for `tv-tpv-013` / `tv-tpv-a12-013`;
- selected build alias `task-005-local-apk-001`;
- app launch to auth/profile guard;
- bounded synthetic phone/OTP auth using local-only secrets;
- first post-auth shell alias;
- initial post-auth focus movement;
- Home/foreground session persistence;
- force-stop/relaunch session persistence;
- crash/ANR summary;
- redacted public-safe summary.

Out of scope:

- WebView, redirect or private URL flows;
- WebRTC, stream, media playback or player flows;
- payment, subscription, purchase, billing or checkout flows;
- network/offline experiments;
- profile/account mutation beyond bounded session persistence observation;
- private endpoint extraction, proxy, packet capture or TLS/security bypass;
- APK patching, resigning or decompilation;
- broad post-auth navigation or compatibility matrix coverage.

## Result

The 2026-07-02 run passed the bounded TASK-019 auth/session scope:

| Check | Status | Evidence status | Notes |
|---|---:|---:|---|
| Phase A repository checks | `pass` | `confirmed` | Required hygiene, tests, compileall and validator dry-runs passed. |
| Secret preflight | `pass` | `confirmed` | Required keys existed, values were non-empty and alias matched; raw values were not printed. |
| Target identity | `pass` | `confirmed` | Public aliases matched `tv-tpv-013` / `tv-tpv-a12-013`. |
| Build presence | `pass` | `confirmed` | Selected build alias remained `task-005-local-apk-001`. |
| App installed/launch | `pass` | `confirmed` | App launched to the auth/profile guard. |
| Auth input | `pass` | `confirmed` | Phone field used its UI prefix plus the remaining digits via on-screen keyboard; OTP was entered locally only. |
| Auth result | `pass` | `confirmed` | Login reached first post-auth shell. |
| Post-auth screen alias | `post_auth_home_unknown` | `confirmed` | Alias only; no broad navigation was performed. |
| Post-auth focus | `pass` | `confirmed` | Minimal post-auth focus movement was observed. |
| Home/foreground session | `pass` | `confirmed` | Session persisted after Home/foreground relaunch. |
| Force-stop/relaunch session | `pass` | `confirmed` | Session persisted after force-stop/relaunch. |
| Crash/ANR summary | `not_observed` | `confirmed` | No crash/ANR signal was observed in the captured summary. |
| Logout | `not_run` | `unknown` | Left out of scope to avoid profile/account mutation ambiguity. |

Local reviewed redacted summary:

```text
.qa_local/evidence/task-019/task-019-20260702T085719Z/redacted/auth_session_summary.redacted.json
```

## Important debug note

Early TASK-019 attempts exposed a UI automation input issue: ADB text/keyevent
entry did not correctly populate the phone field. The passing run used the
visible on-screen numeric keyboard and the field's built-in phone prefix. Those
failed input-method attempts are local-only debug evidence and are not credential
or OTP verdicts.

## Verification

Required checks were run before and after changes. Final recorded commands:

```text
git status --short --branch
git diff --check
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python -m pytest -q tests/test_approval_metadata_validator.py tests/test_runtime_smoke_bootstrap.py tests/test_full_tree_hygiene_scan.py
python -m pytest -q
python -m compileall -q automation tests
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.example.json
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.task005.draft.json
```

## Not run

WebView, redirect, WebRTC, stream/media playback, payment/subscription/purchase,
network/offline, compatibility matrix, broad post-auth navigation, private
endpoint extraction, packet capture/proxy/TLS bypass and profile mutation remain
`not_run`.

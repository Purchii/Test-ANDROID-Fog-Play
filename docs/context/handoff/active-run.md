# Active run

## Run metadata

Mode: `NON_AUTONOMOUS`
Thread title: `TASK-020 XL+ - Post-auth native navigation transitions`
Thread status: `runtime_partial_navigation_coverage_executed_task_branch`
Fresh thread verified: `current_thread_has_task020_prompt_from_owner_archive; current thread id recorded by goal tool`
Task ID: `TASK-020`
Task branch: `qa/task-020-xl-post-auth-navigation-transitions`
Default branch: `main`
Base commit: `ac2e11a2643c7cd4b4834e056b70c3a18fc0f7ad`
Merge/push authority: `NON_AUTONOMOUS; do not merge or push default branch without explicit user command`
Production safety classification: `PROD_SAFE` for Phase A docs, validators,
mocked tests and default fail-closed runner; `PROD_CONDITIONAL` for any later
approved local runtime navigation collection on the selected TASK-005/TASK-019
lane.

## Goal

Implement TASK-020 as a bounded post-auth native navigation coverage layer for
the already validated lane:

- `device_alias`: `tv-tpv-013`;
- `runtime_profile_alias`: `tv-tpv-a12-013`;
- `build_alias`: `task-005-local-apk-001`;
- `synthetic_user_alias`: `qa-user-phone-001`.

The task covers fail-closed Phase A tooling/docs first. Runtime Phase B/C may
run only after Phase A passes and selected-lane prerequisites are still safe and
available. Payment, WebView/redirect, stream/WebRTC/media playback,
profile/account mutation, network/offline manipulation, private endpoint
extraction, proxy/packet capture, APK modification/decompilation and raw
evidence publication remain out of scope.

## Phase A result

Initial implementation added:

- TASK-020 task spec and QA policy docs;
- fail-closed `automation/post_auth_navigation` runner and report validator;
- mocked unit tests for default blocking, output path boundaries, boundary
  detection, alias/report safety and session checkpoint requirements.

Targeted test result so far:

| Check | Status | Notes |
|---|---:|---|
| `python -m pytest -q tests/test_post_auth_navigation_probe.py tests/test_post_auth_navigation_report_validator.py` | `pass` | `23 passed, 1 skipped`; includes QA A false-pass regressions and direct validator script invocation. |
| `python automation/post_auth_navigation/run_post_auth_navigation_probe.py` | `pass` | Default output is `overall_status=blocked`, `runtime_execution_status=not_run`; no runtime call. |

Full Phase A verification passed:

| Check | Status | Notes |
|---|---:|---|
| `git status --short --branch` | `pass` | On `qa/task-020-xl-post-auth-navigation-transitions`; only intended TASK-020 changes present. |
| `git diff --check` | `pass` | No whitespace diff errors. |
| `python automation/quality/full_tree_hygiene_scan.py` | `pass` | Full tracked-tree hygiene passed. |
| `python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree` | `pass` | Public-safe tree hygiene passed. |
| TASK-020 targeted pytest | `pass` | `23 passed, 1 skipped`. |
| Full pytest | `pass` | `427 passed, 1 skipped`. |
| `python -m compileall -q automation tests` | `pass` | Compileall passed. |
| Approval example validator | `pass` | Public example remained `blocked`, `runtime_execution_status=not_run`. |
| TASK-005 draft validator | `pass` | Public draft remained `blocked`, `runtime_execution_status=not_run`. |
| Default TASK-020 runner | `pass` | `overall_status=blocked`, `runtime_execution_status=not_run`; no ADB/runtime call. |

## Runtime result

Runtime Phase B/C executed as bounded partial coverage.

Run ID: `task-020-20260702T100044Z`
Public-safe summary:
`docs/qa/reports/task020_post_auth_navigation_transition.summary.json`
Local raw evidence root:
`.qa_local/evidence/task-020/task-020-20260702T100044Z/`

| Check | Status | Evidence status | Notes |
|---|---:|---:|---|
| Runtime execution | `partial` | `confirmed` | Bounded sampled coverage, not exhaustive proof. |
| Coverage status | `partial_budget_limited_coverage` | `confirmed` | Stopped without Select on semantically uncertain controls. |
| Exhaustive navigation proof | `false` | `confirmed` | All screens and all transitions were not covered. |
| Runtime observations / aliases | `8` | `confirmed` | Alias-only focus/screen samples; not proof of 8 unique product screens. |
| Transitions observed | `4` | `confirmed` | D-pad focus sampling transitions only; no Select-driven screen transition coverage. |
| States observed | `1` | `confirmed` | `post_auth_shell`. |
| Boundaries observed | `0` | `confirmed` | No boundary was entered. |
| Root Home/foreground session | `pass` | `confirmed` | Returned to post-auth shell alias category. |
| Root force-stop/relaunch session | `pass` | `confirmed` | Returned to post-auth shell alias category. |
| Crash/ANR summary | `not_observed` | `confirmed` | Redacted summary only. |
| Public report validation | `pass` | `confirmed` | `errors=[]`. |

Select transitions across native screens were not entered because controls were
not semantically safe enough for unattended selection under TASK-020 stop rules.
Back for each observed D-pad focus transition was not separately verified
(`back_result=not_run` in the public summary).
Payment, WebView/redirect, stream/WebRTC/media playback, profile/account
mutation, network/offline manipulation, compatibility matrix and full
Experience QA remain `not_run`.

## Owner-requested zero-state audit correction

On 2026-07-02, the owner requested deleting local app data and auditing from
zero on the owner-confirmed Philips-new target. This changed the runtime state
from TASK-020 post-auth navigation to a first-run/auth/legal/captcha frontier,
so it must not be treated as completion evidence for the original post-auth
TASK-020 scope.

The local app data reset returned `pm clear: Success`, and launch reached the
phone auth screen. Confirmed zero-state aliases in local-only evidence:

- `screen_zero_auth_phone_001`: phone auth input with visible numeric keypad,
  license-agreement link and personal-data-processing policy link.
- `screen_zero_license_webview_001`: in-app legal WebView for the license /
  public-offer agreement.
- `screen_zero_policy_webview_001`: in-app legal WebView for the personal data
  processing policy.

Hard correction: TASK-019 already solved phone input for this app. Future agents
must not re-litigate this as an open problem, invent a new phone-entry routine,
or use failed ad hoc input as evidence that captcha/OTP was `not_reached`. The
canonical phone input path is the TASK-019 on-screen keyboard method and is a
blocking runtime gate:

1. Confirm the phone auth screen by UI tree/screenshot: title/copy, `+7`
   phone field, numeric keypad, `OK`, and legal links.
2. Use the visible on-screen numeric keyboard, not raw `adb input text`.
3. Enter the local-only synthetic phone value from `.qa_local/secrets/qa_user.env`
   by preserving the UI `+7` prefix and entering the remaining digits.
4. Tap the visible `OK` control from the numeric keypad.
5. Stop at captcha, OTP, error or boundary screen and record category-only
   evidence. Captcha must not be bypassed, solved by automation, or inspected
   for challenge internals.

Known local helper references for this path:

- `.qa_local/helpers/task019_auth_session_smoke.py`
- `.qa_local/helpers/task019_keyboard_probe.py`
- `.qa_local/helpers/task019_phone_continue_probe.py`
- `.qa_local/helpers/task019_phone_input_debug.py`

If this exact helper-backed path is not executed, any captcha/OTP/auth-frontier
claim is invalid for verification. Record `blocked_input_path_not_executed` or
`unknown`, not confirmed `not_reached`, `fail`, or product behavior. A final
report that claims captcha was not reached after bypassing this gate should be
treated as a QA process failure and corrected before task closure.

Mandatory screen checkpoint rule: every newly encountered runtime screen or
state must pause the run before further navigation. The operator/agent must
capture local-only evidence, assign a public-safe screen alias, classify the
state category, record evidence status, list observed focus/action categories,
write a short risk/hypothesis note, and only then choose the next action. This
applies especially to loader, error, captcha, legal WebView, auth, retry,
empty/entitlement and boundary-like screens. Do not rush through transient
screens; they may explain user-path mismatches.

If the screen/state was already encountered earlier in the same run or a prior
evidence run, record the recurrence as a checkpoint too. The checkpoint must
reference the prior public-safe alias/evidence id, state what matched, state
what changed if anything, and record the trigger/path that returned to it.
Repeated screens are evidence about loops, recovery, session persistence or
user-path mismatch; do not collapse them into the first observation.

Long-list and collapsible-menu rule: runtime inventory must not treat a
scrollable list, paged list, lazy-loaded grid or expandable/collapsible menu as
fully covered from a single static viewport. Record the visible segment,
safe scroll/focus samples, truncation/lazy-load evidence and category boundary
where applicable. If a side/menu surface can collapse or expand, capture both
states when safely reachable and state the menu state in each checkpoint.

2026-07-02 continuation note: after the checkpoint rule was added, the current
Philips-new zero-state inventory captured `screen_checkpoint_071` as a
recurrence of the auth-phone screen. The canonical on-screen digit path then
advanced to `screen_auth_phone_filled_001` and `screen_otp_code_entry_001`;
later samples of the OTP/code screen were recorded as recurrence checkpoints.
OTP was not entered. Captcha remains `unknown/not observed as a confirmed
checkpoint`. Earlier local evidence also contains confirmed transient loader
and auth error/retry states; they must remain first-class inventory screens,
not be collapsed into auth success/failure.

Owner-confirmed captcha trigger model: the product flow normally gives the user
three OTP entry attempts and then explicitly moves to captcha. However, the
external authorization service may classify behavior as suspicious and move to
captcha earlier, before the third wrong OTP attempt. Treat OTP/code entry as the
pre-captcha frontier, but do not require exactly three wrong OTP attempts before
accepting a confirmed captcha screen. Do not mark captcha as `not_reached`
unless the relevant OTP/captcha trigger path has been deliberately executed
under an approved captcha-trigger test. Do not execute that trigger path
silently; it is `PROD_CONDITIONAL` and must use a synthetic account, checkpoint
after each wrong OTP attempt, stop at the captcha screen, and never solve or
bypass captcha.

2026-07-02 correction: wrong OTP attempt 1 produced a bottom transient
error/snackbar with remaining-attempts information visible in screenshot
evidence, but UIAutomator XML exposed only the underlying OTP screen. This is a
confirmed XML-vs-visual tooling gap. Runtime inventory must inspect screenshots
for transient overlays and record them as first-class checkpoints; XML-only
classification is insufficient for OTP errors, loaders, snackbars and other
short-lived visual states.

2026-07-02 captcha frontier update: the wrong-OTP trigger path reached a
captcha image-code entry screen on the current Philips-new target. Captcha is
confirmed as `screen_captcha_image_code_entry_001`, but the exact wrong-OTP
attempt count must remain `unknown` because one attempt sequence was interrupted
mid-run and may have partially submitted before evidence was corrected. The
captcha challenge was not solved, bypassed, OCRed or published. Current runtime
state should be treated as stopped at captcha; continuation requires owner/human
input or a separately approved non-bypass handling plan.

Owner clarification: a captcha screen can be valid even if it appears before
three visible wrong OTP attempts, because the external authorization service may
escalate suspicious behavior earlier than the product's normal three-attempt
flow. Therefore, early captcha is not automatically a process error; record the
observed attempt count, evidence status and trigger ambiguity instead of forcing
the event into an exactly-three-attempt model.

Anomaly logging rule: every unexpected navigation result, transient overlay,
classifier/accessibility mismatch, repeated-screen loop, delayed WebView load,
focus trap, failed back/exit or other deviation must be recorded immediately as
an anomaly checkpoint with trigger/action, expected result, observed result,
evidence status, public-safe alias, likely/hypothesis cause and test-design
implication. Do not defer anomaly notes until final reporting.

2026-07-02 post-auth zero-reset update: after successful OTP entry through the
on-screen keypad, the app auto-transitioned through a loader into onboarding.
Three onboarding screens were confirmed: rent-PC intro, cloud-saves explanation
and per-minute payment information. Tapping the final onboarding CTA reached a
post-auth games catalog/home screen with a left navigation rail, banner/QR
surface and scrollable game grid. The game grid and Steam top-up entry are
payment/session-risk boundaries: inventory may capture structure and safe focus
movement, but must stop before starting a paid/session flow or exposing QR/raw
account data. Also record the current navigation rail state because the menu
may collapse/expand.

2026-07-02 evidence-pipeline finding: local files named `redacted` briefly
included a synthetic phone value in labels for the post-auth catalog checkpoint.
This is a redaction defect in the local artifact pipeline, not an app defect.
Correct the local artifacts before any public report and keep public output
category-only.

2026-07-02 catalog focus correction: on the post-auth games catalog screenshot,
the `Игры` navigation item is visually active/focused (white text/icon and left
vertical indicator). UIAutomator still reports `focused_count=0`. Future
inventory must distinguish screenshot-confirmed TV focus/active state from the
accessibility `focused=true` flag; do not state that there is no focus when the
visual focus is clear.

## Multi-agent status

- Orchestrator: `PASS_RUNTIME_PARTIAL_AND_DOCS_REMEDIATED`
- Planner: `PASS_PHASE_A_PLAN`; confirmed base `main`/`origin/main` at
  `ac2e11a` after TASK-019 and recommended Phase A file set/verification.
- Builder: `PASS_MAIN_AGENT_PHASE_A_AND_PARTIAL_RUNTIME`
- QA Reviewer A: `PASS_AFTER_REMEDIATION`; false-pass cases for raw
  `.qa_local` Windows paths, standalone OTP, account IDs, raw hash values,
  schema version and symlink escape were hardened with same-task regressions.
- QA Reviewer B: `PASS_RUNTIME_PARTIAL_WITH_UNVERIFIED_ZONES`; confirmed this
  is partial bounded coverage only, not all screens/all transitions.
- Security/Prod-safety Reviewer: `PASS_FINAL`; no committed APK/secrets/raw
  device identifiers/raw evidence/private endpoints found in TASK-020 files.
- Docs/Scribe: `BLOCK_REMEDIATED`; required `git status` verification record,
  DEC-022 and final multi-agent status updates were applied.
- Subagent closure audit: `complete`; Planner, QA Reviewer A, QA Reviewer B,
  Security/Prod-safety and Docs/Scribe outputs were recorded in this handoff;
  no subagent output is needed for further TASK-020 work after final report.

## Forbidden actions

- committing APK/AAB/APKS/XAPK files, raw APK hashes, raw screenshots, raw logs,
  raw videos, raw UI dumps, raw ADB serials/IPs/MAC/IMEI/Android ID, phone/OTP
  values, tokens, cookies, sessions, private endpoints, routes, deeplinks,
  headers, payloads or account values;
- source/decompiled code, smali or method bodies;
- APK patching, resigning or modification;
- TLS/pinning/security bypass, proxy or packet capture;
- payment, purchase, subscription, billing, WebView/redirect/browser,
  stream/WebRTC/media playback, logout, network/offline manipulation or
  profile/account mutation.

## Stop conditions

Stop if Phase A verification fails; if runtime prerequisites are unavailable;
if a boundary surface would be entered; if raw evidence or private values would
enter public output; if repeated crash/ANR or unrecoverable focus loss occurs;
or if default branch merge/push is requested without explicit user command.

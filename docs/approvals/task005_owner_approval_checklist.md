# TASK-005 Owner Approval Checklist

Task: `TASK-015H/017C - Final scope-version/normalization polish + TASK-005 owner approval handoff finalization`

Status: `owner_input_required`

This checklist is public-safe owner/QA input material only. It does not approve
TASK-005 runtime execution, APK install, app launch, logcat, screenshots,
videos, WebView, WebRTC, stream/media playback, payment, subscription,
purchase or production mutation.

TASK-015H/017C is the final planned pre-runtime polish for the approval
infrastructure. After this task, broad hardening should stop unless a new
concrete false-pass is found. The next step is owner/QA approval input and a
separate TASK-005 limited runtime smoke task.

## Required Owner/QA Inputs

- Choose exactly one P0 TV/STB target from `docs/approvals/task005_owner_device_review.md`.
- Manually confirm the actual device, form factor, D-pad/remote input and ADB stability.
- Confirm the selected target can be represented only by public-safe aliases.
- Place the APK locally at `.qa_local/apks/task-005/app-under-test.apk`.
- Record SHA-256 evidence locally only; do not publish the hash value in the repository.
- Create `.qa_local/secrets/qa_user.env` only if synthetic login is in scope.
- Approve evidence capture policy for screenshots, logcat, videos and retention.
- Keep raw evidence local under `.qa_local/evidence/task-005/`.
- Fill real TASK-005 approval metadata with required QA, Security/Prod-safety and Docs reviews.
- Run `python automation/approvals/validate_approval_metadata.py --metadata <real-local-or-reviewed-metadata>`.
- Start TASK-005 limited runtime smoke only as a separate task after approval metadata validates.

## Public-Safe Defaults

Use these exact public-safe references:

```text
APK path pattern: .qa_local/apks/task-005/app-under-test.apk
Synthetic QA user secret path: .qa_local/secrets/qa_user.env
Evidence raw storage path: .qa_local/evidence/task-005/
Build alias: task-005-local-apk-001
Synthetic user alias: qa-user-phone-001
Evidence public report policy: redacted_summaries_only
Evidence retention: 7 days
```

## Do Not Record In Public Repo

- APK/AAB/APKS/XAPK files.
- Raw SHA-256 hash values.
- Phone numbers, OTPs, tokens, cookies, sessions or credentials.
- Raw ADB serials, IP addresses, MAC addresses, IMEI, Android ID, Google account or full build fingerprint.
- Raw screenshots, logs, videos, packet captures or dumps.
- Private endpoints, routes, deeplinks, redirect chains, headers or payloads.
- Any proof claiming APK install, app launch or runtime smoke passed before the separate TASK-005 run.

## TASK-005 Remains Blocked Until

- one P0 TV/STB target is manually confirmed;
- local APK presence and local hash record are confirmed;
- evidence capture and retention are explicitly approved;
- local synthetic QA user secret file exists if login is in scope;
- real approval metadata validates as `approved_for_limited_runtime`;
- required QA, Security/Prod-safety and Docs reviews are approved or confirmed;
- a fresh separate TASK-005 limited runtime smoke task is opened.

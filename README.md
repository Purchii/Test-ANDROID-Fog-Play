# MTC Fog Play Android QA

Public-safe QA automation and process repository for Android TV / hybrid /
WebView / WebRTC testing of MTC Fog Play.

## Current Safety Status

- Runtime/device/APK execution is blocked until explicit confirmed approvals.
- APK files, raw evidence, secrets, private endpoints and device identifiers are
  local-only and ignored by default.
- Reports and validators fail closed when evidence is missing or not confirmed.
- TASK-015 adds approval metadata validation only; it does not run the app.

## Source Of Truth

Read these before substantial work:

```text
AGENTS.md
CODEX_ANDROID_QA_PROJECT_TZ.md
docs/codex/*.md
docs/context/current-state.md
docs/context/handoff/active-run.md
docs/context/governance/decisions-log.md
docs/context/governance/risk-register.md
docs/context/engineering/quality-gates.md
docs/context/engineering/verification-memory.md
docs/tasks/backlog.md
docs/qa/approval-dependency-map.md
docs/qa/evidence-schema.md
docs/approvals/*.md
```

## Safe Commands

```bash
pytest -q
python -m pytest -q
python -m compileall automation tests
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.example.json
```

These commands are local and public-safe. They must not connect to devices, run
APK files, capture raw evidence or contact production systems.

## Local-Only Artifacts

Use ignored `.qa_local/` storage for APKs, device inventory, evidence and
secrets. Do not commit raw APKs, logs, screenshots, videos, phone numbers, OTPs,
tokens, cookies, sessions, device serials, IMEI, MAC, Android ID, private
routes, deeplinks or endpoint details.

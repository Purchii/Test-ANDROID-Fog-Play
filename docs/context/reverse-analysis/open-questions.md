# Open questions from public-safe reverse-analysis context

Evidence status: `unknown` until answered by product, engineering, security or runtime evidence.

## Product and QA fixtures

- Which build/APK is approved for QA automation work?
- Which Android TV devices or emulator images are in scope?
- Which QA accounts are approved for auth/session testing?
- Which stream fixtures are safe for reconnect, sleep/wake and latency testing?
- Which payment fixtures are staging-only and explicitly non-real-payment?

## Security and privacy

- Which exported surfaces are intentional in production builds?
- What is the expected guard behavior for stream/session entry points?
- Are backup/restore settings acceptable for the release channel?
- What redaction policy is required for screenshots, videos and logs?
- Which analytics, crash and push telemetry checks are allowed in QA?

## Automation governance

- Which runtime actions are approved as `PROD_CONDITIONAL` for future tasks?
- Which tasks must remain `NON_AUTONOMOUS` because they depend on product credentials or staging approval?
- What is the release gate threshold for R0/R1 QA concerns?

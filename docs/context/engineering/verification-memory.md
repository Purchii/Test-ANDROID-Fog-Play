# Verification memory

This file records what was actually verified. Do not claim runtime checks passed unless executed.

## Verification log

| Date | Task | Branch | Checks run | Result | Notes |
|---|---|---|---|---|---|
| 2026-06-05 | TASK-000 planning | qa/task-000-bootstrap-codex-docs | `git status --short --branch`, `git remote -v`, remote HEAD/heads check | passed | Local repo had no commits; GitHub remote was empty. |
| 2026-06-05 | TASK-000 bootstrap | qa/task-000-bootstrap-codex-docs | Public-safety policy review, staged forbidden-artifact scan, `git diff --cached --check`, multi-agent Docs/Security/QA review | passed | Raw artifacts and executable runtime recipes are excluded from public source-of-truth. |

## Known verification rules

- `git status --short --branch` is required for every task.
- Docs-only tasks require diff review and secret/private endpoint scan by Security reviewer.
- Python automation tasks should run `python -m pytest` if test framework exists.
- Android runtime tasks require approved device/APK/config.
- Missing runtime dependencies must produce `blocked` report, not fake pass.

## Unverified zones

- GitHub default branch UI setting after first push; remote had no HEAD before bootstrap.
- Runtime screen map.
- Android TV device matrix.
- QA accounts and fixtures.
- Payment/WebView staging behavior.
- Streaming/WebRTC test oracle.
- Production testing permissions and budgets.

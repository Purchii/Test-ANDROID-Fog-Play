# Risk register

| ID | Risk | Level | Status | Mitigation | Owner |
|---|---|---:|---|---|---|
| RISK-001 | Codex continues next independent task in old thread. | High | active | Fresh-thread gate and final handoff requirement. | Orchestrator |
| RISK-002 | Task branch created from stale default branch. | High | active | Fetch/pull default before every task branch. | Git Reviewer |
| RISK-003 | Default branch pushed in NON_AUTONOMOUS mode without approval. | High | active | AGENTS.md and git policy forbid it. | Orchestrator |
| RISK-004 | Multi-agent degraded into single-agent role-play. | High | active | Strict subagent requirement; block if unavailable. | Orchestrator |
| RISK-005 | Production-impacting test runs without guardrails. | Critical | active | PROD_SAFE/CONDITIONAL/FORBIDDEN classification. | Security Reviewer |
| RISK-006 | Sanitized pack facts treated as confirmed runtime behavior. | High | active | Evidence status policy. | QA Reviewer |
| RISK-007 | Logs/evidence expose secrets or private values. | Critical | active | Redaction-by-default and review before commit. | Security Reviewer |
| RISK-008 | Android runtime tests claimed as passed without device/APK. | High | active | Blocked evidence report required. | QA Reviewer |
| RISK-009 | Public repository receives raw APK analysis, endpoint aliases or compiled cache artifacts. | Critical | active | `.gitignore`, public-safe summaries, secret/raw scan before commit. | Security Reviewer |
| RISK-010 | A future independent task continues in an old thread. | High | active | Fresh-thread gate and final handoff create next thread. | Orchestrator |
| RISK-011 | Autonomous default-branch push occurs without passing gates. | Critical | active | `BOUNDED_AUTONOMOUS` merge requires multi-agent, status, diff and redaction checks. | Git Reviewer |
| RISK-012 | GitHub remote default branch points to task branch instead of `main`. | High | resolved | Repository owner changed GitHub default branch to `main`; Codex verified remote HEAD. | Git Reviewer |
| RISK-013 | Subagents from inactive threads remain open and create audit or continuation confusion. | Medium | active | Completion checkpoint requires using/recording needed outputs, then closing agents no longer needed for review, handoff or debugging. | Orchestrator |
| RISK-014 | Exported component guard skeleton accidentally becomes actionable runtime probing or publishes component/runtime recipes. | High | active | Keep TASK-002 category-level and fail-closed; forbid runtime/device recipes and require Security review before merge. | Security Reviewer |

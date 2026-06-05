# Public-safe reverse-analysis context

This folder contains a public-safe QA planning layer derived from the sanitized reverse-analysis pack.

Rules:

- Treat these notes as QA planning input, not proof of runtime behavior.
- Do not commit raw APK analysis dumps, compiled cache files, APKs, logs, screenshots, credentials, endpoints or private URLs.
- Do not include executable device/runtime command recipes in public docs.
- Keep endpoint and network details at category level only.
- Preserve evidence status: `confirmed`, `likely`, `hypothesis`, `unknown`.

Local source material observed during TASK-000:

- `qa_reverse_analysis/*.md` is available locally as sanitized markdown input.
- `qa_reverse_analysis/raw/` is excluded from public source-of-truth by default.
- `qa_reverse_analysis_documents.zip` is excluded from public source-of-truth by default unless rebuilt from an approved public subset.

Authoritative public summaries:

- `public-risk-summary.md`
- `qa-task-map.md`
- `open-questions.md`

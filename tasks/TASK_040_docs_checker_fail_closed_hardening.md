# TASK-040 — Docs checker fail-closed hardening

## Mode and classification

- Mode: `BOUNDED_AUTONOMOUS`.
- Production safety classification: `PROD_SAFE_OFFLINE_STATIC_ONLY`.
- Task branch: `qa/task-040-docs-checker-fail-closed-hardening`.
- Default branch and exact base: `main@7f3dbf099a4554eb23febfb4028b0dcd0a506480`.
- Audit item: `QA-P0-03`; the exact archive finding ID remains `unknown`
  because the remediation archive is not tracked or public-readable under this
  task's rules.
- Evidence status for implementation and local checks: `confirmed` after the
  listed commands pass; Android/runtime behavior remains `not_run` and
  `unknown`.

## Scope

Harden `automation/quality/docs_consistency_link_sanity.py` so tracked-file
discovery cannot silently degrade into a passing empty scan, every Markdown
scan input crosses one shared validation barrier before content I/O, and
diagnostics cannot disclose raw exception or unsafe path values.

The barrier accepts only existing, regular, non-symlink, repository-contained
`.md` files addressed by unambiguous repo-relative paths. It rejects absolute,
drive, UNC, traversal, encoded traversal, control, query, fragment,
scheme-like, forbidden-prefix and non-Markdown inputs. An invalid member blocks
all content reads for that scan set. Zero eligible Markdown files is a blocked
result, never PASS.

## Boundaries

No ADB, Android device, APK, IP, runtime, WebView, payment, stream/session,
live API, backend, network, ignored `.qa_local` raw evidence, secret, private
endpoint or raw-value access is authorized.

## Acceptance criteria

- `auto` and `tracked` Git discovery failures return controlled exit `2` with
  fixed reason codes and empty stderr.
- `scanned_files` counts validated Markdown inputs, not every tracked path.
- zero eligible Markdown inputs return controlled exit `2`.
- invalid inputs are rejected before any Markdown content is read.
- read failures emit only fixed, sanitized diagnostics.
- external links remain non-crawled.
- focused adversarial tests and static checker verification pass, or an exact
  environment blocker is recorded.

## Residual risk

The checker assumes a trusted, single-writer offline worktree. It rejects
symlinks and validates containment plus regular-file status immediately before
reading, but does not claim an atomic snapshot against concurrent path
replacement. A scan that overlaps workspace mutation must be discarded and
rerun from a stable checkout.

# Docs Consistency and Link Sanity

## Purpose

TASK-018 adds a local static guard for public Markdown links and public
repo-relative documentation references. It complements the TASK-014 tracked-path
public repository safety scan and the TASK-017 synthetic redaction corpus.

This guard does not prove runtime behavior, product behavior, WebView/payment
behavior, stream behavior, network behavior or compatibility coverage.

## Local Guard

Run:

```bash
python automation/quality/docs_consistency_link_sanity.py
```

The guard scans tracked Markdown files by default and checks:

- local Markdown links point to tracked public files;
- local Markdown anchors exist in the target document;
- duplicate headings can be referenced with GitHub-style `-1`, `-2` suffixes;
- public repo-relative references in inline code point to existing tracked
  public files;
- Markdown links do not point into local-only/raw evidence or package artifact
  families.

Before reading any Markdown content, TASK-040 applies one fail-closed input
barrier. Scan inputs must be unambiguous repository-relative `.md` paths to
existing regular non-symlink files inside the selected root. Absolute, drive,
UNC, traversal (including encoded or backslash forms), control-character,
query, fragment, scheme-like, forbidden-prefix, non-Markdown, missing and
nonregular inputs are rejected. If any member is invalid, no member of that
scan set is read.

External links are treated as out of scope for TASK-018. The guard never
fetches, crawls, follows redirects or probes remote URLs.

`auto` and `tracked` mode fail closed with exit `2` when Git discovery is
unavailable or fails. A discovery result with zero eligible validated Markdown
files is also blocked rather than reported as PASS. `scanned_files` counts only
eligible validated Markdown files.

## Output Contract

Findings use:

```text
RULE_ID    source/path.md:line    sanitized-target    category-level reason
```

Forbidden or sensitive-looking local targets are reported with category labels
such as `[forbidden-local-target]`, `[unsafe-local-target]` or
`[query-or-url-like-target]`; the guard must not print raw private-looking
URLs, QR targets, phone/OTP values, device identifiers, APK hashes, account
values or payment values.

Discovery, input-validation and read failures use fixed reason codes. Raw Git
stderr, exception text, unsafe input values and absolute repository roots are
not included in checker output.

The checker assumes a trusted, single-writer offline worktree while a scan is
running. It rejects symlinks and rechecks containment plus regular-file status
immediately before content reads, but it does not provide an atomic filesystem
snapshot against a concurrent path replacement. If the worktree changes during
a scan, discard that result and rerun the guard from a stable checkout.

## Boundaries

Literal `.qa_local/...` examples in policy text are allowed when they describe
ignored local storage contracts. Markdown links or dereferenceable public
references into `.qa_local`, APKs, raw evidence, local secrets or packaged
artifacts are blocked.

No ADB, APK, Android runtime, WebView, WebRTC, payment, stream,
network/offline, browser or production action is part of TASK-018.

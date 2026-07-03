# Public Repository Safety Scan Checklist

## Purpose

TASK-014 defines a public-safe pre-commit and pre-merge guard for this QA
repository. It protects the public source tree from raw local evidence,
packaged Android artifacts, signing material, local config files and packaged
reverse-analysis archives.

This is a static repository check. It does not prove runtime behavior, app
security, payment behavior, network behavior, WebView behavior, stream
behavior or compatibility coverage.

## Local Guard

Run:

```bash
python automation/quality/public_repo_safety_scan.py
```

The guard scans tracked paths by default and fails closed when a tracked path
matches one of these classes:

| Class | Examples | Expected action |
|---|---|---|
| Local-only directories | `.qa_local/`, `qa_reverse_analysis/`, `docs/context/reverse-analysis/raw/`, `safe_archives/` | Keep ignored and out of commits. |
| Android or packaged artifacts | `.apk`, `.aab`, `.apks`, `.xapk`, `.dex`, `.zip`, `.7z` | Remove from public branch and store locally only. |
| Raw evidence media/logs | `.log`, `.mp4`, `.webm`, `.mov`, `.mkv`, screenshot-like `.png` names | Keep under ignored evidence storage. |
| Signing/config/secrets | `.keystore`, `.jks`, `.pem`, `.key`, `.p12`, `.env`, `google-services.json`, `local.properties` | Remove and rotate if a real secret was exposed. |

The guard reports only `rule_id`, `path` and a category-level reason. It must
not print file contents or matched secret-like values.

## Manual Checklist

Before commit, merge or default-branch push:

- Run `git status --short --branch` and confirm only intended tracked files are
  changed.
- Run `git diff --check`.
- Run `python automation/quality/full_tree_hygiene_scan.py`.
- Run `python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree`.
- Run `python automation/quality/public_repo_safety_scan.py`.
- Review new public reports for aliases/categories only, not raw screenshots,
  XML, logs, videos, QR targets, APK hashes, phone/OTP values, device
  identifiers, private endpoints, account-like values or payment values.
- Confirm any `.qa_local/...` strings in public docs are path-pattern contracts
  or redacted local evidence references, not published raw evidence.
- Confirm runtime-dependent claims use `blocked`, `not_run`, `partial` or
  `unknown` unless confirmed evidence exists.

## Evidence Status

- Scanner path findings: `confirmed` when the tracked path is present.
- Absence of findings: `confirmed` only for the scanned tracked path set at the
  command time.
- Runtime, payment, WebView, stream, network and compatibility behavior:
  `unknown` or `not_run` unless a separate approved runtime task captured
  evidence.

## Known Boundaries

The scanner intentionally does not replace a full secret-scanning product. It
keeps a narrow, low-false-positive contract because this repository contains
synthetic redaction tests and public-safe `.qa_local/...` path examples. Any
future content scanner must be designed to avoid printing matched raw values and
must preserve synthetic test fixtures.

# TASK-018 - Docs consistency and link sanity checks

## Task

Add public-safe local documentation consistency and link sanity checks for the
MTC Fog Play Android QA repository.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-018 - Docs consistency and link sanity checks
```

## Branch

```text
qa/task-018-docs-consistency-link-sanity
```

## Context

TASK-014 added a tracked-path public repository safety scan, and TASK-017 added
synthetic redaction corpus coverage. After many runtime and static QA tasks,
the public source-of-truth also needs a local guard for broken Markdown links,
stale public repo-relative references and unsafe dereferenceable local/raw
artifact targets.

## Production safety classification

TASK-018 is `PROD_SAFE` because it performs only local static checks over
tracked/public repository files and updates public-safe documentation.

The following are `PROD_FORBIDDEN` in this task:

- ADB, Android device interaction, APK read/install/launch/inspection or APK
  modification;
- runtime navigation, screenshots, logs, videos, UI XML dumps or QR decoding;
- WebView, WebRTC, payment, stream, network/offline, live CI or production
  execution;
- reading, listing, parsing, copying, summarizing or deriving from ignored
  `.qa_local/` raw evidence, local APKs, local secrets, raw QR artifacts or
  private endpoint inventories;
- external link crawling, redirect following, DNS probing or HTTP requests;
- publishing raw private-looking URL/query values, QR targets, phone/OTP
  values, device identifiers, APK hashes, account values or payment values.

## Scope

In scope:

- a local `automation/quality/docs_consistency_link_sanity.py` checker;
- focused unit tests for valid links, missing files, missing anchors, duplicate
  heading anchors, unsafe absolute/traversal paths, forbidden local/raw link
  targets and external-link non-crawling;
- repairs for confirmed broken public Markdown links or public repo-relative
  references;
- source-of-truth documentation updates for TASK-018 state, gates, risks and
  verification memory.

Out of scope:

- runtime/product behavior validation;
- broad policy rewrites or task resequencing;
- checking internet availability or remote documentation freshness;
- scanning ignored local evidence trees or raw artifacts;
- treating literal `.qa_local/...` policy examples as dereferenceable evidence.

## Acceptance criteria

- TASK-018 has a source-of-truth task spec.
- The checker scans tracked Markdown files by default and does not traverse
  ignored `.qa_local` or raw artifact directories.
- External links are never fetched or crawled.
- The checker fails closed on missing public targets, missing local Markdown
  anchors, unsafe absolute/traversal paths and Markdown links to forbidden
  local/raw/package/secret-like targets.
- Checker output reports rule id, source path, line and sanitized/category-level
  target information without echoing raw forbidden targets.
- Tests cover the behavior above.
- Source-of-truth docs state that TASK-018 does not approve runtime, APK, ADB,
  WebView, WebRTC, payment, network/offline or raw evidence work.

## Verification

Required checks:

```bash
git status --short --branch
git diff --check
python -m pytest -q tests/test_docs_consistency_link_sanity.py
python -m pytest -q tests/test_public_repo_safety_scan.py tests/test_full_tree_hygiene_scan.py tests/test_synthetic_redaction_corpus.py
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/docs_consistency_link_sanity.py
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
```

Runtime/device/APK/WebView/WebRTC/browser/redirect/payment/backend/network/live
CI validation is not run for TASK-018.

## Stop conditions

Stop and ask for guidance if any requested change would require:

- real raw evidence, secrets, endpoints, QR targets, account/payment data or
  device identifiers;
- APK/device/runtime execution;
- executable production, Android, browser or network command recipes;
- external link crawling;
- scanner output that prints raw forbidden target values;
- a failing check that cannot be fixed within the bounded task scope.

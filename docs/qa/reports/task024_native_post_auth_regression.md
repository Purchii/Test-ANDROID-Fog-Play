# TASK-024 native post-auth regression summary

## Status

TASK-024 adds the native regression model, suite schema, fail-closed runner and
public-safe validator for the selected post-auth lane.

Phase C runtime status: `blocked`. The explicit `--allow-runtime` command was
attempted after Phase A/B gates, but the runner blocked before ADB/device/APK
interaction because no approved TASK-024 runtime collector/input report was
provided.

## Scope

The regression pack is derived from TASK-020, TASK-021, TASK-022 and TASK-023
public-safe evidence. It asserts screen families, focus/actionability,
category-level data, recovery behavior, session checkpoints and redaction
invariants.

It does not assert fixed game titles, game counts, server rows, server aliases,
prices, ping values, hardware rows, QR targets or account-like values.

## Boundaries

Payment, WebView/browser/external QR traversal, stream/media/session start,
Steam/account connection, profile mutation, captcha solving, network/offline
manipulation, packet capture/proxy/TLS bypass and APK patch/decompile/resign
remain forbidden in TASK-024.

Raw evidence remains local-only under ignored TASK-024 evidence storage when a
future approved runtime input is collected. The Phase C blocked local JSON is
not public source.

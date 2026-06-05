# Public-safe QA risk summary

Evidence status for this summary: `likely`.

This file preserves the QA meaning of the local sanitized reverse-analysis material without publishing raw dumps, endpoint aliases, executable runtime recipes or compiled artifacts.

## P0 / Critical planning areas

| Area | Evidence status | QA concern | Public-safe next action |
|---|---|---|---|
| Android TV launch and first focus | likely | Startup, first focus, Back/Home behavior and crash-free entry need runtime evidence. | Prepare runtime discovery checklist in TASK-001. |
| Session guard around stream entry | likely | Stream/session entry points must not bypass valid auth/session state. | Define expected guard behavior and ask product/security for confirmation. |
| Exported component exposure | likely | Exported surfaces need benign guard checks and release-gate visibility. | Create safe guard-check plan; no direct runtime probing until fixtures are approved. |
| Auth and session lifecycle | likely | Invalid/expired codes, resend, logout, restore and process death can break TV UX. | Convert to smoke/regression charters. |
| Streaming/WebRTC lifecycle | likely | Reconnect, latency, black screen, sleep/wake and controller input need evidence. | Define test oracle and fixture prerequisites. |
| WebView/payment-safe flows | likely | Payment and external response flows require staging-only fixtures and no real payments. | Draft staging fixture contract before any execution. |

## P1 / High planning areas

| Area | Evidence status | QA concern | Public-safe next action |
|---|---|---|---|
| Catalog/search/library | hypothesis | Empty states, pagination and unavailable items can block navigation. | Add exploratory charters. |
| Settings persistence | hypothesis | Settings may regress across restart/process death. | Add persistence checklist. |
| Backup/restore | hypothesis | Backup behavior needs product/security decision. | Track as governance question. |
| Vendor/platform permissions | hypothesis | Denied/unavailable vendor services need graceful behavior. | Add compatibility matrix items. |
| Analytics/crash/push behavior | hypothesis | Privacy, consent and environment separation need verification. | Require redaction and environment policy. |
| Accessibility/localization | hypothesis | D-pad focus, long localized strings and screen-reader behavior need checks. | Add to manual runtime map. |

## Public redaction boundary

Do not add:

- raw APK analysis JSON;
- compiled cache files;
- APK/AAB/DEX/native binaries;
- real or redacted endpoint inventories as URL-like lists;
- secrets, tokens, cookies, sessions or credentials;
- executable device/runtime command snippets;
- screenshots/logs containing user data or device identifiers.

# Post-Auth State And Session Policy

Task: `TASK-020 XL+ - Post-auth native navigation transitions`

## Session Policy

TASK-020 may start from the existing authenticated session. If the app is at an
auth guard, login is allowed only with the local ignored synthetic user file and
the TASK-019 working on-screen keyboard method.

Raw phone and OTP values must not be printed, logged or committed.

## Required Session Checkpoints

- root Home/foreground session persistence;
- root force-stop/relaunch session persistence;
- selected deeper screen Home/foreground return behavior when safely reached;
- selected deeper screen force-stop/relaunch behavior when safely reached;
- auth state after relaunch remains post-auth or safe logged-in root;
- crash/ANR summary remains redacted.

Returning to a safe post-auth root after force-stop is acceptable. Unexpected
auth loss, unrecoverable blank state, crash/ANR or boundary entry is a failure
or blocker depending on evidence.

## Natural State Policy

Record natural states only if encountered without forcing negative conditions:

```text
post_auth_shell
native_home
catalog_or_list
detail_or_item
search_entry
search_results
settings_or_profile_boundary
loading
empty
error
entitlement_or_subscription_boundary
payment_boundary
webview_boundary
stream_or_playback_boundary
account_mutation_boundary
unknown_native
```

Do not force offline, expired session, wrong OTP or backend timeout in
TASK-020.

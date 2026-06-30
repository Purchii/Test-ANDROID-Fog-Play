# Local Paths Policy

Task: `TASK-015F/017A - Final strict-schema polish + owner target review handoff`

Local QA artifacts are ignored by default. Public source control may document
path patterns, but must not commit raw APKs, raw evidence, secrets, private
device identifiers or machine-specific absolute paths.

## Local-Only Structure

```text
.qa_local/
  apks/
    task-005/
      app-under-test.apk
      SHA256.txt
  devices/
    raw_adb_devices.json
    serial_alias_map.json
    preflight_report.json
    device_inventory.public_safe.generated.json
  evidence/
    task-005/
  secrets/
    qa_user.env
```

## Public-Safe References

Allowed in public docs:

```text
.qa_local/apks/task-005/app-under-test.apk
.qa_local/evidence/task-005/
.qa_local/secrets/qa_user.env
.qa_local/devices/raw_adb_devices.json
.qa_local/devices/serial_alias_map.json
.qa_local/devices/preflight_report.json
.qa_local/devices/device_inventory.public_safe.generated.json
build alias: task-005-local-apk-001
device aliases: tv-tcl-001, stb-xiaomi-001, phone-samsung-001
synthetic user alias: qa-user-phone-001
```

Forbidden in public docs:

```text
APK/AAB/APKS/XAPK binaries
absolute paths under a real user profile
raw phone number or OTP
tokens, cookies, sessions or credentials
raw screenshots, logs or videos
serial, IP address, IMEI, MAC, Android ID, full build fingerprint or Google account
private endpoint, route or deeplink details
```

## APK Rule

APK files can be placed only in ignored local storage by the owner or a local
developer. The repository may reference a build alias. Public reports do not
need to publish the APK hash; if a hash is used, keep the raw file and local
hash record in ignored storage.

Approval metadata must use exact local path families:

- APK/build path: `.qa_local/apks/task-005/*.apk`, preferably
  `.qa_local/apks/task-005/app-under-test.apk`. The approved pattern must be a
  single concrete `.apk` file directly under `.qa_local/apks/task-005/`; no
  wildcard, nested subdirectory or double-extension form such as
  `.apk.tmp.apk` is accepted.
- Synthetic QA secret path: `.qa_local/secrets/*.env`, preferably
  `.qa_local/secrets/qa_user.env`. The path must be a direct child of
  `.qa_local/secrets/`; nested `apks` or `devices` labels are blocked.
- Evidence path: `.qa_local/evidence/task-005/` or a direct child under that
  directory. Nested `secrets`, `devices` or `apks` labels are blocked.
- ADB inventory local paths: `.qa_local/devices/`.

Cross-family paths are blocked. For example, APK paths under
`.qa_local/secrets/`, evidence under `.qa_local/apks/`, synthetic secrets under
`.qa_local/devices/`, absolute user paths and `..` traversal are invalid.

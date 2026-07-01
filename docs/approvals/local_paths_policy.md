# Local Paths Policy

Task: `TASK-015H/017C - Final scope-version/normalization polish + TASK-005 owner approval handoff finalization`

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

Approval metadata for TASK-005 must use exact local path patterns:

- APK/build path: `.qa_local/apks/task-005/app-under-test.apk`.
- Synthetic QA secret path: `.qa_local/secrets/qa_user.env`.
- Evidence path: `.qa_local/evidence/task-005/`.
- Alternate direct-child names such as `secret-app.apk`, `home-app.apk`,
  `home.env` or nested labels such as `private/` are blocked for approval
  metadata because they can imply secrets, owner location or private evidence
  semantics.
- ADB inventory local paths: `.qa_local/devices/`.

Cross-family paths are blocked. For example, APK paths under
`.qa_local/secrets/`, evidence under `.qa_local/apks/`, synthetic secrets under
`.qa_local/devices/`, absolute user paths and `..` traversal are invalid.

# Local Paths Policy

Task: `TASK-015 - Approval Metadata Schema Validator`

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
    device_inventory.local.yaml
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
build alias: task-005-local-apk-001
device aliases: tv-001, stb-001, phone-001
synthetic user alias: qa-user-phone-001
```

Forbidden in public docs:

```text
APK/AAB/APKS/XAPK binaries
absolute paths under a real user profile
raw phone number or OTP
tokens, cookies, sessions or credentials
raw screenshots, logs or videos
serial, IMEI, MAC or Android ID
private endpoint, route or deeplink details
```

## APK Rule

APK files can be placed only in ignored local storage by the owner or a local
developer. The repository may reference a build alias. Public reports do not
need to publish the APK hash; if a hash is used, keep the raw file and local
hash record in ignored storage.


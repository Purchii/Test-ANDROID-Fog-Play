# Device Alias Policy

Task: `TASK-015B/016A - Final approval validator hardening and ADB inventory rerun/preflight`

Production safety classification: `PROD_SAFE` for docs, schemas, validators and
unit tests. This policy does not approve Android runtime execution.

## Purpose

Device aliases are the only public-safe representation of local devices. Raw
ADB serials, network addresses, account identifiers, Android IDs, IMEI, MAC,
full build fingerprints, owner names and room labels must stay out of source
control.

## Grammar

Allowed device alias grammar:

```text
(tv|stb|phone|tablet|emulator|unknown)-<safe-slug>-<three-digit-index>
```

Allowed runtime profile alias grammar:

```text
(tv|stb|phone|tablet|emulator|unknown)-<safe-slug>-a<android-major>-<three-digit-index>
```

Grammar alone is not enough. Semantic reserved-token validation must also pass.

## Reserved Tokens

Aliases and runtime profile aliases must not contain tokenized forms of:

```text
serial
serialnumber
serial-number
serial_number
imei
imsi
mac
macaddress
mac-address
mac_address
androidid
android-id
android_id
google-account
google_account
account
phone
otp
token
secret
password
cookie
session
oleg
home
livingroom
living-room
bedroom
office
kitchen
personal
private
```

IP-like, MAC-like, IMEI-like, Android-ID-like and fingerprint-like values also
block aliases.

## Important Distinction

Reserved-token validation applies to public aliases and free-text identifiers.
It does not block structured category enums such as `google_tv` or fields such
as `google_play_services`.

The synthetic QA user alias `qa-user-phone-001` is governed by
`docs/approvals/synthetic_qa_user_policy.md`; it is not a device alias.

## Runtime Approval Boundary

Generated TASK-016 inventory aliases are heuristic until owner/QA review. Future
TASK-005 approval metadata may pass only with a selected P0 Android TV/STB D-pad
target that is:

- `adb_available: yes`;
- `classification_confidence: manual_confirmed`;
- `manual_review_required: false`;
- `forbidden_identifiers_excluded: true`.

# Device Alias Policy

Task: `TASK-015C/016B - Approval/device-inventory consistency polish and local ADB inventory readiness`

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

Exception: `phone` is allowed only as the first form-factor segment for a
structured phone target, for example `phone-samsung-001` and
`phone-samsung-a14-001` when `form_factor: phone`. It remains forbidden in any
later segment, for example `tv-phone-001`, `stb-phone-a12-001` or
`phone-my-phone-001`.

IP-like, MAC-like, IMEI-like, Android-ID-like and fingerprint-like values also
block aliases.

## Important Distinction

Reserved-token validation applies to public aliases and free-text identifiers.
It does not block structured category enums such as `google_tv` or fields such
as `google_play_services`.

The synthetic QA user alias `qa-user-phone-001` is governed by
`docs/approvals/synthetic_qa_user_policy.md`; it is not a device alias.

Runtime profile aliases for approval metadata must preserve the stable device
alias prefix and index while encoding the same Android major version as
`android_major`. For example, `tv-tcl-001` maps to `tv-tcl-a11-001` only when
`android_major: 11`.

## Runtime Approval Boundary

Generated TASK-016 inventory aliases are heuristic until owner/QA review. Future
TASK-005 approval metadata may pass only with a selected P0 Android TV/STB D-pad
target that is:

- `adb_available: yes`;
- `classification_confidence: manual_confirmed`;
- `manual_review_required: false`;
- `forbidden_identifiers_excluded: true`.

For manual-confirmed TASK-005 TV/STB targets, the device alias first segment
must match the structured form factor: `tv-*` for `form_factor: tv` and `stb-*`
for `form_factor: stb`. Generated `unknown-*` aliases remain heuristic inventory
only and must not be copied into runtime approval metadata as manual-confirmed
TV/STB targets.

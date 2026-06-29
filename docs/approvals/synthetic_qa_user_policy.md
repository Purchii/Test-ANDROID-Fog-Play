# Synthetic QA User Policy

Task: `TASK-015 - Approval Metadata Schema Validator`

The project may use a synthetic QA user only through a public-safe alias.

## Public Representation

```text
Synthetic QA user: yes, if approved
User alias: qa-user-phone-001
Credential storage: local-only ignored secret file
Raw phone in public docs: forbidden
Raw OTP in public docs: forbidden
Reports: alias only
```

## Local Secret File

Recommended ignored local path:

```text
.qa_local/secrets/qa_user.env
```

Allowed local-only keys:

```env
QA_USER_ALIAS=qa-user-phone-001
QA_PHONE_E164=<local-only-phone-number>
QA_STATIC_OTP=<local-only-static-otp>
QA_AUTH_SCOPE=login-only
QA_ACCOUNT_TYPE=synthetic
```

OTP is treated as a password. Raw phone and OTP values must not appear in
repository docs, Codex prompts, public reports or validation output.

## Early Runtime Scope

Allowed only after explicit confirmed approvals:

```text
login
logout
session_persistence
```

Forbidden without separate approval:

```text
payment
purchase
subscription
profile_mutation
destructive_account_action
real_user_data_changes
```


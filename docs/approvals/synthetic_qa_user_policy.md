# Synthetic QA User Policy

Task: `TASK-015E/017 - Final metadata hardening and inventory review package`

The project may use a synthetic QA user only through a public-safe alias.
TASK-015D/016C does not approve login or runtime use of that alias. Any future
TASK-005 synthetic login remains blocked until approval metadata, fixture
policy, evidence storage, cleanup and required reviews are confirmed.

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

When `synthetic_qa_user.approved: true`, approval metadata must include both:

```text
local_secret_file_pattern: .qa_local/secrets/qa_user.env
repo_allowed_file: docs/approvals/qa_user.env.example
```

The local secret path must remain under `.qa_local/`. The repository allowed
file must be a placeholder/template path outside `.qa_local/`; a real
`.qa_local/secrets/qa_user.env` file must never be committed.

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

## Validator Requirements

When synthetic login is in TASK-005 scope, `allowed_auth_scope` must include at
least:

```text
login
session_persistence
```

The only allowed auth-scope values are:

```text
login
logout
session_persistence
```

`forbidden_account_actions` must include at least:

```text
payment
purchase
profile_mutation
destructive_account_action
```

Unsupported typo values block approval. The raw-public flags
`raw_phone_allowed_in_public_docs` and `raw_otp_allowed_in_public_docs` must
always be `false`, including no-auth metadata variants.

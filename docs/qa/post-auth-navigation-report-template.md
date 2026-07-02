# Post-Auth Navigation Report Template

Task: `TASK-020 XL+ - Post-auth native navigation transitions`

Public reports may contain only aliases, category-level states, status values,
resource budgets, redacted evidence references and coverage frontier notes.

## Required Public-Safe Shape

```json
{
  "schema_version": "task-020-post-auth-navigation-v1",
  "task_id": "TASK-020",
  "coverage_status": "sampled_bounded_runtime_coverage",
  "runtime_execution_status": "partial",
  "target": {
    "device_alias": "tv-tpv-013",
    "runtime_profile_alias": "tv-tpv-a12-013",
    "build_alias": "task-005-local-apk-001",
    "synthetic_user_alias": "qa-user-phone-001"
  },
  "resource_budget": {
    "max_screens": 40,
    "max_transition_edges": 160,
    "max_actions_total": 500
  },
  "screens_observed": [],
  "transitions_observed": [],
  "states_observed": [],
  "boundaries_observed": [],
  "session_persistence_results": {
    "root_home_foreground": {
      "result": "not_run",
      "reason": "Runtime was not executed."
    },
    "root_force_stop_relaunch": {
      "result": "not_run",
      "reason": "Runtime was not executed."
    }
  },
  "public_safety": {
    "raw_phone_otp_committed": false,
    "raw_device_identifiers_committed": false,
    "raw_evidence_committed": false,
    "payment_webview_stream_profile_mutation_entered": false
  }
}
```

## Forbidden Public Fields

- raw phone, OTP, tokens, cookies or sessions;
- raw UI hierarchy dumps, screenshots, videos or logs;
- ADB serial, IP, MAC, IMEI, Android ID or Google account values;
- private package, class, activity, endpoint, deeplink, URL, route, header or
  payload values;
- raw APK paths or hashes;
- `.qa_local/` raw evidence paths.

Validate committed summaries with:

```text
python automation/post_auth_navigation/validate_post_auth_navigation_report.py --report docs/qa/reports/task020_post_auth_navigation_transition.summary.json
```

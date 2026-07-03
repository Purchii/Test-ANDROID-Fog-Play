# TASK-025B runtime preflight checklist

Do not start TASK-025B until every item is confirmed:

| Check | Required value | Status before TASK-025B |
|---|---|---|
| Physical device available | `true` | deferred |
| Selected device connected and authorized | `yes` | deferred |
| Runtime lane aliases | refreshed/confirmed | deferred |
| APK local presence | `.qa_local/apks/task-005/app-under-test.apk` | deferred |
| APK hash evidence | local-only SHA-256 recorded | deferred |
| Synthetic QA user env | `.qa_local/secrets/qa_user.env` exists | deferred |
| Raw phone/OTP printing | forbidden | deferred |
| Evidence capture approval | explicit | deferred |
| Evidence storage | ignored local storage | deferred |
| Cleanup policy | explicit | deferred |
| Payment/WebView/stream/profile/network boundaries | forbidden | deferred |

TASK-025B remains blocked until this checklist is refreshed in a fresh task
thread with current owner approval.

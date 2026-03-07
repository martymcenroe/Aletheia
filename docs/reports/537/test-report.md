# Test Report: Issue #537

## Verification

IAM policy already deployed live and verified:
- `curl -s https://api.aletheia.study/health` -> `{"status":"ok"}`
- Direct Lambda invocation "eschews" -> `Status: success, Signal: Formal Academic Term`

## No Code Changes

This is an infrastructure-only fix (provision.sh). No unit tests affected.

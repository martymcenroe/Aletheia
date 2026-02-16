# Test Report: Issue #341

**Feature:** JWT Authentication + Daily Token Cap
**Date:** 2026-02-16
**Runner:** pytest 9.0.2, Python 3.14.0

## Summary

| Suite | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| test_jwt_service.py | 38 | 0 | 0 |
| test_token_cap_service.py | 38 | 0 | 0 |
| test_auth_middleware.py | 61 | 0 | 0 |
| **Total new (unit)** | **137** | **0** | **0** |
| test_auth_flow.py (integration) | 0 | 0 | 37 (Docker required) |
| **Full suite** | **734** | **4** | **2** |

## Integration Tests

The 37 integration tests in `tests/integration/test_auth_flow.py` require Docker
(DynamoDB Local container via testcontainers). They are skipped when Docker is
unavailable. These tests should be run in CI where Docker is available.

## Pre-existing Failures (Not Related)

- `test_verify_audits.py::test_010_valid_claim_extracted`
- `test_verify_audits.py::test_070_multiple_sessions_in_weekly_log`
- `test_verify_audits.py::test_full_verification_flow`
- `test_index_consistency.py::test_adr_index_next_number_current`

## LLD Test Coverage

| LLD Test ID | Test | Status |
|-------------|------|--------|
| T010 | test_create_jwt_valid (Req 6) | PASS |
| T020 | test_validate_jwt_success (Req 4) | PASS |
| T030 | test_validate_jwt_expired (Req 3) | PASS |
| T040 | test_validate_jwt_invalid_signature (Req 2) | PASS |
| T050 | test_validate_jwt_malformed (Req 2) | PASS |
| T060 | test_check_cap_under_limit (Req 5) | PASS |
| T070 | test_check_cap_at_limit (Req 7) | PASS |
| T080 | test_check_cap_race_condition (Req 7) | PASS |
| T090 | test_middleware_missing_header (Req 1, Req 9) | PASS |
| T100 | test_middleware_invalid_format (Req 1, Req 9) | PASS |
| T110 | test_middleware_valid_token (Req 4) | PASS |
| T120 | test_admin_set_cap (Req 8) | PASS |
| T130 | test_log_auth_failure_format (Req 9) | PASS |
| T140 | test_get_jwt_secret_from_secrets_manager (Req 10) | PASS |
| T150 | test_validate_jwt_dual_secret (Req 10) | PASS |

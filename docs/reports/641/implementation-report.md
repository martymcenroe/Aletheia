# Implementation Report — Issues #641, #642, #643, #648, #649 (audit umbrella #637)

## Scope

PR 3 of 5 in the audit-umbrella #637 arc. Applies the class-name-only pattern to all 5 audit-identified exception-text leak surfaces in `src/lambda_auth_function.py`, plus 3 adjacent leaks in the same handlers not flagged by the original audit.

## Audit-identified surfaces fixed (5)

| Issue | Line(s) | Pattern before | Pattern after |
|---|---|---|---|
| #641 (HIGH) | 564, 612 | `json.dumps({"error": str(e)})` (ValueError handlers) | `f"ValueError: {error_class}"` |
| #642 (HIGH) | 268, 649 | `"message": str(e)` (LinkedIn API error) | `"message": error_class` |
| #643 (HIGH) | 498 | `"error": str(e)` in logged JSON dict | `"error": e.__class__.__name__` |
| #648 (MEDIUM) | 131, 165 | `f"...: {response.status_code} - {response.text}"` | `f"...: status={response.status_code}"` |
| #649 (MEDIUM) | 467 | `logger.info(f"... redirectUri: {redirect_uri}")` | line removed |

## Additional adjacent fixes (NOT in original audit)

The same exception handlers had 3 more `f"...: {e}"` style logger lines:

- Line 262 (`logger.error f"LinkedIn API error during token validation: {e}"`) → `LINKEDIN_API_ERROR_TOKEN_VALIDATION: {class}`
- Line 567 (`logger.error f"Token exchange error: {e}"`) → `TOKEN_EXCHANGE_ERROR: {class}`
- Line 615 (`logger.error f"Token refresh error: {e}"`) → `TOKEN_REFRESH_ERROR: {class}`
- Line 643 (`logger.error f"LinkedIn API error during validation: {e}"`) → `LINKEDIN_API_ERROR_VALIDATION: {class}`

These were fixed in the same PR because they're in the same `except` branches as the audit-identified issues — leaving them in place would have been worse than incomplete.

## Test Updates

### New: `TestAuthLambdaExceptionTextDoesNotLeak` in `tests/unit/test_lambda_auth.py`

3 tests using canary strings:

| Test | Asserts |
|---|---|
| `test_token_exchange_failure_log_does_not_include_response_text` | OAuth response body canary absent from log; `TOKEN_EXCHANGE_FAILED` + status code present |
| `test_token_refresh_failure_log_does_not_include_response_text` | Same for refresh path |
| `test_redirect_uri_not_logged` | User-supplied redirect URI canary absent from logs entirely |

The 5 audit issues span 8 code locations; 3 are tested by direct canary, the remaining 5 are tested-by-pattern (same mechanical fix applied) and covered by the existing 46-test auth regression suite. Re-audit at the end of the umbrella will surface any leaks the unit tests miss.

## Resolves

- #641 (H4, HIGH)
- #642 (H5, HIGH)
- #643 (H6, HIGH)
- #648 (M11, MEDIUM)
- #649 (M12, MEDIUM)

Part of umbrella #637 (13 of 14 surfaces resolved after this PR; 1 remaining across PRs 4-5).

## Blast Radius

Code change in `src/lambda_auth_function.py` only. `provision.sh` redeploys the **Auth Lambda** (`AletheiaAuth`) — this is the FIRST audit-arc PR that touches the Auth Lambda specifically. Smoke test must exercise an auth endpoint (e.g. `POST /auth/token` returns 400 for missing params, confirms handler loads).

# Implementation Report — Issue #668

## Scope

Surgical revert of response-payload scrubbing introduced in PRs #636, #652, #653, #654, #656. Keeps the (correct) log-side scrubbing. Aligns main with what's currently deployed in production.

## Why

Earlier today's umbrella-#637 fix arc conflated two distinct concerns:

- **Logs (server-side)** — Aletheia's public observability commitment in `docs/observability.html` is absolute: *"NEVER log prompt text, user input, completion text, URLs, or user IDs."* Scrubbing exception text from `logger.*` calls is correct.
- **Response payloads (user-facing)** — The privacy policy in `docs/privacy.html` makes no commitment to scrub responses going back to the user who made the request. The user is the source of their own input; receiving their own error text isn't a privacy leak.

The fix arc applied the same scrub to BOTH surfaces, making user-facing errors strictly worse (e.g., `{"error": "ValueError: ValueError"}` tautology) with zero privacy gain.

## State before this PR

| Surface | State |
|---|---|
| Production | Reverted to `str(e)` via emergency direct `provision.sh` deploy |
| Origin/main | Still has the broken class-name-only response fields from PRs #636, #652, #653, #654, #656 |
| Risk | Anyone running `provision.sh` from clean main re-deploys the broken behavior |

This PR closes that gap.

## Source code reverts (8 lines)

| File:line | Before this PR | After this PR |
|---|---|---|
| `src/guardrails/semantic.py:174` | `"reason": f"Guardrail Error: {error_class}"` | `f"Guardrail Error: {str(e)}"` |
| `src/lambda_function.py:511` | `"gem": f"Generation Error: {error_class}"` | `"gem": str(e)` |
| `src/etymologist.py:789` | `"error": error_class` | `"error": str(e)` |
| `src/etymologist.py:862` | `metadata["opus_verifier_error"] = error_class` | `= str(e)` |
| `src/lambda_auth_function.py:271` | `"message": error_class` | `"message": str(e)` |
| `src/lambda_auth_function.py:570` | `"error": f"ValueError: {e.__class__.__name__}"` | `"error": str(e)` |
| `src/lambda_auth_function.py:620` | same pattern | same fix |
| `src/lambda_auth_function.py:660` | `"message": error_class` | `"message": str(e)` |

All `logger.error/info/warning` lines REMAIN class-name-only. The privacy comments referencing audit issues were either updated or stayed in place where the log-side reasoning still applies.

## NOT reverting

- `src/signal_inspector/fetcher.py` — CLI-only, not in Lambda's import path.
- `src/poetic_analyzer.py:333` — only had a log change, no response change to revert.
- The `_log_unicode_diagnostics` deletion in `src/etymologist.py` — that function logged LLM completion-text characters, which IS a real observability.html violation. Deletion stays.
- The `json_str[:200]` log removal in `src/etymologist.py` — same reasoning.
- `tools/cws_image_pad.py` and `screenshots/cws/` (today's CWS image work — uncommitted on local main; separate concern).
- All doc edits (privacy.html, observability.html, CLAUDE.md, ENGINEERING-JOURNAL.md, 10816 audit) — separate concerns.

## Tests

Full unit suite: **835 passed, 0 failures.**

Changes:
- Deleted response-checking tests added in the umbrella-#637 arc; kept their log-checking siblings.
  - `test_semantic.py::TestExceptionTextDoesNotLeak` — kept only `test_exception_message_not_in_log_output`, renamed class to `TestExceptionTextDoesNotLeakIntoLog`.
  - `test_etymologist.py::TestEtymologistExceptionTextDoesNotLeak` — kept `test_bedrock_exception_text_not_in_log` and `test_json_decode_error_does_not_log_completion_text`, renamed class to `TestEtymologistExceptionTextDoesNotLeakIntoLog`.
- Restored 3 existing tests that had been modified to codify the broken response-field behavior:
  - `test_etymologist.py::test_bedrock_exception_returns_error`
  - `test_etymologist.py::test_verifier_falls_back_on_opus_exception`
  - `test_persistence.py::test_020_generation_failure_still_saves`

## Deploy

`provision.sh` deploy required after merge to confirm a deploy from clean main produces the same state production already has. Smoke test: curl `/auth/token` with bogus code — expected `{"error": "Token exchange failed: 401"}`, NOT `{"error": "ValueError: ValueError"}`.

## Closes

- #668

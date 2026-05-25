# Implementation Report — Issue #644 (audit umbrella #637)

## Scope

PR 4 of 5 in the audit-umbrella #637 arc. Fixes `src/signal_inspector/fetcher.py` line 140 (audit M7) plus 4 adjacent URL/exception-text leaks in the same exception handlers.

## Audit-identified surface (1)

| Issue | Line | Pattern before | Pattern after |
|---|---|---|---|
| #644 (MEDIUM) | 140 | `return None, {}, None, str(e)` | `return ..., e.__class__.__name__` |

## Additional adjacent fixes (NOT in original audit)

The fetcher's three exception handlers (lines 132-140) all logged the user-supplied `url` AND, where applicable, `{e}`. The URL logging violates the never-log-URLs constraint from `docs/observability.html`:

| Line | Pattern before | Pattern after |
|---|---|---|
| 133 | `logger.warning(f"Timeout fetching {url}")` | `logger.warning("FETCH_TIMEOUT")` |
| 136 | `logger.warning(f"Connection error fetching {url}: {e}")` | `logger.warning(f"FETCH_CONNECTION_ERROR: {class}")` |
| 139 | `logger.warning(f"Error fetching {url}: {e}")` | `logger.warning(f"FETCH_REQUEST_ERROR: {class}")` |

## Deploy Disposition

**No `provision.sh` required.** `signal_inspector` is not imported by anything in `src/` — it's a CLI-only module used by `tools/inspect_signals.py` for offline signal auditing. The fix lands on `main` but does not need a Lambda redeploy.

## Test Updates

### New: `TestFetcherExceptionTextDoesNotLeak` (2 tests)

| Test | Asserts |
|---|---|
| `test_request_exception_does_not_leak_url_or_message_into_log` | Canary URL absent from log; `FETCH_*` token present |
| `test_request_exception_does_not_leak_message_into_return_tuple` | Canary URL absent from 4th tuple element of `fetch_page` return |

## Resolves

- #644 (M7, MEDIUM)

Part of umbrella #637 (14 of 14 surfaces resolved after this PR plus PR 5; this PR resolves 1).

## Blast Radius

CLI-only. No runtime change to any Lambda. Rollback is `git revert`.

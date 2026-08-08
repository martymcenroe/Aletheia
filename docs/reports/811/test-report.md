# Test Report — Issue #811

## Result

```
857 passed, 4 deselected in 5.02s
ruff check src/ tests/  — All checks passed
bash -n provision.sh    — syntax OK
```

23 new tests. No regressions.

The 4 deselected are `tests/unit/test_signal_inspector.py::TestLiveWebsites`,
covered under "Pre-existing failure" below.

## New — `tests/unit/test_refresh_token_service.py` (14 tests)

Backed by `moto` against a real DynamoDB table shape.

### Generation and hashing
- Tokens are unique across 200 generations.
- Tokens carry at least 43 characters (32 bytes urlsafe-encoded).
- Hashing is deterministic per token and distinct across tokens.

### Storage secrecy
- `test_only_the_hash_is_persisted_never_the_plaintext` — scans the table after
  a store and asserts the plaintext token does not appear anywhere in the
  persisted item, and that the hash does. This is the assertion that makes a
  table read worthless to an attacker.

### Validation
- Round-trip store → validate returns the owning `user_id`.
- Unknown tokens rejected.
- Empty and non-string input rejected.
- Revoked tokens rejected.
- `test_expired_token_is_rejected_in_code_not_left_to_dynamodb_ttl` — rewrites
  `ttl` into the past while leaving the row present, reproducing exactly what a
  lagging DynamoDB sweeper looks like, and asserts the token is still refused.
  Without this, expiry would be enforced only by a mechanism documented to lag
  up to 48 hours.
- `test_returned_user_id_comes_from_storage_not_the_caller` — two tokens owned
  by two users each resolve strictly to their own owner. Guards the highest-
  severity failure mode: a valid token minting a session for someone else.

### Failure behavior
- `last_used_at` is recorded on successful validation.
- `test_touch_failure_does_not_deny_a_valid_refresh` — an `update_item` failure
  during bookkeeping must not deny an otherwise-valid refresh.
- `test_lookup_failure_fails_closed` — a datastore error denies rather than
  admits.
- `test_lookup_failure_does_not_log_exception_text` — plants a canary inside the
  raised exception and asserts it never reaches the log records, per the
  standing rule that exception text must not appear in auth paths.

## New — `tests/unit/test_auth_refresh_endpoint.py` (9 tests)

- Missing `aletheiaRefreshToken` → 400.
- Invalid token → 401.
- Valid token → 200 with a JWT whose `user_id` is the stored owner.
- `test_refresh_preserves_tier_and_billing_anchor` — parameterized over
  `free`/`pro`/`unlimited`. `create_jwt` defaults `tier` to `"free"`, so without
  the tier lookup every renewal would silently downgrade a paying user. This
  test fails if that lookup is ever dropped.
- `test_tier_is_reread_on_every_refresh` — an upgrade takes effect on the next
  renewal without a re-login.
- `test_refresh_never_calls_linkedin` — asserts both LinkedIn call sites are
  untouched on the refresh path. This is the structural guarantee that the
  session no longer depends on a provider that cannot support it.
- `test_refresh_response_carries_no_token_material` — the response exposes the
  JWT only, never the refresh token.

## Changed — `tests/unit/test_lambda_auth.py`

- `aws_env` fixture now provisions the refresh-tokens table.
- `test_handle_token_exchange` additionally asserts login returns a non-empty
  `aletheiaRefreshToken`. Without this the login path could regress to issuing
  an unrenewable session and the suite would stay green.
- `test_handle_token_refresh` was **rewritten**. It previously asserted the
  LinkedIn `grant_type=refresh_token` path returning an `accessToken`. That test
  passed while the feature was entirely non-functional in production, because it
  asserted the behavior of a code path the real client could never successfully
  reach — LinkedIn does not issue refresh tokens for the requested scopes, so
  the input it mocked never existed in the wild. It now asserts the real
  contract: an Aletheia refresh token in, a verified JWT out.
- Added `test_handle_token_refresh_rejects_unknown_token`.

## Not covered by automated tests

- **Live AWS round-trip.** DynamoDB access is exercised against `moto`, not real
  DynamoDB. The new IAM statement and `REFRESH_TOKENS_TABLE` env var are
  unverified until `provision.sh` runs; a missing permission would surface as a
  fail-closed 401 at runtime, not as a test failure.
- **End-to-end browser behavior.** No client change ships here, so the
  user-visible defect is not yet fixed or testable end to end. That arrives with
  #812/#813/#814.

## Pre-existing failure (not from this change)

`tests/unit/test_signal_inspector.py::TestLiveWebsites::test_noarchive_net_blocked_without_force`
fails identically on a clean `main` at `6be7bcb` with no working-tree changes.
It asserts a third party's live robots.txt, which appears to have changed.
Filed as #817 and deselected from this run. It is unrelated to auth.

# Test Report — Issues #815, #816, #819, #824

## Result

```
879 passed, 4 deselected in 14.30s
ruff check src/ tests/  — All checks passed
bash -n provision.sh    — syntax OK
```

Up from 857. No regressions.

The 4 deselected are `tests/unit/test_signal_inspector.py::TestLiveWebsites`
(#817 — fails locally against a live third-party site, passes in CI).

## New — `tests/unit/test_auth_401_reasons.py` (9 tests, #815)

- Six parameterized cases mapping each internal validation reason onto the
  public enum.
- `test_expired_is_distinguishable_from_invalid` — the entire point of the
  issue. If these ever collapse to the same value the client is back to
  guessing, and this test fails.
- `test_secret_unavailable_is_not_reported_as_a_bad_credential` — asserts a
  missing signing secret maps to `server_error` and explicitly **not** to
  `invalid_token`. Getting this wrong would make clients discard valid sessions
  during a server outage, converting a brief incident into mass sign-outs.
- `test_unknown_internal_reason_is_not_echoed` — a future internal reason
  string collapses to `invalid_token` rather than crossing the boundary.
- `test_no_reason_escapes_the_fixed_enum` — parameterized over every known
  input plus unknown and `None`; the enum is closed.
- `test_401_body_never_carries_token_or_claim_material` — asserts the body keys
  are exactly `{"error", "reason"}` and that `user_id`, `jti`, `exp`, `claims`,
  `token`, `sub` are absent. This is the assertion that fails if someone later
  adds a "helpful" debugging field.
- `test_default_reason_is_the_conservative_one` — an un-annotated call must not
  imply a renewable condition.

## New — `test_linkedin_refresh_path_no_longer_exists` (#816)

Asserts `refresh_access_token` is gone from the module, not merely unwired, so
the dead path cannot quietly return.

## Retargeted — the #648 privacy canary (#816 / #824)

`test_token_refresh_failure_log_does_not_include_response_text` was the sole
caller of the removed function. Rather than delete the assertion, it was
**retargeted** at `fetch_linkedin_profile` — a live call site that was actually
leaking — and renamed accordingly. It plants a canary in a mocked LinkedIn
error body and asserts the body never reaches log records, while
`LINKEDIN_USERINFO_FAILED` and `status=500` do.

Net effect: log-hygiene coverage **increased**. The retired test guarded code
that could not run; its replacement guards code that runs on every failed
profile fetch.

## Changed — `test_refresh_never_calls_linkedin`

Dropped its `patch.object(auth_func, "refresh_access_token")`, which would now
fail against a deleted attribute. The guarantee is stronger than before: the
function does not exist, asserted directly by the new test above.

## A mistake worth recording

The retargeted canary initially called `get_linkedin_user_info` and failed with
`DID NOT RAISE`. The leak was in `fetch_linkedin_profile`. Both issue #824's
body and the first draft of this test named the wrong function, because the
file and line number were correct while the enclosing function was assumed
rather than checked.

That is the same confusion that let the defect survive #648: two near-duplicate
functions call the same endpoint, and the one whose name reads like the obvious
target is the one that was already correct. Issue #824 has been corrected, and
the duplication is filed as #825.

## Not covered by automated tests

- **No test exercises the deployed 401 discriminator.** The middleware is
  tested directly; nothing here proves the field survives to the wire through
  the CloudFlare Worker. Verifiable post-deploy with an unauthenticated `curl`.
- **The client does not yet branch on `reason`.** #814 renews on any 401 and
  only prompts after renewal fails, which is correct but coarser than the
  discriminator now permits. No test asserts client behavior per reason,
  because no such behavior exists yet.
- **#819 is unverified by any test.** It changes text `provision.sh` prints;
  confirmed only by `bash -n` and reading. It will be observable on the next
  legitimate provisioning run.

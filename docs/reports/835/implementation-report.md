# Implementation Report — Issue #835

## What was found

A fresh scan of `src/` found **50** `logger.*` calls interpolating exception
text into log messages:

- **34** in files umbrella #637 never scoped — `src/auth/*.py`,
  `src/guardrails/denylist.py`, `src/observability.py`.
- **16** in files #637 *did* cover. That audit fixed 14 enumerated line
  numbers; the pattern persisted elsewhere in the same files.

This is the second time #637's inventory has proven incomplete. #824
(`fetch_linkedin_profile` logging `response.text`) was a live leak absent from
its table, found only by following a sibling issue's pre-removal gate.

## Why it matters

`docs/observability.html` is a public, absolute commitment:

> NEVER log prompt text, user input, completion text, URLs, or user IDs.

Exception messages are unbounded third-party text.
`botocore.exceptions.ClientError` can echo request field values back, and
several of these sites wrap DynamoDB operations keyed on `user_id`.

## Change

49 sites rewritten to `e.__class__.__name__`, the pattern established by
#636/#619. The diff is 49 insertions and 49 deletions — strictly one-for-one
line rewrites, no control flow touched.

Both call styles were handled:

```python
logger.error(f"...: {e}")                 →  logger.error(f"...: {e.__class__.__name__}")
logger.error("...: %s", str(e))           →  logger.error("...: %s", e.__class__.__name__)
```

## Deliberately unchanged

**One site kept**, at `src/lambda_function.py:237`:

```python
logger.error(f"DynamoDB error: {e.response['Error']['Code']}")
```

This extracts a single audited attribute rather than the whole message, which is
the documented way to retain more signal than a bare class name. Rewriting it
would have lost real diagnostic value for no privacy gain.

**Response payloads untouched.** Issue #668 reverted an earlier over-scrub that
reached returned fields — `gem`, `reason`, `message`, `error`,
`metadata.error`, `metadata.opus_verifier_error`. The operator caught that
regression in production and ordered an emergency fix. The recorded reasoning
is that the response goes back to the user who made the request, who already
knows their own input, and that the scrubbing produced tautologies like
`{"error": "ValueError: ValueError"}` for zero benefit. Nothing here touches a
returned field.

**Identifier logging left in place.** Three sites log an identifier directly
alongside the exception:

```
src/lambda_auth_function.py:422   f"Failed to get user tier for {user_id}: ..."
src/lambda_auth_function.py:997   f"GDPR deletion error for user {user_id}: ..."
src/lambda_auth_function.py:755   f"...Stripe cancellation failed for {sub_id}: ..."
```

Two sit on the GDPR erasure path — the one place a user has explicitly asked to
stop being identifiable. This is a direct violation of the same commitment and
arguably worse than the exception-text class, since no inference is required.

It is **not** fixed here because #711 already owns identifier handling in audit
log lines, and whether these become hashed or dropped is that issue's decision.
Settling it unilaterally inside a log-scrubbing PR would pre-empt it. A fourth
site, `lambda_auth_function.py:386` (`f"Created new user: {user_id}"`), was
noticed during this work and belongs to the same decision.

## The regression test

`tests/compliance/test_log_privacy.py` scans `src/` and fails on any logger call
interpolating exception text.

This is the substantive part. #637 demonstrated that fixing enumerated line
numbers does not hold — the same files regrew the pattern, and 34 more surfaces
sat outside the audited set entirely. A source scan makes the defect class
unrepresentable rather than merely absent today.

It carries an explicit out-of-scope assertion so it can never be extended into
response payloads and re-cause the #668 regression.

## Blast radius

Log text only. No control flow, no response payload, no auth decision.

Diagnostic detail is reduced: an exception's message is lost, leaving its class
plus any safe attribute extraction. That is the tradeoff the observability
commitment already accepts and which #668 explicitly preserved for logs.

## Deploy

Server-side; merging does not deploy. **Not deployed** — landed overnight for
review. A code-only deploy is sufficient:

```
aws lambda update-function-code --function-name AletheiaAgent --zip-file fileb://<new>.zip
aws lambda update-function-code --function-name AletheiaAuth  --zip-file fileb://<new>.zip
```

Avoid a full `provision.sh` run — it re-applies the whole environment and can
blank `CLOUDFLARE_ORIGIN_SECRET` on a transient SSM failure (#779).

## Rollback

`git revert <sha>` plus the same code-only deploy.

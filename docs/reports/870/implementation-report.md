# Implementation Report — Issue #870 (with the code half of #869)

## What changed

**The operator's own analysis records are attributed and kept forever. Everyone
else's carry no user identifier and expire in 30 days.** This is a standing
operator directive and cannot be overridden.

### `src/lambda_function.py`

- `operator_user_ids()` reads `OPERATOR_USER_IDS` from the environment on every
  call (comma, pipe or whitespace separated). `is_operator()` is an exact string
  match only.
- `save_state` writes `user_id` **and no `ttl`** when the ID is an operator's.
  For anyone else it writes no `user_id` and a 30-day `ttl`. The operator check
  lives inside `save_state`, so no caller can attribute a non-operator row.
- The call site passes the middleware-authenticated `auth_user_id` only. The
  old `body.get("userId")` fallback is gone: any client can put any value in
  the body, so it could have claimed the carve-out.
- If an authenticated write happens while `OPERATOR_USER_IDS` is unset, a
  class-only warning (`OPERATOR_USER_IDS_UNSET`) is logged on every such write,
  because the operator's records would otherwise expire silently.

### `src/lambda_auth_function.py`

- `_delete_analysis_records` and its call in `delete_user_data` are removed.
  Erasure still covers the profile, the Stripe cancellation, coupons and rate
  limits. `analysis_records` is no longer in the `DELETE /my-data` summary.
- **This also repairs production erasure.** The live table has no
  `user_id-index`, so the removed first step failed with `ValidationException`
  and `DELETE /my-data` returned 500 having deleted nothing (verified read-only
  on 2026-09-22).

### `provision.sh`

- The block that created `user_id-index` is removed, so a full provision run
  will not rebuild it.
- `OPERATOR_USER_IDS` is read from SSM `/aletheia/operator-user-ids` and passed
  into the analysis Lambda's environment. The script **aborts before any
  change** if the value is missing or empty, so a failed read cannot silently
  write an empty value (the #779 pattern).

### `tools/data_hygiene.py` — the cleanup script

- Every mode that writes or deletes (`--normalize`, `--backfill-ttl`,
  `--deduplicate`, `--clean-common`) now takes its rows from
  `scan_modifiable_items()`, which withholds retained records before any mode
  sees them. It is the single choke point, so no mode can bypass it.
- A record is **retained** if it carries an operator `user_id` or has no `ttl`
  (the operator's records are written without one, and so were the legacy rows).
- The operator IDs load from SSM at startup for every mode. If they cannot be
  loaded, or the value is empty, the tool exits before scanning anything.
- `--normalize` needed this as much as `--backfill-ttl`: it deletes and
  re-creates `raw_capture` rows, which would have dropped `user_id` and added
  a `ttl`.

### `tools/backfill_operator_attribution.py` — new, one-off

Sets `user_id` on rows that have neither `user_id` nor `ttl` (the 19 legacy
rows from 2026-01-01 to 01-04, which are the operator's). It dry-runs by default,
needs `--apply` to write, saves the keys to `data/backfill-870-<ts>.json` before
writing, and makes each write conditional on the row still having neither
attribute. It never deletes and never adds a `ttl`.

## Where the operator ID lives

SSM `/aletheia/operator-user-ids` (String). It is never in git, because this
repository is public. The analysis Lambda gets it through `provision.sh`, and
the cleanup and backfill tools read it directly.

## Not in this change

- **`docs/privacy.html`** — per #869, the policy changes after the code is
  deployed and verified, so every sentence traces to running code. #869 stays
  open for that.
- **Refresh-token erasure** — `delete_user_data` has never deleted refresh
  tokens. That was raised on #869 and is not addressed here.
- **Other accounts.** `aletheia-users` holds two accounts besides the
  operator's. Their records follow #869; the carve-out is the configured ID only.

## Deploy sequence (none of this happens on merge)

1. Create the SSM parameter `/aletheia/operator-user-ids` with the operator's ID.
2. Add `OPERATOR_USER_IDS` to the `AletheiaAgent` environment **without
   rewriting the rest of it** (#779), then deploy the code to `AletheiaAgent`
   and `AletheiaAuth` with `update-function-code`.
3. Run the backfill: dry run, then `--apply`.
4. Verify: a live operator analysis writes `user_id` and no `ttl`; the 19 rows
   carry `user_id`; `data_hygiene.py --scan` reports them as retained.

## Rollback

- Code: `git revert <sha>`, then `update-function-code` on both Lambdas.
- Env: remove `OPERATOR_USER_IDS` from `AletheiaAgent`. New operator rows then
  get a `ttl`, so do this only alongside a code revert.
- Backfill: `REMOVE user_id` on the keys in the saved `data/backfill-870-*.json`.

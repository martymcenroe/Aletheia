# Implementation Report — Issue #680

## Scope

Two things in one PR:

1. **Fix the three failing assertions** that have kept `mergeable_state` at `unstable` on every Aletheia PR for months. Test bug from PR #568, not a production bug — `_delete_user_profile` and the rest of the GDPR erasure path were correct all along.
2. **Add coverage for the state-space holes** the existing three tests didn't reach. With #697 closing the `test-edge` half of the unstable signal, fixing #680 fully is what restores `clean` as a reachable merge gate. While we're in the file, the integration suite is the cheapest place to add the missing coverage.

Production code in `src/lambda_auth_function.py` is untouched. All work is in the integration test file plus the report pair.

## Background — the state space

`delete_user_data(user_id)` touches five data-bearing surfaces:

| Surface | Helper | What deletion means |
|---|---|---|
| `AletheiaAgentState` (analysis records) | `_delete_analysis_records` | Query GSI on `user_id`, paginate, delete each item |
| `aletheia-users` (profile row) | `_delete_user_profile` | DeleteItem with `ReturnValues=ALL_OLD`; True iff the row existed |
| Stripe subscription | `_cancel_stripe_subscription` | If profile has `stripe_subscription_id`, call `stripe.Subscription.cancel` |
| `aletheia-coupons` (`redeemed_by` SS) | `_remove_from_coupon_redeemed_by` | Scan for `contains(redeemed_by, :uid)`, paginate, `DELETE redeemed_by :user_set` on each |
| `aletheia-token-cap` (rate-limit windows) | `_delete_rate_limit_records` | Query `PK = USER#{user_id}`, paginate, delete each row |

Each surface can be in 2+ states for a given `user_id`, independently of the others. Pre-#680 the integration suite exercised the analysis-records dimension only (happy path, pagination, no-records). Every other surface was untested at the integration boundary.

## Changes

### `tests/integration/test_dynamodb_ops.py`

Replaced `TestDeleteUserData` (three tests, all asserting `profile_deleted is True` without seeding a profile row) with eleven tests covering each surface and a full-spectrum integration validator. Three small module-level helpers added for seed setup:

| Helper | Seeds |
|---|---|
| `_seed_user_profile(client, users_table, user_id, stripe_subscription_id=None)` | One row in `aletheia-users`; optionally with a Stripe sub ID |
| `_seed_coupon_redemption(client, coupons_table, code, redeemed_by_user_ids)` | One coupon row with `redeemed_by` as String Set |
| `_seed_token_cap_rows(client, token_cap_table, user_id, count)` | N rows under `PK=USER#{user_id}`, distinct SKs |

Test list:

| Test | Scenario | New / Fixed |
|---|---|---|
| `test_010_delete_user_data_happy_path` | Profile + 10 analysis records, no Stripe | Fixed — now seeds profile |
| `test_011_profile_only` | Profile exists, no analysis records | New |
| `test_020_delete_user_data_pagination` | Profile + 2000 analysis records (>1MB) | Fixed — now seeds profile |
| `test_030_delete_user_data_no_items` | Nonexistent user, nothing anywhere | Fixed — flipped assertion to `profile_deleted is False` |
| `test_031_records_only_orphan` | Analysis records, no profile (partial-erasure state) | New |
| `test_032_stripe_subscriber_cancel_succeeds` | Profile with Stripe sub, mock cancel returns OK | New |
| `test_033_stripe_cancel_fails_but_rest_completes` | Stripe.cancel raises, rest of erasure must still complete | New |
| `test_034_coupon_single_redemption` | One coupon with user_id in `redeemed_by` set | New |
| `test_035_coupon_many_redemptions_pagination` | 100 coupons exercising the scan-loop | New |
| `test_036_token_cap_rows` | 5 rate-limit window rows | New |
| `test_037_full_spectrum` | Every surface active simultaneously | New |

All new tests assert on both the summary dict that `delete_user_data` returns AND the actual state of every relevant DynamoDB table after the call. The full-spectrum test (037) is the integration validator: if a future refactor of `delete_user_data` forgets one of the five surfaces, 037 catches it without needing a per-surface deep dive.

### Mocking strategy for Stripe

`_cancel_stripe_subscription` imports `stripe` lazily inside its try block (line 724). Tests patch at the package level:

```python
with patch("stripe.Subscription.cancel") as mock_cancel, patch(
    "auth.stripe_handler.get_stripe_api_key", return_value="sk_test_fake"
):
    result = auth_module.delete_user_data(user_id)
```

Patching at the package level (`stripe.Subscription.cancel`) rather than the import site means the patch survives the lazy import inside the function body. The fake API key prevents the real `get_stripe_api_key` from trying to hit Secrets Manager during a unit-flavor test.

### Helper docstrings record the production contract

Each helper's docstring names the production code path it feeds — `_remove_from_coupon_redeemed_by` requires `redeemed_by` as an SS (String Set) attribute, not a list, because the production code uses both `contains(redeemed_by, :uid)` and `DELETE redeemed_by :user_set`, both SS-specific. Future maintainers reading the helper see why the type matters.

## Out of scope

- **Production code changes.** `_delete_user_profile`, `_cancel_stripe_subscription`, `_delete_analysis_records`, `_remove_from_coupon_redeemed_by`, `_delete_rate_limit_records`, and `delete_user_data` itself are all unchanged. The tests now correctly verify the behavior these helpers already had.
- **Audit log hashing** (the `user_id` and `sub_id` leakage into CloudWatch) — tracked separately as #711. Brought up during the discussion that led to this PR; deliberately split so the test-bug-fix and the compliance gap don't get conflated.
- **Exception-text leaks** in `logger.warning(... {e})` on lines 731, 780, 815, 973 — tracked under #637.
- **Other un-touched-by-this-test user_id log emissions** (lines 409, 445) — same shape of concern as #711 but on the login-and-tier paths, not the deletion path; would be a separate issue.
- **Concurrency / mid-deletion-failure recovery** — `delete_user_data` runs serially through the five surfaces with no transaction. If a Lambda timeout cuts the procedure in half, the user is left partially erased. This is a real concern but out of scope here; tests verify each surface independently and in combination, not the interrupted-mid-flight case.

## Verification

```bash
cd /c/Users/mcwiz/Projects/Aletheia
poetry run pytest tests/integration/test_dynamodb_ops.py -k TestDeleteUserData -v
```

Local run on this branch: 11 tests pass in 4.35 seconds (moto-based fixtures, no network).

Side effect: the `integration-tests` CI check should turn green on this PR. Together with #697 having removed the `test-edge` check entirely, this means `mergeable_state == clean` becomes reachable again on every future Aletheia PR — restoring the local-confidence signal the universal CLAUDE.md merge sequence was designed around.

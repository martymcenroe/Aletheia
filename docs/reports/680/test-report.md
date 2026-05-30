# Test Report — Issue #680

## What this PR tests

Eleven integration tests under `tests/integration/test_dynamodb_ops.py::TestDeleteUserData`, covering the GDPR Article 17 erasure procedure in `src/lambda_auth_function.py::delete_user_data` across the full state-space of user data.

## Run results

```
$ cd /c/Users/mcwiz/Projects/Aletheia-680
$ poetry run pytest tests/integration/test_dynamodb_ops.py -k TestDeleteUserData -v
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\mcwiz\Projects\Aletheia-680
configfile: pyproject.toml
plugins: benchmark-5.2.3, cov-7.1.0
collected 14 items / 3 deselected / 11 selected

test_010_delete_user_data_happy_path             PASSED   [  9%]
test_011_profile_only                            PASSED   [ 18%]
test_020_delete_user_data_pagination             PASSED   [ 27%]
test_030_delete_user_data_no_items               PASSED   [ 36%]
test_031_records_only_orphan                     PASSED   [ 45%]
test_032_stripe_subscriber_cancel_succeeds       PASSED   [ 54%]
test_033_stripe_cancel_fails_but_rest_completes  PASSED   [ 63%]
test_034_coupon_single_redemption                PASSED   [ 72%]
test_035_coupon_many_redemptions_pagination      PASSED   [ 81%]
test_036_token_cap_rows                          PASSED   [ 90%]
test_037_full_spectrum                           PASSED   [100%]

====================== 11 passed, 3 deselected in 4.35s =======================
```

All 11 pass. Total wall-clock 4.35 seconds (moto-based fixtures, no network, no Docker).

The "3 deselected" are the other classes in the file (`TestSaveState`, `TestGSIQuery`, `TestTableCreation`) — `-k TestDeleteUserData` filtered to the class under test.

## What each test verifies

Per-test verification is dual: the **summary dict** returned by `delete_user_data` AND the **actual state of every relevant DynamoDB table** after the call. If a future refactor of `delete_user_data` started lying about the counts in its return value, the table-state assertions catch it. If it started skipping a surface but returning honest counts, the dict assertions don't catch it but the table-state assertions do.

| Test | Profile seeded? | Records | Stripe | Coupons | Token-cap | Asserts that... |
|---|---|---|---|---|---|---|
| 010 | yes, plain | 10 | — | — | — | analysis_records=10, profile_deleted=True, table empty |
| 011 | yes, plain | 0 | — | — | — | analysis_records=0, profile_deleted=True, table empty |
| 020 | yes, plain | 2000 (pagination) | — | — | — | analysis_records=2000, profile_deleted=True, table empty |
| 030 | no | 0 | — | — | — | analysis_records=0, **profile_deleted=False** (was the bug), all other surfaces zero |
| 031 | no | 10 (sample_user_data) | — | — | — | analysis_records=10, profile_deleted=False, records still wiped |
| 032 | yes, +stripe sub | 0 | mock.cancel returns OK | — | — | stripe_cancelled=True, mock called once with sub_id |
| 033 | yes, +stripe sub | 10 | mock.cancel raises | — | — | stripe_cancelled=False, BUT profile_deleted=True and analysis_records=10 (rest completed despite Stripe failure) |
| 034 | yes, plain | 0 | — | 1 coupon, redeemed_by=[user, other-user] | — | coupons_updated=1, user_id absent from set, other-user preserved |
| 035 | yes, plain | 0 | — | 100 coupons in user's name | — | coupons_updated=100, spot-checked across the range |
| 036 | yes, plain | 0 | — | — | 5 windows | rate_limits_deleted=5, all rows for PK=USER#... gone |
| 037 | yes, +stripe sub | 10 | mock.cancel returns OK | 1 coupon | 3 windows | every count correct, every surface wiped |

## Regression scope

Production source files (`src/lambda_auth_function.py` and everything else in `src/`) are not touched by this PR. The `dist/aletheia-firefox-v1.1.2.zip` and `dist/aletheia-chrome-v1.1.2.zip` content is unaffected. CI workflows are unaffected. The change is bounded to:

- `tests/integration/test_dynamodb_ops.py` — `TestDeleteUserData` class rewritten in full, plus three module-level helpers and one import. `TestSaveState`, `TestGSIQuery`, `TestTableCreation` are preserved byte-for-byte.
- `docs/reports/680/implementation-report.md` — this PR's implementation report
- `docs/reports/680/test-report.md` — this file

No production behavior change is being asserted by these tests that wasn't already production behavior. The pre-#680 tests asserted incorrect expected values (`profile_deleted is True` without seeding a profile); this PR brings the assertions in line with what the production code actually returns.

## Mocking — why it's safe

`_cancel_stripe_subscription` (line 717) imports `stripe` lazily and calls `stripe.Subscription.cancel(sub_id)`. The two tests that exercise the Stripe path (032, 033, and indirectly 037) use `unittest.mock.patch`:

```python
with patch("stripe.Subscription.cancel") as mock_cancel, patch(
    "auth.stripe_handler.get_stripe_api_key", return_value="sk_test_fake"
):
    result = auth_module.delete_user_data(user_id)
    mock_cancel.assert_called_once_with(sub_id)
```

Patching at the package level (`stripe.Subscription.cancel`) means the patch is in effect when the lazy `import stripe as stripe_lib` runs inside the function body — `stripe_lib.Subscription.cancel` resolves to the mock. The fake API key prevents the real `get_stripe_api_key` from trying to fetch from Secrets Manager during a test.

No real Stripe API call is made by any test. No real Secrets Manager call either. The Stripe behavior we're verifying is: "production code correctly handles cancel-succeeds, correctly handles cancel-raises, correctly skips when no subscription is on the profile." We are not verifying Stripe's own behavior; that's Stripe's job.

## What this report does NOT claim

- Does not claim the production code is bug-free. It claims that the production code behaves as the tests assert for the eleven scenarios covered, and that the pre-#680 tests' assertion failures were the tests' bugs, not the production code's.
- Does not claim Lambda-timeout-mid-deletion is handled. The procedure is non-transactional; a Lambda timeout in the middle leaves the user partially erased. That's a real concern but a separate scope.
- Does not claim concurrent erasure calls are safe. If two erasure requests for the same user_id fire simultaneously, the helpers' interactions with DynamoDB are best-effort. Outside scope of this issue.
- Does not assert anything about Stripe's actual `cancel` API behavior. Only that our code's response to mocked success and mocked failure is correct.

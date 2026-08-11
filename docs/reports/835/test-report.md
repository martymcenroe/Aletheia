# Test Report — Issue #835

## Result

```
poetry run pytest -q            →  934 passed, 3 skipped, 4 deselected   exit 0
poetry run ruff check src/ tests/  →  All checks passed
```

Up from 930. The four added tests are the whole increase — **no existing test
changed**, which is the important signal: 49 log messages were rewritten and
nothing in the suite depended on their text.

## Scan results

| | Before | After |
|---|---|---|
| Files never scoped by #637 | 34 | 0 |
| Files #637 did cover | 16 | 1 |

The single remaining site is `src/lambda_function.py:237`
(`e.response['Error']['Code']`), deliberately preserved as a sanctioned
audited-attribute extraction.

## New — `tests/compliance/test_log_privacy.py` (4 tests)

- `test_no_logger_call_interpolates_exception_text` — scans every `src/**/*.py`
  and fails on `{e}`, `str(e)`, `repr(e)`, or `e.args` inside a logger call,
  listing file, line and source so the failure is actionable rather than a bare
  count.
- `test_the_scan_actually_inspects_source` — asserts at least 10 files were read
  and that `logger.` appears among them. A scan that silently walks an empty
  tree reports success forever; that is precisely the failure mode this issue is
  about, so it is asserted rather than assumed.
- `test_sanctioned_patterns_are_not_flagged` — the class-name and
  audited-attribute forms must remain usable, otherwise the fix becomes
  unadoptable and future authors work around the test.
- `test_response_payload_assignments_are_out_of_scope` — asserts payload lines
  such as `"gem": str(e)` do not match the logger pattern. This exists so the
  scan can never be widened into returned fields and re-cause the #668
  regression the operator caught in production.

## Mutation testing

The guard was verified by reintroducing the defect, not assumed to work:

```
# appended to src/observability.py
logger.error(f"PROBE: {e}")
```

Result:

```
FAILED ...::test_no_logger_call_interpolates_exception_text
assert not [('src/observability.py', 407, 'logger.error(f"PROBE: {e}")')]
1 failed, 3 passed
```

It bites, and it reports the exact location. The probe was then reverted.

**A mistake made and caught during that revert:** `git checkout
src/observability.py` removed the probe *and* the nine legitimate scrubs in the
same file. The rescan caught it — 10 surfaces reappeared where there had been 1
— and the rewrite was re-applied. Had the rescan not been re-run, the PR would
have shipped one file silently unfixed while the test still passed, because the
test and the file would have regressed together. The lesson is that the rescan,
not the test run, is what proves the source state.

## Not covered

- **Nothing verifies behavior in CloudWatch.** These are static source
  assertions; no test observes a real log line. That gap is structural — proving
  it end to end would mean invoking the Lambdas and reading their log groups.
- **Identifier logging is still present and untested**, deliberately: three
  sites log `user_id`/`sub_id` directly, two on the GDPR erasure path. Owned by
  #711. This report is where that overlap is recorded so it is not lost.
- **Not deployed.** The suite proves the source is clean; production still runs
  the previous code until a code-only deploy is made.

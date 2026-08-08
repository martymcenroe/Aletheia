# Test Report — Issue #817

## Result

```
pytest tests/unit -q                    →  879 passed, 4 deselected   (green)
pytest tests/unit -q -m "not audit"     →  live tests still run       (CI form)
pytest tests/unit -q -m live            →  1 failed, 3 passed, 879 deselected
ruff check src/ tests/                  →  All checks passed
```

No test code changed. No assertion was added, removed, or weakened.

## What was verified

This change alters test *selection*, so the verification is about which tests
run under which invocation — not about new assertions.

**1. The default run is green again.** `879 passed, 4 deselected`. The four
deselected are exactly `TestLiveWebsites`. This is the reported problem fixed.

**2. CI behavior is unchanged — proven, not assumed.** Running CI's actual
command form (`-m "not audit"`) still executes the live tests, and the known
environment-specific failure still appears locally. This confirms a
command-line `-m` overrides `addopts`, which is the mechanism the whole change
depends on. Had this not held, the change would have silently removed live
coverage from CI.

**3. The documented opt-in works.** `-m live` selects exactly the four live
tests and deselects the other 879, matching what the class docstring has always
instructed.

## What is NOT fixed by this change

**The underlying assertion is still wrong.** `noarchive.net` no longer appears
to be robots-blocked for the operator's network, and this change does not
correct that expectation — it stops the failure from contaminating unrelated
local work. The test still fails when run deliberately with `-m live`, and it
still fails on the operator's machine in CI's command form.

That is the honest state: the signal was restored, the underlying disagreement
with reality was not resolved. Whether `noarchive.net` genuinely changed policy,
or whether the operator's network (ISP, DNS, or a proxy) returns a different
robots.txt than GitHub's runners do, is unestablished — and the difference
matters, because one means the assertion is stale and the other means the tool
behaves differently on different networks.

**No fixture was recorded.** The issue proposed pinning behavior with recorded
responses. That was not done, because the tests were already designed as opt-in
live checks and converting them would have discarded real end-to-end coverage
to solve a selection problem. If the live checks later prove flaky in CI as
well, recording fixtures becomes the right answer and should be revisited then.

**CI still runs the live tests.** Excluding them there needs a
`.github/workflows/` edit, which the fine-grained PAT cannot push. Left
deliberately, and explained in the implementation report.

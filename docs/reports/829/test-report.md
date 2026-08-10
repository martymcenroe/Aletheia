# Test Report — Issue #829

## Result

```
poetry run pytest -q          →  930 passed, 3 skipped, 4 deselected   exit 0
poetry run ruff check src/ tests/  →  All checks passed
```

Baseline on `main` @ `cb07b43` was `1 failed, 927 passed` (exit 1). The gate is
unblocked.

The count rises by 3: the previously-failing test now passes, plus two new
tests.

## Baseline comparison performed

The work order asked whether #805's failures also occur on main. They do,
identically:

| Ref | Failures | Disposition |
|---|---|---|
| `main` @ `cb07b43` | `test_audit_index_complete` | `1 failed, 927 passed, 3 skipped, 4 deselected` |
| PR #805 @ `8f0bda5` | `test_audit_index_complete` | `1 failed, 927 passed, 3 skipped, 4 deselected` |

Run in a separate worktree with its own `poetry install --no-root --with dev`,
using the gate's own command shape (`pytest -q --tb=short`), so the comparison
reflects what the tool sees rather than what a narrower invocation would.

## New tests

`TestAuditDiscoveryScope` pins discovery scope from **both** directions,
because either extreme is a silent failure:

- `test_infix_artifacts_are_not_treated_as_indexable_audits` — asserts
  `10833-wiki-audit-and-refresh-plan.md` and `10834-wiki-audit-report-2026-06.md`
  are not discovered as indexable audits. Too-permissive discovery re-admits
  them and the original bug returns.
- `test_conventionally_named_audits_are_still_discovered` — asserts at least 20
  audits are found and names two specific ones. Too-strict discovery would make
  the suite green while quietly enforcing nothing, which is the more dangerous
  direction because nothing complains.

## Mutation testing — and a test I threw away

Both new tests were verified by deliberately reintroducing the defect rather
than assumed to work.

**Mutation:** loosen `AUDIT_PATTERN` to `r"108.*-audit-[^)]+\.md"` (the glob's
semantics). Result:

```
FAILED ...::test_audit_index_complete
FAILED ...::test_infix_artifacts_are_not_treated_as_indexable_audits
2 failed, 5 passed
```

The guard bites, and the mutation reproduces the original failure exactly —
confirming the diagnosis rather than merely being consistent with it.

**A third test was written, then deleted.** It synthesised an index entry for
every discovered file and asserted extraction could match it back. Under
mutation it **passed**, which exposed it as tautological: it took a single
pattern and checked that a file matching that pattern could be matched by that
same pattern — true for any input, incapable of failing.

That is the same defect logged in #827 for three e2e tests. Shipping it would
have added a test that looked like a regression guard and guarded nothing, so
it was removed rather than kept for appearance. The two surviving tests were
kept only because mutation proved they fail.

## Scope verified beyond the failing test

All four index tests shared the glob/regex divergence; only audits had a
filename that triggered it. After the change, the full
`test_index_consistency.py` module passes (7 tests), so the ADR, template and
skill paths still enforce their indexes under the tightened discovery.

An intermediate version of the round-trip test failed on templates, which
correctly revealed that the template guide uses a table row
(`| \`name.md\` | … | Active |`) rather than a markdown link. That difference is
real and is preserved.

## Not covered

- **Whether the fleet gate now exonerates #805** is unverified here. It depends
  on the tool re-running against a green main; the disposition can only be
  confirmed on the next scheduled run.
- **#809 is untouched and still expected to fail.** Its blocker is the
  fleet-wide `cryptography` 50.0.0 install/wheel problem (AssemblyZero#2153),
  which no local change affects.
- **No dependabot PR was merged or approved**, per the work order.

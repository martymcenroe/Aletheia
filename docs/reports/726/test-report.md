# Test Report — Issue #726

## What this PR changes

One runbook file restructured top-to-bottom. Pure documentation. No code, no config, no tests.

## Regression scope

None possible. Documentation rewrite to a runbook that is read, not executed.

## Verification

```bash
# Version bump:
grep -E "^> \*\*Version:" docs/runbooks/10907-runbook-amo-publish.md
# Expected: > **Version:** 2.0.0

# Section structure is flat §1–§17:
grep -n "^# \|^## [0-9]" docs/runbooks/10907-runbook-amo-publish.md

# Anti-patterns from the audit are gone from operational text
# (matches in the change-log block are historical record-keeping):
grep -F "Split by responsibility" docs/runbooks/10907-runbook-amo-publish.md
grep -F "Maintainer note" docs/runbooks/10907-runbook-amo-publish.md
# Expected for both: empty

# Listing paste-blocks preserved byte-for-byte in their new §11 home:
grep -F "We do not enumerate, retain, transmit, or analyze data from tabs" \
  docs/runbooks/10907-runbook-amo-publish.md
# Expected: one match (the §11d Description block)

grep -F "https://aletheia.study/privacy.html" \
  docs/runbooks/10907-runbook-amo-publish.md
# Expected: at least two matches (§11i + §5 diff table + §16 related docs)
```

All confirmed locally during write.

## Operator end-to-end test plan

After merge, the operator can re-run the test that drove this restructure:

1. Open the runbook from the start.
2. Try to follow §1–§10 top-to-bottom for the AMO 1.1.2 update they have ready.
3. At each step, the URL, click, what-to-look-for, and what-to-do-if-it-fails should be on the page. No "see also" pointers to other sections except for the listing paste-blocks at §11.
4. The §5 diff step should produce a concrete list of fields to overwrite (or "no drift, skip §7"). §7 should name the exact dashboard surface for each field.

If the operator hits another structural gap during the actual upload, file a follow-up issue. This PR addresses every gap identified in the 2026-05-30 audit; future audits may surface more.

## What this report does NOT claim

- Does not assert the runbook is "complete" — runbooks accumulate gaps over time as AMO's dashboard surfaces evolve.
- Does not assert §11 paste-block content is correct. That was validated by the prior audit corrections (#663 / #670–#672 / #673); this PR moves the blocks, doesn't rewrite their text.
- Does not change Chrome runbook 10905. It has its own structure and decisions.

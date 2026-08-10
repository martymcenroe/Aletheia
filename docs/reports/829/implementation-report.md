# Implementation Report — Issue #829

## What actually blocked the dependabot gate

Not the dependency bumps. `tests/compliance/test_index_consistency.py::test_audit_index_complete`
failed on **main**, and it would have failed for any PR riding the same suite.

Measured, not inferred:

| Ref | Result |
|---|---|
| `main` @ `cb07b43` | `1 failed, 927 passed, 3 skipped, 4 deselected` — exit 1 |
| PR #805 @ `8f0bda5` | `1 failed, 927 passed, 3 skipped, 4 deselected` — exit 1 |

Identical dispositions, same single failure. A types-only stub bump
(`types-requests`) introduces nothing at runtime, which is exactly what the
numbers show.

## Root cause

The test discovered audit files with a **shell glob** and matched index entries
with a **regex**, and the two disagreed about what an audit file is:

```python
AUDITS_DIR.glob("108*-audit-*.md")       # discovery  — permissive
r"108\d{2}-audit-[^)]+\.md"              # extraction — strict
```

The glob's `*` spans any characters, so it matched files whose `-audit-` sits
mid-name:

- `10833-wiki-audit-and-refresh-plan.md`
- `10834-wiki-audit-report-2026-06.md`

The regex requires `-audit-` immediately after the two-digit serial, so it can
never match those names inside the index.

The consequence is a test that **cannot be satisfied by editing the index**: it
demands entries for two files and would then refuse to recognise them. The
failure message says *"Add these to docs/audits/10800-audit-index.md section
10.1"* — following that instruction would not have fixed it. Any attempt to
clear this by adding index rows would have failed and looked inexplicable.

## Why those two files should not be indexed anyway

`10833` states its own status:

> **Supersedes:** Nothing. Complements `docs/audits/10817-audit-wiki-alignment.md`
> (the recurring checklist). This document is the project-specific, **one-time**
> refresh plan that 10817 cannot generate from first principles.

`10834` is that plan's output — a report of a single June 2026 run.

The index's stated purpose, per the test's own docstring, is *"audits that
won't be scheduled or run"*. A one-time plan and a historical report are
neither. The recurring wiki audit, `10817-audit-wiki-alignment.md`, is already
indexed. So the glob was not merely inconsistent — it was wrong about the
domain.

## Change

One pattern per document type, used by **both** discovery and extraction, so
they cannot drift:

```python
ADR_PATTERN      = r"102\d{2}-ADR-[^)]+\.md"
AUDIT_PATTERN    = r"108\d{2}-audit-[^)]+\.md"
SKILL_PATTERN    = r"106\d{2}-skill-[^)]+\.md"
TEMPLATE_PATTERN = r"101\d{2}-TEMPLATE-[^`]+\.md"
```

plus `discover_documents()`, which is regex-based rather than glob-based
precisely so it can share those patterns.

All four index tests (ADR, audit, template, skill) carried the same
glob/regex divergence. Only audits had a filename that exercised it; the other
three were latent. All four are fixed, not just the one that was failing.

No documentation was edited. No file was renamed. No assertion was weakened.

## Deliberately not done

- **Adding the two files to the index** — impossible, as shown above, and
  wrong on the merits.
- **Renaming them to `108NN-audit-*.md`** — they are referenced by issues #739,
  #741 and #743 and cross-linked from each other; renaming breaks those links
  to make two non-audits look like audits.
- **Touching #809** — the `cryptography` 48→50 bump fails on a fleet-wide
  install/wheel problem tracked in AssemblyZero#2153. Nothing local affects it.
- **Merging or approving any dependabot PR** — per the work order, the 6 AM
  fleet pipeline does that once the blocker falls.

## Blast radius

Test-only; no production code path, no deploy.

The real risk is the tightened pattern silently under-discovering, which would
stop enforcing the audit index without failing anything. That is guarded by an
explicit lower-bound test (see the test report).

## Rollback

`git revert <sha>`. No deploy dependency.

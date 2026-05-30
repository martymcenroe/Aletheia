# Implementation Report — Issue #721

## Scope

Drop the `§0` section number from `docs/runbooks/10907-runbook-amo-publish.md`. The agent-invocation-phrases table at that position is reference material — what the operator types to trigger agent actions — not a procedure step. A `§N` heading reads as "step N, do this first" when the operator opens the runbook top-to-bottom; numbering a reference block invites that misread.

## Changes

Five text edits, all in `docs/runbooks/10907-runbook-amo-publish.md`:

| Location | Before | After |
|---|---|---|
| Header | `Version: 1.0.9` / last-updated | `Version: 1.0.10` / last-updated |
| Aletheia AMO deployment state lead-in | `Agent commands below (§0) reference these.` | `Agent commands (see *Agent invocation phrases* below) reference these.` |
| "Throughout this runbook" Agent definition | `Invoked by the canonical phrases in §0.` | `Invoked by the canonical phrases listed below.` |
| "How to verify" step 2 | `Say \`Run amo prep\` or \`Audit 10907\` (§0) — ...` | `Say \`Run amo prep\` or \`Audit 10907\` — ...` (parenthetical dropped; phrases speak for themselves) |
| Former §0 heading | `## 0. Invoke the agent (canonical phrases)` | `## Agent invocation phrases (reference)` (no section number) |
| §20 Change log | — | new v1.0.10 entry |

## Numbering policy after this PR

Sections numbered `§N` in this runbook are procedure steps the operator does in sequence. Reference material is unnumbered. The runbook's numbered sequence is now `§1` (Where to start — navigation guide) through `§20` (Change log); the agent-invocation-phrases table sits between the front matter and `§1` as an unnumbered reference block.

The remaining unnumbered front matter (deployment state, "Throughout this runbook" definitions, "How to verify you have the latest copy") was already unnumbered; the agent-invocation-phrases block joins them in shape.

## Not changed

- `§1 Where to start` numbering — operator's end-to-end test explicitly went there and read it as navigation, not action. Out of scope.
- All change-log references to historical `§0` — honest record-keeping that this PR does not rewrite. The new v1.0.10 entry itself mentions `§0` for the same reason.
- Content of any agent-invocation phrase, any procedure step, any paste-block. Pure rename + cross-reference rewording.

## Verification

```bash
grep -nE "§0|^## 0\." docs/runbooks/10907-runbook-amo-publish.md \
  | grep -v "^4[4-5][0-9]:"
# Expected: empty (all remaining §0 references are in the change-log block, lines 440s-450s)
```

Confirmed locally: zero `§0` references outside the change log.

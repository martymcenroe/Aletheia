# Implementation Report — Issue #719

## Scope

Drop "pre-flight" framing from `docs/runbooks/10907-runbook-amo-publish.md`. Operator feedback: a runbook is a checklist; the aviation metaphor sets the wrong cognitive expectation. §3 reads as "quick visual check" when it's actually 13 substantive items including a 14-second pytest run and a 1.7-minute playwright run.

## Changes

Four text-edits in the runbook plus a change-log entry:

| Location | Before | After |
|---|---|---|
| Header | `Version: 1.0.8` / last-updated | `Version: 1.0.9` / last-updated |
| §3 heading | `## 3. Pre-flight checklist` | `## 3. Verification (before §4 build)` |
| §0 phrases table | `Run §3a pre-flight + §4 build … \| Run amo pre-flight` | `Run §3a verification + §4 build … \| Run amo prep` |
| §0 phrases table | `Run §4 build + verify (pre-flight already passed)` | `Run §4 build + verify (§3 already passed)` |
| "How to verify" line | `Run amo pre-flight` | `Run amo prep` |
| §20 Change log | — | New v1.0.9 entry |

## Content stays the same

All 13 §3 items are unchanged. Every paste-block, build command, upload procedure, post-publish step, troubleshooting row stays exactly as worded. This PR renames; it does not edit any operational instruction.

## Verification

```bash
grep -i "pre-flight\|preflight" docs/runbooks/10907-runbook-amo-publish.md \
  | grep -v "^| 1\."
# Expected: empty (the only remaining 'pre-flight' string is in the v1.0.9 change-log entry recording the rename)
```

Confirmed locally: zero matches outside the change log.

## Out of scope

- Chrome runbook 10905 still uses `Run cws pre-flight`. That's a separate runbook with its own choices; not bundled here.
- AZ#1362 runbook standard (header reference) — if/when shipped, may have opinions on phase naming. Not waiting for it; this is a local fix to local friction.

# Implementation Report — Issue #717

## Scope

Remove three references to `docs/10920-cws-listing-corrections-2026-05-27.md` from `docs/runbooks/10907-runbook-amo-publish.md`. The references carried no information the runbook lacked — they were "see also" pointers at scan-overhead cost to the operator. Pure cleanup.

## Changes

### `docs/runbooks/10907-runbook-amo-publish.md`

| Section | Before | After |
|---|---|---|
| Header | `Version: 1.0.7` | `Version: 1.0.8` |
| §3b.4 | "...verify AMO too per `docs/10920`" | "...verify in private browsing and overwrite §7d Description if so" (operator-relevant claim now inline) |
| §10a | "...not the stale URL (per `docs/10920-cws-listing-corrections-2026-05-27.md`)" | "...not the stale URL" |
| §18 Troubleshooting | "Overwrite §7d Description; verify in private browsing (per `docs/10920`)" | "Overwrite §7d Description; verify in private browsing" |
| §20 Change log | — | New v1.0.8 entry |

Where 10920 contributed an operator-relevant claim (§3b.4's "live listing may still carry pre-audit wording" caveat), that claim is now inline in the runbook rather than behind a reference. Where 10920 was decorative (§10a, §18), the parenthetical is simply gone.

### Remaining `10920` strings

Two references remain in the change log itself (lines 446, 454 after edit) — the new v1.0.8 entry recording what was removed, and the v1.0.0 origin note recording where the runbook was lifted from. Both are historical record-keeping, not operational pointers. An operator reading the publishing procedure no longer encounters `10920` anywhere in §0–§19.

## Not changed

- `docs/10920-cws-listing-corrections-2026-05-27.md` itself. Out of scope. Lifecycle is operator-owned.
- Anything in `docs/runbooks/10905-runbook-cws-publish.md`. This is the AMO runbook only.
- All paste-blocks, canonical phrases, build commands, upload procedures, post-publish flow, version-bump procedure, web-ext API path, related documents — unchanged.

## Verification

```bash
grep "10920" docs/runbooks/10907-runbook-amo-publish.md | grep -v "^| 1\." | wc -l
# Expected: 0 (no 10920 references outside the change-log entries)
```

Confirmed locally: 0 non-change-log references after edit.

# Issue #691 — Test Report

## What changed

Docs-only edits to two markdown files: `docs/runbooks/10907-runbook-amo-publish.md` and `docs/runbooks/10905-runbook-cws-publish.md`. No code, no configuration, no build artifacts touched.

## Test plan

| Check | Result |
|---|---|
| Automated test suites (`poetry run pytest`, `npx playwright test`) | Not applicable — no Python or JavaScript was modified. No code paths changed. |
| Lint (`npm run lint`, `web-ext lint`) | Not applicable — no JavaScript or extension manifest was modified. |
| Markdown rendering | Both files render correctly under GitHub Flavored Markdown; numbered lists in §3a maintain sequential numbering after the deletion + renumber. |
| Cross-reference integrity | `grep -n '§3a\.[0-9]\+' docs/runbooks/10907-runbook-amo-publish.md docs/runbooks/10905-runbook-cws-publish.md` — every surviving §3a.N reference still resolves to a valid §3a item in its file. |
| No banned-rule survivors | `grep -in 'no live debug-tier console' docs/runbooks/` — no matches in the body text of either runbook. (The phrase still appears inside the change-log entries that record the deletion; that is correct and expected.) |
| Existing main-branch test failure | The pre-existing failure in `tests/integration/test_user_data_deletion.py` is tracked at issue #680 and is unrelated to this PR. It will cause `mergeable_state` to read `unstable` rather than `clean` on this PR; squash-merge still works and Cerberus still auto-approves under `unstable`. |

## Verification on merge

After merge to `main`:

```
grep -n 'no live debug-tier console' docs/runbooks/*.md
```

Expected output: matches **only** inside the change-log rows of `10905-runbook-cws-publish.md` and `10907-runbook-amo-publish.md` that record this deletion. Zero matches in the body text of either runbook.

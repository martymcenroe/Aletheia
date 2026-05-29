# Test Report — #686, #687

**Issues:** [#686](https://github.com/martymcenroe/Aletheia/issues/686), [#687](https://github.com/martymcenroe/Aletheia/issues/687)
**Date:** 2026-05-29 Central
**Type:** Documentation — no application code changed.

## Verification performed

| Check | Method | Result |
|---|---|---|
| Secret flags removed from §17c command | `sed` print of the `web-ext sign` block | ✅ command is `--channel listed --source-dir extensions/firefox --artifacts-dir dist` only |
| §17b/§17c now consistent | inspect | ✅ note states the secret is read from env, never passed on the command line |
| §15a refreshes the version pin | `grep` for the new step 5 | ✅ "Update this runbook's deployment-state Current published version…" present |
| Update trigger covers publishes | inspect line after deployment-state table | ✅ "and on each publish (§15a)" |
| §1 Path B / §3a.1 dereference the pin | inspect | ✅ both now say "see the deployment-state block" |
| §10b ellipsis rows removed | `grep '\.\.\.\]'` | ✅ none remain; single `required` array shown |
| Version bumped | `grep "Version:** 1.0.3"` | ✅ |
| Timestamps | produced with plain `date` | ✅ 2026-05-29 12:41:37 AM Central |

## Conclusion

All `Audit 10907` findings (two substantive + three cosmetic) are applied. The runbook is internally consistent and the secret-handling contradiction is resolved. No automated regression surface.

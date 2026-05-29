# Test Report — #681, #682

**Issues:** [#681](https://github.com/martymcenroe/Aletheia/issues/681), [#682](https://github.com/martymcenroe/Aletheia/issues/682)
**Date:** 2026-05-29 Central
**Type:** Documentation — no application code changed; automated suites not applicable.

## Verification performed

| Check | Method | Result |
|---|---|---|
| No `rm -f` command remains | `grep -n "rm -f"` over both runbooks | ✅ only the changelog text describing the change + the safe named-delete example `rm dist/…-v1.1.1.zip` |
| Safe deletion pattern present | inspect §4a (both) | ✅ `ls -1` list → inspect → delete by name → STOP-if-unexpected |
| AMO version corrected | `grep "1.1.1\|1.1.2"` in 10907 | ✅ deployment-state, §1 Path B, §3a.1 all state 1.1.1 live / 1.1.2 pending |
| AMO live version is actually 1.1.1 | AMO public API `addons.mozilla.org/api/v5/addons/addon/aletheia-ai/` | ✅ `current_version` = 1.1.1, updated 2026-03-06 |
| CWS version unchanged (correct) | operator confirmed CWS = 1.1.2 (updated 2026-05-25) | ✅ 10905 keeps 1.1.2, date refined |
| Version headers bumped | `grep "Version:** 1.0."` | ✅ both at 1.0.1 |
| Changelog entries added | inspect §20 (both) | ✅ 1.0.1 rows with Closes #681 / #682 |

## Conclusion

Both defects corrected; runbooks are internally consistent and factually aligned with the live stores. No automated regression surface.

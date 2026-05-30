# Implementation Report — Issue #726

## Scope

Major restructure of `docs/runbooks/10907-runbook-amo-publish.md` per the operator's end-to-end test audit. The prior runbook was a checklist wrapped in maintainer commentary, redundant steps, and nebulous directions. This version is a flat numbered procedure with explicit URLs, clicks, what-to-look-for, and what-to-do-if-it-fails on every step.

Major version bump: **1.0.10 → 2.0.0** because section numbers move. Listing field content (the paste-blocks) is unchanged in text; only its position and numbering shifted.

## Structural changes

**Old structure (1.0.x):**

- Front matter with 4 lines of maintainer references (Tracking issue, Versioning, Standard, Chrome cross-reference)
- Deployment-state table with a lead-in and post-commentary
- "Throughout this runbook" definitions
- "How to verify you have the latest copy"
- Agent invocation phrases (reference)
- §1 Reading paths (Path A/B/C table)
- §2 Account check
- §3 Verification (split into §3a agent, §3b operator with 5 items each)
- §4 Build (split into §4a build, §4b verify)
- §5 First submission upload (historical, but wedged mid-procedure)
- §6 Subsequent update upload
- §7–§13 listing fields
- §14 Submit
- §15 Post-publish (split into §15a agent, §15b operator, §15c smoke-test-fail)
- §16 Version bump
- §17 Web-ext API path
- §18 Troubleshooting
- §19 Related docs
- §20 Change log

**New structure (2.0.0):**

- Front matter: 3 lines (Version, Last updated, Applies to)
- Aletheia AMO deployment state (table only, no commentary)
- Agent invocation phrases (reference)
- **§1–§10 numbered procedure** (flat, for the update path):
  1. Sign in to AMO Developer Hub
  2. Confirm the new version is not already uploaded
  3. Agent: verify build prerequisites
  4. Agent: build and verify the ZIP
  5. Diff the live listing against §11 listing content
  6. Upload the new ZIP
  7. Overwrite drifted listing fields (only if §5 found drift)
  8. Submit for review
  9. AMO approves — operator action
  10. Agent: post-publish
- §11 Listing field content (paste-ready) + smoke-test
- §12 First submission (Path A — historical, brief)
- §13 Version bump procedure
- §14 Web-ext API signing (optional)
- §15 Troubleshooting
- §16 Related documents
- §17 Change log

## Specific audit findings addressed

Each finding from the issue body:

| Finding | Resolution |
|---|---|
| §3b.1 redundant with §2 | §2 happens once in the new §1 (sign in). No restated "account check passes" item. |
| §1 Path B reads §13 twice | Procedure is linear §1–§10; no path table needed for the normal case. |
| §3a.5 includes `web-ext lint` (runs DURING §4 build, not before) | §3 verify covers pytest + playwright only. Lint stays in §4 build where it actually runs. |
| §3a.8 is output, not verification | Dropped. The agent reports as part of its normal output, not as a verification item. |
| §3a.7 + §8b duplicate screenshot prep | §11f makes screenshots a no-op for updates by default. No cross-references needed. |
| §3b.3 references nonexistent screenshot set on updates | Same — folded into §11f conditional. |
| §3b.4 "review for changes" is nebulous | §5 is now a per-field comparison table: which live field, compare to which §11 subsection, what to look for. |
| §3b.5 "printed-copy version matches" assumes paper | Dropped. Use `Audit 10907` if you want to verify the runbook version. |
| §2 line 74 hedge about Chrome profile | Dropped. §1 has the concrete signin procedure. |
| §3a.6 "see §18" misleading pointer (§18 doesn't explain release notes) | §3 step 6 just says the release notes file must exist. |
| §6 doesn't say how to overwrite listing fields | §7 is the new step with explicit dashboard surfaces per field. |
| §14 "the release issue" undefined | §8 says "the release tracking issue for this version" — clearer; the tracking issue is per-release per §13. |
| Front matter padding (Tracking, Versioning, Standard, Chrome) | Dropped. Title says it's the AMO runbook. |
| Deployment-state lead-in + post-commentary | Dropped. Just the table. |
| §3 line 78 "Split by responsibility..." | Dropped. The new §3 is flatly "Agent: verify build prerequisites". |
| §4 anecdote about a cleanup-agent incident | Dropped. The "don't include docs/tests/ in the ZIP" reminder is implicit in §4 step 3's "no unexpected files" check. |
| §4a "Known hardening gap" bug commentary | Dropped. Belongs in a separate issue if it's a real gap. |
| §7d Maintainer note | Dropped. |
| §7e Categories rationale history | Dropped. §11e just says `Other`. |
| §11 license rationale | Dropped. §11k says PolyForm + how to use AMO's Custom License field. |
| §12 "Why fewer than Chrome" | Dropped. §11l says "5 permissions + host". The reader doesn't need to know why Chrome is different. |
| §16 version bump 200 words for one-line action | §13 is 6 steps, tightly worded. |

## What stays the same

- Listing field content (now §11a–§11l): byte-identical to the prior runbook's §7–§13.
- Deployment-state identifiers (slug, gecko ID, URLs, account, version state).
- Agent invocation phrases (the table). Phrase descriptions updated to match new section numbers.
- Change log entries 1.0.0 through 1.0.10 (history doesn't change).

## Verification

```bash
# Anti-patterns from the audit gone (or only in change-log entries as historical record):
grep -F "Split by responsibility" docs/runbooks/10907-runbook-amo-publish.md
# Expected: empty

grep -F "Maintainer note" docs/runbooks/10907-runbook-amo-publish.md
# Expected: empty

# "Known hardening gap" and "pre-flight" appear only in historical change-log entries:
grep -nF "Known hardening gap" docs/runbooks/10907-runbook-amo-publish.md
grep -nE "pre-flight|preflight" docs/runbooks/10907-runbook-amo-publish.md
# Expected: both match only in the change-log section (lines ~400+)

# Section structure flat 1-17:
grep -n "^# \|^## [0-9]" docs/runbooks/10907-runbook-amo-publish.md
# Expected: §1 through §17 contiguous

# Version header:
grep -E "^> \*\*Version:" docs/runbooks/10907-runbook-amo-publish.md
# Expected: 2.0.0
```

Confirmed locally.

## Out of scope

- Chrome runbook 10905. Different document.
- The 200-word version-bump cross-reference in 10905 §16 — that runbook has its own restructure decisions to make if any.
- The `build_release.py` "Known hardening gap" (stale-zip auto-clean). If that's worth fixing, it's a separate issue against `tools/build_release.py`, not runbook commentary.

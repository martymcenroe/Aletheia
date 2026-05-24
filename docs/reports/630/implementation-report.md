# Implementation Report — Issue #630

**Title:** fix: revert overreach on Discworld asides — restore originals on engineering pages
**Date:** 2026-05-23
**Status:** Complete (pending review + merge)
**Branch:** `630-restore-discworld-asides`

## Summary

#628 over-scoped. The user direction (during #625 review) was to remove the Discworld reference I had introduced in `demos.html`, not to touch the pre-existing Discworld asides on the engineering documentation pages. This PR restores the original Pratchett character on the four engineering pages and leaves the legitimate Ulysses replacement in `demos.html` alone.

## Files Modified

| File | Action | Restored content |
|------|--------|------------------|
| `docs/architecture.html` | Restore | Unseen University Library + cataloguing + Ook |
| `docs/observability.html` | Restore | Clacks towers / Grand Trunk / GNU Terry Pratchett |
| `docs/operations.html` | Restore | Lord Vetinari governing Ankh-Morpork |
| `docs/safety.html` | Restore | Librarian of Unseen University zero-tolerance |

## Files NOT Modified

- `docs/demos.html` — keeps the Ulysses / Trojan Horse aside from #628. That was the one legitimate change (the Lancre quote was something I added in #625; the user asked for it to be replaced with something mainstream).
- `docs/threat-model.html` — its `discworld-aside` CSS class styles a paragraph whose content is not actually Discworld (it's an original observation about hostile-text-on-the-page). Unaffected.

## Lesson

When the user said "nobody knows Discworld," that applied specifically to the new Discworld reference I had introduced — not as an invitation to clean up every Discworld reference site-wide. The pre-existing engineering-page asides are part of the project's voice and were not part of the request. I should have asked before expanding the scope.

## Verification

- Diff against pre-#628 content for each file is byte-equivalent
- Post-merge: `https://aletheia.study/architecture.html`, `/observability.html`, `/operations.html`, `/safety.html` show their original Pratchett asides

## Related

- #625 — original demo content
- #628 — the over-scoped change being partially reverted

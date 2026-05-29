# Test Report — #678

**Issue:** [#678](https://github.com/martymcenroe/Aletheia/issues/678)
**Date:** 2026-05-28 Central
**Type:** Documentation (runbooks) — no application code changed

## Scope

Documentation-only change (Markdown runbooks + index). No `src/`, `extensions/`, or `tools/` code was modified, so the automated suites (`poetry run pytest`, `npx playwright test`) are not applicable and were not run — there is no behavior to regress. Verification is structural and factual accuracy of the runbook content.

## Verification performed

| Check | Method | Result |
|---|---|---|
| Both new runbooks created | `glob docs/runbooks/*.md` | ✅ `10905-runbook-cws-publish.md`, `10907-runbook-amo-publish.md` present |
| Old combined runbook removed | git status | ✅ `10905-runbook-extension-store-publish.md` deleted |
| No dangling references to old filename | `grep 10905-runbook-extension-store-publish` | ✅ only intentional change-log history refs in the two new files (principle 16) |
| Index cross-refs updated | inspect `10900-runbook-index.md` | ✅ 10905→CWS, new 10907→AMO row |
| Image-pad cross-ref updated | inspect `10906-runbook-cws-image-pad.md` | ✅ points at both new runbooks |
| Extension ID accurate | vs `docs/index.html` / `docs/demos.html` install links | ✅ `pfkfdlcdbajamklbneflfbkmnceooijm` |
| Permission sets accurate | vs `extensions/chrome/manifest.json` (7 perms) + `extensions/firefox/manifest.json` (5 perms) | ✅ CWS §12 has 7+host; AMO §12 has 5+host |
| `data_collection_permissions` accurate | vs Firefox manifest | ✅ authenticationInfo + websiteContent reflected in AMO §10b |
| Privacy Policy URL correct | vs `docs/10920` correction + `docs/privacy.html` og:url | ✅ `https://aletheia.study/privacy.html` |
| Long Description corrected wording | vs `docs/10920` #1 | ✅ "do not enumerate…", no "cannot see browsing history" |
| Build command accurate | vs `tools/build_release.py` | ✅ `poetry run python tools/build_release.py` produces both ZIPs |
| Short description ≤ 132 chars | manual count | ✅ 129 chars |
| AZ#1362 20-principle checklist | manual review | ✅ all 20 addressed (see implementation report) |

## Manual verification deferred to operator

The runbooks describe operator-only dashboard actions (CWS / AMO uploads, listing-field edits, 2FA login, clean-profile smoke tests). These execute against live store dashboards and cannot be agent-driven; they are exercised the next time a version is published using these runbooks.

## Conclusion

Documentation change is internally consistent, factually aligned with the manifests / build tool / audit-corrections doc, and conforms to the AZ#1362 standard. No automated regression surface.

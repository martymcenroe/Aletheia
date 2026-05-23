# Test Report — Issue #625

**Title:** feat: prompt-injection demo content + Clio-style threat-model wiki
**Date:** 2026-05-23
**Branch:** `625-demo-content-and-threat-model`

## Static validation

This change is docs-only — HTML/CSS, no JavaScript, no backend code, no test code. The validation surface is:

- **HTML structure:** each new page is a complete standalone HTML5 document with correct doctype, viewport meta, and structural elements.
- **Linkage:** nav links across all updated pages point to existing files.
- **No relative-path breakage:** demo subpages use `../demos.html` to navigate back to the index, which resolves correctly from `docs/demos/*.html`.

## Manual checks performed

| Check | Result |
|-------|--------|
| All 5 demo pages render without parser errors when opened locally | ✓ |
| Threat-model page renders without parser errors | ✓ |
| Demos index page renders without parser errors | ✓ |
| Safety page additions render in context (no broken table/list structures) | ✓ |
| Nav additions resolve to new files (threat-model.html, demos.html) | ✓ |
| Demo page footer disclaimers visible and link back to demos.html | ✓ |
| Each demo contains the expected injection-surface element identified in the implementation report | ✓ |
| No real-IP names used in primary content (parody names where direct use would create infringement risk) | ✓ |

## Linter

The project linter (`ruff`) is Python-only and does not cover HTML. No JavaScript was added; ESLint not exercised. The site uses no build step that would catch HTML issues automatically.

## Manual content validation

Each demo page was reviewed for:

1. **Injection authenticity** — does the embedded prompt-injection text use the techniques real attackers use (imperative override verbs, role-play takeover, "ignore previous instructions," "do not acknowledge," "confirm receipt by responding with X")? **Yes** for all five.
2. **Plausibility of host content** — does the surrounding content read as a genuine artifact of its genre? **Yes** for all five — each follows the genre's conventions (byline + dateline for the news article, version numbers and warning boxes for the tech spec, DOI and references for the academic paper, etc.).
3. **Visible demo banner** — is the page identified as a parody artifact at the top? **Yes** for all five.
4. **Footer disclaimer** — is the parody status restated at the bottom with IP attribution? **Yes** for all five.

## What this change does NOT test

- **End-to-end Aletheia interaction:** there is no automated test that opens a demo page in a browser, selects the injection text, and asserts the overlay response. Doing this requires a test JWT (`AUTH_ENABLED=true` blocks anon) and a headless browser harness. Out of scope for this PR; recommend tracking as separate work if recurring verification is desired.
- **CloudFlare Pages deploy:** static-site auto-deploy is presumed working from the existing site behavior. Post-merge, the new pages should appear at `https://aletheia.study/*` without manual intervention.
- **Cross-browser rendering:** demos use bespoke styling per page. Manual verification was in modern Chrome only. Edge cases (older Safari, IE11, exotic mobile browsers) untested. For demo material this is acceptable; the YouTube recording will be on Chrome anyway.

## Post-deploy smoke

After merge:

```bash
# Confirm new pages publish
for path in threat-model.html demos.html demos/daily-planet.html demos/discovery-one.html demos/seldon-journal.html demos/sparx-linkedin.html demos/nexus-wiki.html; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "https://aletheia.study/$path")
  echo "$path: $status"
done
# Expect: 200 for all
```

Then, in a browser with Aletheia installed:

1. Visit each demo page.
2. Select the highlighted injection text.
3. Right-click → "Explain with AI."
4. Verify the overlay shows `Prompt Injection Attempt` (or the Opus downgrade for any false-positive surface — though none should be false positives, since each demo intentionally contains a real injection).
5. Verify Aletheia does NOT echo the attacker's instructions in any output field.

## Regression risk

**Very low.** This change adds new files and updates navigation only. No existing-page content was modified except `safety.html` (one new section, one updated paragraph) and the standard nav block (consistent edit across all 7 existing pages). No code paths changed.

# Implementation Report — Issue #705

## Scope

Close the loop on #697 by removing the residual source-tree references to the now-deleted Edge E2E test path. #697 was auto-closed when PR #698 deleted `.github/workflows/e2e-edge.yml`, but the companion source items called for in #697's body were deferred to this issue because the workflow YAML half required GitHub web UI (PAT scope restriction) while these items go through the standard PR procedure.

## Changes

### `playwright.config.js`

Removed the `edge` project block (formerly lines 97–108):

```js
{
    // Issue #263: Edge E2E test matrix
    // Visual baselines: Edge shares Chromium rendering engine;
    // separate baselines not needed (ref #458)
    name: 'edge',
    use: {
        channel: 'msedge',
        // Extensions require headed mode
        headless: false
        // Inherits launchOptions from global use block (extension loading)
    }
},
```

With `.github/workflows/e2e-edge.yml` deleted in #698, this block was dead config — no CI procedure invoked it. The `projects` array now contains `chromium` and `firefox-overlay` only.

### `docs/lld/done/10263-edge-e2e-test-matrix.md`

Added a SUPERSEDED notice immediately under the title, citing #697 and #705, naming the FAQ that disclaims Edge support, and pointing at the two PRs that effected the removal (#698 for the YAML, this PR for the residual). The body of the LLD is preserved for historical reference. No other lines changed.

## Verified absent

- `tests/e2e/edge/` — directory does not exist; nothing to delete.
- Saved-memory entries about `test-edge` / accepted-flaky — `grep` of `C:\Users\mcwiz\.claude\projects\C--Users-mcwiz-Projects-Aletheia\memory\` returns no matches. The "accepted-flaky" framing lived only in session handoffs, not in long-term memory. No memory file edits required.

## Out of scope

- The other half of the `mergeable_state == unstable` problem (`integration-tests` failure tracked as #680) is unchanged by this PR.
- The FAQ wording stands as-is; this PR does not edit `Aletheia.wiki/FAQ.md`.
- No CI procedure files (`.github/workflows/*.yml`) are touched by this PR. The companion YAML deletion was #698.

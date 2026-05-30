# Implementation Report — Issue #695

## Scope

Resolve the local playwright Firefox `browserContext.newPage()` hang on the operator workstation that blocked runbook 10907 §3a.5 pre-flight ("All tests pass") for the Aletheia 1.1.2 AMO publish.

## Root cause (per Gemini investigation)

The Windows content sandbox was silently crashing Playwright's Firefox renderer during `newPage` initialization, producing a Juggler `remoteTab is null` IPC error. Playwright's `newPage()` promise never resolved because the renderer it was waiting on had already died on the sandbox boundary.

This matches the symptom recorded in #695:
- `firefox.launch()` succeeded in ~330 ms (parent process started fine)
- `browser.newContext()` succeeded in ~75 ms (context handle created)
- `context.newPage()` never returned (renderer died on sandbox; no signal back to Playwright)
- CI green on the same commit (CI runs Firefox in a Linux container where the Windows sandbox path is not exercised)

The handoff also confirms the local repro is now resolved with the change applied.

## Change

### `playwright.config.js`

Injected `MOZ_DISABLE_CONTENT_SANDBOX: '1'` into the `firefox-overlay` project's `launchOptions.env`. The `...process.env` spread preserves the existing environment; only the one variable is added.

```js
launchOptions: {
    args: [],
    env: {
        ...process.env,
        MOZ_DISABLE_CONTENT_SANDBOX: '1'
    }
}
```

Scope notes:
- The change is **per-project** (firefox-overlay only). Other Firefox projects in the config are unaffected.
- The change is **build-tool scope**, not production scope. The sandbox setting applies to Playwright's bundled Firefox executable launched for tests; it has no effect on the user-facing extension or on Firefox installations users have.
- The env var is read by Firefox itself (it's a Mozilla-supported runtime switch); no Playwright API was added or modified.

### `docs/runbooks/10907-runbook-amo-publish.md`

- §18 Troubleshooting: new row documenting the hang signature and pointing at the applied fix.
- Header version bumped 1.0.5 → 1.0.6.
- §20 Change log: new 1.0.6 entry.

## Files changed

| File | Change |
|---|---|
| `playwright.config.js` | +4 / −1 — `env` block added to firefox-overlay launchOptions |
| `docs/runbooks/10907-runbook-amo-publish.md` | +2 / 0 in §18 + §20, header version line updated |

No other files modified. No code changes outside the test config. No new dependencies.

## Out of scope

- Not investigated: the deeper question of why Windows content sandbox crashes Playwright's Firefox renderer specifically on this workstation. Disabling the sandbox is a workaround, not a root-cause fix. If the cause is workstation-specific (Defender, AV, driver), other workstations may not need the workaround; if it's a general Playwright + Firefox + Windows interaction, it's a fleet-level concern that would belong in a separate AssemblyZero runbook.
- Not modified: production extension code, manifest, release-notes, or any user-facing surface. `dist/aletheia-firefox-v1.1.2.zip` content is unaffected.

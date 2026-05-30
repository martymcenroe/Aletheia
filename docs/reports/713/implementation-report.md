# Implementation Report — Issue #713

## Scope

Two precision nits surfaced by today's `Audit 10907` self-audit. Both are pure operational clarity in `docs/runbooks/10907-runbook-amo-publish.md`; no semantic change to the publishing procedure.

## Changes

### `docs/runbooks/10907-runbook-amo-publish.md`

- **Header:** version bump `1.0.6` → `1.0.7`, last-updated stamp refreshed.
- **§3a.7:** *"Current state: none exist"* → *"Current state: directory does not exist; it will be created on first AMO screenshot upload."* The directory itself (`screenshots/amo/`) does not exist; the previous wording read as "directory exists, no files" which would leave an operator wondering whether `ls screenshots/amo/` returning "no such file or directory" was a problem.
- **§7c:** *"(129 chars)"* → *"(129 characters / 131 bytes UTF-8 — the em-dash is 3 bytes)."* AMO's 250-char limit is by visible character, which is what 129 measures. A naive reproducibility check with `wc -c` returns 131 because the em-dash in the copy is 3 UTF-8 bytes — operator should not have to think about why.
- **§20 Change log:** new v1.0.7 entry, one line, describing the two text changes.

## What this does NOT change

- §3a.5 — gate text. Both sub-conditions (`poetry run pytest` and `npx playwright test`) are now genuinely satisfiable on `main` HEAD as of today (after #680/#712 and #695/#696), but the gate's *text* always made the right ask. Per operator preference, the runbook is for getting through the work — adding a "no-text-change archival" change-log entry to record when the underlying state became aligned would be cognitive overhead for the reader at scan time without operational payoff. Deliberately omitted.
- Deployment-state block — `Current published version: 1.1.1` is still accurate; 1.1.2 is still the pending upload.
- All paste-blocks (§7–§13) — unchanged.
- All canonical phrases (§0), reading paths (§1), build commands (§4), upload procedures (§5/§6), post-publish flow (§15), version-bump procedure (§16), web-ext API path (§17), troubleshooting (§18), and related documents (§19) — unchanged.

## Out of scope

- §3a.7's "create the directory on first upload" wording is precise but does not document HOW to create it. The runbook elsewhere implies `mkdir -p screenshots/amo/` would be the operator's step; this PR doesn't add that detail because the runbook is not a screenshot-creation guide ([10906](../runbooks/10906-runbook-cws-image-pad.md) is).
- §7c could grow into a generic "Unicode + byte counts" note, but every paste-block having a byte-count footnote is operator-hostile. The em-dash in §7c is the only multi-byte character in any paste-block; surfacing it once at the location of confusion is sufficient.

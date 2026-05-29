# Implementation Report — #684

**Issue:** [#684](https://github.com/martymcenroe/Aletheia/issues/684) — runbook timestamps were UTC mislabeled as Central
**Date:** 2026-05-29 Central
**Type:** Documentation (timestamp correction)

## Root cause

The runbook timestamps were generated with `TZ='America/Chicago' date`. Git Bash has no IANA timezone database, so it ignores the named zone and returns **UTC**, which was then labeled "Central" — off by 5 hours (CDT, UTC-5) and a calendar day after ~7 PM Central. The correct command is plain `date` (the system clock is already Central); it was used to produce the v1.0.2 timestamps in this change.

## Changes (both `10905-runbook-cws-publish.md` and `10907-runbook-amo-publish.md`)

| Field | Was (UTC-as-Central) | Now (true Central) |
|---|---|---|
| v1.0.0 changelog date | 2026-05-28 11:49:42 PM | 2026-05-28 06:49:42 PM |
| v1.0.1 changelog date | 2026-05-29 01:05:10 AM | 2026-05-28 08:05:10 PM |
| Header "Last updated" | 2026-05-29 01:05:10 AM | 2026-05-29 12:18:55 AM (v1.0.2 stamp) |
| Version | 1.0.1 | 1.0.2 |

Added a v1.0.2 changelog row to each runbook documenting the correction and the cause.

## Out of repo (also done this session)

- Root CLAUDE.md (`C:\Users\mcwiz\Projects\CLAUDE.md`): the "Surface timestamps in US Central" rule now states to use plain `date`, never the `TZ=` prefix, never PowerShell.
- Agent memory `reference-central-time-on-windows`: corrected to recommend plain `date`.

## Verification

See test-report.md. `grep` confirms no `01:05:10 AM` / `11:49:42 PM` remain; corrected values present; both runbooks at v1.0.2.

# Implementation Report — Issue #404: Post-Deploy Smoke Test

## Summary

Added `post-deploy-smoke` job to `.github/workflows/ci.yml` that runs after `deploy-infra` on pushes to main. The job performs two HTTP checks against the production API:

1. **Health check** — `GET /health` must return 200
2. **AUTH_ENABLED guard** — `POST /` must not return 401 (catches premature auth enablement)

## Design Decisions

- **Pure curl, no checkout** — the job needs no code, just HTTP access to the production API
- **Only fails on 401** — 429 (rate limit) and 403 (blocked term) are acceptable; they indicate the API is functioning correctly
- **Runs only on main push** — mirrors `deploy-infra` condition since it's verifying that deployment

## Files Changed

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | Added `post-deploy-smoke` job between `deploy-infra` and `compliance-audit` |

## Risk Assessment

- **Blast radius:** CI only — no production changes
- **Rollback:** Revert the commit

# Implementation Report: Issue #157 - ESLint Flat Config Migration

**Issue:** #157
**LLD:** docs/1157-eslint-flat-config.md
**Status:** Complete
**Date:** 2026-01-05
**Agent:** Claude Opus 4.5

## Summary

Migrated ESLint configuration from legacy `.eslintrc.json` format to ESLint v9 flat config format (`eslint.config.mjs`). Removed the band-aid `ESLINT_USE_FLAT_CONFIG=false` environment variable from CI.

## Changes Made

### New Files
| File | Purpose |
|------|---------|
| `eslint.config.mjs` | ESLint flat config for browser extensions (ESM format) |

### Modified Files
| File | Change |
|------|--------|
| `package.json` | Added `@eslint/js` and `globals` devDependencies |
| `package-lock.json` | Updated dependency tree |
| `.github/workflows/ci.yml` | Removed `ESLINT_USE_FLAT_CONFIG: false` and `--ext .js` flags |
| `docs/0003-file-inventory.md` | Added `eslint.config.mjs` entry |
| `docs/1157-eslint-flat-config.md` | Updated status to Complete, resolved open questions |

### Removed Files
| File | Reason |
|------|--------|
| `.eslintrc.json` | Replaced by `eslint.config.mjs` |

## Technical Decisions

### ESM vs CommonJS
Used `.mjs` extension for ESM syntax. This works with `"type": "commonjs"` in package.json because the `.mjs` extension explicitly signals ESM regardless of package type.

### globals.webextensions
Verified that the `globals` npm package (v17.0.0) exports `webextensions` containing `browser`, `chrome`, and `opr`. Used spread operator with explicit `chrome: "readonly"` fallback for future-proofing.

### File Targeting
Changed from `--ext .js` CLI flag to `files: ["extensions/**/*.js"]` in config. This is the flat config way of specifying which files to lint.

## Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| `@eslint/js` | ^9.39.2 | Provides `js.configs.recommended` |
| `globals` | ^17.0.0 | Provides browser and webextension globals |

## Verification

- Linted Chrome extension: PASS (no errors)
- Linted Firefox extension: PASS (no errors)
- Compared output with legacy config: Identical (only deprecation warnings removed)

## Risks Addressed

| Risk from LLD | Mitigation | Result |
|---------------|------------|--------|
| Plugin incompatibility | No third-party plugins used | N/A |
| Rule behavior changes | Compared lint outputs | Identical |
| CI breaks | Tested locally before removing band-aid | PASS |

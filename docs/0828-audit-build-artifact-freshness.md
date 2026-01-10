# 0828 - Audit: Build Artifact Freshness

## 1. Purpose

Verify that extension build artifacts in `dist/` are not stale before store submission. Stale artifacts risk deploying outdated code that diverges from the source tree.

**Key Principle:** Never submit an artifact to Chrome Web Store or Firefox Add-ons without verifying it was built from the current source.

---

## 2. Trigger Conditions

| Trigger | Context |
|---------|---------|
| **Pre-Store Submission** | MUST run before uploading to any store |
| **Post-Extension Change** | After any change to `extensions/chrome/` or `extensions/firefox/` |
| **Quarterly** | Part of release readiness check |

---

## 3. Procedure

### Phase 1: Automated Check

```bash
# Run the freshness check script
poetry run python tools/check_artifact_freshness.py

# Expected output for fresh artifacts:
# Chrome: [FRESH]
# Firefox: [FRESH]
```

**Exit Codes:**
| Code | Meaning | Action |
|------|---------|--------|
| 0 | All artifacts fresh | Safe to submit |
| 1 | One or more stale | Rebuild required |
| 2 | Artifact missing | Build required |
| 3 | Config error | Fix paths |

**Stop Condition:** If ANY artifact is STALE or MISSING, run `build_release.py` before proceeding.

### Phase 2: Rebuild (if needed)

```bash
poetry run python tools/build_release.py
```

Verify:
- All 7 steps complete successfully
- Both Chrome and Firefox artifacts created
- No lint errors

### Phase 3: Re-verify

```bash
poetry run python tools/check_artifact_freshness.py
# Must report [FRESH] for all browsers
```

### Phase 4: Pre-Submission Checklist

Before uploading to stores:

| Check | Command/Action | Expected |
|-------|----------------|----------|
| Freshness | `check_artifact_freshness.py` | All FRESH |
| Version match | Compare manifest versions | Chrome = Firefox |
| Local test | Load unpacked in browser | Extension works |
| Lint passes | `npx web-ext lint` | No errors |

---

## 4. Decision Tree

```
Run check_artifact_freshness.py
           │
    ┌──────┴──────┐
    │             │
 FRESH         STALE/MISSING
    │             │
    ▼             ▼
 Safe to      Run build_release.py
 submit       then re-run check
              until FRESH
```

---

## 5. Relationship to Other Audits

| Audit | Relationship |
|-------|--------------|
| 0809 Security | Run security audit BEFORE building final artifacts |
| 0826 Cross-Browser | Run AFTER freshness check passes |
| 0813 Code Quality | CI validates code before artifact is considered safe |

---

## 6. Audit Record

| Date | Auditor | Browser | Result | Notes |
|------|---------|---------|--------|-------|
| 2026-01-10 | Claude Opus 4.5 | Both | FRESH | Initial audit after #277 fix |

---

## 7. References

- `tools/check_artifact_freshness.py` - Automated freshness check
- `tools/build_release.py` - Build script for release artifacts
- Issue #280 - Feature implementation

---

## 8. History

| Date | Change |
|------|--------|
| 2026-01-10 | Created. Artifact freshness verification for store submissions. |

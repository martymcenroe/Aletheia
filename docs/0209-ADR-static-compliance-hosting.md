# 0209 - ADR: Static Compliance Hosting

**Status:** Implemented
**Date:** 2025-12-29
**Categories:** Compliance, Cost Optimization, Infrastructure

## 1. Context
The Chrome Web Store requires a publicly accessible "Privacy Policy" URL.
* **Constraint:** We want zero recurring costs for static assets.
* **Constraint:** We want the policy versioned with the code.

## 2. Decision
**We will host compliance documents via GitHub Pages on the `gh-pages` branch of the main repository.**

## 3. Alternatives Considered

### Option A: GitHub Pages — SELECTED
**Pros:**
- **Free:** Included with repo.
- **Versioning:** Policy changes are git commits.
- **Simplicity:** Just an `index.html` file.

**Cons:**
- Requires separate branch management (`gh-pages`).

### Option B: External CMS (Wordpress/Wix)
**Pros:**
- WYSIWYG editing.

**Cons:**
- Cost ($10-20/mo).
- Disconnected from codebase.

## 4. Rationale
Compliance documents should be treated as code (versioned, reviewed). GitHub Pages is the leanest solution.

## 5. Security Risk Analysis
Low risk. Public static content only.

## 6. Consequences
- **Positive:** Free, versioned privacy policy.
- **Negative:** Must manually sync `gh-pages` branch updates.

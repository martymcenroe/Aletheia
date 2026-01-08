# 0212 - Unified Manifest V3 and Secure DOM Standards

## Status
Accepted

## Context
During the expansion to Firefox (Issue #193), we faced a choice between maintaining a legacy Manifest V2 version (for broader compatibility) or enforcing Manifest V3 (for codebase unity).

Additionally, Mozilla's linter flagged our use of `innerHTML` for UI construction as a security risk (Issue #194). While `innerHTML` is convenient for templating, it introduces Cross-Site Scripting (XSS) vectors and blocks automated store validation.

## Decision

### 1. Unified Manifest V3
We will target **Manifest V3 exclusively** for all supported browsers (Chrome, Firefox, Edge, Safari).
* We will **not** maintain a Manifest V2 branch.
* We will use polyfills or distinct manifest files (e.g., `manifest.firefox.json`) to handle browser differences, but the target API version must always be V3.
* **Rationale:** This allows a single shared codebase (`service-worker.js`, `overlay.js`) without complex build-time transpilation or conditional logic for legacy APIs.

### 2. Strict Prohibition of innerHTML
We strictly prohibit the use of `.innerHTML` (and jQuery equivalents) for both dynamic content and static UI construction.
* **Required Pattern:** Use `document.createElement()`, `setAttribute()`, and `.appendChild()` (or a typesafe helper function).
* **Text Safety:** Use `.textContent` for all dynamic text injection.
* **Rationale:** This ensures "Secure by Design" UI that passes strict Linters (Mozilla/Chrome) and eliminates a massive class of XSS vulnerabilities.

## Consequences

### Positive
* **Development Velocity:** No context switching between V2/V3 APIs.
* **Security:** XSS via injection is structurally impossible in the overlay.
* **Compliance:** "Green Checkmark" validation from Mozilla and Chrome Web Store is automatic.

### Negative
* **Verbosity:** DOM construction code is ~30% longer than HTML template strings.
* **Browser Support:** We drop support for pre-2023 Firefox versions (pre-v109).

## Compliance
* **Automated:** `grep` checks in CI pipeline reject `innerHTML`.
* **Manual:** Code reviews must reject V2 manifest submissions.

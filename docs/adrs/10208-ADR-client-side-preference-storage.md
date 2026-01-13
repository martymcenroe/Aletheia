# 0208 - ADR: Client-Side Preference Storage

**Status:** Implemented
**Date:** 2025-12-29
**Categories:** Privacy, UX, Data

## 1. Context
Users need to store preferences (like the Allowlist) that persist across browser sessions.
* **Constraint:** We are "Privacy-First" and avoid backend user accounts.
* **Problem:** Standard cookies are easily cleared. `localStorage` is vulnerable to XSS from the host page.

## 2. Decision
**We will use `chrome.storage.local` for all user preference persistence.**

## 3. Alternatives Considered

### Option A: chrome.storage.local — SELECTED
**Pros:**
- **Extension-Owned:** Not accessible by host page JS (secure from site XSS).
- **Persistent:** Survives "Clear Browsing Data" unless "Hosted app data" is checked.
- **Sync Capable:** Can switch to `chrome.storage.sync` later for cross-device support.

**Cons:**
- Asynchronous API (callback/promise based) adds code complexity.

### Option B: localStorage
**Pros:**
- Synchronous, easy API.

**Cons:**
- Cleared easily.
- Vulnerable to host page scripts.

## 4. Rationale
`chrome.storage` provides the best balance of persistence, security, and privacy without requiring a remote database.

## 5. Security Risk Analysis
| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| Local data extraction by malware | High | Low | Med | Risk inherent to local execution; OS-level security required. |

## 6. Consequences
- **Positive:** robust persistence, privacy compliance.
- **Negative:** Async/await pattern required for all reads/writes.

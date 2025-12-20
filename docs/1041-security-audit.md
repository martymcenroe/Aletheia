# 1041 - Feature: Permission Culling & Security Hardening

## Context
Linked to Issue #41.
To pass Google Chrome Web Store review by Jan 15, we must adhere to the "Principle of Least Privilege."

## Requirements
1.  **Manifest Audit:** Remove '<all_urls>' and 'activeTab' if not strictly required.
2.  **Justification:** Write clear justification strings for any permission retained.
3.  **Goal:** Eliminate any permission that triggers an automatic "Manual Review" flag to ensure we beat the holiday freeze.

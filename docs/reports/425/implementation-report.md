# Implementation Report — Issue #425

**Feature:** Stripe SDK upgrade 7.14.0 → 14.3.0
**Branch:** `425-stripe-14-migration`
**Date:** 2026-02-24

## Summary

Upgraded the Stripe Python SDK from v7.14.0 to v14.3.0 (7 major versions). The legacy module-level API (`stripe.api_key`, `stripe.checkout.Session.create()`) remains supported in v14, so no code changes were required. The upgrade brings bug fixes, new API features, and Python 3.14 support.

## Files Changed

| File | Change |
|------|--------|
| `pyproject.toml` | `stripe = ">=7.0.0,<8.0.0"` → `">=14.0.0,<15.0.0"` |
| `poetry.lock` | Regenerated for stripe 14.3.0 |

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking API changes (v8 removed `stripe.api_key` global) | Verified: legacy API still works in v14 (deprecated, not removed) |
| Exception class changes | Verified: `stripe.StripeError` and `stripe.SignatureVerificationError` still exist at same paths |
| Module restructuring | Verified: `stripe.checkout.Session.create()` and `stripe.Webhook.construct_event()` still work |

## Future Work

The legacy `stripe.api_key` pattern is deprecated. A future issue should migrate to `stripe.StripeClient(api_key)` before a future major version removes it. This is low priority — the current code works correctly.

## Supersedes

Dependabot PR #425 (auto-generated, no code migration).

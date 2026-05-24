# Test Report — Issue #630

**Title:** fix: revert overreach on Discworld asides
**Date:** 2026-05-23

## Validation

Four single-paragraph content reverts. No structural change, no CSS change, no code change.

| Check | Result |
|-------|--------|
| `docs/architecture.html` aside restored to UU Library / Ook | ✓ |
| `docs/observability.html` aside restored to Clacks towers / GNU Terry Pratchett | ✓ |
| `docs/operations.html` aside restored to Lord Vetinari / Ankh-Morpork | ✓ |
| `docs/safety.html` aside restored to Librarian of UU | ✓ |
| `docs/demos.html` Ulysses aside untouched | ✓ |
| `docs/threat-model.html` original-observation aside untouched | ✓ |

## Post-deploy smoke

```bash
curl -s https://aletheia.study/architecture.html | grep -ic "unseen university\|librarian"
curl -s https://aletheia.study/observability.html | grep -ic "clacks\|gnu terry pratchett"
curl -s https://aletheia.study/operations.html | grep -ic "vetinari\|ankh-morpork"
curl -s https://aletheia.study/safety.html | grep -ic "librarian of unseen university"
```

Each should return at least 1 after CloudFlare publishes.

## Regression risk

Zero. Reverting to known-good prior content.

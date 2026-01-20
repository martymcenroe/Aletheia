# Implementation Report: Issue #45 - Deterministic Hate Speech Filter (Denylist)

## Metadata
- **Issue:** #45
- **LLD:** docs/1045-deterministic-hate-filter.md
- **Agent:** Claude Opus 4.5
- **Date:** 2025-12-31 13:02 CT
- **Status:** Ready for Review

## Summary

Implemented a deterministic hate speech filter using a HashSet denylist for O(1) token lookup. The filter runs before the LLM layer to block known terms immediately, reducing latency and cost while shifting liability to an external database (RSDB).

## Files Created

| File | Purpose |
|------|---------|
| `src/guardrails/denylist.py` | Core implementation: load_denylist, normalize_text, check_denylist |
| `src/guardrails/resources/denylist.json` | Placeholder denylist file (terms array empty - populated server-side) |
| `tests/test_denylist.py` | 20 unit tests covering all LLD Section 10.1 scenarios |

## Implementation Details

### Adherence to LLD

The implementation follows LLD Section 6 precisely:

| LLD Requirement | Implementation |
|-----------------|----------------|
| Tokenization: `re.findall(r'\w+', text)` | ✅ Line 85 of denylist.py |
| Normalization: `unicodedata.normalize('NFKC', text)` | ✅ Line 65 of denylist.py |
| O(1) HashSet lookup | ✅ Uses Python set, O(1) average case |
| Singleton pattern for denylist | ✅ Global `_denylist` variable, loaded once |
| Fail open on errors | ✅ Returns empty set on file/JSON errors |
| Redacted term in result | ✅ Returns `"[REDACTED]"` not actual term |

### DenylistResult Type

```python
class DenylistResult(TypedDict):
    blocked: bool
    term: str | None  # "[REDACTED]" if blocked
    reason: str       # "denylist" or "clean"
```

### Key Design Decisions

1. **Path Resolution:** Default path uses `Path(__file__).parent` for relative resource lookup, compatible with Lambda deployment.

2. **Global Singleton:** The `_denylist` global is loaded once on cold start via `load_denylist()`. Subsequent calls use cached set.

3. **Test Data Hygiene:** Tests mock the denylist with safe placeholder terms (`test_block_term`, `forbidden_fruit`, `blocked_word`) per Gemini review guidance. No real slurs in test files.

## Deviations from LLD

None. Implementation matches LLD specification exactly.

## Performance

Benchmark result from test_070_performance_benchmark:
- **1000 lookups:** < 5ms (budget: 5ms)
- **Actual timing:** ~0.06ms per 1000 lookups

## Known Limitations

Per LLD Section 2 (Deferred to Future):
- Partial word matching for compound slurs requires Trie/Aho-Corasick, incompatible with O(1) hash lookup
- L33t speak bypass (h4te) mitigation deferred

## Integration Notes

The denylist module is self-contained. To integrate with `lambda_function.py`:

```python
from src.guardrails.denylist import check_denylist

# In request handler:
result = check_denylist(user_input)
if result["blocked"]:
    return {"statusCode": 400, "body": "Request blocked"}
```

## Lessons Learned (Post-Implementation)

**Gap Identified:** The LLD specified `denylist.json` but never documented:
- Where the data comes from (RSDB)
- How to download/transform it
- How it gets deployed to Lambda

**Impact:** Implementation is complete but not usable without additional work (#119 RSDB utility).

**Process Improvements:**
1. Created `AgentOS:templates/0108-lld-pre-impl-review` - reviewer checklist for data sources
2. LLD template should require a "Data & Fixtures" section
3. Added entries to `docs/9000-lessons-learned.md`

**Recommendation:** Run the pre-implementation review prompt on all future LLDs before coding begins.

## Next Steps for Orchestrator

1. ~~Review this PR~~ ✅
2. Complete #119 (RSDB download utility) to populate `denylist.json`
3. Integrate with Lambda pipeline (#113 Naked Python)
4. Deploy and verify via CloudWatch logs

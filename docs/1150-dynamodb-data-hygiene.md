# 1150 - Feature: DynamoDB Data Hygiene Tool (Novelty Filter)

## 1. Context & Goal
* **Issue:** #150
* **Objective:** Create CLI tool to clean DynamoDB by keeping novel/interesting words and deleting common words, plus backfill TTL for historical data.
* **Status:** Draft
* **Related Issues:** #145 (DynamoDB TTL), #147 (GDPR erasure)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [x] ~~Which AI model should be used?~~ **None - using simple dictionary filter instead**
- [x] ~~Cost implications?~~ **Zero - no AI calls, just dictionary lookup**
- [x] ~~One-time or ongoing?~~ **One-time cleanup + TTL backfill**
- [x] ~~What about typos like "asdf"?~~ **Acceptable to keep - solution doesn't need to be perfect**
- [ ] Source for common words list? (Options: top 10-20k most frequent English words)

### Resolved Questions (Gemini Review 2026-01-05)

1. **Q: What filtering logic?**
   **A: Novelty Filter (inverted).** Delete COMMON words (boring), keep NOVEL words (interesting).
   - "hello", "test", "working" → DELETE (common)
   - "petrichor", "defenestrate" → KEEP (novel)
   - "asdf" → KEEP (not in common list, acceptable trade-off)

2. **Q: What about historical data without TTL?**
   **A: Add `--backfill-ttl` mode.** Sets `ttl = now + 30 days` on all items missing TTL attribute.

## 2. Requirements

1. **TTL Backfill (CRITICAL):** Add `ttl` attribute to historical data missing it
2. **Novelty Filter:** Keep rare/interesting words, delete common words
3. **Dry-run default:** No deletes without explicit confirmation
4. **Duplicate detection:** Find and flag duplicate (word, url) entries
5. **Audit logging:** Log all deletions

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| AI-powered screening | Smart detection | Cost, privacy, complexity | **Rejected** |
| Simple Dictionary Filter | Zero cost, deterministic, fast | May miss some edge cases | **Selected** |
| Manual review only | Precise | Time-consuming | Rejected |

**Rationale:** Simple dictionary lookup is free, fast, and deterministic. Typos remaining is acceptable trade-off.

## 4. Data & Fixtures

### 4.1 Data Sources

| Attribute | Value |
|-----------|-------|
| Source | DynamoDB AletheiaState table |
| Format | DynamoDB items |
| Size | Unknown - need scan count |
| Refresh | On-demand scan |
| Copyright/License | User data |
| Common Words List | Static text file (10-20k words) |

### 4.2 Data Pipeline

```
DynamoDB ──scan──► Python ──dictionary filter──► Flag common words ──confirm──► Delete
                          ──backfill TTL──► Update items missing TTL
```

### 4.3 Test Fixtures

| Fixture | Source | Notes |
|---------|--------|-------|
| Mock DynamoDB items | Generated | Mix of common and novel words |
| Common words list | Public domain | Top 10-20k English words |

## 5. Diagram

```mermaid
flowchart TD
    A[Start Scan] --> B[Query DynamoDB]
    B --> C{Has TTL?}
    C -->|No| D[Backfill TTL = now + 30d]
    C -->|Yes| E[Check Word]
    D --> E
    E --> F{Duplicate?}
    F -->|Yes| G[Flag for deletion]
    F -->|No| H{In Common Words List?}
    H -->|Yes| G
    H -->|No| I[KEEP - Novel word]
    G --> J{Dry-run mode?}
    J -->|Yes| K[Report only]
    J -->|No| L[Delete]
```

## 6. Technical Approach

* **Module:** `tools/data_hygiene.py`
* **Dependencies:** boto3, click (CLI)
* **Pattern:** Scan, filter, confirm, delete

### 6.1 TTL Backfill (CRITICAL)

```python
TTL_SECONDS = 2592000  # 30 days

def backfill_ttl(dry_run: bool = True) -> int:
    """Add TTL to all items missing it. Returns count updated."""
    table = boto3.resource('dynamodb').Table('AletheiaState')
    count = 0
    ttl_value = int(time.time()) + TTL_SECONDS

    for item in scan_all_items():
        if 'ttl' not in item:
            if not dry_run:
                table.update_item(
                    Key={'thread_id': item['thread_id']},
                    UpdateExpression='SET #ttl = :ttl',
                    ExpressionAttributeNames={'#ttl': 'ttl'},
                    ExpressionAttributeValues={':ttl': ttl_value}
                )
            count += 1

    return count
```

### 6.2 Novelty Filter (Simple Dictionary)

```python
# Load common words once at startup
COMMON_WORDS: set[str] = set()

def load_common_words(path: str = "data/common_words.txt") -> None:
    """Load common words list (10-20k words)."""
    global COMMON_WORDS
    with open(path) as f:
        COMMON_WORDS = {line.strip().lower() for line in f}

def is_common_word(word: str) -> bool:
    """Check if word is in common vocabulary."""
    return word.lower().strip() in COMMON_WORDS

def should_delete(word: str) -> bool:
    """
    Returns True if word should be deleted.

    DELETE if:
    - Word is in common words list (boring)
    - Word length < 3 (fragments like "a", "hi")

    KEEP if:
    - Word is NOT in common list (novel/interesting)
    - Even if it's a typo like "asdf" (acceptable)
    """
    word = word.strip()

    # Delete very short fragments
    if len(word) < 3:
        return True

    # Delete common words
    if is_common_word(word):
        return True

    # Keep everything else (novel words, even typos)
    return False
```

### 6.3 Common Words List

Source options (ranked):
1. **NLTK words corpus** - ~235k words (too broad)
2. **Google 10000 English** - Top 10k most frequent (good)
3. **Custom curated list** - Top 20k + stop words (best)

**Recommendation:** Start with Google 10000 English + explicit stop words.

```python
# Ensure stop words are included
STOP_WORDS = {
    'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and',
    'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
    'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
    'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom',
    'test', 'hello', 'hi', 'bye', 'yes', 'no', 'ok', 'okay',
}
COMMON_WORDS = COMMON_WORDS.union(STOP_WORDS)
```

### 6.4 CLI Interface

```bash
# Scan and report (dry run) - DEFAULT
python tools/data_hygiene.py --scan

# Backfill TTL on historical data (dry run first)
python tools/data_hygiene.py --backfill-ttl --dry-run
python tools/data_hygiene.py --backfill-ttl  # Actually do it

# Delete common words (dry run first)
python tools/data_hygiene.py --clean-common --dry-run
python tools/data_hygiene.py --clean-common  # Actually do it

# Find and show duplicates
python tools/data_hygiene.py --duplicates

# Full cleanup: backfill TTL + delete common words
python tools/data_hygiene.py --full-cleanup --dry-run
```

## 7. Interface Specification

### 7.1 Data Structures
```python
@dataclass
class DynamoDBEntry:
    thread_id: str
    input: str  # The word/phrase
    url: str
    ttl: int | None  # Epoch timestamp, may be missing
    timestamp: datetime | None

@dataclass
class CleanupReport:
    total_scanned: int
    missing_ttl: int
    ttl_backfilled: int
    common_words_found: int
    common_words_deleted: int
    duplicates_found: int
    duplicates_deleted: int
    novel_words_kept: int
```

### 7.2 Function Signatures
```python
def scan_entries() -> list[DynamoDBEntry]:
    """Scan all DynamoDB entries."""
    ...

def backfill_ttl(dry_run: bool = True) -> int:
    """Add TTL to items missing it. Returns count."""
    ...

def find_duplicates(entries: list[DynamoDBEntry]) -> list[tuple[DynamoDBEntry, ...]]:
    """Group entries by (word, url) and return duplicate groups."""
    ...

def filter_common_words(entries: list[DynamoDBEntry]) -> list[DynamoDBEntry]:
    """Return entries that should be deleted (common words)."""
    ...

def delete_entries(entries: list[DynamoDBEntry], dry_run: bool = True) -> int:
    """Delete entries from DynamoDB. Returns count deleted."""
    ...
```

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Accidental data loss | Dry-run default, confirmation required | TODO |
| Audit trail | Log all deletions with thread_id | TODO |
| No AI privacy concerns | Using local dictionary, no external calls | Resolved |

**Fail Mode:** Fail Closed - Require explicit `--no-dry-run` for real deletions.

## 9. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| Scan time | < 5 min | Paginated scan |
| Memory | < 100MB | Stream items, don't load all |
| Cost | $0 | No AI calls, just DynamoDB reads/writes |

**Bottlenecks:** DynamoDB scan throughput. Use pagination.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Delete novel word by mistake | Med | Low | Review common words list carefully |
| Keep too many typos | Low | Med | Acceptable trade-off per decision |
| TTL backfill fails | High | Low | Retry logic, idempotent operation |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Common word detected | Auto | "hello" | should_delete=True | Flagged |
| 020 | Novel word kept | Auto | "petrichor" | should_delete=False | Kept |
| 030 | Typo kept | Auto | "asdf" | should_delete=False | Kept (acceptable) |
| 040 | Short word deleted | Auto | "hi" | should_delete=True | Flagged |
| 050 | TTL backfill | Auto | Item without TTL | TTL added | ttl = now + 30d |
| 060 | Dry-run mode | Auto | --dry-run | No changes | DynamoDB unchanged |

### 11.2 Test Commands

```bash
# Unit tests (mocked DynamoDB)
poetry run pytest tests/test_data_hygiene.py -v

# Dry run on real data
python tools/data_hygiene.py --scan --dry-run
```

## 12. Definition of Done

### Code
- [ ] CLI tool with all modes implemented
- [ ] TTL backfill functionality
- [ ] Novelty filter (common words list)
- [ ] Dry-run default behavior
- [ ] Deletion audit logging

### Data
- [ ] Common words list sourced (10-20k words)
- [ ] Stop words added to list

### Tests
- [ ] Unit tests with mocked DynamoDB
- [ ] Dry-run verified on production

### Documentation
- [ ] Usage instructions in tool docstring
- [ ] Add to file inventory

---

## Appendix: Gemini Review Response

**Review Date:** 2026-01-05
**Reviewer:** Gemini 3 Pro

### Tier 1 Issues (BLOCKING) - Addressed

| Issue | Resolution |
|-------|------------|
| Missing TTL Backfill | Added `--backfill-ttl` mode in §6.1 |

### Tier 2 Issues (HIGH) - Addressed

| Issue | Resolution |
|-------|------------|
| Logic Inversion (Novelty Filter) | Completely replaced AI screening with dictionary filter in §6.2 |

### Tier 3 Issues (SUGGESTIONS) - Addressed

| Issue | Resolution |
|-------|------------|
| Stop Words | Added explicit STOP_WORDS set in §6.3 |
| Minimum Length | Added `len(word) < 3` check in §6.2 |
| Dry Run | Retained as default behavior |

### Accepted Trade-off

Typos like "asdf" may remain in database. This is acceptable per orchestrator decision ("solution doesn't need to be perfect").

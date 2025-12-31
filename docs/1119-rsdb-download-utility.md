# 1119 - Feature: RSDB Download Utility

## 1. Context & Goal
* **Issue:** #119
* **Objective:** Create a utility to download RSDB terms and populate denylist.json
* **Status:** Draft
* **Related Issues:** #45 (Denylist implementation), #113 (Naked Python Architecture)

**Why:**
- #45 implemented the denylist filter but `denylist.json` is empty
- RSDB (Racial Slur Database) is the authoritative source for blocked terms
- Need automated way to fetch and format data

## 2. Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Download RSDB data from GitHub Gist source | Must |
| R2 | Extract and dedupe slur terms | Must |
| R3 | Output in denylist.json schema format | Must |
| R4 | Store output in .gitignored directory | Must |
| R5 | Handle network errors gracefully | Must |
| R6 | Log statistics (term count, duplicates removed) | Should |

## 3. Data & Fixtures

*Per [0108-lld-pre-implementation-review.md](0108-lld-pre-implementation-review.md)*

### 3.1 Data Source

| Attribute | Value |
|-----------|-------|
| Source URL | https://gist.githubusercontent.com/Vizdun/0e9d76834d609dde09842be9bab53db7/raw/rsdb.json |
| Format | JSON array of `{slur, group, desc}` objects |
| Size | ~2,500 entries |
| Copyright | Public domain ("not copyrighted in any way") |
| Refresh | Manual (run utility when update needed) |

### 3.2 Data Pipeline

```
GitHub Gist ──fetch──► Python script ──transform──► .rsdb/denylist.json
                            │
                            └──► .rsdb/rsdb-raw.json (backup of source)
```

### 3.3 Output Locations

| File | Purpose | .gitignored |
|------|---------|-------------|
| `.rsdb/denylist.json` | Formatted for denylist.py | Yes |
| `.rsdb/rsdb-raw.json` | Raw backup from source | Yes |

### 3.4 Deployment Pipeline

```
.rsdb/denylist.json ──copy──► src/guardrails/resources/denylist.json ──deploy.sh──► Lambda
```

**Note:** The copy step is manual (or scripted) before deployment. The `.rsdb/` directory is for local storage only.

## 4. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **GitHub Gist (raw JSON)** | Already structured, ~2500 terms, no scraping needed | Third-party maintained, may drift from original | **Selected** |
| Scrape rsdb.org directly | Authoritative source | Complex HTML parsing, site may be down | Rejected |
| Wikipedia list of slurs | Also comprehensive | Different format, more manual curation | Rejected |

**Rationale:** GitHub Gist provides pre-structured JSON data. If it becomes stale, we can add scraping later.

## 5. Technical Approach

* **Module:** `tools/rsdb_download.py`
* **Dependencies:** Standard library only (`urllib`, `json`, `pathlib`)
* **Pattern:** CLI utility (run manually by Orchestrator)

## 6. Interface Specification

### 6.1 Output Schema
```json
{
    "version": "1.0",
    "source": "rsdb.org",
    "source_url": "https://gist.githubusercontent.com/...",
    "updated": "2025-12-31",
    "term_count": 2347,
    "terms": ["term1", "term2", ...]
}
```

### 6.2 CLI Interface
```bash
# Download and save to .rsdb/
poetry run python tools/rsdb_download.py

# Optional: specify output directory
poetry run python tools/rsdb_download.py --output-dir /path/to/dir

# Dry run (fetch and report stats, don't save)
poetry run python tools/rsdb_download.py --dry-run
```

### 6.3 Logic Flow (Pseudocode)
```
1. Parse CLI arguments
2. Fetch JSON from Gist URL
3. Save raw JSON to .rsdb/rsdb-raw.json (backup)
4. Extract 'slur' field from each entry
5. Normalize: lowercase, strip whitespace
6. Dedupe using set()
7. Sort alphabetically
8. Format as denylist schema
9. Save to .rsdb/denylist.json
10. Print statistics
```

## 7. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Terms committed to repo | Output to .gitignored directory | Addressed |
| Network MITM | Use HTTPS | Addressed |
| Malformed JSON injection | json.load() handles safely | Addressed |

**Fail Mode:** Fail Closed - If download fails, don't overwrite existing file.

## 8. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| Download time | < 5s | Single small JSON file (~100KB) |
| Memory | < 50MB | Stream not needed for 2500 terms |
| Disk | < 1MB | JSON text file |

**Bottlenecks:** Network latency is the only variable. No optimization needed.

## 9. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Gist deleted/moved | High | Low | Save raw backup, document alternative sources |
| Data format changes | Med | Low | Validate expected fields before processing |
| Terms missing/incomplete | Med | Med | Log statistics, manual review before deploy |

## 10. Verification & Testing

*Ref: [0005-testing-strategy-and-protocols.md](0005-testing-strategy-and-protocols.md)*

### 10.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Successful download | Auto | Mock JSON | denylist.json created | File exists with terms |
| 020 | Network error | Auto | Unreachable URL | Error message, no file change | Graceful failure |
| 030 | Malformed JSON | Auto | Invalid JSON | Error message, no file change | No crash |
| 040 | Empty response | Auto | `[]` | Empty terms array | Valid schema, 0 terms |
| 050 | Duplicate removal | Auto | Repeated terms | Unique terms only | Count matches set size |
| 060 | Dry run mode | Auto | --dry-run flag | Stats printed, no file | No file written |

### 10.2 Test Modules

* **Unit Tests:** `poetry run pytest tests/test_rsdb_download.py -v`
* **Semantic (Module B):** No - deterministic utility
* **End-to-End (Module C):** No - offline utility

### 10.3 Manual Smoke Test

1. Run `poetry run python tools/rsdb_download.py`
2. Verify `.rsdb/denylist.json` exists
3. Verify JSON is valid: `python -m json.tool .rsdb/denylist.json`
4. Verify term count is ~2000+
5. Spot check: terms are lowercase, no duplicates

## 11. Definition of Done

### Code
- [ ] `tools/rsdb_download.py` implemented
- [ ] `.rsdb/` added to `.gitignore`
- [ ] Code comments reference this LLD

### Tests
- [ ] `tests/test_rsdb_download.py` covers all scenarios
- [ ] Tests use mocked network responses (no live fetch in tests)

### Documentation
- [ ] LLD updated with any deviations
- [ ] Usage documented in script docstring
- [ ] README or CLAUDE.md updated with deployment pipeline

### Review
- [ ] Code review completed
- [ ] Manual smoke test passed
- [ ] Orchestrator verified denylist.json is usable

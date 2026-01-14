# 10069 - Feature: CLI Log Inspector

## 1. Context & Goal
* **Issue:** #69
* **Objective:** Detailed CLI tool to inspect Aletheia DynamoDB telemetry without creating local artifacts.
* **Status:** In Progress

## 2. Requirements
* **Source:** DynamoDB table `AletheiaAgentState` (us-east-1).
* **Output:** Stdout (Console) only.
* **Sort:** Oldest -> Newest (Log file style).
* **Filter:**
    * Default: Show all records.
    * Option: `--tail N` (Show last N records).
* **Formatting:**
    * Columns: `[Index/Total]`, `Timestamp`, `Word`, `Site`.
    * **Timezone:** Central Time (America/Chicago).
    * **Timestamp Format:** `Dec 20 14:13` (`%b %d %H:%M`).
    * **Site Display:** Defaults to Domain (e.g., `wsj.com`). Flag `--full-url` shows complete link.
    * **Dynamic Alignment:** Column widths expand to fit content + 3 spaces padding.

## 3. Technical Approach
* **Script:** `tools/log_viewer.py`
* **Dependencies:**
    * `boto3` (AWS SDK)
    * `argparse` (CLI parsing)
    * `tzdata` (Windows Timezone Database)
* **Performance:** Scan operation.

## 4. Implementation Details

### 4.1 Data Structure
```python
@dataclass
class LogEntry:
    raw_timestamp: str # ISO 8601 for sorting
    display_time: str  # Formatted for display
    word: str
    site_full: str     # Full URL
    site_domain: str   # Parsed domain

```

### 4.2 Logic

1. **Fetch:** Scan `AletheiaAgentState`.
2. **Normalize:**
* Parse ISO timestamp -> UTC -> Central Time.
* Parse URL -> Domain (`urllib.parse.urlparse`).


3. **Sort:** By `raw_timestamp` (ascending).
4. **Filter:** Apply `--tail N` if requested.
5. **Format:**
* Calculate max width of each column (based on filtered set).
* Print with 3-space separation.



## 5. Verification & Testing

### 5.1 Manual Smoke Test

```bash
# 1. Default (Domain only, oldest first)
poetry run python tools/log_viewer.py

# 2. Tail + Domain
poetry run python tools/log_viewer.py --tail 5

# 3. Tail + Full URL
poetry run python tools/log_viewer.py --tail 5 --full-url

# 4. Help
poetry run python tools/log_viewer.py --help

```

## 6. Definition of Done

* [ ] Script `tools/log_viewer.py` created.
* [ ] Output aligns perfectly with variable data lengths.
* [ ] Timezone is correct (Central).
* [ ] LLD (this file) committed.
* [ ] `docs/0003-file-inventory.md` updated with `tools/log_viewer.py`.
* [ ] PR Merged & Branch Cleanup.

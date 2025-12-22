# 0007 - Strategy: Legal Compliance & Signal Handling

## 1. Philosophy: Assistant vs. Crawler
Aletheia is a **User Agent** acting on behalf of a human, not a **Search Crawler** indexing the web.
* **We DO NOT index.** (We answer specific questions).
* **We DO NOT archive.** (We store ephemeral context for the chat session).
* **We DO NOT publish.** (The chat is private to the user).

Therefore, standard SEO signals (`noindex`, `robots.txt`) do not apply. We honor signals related to **Persistence** and **AI Training**.

## 2. Signal Matrix

| Signal | Meaning | Standard Crawler Action | Aletheia Action | Reasoning (The "Why") |
| :--- | :--- | :--- | :--- | :--- |
| **`noai`** / **`noimageai`** | No AI Training | Block | **HARD STOP** | We respect explicit "No AI" wishes. |
| **`noarchive`** | Do not cache | Block Cache | **Summarize Only** | We will not persist raw text to DynamoDB. We convert to ephemeral summary. |
| **`noindex`** | Do not Search Index | Block Indexing | **Ignore** | We are not a search engine. User is reading a private page. |
| **`nosnippet`** | No Search Snippets | Block Snippets | **Ignore** | Chat UI is not a Search Result Page (SERP). |
| **`robots.txt`** | Crawler Rules | Block Path | **Ignore** | We are a User Agent driven by explicit user action. |

## 3. The "Summarization" Switch
* **Default State:** **Raw Text.** The user's selection and context are sent to the Agent for maximum accuracy.
* **Restricted State (`noarchive`):** **Summary Only.** The system extracts a "Fair Use" summary and discards the raw text immediately.

## 4. Implementation
* **Detection:** Browser Extension (`content.js`) parses Meta Tags and Headers.
* **Enforcement:** Backend (`summarizer.py`) checks `signals` payload.

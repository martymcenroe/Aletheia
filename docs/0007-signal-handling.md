# 0007 - Signal Handling Strategy

## 1. Philosophy: Assistant vs. Crawler
Aletheia is a **User Agent** acting on behalf of a human, not a **Search Crawler** indexing the web.
* **We DO NOT index.** (We answer specific questions).
* **We DO NOT archive.** (We store ephemeral context for the chat session).
* **We DO NOT publish.** (The chat is private to the user).
* **We DO NOT train.** (We perform inference only, no model training).

Therefore, standard SEO signals (`noindex`, `robots.txt`) do not apply. We honor signals related to **Persistence** and **Content Safety**.

## 2. Signal Matrix

| Signal | Meaning | Standard Crawler Action | Aletheia Action | Reasoning (The "Why") |
| :--- | :--- | :--- | :--- | :--- |
| **`noai`** / **`noimageai`** | No AI Training | Block | **Ignore** | We do inference, not training. These signals target training crawlers. |
| **`noarchive`** | Do not cache | Block Cache | **Transform** | We will not persist raw text. Transform layer summarizes before storage. |
| **`noindex`** | Do not Search Index | Block Indexing | **Ignore** | We are not a search engine. User is reading a private page. |
| **`nosnippet`** | No Search Snippets | Block Snippets | **Ignore** | Chat UI is not a Search Result Page (SERP). |
| **`robots.txt`** | Crawler Rules | Block Path | **Ignore** | We are a User Agent driven by explicit user action. |
| **`rating="adult"`** | Age-restricted content | N/A | **Block Site** | Extension will not function on adult-rated sites. See Issue #104. |

## 3. The Transform Switch
* **Default State:** **Raw Text.** The user's selection and context are sent to the Agent for maximum accuracy.
* **Restricted State (`noarchive`):** **Summary Only.** The Transform layer extracts a "Fair Use" summary and discards the raw text immediately.

## 4. Implementation
* **Detection:** Browser Extension (`service-worker.js`) parses Meta Tags and Headers.
* **Enforcement:** Backend Transform layer (`lambda_function.py`) checks `signals` payload.

## 5. Decision Rationale

### Why Ignore `noai`?
The `noai` and `noimageai` meta tags were created to prevent AI training crawlers from ingesting content. Aletheia:
- Does **not** train models
- Does **not** store content for future training
- Performs **inference only** on user-selected text
- Acts as a **user agent**, not a crawler

Therefore, honoring `noai` would be overly restrictive and misinterpret the tag's intent.

### Why Transform on `noarchive`?
The `noarchive` tag indicates the publisher doesn't want their content cached/archived. We respect this by:
- Not persisting raw text to DynamoDB
- Running the Transform layer to create a summary
- Storing only the derived summary (if needed)
- Discarding the original text after processing

This aligns with the spirit of `noarchive` while still providing value to the user.

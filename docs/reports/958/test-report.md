# Test Report — Issue #958

Run against production on 2026-11-13 at about 2:58 PM Central, after `wrangler triggers deploy`.

| Test | Command | Result |
|---|---|---|
| T1 | `curl -s https://aletheia-api.thrivetech.ai/health` | `{"status": "ok", "version": "1.0"}`, HTTP 200. The first attempt failed to resolve the brand-new DNS record (curl exit 6); the retry a few seconds later passed. |
| T2 | `curl -s -X POST https://aletheia-api.thrivetech.ai/ -H 'Content-Type: application/json' -H 'X-Aletheia-Client-Version: 1.0' -d '{"text":"test"}'` | `{"error": "Unauthorized", "reason": "missing_token"}`, HTTP 401: Worker, origin secret and version check all pass. |
| T3 | `curl -s https://api.aletheia.study/health` | `{"status": "ok", "version": "1.0"}`, HTTP 200: the old route still answers. |

No unit test reads `wrangler.toml`.

# Test Report: #496 Route Auth Through Custom Domain

## Verification
- `grep -r 'sk33bz56yi5qlbrrwzqnprmeuy0xwhzn' extensions/` returns no matches
- Both auth.js files point to `https://api.aletheia.study`
- Both manifest.json files have single clean host_permission
- CloudFlare Worker already routes `/auth/*` to Auth Lambda (verified in worker.js)
- Full OAuth flow requires manual LinkedIn redirect URI update before testing

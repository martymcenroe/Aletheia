# Implementation Report: #496 Route Auth Through Custom Domain

## Changes
- `extensions/chrome/auth.js`: LAMBDA_AUTH_URL → `https://api.aletheia.study`
- `extensions/firefox/auth.js`: LAMBDA_AUTH_URL → `https://api.aletheia.study`
- `extensions/chrome/manifest.json`: removed raw Lambda URL from host_permissions
- `extensions/firefox/manifest.json`: removed raw Lambda URL from host_permissions

## How It Works
The CloudFlare Worker (`workers/aletheia-api/worker.js`) already routes `/auth/*` paths to the Auth Lambda. The extension now uses the clean custom domain URL instead of the raw Lambda Function URL.

## Manual Steps Required
1. **LinkedIn OAuth App:** Update redirect URI from `https://sk33bz56yi5qlbrrwzqnprmeuy0xwhzn.lambda-url.us-east-1.on.aws/auth/callback` to `https://api.aletheia.study/auth/callback`
2. **Chrome identity redirect:** Already uses `chrome.identity.getRedirectURL()` — no change needed
3. **Firefox AMO:** Resubmit extension with updated manifest

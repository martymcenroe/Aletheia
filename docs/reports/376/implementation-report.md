# Implementation Report: #376 Admin ID Resolution CLI

## Summary
New CLI tool for mapping between real user IDs and their anonymized hashes from the CloudWatch Usage Dashboard (#369).

## Files
| File | Purpose |
|------|---------|
| `tools/admin_id_resolve.py` | CLI with `forward` and `reverse` subcommands |
| `tests/unit/test_admin_id_resolve.py` | 8 unit tests with mocked DynamoDB |

## Design
- **Forward resolve**: Calls `anonymize_user_id()` to hash a known user_id
- **Reverse resolve**: Brute-force scans users table, hashes each user_id, matches against target
- **PII guard**: Reverse lookup requires `--confirm` flag (dry_run default)
- **Pattern**: Follows `admin_subscriptions.py` (argparse, lazy DynamoDB client, env-var config)

## Usage
```bash
poetry run python tools/admin_id_resolve.py forward USER_ID
poetry run python tools/admin_id_resolve.py reverse HASH --confirm
```

# Aletheia: AI-Powered Context Analysis Engine

![CI](https://github.com/martymcenroe/Aletheia/actions/workflows/ci.yml/badge.svg)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Aletheia** (Greek: *truth, unconcealment*) is a privacy-first browser extension that helps users understand the historical context and etymology of words and phrases. Select text on any webpage, right-click "Explain with AI", and get an etymology-rich analysis powered by a serverless AI backend.

**[aletheia.study](https://aletheia.study)** | **[Wiki](https://github.com/martymcenroe/Aletheia/wiki)** | **[Privacy Policy](https://github.com/martymcenroe/Aletheia/wiki/Privacy)**

---

## Features

- **Etymology Analysis** — Understand the origins and evolution of words and phrases
- **Context-Aware** — Considers surrounding text for disambiguation
- **Privacy-First** — Minimal permissions, anonymized logging, no browsing history access
- **Multi-Browser** — Chrome (Manifest V3) and Firefox (Manifest V2)
- **Tiered Subscriptions** — Free tier with generous limits, premium tier for heavy users
- **JWT Authentication** — LinkedIn OAuth sign-in with local token validation (<1ms)
- **Rate Limiting** — Per-user multi-window caps (hourly/daily/monthly) with DynamoDB atomic counters

## Architecture

```
Browser Extension → CloudFlare Worker → Lambda Function URL → Lambda (Python 3.12)
                                              ↓
                                     AWS Bedrock (Claude) + DynamoDB
```

| Layer | Technology |
|-------|------------|
| **Frontend** | Browser extension (JavaScript, Manifest V3) |
| **Edge** | CloudFlare Workers (rate limiting, DDoS, shared secret) |
| **Compute** | AWS Lambda (Python 3.12) — Agent + Auth |
| **AI** | AWS Bedrock (Anthropic Claude) |
| **State** | DynamoDB (agent state, users, token cap, coupons) |
| **Auth** | LinkedIn OAuth → JWT (HS256) → Secrets Manager |
| **Billing** | Stripe (subscriptions, webhooks, checkout) |
| **Observability** | CloudWatch (EMF metrics, X-Ray tracing, 14-day retention) |

## Tech Stack

| Category | Tools |
|----------|-------|
| **Language** | Python 3.12 (backend), JavaScript (extension) |
| **Cloud** | AWS Lambda, DynamoDB, Secrets Manager, CloudWatch, Bedrock |
| **Edge** | CloudFlare Workers, CloudFlare DNS |
| **Auth** | LinkedIn OAuth, JWT (PyJWT), dual-secret rotation |
| **Billing** | Stripe SDK (subscriptions, webhooks, checkout sessions) |
| **AI** | LangGraph (agent orchestration), AWS Bedrock (Anthropic Claude) |
| **Testing** | pytest (975+ tests), mypy, ruff, gitleaks |
| **CI/CD** | GitHub Actions, pre-commit hooks (12 checks) |
| **IaC** | Bash/AWS CLI provisioning (`provision.sh`) |

## Quick Start (Development)

```bash
# Clone
git clone https://github.com/martymcenroe/Aletheia.git
cd Aletheia

# Install dependencies
poetry install

# Run tests
poetry run pytest tests/ --ignore=tests/integration -q

# Provision AWS infrastructure (requires configured AWS CLI)
./provision.sh

# Load extension in Chrome
# 1. Navigate to chrome://extensions/
# 2. Enable Developer mode
# 3. Click "Load unpacked" → select extensions/chrome/
```

## Project Structure

```
Aletheia/
├── extensions/chrome/       # Chrome Manifest V3 extension
├── extensions/firefox/      # Firefox Manifest V2 extension
├── src/                     # Python backend
│   ├── auth/                # JWT, middleware, OAuth, rate limiting, Stripe
│   ├── guardrails/          # Content safety filtering
│   ├── signal_inspector/    # Signal analysis logic
│   └── lambda_function.py   # Agent Lambda handler
├── tests/                   # 975+ unit tests
├── tools/                   # Admin CLIs (subscriptions, coupons, token cap, ID resolve)
├── docs/                    # ADRs, LLDs, audits, runbooks, reports
└── provision.sh             # AWS infrastructure provisioning
```

## Admin Tools

```bash
# Subscription management
poetry run python tools/admin_subscriptions.py view --user-id USER_ID

# Coupon management
poetry run python tools/admin_coupons.py create --tier premium --duration 30

# Token cap management
poetry run python tools/admin_token_cap.py --new-cap 50 --admin-id admin@example.com

# ID resolution (anonymized hash ↔ user ID)
poetry run python tools/admin_id_resolve.py forward USER_ID
poetry run python tools/admin_id_resolve.py reverse HASH --confirm
```

## Security

- **Defense in depth**: CloudFlare DDoS → rate limiting → shared secret → JWT validation → input validation → AI guardrails
- **Minimal permissions**: Extension requests only `contextMenus`, `activeTab`, `storage`
- **Privacy-preserving logs**: User IDs anonymized via SHA-256 truncation before logging
- **Secret management**: All secrets in AWS Secrets Manager, never in code or env vars
- **Pre-commit hooks**: gitleaks, ruff, mypy, ESLint security rules

See [Security Policy](https://github.com/martymcenroe/Aletheia/wiki/Security) and [20 ADRs](https://github.com/martymcenroe/Aletheia/tree/main/docs/adrs) documenting architectural decisions.

## Documentation

| Resource | Description |
|----------|-------------|
| [Wiki](https://github.com/martymcenroe/Aletheia/wiki) | User guide, architecture, API reference |
| [ADRs](docs/adrs/) | 20 architecture decision records |
| [Privacy Policy](https://github.com/martymcenroe/Aletheia/wiki/Privacy) | Data handling and retention |
| [aletheia.study](https://aletheia.study) | Product landing page |

## License

[MIT](LICENSE)

---

*Built by [Marty McEnroe](https://github.com/martymcenroe) using the AI-as-Workforce development paradigm.*

# Implementation Report: #371 Web Presence Updates

## Summary
Full rewrite of README.md and 7 wiki pages, plus marketing copy and LinkedIn launch post in dispatch repo.

## Changes

### README.md (Full Rewrite)
- Fixed broken badge syntax (was raw shell commands in markdown)
- Updated tech stack: CloudFlare Workers (not CloudFront+WAF), Bedrock Claude (not OpenAI)
- Added features: JWT auth, LinkedIn OAuth, Stripe billing, tiered rate limiting, admin tools
- Fixed Quick Start paths: `extensions/chrome/` (was `extension/`)
- Added architecture diagram, project structure, admin tools section, security highlights
- Added links to aletheia.study, wiki, privacy policy

### Wiki Pages Updated (7 of 13)
| Page | Key Changes |
|------|-------------|
| `Home.md` | Tech stack (CloudFlare, Stripe, Bedrock Claude), features (auth, billing, rate limiting), milestones updated |
| `Architecture.md` | New Mermaid diagram (CloudFlare Worker + Auth Lambda), 4 DynamoDB tables, ADR references 10217-10219, 7-layer security |
| `API-Reference.md` | Base URL → api.aletheia.study, JWT auth docs, billing/admin/GDPR endpoints, per-tier rate limits |
| `User-Guide.md` | Authentication section, subscription tiers, upgrade flow |
| `Developer-Guide.md` | Repo structure (auth package, admin tools), workflow (worktrees, pre-merge gate), 12 pre-commit hooks |
| `Getting-Started.md` | Sign-in step added, JWT troubleshooting |
| `_Sidebar.md` | aletheia.study link added |

### NOT Modified
- `Privacy.md` — Chrome Web Store submission, frozen

### Dispatch Repo (Marketing Copy)
| File | Purpose |
|------|---------|
| `drafts/2026-02-19-aletheia-launch-linkedin.md` | LinkedIn launch post (short + long versions) |
| `drafts/2026-02-19-aletheia-product-copy.md` | Core messaging, feature list, tier comparison, Chrome Web Store listing |

## Constraints
- Privacy.md preserved unchanged (Chrome Web Store requirement)
- Wiki changes pushed directly (no PR process for wiki)
- ADRs 10217-10219 referenced by Architecture page (must merge #370 first)

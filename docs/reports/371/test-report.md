# Test Report: #371 Web Presence Updates

## Verification
- README.md badges render as proper markdown (not shell commands)
- README.md links: aletheia.study, wiki, privacy policy, ADRs, LICENSE all correct
- Wiki pages: no references to CloudFront or WAF remain in updated pages
- Wiki Privacy.md: NOT modified (verified via git diff exclusion)
- All wiki pages have updated timestamps (2026-02-19)
- Dispatch drafts have valid YAML frontmatter
- No unit tests required (documentation/content-only change)

## Wiki Changes Verification
- [x] Home.md — Tech stack shows CloudFlare, Bedrock Claude (not CloudFront, OpenAI)
- [x] Architecture.md — Mermaid diagram shows CloudFlare Worker → Lambda Function URL
- [x] API-Reference.md — Base URL is api.aletheia.study, JWT auth documented
- [x] User-Guide.md — Authentication and subscription sections added
- [x] Developer-Guide.md — Repo structure includes auth package
- [x] Getting-Started.md — Sign-in step and JWT troubleshooting added
- [x] _Sidebar.md — aletheia.study link present
- [x] Privacy.md — Unchanged

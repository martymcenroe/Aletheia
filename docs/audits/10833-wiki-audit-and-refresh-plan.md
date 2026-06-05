# 10833 — Wiki Audit + Refresh Plan

> **Issues:** #739 (original plan), #741 (revisions per operator decisions)
> **Status:** Decisions captured; plan ready to drive follow-up issues per § 9
> **Authored:** 2026-06-04 | **Revised:** 2026-06-04 (operator decisions; see § 12)
> **Scope:** `https://github.com/martymcenroe/Aletheia.wiki` only. The repo itself, the marketing site, the store listings, and the runbooks are out of scope.
> **Supersedes:** Nothing. Complements `docs/audits/10817-audit-wiki-alignment.md` (the recurring checklist). This document is the project-specific, one-time refresh plan that 10817 cannot generate from first principles.
> **Mermaid standard:** `AssemblyZero/docs/standards/0004-mermaid-diagrams.md` is adopted verbatim for all diagrams produced by this refresh. See § 5.1.

---

## 1. Why this plan exists

The wiki was last touched 2026-01-06 (Architecture, Home, API-Reference) and 2026-01-04 (Security) — five months stale. During the 2026-06-04 session, a resume-writing agent's accurate model-routing claim (Haiku default + Opus verifier on injection flag) was checked against the wiki and the wiki contradicted both the code and itself.

A small sample of what is currently published on the wiki and is wrong:

| Wiki page / line | What it says | What is true | Evidence |
|---|---|---|---|
| `Home.md:27, :49, :51, :71` | Firefox MV2; AI = Nova Micro; Security = CloudFront + WAF; License = MIT | MV3; Haiku 4.5 default; CloudFlare Worker + Lambda; PolyForm Noncommercial 1.0.0 | `extensions/firefox/manifest.json`, `src/etymologist.py:30`, `workers/aletheia-api/worker.js`, `LICENSE` |
| `Architecture.md:16, :18, :46, :52, :77` | CloudFront + WAF in current diagram; Bedrock Nova Micro is THE model; Firefox MV2; API Gateway as routing | All abandoned or wrong | Issue #349, `src/lambda_function.py:50`, manifest, `workers/aletheia-api/worker.js` |
| `Security.md:50-51, :87` | WAF Protection; CloudFront rate limits; CloudFront in third-party services | Edge is CloudFlare Worker; rate limit is 3 req / 10 s / IP at the Worker | `workers/aletheia-api/worker.js` (rate limit not visible in this file — set in dashboard) |
| `API-Reference.md:9, :16, :29` | "REST API via AWS CloudFront"; base URL is `[cloudfront-distribution].cloudfront.net`; endpoint is `POST /analyze` | API is at `https://api.aletheia.study` (CloudFlare); the analysis endpoint is `POST /` (root), with `/auth/*`, `/admin/*`, `/metrics`, `/my-data`, `/redeem-coupon`, `/upgrade-*`, `/create-checkout-session`, `/stripe-webhook`, `/subscription-status` routing to AletheiaAuth; `/health` is documented in CLAUDE.md smoke test | `workers/aletheia-api/worker.js:11-15` |

The wiki has also drifted in framing. `Home.md:5` still positions Aletheia as a "Digital Etymologist" focused on historical context — the product now markets itself (AMO and CWS listings) as a privacy-first context analyzer with prompt-injection detection.

The operator also needs the wiki to function as an interview reference. Today there is no single page that maps technical concepts (model routing, edge architecture, four-Lambda topology, OAuth flow, cost tagging, the Digital Etymologist product concept) to one-paragraph explanations and pointers into the wiki. Engineers and hiring managers ask about these concepts; the answer should not require the operator to skim 1,542 lines of wiki text mid-conversation.

This plan exists to define how to fix all of the above.

---

## 2. Scope

In scope:

| Page | Lines | Notes |
|---|---|---|
| `Home.md` | 83 | Project positioning, stack table, status |
| `Getting-Started.md` | 121 | Install steps for end users |
| `User-Guide.md` | 105 | Usage instructions |
| `FAQ.md` | 113 | Q&A |
| `Architecture.md` | 142 | Mermaid diagram + components |
| `Developer-Guide.md` | 225 | Local dev, testing, deploy |
| `API-Reference.md` | 193 | Endpoints, request/response schemas |
| `Privacy.md` | 174 | Data handling, retention |
| `Security.md` | 124 | Threat model, controls |
| `Terms-of-Use.md` | 76 | Content policy |
| `Contributing.md` | 156 | PR workflow |
| `_Sidebar.md` | 26 | Wiki navigation |
| `_Footer.md` | 4 | Wiki footer |

Out of scope: every file outside `Aletheia.wiki/`. Cross-references from the wiki INTO the repo (e.g. a link to `docs/runbooks/10907`) stay as references; we do not edit the repo targets.

Also out of scope: actually applying any fixes. This PR is the plan only. Each fix is a follow-up issue per § 9.

---

## 3. Methodology

### 3.1 Operating principle

The repo audit philosophy already says it (`docs/audits/10800-audit-index.md` § 2.1): **"The code is the truth. The docs are a claim about the truth."** Evidence-over-inference applies everywhere. Every wiki claim about behavior, infrastructure, or API shape gets a grep / read citation before it is accepted or marked drifted.

### 3.2 Per-page procedure

For each wiki page, the audit produces a findings section in the eventual audit report (a separate doc, not this plan). The procedure:

1. **Read the page top-to-bottom**, listing every factual claim (architecture, API shape, license, version, behavior). Opinion sentences ("designed to inform, not judge") are noted separately and only flagged if they contradict the published positioning.
2. **For each factual claim, grep the code or read the canonical source.** Cite file:line. If the claim is true, mark `OK`. If wrong, capture both the wiki text and the source-of-truth text.
3. **For each diagram (mermaid or embedded image)**, render it mentally against the current architecture. Capture nodes that are stale, edges that are missing, and edges that no longer exist.
4. **List missing concepts.** A page is incomplete if a reader following its TOC could not learn things the page is positioned to teach (e.g. `Security.md` says nothing about the kill-switch Lambda, the audit-log hashing PRs, or the CloudFlare-Worker edge shared-secret pattern).
5. **List unclear concepts.** Things technically present but written so a reader who does not already know Aletheia cannot follow.

### 3.3 Cross-cutting checks

After per-page audits, run the cross-cutting checks:

- **Terminology consistency.** "Etymology" vs "context analysis" vs "explanation"; "Digital Etymologist" as product name vs as internal module name; "Bedrock" vs "AWS Bedrock"; "Lambda" (which one of the four?) vs "AletheiaAgent" etc.
- **Naming consistency.** `aletheia-state` table, `aletheia-api` Worker, `AletheiaAgent` / `AletheiaAuth` / `AletheiaKillSwitch` / `AletheiaHermesPoller` Lambdas, `aletheia-haiku` / `aletheia-opus` / `aletheia-nova-micro` AIPs — all canonical, all should be used consistently.
- **Sidebar / Footer accuracy.** `_Sidebar.md` lists the pages; if pages are renamed or added, the sidebar is updated in lock-step.
- **Internal link integrity.** Wiki-internal `[[Page]]` links resolve.
- **External link integrity.** Repo links (e.g. `.../blob/main/LICENSE`) point at files that still exist.

### 3.4 Evidence files the auditor must read

Required reading before findings are credible:

- `src/lambda_function.py` (Agent Lambda entry, ~600 lines)
- `src/lambda_auth_function.py` (Auth Lambda entry)
- `src/etymologist.py` (model dispatch, Haiku/Opus/Nova routing, Opus verifier)
- `src/poetic_analyzer.py` (Poetic Analyzer, if still wired)
- `src/guardrails/` (Defense funnel)
- `src/signal_inspector/` (signal logic)
- `src/auth/auth_middleware.py` (auth integration)
- `workers/aletheia-api/worker.js` (CloudFlare Worker — short, read in full)
- `provision.sh` (Lambda + IAM + AIP provisioning; ground-truth topology)
- `extensions/chrome/manifest.json`, `extensions/firefox/manifest.json`
- `extensions/{chrome,firefox}/service-worker.js`, `auth.js`, `overlay.js`
- `LICENSE` (license name)
- `docs/runbooks/10905-runbook-cws-publish.md`, `docs/runbooks/10907-runbook-amo-publish.md` (current published versions / store state)
- `docs/architecture/*` (existing architecture docs; cross-reference, do not assume current)

### 3.5 Required reading the auditor must NOT skip

The auditor must not write findings from memory or from a single representative file. The historical drift in the wiki happened in part because the wiki was updated once from a single sweep of headline files; subsequent reorganizations (multi-Lambda split, CloudFront deletion, AIP introduction, Auth Lambda addition, MV3 migration, Opus verifier) each added their own drift because no per-claim re-grep ever happened.

If § 3.4's reading list is felt as a burden mid-audit, the audit is being done at the wrong altitude — pause and re-scope rather than skip files. Skipped files become next year's wiki drift.

---

## 4. Page-by-page audit checklist

For each page, the audit report's per-page section answers these questions:

| # | Question | Action if "no" |
|---|---|---|
| 1 | Does every factual claim cite the code/config it describes? | Capture drift table row |
| 2 | Are all current architectural components mentioned? | List missing components |
| 3 | Is the diagram (if any) current? | Capture stale nodes + missing edges |
| 4 | Does the page address the concepts a reader would expect from its title? | List missing concepts |
| 5 | Is terminology consistent with other pages and with the marketing positioning? | Note inconsistency |
| 6 | Do internal/external links resolve? | List broken links |
| 7 | Is the `*Last updated*` stamp present and ≤30 days from this audit's commit date? | Update at refresh time |

The plan does NOT contain the per-page findings; that is the audit report's deliverable. The plan only specifies what the report must answer.

### 4.1 Known starting points (planning input — auditor extends)

Auditor begins each page with a head-start drift list seeded from the 2026-06-04 surfacing. Auditor MUST treat this as starting input, not final input — drift not in the table below is still drift if found.

**`Home.md` known drift seeds:**

- Line 27: "Firefox (Manifest V2)" → MV3.
- Line 49: "AWS Bedrock (Amazon Nova Micro)" → Bedrock with three AIPs; Haiku 4.5 is the default routing target; Opus 4.6 is the verifier on prompt-injection flag; Nova Micro is a supported alternative.
- Line 51: "CloudFront + WAF" → CloudFlare Worker `aletheia-api` (edge auth + rate limit) → Lambda Function URLs.
- Line 65: Project status table is stale ("Store Compliance: In Progress" — CWS is live at 1.1.2; AMO is live at 1.1.1, 1.1.2 built and pending upload).
- Line 71: "MIT License" → PolyForm Noncommercial 1.0.0.
- Line 5: "Digital Etymologist" framing predates the privacy-first-context-analyzer positioning of the AMO and CWS listings. Re-decide product framing.
- Missing entirely: the Auth Lambda, the OAuth / LinkedIn flow, the four-Lambda topology, the Stripe / subscription / coupon surface, the kill-switch Lambda, the Hermes poller.

**`Architecture.md` known drift seeds:**

- Lines 16, 18, 60-63, 73-74: CloudFront + WAF in current mermaid + Security Layers + Data Flow.
- Line 46: Firefox MV2.
- Lines 52-55: Backend Services table names API Gateway / CloudFront / WAF / Claude 3 Haiku.
- Line 77: Data Flow step 7 sends to "Bedrock (Nova Micro)" — wrong default.
- Diagram (lines 9-29) has no CloudFlare, no Worker, no Auth Lambda, no second Lambda Function URL, no Bedrock AIPs, no Opus verifier path, no defense funnel.
- ADR Highlights table (lines 94-100) ends at 0207; later ADRs are not surfaced.

**`Security.md` known drift seeds:**

- Lines 50-51: "WAF Protection" + "CloudFront rate limits" — wrong; rate limit is at the CloudFlare Worker.
- Line 87: CloudFront listed as a third-party-service component.
- Missing: kill-switch Lambda; per-Lambda IAM separation (HermesPollerRole vs AletheiaLambdaRole); shared-secret pattern (`X-Origin-Secret` header injected by Worker, SSM `/aletheia/cloudflare-origin-secret`); CloudWatch deny budget gate (#535). (Opus verifier is NOT a flagship defense layer per operator decision § 12; mentioned only factually if the page enumerates the defense funnel.)

**`API-Reference.md` known drift seeds:**

- Line 9: "REST API via AWS CloudFront" → CloudFlare.
- Line 16: base URL is `[cloudfront-distribution].cloudfront.net` → `https://api.aletheia.study`.
- Line 23: "rate limiting rather than authentication tokens" — LinkedIn OAuth IS now an authentication option; both are in play.
- Line 29: `POST /analyze` → `POST /` (root path per CLAUDE.md smoke test).
- Lines 56-66: Response schema includes nested `etymology.{origin, period, evolution}` — verify against actual response shape in `etymologist.py` and `lambda_function.py`.
- Missing endpoints: all `/auth/*`, `/admin/*`, `/metrics`, `/my-data`, `/redeem-coupon`, `/upgrade-*`, `/create-checkout-session`, `/stripe-webhook`, `/subscription-status`, `/health`. Each routes to `AletheiaAuth` via the Worker's prefix list.

**Other pages: no seeded drift list.** The auditor must produce these from scratch using § 3.

---

## 5. Mermaid diagram refresh

### 5.1 Standard — AssemblyZero 0004

Every diagram produced by this refresh follows `C:/Users/mcwiz/Projects/AssemblyZero/docs/standards/0004-mermaid-diagrams.md` verbatim. Load-bearing rules from 0004:

- **§ 2.1, § 4.1:** `flowchart TD` for vertical flows; `graph TB` for request/response patterns; never `LR` if any edge points backward.
- **§ 3:** Router pattern — funnel decisions through a single diamond rather than connecting every node to every other.
- **§ 5.1:** "Quote Everything" — all label text in double quotes if it contains spaces, parens, or special characters. `Node["User Input"]` not `Node[User Input]`.
- **§ 5.2:** Line breaks inside labels via `<br/>` inside the quoted string. Never raw newlines.
- **§ 5.3:** Hash/semicolon/braces inside labels must be quoted (`Node["Issue #80"]`).
- **§ 7.2:** Request/response — TB layout, dashed arrows (`-.->`) for the response leg.
- **§ 7.4:** Cyclic flows — eliminate the cycle, use an explicit return node, dashed backward edge, or split into two diagrams. Never let an arrow route behind a box.
- **§ 8.1:** Collapse near-identical nodes (Chrome+Firefox extension nodes collapse to "Extension" unless their interactions differ).
- **§ 8.4 / § 8.5:** Visual inspection is REQUIRED before commit. Agent procedure: base64-encode the diagram, fetch from `mermaid.ink`, view the PNG with the Read tool, inspect against the § 8.4 checklist (touching elements, hidden lines, label readability, flow clarity).
- **§ 8.6:** Dark-mode compatibility — avoid `#334155` (invisible on dark) and `#f8fafc` (invisible on light); test in both modes; prefer no custom fills unless color carries semantic meaning.
- **§ 8.7:** After landing, take Playwright screenshots of the rendered wiki page in both GitHub themes to verify the iframe-rendered diagram looks right (accessibility snapshots cannot read inside the iframe).

Any deviation from 0004 in this refresh is a finding to surface, not a license to deviate.

### 5.2 Existing diagrams

Currently the wiki has one mermaid diagram (`Architecture.md:9-29`). It depicts: Browser Extension → CloudFront+WAF → Lambda → Bedrock (Nova Micro) + DynamoDB. As § 4.1 records, this is wrong on at least four nodes. It also pre-dates 0004 — it would need a 0004 pass even if every label were correct.

### 5.3 Diagrams the refresh should produce

The plan recommends the refreshed wiki carry four diagrams. Per operator decision (§ 12), all four live INLINE in `Architecture.md` — no `AI-Pipeline.md` or `Extension-Internals.md` split. Architecture.md becomes longer; that is acceptable.

**Diagram A — Edge & request routing.**
Shows: Browser → CloudFlare DNS (`api.aletheia.study`) → CloudFlare Worker (`aletheia-api`) → either AletheiaAgent Lambda Function URL (POST /, analysis) or AletheiaAuth Lambda Function URL (`/auth/*`, `/admin/*`, `/metrics`, `/my-data`, `/redeem-coupon`, `/upgrade-*`, `/create-checkout-session`, `/stripe-webhook`, `/subscription-status`). Annotates the `X-Origin-Secret` header injection and the 3 req / 10 s / IP rate limit at the Worker. Request/response pattern → TB orientation, dashed return arrows per 0004 § 7.2.

**Diagram B — AI request lifecycle.**
Shows: Lambda Agent → Defense Funnel (guardrails) → Bedrock via AIP → Haiku 4.5 (default). Nova Micro is shown as an alternative model dispatch path. The Opus verifier is NOT a primary node in this diagram — it is a corner-case path that fires when Haiku returns a specific classification, and per operator decision (§ 12) prompt-injection detection is a minor implementation detail with no user value. If shown at all, the verifier is a sidebar note on the Haiku node, not a flagged box. The AIP layer is shown explicitly because that is what enables the `Project:Aletheia` cost tag.

**Diagram C — Lambda topology.**
Shows: four Lambdas — AletheiaAgent, AletheiaAuth, AletheiaKillSwitch, AletheiaHermesPoller — with their IAM roles (AletheiaLambdaRole vs HermesPollerRole), their triggers (Function URLs vs scheduled), and the data they touch (DynamoDB `aletheia-state`, Secrets Manager, SSM Parameter Store, Bedrock).

**Diagram D — Browser extension internals.**
Shows: per-browser flow. Chrome: popup → service worker → `chrome.identity.launchWebAuthFlow` for OAuth. Firefox: popup → service worker → tabs-based OAuth callback flow (both manifests are MV3 but auth UX differs). Content script injection on user activation. Shadow DOM overlay. Per 0004 § 8.1, the two browsers are shown as separate nodes ONLY where their interactions differ (the OAuth path) and collapse to "Extension" elsewhere.

### 5.4 Optional diagrams

- **Diagram E — Cost separation.** AIPs + `Project:Aletheia` tag → cost-allocation tag → CloudWatch deny budget. Only include if there is a wiki page for cost / operations; otherwise it lives in `docs/architecture/*` not the wiki.
- **Diagram F — OAuth sequence.** Sequence diagram of LinkedIn OAuth across the Worker, AletheiaAuth, and the extension. Worth doing if the OAuth flow is a frequently-asked interview topic (see § 7).

### 5.5 Diagram authoring rules (Aletheia-specific, on top of 0004)

- No PNG/SVG screenshots — they rot silently when the architecture changes and no one notices.
- Every node label is the canonical name from the code: `AletheiaAgent` not "Main Lambda"; `aletheia-api` not "Edge Worker"; `Haiku 4.5` not "Claude Haiku".
- Every diagram has a one-paragraph caption underneath naming what it shows AND what it deliberately does NOT show, to deflect the "but where is X?" follow-up.

---

## 6. Information architecture refactor (Outcome B — operator decision)

Per operator decision 2026-06-04 (§ 12), the refresh is a **full refactor of the wiki**, not refresh-in-place. The wiki is reorganized by reader audience; pages are renamed, split, or merged where current structure does not serve a reader.

### 6.1 The four reader audiences

| Audience | Reads to | Pages |
|---|---|---|
| **End users** | Install, use, get unstuck | `Home`, `Getting-Started`, `User-Guide`, `FAQ` |
| **Developers** | Build, run, deploy, contribute | `Architecture`, `API-Reference`, `Developer-Guide`, `Contributing` |
| **Reviewers / auditors** | Verify privacy, security, legal posture | `Security`, `Privacy`, `Terms-of-Use` |
| **Concept-seekers** | Understand the interesting parts at high altitude (incl. interview prep) | `Concepts` (new), `Architecture` (shared with developers) |

The sidebar is rebuilt around these four groups. Today's sidebar groups by topic (which loosely tracks audience but does not name it); the refactored sidebar names the audience and groups under it.

### 6.2 Sidebar structure

```
For users
  Home
  Getting Started
  User Guide
  FAQ

For developers
  Architecture
  API Reference
  Developer Guide
  Contributing

For reviewers
  Security
  Privacy
  Terms of Use

Concepts
  Concepts (single page; see § 7)
```

Wiki convention is one flat sidebar with H2 group headers. `_Sidebar.md` is rebuilt accordingly; no functional change to GitHub wiki rendering.

### 6.3 Page-level restructuring

Most existing pages keep their names. The audit identifies which pages need internal restructuring (not just content refresh) — likely candidates based on current content:

- **`Architecture.md`** — gains inline Diagrams A, B, C, D per § 5.3. Page grows substantially. Internal structure shifts from "one diagram + components table + ADR list" to "diagram set + per-component depth + ADR list." Stays one page per operator decision (§ 12).
- **`API-Reference.md`** — restructured into sections by audience: public endpoints (POST /, /health), authenticated endpoints (/auth/*, /my-data, /subscription-status), admin endpoints (/admin/*), webhooks (/stripe-webhook). Today's "REST API via CloudFront" framing is replaced by an honest endpoint inventory grouped by routing prefix.
- **`Developer-Guide.md`** — at 225 lines, today's biggest page. Audit evaluates whether to split into Local-Development + Deployment, or keep as one with better section headers. Default is keep as one unless audit finds a strong split signal.
- **`Security.md`, `Privacy.md`** — content refresh per § 4.1 seeds, no structural change. These pages are already focused.
- **Other pages** — content refresh per audit; structural changes only if audit surfaces a specific reason.

Page renames are avoided where possible (link breakage on existing search results). If a rename is needed, the audit names it as a finding so it gets its own follow-up issue.

### 6.4 New pages the refresh adds

One: `Concepts.md` (§ 7). One page, additive.

The refresh does NOT add a `Deploy.md` / `Operations.md` page — those concepts belong in runbooks under `docs/runbooks/10xxx-*` in the repo, not in the wiki. The wiki is for stable conceptual material that does not change every release. Operational procedures change every release.

### 6.5 Pages the refresh removes

None. Every existing page has a clear reader and a clear function. Removal is link breakage with no payoff.

---

## 7. Technical concepts index proposal

### 7.1 Why

The operator interviews. Interviewers ask "tell me about the model-routing decision" or "why did you use a verifier instead of a better classifier" or "why CloudFlare Worker and not API Gateway." Today the wiki has no single page that answers those questions at the right altitude — the operator either has to skim multiple wiki pages mid-conversation or rely on memory.

A technical concepts index gives the operator a single page where every "explain this in 30 seconds" topic has a one-paragraph answer and a pointer into the deeper material.

It also serves a second audience: an engineer reading the wiki for the first time who wants to understand the *interesting* parts of the system before diving into architecture or code. Without an index, that engineer skims everything and remembers nothing.

### 7.2 Page shape

**Title:** `Concepts.md` (short, sidebar-friendly). Subtitle: "Aletheia's technical concepts — what they are, why they were chosen, where to read more."

**Structure:** Five sections, grouping concepts by domain. Each concept is an `### Heading` followed by:
- **What it is** — one sentence.
- **Why we did it this way** — one short paragraph (the trade-off, the decision).
- **In the wiki** — links to the wiki page(s) where it is documented in depth.
- **In the code** — `path/to/file.py:line` pointers (one or two; not exhaustive).

That is it. No mermaid on this page (the deep pages have the diagrams). No exhaustive lists. The discipline is one paragraph per concept.

### 7.3 Proposed concept list

These are the concepts the refresh should seed the page with. The auditor adds, removes, or merges as warranted; this is a draft list, not a final list.

**Architecture & Infrastructure**

- Bedrock Application Inference Profiles (AIPs) and why they enable cost separation
- Four-Lambda topology (Agent / Auth / KillSwitch / HermesPoller) and per-Lambda IAM
- CloudFlare Worker as the edge layer (vs API Gateway) — Host rewrite, shared-secret injection, edge rate limit
- Lambda Function URLs (vs API Gateway) and why
- DynamoDB `aletheia-state` schema posture (no PII, TTL-based retention)
- Cost separation via `Project:Aletheia` tag and the $25 CloudWatch deny budget

**AI / ML**

- Tiered model routing (Haiku 4.5 default; Nova Micro as an alternative dispatch). The Opus verifier is mentioned in this entry as a brief implementation note, not as its own concept — per operator decision (§ 12) the Opus verifier / prompt-injection detection is a minor implementation detail with no user value, and does not warrant a flagship Concepts entry.
- Defense funnel (`src/guardrails/`) — what each layer does at a high level. Defense-against-injection is one item among many; the entry should not over-index on it.
- Signal / gem response shape — what the response conveys and why it is shaped that way (the readable-at-a-glance educational gem is the product, not the underlying classification)
- Digital Etymologist as a product concept — the etymology framing predates the privacy-first context-analyzer positioning but is still valid (operator decision § 12). Concepts entry covers what "Digital Etymologist" means as a product idea and how it relates to the technical model dispatch
- The Bedrock model dispatch (`is_nova_model`) — supporting Nova alongside Anthropic models from the same code path

**Browser Extension**

- Manifest V3 service worker model (Chrome and Firefox)
- LinkedIn OAuth — Chrome `chrome.identity.launchWebAuthFlow` vs Firefox tabs-based flow
- Content-script injection on user activation only
- Shadow DOM overlay (style isolation)
- Cross-browser parity via `tools/build_release.py`

**Operations**

- The kill-switch Lambda (AletheiaKillSwitch) — what triggers it
- Audit-log hashing for GDPR (in flight, #711)
- CloudWatch alarm-driven budget cap
- Provisioning via `provision.sh` (not CDK / not Terraform — why)
- Store publishing workflow (CWS + AMO version parity)

**Privacy & Security**

- PolyForm Noncommercial 1.0.0 — why not MIT
- "We do not enumerate" data posture (vs "we cannot see browsing history")
- Shared-secret pattern (Worker → Lambda) and rotation story
- Per-extension permission justifications and the activeTab model
- No third-party analytics / tracking

That seeds approximately 25 entries. Each entry is one paragraph of explanation plus pointers — likely 4 to 7 lines of markdown each. Estimated page size: 250 to 400 lines, dense but scannable, sorted within each section by importance to the interview use case.

### 7.4 Maintenance discipline

The concepts page rots faster than any other page because it is the densest in claims. The plan recommends:

- Each entry has an "In the code: `path:line`" link. When the linked code moves, the entry is updated.
- A recurring `/audit` task validates that every `path:line` link still resolves.
- New ADRs (`docs/adrs/102xx-*`) added in the repo trigger a one-paragraph addition to the concepts page if the ADR introduces a concept that did not exist before.
- The page does NOT track changelog-style updates (no "as of 2026-05" timestamps per concept). The git history of the wiki repo is the changelog.

### 7.5 What this page does NOT replace

The concepts page is a high-altitude index. It does NOT replace:

- `Architecture.md` (deeper component-by-component reference)
- `API-Reference.md` (endpoint-by-endpoint reference)
- `Security.md` (threat model)
- `Privacy.md` (legal-grade disclosure)
- Runbooks in the repo (`docs/runbooks/10xxx-*`)

The concepts page POINTS to those. It does not duplicate them.

---

## 8. Existing `10817-audit-wiki-alignment.md` — disposition

10817 is a generic recurring checklist (run monthly, run after feature changes). It is useful for the steady-state but it cannot generate a one-time refresh plan from first principles — that is why this plan (10833) exists.

The plan recommends:

1. **Do not deprecate 10817.** It stays as the recurring checklist after the refresh lands.
2. **Update 10817's § 1 (Purpose) to point at 10833** for one-time refreshes when significant drift has accumulated, so future operators do not duplicate the work.
3. After this refresh ships, 10817's checklist becomes more meaningful (the checked-off boxes mean something because the baseline is current).

These are recommendations; they are out of scope for THIS PR. They become follow-up issues per § 9.

---

## 9. Follow-up issues to file

Each refresh task is its own issue per `One Issue Per Concern`. Bundling is forbidden. Below is the proposed issue list. The audit report (the deliverable that uses this plan) will add or split as findings warrant.

Issues F2 through F9 are filed only after F1 (the audit report) lands, because the audit report's findings — including its per-page time-to-refresh estimates per § 12 decision — define each follow-up's exact scope. Issues F10, F11, F13 can be filed concurrently with F1 because their scope is set by this plan.

| # | Title | Scope |
|---|---|---|
| F1 | `docs(wiki): audit report against the code per #739 plan` | The audit findings report itself, produced by applying § 3 + § 4. Lives in `docs/audits/108xx-wiki-audit-report-2026-06.md`. Includes per-page estimated time-to-refresh (operator decision § 12). Does NOT touch the wiki. |
| F2 | `docs(wiki): refresh Home.md — stack table, status, license` | All Home.md drift fixes. PR against `Aletheia.wiki`. Product framing ("Digital Etymologist") is kept per operator decision (§ 12); not relitigated here. |
| F3 | `docs(wiki): refresh Architecture.md — mermaid, components, ADR table` | All Architecture.md drift fixes; replaces the stale mermaid with all four inline diagrams (A, B, C, D) per § 5.3 and operator decision (§ 12). |
| F4 | `docs(wiki): refresh Security.md — controls, third-party services, defense layers` | All Security.md drift fixes. Surfaces the kill switch and CloudFlare-Worker edge controls as defense layers. The Opus verifier / prompt-injection detection is NOT surfaced as a flagship defense layer per operator decision (§ 12) — mention it only factually if the page enumerates the defense funnel. |
| F5 | `docs(wiki): refresh API-Reference.md — base URL, endpoints, auth, /health` | All API-Reference.md drift fixes; full endpoint inventory from `workers/aletheia-api/worker.js`. Restructured into sections by routing prefix per § 6.3. |
| F6 | `docs(wiki): refresh Privacy.md — data retention, anonymization, hashing roadmap` | All Privacy.md drift; reflect #711 plan. |
| F7 | `docs(wiki): refresh Developer-Guide.md — local dev, deploy, smoke test` | All Developer-Guide.md drift; align with `provision.sh`. Internal structure: see § 6.3 (split vs single-page is an audit-report finding). |
| F8 | `docs(wiki): refresh Getting-Started.md, User-Guide.md, FAQ.md, Terms-of-Use.md, Contributing.md` | Lower-density pages; if drift per page warrants splitting, split. |
| F9 | `docs(wiki): restructure _Sidebar.md by reader audience (Outcome B)` | Per § 6.2 — rebuild sidebar into four groups (Users, Developers, Reviewers, Concepts). Update `_Footer.md` if needed. Verify all internal links. |
| F10 | `docs(wiki): add Concepts.md — technical concepts index (§ 7)` | New page per § 7. Seed concept list per § 7.3; iterate. |
| F13 | `docs(audits): update 10817-audit-wiki-alignment.md § 1 to point at 10833 for one-time refreshes` | Repo-side; not a wiki change. |

(F11 and F12 from the original plan are absorbed into F3 — operator decided all four diagrams live inline in `Architecture.md`, not in separate pages.)

The plan does NOT pre-file these issues. Pre-filing placeholder issues clutters the issue tracker. They are filed at the moment they become actionable.

---

## 10. Definition of done (for the plan)

- This document exists at `docs/audits/10833-wiki-audit-and-refresh-plan.md`.
- All six sections promised in #739 are present: methodology (§ 3), known drift (§ 4.1), IA approach (§ 6), mermaid refresh (§ 5), concepts index proposal (§ 7), follow-up issue list (§ 9).
- The audit philosophy in § 3.1 is consistent with `docs/audits/10800-audit-index.md` § 2.1.
- All five open questions from the original plan are resolved with operator decisions documented in § 12.
- The follow-up issue list (§ 9) is granular enough to satisfy `One Issue Per Concern` — no issue bundles two unrelated wiki pages, no issue bundles a wiki page with a repo change.
- F1 (audit report) and F10 (Concepts.md) can be filed as soon as the operator wants to start; their scope is fully set by this plan.

---

## 11. Residual risks

- **Risk: the audit produces too much drift to land in one cycle.** Mitigation: the issue list (§ 9) is already split per page so PRs are mergeable independently; nothing forces them to land together. Worst case is partial refresh and a second audit a few months later.
- **Risk: the Concepts page becomes a maintenance burden and rots faster than the rest of the wiki.** Mitigation: § 7.4 maintenance rules. If those rules feel too heavy, the page is too long — trim, do not abandon.
- **Risk: the IA refactor (Outcome B) breaks external search-engine deep links into renamed/restructured pages.** Mitigation: § 6.3 keeps page names stable wherever possible; only splits or renames a page if the audit surfaces a concrete reason; each such split/rename gets its own follow-up issue so the link breakage is visible at PR review.
- **Risk: the AZ 0004 mermaid auto-inspection step (§ 5.1, § 8.5 of 0004) is treated as optional under time pressure.** Mitigation: § 5.1 names it as REQUIRED, not advisory; an unrendered diagram is the wrong unit of completion.

---

## 12. Decisions made (operator, 2026-06-04)

The original plan posed five open questions in § 12. All five are now resolved.

| # | Question | Operator decision |
|---|---|---|
| 1 | Refresh in place (Outcome A) or full IA refactor (Outcome B)? | **Outcome B** — full refactor of the wiki. Restructure by reader audience per § 6.1. |
| 2 | Product framing — keep "Digital Etymologist" or migrate fully to "privacy-first context analyzer"? | **Keep "Digital Etymologist"** as a product concept. It is a valid framing, not drift. Concepts page entry covers what it means. Refresh does not relitigate. |
| 3 | Concepts page name — `Concepts`, `Technical-Concepts`, `Stack`, `Reference`, or other? | **`Concepts.md`** (verbatim "fine" on the recommendation). |
| 4 | F1 audit report — findings only, or include time-to-refresh estimates per page? | **Include estimates.** Operator framing: "I don't care how hard you work. I want you to do the work." Estimates exist to schedule PRs, not to justify scope cuts. |
| 5 | Diagrams B + D — inline in `Architecture.md` or split into separate pages? | **Inline.** All four diagrams live in `Architecture.md`. |

Two further operator directives recorded the same conversation:

- **Prompt-injection detection / Opus verifier is a very minor implementation detail with no user value.** Removed from `Concepts.md` as a flagship entry (§ 7.3). Not surfaced as a defense layer headline in `Security.md` (F4). Not flagged in Diagram B (§ 5.3). Mentioned factually where the page enumerates internals; never as a flagship feature.
- **Mermaid diagrams follow AssemblyZero `docs/standards/0004-mermaid-diagrams.md` verbatim.** Adopted as § 5.1. Includes the agent auto-inspection procedure via `mermaid.ink` (0004 § 8.5) and the Playwright-based GitHub-render verification (0004 § 8.7). Non-negotiable.

---

*Plan author: PR #740 (original) and PR for #741 (revision). Plan execution: future PRs per § 9. Plan validity: until the wiki is refreshed; this document becomes a historical record after F1 ships.*

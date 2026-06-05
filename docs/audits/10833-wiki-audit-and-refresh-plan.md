# 10833 — Wiki Audit + Refresh Plan

> **Issue:** #739
> **Status:** Draft (plan only; execution is out of scope for this PR)
> **Authored:** 2026-06-04
> **Scope:** `https://github.com/martymcenroe/Aletheia.wiki` only. The repo itself, the marketing site, the store listings, and the runbooks are out of scope.
> **Supersedes:** Nothing. Complements `docs/audits/10817-audit-wiki-alignment.md` (the recurring checklist). This document is the project-specific, one-time refresh plan that 10817 cannot generate from first principles.

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

The operator also needs the wiki to function as an interview reference. Today there is no single page that maps technical concepts (model routing, edge architecture, the Opus verifier pattern, four-Lambda topology, OAuth flow, cost tagging) to one-paragraph explanations and pointers into the wiki. Engineers and hiring managers ask about these concepts; the answer should not require the operator to skim 1,542 lines of wiki text mid-conversation.

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
4. **List missing concepts.** A page is incomplete if a reader following its TOC could not learn things the page is positioned to teach (e.g. `Security.md` says nothing about the Opus verifier, the kill-switch Lambda, or the audit-log hashing PRs).
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
- Missing: Opus verifier as a defense layer; kill-switch Lambda; per-Lambda IAM separation (HermesPollerRole vs AletheiaLambdaRole); shared-secret pattern (`X-Origin-Secret` header injected by Worker, SSM `/aletheia/cloudflare-origin-secret`); CloudWatch deny budget gate (#535).

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

### 5.1 Existing diagrams

Currently the wiki has one mermaid diagram (`Architecture.md:9-29`). It depicts: Browser Extension → CloudFront+WAF → Lambda → Bedrock (Nova Micro) + DynamoDB. As § 4.1 records, this is wrong on at least four nodes.

### 5.2 Diagrams the refresh should produce

The plan recommends the refreshed wiki carry four diagrams, not one. Each lives on its most relevant page; cross-link from the others.

**Diagram A — Edge & request routing (`Architecture.md` or new `Request-Flow.md`).**
Shows: Browser → CloudFlare DNS (`api.aletheia.study`) → CloudFlare Worker (`aletheia-api`) → either AletheiaAgent Lambda Function URL (POST /, analysis) or AletheiaAuth Lambda Function URL (`/auth/*`, `/admin/*`, `/metrics`, `/my-data`, `/redeem-coupon`, `/upgrade-*`, `/create-checkout-session`, `/stripe-webhook`, `/subscription-status`). Annotates the `X-Origin-Secret` header injection and the 3 req / 10 s / IP rate limit at the Worker.

**Diagram B — AI request lifecycle (`Architecture.md` or new `AI-Pipeline.md`).**
Shows: Lambda Agent → Defense Funnel (guardrails) → Bedrock via AIP → Haiku 4.5 (default) → if Haiku flags "Prompt Injection Attempt" then re-classify via Opus 4.6 verifier; Nova Micro available as alternative. Captures the AIP layer explicitly because that is what enables the `Project:Aletheia` cost tag.

**Diagram C — Lambda topology (`Architecture.md`).**
Shows: four Lambdas — AletheiaAgent, AletheiaAuth, AletheiaKillSwitch, AletheiaHermesPoller — with their IAM roles (AletheiaLambdaRole vs HermesPollerRole), their triggers (Function URLs vs scheduled), and the data they touch (DynamoDB `aletheia-state`, Secrets Manager, SSM Parameter Store, Bedrock).

**Diagram D — Browser extension internals (`Architecture.md` or new `Extension-Internals.md`).**
Shows: per-browser flow. Chrome: popup → service worker → `chrome.identity.launchWebAuthFlow` for OAuth. Firefox: popup → service worker → tabs-based OAuth callback flow (the manifest is MV3 but auth UX differs). Content script injection on user activation. Shadow DOM overlay.

### 5.3 Optional diagrams

- **Diagram E — Cost separation.** AIPs + `Project:Aletheia` tag → cost-allocation tag → CloudWatch deny budget. Only include if there is a wiki page for cost / operations; otherwise it lives in `docs/architecture/*` not the wiki.
- **Diagram F — OAuth sequence.** Sequence diagram of LinkedIn OAuth across the Worker, AletheiaAuth, and the extension. Worth doing if the OAuth flow is a frequently-asked interview topic (see § 7).

### 5.4 Diagram authoring rules

- All mermaid. No PNG/SVG screenshots — they rot silently when the architecture changes and no one notices.
- Every node label is the canonical name from the code: `AletheiaAgent` not "Main Lambda"; `aletheia-api` not "Edge Worker"; `Haiku 4.5` not "Claude Haiku".
- Every diagram has a one-paragraph caption underneath naming what it shows AND what it deliberately does NOT show, to deflect the "but where is X?" follow-up.
- TD (top-down) layout where the request flow is vertical; LR (left-right) only when the flow naturally reads horizontally.

---

## 6. Information architecture analysis

### 6.1 Question the audit must answer

Does the current 11-page structure (excluding `_Sidebar`, `_Footer`) serve a reader?

The audit recommendation should answer this directly. The plan presents two reasonable IA outcomes; the audit picks one (or argues for a third).

**Outcome A — keep current pages, refresh in place.** Low risk, low IA cost. Refresh each page; do not reshape. The reader navigates the same way they do now. The wiki feels familiar. Downside: misses the chance to fix structural problems (e.g. Architecture.md is currently doing the work that Architecture + AI-Pipeline + Request-Flow should split).

**Outcome B — refactor for the four readers.** The wiki actually has four distinct readers: end users (User-Guide, FAQ, Getting-Started), developers (Developer-Guide, API-Reference, Contributing), reviewers / auditors (Privacy, Security, Terms-of-Use), and concept-seekers (Architecture + the proposed Concepts page from § 7). Refactor reorganizes the sidebar by reader, not by topic, and moves pages to fit. Higher risk (link breakage on existing google results), higher payoff.

The plan recommends **Outcome A for this refresh** because: (a) the operator's stated drivers are accuracy + interview reference, not IA; (b) the existing sidebar groups by topic already, which is a reasonable IA; (c) any IA churn during a refresh dilutes the accuracy work the operator actually asked for. The plan also recommends scheduling Outcome B as a SEPARATE later effort, if the operator decides it is worth the link breakage.

### 6.2 New pages the refresh should add

Outcome A still adds one new page: the technical concepts index (§ 7). One page, additive, no link breakage.

The plan recommends NOT adding a `Deploy.md` / `Operations.md` page — those concepts belong in runbooks under `docs/runbooks/10xxx-*` in the repo, not in the wiki. The wiki is for stable conceptual material that does not change every release. Operational procedures change every release.

### 6.3 Pages the refresh should remove

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

- Tiered model routing (Haiku default + Opus verifier)
- Bedrock Application Inference Profiles (AIPs) and why they enable cost separation
- Four-Lambda topology (Agent / Auth / KillSwitch / HermesPoller) and per-Lambda IAM
- CloudFlare Worker as the edge layer (vs API Gateway) — Host rewrite, shared-secret injection, edge rate limit
- Lambda Function URLs (vs API Gateway) and why
- DynamoDB `aletheia-state` schema posture (no PII, TTL-based retention)
- Cost separation via `Project:Aletheia` tag and the $25 CloudWatch deny budget

**AI / ML**

- The Opus verifier pattern (cost vs precision trade-off; #623)
- Defense funnel (`src/guardrails/`) — what each layer does
- Signal / gem response shape and what each conveys
- Prompt-injection detection vs prompt-injection prevention
- The Bedrock model dispatch (`is_nova_model`) — supporting Nova alongside Anthropic models

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

| # | Title | Scope |
|---|---|---|
| F1 | `docs(wiki): audit report against the code per #739 plan` | The audit findings report itself, produced by applying § 3 + § 4. Lives in `docs/audits/108xx-wiki-audit-report-2026-06.md`. Does NOT touch the wiki. |
| F2 | `docs(wiki): refresh Home.md — stack table, status, license, framing` | All Home.md drift fixes. PR against `Aletheia.wiki`. |
| F3 | `docs(wiki): refresh Architecture.md — mermaid, components, ADR table` | All Architecture.md drift fixes; replaces the stale mermaid with Diagrams A + C. |
| F4 | `docs(wiki): refresh Security.md — controls, third-party services, defense layers` | All Security.md drift fixes; surfaces Opus verifier and kill switch as defense layers. |
| F5 | `docs(wiki): refresh API-Reference.md — base URL, endpoints, auth, /health` | All API-Reference.md drift fixes; full endpoint inventory from `workers/aletheia-api/worker.js`. |
| F6 | `docs(wiki): refresh Privacy.md — data retention, anonymization, hashing roadmap` | All Privacy.md drift; reflect #711 plan. |
| F7 | `docs(wiki): refresh Developer-Guide.md — local dev, deploy, smoke test` | All Developer-Guide.md drift; align with `provision.sh`. |
| F8 | `docs(wiki): refresh Getting-Started.md, User-Guide.md, FAQ.md, Terms-of-Use.md, Contributing.md` | Lower-density pages; if drift per page warrants splitting, split. |
| F9 | `docs(wiki): refresh _Sidebar.md and _Footer.md` | Add Concepts page link; verify all internal links. |
| F10 | `docs(wiki): add Concepts.md — technical concepts index (§ 7)` | New page per § 7. Initial seed of ~25 concepts; iterate. |
| F11 | `docs(wiki): add AI-Pipeline diagram (Diagram B)` | Either inline in Architecture.md or new page, per audit recommendation. |
| F12 | `docs(wiki): add Extension-Internals diagram (Diagram D)` | Either inline in Architecture.md or new page, per audit recommendation. |
| F13 | `docs(audits): update 10817-audit-wiki-alignment.md § 1 to point at 10833 for one-time refreshes` | Repo-side; not a wiki change. |

Issues F2 through F9 are filed only after F1 (the audit report) lands, because the audit report's findings define their exact scope. Issues F10, F11, F12, F13 can be filed concurrently with F1 because their scope is set by this plan.

The plan does NOT pre-file these issues. Pre-filing 12 placeholder issues clutters the issue tracker. They are filed at the moment they become actionable.

---

## 10. Definition of done (for #739, the plan)

- This document exists at `docs/audits/10833-wiki-audit-and-refresh-plan.md`.
- All six sections promised in #739 are present: methodology (§ 3), known drift (§ 4.1), IA analysis (§ 6), mermaid refresh (§ 5), concepts index proposal (§ 7), follow-up issue list (§ 9).
- The audit philosophy in § 3.1 is consistent with `docs/audits/10800-audit-index.md` § 2.1.
- The follow-up issue list (§ 9) is granular enough to satisfy `One Issue Per Concern` — no issue bundles two unrelated wiki pages, no issue bundles a wiki page with a repo change.
- The operator has reviewed and approved the plan before any follow-up issue is filed.

---

## 11. Risks & decisions deferred

- **Risk: the audit produces too much drift to land in one cycle.** Mitigation: the issue list (§ 9) is already split per page so PRs are mergeable independently; nothing forces them to land together. Worst case is partial refresh and a second audit a few months later.
- **Risk: the Concepts page becomes a maintenance burden and rots faster than the rest of the wiki.** Mitigation: § 7.4 maintenance rules. If those rules feel too heavy, the page is too long — trim, do not abandon.
- **Risk: the IA refactor (Outcome B in § 6.1) gets revisited mid-refresh and derails it.** Mitigation: this plan recommends Outcome A explicitly to prevent that. If the operator wants Outcome B, file it as a separate effort after the accuracy refresh ships.
- **Decision deferred to operator: product framing.** "Digital Etymologist" vs "privacy-first context analyzer" vs both. The store listings use the latter; `Home.md:5` uses the former. The auditor cannot make this call — it is a positioning decision, not a drift correction. Operator answers before F2 (Home.md refresh) starts.
- **Decision deferred to operator: Concepts page name.** `Concepts.md` is the plan's recommendation. Alternatives: `Technical-Concepts.md`, `Stack.md`, `Concept-Index.md`, `Reference.md`. The chosen name appears in the sidebar; pick before F10 starts.

---

## 12. Open questions for the operator (please answer before F1 starts)

1. Outcome A (refresh in place) or Outcome B (IA refactor)? Plan recommends A.
2. Product framing — keep "Digital Etymologist" anywhere, or fully migrate to the AMO/CWS positioning ("privacy-first context analyzer with prompt-injection detection")?
3. Concepts page name — `Concepts`, `Technical-Concepts`, `Stack`, `Reference`, or other?
4. Should the audit report (F1) include estimated time-to-refresh per page so PRs can be scheduled, or just findings? Plan defaults to findings only.
5. Should diagrams B + D live inline in `Architecture.md` (one long page) or as separate pages (`AI-Pipeline.md`, `Extension-Internals.md`)? Plan defaults to inline; happy to split if the page gets too long.

---

*Plan author: this PR. Plan execution: future PRs per § 9. Plan validity: until the wiki is refreshed; this document becomes a historical record after F1 ships.*

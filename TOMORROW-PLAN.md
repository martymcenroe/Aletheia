# Tomorrow's Plan: Chrome/Firefox Store Submission Readiness

**Created:** 2025-12-29 00:50 CT
**Goal:** Prepare Aletheia for Chrome Web Store and Firefox Add-ons store submission

---

## Executive Summary

**Store submission requires 3 critical paths:**

1. **Core Functionality (#80)** - Wire agent.py to guardrails/compliance (MUST HAVE)
2. **Store Compliance (#51, #53)** - Meet Chrome Web Store requirements (MUST HAVE)
3. **Security Hardening (#95)** - Rate limiting and API protection (MUST HAVE)

**Current State:**
- Extension UI: ✅ Complete (Issue #77 closed, #98 minor positioning bug deferred)
- Backend Logic: ❌ Not wired (#80 blocks everything)
- Store Assets: ❌ Not generated (#53)
- Security: ❌ Vulnerable to DoS (#95 - Lambda concurrency=0 currently)

**Bottom Line:** Cannot submit until #80 is complete. Everything else can happen in parallel.

---

## Phase 1: Critical Blockers (MUST COMPLETE)

### Issue #80 - Wire agent.py to Guardrails and Compliance 🔴 BLOCKER
**Status:** Bug (mislabeled - actually core feature implementation)
**Priority:** CRITICAL - Nothing works without this
**LLD:** `docs/1080-wire-agent-logic.md` (production-ready, reviewed by Opus)

**What it does:**
- Connects browser extension → Lambda → Bedrock
- Implements guardrails_node (3-layer content filtering)
- Implements summarizer_node (compliance checking + summarization)
- Implements routing logic (should_continue)

**Dependencies:** None - this IS the foundation
**Blocks:** #25 (auth), #44 (warning UI), #45 (hate filter), #14 (compliance)

**Deliverables:**
1. Implement guardrails_node in agent.py
2. Implement summarizer_node in agent.py
3. Implement should_continue routing
4. Update lambda_function.py to use new graph
5. Test end-to-end: extension → Lambda → Bedrock → response

**Time Estimate:** 1-2 days (LLD complete, code ready to write)

---

### Issue #95 - Security Hardening & Rate Limiting 🔴 BLOCKER
**Status:** High-priority, security
**Why Critical:** Currently vulnerable to "Denial of Wallet" attacks

**What it needs:**
1. AWS WAF with rate limiting rules
2. API key requirement (prevent anonymous abuse)
3. Per-user quotas
4. Cost monitoring alerts

**Dependencies:** None (infrastructure work)
**Blocks:** Production deployment (current Lambda set to concurrency=0 for safety)

**Recommendation:** Start in parallel with #80

---

### Issue #51 - Chrome Web Store Compliance 🟡 REQUIRED
**Status:** High-priority, chore
**LLD:** `docs/1051-store-compliance.md` (Beta status)

**What it needs:**
1. Privacy policy page (required by Chrome)
2. Store listing description
3. Compliance verification checklist
4. Permission justification documentation

**Dependencies:** #53 (store assets)
**Blocks:** Submission

**Recommendation:** Can start now (mostly documentation)

---

### Issue #53 - Generate Store Assets 🟡 REQUIRED
**Status:** Chore
**Tool:** `tools/generate_store_assets.py` (placeholder)

**What it needs:**
1. Screenshots (1280x800 or 640x400)
2. Promotional images (440x280 small tile, 920x680 marquee, 1400x560 large)
3. Icon (already have: 128x128 lambda icon)
4. Video demo (optional but recommended)

**Dependencies:** #77 (complete ✅)
**Blocks:** #51 (store compliance)

**Recommendation:** Start now (UI is ready to screenshot)

---

## Phase 2: Firefox Compatibility (SHOULD HAVE)

### Issue #100 - Firefox Compatibility 🟢 ENHANCEMENT
**Status:** Enhancement
**What it needs:** Single-line manifest.json fix + cross-browser testing

**Dependencies:** #77 (complete ✅)
**Time Estimate:** 1-2 hours

**Recommendation:** Do after #80 but before final submission

---

## Phase 3: Quality & Polish (NICE TO HAVE)

### Issue #98 - Overlay Positioning Bug 🟢 DEFERRED
**Status:** Bug (minor - overlay appears below selection instead of above at viewport bottom)
**Fix Location:** service-worker.js line 30 (not overlay.js - that's dead code)

**Recommendation:** Defer until after store submission (not blocking)

---

### Issue #99 - Automated Testing Framework 🟢 FUTURE
**Status:** Enhancement, testing
**What:** Playwright + TypeScript for automated browser extension tests

**Recommendation:** Defer until after store submission (test manually for now)

---

### Issue #103 - Log Document Formatting Standards 🟢 FUTURE
**Status:** Documentation, enhancement
**What:** Standards to prevent print overflow in docs

**Recommendation:** Defer (printing infrastructure works, standards can evolve)

---

## Phase 4: Backlog (DEFER)

**These are important but NOT required for store submission:**

| Issue | Title | Why Deferred |
|-------|-------|--------------|
| #102 | Repository reorganization | Tooling/aesthetics, not functionality |
| #94 | XSS test harness | Already manually verified in #77 |
| #88 | LinkedIn OAuth rewrite | #25 needs design decision first |
| #85 | Rename Compliance→Summarization | Refactoring, not new functionality |
| #84 | Signal Inspector CLI | Debugging tool, not user-facing |
| #81 | Landing page redesign | Marketing, not core functionality |
| #79 | Firing Range test page | Testing infrastructure (nice to have) |
| #58 | SonarQube/SonarLint | Code quality tooling (defer) |
| #25 | LinkedIn auth gate | Needs #80 first, then design decision |
| #45 | Hate speech filter | Layer 2 guardrail (not in MVP scope) |
| #44 | Warning UI | Needs #80 first to know what to warn about |
| #14 | Compliance engine | Already implemented in summarizer_node (#80) |
| #7 | Observability tracing | Post-launch enhancement |
| #6 | RAG Vector Store | Not needed for MVP |
| #5 | Graph node unit tests | Good practice but not blocking |

---

## Recommended Workflow: How We Work Together

### **Model Selection Strategy**

**For Issue #80 (Critical Implementation):**
- **Planning:** Use me (Claude Sonnet 4.5 via Claude Code) to review LLD, ask clarifying questions
- **Implementation:** Use me OR Gemini Pro (both capable of Python/LangGraph)
- **Testing:** Use me for test script generation, user runs tests
- **Review:** Use Claude Opus 4.5 for final security review before deployment

**For Issues #51, #53 (Documentation/Assets):**
- **Planning:** Use me to outline requirements
- **Execution:** Any model (Sonnet, Gemini, ChatGPT)
- **Review:** User review (these are user-facing materials)

**For Issue #95 (AWS Infrastructure):**
- **Planning:** Use me to design WAF rules and architecture
- **Implementation:** Any model capable of AWS CLI/CloudFormation
- **Testing:** User tests with manual DoS simulation
- **Review:** Security review recommended

### **Parallel Work Approach**

**You can run multiple sessions simultaneously using git worktrees:**

1. **Main worktree (Aletheia/)** - Work on #80 with one agent
2. **Second worktree (Aletheia-95/)** - Work on #95 security with another agent
3. **Third worktree (Aletheia-51/)** - Work on store compliance docs

**Key Rules:**
- Each worktree has its own branch
- Use `git worktree list` to see active worktrees
- Coordinate merges via PRs (don't merge directly to main)
- See `docs/0008-orchestrator-instructions.md` Section 6 for worktree workflow

### **Daily Workflow Recommendation**

**Morning (High Focus):**
- Work on #80 implementation with a single agent
- Use 2-3 hour focused sessions
- Test each component as you build it

**Afternoon (Parallelizable Work):**
- Launch multiple agents for #51, #53, #95
- Review morning's #80 work
- User testing of completed components

**Evening (Planning/Review):**
- Review all PRs from the day
- Update session logs
- Plan next day's priorities

### **Testing Strategy**

**For Issue #80:**
1. **Unit tests** - Test each node independently
2. **Integration tests** - Test graph flow end-to-end
3. **Manual smoke tests** - User tests extension → Lambda → response
4. **Edge cases** - Test guardrail blocking, compliance failures

**Important:** DO NOT close #80 until user testing complete (per Section 6.5 of coding standards)

### **Communication Protocol**

**When working with me (Claude via Claude Code):**
- I can see full conversation history
- I have access to all project files
- I can execute commands, tests, and deployments
- Use me for: code implementation, testing, debugging, git operations

**When you need to switch agents:**
- Update session log before switching
- New agent reads session log to get context
- Use `CLAUDE.md`, `GEMINI.md`, or `CHATGPT.md` for agent onboarding

**When you need approval:**
- I'll ask before: closing issues, creating PRs, destructive operations
- You can say "go ahead" to unblock me if I'm being too cautious
- I'll pause on errors and wait for guidance

---

## Dependency Graph

```
Store Submission
├── #80 (Wire agent.py) ← CRITICAL PATH
│   ├── Blocks: #25, #44, #45, #14
│   └── No dependencies
├── #95 (Security/Rate Limiting) ← CRITICAL PATH
│   └── No dependencies (can run in parallel with #80)
├── #51 (Store Compliance)
│   ├── Depends on: #53
│   └── Can start now (documentation)
└── #53 (Store Assets)
    ├── Depends on: #77 (complete ✅)
    └── Can start now (UI ready)

Optional:
├── #100 (Firefox)
│   ├── Depends on: #77 (complete ✅)
│   └── Recommended before submission
└── #98, #99, #103, etc.
    └── Defer until after submission
```

---

## Critical Path Timeline

**Day 1 (Tomorrow):**
- ✅ Morning: Start #80 implementation (guardrails_node)
- ✅ Afternoon: Continue #80 (summarizer_node)
- ✅ Evening: Launch parallel work on #95 (security) and #53 (assets)

**Day 2:**
- ✅ Morning: Complete #80 (routing logic, integration)
- ✅ Afternoon: Test #80 end-to-end, fix bugs
- ✅ Evening: #51 compliance documentation, #95 WAF deployment

**Day 3:**
- ✅ Morning: Final #80 testing, user smoke tests
- ✅ Afternoon: #100 Firefox compatibility
- ✅ Evening: Final review, prepare submission package

**Day 4:**
- ✅ Submit to Chrome Web Store
- ✅ Submit to Firefox Add-ons

**Contingency:** If #80 takes longer, everything else waits. That's okay - better to get it right.

---

## Success Criteria for Store Submission

**Chrome Web Store Requirements:**
- [ ] Extension functions end-to-end (#80)
- [ ] Privacy policy page live (#51)
- [ ] Store assets generated (#53)
- [ ] Permission justifications documented (#51)
- [ ] Security hardening in place (#95)
- [ ] No known critical bugs
- [ ] Manual testing complete

**Firefox Add-ons Requirements:**
- [ ] All Chrome requirements met
- [ ] Firefox manifest compatibility (#100)
- [ ] Tested in Firefox browser
- [ ] Add-ons listing prepared

**Definition of Done:**
- User can install extension
- User can select text and click "Explain with AI"
- Backend processes request through guardrails
- Backend returns safe, compliant summary
- User sees result in extension
- No crashes, no errors, no security vulnerabilities

---

## Questions to Answer Tomorrow Morning

1. **Do you want to tackle #80 yourself or should I implement it?**
   - If me: I'll create branch, implement, test, create PR
   - If you: I'll provide guidance and review

2. **Which model should implement #80?**
   - Option A: Me (Claude Sonnet 4.5 via Claude Code) - I know the codebase well
   - Option B: Gemini Pro - Has written the LLD, familiar with design
   - Option C: Pair programming - Gemini writes, I review

3. **Do you want to run parallel sessions for #95 and #53?**
   - If yes: Set up worktrees for Aletheia-95 and Aletheia-53
   - If no: Do them sequentially after #80

4. **What's your target submission date?**
   - This affects how aggressive we are with testing vs speed
   - Recommendation: Don't rush - better to launch solid in 1 week than broken in 3 days

5. **Do you want Firefox support in the first submission?**
   - If yes: Add #100 to critical path
   - If no: Submit Chrome first, Firefox later (less risky)

---

## Final Recommendation

**Start here tomorrow:**

1. **Read this plan** (you're doing it now!)
2. **Review `docs/1080-wire-agent-logic.md`** (the #80 LLD)
3. **Decide on workflow** (answer the 5 questions above)
4. **Create branch for #80:** `git checkout -b 80-wire-agent`
5. **Begin implementation** with focused 2-hour session

**Don't overthink it.** #80 is the only thing that matters for store submission. Everything else is noise until the core works.

You've got this. The infrastructure is solid, the docs are complete, the extension UI works beautifully. Now we just need to wire the brain to the body.

See you tomorrow! 🚀

---

**P.S.** All 40 docs are printed and in the garage. The session log is updated. Everything is committed. You can start fresh tomorrow morning with zero technical debt.

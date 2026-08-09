# Pre-Finalisation Analysis and Prioritised Recommendations

**Date:** 2026-08-10 · **Companion to:** `prd.md`, `../../architecture/core-intelligence-loop.md`
**Purpose:** the contradictions, missing dependencies, unrealistic assumptions, security risks and scope risks you asked to have identified before the PRD is acted on.

Nothing in your specification was silently changed. Everything below is stated as a finding for you to accept or reject.

---

## Part A — Contradictions

### C-1 · The MVP contradicts your own operating principle — and your deadline ⚠️ CRITICAL

Your project brief states: *"do not build everything at once; define architecture and scope first, then implement incrementally."*

Your MVP list (§44 of your spec) contains **26 subsystems**: agent core, memory architecture, goal engine, priority engine, task system, scheduler, notifications, executor, daily planning, dynamic replanning, decision journal, experiments, business dashboard, revenue tracking, permissions, audit log, error handling, web UI, voice, GitHub, filesystem, browser, Telegram, WhatsApp, configuration, secrets.

These cannot both be true. The second is not an MVP — it is the finished product.

**The arithmetic that matters.** Your available build time is Sundays plus fragments of weeknights after client work — call it 8–12 hours a week, optimistically. That list is comfortably a full-time year. At your availability it is **considerably more than the six months you have**.

**So the contradiction is not academic:** building this MVP consumes the entire window in which you want to earn ₹1 crore. The tool competes directly with the goal it exists to serve. If you build all 26 subsystems first, the system goes live at roughly the moment the six months expire, having contributed nothing to them.

### C-2 · Loop shape stated two different ways — resolved

Your first spec: `GOAL → PLAN → PRIORITIZE → EXECUTE → MEASURE → LEARN → REPLAN`. Your second: `GOAL → PRIORITIZE → EXECUTE → MEASURE → LEARN → REPLAN`.

**Resolved, not silently:** planning is the PRIORITIZE → EXECUTE *transition* (your own §4: "once a priority is selected, convert it into an executable plan"). PLAN is a transition, not a stage. Both descriptions agree under that reading. Documented in the architecture spec's opening.

### C-3 · Six memory partitions or eight stores — resolved

First spec: six partitions. Second: eight stores, adding Execution Log and Audit Log.

**Resolved:** six *memory partitions* plus two *append-only logs*, which were already separate concerns in the first spec. Both are satisfied. Documented at §17 of the architecture spec.

### C-4 · "Agent office with employees" vs. "do not create unnecessary autonomous agents"

You asked for an office of employees with Jarvis directing them, and separately warned against unnecessary autonomous agents, preferring a single orchestration layer.

**Resolved as you directed:** the office is a **UX metaphor**. One Agent, many Worker Roles (prompt profile + tool subset). No agent swarm. This is already reflected in both documents.

### C-5 · ₹1 crore appears as both a hard-coded target and a configured goal

Your first spec built the goal engine around ₹1 crore; your second explicitly forbids hard-coding it.

**Resolved in favour of the second.** The PRD has been amended: goals are configuration, the engine is goal-type-agnostic, and the acceptance test is that deleting the ₹1 crore goal leaves a working system.

---

## Part B — Unrealistic assumptions

### U-1 · ₹16.7 lakh/month within six months, from a standing start ⚠️

Your three engines today: Railzy (live, revenue **[OPEN-12]** unknown to me), content (channel size unknown), Naxova (**not formed, no website**).

For context on the content engine specifically: AdSense on travel/lifestyle content in India typically returns on the order of ₹100–₹300 per 1,000 monetised views. Reaching ₹16.7 lakh/month from ads alone implies roughly **50–150 million monetised views per month**. That is top-tier national-creator scale, and it is not reachable in six months from a channel that is currently growing.

**This does not mean the target is wrong.** It means the target is almost certainly not reachable *through ads and early product revenue*, which is where your plan currently points. Paths that could plausibly produce that number in six months look different — high-ticket B2B contracts, an agency or services business on your existing skills, a large freelance expansion, or an equity/exit event. Those are strategy choices, not build choices.

**This is precisely why FR-9 / CFR-9 exist.** I have specified the system to tell you this in month two rather than month five. But the system cannot tell you today what you have not yet given it — see D-1.

### U-2 · Building the tool will accelerate the goal within the window

Implicit in the plan, and not true on this timeline. The system pays off over quarters. Inside six months, hours spent building are hours not spent earning.

**This is an argument for a much smaller first build, not for abandoning it.** See R-1.

### U-3 · Manual metric entry will be sustained

The MVP defers analytics integrations, so KPIs are entered by hand. Your day has no slack at 23:30. Manual entry is the first thing that will lapse — and once KPIs go stale, trajectory, prioritisation and every recommendation degrade with them.

The system is honest about staleness (CFR-7), so it will *say* it has gone blind. But a blind system gives no advice.

### U-4 · A local-only system can wake you at 06:00

Only if the machine is on overnight, every night. One overnight Windows update reboot without auto-login and the wake-up silently does not happen. FR-97 proposes a Windows Service specifically to survive this, but the machine must still be powered on.

---

## Part C — Missing dependencies

| ID | Missing | Blocks | Severity |
|---|---|---|---|
| **D-1** | **Baseline numbers** — current Railzy revenue and users, channel size and earnings, freelance income, salary | The entire goal engine. Trajectory, pace and gap are uncomputable. Every recommendation depends on them. | 🔴 Blocking |
| **D-2** | **Goal decomposition** — how ₹1 crore splits across Railzy / Content / Freelance / Naxova | Prioritisation. Without it the engine cannot compare a Railzy task against a content task. | 🔴 Blocking |
| **D-3** | **Definition of the target** — revenue, profit, or take-home | Changes strategy materially. ₹1 crore revenue and ₹1 crore take-home are very different businesses. | 🔴 Blocking |
| **D-4** | **Railzy metric sources** — where users, conversions, SEO and revenue data actually live | The Railzy dashboard panel; the funnel/bottleneck model of CFR-31 | 🟠 High |
| **D-5** | **Actual-time capture method** | Time-allocation analysis, effort calibration — the entire Learning stage | 🟠 High |
| **D-6** | **Which decisions you get wrong or delay** | Tuning the advice layer. Asked in `understanding.md` §6; still unanswered. | 🟠 High |
| **D-7** | **Priority weights** | Every ranking the engine produces | 🟡 Medium |
| **D-8** | **WhatsApp route** and **wake-up mechanism** | Notification delivery | 🟡 Medium |

**D-1 through D-3 are genuinely blocking.** The goal engine is the heart of both documents and it cannot produce a single meaningful output without them. They are five minutes of your time to answer and they unblock the most valuable part of the system.

---

## Part D — Security risks

| ID | Risk | Severity | Mitigation (specified) |
|---|---|---|---|
| **S-1** | **Employer/client data reaching a hosted model.** You are a TPM at Gate6 with a separate paying client. This could breach an NDA or your employment terms. | 🔴 Critical | Confidentiality classification + hosted-model exclusion (FR-44, SEC-7). Local model only for classified context. |
| **S-2** | **Prompt injection.** An agent with GitHub, filesystem, shell and browser access that reads web pages and issue bodies is directly attackable. A malicious issue body could attempt to drive actions. **Your specification did not cover this** — I added it. | 🔴 Critical | Fetched content is data, never instruction. Actions originating from fetched content always require approval regardless of tool level (SEC-5). |
| **S-3** | **WhatsApp account compromise.** Unofficial bridges authenticate as you. A ban costs your primary personal comms; a breach lets an attacker message your family and clients as you. | 🟠 High | Dedicated number, never personal. **[OPEN-3]** still undecided. |
| **S-4** | **Credential concentration.** One machine holding GitHub tokens, WhatsApp session, and your entire professional and personal history. Compromise means an attacker can *act* as you, not merely read you. | 🟠 High | Encryption at rest (SEC-10), secrets store, no inbound network exposure, L3 local-UI-only confirmation. |
| **S-5** | **Local shell tool.** Effectively arbitrary code execution on your primary machine. | 🟠 High | L3, **disabled by default**, explicit opt-in (§20). |
| **S-6** | **Audit log leakage.** Action inputs/outputs could capture secrets or client data. | 🟡 Medium | Redaction by classification before persistence (SEC-6). |
| **S-7** | **Supply chain.** Community tools or skills running with your permissions. | 🟡 Medium | Pinned dependencies; vetting before registration. |

---

## Part E — Scope risks

| ID | Risk | Note |
|---|---|---|
| **SR-1** | **Abandonment.** The dominant failure mode. If it nags, misfires, or costs more attention than it returns, it dies in two weeks — and takes the build time with it. | Notification budget, brevity, and early value delivery are the countermeasures. |
| **SR-2** | **The advice layer is the hardest part and depends on data you don't have yet.** Levels 1 and 2 (remind, execute) are ordinary engineering. Level 3 (advise) needs history to be any good. | Argues for building 1 and 2 now and *accumulating data* while you build 3. |
| **SR-3** | **The office visualisation is a large UI investment with no decision value.** | FR-88 already defaults to a list view. Ship the metaphor when the engine works. |
| **SR-4** | **Voice is expensive and its value is concentrated in ~3 hrs/week of commute.** Real value, but not the first thing. | Milestone M6, not M1. |
| **SR-5** | **Twenty-six subsystems on a solo evening budget invites a half-finished system that does nothing well.** | The core scope risk. See R-1. |

---

## Part F — Prioritised recommendations

Ranked by impact on your actual outcome.

### 🔴 R-1 · Cut the MVP to the nudge loop, and use it while you build the rest

**The single most important recommendation in this document.**

Ship **M0 + M1 only** as the first release: service starts on boot, scheduler, notifier, Telegram, and your routine nudges. That is roughly **2–4 weekends**, not a year. It fires your 06:00 / 07:30 / 09:10 / 20:00 nudges and delivers real daily value immediately.

Then add M2–M8 incrementally while *living inside it*. Every subsequent milestone is validated by use rather than by guesswork, and you stop building things you turn out not to want.

**Why this matters more than anything else here:** it is the only version of this plan where the tool does not eat the six months it exists to serve. It also matches your own stated operating principle, which the current MVP contradicts.

The full scope is not discarded — §31 of the PRD sequences all of it. Only the *release boundary* moves.

### 🔴 R-2 · Answer D-1, D-2 and D-3 before any code is written

Baseline numbers, the goal split, and what ₹1 crore actually means. Roughly five minutes of your time.

Without them the goal engine — the heart of both documents — cannot produce one meaningful output. With them, it can start computing trajectory from day one and start warning you early, which is the whole point.

### 🔴 R-3 · Decide the confidentiality boundary before connecting anything

Before the first integration, write down explicitly what Gate6 and client material the system may and may not see, and enforce it in classification rules from the first commit rather than retrofitting.

This is the one risk here that could cost you a job rather than a weekend.

### 🟠 R-4 · Simplify the MVP stack

Your brief nominates Postgres + pgvector + Redis + Celery/Dramatiq/RQ + FastAPI + Next.js. For a **single-user local-first Windows app**, that is a lot of operational surface for one developer with 8 hours a week — three services to install, run, monitor and keep alive on your own desktop.

Consider for MVP: one embedded database (SQLite with a vector extension), in-process scheduling, no broker, and a single process serving both API and UI. Introduce the heavier stack at the phase-2 cloud lift, where it earns its keep.

**This is a recommendation, not a decision** — final technology selection belongs to `bmad-architecture`. But every hour spent on infrastructure is an hour not spent on the loop.

### 🟠 R-5 · Test the ₹1 crore strategy on paper this week, before building anything to track it

Write down the actual arithmetic for each engine: what Railzy would have to charge and to how many users; what the channel would have to reach; what freelance capacity you could realistically add. Compare the sum to ₹1 crore.

If the number does not close, you have learned it in week one for the cost of an hour — instead of in month five for the cost of six months. That is exactly the service FR-9 is designed to provide, delivered manually before the system exists to deliver it.

Based on U-1, I expect the ads-and-product path not to close, and that the answer lies in higher-ticket services on skills you already have. **Better to discover that now.**

### 🟠 R-6 · Solve the metric-entry problem before it silently kills the system

Manual entry at 23:30 will lapse (U-3), and stale KPIs make every downstream recommendation worthless.

Options: pull the two or three metrics that matter most automatically even at MVP; or make entry a 30-second voice interaction during the commute rather than a form at midnight. The second fits your day far better and uses time that is currently dead.

### 🟡 R-7 · Defer the office visualisation and voice to after the loop closes

Both are real requirements and both are in the roadmap. Neither improves a single decision until the engine underneath produces good recommendations. List view first (FR-88), voice at M6.

### 🟡 R-8 · Decide the wake-up mechanism now, because it may change the architecture

If the 06:00 wake-up must genuinely ring, and leaving the PC on overnight is unacceptable, then you need a small always-on component — which is phase 2, not MVP, and changes the first release.

The cheapest honest answer is likely: local machine alarm on the running PC for MVP, PSTN call in phase 2. But decide it deliberately rather than discovering it on the first morning it fails.

---

## Part G — What I need from you

Blocking, in order:

1. **Baseline numbers** — Railzy revenue and users today; channel subscribers/followers and current earnings; freelance monthly income; salary.
2. **Does ₹1 crore mean revenue, profit, or take-home?**
3. **How does it split** across Railzy / Content / Freelance / Naxova?
4. **Do you accept R-1** — ship the nudge loop first, build the rest while using it?

Non-blocking but valuable: the remaining fourteen open questions in PRD §33, particularly which decisions you most often get wrong or delay (D-6), since that is what the advice layer must be tuned to attack.

---

*These are findings, not changes. Nothing in your specification has been altered — the PRD records your MVP scope as you gave it, with this analysis referenced alongside.*

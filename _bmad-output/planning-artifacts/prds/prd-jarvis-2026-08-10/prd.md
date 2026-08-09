---
title: Personal AI Operating System (working name "Jarvis")
status: draft
created: 2026-08-10
updated: 2026-08-10
---

# PRD: Personal AI Operating System

*Working name "Jarvis" — the name is configuration, not identity. See FR-121.*

---

## 0. Document Purpose

This PRD specifies a single-user personal AI operating system: a decision, prioritisation, execution and business-management partner for one named user. It is written to be consumed by downstream BMad workflows (`bmad-architecture`, `bmad-create-epics-and-stories`, `bmad-ux`) without the product concept needing re-explanation.

**How to read it.** §1–§8 establish why the product exists and the principles that constrain every later decision. §9 is the Glossary — every domain noun used in this document is defined there once, and downstream artifacts must use those terms verbatim. §10 holds the functional requirements, grouped by feature with globally-numbered stable IDs (FR-1 … FR-133). §11 holds cross-cutting non-functional requirements. §12–§13 cover journeys and UX. §14–§27 are architecture and cross-cutting design. §28–§34 are scope, roadmap, risks and acceptance.

**Requirement status is marked explicitly**, as requested:

| Tag | Meaning |
|---|---|
| **[CONFIRMED]** | Stated directly by the user. Not to be altered without their decision. |
| **[PROPOSED]** | Introduced by this PRD to make a confirmed requirement implementable. Needs the user's yes/no. |
| **[ASSUMPTION]** | Inferred without confirmation. Indexed in §35. |
| **[OPEN]** | Genuinely unknown. Indexed in §33. Not invented. |

Untagged requirements are **[CONFIRMED]** — the default, since the bulk of this document derives from the user's own 48-section specification.

**Source inputs.** The user's 48-section specification (2026-08-10); the brainstorming intent doc at `_bmad-output/brainstorming/brainstorm-daily-reel-2026-08-10/brainstorm-intent.md`; the project brief at `docs/N-a.pdf`; and the session memlog at `.memlog.md` in this folder.

**Companion documents.** `recommendations.md` in this folder carries the pre-finalisation analysis the user requested — contradictions, missing dependencies, unrealistic assumptions, security risks, scope risks, and a prioritised recommendation list. **It should be read before this PRD is acted on**, because its first finding materially affects §28 MVP Scope.

---

## 1. Executive Summary

The user is a Technical Project Manager at Gate6 Technologies who simultaneously runs a live product (Railzy), a daily content operation across three social platforms, a freelance client engagement, and the formation of a parent company (Naxova). These four commitments compete for a single ~17-hour day that has no remaining slack. He has set a financial goal of **₹1 crore within six months**.

The bottleneck is not capacity — he is already at capacity. The bottleneck is **allocation**: whether the hours he already spends land on the work that moves the goal. Existing tools do not help with this. Task managers accept whatever he types. Calendars accept whatever he schedules. Neither has an opinion, and neither knows whether today's work made him any money.

This product is that opinion. It maintains a live model of his goals, projects, revenue and time; it computes what matters most right now; it reaches him wherever he is — WhatsApp, Telegram, voice in the car — and it tells him what to do, what to stop doing, and when his plan has stopped adding up. It executes approved work on his behalf, and it records every decision so that past reasoning can be re-examined when the facts change.

Success is not measured in tasks completed. It is measured in whether his time, decisions and business outcomes measurably improve.

---

## 2. Problem Statement

**The user is time-bankrupt and allocation-blind.**

His day runs 06:00 to 23:30 with no unallocated blocks. Every new commitment displaces an existing one, but he has no instrument that tells him *which* displacement is correct. Four specific failures follow:

1. **No prioritisation across domains.** Railzy work, content work, client work and company-formation work sit in different tools and different mental contexts. Nothing compares a Railzy bug against tonight's reel against a Naxova filing deadline. He arbitrates by whatever is loudest.
2. **The highest-value asset gets the least time.** Railzy — the product intended to sit under Naxova and generate revenue — is the only commitment in his week with **no protected time slot**. Everything else has one. Work that lives in the cracks does not happen reliably.
3. **No feedback loop between effort and outcome.** He publishes daily and ships product changes, but nothing correlates that effort with subscribers, users, or revenue. Without that link, he cannot tell a high-return activity from a comfortable one.
4. **He is away from his desk when decisions are needed.** Gym, a ~30-minute commute each way three days a week, and a full office day mean that any tool requiring him to sit at a screen captures almost none of his day. Screen-bound tools lose by default.

Underneath all four sits the hardest problem: **the ₹1 crore target has no plan attached to it that has been tested against arithmetic.** Nothing currently tracks the required run-rate, the actual run-rate, or the gap — so there is no mechanism to discover that a chosen strategy cannot reach the target until the six months have already elapsed.

---

## 3. Product Vision

A personal operating system that behaves like a chief of staff who has read everything, remembers every decision, watches every metric, and is not afraid to disagree.

It knows the user's goals and the arithmetic required to hit them. It knows every project, its state, and its risks. It knows the shape of his day and where his attention is actually available. From these it continuously answers two questions:

> **"What is the single highest-value thing I should do right now?"**
> **"What should I stop doing?"**

It reaches him through whatever channel fits the moment — a spoken briefing in the car, a WhatsApp nudge at the gym, a HUD on the desktop at night. It executes approved work so that a decision becomes an outcome without a context switch. And it keeps a durable record of what was decided and why, so that when the facts change, the decision can be revisited rather than silently inherited.

It is explicitly **not** a productivity theatre. Completing more tasks is not the objective. Making the user's time, decisions and business outcomes measurably better is.

---

## 4. Goals

**Product goals**

| ID | Goal |
|---|---|
| **G-1** | The user knows, at any moment and through any channel, what the highest-value action available to him is — and why. |
| **G-2** | The user is told, early and unambiguously, when his trajectory cannot reach ₹1 crore by 2027-02-10 under current assumptions. |
| **G-3** | Work that the user approves is executed by the system rather than by the user. |
| **G-4** | Every commitment, decision, experiment and outcome is durably recorded and retrievable by question, not by filename. |
| **G-5** | The system is useful while the user is away from a screen — in the car, at the gym, mid-office-day. |
| **G-6** | The user's protected time reflects his stated priorities, and deviation is surfaced weekly. |

**Business goal — a configured instance, not a product feature**

The user's current strategic goal is **₹1,00,00,000 in aggregate earnings within six months** — by **2027-02-10** from a start of **2026-08-10**, requiring **≈₹16.7 lakh per month**.

This appears throughout the document as the *worked example*, because it is the goal the system will actually run against on day one. It is **configuration**. The engine treats it identically to a subscriber target, a product launch, or a learning objective, and the system must remain fully functional if it is deleted (FR-6).

- **[OPEN-1]** Whether this figure means *revenue*, *profit*, or *personal take-home* is not yet defined, and the three imply materially different strategies. See §33.

---

## 5. Non-Goals

The product is explicitly **not**, and will not become in v1:

- A reminder app, to-do list, chatbot, calendar replacement, or generic voice assistant. Each of these is a *component* of the system; none is the product.
- A multi-tenant or multi-user product. It serves one user. No sign-up, no tenancy, no role model beyond the single owner. Any future Naxova product is a separate build.
- A fully autonomous agent. It proposes; the user disposes. Autonomy expands only through the permission model in §19, one deliberate step at a time.
- A general-purpose assistant. It has an opinion, grounded in the user's goals. Requests unrelated to those goals are not a design target.
- A replacement for the user's judgement. It argues, evidences, and warns — it does not decide unilaterally on anything above Permission Level 1.
- A social-media management SaaS, a project-management SaaS, or an analytics product. It integrates with these domains for one user's benefit; it does not productise them.
- **Not a source of truth for money it cannot see.** Revenue figures the user does not enter or connect are not invented, estimated, or inferred. See §11 NFR-18.

---

## 6. User Persona

**The Operator — one real person, not a segment.**

Software engineer by training, Technical Project Manager by title, at Gate6 Technologies. Runs three ventures in the margins of a full-time job while raising school-age children.

| Dimension | Detail |
|---|---|
| **Technical level** | High. Ships production code, manages infrastructure, runs deployments. Will read logs. Will not be satisfied by a black box. |
| **Time available** | Effectively zero unallocated hours. Any time the product costs must be repaid the same week. |
| **Attention pattern** | Fragmented. Long screen-free stretches (gym, commute, office), concentrated screen time late at night when fatigue is highest. |
| **Decision style** | Moves fast, commits to many parallel initiatives, and is at risk of spreading thin — the behaviour §10.18 is designed to detect. |
| **Tolerance for bluntness** | Explicitly requested. Asked for an agent that is "brutally honest rather than agreeable." |
| **Failure mode to design against** | Abandoning the tool. If it nags, misfires, or costs more attention than it returns, it is dead within two weeks. |

**Jobs To Be Done**

- When my day starts, help me know the two or three things that actually matter, so I stop arbitrating by whatever is loudest.
- When I am driving, let me think out loud and have it captured and acted on, so the commute stops being dead time.
- When I am about to spend an evening on something, tell me if there is something better, so I stop losing weeks to comfortable work.
- When I am behind on my goal, tell me while I can still act, not in month five.
- When I ask why we decided something months ago, give me the reasoning and whether it still holds.
- When work can be done without me, do it — and show me what you did.

**Non-Users (v1):** the user's family; Gate6 colleagues; Railzy end users; freelance-client staff; any future Naxova employee. None of these has an account, a view, or a notification channel.

---

## 7. User Context

The system must model this schedule as first-class data (see FR-31), not treat it as prose.

**Daily shape**

| Time | Activity | Attention available |
|---|---|---|
| 06:00–06:30 | Wake | None — asleep until nudged |
| 06:30–07:30 | Kids ready for school | None |
| 07:30–09:15 | Gym | **Audio only** |
| 09:15–10:00 | Home, prepare for office | Low |
| 10:00–10:30 | Commute (Tue/Wed/Thu only) | **Audio only, hands and eyes busy** |
| 10:30–19:00 | Gate6 work | Low — employer's time |
| 19:00–19:30 | Commute home (Tue/Wed/Thu only) | **Audio only** |
| 19:30–20:00 | Home, freshen up | Low |
| 20:00–20:30 | Client standup (Mon–Fri) | None — on a call |
| 20:30–23:00 | Client work, dinner | Medium — screen available, fatigue rising |
| ~23:30 | Daily reel upload | **Low — highest fatigue, daily deadline** |

**Weekly shape**

| | Sun | Mon | Tue | Wed | Thu | Fri | Sat |
|---|---|---|---|---|---|---|---|
| Gate6 | — | — | Office | Office | Office | WFH | WFH |
| Commute | — | — | ✅ | ✅ | ✅ | — | — |
| Client standup 20:00 | — | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Reel upload ~23:30 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Consequences that constrain the design**

1. **Screen-free is the majority context.** ~3 hrs/week commute plus ~12 hrs/week gym are audio-available and screen-unavailable. Voice is not a v2 nicety (§10.15).
2. **Sunday is the only clear day.** It is the sole candidate for deep work, weekly review, or building this system.
3. **The reel has a supply gap.** Seven uploads a week are fed by three days of office-travel footage. Four uploads per week have no scheduled source material (§10.13).
4. **Late-night is the worst time for judgement.** The system should not ask for decisions at 23:30 that could have been asked at 10:00 (NFR-9).
5. **Railzy is unprotected.** Every other commitment owns a recurring slot. Railzy does not. This is the single largest structural finding from discovery.

---

## 8. Product Principles

Binding constraints on every downstream decision. Where a later requirement appears to conflict with one of these, the principle wins and the conflict is a defect.

| ID | Principle | Consequence |
|---|---|---|
| **P-1** | **Outcomes over activity.** | Never optimise for tasks completed. Dashboards lead with goal progress, not throughput. Counter-metric SM-C1 exists to enforce this. |
| **P-2** | **Honest over agreeable.** | The system says when the user is wasting time, when a goal is unreachable, and when it disagrees. Politeness never suppresses a material warning. |
| **P-3** | **Never fabricate.** | No invented metrics, no claimed success for a failed action, no confident answer from missing data. Uncertainty is stated explicitly. |
| **P-4** | **Propose, don't presume.** | Anything above Permission Level 1 requires approval. Autonomy is granted, never assumed. |
| **P-5** | **Reach the user; don't wait for him.** | Value is delivered by pushing to where he already is. Any capability that only works when he opens a screen is half-built. |
| **P-6** | **Respect attention as the scarcest resource.** | Notification volume is a tracked metric with a budget. Silence is a valid and often correct output. |
| **P-7** | **Explain every recommendation.** | Every priority, warning and suggestion exposes the inputs that produced it. No unexplainable scores. |
| **P-8** | **Provider-independent.** | No architectural coupling to one LLM vendor. Models are configuration. |
| **P-9** | **Local and private by default.** | Data stays on the user's machine unless he explicitly connects something. Employer and client confidential material never leaves to a hosted model. |
| **P-10** | **The name is configuration.** | "Jarvis" appears in exactly one config default and in message templates. Never in code. |
| **P-11** | **Build incrementally.** | From the user's own brief: *"do not build everything at once; define architecture and scope first, then implement incrementally."* This principle is currently in tension with §28 — see `recommendations.md` R-1. |

---

## 9. Glossary

Downstream workflows must use these terms exactly. Introducing a synonym anywhere is a discipline violation.

- **Agent** — the single orchestration layer that interprets input, plans, selects Tools, and produces Recommendations. There is exactly one. Specialised behaviour is expressed as Worker Roles, not as separate agents.
- **Worker Role** — a named specialisation (Researcher, Developer, Content Manager, SEO Analyst, Business Analyst, Scheduler, Data Analyst) presented to the user as an "employee" in the UI, and implemented as a prompt profile plus a Tool subset bound to the Agent. A Worker Role is not an independent process. Cardinality: one Agent, many Worker Roles.
- **Tool** — a registered capability the Agent can invoke (GitHub, filesystem, browser, web research, shell, messaging). Every Tool declares capability, inputs, outputs, side effects, Permission Level, and confirmation requirement.
- **Tool Registry** — the controlled catalogue of all available Tools. Nothing is invocable unless registered.
- **Permission Level** — one of L0 Observe, L1 Safe, L2 Approval Required, L3 High Risk. Attaches to Tools and to individual actions. Defined in §19.
- **Approval** — an explicit user grant for a single pending Action at L2 or L3. Time-bounded; expires unactioned.
- **Action** — one concrete invocation of a Tool by the Agent, with inputs, outputs, permission decision, and result. The unit of the Audit Log.
- **Task** — a unit of the user's work, tracked by the system, belonging to exactly one Project, carrying a Priority Score. May be executed by the user or by the Agent.
- **Project** — a durable container for work: Railzy, Content, Freelance, Naxova, Personal. Holds objective, status, roadmap, backlog, Tasks, deadlines, risks, dependencies, KPIs, Decisions, documentation.
- **Goal** — a measurable target with a deadline, arranged in a hierarchy under a Root Goal. Carries goal type, target, current value, projected value, required pace, confidence, status. Goal types include monetary, count, milestone, ratio, duration and qualitative-with-proxy.
- **Root Goal** — whichever Goal sits at the top of a Goal tree. **A Root Goal is configuration, never code.** The user's ₹1 crore by 2027-02-10 is one configured instance and is indistinguishable to the engine from any other strategic goal — a user-growth target, a product launch, a learning objective. Deleting it must leave a fully functional system.
- **KPI** — a named measure attached to a Goal or Project, with a current value, a history, and a source.
- **Priority Score** — the computed ranking of a Task, derived by the Priority Engine from weighted factors. Always accompanied by its factor breakdown.
- **Priority Band** — the human-facing bucket a Priority Score falls into: P1 (do now), P2 (this week), P3 (scheduled), P4 (candidate for deletion).
- **Plan** — the ordered set of Tasks and protected blocks proposed for a given day, with an explicit unallocated buffer.
- **Replan** — a regeneration of the current Plan triggered by a change in circumstances, always presented for approval before it replaces the standing Plan.
- **Protected Block** — a time range reserved for one Project that the planner may not fill with other work without explicit user consent.
- **Context Mode** — the user's current situation: Commute, Work, Evening, Creator, Planning. Determines channel, verbosity, and which Tools are offered.
- **Briefing** — a scheduled spoken or written summary: Daily Briefing, Commute Briefing, Weekly Business Review, End-of-Day Review.
- **Recommendation** — a proactive suggestion produced by the Agent, carrying a rationale, the evidence behind it, and a confidence level. The user may accept, reject, or defer it; the outcome is recorded.
- **Decision** — a recorded choice in the Decision Journal, with reasoning, alternatives considered, expected outcome, review trigger, and validity status.
- **Review Trigger** — the condition that causes a Decision to be resurfaced for reconsideration (a date, a KPI threshold, or an event).
- **Experiment** — a tested hypothesis with objective, action, metric, baseline, target, duration, result, conclusion, and resulting Decision.
- **Revenue Record** — a money entry classified as Actual, Expected, Pipeline, or Projected, attributed to a Revenue Stream.
- **Revenue Stream** — a named income source: Salary, Freelance, Railzy, Content, Sponsorship, Affiliate, Naxova, Other.
- **Trajectory** — the projected end-state of the Root Goal given current run-rate, compared against Required Pace.
- **Required Pace** — the per-day, per-week and per-month earnings needed from today to reach the Root Goal by its deadline.
- **Content Item** — one piece of content through its lifecycle: idea → concept → source footage → title/hook/description/tags/thumbnail/caption → scheduled → published → measured.
- **Memory Partition** — one of the six separated stores: User, Knowledge, State, Decisions, Events, Goals. Defined in §16.
- **Event** — an immutable record of something that happened: a Task completed, a deployment, a publication, a failure, a business event.
- **Notification Class** — Critical, Important, Normal, or Informational. Determines channel, timing, and whether it may interrupt.
- **Audit Log** — the immutable, append-only record of every Action, its rationale, approval, and result.
- **Assistant Name** — the configured display name, default `"Jarvis"`. The only place the literal appears outside message templates.

---

## 10. Functional Requirements

FRs are numbered globally and are stable. Downstream artifacts reference them by ID.

### 10.1 Agent Core and Decision Loop

**Description:** The Agent is a single orchestration layer running a continuous loop: **Goal → Plan → Prioritize → Execute → Measure → Learn → Replan**. Each pass consumes current State, Goals and Events, and emits a Plan plus Recommendations. Worker Roles are prompt profiles with scoped Tool access bound to this one Agent — not separate processes. Realizes UJ-1, UJ-2.

#### FR-1: Run the decision loop
The Agent executes the full loop on a schedule and on demand.

**Consequences (testable):**
- A full loop pass runs at least at: 05:45 (pre-briefing), on Context Mode change, on Replan trigger, and at 22:30 (end-of-day).
- Each pass writes an Event recording inputs consumed, Plan produced, and Recommendations emitted.
- A pass completes in ≤ 60 s or reports which stage exceeded budget.

#### FR-2: Answer the two core questions on demand
Through any channel, the user can ask what to do now and what to stop doing, and receive a ranked, evidenced answer.

**Consequences:**
- "What should I do now?" returns exactly one primary recommendation plus at most two alternates.
- Every answer names the Goal it serves and the factors that produced its rank.
- If data is insufficient to rank, the Agent says so rather than guessing (P-3).

#### FR-3: Disagree with the user when evidence supports it
When a user-chosen action is materially lower-value than an available alternative, the Agent states the disagreement, its evidence, and its recommendation.

**Consequences:**
- Disagreement is raised once per decision, not repeated until compliance (P-6).
- The user can override; the override is recorded as a Decision with its rationale.
- If an overridden recommendation is later validated by outcome data, the Agent surfaces this in the Weekly Business Review — never in the moment.

#### FR-4: Bind Worker Roles to the orchestration layer
The Agent selects a Worker Role per unit of work; the role scopes prompt profile and available Tools.

**Consequences:**
- Adding a Worker Role requires no new process, service, or deployment unit.
- Every Action records the Worker Role that produced it.
- **[PROPOSED]** Roles at MVP: Researcher, Developer, Content Manager, Business Analyst. SEO Analyst, Scheduler and Data Analyst are post-MVP.

#### FR-5: State uncertainty explicitly
Every Recommendation carries a confidence level, and low-confidence output declares what data would raise it.

**Consequences:**
- Confidence is one of High / Medium / Low, with the limiting factor named at Medium or Low.
- No Recommendation is issued at Low confidence for a Critical notification.

---

### 10.2 Goal and KPI Engine

**Description:** A generic hierarchical Goal engine. It computes required pace, trajectory and gap for **any** configured strategic goal, and is the arithmetic conscience of the product. The user's current tree — ₹1 crore by 2027-02-10, with Railzy, Content, Freelance and Naxova as first-level children — is **seed configuration, not a feature**. Realizes UJ-3.

> **Design constraint [CONFIRMED]:** no strategic target is hard-coded anywhere. The authoritative specification is `../../architecture/core-intelligence-loop.md` §3.2 (CFR-4). **Acceptance: deleting the ₹1 crore Goal leaves a fully functional system with zero code changes.**

#### FR-6: Maintain a hierarchical Goal tree of arbitrary goal types
Goals nest arbitrarily deep under a Root Goal; children roll up to parents. Supported goal types at minimum: monetary, count (users / subscribers / views), milestone (binary), ratio, duration, and qualitative-with-proxy.

**Consequences:**
- Each Goal stores: name, parent, target value, unit, current value, deadline, owner, status, confidence, dependencies.
- Editing a child's current value updates every ancestor's rollup within one loop pass.
- A Goal with no measurable target is rejected at creation with an explanatory error.

#### FR-7: Compute Required Pace
The engine derives the per-month, per-week and per-day earnings needed to reach each Goal from today.

**Consequences:**
- Root Goal at creation yields ≈ ₹16,66,667/month, ≈ ₹3,84,615/week, ≈ ₹54,945/day over 182 days.
- Required Pace recomputes daily and after every Revenue Record change.
- Pace is expressed against *remaining* time and *remaining* amount, never the original figures.

#### FR-8: Compute Trajectory and Gap
The engine projects the end-state from actual run-rate and reports the gap to target.

**Consequences:**
- Trajectory states projected total at deadline, absolute gap, and percentage of target.
- Projection method is named in the output (**[PROPOSED]** trailing 30-day mean, switching to 90-day once history allows).
- With fewer than 14 days of Revenue Records, the engine reports "insufficient history" instead of projecting (P-3).

#### FR-9: Declare a Goal mathematically unrealistic
When required acceleration exceeds a configured plausibility threshold, the Agent states plainly that the Goal is not reachable under current assumptions.

**Consequences:**
- Triggered when Required Pace exceeds the trailing realised pace by ≥ 5× **[PROPOSED — threshold needs the user's judgement]**.
- Output names which assumptions would have to change, and by how much, for the Goal to become reachable.
- Raised as Important, at most weekly, never as a repeated daily nag (P-6).
- The user may acknowledge and continue; the acknowledgement is recorded as a Decision with a Review Trigger.

#### FR-10: Track KPIs against Goals and Projects
Named measures with values, history, and a declared source.

**Consequences:**
- Each KPI records whether its source is manual entry, an integration, or a computation.
- A KPI unrefreshed beyond its expected interval is flagged stale and excluded from Trajectory.
- KPI history is retained for the full six-month window at minimum.

#### FR-11: Seed the initial Goal tree
The system ships with the Root Goal and the four first-level Projects pre-structured.

**Consequences:**
- First run creates: ₹1 Crore → {Railzy, Content, Freelance, Naxova}, each with the sub-goals in the user's §5 specification.
- Targets for each child are **[OPEN-2]** — the split is not yet decided. Until set, children carry target `null` and the engine reports the Root Goal as unallocated.

---

### 10.3 Priority Engine

**Description:** Every Task is scored on weighted factors and assigned a Priority Band. The engine's distinguishing behaviour is that it actively recommends *not* doing low-value work. Realizes UJ-1, UJ-4.

#### FR-12: Score every Task
Each Task receives a Priority Score from weighted factors: business impact, revenue impact, user impact, urgency, effort, deadline proximity, dependencies, strategic importance, opportunity cost, risk reduction.

**Consequences:**
- No Task exists without a score; unscored input is queued for scoring, not silently dropped.
- The full factor breakdown is retrievable for any Task (P-7).
- Rescoring occurs on Task edit, on dependency change, and on every loop pass.

#### FR-13: Assign a Priority Band
Scores map to P1 (do now), P2 (this week), P3 (scheduled), P4 (delete candidate).

**Consequences:**
- Band boundaries are configuration, not hardcoded.
- "Fix Railzy signup bug" (impact H, revenue H, user H, effort 45 min, urgency H) lands P1.
- "Change button radius 10px → 12px" (impact L, revenue L, effort 30 min) lands P4.

#### FR-14: Recommend against low-value work
When the user schedules or starts a P3/P4 Task while a P1 exists, the Agent says so.

**Consequences:**
- The message names both Tasks and the value difference.
- Raised once per occurrence.
- The user may proceed; proceeding is recorded as an Event for §10.19 analysis.

#### FR-15: Surface deletion candidates
P4 Tasks that have survived a configured period without progress are proposed for removal.

**Consequences:**
- **[PROPOSED]** Threshold: P4 and untouched for 21 days.
- Presented in the Weekly Business Review as a batch, never as individual interruptions.
- Removal requires approval; the removal is recorded.

#### FR-16: Explain any score
For any Task the user can ask why it ranks where it does.

**Consequences:**
- The answer lists each factor, its value, its weight, and its contribution.
- Available by voice in a form short enough to speak (NFR-6).

---

### 10.4 Daily Planning

**Description:** The planner generates a realistic Plan from fixed commitments, available focus time, current priorities and energy context — and deliberately under-fills it. Realizes UJ-1.

#### FR-17: Generate a daily Plan
A Plan is produced for each day covering fixed commitments, Protected Blocks and prioritised Tasks.

**Consequences:**
- Generated by 05:45 for the current day.
- Every scheduled item names the Goal it serves.
- The Plan is presented for approval; it does not silently become authoritative.

#### FR-18: Respect fixed commitments
Office hours, commute, gym, kids' routine, client standup and family time are treated as immovable unless the user moves them.

**Consequences:**
- The planner never schedules work into a fixed commitment.
- Commute and gym windows are marked audio-only and only voice-suitable work is placed there.
- Gate6 working hours are never filled with Railzy, Content or Naxova work (see §26 Privacy).

#### FR-19: Do not over-schedule
The Plan preserves an explicit unallocated buffer.

**Consequences:**
- **[PROPOSED]** At least 20% of discretionary time is left unallocated.
- If priorities exceed available time, the planner drops the lowest-value items and says which and why — it never compresses estimates to fit.
- A Plan that would exceed available time is rejected, not silently overcommitted.

#### FR-20: Protect Railzy time
Railzy receives a recurring Protected Block, on the same footing as the client standup.

**Consequences:**
- At least one Protected Block per week, defaulting to Sunday **[ASSUMPTION — the only clear day; needs confirmation]**.
- Filling it with other work requires explicit consent.
- Repeated sacrifice of the block is flagged by FR-70.

#### FR-21: Match work to attention
Tasks are placed against the attention available in each window.

**Consequences:**
- Deep or decision-heavy work is never placed after 22:30 (NFR-9).
- Audio-only windows receive only voice-suitable Tasks.
- Each Task carries an attention requirement: Deep, Shallow, or Audio.

---

### 10.5 Dynamic Replanning

**Description:** The Plan is a living object. Changed circumstances trigger a proposed Replan; the user approves or rejects.

#### FR-22: Detect replan triggers
The system detects events that invalidate the standing Plan.

**Consequences:**
- Triggers include: a Railzy production issue, a new P1 Task, a missed Protected Block, a deadline moving inside the horizon, and explicit user request.
- Each trigger writes an Event naming what changed.

#### FR-23: Propose a revised Plan
On trigger, the Agent produces a revised Plan with an explicit diff.

**Consequences:**
- The diff states what moved, what was dropped, and what was protected — in that order.
- Rationale accompanies every change (P-7).
- Example form: *"Move Naxova research to tomorrow. Protect the production fix and today's client deadline."*

#### FR-24: Require approval for a Replan
A revised Plan replaces the standing Plan only after the user accepts it.

**Consequences:**
- Accept / reject / modify are all available by voice.
- Rejection preserves the original Plan and records the rejection.
- An unanswered Replan proposal expires after **[PROPOSED]** 4 hours, leaving the original Plan standing.

---

### 10.6 Scheduler

**Description:** Core infrastructure primitive. Fires time- and condition-based triggers into the Notification System and the Agent.

#### FR-25: Support scheduled trigger types
One-time, recurring, deadline-derived, and conditional triggers.

**Consequences:**
- Recurrence supports daily, weekday-set, weekly, monthly, and cron expressions.
- Conditional triggers evaluate on each loop pass where technically possible.
- Triggers survive restart — schedule state is persisted, not in-memory.

#### FR-26: Fire the standing schedule
The user's routine nudges are configured as first-class scheduled triggers.

**Consequences:**
- Ships configured with: 06:00 wake, 07:30 gym, 09:10 leave gym, 20:00 client standup (Mon–Fri), reel deadline warning, daily briefing, weekly review, end-of-day review.
- Each is individually editable and disableable by the user.
- Missed triggers (machine off) are detected on next start and reported, not silently swallowed (FR-28).

#### FR-27: Trigger the Notifier
The Scheduler's output is a Notification request, never a direct channel call.

**Consequences:**
- The Scheduler has no knowledge of WhatsApp, Telegram, or any channel.
- Swapping a channel requires no Scheduler change (§22).

#### FR-28: Report missed triggers honestly
Triggers that could not fire because the machine was off are surfaced.

**Consequences:**
- On start, the system lists triggers missed while down, with their scheduled times.
- The user is warned at setup that scheduled nudges require the machine to be running (§27).
- Missed Critical triggers are re-raised on start; missed Informational ones are discarded.

---

### 10.7 Notification System

**Description:** Classified, budgeted delivery across three channels. Notification fatigue is treated as a first-class failure mode.

#### FR-29: Classify every Notification
Critical, Important, Normal, or Informational.

**Consequences:**
- Class determines channel, timing, and interrupt behaviour.
- Critical may interrupt any Context Mode, including during the client standup.
- Informational never interrupts; it batches into the next Briefing.

#### FR-30: Deliver across three channels
Local web UI, Telegram, and WhatsApp.

**Consequences:**
- Channel is selected per Notification Class per Context Mode, from configuration.
- Delivery failure on the primary channel falls back to the next configured channel and records the failure.
- **[OPEN-3]** WhatsApp delivery route — unofficial bridge on a dedicated number vs. paid WhatsApp Business API. See §33.

#### FR-31: Respect a notification budget
Volume is capped and tracked.

**Consequences:**
- **[PROPOSED]** Default budget: ≤ 12 Normal + Informational per day; Critical and Important are uncapped.
- Exceeding the budget suppresses and batches the remainder rather than delivering them.
- Daily notification count is an observability metric (FR-118) and a counter-metric (SM-C1).

#### FR-32: Honour quiet hours
Configured windows suppress all but Critical.

**Consequences:**
- **[PROPOSED]** Default quiet hours 23:45–05:45, and during the 20:00–20:30 client standup.
- Suppressed Notifications are delivered at the next permitted window.

#### FR-33: Deliver a ringing wake-up
The 06:00 wake nudge must be capable of actually waking the user.

**Consequences:**
- **[OPEN-4]** A WhatsApp message cannot ring reliably; WhatsApp's API cannot place programmatic voice calls. Options: local machine alarm (audio out on the user's PC), a PSTN call via Twilio/Exotel, or an escalating message sequence. Not decided.
- Whichever is chosen, the mechanism is behind the Notifier interface and swappable (§22).

---

### 10.8 Task Executor and Tool Architecture

**Description:** The second core primitive. Executes registered Tools on the user's behalf, under the permission model.

#### FR-34: Maintain a Tool Registry
Only registered Tools are invocable.

**Consequences:**
- Each entry declares: name, capability description, input schema, output schema, side effects, default Permission Level, confirmation requirement.
- An unregistered Tool call fails closed with a logged error.
- The registry is inspectable from the UI (§13, Integrations).

#### FR-35: Execute an approved Action
The executor invokes a Tool and records the full Action.

**Consequences:**
- Every Action records: Tool, inputs, outputs, Worker Role, permission decision, approver, duration, result, errors.
- Actions are idempotent where the underlying Tool allows, and duplicate-guarded where it does not (FR-45).
- Execution never proceeds without a resolved permission decision.

#### FR-36: Ship the MVP Tool set
**Consequences:**
- MVP Tools: filesystem (read/write within configured roots), GitHub, web research, browser automation, local shell, document generation, messaging (Telegram/WhatsApp send).
- Local shell defaults to L3 and is disabled until explicitly enabled.
- Each Tool is independently enableable; disabling one does not degrade the others.

#### FR-37: Report failure honestly
A failed Action is never reported as success.

**Consequences:**
- Failures state what failed, at which stage, and what the user can do next (P-3).
- The Agent never claims completion of work it did not complete.
- Partial completion is reported as partial, naming what did and did not land.

---

### 10.9 Permission and Approval

**Description:** Mandatory four-level model governing everything the Agent can do. This is the primary safety mechanism and is non-negotiable at MVP.

#### FR-38: Enforce four Permission Levels

| Level | Grants | Examples |
|---|---|---|
| **L0 Observe** | Read, analyse, summarise. No mutation. | Read repo, summarise backlog, compute KPIs |
| **L1 Safe** | Create reversible local artifacts | Draft content, create Task, create GitHub issue, organise files, prepare report |
| **L2 Approval Required** | Anything outward-facing or production-affecting | Send message, publish content, push code, modify production, change project settings |
| **L3 High Risk** | Always explicit confirmation, never batched | Destructive DB operations, delete files, production deploy, financial transactions, account deletion, credential changes |

**Consequences:**
- Default for any newly registered Tool is L2 — never L0 or L1 by omission.
- L3 confirmation cannot be granted in advance or by a standing rule.
- L2/L3 approval prompts state the exact action, target, and irreversible consequences.

#### FR-39: Time-bound Approvals
An Approval authorises one Action and expires.

**Consequences:**
- **[PROPOSED]** Default expiry 30 minutes for L2, 5 minutes for L3.
- An expired Approval requires re-request; it never silently executes late.

#### FR-40: Approve by any channel
Approvals can be granted from web UI, Telegram, or WhatsApp.

**Consequences:**
- The approval message states the action in one line plus consequences.
- **[PROPOSED]** L3 approval is restricted to the local web UI — a chat-channel compromise must not be able to authorise destructive actions.

#### FR-41: Review permissions
The user can see and change every Tool's Permission Level in one place.

**Consequences:**
- A permission change is itself recorded in the Audit Log.
- Raising a Tool to L1 or L0 from L2 requires a confirmation naming what that Tool can then do unattended.

---

### 10.10 Memory Architecture

**Description:** Six separated partitions, not one generic store. The separation is structural — reflected in schema, not merely in tags.

#### FR-42: Maintain six Memory Partitions

| Partition | Holds | Mutability |
|---|---|---|
| **User** | Preferences, routines, stable facts, working style | Slow-changing |
| **Knowledge** | Project docs, PDFs, manuals, business and technical documentation | Append + version |
| **State** | Current Tasks, schedule, project status, KPIs, Context Mode | Live |
| **Decisions** | Decision Journal entries | Append-only; status mutable |
| **Events** | What happened — completions, failures, deployments, publications | Immutable, append-only |
| **Goals** | Objectives, targets, deadlines, progress | Live + history |

**Consequences:**
- Each partition has its own schema and its own retention rule.
- A write to the wrong partition is a schema error, not a convention violation.
- Events and Decisions are append-only; no update-in-place path exists.

#### FR-43: Retrieve by question
The user can ask natural-language questions and receive answers grounded in the partitions, with sources.

**Consequences:**
- Answers cite which partition and which record produced them.
- Absence of data returns "I don't have that" — never a plausible reconstruction (P-3).

#### FR-44: Isolate confidential material
Employer and client content is partitioned and excluded from any hosted model call.

**Consequences:**
- Records carry a confidentiality classification: Public, Personal, Client-Confidential, Employer-Confidential.
- Client- and Employer-Confidential records are excluded from hosted-model context assembly and may only reach a local model.
- Attempted inclusion is blocked and logged as a security event (§26).

---

### 10.11 Error Recovery

#### FR-45: Recover from failure without compounding it
**Consequences:**
- Failures are explained, recorded, and accompanied by suggested alternatives.
- Dangerous Actions are never silently retried; retry requires fresh Approval.
- Duplicate-action guards prevent a retry from repeating an already-applied side effect.
- Destructive Actions capture a reversal path (backup, branch, or undo token) before executing where technically possible.

---

### 10.12 Decision Journal

**Description:** Durable institutional memory. The system remembers not only what was decided but why, and detects when the reasoning has expired.

#### FR-46: Record Decisions
**Consequences:**
- Each Decision stores: id, date, statement, reasoning, alternatives considered, expected outcome, Review Trigger, status (Active / Superseded / Invalidated), related Project and Goals.
- Decisions are created from Recommendations accepted or rejected, and manually by the user.

#### FR-47: Answer historical "why" questions
**Consequences:**
- "Why didn't we build the Railzy app?" returns the Decision, its reasoning, and its current validity.
- Answerable by voice in Commute Mode.

#### FR-48: Detect invalidated assumptions
When a Review Trigger fires, the Decision is resurfaced.

**Consequences:**
- Triggers may be a date, a KPI threshold, or an Event.
- Example: *"The condition that caused you to postpone the app may no longer apply. Do you want to reconsider?"*
- Resurfacing is Important class, delivered in the Weekly Business Review unless time-critical.

---

### 10.13 Experiment System

#### FR-49: Track Experiments
**Consequences:**
- Each Experiment stores: hypothesis, objective, action, metric, baseline, target, duration, result, conclusion, resulting Decision.
- An Experiment cannot be created without a metric and a baseline.

#### FR-50: Conclude and learn from Experiments
**Consequences:**
- At end of duration, the system prompts for or computes the result and requires a conclusion.
- Concluded Experiments are consulted before the Agent proposes a similar action, and prior results are cited.
- Inconclusive is a permitted conclusion; it is not forced into positive or negative.

---

### 10.14 Content Pipeline

**Description:** The complete creator workflow across YouTube, Instagram and Facebook, including the structural problem that seven weekly uploads are fed by three days of source footage.

#### FR-51: Model a Content Item through its lifecycle
**Consequences:**
- Fields: idea, source footage reference, concept, title, hook, description, tags, hashtags, thumbnail idea, caption, per-platform copy, publish date, status, performance, learnings.
- Status progresses idea → concept → assets → drafted → scheduled → published → measured.
- A Content Item can exist at idea stage with nothing else populated.

#### FR-52: Maintain a content calendar
**Consequences:**
- Shows planned and published items per platform per day.
- Flags any day within the horizon with no Content Item at or beyond `drafted`.
- **[PROPOSED]** Warning threshold: fewer than 3 ready items in the pipeline.

#### FR-53: Generate content assets on request
Titles, hooks, descriptions, tags, hashtags, captions, per-platform copy, and content ideas.

**Consequences:**
- Generation is L1 (draft only); publishing is L2.
- Output is generated per platform, not one text reused across three.
- Requestable by voice in Commute Mode ("give me three reel ideas").

#### FR-54: Address the footage supply gap
The system tracks available source footage against upcoming publish dates.

**Consequences:**
- Warns when upcoming publish dates exceed available unused footage.
- Suggests capture opportunities from the Plan (e.g. an upcoming commute or travel).
- **[PROPOSED]** Supports designating footage-light formats for the four non-travel days.

#### FR-55: Prepare publication
Assemble everything needed so publishing is a single approval.

**Consequences:**
- A prepared item presents final title, description, tags, caption, thumbnail idea and target platforms in one approval.
- Approval triggers publication where an integration exists; otherwise it produces a copy-paste-ready bundle.
- **[NOTE FOR PM]** Direct publishing integrations are post-MVP (§29). MVP produces the bundle.

#### FR-56: Learn content performance
Track views, watch time, retention, likes, comments, shares, saves, subscribers/followers gained, and revenue per item.

**Consequences:**
- Identifies patterns across items and states them with the evidence, e.g. *"Dubai travel reels produce 2.4× more subscribers per 1,000 views than daily office reels."*
- Recommendations from patterns cite the sample size; below **[PROPOSED]** 5 items the pattern is reported as provisional.
- **[OPEN-5]** MVP performance data entry is manual; platform analytics integrations are post-MVP. Confirm this is acceptable.

---

### 10.15 Voice and Commute Mode

**Description:** Voice is where the user's uncommitted attention actually is. Commute Mode is a first-class feature, not a wrapper over the text UI.

#### FR-57: Speech input and output
**Consequences:**
- The user can speak a request and hear a spoken answer without touching a screen.
- Spoken responses are concise by default — **[PROPOSED]** ≤ 3 sentences unless a Briefing is requested.
- Interruption is supported: new speech input stops playback and takes precedence.

#### FR-58: Deliver a Commute Briefing
On entering Commute Mode, a spoken briefing covering time remaining, top priorities, and a recommendation.

**Consequences:**
- Names the time available before arrival, top 3 priorities, and one explicit recommendation of what to do first.
- Completes within **[PROPOSED]** 90 seconds of speech.
- Matches the user's specified form: *"Good morning. You have 42 minutes before reaching the office. You have three important priorities today… I recommend fixing Railzy first."*

#### FR-59: Support conversational voice commands
**Consequences:**
- Supports at minimum: create Task, reschedule Task, ask priorities, ask business status, ask project status, generate content ideas, retrieve information, start an approved workflow, ask goal progress.
- Handles the user's stated examples: *"Move the Railzy task to tomorrow." / "What should I work on tonight?" / "Give me three reel ideas." / "What's the biggest risk today?" / "How far am I from the ₹1 crore target?"*
- Conversational context persists across turns within a session.

#### FR-60: Never require a screen in Commute Mode
**Consequences:**
- No voice interaction terminates in a state requiring visual confirmation.
- L3 Actions are refused in Commute Mode and deferred to the web UI (FR-40).

---

### 10.16 Context Modes

#### FR-61: Support five Context Modes
Commute, Work, Evening, Creator, Planning.

**Consequences:**
- Mode determines channel, verbosity, Tool subset, and which Notification Classes may interrupt.
- Work Mode suppresses Content and Naxova prompts (§26 Privacy).
- Creator Mode surfaces the content pipeline and generation Tools.
- Planning Mode surfaces Goals, Trajectory, Decisions and Experiments.

#### FR-62: Infer mode, allow manual override
**Consequences:**
- Inference uses time of day, day of week, and the Plan. **[PROPOSED]** Optional signals: Bluetooth connection to the car, calendar state.
- Inferred mode is displayed and always manually overridable by voice or UI.
- A manual override persists until the next scheduled mode boundary.

---

### 10.17 Briefings and Reviews

#### FR-63: Daily Briefing
**Consequences:**
- Contains: schedule, top 3 priorities, critical issues, goal trajectory, revenue status, deadlines, content requirement, recommended focus.
- Delivered at **[PROPOSED]** 06:00, and re-deliverable on request.
- Concise: **[PROPOSED]** ≤ 200 words written, ≤ 90 s spoken.

#### FR-64: Weekly Business Review
**Consequences:**
- Covers all 15 elements the user specified: revenue, goal progress, Railzy performance, content performance, freelance, Naxova, accomplishments, missed commitments, failed experiments, successful experiments, decisions, time allocation, risks, opportunities, recommended priorities.
- **Concludes with exactly three recommended focus items for next week — not twenty.**
- **[PROPOSED]** Delivered Sunday morning, the user's only clear day.

#### FR-65: End-of-Day Review
**Consequences:**
- Asks or infers: what completed, what didn't, why, what changed, what should move, whether the day advanced the Root Goal.
- Updates Task state, Goal progress, Decision Journal, Experiment results, and tomorrow's priorities.
- **[PROPOSED]** Runs at 22:30 and completes in under 2 minutes of user attention — it must not become another late-night task.

---

### 10.18 Proactive Intelligence and Accountability

**Description:** The behaviours that make this a partner rather than a database. It watches for patterns the user cannot see from inside them.

#### FR-66: Surface proactive signals
Approaching deadlines, production issues, missed KPIs, revenue gaps, repeated delays, recurring problems, opportunities, unusual changes, abandoned projects, low-value work, conflicting commitments.

**Consequences:**
- Each signal names the evidence and the recommended response.
- Signals are subject to the notification budget (FR-31); the highest-value signal wins when the budget binds.

#### FR-67: Detect procrastination patterns
Repeated postponement, excessive polishing, project proliferation, abandonment, disproportionate low-impact time, avoidance of high-value work.

**Consequences:**
- Example output: *"You've postponed Railzy SEO three times this week. Either remove it from the plan or commit a protected 90-minute block tomorrow."*
- Always paired with a concrete choice, never a bare accusation.
- **[PROPOSED]** Postponement threshold: 3 occurrences within 7 days.

#### FR-68: Detect project proliferation
**Consequences:**
- Flags when active Projects or in-flight initiatives exceed a threshold **[PROPOSED: 5 active]**.
- Names which have received no time in **[PROPOSED]** 14 days and proposes explicit pause or removal.

#### FR-69: Challenge time sinks
**Consequences:**
- When actual time on a Project materially exceeds its contribution to Goals, the Agent says so and proposes reallocation or outsourcing.
- Example: *"Your biggest time sink is content editing. Recommendation: outsource editing."*

#### FR-70: Flag sacrificed Protected Blocks
**Consequences:**
- Repeated loss of a Protected Block is raised with the count and the displacing work.
- Escalates to Important after **[PROPOSED]** 2 consecutive weeks.

---

### 10.19 Time Allocation Analysis

#### FR-71: Track planned vs. actual time per Project
**Consequences:**
- Weekly table per Project: planned hours, actual hours, variance.
- **[OPEN-6]** Actual-time capture method is undecided — manual confirmation, inference from Events, or active timing. Inference is cheapest but least accurate.

#### FR-72: Analyse allocation against priorities
**Consequences:**
- Reports whether time matched stated priorities, where it was lost, and where it should shift.
- Feeds the Weekly Business Review and FR-69.

---

### 10.20 Project Management

#### FR-73: Model Projects, not just Tasks
**Consequences:**
- Projects at MVP: Railzy, Content / Explore The Unmapped, Freelance Client, Naxova, Personal / Life.
- Each holds objective, status, roadmap, backlog, Tasks, deadlines, risks, dependencies, KPIs, Decisions, documentation.
- Every Task belongs to exactly one Project.

#### FR-74: Answer project-level questions
**Consequences:**
- Supports: what's wrong, what's next, top technical risks, what's blocking growth, highest-value feature.
- Answers cite the underlying Tasks, Events or KPIs.

#### FR-75: Track Naxova formation without assuming it exists
**Consequences:**
- Naxova is modelled as **not yet legally formed, with no website**.
- Tracks: formation steps, legal/admin tasks, branding, domain, website, products, revenue, opportunities, ad monetisation, future Railzy relationship.
- No output implies Naxova is an operating company until its formation status says so.

---

### 10.21 Railzy and GitHub Integration

#### FR-76: Understand the Railzy codebase and operations
**Consequences:**
- Ingests repository, branches, commits, PRs, issues, deployment and production status, domain, infrastructure, bugs, roadmap, backlog.
- **[OPEN-7]** Analytics, SEO and business-metric sources for Railzy are not yet identified. **[ASSUMPTION]** the domain is `railzy.in` — the user wrote "railzy.on", presumed a typo.

#### FR-77: Summarise Railzy state on demand
**Consequences:**
- Answers "what is currently wrong with Railzy?", "what should I work on next?", "top 5 technical risks", "what's blocking growth?", "highest-value feature?"
- Every answer is grounded in retrievable artifacts, never inferred from the project name.

#### FR-78: Provide GitHub read capability (L0)
**Consequences:**
- Repositories, issues, PRs, commits, branches, releases, CI/CD status, deployment status where available.

#### FR-79: Provide GitHub write capability under permission
**Consequences:**
- Create issue, update issue, comment: **L1**.
- Prepare commit, prepare PR, summarise PR, review code: **L1** (preparation only).
- Push, merge, and any production-affecting change: **L2** minimum.
- Production deployment: **L3**.

---

### 10.22 Revenue and Expense Intelligence

#### FR-80: Track all Revenue Streams
Salary, Freelance, Railzy, Content, Sponsorships, Affiliate, Naxova, Other.

**Consequences:**
- Each Revenue Record carries stream, amount, date, and classification.

#### FR-81: Distinguish revenue classifications
Actual, Expected, Pipeline, Projected, and probability-weighted.

**Consequences:**
- Trajectory (FR-8) uses Actual only; Expected and Pipeline are shown separately and never silently merged.
- Probability-weighted figures always display the probability applied.

#### FR-82: Identify highest-potential opportunities
**Consequences:**
- Ranks opportunities by probability-weighted value against effort.
- Each ranking exposes its inputs (P-7).

#### FR-83: Warn on unrealistic revenue assumptions
**Consequences:**
- When an Expected or Pipeline figure implies a rate far outside historical Actuals, the Agent challenges it explicitly and states the implied multiple.
- This applies to the Root Goal itself (FR-9).

#### FR-98: Capture an earning in seconds, from any channel
The user records earnings continuously as they happen, including by voice. **[CONFIRMED — his stated working method.]**

**Consequences:**
- Logging one earning takes **[PROPOSED]** ≤ 15 seconds and ≤ 3 inputs: amount, stream, and optionally a note.
- Available by voice in Commute Mode — *"log forty thousand from the client"* — because that is when he has free attention and the desk is not available.
- Stream is inferred from context where possible and confirmed, not typed.
- Date defaults to today and is overridable for retrospective entry (CFR-53).

#### FR-99: Record planned earnings as forward pipeline
The user plans the next earning alongside logging the last. **[CONFIRMED.]**

**Consequences:**
- A planned earning is a Pipeline Revenue Record with expected amount, stream, expected date, and probability.
- Pipeline is never merged into Trajectory (FR-81); it is displayed as a separate, clearly-labelled line.
- When an expected date passes without a matching Actual, the record is flagged `slipped` and surfaced — not silently carried forward.

#### FR-100: Operate correctly with an unallocated goal split
The Root Goal may run with no child targets set, and the engine proposes a split from evidence once data exists.

**Consequences:**
- With child targets `null`, the engine still computes Required Pace, Actual Pace, Trajectory and Gap **for the Root Goal**, and reports children as unallocated (FR-6).
- After **[PROPOSED]** 4 weeks of Revenue Records, the system proposes a split derived from where earnings actually came from, with the evidence.
- The proposed split is a Recommendation the user accepts or rejects — never applied automatically.
- Until a split exists, the engine says which stream is *producing*, not which stream is *behind* — it does not invent a target to measure against (P-3).

#### FR-101: Record expenses continuously, at the same friction budget
The user enters expenses as well as earnings. **[CONFIRMED — his stated working method.]**

**Consequences:**
- Same capture contract as FR-98: **[PROPOSED]** ≤ 15 seconds, ≤ 3 inputs, voice-capable.
- Each Expense Record carries amount, date, category, Project attribution, and recurrence (one-off / monthly / annual).
- Expense categories at minimum: infrastructure/hosting, tools and subscriptions, content production, legal and company formation, contractor/staff, marketing, personal.
- A recurring expense is entered once and generates forward records automatically; the user is never asked to re-enter a monthly cost.

#### FR-102: Compute net position and per-Project profitability
**Consequences:**
- Gross earnings, total expenses and **net** are each computed and reported separately — this resolves the revenue-versus-take-home ambiguity by showing both rather than choosing (**[OPEN-1]**).
- **Profitability per Project** = attributable revenue − attributable expenses, over any window.
- A Project whose expenses exceed its revenue is flagged explicitly, with the monthly bleed stated.
- Unattributed expenses are held in an explicit `unattributed` bucket, never silently spread across Projects.

#### FR-103: Make prioritisation profit-aware
The Priority Engine's revenue factor uses **net contribution**, not gross.

**Consequences:**
- `RevenueImpact` is computed from expected net effect, so work that raises revenue while raising costs more is ranked accordingly.
- A Project running at a loss raises its own `RiskReduction` weighting — cost-cutting work on a bleeding Project competes properly against growth work elsewhere.
- **[PROPOSED]** The Agent surfaces any subscription or recurring cost attached to a Project that has produced no revenue in 60 days, as a `do_not_do` / cancel candidate.

#### FR-104: Track burn rate and runway
**Consequences:**
- Monthly burn (recurring + trailing average one-off) is computed and shown on the Dashboard.
- Where a Project has a committed forward cost (contractors, hosting), its runway against attributable revenue is stated.
- Rising burn against flat revenue is a proactive signal (FR-66), raised as Important.

---

### 10.23 Business Dashboard

#### FR-84: Present the goal cockpit
**Consequences:**
- Shows: ₹1 crore target, actual revenue, projected revenue, gap, days remaining, Required Pace, Trajectory, confidence.
- Above the fold, without interaction.

#### FR-85: Present per-Project panels
**Consequences:**
- **Railzy** — users, active users, revenue, growth, SEO, conversions, key issues.
- **Content** — views, subscribers/followers, engagement, revenue, publishing frequency, top performers.
- **Freelance** — revenue, workload, deadlines, client status.
- **Naxova** — formation status, business progress, revenue, opportunities.
- Any panel lacking a data source displays "no data source connected" rather than zero (P-3).

#### FR-86: Present the Agent Assessment
A written judgement, not just numbers.

**Consequences:**
- States trajectory position, largest growth opportunity, biggest time sink, and one recommendation.
- Refreshes at least daily and after any material change.

---

### 10.24 Web UI

#### FR-87: Provide the fourteen UI sections
Dashboard, Agent, Tasks, Calendar/Schedule, Projects, Goals/KPIs, Revenue, Memory, Decisions, Experiments, Notifications, Integrations, Audit Log, Settings.

**Consequences:**
- Every section is reachable within two clicks of the Dashboard.
- Each renders a usable empty state before any data exists.

#### FR-88: Render the Agent Office
The Agent section visualises Worker Roles as employees in an office, with the Agent directing them.

**Consequences:**
- Each employee shows role, current task, status (idle / working / blocked / awaiting approval), elapsed time, and token/cost.
- **Usability and performance take precedence over the metaphor** — the visualisation must not delay comprehension or degrade the UI.
- **[PROPOSED]** A plain list view is available as a toggle and is the default on first load until the user opts into the office view.

#### FR-89: Apply the HUD aesthetic without sacrificing usability
**Consequences:**
- Dark, glowing, HUD-styled — but text remains legible and interactive targets remain standard-sized.
- The aesthetic must not increase time-to-comprehension for the Dashboard (NFR-5).

---

### 10.25 Observability and Audit

#### FR-90: Maintain an immutable Audit Log
**Consequences:**
- Records what the Agent did, when, why, which Tool, inputs, outputs, approval, result, errors.
- Append-only; no deletion or edit path exists in the application.
- Fully inspectable and filterable from the UI.

#### FR-91: Answer "why did the agent do this?"
**Consequences:**
- Any Action links to the Recommendation, Plan or trigger that caused it, and the Goal it served.

#### FR-92: Track operational metrics
**Consequences:**
- Agent executions, Tool executions, latency, errors, failed tasks, token/API usage, model usage, notification counts, automation success rate.
- Cost per day and per Project is retrievable.

---

### 10.26 Configuration, Secrets and Naming

#### FR-93: Externalise all configuration
**Consequences:**
- Configuration, secrets, user data and logs are stored separately.
- No secret is ever written to a log, an Event, or the Audit Log.

#### FR-94: Manage credentials securely
**Consequences:**
- Never hardcode API keys, tokens, passwords or OAuth secrets.
- Supports storage, rotation, revocation, integration disconnect, and permission review.
- Disconnecting an integration revokes its stored credential.

#### FR-95: Enforce the naming rule
**Consequences:**
- One configuration key — `AGENT_NAME`, default `"Jarvis"` — is the single source of truth.
- Code uses neutral identifiers throughout: modules, classes, packages, DB tables, API routes, env prefixes (`AGENT_`, never `JARVIS_`).
- **Acceptance test:** `grep -ri jarvis` across source returns zero hits outside the config default and message templates.
- Renaming requires changing exactly one configuration value.

#### FR-96: Abstract the model provider
**Consequences:**
- All LLM access passes through a single provider interface.
- Cloud and local providers are both supported and selectable by configuration.
- Model selection is configurable per task class **[PROPOSED]** — cheap models for classification, stronger models for planning and advice.
- No provider-specific type or call appears outside the provider adapter.

#### FR-97: Start automatically and greet
**Consequences:**
- The system starts when the machine starts, without user login **[PROPOSED: Windows Service]**, so the 06:00 trigger can fire after an overnight reboot.
- On start it emits a welcome message through the configured channel.
- Startup failure is surfaced visibly rather than failing silently.

---

## 11. Non-Functional Requirements

Cross-cutting. Feature-specific NFRs are stated inline in §10.

| ID | Requirement |
|---|---|
| **NFR-1** | **Local-first.** The MVP runs entirely on the user's machine — local database, local configuration, local memory, local web UI, local agent engine. No server dependency for core function. |
| **NFR-2** | **Cloud-ready.** Architecture must permit later cloud deployment of the Scheduler and Notifier without redesign. The local agent dials out; no inbound ports are ever required. |
| **NFR-3** | **Provider independence.** No coupling to a single LLM vendor. Swapping providers is configuration (FR-96). |
| **NFR-4** | **Modularity.** Scheduler, Notifier, Executor, Memory, Priority Engine and Goal Engine are independently testable and independently replaceable. |
| **NFR-5** | **Responsiveness.** Voice response begins within **[PROPOSED]** 2 s. Dashboard renders within 1.5 s. A loop pass completes within 60 s. |
| **NFR-6** | **Spoken brevity.** Any response deliverable by voice fits in ≤ 3 sentences unless it is an explicitly requested Briefing. |
| **NFR-7** | **Low cost.** Running cost is tracked and reportable (FR-92). **[OPEN-8]** A monthly ceiling is not yet set. |
| **NFR-8** | **Attention economy.** Notification volume is budgeted and tracked (FR-31). Silence is a valid output. |
| **NFR-9** | **Fatigue awareness.** No decision-heavy prompt after 22:30. Anything answerable earlier is asked earlier. |
| **NFR-10** | **Durability.** No user data loss on crash or power failure. Schedules, Tasks and Events survive restart. **[PROPOSED]** Automatic local backup daily, retained 30 days. |
| **NFR-11** | **Restart safety.** A restart mid-Action never repeats a completed side effect (FR-45). |
| **NFR-12** | **Auditability.** Every Action is traceable to its cause and its approver, permanently. |
| **NFR-13** | **Maintainability.** Single-developer maintainable — conventional structure, no exotic infrastructure, runnable with one command. |
| **NFR-14** | **Testability.** Priority Engine, Goal Engine and Scheduler are deterministic and unit-testable without an LLM call. |
| **NFR-15** | **Security by default.** New Tools default to L2. Secrets are never logged. L3 requires local UI confirmation. |
| **NFR-16** | **Privacy.** Employer- and client-confidential data never reaches a hosted model (FR-44). |
| **NFR-17** | **Windows-first.** The MVP targets the user's Windows environment and must run there natively. Cross-platform is not an MVP requirement. |
| **NFR-18** | **No fabrication.** Missing data renders as "no data source connected", never as zero or an estimate. |
| **NFR-19** | **Graceful degradation.** LLM unavailability disables advice but leaves Scheduler, Notifier, Tasks and Audit fully functional. |
| **NFR-20** | **Honest limitation disclosure.** The system states plainly, at setup and on missed triggers, that scheduled notifications require the machine to be running. |

---

## 12. User Journeys

### UJ-1. Laxmikant learns what actually matters before he reaches the office

Laxmikant, TPM by day and running three ventures in the margins, reverses out of the driveway at 10:02 on a Wednesday. He is already authenticated; the system has been running since the machine booted. His phone connects to the car and the system infers **Commute Mode**.

He says *"good morning."* The spoken briefing comes back in under ninety seconds: twenty-eight minutes to the office; Railzy signup failures affected fourteen users overnight; the client standup is at 20:00; tonight's reel has no footage selected. Then one recommendation — fix Railzy signups first, because acquisition is the current bottleneck on the only Project with revenue upside inside the six-month window.

**Climax:** he replies *"block ninety minutes tonight for Railzy, move the Naxova research to Sunday"* — and the system confirms the revised Plan aloud before he reaches the highway.

**Resolution:** he arrives at the office with the day already decided. The Plan is updated, the Naxova Task is rescheduled, and a Protected Block exists for tonight.

**Edge case:** if the machine was off overnight, the briefing opens by saying which triggers it missed and that the Railzy data is stale as of the last run — it does not present old data as current.

### UJ-2. The system stops him from spending an evening badly

It is 21:40 on a Thursday. Laxmikant opens the web UI and starts a Task called *"polish Railzy landing page spacing."*

The Agent interrupts once: that Task scores P4; meanwhile the signup bug is P1, unresolved for three days, and estimated at 45 minutes. It states the difference in plain terms — one affects revenue and live users, the other does not.

**Climax:** he switches. Forty minutes later the bug is fixed and the Event is recorded against the Railzy Goal.

**Resolution:** the polish Task remains at P4. It surfaces again in Sunday's review as a deletion candidate, not as a nightly nag.

**Edge case:** if he proceeds with the polish anyway, the Agent drops it immediately and records the override. It appears once more — in the weekly time-allocation analysis, as data, not as a scold.

### UJ-3. He finds out in month two, not month five, that the plan doesn't add up

Sunday morning, Planning Mode. The Weekly Business Review opens with the arithmetic: eight weeks elapsed, ₹X actual against a required ₹1.33 crore-pace-to-date, and a projected six-month total well short of target.

The Agent does not soften it. It states which assumption is carrying the plan — that content revenue reaches a level it has never reached — and quantifies what that would require: a multiple on current run-rate that no observed week supports.

**Climax:** it presents the three options that could close the gap, ranked by probability-weighted value against effort, and names the one it recommends.

**Resolution:** he picks one. It becomes a Decision with its reasoning and a Review Trigger at four weeks. The Goal tree is re-weighted; next week's plan reflects the new allocation.

**Edge case:** if fewer than fourteen days of revenue data exist, the review says "insufficient history to project" and asks for the missing inputs instead of producing a confident wrong number.

### UJ-4. He asks why a decision was made four months ago

Driving home, he asks: *"why didn't we build the Railzy mobile app?"*

The system returns Decision #128 in two sentences — postponed because API and infrastructure costs were too high, to be revisited when Railzy revenue exceeded ₹1 lakh/month — and adds that Railzy revenue crossed that threshold eleven days ago, so the Review Trigger has fired and the Decision is awaiting reconsideration.

**Climax:** the reasoning is available at the moment it is relevant, in the car, without a search.

**Resolution:** he asks for it to be added to Sunday's review with a cost estimate attached.

### UJ-5. The night's reel ships without becoming a crisis

23:10, Creator Mode. The system has already flagged that today's publish slot has no source footage — it warned at 10:00, when he could still act, not at 23:10 when he cannot.

Because it warned early, a footage-light format was selected during the commute. The title, hook, description, tags and three per-platform captions are drafted and waiting.

**Climax:** one approval publishes to all three platforms — or, at MVP, produces the copy-paste bundle in one place.

**Resolution:** the Content Item moves to `published`; performance collection is scheduled for 72 hours later, feeding FR-56.

**Edge case:** if no footage exists at all, the system says so plainly and offers the footage-light options rather than pretending an asset is ready.

---

## 13. UX Requirements and Information Architecture

### 13.1 Principles

1. **Voice is a first-class surface, not an accessory.** Every high-frequency action has a voice path.
2. **The dashboard answers one question above the fold:** *am I on track, and what do I do next?*
3. **Every number is traceable.** Clicking any figure reveals its source and freshness.
4. **The metaphor serves the work.** The office view is a way to see agent activity, not a reason to slow it down.
5. **Empty states teach.** Before data exists, each section explains what will live there and how to populate it.
6. **Bluntness is visual too.** Being behind trajectory is shown plainly, not softened by design.

### 13.2 Information Architecture

| # | Section | Primary content |
|---|---|---|
| 1 | **Dashboard** | Goal cockpit, trajectory, Agent Assessment, today's Plan, top 3 priorities |
| 2 | **Agent** | Office view of Worker Roles, live activity, pending approvals, cost/time per role |
| 3 | **Tasks** | Backlog with Priority Scores and factor breakdown; filter by Project and Band |
| 4 | **Calendar / Schedule** | Day and week view, Protected Blocks, fixed commitments, Plan vs. actual |
| 5 | **Projects** | Railzy, Content, Freelance, Naxova, Personal — each with objective, status, roadmap, backlog, risks, KPIs |
| 6 | **Goals / KPIs** | Goal tree, required pace, trajectory, gap, confidence, history |
| 7 | **Revenue** | Streams, records by classification, pipeline, projections, opportunity ranking |
| 8 | **Memory** | Six partitions, browsable and searchable, with confidentiality classification visible |
| 9 | **Decisions** | Decision Journal, status, Review Triggers, fired triggers awaiting reconsideration |
| 10 | **Experiments** | Active and concluded, with hypothesis, metric, baseline, result |
| 11 | **Notifications** | History, class, channel, delivery status, daily budget consumption |
| 12 | **Integrations** | Tool Registry, connection status, Permission Level per Tool, credential management |
| 13 | **Audit Log** | Immutable Action history, filterable, with rationale links |
| 14 | **Settings** | Agent name, routine and fixed commitments, quiet hours, channels, model providers, permission defaults, backup |

### 13.3 Aesthetic and Tone

- **Visual:** JARVIS-style HUD — dark ground, luminous accents, technical/telemetric character. Reference: Iron Man HUD. **Anti-reference:** generic SaaS dashboards; anything that reads as a consumer to-do app.
- **Constraint:** the aesthetic never wins over legibility, target size, or render performance (FR-89).
- **Voice and tone of generated text:** direct, concise, evidence-first. States the conclusion, then the reason. No filler openings, no congratulation, no hedging where data is clear — and explicit uncertainty where it is not.
- **[OPEN-9]** Whether the office view is literal (floor plan, avatars, motion) or abstract (status cards / node graph using office language) is undecided and materially changes effort. FR-88 proposes shipping the list view first.

---

## 14. System Architecture

**Shape:** a single local process hosting the Agent, the two primitives, and the web UI, over a local database. Deliberately modest — NFR-13 requires one developer can maintain it.

```
┌──────────────────────────────────────────────────────────────────┐
│  Channels        Web UI (local)   Telegram   WhatsApp   Voice I/O│
└───────────────────────────┬──────────────────────────────────────┘
                            │  (channel adapters — interface-bound)
┌───────────────────────────▼──────────────────────────────────────┐
│                        NOTIFIER  (§22)                           │
│        classification · budget · quiet hours · fallback          │
└───────────────────────────▲──────────────────────────────────────┘
                            │
┌───────────────────────────┴──────────────────────────────────────┐
│                     AGENT ORCHESTRATION LAYER                    │
│   loop: Goal→Plan→Prioritize→Execute→Measure→Learn→Replan        │
│   Worker Roles = prompt profile + Tool subset (not processes)    │
└──┬─────────┬──────────┬──────────┬──────────┬────────────┬───────┘
   │         │          │          │          │            │
┌──▼───┐ ┌───▼────┐ ┌───▼─────┐ ┌──▼──────┐ ┌─▼────────┐ ┌─▼──────┐
│GOAL  │ │PRIORITY│ │ PLANNER │ │SCHEDULER│ │ EXECUTOR │ │PERMIS- │
│ENGINE│ │ ENGINE │ │+ REPLAN │ │  (§21)  │ │ + TOOLS  │ │ SIONS  │
│(§24) │ │ (§25)  │ │         │ │         │ │  (§20)   │ │ (§19)  │
└──┬───┘ └───┬────┘ └───┬─────┘ └────┬────┘ └────┬─────┘ └───┬────┘
   └─────────┴──────────┴────────────┴───────────┴───────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│   MEMORY (§16)   User │ Knowledge │ State │ Decisions │ Events │ Goals │
├──────────────────────────────────────────────────────────────────┤
│   LLM PROVIDER INTERFACE (§17)   cloud ⇄ local, per-task-class    │
├──────────────────────────────────────────────────────────────────┤
│   AUDIT LOG (append-only)  ·  OBSERVABILITY  ·  SECRETS STORE     │
└──────────────────────────────────────────────────────────────────┘
```

**Load-bearing boundaries** — each is a seam the design depends on:

1. **Scheduler ⇄ Notifier.** The Scheduler emits Notification requests and knows no channel. This is what permits the phase-2 cloud lift (NFR-2).
2. **Notifier ⇄ channel adapters.** Adding a channel or swapping WhatsApp for a PSTN call touches only an adapter.
3. **Agent ⇄ LLM provider.** No provider type escapes the adapter (FR-96).
4. **Executor ⇄ Tool Registry.** Tools are data-described and permission-tagged; adding one requires no executor change.
5. **Engines ⇄ LLM.** Goal, Priority and Scheduler logic is deterministic and LLM-free (NFR-14). The LLM explains and advises; it does not compute the arithmetic.

**[PROPOSED] Technology direction** — the user's brief nominates Python/FastAPI backend with Next.js/React/TypeScript/Tailwind frontend, PostgreSQL + pgvector, Redis, and a task queue. For a **local-first single-user MVP on Windows**, Postgres + Redis + a queue is heavy operational surface for one developer. A lighter local stack (embedded relational DB, in-process scheduling, no broker) is worth considering, with the heavier stack introduced at the phase-2 cloud lift. This is a recommendation, not a decision — see `recommendations.md` R-4. Final technology selection belongs to `bmad-architecture`.

---

## 15. Agent Architecture

**One Agent. Many Worker Roles. No agent swarm.** The user was explicit: prefer a single orchestration layer with specialised capabilities unless there is a strong technical reason to separate. The office metaphor is a UX layer (§13.2), not a process model.

**A Worker Role is:** a name, a prompt profile, a Tool subset, and a permission ceiling. It is selected per unit of work and recorded on every Action.

| Worker Role | Tools | MVP |
|---|---|---|
| **Researcher** | web research, browser (read), filesystem (read) | ✅ |
| **Developer** | GitHub, filesystem, shell (if enabled) | ✅ |
| **Content Manager** | document generation, filesystem, messaging (draft) | ✅ |
| **Business Analyst** | memory query, goal/revenue computation, document generation | ✅ |
| **SEO Analyst** | web research, analytics | Post-MVP |
| **Scheduler Role** | scheduler management | Post-MVP |
| **Data Analyst** | analytics, computation | Post-MVP |

**Execution model:** a request resolves to a Worker Role, a plan of Actions, and a permission decision per Action. Actions execute sequentially by default; parallelism is an optimisation, not a requirement, at MVP.

**Escalation:** the Agent never escalates its own permission ceiling. A role needing an L2 Tool raises an Approval; it does not select a different role to route around the restriction.

---

## 16. Memory Architecture

Six partitions with distinct schemas, retention rules and mutability (FR-42).

| Partition | Mutability | Retention | Primary consumers |
|---|---|---|---|
| **User** | Slow-changing, versioned | Indefinite | Planner, Notifier, all prompts |
| **Knowledge** | Append + version | Indefinite | Researcher, Business Analyst, Q&A |
| **State** | Live | Current + rolling history | Planner, Priority Engine, Dashboard |
| **Decisions** | Append-only; status mutable | Indefinite | Decision Journal, Agent advice |
| **Events** | Immutable, append-only | Indefinite | Time allocation, learning, audit |
| **Goals** | Live + full history | Indefinite | Goal Engine, Dashboard, Trajectory |

**Cross-cutting rules**

- Every record carries a **confidentiality classification** (Public / Personal / Client-Confidential / Employer-Confidential). Classification governs which model may see it (FR-44).
- **Retrieval is partition-aware.** Context assembly draws deliberately from named partitions, not from one undifferentiated similarity search.
- **[PROPOSED]** Semantic search over Knowledge uses embeddings; State, Goals and Events are queried relationally. Decisions and Events are never summarised destructively — the original record is always retained.
- **Provenance is mandatory.** Every answer names the partition and record it came from (FR-43).

---

## 17. LLM Provider Architecture

- A **single provider interface** — completion, streaming, tool-calling, embeddings — with adapters per provider (FR-96).
- **Per-task-class model selection [PROPOSED]:** classification and extraction on a cheap model; planning, advice and the Weekly Review on a strong model; anything touching Client- or Employer-Confidential data on a **local** model only (FR-44).
- **Graceful degradation (NFR-19):** if no provider is reachable, deterministic functions — Scheduler, Notifier, Tasks, Priority scoring, Goal arithmetic — continue unaffected. Only advice and generation degrade, and the UI says so.
- **Cost accounting:** tokens and cost recorded per Action, aggregated per day and per Project (FR-92).

---

## 18. Data Model

Indicative entities and key relationships, for `bmad-architecture` to refine.

| Entity | Key fields | Relationships |
|---|---|---|
| **Goal** | id, parent_id, name, target_value, unit, current_value, deadline, status, confidence, owner | self-referencing tree; ← KPI, RevenueRecord |
| **KPI** | id, goal_id, project_id, name, value, unit, source_type, last_refreshed, expected_interval | → Goal, Project |
| **Project** | id, name, objective, status, roadmap, risks | ← Task, Decision, KPI, Document |
| **Task** | id, project_id, title, description, effort_estimate, attention_type, deadline, status, priority_score, priority_band | → Project; ← PriorityFactor, Event |
| **PriorityFactor** | id, task_id, factor_name, value, weight, contribution | → Task |
| **Plan** | id, date, status, approved_at | ← PlanItem |
| **PlanItem** | id, plan_id, task_id, start, end, protected, goal_id | → Plan, Task |
| **ScheduledTrigger** | id, name, type, cron/rrule, condition, notification_class, enabled, last_fired | → Notification |
| **Notification** | id, class, title, body, channel, status, sent_at, batched | → ScheduledTrigger |
| **Tool** | id, name, capability, input_schema, output_schema, side_effects, permission_level, requires_confirmation | ← Action |
| **Action** | id, tool_id, worker_role, inputs, outputs, permission_decision, approver, started_at, duration, result, error, cost_tokens | → Tool; ← AuditEntry |
| **Approval** | id, action_id, level, requested_at, expires_at, granted_at, channel | → Action |
| **Decision** | id, date, statement, reasoning, alternatives, expected_outcome, review_trigger, status, project_id | → Project; ← Experiment |
| **Experiment** | id, hypothesis, objective, action, metric, baseline, target, duration, result, conclusion, decision_id | → Decision |
| **RevenueRecord** | id, stream, amount, currency, date, classification, probability, source | → Goal |
| **ContentItem** | id, idea, concept, footage_ref, title, hook, description, tags, hashtags, thumbnail_idea, caption, platform_copy, publish_date, status | ← ContentPerformance |
| **ContentPerformance** | id, content_item_id, platform, views, watch_time, retention, likes, comments, shares, saves, subs_gained, revenue, collected_at | → ContentItem |
| **Event** | id, type, payload, occurred_at, project_id, task_id | immutable |
| **MemoryRecord** | id, partition, content, embedding, classification, source, created_at | partition-scoped |
| **AuditEntry** | id, action_id, what, why, approval_ref, result, timestamp | append-only |

**Invariants**

- Every Task belongs to exactly one Project.
- Every child Goal's rollup contributes to its parent.
- `Event` and `AuditEntry` have no update or delete path.
- `Action` cannot exist without a resolved permission decision.
- Trajectory is computed only from `RevenueRecord.classification = 'actual'`.

---

## 19. Permission Model

Defined in FR-38 through FR-41. Design rules:

1. **Fail closed.** Unknown Tool, unknown level, or unresolved approval ⇒ no execution.
2. **Default L2.** A newly registered Tool is L2 until deliberately lowered.
3. **L3 is never pre-granted.** No standing rule, no batch approval, no "always allow."
4. **L3 confirmation is local-UI only [PROPOSED].** A compromised chat channel must not be able to authorise a destructive action.
5. **Approvals expire** (FR-39) and are single-use.
6. **Permission changes are audited** like any other Action.
7. **Escalation is impossible from inside.** The Agent cannot raise its own ceiling.

---

## 20. Tool Architecture

Every Tool declares capability, input schema, output schema, side effects, default Permission Level, and confirmation requirement (FR-34).

| Tool | Default level | Notes |
|---|---|---|
| Filesystem (read) | L0 | Restricted to configured roots |
| Filesystem (write) | L1 | Within configured roots only |
| Web research | L0 | Read-only |
| GitHub (read) | L0 | Repos, issues, PRs, CI status |
| GitHub (write — issue/comment) | L1 | Reversible |
| GitHub (push / merge) | L2 | |
| GitHub (production deploy) | L3 | |
| Browser automation | L2 | Read-only browsing may be L1 **[PROPOSED]** |
| Document generation | L1 | Local artifacts |
| Messaging (draft) | L1 | |
| Messaging (send) | L2 | Outward-facing |
| Content publishing | L2 | Outward-facing |
| Local shell | L3 | **Disabled by default**, opt-in only |
| Database destructive ops | L3 | Reversal path required (FR-45) |

**Prompt-injection containment:** content fetched by a Tool is data, never instruction. Web pages, issue bodies, emails and file contents cannot alter the Agent's permission decisions or trigger Actions on their own. Any Action originating from fetched content is treated as untrusted and requires approval regardless of the Tool's normal level. **[PROPOSED]** — this rule is added by this PRD because the user's spec did not cover it, and it is the primary attack path against an agent with tool access.

---

## 21. Scheduler Architecture

- **Persistent triggers.** Schedule state lives in the database and survives restart (FR-25).
- **Tick-based evaluation.** A single scheduling loop evaluates due triggers; conditional triggers are evaluated on each loop pass.
- **Emits requests, not deliveries.** Output is a Notification request handed to the Notifier (FR-27).
- **Catch-up on start.** Triggers missed while the machine was down are identified and reported; Critical ones are re-raised, Informational discarded (FR-28).
- **No inbound network requirement.** Nothing about the Scheduler needs a public endpoint — this is what makes both the local MVP and the phase-2 cloud lift work.

---

## 22. Notification Architecture

```
Scheduler / Agent  ──▶  Notifier  ──▶  Channel Adapter  ──▶  User
                          │
                    classify · budget · quiet hours ·
                    mode-routing · fallback · record
```

- **Classification first** (FR-29), then budget (FR-31), then quiet hours (FR-32), then channel selection by Context Mode.
- **Channel adapters are interchangeable.** Web UI, Telegram, WhatsApp at MVP; PSTN call is an adapter, not a redesign (FR-33).
- **Fallback chain** on delivery failure, with the failure recorded.
- **This interface is the phase-2 seam.** Moving the Notifier to a cloud host changes deployment, not callers (NFR-2).

---

## 23. Integration Architecture

| Integration | MVP | Notes |
|---|---|---|
| GitHub | ✅ | Full read; scoped write under permission |
| Filesystem | ✅ | Configured roots only |
| Browser | ✅ | Automation under L2 |
| Web research | ✅ | |
| Telegram | ✅ | Long-polling — works behind NAT, no public endpoint |
| WhatsApp | ✅ | **[OPEN-3]** route undecided |
| Voice (STT/TTS) | ✅ | **[OPEN-10]** local vs. cloud engines undecided |
| Google Calendar / Gmail | ❌ | Post-MVP |
| YouTube / Instagram / Facebook APIs | ❌ | Post-MVP; MVP produces publish bundles |
| Google Analytics / Search Console | ❌ | Post-MVP |
| Payment systems | ❌ | Post-MVP |

Every integration is a Tool in the registry, carries a credential managed under FR-94, and can be disconnected — revoking its credential — from the Integrations UI.

---

## 24. Goal and KPI Architecture

- **Tree.** Root Goal → Project Goals → sub-Goals, rolling up (FR-6).
- **Deterministic arithmetic.** Required Pace, Trajectory and Gap are computed in code, not by an LLM (NFR-14). The LLM explains and advises on the numbers; it never produces them.
- **Actuals only for Trajectory.** Expected, Pipeline and Projected are displayed separately and never merged into the trajectory line (FR-81).
- **Insufficient history is a first-class state**, not a zero (FR-8).
- **Confidence** is derived from data completeness, KPI freshness and history length, and is always displayed alongside a projection.

---

## 25. Priority Algorithm

**[PROPOSED] — the shape is specified; the weights need the user's calibration.**

```
PriorityScore =
      w1 · RevenueImpact
    + w2 · BusinessImpact
    + w3 · UserImpact          (live-product harm weighs heavily)
    + w4 · Urgency             (derived from deadline proximity)
    + w5 · StrategicImportance (alignment to Root Goal path)
    + w6 · RiskReduction
    + w7 · DependencyUnblocking
    − w8 · Effort
    − w9 · OpportunityCost
```

**Rules**

- Factors are normalised to a common scale; weights are configuration.
- The full breakdown is always retrievable (FR-16, P-7).
- A Task affecting live Railzy users carries a floor on UserImpact — production harm cannot be outranked by convenience work.
- Bands: P1 / P2 / P3 / P4 by configurable thresholds (FR-13).
- **Determinism:** identical inputs always produce an identical score. No LLM in the scoring path; the LLM may *estimate a factor value* when the user has not supplied one, and such estimates are marked as estimated.
- **Worked examples** (from the user's spec): *fix Railzy signup bug* (impact H, revenue H, user H, urgency H, effort 45 min) ⇒ **P1**. *Change button radius 10 → 12px* (impact L, revenue L, effort 30 min) ⇒ **P4**.

**[OPEN-11]** Initial weights are undecided. Proposed starting point: revenue and user impact dominant, effort a moderate penalty, opportunity cost active only when a P1 exists.

---

## 26. Security and Privacy

**Security**

- Secrets stored in a dedicated store, never in code, logs, Events, or the Audit Log (FR-93, FR-94).
- Credential lifecycle: storage, rotation, revocation, disconnect, periodic permission review.
- L3 actions require local-UI confirmation (§19).
- Prompt-injection containment: fetched content is data, never instruction (§20).
- No inbound network exposure in the MVP. All channel connections are outbound.
- **[PROPOSED]** Encryption at rest for the memory store and the secrets store — the machine holds the user's entire professional and personal life.
- Dependencies pinned; third-party tools and skills vetted before registration.

**Privacy**

- **Employer/client firewall (NFR-16, FR-44).** Gate6 and freelance-client material is classified and excluded from hosted-model calls. This protects the user's employment and contractual position and is not negotiable.
- **[PROPOSED]** A dedicated WhatsApp number, never the personal one — unofficial bridges authenticate as the user, and a ban or a breach would compromise his primary personal communications.
- Local-first by default; nothing leaves the machine unless the user connects it (P-9).
- The user can inspect, export and delete any memory record except immutable Event and Audit entries, whose deletion is deliberately not offered.

---

## 27. Local-First Architecture and Deployment

**MVP**

- Runs entirely on the user's Windows machine: local database, configuration, memory, web UI and agent engine (NFR-1).
- **Starts as a Windows Service [PROPOSED]** rather than a Startup-folder entry, so triggers fire after an overnight reboot without a login (FR-97).
- Emits a welcome message on start.
- Outbound-only connections: Telegram long-polling and the WhatsApp bridge need no public IP, no port forwarding, no router configuration.
- **States its limitation plainly** (NFR-20): scheduled notifications only fire while the machine is running.

**Phase 2 — cloud lift (designed for, not built)**

- Only the Scheduler and Notifier move to a small always-on host.
- The local agent **dials out**; no inbound ports are opened.
- Nudges then fire regardless of machine state; execution Tasks queue until the local agent reconnects.
- Because the two primitives are already separate and the Notifier is interface-bound, this is a deployment change, not a rewrite (NFR-2).

---

## 28. Testing Strategy

| Layer | Approach |
|---|---|
| **Deterministic engines** | Unit tests without any LLM call — Priority Engine, Goal Engine arithmetic, Scheduler trigger evaluation, notification budgeting and quiet hours (NFR-14). |
| **Permission model** | Exhaustive tests per level; explicit negative tests that an unregistered Tool, an expired Approval, and an L3 request from a chat channel all fail closed. |
| **Memory partitions** | Schema-level tests that a write to the wrong partition fails, and that Client/Employer-Confidential records are excluded from hosted-model context assembly. |
| **Executor** | Idempotency and duplicate-guard tests; restart-mid-action tests (NFR-11). |
| **Integrations** | Contract tests against recorded fixtures; no live production calls in the test suite. |
| **Prompt/LLM layer** | Golden-set evaluation for Recommendation quality and Briefing brevity; regression on refusal-to-fabricate (P-3). |
| **End-to-end** | The five User Journeys in §12 as acceptance scenarios. |
| **Safety regression** | A standing test that no fetched content can cause an Action without approval (§20). |
| **Naming rule** | `grep -ri jarvis` in CI returns zero hits outside config default and message templates (FR-95). |

---

## 29. MVP Scope

> ⚠️ **This section is contested by `recommendations.md` R-1 and should be read alongside it.** The user's specification lists the scope below as MVP. Analysis indicates it is roughly a full-time year of work for a solo developer with ~1–2 discretionary hours per day — which would consume the entire six-month window in which the ₹1 crore goal must be achieved. The scope is recorded here **as specified**, per the user's instruction not to silently change requirements. A phased alternative is proposed in `recommendations.md`, for the user to accept or reject.

### 29.1 In scope (as specified by the user)

Agent core · Memory architecture · Goal/KPI engine · Priority engine · Task system · Scheduler · Notification system · Task executor · Daily planning · Dynamic replanning · Decision journal · Experiment tracking · Business dashboard · Revenue tracking · Approval/permission system · Audit log · Error handling · Local web UI · Voice / Commute Mode · GitHub integration · Filesystem integration · Browser capability · Telegram · WhatsApp · Configuration system · Secrets management

### 29.2 Out of scope for MVP

- Google Calendar, Gmail — deferred; no current dependency.
- YouTube / Instagram / Facebook publishing APIs — MVP produces copy-paste-ready bundles instead (FR-55).
- Google Analytics, Search Console — content and Railzy metrics are manually entered at MVP (FR-56, **[OPEN-5]**).
- Cloud deployment — designed for, not built (§27).
- Mobile application — channels are WhatsApp and Telegram, which are already mobile.
- Advanced computer control beyond the declared Tool set.
- Payment systems and financial-account integrations.
- Autonomous workflows beyond the permission model — the Agent proposes; the user disposes.
- Multi-user, tenancy, or any Naxova-facing product surface.
- **[NOTE FOR PM]** Direct publishing and platform analytics are the two deferrals most likely to be missed in practice — they are the difference between the content pipeline saving real time and merely organising it. Revisit first if timeline permits.

---

## 30. Post-MVP Roadmap

| Phase | Contents |
|---|---|
| **Phase 2 — Always-on** | Cloud lift of Scheduler + Notifier; nudges independent of machine state; PSTN wake-up call |
| **Phase 3 — Connected metrics** | YouTube / Instagram / Facebook analytics; Google Analytics; Search Console; automatic KPI refresh replacing manual entry |
| **Phase 4 — Publishing** | Direct multi-platform publishing; scheduled release; thumbnail generation |
| **Phase 5 — Deeper workspace** | Google Calendar, Gmail, richer document handling |
| **Phase 6 — Local computer agent** | Advanced local control (the original brief's V3) |
| **Phase 7 — Increased autonomy** | Expanded L1 surface based on demonstrated reliability; standing approvals for proven low-risk workflows |
| **Later** | Payment systems, additional business systems, mobile app if channels prove insufficient |

Sequencing is by observed value, not by this list order.

---

## 31. Milestones

**[PROPOSED]** — durations assume the user's realistic availability (Sundays plus fragments of weekday evenings), not full-time work.

| M | Milestone | Delivers | Exit criterion |
|---|---|---|---|
| **M0** | Skeleton | Service starts on boot, welcome message, config, secrets, naming rule enforced in CI | Survives reboot; `grep -ri jarvis` clean |
| **M1** | Nudge loop | Scheduler + Notifier + Telegram; routine triggers configured | The 06:00 / 07:30 / 09:10 / 20:00 nudges fire for one full week unattended |
| **M2** | Memory + Tasks | Six partitions, Task model, Project model, local web UI shell | Tasks survive restart; partitions enforced at schema level |
| **M3** | Priority + Plan | Priority Engine, daily Plan, Protected Blocks | A generated Plan is accepted unmodified for three consecutive days |
| **M4** | Executor + Permissions | Tool Registry, permission levels, approvals, Audit Log, GitHub + filesystem Tools | An L2 action executes only after approval; every action is auditable |
| **M5** | Goals + Revenue | Goal tree, Required Pace, Trajectory, Revenue records, Dashboard cockpit | Trajectory and gap render correctly against real entered revenue |
| **M6** | Voice + Commute | STT/TTS, Commute Briefing, voice commands | UJ-1 completes end-to-end in the car without touching a screen |
| **M7** | Advice layer | Recommendations, proactive signals, Decision Journal, Weekly Review | The Weekly Review produces exactly three focus items from real data |
| **M8** | Content + Experiments | Content pipeline, calendar, generation, performance entry, Experiments | UJ-5 completes; one Experiment runs to conclusion |

M0–M1 alone deliver a working proactive nudge system. See `recommendations.md` R-1 for why that ordering matters.

---

## 32. Risks

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| **RK-1** | **Building the system consumes the six months it exists to serve.** | Critical | Ship M0–M1 first and use it while building the rest. See `recommendations.md` R-1. |
| **RK-2** | Scope is far larger than available build time. | Critical | Phase per §31; treat §29 as a target state, not a first release. |
| **RK-3** | Abandonment — the tool becomes another obligation. | High | Notification budget (FR-31); ruthless brevity; M1 must deliver value before M4. |
| **RK-4** | Bad advice from thin data — confident recommendations on 14 days of history. | High | Confidence levels (FR-5); insufficient-history state (FR-8); no fabrication (P-3). |
| **RK-5** | WhatsApp account ban via unofficial bridge. | High | Dedicated number, never personal (§26). **[OPEN-3]**. |
| **RK-6** | Employer/client confidentiality breach through a hosted model. | Critical | Classification + hosted-model exclusion (FR-44); local model for confidential context. |
| **RK-7** | Prompt injection driving unapproved actions. | High | Fetched content is data, not instruction; untrusted-origin actions always require approval (§20). |
| **RK-8** | Machine-off gap — nudges silently missed. | Medium | Missed-trigger reporting (FR-28); explicit limitation disclosure (NFR-20); phase-2 cloud lift. |
| **RK-9** | Notification fatigue. | Medium | Budget, classes, quiet hours (FR-29–32); count as counter-metric. |
| **RK-10** | The office visualisation degrades usability. | Medium | List view default; metaphor subordinate to usability (FR-88). |
| **RK-11** | Single point of failure — one machine holding everything. | Medium | Daily local backup (NFR-10); encryption at rest. |
| **RK-12** | LLM cost drift. | Low–Med | Per-task-class model selection; cost tracking (FR-92); **[OPEN-8]** ceiling. |
| **RK-13** | The ₹1 crore target proves unreachable and the system's honesty is demoralising. | Medium | FR-9 pairs every such finding with what *would* have to change — never a bare verdict. |

---

## 33. Open Questions

Genuinely undecided. Not invented, not silently resolved.

| ID | Question | Blocks |
|---|---|---|
| **OPEN-1** | Does ₹1 crore mean revenue, profit, or personal take-home? The three imply different strategies. | Goal Engine semantics; all advice |
| **OPEN-2** | How does the ₹1 crore split across Railzy, Content, Freelance and Naxova? | Goal tree targets; prioritisation |
| **OPEN-3** | WhatsApp route — unofficial bridge on a dedicated number, or paid Business API? | Notification channel; RK-5 |
| **OPEN-4** | How does the 06:00 wake-up actually ring — local machine alarm, PSTN call, or escalating messages? | FR-33 |
| **OPEN-5** | Is manual entry of content and Railzy metrics acceptable at MVP? | FR-56; dashboard credibility |
| **OPEN-6** | How is *actual* time captured — manual, inferred, or timed? | FR-71; time-allocation analysis |
| **OPEN-7** | What are Railzy's analytics, SEO and business-metric sources? And is the domain `railzy.in`? | FR-76; Railzy panel |
| **OPEN-8** | What monthly running-cost ceiling is acceptable? | Model selection; NFR-7 |
| **OPEN-9** | Is the Agent Office literal (floor plan, avatars) or abstract (cards/graph)? Materially different effort. | FR-88; UI estimate |
| **OPEN-10** | Voice engines — local (Whisper/Piper) or cloud STT/TTS? Local is private and free but heavier; cloud is easier but sends audio out. | §23; privacy posture |
| **OPEN-11** | Initial Priority Engine weights. | FR-12; every ranking |
| **OPEN-12** | What existing revenue and audience baselines exist today (Railzy revenue, channel size, freelance income)? Without these, Trajectory cannot start. | Goal Engine; UJ-3 |
| **OPEN-13** | Which decisions does the user most often get wrong or delay? This is what the advice layer must target. | FR-66, FR-67 tuning |
| **OPEN-14** | Is the Sunday Protected Block for Railzy correct, given Sunday is his only clear day? | FR-20 |

---

## 34. Dependencies

**External**

- An LLM provider (hosted and/or local) — required for advice and generation only; deterministic functions work without one (NFR-19).
- Telegram Bot API — MVP notification channel.
- WhatsApp delivery route — **[OPEN-3]**.
- GitHub API — Railzy and repository capability.
- STT/TTS engines — **[OPEN-10]**.
- The user's Windows machine, running, for scheduled triggers to fire.

**Internal / user-supplied**

- Baseline revenue and audience figures — **[OPEN-12]**. Trajectory cannot function without them.
- The goal split — **[OPEN-2]**.
- Railzy repository access and metric sources — **[OPEN-7]**.
- The user's routine and fixed commitments as structured configuration (§7).

**Sequencing dependencies**

- Priority Engine depends on the Goal tree having targets (**[OPEN-2]**).
- Trajectory depends on baseline revenue (**[OPEN-12]**).
- Daily planning depends on the routine model and the Priority Engine.
- Commute Mode depends on the Notifier, voice, and the Priority Engine.
- Everything executable depends on the permission model — it is built before, not after, the Tools.

---

## 35. Assumptions Index

Every `[ASSUMPTION]` in this document, surfaced for confirmation:

| # | Assumption | Where |
|---|---|---|
| A-1 | The Railzy domain is `railzy.in`; the user wrote "railzy.on", presumed a typo. | §10.21 FR-76 |
| A-2 | The weekly Railzy Protected Block belongs on Sunday, as the only clear day. | FR-20, OPEN-14 |
| A-3 | The user's stated schedule (§7) is stable enough to model as fixed configuration. | §7 |
| A-4 | The ₹1 crore window runs 2026-08-10 → 2027-02-10. | §4 |
| A-5 | "Personal but real" stakes — one user now, possibly a product later; no multi-user design at MVP. | §5 |
| A-6 | The user will accept manual metric entry at MVP rather than waiting for integrations. | OPEN-5 |
| A-7 | Existing salary counts toward the ₹1 crore, rather than the target being incremental earnings only. | §4, OPEN-1 |

---

## 36. Acceptance Criteria

The MVP is accepted when all of the following hold:

**Reliability**

1. The system starts automatically on machine start, without login, and emits a welcome message.
2. Routine nudges (06:00, 07:30, 09:10, 20:00) fire correctly for seven consecutive days.
3. Triggers missed while the machine was off are reported on next start, never silently dropped.
4. All Tasks, Goals, schedules and Events survive a forced restart with no loss.

**Decision value**

5. Asking "what should I do now?" through any channel returns one primary recommendation with its rationale and the Goal it serves.
6. Any Priority Score can be decomposed into its factors on request.
7. The Agent visibly disagrees at least once when the user selects a P4 Task while a P1 is outstanding — and drops it after one statement.
8. The Weekly Business Review produces exactly three focus items, derived from real recorded data.

**Goal arithmetic**

9. Required Pace, Trajectory and Gap compute correctly against entered revenue.
10. With fewer than 14 days of history, the system reports "insufficient history" rather than projecting.
11. When required acceleration exceeds the threshold, the system states the Goal is unreachable under current assumptions and names what would have to change.

**Safety**

12. No L2 action executes without a recorded Approval; no L3 action executes without local-UI confirmation.
13. An unregistered Tool call fails closed and is logged.
14. Client- and Employer-Confidential records are provably excluded from hosted-model calls.
15. Content fetched by a Tool cannot cause an Action without approval.
16. No secret appears in any log, Event, or Audit entry.
17. Every Action is traceable to its cause, its approver and its result.

**Voice**

18. UJ-1 completes end-to-end in the car: briefing delivered, plan changed by voice, confirmation heard — without touching a screen.
19. Spoken responses hold to ≤ 3 sentences outside Briefings.

**Discipline**

20. `grep -ri jarvis` over the source tree returns zero hits outside the config default and message templates.
21. Renaming the assistant requires exactly one configuration change.
22. Daily notification volume stays within budget for a full week without suppressing a Critical notification.

**The real test**

23. After four weeks of use, the user's time allocation has measurably shifted toward the Projects that carry the Root Goal — and he has not abandoned the tool.

---

## 37. Success Metrics

**Primary**

- **SM-1 — Allocation shift.** Percentage of discretionary hours spent on Root-Goal-carrying Projects (Railzy, Content, Naxova). Target: measurably higher in week 8 than week 1. Validates FR-12, FR-17, FR-71.
- **SM-2 — Early warning.** The system flags an unreachable-trajectory condition, if one exists, before the halfway point (2026-11-10) rather than after. Validates FR-8, FR-9, FR-64.
- **SM-3 — Sustained use.** Still in daily use at week 12 without a gap longer than three days. Validates the whole product; abandonment is the primary failure mode (RK-3).

**Secondary**

- **SM-4 — Protected Block integrity.** Railzy's weekly Protected Block is honoured ≥ 75% of weeks. Validates FR-20, FR-70.
- **SM-5 — Execution leverage.** Count of Actions executed by the Agent under approval rather than performed manually. Validates FR-35.
- **SM-6 — Recall value.** Decision Journal answers a "why did we…" question correctly at least monthly. Validates FR-46, FR-47.

**Counter-metrics (do not optimise)**

- **SM-C1 — Notification volume.** Should stay flat or fall. A rising count means the system is buying engagement with attention — the opposite of P-6.
- **SM-C2 — Tasks completed.** Explicitly *not* a success measure (P-1). Rising task throughput with flat SM-1 means the system is generating busywork.
- **SM-C3 — Time spent inside the product.** Should fall over time. This is a tool for acting, not a place to live.
- **SM-C4 — Recommendation acceptance rate.** Should *not* approach 100%. A system never disagreed with is a system that stopped disagreeing (P-2).

---

*End of PRD. Read `recommendations.md` before acting on §29.*


---
title: Core Intelligence Loop — Architecture and Product-Design Specification
status: draft
created: 2026-08-10
updated: 2026-08-10
scope: The central operating loop of the personal AI operating system
companion: ../prds/prd-jarvis-2026-08-10/prd.md
---

# Core Intelligence Loop

**GOAL → PRIORITIZE → EXECUTE → MEASURE → LEARN → REPLAN**

This document specifies the central intelligence of the personal AI operating system. It is deliberately narrower than the PRD: the PRD says *what the product does*; this says *how the thinking works*.

**Requirement IDs here use the `CFR-` / `CNFR-` prefix** so they never collide with the PRD's `FR-` / `NFR-` numbering. Where this document and the PRD overlap, **this document is authoritative for the loop**, and the PRD is authoritative for everything around it.

**Status tags** carry the same meaning as in the PRD: **[CONFIRMED]** (stated by the user), **[PROPOSED]** (introduced here to make a confirmed requirement implementable — needs a yes/no), **[ASSUMPTION]** (inferred), **[OPEN]** (genuinely undecided, not invented). Untagged items are CONFIRMED.

### Two reconciliations, stated rather than silently resolved

1. **Loop shape.** The earlier specification described *GOAL → PLAN → PRIORITIZE → EXECUTE → MEASURE → LEARN → REPLAN* (seven stages). This specification describes six, without PLAN. **Resolution:** planning is the **PRIORITIZE → EXECUTE transition** (§7 of the source: *"once a priority is selected, convert it into an executable plan"*). PLAN is a transition, not a stage. Both descriptions agree under that reading. Adopted throughout.
2. **Store count.** The earlier specification named **six memory partitions**; this one names **eight stores**, adding Execution Log and Audit Log. **Resolution:** six *memory partitions* plus two *append-only logs*, which were already separate cross-cutting concerns. §16 defines all eight.

---

## 1. Product Principles

Binding on every design decision in this document. Where a later section appears to conflict, the principle wins and the conflict is a defect.

| ID | Principle | Consequence in this architecture |
|---|---|---|
| **CP-1** | **Optimise for progress, not throughput.** | No component counts completed tasks as success. The Measurement model (§8) records outcome, not activity. `SM-C2` in the PRD makes task count an explicit counter-metric. |
| **CP-2** | **One high-value action beats ten low-value actions.** | The Decision Engine returns **one** primary recommendation, not a ranked backlog (§6). |
| **CP-3** | **Goals are configuration, never code.** | No strategic target — ₹1 crore or any other — appears in the codebase. The engine is goal-type-agnostic (§3). |
| **CP-4** | **Never confuse the seven entity types.** | Goal, KPI, Project, Task, Event, Decision and Experiment have distinct schemas, distinct lifecycles, and no shared table (§3, §17). |
| **CP-5** | **Every recommendation is explainable.** | The transparency chain (§19) is a required output structure, not a presentation option. |
| **CP-6** | **The engine may say "do nothing" and "stop doing".** | "Stop doing" is a first-class output, not the absence of a recommendation (§16). |
| **CP-7** | **Deterministic arithmetic, probabilistic advice.** | Pace, gap, scoring and calibration are computed in code. The LLM interprets and explains; it never produces the numbers. |
| **CP-8** | **The agent proposes; the user disposes.** | No action above Permission Level 1 executes without approval (§11, §12). Strategic decisions are never auto-reversed (§15). |
| **CP-9** | **Learning changes future estimates, not past records.** | Events and Actions are immutable. Learning produces *calibration factors*, applied forward only (§9). |
| **CP-10** | **Honest about uncertainty.** | Confidence accompanies every recommendation. Insufficient data yields "insufficient data", never a plausible guess. |

---

## 2. Core Loop Architecture

```
              ┌────────────────────────────────────────────────┐
              │                                                │
              ▼                                                │
      ┌───────────────┐                                        │
      │     GOAL      │  strategic objectives + KPI state      │
      │   (§3, §4)    │  "what is the user trying to achieve?" │
      └───────┬───────┘                                        │
              │                                                │
              ▼                                                │
      ┌───────────────┐                                        │
      │  PRIORITIZE   │  score candidates against goals        │
      │   (§5, §6)    │  "what matters most right now?"        │
      └───────┬───────┘                                        │
              │  ── plan transition: priority → executable ──  │
              ▼                                                │
      ┌───────────────┐                                        │
      │    EXECUTE    │  approval → action → result            │
      │  (§7,§11,§12) │  "what action should be taken?"        │
      └───────┬───────┘                                        │
              │                                                │
              ▼                                                │
      ┌───────────────┐                                        │
      │    MEASURE    │  expected vs actual, outcome capture   │
      │     (§8)      │  "was it done, and what did it do?"    │
      └───────┬───────┘                                        │
              │                                                │
              ▼                                                │
      ┌───────────────┐                                        │
      │     LEARN     │  calibration, pattern extraction       │
      │     (§9)      │  "what did we learn?"                  │
      └───────┬───────┘                                        │
              │                                                │
              ▼                                                │
      ┌───────────────┐                                        │
      │    REPLAN     │  is the plan still valid?              │
      │    (§10)      │  "what should happen next?"            │
      └───────┬───────┘                                        │
              │                                                │
              └────────────────────────────────────────────────┘
```

### 2.1 How the loop actually runs

The loop is **not** a batch job that runs once a day. It is a set of stage functions invoked by triggers.

| Trigger | Stages executed |
|---|---|
| Scheduled tick (**[PROPOSED]** 05:45, 12:00, 22:30) | Full loop |
| Context Mode change | GOAL → PRIORITIZE → REPLAN |
| Action completion | MEASURE → LEARN → REPLAN |
| KPI or revenue change | GOAL → PRIORITIZE → REPLAN |
| Incident / failed task / blocked dependency | REPLAN (immediate) |
| Explicit user question ("what now?") | PRIORITIZE (read-only, no state mutation) |
| Decision Review Trigger fires | GOAL → REPLAN |

**CFR-1: The loop is trigger-driven and idempotent.**
- A stage invoked twice with unchanged inputs produces an identical result and no duplicate side effects.
- Every loop pass writes one `LoopRun` Event recording trigger, stages executed, duration, and outputs produced.
- A read-only pass (user question) never mutates State.

**CFR-2: Each stage is independently testable.**
- Stages communicate through persisted state, not in-memory handoff, so any stage can be run in isolation against a fixture.
- No stage calls an LLM for arithmetic (CP-7).

---

## 3. Goal Model

### 3.1 The seven entity types — never conflated

This distinction is the backbone of the system. Confusing any two of these is the failure mode that turns the product into a task manager.

| Entity | Answers | Lifecycle | Never |
|---|---|---|---|
| **Goal** | What the user wants to achieve | Long-lived; revised deliberately | …a task with a deadline |
| **KPI** | How progress is measured | Continuously refreshed | …a goal; a KPI has no intent |
| **Project** | Which initiative pursues the goal | Long-lived; has status | …a task container only — it carries strategy |
| **Task** | What specific action is required | Short-lived; completes | …a goal; a task cannot be "partially strategic" |
| **Event** | What actually happened | Immutable, append-only | …editable, ever |
| **Decision** | What was chosen and why | Append-only; status mutates | …a task; a decision has no assignee |
| **Experiment** | What hypothesis was tested | Bounded duration; concludes | …an open-ended project |

**CFR-3: Entity separation is enforced structurally.**
- Each type has its own table and its own schema. There is no polymorphic "item" table.
- A Task cannot be promoted to a Goal, nor a Goal demoted to a Task. Converting requires explicit creation of the new entity with a recorded link.
- Cross-references are typed foreign keys, never free-text.

### 3.2 Goals are configuration

**CFR-4: The engine supports arbitrary strategic goal types. [CONFIRMED — explicit user correction]**
- **No strategic target is hard-coded.** ₹1 crore in six months is *one configured Goal instance*, indistinguishable to the engine from any other.
- Supported goal types at minimum: **monetary**, **count** (users, subscribers, views), **milestone** (binary — launched / not launched), **ratio/percentage**, **duration** (learning hours), and **qualitative-with-proxy** (a subjective goal that declares a measurable proxy KPI).
- Adding a new goal type requires a new evaluator strategy, not a change to the loop.
- **Acceptance:** deleting the ₹1 crore Goal leaves a fully functional system with zero code changes.

### 3.3 Goal schema

| Field | Meaning |
|---|---|
| `id`, `parent_id` | Position in the goal tree; arbitrary depth |
| `name`, `description` | Human statement of intent |
| `goal_type` | monetary / count / milestone / ratio / duration / qualitative-proxy |
| `target_value`, `unit` | What success is; `null` permitted while unallocated |
| `current_value` | Derived from linked KPIs, never entered directly |
| `start_date`, `deadline` | The window |
| `status` | draft / active / at-risk / achieved / missed / abandoned |
| `confidence` | Derived (§4.3), not asserted |
| `owner` | The user, or a delegate |
| `dependencies` | Other Goals that must advance first |
| `rollup_policy` | sum / max / weighted / manual — how children contribute |
| `priority_weight` | Relative importance among siblings |

**CFR-5: Goals roll up deterministically.**
- A child's contribution to its parent follows `rollup_policy`; no LLM participates.
- Rollup recomputes within one loop pass of any child change.
- A Goal with `target_value = null` is reported as **unallocated**, and its parent's coverage is reported as partial — never as zero and never as complete.

**CFR-6: A Goal without a measurable KPI cannot be `active`.**
- Creation with no KPI and no proxy is rejected with an explanatory error.
- This is what prevents aspiration from masquerading as strategy.

---

## 4. KPI Model

### 4.1 Schema

| Field | Meaning |
|---|---|
| `id`, `goal_id`, `project_id` | What it measures progress toward |
| `name`, `unit` | |
| `value`, `previous_value` | Current and prior reading |
| `source_type` | manual / integration / computed |
| `source_ref` | Which integration or computation |
| `last_refreshed`, `expected_interval` | Freshness contract |
| `direction` | higher-is-better / lower-is-better |
| `baseline` | Value at goal start — required for any progress claim |

### 4.2 Freshness and honesty

**CFR-7: Stale KPIs are excluded, not guessed.**
- A KPI unrefreshed beyond `expected_interval` is flagged `stale`.
- Stale KPIs are excluded from trajectory and confidence computation, and the exclusion is visible in the output.
- A KPI with no `baseline` cannot produce a progress percentage; it reports absolute value only.

### 4.3 Derived progress metrics

Computed in code (CP-7):

- **Required Pace** — remaining amount ÷ remaining time, expressed per day / week / month. Always against *remaining*, never original.
- **Actual Pace** — trailing realised rate. **[PROPOSED]** trailing 30 days, widening to 90 once history permits.
- **Trajectory** — projected value at deadline given Actual Pace.
- **Gap** — Trajectory minus target, absolute and percentage.
- **Required Acceleration** — Required Pace ÷ Actual Pace.
- **Confidence** — derived from history length, KPI freshness, data completeness and estimate-calibration error (§9). Never asserted by the LLM.

**CFR-8: Insufficient history is a first-class state.**
- Below **[PROPOSED]** 14 days of history, the engine reports `insufficient_history` and refuses to project.
- This state is rendered explicitly in the UI, never as a zero, a flat line, or an optimistic default.

**CFR-9: The engine declares a goal unreachable when arithmetic says so.**
- When Required Acceleration exceeds a configured threshold (**[PROPOSED]** ≥ 5×, **[OPEN-A]** needs the user's calibration), the engine emits an `unreachable_under_current_assumptions` finding.
- The finding **must name which assumptions would have to change, and by how much** — a bare verdict is non-compliant.
- Raised at most **[PROPOSED]** weekly. The user may acknowledge and continue; the acknowledgement becomes a Decision with a Review Trigger.
- This applies to *any* configured Goal, not to one special case (CP-3).

---

## 5. Priority Engine

**Deterministic. No LLM in the scoring path.** The LLM may *estimate a missing factor value*, and such estimates are flagged `estimated: true` and carry reduced weight.

### 5.1 Scoring

```
Score(task) =
      w_rev  · RevenueImpact
    + w_bus  · BusinessImpact
    + w_user · UserImpact
    + w_urg  · Urgency                (from deadline proximity)
    + w_str  · StrategicImportance    (alignment to an active Goal path)
    + w_risk · RiskReduction
    + w_dep  · DependencyUnblocking
    − w_eff  · EffortCalibrated       (§9 — calibrated, not raw estimate)
    − w_opp  · OpportunityCost        (active only when a higher band exists)
```

**CFR-10: Every candidate action is scored.**
- No Task enters a plan unscored. Unscorable input is queued for scoring, never silently dropped.
- Factors normalise to a common scale; weights are configuration (**[OPEN-B]** initial weights undecided).
- Identical inputs always produce an identical score.

**CFR-11: The factor breakdown is always retrievable.**
- For any score: each factor, its raw value, whether it was estimated, its weight, and its contribution.
- Available in a form short enough to speak aloud.

**CFR-12: Strategic alignment is computed from the goal tree, not asserted.**
- `StrategicImportance` derives from the task's Project → Goal path, that Goal's `priority_weight`, and how far behind that Goal currently is.
- A task serving an at-risk Goal outranks an identical task serving an on-track one. **This is what makes the engine strategic rather than clerical.**

**CFR-13: Live-user harm has a floor.**
- A Task affecting users of a live Project carries a minimum `UserImpact`, so production harm cannot be outranked by convenience work.

### 5.2 Bands

P1 do now · P2 this week · P3 scheduled · P4 delete candidate. Thresholds are configuration.

**Worked example (from the user's specification).** Goal: increase Railzy revenue. Revenue is low. Candidates:

| Action | Goal impact | Expected value | Urgency | Effort | Result |
|---|---|---|---|---|---|
| A. Redesign logo | Low | Low | Low | High | **P4** |
| B. Fix signup bug | High | High | High | Low | **P1** |
| C. SEO landing pages | High | Medium | Medium | Medium | **P2** |
| D. Research competitors | Low–Med | Low | Low | Medium | **P3** |

**CFR-14: The engine explicitly recommends against low-value work.**
- Output includes a `do_not_do` list, not merely a ranked list (CP-6, §16).
- For the example above the engine must be capable of emitting: *"Do not work on A right now."*

---

## 6. Decision Engine

The component that answers **"What should the user do now?"** It consumes the Priority Engine's scores; it does not duplicate them.

### 6.1 Inputs

Active Goals · KPI status · current Context Mode · available time in the current window · deadlines · Tasks · Projects · dependencies · recent Events · previous Decisions · revenue opportunities · **historical execution performance (§9)**.

### 6.2 Output contract

**CFR-15: The Decision Engine returns a structured Recommendation, never prose alone.**

```
Recommendation {
  recommended_action      : TaskRef | ActionSpec
  reason                  : string          // grounded in evidence, not restated score
  evidence                : EvidenceRef[]   // KPIs, Events, Decisions consulted
  expected_impact         : { goal_id, magnitude, unit }
  estimated_effort        : Duration        // calibrated (§9)
  confidence              : HIGH | MEDIUM | LOW
  should_postpone         : TaskRef[]       // what this displaces
  do_not_do               : { task, why }[] // §16
  approval_required       : bool
  permission_level        : L0 | L1 | L2 | L3
  transparency_chain      : Chain           // §19 — mandatory for important recs
}
```

- **Exactly one** `recommended_action` (CP-2). Alternates are a separate, optional field capped at two.
- `confidence: LOW` blocks the Recommendation from being raised as a Critical notification.
- If inputs are insufficient to rank, the engine returns `insufficient_data` naming what is missing — it does not guess (CP-10).

**CFR-16: Time-awareness is mandatory.**
- The engine knows how much time the current window holds and never recommends a 3-hour action into a 40-minute gap.
- When the best action does not fit, it says so and recommends the best action that does — naming the trade-off.

**CFR-17: The engine may recommend rest or nothing.**
- "Nothing further tonight" is a valid, deliberate output when the marginal value of more work is negative.
- This is a designed behaviour, not a fallback.

---

## 7. Execution Model

The PRIORITIZE → EXECUTE transition converts a chosen priority into an executable plan.

**CFR-18: An executable plan declares its full shape before execution.**

Every planned action specifies: exact task · expected duration · required tools · dependencies · deadline · required approval level · expected outcome.

**CFR-19: The user can accept, modify, reject or postpone.**
- All four are available through every channel, including voice.
- Rejection and postponement are recorded as Events with reason where given.
- A postponement increments the task's postpone counter, which feeds §9 and §18.

**CFR-20: Risky actions never assume approval.**
- L2 and L3 require an explicit, unexpired Approval before execution (§11).
- There is no "assume yes on timeout" path anywhere in the system.

### 7.1 Action state machine

**CFR-21: Every Action follows exactly this lifecycle.**

```
                 ┌──────────────────┐
                 │ PENDING_APPROVAL │
                 └────┬────────┬────┘
              approve │        │ reject / expire
                      ▼        ▼
              ┌──────────┐  ┌──────────┐
              │ APPROVED │  │ REJECTED │ (terminal)
              └────┬─────┘  └──────────┘
                   │ dispatch          ┌───────────┐
                   ▼               ┌──▶│ CANCELLED │ (terminal)
             ┌───────────┐  cancel │   └───────────┘
             │ EXECUTING │─────────┘
             └─────┬─────┘
            ┌──────┴───────┐
            ▼              ▼
      ┌──────────┐   ┌──────────┐
      │ SUCCESS  │   │  FAILED  │  (both terminal)
      └──────────┘   └──────────┘
```

- L0/L1 actions enter at `APPROVED` directly; the transition is still recorded.
- Terminal states are immutable. A retry creates a **new** Action linked to the original — it never reopens the old one.
- A crash during `EXECUTING` resolves on restart to `FAILED` with `interrupted: true`, never silently to `SUCCESS`.

---

## 8. Measurement Model

**CFR-22: Every executed Action records expected versus actual.**

| Captured | Field |
|---|---|
| What was done | `action`, `tool`, `parameters` |
| When | `started_at`, `ended_at` |
| Outcome | `result`, `status`, `output`, `errors` |
| Effort | `expected_effort`, `actual_effort` |
| Impact | `expected_outcome`, `actual_outcome`, `outcome_measured_at` |

**Worked example (the user's):** expected — fix signup bug in 45 minutes. Actual — 90 minutes. Result — signup conversion improved 8%. Three separate facts: effort was underestimated 2×, the action succeeded, and the impact was positive and measurable.

**CFR-23: Outcome measurement is deferred and scheduled, not guessed at completion.**
- Completing an Action schedules an outcome check at a horizon appropriate to the KPI (**[PROPOSED]** 72 h for content, 7 days for product changes).
- Until then `actual_outcome` is `pending`, never `assumed_as_expected`.
- An outcome that never becomes measurable is recorded as `unmeasurable` with a reason — it is not quietly dropped.

**CFR-24: Measurement data is immutable and reusable.**
- Records feed the Learning model (§9) and can never be edited retroactively (CP-9).

---

## 9. Learning Model

Compares expected against actual and turns the difference into forward-applied calibration.

### 9.1 What is learned

| Pattern | Detection | Applied to |
|---|---|---|
| **Effort bias** | Ratio of actual to expected effort, by Project and task category | Future effort estimates |
| **Impact bias** | Actual versus expected outcome magnitude | `expected_impact` in Recommendations |
| **Successful assumptions** | Predictions borne out | Confidence weighting |
| **Failed assumptions** | Predictions contradicted | Confidence weighting; Decision review (§15) |
| **Repeated problems** | Same failure class recurring | Risk surfacing |
| **Postponement patterns** | Same Task deferred N times | §18 accountability |
| **Category performance** | Outcome by content or work category | Priority weighting |

**CFR-25: Learning produces calibration factors, applied forward only.**
- Example: *"Development estimates for this Project have historically been underestimated by ≈2×."*
- The factor is applied to future estimates as `EffortCalibrated = EffortRaw × factor`, and the adjustment is **visible** — the user sees both raw and calibrated values.
- Historical records are never rewritten (CP-9).

**CFR-26: Calibration requires a minimum sample.**
- **[PROPOSED]** Minimum 5 comparable observations before a factor is applied.
- Below the minimum, the raw estimate stands and the engine reports low confidence in it.
- Sample size is always visible alongside any learned claim.

**CFR-27: Learned patterns are stated with evidence.**
- Every learned claim names the observations behind it and the sample size.
- Patterns below the threshold are labelled *provisional* and never drive an automatic change.

**CFR-28: Category performance feeds prioritisation.**
- Example: if a content category consistently outperforms, its `StrategicImportance` contribution increases.
- The adjustment is bounded (**[PROPOSED]** ±25%) so one strong run cannot dominate the engine.

---

## 10. Replanning Model

**CFR-29: The system never blindly continues an invalidated plan.**

### 10.1 Triggers

New information · failed task · production incident · deadline change · KPI change · revenue change · user decision · unexpected opportunity · resource or time change · blocked dependency.

**CFR-30: Every trigger writes an Event naming what changed** before replanning begins.

### 10.2 Reassessment scope

On trigger the engine reassesses: goals · KPIs · priorities · projects · tasks · assumptions · deadlines · available time.

**CFR-31: Replanning is bottleneck-aware, not merely re-sorting.**

The worked example is the requirement: original plan focuses on Railzy SEO; new information shows signup conversion is broken. The engine must recognise that **traffic acquisition is not the current bottleneck** and recommend fixing conversion before increasing traffic.

- The engine identifies the binding constraint on the goal path, not just the highest-scoring isolated task.
- **[PROPOSED]** Implementation: a funnel/dependency model per Goal — improvements upstream of a broken downstream stage are discounted until the downstream stage is repaired.

**CFR-32: Every plan change is explained.**
- The output states what moved, what was dropped, what was protected, and why — in that order.
- Example form: *"Move Naxova research to tomorrow. Protect the production fix and today's client deadline."*

**CFR-33: A revised plan requires approval.**
- Accept / reject / modify available by voice.
- **[PROPOSED]** An unanswered proposal expires after 4 hours, leaving the prior plan standing.
- Rejection is recorded with reason where given, and feeds §9.

**CFR-34: Replanning is rate-limited.**
- **[PROPOSED]** At most one unsolicited replan proposal per 3 hours outside incidents.
- Incidents and explicit user requests bypass the limit.
- Without this, a volatile day produces continuous churn and the user stops reading proposals.

---

## 11. Approval System

**CFR-35: Every executable action carries a complete approval record.**

| Field | Notes |
|---|---|
| `action_id` | |
| `requested_by` | The agent component that raised it |
| `agent` | Agent identity and version |
| `worker_role` | Which specialisation produced it |
| `tool` | |
| `action` | Human-readable statement of intent |
| `parameters` | Full, inspectable |
| `risk_level` | Assessed risk, independent of permission level |
| `permission_level` | L0–L3 |
| `approval_status` | The state machine of §7.1 |
| `approved_by`, `approved_at` | |
| `expires_at` | |
| `channel` | Where approval was granted |
| `timestamp`, `result` | |

**CFR-36: The user sees exactly what will happen before approving.**
- The prompt states the action, its target, its parameters, and its irreversible consequences in plain language.
- Nothing is hidden behind "details" for L2 or L3.
- **[PROPOSED]** L3 prompts require the user to confirm the specific target (e.g. type or select the resource name), not just press yes.

**CFR-37: Approvals are single-use and time-bounded.**
- **[PROPOSED]** L2 expires in 30 minutes; L3 in 5 minutes.
- An expired approval requires re-request. There is no late execution.

---

## 12. Permission Model

**CFR-38: Four levels, enforced fail-closed.**

| Level | Grants | Examples |
|---|---|---|
| **L0 Observe** | Read, analyse, summarise | Read repo, summarise backlog, compute KPIs |
| **L1 Safe** | Reversible low-risk actions | Create task, create draft, create GitHub issue, prepare content, organise non-critical files |
| **L2 Approval Required** | Outward-facing or configuration-affecting | Send message, publish content, push code, modify project configuration, external communication |
| **L3 High Risk** | Always explicit confirmation | Production deployment, destructive DB operation, delete important files, financial transaction, delete account, change credentials or security configuration |

**Rules**

- Unknown tool, unknown level, or unresolved approval ⇒ **no execution**.
- A newly registered Tool defaults to **L2** — never L0 or L1 by omission.
- **L3 is never pre-granted.** No standing rules, no batch approval, no "always allow".
- **[PROPOSED]** L3 confirmation only from the local UI, so a compromised chat channel cannot authorise destruction.
- The agent cannot raise its own ceiling, and cannot select a different Worker Role to route around a restriction.
- Permission changes are themselves audited actions.

---

## 13. Audit Log

**CFR-39: Every meaningful agent action produces an immutable audit record.**

Captured: `timestamp` · `action` · `reason` · `goal_id` · `project_id` · `task_id` · `tool` · `input` · `output` · `approval_ref` · `result` · `error`.

**CFR-40: The audit log answers four questions directly.**

| Question | Answered by |
|---|---|
| *What did the agent do?* | `action`, `tool`, `input`, `output` |
| *Why did it do that?* | `reason`, `goal_id`, and the linked Recommendation with its transparency chain |
| *Did I approve it?* | `approval_ref` → approver, channel, timestamp |
| *What happened afterward?* | `result`, plus the linked measurement record (§8) |

- Append-only. The application exposes no update or delete path.
- Secrets never appear in `input` or `output`; parameters are redacted by classification before writing.
- Retention: indefinite (**[PROPOSED]**).

---

## 14. Decision Journal

Preserved **independently of task history**, because a decision outlives the tasks that implemented it.

**CFR-41: Decisions are first-class and append-only.**

| Field | Notes |
|---|---|
| `id`, `date` | |
| `decision` | The choice, stated plainly |
| `reason` | Why |
| `alternatives` | What else was considered, and why rejected |
| `assumptions` | **The beliefs the decision rests on** — this is what §15 monitors |
| `expected_outcome` | |
| `review_condition` | Date, KPI threshold, or event |
| `status` | active / under-review / superseded / invalidated |
| `actual_outcome` | Filled when known |
| `project_id`, `goal_id` | |

**Worked example (the user's):** *Do not build a Railzy mobile app yet.* Reason: current API/infrastructure economics do not justify it. Assumption: API cost is too high. Review condition: Railzy reaches a defined revenue/user threshold. Status: active.

**CFR-42: The agent answers historical "why" questions from the journal.**
- *"Why didn't we build the app?"* returns the decision, its reasoning, and its current validity — in two sentences, answerable by voice.
- If no Decision exists, the agent says so. It does not reconstruct a plausible rationale (CP-10).

---

## 15. Decision Review System

**CFR-43: Decisions carry review conditions and the system monitors them.**
- Conditions may be a date, a KPI threshold, or an event.
- Conditions are evaluated on each loop pass.

**CFR-44: The system detects when the assumptions behind a decision have changed.**
- Monitors the `assumptions` field against current State and KPI values.
- Example: original assumption *"API cost is too high"*; new condition *a suitable low-cost API becomes available* ⇒ the assumption no longer holds.

**CFR-45: The agent recommends review; it never auto-reverses a strategic decision. [CONFIRMED — explicit]**
- Output form: *"The condition behind Decision #X has changed. Would you like to reconsider?"*
- The Decision moves to `under-review`. It does **not** move to `superseded` without the user's act.
- **This is a hard constraint.** Automatic reversal of a strategic decision is prohibited regardless of confidence.

**CFR-46: Review surfacing respects attention.**
- Delivered in the periodic review unless genuinely time-critical.
- **[PROPOSED]** At most 3 decision reviews surfaced per week; the rest queue by staleness.

---

## 16. "Stop Doing" Intelligence

A first-class output, not the absence of a recommendation (CP-6).

**CFR-47: The engine identifies what the user should not do.**

Detected categories: low-impact tasks · repeated UI polishing · unnecessary work · poor expected return · abandoned projects · activity consuming time without measurable progress.

**CFR-48: Each `do_not_do` item carries its evidence and a disposition.**
- Every item states why, and proposes one of: **delete**, **defer with a trigger**, **delegate/outsource**, or **shrink**.
- A bare "don't do this" with no proposed disposition is non-compliant.
- Must be capable of emitting: *"Do not spend your next hour on this."*

**CFR-49: Stop-doing findings batch; they do not interrupt.**
- Surfaced in the periodic review, except when the user is actively starting a flagged task — then once, immediately, and not repeated (§18).

**CFR-50: Abandoned-project detection.**
- **[PROPOSED]** A Project with no Event in 14 days and an active Goal is flagged.
- The engine proposes explicit pause or closure. Ambiguous limbo is treated as a defect in the plan.

---

## 17. Memory / State Separation

**CFR-51: Eight distinct stores. No generic memory blob.**

| # | Store | Holds | Mutability | Retention |
|---|---|---|---|---|
| 1 | **MEMORY (User)** | Stable information about the user — preferences, routines, working style | Slow, versioned | Indefinite |
| 2 | **STATE** | Current operational state — active tasks, schedule, current context, live KPI values | Live | Current + rolling history |
| 3 | **GOALS** | Strategic objectives and their history | Live + history | Indefinite |
| 4 | **EVENTS** | Things that happened | **Immutable, append-only** | Indefinite |
| 5 | **DECISIONS** | Strategic choices and reasoning | Append-only; status mutable | Indefinite |
| 6 | **KNOWLEDGE** | Documents and reference information | Append + version | Indefinite |
| 7 | **EXECUTION LOG** | Actions performed by the agent, with expected-vs-actual | **Immutable, append-only** | Indefinite |
| 8 | **AUDIT LOG** | Security and accountability record | **Immutable, append-only** | Indefinite |

**Rules**

- Each store has its own schema. A write to the wrong store is a **schema error**, not a convention violation.
- Stores 4, 7 and 8 have no update or delete path in the application layer.
- **Execution Log ≠ Audit Log.** Execution Log answers *"how did work actually go?"* and feeds Learning. Audit Log answers *"who authorised what?"* and feeds accountability. They overlap in time but serve different consumers and different retention obligations.
- Every record carries a **confidentiality classification** (Public / Personal / Client-Confidential / Employer-Confidential) governing which model may see it.
- **Retrieval is store-aware.** Context assembly draws deliberately from named stores; there is no single undifferentiated similarity search across everything.

---

## 18. Event Model

**CFR-52: Events are the immutable spine of learning and audit.**

**[PROPOSED] Event taxonomy**

| Category | Examples |
|---|---|
| **Task** | created, scored, planned, started, completed, failed, postponed, deleted |
| **Goal** | created, target changed, progressed, at-risk, achieved, missed, abandoned |
| **KPI** | refreshed, stale, threshold crossed |
| **Action** | requested, approved, rejected, executed, failed, cancelled |
| **Decision** | recorded, review triggered, superseded, invalidated |
| **Experiment** | started, concluded |
| **Plan** | generated, accepted, rejected, replanned |
| **Incident** | production issue opened, resolved |
| **Business** | revenue recorded, opportunity identified, content published |
| **System** | started, stopped, trigger missed, integration failed |

Schema: `id` · `type` · `payload` · `occurred_at` · `recorded_at` · `goal_id` · `project_id` · `task_id` · `action_id` · `source`.

**CFR-53: Events carry both `occurred_at` and `recorded_at`.**
- Late-recorded events (machine was off; user confirms retrospectively) are placed correctly in time while remaining honest about when the system learned of them.

**CFR-54: Postponement is an Event, not a field update.**
- Each postponement appends an Event, so the count is derivable from history and cannot be lost by an edit.
- This is what makes *"you've postponed this for the fourth time"* provable rather than approximate.

---

## 19. Recommendation Model and Transparency

**CFR-55: Important recommendations must expose the full chain.**

```
OBSERVATION   →   EVIDENCE   →   REASONING   →   RECOMMENDATION   →   EXPECTED OUTCOME
                                                                    (+ CONFIDENCE)
```

**Worked example (the user's), which is the required output form:**

> **Observation:** Railzy traffic increased 30%.
> **Evidence:** Registrations remained flat.
> **Reasoning:** Acquisition is improving but conversion is not.
> **Recommendation:** Fix signup conversion before increasing SEO acquisition.
> **Expected outcome:** Registrations rise with existing traffic; SEO spend stops being wasted.
> **Confidence:** HIGH

**CFR-56: No unexplained AI decisions.**
- Every element of the chain links to the records that produced it — a KPI reading, an Event, a prior Decision.
- **Evidence must be retrievable**, not merely described. A reader can click through to the underlying record.
- A recommendation that cannot produce a chain is downgraded to `LOW` confidence and may not be raised as Critical.

**CFR-57: Confidence is derived, not asserted.**
- Inputs: evidence count and freshness, history length, calibration error for the relevant category (§9), and whether any factor was LLM-estimated rather than measured.
- The limiting factor is named at MEDIUM or LOW.

---

## 20. User Stories

| ID | Story | Acceptance |
|---|---|---|
| **US-1** | As the user, I can ask "what should I do now?" and get one action with its reason, so I stop arbitrating by what's loudest. | One primary recommendation, with reason, expected impact, effort and confidence |
| **US-2** | As the user, I am told what *not* to do, so I stop losing evenings to comfortable low-value work. | `do_not_do` list with evidence and a disposition per item |
| **US-3** | As the user, I see why a recommendation was made, so I can trust or challenge it. | Full transparency chain with clickable evidence |
| **US-4** | As the user, I approve or reject what the agent proposes to do, so it never acts beyond its authority. | L2/L3 blocked without explicit unexpired approval |
| **US-5** | As the user, I can ask why we decided something months ago, so past reasoning isn't lost. | Decision returned with reasoning and current validity |
| **US-6** | As the user, I am told when a past decision's assumptions no longer hold, so stale choices don't persist by default. | Review proposal raised; decision never auto-reversed |
| **US-7** | As the user, my effort estimates improve over time, so plans become realistic. | Calibration factor applied and visible after the minimum sample |
| **US-8** | As the user, I am told when my goal is not reachable, early enough to act. | `unreachable_under_current_assumptions` with the required change quantified |
| **US-9** | As the user, the plan adapts when something breaks, so I'm not following yesterday's plan into today's incident. | Replan proposed with an explicit diff and rationale |
| **US-10** | As the user, I can see everything the agent has ever done and who approved it. | Complete, filterable, immutable audit trail |
| **US-11** | As the user, I can set any strategic goal — not just a revenue target. | A count, milestone or duration goal works with zero code change |
| **US-12** | As the user, I am told when I keep postponing something, with a concrete choice. | Postponement pattern surfaced with schedule-or-remove options |

---

## 21. Functional Requirements — index

CFR-1 … CFR-57 are defined in place above. Grouped:

| Group | Requirements |
|---|---|
| Loop mechanics | CFR-1, CFR-2 |
| Goal model | CFR-3 – CFR-6 |
| KPI model | CFR-7 – CFR-9 |
| Priority engine | CFR-10 – CFR-14 |
| Decision engine | CFR-15 – CFR-17 |
| Execution | CFR-18 – CFR-21 |
| Measurement | CFR-22 – CFR-24 |
| Learning | CFR-25 – CFR-28 |
| Replanning | CFR-29 – CFR-34 |
| Approval | CFR-35 – CFR-37 |
| Permission | CFR-38 |
| Audit | CFR-39, CFR-40 |
| Decision journal | CFR-41, CFR-42 |
| Decision review | CFR-43 – CFR-46 |
| Stop-doing | CFR-47 – CFR-50 |
| Memory separation | CFR-51 |
| Events | CFR-52 – CFR-54 |
| Recommendations | CFR-55 – CFR-57 |

---

## 22. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **CNFR-1** | **Determinism.** Priority scoring, pace/gap arithmetic, rollups and calibration are pure functions — identical inputs, identical outputs, no LLM in the path. |
| **CNFR-2** | **Testability without an LLM.** The entire loop is exercisable in tests using fixtures and a stub provider. |
| **CNFR-3** | **Loop latency.** A full pass completes within **[PROPOSED]** 60 s; a read-only "what now?" answers within 2 s. |
| **CNFR-4** | **Idempotency.** Re-running any stage on unchanged inputs produces no duplicate side effects. |
| **CNFR-5** | **Crash safety.** Interruption mid-`EXECUTING` never resolves to `SUCCESS`. |
| **CNFR-6** | **Immutability guarantees.** Events, Execution Log and Audit Log are append-only at the storage layer, not merely by convention. |
| **CNFR-7** | **Explainability.** No score, projection or recommendation exists that cannot be decomposed into its inputs. |
| **CNFR-8** | **Goal-type agnosticism.** No strategic target, threshold or currency is hard-coded (CP-3). |
| **CNFR-9** | **Graceful degradation.** Without an LLM, scoring, pace arithmetic, scheduling and audit continue; only advice and explanation degrade, and the UI says so. |
| **CNFR-10** | **Attention economy.** Replan proposals, decision reviews and stop-doing findings are rate-limited (CFR-34, CFR-46, CFR-49). |
| **CNFR-11** | **Auditability retention.** Audit records survive for the life of the system and cannot be pruned by the application. |
| **CNFR-12** | **Confidentiality routing.** Classified records never reach a model not permitted to see them. |

---

## 23. API Requirements

**[PROPOSED]** — internal HTTP API consumed by the local web UI and channel adapters. Shapes are indicative; `bmad-architecture` refines.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/loop/state` | Current loop state, last run, next trigger |
| `POST` | `/loop/run` | Force a pass; body names the trigger |
| `GET` | `/decide/now?window_minutes=` | **The core call.** Returns a Recommendation (§6.2) |
| `GET` | `/decide/stop-doing` | Current `do_not_do` list with evidence |
| `GET` | `/goals`, `/goals/{id}` | Goal tree; pace, trajectory, gap, confidence |
| `POST` | `/goals` | Create a goal of any supported type |
| `GET` | `/goals/{id}/reachability` | Required acceleration and the unreachability finding |
| `GET` | `/kpis`, `POST /kpis/{id}/reading` | Read KPIs; record a reading |
| `GET` | `/tasks?band=` | Tasks with scores |
| `GET` | `/tasks/{id}/score` | Full factor breakdown (CFR-11) |
| `GET` | `/plan/today`, `POST /plan/{id}/accept\|reject\|modify` | Plan lifecycle |
| `GET` | `/replan/proposals` | Outstanding proposals with diffs |
| `POST` | `/actions` | Request an action; returns `PENDING_APPROVAL` or `APPROVED` |
| `POST` | `/actions/{id}/approve\|reject\|cancel` | Approval transitions |
| `GET` | `/actions/{id}` | State, result, transparency chain |
| `POST` | `/actions/{id}/outcome` | Record deferred outcome (CFR-23) |
| `GET` | `/decisions`, `POST /decisions` | Decision journal |
| `GET` | `/decisions/reviews` | Decisions whose conditions have fired |
| `POST` | `/decisions/{id}/supersede` | User-only; never agent-initiated (CFR-45) |
| `GET` | `/learning/calibration` | Current factors, sample sizes, confidence |
| `GET` | `/events?type=&since=` | Event stream |
| `GET` | `/audit?since=&action_id=` | Audit records |

**Contract rules**

- Every recommendation-bearing response embeds its transparency chain.
- Every response carrying a projection includes `confidence` and, when applicable, `insufficient_history: true`.
- No endpoint executes an L2/L3 action as a side effect of a `GET`.
- Approval endpoints are idempotent by `action_id`.

---

## 24. Database Requirements

**Core tables** (one per entity — CFR-3): `goal` · `kpi` · `kpi_reading` · `project` · `task` · `task_score` · `task_score_factor` · `plan` · `plan_item` · `action` · `approval` · `event` · `decision` · `decision_assumption` · `decision_review` · `experiment` · `calibration_factor` · `recommendation` · `evidence_link` · `memory_record` · `knowledge_document` · `execution_log` · `audit_log`.

**Requirements**

| ID | Requirement |
|---|---|
| **DB-1** | `event`, `execution_log` and `audit_log` are append-only — enforced by database permissions or triggers, not application discipline alone. |
| **DB-2** | Every table carries `created_at`; mutable tables carry `updated_at`; temporal tables carry both `occurred_at` and `recorded_at` (CFR-53). |
| **DB-3** | `goal.parent_id` is self-referencing with a cycle constraint. |
| **DB-4** | `task.project_id` is NOT NULL — every task belongs to exactly one project. |
| **DB-5** | `action` cannot be inserted without a resolved permission decision (constraint, not convention). |
| **DB-6** | `task_score_factor` stores one row per factor per scoring run, preserving the full breakdown historically. |
| **DB-7** | Every record carries a `confidentiality` column; queries assembling model context filter on it. |
| **DB-8** | `calibration_factor` stores category, factor value, sample size, computed_at — never overwriting prior values. |
| **DB-9** | Trajectory queries read only `revenue_record.classification = 'actual'` / measured KPI readings. |
| **DB-10** | `decision_assumption` is a separate table so assumptions are individually monitorable (CFR-44). |
| **DB-11** | Local-first: an embedded or single-file database is acceptable and preferred for the MVP (PRD §14 note). Schema must remain portable to a server database for the phase-2 lift. |
| **DB-12** | Daily automated local backup, retained **[PROPOSED]** 30 days. |

---

## 25. UI Requirements

Loop-specific surfaces. General IA lives in the PRD §13.

| Surface | Must show |
|---|---|
| **Now** | The single recommendation, its reason, expected impact, effort, confidence, and the approve/modify/reject/postpone controls |
| **Stop Doing** | Current `do_not_do` items, each with evidence and a disposition button (delete / defer / delegate / shrink) |
| **Why** | The transparency chain for any recommendation, with clickable evidence to the underlying records |
| **Goal cockpit** | Per goal: target, current, required pace, actual pace, trajectory, gap, confidence — and `insufficient_history` when true |
| **Reachability** | Required acceleration, and, when unreachable, exactly which assumptions must change and by how much |
| **Score breakdown** | Every factor, value, estimated-flag, weight and contribution for any task |
| **Plan + diff** | Current plan, and for any replan a clear what-moved / what-dropped / what-was-protected diff |
| **Approval queue** | Pending actions with full parameters and consequences; L3 with target confirmation |
| **Decision journal** | Decisions with assumptions and review conditions; a distinct queue for fired reviews |
| **Calibration** | Learned factors with sample size and effect on current estimates |
| **Audit** | Filterable immutable log answering the four questions of CFR-40 |

**Rules**

- **[PROPOSED]** A projection is never rendered as a number alone — confidence renders beside it or it is not shown.
- `insufficient_history` renders as an explicit state, never as zero or a flat line.
- Every "estimated" factor is visually distinguished from a measured one.

---

## 26. Security Requirements

| ID | Requirement |
|---|---|
| **SEC-1** | Fail closed — unknown tool, unknown level, or unresolved approval means no execution. |
| **SEC-2** | New tools default to L2. |
| **SEC-3** | L3 is never pre-granted and **[PROPOSED]** is confirmable only from the local UI. |
| **SEC-4** | The agent cannot escalate its own permission, nor route around a restriction by changing Worker Role. |
| **SEC-5** | **Content fetched by a tool is data, never instruction.** Web pages, issue bodies, file contents and messages cannot alter permission decisions or initiate actions. Any action originating from fetched content requires approval regardless of the tool's normal level. *(Added here — the source specification did not cover prompt injection, and it is the primary attack path against an agent with tool access.)* |
| **SEC-6** | Secrets never appear in events, execution logs, audit records, or model context. Parameters are redacted by classification before persistence. |
| **SEC-7** | Confidential records (Client / Employer) never reach a hosted model. |
| **SEC-8** | Permission changes are audited actions. |
| **SEC-9** | Approvals are single-use and expire. |
| **SEC-10** | **[PROPOSED]** Encryption at rest for memory and secret stores. |
| **SEC-11** | Destructive actions capture a reversal path (backup, branch, undo token) before executing, where technically possible. |

---

## 27. Failure Scenarios

| # | Scenario | Required behaviour |
|---|---|---|
| **F-1** | LLM provider unavailable | Scoring, pace arithmetic, scheduling, audit continue. Advice and explanation degrade; the UI states this. Never fall back to a fabricated recommendation. |
| **F-2** | Crash mid-`EXECUTING` | On restart the action resolves to `FAILED` with `interrupted: true`. Duplicate-guard prevents a repeated side effect on retry. |
| **F-3** | Machine off through a scheduled trigger | Missed triggers are identified on start and reported. Critical re-raised; informational discarded. Never silently swallowed. |
| **F-4** | KPI source unreachable | KPI marked stale, excluded from trajectory, exclusion visible. No last-known-value presented as current. |
| **F-5** | No revenue/KPI history yet | `insufficient_history`. No projection, no zero, no optimistic default. |
| **F-6** | Conflicting priorities of identical score | Deterministic tie-break (**[PROPOSED]** earlier deadline, then lower effort, then older creation). Never random. |
| **F-7** | Approval expires unactioned | Action moves to `REJECTED`/expired. Never executes late. |
| **F-8** | Tool returns malformed output | Action `FAILED` with the parse error recorded. Output is never coerced into a plausible shape. |
| **F-9** | Replan storm (rapid successive triggers) | Rate limit (CFR-34) collapses them into one proposal naming all triggers. |
| **F-10** | Calibration sample poisoned by one outlier | **[PROPOSED]** Outlier-resistant statistic (median ratio); bounded adjustment (CFR-28). |
| **F-11** | Circular goal dependency | Rejected at creation (DB-3). |
| **F-12** | User rejects every recommendation for a sustained period | Surfaced as a signal that the engine is miscalibrated — the system asks what it is getting wrong rather than continuing unchanged. |
| **F-13** | Decision review condition fires while the user is unavailable | Queues; never auto-acts (CFR-45). |
| **F-14** | Database corruption or disk failure | Restore from the most recent daily backup; the gap is reported explicitly rather than silently accepted. |

---

## 28. Edge Cases

| # | Case | Required behaviour |
|---|---|---|
| **E-1** | Available window is shorter than every candidate task | Recommend the best fitting action, or explicitly recommend rest (CFR-17). Never propose an action that cannot fit. |
| **E-2** | Two goals demand opposite actions | Surface the conflict explicitly with both goal paths; ask the user to arbitrate. Never silently pick one. |
| **E-3** | A goal is achieved early | Mark achieved; prompt to re-allocate its priority weight rather than continuing to schedule its tasks. |
| **E-4** | A goal's deadline passes unmet | Status `missed`. Retained in history — never deleted, never quietly extended. |
| **E-5** | The user completes work the system never knew about | Accept retrospective Events with `occurred_at` in the past (CFR-53); recompute affected KPIs. |
| **E-6** | An action succeeds but its outcome is negative | `status: SUCCESS`, `actual_outcome: negative`. These are distinct fields and must not be conflated. |
| **E-7** | Effort estimate absent entirely | Use the category calibration default; flag as estimated; reduce confidence. |
| **E-8** | A task serves two goals | Permitted via a link table; `StrategicImportance` uses the strongest path, not the sum, to prevent double-counting. |
| **E-9** | A decision's review condition can never fire (unmeasurable) | Flagged at creation as unreviewable; the user is asked for a date-based fallback. |
| **E-10** | Recommendation accepted but never started | Detected after **[PROPOSED]** 48 h; treated as an implicit postponement Event (CFR-54). |
| **E-11** | The user overrides a recommendation and is proven right | Recorded. Feeds calibration — the engine learns from being wrong (§9). |
| **E-12** | All goals are on track | Valid state. The engine says so and may recommend rest or opportunistic work. It does not manufacture urgency. |
| **E-13** | Experiment ends inconclusive | `inconclusive` is a permitted conclusion. Never forced positive or negative. |
| **E-14** | Clock change / DST / timezone shift | All timestamps stored UTC; scheduling evaluated in the user's local zone. Triggers neither double-fire nor skip. |

---

## 29. Acceptance Criteria

The core intelligence loop is accepted when:

**Loop**
1. Every trigger in §2.1 invokes its stages and writes a `LoopRun` Event.
2. Re-running a stage on unchanged inputs produces no duplicate side effects.
3. A read-only "what now?" mutates no state.

**Goal agnosticism**
4. A count goal, a milestone goal and a duration goal are each created and evaluated with **zero code change**.
5. **Deleting the ₹1 crore goal leaves the system fully functional** — proving nothing is hard-coded.
6. `grep` for any hard-coded strategic target or currency amount in source returns nothing.

**Prioritisation**
7. Every task carries a score, and the full factor breakdown is retrievable.
8. Identical inputs produce identical scores across runs.
9. Given the Railzy worked example, the engine ranks *fix signup bug* above *redesign logo* and emits "do not work on the logo now".
10. A task serving an at-risk goal outranks an identical task serving an on-track goal.

**Decision engine**
11. "What should I do now?" returns exactly one primary recommendation with reason, impact, effort, confidence and approval requirement.
12. The engine never recommends an action that does not fit the available window.
13. `do_not_do` items each carry evidence and a disposition.

**Execution and approval**
14. No L2/L3 action executes without an explicit unexpired approval.
15. The approval prompt shows the exact action, target and irreversible consequences.
16. The action state machine permits no transition outside §7.1.
17. A crash during execution never resolves to `SUCCESS`.

**Measurement and learning**
18. Expected versus actual effort and outcome are recorded for every executed action.
19. After the minimum sample, a calibration factor is applied to future estimates and is visible to the user.
20. Historical records are never rewritten by learning.
21. A learned claim always states its sample size.

**Replanning**
22. Given the SEO-versus-conversion scenario, the engine identifies conversion as the binding constraint and recommends fixing it before increasing traffic.
23. Every plan change states what moved, what was dropped and what was protected — with reasons.
24. Replan proposals are rate-limited outside incidents.

**Decisions**
25. A historical "why" question returns the decision, its reasoning and its current validity.
26. When an assumption changes, review is proposed — and the decision is **never** auto-reversed.

**Transparency**
27. Every important recommendation renders the full observation → evidence → reasoning → recommendation → expected-outcome chain.
28. Every evidence item is clickable through to its underlying record.
29. Confidence is derived and its limiting factor named at MEDIUM or LOW.

**Honesty**
30. With insufficient history the system reports so and refuses to project.
31. When required acceleration exceeds threshold, the system declares the goal unreachable **and names what would have to change**.
32. No fabricated metric, no success claimed for a failed action, no reconstructed rationale for an absent decision.

**Separation**
33. All eight stores exist with distinct schemas; a cross-store write fails at the schema layer.
34. Events, Execution Log and Audit Log have no application update or delete path.

---

## 30. MVP vs Post-MVP Scope

### 30.1 MVP — the loop must close

The loop's value comes from closing. A half-loop is a task manager.

| Stage | MVP contents |
|---|---|
| **GOAL** | Goal tree (arbitrary types), KPI model with manual + computed sources, pace/trajectory/gap arithmetic, reachability finding |
| **PRIORITIZE** | Deterministic scoring with full breakdown, bands, strategic alignment from the goal tree, live-user floor |
| **DECIDE** | Single-recommendation output contract, time-window awareness, `do_not_do` list, transparency chain |
| **EXECUTE** | Executable plan shape, accept/modify/reject/postpone, action state machine, approval + four permission levels, audit log |
| **MEASURE** | Expected-vs-actual effort and outcome, deferred outcome checks |
| **LEARN** | Effort calibration with minimum sample, postponement detection |
| **REPLAN** | All triggers, explained diffs, approval, rate limiting |
| **Stores** | All eight, with enforced separation and immutability |
| **Decisions** | Journal with assumptions, review conditions, review proposals |

### 30.2 Post-MVP

| Item | Why deferred |
|---|---|
| Bottleneck/funnel modelling per goal (CFR-31 full form) | MVP uses a simpler dependency heuristic; the full funnel model needs real data first |
| Impact calibration (as opposed to effort calibration) | Requires measured outcomes across many actions — months of history |
| Category-performance priority weighting (CFR-28) | Needs sufficient content history |
| Automatic KPI refresh via integrations | MVP is manual entry; integrations are PRD Phase 3 |
| Multi-goal conflict auto-arbitration | MVP surfaces conflicts for the user (E-2); automation is unsafe before calibration is trusted |
| Predictive replanning (anticipating a trigger) | Reactive replanning must be proven first |
| Cross-project opportunity discovery | Requires broader data than MVP will hold |
| Standing approvals for proven low-risk workflows | Only after demonstrated reliability; expands L1 surface deliberately |

### 30.3 Explicitly out of scope, permanently

- Autonomous reversal of strategic decisions (CFR-45).
- Any component that optimises for task count (CP-1).
- Hard-coded strategic targets of any kind (CP-3).
- Execution above L1 without approval (CP-8).

---

*Companion to the PRD at `../prds/prd-jarvis-2026-08-10/prd.md`. Where the two overlap, this document is authoritative for the loop.*

---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-jarvis-2026-08-10/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-jarvis-2026-08-10/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/core-intelligence-loop.md
  - _bmad-output/planning-artifacts/prds/prd-jarvis-2026-08-10/recommendations.md
  - _bmad-output/planning-artifacts/prds/prd-jarvis-2026-08-10/goal-model.md
  - _bmad-output/planning-artifacts/ux/ui-design-direction.html
  - _bmad-output/planning-artifacts/ux/ui-living-office.html
---

# Personal AI Operating System - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the Personal AI Operating System, decomposing the requirements from the PRD, the UX design direction, and the Architecture Spine into implementable stories.

**Naming rule (AD-9, non-negotiable):** the literal string "Jarvis" must never appear in source. One config key `AGENT_NAME` is the single source of truth; CI fails on `grep -ri jarvis` outside the config default and message templates.

### Release plan — revised after the roundtable review

The epic order below is **not** a product-launch sequence. It is shaped around one developer with 8–12 hours a week and a six-month revenue window.

| Release | Epics | Duration | Purpose |
|---|---|---|---|
| **R1 — Survive and measure** | 1, 2, 3 | ~2 months | The system wakes him, remembers his work, and reports weekly whether the revenue target is still reachable |
| **⏸ Stop and earn** | — | ~4 months | Building pauses. The window is spent selling and delivering, with R1 running daily and reporting trajectory |
| **R2 — Leverage** | 4, 5, 6 | month 7+ | Planning, execution and voice, resumed with four months of real usage data behind the decisions |
| **R3 — Judgement and reach** | 7, 8, 9 | later | Advice layer, remote reach, content pipeline |
| **R4 — The floor** | 10 | later | The isometric office as the full agent surface |

**Why the pause is in the plan.** The review concluded that this software does not earn the target — services do — and that spending the entire window building it guarantees the tool arrives after the deadline it was meant to serve. R1 exists to keep him functioning and to tell him in month two, not month five, whether the trajectory is dead. Epics 4–10 resume once that question has resolved.

**Detail level is deliberate.** Epics 1–3 carry full stories with acceptance criteria, because that work starts now. Epics 4–10 carry story outlines only. Writing detailed acceptance criteria for work that begins in month seven — against a system whose real usage will have reshaped it — is waste. They are expanded when their release is reached.

## Requirements Inventory

### Functional Requirements

**Agent core and decision loop**
- FR-1: The Agent executes the full Goal→Prioritize→Execute→Measure→Learn→Replan loop on a schedule and on demand.
- FR-2: Through any channel the user can ask what to do now and what to stop doing, and receive a ranked, evidenced answer.
- FR-3: The Agent states disagreement, with evidence, when a user-chosen action is materially lower-value than an available alternative.
- FR-4: Worker Roles bind to the single orchestration layer as prompt profile plus scoped Tool set — no separate processes.
- FR-5: Every Recommendation carries a confidence level; low confidence declares what data would raise it.

**Goal and KPI engine**
- FR-6: Maintain a hierarchical Goal tree of arbitrary goal types (monetary, count, milestone, ratio, duration, qualitative-proxy).
- FR-7: Compute Required Pace per month, week and day against remaining time and remaining amount.
- FR-8: Compute Trajectory and Gap from actual run-rate; report `insufficient_history` below 14 days rather than projecting.
- FR-9: Declare a Goal unreachable when required acceleration exceeds threshold, naming what would have to change.
- FR-10: Track KPIs against Goals and Projects with declared source and freshness; exclude stale KPIs from Trajectory.
- FR-11: Seed the initial Goal tree from configuration; children may carry null targets and report as unallocated.

**Priority engine**
- FR-12: Score every Task from weighted factors; no Task exists unscored.
- FR-13: Assign a Priority Band (P1–P4) from configurable thresholds.
- FR-14: Recommend against low-value work when the user starts a P3/P4 while a P1 exists.
- FR-15: Surface P4 deletion candidates in batch at the weekly review.
- FR-16: Explain any score as factor, value, weight and contribution — speakable by voice.

**Daily planning**
- FR-17: Generate a daily Plan covering fixed commitments, Protected Blocks and prioritised Tasks; present for approval.
- FR-18: Respect fixed commitments; never schedule into office hours, commute, gym, kids or client standup.
- FR-19: Do not over-schedule; preserve an explicit unallocated buffer and drop lowest-value items rather than compress estimates.
- FR-20: Give Railzy a recurring Protected Block on the same footing as the client standup.
- FR-21: Match work to available attention (Deep / Shallow / Audio); no deep work after 22:30.

**Dynamic replanning**
- FR-22: Detect replan triggers and write an Event naming what changed.
- FR-23: Propose a revised Plan with an explicit diff — what moved, what was dropped, what was protected, and why.
- FR-24: Require approval before a revised Plan replaces the standing Plan; expire unanswered proposals.

**Scheduler**
- FR-25: Support one-time, recurring, deadline-derived and conditional triggers, persisted across restart.
- FR-26: Ship the user's routine nudges as first-class editable triggers.
- FR-27: Emit Notification requests only; the Scheduler knows no channel.
- FR-28: Detect and report triggers missed while the machine was down; re-raise Critical, discard Informational.

**Notification system**
- FR-29: Classify every Notification as Critical, Important, Normal or Informational.
- FR-30: Deliver across local web UI, Telegram and WhatsApp, with fallback on delivery failure.
- FR-31: Enforce a notification budget; suppress and batch beyond it.
- FR-32: Honour quiet hours, suppressing all but Critical.
- FR-33: Deliver a wake-up capable of actually ringing the user.

**Task executor and tools**
- FR-34: Maintain a Tool Registry; unregistered Tool calls fail closed and are logged.
- FR-35: Execute an approved Action and record Tool, inputs, outputs, role, permission decision, duration and result.
- FR-36: Ship the MVP Tool set, independently enableable.
- FR-37: Report failure honestly; never claim success for a failed or partial Action.

**Permission and approval**
- FR-38: Enforce four Permission Levels; default new Tools to L2.
- FR-39: Time-bound Approvals to a single Action; expired approvals never execute late.
- FR-40: Accept approvals from any channel; restrict L3 to the local web UI.
- FR-41: Let the user review and change every Tool's Permission Level, auditing the change.

**Memory**
- FR-42: Maintain six Memory Partitions with distinct schemas.
- FR-43: Retrieve by natural-language question with partition and record provenance cited.
- FR-44: Classify confidentiality and exclude client/employer-confidential records from hosted-model context.

**Error recovery**
- FR-45: Explain, record and offer alternatives on failure; never silently retry dangerous Actions; capture a reversal path.

**Decision journal**
- FR-46: Record Decisions with reasoning, alternatives, assumptions, expected outcome, review trigger and status.
- FR-47: Answer historical "why did we…" questions from the journal, by voice.
- FR-48: Detect invalidated assumptions and resurface the Decision for review.

**Experiments**
- FR-49: Track Experiments with hypothesis, metric, baseline, target, duration and result.
- FR-50: Conclude Experiments and consult prior results before proposing a similar action; permit `inconclusive`.

**Content pipeline**
- FR-51: Model a Content Item through idea → concept → assets → drafted → scheduled → published → measured.
- FR-52: Maintain a content calendar and flag days with no item at or beyond `drafted`.
- FR-53: Generate per-platform titles, hooks, descriptions, tags, hashtags, captions and ideas as L1 drafts.
- FR-54: Track source footage against upcoming publish dates and warn on the supply gap.
- FR-55: Prepare publication so shipping is a single approval; produce a copy-paste bundle at MVP.
- FR-56: Track content performance and state learned patterns with sample size.

**Voice and commute**
- FR-57: Provide speech input and output with interruption handling and concise spoken responses.
- FR-58: Deliver a Commute Briefing — time remaining, top three priorities, one explicit recommendation.
- FR-59: Support conversational voice commands.
- FR-60: Never require a screen in Commute Mode; defer L3 to the local UI.

**Context modes**
- FR-61: Support Commute, Work, Evening, Creator and Planning modes.
- FR-62: Infer mode from time, day and Plan; always allow manual override.

**Briefings and reviews**
- FR-63: Deliver a concise Daily Briefing.
- FR-64: Deliver a Weekly Business Review covering all fifteen specified elements, concluding with exactly three focus items.
- FR-65: Run an End-of-Day Review that updates Task state, Goal progress, journal, experiments and tomorrow's priorities.

**Proactive intelligence and accountability**
- FR-66: Surface proactive signals with evidence.
- FR-67: Detect procrastination patterns and pair every callout with a concrete choice.
- FR-68: Detect project proliferation and propose explicit pause or removal.
- FR-69: Challenge time sinks where time spent exceeds contribution to Goals.
- FR-70: Flag repeatedly sacrificed Protected Blocks and escalate.

**Time allocation**
- FR-71: Track planned versus actual time per Project.
- FR-72: Analyse allocation against stated priorities and feed the weekly review.

**Project management**
- FR-73: Model Projects with objective, roadmap, backlog, risks, KPIs and decisions.
- FR-74: Answer project-level questions grounded in retrievable artifacts.
- FR-75: Track Naxova formation without implying the company exists.

**Railzy and GitHub**
- FR-76: Understand the Railzy repository, deployment, production status, infrastructure, bugs, roadmap and backlog.
- FR-77: Summarise Railzy state on demand, grounded in retrievable artifacts.
- FR-78: Provide GitHub read capability at L0.
- FR-79: Provide GitHub write capability under permission.

**Revenue and expense intelligence**
- FR-80: Track all Revenue Streams.
- FR-81: Distinguish Actual, Expected, Pipeline, Projected and probability-weighted revenue; Trajectory uses Actual only.
- FR-82: Rank opportunities by probability-weighted value against effort, exposing inputs.
- FR-83: Warn when a revenue assumption implies a rate far outside historical actuals.
- FR-98: Capture an earning in ≤15 seconds and ≤3 inputs, voice-capable, with inferred stream.
- FR-99: Record planned earnings as forward Pipeline with expected date and probability; flag slipped entries.
- FR-100: Operate correctly with an unallocated goal split; propose a split from evidence after four weeks.
- FR-101: Record expenses at the same friction budget, with category, project attribution and recurrence.
- FR-102: Compute gross, expenses and net separately, plus per-Project profitability; flag loss-making Projects.
- FR-103: Make prioritisation profit-aware; surface unused recurring costs as cancel candidates.
- FR-104: Track burn rate and runway; raise rising burn against flat revenue as a proactive signal.

**Business dashboard**
- FR-84: Present the goal cockpit above the fold.
- FR-85: Present per-Project panels; render "no data source connected" rather than zero.
- FR-86: Present the Agent Assessment as a written judgement, refreshed at least daily.

**Web UI**
- FR-87: Provide the fourteen UI sections, each reachable within two clicks and each with a usable empty state.
- FR-88: Render the Agent Office as the production agent surface.
- FR-89: Apply the HUD aesthetic without sacrificing legibility, target size or render performance.

**Observability and audit**
- FR-90: Maintain an immutable, append-only, inspectable Audit Log.
- FR-91: Answer "why did the agent do this?" by linking any Action to its cause and the Goal it served.
- FR-92: Track operational metrics.

**Configuration, secrets and naming**
- FR-93: Externalise configuration; store configuration, secrets, user data and logs separately; never log a secret.
- FR-94: Manage credentials securely with storage, rotation, revocation, disconnect and permission review.
- FR-95: Enforce the naming rule; renaming requires exactly one configuration change; CI verifies.
- FR-96: Abstract the model provider; select provider and model per task class by configuration.
- FR-97: Start automatically on machine start without login and emit a welcome message; surface startup failure visibly.

**Core intelligence loop (CFR-1 … CFR-57)** — specified in `core-intelligence-loop.md` and authoritative for the loop.

### NonFunctional Requirements

- NFR-1: Local-first — the MVP runs entirely on the user's machine.
- NFR-2: Cloud-ready — Scheduler and Notifier can later move to a host without redesign.
- NFR-3: Provider independence — no coupling to a single LLM vendor.
- NFR-4: Modularity — core components independently testable and replaceable.
- NFR-5: Responsiveness — voice within ~2 s; dashboard within 1.5 s; loop pass within 60 s.
- NFR-6: Spoken brevity — ≤3 sentences outside Briefings.
- NFR-7: Low cost — running cost tracked and reportable.
- NFR-8: Attention economy — notification volume budgeted; silence is a valid output.
- NFR-9: Fatigue awareness — no decision-heavy prompt after 22:30.
- NFR-10: Durability — no data loss on crash; daily local backup retained 30 days.
- NFR-11: Restart safety — a restart mid-Action never repeats a completed side effect.
- NFR-12: Auditability — every Action traceable to cause and approver, permanently.
- NFR-13: Maintainability — single-developer maintainable; one command to run.
- NFR-14: Testability — Priority, Goal and Scheduler logic deterministic and unit-testable without an LLM.
- NFR-15: Security by default — new Tools default to L2; secrets never logged; L3 local UI only.
- NFR-16: Privacy — client/employer-confidential data never reaches a hosted model.
- NFR-17: Windows-first.
- NFR-18: No fabrication — missing data renders as "no data source connected", never zero.
- NFR-19: Graceful degradation — LLM unavailability leaves Scheduler, Notifier, Tasks and Audit functional.
- NFR-20: Honest limitation disclosure — the machine-must-be-running constraint stated at setup and on missed triggers.
- CNFR-1 … CNFR-12: loop-specific non-functionals in `core-intelligence-loop.md`.

### Additional Requirements

From the Architecture Spine (AD-1 … AD-26, `final`). Binding on every story.

**Paradigm and structure** — Hexagonal ports and adapters; dependencies point inward; `domain/` imports nothing (AD-1). `src/` layout, `pyproject.toml` as single source of truth. **No starter template** — hand-rolled to the spine's tree.

**Bootstrap and operations** — One idempotent `run.py` is the only supported start (AD-19). **Windows Task Scheduler**, not NSSM (no stable release in over a decade). Single-instance lock before scheduler or polling (AD-17). Dev and live select adapter sets by environment so a dev run can never message a real channel. Forward-only migrations safe on live data. Heartbeat per loop pass (AD-26). Backup with an **exercised restore drill**.

**Persistence** — All persistence behind repository ports; no ORM type in domain or application code; backend is one config value (AD-2). Relational schema canonical; non-relational adapters enforce the same invariants (AD-3). `event`, `execution_log`, `audit_log` append-only at the storage layer (AD-8). Every derived value has exactly one writer (AD-22). Eight stores, distinct schemas (AD-14).

**Security and safety** — Relay holds no authority (AD-4). Local host never accepts inbound; UI binds loopback (AD-5). Permission evaluated locally; L3 not remotely grantable (AD-7). Confidentiality fails closed (AD-24). Fetched content is data, never instruction (AD-13). Screen capture leaves the host only as ciphertext (AD-15).

**Integration** — Channels are duplex (AD-6). Notifications carry deterministic dedupe keys (AD-23). Relay envelopes versioned and opaque (AD-25). Scheduler emits requests only (AD-11). Model access behind one port; confidential context routes local-only (AD-10). Telegram is the primary free-form channel; WhatsApp Business API carries the ringing wake-up and templated nudges.

**Code quality** — Module ≤400 lines (CI fails >500); function ≤50; params ≤5; complexity ≤10; nesting ≤4; line length 100 (AD-20). Comments carry *why*, never *what*; mypy strict; Ruff for lint and format. Shared code in named modules under `common/`; `utils`/`helpers`/`misc`/`shared` forbidden (AD-21). Time stored UTC, evaluated local; `occurred_at` and `recorded_at` (AD-16). Side effects idempotent or duplicate-guarded (AD-18). Strategic goals are data (AD-12). `AGENT_NAME` is one config value (AD-9).

**Stack** — Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, SQLite → PostgreSQL, APScheduler **3.11.x**, python-telegram-bot 22.8, pydantic-settings, keyring, Ruff, mypy, pytest. VPS in an India region.

### UX Design Requirements

- UX-DR1: Design token system — ground `#080C11`, surface `#101822`, rule `#1E2C3A`, ink `#DEE8F0`, accent `#3ED0DE`, gold `#E7B25C`, semantic ok/warn/crit held separate from the accent.
- UX-DR2: Typography roles — monospace with `tabular-nums` for figures, uppercase letter-spaced micro-labels, sans for prose only.
- UX-DR3: `Instrument` panel component — bordered container, label bar, status pill, body slot.
- UX-DR4: Severity encoded as a 2px left stripe, never colour swap alone.
- UX-DR5: Priority Band chips P1–P4.
- UX-DR6: Fourteen IA sections, each within two clicks.
- UX-DR7: Goal cockpit above the fold with a required-pace marker on the progress track.
- UX-DR8: Transparency-chain component with clickable evidence.
- UX-DR9: Empty and `insufficient_history` states designed explicitly — never a zero or a flat line.
- UX-DR10: Isometric office floor on Canvas as the production agent surface, single rAF loop.
- UX-DR11: Worker cabins with nameplate, desk, monitor, seated persona; roles separable by silhouette.
- UX-DR12: Orchestrator office — glass, holographic rings that spin with load; never leaves the room.
- UX-DR13: Owner's office as the largest room, gold-accented, approval tray, "N waiting on you".
- UX-DR14: Approval round-trip animation — request to the owner's desk, glows pending, returns green.
- UX-DR15: Assignment animated as walking; a figure in the corridor always means work changed hands.
- UX-DR16: "Awaiting approval" encoded as a raised hand with motion stopped, pulsing amber.
- UX-DR17: Lighting model — ceiling pools, wall gradients, ambient occlusion, contact shadows, monitor spill.
- UX-DR18: Honour `prefers-reduced-motion`; explicit motion toggle; all states readable with motion off.
- UX-DR19: Live readout strip.
- UX-DR20: Timestamped activity feed with `aria-live`.
- UX-DR21: Performance budget for a screen left open all day.
- UX-DR22: Production floor states — zero workers, crashed worker, more tasks than cabins, long titles, offline integration.
- UX-DR23: Mobile relay view — latest encrypted screenshot, command box, conversation thread.
- UX-DR24: Accessibility — visible focus, `aria-label` on canvas, `aria-live` on feed, standard target sizes.

### FR Coverage Map

**Epic 1 — It wakes me up:** FR-25, FR-26, FR-27, FR-28, FR-29, FR-30 *(Telegram)*, FR-31, FR-32, FR-54 *(footage warning only)*, FR-93, FR-94, FR-95, FR-96, FR-97
**Epic 2 — It knows my work:** FR-42, FR-43, FR-44, FR-73, FR-74, FR-75, FR-87
**Epic 3 — It follows the money:** FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, FR-80, FR-81, FR-82, FR-83, FR-84, FR-85, FR-86, FR-98, FR-99, FR-100, FR-101, FR-102, FR-103, FR-104
**Epic 4 — It tells me what to do next:** FR-1, FR-2, FR-12 … FR-24
**Epic 5 — It does work when I ask:** FR-34 … FR-41, FR-45, FR-76, FR-77, FR-78, FR-79, FR-90, FR-91, FR-92 · UX-DR13 *(list-view owner approvals)*
**Epic 6 — I can use it in the car:** FR-57 … FR-62
**Epic 7 — It advises me:** FR-3, FR-4, FR-5, FR-46 … FR-50, FR-63 … FR-72 · UX-DR8
**Epic 8 — It reaches me anywhere:** FR-30 *(WhatsApp)*, FR-33 · UX-DR23
**Epic 9 — The reel ships itself:** FR-51, FR-52, FR-53, FR-55, FR-56 *(FR-54 partly in Epic 1)*
**Epic 10 — The office floor:** FR-88, FR-89 · UX-DR10, 11, 12, 14, 15, 16, 17, 21, 22

Cross-cutting and carried by every epic as story acceptance criteria rather than owned by one: NFR-1…NFR-20, CNFR-1…CNFR-12, AD-1…AD-26, UX-DR1–7, UX-DR9, UX-DR18–20, UX-DR24.

**Coverage check:** FR-1 … FR-104 all mapped. FR-30 is split by channel and FR-54 by scope, both deliberately.

## Epic List

### Epic 1: It wakes me up
Nudges fire on the user's real routine from a service that starts itself on boot and survives reboot without a login. Usable alone.
**FRs covered:** FR-25–FR-32, FR-30 *(Telegram)*, FR-54 *(footage warning)*, FR-93–FR-97

### Epic 2: It knows my work
The user messages the system on Telegram and it understands and remembers — routine, projects, tasks, stable facts. State survives restart and restore is proven.
**FRs covered:** FR-42, FR-43, FR-44, FR-73, FR-74, FR-75, FR-87

### Epic 3: It follows the money
Log an earning or expense in seconds; see required pace, trajectory, gap and net; get told early when the numbers stop adding up.
**FRs covered:** FR-6–FR-11, FR-80–FR-86, FR-98–FR-104

### Epic 4: It tells me what to do next
A realistic daily plan that respects fixed commitments and leaves buffer, and one answer with reasoning whenever asked.
**FRs covered:** FR-1, FR-2, FR-12–FR-24

### Epic 5: It does work when I ask
Executes approved work through GitHub, files, browser and research — nothing above a safe local draft without approval, everything audited.
**FRs covered:** FR-34–FR-41, FR-45, FR-76–FR-79, FR-90–FR-92

### Epic 6: I can use it in the car
Spoken commute briefing; create, reschedule and ask by voice without touching a screen.
**FRs covered:** FR-57–FR-62

### Epic 7: It advises me
Recommendations with evidence, a decision journal that answers "why did we…", experiments that conclude, and a weekly review ending in exactly three focus items.
**FRs covered:** FR-3, FR-4, FR-5, FR-46–FR-50, FR-63–FR-72

### Epic 8: It reaches me anywhere
WhatsApp nudges, a ringing wake-up call, and a phone view of the latest encrypted screen capture with command entry.
**FRs covered:** FR-30 *(WhatsApp)*, FR-33

### Epic 9: The reel ships itself
Content calendar, per-platform generation, and shipping reduced to a single approval.
**FRs covered:** FR-51, FR-52, FR-53, FR-55, FR-56

### Epic 10: The office floor
The isometric office as the full agent surface — cabins, orchestrator, owner's corner office, approvals arriving at the desk.
**FRs covered:** FR-88, FR-89

---

## Epic 1: It wakes me up

Nudges fire on the user's real routine — 06:00 wake, 07:30 gym, 09:10 leave gym, 20:00 client standup — delivered to Telegram by a service that starts itself on boot and survives reboot without a login. After this epic the system reaches out every day without the user opening anything.

### Story 1.1: Start on boot and say hello

As the owner,
I want the system to start itself whenever my machine starts and greet me,
So that I never have to remember to launch it and I know immediately that it is alive.

**Acceptance Criteria:**

**Given** a machine with only Python installed and no prior setup
**When** I run `run.py` for the first time
**Then** it creates the virtual environment, installs dependencies, creates the database, applies migrations and writes a configuration scaffold
**And** it then starts the system without requiring a second command

**Given** a healthy existing installation
**When** I run `run.py` again
**Then** it detects setup is complete, skips every setup step, and starts
**And** no existing data is modified or destroyed

**Given** the system is registered with Windows Task Scheduler
**When** the machine reboots and no user logs in
**Then** the system starts and emits its welcome message
**And** the message renders the configured `AGENT_NAME`, not a hardcoded string

**Given** an already-running instance holds the single-instance lock
**When** a second instance is launched
**Then** it exits with a clear diagnostic naming the existing holder
**And** neither the scheduler nor any channel poller starts in the second process

**Given** startup fails for any reason
**When** the failure occurs
**Then** it is surfaced visibly to the user rather than only written to a log

### Story 1.2: Keep configuration and secrets out of the code

As the owner,
I want configuration and credentials handled properly from the first commit,
So that I can rename the assistant, swap a model provider or rotate a token without touching source.

**Acceptance Criteria:**

**Given** the source tree at any commit
**When** CI runs `grep -ri jarvis` across it
**Then** zero hits are returned outside the config default and message templates
**And** the build fails if that check does not pass

**Given** a running system
**When** I change `AGENT_NAME` in configuration and restart
**Then** every user-facing message uses the new name
**And** no code change was required

**Given** any credential is stored
**When** it is written
**Then** it goes to the OS credential store, never to a config file, a log, an event or an audit record
**And** attempting to log a value marked secret is redacted before write

**Given** the model provider port
**When** a provider is selected by configuration
**Then** no provider-specific type appears outside its adapter
**And** switching provider requires no change in `domain/` or `app/`

### Story 1.3: Schedule my routine

As the owner,
I want my fixed daily routine held as real scheduled triggers,
So that the system knows when my day happens without me re-explaining it.

**Acceptance Criteria:**

**Given** a first run
**When** setup completes
**Then** triggers exist for 06:00 wake, 07:30 gym, 09:10 leave gym and 20:00 client standup on Mon–Fri
**And** each is individually editable and disableable

**Given** a scheduled trigger exists
**When** the system restarts
**Then** the trigger survives and still fires at its next occurrence
**And** schedule state was read from the database, not reconstructed from code

**Given** a trigger fires
**When** it produces output
**Then** it emits a Notification request only
**And** the scheduler contains no reference to Telegram or any other channel

**Given** trigger evaluation
**When** a clock change or DST transition occurs
**Then** the trigger neither double-fires nor silently skips
**And** timestamps are stored in UTC and evaluated in the configured local timezone

### Story 1.4: Reach me on Telegram

As the owner,
I want nudges delivered to Telegram and to be able to reply,
So that the system reaches me on a phone I already carry, and I can answer it.

**Acceptance Criteria:**

**Given** a configured bot token
**When** the system starts
**Then** it connects by long polling with no inbound port opened and no router configuration required

**Given** a Notification is raised
**When** it is delivered
**Then** it arrives in Telegram
**And** the delivery outcome is recorded

**Given** I reply to a message in Telegram
**When** the reply arrives
**Then** it is routed into the common command-intake path
**And** the channel adapter implements both send and receive against the same port

**Given** delivery fails on the primary channel
**When** a fallback channel is configured
**Then** the message is attempted on the fallback
**And** the original failure is recorded rather than swallowed

**Given** the environment is set to `dev`
**When** any notification is produced
**Then** it is delivered to a stub adapter and no real Telegram message is ever sent

### Story 1.5: Don't spam me

As the owner,
I want the system to respect my attention,
So that I keep reading its messages instead of muting it.

**Acceptance Criteria:**

**Given** any Notification
**When** it is created
**Then** it carries a class of Critical, Important, Normal or Informational
**And** it carries a deterministic dedupe key derived from trigger identity and target occurrence

**Given** two producers raise a notification for the same underlying event
**When** both reach the notifier within the dedupe window
**Then** only one is delivered
**And** the suppression is recorded

**Given** the configured quiet hours are in effect
**When** a non-Critical notification is raised
**Then** it is withheld and delivered at the next permitted window
**And** Critical notifications are delivered regardless

**Given** the daily notification budget is exhausted
**When** further Normal or Informational notifications are raised
**Then** they are batched rather than delivered
**And** the day's notification count is retrievable as a metric

### Story 1.6: Tell me what you missed

As the owner,
I want to know when the system was down and what it missed,
So that I can trust its silence instead of wondering whether it broke.

**Acceptance Criteria:**

**Given** the machine was off across a scheduled trigger
**When** the system next starts
**Then** it reports which triggers were missed and their scheduled times
**And** missed Critical triggers are re-raised while Informational ones are discarded

**Given** the system is running
**When** each loop pass completes
**Then** a heartbeat is written

**Given** the heartbeat has not been written beyond the configured threshold
**When** the system next starts
**Then** the gap is surfaced to the user as a visible signal, not only a log line

**Given** first-time setup
**When** the user completes it
**Then** they are told plainly that scheduled notifications only fire while the machine is running

### Story 1.7: Warn me before tonight's reel has no footage

As the owner,
I want to be told during the day when tonight's upload has nothing behind it,
So that I find out at 10:00 while I can still act, not at 23:10 when I cannot.

**Acceptance Criteria:**

**Given** a list of upcoming publish dates and a record of available unused footage
**When** the daily check runs
**Then** any upcoming date with no footage behind it is identified

**Given** tonight's slot has no footage
**When** the check runs
**Then** a notification is raised in the morning window, not in the evening
**And** it states which date is short and how many days of footage remain

**Given** every upcoming date is covered
**When** the check runs
**Then** no notification is raised at all

*Note: this is the footage-gap warning only. Content generation, calendar management and publishing are Epic 9.*

---

## Epic 2: It knows my work

The user can message the system on Telegram and have it understand and remember — routine, projects, tasks, and stable facts about how they work. State survives restart, restore is proven, and the local web UI shell exists with honest empty states.

### Story 2.1: Remember who I am and how my week runs

As the owner,
I want the system to hold my routine and working style as structured data,
So that everything it later plans or suggests is built on how my week actually works.

**Acceptance Criteria:**

**Given** the User memory partition
**When** my routine is stored
**Then** daily times and the weekly pattern of office, work-from-home and clear days are queryable as structured data, not prose

**Given** a write addressed to the wrong partition
**When** it is attempted
**Then** it fails at the interface as a schema error

**Given** any stored record
**When** it is written
**Then** it carries a confidentiality classification
**And** a write with no classification is rejected rather than defaulted permissively

### Story 2.2: Capture a task from a message

As the owner,
I want to send a message and have it become a tracked task,
So that things stop living in my head while I am away from a desk.

**Acceptance Criteria:**

**Given** I send a message describing something to do
**When** it is processed
**Then** a Task is created belonging to exactly one Project
**And** it is confirmed back to me in one short line

**Given** a created Task
**When** the system restarts
**Then** the Task still exists with the same state

**Given** any Task state change
**When** it occurs
**Then** an Event is appended recording it
**And** the Event store exposes no update or delete path

### Story 2.3: Organise my work into projects

As the owner,
I want my work grouped into the ventures I actually run,
So that the system can later reason about them separately.

**Acceptance Criteria:**

**Given** first-time setup
**When** it completes
**Then** Projects exist for Railzy, Content, Freelance Client, Naxova and Personal
**And** each carries an objective and a status

**Given** the Naxova project
**When** it is displayed or referenced
**Then** its formation status is shown as not yet formed
**And** no output implies it is an operating company

**Given** a question about a Project
**When** I ask what is open on it
**Then** the answer cites the underlying Tasks or Events it came from

### Story 2.4: Ask it what I've got on

As the owner,
I want to ask questions in natural language and get grounded answers,
So that I can check state from my phone without opening anything.

**Acceptance Criteria:**

**Given** a natural-language question
**When** it is answered
**Then** the answer names the partition and records it drew from

**Given** the system holds no relevant data
**When** I ask about it
**Then** it says it does not have that
**And** it does not construct a plausible answer

**Given** the LLM provider is unreachable
**When** I ask a question
**Then** scheduling, notification, task capture and audit continue to work
**And** the UI states that answering is degraded

### Story 2.5: Keep client work off hosted models

As the owner,
I want confidential work provably excluded from third-party models,
So that using this system cannot breach my client obligations.

**Acceptance Criteria:**

**Given** a record classified client-confidential or employer-confidential
**When** model context is assembled for a hosted provider
**Then** the record is excluded
**And** the exclusion is enforced at the routing layer, not by prompt instruction

**Given** a record whose provenance cannot be established
**When** it is classified
**Then** it receives the most restrictive class

**Given** an attempt to route confidential context to a hosted provider
**When** it occurs
**Then** the call is denied and the attempt is recorded as a security event

### Story 2.6: Survive a restart, and prove I can restore

As the owner,
I want my data durable and my backups actually tested,
So that months of accumulated context cannot vanish.

**Acceptance Criteria:**

**Given** the system is running
**When** the process is killed without warning
**Then** no committed Task, Event, Project or configuration is lost on restart

**Given** the daily backup has run
**When** I perform a restore drill into a scratch location
**Then** the restored database opens, passes integrity checks, and contains the expected records
**And** the drill is documented as performed

**Given** a schema migration
**When** it is applied to a database containing real data
**Then** it completes without data loss
**And** a failed migration leaves the previous version running

### Story 2.7: See it in a browser

As the owner,
I want a local web interface with honest empty states,
So that I have somewhere to look that tells me the truth on day one.

**Acceptance Criteria:**

**Given** the system is running
**When** I open the local UI
**Then** it is served on loopback only and is not reachable from another machine

**Given** a section with no data yet
**When** I open it
**Then** it explains what will live there and how to populate it
**And** it does not render a zero or an empty chart as though it were a real value

**Given** the fourteen sections
**When** I navigate from the Dashboard
**Then** each is reachable within two clicks

---

## Epic 3: It follows the money

The user can log an earning or an expense in seconds and see required pace, actual pace, trajectory, gap, net position and per-project profitability. When the numbers stop adding up, the system says so early and names what would have to change.

### Story 3.1: Log an earning in seconds

As the owner,
I want to record money received in a few words,
So that logging never becomes the thing I stop doing.

**Acceptance Criteria:**

**Given** I send a short message such as "log forty thousand from the client"
**When** it is processed
**Then** a Revenue Record is created with amount, stream and date
**And** the interaction takes no more than three inputs from me

**Given** the stream can be inferred from context
**When** the record is created
**Then** the inferred stream is confirmed back rather than typed by me

**Given** an earning that happened earlier
**When** I log it with a past date
**Then** it is stored with the correct `occurred_at` and a separate `recorded_at`

**Given** money is stored
**When** any amount is persisted
**Then** it is held as integer minor units with an ISO currency code, never as a float

### Story 3.2: Log an expense the same way

As the owner,
I want expenses captured at the same low friction,
So that I see net rather than only gross.

**Acceptance Criteria:**

**Given** I log an expense
**When** it is created
**Then** it carries amount, date, category, project attribution and recurrence

**Given** a recurring expense
**When** I enter it once
**Then** forward records are generated automatically
**And** I am never asked to re-enter a monthly cost

**Given** an expense with no clear project
**When** it is stored
**Then** it sits in an explicit unattributed bucket
**And** it is never silently spread across projects

### Story 3.3: Set any goal, not just a money one

As the owner,
I want the goal engine to hold any kind of target,
So that the system is not welded to one number I might abandon.

**Acceptance Criteria:**

**Given** the goal engine
**When** I create a monetary, count, milestone, ratio or duration goal
**Then** each is accepted and evaluated with no code change

**Given** the source tree
**When** it is searched for a strategic target, currency amount or threshold
**Then** none is found

**Given** every configured goal is deleted
**When** the system starts
**Then** it starts, runs and passes its test suite

**Given** a goal with no measurable KPI or proxy
**When** creation is attempted
**Then** it is rejected with an explanatory error

### Story 3.4: See required pace and where I actually am

As the owner,
I want the arithmetic of my target computed honestly,
So that I know the gap rather than guessing it.

**Acceptance Criteria:**

**Given** a goal with a target and deadline
**When** pace is computed
**Then** required per-day, per-week and per-month figures are derived from *remaining* amount and *remaining* time

**Given** fewer than fourteen days of revenue history
**When** trajectory is requested
**Then** the system reports `insufficient_history`
**And** renders that state explicitly rather than as a zero or a flat line

**Given** sufficient history
**When** trajectory is computed
**Then** it uses Actual revenue only
**And** Expected, Pipeline and Projected are displayed separately and never merged into the trajectory line

**Given** any projection is displayed
**When** it is rendered
**Then** a derived confidence accompanies it, with the limiting factor named at Medium or Low

### Story 3.5: Tell me when it doesn't add up

As the owner,
I want to be told early and plainly when my target is out of reach,
So that I can change strategy while there is still time.

**Acceptance Criteria:**

**Given** required acceleration exceeds the configured threshold
**When** the check runs
**Then** the system states the goal is not reachable under current assumptions
**And** it names which assumptions would have to change, and by how much

**Given** the unreachable finding has already been raised
**When** the check runs again the same week
**Then** it is not raised again

**Given** I acknowledge the finding and continue
**When** I do so
**Then** the acknowledgement is recorded as a Decision with a review trigger

**Given** an Expected or Pipeline figure implies a rate far outside historical actuals
**When** it is entered
**Then** the system challenges it and states the implied multiple

### Story 3.6: Show me net, not just gross

As the owner,
I want gross, expenses and net side by side, and profitability per venture,
So that I can see which projects actually make money.

**Acceptance Criteria:**

**Given** revenue and expense records exist
**When** the cockpit renders
**Then** gross, total expenses and net are each shown separately

**Given** a project with attributable revenue and expenses
**When** profitability is computed
**Then** it is shown for any selected window
**And** a project whose expenses exceed its revenue is flagged with the monthly bleed stated

**Given** a recurring cost attached to a project with no revenue in sixty days
**When** the check runs
**Then** it is surfaced as a cancel candidate

**Given** monthly burn and committed forward costs
**When** the cockpit renders
**Then** burn rate is shown, and rising burn against flat revenue is raised as a signal

### Story 3.7: Propose the split once there's evidence

As the owner,
I want the system to derive my goal split from where money actually arrives,
So that my targets stop being guesses.

**Acceptance Criteria:**

**Given** child goals carry null targets
**When** the engine runs
**Then** required pace, actual pace, trajectory and gap are still computed for the root goal
**And** children are reported as unallocated, never as zero

**Given** four weeks of revenue records exist
**When** the review point is reached
**Then** the system proposes a split derived from actual arrivals, with the evidence attached

**Given** a proposed split
**When** it is produced
**Then** it is presented as a recommendation I accept or reject
**And** it is never applied automatically

**Given** no split has been set
**When** I ask which stream is behind
**Then** the system reports which stream is *producing* instead
**And** it does not invent a target to measure against

---

## Epic 4: It tells me what to do next

*Story outline — expanded when R2 begins.*

- **4.1** Score every task against my goals — deterministic scoring, full factor breakdown retrievable
- **4.2** Sort my backlog into do-now, this-week, scheduled and delete — priority bands
- **4.3** Build me a realistic day — fixed commitments respected, buffer preserved, work matched to available attention
- **4.4** Protect the time that never gets protected — recurring Protected Block, Naxova first per Split B
- **4.5** Ask what to do right now — one answer, its reasoning, and what it displaces
- **4.6** Tell me when I'm about to waste an evening — P4-while-P1-exists callout, stated once
- **4.7** Replan when the day breaks — trigger detection, explicit diff, approval required
- **4.8** Explain any ranking — factor, value, weight, contribution, speakable aloud

## Epic 5: It does work when I ask

*Story outline — expanded when R2 begins.*

- **5.1** Refuse anything not in the registry — Tool Registry, fail closed
- **5.2** Ask before you act — four permission levels, default L2, built before the tools it governs
- **5.3** Approve from wherever I am — any channel for L2, local UI only for L3
- **5.4** Never act twice — idempotency keys, duplicate guards, crash-safe terminal states
- **5.5** Read my repositories — GitHub read at L0
- **5.6** Draft and file, but don't push — issues and comments at L1, push and merge at L2, deploy at L3
- **5.7** Work with my files and the web — filesystem, research, browser tools, each independently enableable
- **5.8** Treat what you read as data, not orders — prompt-injection containment; untrusted-origin actions always need approval
- **5.9** Tell me the truth when it fails — honest failure, partial reported as partial, reversal path captured
- **5.10** Show me everything you did and who approved it — append-only audit, "why did you do this?" answerable
- **5.11** Show me who's working — agent activity list view with owner approval queue *(the office metaphor, minus the room)*
- **5.12** Know what's wrong with Railzy — repository, deployment, bugs, backlog summarised on demand

## Epic 6: I can use it in the car

*Story outline — expanded when R2 begins.*

- **6.1** Talk to me on the drive — local STT/TTS, no audio leaves the machine
- **6.2** Brief me before I arrive — time remaining, top three, one recommendation, inside 90 seconds
- **6.3** Change my plan by voice — create, reschedule, ask, without touching a screen
- **6.4** Know where I am — context modes inferred, always manually overridable
- **6.5** Never make me look at a screen mid-drive — L3 refused in Commute Mode

## Epic 7: It advises me

*Story outline — expanded when R3 begins.*

- **7.1** Show your working — observation → evidence → reasoning → recommendation → expected outcome, evidence clickable
- **7.2** Disagree with me when the data supports it — stated once, override recorded
- **7.3** Remember why we decided things — decision journal with assumptions and review conditions
- **7.4** Tell me when a past decision has expired — review proposed, never auto-reversed
- **7.5** Run experiments that actually conclude — hypothesis, baseline, metric, result, `inconclusive` permitted
- **7.6** Learn how wrong my estimates are — effort calibration applied forward only, sample size always shown
- **7.7** Brief me each morning and review each night — daily briefing, end-of-day review
- **7.8** Give me three things a week, not twenty — weekly business review
- **7.9** Call out what I keep avoiding — postponement patterns, project proliferation, time sinks, sacrificed blocks
- **7.10** Show me where my time actually went — planned versus actual per project

## Epic 8: It reaches me anywhere

*Story outline — expanded when R3 begins. Depends on external lead time: WhatsApp Business API verification through a BSP, a second number, and pre-approved templates.*

- **8.1** Nudge me on WhatsApp — Business API, templated messages outside the 24-hour window
- **8.2** Actually wake me up — ringing call via the Business Calling API
- **8.3** Put a courier on a server that can't do anything — relay with no authority, outbound-only local agent
- **8.4** Let me see my screen from my phone — on-demand capture, encrypted on the host, relay stores ciphertext only
- **8.5** Command it from anywhere — mobile relay view, commands executed locally under the normal permission model

## Epic 9: The reel ships itself

*Story outline — expanded when R3 begins.*

- **9.1** Track every piece of content through its lifecycle
- **9.2** Show me the calendar and what's missing
- **9.3** Draft titles, hooks, descriptions, tags and captions per platform
- **9.4** Reduce shipping to one approval — copy-paste bundle at MVP
- **9.5** Learn what actually performs — patterns stated with sample size, provisional below five items

## Epic 10: The office floor

*Story outline — expanded when R4 begins. The list view from Story 5.11 already covers the functional need; this epic is the full surface.*

- **10.1** Build the isometric floor — cabins, corridor, orchestrator office, owner's corner office
- **10.2** Give every role a recognisable person — silhouette, gear, seated and walking states
- **10.3** Make assignment visible — walking, collecting, carrying, returning
- **10.4** Make approvals arrive at my desk — request travels, glows pending, returns green
- **10.5** Light the room — ceiling pools, wall gradients, ambient occlusion, contact shadows, monitor spill
- **10.6** Handle a real floor, not a demo — zero workers, crashed worker, more tasks than cabins, long titles, offline integrations
- **10.7** Stay cheap enough to leave open all day — performance budget, reduced-motion support

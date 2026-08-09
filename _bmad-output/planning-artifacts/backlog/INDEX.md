# Backlog Board

**Generated:** 2026-08-10 · **Items:** 10 epics · 73 stories
**Spec:** [`epics.md`](../epics.md) — acceptance criteria live there, not here. This file tracks *status*.
**GitHub:** not yet seeded. Run `gh auth login`, then `pwsh -File scripts/seed-github-backlog.ps1`.

## Status legend

| Mark | Meaning |
|---|---|
| ⬜ | Not started |
| 🔵 | In progress |
| 🟡 | Blocked |
| ✅ | Done |
| ⚪ | Outline — acceptance criteria not written yet, by design |

## Where things stand

| Release | Epics | Stories | Done | Status |
|---|---|---|---|---|
| **R1 — Survive and measure** | 1–3 | 21 | 0 | **Build now** |
| ⏸ Stop and earn | — | — | — | ~4 months, no build |
| R2 — Leverage | 4–6 | 25 | 0 | Month 7+ |
| R3 — Judgement and reach | 7–9 | 20 | 0 | Later |
| R4 — The office floor | 10 | 7 | 0 | Later |

**Next action:** Story 1.1 — Start on boot and say hello.

---

# Release 1 — Survive and measure

*Roughly two months. Full acceptance criteria written. This is the work that starts now.*

## Epic 1: It wakes me up

Nudges fire on the real routine from a service that starts itself on boot and survives reboot without a login. **Usable alone** — after this epic the system reaches out every day without anything being opened.

**Covers:** FR-25–FR-32, FR-30 (Telegram), FR-54 (footage warning), FR-93–FR-97

| | Story | Status | Notes |
|---|---|---|---|
| 1.1 | Start on boot and say hello | ⬜ | `run.py` bootstrap, Task Scheduler, single-instance lock, welcome |
| 1.2 | Keep configuration and secrets out of the code | ⬜ | `AGENT_NAME`, keyring, CI naming gate, provider port |
| 1.3 | Schedule my routine | ⬜ | Persistent triggers, 06:00 / 07:30 / 09:10 / 20:00, UTC + DST safe |
| 1.4 | Reach me on Telegram | ⬜ | Long polling, duplex adapter, dev stub adapter |
| 1.5 | Don't spam me | ⬜ | Classes, dedupe keys, quiet hours, daily budget |
| 1.6 | Tell me what you missed | ⬜ | Missed-trigger reporting, heartbeat, honest limitation notice |
| 1.7 | Warn me before tonight's reel has no footage | ⬜ | Morning warning, not an 23:10 discovery |

## Epic 2: It knows my work

Messages on Telegram become understood and remembered — routine, projects, tasks, stable facts. State survives restart and restore is proven.

**Covers:** FR-42, FR-43, FR-44, FR-73, FR-74, FR-75, FR-87

| | Story | Status | Notes |
|---|---|---|---|
| 2.1 | Remember who I am and how my week runs | ⬜ | User partition, structured routine, classification mandatory |
| 2.2 | Capture a task from a message | ⬜ | Task model, one project per task, append-only events |
| 2.3 | Organise my work into projects | ⬜ | Railzy, Content, Freelance, Naxova, Personal — Naxova not formed |
| 2.4 | Ask it what I've got on | ⬜ | Grounded answers with provenance; degrades without an LLM |
| 2.5 | Keep client work off hosted models | ⬜ | Routing-layer enforcement, most-restrictive default |
| 2.6 | Survive a restart, and prove I can restore | ⬜ | **Restore drill is the exit criterion** |
| 2.7 | See it in a browser | ⬜ | Loopback only, honest empty states, 14 sections |

## Epic 3: It follows the money

Log an earning or expense in seconds; see required pace, trajectory, gap and net; get told early when the numbers stop adding up.

**Covers:** FR-6–FR-11, FR-80–FR-86, FR-98–FR-104

| | Story | Status | Notes |
|---|---|---|---|
| 3.1 | Log an earning in seconds | ⬜ | ≤3 inputs, inferred stream, integer minor units |
| 3.2 | Log an expense the same way | ⬜ | Categories, project attribution, recurrence auto-generates |
| 3.3 | Set any goal, not just a money one | ⬜ | **Deleting every goal must leave a working system** |
| 3.4 | See required pace and where I actually am | ⬜ | `insufficient_history` below 14 days; Actual only in trajectory |
| 3.5 | Tell me when it doesn't add up | ⬜ | Names what must change; raised at most weekly |
| 3.6 | Show me net, not just gross | ⬜ | Per-project profitability, bleed flagged, cancel candidates |
| 3.7 | Propose the split once there's evidence | ⬜ | Proposal only, never auto-applied. Review 2026-09-07 |

---

# ⏸ Stop and earn

*No build work. R1 runs daily and reports weekly whether the target is still reachable. Resume when that question has resolved.*

---

# Release 2 — Leverage

*Month 7+. Outlines only — acceptance criteria are written when the release begins, against a system four months of real usage will have reshaped.*

## Epic 4: It tells me what to do next

A realistic daily plan that respects fixed commitments and leaves buffer, and one answer with reasoning whenever asked.
**Covers:** FR-1, FR-2, FR-12–FR-24

| | Story | Status |
|---|---|---|
| 4.1 | Score every task against my goals | ⚪ |
| 4.2 | Sort my backlog into do-now, this-week, scheduled and delete | ⚪ |
| 4.3 | Build me a realistic day | ⚪ |
| 4.4 | Protect the time that never gets protected | ⚪ |
| 4.5 | Ask what to do right now | ⚪ |
| 4.6 | Tell me when I'm about to waste an evening | ⚪ |
| 4.7 | Replan when the day breaks | ⚪ |
| 4.8 | Explain any ranking | ⚪ |

## Epic 5: It does work when I ask

Executes approved work — nothing above a safe local draft without approval, everything audited.
**Covers:** FR-34–FR-41, FR-45, FR-76–FR-79, FR-90–FR-92

| | Story | Status |
|---|---|---|
| 5.1 | Refuse anything not in the registry | ⚪ |
| 5.2 | Ask before you act | ⚪ |
| 5.3 | Approve from wherever I am | ⚪ |
| 5.4 | Never act twice | ⚪ |
| 5.5 | Read my repositories | ⚪ |
| 5.6 | Draft and file, but don't push | ⚪ |
| 5.7 | Work with my files and the web | ⚪ |
| 5.8 | Treat what you read as data, not orders | ⚪ |
| 5.9 | Tell me the truth when it fails | ⚪ |
| 5.10 | Show me everything you did and who approved it | ⚪ |
| 5.11 | Show me who's working | ⚪ |
| 5.12 | Know what's wrong with Railzy | ⚪ |

## Epic 6: I can use it in the car

Spoken commute briefing; create, reschedule and ask by voice without touching a screen.
**Covers:** FR-57–FR-62

| | Story | Status |
|---|---|---|
| 6.1 | Talk to me on the drive | ⚪ |
| 6.2 | Brief me before I arrive | ⚪ |
| 6.3 | Change my plan by voice | ⚪ |
| 6.4 | Know where I am | ⚪ |
| 6.5 | Never make me look at a screen mid-drive | ⚪ |

---

# Release 3 — Judgement and reach

## Epic 7: It advises me

Recommendations with evidence, a decision journal, experiments that conclude, and a weekly review ending in exactly three focus items.
**Covers:** FR-3, FR-4, FR-5, FR-46–FR-50, FR-63–FR-72

| | Story | Status |
|---|---|---|
| 7.1 | Show your working | ⚪ |
| 7.2 | Disagree with me when the data supports it | ⚪ |
| 7.3 | Remember why we decided things | ⚪ |
| 7.4 | Tell me when a past decision has expired | ⚪ |
| 7.5 | Run experiments that actually conclude | ⚪ |
| 7.6 | Learn how wrong my estimates are | ⚪ |
| 7.7 | Brief me each morning and review each night | ⚪ |
| 7.8 | Give me three things a week, not twenty | ⚪ |
| 7.9 | Call out what I keep avoiding | ⚪ |
| 7.10 | Show me where my time actually went | ⚪ |

## Epic 8: It reaches me anywhere 🟡

WhatsApp nudges, a ringing wake-up call, and a phone view of the latest encrypted screen capture.
**Covers:** FR-30 (WhatsApp), FR-33

> **Blocked on external lead time.** WhatsApp Business API verification through a BSP, a second number (the Business Platform number cannot be a personal WhatsApp number), and pre-approved templates for messages outside the 24-hour service window. **Worth starting the paperwork early** — it runs in parallel with everything else.

| | Story | Status |
|---|---|---|
| 8.1 | Nudge me on WhatsApp | 🟡 |
| 8.2 | Actually wake me up | 🟡 |
| 8.3 | Put a courier on a server that can't do anything | ⚪ |
| 8.4 | Let me see my screen from my phone | ⚪ |
| 8.5 | Command it from anywhere | ⚪ |

## Epic 9: The reel ships itself

Content calendar, per-platform generation, shipping reduced to a single approval.
**Covers:** FR-51, FR-52, FR-53, FR-55, FR-56 *(FR-54's warning already ships in Story 1.7)*

| | Story | Status |
|---|---|---|
| 9.1 | Track every piece of content through its lifecycle | ⚪ |
| 9.2 | Show me the calendar and what's missing | ⚪ |
| 9.3 | Draft titles, hooks, descriptions, tags and captions per platform | ⚪ |
| 9.4 | Reduce shipping to one approval | ⚪ |
| 9.5 | Learn what actually performs | ⚪ |

---

# Release 4 — The office floor

## Epic 10: The office floor

The isometric office as the full agent surface. *Story 5.11 already covers the functional need with a list view — this epic is the surface itself.*
**Covers:** FR-88, FR-89

| | Story | Status |
|---|---|---|
| 10.1 | Build the isometric floor | ⚪ |
| 10.2 | Give every role a recognisable person | ⚪ |
| 10.3 | Make assignment visible | ⚪ |
| 10.4 | Make approvals arrive at my desk | ⚪ |
| 10.5 | Light the room | ⚪ |
| 10.6 | Handle a real floor, not a demo | ⚪ |
| 10.7 | Stay cheap enough to leave open all day | ⚪ |

---

## Standing rules for every story

A story is not done unless it also satisfies the architecture invariants it touches. The ones that bite most often:

- **AD-9** — `grep -ri jarvis` returns nothing outside the config default and message templates. CI enforces it.
- **AD-20** — module ≤400 lines (CI fails >500), function ≤50, params ≤5, complexity ≤10, nesting ≤4.
- **AD-24** — confidentiality fails closed. No permissive default anywhere.
- **AD-8** — events, execution log and audit log are append-only *at the storage layer*, not by convention.
- **AD-2** — no ORM or driver type escapes an adapter into `domain/` or `app/`.
- **AD-1** — no LLM call in scoring, pace arithmetic or scheduling. Those are pure functions.

# Brainstorm Intent — JARVIS Requirement #1

**Date:** 2026-08-10
**Source:** `.memlog.md` (same folder)
**Status:** Requirement #1 locked. Next step: PRD.

---

## Product

A personal AI operating system — a JARVIS-style agent for one user (Laxmikant). Long-term roadmap is V1 Foundation → V2 Personal productivity → V3 Local computer agent → V4 Autonomous agent. This document scopes **only the first requirement**.

**The name is user-owned and swappable at any time.** This is a hard rule, not a preference — see *Naming rule* below.

### Naming rule (non-negotiable)

The word **"Jarvis" must never appear in code.** It may appear in **user-facing messages only**, and even there it must be interpolated from configuration — the assistant will be renamed later.

- One config key — `ASSISTANT_NAME`, default `"Jarvis"` — is the single source of truth.
- Code uses **neutral identifiers everywhere**: `agent`, `assistant`, `core`. This covers module names, package names, class names, DB tables and columns, API routes, log channels, and env var prefixes (`AGENT_`, never `JARVIS_`).
- Every user-facing string interpolates the config value: `f"Good morning. {assistant_name} is online."`
- **Acceptance test:** `grep -ri jarvis` across the source tree returns zero hits outside the config default and message templates.

---

## Requirement #1 (locked)

> **An application that reaches out to me on its own, and does work when I ask.**

Four capabilities:

1. **Knows my routine** — stores my fixed daily and weekly schedule as structured data.
2. **Nudges me proactively over WhatsApp** at scheduled times, without me opening anything.
3. **Tracks what is pending from my side** and reminds me about it.
4. **Executes tasks on demand** when I ask it to.

### The two primitives underneath

Everything above reduces to two things, and every future feature is an extension of one of them:

| Primitive | What it does | Later becomes |
|---|---|---|
| **Scheduler + Notifier** | Fires time- and condition-based nudges to a delivery channel | Railzy backlog briefings, reel deadline, client standup prep |
| **Task Executor** | Runs a requested action through a controlled tool registry | Web research, GitHub, file handling, browser automation |

They share **one memory** of the routine and the pending-work list. Build these two well and later capabilities are new *nudge types* and new *tools* — not new systems.

---

## Concrete acceptance examples

Real nudges from the user's actual routine — these are the V1 test cases:

- **06:00 / 06:30** — wake-up. Must actually *ring*, not sit silently in a notification tray.
- **07:30** — leave for gym.
- **09:10** — leave the gym (to stay on schedule for a ~10:00 departure).
- **~20:00 Mon–Fri** — personal client standup call reminder.
- **Pending-work nudge** — "these things are still open from your side," on a sensible cadence.

Reference routine (needed as seed data):

- 06:00–06:30 wake → kids ready for school → 07:30 gym → 09:15–09:30 home → ~10:00 leave for office (~30 min drive) → 19:00–19:30 home → 20:00 client standup (Mon–Fri) → client work + dinner → ~23:30 daily reel upload.
- Office days **Tue–Sat**; in-office **Tue/Wed/Thu**, WFH **Fri/Sat**; Sunday clear.

---

## UI / experience direction

- **Overall look and feel: JARVIS.** Iron-Man-style HUD aesthetic — dark, glowing, holographic, animated. The interface should feel like an operating system for one person, not a SaaS dashboard.
- **The agent section is an office.** Each specialized agent is rendered as an **employee** at a desk; **Jarvis is the boss driving all of them**, visibly dispatching work.

This metaphor is not decoration — it is the **observability requirement made visible**. Each employee surfaces live state: current task, status (idle / working / blocked / awaiting approval), elapsed time, and token/cost. Delegation and approvals become the main screen instead of buried log lines.

**To settle in the PRD:** whether the office is literal (floor plan, desks, avatars, motion) or abstract (status cards / node graph with the office as language only). This materially changes build effort.

## Constraints and non-negotiables

- **Delivery channel — unresolved plumbing.** The WhatsApp Business API sends *messages* only; it cannot place programmatic voice calls. A ringing wake-up therefore needs a real PSTN call (Twilio / Exotel) or an escalating WhatsApp message. **Decide channel per nudge type** — message for soft nudges, actual call for wake-up.
- **Model independence.** All LLM access behind an `LLMProvider` abstraction. No provider lock-in.
- **Controlled tool registry** with per-tool permission and risk levels; risky actions require approval.
- **Audit logging** of plans, tool inputs/outputs, errors, retries, approvals, durations, and token/cost.
- **Product philosophy:** useful, reliable, transparent, controllable, extensible, model-independent, private.
- **Operating principle:** do not build everything at once — define architecture and scope first, then build incrementally.
- **Owner has ~zero spare hours** (a ~17-hour day, 6:00 AM–11:30 PM). Anything requiring him to sit at a dashboard will not get used. Push, don't wait to be pulled.

---

## Build vs. adopt — decided

**Decision: build the engine.** The scheduler/notifier/executor is built in-house on the planned Python/FastAPI stack. No third-party agent runtime as a dependency.

Two projects were evaluated and rejected as dependencies, but are worth studying as reference architectures:

| Project | Verdict |
|---|---|
| [OpenClaw](https://github.com/openclaw/openclaw) — MIT, self-hosted Node gateway; WhatsApp/Telegram/Signal channels, cron, proactive briefings, memory, skills | **Closest match to requirement #1, and free** (MIT, commercial use permitted, no paid tier). Rejected only to retain ownership and stack control. Study its channel and cron design. |
| [isair/jarvis](https://github.com/isair/jarvis) — Python, Ollama/Whisper/Piper, MCP tools | **Does not fit.** Local desktop voice assistant: no messaging channels, no scheduling, no web UI, macOS-primary, needs a local GPU, dual-licensed (commercial use requires author contact). Fatal flaw: pull-based and only runs when the PC is on — cannot push a 6 AM wake-up. Its memory design (topic auto-split, knowledge graph, redaction before storage) is worth borrowing, and it is a candidate reference for V3. |

**Cost note:** building instead of adopting saves no running cost. LLM usage, always-on hosting, WhatsApp channel, and per-call charges apply either way. Adoption would only have saved engineering time.

## MVP deployment architecture — decided

**Local-first. No server in the MVP.**

The agent runs on the user's own machine, **starts automatically when the system starts, and greets him with a welcome message**, then accepts commands over **WhatsApp, Telegram, or a local web UI**. Cloud is deferred and expanded to later.

**Startup mechanism:** on Windows, prefer a **Windows Service** over the Startup folder or a logon task — the scheduler must be able to fire the 6:00 AM nudge even when no user is logged in. The welcome message is emitted on service start.

**Why this works:** receiving commands needs no public IP, no port forwarding, and no router changes — Telegram long-polling and the WhatsApp Web bridge are both *outbound* connections and work behind home NAT. It also eliminates the two highest-ranked data risks below outright: nothing is sent to a hosted model, and there is no internet-facing gateway holding OAuth tokens.

**Accepted trade-off:** scheduled nudges only fire while the PC is running. The **6:00 AM wake-up therefore requires leaving the machine on overnight** — otherwise that single feature slips to phase 2. Everything else in requirement #1 is unaffected.

**Design guardrail (build this in from day one):** put the **notifier behind an interface**, so both the delivery channel (WhatsApp / Telegram / PSTN call) and the host (local / cloud) can be swapped without touching the scheduler or the executor.

**Phase 2 expansion path:** lift *only* the scheduler + notifier onto a small cloud box; the local agent dials **out** to it. No inbound ports, no rewrite — the two primitives are already separate. This is the cloud-component-plus-local-computer-agent split the original brief already described.

## Data risk and required mitigations

These apply to any personal agent, not to any particular framework. The two that matter most are ranked first.

1. **Personal WhatsApp number at risk.** Unofficial bridges authenticate as the user via a WhatsApp Web session — the number can be banned (it is his primary comms), and a server breach lets an attacker message his family and clients as him. → **Use a dedicated number, never the personal one.**
2. **Employer and client confidentiality.** He is a TPM at Gate6 with a separate paying client. Sending that work to a hosted LLM may breach an NDA or employment terms. → **Hard rule: employer/client data never leaves to a hosted model.** Local model or explicit exclusion.
3. **Always-on gateway holds OAuth tokens** (GitHub, Gmail, Calendar) and tool access — a breach means the attacker can *act* as him. → **Not exposed to the public internet** (VPN/Tailscale, no open ports); secrets in a manager, not `.env`.
4. **Prompt injection** via web pages or email the agent reads. → Per-tool permissions plus human approval on risky actions.
5. **Supply chain** — community skills/plugins run with his permissions. → Pin dependencies; vet any third-party skill.
6. **Memory store concentrates his whole life** (routine, family, finances, clients) in one place. → Encrypt at rest; redact sensitive data before storage.

Most of this is already in the product philosophy from the source brief. The change is that it must land **in V1**, not be deferred.

## Explicitly out of scope for #1

Deferred, but the design should not block them: reel/video pipeline automation, Railzy repo and backlog awareness, YouTube content workflow (*Explore The Unmapped*), voice interaction during the commute, local computer agent, autonomous multi-step planning.

---

## Open questions for the PRD

1. Which channel handles which nudge — WhatsApp message, PSTN call, or escalation from one to the other? And which WhatsApp route: unofficial bridge on a dedicated number, or the paid official Business API?
2. How does a nudge get acknowledged, snoozed, or marked done — reply in WhatsApp, or a separate surface?
3. Where does "pending from my side" come from initially — manual entry, or synced from an existing source?
4. Which tools ship in the first executor registry?
5. Hosting for the always-on scheduler (existing AWS EC2 vs. new).

---

## Deferred capability backlog (from the session, ranked by felt impact)

| Candidate | Impact | Effort |
|---|---|---|
| Voice briefing during commute (~3 hrs/wk currently unusable) | High | High |
| Daily reel pipeline — 7 uploads/wk vs. 3 days of source footage | High | High |
| Railzy backlog awareness and priority summaries | Med | Med |
| GitHub integration | Med | Low |
| Task management surface | Med | Low |

**Structural finding worth carrying forward:** Railzy — the product intended to sit under the Naxova parent company — currently has **no protected time slot** in the week. Every other commitment does. Any future scheduling capability should treat that as the problem to solve.

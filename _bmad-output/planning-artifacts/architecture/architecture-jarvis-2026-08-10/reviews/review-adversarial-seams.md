# Review — adversarial seam attack

**Lens:** construct two units one level down that each obey **every** AD to the letter and still build incompatibly. Every such pair is a hole.
**Target:** `ARCHITECTURE-SPINE.md` (AD-1 … AD-21)
**Date:** 2026-08-10
**Verdict:** FAIL — five compliant-but-divergent pairs found. Four are closed by new ADs; one is a whole missing dimension.

---

## 🔴 CRITICAL — S-1: Derived fields have no declared owner

**The pair.** The Priority Engine and the Planner are both built strictly to AD-1 (deterministic core) and AD-2 (persistence is a port).

- *Planner* treats `priority_score` as **derived**: recomputes it on every read, never persists it.
- *Scoring service* treats it as **stored**: computes once and writes it, reading it back later.

Both obey every AD. Together they produce a system where the plan ranks tasks by a freshly-computed score while the dashboard shows a stale stored one — and neither is wrong by the spine.

**Same hole applies to:** `goal.current_value` (rollup), trajectory, required pace, and calibration factors.

**Fix:** new **AD-22** — every derived value has exactly one writer, is persisted with the inputs' version stamp, and is never recomputed opportunistically by a reader.

## 🔴 CRITICAL — S-2: Confidentiality has no declared default

**The pair.** AD-10 forbids classified context reaching a hosted model, and AD-14 requires every record to carry a classification. Neither says what a record classified by *nobody* is.

- *Memory writer A* defaults an unclassified record to `personal` — permitted to a hosted model.
- *Memory writer B* defaults to `client-confidential` — local model only.

Both obey the ADs. Writer A silently leaks client work to a hosted provider the first time someone forgets to set the field.

**This is the security hole in the set** — it fails open, and it fails silently.

**Fix:** new **AD-24** — classification is mandatory at write, storage rejects null, and any record whose provenance cannot be established is treated as the **most restrictive** class. Default deny, never default allow.

## 🟠 HIGH — S-3: Notifications have no idempotency contract

**The pair.** AD-18 gives idempotency keys to *actions*. Notifications are not actions.

- *Scheduler* fires the 20:00 client-standup nudge.
- *Proactive-signal generator* independently notices the same standup approaching and raises its own.

Both obey AD-11 (scheduler emits requests, notifier delivers) and AD-6. The user gets two nudges for one event — precisely the notification fatigue NFR-8 and P-6 exist to prevent, arriving through fully compliant code.

**Fix:** new **AD-23** — every notification carries a deterministic dedupe key derived from (trigger identity, target occurrence). The notifier collapses duplicates within a window; the budget counts occurrences, not emissions.

## 🟠 HIGH — S-4: The relay envelope has no version contract

**The pair.** The local agent and the relay are **separately deployed** — that is the whole point of AD-4 and AD-5. Version skew is therefore guaranteed, not hypothetical.

- *Local agent v2* adds a field to the envelope and starts sending it.
- *Relay v1* is still running and rejects or silently drops the unknown shape.

Both obey the envelope convention as written (`{id, kind, created_at, nonce, ciphertext}`), because it fixes the fields but not their evolution.

**Fix:** new **AD-25** — the envelope carries an explicit version; the relay treats the payload as opaque and must forward unknown versions untouched; outer-field additions are additive-only and never required for routing.

## 🟠 HIGH — S-5: The operational envelope is silent

Not a pair — a whole dimension the good-spine checklist names explicitly, and this spine skipped.

The spine covers deployment *topology* (local + relay) but says nothing about:

- **Environments** — is there a dev configuration separate from the live one, and how does a developer run against throwaway data without touching real memory?
- **Upgrade path** — how a running service takes a new version, including schema migration on a machine that must nudge at 06:00 the next morning.
- **Relay deployment and update** — how the VPS component is shipped and rolled back.
- **Self-monitoring** — the system watches the user's goals but nothing watches the system. Silent death is the realistic failure mode for an always-on local service, and NFR-20 only covers *missed triggers reported on next start*, which assumes it starts again.
- **Backup and restore** — Deferred mentions a daily local copy, but restore is untested and unspecified.

**Fix:** new **Operational Envelope** section, plus **AD-26** (self-monitoring heartbeat) since silent failure defeats the product's entire purpose.

---

## Attacks that failed (the spine held)

- **Two persistence adapters diverging on entity shape** — AD-3 plus the contract-test convention closes it: an adapter is compliant only if it passes the same suite.
- **A worker role escalating its own permission** — AD-7 forbids it explicitly, including via role-switching.
- **An LLM producing a reported number** — AD-1 is unambiguous.
- **The relay being trusted** — AD-4 is unusually well-drawn; the "must be capable of nothing beyond denial of service" phrasing leaves no room.
- **A rename leaking into code** — AD-9 is enforced in CI, not by convention.
- **Money precision drift** — the convention fixes integer minor units plus currency code.

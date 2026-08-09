# Review — good-spine rubric walker

**Target:** `ARCHITECTURE-SPINE.md`
**Date:** 2026-08-10
**Verdict:** STRONG, with one dimension missing — closed by the Operational Envelope section and AD-22 … AD-26.

---

| Rubric criterion | Judgement |
|---|---|
| **Fixes the real divergence points for the level below** | Mostly. Five compliant-but-divergent pairs were found by the adversarial lens (see `review-adversarial-seams.md`). Now closed. |
| **Every Rule is enforceable and prevents its stated divergence** | Strong. AD-9 is enforced in CI, AD-8 at the storage layer, AD-12 by a deletion test, AD-20 by lint limits. These are checks, not aspirations — which is the difference between a rule and a wish. |
| **Nothing under Deferred lets two units diverge** | Pass. Each deferred item is adapter-local behind an existing port (WhatsApp transport, wake-up mechanism, voice engines, vector store) or explicitly bounded by AD-3 (Mongo). Priority weights are configuration, not structure. |
| **Named tech is verified-current** | One critical miss — NSSM. See `review-version-verification.md` V-1. Everything load-bearing else was checked against live sources. |
| **Ratifies rather than contradicts a brownfield codebase** | N/A — greenfield. No code exists beyond BMad scaffolding. |
| **Covers the driving spec's capabilities** | Pass. The Capability → Architecture Map traces FR-1…FR-104 and CFR-1…CFR-57 groups to modules and governing ADs. Spot-checked: revenue/expense (FR-80–104) → `domain/goal/` + money convention; permissions (FR-38–41) → `domain/permission/` + AD-4/AD-7. |
| **No new AD weakens an inherited one** | N/A — no parent spine. |
| **Every dimension the altitude owns is decided, deferred, or open** | **FAIL as drafted.** The operational and environmental envelope was silent: environments, upgrade path, relay deployment, self-monitoring, restore. This is exactly the dimension the checklist warns a domain-focused draft skips. Now closed. |

## Notes on quality

**What is unusually strong.** AD-4's phrasing — *"a fully compromised relay must be capable of nothing beyond denial of service"* — is a testable security property rather than an intention, and it makes the whole local/relay split safe to reason about. AD-1's separation of deterministic arithmetic from probabilistic advice is the decision that makes the system testable at all, and it is stated crisply enough that a violation would be obvious in review.

**What was thin and is now fixed.** The spine was written from the *domain* outward and stopped at the domain's edge. Everything about running the thing for months — upgrades, environments, watching it stay alive — was absent. For an always-on personal service whose value depends entirely on it firing at 06:00 unattended, that was the most consequential gap in the document.

**Altitude check.** Initiative altitude is correct: the spine fixes what features must share and defers what individual features own. It resists the common failure of over-specifying — the data model is entity names and relationships, not columns, and the source tree is scaffold rather than a mirror to maintain.

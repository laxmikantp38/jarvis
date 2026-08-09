# Goal Model — proposed decomposition of the ₹1 crore target

**Date:** 2026-08-10 · **Status:** proposal, needs your decision
**Window:** 2026-08-10 → 2027-02-10 (182 days) · **Target:** ≈ ₹1,00,00,000 gross earnings, all streams

This is the seed configuration for the Goal engine (PRD FR-6, FR-11). It is *data*, not a feature — see `../../architecture/core-intelligence-loop.md` §3.2.

---

## 1. First, the arithmetic you asked me to skip past

You answered "connect Google AdSense" for Railzy. Combined with reels on YouTube/Instagram/Facebook, that puts **the entire ₹1 crore plan on advertising revenue**. So here is what advertising would actually have to deliver.

**Required: ≈ ₹16.7 lakh per month for six straight months.**

### Railzy via AdSense

Indian web traffic earns roughly **₹40–₹150 per 1,000 pageviews** on display ads. Travel/rail is a decent advertiser category, so take an optimistic **₹150 RPM**.

| RPM | Pageviews/month needed | Per day |
|---|---|---|
| ₹150 (optimistic) | **11.1 million** | ~371,000/day |
| ₹80 (realistic) | **20.9 million** | ~696,000/day |

That is established-major-Indian-train-site scale — confirmtkt / erail territory. Not impossible as a destination, but **SEO takes 6–12 months to mature**, which is the entire window. Railzy realistically contributes *late*, and modestly.

### Content via AdSense

Short-form is the weak spot. **Reels and Shorts earn roughly ₹5–₹40 per 1,000 views** in India.

| RPM | Views/month needed |
|---|---|
| ₹40 (very optimistic) | **41.8 million** |
| ₹20 (realistic) | **83.5 million** |

**Nearly 84 million views a month, every month.** Your channel is not near this, and no daily-reel cadence closes that gap in six months.

### The conclusion

> **Ads alone cannot reach ₹1 crore in six months.** Not from Railzy, not from content, not from both combined. The gap is roughly an order of magnitude, not a matter of working harder.

This is not an argument against the target. It is an argument that **the target needs a different vehicle** — and it is exactly the finding FR-9 / CFR-9 exist to surface. Better now, at zero cost, than in month five.

**What ads are actually good for:** compounding, low-maintenance income that keeps paying after the work stops. Railzy AdSense is worth connecting — just not as the thing that carries ₹1 crore.

---

## 2. What could plausibly carry it

Ranked by ₹ per hour of your time, given what you already have.

| Vehicle | Why it ranks here | 6-month ceiling |
|---|---|---|
| **Services / consulting** — senior engineering + TPM, sold at market rate | You already do this for one client, so it is proven, not speculative. Highest certainty, fastest cash, no audience needed. Scales by adding people. | **High** — the only vehicle that can realistically carry the majority |
| **Brand deals / sponsorships** | Pays 10–100× AdSense for the same audience. A travel creator with an engaged following charges ₹20k–₹1L per integration. Needs audience, but far less audience than ads need. | **Medium** |
| **Railzy as a paid product** — subscription, booking commission, B2B/API rather than ads only | Monetises the users you have instead of needing millions you don't | **Medium**, back-loaded |
| **Railzy AdSense** | Compounding, passive, but slow and traffic-hungry | **Low** in this window |
| **Content AdSense** | Effectively noise at this scale | **Very low** |
| **Naxova** | An enabler — legal entity, invoicing, brand. **Not a revenue source in six months.** | **Zero** — by design |

---

## 3. Proposed goal tree

**Two splits are given.** The engine can hold either; you pick.

### Split A — "Ads-led" (what your current plan implies)

Recorded so the system can track it and tell you honestly how it is going.

| Goal | Target | Share | Assessment |
|---|---|---|---|
| Salary (Gate6) | *baseline — unknown* | — | Fixed, certain |
| Freelance (current client) | *baseline — unknown* | — | Fixed, certain |
| Railzy AdSense | ₹35,00,000 | 35% | Needs ~11–21M pageviews/mo. **Very unlikely** |
| Content AdSense | ₹25,00,000 | 25% | Needs ~42–84M views/mo. **Not achievable** |
| Brand deals | ₹15,00,000 | 15% | Possible with audience growth |
| Naxova | ₹0 | 0% | Enabler only |

> **The engine's verdict on Split A, on day one:** `unreachable_under_current_assumptions`. Required acceleration on both ad goals exceeds any observed rate by more than an order of magnitude.

### Split B — "Services-led" ✅ recommended

| Goal | Target | Share | Why |
|---|---|---|---|
| **Salary (Gate6)** | *baseline — unknown* | — | Certain. Continues regardless. |
| **Services / consulting** — expand beyond the one client | **₹55,00,000** | **55%** | Highest certainty per hour. Uses skills you already sell. Scales by adding contractors under Naxova. |
| **Railzy — paid product** (subscription / commission / B2B) | ₹20,00,000 | 20% | Monetises existing users rather than needing millions of new ones |
| **Brand deals / sponsorships** | ₹15,00,000 | 15% | 10–100× AdSense per unit of audience |
| **Railzy AdSense** | ₹7,00,000 | 7% | Worth connecting. Compounds. Not load-bearing. |
| **Content AdSense** | ₹3,00,000 | 3% | Realistic rather than aspirational |
| **Naxova** | ₹0 | 0% | Enabler: entity, invoicing, contracts — the thing that lets services scale |

**Split B is still ambitious.** ₹55 lakh of services in six months means roughly ₹9 lakh/month of billed work — more than you can personally deliver alongside a full-time job. It implies **hiring or subcontracting**, which is precisely what forming Naxova is for. That is the honest shape of a ₹1 crore plan.

**Naxova stops being a side item under Split B.** It becomes the critical path: without an entity you cannot contract, invoice, or subcontract at that scale. It should get the protected time Railzy currently lacks.

---

## 4. What each goal needs to be trackable

The engine cannot compute pace, trajectory or gap without a KPI per goal.

| Goal | KPI | Source | Refresh |
|---|---|---|---|
| Salary | Monthly credit | Manual | Monthly |
| Services | Signed contract value; invoiced; collected | Manual | Weekly |
| Railzy paid | Paying users × ARPU | Railzy DB | Weekly |
| Railzy AdSense | Pageviews; RPM; earnings | AdSense (manual at MVP) | Weekly |
| Brand deals | Deals signed; value | Manual | Weekly |
| Content AdSense | Views; RPM; earnings | YouTube Studio / Meta (manual at MVP) | Weekly |
| Naxova | Formation milestones (binary) | Manual | Weekly |

Naxova is a **milestone-type** goal, not monetary — which is exactly why the engine must support arbitrary goal types (CFR-4).

---

## 5. Still blocking

Baselines are still unanswered. Without them the engine cannot compute a single trajectory:

1. **Salary** — monthly take-home from Gate6
2. **Freelance** — monthly income from the current client
3. **Railzy today** — monthly pageviews and users (AdSense revenue is ₹0 until connected)
4. **Channel today** — subscribers/followers per platform, monthly views, current earnings

These four numbers turn the whole document from a proposal into a live tracker.

---

## 6. Decision needed

1. **Split A or Split B?** (Or your own numbers — the engine holds whatever you choose.)
2. If B: **does Naxova formation become the first protected block**, ahead of Railzy?
3. Give me the four baselines in §5.

*Configuration, not code. Any of this can change without touching the system.*

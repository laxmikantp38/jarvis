# Review — version and reality verification

**Lens:** was every committed technology decision web-researched or reality-checked, rather than asserted from training data?
**Target:** `ARCHITECTURE-SPINE.md`
**Date:** 2026-08-10
**Verdict:** PASS WITH FIXES — the load-bearing choices were verified; two rows were asserted and one is materially wrong.

---

## Verified against live sources ✅

| Claim | Status |
|---|---|
| APScheduler 4.0 still in development, stores redesigned incompatibly; 3.11.x is the production line | ✅ Verified |
| python-telegram-bot 22.8, released 2026-06-12, requires Python ≥3.10, long-polling supported | ✅ Verified |
| Only one active polling connection permitted per bot token (drives AD-17) | ✅ Verified |
| `sqlite-vec` still pre-beta, documented as not ready for general use | ✅ Verified — correctly deferred, not bound |
| WhatsApp Business Calling API GA since late 2025; business-initiated calls to opted-in users possible | ✅ Verified — corrected an earlier wrong statement |
| WhatsApp on-premise deprecated Oct 2025; Cloud API via BSP is the only route | ✅ Verified |
| Business Platform number cannot be an existing personal WhatsApp number | ✅ Verified |
| Template requirement outside the 24-hour service window | ✅ Verified — drives the channel role split |
| India messaging pricing ≈ ₹0.115–0.13 utility + 18% GST | ✅ Verified |
| VPS: Vultr Mumbai from $2.50/mo, DO Bangalore $4, Linode Mumbai $5, all sub-35ms in India | ✅ Verified |
| Hetzner 180–220ms from India, unsuitable | ✅ Verified |
| 2026 Python standard: `src/` layout, `pyproject.toml`, Ruff for lint **and** format, mypy, pytest | ✅ Verified |
| `uv` has largely replaced pip/venv/poetry but is not installed on this machine | ✅ Verified — hence the stdlib fallback |

## Findings

### 🔴 CRITICAL — V-1: NSSM is effectively abandoned

The Stack pins **NSSM 2.24+** to run the service. This was asserted from training data, not checked.

**Reality:** NSSM has had no stable release in **over a decade**. WinSW, the closest direct replacement, is itself described as being in maintenance limbo. Servy is a newer entrant but young and unproven.

**Impact:** M0 depends on this. Binding an abandoned tool to the one component that must survive every reboot is a poor trade, and it adds a third-party dependency to a system whose NFR-13 asks for single-developer maintainability.

**Fix applied:** switch to **Windows Task Scheduler** with an at-startup trigger and *run whether the user is logged on or not*. It is built into Windows, has no third-party dependency, survives reboots without a login, and supports restart-on-failure. WinSW is recorded as the fallback if true service-control semantics are later required.

### 🟠 HIGH — V-2: Several Stack rows are unpinned

FastAPI, Uvicorn, Alembic, pydantic-settings, keyring, Ruff, mypy and pytest all read "latest stable" — a placeholder, not a verified version. The lint passes because the field is populated, but the intent of a pinned Stack is not met.

**Fix applied:** these rows are now explicitly marked **unpinned at authoring; pin at first install from the resolved lockfile**. That is honest about what was and was not verified, and puts the pin where it belongs — in `pyproject.toml`, which the code owns once it exists (Stack is seed, not contract).

### 🟡 MEDIUM — V-3: PostgreSQL 16+ was asserted

Not checked against current releases. Low risk — the major version only needs to support what SQLAlchemy 2.x emits, and any currently-supported Postgres does. Recorded as an assumption to confirm at the phase-2 lift rather than a fix.

## Not findings

- **Python 3.12+** — safe floor; python-telegram-bot's ≥3.10 requirement is satisfied.
- **SQLite bundled with Python** — correct.
- **Ruff replacing black/isort/flake8/pyupgrade** — verified as the 2026 default.

# Phase 5 — smoke & acceptance checklist

**Purpose:** One runnable checklist to validate **Mini App MVP + private bot launcher** after deploy (local or Railway).  
**Acceptance:** Phase 5 closure is documented in **`docs/PHASE_5_ACCEPTANCE_SUMMARY.md`**.  
**Detail:** Per-feature notes live in `docs/PHASE_5_STEP_*_NOTES.md` (8–19); this file stays short.

---

## Preconditions

- API + bot + Mini App UI point at the same environment; `TELEGRAM_MINI_APP_URL` set for URL buttons.
- Mini App API calls use the configured dev user (`MINI_APP_DEV_TELEGRAM_USER_ID`) until init-data auth ships.
- For staging tour **`TEST_BELGRADE_001`**, if smoke fails with sold-out or stale dates, run from repo root (with `DATABASE_URL`):

```powershell
python scripts/reset_test_belgrade_tour_state.py
```

Stdout should report **`SMOKE_READY=YES`** when possible. See `docs/PHASE_5_STEP_8C_NOTES.md`.

---

## Phase 5 smoke (ordered)

1. **Bot:** `/start` — welcome; **Open Mini App** / **My bookings** visible; optional filters below.
2. **Bot:** Open Mini App — catalog loads (HTTPS).
3. **Mini App:** Catalog scrolls; open **tour detail** → **preparation** → create hold → **payment** screen.
4. **Mock pay (staging):** With `ENABLE_MOCK_PAYMENT_COMPLETION=true` on API, complete pay from Mini App → success → **My bookings** shows confirmed (see `docs/PHASE_5_STEP_10_NOTES.md`).
5. **My bookings:** Sections **Confirmed** / **Active holds** / **History**; History capped (Step 19) with note if truncated.
6. **Waitlist (sold-out open tour):** Detail shows join / status / in_review copy per Step 18.
7. **Help / support:** Help screen; **Log support request** where implemented — handoff row in DB (Step 13).
8. **Bot:** `/bookings`, `/help`, `/contact` — text + Mini App URL buttons; `/language` works.
9. **Webhook:** Bot responds with webhook (no long polling in prod).

**Lazy expiry:** Opening catalog/prepare/bookings runs expiry logic (Step 9) — expired holds release seats without relying only on reset script.

**Ops (optional):** With `OPS_QUEUE_TOKEN`, `GET /internal/ops/handoffs/open` and `.../waitlist/active` list actionable rows only; claim/close via PATCH (Steps 15–17). Not required for end-user smoke.

---

## Out of scope for this checklist

- Admin panel, group bot, real PSP, full init-data auth, automated retention jobs — later phases.

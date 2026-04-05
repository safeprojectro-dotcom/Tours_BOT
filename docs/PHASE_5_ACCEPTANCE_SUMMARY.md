# Phase 5 (Mini App MVP) — acceptance summary

**Status:** MVP **accepted** (Phase 5 / Step 20 consolidation, 2026).  
This document maps execution work (project Steps 4–19 and related checkpoints) to `docs/IMPLEMENTATION_PLAN.md` Phase 5 and records intentional limits.

---

## 1. Mapping to IMPLEMENTATION_PLAN Phase 5

| Plan item (abridged) | Project delivery |
|----------------------|------------------|
| Mini App UX definition | `docs/MINI_APP_UX.md` + iterative Mini App work |
| Catalog, filters, cards, detail | Mini App catalog/detail/preparation flows |
| Reserve seats, timer, payment scenario | Reuses Phase 2–4 services; temporary reservation + payment entry + mock completion path |
| My bookings + status | Grouped list (Confirmed / Active / History), detail, payment UX, Step 19 history cap |
| Help / handoff entry | Support request + handoff rows; honest copy (no live operator promise) |
| Waitlist (interest) | Join + status API + ops lifecycle + user visibility polish |
| Language / settings / help | Settings + help endpoints and Mini App screens |
| Reuse service layer | Business rules stay in backend services |
| **Plan line:** “Implement Mini App authentication/init flow with Telegram context” | **Deferred:** dev `MINI_APP_DEV_TELEGRAM_USER_ID` / query param; production init-data validation is a **follow-up**, not a blocker for this MVP acceptance |
| **Plan line:** gallery, rich media | **Not required for MVP acceptance**; detail uses text/boarding as implemented |
| **Plan line:** waitlist on My bookings as separate list | **Deferred:** waitlist is tour-detail + API; not merged into bookings list (acceptable MVP) |

---

## 2. Done-When criteria (IMPLEMENTATION_PLAN) — assessment

| Criterion | Met? | Notes |
|-----------|--------|--------|
| UX defined (structure, CTA, loading/empty/error, timer, help entry) | **Yes** | See `MINI_APP_UX.md` + step notes |
| User can open Mini App and browse tours | **Yes** | |
| View tour, reserve, start payment, view booking status | **Yes** | Mock payment path for staging (`ENABLE_MOCK_PAYMENT_COMPLETION`) |
| Multilingual + fallback | **Yes** | Shell i18n + API fallback |
| Help paths without business logic in frontend | **Yes** | Flet calls API only |

**Suggested tests in plan** (auth/init integration tests, staging auth context): partially met — catalog/booking/payment tests exist; full **production** Telegram Web App auth is **out of scope** for this MVP acceptance.

---

## 3. What works end-to-end (staging-realistic)

- Private bot: launch Mini App, filters, bookings/help/contact shortcuts; selective message cleanup (Step 12A/12B).
- Mini App: catalog → detail → preparation → hold → payment entry → mock pay (when enabled) → success → My bookings with sections + history cap.
- Lazy expiry; configurable TTL for holds (staging).
- Waitlist: sold-out open tour → join → status including `in_review` after ops claim.
- Support signals: handoff + waitlist rows; internal ops JSON + claim/close for handoff and waitlist (`OPS_QUEUE_TOKEN`).
- Ops queues remain **actionable-only** (open handoffs, active waitlist).

---

## 4. Intentionally limited / staging-only

- **Mock payment completion** flag — not a real PSP.
- **Mini App user identity** — dev telegram user id until init-data auth.
- **Internal ops API** — shared secret, not a full admin product.
- **History** — UI shows last 15 history items; full data still in API/DB.

---

## 5. Non-blocking debt (see also `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`)

- Real payment provider + production webhook hardening.
- Telegram **Web App init-data** validation for Mini App API.
- Waitlist: no auto-promotion, no customer notifications.
- Handoff: no operator inbox UI, no customer notifications.
- `MemoryStorage` for bot FSM.
- Full i18n for all shell languages (fallback to English).
- Reservation/booking status semantics for analytics/admin (existing open questions).

None of the above blocks calling **Phase 5 Mini App MVP** done for the agreed scope.

---

## 6. Explicitly not Phase 5 (next phases)

- **Phase 6:** Admin panel, tour/order CRUD, role-based admin API.
- **Phase 7+:** Group assistant, full handoff lifecycle, notifications at scale.
- **Real PSP**, refunds, advanced payment states.
- **Retention jobs** / automated DB cleanup.

---

## 7. Reference: execution checkpoints (project Steps)

Steps are documented in `docs/CHAT_HANDOFF.md` and individual `docs/PHASE_5_STEP_*_NOTES.md` files (4–19). Step 20 is consolidation only (this acceptance pack).

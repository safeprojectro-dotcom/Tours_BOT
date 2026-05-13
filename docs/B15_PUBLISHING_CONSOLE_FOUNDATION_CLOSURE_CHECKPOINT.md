# B15 — Admin Publishing Console foundation closure checkpoint

**Status:** Closed (docs checkpoint).  
**Scope:** **B15B–B15F** — safe, **read-only** admin publishing console **foundation**; execution-heavy product (auto-publish, console-side mutations, template/channel editors) stays **approval-gated**.  
**Handoff:** [`docs/HANDOFF_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md`](HANDOFF_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md).  
**Prompt archive:** [`docs/CURSOR_PROMPT_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT.md`](CURSOR_PROMPT_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT.md).

**Related:** **B15A** umbrella design [`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`](B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md); **B15C** exact CTA gate [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md); **B15C6** chain checkpoint [`docs/B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md`](B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md).

---

## 1. Scope

The **safe publishing console foundation** delivered across **B15B–B15F** is **closed** for its intended slice:

- **B15B** — read-only candidate queue API.
- **B15C** — exact-tour **Rezervă** / conversion safety chain (product + gates; not the console HTTP route itself).
- **B15D** — richer readiness, blockers, CTA safety, admin/preview paths on the console read model.
- **B15E** — read-only **`actions[]`** affordance metadata (no execution from the console route).
- **B15F** — source / template / channel / media metadata plus future-disabled capability hints.

**B15C** remains documented as the **accepted operator conversion order** and production-smoke baseline; see §3–§4.

---

## 2. What is now available (`GET /admin/publishing-console`)

Single **read-only** endpoint (B15B) extended additively:

| Capability | Slice | Notes |
|------------|-------|--------|
| Candidate cards (supplier offers, tour promotion) | B15B | `limit` / `kind`; no mutations. |
| Readiness / blocker summaries | B15D | e.g. `readiness_summary`, `readiness_level`, `primary_blocker`, `blocker_codes`. |
| Exact CTA safety visibility | B15D | e.g. `cta_safety_status`, conversion target fields, B15C-aligned hints. |
| Next action hints | B15D | e.g. `next_action_code`, `next_action_label`, `admin_action_path`, `preview_path`, `audit_hint`. |
| Read-only action affordances | B15E | per-item `actions[]` — metadata only; mirrors `operator_workflow` / console / future. |
| Source / template / channel / media metadata | B15F | e.g. `source_*`, `template_*`, `channel_*`, `media_policy_status`, `media_summary`. |
| Future-disabled capability hints | B15F | `template_actions[]`, `channel_actions[]` (`implemented: false`). |

Canonical field lists: [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md), [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md), [`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md).

---

## 3. Correct supplier-offer publish / conversion order (B15C accepted chain)

1. Packaging / moderation **approved** for the path that allows bridge and showcase work.
2. **Tour bridge** created or linked (offer → `Tour` instance).
3. **Tour activated** for Mini App catalog (`open_for_sale` where applicable).
4. **Active execution link** created (booking link before channel publish when gates require it).
5. **Showcase / channel publish** allowed when workflow + B15C gates pass.
6. Channel **Rezervă** opens **exact Mini App tour** (e.g. short-name `startapp` link to `/tours/{tour_code}`).
7. **Layer A** handles reservation / payment after the customer lands on the tour.

Operators should treat **`GET …/review-package`** as the source of truth for what is blocking, not button order alone.

---

## 4. Production evidence (B15C / B15C5)

Recorded operator smoke — Offer **#15**, Tour **#9**, tour code **`B10-SO15-460344`**, execution link **#8**, publish attempt **#6**, showcase message **#28**, CTA  
`https://t.me/tours_tm_bot/banattours?startapp=tour_B10-SO15-460344`, temp hold/order **#55**, no identity warning, payment screen reached.  
Detail: [`docs/B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md`](B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md); additional B15C notes: [`docs/B15C_PRODUCTION_SMOKE_RESULT.md`](B15C_PRODUCTION_SMOKE_RESULT.md).

---

## 5. Safety boundaries preserved (B15B–B15F)

The console **foundation** does **not** introduce:

- **Auto-publish** or **scheduler** from `GET /admin/publishing-console`.
- **Action execution** endpoint on the console read path (B15E is metadata only).
- **Template editor** or **channel selector** (B15F hints only; `implemented: false`).
- **Telegram send / retry** triggered by the console read route.
- **Layer A** changes, **Mini App routing** changes, or **migrations** for these slices.
- **Supplier-side publish** (supplier marketplace remains out of scope for this checkpoint).
- **Fake urgency / availability** copy as a product requirement for the console (console remains observational).

Dangerous automation and execution UX remain **explicitly future-gated** (§7).

---

## 6. Tests and evidence pointers

- **Unit:** `tests/unit/test_admin_publishing_console.py` — **8 passed** (covers B15D / B15E / B15F additive read model on the same endpoint).
- **Production / operator smoke:** **B15C** docs (§4 and linked runbooks), not replaced by console unit tests.

---

## 7. Future gated options

**Only** after explicit product / security / design approval:

| Option | Intent |
|--------|--------|
| **B15F2** | Template editor — design / read model. |
| **B15F3** | Channel selector — design / read model. |
| **B15E2** | Explicit **action execution** from console or sibling flows (not metadata only). |
| **B15G** | Guarded **auto-publish** (and related send automation). |
| **B16** / **Admin OPS visibility** | If roadmap priority shifts to broader ops surfaces outside this foundation. |

**Related (design record — not implemented by B15B–F):** **[`docs/B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md)** — guarded **`prepare_conversion_chain`** (internal bridge / catalog / execution link **without** Telegram); **B15** read-only foundation unchanged until **B16D2** / **B15E2**.

---

## 8. Recommended next step

1. **Pause B15** and return to the **broader business plan** / next product block **until** a slice above is chartered, **or**
2. Open **B15F2**, **B15F3**, or **B15E2** as a **design-only** next slice with an explicit gate (no execution assumptions).

---

## 9. Slice index (implementation record)

| Slice | Doc |
|-------|-----|
| B15B | [`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md) |
| B15C | [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md) |
| B15D | [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md) |
| B15E | [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md) |
| B15F | [`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md) |

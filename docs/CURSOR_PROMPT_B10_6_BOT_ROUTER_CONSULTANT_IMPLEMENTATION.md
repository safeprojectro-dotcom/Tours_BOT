# CURSOR_PROMPT_B10_6_BOT_ROUTER_CONSULTANT_IMPLEMENTATION

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is the first small B10.6 implementation slice.

---

## Current checkpoint

B10.6 design accepted.

Recent completed work:

### B11
- `/start supoffer_<id>` resolves active `supplier_offer_execution_link`.
- If linked Tour is `OPEN_FOR_SALE` and customer-visible:
  - bot provides exact Mini App CTA to `/tours/{tour_code}`;
  - generic catalog overview is skipped.
- Fallback remains safe.
- Commit:
  - b29d7e4 — feat: route supplier offer deep links to exact tours
  - 72af8bc — docs: add B11 exact tour CTA handoff

### B7
- B7.3A policy accepted.
- B7.3B metadata-only `publish_safe` stub implemented.
- No real download/storage/render/publish.

### B8
- B8 recurring supplier offers line closed.

---

## Business goal

Telegram Bot should become router / consultant / entry point, not a duplicate Mini App catalog.

Mini App remains execution truth and conversion.

This first B10.6 slice should align `/start tour_<code>` with the new B11 pattern:

- when user enters by exact Tour code, bot should provide a primary WebApp CTA to exact Mini App Tour detail:
  `{TELEGRAM_MINI_APP_URL}/tours/{tour_code}`
- keep existing policy-gated prepare/assistance behavior unless it conflicts
- do not remove generic `/start` or `/tours` catalog overview in this slice
- do not rewrite all bot flows

---

## Scope of this implementation

Implement only:

### `/start tour_<code>` router alignment

Current behavior:
- `/start tour_<code>` loads tour detail;
- sends in-chat tour detail;
- keyboard Mini App URL points to catalog root only;
- prepare/assistance callbacks remain.

Target behavior:
- `/start tour_<code>` still works;
- for eligible tour detail, primary WebApp button should point to exact Mini App Tour URL:
  `{TELEGRAM_MINI_APP_URL.rstrip("/")}/tours/{tour_code}`;
- keep existing prepare/assistance buttons according to current policy;
- do not introduce misleading full_bus/per-seat wording;
- do not change booking/payment logic.

This is not the step to remove `_send_catalog_overview` from generic `/start` or `/tours`.

---

## Architecture rules

- Telegram Bot = router / consultant / entry point.
- Mini App = execution truth and conversion.
- Layer A = booking/payment authority.
- visibility != bookability.
- Business rules stay in service layer.
- Repositories stay persistence-oriented.
- Bot must not invent price/seats/status.
- Full_bus fixed package must not be described as individual-seat selection.

---

## Files to inspect/change

Inspect:

- app/bot/handlers/private_entry.py
- app/bot/keyboards.py
- app/bot/messages.py
- app/bot/services.py
- app/services/supplier_offer_deep_link.py
- app/services/customer_catalog_visibility.py
- tests around `/start tour_<code>` / private foundation

Likely change:

- app/bot/keyboards.py
- maybe app/bot/handlers/private_entry.py
- maybe app/bot/messages.py
- tests/unit/* relevant test file
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md if B10.6/B11 status is tracked there

---

## Required behavior

### 1. Exact Mini App Tour CTA

When `/start tour_<code>` successfully resolves a customer-visible Tour detail, the keyboard should include a primary WebApp button to:

```python
f"{settings.telegram_mini_app_url.rstrip('/')}/tours/{tour.code}"
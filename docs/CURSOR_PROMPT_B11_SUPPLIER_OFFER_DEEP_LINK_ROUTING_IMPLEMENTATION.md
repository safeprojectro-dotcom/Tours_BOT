# CURSOR_PROMPT_B11_SUPPLIER_OFFER_DEEP_LINK_ROUTING_IMPLEMENTATION

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Используй самый сильный доступный reasoning model.

Cursor mode: Agent.

Это небольшой implementation step для B11.

---

## Before coding

Сначала кратко проверь текущие файлы/сервисы и только потом меняй код.

Не начинай широкую переработку bot architecture.

---

## Current checkpoint

B11 design contract accepted.

Current known behavior:

- `/start supoffer_<id>` currently:
  - parses SupplierOffer id;
  - loads SupplierOffer;
  - requires lifecycle_status == PUBLISHED;
  - sends supplier offer intro;
  - sends generic private home keyboard / Mini App root;
  - then sends generic catalog overview;
  - does NOT resolve active SupplierOfferExecutionLink;
  - does NOT route to exact Mini App Tour detail.

Accepted B11 target:

- `/start supoffer_<id>` should act as a router to the best safe conversion target.
- If active supplier_offer_execution_link exists and linked Tour is OPEN_FOR_SALE + customer-visible/actionable:
  - show short safe text;
  - add primary WebApp button to exact Mini App Tour detail:
    `{TELEGRAM_MINI_APP_URL.rstrip("/")}/tours/{tour_code}`
- If no active execution link:
  - fallback to supplier offer landing or generic catalog/help.
- If linked Tour exists but is not bookable/visible:
  - do not provide misleading booking CTA;
  - fallback safely.
- Do not create Tour.
- Do not activate Tour.
- Do not create SupplierOfferTourBridge.
- Do not touch booking/payment/order/reservation logic.
- Do not change Telegram channel publishing.
- Do not change media pipeline.
- Do not change Mini App UI.

---

## Architecture rules

- Telegram Bot = router / consultant / entry point.
- Mini App = execution truth and conversion.
- Supplier Offer = source facts.
- Tour = customer-facing sellable catalog object.
- Admin = final decision maker.
- AI = draft generator only.
- visibility != bookability.
- No automatic publish.
- No supplier lifecycle side effects.
- No payment/order/reservation side effects.

---

## Source documents to read if needed

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/MINI_APP_UX.md
- docs/TESTING_STRATEGY.md

---

## Files to inspect

Inspect before editing:

- app/bot/handlers/private_entry.py
- app/services/supplier_offer_deep_link.py
- app/services/mini_app_supplier_offer_landing.py
- app/repositories/supplier_offer_execution_link.py if exists
- app/repositories/supplier_offer.py
- app/repositories/tour.py
- app/bot/keyboards.py
- app/bot/messages.py
- app/core/config.py
- tests/unit/test_private_entry_supoffer_start_hotfix.py if exists
- existing bot private entry tests

If names differ, locate equivalent files.

---

## Implementation goal

Implement the first safe B11 slice:

Update `/start supoffer_<id>` private bot routing so that published supplier offers with an active execution link to a visible/open_for_sale Tour get an exact Mini App Tour WebApp CTA.

Keep all unsafe/non-actionable cases on safe fallback.

---

## Required behavior

### 1. Source of truth

Use active `supplier_offer_execution_links` as the source of truth for linked Tour routing.

Do NOT infer from:

- SupplierOfferTourBridge alone
- B8 recurrence generated tours
- title/date matching
- latest Tour row
- AI/package metadata

If no active execution link exists, do not route to exact Tour.

---

### 2. Tour status / visibility gate

Only provide exact `/tours/{tour_code}` Mini App WebApp CTA if the linked Tour is safe for customer detail/conversion.

Minimum safe gate:

- Tour exists.
- Tour has stable code.
- Tour.status == OPEN_FOR_SALE.
- Customer catalog visibility is valid according to existing helper, e.g. `tour_is_customer_catalog_visible` or equivalent.
- For full_bus, do not use misleading per-seat wording.

If Tour is draft / not open_for_sale / sales closed / not customer-visible:

- no exact booking CTA;
- fallback to supplier offer landing or generic catalog/help.

Important:
MiniAppTourDetailService serves only OPEN_FOR_SALE Tours, so do not send `/tours/{code}` for draft or unavailable Tours if the Mini App would 404.

---

### 3. Mini App URL contract

Build exact Tour URL:

```python
f"{settings.telegram_mini_app_url.rstrip('/')}/tours/{tour.code}"
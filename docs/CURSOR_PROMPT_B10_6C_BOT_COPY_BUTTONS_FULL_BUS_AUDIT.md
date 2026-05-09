# CURSOR_PROMPT_B10_6C_BOT_COPY_BUTTONS_FULL_BUS_AUDIT

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a small B10.6C copy/UX audit step.

Do not change booking/payment/order/reservation logic.
Do not change Mini App UI.
Do not change Tour/SupplierOffer lifecycle.
Do not change Telegram publish/media/storage logic.
Do not change B11 routing behavior.
Do not change catalog filtering behavior.

---

## Current checkpoint

B10.6B router-first generic private entry is implemented.

Current behavior:

- `/start` sends router-home message instead of automatic catalog cards.
- `/tours` sends router-home message instead of automatic catalog cards.
- Explicit browse/filter callbacks still work and may show in-chat catalog cards.
- `/start tour_<code>` has exact Mini App Tour CTA.
- `/start supoffer_<id>` B11 exact supplier-offer routing remains implemented.

Observed UX issue after manual check:

- `/tours` copy says something like:
  `folosește „Arată lista în chat”`
- But the visible button says:
  `Vezi tururi`

This should be aligned.

---

## Goal

Polish bot copy/buttons after B10.6B.

Main goals:

1. Align router-home copy with actual button labels.
2. Audit full_bus/per_seat wording in bot messages/buttons.
3. Ensure bot copy does not imply individual seat selection for full_bus package cases.
4. Keep Telegram Bot as router/consultant, not a duplicate Mini App catalog.
5. Preserve all current behavior.

---

## Files to inspect

Inspect:

- app/bot/messages.py
- app/bot/keyboards.py
- app/bot/handlers/private_entry.py
- app/bot/services.py
- tests/unit/test_private_entry_router_first_b10_6b.py
- tests/unit/test_bot_private_foundation.py
- tests/unit/test_private_entry_supoffer_start_hotfix.py
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

---

## Required changes

### 1. Align router-home copy and button labels

Find router-home body translations added in B10.6B.

If the copy references a button/action name, make it match the actual button label.

Example issue:

- text says: “Arată lista în chat”
- button says: “Vezi tururi”

Pick one consistent wording.

Preferred safe direction:

- Use the existing visible button label where possible.
- Do not introduce many new labels unless needed.
- Romanian copy should be clear and natural.

Suggested Romanian semantics:

For `/start`:

```text
Bun venit. Mini App este locul principal pentru catalog, rezervări și plată.

Poți deschide Mini App pentru experiența completă sau folosi scurtăturile din chat.
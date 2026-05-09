# CURSOR_PROMPT_B10_6A_SUPPLIER_OFFER_START_SMOKE

You are working on Tours_BOT.

Run B10.6A supplier-offer start routing smoke/readiness validation.

This is a verification/debug step, not an implementation step.

## Current checkpoint

B10.6A is closed and pushed:

- `/start supoffer_<id>` copy is driven by `nav.copy_bucket` from `resolve_sup_offer_start_mini_app_routing`.
- The private entry handler does not invent routing rules.
- Exact Tour available state gets customer-facing copy and CTA.
- Non-bookable/unavailable states get safe fallback copy.
- Full-bus note is shown when `linked_is_full_bus`.
- Translations for `sr/hu/it/de` are filled to avoid missing translation keys.
- No bridge/catalog/execution/publish mutations.
- No Mini App changes.
- No booking/payment/order changes.
- No B11 routing semantics changes.

## Goal

Verify that B10.6A is safe and understandable from a customer-facing perspective.

Do not change code unless a serious typo blocks smoke documentation.

## What to inspect

Read-only inspect:

- `docs/CHAT_HANDOFF.md`
- `docs/HANDOFF_B10_6A_BOT_AS_ROUTER_SUPPLIER_OFFER_START_TO_NEXT_STEP.md`
- `docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`
- `app/services/supplier_offer_bot_start_routing.py`
- `app/bot/handlers/private_entry.py`
- `app/bot/messages.py`
- tests:
  - `tests/unit/test_supplier_offer_bot_start_routing_b11.py`
  - `tests/unit/test_private_entry_supoffer_start_hotfix.py`

## Required validation

### 1. Source-of-truth preservation

Confirm:

- `/start supoffer_<id>` uses resolver output / `nav.copy_bucket`;
- private handler does not add new routing readiness logic;
- no B11 routing semantics changed.

### 2. Customer copy safety

Confirm customer copy does not expose:

- `supplier_offer`
- `execution_link`
- `tour_bridge`
- `conversion_closure`
- `operator_workflow`
- raw lifecycle enums
- media blocker codes
- admin disabled reasons

### 3. States covered

Confirm copy exists for:

- exact Tour available;
- published but no active link / not bookable yet;
- departure not in catalog;
- departure not visible;
- mini app config missing;
- link broken / unavailable;
- full-bus note when applicable.

### 4. Test command

Run or confirm:

```powershell
python -m compileall app tests
python -m unittest tests/unit/test_supplier_offer_bot_start_routing_b11.py -v
python -m unittest tests/unit/test_private_entry_supoffer_start_hotfix.py -v
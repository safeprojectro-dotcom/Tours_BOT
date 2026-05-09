
---

## HANDOFF name

`HANDOFF_B10_6A_SUPPLIER_OFFER_START_SMOKE_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B10_6A_SUPPLIER_OFFER_START_SMOKE_TO_NEXT_STEP

## Project

Tours_BOT — B10.6A supplier offer bot-as-router.

## Step

B10.6A supplier-offer start smoke/readiness validation.

## Purpose

Verify that `/start supoffer_<id>` uses safe customer-facing copy and CTA based on existing B11 resolver output.

## Current checkpoint

B10.6A is implemented and pushed:

- resolver `copy_bucket` drives private bot text;
- handler does not invent routing rules;
- exact Tour CTA only when resolver allows it;
- fallback copy for non-bookable/unavailable states;
- no Mini App / booking / payment / order changes;
- no B11 routing semantic changes.

## Smoke goals

Confirm:

- no internal terms leak to customer;
- all copy states have translations;
- exact Tour / fallback behavior is safe;
- tests pass;
- manual Telegram smoke is ready for operator.

## Non-goals

No:

- code changes;
- routing changes;
- mutations;
- Mini App changes;
- booking/payment/order changes;
- publish/media changes.

## Expected next steps

After this smoke:

1. Optional manual Telegram smoke with a safe offer.
2. Customer copy polish if needed.
3. Otherwise pause and choose next major product block.

## Validation recorded (in-repo smoke, read-only)

- **Source of truth:** routing/gates remain in `resolve_sup_offer_start_mini_app_routing`; `_supplier_offer_start_intro` maps `copy_bucket` only.
- **Copy safety:** `start_sup_offer_router_*` strings (EN and parallel locales) avoid supplier/admin tokens (`supplier_offer`, `execution_link`, `tour_bridge`, `conversion_closure`, `operator_workflow`, lifecycle enums, media blocker codes) in customer-facing text for this path.
- **Locales:** `start_sup_offer_router_*` present for supported bundles including **en**, **ro**, **ru**, **sr**, **hu**, **it**, **de** — avoids missing-key `translate()` failures.
- **Automation:** `python -m compileall app tests`; `unittest` — `tests/unit/test_supplier_offer_bot_start_routing_b11.py` (7 tests), `tests/unit/test_private_entry_supoffer_start_hotfix.py` (6 tests) — all **OK**.
- **Operator:** manual Telegram `/start supoffer_<id>` for each bucket remains optional — use a non-production or safe staging offer per [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md) policy.
```

---

## Notes (wrapper)

The block above is the portable handoff payload for the next chat or PR. Prompt reference: [`docs/CURSOR_PROMPT_B10_6A_SUPPLIER_OFFER_START_SMOKE.md`](CURSOR_PROMPT_B10_6A_SUPPLIER_OFFER_START_SMOKE.md).

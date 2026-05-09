# HANDOFF_TELEGRAM_EXECUTION_LINK_BUTTON_C2B10T_C_TO_NEXT_STEP

Project: Tours_BOT — Supplier Offer → Tour (**Telegram operator workflow**).

## Status

**C2B10T-C implemented** — Telegram entry path for **`create_execution_link`** via existing **`SupplierOfferExecutionLinkService.link_offer_to_tour`** (same semantics as HTTP **`POST …/execution-link`** / replace path).

## Current checkpoint

- **C2B8B:** showcase **Publică / Publish**; **`publish_showcase_channel.enabled`**; double **review-package** re-read; legacy one-tap publish off the main detail keyboard.
- **C2B9A / C2B9B:** bridge + conversion chain documented; execution link + catalog + **`published`** gates unchanged in business rules.
- **C2B10T-A:** **Link tour / Leagă tur**; **`create_tour_bridge.enabled`**; bridge only.
- **C2B10T-B:** **List for sale / În catalog**; **`activate_tour_for_catalog.enabled`**; catalog activation only; **no** execution link.

## Implemented behavior (C2B10T-C)

- **Button:** EN **Booking link**, RO **Link rezervări**, only when **`operator_workflow.actions`** contains **`create_execution_link`** with **`enabled == true`** on the current **`review-package`** read.
- **Propose → confirm / cancel:** each step uses fresh **`SupplierOfferReviewPackageService.review_package`**; confirm re-checks the action is still enabled.
- **Confirm:** **`tour_id`** from **`pkg.linked_tour_catalog.tour_id`**; **`SupplierOfferExecutionLinkService.link_offer_to_tour(session, offer_id=..., tour_id=..., link_note=None)`**, **`session.commit()`**, success line + refreshed offer card.
- **Missing** **`linked_tour_catalog` / `tour_id`:** **`admin_offer_ow_action_unavailable`** (defensive).
- **Validation / not-found:** **`SupplierOfferExecutionLinkValidationError`** / **`SupplierOfferExecutionLinkNotFoundError`** surfaced as **`admin_offer_ow_exec_link_failed`** (or alert for not-found where applicable).

## Keyboard order (workflow block, when enabled)

```text
Link tour -> List for sale -> Publish -> Booking link
```

## Files changed summary

| Area | Files |
|------|--------|
| Callbacks / keyboard | **`app/bot/handlers/admin_moderation.py`** — **`admin_ops_operator_workflow_c2b10tc_execution_link`**, **`_operator_workflow_c2b10tc_exec_link_propose_callback`**, **`_detail_keyboard`** |
| Constants | **`app/bot/constants.py`** — **`ADMIN_OPS_OW_EXEC_LINK_*`** (propose / confirm / cancel) |
| Copy | **`app/bot/messages.py`** — **`admin_offer_ow_exec_link_*`** |
| Tests | **`tests/unit/test_operator_workflow_c2b10tc_specs.py`**, **`tests/unit/test_operator_workflow_c2b3_keyboard.py`**, **`tests/unit/test_telegram_admin_moderation_y281.py`** |

## Tests run

```text
python -m pytest tests/unit/test_operator_workflow_c2b10tc_specs.py tests/unit/test_operator_workflow_c2b3_keyboard.py tests/unit/test_telegram_admin_moderation_y281.py -q
```

**Result (2026-05-09):** 62 passed in ~3.1s.

No new execution-link **business** rules beyond existing service; no showcase **publish** / bridge / catalog activation paths changed from this slice; no Mini App surface; no booking / payment / orders; **no** DB migrations.

## Next likely step

- **Docs sync** — **`docs/CHAT_HANDOFF.md`**, **`docs/ADMIN_OPERATOR_WORKFLOW.md`**, **`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`** if the team tracks **C2B10T-C** there; or **OPS smoke** (**`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`**).

## Prompt

**[`docs/CURSOR_PROMPT_TELEGRAM_EXECUTION_LINK_BUTTON_C2B10T_C.md`](CURSOR_PROMPT_TELEGRAM_EXECUTION_LINK_BUTTON_C2B10T_C.md)**

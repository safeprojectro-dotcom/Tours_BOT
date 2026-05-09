# HANDOFF_TELEGRAM_ACTIVATE_TOUR_FOR_CATALOG_BUTTON_C2B10T_B_TO_NEXT_STEP

Project: Tours_BOT — Supplier Offer → Tour (**Telegram operator workflow**).

## Status

**C2B10T-B implemented and docs finalized** — Telegram entry path for **`activate_tour_for_catalog`** (B10.2 **`draft` → `open_for_sale`** via existing **`AdminTourWriteService`**; no new catalog rules).

## Current checkpoint

- **C2B8B:** showcase **Publică / Publish** on Telegram; **`publish_showcase_channel.enabled`**; double **review-package** re-read; legacy one-tap publish off the detail keyboard.
- **C2B9A / C2B9B:** bridge exists in backend; conversion-chain docs synced (**showcase ≠ bookable**; bridge ≠ catalog-visible; execution link + visibility for exact Mini App routing).
- **C2B10T-A:** **Link tour / Leagă tur**; **`create_tour_bridge.enabled`**; **`SupplierOfferTourBridgeService.create_or_replay_bridge`**; no catalog activation from that action.
- **Docs:** slice recorded in **`docs/CHAT_HANDOFF.md`**; playbook and business plan aligned (**`docs/ADMIN_OPERATOR_WORKFLOW.md`**, **`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`**).

## Implemented behavior (C2B10T-B)

- **Button:** EN **List for sale**, RO **În catalog**, only when **`operator_workflow.actions.activate_tour_for_catalog.enabled`** is true (same gate as Admin API; bot does not duplicate readiness beyond **`review-package`** / **`linked_tour_catalog`** on each read).
- **Propose → confirm / cancel:** each step uses fresh **`SupplierOfferReviewPackageService.review_package`** (operator_workflow + **`linked_tour_catalog`** on that read).
- **Confirm:** **`tour_id`** from **`pkg.linked_tour_catalog.tour_id`**; **`AdminTourWriteService.activate_tour_for_catalog`**, **`activated_by="telegram:{telegram_user_id}"`**, **`notes=None`**, **`session.commit()`** after success, success line + refreshed offer card.
- **If** action enabled but **`linked_tour_catalog`** / **`tour_id`** missing: **`admin_offer_ow_action_unavailable`** (defensive).
- **No** execution link creation, **no** publish path changes, **no** Mini App / booking / payment / order logic, **no** migrations.

## Keyboard order (workflow block, when enabled)

```text
Link tour -> List for sale -> Publish
```

(**Link tour** = C2B10T-A; **List for sale** = C2B10T-B; **Publish** = C2B8B.)

## Files changed summary (implementation slice)

| Area | Files |
|------|--------|
| Callbacks / keyboard | **`app/bot/handlers/admin_moderation.py`** — **`admin_ops_operator_workflow_c2b10tb_activate_catalog`**, **`_operator_workflow_c2b10tb_activate_catalog_propose_callback`**, **`_detail_keyboard`** |
| Constants | **`app/bot/constants.py`** — **`ADMIN_OPS_OW_ACTIVATE_CATALOG_*`** (propose / confirm / cancel prefixes) |
| Copy | **`app/bot/messages.py`** — **`admin_offer_ow_activate_catalog_*`** |
| Spec / regression tests | **`tests/unit/test_operator_workflow_c2b10tb_specs.py`**, **`tests/unit/test_operator_workflow_c2b3_keyboard.py`**, **`tests/unit/test_telegram_admin_moderation_y281.py`** |

## Tests run

```text
python -m pytest tests/unit/test_operator_workflow_c2b10tb_specs.py tests/unit/test_operator_workflow_c2b3_keyboard.py tests/unit/test_telegram_admin_moderation_y281.py -q
```

**Result (2026-05-09):** 61 passed in ~3.3s.

## Non-goals preserved

No execution link creation; no showcase **`publish`** semantics changes; no Mini App surface; no booking / payment / orders; **no** DB migrations.

## Next likely step

1. **C2B10T-C** — Telegram entry for **create/activate execution link** aligned with **`operator_workflow`** and existing published-offer link UX; or
2. **OPS smoke** — e.g. **`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`** through the current operator chain.

## Prompt

**[`docs/CURSOR_PROMPT_TELEGRAM_ACTIVATE_TOUR_FOR_CATALOG_BUTTON_C2B10T_B.md`](CURSOR_PROMPT_TELEGRAM_ACTIVATE_TOUR_FOR_CATALOG_BUTTON_C2B10T_B.md)**

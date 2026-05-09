# HANDOFF_ADMIN_OPERATOR_WORKFLOW_GENERATE_PACKAGING_BUTTON_C2B2_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — C2B2

## Status

**Implemented.** Telegram **`operator_workflow`** action **`generate_packaging_draft`** — propose button **Pregătește** (RO) / **Prepare** (EN); keys **`admin_offer_ow_pkg_gen_*`** in **`app/bot/messages.py`**.

## Behavior (as shipped)

The button is shown only when **`operator_workflow.actions`** has **`generate_packaging_draft`** with **`enabled == true`** (disabled actions are hidden).

First tap opens confirmation only.

On **confirm**:

- re-read **`GET …/review-package`**;
- verify the action is still **enabled**;
- execute **only** **`SupplierOfferPackagingService.generate_and_persist`** (packaging draft generation — **no** auto **`approve_packaging_for_publish`**);
- refresh the admin card.

On **cancel**: no mutation.

## Code pointers

- **`app/bot/handlers/admin_moderation.py`** — **`OPERATOR_WORKFLOW_C2B2_GENERATE_CODE`**, handler **`admin_ops_operator_workflow_c2b2_generate_packaging`** **;** callbacks **`ADMIN_OPS_OW_PKG_*`** in **`app/bot/constants.py`**.
- **`app/services/supplier_offer_operator_workflow.py`** — builds **`generate_packaging_draft`** in **`operator_workflow.actions`**.
- Tests **`tests/unit/test_operator_workflow_c2b2_specs.py`**, **`tests/unit/test_operator_workflow_c2b3_keyboard.py`**.

## Hard boundaries

C2B2 must not:

- approve packaging automatically after generation
- add approve_offer_moderation workflow button
- add create_tour_bridge button
- add activate_tour_for_catalog button
- add publish_showcase_channel button
- add create_execution_link button
- add batch workflow action

Legacy Aprobă / Respinge remain unchanged.

## Next possible slices

1. manual Telegram verification on a real new offer;
2. legacy moderation consolidation;
3. create_tour_bridge only in a later conversion-action slice;
4. public/dangerous publish only in a later double-confirmation slice.

Do not start next slice automatically.
# CURSOR_PROMPT_TELEGRAM_CREATE_TOUR_BRIDGE_BUTTON_C2B10T_A

You are working on Tours_BOT.

Implement C2B10T-A: Telegram admin/operator button for Supplier Offer -> Tour bridge creation/linking.

This step adds only the Telegram entry path for the already-existing bridge action.

## Current checkpoint

C2B8B is closed and pushed:
- Telegram admin `Publică / Publish` button implemented.
- It is workflow-gated by `operator_workflow.actions.publish_showcase_channel.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Legacy one-step Telegram publish was retired/suppressed from the main detail keyboard.
- No Mini App, booking/payment/order, Tour/catalog/execution link, storage, or migration changes.

C2B9A audit found:
- Supplier Offer -> Tour bridge already exists in code.
- Existing pieces include bridge model/table/enums/repository/service/admin endpoints.
- `operator_workflow` already exposes bridge/conversion actions such as:
  - `create_tour_bridge`
  - `activate_tour_for_catalog`
  - `create_execution_link`
  - `publish_showcase_channel`

C2B9B is closed and pushed:
- docs synced to reflect current conversion chain reality.
- docs clarify: published offer != bookable Tour.
- bridge/activate/execution link remain explicit steps.
- Layer A remains reservation/payment truth.

## Goal

Add a Telegram admin/operator button for the existing `create_tour_bridge` workflow action.

The button must allow an admin/operator to create or link the Tour bridge through Telegram only when the review-package/operator_workflow action says it is enabled.

## Authority for showing the button

Telegram must not implement its own bridge readiness logic.

It may rely only on:

```text
operator_workflow.actions[].code == "create_tour_bridge"
enabled == true
```

## Behavior (mirror C2B8B)

- **Propose** tap: single fresh `review_package(offer_id)`; if the action is not enabled → `admin_offer_ow_action_unavailable` alert.
- **Confirm** tap: **re-read** `review_package` again; if disabled → alert; else `SupplierOfferTourBridgeService.create_or_replay_bridge(session, supplier_offer_id=..., created_by="telegram:{admin_id}", notes=None, existing_tour_id=None)`, `session.commit()`, success message + refreshed offer card.
- **Cancel** on confirm keyboard: same UX as other workflow confirms (cancel message; no mutation).

## Non-goals

- No changes to bridge business rules, HTTP routes, `operator_workflow` derivation, Mini App, execution link, catalog activation, or Layer A booking/payment.
# CURSOR_PROMPT_TELEGRAM_ACTIVATE_TOUR_FOR_CATALOG_BUTTON_C2B10T_B

You are working on Tours_BOT.

Implement C2B10T-B: Telegram admin/operator button for activating a linked Tour for catalog.

This step adds only the Telegram entry path for the already-existing `activate_tour_for_catalog` operator workflow action.

## Current checkpoint

C2B8B is closed and pushed:
- Telegram admin `Publică / Publish` button implemented.
- It is workflow-gated by `operator_workflow.actions.publish_showcase_channel.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Legacy one-step Telegram publish was retired/suppressed from the main detail keyboard.

C2B9A/C2B9B are closed:
- Supplier Offer -> Tour bridge already exists.
- Docs synced to current conversion chain:
  - published showcase offer != bookable Tour;
  - bridge/link != catalog-visible;
  - catalog-visible + active execution link is required for exact Mini App conversion;
  - Layer A remains reservation/payment truth.

C2B10T-A is expected to be closed before this step:
- Telegram `Link tour / Leagă tur` button implemented.
- Gated by `operator_workflow.actions.create_tour_bridge.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Confirm reuses `SupplierOfferTourBridgeService.create_or_replay_bridge(...)`.
- It creates/links Tour bridge only.
- No catalog activation.
- No execution link.
- No Mini App / booking / payment / order changes.

## Goal

Add Telegram admin/operator button for activating the linked Tour for catalog.

The button must rely only on:

```text
operator_workflow.actions[].code == "activate_tour_for_catalog"
enabled == true
```

## Behavior (mirror C2B10T-A / C2B8B)

- **Propose:** re-read `review_package`; if action not enabled → `admin_offer_ow_action_unavailable` alert.
- **Confirm:** re-read `review_package` again; if disabled → alert; else resolve **`tour_id`** from the same read model: **`linked_tour_catalog.tour_id`** (present when the workflow enables catalog activation).
- **Execute:** `AdminTourWriteService.activate_tour_for_catalog(session, tour_id=..., activated_by="telegram:{user_id}", notes=None)`, `session.commit()`, success message + refreshed offer card.
- **Cancel:** same as other workflow confirms (no mutation).

## Keyboard order

After **Link tour** (C2B10T-A), before **Publish** (C2B8B), when enabled.

## Non-goals

- No changes to B10.2 / B8.3 guard semantics, HTTP routes, or `operator_workflow` derivation.
- No showcase publish, execution link, Mini App, booking/payment/order, or migrations.

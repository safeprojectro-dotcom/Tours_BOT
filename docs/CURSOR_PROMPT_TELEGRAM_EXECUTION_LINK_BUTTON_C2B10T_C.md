# CURSOR_PROMPT_TELEGRAM_EXECUTION_LINK_BUTTON_C2B10T_C

You are working on Tours_BOT.

Implement C2B10T-C: Telegram admin/operator button for creating or activating Supplier Offer execution link.

This step adds only the Telegram entry path for the already-existing `create_execution_link` operator workflow action.

## Current checkpoint

C2B8B is closed and pushed:
- Telegram admin `Publică / Publish` button implemented.
- Workflow-gated by `operator_workflow.actions.publish_showcase_channel.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Legacy one-step Telegram publish retired from main detail keyboard.

C2B9A/C2B9B are closed:
- Supplier Offer -> Tour bridge already exists.
- Docs synced to current conversion chain:
  - published showcase offer != bookable Tour;
  - bridge/link != catalog-visible;
  - catalog-visible + active execution link is required for exact Mini App conversion;
  - Layer A remains reservation/payment truth.

C2B10T-A is closed and pushed:
- Telegram `Link tour / Leagă tur` button implemented.
- Gated by `operator_workflow.actions.create_tour_bridge.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Creates/links Tour bridge only.

C2B10T-B is closed and pushed:
- Telegram `List for sale / În catalog` button implemented.
- Gated by `operator_workflow.actions.activate_tour_for_catalog.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Activates linked Tour for catalog only.
- Does not create execution link.

## Goal

Add Telegram admin/operator button for creating/activating execution link.

The button must rely only on:

```text
operator_workflow.actions[].code == "create_execution_link"
enabled == true
```

## Required behavior (mirror C2B10T-A / C2B10T-B)

- Short RO/EN labels (e.g. EN **Booking link**, RO **Link rezervări**).
- **Propose** and **confirm** each load fresh `review-package` / `operator_workflow`; gate on `create_execution_link` **enabled** on that read (otherwise `admin_offer_ow_action_unavailable`).
- **Confirm** calls `SupplierOfferExecutionLinkService.link_offer_to_tour(session, offer_id=..., tour_id=..., link_note=None)` — same semantics as HTTP `POST …/execution-link` (`replace_link_for_offer` path).
- **`tour_id`** from `pkg.linked_tour_catalog.tour_id` (defensive if missing).
- `session.commit()` after success; success line + refreshed offer card.
- **Non-goals:** no new execution-link business rules; no publish/catalog/bridge/Mini App/booking changes; no migrations.

## Keyboard order (when enabled)

Workflow block: **Link tour → List for sale → Publish → Booking link** (after **C2B10T-C**).
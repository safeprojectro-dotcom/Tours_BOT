# CURSOR_PROMPT_SUPPLIER_OFFER_CONVERSION_DOCS_SYNC_C2B9B

You are working on Tours_BOT.

Implement C2B9B: Supplier Offer conversion documentation sync.

This is a docs-only step.

## Current checkpoint

C2B8B is closed and pushed:

- Telegram admin `Publică / Publish` button implemented.
- It is workflow-gated by `operator_workflow.actions.publish_showcase_channel.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Legacy one-step Telegram publish was retired/suppressed from the main detail keyboard.
- No Mini App, booking/payment/order, Tour/catalog/execution link, storage, or migration changes were made.

C2B9A audit found:

- Supplier Offer -> Tour bridge already exists in code.
- Relevant pieces include:
  - `SupplierOfferTourBridgeStatus`
  - `SupplierOfferTourBridgeKind`
  - `supplier_offer_tour_bridges`
  - `SupplierOfferTourBridgeService`
  - admin bridge endpoints
  - execution link endpoints
  - `activate_tour_for_catalog`
  - review-package/operator_workflow actions:
    - `create_tour_bridge`
    - `activate_tour_for_catalog`
    - `create_execution_link`
    - `publish_showcase_channel`
  - B11 `supoffer_<id>` routing via active execution link + OPEN_FOR_SALE + catalog visibility.
- Therefore the next task is not to create the bridge from scratch.
- The next task is to sync docs and OPS runbook so the team understands the actual conversion chain.

## Goal

Update documentation so it matches current implementation reality:

```text
Supplier Offer
-> AI/admin packaging
-> admin approval / publish readiness
-> Telegram showcase publish
-> explicit Tour bridge / link
-> activate Tour for catalog when allowed
-> create/activate execution link
-> B11 deep link routes to exact Mini App Tour only when execution link is active and Tour is bookable/visible
-> Layer A handles reservation/payment
```

## Deliverables (this prompt)

- **`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`** — conversion chain subsection (C2B9B); B11 row; C2A / C2B2 / C2B3 / Telegram UX policy aligned with **C2B8B** and **Admin API** bridge/activate.
- **`docs/ADMIN_OPERATOR_WORKFLOW.md`** — §1 narrative chain; step **9** HTTP **or** Telegram publish; **C2A** / UX policy; **C2B3** row order.
- **`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`** — pointer to full chain + **`ADMIN_OPERATOR_WORKFLOW`**.
- **`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`** — C2B9B completion notes in gaps / §4 / §5.
- **`docs/CHAT_HANDOFF.md`** — **C2B9B** done; **C2B2** / UX / **C2B3** bullets consistent with above.
- **`docs/HANDOFF_SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A_TO_NEXT_STEP.md`** — C2B9B struck through as done; next steps **C2B10T-*** / **B7.3B** / **B11**.
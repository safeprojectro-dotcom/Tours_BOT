# CURSOR_PROMPT_C2B10T_C_DOCS_FINALIZE

Finalize C2B10T-C documentation only.

C2B10T-C code is already implemented:
- Telegram admin/operator `Booking link / Link rezervări` button.
- Button visible only when `operator_workflow.actions.create_execution_link.enabled == true`.
- Propose and confirm both load fresh review-package/operator_workflow.
- Confirm checks the action is still enabled.
- Confirm uses `linked_tour_catalog.tour_id`.
- Missing linked catalog blocks with `admin_offer_ow_action_unavailable`.
- Confirm calls `SupplierOfferExecutionLinkService.link_offer_to_tour(...)`.
- `link_note=None`.
- Commits after success and refreshes offer card.
- No B11 routing changes.
- No catalog activation.
- No publish semantics changes.
- No Mini App.
- No booking/payment/orders.
- No migrations.

## Required docs updates

Update `docs/CHAT_HANDOFF.md` with a short C2B10T-C completed entry:

- Telegram `Booking link / Link rezervări` implemented.
- Gated only by `operator_workflow.actions.create_execution_link.enabled`.
- Propose and confirm load fresh review-package/operator_workflow.
- Confirm reuses existing execution-link service semantics.
- Creates/replaces active execution link only.
- Does not publish.
- Does not activate catalog.
- Does not change B11 routing.
- Does not touch Mini App / booking / payment / orders.
- No migrations.

Update:

- `docs/ADMIN_OPERATOR_WORKFLOW.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`

to reflect that the Telegram conversion workflow now includes:

```text
Link tour → List for sale → Publish → Booking link
```

## Deliverables (done)

- **`docs/CHAT_HANDOFF.md`** — **Slice C2B10T-C** **+** **C2B2** / **UX** / **C2B3** / **C2B9A** pointer refresh **.**
- **`docs/ADMIN_OPERATOR_WORKFLOW.md`** — цепочка §1, шаг **10**, **C2A**, UX, **C2B3**, тип документа **.**
- **`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`** — conversion chain **+** **C2B2** / **UX** / **C2B3** **.**
- **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** **/** **`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`** — согласованы с **C2B10T-C** (устранение устаревших формулировок) **.**
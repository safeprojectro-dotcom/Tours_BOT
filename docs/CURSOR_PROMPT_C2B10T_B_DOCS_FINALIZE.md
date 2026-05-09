# CURSOR_PROMPT_C2B10T_B_DOCS_FINALIZE

Finalize C2B10T-B documentation only.

C2B10T-B code is already implemented:
- Telegram admin/operator `List for sale / În catalog` button.
- Button visible only when `operator_workflow.actions.activate_tour_for_catalog.enabled == true`.
- Propose and confirm both re-read review-package/operator_workflow.
- Confirm calls existing `AdminTourWriteService.activate_tour_for_catalog(...)`.
- Uses `tour_id` from `pkg.linked_tour_catalog.tour_id`.
- Uses `activated_by="telegram:{user_id}"`.
- Commits after success and refreshes offer card.
- No execution link creation.
- No publish semantics changes.
- No Mini App.
- No booking/payment/orders.
- No migrations.

## Required docs updates

Update `docs/CHAT_HANDOFF.md` with a short C2B10T-B completed entry:

- Telegram `List for sale / În catalog` implemented.
- Gated only by `operator_workflow.actions.activate_tour_for_catalog.enabled`.
- Propose and confirm re-read review-package.
- Confirm reuses existing catalog activation service.
- Activates linked Tour for catalog only.
- Does not create execution link.
- Does not publish.
- Does not touch Mini App / booking / payment / orders.
- No migrations.

Create or update:

`docs/HANDOFF_TELEGRAM_ACTIVATE_TOUR_FOR_CATALOG_BUTTON_C2B10T_B_TO_NEXT_STEP.md`

Include:
- current checkpoint;
- implemented behavior;
- files changed summary;
- tests run;
- non-goals preserved;
- next likely step:
  - C2B10T-C — Telegram button for create/activate execution link;
  - or OPS smoke through current chain.

## Also note

The implemented keyboard order is:

```text
Link tour -> List for sale -> Publish
```

## Deliverables (done)

- **`docs/CHAT_HANDOFF.md`** — C2B10T-B slice + UX/C2B3 alignment (already present in repo; verify after merge).
- **`docs/HANDOFF_TELEGRAM_ACTIVATE_TOUR_FOR_CATALOG_BUTTON_C2B10T_B_TO_NEXT_STEP.md`** — checkpoint, behavior, files changed, tests run, non-goals, next step.
- **`docs/ADMIN_OPERATOR_WORKFLOW.md`** / **`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`** — Telegram List for sale / C2B10T-B in conversion chain and keyboard policy.
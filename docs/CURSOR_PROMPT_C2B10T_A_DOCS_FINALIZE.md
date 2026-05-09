# CURSOR_PROMPT_C2B10T_A_DOCS_FINALIZE

Finalize C2B10T-A documentation only.

C2B10T-A code is already implemented:
- Telegram admin/operator `Link tour / Leagă tur` button.
- Button visible only when `operator_workflow.actions.create_tour_bridge.enabled == true`.
- Propose and confirm both re-read review-package/operator_workflow.
- Confirm calls existing `SupplierOfferTourBridgeService.create_or_replay_bridge(...)`.
- `created_by="telegram:{user_id}"`.
- No catalog activation.
- No execution link creation.
- No Mini App.
- No booking/payment/orders.
- No migrations.

## Required docs updates

Update `docs/CHAT_HANDOFF.md` with a short C2B10T-A completed entry:

- Telegram `Link tour / Leagă tur` implemented.
- Gated only by `operator_workflow.actions.create_tour_bridge.enabled`.
- Propose and confirm re-read review-package.
- Confirm reuses existing bridge service semantics.
- Creates/links Tour bridge only.
- Does not activate Tour for catalog.
- Does not create execution link.
- Does not touch Mini App / booking / payment / orders.
- No migrations.

Create or update:

`docs/HANDOFF_TELEGRAM_CREATE_TOUR_BRIDGE_BUTTON_C2B10T_A_TO_NEXT_STEP.md`

Include:
- current checkpoint;
- implemented behavior;
- files changed summary;
- tests run;
- non-goals preserved;
- next likely steps:
  1. C2B10T-B — Telegram button for activate Tour for catalog;
  2. C2B10T-C — Telegram button for create/activate execution link;
  3. production/OPS smoke.

## Also verify/report

Report whether the changed constants file is:

- `app/bot/constants.py`

and not accidentally:

- `app/bot/constants.md`

## Forbidden

Do not change application behavior.

Do not change:
- app logic except typo/docstring only if absolutely necessary;
- tests unless there is a typo in filename/reference;
- migrations;
- Mini App;
- booking/payment/orders;
- catalog activation;
- execution link;
- publish behavior.

## After completion report

Return:

1. docs changed;
2. whether `app/bot/constants.py` is the actual changed constants file;
3. tests already run / whether any additional tests run;
4. `git status --short`;
5. `git diff --stat`;
6. explicit confirmation:
   - no migrations;
   - no Mini App;
   - no booking/payment/orders;
   - no catalog activation;
   - no execution link creation;
   - no publish semantics changes.
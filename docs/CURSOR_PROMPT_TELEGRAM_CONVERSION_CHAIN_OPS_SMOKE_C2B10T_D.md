# CURSOR_PROMPT_TELEGRAM_CONVERSION_CHAIN_OPS_SMOKE_C2B10T_D

You are working on Tours_BOT.

Run C2B10T-D: OPS smoke / runbook validation for Telegram Supplier Offer conversion chain.

This is a verification/debug step, not an implementation step.

## Current checkpoint

C2B8B closed and pushed:
- Telegram `Publică / Publish`
- gated by `operator_workflow.actions.publish_showcase_channel.enabled`
- propose/confirm both re-read review-package
- legacy one-step publish retired

C2B10T-A closed and pushed:
- Telegram `Link tour / Leagă tur`
- gated by `operator_workflow.actions.create_tour_bridge.enabled`
- propose/confirm both re-read review-package
- creates/links Tour bridge only

C2B10T-B closed and pushed:
- Telegram `List for sale / În catalog`
- gated by `operator_workflow.actions.activate_tour_for_catalog.enabled`
- propose/confirm both re-read review-package
- activates linked Tour for catalog only

C2B10T-C closed and pushed:
- Telegram `Booking link / Link rezervări`
- gated by `operator_workflow.actions.create_execution_link.enabled`
- propose/confirm both re-read review-package
- creates/replaces active execution link only

Current Telegram operator conversion order:

```text
Link tour → List for sale → Publish → Booking link
```

## Required verification (no product code)

1. Confirm **`_detail_keyboard`** order matches the block above (`app/bot/handlers/admin_moderation.py`).
2. Confirm each Telegram flow re-reads **`review-package`** on propose and on confirm (parity with **C2B8B**).
3. Confirm runbook documents Telegram ↔ HTTP parity for ops (`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`).
4. Run automated regression tests listed below.

## Automated test run (2026-05-09)

```text
python -m pytest tests/unit/test_supplier_offer_catalog_conversion_closure.py tests/unit/test_operator_workflow_c2b3_keyboard.py tests/unit/test_operator_workflow_c2b10ta_specs.py tests/unit/test_operator_workflow_c2b10tb_specs.py tests/unit/test_operator_workflow_c2b10tc_specs.py tests/unit/test_telegram_admin_moderation_y281.py -q
```

**Result:** 68 passed (~7s on dev machine).

## Runbook updates (done)

- `docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md` — § «Telegram admin card parity»; optional Telegram row in run log; document control note.
- `docs/CHAT_HANDOFF.md` — **Slice C2B10T-D** verification line.

## Still operator-owned (not substituted by repo)

- Mode **B** walkthrough against real **BASE_URL**, **ADMIN_TOKEN**, showcase channel, and allowlisted Telegram admin.
- Manual `/start supoffer_<id>` check (walkthrough step 11).
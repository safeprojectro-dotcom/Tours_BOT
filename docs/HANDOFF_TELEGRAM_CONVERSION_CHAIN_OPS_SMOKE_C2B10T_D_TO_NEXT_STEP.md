# HANDOFF_TELEGRAM_CONVERSION_CHAIN_OPS_SMOKE_C2B10T_D_TO_NEXT_STEP

Project: Tours_BOT — Supplier Offer → Tour (**Telegram operator conversion chain**).

## Status

**C2B10T-D completed (verification + docs)** — no product code changes. Repo-side validation and runbook parity for **C2B8B** + **C2B10T-A/B/C**; live staging/production Telegram smoke remains **operator-owned**.

## Current checkpoint

- **C2B8B:** **Publică / Publish**; **`publish_showcase_channel.enabled`**; propose/confirm + double **`review-package`** re-read; legacy one-tap publish retired from main card.
- **C2B10T-A:** **Link tour / Leagă tur**; **`create_tour_bridge.enabled`**; bridge only.
- **C2B10T-B:** **List for sale / În catalog**; **`activate_tour_for_catalog.enabled`**; catalog activation only.
- **C2B10T-C:** **Booking link / Link rezervări**; **`create_execution_link.enabled`**; execution link create/replace only (**`link_offer_to_tour`** semantics).

## Keyboard order (workflow block, when enabled)

```text
Link tour -> List for sale -> Publish -> Booking link
```

Implementation: **`app/bot/handlers/admin_moderation.py`** **`_detail_keyboard`**.

## What was validated (repo)

- Telegram ↔ **HTTP** parity table and ops ordering notes added to **`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`** (**§ Telegram admin card parity**).
- **CHAT_HANDOFF** **Slice C2B10T-D** records automated test bundle + pass count.

## Tests run

```text
python -m pytest tests/unit/test_supplier_offer_catalog_conversion_closure.py tests/unit/test_operator_workflow_c2b3_keyboard.py tests/unit/test_operator_workflow_c2b10ta_specs.py tests/unit/test_operator_workflow_c2b10tb_specs.py tests/unit/test_operator_workflow_c2b10tc_specs.py tests/unit/test_telegram_admin_moderation_y281.py -q
```

**Result (2026-05-09):** 68 passed (~7s).

## Docs touched (this slice)

| File | Change |
|------|--------|
| **`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`** | Telegram parity §, optional run-log row, document control |
| **`docs/CHAT_HANDOFF.md`** | **C2B10T-D** verification line |
| **`docs/CURSOR_PROMPT_TELEGRAM_CONVERSION_CHAIN_OPS_SMOKE_C2B10T_D.md`** | Full prompt + results |

## Non-goals (preserved)

No migrations, no Mini App/UI template edits, no booking/payment/order logic changes from this step.

## Still operator-owned

- **Mode B** in **`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`** against real **BASE_URL**, **ADMIN_TOKEN**, showcase config, allowlisted Telegram admin.
- Manual **`/start supoffer_<id>`** (walkthrough step 11).

## Next likely step

- Run **Mode B** on staging and fill the run log **;** or pick next product slice from **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** / stakeholder backlog.

## Prompt

**[`docs/CURSOR_PROMPT_TELEGRAM_CONVERSION_CHAIN_OPS_SMOKE_C2B10T_D.md`](CURSOR_PROMPT_TELEGRAM_CONVERSION_CHAIN_OPS_SMOKE_C2B10T_D.md)**

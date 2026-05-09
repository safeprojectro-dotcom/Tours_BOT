# HANDOFF_TELEGRAM_CREATE_TOUR_BRIDGE_BUTTON_C2B10T_A_TO_NEXT_STEP

Project: Tours_BOT — Supplier Offer → Tour (**Telegram operator workflow**).

## Current checkpoint

- **C2B8B** shipped: Telegram showcase **Publică / Publish**; `publish_showcase_channel.enabled`; propose/confirm + **review-package** re-reads; legacy one-tap publish retired from detail keyboard.
- **C2B9A / B10:** bridge service + **`POST …/tour-bridge`** already in backend.
- **C2B9B:** conversion-chain docs synced.
- **C2B10T-A shipped (code):** Telegram **Link tour / Leagă tur** for **`create_tour_bridge`**; docs finalized in **`CHAT_HANDOFF.md`**, **`ADMIN_OPERATOR_WORKFLOW.md`**, **`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`**, this handoff.

## Implemented behavior (C2B10T-A)

- **Button:** EN **Link tour**, RO **Leagă tur** on admin offer detail keyboard.
- **Gate:** only **`operator_workflow.actions[].code == "create_tour_bridge"`** and **`enabled == true`** (no extra readiness logic in the bot).
- **Flow:** propose → confirm/cancel; **both** steps load fresh **`SupplierOfferReviewPackageService.review_package`** before showing confirm / before mutation.
- **Confirm:** **`SupplierOfferTourBridgeService.create_or_replay_bridge`**, **`created_by="telegram:{telegram_user_id}"`**, **`existing_tour_id=None`**, **`session.commit()`** — same semantics as HTTP.
- **Non-goals preserved:** no **activate-for-catalog**, no **execution link** creation from this action, no Mini App, no booking/payment/orders, **no migrations**, no publish semantics changes.

## Files changed summary (implementation + docs finalize)

**Code (already merged before this doc pass; unchanged in doc-only task):**

| Area | Path |
|------|------|
| Callback prefixes | `app/bot/constants.py` (**not** `constants.md`) |
| Handler + keyboard | `app/bot/handlers/admin_moderation.py` |
| i18n | `app/bot/messages.py` |
| Tests | `tests/unit/test_operator_workflow_c2b10ta_specs.py`, `tests/unit/test_operator_workflow_c2b3_keyboard.py`, `tests/unit/test_telegram_admin_moderation_y281.py` |

**Docs (this finalize step):**

| Path |
|------|
| `docs/CHAT_HANDOFF.md` |
| `docs/HANDOFF_TELEGRAM_CREATE_TOUR_BRIDGE_BUTTON_C2B10T_A_TO_NEXT_STEP.md` (this file) |
| `docs/ADMIN_OPERATOR_WORKFLOW.md` |
| `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md` |

## Tests run

- **During C2B10T-A implementation:** `pytest` on `test_operator_workflow_c2b10ta_specs.py`, `test_operator_workflow_c2b3_keyboard.py`, `test_telegram_admin_moderation_y281.py::TelegramAdminModerationY281Tests::test_workflow_tour_bridge_confirm_calls_service_when_gate_enabled` — all passed.
- **This doc-only finalize:** no additional tests required; none were run for this step.

## Next likely steps

1. **C2B10T-B** — Telegram button for **`activate_tour_for_catalog`** (same propose / confirm / double **review-package** pattern; product sign-off).
2. **C2B10T-C** — Telegram entry for **create/activate execution link** (align with **`operator_workflow`** and existing published-offer link UX; product sign-off).
3. **Production / OPS smoke** — e.g. [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md), staging channel/offers.

## Prompts

- Implementation: [`docs/CURSOR_PROMPT_TELEGRAM_CREATE_TOUR_BRIDGE_BUTTON_C2B10T_A.md`](CURSOR_PROMPT_TELEGRAM_CREATE_TOUR_BRIDGE_BUTTON_C2B10T_A.md)
- Docs finalize: [`docs/CURSOR_PROMPT_C2B10T_A_DOCS_FINALIZE.md`](CURSOR_PROMPT_C2B10T_A_DOCS_FINALIZE.md)

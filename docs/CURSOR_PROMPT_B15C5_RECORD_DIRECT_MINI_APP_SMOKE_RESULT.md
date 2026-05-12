# CURSOR_PROMPT_B15C5_RECORD_DIRECT_MINI_APP_SMOKE_RESULT

Record the production smoke result for B15C5 direct Mini App short-name channel CTA.

## Context

B15C5 was implemented and deployed.

Relevant commits:

- `06741d fix: support direct Mini App short-name tour links`
- `19f50da fix: guard showcase cover replacement workflow`
- `17ddd4c fix: open channel tour CTA through Telegram Mini App`
- `37f213e feat: require exact tour CTA before supplier offer publish`

Railway/BotFather config was completed:

- BotFather Mini App URL points to `https://miniappui-production.up.railway.app`
- `TELEGRAM_MINI_APP_SHORT_NAME=banattours`
- Backend preview generates: `https://t.me/tours_tm_bot/banattours?startapp=tour_<tour_code>`

## Production smoke evidence (template — fill when running)

Use **[`docs/B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md`](B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md)** as the canonical record once filled.

## Required docs to update (when executing this prompt)

Update:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B15C_PRODUCTION_SMOKE_RESULT.md`
- `docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`
- `docs/HANDOFF_B15C5_DIRECT_MINI_APP_LINK_SHORT_NAME_TO_NEXT_STEP.md`

Create or refresh:

- `docs/B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md`
- `docs/HANDOFF_B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`

## Non-goals

Do not change application code.

Do not publish again from this doc step.

Do not mutate production data.

Do not edit existing Telegram posts.

Do not create orders/payments/reservations from tooling.

Do not run migrations.

## Completion — 2026-05-09

Executed: smoke result and cross-doc updates recorded; see **[`docs/B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md`](B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md)** and **[`docs/HANDOFF_B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`](HANDOFF_B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md)**.

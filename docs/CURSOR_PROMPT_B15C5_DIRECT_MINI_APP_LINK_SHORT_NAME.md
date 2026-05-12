# CURSOR_PROMPT_B15C5_DIRECT_MINI_APP_LINK_SHORT_NAME

Fix channel Rezervă link so it opens the Mini App directly when Telegram/BotFather configuration supports direct Mini App links.

## Context

B15C/B15C1/B15C4 are complete.

Relevant commits:
- `37f213e feat: require exact tour CTA before supplier offer publish`
- `17ddd4c fix: open channel tour CTA through Telegram Mini App`
- `19f50da fix: guard showcase cover replacement workflow`

B15C1 changed channel CTA from direct HTTPS Mini App URL to:

`https://t.me/tours_tm_bot?startapp=tour_<tour_code>`

This fixed the unsafe direct-web identity path in principle, but production smoke on Offer #14 showed this UX:

`Channel post → Rezervă → private bot chat → bot message → Deschide această plecare (Mini App) → Mini App`

The user confirmed that pressing `Deschide această plecare (Mini App)` reaches the reservation page, but the channel CTA should ideally open the Mini App directly.

## Telegram platform context

Telegram supports Mini App direct links. Relevant formats include:

1. Main Mini App:
   `https://t.me/{bot_username}?startapp={payload}`

2. Direct-link Mini App with short app name:
   `https://t.me/{bot_username}/{app_short_name}?startapp={payload}`

The second form may be required for direct Mini App open depending on BotFather setup/client behavior.

## Goal

Add explicit support for an optional Telegram Mini App short name / direct app path so channel `Rezervă` can generate:

`https://t.me/tours_tm_bot/{mini_app_short_name}?startapp=tour_<tour_code>`

instead of bare:

`https://t.me/tours_tm_bot?startapp=tour_<tour_code>`

when configured.

If no short name is configured, preserve the existing bare `?startapp=` behavior as fallback.

## Required docs to read first

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B15C_PRODUCTION_SMOKE_RESULT.md`
- `docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`
- `docs/HANDOFF_B15C1_MINI_APP_IDENTITY_FROM_CHANNEL_EXACT_TOUR_ENTRY_TO_NEXT_STEP.md`
- `docs/HANDOFF_B15C4_COVER_REPLACEMENT_WORKFLOW_SUPPLIER_AND_ADMIN_TO_NEXT_STEP.md`
- settings/env docs if present
- Telegram setup docs if present

Inspect:
- `app/services/supplier_offer_deep_link.py`
- `app/services/supplier_offer_showcase_message.py`
- `app/services/supplier_offer_moderation_service.py`
- settings/config class for Telegram bot username / Mini App URL
- tests:
  - `tests/unit/test_supplier_offer_deep_link.py`
  - `tests/unit/test_supplier_offer_showcase_ro.py`
  - `tests/unit/test_supplier_offer_track3_moderation.py`

## Implementation requirements

### 1. Add optional config

Add optional setting/env var, naming suggestion:

`TELEGRAM_MINI_APP_SHORT_NAME`

or if project naming prefers:

`TELEGRAM_MAIN_MINI_APP_SHORT_NAME`

This value is the BotFather Mini App short name / app path, e.g.:

`banattours`

Do not hardcode it.

### 2. Link generation

Update direct Mini App launcher helper to support:

If `bot_username` and `mini_app_short_name` exist:

`https://t.me/{bot_username}/{mini_app_short_name}?startapp=tour_{tour_code}`

Else if only `bot_username` exists:

`https://t.me/{bot_username}?startapp=tour_{tour_code}`

Else fallback remains existing HTTPS Mini App route:

`{mini_app_base}/tours/{tour_code}`

### 3. Validation

Validate:
- bot username safe chars;
- short name safe chars;
- tour code safe chars;
- no arbitrary URL injection.

Do not accept `/`, `?`, `&`, spaces, or URL-like values inside short name.

### 4. Preserve start_param route mapping

Do not change `assets/index.html` behavior unless needed. Current start_param mapping:

`tour_<code> → /tours/<code>`

must stay.

### 5. Do not break bot fallback

The existing bare `https://t.me/{bot}?startapp=tour_...` path may be useful when short name is absent. Keep it.

### 6. Tests

Add/update tests proving:

- with bot username + short name:
  - CTA is `https://t.me/previewbot/appshort?startapp=tour_<code>`;
- with bot username but no short name:
  - CTA is `https://t.me/previewbot?startapp=tour_<code>`;
- with no bot username:
  - fallback HTTPS `/tours/<code>`;
- invalid short name is rejected or ignored safely;
- B15C execution-link gating remains unchanged;
- B15C4 media text-only fallback not regressed.

Run focused tests:

```bash
python -m pytest tests/unit/test_supplier_offer_deep_link.py tests/unit/test_supplier_offer_showcase_ro.py tests/unit/test_supplier_offer_track3_moderation.py tests/unit/test_supplier_offer_showcase_cover_sendability.py -q
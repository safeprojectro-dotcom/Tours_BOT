# Handoff — B15C5 direct Mini App link (BotFather short name)

## Problem context (pre-B15C5)

**B15C1** set channel **Rezervă** to:

`https://t.me/{bot}?startapp=tour_<tour_code>`

That restores **Telegram WebApp** **`initData`** (vs plain HTTPS Mini App host). Production smoke (e.g. Offer **#14**) could still feel like:

`Channel → Rezervă → private bot → «Deschide această plecare (Mini App)» → …`

depending on client/BotFather setup — **not** always one tap from the channel into the Mini App.

## What shipped (in-repo)

1. **Env / Settings** — **`TELEGRAM_MINI_APP_SHORT_NAME`** → **`Settings.telegram_mini_app_short_name`** (`app/core/config.py`).

2. **URL builder** — `mini_app_tour_channel_startapp_url` in **`app/services/supplier_offer_deep_link.py`**:
   - With validated short name: **`https://t.me/{bot}/{short}?startapp=tour_{code}`**
   - Without / if short name invalid (ignored safely): **`https://t.me/{bot}?startapp=tour_{code}`**
   - HTTPS **`{mini_app}/tours/{code}`** fallback unchanged when bot username is missing.

3. **Wiring** — **`build_showcase_publication` / `_cta_block_html`** and **`SupplierOfferModerationService.showcase_preview`** (`cta_rezerva_href`) pass the normalized short name.

4. **Bootstrap** — **`assets/index.html`** **`start_param` → `/tours/{code}`** unchanged.

5. **Examples** — **`.env.example`**, **`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`**, **`docs/CHAT_HANDOFF.md`** (B15C5 bullet).

### Tests (pointers)

- **`tests/unit/test_supplier_offer_deep_link.py`**
- **`tests/unit/test_supplier_offer_showcase_ro.py`**
- **`tests/unit/test_supplier_offer_track3_moderation.py`**

## Operator next steps (production / Railway)

1. In **BotFather**, confirm the Mini App **short name** matches what you will set in env (no `@`, no path punctuation).
2. Set **`TELEGRAM_MINI_APP_SHORT_NAME=<that_short_name>`** on the **API** service (same app that builds showcase previews / publish).
3. **Redeploy** so Settings pick up the var.
4. Validate on a **new** **`showcase-preview`** / **new** channel post — **do not** rely on editing old messages.

## Safety

- **Identity** — still WebApp / **`startapp`**; no trusted **`user_id`** from query string; **Layer A** unchanged.
- **Old posts** — leave as-is; only new captions get the new link shape.
- **Invalid short name** in env is **ignored** (falls back to bare **`?startapp=`**), so a typo should not blank the CTA if bot username is still set.

## Production smoke (operator, **PASS**, 2026-05-09)

With **`TELEGRAM_MINI_APP_SHORT_NAME=banattours`** and BotFather Mini App URL on **`https://miniappui-production.up.railway.app`**, **new** showcase message **#28** (Offer **#15**, tour **`B10-SO15-460344`**) validated **direct** **`https://t.me/tours_tm_bot/banattours?startapp=tour_B10-SO15-460344`** → Mini App → exact tour → reservation → temp hold **#55** → payment screen; **no** private-bot launcher; **no** red identity warning.

**Record:** [`docs/B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md`](B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md)  
**Post-smoke handoff:** [`docs/HANDOFF_B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`](HANDOFF_B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md)

## Related

- Prompt: **`docs/CURSOR_PROMPT_B15C5_DIRECT_MINI_APP_LINK_SHORT_NAME.md`**
- Smoke prompt: **`docs/CURSOR_PROMPT_B15C5_RECORD_DIRECT_MINI_APP_SMOKE_RESULT.md`**
- Identity / **`start_param`**: **`docs/HANDOFF_B15C1_MINI_APP_IDENTITY_FROM_CHANNEL_EXACT_TOUR_ENTRY_TO_NEXT_STEP.md`**

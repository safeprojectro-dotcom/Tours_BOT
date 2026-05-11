# Handoff — B15C1 Mini App identity from channel exact-tour entry

## Production context (B15C smoke, pre-B15C1)

Operator-recorded validation that **B15C** behaved as intended (exact tour CTA, prep UX); **Rezervă** at that time used a **plain HTTPS** tour URL.

| Field | Value |
|--------|--------|
| Supplier offer | **#13** (*Excursie In Arad*) |
| Tour | **#7** |
| Tour code | **`B10-SO13-e9f389`** |
| Execution link | **#6** |
| Publish attempt | **#3** |
| Showcase `message_id` | **26** |
| Observed route | **`/tours/B10-SO13-e9f389`** ✓ |

**Not** a B15C CTA failure: the exact tour opened; **user-scoped** flows failed because **`initData`** was missing for that entry path.

## Problem (resolved in-repo)

Previously, continuing into reservation completion, **My bookings**, or **Settings** after channel **Rezervă** showed: *Unable to verify your Telegram identity for this session. Reopen the Mini App from Telegram.*

**Cause:** channel HTML used `<a href="https://{mini_app}/tours/{code}">`, which often opens outside Telegram WebApp → no **`initData`** → **`tg_bridge_user_id`** never injected.

## Safety boundary (unchanged)

- Do **not** weaken identity checks or allow booking without verified Telegram identity.
- Do **not** trust query-string user IDs as proof of identity.
- Do **not** change Layer A booking/payment logic.

## What shipped (in-repo)

### Diagnosis (short)

1. **Bot-opened flows:** **`WebAppInfo`** opens the Mini App inside Telegram; **`assets/index.html`** loads **`telegram-web-app.js`**, calls **`Telegram.WebApp.ready()`**, reads **`initData`/`initDataUnsafe.user`**, and injects **`tg_bridge_user_id`** into the URL before **`python.js`** runs; **`MiniAppShell`** resolves runtime identity from query parameters (**no** trusted raw `user_id` from untrusted sources).
2. **Plain HTTPS channel link:** Telegram opened **`https://{mini_app_host}/tours/{code}`** as a **normal in-app browser / external web** view **without** attaching WebApp **`initData`**, so the bridge never saw a user id → user-scoped actions hit **`identity_required_my_data`**.
3. **`initData` in channel-entry case:** **Not** available for plain `<a href="https://...">` showcase links.
4. **`startapp` entry:** Treated as **Telegram WebApp** when the user follows **`https://t.me/{bot}?startapp=tour_{code}`** and the bot’s **Main Mini App** URL points at the Flet deployment.
5. **Code-only vs CTA:** **Not** fixable by parsing alone when **`initData` is absent**; **safe** fix is **CTA + client routing** (Main Mini App launcher + **`start_param`** mapping).

### Implementation

- **`app/services/supplier_offer_deep_link.py`**: **`mini_app_tour_channel_startapp_url`** (`t.me/{bot}?startapp=tour_{tour_code}`) with charset validation aligned with Telegram **`startapp`** rules.
- **`app/services/supplier_offer_showcase_message.py`**: **Rezervă** prefers **`startapp`** when bot username + tour code exist; HTTPS **`mini_app_tour_detail_url`** fallback when **`startapp`** cannot be built (e.g. missing bot username).
- **`app/services/supplier_offer_moderation_service.py`**: **`showcase_preview`** **`cta_rezerva_href`** matches the same **startapp** / HTTPS fallback rules.
- **`assets/index.html`**: **`applyStartParamTourRoute`** — if **`initDataUnsafe.start_param`** is **`tour_{code}`** (**regex-safe** code), **`history.replaceState`** sets **`pathname`** to **`/tours/{code}`** **before** identity bridge + Flet bootstrap.

**Identity rules unchanged:** no new trusted identity sources; no query-string **`user_id`**; Layer A untouched.

### Tests

- **`tests/unit/test_supplier_offer_deep_link.py`**
- **`tests/unit/test_supplier_offer_showcase_ro.py`** (**startapp** + HTTPS fallback)
- **`tests/unit/test_supplier_offer_track3_moderation.py`** (admin preview **href**)

## Operator next steps (production)

- Confirm **BotFather → Bot → Mini App → Main Mini App URL** matches the **same** Flet `/` entrypoint as **`TELEGRAM_MINI_APP_URL`** (path-only routing).
- **Do not** edit historical channel messages; validate on a **new** publish or staging channel.
- Re-smoke: channel **Rezervă** → lands on exact **`/tours/{code}`** **and** **My bookings** / **Settings** / reservation completion work (identity present).

## Related docs

- [`docs/B15C_PRODUCTION_SMOKE_RESULT.md`](B15C_PRODUCTION_SMOKE_RESULT.md) (historical smoke + §8.1 / §10)
- [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md)
- [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (B15C1 bullet)

## Related follow-ups still open (not B15C1)

- **B15C2:** Telegram admin should stay on the current offer after **Leagă tur** and surface **În catalog** (UX).
- **B15C3:** Replace stale copy implying execution links are created **after** showcase publish (docs/copy; B15C ordering is link **before** publish).

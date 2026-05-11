# CURSOR_PROMPT_B15C1_MINI_APP_IDENTITY_FROM_CHANNEL_EXACT_TOUR_ENTRY

Diagnose and fix Mini App identity/session handling when a user enters from a Telegram channel exact-tour CTA.

## Context

B15C is complete and production-smoked.

Relevant commits:

- `37f213e feat: require exact tour CTA before supplier offer publish`
- `18278cf docs: record B15C production smoke result`

B15C production smoke passed:

- Supplier Offer: `#13`
- Tour: `#7`
- Tour code: `B10-SO13-e9f389`
- Execution link: `#6`
- Publish attempt: `#3`
- Telegram showcase message_id: `26`
- Channel `Rezervă` CTA opens:
  - `https://miniappui-production.up.railway.app/tours/B10-SO13-e9f389`

Observed result:

- Exact Mini App tour opens correctly.
- Tour detail shows:
  - `Excursie In Arad`
  - Open For Sale
  - seats available
  - boarding point materialized
- Reservation preparation opens.
- Seat selector and boarding selector are visible.
- Preview summary works.

Problem:

When continuing into user-scoped actions, Mini App shows:

`Unable to verify your Telegram identity for this session. Reopen the Mini App from Telegram.`

Affected surfaces observed:

- reservation creation / final booking action;
- `/bookings`;
- `/settings`.

Important: this is not a B15C exact CTA failure. Exact route opens correctly. The problem is identity/session propagation when entering Mini App from channel exact-tour CTA.

## Required docs to read first

Read:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B15C_PRODUCTION_SMOKE_RESULT.md`
- `docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`
- `docs/MINI_APP_UX.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/AI_ASSISTANT_SPEC.md` only if identity/bot handoff assumptions are referenced.

Also inspect previous identity-related code paths:

- `mini_app/app.py`
- `mini_app/main.py`
- `mini_app/api_client.py`
- `app/api/routes/mini_app.py`
- any identity extraction/session helper used by Mini App
- bot deep-link / WebApp URL generation code
- supplier-offer showcase CTA construction code touched by B15C

## Goal

Determine why Mini App identity is missing when opened from Telegram channel exact-tour CTA and implement the safest minimal fix if possible.

The fix must not weaken identity requirements for user-scoped actions.

## Important architecture rules

Do not bypass identity checks.

Do not allow booking creation without a verified Telegram identity.

Do not create fake customer identity.

Do not move booking/payment logic into UI.

Layer A booking/payment logic must remain unchanged.

Mini App may display public tour detail without identity, but user-scoped actions must require verified identity.

## Investigation requirements

Before coding, produce a concise diagnosis in comments/report:

1. How identity currently reaches Mini App in working bot-opened flows.
2. What happens when opening direct channel URL:
   - `/tours/{tour_code}`
   - `/tours/{tour_code}/preparation`
   - `/bookings`
   - `/settings`
3. Whether Telegram WebApp `initData` is available in this channel-entry case.
4. Whether the current direct URL is treated as:
   - Telegram WebApp context;
   - normal webview/browser context;
   - Flet page route without Telegram init data.
5. Whether this can be fixed in Mini App code alone, or whether the CTA must route through a bot deep-link / Telegram WebApp launcher.

## Preferred solution direction

Prefer a safe identity bridge that preserves exact destination.

Potential acceptable patterns:

### Pattern A — Bot deep-link launcher for authenticated Mini App

Channel CTA may use a Telegram bot deep-link such as:

`https://t.me/tours_tm_bot?start=tour_<tour_code>`

The bot then opens/sends a WebApp button to exact Mini App route:

`/tours/{tour_code}`

This should provide Telegram identity through normal Telegram WebApp entry.

If this is the correct Telegram platform constraint, document it clearly and adjust CTA generation only if safe and already supported.

### Pattern B — Mini App initData extraction hardening

If Telegram init data is present but not parsed, harden extraction in the Mini App client/server path.

Do not invent identity. Only parse verified Telegram-provided identity.

### Pattern C — Public route + authenticated continuation CTA

If channel URL cannot carry identity, keep public tour detail accessible but route user-scoped action through a bot-authenticated re-open flow.

For example:
- direct channel link opens exact public tour;
- clicking “Reserve seats” without identity shows a clear CTA:
  - “Open in Telegram bot to reserve”
  - deep link to bot with exact tour code.

Only implement this if the current architecture already supports a safe route or if the change is small.

## Deliverables

Implement the smallest safe fix or, if platform constraints prevent code-only fix, produce a documented diagnostic and no unsafe workaround.

Required code/docs depending on diagnosis:

### If code fix is implemented

- Add/adjust tests proving:
  1. public exact tour can still open without identity;
  2. user-scoped booking creation still fails without identity;
  3. authenticated bot/Mini App entry still allows reservation flow;
  4. channel exact-tour entry now has a safe path to authenticated reservation;
  5. B15C exact CTA is not regressed.

- Update docs:
  - `docs/B15C_PRODUCTION_SMOKE_RESULT.md`
  - `docs/CHAT_HANDOFF.md`
  - `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

- Create handoff:
  - `docs/HANDOFF_B15C1_MINI_APP_IDENTITY_FROM_CHANNEL_EXACT_TOUR_ENTRY_TO_NEXT_STEP.md`

### If no code fix is safe in this step

Create diagnostic doc:

- `docs/B15C1_MINI_APP_IDENTITY_FROM_CHANNEL_EXACT_TOUR_ENTRY_DIAGNOSTIC.md`

Include:
- root cause;
- platform limitation if applicable;
- recommended safe product path;
- exact next implementation prompt.

Update:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B15C_PRODUCTION_SMOKE_RESULT.md`

Create handoff:
- `docs/HANDOFF_B15C1_MINI_APP_IDENTITY_FROM_CHANNEL_EXACT_TOUR_ENTRY_TO_NEXT_STEP.md`

## Safety constraints

Forbidden:

- No production API calls.
- No production data mutation.
- No Telegram publish/send/retry.
- No execution-link mutation.
- No orders/payments/reservations in production.
- No migrations unless absolutely required and justified before implementation.
- No weakening of identity guards.
- No fallback to arbitrary `dev user` in production.
- No accepting user_id from query string as trusted identity.
- No Layer A booking/payment logic changes.

## Tests

Run focused tests relevant to changed code.

Likely candidates:

```bash
python -m pytest tests/unit/test_api_mini_app.py tests/unit/test_services_mini_app_booking.py -q
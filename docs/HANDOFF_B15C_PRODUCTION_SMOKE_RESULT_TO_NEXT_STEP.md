# HANDOFF_B15C_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP

## Checkpoint

B15C implementation is committed:

- `37f213e feat: require exact tour CTA before supplier offer publish`

## Production smoke result

Production smoke passed for:

- Supplier Offer: `#13`
- Tour: `#7`
- Tour code: `B10-SO13-e9f389`
- Execution link: `#6`
- Publish attempt: `#3`
- Telegram showcase message_id: `26`

Confirmed:

- Channel post was published.
- `Rezervă` opens exact Mini App tour:
  - `/tours/B10-SO13-e9f389`
- Mini App shows exact tour:
  - `Excursie In Arad`
  - `Open For Sale`
  - seats available
  - boarding point materialized
- Reservation preparation opens with seat and boarding selectors.

Conclusion:

B15C exact-tour CTA gate passed.

## Follow-ups

### 1. Mini App identity/session from channel exact-tour entry

When continuing into user-scoped actions, Mini App displayed:

`Unable to verify your Telegram identity for this session. Reopen the Mini App from Telegram.`

This affected reservation creation / bookings / settings. Exact CTA itself is correct; identity/session needs separate diagnosis.

Recommended prompt:

`CURSOR_PROMPT_B15C1_MINI_APP_IDENTITY_FROM_CHANNEL_EXACT_TOUR_ENTRY.md`

### 2. Telegram admin navigation after Leagă tur

After `Leagă tur`, Telegram admin moved to the next offer instead of staying on the current offer and showing `În catalog`.

Recommended prompt:

`CURSOR_PROMPT_B15C2_ADMIN_NAV_STAY_ON_OFFER_AFTER_BRIDGE.md`

### 3. Stale B15C wording

Some copy still says:

`execution links are created after showcase publish`

After B15C this should become:

`create execution link before channel publish`

Recommended prompt:

`CURSOR_PROMPT_B15C3_POST_B15C_COPY_POLISH.md`

## Safety

This handoff is documentation-only. Do not implement fixes here.

## Related

- Full operator evidence (API fields, channel ref, `cta_rezerva_href`, non-goals): **[`docs/B15C_PRODUCTION_SMOKE_RESULT.md`](B15C_PRODUCTION_SMOKE_RESULT.md)**
- B15C gate / checklist: **[`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md)**
- Continuity: **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)** · debt: **[`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md)** (B15 row)
- Smoke recording prompt: **[`docs/CURSOR_PROMPT_B15C_RECORD_PRODUCTION_SMOKE_RESULT.md`](CURSOR_PROMPT_B15C_RECORD_PRODUCTION_SMOKE_RESULT.md)**
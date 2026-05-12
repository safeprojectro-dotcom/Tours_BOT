# CURSOR_PROMPT_B15C2_ADMIN_NAV_STAY_ON_OFFER_AFTER_BRIDGE

## Context

Project: Tours_BOT.

We are continuing after the accepted B15C / B15C1 / B15C5 chain.

Recent accepted checkpoints:
- B15C: exact Tour CTA gate before supplier offer publish.
- B15C1: channel `Rezervă` opens Telegram Mini App correctly via `startapp=tour_<code>`.
- B15C4: cover replacement / text-only showcase safety guard.
- B15C5: direct Mini App short-name link smoke PASS with `https://t.me/tours_tm_bot/banattours?startapp=tour_<code>`.

Production smoke confirmed:
- Supplier offer #15
- Tour #9
- Tour code `B10-SO15-460344`
- Execution link #8
- Publish attempt #6
- Showcase message #28
- `Rezervă` opened exact Mini App tour and allowed reservation/payment entry through existing Layer A.

Important architecture rules:
- Do not change Layer A booking/payment/reservation logic.
- Do not change public customer conversion behavior.
- Do not change Telegram Mini App startapp routing.
- Do not change supplier offer publish rules.
- Do not change execution link semantics.
- This is an admin/operator UX navigation polish only.

## Goal

Implement B15C2: improve admin Telegram navigation after supplier-offer admin actions so the admin stays on the same offer context after actions like:

- `Leagă tur`
- `În catalog`
- similar review/action buttons around the supplier offer publishing console

The desired operator experience:

After an admin action that creates/links/activates catalog state, the bot/admin surface should return to or refresh the same supplier offer review/action panel instead of leaving the admin in a dead-end, unrelated screen, raw success message, or forcing manual re-navigation.

## Required behavior

1. Find the Telegram/admin callback handlers and keyboards related to supplier offer review/package/publishing actions.

2. Identify actions that currently break context after execution, especially:
   - create tour bridge / `Leagă tur`
   - activate tour for catalog / `În catalog`
   - any related supplier-offer review actions that should return to the same offer panel.

3. After successful mutation, show a short success notice and then present the refreshed supplier offer review/action panel for the same `supplier_offer_id`.

4. The refreshed view must reflect the new state:
   - active bridge if created
   - linked tour catalog state
   - catalog activation status
   - execution link availability if relevant
   - publish availability if relevant

5. Do not duplicate business logic in the bot/UI layer:
   - use existing review-package/admin service/read surfaces where possible
   - keep mutation services as the only owners of state changes
   - keep UI as thin as possible

6. Preserve existing confirmation boundaries:
   - dangerous/public actions still require confirmation
   - conversion-enabling actions still require confirmation where already required
   - do not make publish easier or automatic

7. Add/adjust tests if the project already has callback/keyboard tests for these admin flows.
   - If no practical bot callback test harness exists, add focused tests for pure helper functions only.
   - Do not create a huge new test framework.

8. Update docs:
   - `docs/CHAT_HANDOFF.md`
   - `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
   - create handoff doc:
     `docs/HANDOFF_B15C2_ADMIN_NAV_STAY_ON_OFFER_AFTER_BRIDGE_TO_NEXT_STEP.md`

## Non-goals

Do NOT:
- modify Layer A reservation/payment/order logic
- modify Mini App customer routing
- modify startapp logic
- modify BotFather config assumptions
- publish to Telegram
- create or mutate production data
- change execution link rules
- change supplier offer lifecycle rules
- implement B15C3 copy polish unless it is a tiny wording directly touched by this work
- implement B15D/B15E/B15F/B15G

## Before coding

Report briefly:
1. Which files/handlers currently own supplier offer admin callbacks.
2. Which exact callbacks/actions will be adjusted.
3. Whether a shared “refresh offer review panel” helper already exists or should be introduced.
4. What tests are realistic for this slice.

## Implementation guidance

Prefer a small helper such as:

- render/refetch supplier offer review package by offer id
- send or edit admin review message with refreshed buttons
- append a short success line like:
  - `✅ Tur legat. Panoul ofertei a fost actualizat.`
  - `✅ Turul este în catalog. Panoul ofertei a fost actualizat.`

Exact wording can follow existing translation/template conventions.

If the current implementation uses separate routes/messages, preserve the current style and only improve post-action navigation.

## Expected output

After coding, report:

1. Files changed.
2. What admin actions now return to refreshed offer context.
3. Tests run and result.
4. Confirmation that:
   - no Layer A logic changed
   - no public publish behavior changed
   - no Mini App routing changed
   - no production API calls were made
   - no migrations were added unless truly necessary
5. `git status --short`
6. `git diff --stat`
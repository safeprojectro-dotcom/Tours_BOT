Продолжаем ЭТОТ ЖЕ проект Tours_BOT.

Нужен узкий hotfix.
Не трогай Mini App.
Не трогай booking/payment core.
Не открывай новый дизайн.
Не расширяй scope beyond fixing the bot entry from channel deep link.

## Problem
There is a production issue around the Telegram channel -> bot deep link entry.

Observed behavior:
- user clicks the bot link from the channel
- the bot opens with `/start`
- but the intended deep-link flow does not continue automatically
- only after pressing the shown `/start` command manually does the flow proceed

Separately, production logs also showed a crash in the supplier-offer `/start` flow:
- `KeyError: 'title'`
- path: `app/bot/handlers/private_entry.py` -> `handle_start`
- translation key: `start_sup_offer_intro`

This strongly suggests the deep-link/start payload handling for supplier-offer start is not robust enough.

## Goal
Fix the Telegram channel -> bot deep-link start flow so that:
1. the intended `/start <payload>` path is handled correctly when the user opens the bot from the channel link
2. supplier-offer intro does not crash on missing `title`
3. the bot entry is fail-safe and user-friendly

## What to audit
Check the full deep-link entry chain:
- how the channel post constructs the link (`supoffer_<id>` or equivalent)
- how `/start` payload is parsed in private bot handlers
- how `handle_start` branches for supplier offer payloads
- how supplier-offer data is loaded
- how message formatting is done for `start_sup_offer_intro`

## What must be fixed

### 1. Deep-link start payload handling
Ensure that when Telegram opens the bot from the channel link, the bot correctly processes the deep-link payload in the `/start` flow.

The user should not need to manually “activate” a second `/start` click to continue the intended entry path.

### 2. Supplier-offer intro robustness
If `start_sup_offer_intro` expects `{title}`, the rendering path must always supply `title`, or use a safe fallback.
No `KeyError` must be possible from partial/legacy supplier-offer data.

### 3. Graceful fallback behavior
If the supplier offer payload is invalid, missing, stale, or incomplete:
- do not crash
- show a safe fallback message
- route the user into a normal safe browse flow if needed

## Must not change
- Mini App code
- booking/payment logic
- RFQ/bridge logic
- supplier marketplace business model
- publication workflow semantics
- unrelated private bot flows unless strictly needed for the hotfix

## Preferred fix style
- minimal hotfix
- keep current architecture
- fix parsing/branching/rendering at the entry point
- prefer safe fallback over exception
- keep the bot entry thin and service-driven

## Likely files/modules to touch
Only if needed:
- `app/bot/handlers/private_entry.py`
- `app/bot/messages.py`
- any helper used for start/deep-link payload parsing
- possibly the supplier-offer read helper if it fails to provide safe title data
- focused tests for `/start` deep-link handling

## Tests required
Add focused tests only:
1. `/start supoffer_<id>` correctly enters supplier-offer flow
2. supplier-offer intro renders when title exists
3. supplier-offer intro does not crash when title is missing
4. invalid/stale supplier-offer payload falls back safely
5. normal `/start` without payload is not regressed

## Before coding
Output briefly:
1. root cause hypothesis
2. exact files likely to change
3. risks
4. what stays out of scope

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. exact root cause found
6. what behavior is now fixed
7. compatibility notes
8. postponed items

## Extra continuity note
This is only a bot-entry hotfix for channel deep-link `/start`.
It is not permission to redesign supplier-offer conversion or broader bot onboarding.
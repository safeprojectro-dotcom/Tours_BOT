Продолжаем ЭТОТ ЖЕ проект Tours_BOT.

Нужен узкий hotfix.
Не трогай RFQ semantics.
Не трогай bridge/payment core.
Не делай broad redesign.

## Problem
On Mini App custom request form (`/custom-request`), after successful submit:
- the form stays filled
- there is no clear success confirmation
- the user cannot tell whether the request was sent
- repeated clicks can create duplicate requests

This is already confirmed in live behavior:
- POST succeeds
- request appears in `My Requests`
- but the form screen itself remains visually ambiguous

## Goal
Make successful custom request submission explicit and safe.

## Required behavior
1. While submitting:
- disable the submit button
- optionally change button label to a submitting state

2. After successful submit:
- show a clear Romanian success confirmation
- reset/clear the form fields
- make it obvious that the request was sent
- provide a clear CTA to `Cererile mele`

3. Prevent accidental duplicate submission from immediate repeated clicks.

## Preferred UX
After success:
- success message/block/dialog in Romanian
- short explanation:
  - request was sent
  - this is not a reservation/payment
  - track status in `Cererile mele`
- CTA:
  - `Vezi cererile mele`
- optional secondary action:
  - `Trimite altă cerere`
  - or `Înapoi la catalog`

## Important
Do NOT:
- redesign the custom request form broadly
- change request lifecycle semantics
- change API semantics
- change supplier/admin logic
- add fake delivery promises
- add broad navigation redesign

## Likely files
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- focused tests if practical

## Before coding
Output briefly:
1. root cause
2. exact fix approach
3. files likely to change
4. risks
5. what stays out of scope

## Tests required
If practical:
1. submit button cannot be double-fired while request is in progress
2. successful submit clears form state
3. success confirmation is shown
4. CTA to `My Requests` is available
5. no request lifecycle semantics are changed

## After coding
Report exactly:
1. files changed
2. migrations none
3. tests run
4. results
5. what user-visible behavior changed
6. compatibility notes
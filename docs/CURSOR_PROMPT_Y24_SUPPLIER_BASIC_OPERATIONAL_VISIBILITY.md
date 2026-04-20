Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2.3 supplier moderation/publication workspace implemented
- Y2.1a supplier legal/compliance hardening implemented
- updated `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment core semantics.
Не менять RFQ/bridge execution semantics.
Не менять payment-entry/reconciliation semantics.
Не делать broad supplier/admin portal redesign.

## Goal
Implement a narrow supplier read-side operational visibility slice.

Supplier should be able to see basic operational progress for their own published offers, without exposing customer PII or creating booking/payment control capabilities.

## Why this step
Supplier onboarding exists.
Supplier offer intake exists.
Moderation/publication exists.
Supplier notifications exist.

The next missing operational piece is: supplier needs limited visibility into how their published offers are performing.

## Exact scope
Add a narrow supplier read-side view in Telegram for supplier-owned offers showing only safe aggregate operational signals.

Preferred entry:
- extend existing `/supplier_offers`
or
- another very narrow supplier read-only command if clearly safer

But avoid broad UX redesign.

## What supplier should see
For each supplier-owned offer, when safe and derivable:
- offer status
- whether offer is published
- basic aggregate capacity/progress indicators
- examples:
  - seats_total / declared capacity
  - sold/confirmed seats count
  - reserved/temporary hold count
  - remaining seats
  - load/progress hint

Only if mapping from supplier offer to operational object is already safe and grounded.

## What supplier must NOT see
Do NOT expose:
- customer names
- Telegram IDs
- phone numbers
- payment rows
- payment provider details
- admin-only moderation internals beyond already-allowed status/reason signals
- RFQ/customer-request sensitive data outside already allowed supplier domain

## Important architecture rule
Reuse existing source-of-truth read paths.
Do not invent parallel booking math in Telegram bot layer.
If safe aggregate visibility cannot be derived cleanly for some offer states, return a narrow “not yet available” style signal rather than inventing data.

## Safe scope boundaries
- no new booking mutations
- no payment actions
- no publication redesign
- no analytics dashboard
- no charts/reporting suite
- no customer list view
- no finance metrics
- no RFQ redesign
- no Mode 2 / Mode 3 merge

## Preferred behavior
For supplier-owned offers:
- draft / ready_for_moderation / approved but unpublished: show lifecycle status only
- published offers: show aggregate operational visibility if derivable
- rejected: show rejected + existing reason path if already supported

## Likely files
Likely:
- supplier read service / moderation read service
- supplier Telegram workspace handler
- bot messages
- focused tests

Avoid touching unrelated files.

## Before coding
Output briefly:
1. current project state
2. why this is the next safe step
3. exact metrics/signals proposed
4. likely files to change
5. risks
6. what remains postponed

## Implementation guidance
- prefer additive read-side only
- keep copy concise and supplier-friendly
- if some metrics are ambiguous, expose only the unambiguous subset
- if offer-to-live-tour linkage is partial, document the fallback behavior in code comments/tests

## Required tests
Add focused tests for:
1. supplier sees own offers only
2. unpublished offers do not pretend to have live operational stats
3. published offers expose only safe aggregate metrics
4. no customer PII leaks
5. no booking/payment semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier can now see
6. what remains intentionally hidden
7. compatibility notes
8. postponed items

## Important note
This is a narrow read-side visibility step only.
Do not silently expand into dashboards, finance, booking controls, customer lists, or RFQ redesign.
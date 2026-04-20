Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2 design gate accepted
- Y2.1 supplier onboarding live-verified
- Y2.2 supplier Telegram offer intake live-verified
- Y2.2a supplier offer intake polish/navigation/validation live-smoke verified
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment core.
Не менять RFQ/bridge execution semantics.
Не менять payment-entry/reconciliation semantics.
Не смешивать Mode 2 и Mode 3.
Не делать broad supplier/admin portal rewrite.

## Continuity base
Use as source of truth:
- current codebase
- `docs/CHAT_HANDOFF.md`
- `docs/SUPPLIER_TELEGRAM_OPERATING_MODEL_Y2.md`

Already true:
- supplier onboarding exists
- approved supplier can create supplier offer drafts in Telegram
- supplier can submit draft to `ready_for_moderation`
- moderation/publication lifecycle already exists in supplier offer domain
- Telegram channel publication path already exists in earlier supplier offer publication logic
- moderation boundary must remain intact

## Product decision now accepted
For this project:
- `approve` does NOT automatically mean `publish`
- `approve` means the offer passed moderation and is eligible for publication
- `publish` is a separate admin action
- `reject` must include a supplier-visible reason
- later `unpublish/retract` must exist as a narrow operational action

Reasoning:
- admin may need timing control
- admin may need to correct content before publishing
- admin may need to hide/retract a published offer later
- moderation decision and channel delivery should stay separable

# Exact step
## Y2.3 — Supplier/admin moderation and publication workspace (narrow ops path)

## Goals
Build a narrow operational path so:
1. supplier can see own submitted offers and statuses
2. admin can review moderation-ready offers more clearly
3. admin can:
   - approve
   - reject with reason
   - publish approved offers
   - unpublish/retract published offers
4. supplier gets clear bot notifications for:
   - approved
   - rejected with reason
   - published
   - unpublished/retracted (if included in this step)

This is not a broad admin portal rewrite.
This is not analytics/dashboard.
This is not a full supplier management platform.

## What this step must implement

### 1. Supplier read-side workspace (narrow)
Supplier must be able to view own offers and their statuses in a narrow read-side way.

Minimum useful statuses:
- draft
- ready_for_moderation
- approved
- rejected
- published

Keep it narrow:
- list of own offers
- short summary
- status
- maybe updated time / reference
- no customer PII
- no booking/payment control
- no RFQ merge

Telegram-first entry is acceptable if that fits current architecture better than building a new UI surface.

### 2. Reject with reason
Admin reject must include a reason that can be shown back to supplier safely.

Requirements:
- reject reason stored in existing domain if possible
- supplier gets notification in Telegram
- supplier-facing copy should be clear and operational
- reason should help supplier fix and resubmit later

Do not create a huge dispute workflow.

### 3. Approve as separate from publish
Admin approve should:
- move offer into approved state
- not publish automatically
- preserve ability to publish later

Supplier should get notification that:
- offer was approved
- publication may happen separately / later

Use concise operational copy.

### 4. Publish action
Admin publish should:
- work only for approved offers
- use the existing Telegram channel publication path
- move offer into published state
- notify supplier that offer is now published

Preserve existing publication/moderation boundaries.

### 5. Unpublish / retract action
Add a narrow admin action to remove/hide a previously published offer from active customer-facing publication state.

Goal:
- operator safety if something was published by mistake
- timing/control flexibility
- allow later correction

This step should be narrow and operational.
Do not build a huge publication management suite.

Decide the safest minimal semantics:
- whether this removes only future visibility
- whether it preserves historical publication record
- whether channel post deletion/edit is supported now or only customer-facing state is withdrawn

Prefer the narrowest honest implementation and document limitations clearly.

### 6. Supplier notifications
Supplier should get Telegram notifications for relevant moderation/publication state changes:
- approved
- rejected (with reason)
- published
- unpublished/retracted if included

Keep messages concise and factual.

## What this step must NOT do
Do NOT:
- redesign supplier onboarding legal/compliance block
- redesign Layer A booking/payment semantics
- redesign RFQ supplier flow
- create full supplier dashboard analytics
- add customer PII visibility to supplier
- create broad admin SPA rewrite
- collapse approve and publish into one action
- create a second supplier-offer lifecycle model

## Architecture guardrails
- reuse existing supplier offer domain and lifecycle
- keep moderation and publication separate
- keep Telegram notifications thin and service-driven
- preserve separation between supplier offers and custom requests/RFQ
- keep route/handler layers thin

## Likely files to touch
Likely:
- supplier offer moderation/publication services/routes already in place
- narrow supplier read-side service/schemas/routes if needed
- Telegram bot notifications/messages
- maybe a narrow supplier list/detail bot flow or small read-side surface
- focused tests

Avoid touching unless strictly needed:
- Layer A reservation/payment services
- RFQ/bridge services
- broad Mini App booking/payment UI
- broad admin rewrite

## Before coding
Output briefly:
1. current state
2. accepted approve vs publish decision
3. exact Y2.3 goal
4. likely files to change
5. risks
6. what remains postponed

## Suggested implementation order
1. inspect current supplier offer lifecycle + publication path
2. define reject-reason persistence/reuse
3. add supplier-facing read-side listing of own offers
4. add/reuse admin approve as approval-only
5. add/reuse admin reject with reason
6. add/reuse publish action
7. add narrow unpublish/retract action
8. add supplier Telegram notifications
9. add focused tests

## Required focused tests
Add focused tests for:
1. supplier can view own offers/statuses
2. reject stores and exposes supplier-safe reason
3. approve does not auto-publish
4. publish works only from approved
5. published offer can be retracted/unpublished via narrow admin action
6. supplier receives correct notifications
7. no booking/payment/RFQ semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier-facing behavior now works
6. what admin-facing moderation/publication behavior now works
7. retract/unpublish limitations if any
8. compatibility notes
9. postponed items

## Important note
This step is a narrow moderation/publication workspace step.
Do not silently expand into supplier analytics, legal compliance redesign, RFQ redesign, or broad admin/supplier platform architecture.
Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- `docs/SUPPLIER_ADMIN_MODERATION_AND_STATUS_POLICY_DESIGN.md` accepted
- current `docs/CHAT_HANDOFF.md`
- supplier onboarding/approval flow already exists
- supplier offer moderation/publication flow already exists

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не смешивать supplier profile lifecycle с supplier offer lifecycle.
Не делать Telegram admin workspace в этом шаге.

## Goal
Implement the additive supplier profile status model needed for future supplier governance.

## Accepted design truth
Supplier profile lifecycle should support:
- `pending_review`
- `approved`
- `rejected`
- `suspended`
- `revoked`

`reactivate` is an admin action that returns supplier profile to `approved`.

This step is only about supplier profile status truth/model/service/API support.
Do NOT implement Telegram admin supplier workspace yet.

## Exact scope

### 1. Additive status model
Extend supplier profile status model to support:
- suspended
- revoked

Preserve existing statuses and backward compatibility.

### 2. Supplier reasons / admin rationale
Add narrow support for admin reason fields where needed for:
- reject reason
- suspend reason
- revoke reason

Keep it additive and narrow.
Do not overbuild audit/history subsystem in this step.

### 3. Service-layer status transitions
Implement safe supplier profile transitions in service layer:
- pending_review -> approved
- pending_review -> rejected
- approved -> suspended
- suspended -> approved (reactivate)
- approved -> revoked
- suspended -> revoked if design allows
- explicitly reject invalid transitions

Keep this supplier-profile-only.

### 4. Admin API support
Add or extend narrow admin endpoints/actions for supplier profile governance, such as:
- suspend
- reactivate
- revoke

Reuse existing admin auth model.
Do not implement Telegram handlers here.

### 5. Backward compatibility
Keep current legacy approved suppliers working.
Do not break existing supplier onboarding/approval flow.

### 6. No offer-side cascading yet
Do NOT implement automatic offer retract/blocking policy in this step.
That belongs to later gating/policy steps.

## What this step must NOT do
Do NOT:
- implement Telegram admin supplier workspace
- implement supplier back/home navigation
- implement offer visibility cascading
- retract supplier offers automatically
- redesign supplier onboarding fields
- redesign Layer A / RFQ / payment semantics
- merge supplier status transitions with offer moderation lifecycle

## Likely files
Likely:
- `app/models/enums.py`
- `app/models/supplier.py`
- `app/schemas/admin.py` or supplier-admin schema files
- `app/services/supplier_onboarding_service.py` or a supplier governance service
- `app/api/routes/admin.py`
- migration file
- focused unit tests

Avoid unrelated files.

## Before coding
Output briefly:
1. current state
2. why Y29.2 is the next safe step
3. likely files to change
4. risks
5. what remains postponed

## Required tests
Add/update focused tests for:
1. legacy approve/reject still works
2. approved -> suspended works
3. suspended -> approved (reactivate) works
4. approved -> revoked works
5. invalid transitions are rejected
6. legacy approved suppliers remain compatible

## After coding
Report exactly:
1. files changed
2. migrations added
3. tests run
4. results
5. what admin/profile truth can now do
6. what remains postponed
7. compatibility notes

## Important note
This is supplier profile status truth only.
Do not implement Telegram admin supplier moderation workspace in this step.
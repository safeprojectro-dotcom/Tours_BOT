# CURSOR_PROMPT_B16E_OPS_AUDIT_VISIBILITY_CODE_FIRST

## Context

Project: Tours_BOT.

Current clean checkpoint:
- `a3e435 feat: add prepare conversion chain readiness summary`
- `e74f505 feat: expose prepare conversion chain plan paths`
- `d5d9e8a feat: add prepare conversion chain plan preview`
- `c27044 feat: add ops dashboard navigation paths`
- `a3f100 feat: add ops dashboard filters and limits`
- `b0f11e2 docs: design guarded ops automation`

B16 currently has:
- `GET /admin/ops-dashboard`
- filters / limits / include_sections
- admin navigation paths
- prepare_conversion_chain plan path
- prepare_conversion_chain readiness summary/status
- all read-only

B15/B16 boundaries:
- no Telegram send/publish/retry from dashboard
- no order/payment/reservation/seat mutation
- no Layer A changes
- no Mini App routing changes
- no auto-publish
- no action execution

## Goal

Implement B16E as a code-first read-only visibility extension for OPS/audit signals.

The operator should be able to see recent operational/audit events related to:

- recent showcase publish attempts
- failed showcase publish attempts
- supplier execution requests/attempts if existing models are available
- notification/outbox failures if existing read models are available
- payment/order attention remains existing dashboard responsibility

Keep the scope small and read-only.

## Preferred implementation

Extend existing `GET /admin/ops-dashboard` with one new optional section:

```text
audit_events
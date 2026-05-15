# CURSOR_PROMPT_B16D2B_PREPARE_CONVERSION_CHAIN_SERVICE_EXECUTION

## Context

Project: Tours_BOT.

Current clean checkpoint:
- `77f1b0d feat: add guarded action audit foundation`
- `3057ba8 docs: design prepare conversion chain execution`
- `e301088 feat: add ops dashboard audit visibility`
- `a3e435 feat: add prepare conversion chain readiness summary`
- `e74f505 feat: expose prepare conversion chain plan paths`
- `d5d9e8a feat: add prepare conversion chain plan preview`

B16D2A is complete and Railway migration was applied:
- `admin_guarded_action_attempts`
- `admin_guarded_action_steps`
- unique idempotency:
  `(action_code, source_entity_type, source_entity_id, idempotency_key)`
- service:
  `app/services/admin_guarded_action_audit_service.py`
- tests:
  `tests/unit/test_admin_guarded_action_audit.py`

Production DB migration already applied:
- `20260609_30 (head)`

B16D2 design gate says the future endpoint will be:

`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`

But this prompt is B16D2B only.

## Goal

Implement the service-level execution for `prepare_conversion_chain`.

Do NOT add the HTTP endpoint yet.

Create a service that can be called later by the POST route, but for now is tested directly at service level.

Future action chain:

1. ensure tour bridge
2. activate tour for catalog
3. ensure active execution link

## Hard boundaries

Do NOT:
- add `POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`
- add any new admin route
- publish to Telegram
- send Telegram messages
- retry publish
- create showcase publish attempts
- mutate orders
- mutate payments
- mutate reservations
- change seats directly
- call Layer A booking/payment services
- change Mini App routing
- create supplier execution attempts
- create notification outbox rows

Allowed mutation:
- audit/idempotency rows from B16D2A
- existing supplier-offer → tour bridge creation through existing service only
- existing catalog activation through existing admin service only
- existing execution link creation through existing service only

No hidden publish.

## Service to create

Create:

`app/services/prepare_conversion_chain_execution_service.py`

or similar project-style name.

Suggested public method:

```python
execute(
    session: Session,
    *,
    supplier_offer_id: int,
    idempotency_key: str,
    confirm: bool,
    actor_surface: str = "service",
    requested_by: str | None = None,
    dry_run: bool = False,
) -> AdminPrepareConversionChainExecutionResultRead
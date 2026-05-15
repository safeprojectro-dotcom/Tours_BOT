# HANDOFF_B16D2C_PREPARE_CONVERSION_CHAIN_API_ENDPOINT

## Project
Tours_BOT

## Block
B16D2C — API Execution Endpoint

## Status
**Closed (implemented).** Continuity: **`docs/CHAT_HANDOFF.md`** · parent design handoff **`docs/HANDOFF_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE_TO_NEXT_STEP.md`**.

## Goal
Expose the already implemented service-level prepare_conversion_chain execution through a guarded central-admin API endpoint:

POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain

## Foundation (B16D2A + B16D2B)
- `admin_guarded_action_attempts` / `admin_guarded_action_steps`
- idempotency uniqueness:
  `(action_code, source_entity_type, source_entity_id, idempotency_key)`
- `PrepareConversionChainExecutionService.execute(...)`
- `dry_run`, `partial_success`, idempotent replay (succeeded / partial_success / failed), step-level audit

Alembic (B16D2A): **`alembic/versions/20260609_30_admin_guarded_action_audit.py`** — apply on new envs with `python -m alembic upgrade head` (Railway was already at this revision when B16D2A shipped).

## Delivered (B16D2C)
- **Route:** `POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain` — **`app/api/routes/admin.py`** (`post_admin_supplier_offer_prepare_conversion_chain`). Thin wrapper only; **`actor_surface="admin_http"`**.
- **Request body:** **`AdminPrepareConversionChainExecuteBody`** — **`app/schemas/admin_prepare_conversion_chain_plan.py`** (`idempotency_key` required non-blank after trim; **`confirm=true`** required for live unless **`dry_run=true`**).
- **Response:** **`AdminPrepareConversionChainExecutionResultRead`** (same as service).
- **Auth:** existing **`require_admin_api_token`** on `/admin` router.
- **Errors:** e.g. missing offer **404**; live without confirm **422**; conflicting running idempotency **409**; other mapped **`ValueError`** → **422** where applicable.
- **Tests:** **`tests/unit/test_admin_prepare_conversion_chain_api.py`**.
- **Docs:** **`docs/CHAT_HANDOFF.md`** (B16D2C bullet); design handoff status line updated.

## What B16D2C must not do
- no dashboard button
- no publishing console action execution
- no Telegram publish/send/retry
- no channel post
- no scheduler
- no auto-publish
- no Mini App routing changes
- no B11 deep-link changes
- no order/payment/reservation mutation
- no Layer A booking/payment changes
- no migration

## Verification
Run at minimum:
- `python -m compileall app tests`
- `python -m pytest tests/unit/test_prepare_conversion_chain_execution_service.py -q`
- `python -m pytest tests/unit/test_admin_prepare_conversion_chain_api.py -q`
- `python -m pytest tests/unit/test_admin_prepare_conversion_chain_plan.py tests/unit/test_admin_guarded_action_audit.py -q`

Regression spot-check (optional): `test_admin_ops_dashboard`, `test_admin_publishing_console`.

## Next block after B16D2C
B16D2D — Read Model / Action Affordance Integration

Goal:
Expose action metadata/read affordances in:
- review package
- publishing console
- ops dashboard
- operator workflow if appropriate

Still no Telegram publish/send/retry.
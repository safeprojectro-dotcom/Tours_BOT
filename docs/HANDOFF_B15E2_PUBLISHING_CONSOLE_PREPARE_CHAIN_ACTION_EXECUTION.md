# HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION

## Project
Tours_BOT

## Block
B15E2 — Publishing console **execution** entry for **`prepare_conversion_chain`**

## Status
**Implemented.** Parent foundation checkpoint: **[`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md)** · **`GET /admin/publishing-console`** remains read-only · execution is a **separate POST**.

## Endpoint

**`POST /admin/publishing-console/supplier-offers/{offer_id}/prepare-conversion-chain`**

- **Auth:** same as all `/admin` routes (`Authorization: Bearer` or `X-Admin-Token`).
- **Body:** **`AdminPrepareConversionChainExecuteBody`** — **`idempotency_key`** (required), **`confirm`**, **`dry_run`** (same rules as B16D2C).
- **Response:** **`AdminPrepareConversionChainExecutionResultRead`** · **`actor_surface`** = **`publishing_console`**.

## Implementation

- **`app/api/routes/admin.py`**: shared **`_handle_prepare_conversion_chain_post`** used by **B16D2C** (`actor_surface=admin_http`) and **B15E2** (`actor_surface=publishing_console`).
- **Delegates only to** **`PrepareConversionChainExecutionService.execute`** — no Telegram, no publish service, no Layer A booking/payment mutation.

## Tests

**`tests/unit/test_admin_publishing_console_prepare_chain_action.py`**

Regression: **`test_admin_prepare_conversion_chain_api`**, **`test_admin_publishing_console`**, **`test_prepare_conversion_chain_execution_service`**, **`test_prepare_conversion_chain_d2d_affordance`**.

## Boundaries

Not in scope: generic action framework, **`POST …/publish`**, Mini App / B11 changes, new migrations.

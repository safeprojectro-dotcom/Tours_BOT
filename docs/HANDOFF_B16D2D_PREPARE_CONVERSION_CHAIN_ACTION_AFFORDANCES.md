# HANDOFF_B16D2D_PREPARE_CONVERSION_CHAIN_ACTION_AFFORDANCES

## Project
Tours_BOT

## Block
B16D2D — Read model / action affordance integration for **`prepare_conversion_chain`**

## Status
**Closed (implemented).** Continuity: **`docs/CHAT_HANDOFF.md`** · execution endpoint handoff **`docs/HANDOFF_B16D2C_PREPARE_CONVERSION_CHAIN_API_ENDPOINT.md`**.

## Goal
Expose read-only metadata so admin/read surfaces know the guarded **`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`** (B16D2C) exists, when it may be proposed, and what the HTTP contract requires.

## Delivered
- **Schema:** **`PrepareConversionChainActionAffordanceRead`** — **`app/schemas/admin_prepare_conversion_chain_plan.py`**
- **Logic:** **`derive_prepare_conversion_chain_action_affordance`**, **`append_prepare_conversion_chain_operator_action`** — **`app/services/prepare_conversion_chain_readiness.py`**
- **Navigation:** **`supplier_offer_prepare_conversion_chain_execute_path`** — **`app/services/admin_navigation_paths.py`**
- **Surfaces:**
  - **`GET …/review-package`** — field **`prepare_conversion_chain_action`**; **`operator_workflow.actions`** gains a read-only **`prepare_conversion_chain`** row (**`POST`**, **`conversion_enabling`**).
  - **`GET …/publishing-console`** — supplier-offer rows: **`prepare_conversion_chain_action`** (tour-promotion rows: **`null`**).
  - **`GET …/ops-dashboard`** — **`recent_publications`**, **`conversion_links`**, supplier-offer-scoped **`attention_items`**: **`prepare_conversion_chain_action`** where **`review-package`** is loaded.
- **Strict:** no calls to **`PrepareConversionChainExecutionService`** from read paths; no new audit rows from GETs.

## Enabled / disabled
- **`partial`** or **`already_prepared`** → **`enabled=true`**
- **`ineligible`** or **`blocked`** → **`enabled=false`** with **`disabled_reason`**

## Verification
- `python -m compileall app tests`
- `python -m pytest tests/unit/test_prepare_conversion_chain_d2d_affordance.py -q`
- `python -m pytest tests/unit/test_supplier_offer_review_package.py tests/unit/test_admin_publishing_console.py tests/unit/test_admin_ops_dashboard.py tests/unit/test_admin_prepare_conversion_chain_api.py -q`

## Next (out of scope for B16D2D)
Optional: richer publishing-console / Telegram UX that **calls** B16D2C POST only behind explicit product gates — not implemented here.

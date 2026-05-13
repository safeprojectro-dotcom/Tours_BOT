# CURSOR_PROMPT_B16D1_FIX_ADMIN_OPS_DASHBOARD_REGRESSION

## Context

B16D1 implementation added:

- GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan
- app/schemas/admin_prepare_conversion_chain_plan.py
- app/services/admin_prepare_conversion_chain_plan_service.py
- tests/unit/test_admin_prepare_conversion_chain_plan.py

Focused B16D1 tests passed with:

python -m pytest tests/unit/test_admin_prepare_conversion_chain_plan.py tests/unit/test_supplier_offer_review_package.py -q
→ 12 passed

But regression failed:

python -m pytest tests/unit/test_admin_publishing_console.py tests/unit/test_admin_ops_dashboard.py -q

Failure:

NameError: name 'AdminOpsDashboardService' is not defined
app/api/routes/admin.py:253

This indicates the B16D1 route/import change likely broke the existing /admin/ops-dashboard handler.

## Goal

Fix only the regression.

Restore AdminOpsDashboardService availability in app/api/routes/admin.py without changing B16D1 behavior.

## Required work

1. Inspect `app/api/routes/admin.py`.
2. Find why `AdminOpsDashboardService` is not defined.
3. Restore the correct import or reference.
4. Keep the existing B16D1 plan endpoint unchanged unless required for import organization.
5. Do not refactor unrelated admin routes.
6. Do not change business behavior.

## Safety

Do NOT:
- create bridge
- activate catalog
- create execution link
- publish/send Telegram
- mutate orders/payments/reservations/seats
- change Layer A
- change Mini App routing
- add migrations

## Tests to run

Run exact commands:

```powershell
python -m pytest tests/unit/test_admin_prepare_conversion_chain_plan.py tests/unit/test_supplier_offer_review_package.py -q
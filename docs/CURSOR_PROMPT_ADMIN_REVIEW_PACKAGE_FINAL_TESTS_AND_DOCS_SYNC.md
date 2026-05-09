# CURSOR_PROMPT_ADMIN_REVIEW_PACKAGE_FINAL_TESTS_AND_DOCS_SYNC

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Это final verification + docs sync для блока:

ADMIN OFFER REVIEW & APPROVAL GATE — Slice 1

Не менять бизнес-логику.
Не менять endpoint contract без необходимости.
Не менять booking/payment/order/reservation.
Не менять Mini App UI.
Не менять publish/bridge/catalog activation behavior.

## Current implemented endpoint

GET /admin/supplier-offers/{offer_id}/review-package

It is read-only and aggregates:

- offer raw/admin snapshot
- packaging status
- showcase preview
- bridge readiness
- active bridge / linked Tour
- catalog activation readiness
- execution-link readiness
- Mini App conversion preview
- warnings
- recommended_next_actions

## Required final checks

Run and report:

```bash
python -m pytest tests/unit/test_supplier_offer_review_package.py -v
python -m pytest tests/unit/test_supplier_offer_tour_bridge_b10.py -v
python -m pytest tests/unit/test_supplier_offer_track3_moderation.py -v
python -m pytest tests/unit/test_supplier_offer_showcase_ro.py -v
python -m compileall app alembic -q

Create docs-only acceptance checkpoint after Y37.5.

Update:
- docs/CHAT_HANDOFF.md
- optionally docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Record accepted state:
- Y37.4 first operator intent need_manual_followup is live.
- Y37.5 added second intent need_supplier_offer.
- Migration 20260501_20 applied.
- Telegram UI shows readable labels:
  - Need manual follow-up
  - Need supplier offer
- Raw enum display bug fixed for NEED_SUPPLIER_OFFER.
- Operator intent remains internal admin/ops only.
- No supplier action, RFQ, bridge, booking, payment, Mini App, customer notification, execution-link, or identity bridge side effects.
- Tests:
  - AdminRouteTests::test_admin_custom_request_operator_decision
  - full tests/unit/test_telegram_admin_moderation_y281.py -> 54 passed

Next safe pointer:
- Before supplier/RFQ/bridge implementation, create a separate Y38 supplier-intent handoff/design gate.
- Do not let need_supplier_offer automatically contact suppliers yet.

No runtime code changes.
No migrations.
No tests changes.
Stop and report docs-only files changed.
# HANDOFF_B9_SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md

B9 — Supplier Offer → Tour Bridge Design is completed.

Current state:
- B1–B4.3: supplier offer intake, packaging, marketing formatting, and truth rules are in place.
- B5: admin packaging review is in place; `approved_for_publish` does not publish.
- B6: branded Telegram preview JSON exists.
- B7.1: media visual review metadata exists.
- B7.2: card render preview plan exists.
- Supplier Offer still does not automatically become a Tour.

B9 decision:
Supplier Offer is the source/raw commercial proposal.
Tour is the customer-facing sellable catalog object.
Bridge is an explicit admin-controlled action that creates or links a Tour from an approved Supplier Offer.

Core bridge rules:
- No silent ORM trigger.
- No AI-created Tour.
- No supplier bypass.
- No automatic Telegram publish.
- No booking/payment changes.
- No recurring generation in this step.
- No media download/storage in this step.

Required preconditions for B10:
- `packaging_status = approved_for_publish`
- required supplier offer fields exist: title, route/description, departure/return or recurrence policy, price, currency, sales_mode, capacity/vehicle, program, included/excluded
- quality warnings accepted or resolved
- media may remain optional but must be flagged if not publish-safe

Recommended MVP implementation:
- Add explicit bridge persistence:
  - bridge table preferred over silent `tour_id` only
  - one active bridge per supplier offer
  - idempotent create/link behavior
- Admin API creates/links Tour from Supplier Offer.
- Repeated call returns existing bridge/Tour, not duplicate Tour.
- New Tour starts in the safest status defined by design, preferably `draft` unless explicitly opened by admin policy.
- `full_bus` must not accidentally become per-seat self-service.

Next safe step:
B10 — Supplier Offer → Tour Bridge Implementation.

B10 should include:
- migration for bridge table or explicit link field
- admin POST create/link bridge endpoint
- admin/read bridge status
- data mapping from supplier_offer to Tour
- idempotency tests
- no Telegram publish
- no payment/booking changes
- no Mini App UI redesign
- smoke: approved offer #8 → bridge created → Tour linked/created → catalog visibility only if status policy allows.
BUSINESS baseline + B1 are completed.

Source of truth:
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Accepted business rule:
Published supplier offer should become or attach to a Tour in the Mini App catalog through an explicit bridge.

Supplier provides raw facts.
AI creates draft packaging.
Admin reviews/edits/approves.
Only approved package can be published.

AI is draft-only:
- no invented dates/prices/seats
- no publishing
- no booking/order/payment
- no silent Tour creation

Next safe step:
B2 — Supplier Offer Content/Data Upgrade.
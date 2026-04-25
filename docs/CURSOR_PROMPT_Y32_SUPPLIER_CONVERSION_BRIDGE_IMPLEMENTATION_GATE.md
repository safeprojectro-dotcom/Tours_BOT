Continue Tours_BOT strict continuation.

Task:
Create a supplier conversion bridge implementation gate.

Read first:
- docs/CHAT_HANDOFF.md
- docs/DESIGN_1_SUPPLIER_MARKETPLACE_ARCHITECTURE_CHECKPOINT.md
- docs/PHASE_7_1_SALES_MODE_FULL_BUS_REVIEW_GATE.md
- docs/PHASE_7_1_ACTIONABILITY_MATRIX.md
- docs/SUPPLIER_OFFER_EXECUTION_LINKAGE_DESIGN.md
- docs/SUPPLIER_OFFER_MINI_APP_CONVERSION_BRIDGE_DESIGN.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Goal:
Define the next safe implementation slice for Supplier Offer → Conversion Bridge.

Rules:
- Do not change runtime code in this step.
- Do not merge supplier_offer and tour.
- Do not alter Layer A booking/payment.
- Do not change RFQ semantics.
- Preserve visibility != bookability.
- Mini App execution truth wins.
- Direct booking CTA only if active authoritative execution link exists.

Create:
docs/SUPPLIER_CONVERSION_BRIDGE_IMPLEMENTATION_GATE.md

Document:
1. Current state
2. Existing entities and assumed tables
3. What is already implemented
4. What is missing
5. Safe first implementation slice
6. Explicit out-of-scope items
7. Tests required before runtime change
8. Rollback/fail-safe behavior

Update:
docs/CHAT_HANDOFF.md

No runtime code.
No migrations.
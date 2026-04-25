Continue Tours_BOT strict continuation.

Task:
Create a design gate for operator/admin workflow to create, replace, and close supplier_offer_execution_links.

Read first:
- docs/CHAT_HANDOFF.md
- docs/SUPPLIER_CONVERSION_BRIDGE_IMPLEMENTATION_GATE.md
- docs/DESIGN_1_SUPPLIER_MARKETPLACE_ARCHITECTURE_CHECKPOINT.md
- docs/SUPPLIER_OFFER_EXECUTION_LINKAGE_DESIGN.md

Goal:
Define safe operator/admin workflow for managing authoritative execution links between supplier_offers and tours.

Rules:
- Do not change runtime code.
- Do not add migrations.
- Do not auto-create tours.
- Do not merge supplier_offer and tour.
- Do not change Layer A booking/payment.
- Direct booking CTA must remain enabled only through active authoritative link.

Create:
docs/OPERATOR_EXECUTION_LINK_WORKFLOW_GATE.md

Document:
1. Current state
2. Required operator actions:
   - create link
   - replace link
   - close link
   - view link history
3. Required validations
4. Fail-safe behavior
5. Admin permissions/security
6. Audit/history requirements
7. What remains postponed
8. First safe implementation slice

Update:
docs/CHAT_HANDOFF.md

Docs only.
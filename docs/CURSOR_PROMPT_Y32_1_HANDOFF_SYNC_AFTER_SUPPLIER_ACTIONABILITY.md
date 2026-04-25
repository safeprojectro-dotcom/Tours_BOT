Continue Tours_BOT strict continuation.

Task:
Docs-only handoff sync after Y32.1 Supplier Conversion Bridge read-side actionability implementation.

Accepted result:
- Supplier offer landing/read-side resolver now exposes:
  - actionability_state
  - has_execution_link
  - linked_tour_id / linked_tour_code where safe
  - execution_cta_enabled
  - fallback_cta
- Direct booking CTA is enabled only when:
  - supplier offer has active authoritative execution link
  - linked tour is bookable by execution/sales_mode policy
- No active link -> view_only / browse_catalog fallback
- full_bus partial -> assisted_only, no execution CTA
- sold out / invalid linked tour -> no false booking CTA
- execution_activation_available remains backward-compatible alias of execution_cta_enabled

Confirm guardrails:
- no auto-create tour
- supplier_offer != tour
- no Layer A booking/payment changes
- no RFQ changes
- no identity bridge changes
- no coupons/incidents/admin workflows

Update docs only:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if needed

Next safe options:
1. Operator/admin workflow for creating/replacing/closing execution links
2. Admin operational visibility for bookings/requests
3. Incident/disruption design gate
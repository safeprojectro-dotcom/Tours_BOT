# Design 1 Supplier Marketplace Architecture Checkpoint

## Status
- Intermediate architecture checkpoint before next execution tracks.
- Scope: documentation only; no runtime/code/schema changes in this checkpoint.

## 1) Accepted State After Mini App Identity Stabilization
- Mini App identity bridge is stable in production (`has_identity=True`, `source=route_query_user_id`).
- User-scoped Mini App surfaces are working for the same Telegram user context:
  - `My bookings`
  - `My requests`
  - `Settings`
  - custom request creation
  - reservation/payment flow (including payment-entry and mock completion path)
- Fail-closed privacy behavior is preserved when identity is absent.

## 2) Design 1 Principles
- **Supplier Offer** remains a supplier-side commercial artifact, not a direct Layer A executable order object.
- **Public Showcase** is intentionally softer: visibility and discovery, not execution authority.
- **Conversion Bridge** is the controlled path from supplier/public context to executable customer path.
- **Execution Truth** is strict and current in Mini App/backend runtime surfaces.
- **`visibility != bookability`** is explicit and mandatory.
- **Channel showcase softer**: channel/public CTA does not imply immediate executable checkout rights.
- **Mini App execution truth strict and current**: customer actionability is determined from current runtime state, not stale publication state.
- **`supplier_offer != tour`** is a hard boundary.
- **Explicit authoritative linkage only** between supplier offer and executable Layer A tour path.

## 3) Entity Separation (Must Stay Explicit)
- `supplier_offers` (supplier publication/commercial context)
- `tours` (Layer A executable product and inventory context)
- `supplier_offer_execution_links` (authoritative linkage/governance layer)
- `custom_marketplace_requests` (Layer C request/negotiation domain)
- `orders` / bookings (Layer A reservation and payment domain)

No implicit merges across these entities without explicit design gate.

## 4) Admin/Ops Principle
- User self-service view is not the same as admin operational view.
- `My bookings` / `My requests` remain strictly user-scoped.
- Admin/ops must have separate operational surfaces for all bookings and all requests (cross-user operational visibility and actions), without exposing that through customer-scoped screens.

## 5) Safe Implementation Order From This Checkpoint
- **A. Phase 7.1 continuation**
  - `sales_mode` / `full_bus` continuation in scoped steps.
- **B. Supplier -> Conversion Bridge**
  - authoritative execution linkage
  - actionability states
  - safe Mini App landing continuation
- **C. Operator workflows**
  - process requests
  - close / resolve / reassign
  - admin operational visibility/actions

## 6) Explicit Non-Goals
- No broad refactor.
- No Layer A rewrite.
- No unsafe identity fallback.
- No merging `supplier_offer` and `tour`.
- No admin access through user-scoped screens.
- No coupon/incident automation before explicit design gate.

## 7) Recommended Next Tracks
- `ADMIN_OPERATIONAL_VISIBILITY_FOR_BOOKINGS_AND_REQUESTS`
- `PHASE_7_1_SALES_MODE_FULL_BUS_CONTINUATION`
- `SUPPLIER_CONVERSION_BRIDGE_EXECUTION_LINKAGE`
- `OPERATOR_REQUEST_WORKFLOW`

## Guardrail
- Do not reopen Mini App identity bridge work unless a concrete production regression appears.

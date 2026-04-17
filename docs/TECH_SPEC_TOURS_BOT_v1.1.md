# TECH_SPEC_TOURS_BOT v1.1

## 1. Document Status
- Version: `v1.1`
- Nature: coordinated expansion spec
- Scope: extends `docs/TECH_SPEC_TOURS_BOT.md` without invalidating implemented MVP core

## 2. Compatibility Principle
The current production-real core is treated as **Core Booking Platform Layer** and remains the default behavior unless explicitly expanded.

Must be preserved:
- per-seat booking flows
- reservation/payment foundations
- Mini App and private bot conversion paths
- current `sales_mode` behavior (Phase **7.1**)
- current assisted `full_bus` path (Phase **7.1** Step **5**)
- **closed Phase 7** **`grp_followup_*`** narrow handoff/operator chain boundaries (**`docs/PHASE_7_REVIEW.md`**) — **do not** broaden by default when adding supplier marketplace layers

## 3. Three-Layer Product Architecture

### Layer A - Core Booking Platform (already implemented or partially implemented)
- tours/catalog
- reservations/orders
- payments/reconciliation
- waitlist/handoff/notifications
- private bot + Mini App
- per-seat and assisted full-bus baseline

### Layer B - Supplier Commerce Layer (MVP-compatible extension)
- supplier entity and supplier account
- supplier admin operations
- supplier-owned offers
- capacity/service composition metadata
- supplier-configured `sales_mode` and payment mode
- moderation-governed publication flow

### Layer C - Request Marketplace Layer (MVP-compatible extension with phased rollout)
- custom/group request intake
- supplier matching and broadcast
- supplier responses
- admin/platform intervention
- winner selection and commercial continuation

## 4. Telegram Surface Model (v1.1)
- **Telegram channel**: primary approved offer showcase
- **Linked discussion group**: warm-up, Q&A, social proof
- **Bot**: routing, conversion, request intake, assisted escalation
- **Mini App**: structured self-service booking and structured request support

Publication/conversion chain:

`supplier admin -> moderation -> channel publication -> discussion group -> bot/Mini App conversion`

## 5. Commercial Modes
Tour-level `sales_mode` remains authoritative (see `docs/TOUR_SALES_MODE_DESIGN.md`):
- `per_seat`
- `full_bus`

Clarifications:
- assisted `full_bus` remains valid baseline
- direct full-bus self-service is optional and deferred behind explicit decision gate
- capacity and pricing are related but not identical concerns

## 6. Request Marketplace (RFQ-like) Domain
**Separation from normal orders:** the request lifecycle is **not** the same as the standard **prepare → temporary reservation → payment** order lifecycle until an **explicit** platform-defined transition (later track). Until then, treat requests as a **parallel** orchestration domain.

Used when ready-made offer does not fit customer needs:
- larger groups
- custom route
- composition requirements (transport + guide/water, etc.)

Lifecycle:
1. Request intake
2. Normalization/categorization
3. Supplier distribution
4. Supplier responses
5. Admin intervention where needed
6. Selection and commercial resolution
7. Optional transition into booking/payment rails

## 7. Roles (v1.1)
- Customer
- Central admin
- Operator
- Supplier
- Supplier admin

Role additions do not remove current customer/admin/operator flows; they extend governance and supply capabilities.

## 8. Scope Classification

### 8.1 Already Implemented Baseline
- Core Layer A behavior listed in section 2
- Existing bot/Mini App/public booking/payment logic
- existing handoff/operator narrow chain
- existing tour `sales_mode` baseline and assisted `full_bus` handling

### 8.2 Current MVP-Compatible Extensions (target of this expansion)
- supplier model and supplier admin foundation
- supplier publication workflow with moderation
- request marketplace foundation and supplier response workflow
- explicit ownership models for commercial resolution

### 8.3 Future / Post-MVP Expansion
- direct whole-bus self-service checkout (if still needed)
- advanced marketplace automation/bidding
- broader supplier financial settlement automations
- deeper AI-assisted matching beyond governance baseline

## 9. Data/Policy Principles
- PostgreSQL-first remains mandatory
- service-layer remains business-policy owner
- API and UI layers reflect policy; they do not invent it
- backward compatibility defaults to "preserve current behavior"
- no hidden migration of existing semantics without explicit rollout and validation

## 10. Non-Goals In v1.1 Design Package
- no code implementation in this document
- no broad re-architecture to microservices
- no broad reopening of closed Phase **7** **`grp_followup_*`** followup chain
- no regression to existing booking/payment/public flows

## 11. Coordination References
- `docs/TECH_SPEC_TOURS_BOT.md` (v1.0 baseline)
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` (V2 Track 0 — frozen Layer A)
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md` (main expansion design)
- `docs/TOUR_SALES_MODE_DESIGN.md` (sales mode policy baseline)
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` (delivery roadmap)

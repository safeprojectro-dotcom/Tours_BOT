# Supplier Admin And Request Marketplace Design

## 1) Purpose And Relation To Existing Docs
This document defines the next major product expansion for Tours_BOT as an extension of the already implemented platform.

It is coordinated with:
- `docs/TECH_SPEC_TOURS_BOT.md` (original MVP baseline)
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` (V2 Track 0 — frozen Layer A compatibility baseline)
- `docs/PHASE_7_REVIEW.md` (Phase 7 closure)
- `docs/TOUR_SALES_MODE_DESIGN.md` (tour-level `sales_mode`)
- `docs/CHAT_HANDOFF.md` (current continuity state)

This document does **not** replace the current system. It defines additional layers on top of the stable core.

## 2) Current Implemented Core That Must Be Preserved
Treat the current codebase as **Layer A: Core Booking Platform**.

Must remain compatible:
- existing per-seat booking flows
- reservation/payment foundations
- current Mini App user journeys
- current private bot user journeys
- current `sales_mode` model and semantics (Phase **7.1**)
- current assisted `full_bus` path (Phase **7.1** Step **5**)
- **Phase 7** **`grp_followup_*`** narrow operator/handoff chain boundaries (**closed** — **`docs/PHASE_7_REVIEW.md`**)

No design choice in this document should require breaking backward-incompatible changes to current MVP behavior by default.

## 3) Core Architectural Split

### Layer A - Core Booking Platform (existing baseline)
- tours, reservations, orders
- payments and reconciliation
- waitlist and handoff
- notifications
- private bot + Mini App conversion flows
- per-seat path + assisted full-bus path

### Layer B - Supplier Commerce Layer (new)
- supplier entity and supplier account model
- supplier admin surface
- supplier-owned offers/tours
- bus and capacity metadata
- service composition model:
  - transport only
  - transport + guide
  - transport + water
  - transport + guide + water
- supplier-configured sales mode and payment mode
- supplier publication workflow with moderation

### Layer C - Request Marketplace Layer (new)
- custom/group request intake (RFQ-like)
- request distribution to eligible suppliers
- supplier responses/offers
- central admin intervention and governance
- winning supplier selection
- transition from request to booking/payment when applicable

## 4) Roles
- **Customer**: browses offers, discusses in group, converts via bot/Mini App, can submit custom request.
- **Central admin**: platform governance, moderation, supplier approvals, escalation/resolution authority.
- **Operator**: assisted handling for complex cases, continuity for customer-facing exceptions.
- **Supplier**: business party providing transport/tour services and commercial terms.
- **Supplier admin**: operational account that configures supplier offers, pricing, service composition, response to requests.

## 5) Telegram Surface Responsibilities
- **Telegram channel**: primary offer showcase (approved/public offers).
- **Linked discussion group**: discussion/warm-up/social proof and questions.
- **Bot**: routing, conversion entry points, request intake, handoff triggers.
- **Mini App**: structured self-service catalog/booking plus structured request support.

This separation keeps public marketing/discovery distinct from transaction and request orchestration.

## 6) Supplier Admin Responsibilities
- maintain supplier profile and operational metadata
- configure supplier-owned offers and availability windows
- configure service composition options
- configure `sales_mode` and payment mode per offer/tour
- submit offers for moderation/publication
- respond to customer requests in request marketplace
- track response status, selected/not selected, and follow-up actions

## 7) Supplier Offer Lifecycle
1. Draft created in supplier admin
2. Validation checks (required fields, mode compatibility)
3. Submitted for moderation
4. Central admin review:
   - approve
   - reject with reason
   - request changes
5. Approved offer published to Telegram channel
6. Discussion happens in linked group
7. Bot/Mini App converts customer into booking or request path
8. Offer can be archived/unpublished by policy

## 8) Publication / Moderation Flow
Canonical flow:

`supplier admin -> platform moderation/approval -> Telegram channel publication -> linked discussion group conversation -> bot/Mini App conversion`

Design principles:
- publication rights are platform-governed, not direct supplier push to channel
- moderation outcomes are explicit and auditable
- content and commercial configuration remain linked (no orphaned "marketing-only" publication)

## 9) Whole-Bus Commercial Mode
- Current implementation keeps `full_bus` as an assisted path and this remains valid.
- Direct full-bus self-service is **not** automatically required in this expansion.
- In this design, whole-bus can exist as:
  - supplier-configured commercial mode
  - assisted commercial path (default-safe early rollout)
  - future direct self-service path only after explicit design decision gate

## 10) Ready-Made Offer vs Custom Request Split

### Ready-made offer path
- customer sees pre-configured published offer
- conversion follows existing booking-compatible routes where possible

### Custom request path
- customer requirement does not fit ready-made offers
- request is captured structurally and routed to request marketplace

Both paths must coexist without forcing all demand into one model.

## 11) Request Marketplace Lifecycle
1. Customer submits request via bot/Mini App
2. Request normalized and categorized
3. Request broadcast/routed to matching suppliers
4. Suppliers submit responses via supplier admin
5. Central admin can intervene (quality, fairness, policy, conflict)
6. Platform/customer selects winning supplier
7. Commercial handling proceeds:
   - assisted closure
   - or transition to structured booking/payment path when available

## 12) Booking/Payment Ownership Options
Design allows explicit ownership patterns per scenario:
- **Platform-owned checkout**: booking/payment processed in current platform rails.
- **Supplier-assisted closure**: operator/supplier-assisted commercial closure, recorded in platform.
- **Hybrid**: request resolved with supplier response, then platform executes booking/payment.

Decision must be explicit per rollout track; avoid hidden mixed ownership.

## 13) Compatibility Constraints With Existing Core
- no regression in existing per-seat booking behavior
- no silent redefinition of reservation, hold, expiry, or payment/reconciliation semantics
- no invalidation of current `sales_mode` semantics (Phase **7.1**)
- no disruption to current Mini App/private bot conversion flows
- no broad reopening of **closed Phase 7** **`grp_followup_*`** followup/operator chain (supplier marketplace is **not** an excuse to expand that chain by default)
- marketplace layers (B/C) are **extensions**, not a **replacement** for Layer A — see **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`**
- PostgreSQL-first data integrity stays mandatory
- service-layer owns business rules; route/UI layers reflect policy only
- no forced microservice rewrite

## 13a) Track 1 — Accepted Product Boundaries (documentation gate)
Aligned with **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`** Track **1** — **no** new code in this gate:
- **Direct whole-bus self-service** is **not** automatically approved; remains behind **Phase 7.1** Step **6** / **Track 6** explicit decision.
- **Assisted full-bus path** (Phase **7.1** Step **5**) remains **valid** baseline.
- **Request marketplace (RFQ)** remains **separate** from the normal **order** lifecycle until an explicit **transition contract** is implemented in a later track.
- **Supplier → Telegram channel** publication remains **platform-moderated** (no unmoderated supplier push).

## 14) Recommended Rollout Order
1. Preserve/freeze current core behavior and invariants
2. Supplier domain model + supplier admin foundation
3. Moderation/publication workflow into channel/group
4. Request marketplace intake + supplier responses
5. Commercial resolution policies (ownership model by scenario)
6. Decision gate on direct full-bus self-service (optional future)

## 15) Explicitly Postponed Items
- automatic direct full-bus self-service checkout as default
- dynamic bidding/auction complexity in first marketplace release
- major payment architecture rewrite
- broad refactor of existing bot/Mini App flows
- distributed microservice split of current monolith
- non-essential AI/RAG marketplace automation before governance baseline is stable

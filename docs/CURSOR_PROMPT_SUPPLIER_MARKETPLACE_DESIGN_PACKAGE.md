Create a single coordinated design package for the next major product expansion of Tours_BOT.

Do not implement code yet.

## Context
The original `TECH_SPEC_TOURS_BOT.md` and `IMPLEMENTATION_PLAN.md` were written for the initial MVP:
- one customer bot
- group + private + Mini App
- one central admin
- one catalog of tours
- booking/payment/waitlist/handoff/content publication

However, the product direction has expanded and now needs a broader architecture that still preserves the already implemented core.

## Critical rule
Do not replace or invalidate the already implemented system.
Treat the current codebase as the stable **Core Booking Platform Layer**.

The new design must extend the platform without breaking:
- existing per-seat booking flows
- current reservation/payment foundations
- current Mini App flows
- current private bot flows
- current `sales_mode` implementation
- current assisted full-bus path

## Goal
Create a coordinated design package consisting of these 3 documents:

1. `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
2. `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
3. `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`

## What the new design package must cover

### A. Core architectural split
The design must clearly separate 3 layers:

#### Layer A — Core Booking Platform
Already implemented or partially implemented:
- tours
- reservations
- orders
- payments
- handoffs
- notifications
- Mini App
- private bot
- per-seat flow
- assisted full-bus path

#### Layer B — Supplier Commerce Layer
New design layer:
- supplier entity / supplier account
- supplier admin surface
- supplier-owned offers/tours
- bus/capacity metadata
- service composition:
  - transport only
  - transport + guide
  - transport + water
  - transport + guide + water
- supplier-configured sales mode
- supplier-configured payment mode
- supplier publication workflow

#### Layer C — Request Marketplace Layer
New design layer:
- custom/group request intake
- request broadcast to suppliers
- supplier responses
- admin/platform intervention
- selection/winning supplier
- transition from request to booking/payment if applicable

### B. Telegram surface model
The design must explicitly model:
- Telegram channel as the primary offer showcase
- linked discussion group as the discussion/warm-up layer
- bot as routing/conversion/request intake
- Mini App as structured self-service and request support surface

### C. Publication flow
The design must explicitly describe:
supplier admin → platform moderation/approval → Telegram channel publication → linked discussion group conversation → bot/Mini App conversion

### D. Whole-bus logic
The design must clarify:
- current `full_bus` path remains assisted in current implementation
- direct whole-bus self-service is NOT automatically required
- whole-bus may exist as:
  - a supplier-configured commercial mode
  - an assisted commercial path
  - a future possible self-service path only after explicit design

### E. Custom request / RFQ flow
The design must cover scenarios like:
- existing ready-made tour does not fit the client need
- customer needs 30 seats / a bus for children / custom route / guide + transport
- bot creates a request
- request is distributed to suppliers
- suppliers respond via supplier admin
- central admin can intervene
- selected supplier proceeds with commercial handling

## Required output: document-specific requirements

### 1. `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
This must be the main new design document.

It must include sections for:
- purpose and relation to existing docs
- current implemented core that must be preserved
- roles:
  - customer
  - central admin
  - operator
  - supplier
  - supplier admin
- channel/group/bot/Mini App responsibilities
- supplier admin responsibilities
- supplier offer lifecycle
- publication/moderation flow
- whole-bus commercial mode
- ready-made offer vs custom request split
- request marketplace lifecycle
- booking/payment ownership options
- compatibility constraints with existing core
- recommended rollout order
- explicit postponed items

### 2. `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
This must be an updated technical/product spec that:
- builds on the original tech spec
- preserves original MVP core
- adds the newly identified supplier-admin and request-marketplace architecture
- clearly marks what is:
  - already implemented
  - current MVP-compatible extension
  - future/post-MVP expansion

It must not pretend everything is already in scope for immediate implementation.

### 3. `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
This must be a new implementation roadmap with large delivery tracks instead of micro-slices.

Use tracks like:
- Track 0 — freeze and preserve current core
- Track 1 — supplier marketplace design package
- Track 2 — supplier admin foundation
- Track 3 — supplier offer publication to Telegram channel
- Track 4 — request marketplace foundation
- Track 5 — commercial resolution layer
- Track 6 — later decision on direct whole-bus self-service, only if still needed

Each track must include:
- goal
- scope
- dependencies
- must-not-break rules
- suggested tests/checks
- exit signal

## Constraints
- do not implement code
- do not change current running flows
- do not invalidate already completed Phase 7.1 work
- do not reopen old Phase 7 followup/operator chain broadly
- do not turn this into a microservice rewrite
- keep compatibility with existing PostgreSQL-first architecture and service-layer discipline

## After writing
Report:
1. files created
2. major design decisions introduced
3. how the new package preserves the current core
4. recommended first implementation track after design approval
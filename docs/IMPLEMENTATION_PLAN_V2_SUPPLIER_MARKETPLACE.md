# IMPLEMENTATION PLAN V2 - Supplier Marketplace Expansion

## Plan Goal
Deliver supplier-admin and request-marketplace capabilities as a major platform extension while preserving the existing Core Booking Platform behavior.

## V2 track status (documentation gates)

| Track | Status | Next |
|------:|--------|------|
| **0** — Freeze core | **Completed** — `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` | — |
| **1** — Design acceptance / alignment | **Completed** — package aligned with Track **0**; see **Track 1** section | — |
| **2** — Supplier admin foundation | **Completed (implementation)** — additive Layer B (`suppliers`, credentials, `supplier_offers`); admin bootstrap + `/supplier-admin/offers`; Alembic **`20260417_07`**; stabilization/review: **`docs/CURSOR_PROMPT_TRACK_2_STABILIZATION_AND_REVIEW_V2.md`** | — |
| **3** — Supplier offer publication | **Completed (implementation)** — moderation (`approved`/`rejected`), showcase publish to Telegram channel (`published`), `supoffer_<id>` private `/start` CTA; Alembic **`20260418_08`** | **Track 4** — request marketplace (when scheduled) |

## Scope Guardrails
- no code implementation in this document
- no broad rewrite of current architecture
- no regression in existing booking/payment/bot/Mini App flows
- no broad reopening of closed Phase **7** **`grp_followup_*`** followup/operator chain outside explicit scoped integration points (**Phase 7.1** sales mode remains a separate, already-shipped sub-track — do not conflate)
- PostgreSQL-first and service-layer policy ownership remain mandatory

## Track 0 - Freeze And Preserve Current Core
**Status (documentation):** **completed**.
**Goal**
- Establish a compatibility baseline before expansion work.

**Scope**
- Declare current core as stable Layer A.
- Record invariants for per-seat booking, payments, Mini App, private bot, `sales_mode`, assisted `full_bus`.
- **Deliverable:** `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` (frozen core, compatibility contracts, must-not-break checklist, smoke checks, migration/deploy guardrails).

**Dependencies**
- `docs/PHASE_7_REVIEW.md`
- `docs/CHAT_HANDOFF.md`
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`

**Must-Not-Break Rules**
- Do not change existing commercial semantics by default.
- Do not alter existing API/UI behavior without explicit compatibility plan.
- Do not deploy code that expects new schema to any environment before migrations are applied there (**schema drift** incidents: `tours.cover_media_reference`, `tours.sales_mode` / `20260416_06`).

**Suggested Tests/Checks**
- Run **§4 + §5** in `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` before/after each future track touchpoint.
- baseline smoke: `/health`, `/healthz`, tour-loading route, booking prep/reservation/payment happy path (staging)
- Mini App basic catalog/detail/booking flow smoke
- private bot basic conversion flow smoke

**Exit Signal**
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` published and referenced from `docs/CHAT_HANDOFF.md` + `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`.
- Team agrees V2 tracks will run the baseline checklist around any Layer A or shared schema changes.

## Track 1 - Supplier Marketplace Design Package
**Status (documentation / alignment gate):** **completed (accepted and aligned)** — design package reviewed against Track **0**; no Layer A invalidation; marketplace treated as **extension layers** (B/C), not replacement.

**Goal**
- Confirm coordinated design artifacts and **explicit product boundaries** before any Track **2** code.

**Scope**
- Align and accept:
  - `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
  - `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
  - this plan document
- Cross-check with `docs/TOUR_SALES_MODE_DESIGN.md` and `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`

**Dependencies**
- Track 0 baseline freeze — **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`** published and acknowledged

**Alignment confirmed (Track 1)**
- **Layer A preserved:** design adds **Layer B** (supplier commerce) and **Layer C** (request marketplace) **on top of** frozen core; no silent redefinition of booking/payment/reservation semantics.
- **Phase 7 `grp_followup_*`:** remains **closed** narrow chain; supplier marketplace docs must **not** broaden it by default.
- **Phase 7.1 `sales_mode`:** remains authoritative tour-level commercial config; assisted **`full_bus`** stays valid; **direct whole-bus self-service** is **not** auto-approved (see **Track 6** / Phase **7.1** Step **6** gates).
- **Request marketplace:** RFQ-like lifecycle is **separate** from normal order lifecycle until an **explicit** transition contract is implemented in a later track.
- **Publication:** supplier → channel remains **moderation-governed** (no unmoderated supplier push).

**Open product boundaries (explicit — not implementation commitments)**
- **Direct whole-bus self-service:** still **not** automatically approved; requires **Phase 7.1** Step **6** / **Track 6** decision gate before any build.
- **Assisted full-bus path:** remains the **valid** current baseline (Phase **7.1** Step **5**).
- **Custom request marketplace:** separate domain from standard **prepare → hold → pay** order flow until explicitly bridged.
- **Supplier publication:** must remain **platform-moderated**.

**Must-Not-Break Rules**
- Design must explicitly preserve Layer A (`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`).
- No hidden implementation commitments.

**Suggested Tests/Checks**
- architecture review walkthrough
- explicit "implemented now vs extension vs future" verification

**Exit Signal**
- This section records **acceptance/alignment**; continuity updated in `docs/CHAT_HANDOFF.md` and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`.
- **Next safe implementation track:** **Track 2** — subject to Track **0** checklist around any Layer A or shared schema touch.

## Track 2 - Supplier Admin Foundation
**Goal**
- Introduce supplier domain foundation and supplier admin control surface.

**Scope**
- supplier entity/account model
- supplier admin auth/roles boundaries
- supplier-owned offer draft model
- configuration fields: service composition, sales/payment modes

**Dependencies**
- Track **1** design acceptance / alignment (**this document, Track 1 section**)
- **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`** — **must-not-break** contracts and smoke (§4–§5) for any Layer A or shared ORM/schema changes

**Must-Not-Break Rules**
- Existing central admin flows continue to work.
- Existing tours remain valid and operable.
- Service-layer validates supplier configuration policy.
- **Track 0 compatibility:** no regression to per-seat booking, payment reconciliation, reservation timers, Mini App/private bot baseline, Phase **7** handoff semantics, or Phase **7.1** `sales_mode` behavior without explicit compatibility plan.

**Suggested Tests/Checks**
- unit tests for supplier policy validation
- integration tests for supplier-admin CRUD and permissions
- migration safety checks (PostgreSQL)

**Exit Signal**
- Supplier admin can create/manage draft offers without affecting existing customer flows.

**Implementation record (Track 2 closure)**
- **Schema:** new tables/enums only; **`tours` / `orders` / `payments`** unchanged; **`supplier_offers.sales_mode`** uses existing Postgres **`tour_sales_mode`** type (reuse, not an alteration of **`tours`** rows).
- **Auth:** **`ADMIN_API_TOKEN`** unchanged for central admin; supplier surface isolated under **`/supplier-admin/*`** with DB-backed bearer credentials (hashed).
- **Lifecycle:** supplier offers support **`draft`** and **`ready_for_moderation`** only at persistence layer; **no** central moderation/publish workflow until **Track 3**.

## Track 3 - Supplier Offer Publication To Telegram Channel
**Goal**
- Deliver moderated publication pipeline from supplier admin to public Telegram surfaces.

**Scope**
- moderation states/workflow
- approval/rejection/change-request actions
- publish to channel and linkage to discussion group
- traceability between offer state and publication state

**Dependencies**
- Track 2 supplier foundation
- existing Telegram operational setup

**Must-Not-Break Rules**
- Publication cannot bypass moderation policy.
- Existing channel/group/bot behavior remains stable.

**Suggested Tests/Checks**
- moderation workflow tests
- publish/unpublish idempotency checks
- Telegram publication smoke and rollback checks

**Exit Signal**
- Approved supplier offers reliably appear in channel with moderated governance path.

**Implementation record (Track 3 closure)**
- **Lifecycle:** extends **`supplier_offer_lifecycle`** with **`approved`**, **`rejected`**, **`published`**; columns **`moderation_rejection_reason`**, **`published_at`**, **`showcase_chat_id`**, **`showcase_message_id`** (Alembic **`20260418_08`**).
- **Admin (central):** **`GET /admin/supplier-offers`**, **`POST .../moderation/approve`**, **`POST .../moderation/reject`**, **`POST .../publish`** — suppliers **cannot** set moderation states or publish (enforced in **`SupplierOfferService`** + separate moderation service).
- **Telegram:** **`POST /publish`** calls Bot API **`sendMessage`** (HTML) to **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`**; deep link **`supoffer_<id>`** in channel post + private **`/start`** branch shows intro then existing catalog (Layer A unchanged).
- **Not in this track:** unpublish/edit channel message, discussion-group wiring, linking published offer to core **`Tour`** SKU, RFQ.
- **Stabilization (reviewed):** additive Layer B publication only; **`docs/CURSOR_PROMPT_TRACK_3_STABILIZATION_AND_REVIEW_V2.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §24.

## Track 4 - Request Marketplace Foundation
**Goal**
- Enable structured custom request intake and supplier response loop.

**Scope**
- customer request intake via bot/Mini App
- request normalization/categorization
- supplier distribution logic
- supplier response submission
- admin intervention points

**Dependencies**
- Tracks 2-3

**Must-Not-Break Rules**
- Existing ready-made offer conversion flow stays intact.
- Request workflow does not replace current booking flow by default.

**Suggested Tests/Checks**
- request intake validation tests
- supplier routing/eligibility tests
- admin intervention integration tests

**Exit Signal**
- End-to-end request lifecycle works from intake to supplier responses with admin governance.

## Track 5 - Commercial Resolution Layer
**Goal**
- Define and implement commercial closure ownership options for request outcomes.

**Scope**
- ownership models:
  - platform-owned checkout
  - supplier-assisted closure
  - hybrid transition
- selection/winner handling
- transition contracts into booking/payment rails where applicable

**Dependencies**
- Track 4 marketplace foundation
- payment and booking compatibility constraints

**Must-Not-Break Rules**
- Payment reconciliation invariants stay unchanged.
- No regressions to existing order/payment lifecycle.

**Suggested Tests/Checks**
- integration tests for each ownership model path
- reconciliation and status transition regression checks
- manual staging smoke for assisted and platform-owned closure variants

**Exit Signal**
- At least one approved commercial resolution model runs safely in staging without core regressions.

## Track 6 - Decision Gate: Direct Whole-Bus Self-Service (Optional)
**Goal**
- Decide whether direct full-bus self-service is still needed after assisted/commercial rollout evidence.

**Scope**
- product/ops decision based on usage and failure modes
- if approved: explicit design + policy updates before implementation
- if not approved: keep assisted full-bus as primary mode

**Dependencies**
- Track 5 operational outcomes
- `docs/TOUR_SALES_MODE_DESIGN.md`

**Must-Not-Break Rules**
- No automatic rollout of direct full-bus checkout without explicit approval.
- Keep current assisted full-bus flow valid until replacement is proven.

**Suggested Tests/Checks**
- decision review with product, operations, and engineering
- risk matrix and rollback readiness check

**Exit Signal**
- Formal go/no-go decision documented; if go, separate implementation scope is approved.

## Cross-Track Validation Discipline
- Keep a compatibility checklist running from Track 0 to Track 6.
- Prefer narrow verifiable increments per track.
- Run minimal relevant tests before broad regression suites.
- Treat staging validation as required for behavior affecting Telegram/channel/public flows.

## Primary References
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/TOUR_SALES_MODE_DESIGN.md`
- `docs/CHAT_HANDOFF.md`

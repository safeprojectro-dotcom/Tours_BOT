# IMPLEMENTATION PLAN V2 - Supplier Marketplace Expansion

## Plan Goal
Deliver supplier-admin and request-marketplace capabilities as a major platform extension while preserving the existing Core Booking Platform behavior.

## V2 track status (documentation gates)

| Track | Status | Next |
|------:|--------|------|
| **0** — Freeze core | **Completed** — `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` | — |
| **1** — Design acceptance / alignment | **Completed** — package aligned with Track **0**; see **Track 1** section | — |
| **2** — Supplier admin foundation | **Completed (implementation)** — additive Layer B (`suppliers`, credentials, `supplier_offers`); admin bootstrap + `/supplier-admin/offers`; Alembic **`20260417_07`**; stabilization/review: **`docs/CURSOR_PROMPT_TRACK_2_STABILIZATION_AND_REVIEW_V2.md`** | — |
| **3** — Supplier offer publication | **Completed (implementation)** — moderation (`approved`/`rejected`), showcase publish to Telegram channel (`published`), `supoffer_<id>` private `/start` CTA; Alembic **`20260418_08`** | — |
| **4** — Request marketplace foundation | **Completed (implementation)** — Layer C RFQ intake (Mini App + `/custom_request`), supplier list/respond (`declined`/`proposed`), admin list/detail/patch; Alembic **`20260421_10`**; stabilization **`docs/CURSOR_PROMPT_TRACK_4_STABILIZATION_AND_REVIEW_V2.md`** | **Track 5a** (below) |
| **5a** — Commercial resolution selection foundation | **Completed (implementation)** — admin **`POST /admin/custom-requests/{id}/resolution`**, selection FK + resolution kind + statuses; customer minimal status reads; **no** order/reservation/payment bridge; Alembic **`20260422_11`**; **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §26 | **Track 5b.1** (below) |
| **5b.1** — RFQ booking bridge record | **Completed (implementation)** — **`custom_request_booking_bridges`**, admin **`POST/PATCH .../booking-bridge`**, detail read; **no** hold/payment; Alembic **`20260423_12`**; §27 | **Track 5b.2** (below) |
| **5b.2** — RFQ bridge execution entry | **Completed (implementation + stabilization reviewed)** — Mini App **`GET/POST .../custom-requests/{id}/booking-bridge/preparation|reservations`**; policy gate; reuse Layer A prep + hold; **no** migration; §28 | **Track 5b.3a** (below) |
| **5b.3a** — RFQ supplier policy + effective execution resolver | **Completed (implementation + stabilization reviewed)** — Alembic **`20260424_13`**; supplier-declared sales/payment on RFQ responses; **`EffectiveCommercialExecutionPolicyService`**; bridge execution uses composed gate; **no** payment execution; §29 | **Track 5b.3b** (below) |
| **5b.3b** — Bridge payment eligibility + payment-entry reuse | **Completed (implementation + stabilization reviewed)** — **`GET .../booking-bridge/payment-eligibility`** read-only; **`POST .../orders/{id}/payment-entry`** unchanged; **`PaymentEntryService.is_order_valid_for_payment_entry`**; **no** migration; §30 closure | **Track 5c** (below); other **5b.x** |
| **5c** — RFQ Mini App UX wiring (bridge execution + payment continuation) | **Completed (implementation + stabilization reviewed)** — route **`/custom-requests/{id}/bridge`**; Flet screen calls existing **`preparation` / `reservations` / `payment-eligibility`** APIs; **`Continue to payment`** only when hold active **and** **`payment_entry_allowed`**; then **`open_payment_entry`** → standard payment stack (**`POST .../payment-entry`** only); **no** migration; §31 closure | **Track 5d** (below); multi-quote UX |
| **5d** — Mini App “My Requests” / RFQ status hub | **Completed (implementation + stabilization reviewed)** — **`/my-requests`**, **`/my-requests/{id}`**; list/detail from existing Layer C + bridge prep + bookings cross-check; CTAs reuse **`/custom-requests/{id}/bridge`**, **`open_payment_entry`**, booking detail; **no** migration; §32 closure | **Track 5e** (below); multi-quote UX; notifications |
| **5e** — Bridge supersede / cancel lifecycle | **Completed (implementation + stabilization reviewed)** — admin **`POST .../booking-bridge/close`**, **`POST .../booking-bridge/replace`**; terminal bridges excluded from active set; customer detail additive fields; hub + bridge fail-closed UX; **no** migration; §33 closure | **Track 5f v1** (below); notifications; **Phase 7.1 Step 6** / Track **0** baseline if paused |
| **5f v1** — Customer multi-quote summary / aggregate visibility | **Completed (implementation + stabilization reviewed)** — **`proposed_response_count`**, **`offers_received_hint`**, **`selected_offer_summary`** on **`GET .../custom-requests/{id}`**; My Requests detail read-only copy; **no** migration; §34 closure | **5f** v2+ compare / localized hints; RFQ **notifications** / bot deep links; **Phase 7.1 Step 6** / Track **0** baseline if paused |

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

**Implementation record (Track 4 closure)**
- **Schema:** **`custom_marketplace_requests`**, **`supplier_custom_request_responses`**, enums **`custom_marketplace_request_*`**, **`supplier_custom_request_response_kind`** (**`20260421_10`**); **`User`** gains optional **`custom_marketplace_requests`** relationship only.
- **Intake:** **`POST /mini-app/custom-requests`**; private **`/custom_request`** (FSM); Mini App Help → **`/custom-request`** form. **No** `Order` / reservation / payment creation.
- **Suppliers:** **`GET /supplier-admin/custom-requests`**, **`GET .../{id}`**, **`PUT .../{id}/response`** — broadcast listing of **`open`** requests; minimal response model (not bidding).
- **Admin:** **`GET/PATCH /admin/custom-requests`**, detail includes supplier responses.
- **Compatibility:** Track **0** Layer A semantics preserved; Track **2**/**3** supplier and publication paths unchanged by RFQ code paths.
- **Stabilization:** **`docs/CURSOR_PROMPT_TRACK_4_STABILIZATION_AND_REVIEW_V2.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §25.

## Track 5a - Commercial Resolution Selection Foundation
**Status (implementation):** **completed** — selection + resolution recording only; **no** RFQ→`Order` bridge.

**Implementation record (Track 5a closure)**
- **Schema:** Alembic **`20260422_11`** — new request status values; migrate **`fulfilled` → `closed_assisted`**; **`commercial_resolution_kind`** enum; **`selected_supplier_response_id`** FK (**`ON DELETE SET NULL`**).
- **Admin:** **`POST /admin/custom-requests/{id}/resolution`** for **`under_review`**, **`supplier_selected`**, **`closed_assisted`**, **`closed_external`**; **`PATCH`** blocks terminal commercial statuses (use resolution endpoint).
- **Suppliers:** responses only **`open`/`under_review`**; portal lists won requests after closure.
- **Customer:** **`GET /mini-app/custom-requests`** (+ by id) — **`customer_visible_summary`** only.
- **Compatibility:** Tracks **0–4** Layer A and RFQ foundation preserved; enum downgrade limitations documented (**§26**).

## Track 5b.1 - RFQ Booking Bridge Record
**Status (implementation):** **completed** — persisted intent toward Layer A; **no** reservation or payment.

**Implementation record**
- **Schema:** **`custom_request_booking_bridges`**, **`custom_request_booking_bridge_status`** (**`20260423_12`**).
- **Admin:** **`POST /admin/custom-requests/{id}/booking-bridge`**, **`PATCH .../booking-bridge`**; detail **`booking_bridge`** field.
- **Non-goals:** no **`Order`**, no **`TemporaryReservationService`**, no payment entry.

**Stabilization review (closure)**
- **Additive / isolated:** bridge table is separate from **`orders`**; FKs **`RESTRICT`** / **`SET NULL`** on **`tour_id`** only; resolution endpoint does **not** create bridges.
- **Uniqueness:** one **active** bridge per request (**409** on duplicate **POST**); see **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §27 for optional future DB uniqueness if needed.
- **Tour link:** validates sellable **time + inventory** for **`open_for_sale`** only; **does not** call **`TourSalesModePolicyService`** at link time — **`Track 5b.2`** applies policy on **customer execution** ( **`full_bus`** → blocked / assisted).

**Next safe track:** **5f v2+** (explicit) anonymized compare / localized hints, RFQ **notifications** / bot deep links, or **Phase 7.1 Step 6** / Track **0** baseline if product pauses marketplace execution. (**Tracks 5b.3a–5f v1** through §34 — **completed** for scoped slices; payment session creation remains **only** via existing **`payment-entry`**.)

## Track 5b.2 - RFQ bridge execution entry (preparation + hold)
**Status (implementation):** **completed** — explicit Mini App routes; **`CustomRequestBookingBridgeExecutionService`** orchestrates into **`MiniAppReservationPreparationService`** + **`MiniAppBookingService`**; **`TourSalesModePolicyService`** enforced; **no** new payment provider behavior.

**Implementation record**
- **Routes:** **`GET /mini-app/custom-requests/{id}/booking-bridge/preparation`**, **`POST /mini-app/custom-requests/{id}/booking-bridge/reservations`**.
- **Context:** **`CustomRequestBookingBridgeService.resolve_customer_execution_context`**, **`load_tour_validated_for_customer_execution`** (catalog visibility).
- **Non-goals:** no **`payment-entry`** in this slice; no implicit execution on resolution/bridge admin actions.

**Stabilization review (closure):** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §28 — no payment side effects; **`full_bus`** non-self-serve; standard **`/mini-app/tours/...`** booking paths unchanged; optional follow-up: **404** vs **400** for unknown **`telegram_user_id`** on bridge routes.

## Track 5 - Commercial Resolution Layer
**Goal**
- Define and implement commercial closure ownership options for request outcomes **including**, when explicitly scoped, **transition contracts into booking/payment rails**.

**Scope**
- ownership models:
  - platform-owned checkout
  - supplier-assisted closure
  - hybrid transition
- **Track 5a already delivered:** central-admin winner selection + resolution status/kind + minimal customer status reads (**no** bridge).
- **Remaining Track 5 scope:** transition contracts into booking/payment rails where applicable (**explicit slice only**)

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

Stabilize and review the completed **Track 4 — Custom Request Marketplace Foundation**.

Do not add new features.

## Context
Track 4 has already been implemented.
Now perform a strict compatibility and scope review before moving further.

## Goal
Confirm that the new custom-request marketplace layer is additive, remains separate from the normal booking/order lifecycle, and does not break the frozen Layer A core or accepted supplier/publication layers.

## What must be reviewed carefully
Review all Track 4 changes, with extra attention to:
- request lifecycle separation from normal orders
- supplier request visibility and responses
- admin oversight visibility
- whether any Layer A customer-facing behavior changed accidentally
- whether request logic leaked into booking/payment core
- whether Track 3 publication or Track 2 supplier admin assumptions were broken
- whether `app/models/user.py` was changed narrowly and safely
- whether new router ordering in bot app affects existing private flows

## Required review tasks

### A. Scope creep review
Confirm Track 4 did NOT accidentally introduce:
- direct whole-bus self-service
- checkout/payment redesign
- auto-auction
- complex ranking
- broad auth rewrite
- broad handoff rewrite
- broad group assistant redesign
- replacement of normal booking/order lifecycle

### B. Layer A compatibility review
Confirm Track 4 preserves:
- current tours/order/payment semantics
- current Mini App routes
- current private bot routes
- current `sales_mode` behavior
- current assisted full-bus path
- current supplier offer publication flow
- current migrate → deploy → smoke discipline

### C. Request-model separation review
Explicitly explain:
- whether requests were kept separate from orders
- whether any bridge to orders is only future/planned
- whether supplier responses remain a minimal foundation and not a full bidding engine

### D. Router and user-model safety review
Explicitly explain:
- why `app/models/user.py` needed changes
- whether those changes are additive and safe
- whether custom request router ordering can interfere with normal private entry flow
- whether any existing bot intent or handler path became more fragile

### E. Docs update
Update the appropriate docs:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`
- optionally `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`

### F. Baseline verification
Run the minimum focused checks necessary to support acceptance.

## Before doing anything
Summarize:
1. intended Track 4 scope
2. main compatibility risks
3. exact files/docs to inspect/update

## After completion
Report:
1. files changed
2. whether scope creep was found
3. whether request/order separation is correct
4. whether `user.py` changes are justified
5. whether router ordering is safe
6. tests/checks run
7. final compatibility statement
8. exact next safe track

---

## Review outcome (2026-04) — completed

- **Scope creep:** None found — no whole-bus self-service, payment redesign, auction/ranking, auth/handoff/group-assistant rewrites, or order lifecycle replacement.
- **Request vs order:** RFQ persists only in **`custom_marketplace_requests`** / **`supplier_custom_request_responses`**; **`CustomMarketplaceRequestService`** does not import booking/reservation/payment modules; no **`order_id`** on requests.
- **`User` model:** Single additive **`custom_marketplace_requests`** relationship; FK **`RESTRICT`** on **`user_id`** preserves referential integrity.
- **Router order:** **`custom_request`** before **`private_entry`** — state-filtered handlers take precedence only while FSM active; default private flows unchanged.
- **Docs updated:** **`docs/CHAT_HANDOFF.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §25, **`COMMIT_PUSH_DEPLOY.md`**, **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`** (table + Track 4 closure record).
- **Checks run:** `pytest tests/unit/test_custom_marketplace_track4.py`, `tests/unit/test_api_mini_app.py::MiniAppCatalogRouteTests::test_catalog_route_returns_filtered_cards`, `tests/unit/test_supplier_offer_track3_moderation.py::SupplierOfferTrack3RegressionTests::test_admin_overview_unchanged` — all passed.
- **Next safe V2 track:** **Track 5 — Commercial resolution layer** (explicit ownership / transition to booking when product scopes it); parallel product gate remains **Phase 7.1 Step 6** (direct whole-bus self-service) — separate decision.
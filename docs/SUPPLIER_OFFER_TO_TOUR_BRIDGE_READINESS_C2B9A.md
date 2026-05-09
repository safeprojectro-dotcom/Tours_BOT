# Supplier Offer → Tour / Mini App bridge readiness (C2B9A)

**Mode:** planning / audit only (no code changes in this checkpoint).  
**Purpose:** reconcile **Layer B** (supplier offer / showcase) with **Layer A** (Tour / catalog / booking truth) after **C2B8B** (Telegram showcase publish).  
**Date:** 2026-05-09.

---

## Executive summary

The **explicit offer→Tour bridge** is **already implemented** in the backend: **`supplier_offer_tour_bridges`**, **`SupplierOfferTourBridgeService`**, admin **`POST/GET …/tour-bridge`**, **`POST …/execution-link`**, **`POST …/tours/{tour_id}/activate-for-catalog`**, **`review-package`** aggregates (**bridge readiness**, **conversion_closure**, **operator_workflow** hints), and **B11**-style **`/start supoffer_<id>`** routing via **`resolve_sup_offer_start_mini_app_routing`** (active execution link + **`OPEN_FOR_SALE`** + catalog visibility).

**C2B9A finding:** the main **gap** is **not** “missing bridge code” but **(a)** **operator UX / Telegram** (**`create_execution_link`** still only via HTTP **or** published-offer link wizard — **optional** **C2B10T-C**; **`create_tour_bridge`** / **`activate_tour_for_catalog`** **shipped** on the admin card as **C2B10T-A** / **C2B10T-B** when **`operator_workflow`** enables each), **(b)** **documentation drift** (partially cleared by **C2B9B** docs sync **2026-05-09**; **C2B10T-*** handoffs **`docs/CHAT_HANDOFF.md`**), **(c)** **product-prioritized follow-ups** (**B7.3** media bytes, **B10.6** bot-as-router, **B11** polish / edge cases).

---

## 1. Current bridge-related state (repo)

### 1.1 Data model & migration

| Area | Notes |
|------|--------|
| **`supplier_offer_tour_bridges`** | Alembic **`20260529_27_supplier_offer_tour_bridge_b10.py`**; model **`SupplierOfferTourBridge`**; statuses / **`bridge_kind`** enums in **`app.models.enums`**. |
| **`supplier_offer_execution_links`** | Active link per offer (`SupplierOfferExecutionLinkRepository.get_active_for_offer`); used for Mini App “exact tour” routing and operator Telegram link UX. |
| **`supplier_offers`**, **`tours`** | Standard Layer B / Layer A tables; bridge maps offer → tour with explicit admin actions. |

### 1.2 Services (business logic)

| Service | Role |
|---------|------|
| **`SupplierOfferTourBridgeService`** | Create new **`Tour`** from offer and/or link existing tour; validation, idempotency, audit-oriented errors (**`app/services/supplier_offer_tour_bridge_service.py`**). |
| **`SupplierOfferModerationService`** | Showcase publish (**unchanged** by C2B9A); separate from bridge. |
| **`SupplierOfferReviewPackageService`** | **`review_package`**: bridge readiness read-model, **`conversion_closure`**, integration with **`resolve_sup_offer_start_mini_app_routing`** for landing/deeplink hints. |
| **`SupplierOfferExecutionLinkService`** | Create/replace/close execution links (admin + Telegram flows for **published** offers). |
| **Catalog activation** | **`POST /admin/tours/{tour_id}/activate-for-catalog`** ( **`AdminTourWriteService`** ) with **B8.3** duplicate-active guard for same offer+departure. |
| **`resolve_sup_offer_start_mini_app_routing`** | **B11**: from **active execution link** + tour **`OPEN_FOR_SALE`** + **customer catalog visibility** → safe **`/tours/{code}`** WebApp URL (**read-only**). |

### 1.3 Admin HTTP

- **`POST /admin/supplier-offers/{offer_id}/tour-bridge`** / **`GET`** (same path) — bridge create/replay/read (**`app/api/routes/admin.py`**).
- **`POST /admin/supplier-offers/{offer_id}/execution-link`**, list, close — execution link lifecycle.
- **`POST /admin/tours/{tour_id}/activate-for-catalog`** — explicit catalog activation (draft → **`open_for_sale`** per B10 policy).
- **`GET /admin/supplier-offers/{offer_id}/review-package`** — single read-model entry for operators (**playbooks:** **`ADMIN_OPERATOR_WORKFLOW.md`**, **`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`**).

### 1.4 Telegram

- **Admin card:** **C2B8B** adds showcase **Publish** (workflow-gated). **Execution link** UX exists for **published** offers (create/replace/close link). **C2B10T-A** adds **Link tour / Leagă tur** when **`create_tour_bridge.enabled`**; **C2B10T-B** adds **List for sale / În catalog** when **`activate_tour_for_catalog.enabled`** (same propose/confirm + double **`review-package`** re-read pattern as **C2B8B**).
- **Customer/private:** **`/start supoffer_<id>`** handled in **`private_entry.py`** with **`parse_supplier_offer_start_arg`** + **`resolve_sup_offer_start_mini_app_routing`**; channel CTA builder references **`supoffer_`** payload (**`supplier_offer_showcase_message.py`**).

### 1.5 Mini App

- Catalog / tour detail / booking paths remain **Layer A** truth; supplier-offer **landing** services sit beside standard catalog (**review-package** **`MiniAppSupplierOfferLandingService`** / conversion preview — read-only aggregation).
- **Closure** test **`tests/unit/test_supplier_offer_catalog_conversion_closure.py`** documents the **full admin chain** (bridge → activate → catalog visibility → publish → execution link → closure flags).

### 1.6 `operator_workflow` (read-model)

**`app/services/supplier_offer_operator_workflow.py`** exposes actions including:

- **`create_tour_bridge`** → endpoint hint **`POST …/tour-bridge`**
- **`activate_tour_for_catalog`** (conversion_enabling)
- **`create_execution_link`**
- **`publish_showcase_channel`** (**C2B8B** on Telegram)

Disabled reasons / blocking reasons are derived from existing review slices (bridge readiness, packaging, lifecycle, execution-link precheck, etc.) — **no** execution from **`GET`**.

### 1.7 Design / business docs (authoritative)

- **`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md`** — B9 contract (gates, mapping, idempotency, draft-first catalog).
- **`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`** — B1–B13 sequence; states B10 path **implemented** / smoke-accepted.
- **`docs/B10_X_SYNC_CHECKPOINT_2026.md`** (referenced from bridge design) — operational B10 closure record.
- **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** — B8.3 duplicate guard, B11/B10.6/B7.3 priorities.

---

## 2. Gaps

| Category | Gap |
|----------|-----|
| **Telegram operator UX** | **`create_tour_bridge`** / **`activate_tour_for_catalog`** on the admin card when **`enabled`** (**C2B10T-A** / **C2B10T-B**) **`;`** **`create_execution_link`** **—** HTTP **or** Telegram link wizard for **`published`** offers only (**optional** **C2B10T-C** for card entry). |
| **Single “readiness” narrative** | **C2B9B:** end-to-end chain documented in **BUSINESS** plan, **`ADMIN_OPERATOR_WORKFLOW`**, showcase runbook **`;`** **`GET …/review-package`** remains the single **read** surface before mutations. |
| **Docs sync** | **C2B9B (2026-05-09):** **`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`**, **`ADMIN_OPERATOR_WORKFLOW.md`**, **`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`**, **`CHAT_HANDOFF.md`** aligned with bridge + C2B8B showcase publish + B11 chain (**this** file §4 **C2B9B** row **done**). |
| **B7.3 media bytes** | Policy **B7.3A** accepted; **storage / download / render** not done — affects polish of showcase vs catalog hero parity (**not** a bridge blocker for core path). |
| **B10.6** | “Bot as router, not duplicate catalog” — **postponed**; channel CTAs today combine bot + Mini App per existing B11 landing contract. |
| **Audit / observability** | Bridge and link rows exist; **cross-session “who did what when”** for ops may need richer admin read-side or exports (product call). |
| **Tests** | Strong **unit** coverage for conversion closure + **C2B10T-A** / **C2B10T-B** handler specs; **Telegram** E2E for **full** chain **not** required for each slice. |

---

## 3. Risks if implementation is rushed

| Risk | Mitigation (existing or planned) |
|------|----------------------------------|
| **Hidden / automatic Tour creation** | Bridge is **explicit** service + admin **`POST`** only; **no** ORM triggers (**B9**). |
| **Duplicate Tours** | **B8.3** guard on **activate-for-catalog**; bridge service idempotency rules (**B9** §7). |
| **Published offer but not bookable** | Treat **showcase publish** and **bookability** as **orthogonal**; **`conversion_closure`** and **B11** routing enforce **execution link + open_for_sale + visibility** before “exact tour” deep link. |
| **Stale Mini App route** | **B11** fails closed to **generic** intro + landing when gates fail; **`tour_is_customer_catalog_visible`** and **`OPEN_FOR_SALE`** checks. |
| **Confusing `published` with `bookable`** | Docs + **`review-package`** **`conversion_closure.next_missing_step`**; training/playbooks. |
| **Bypassing admin approval** | Supplier intake stays **draft**/moderation; bridge gates on **lifecycle + packaging + field completeness** per **`SupplierOfferTourBridgeService`**. |
| **Layer A booking/payment drift** | **Forbidden** to change hold/pay semantics in bridge slices; catalog activation is separate from orders. |

---

## 4. Proposed next implementation slices (after C2B9A)

Naming is **suggestive**; adjust to project ticket scheme.

| Slice | Scope |
|-------|--------|
| **C2B9B (docs-only)** | **Done (2026-05-09):** BUSINESS plan + operator playbook + showcase runbook + handoff — conversion chain packaging → readiness → showcase (**HTTP** / **Telegram C2B8B**) → **`tour-bridge`** → **`activate-for-catalog`** → execution link → **B11** → **Layer A**. |
| **C2B10T-A (Telegram, narrow)** | Optional: **one** conversion action on admin card (e.g. **`create_tour_bridge`** only) with **same** pattern как **C2B8B** (propose, confirm, double **review-package** read). **Scope gate:** product approval; **do not** ship all three mutations at once without UX review. |
| **C2B10T-B** | **`activate_tour_for_catalog`** from Telegram ( **`conversion_enabling`**, confirmation), only if **C2B10T-A** stable. |
| **C2B10T-C** | **`create_execution_link`** from Telegram **already partially** covered by published-offer link UI; align with **`operator_workflow`** **`enabled`** flags if needed. |
| **B7.3B** (parallel track) | Media storage stub / pipeline when product prioritizes hero parity. |
| **B10.6** | Bot-as-router / duplicate-catalog avoidance — **design gate** before code. |

---

## 5. Recommended immediate next Cursor prompt

**After C2B9B:** optional **C2B10T-*** Telegram conversion buttons ( **`create_tour_bridge`** first, then **`activate_tour_for_catalog`**) **—** **product** **approval** **only** **;** **or** **B7.3B** **/** **B11** **polish** **per** **`OPEN_QUESTIONS_AND_TECH_DEBT.md`**.

**Reference (completed):** **`CURSOR_PROMPT_SUPPLIER_OFFER_CONVERSION_DOCS_SYNC_C2B9B`** — **[`docs/CURSOR_PROMPT_SUPPLIER_OFFER_CONVERSION_DOCS_SYNC_C2B9B.md`](CURSOR_PROMPT_SUPPLIER_OFFER_CONVERSION_DOCS_SYNC_C2B9B.md)**.

---

## 6. Files inspected (C2B9A)

**Docs (read):**  
`docs/CHAT_HANDOFF.md`, `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`, `docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md`, `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` (grep/sections), `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` (grep), existence-only: `docs/IMPLEMENTATION_PLAN.md`, `docs/TECH_SPEC_TOURS_BOT.md`, `docs/TECH_SPEC_TOURS_BOT_v1.1.md`, `docs/CURSOR_PROMPT_SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`.

**Missing / not found:** `docs/BUSINESS-план-v2.txt` (equivalent: **`docs/BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md`** present).

**Code (read-only grep/read):**  
`app/services/supplier_offer_tour_bridge_service.py`, `app/services/supplier_offer_operator_workflow.py`, `app/services/supplier_offer_bot_start_routing.py`, `app/services/supplier_offer_review_package_service.py` (imports), `app/api/routes/admin.py` (tour-bridge / execution-link / activate-for-catalog), `app/bot/handlers/private_entry.py`, `app/models/supplier_offer_tour_bridge.py`, `alembic/versions/20260529_27_supplier_offer_tour_bridge_b10.py`, `tests/unit/test_supplier_offer_catalog_conversion_closure.py` (referenced).

---

## 7. CHAT_HANDOFF pointer

Planning checkpoint: this file (**`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`**); **C2B9B** docs sync **done** **;** next optional **C2B10T-*** or **B7.3B** / **B11** per §5.

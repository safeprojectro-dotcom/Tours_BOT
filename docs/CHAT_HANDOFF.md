# Chat Handoff

## Project
Tours_BOT

**Continuity anchor (read this first):** The **live** approved checkpoint is **Phase 7 closed** (**review / closure accepted**; **`docs/PHASE_7_REVIEW.md`**) — **implementation** through **final consolidation** (Steps **1–17** + polish) is **shipped**; **below** expands **Phase 7** surface to date (Steps **1–17** + **final polish**): **group trigger** + **handoff trigger** helpers (Step **2**); **minimal group runtime gating** (Step **3**); **category-aware** short escalation wording (Step **4**); **private CTA** deep-link foundation (Step **5**); **narrow private `/start`** for **`grp_private`** / **`grp_followup`** (Step **6**); **narrow runtime handoff persistence** for **`/start grp_followup`** (Step **7**); **focused runtime/bot-flow tests** for that chain (Step **8**); **narrow admin read-side visibility** for **`group_followup_start`** (Step **9** — **`is_group_followup`**, **`source_label`**); **narrow admin assignment** for **`group_followup_start`** only (Step **10** — **`POST /admin/handoffs/{handoff_id}/assign-operator`**; same narrow rules as Step **21** **`assign`**; general **`POST .../assign`** **unchanged**); **read-side work-state visibility** for **assigned** **`group_followup_start`** (Step **11** — **`is_assigned_group_followup`**, **`group_followup_work_label`**; **read-only**); **narrow take-in-work** for **assigned** **`group_followup_start`** (Step **12** — **`POST /admin/handoffs/{handoff_id}/mark-in-work`**; **`open` → `in_review`**; **`in_review`** idempotent; **`closed`** rejected; **no** new DB column); **narrow resolve/close** for **`group_followup_start`** (Steps **13–14** — **`POST /admin/handoffs/{handoff_id}/resolve-group-followup`**; **`in_review` → `closed`**; **`closed`** idempotent; **`open`** rejected; **no** replacement for general Step **20** **`close`**); **tiny resolved-state read refinement** (Steps **13–14** — derived **`group_followup_resolution_label`** on admin handoff **list** / **detail** / order-detail **`handoffs`** for **closed** **`group_followup_start`** only); **post-resolution queue visibility** (Step **15** — derived **`group_followup_queue_state`** — **`awaiting_assignment`**, **`assigned_open`**, **`in_work`**, **`resolved`**, or **`null`** for non-**`group_followup_start`**; optional narrow **`GET /admin/handoffs?group_followup_queue=`** filter — **read-side only**); **narrow private resolved-followup confirmation** (Step **16** — **`HandoffRepository.find_latest_by_user_reason`**, **`HandoffEntryService.should_show_group_followup_resolved_confirmation`**, **`start_grp_followup_resolved_intro`** when **`/start grp_followup`** and latest **`group_followup_start`** is **`closed`** with **no** **open** row; **no** operator chat, **no** notification delivery; **`_persist_group_followup_handoff`** unchanged); **narrow private followup history/readiness signal** (Step **17** — **`HandoffEntryService.group_followup_private_intro_key`** maps **open** / **assigned-open** / **`in_review`** / **resolved** / **none** to short message keys **`start_grp_followup_readiness_*`**, **`start_grp_followup_resolved_intro`**, or **`start_grp_followup_intro`**; **read-only**; **`grp_private`** unchanged; **no** write semantics change); **final followup/operator consolidation** — unified short private **`grp_followup`** wording + **`/contact`** / **`/human`** CTAs; admin **`group_followup_work_label`**, **`group_followup_resolution_label`** aligned to the same **queued / assigned / in progress / closed** mental model as **`group_followup_queue_state`** (**read-side string changes only**); tests **`test_group_followup_phase7_consolidation`**, chain tests updated; **no** new workflow mutations, **no** API shape changes, **no** public/Mini App churn. **No** automatic operator assignment **from the Telegram `grp_*` bot paths**, **no** booking/payment initiation from Phase **7** **`grp_*`** paths. **Phase 7.1 — tour sales mode** (**separate** from closed Phase **7** **`grp_followup_*`**): **Steps 1–5** are **completed** (admin **`tour.sales_mode`**, backend **`TourSalesModePolicyService`**, Mini App read-side, private bot read-side, **narrow** operator-assisted **full-bus** handoff context — **not** direct whole-bus booking); **Railway production** was **stabilized** after **`tours.sales_mode`** DDL was applied — see **Production stabilization after Phase 7.1 deploy** below (**feature work** vs **schema-drift incident** are distinct). **Next:** **Step 6** (product/design review — whether **direct whole-bus self-service** is needed) — **Next Safe Step**. **Do not** reopen **Phase 7** **`grp_followup_*`** micro-slices by default. **Deploy-critical:** **Phase 7.1** app code **must not** be deployed to a target environment unless the **`tours.sales_mode`** migration (**Alembic `20260416_06`**) is applied there as well — run **`python -m alembic upgrade head`** (or equivalent) **before** or **with** deploy; details **`COMMIT_PUSH_DEPLOY.md`**. Design reference: **`docs/TOUR_SALES_MODE_DESIGN.md`**. **Phase 6** / **`docs/PHASE_6_REVIEW.md`** — historical admin closure. **Not** **Phase 6 / Step 31**, **not** **admin payment** mutation. **Phase 5** — do **not** resume old **Step 4–5** narratives. Use **`Next Safe Step`** + **Current Status** + **`docs/PHASE_7_REVIEW.md`**.

## Current Status

### Current continuity state
- **V2 supplier marketplace — Track 0 (freeze) — completed (documentation):** **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`**.
- **V2 supplier marketplace — Track 1 (design acceptance / alignment) — completed (documentation):** design package confirmed against Track **0** (Layer A preserved; Layers B/C are extensions; **no** silent booking/payment semantic change; **no** broad Phase **7** **`grp_followup_*`** reopening; **moderated** publication; RFQ **separate** from normal order lifecycle until explicit bridge). Record: **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`** (Track **1** section).
- **V2 supplier marketplace — Track 2 (Supplier Admin Foundation) — completed (implementation, stabilization reviewed):** additive **Layer B** only — new tables **`suppliers`**, **`supplier_api_credentials`** (hashed bearer tokens), **`supplier_offers`** (draft / **`ready_for_moderation`**); **`POST /admin/suppliers`** bootstraps supplier + one-time API token (central admin, **`ADMIN_API_TOKEN`**); **`/supplier-admin/offers`** CRUD scoped by supplier token; **no** customer catalog/checkout wiring; **no** `Tour` / `Order` / `Payment` schema changes; reuse of Postgres enum **`tour_sales_mode`** on offers is **column-level only** on **`supplier_offers`** (does not alter core **`tours`**). Alembic **`20260417_07`**. Deploy gate: **`migrate → deploy → smoke`** (see **`COMMIT_PUSH_DEPLOY.md`**).
- **V2 supplier marketplace — Track 3 (Supplier offer publication / moderation) — completed (implementation, stabilization reviewed):** extends **`supplier_offer_lifecycle`** with **`approved`**, **`rejected`**, **`published`** and moderation/showcase columns (**Alembic `20260418_08`**); moderation/publish routes are **central admin only** under the same **`ADMIN_API_TOKEN`** gate as **`/admin/*`** — **`GET /admin/supplier-offers`**, **`POST .../moderation/approve`**, **`POST .../moderation/reject`**, **`POST .../publish`** (Telegram channel via **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`** + bot token); **suppliers cannot** set moderation/publish states or edit **`approved`**/**`published`** offers (**`SupplierOfferService`** guards); **`publish`** requires prior **`approved`** (rejected/draft/ready cannot publish); private **`/start supoffer_<id>`** intro only when offer is **`published`** — then existing catalog/Mini App CTAs (**Layer A** unchanged).
- **V2 supplier marketplace — Track 4 (Custom request marketplace foundation) — completed (implementation, stabilization reviewed):** additive **Layer C** only — new tables **`custom_marketplace_requests`**, **`supplier_custom_request_responses`** (**Alembic `20260421_10`**); **no** **`orders` / `payments` / `tours`** DDL; RFQ lifecycle is **separate** from normal booking (**no** order rows, **no** reservation/payment wiring). **Intake:** **`POST /mini-app/custom-requests`**, private **`/custom_request`** FSM, Mini App Help → custom request route. **Suppliers:** **`GET/PUT /supplier-admin/custom-requests`** (list open requests, detail, **`declined`/`proposed`** response upsert — broadcast MVP, not bidding). **Admin:** **`GET/PATCH /admin/custom-requests`**. **Track 3** publication and **Track 2** supplier-offer CRUD/moderation assumptions **unchanged**. **Stabilization:** **`docs/CURSOR_PROMPT_TRACK_4_STABILIZATION_AND_REVIEW_V2.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §25.
- **V2 supplier marketplace — Track 5a (Commercial resolution selection foundation) — completed (implementation, stabilization reviewed):** extends **`custom_marketplace_requests`** only (**Alembic `20260422_11`**) with **`selected_supplier_response_id`** (FK → **`supplier_custom_request_responses`**, **`ON DELETE SET NULL`**), **`commercial_resolution_kind`** (**`assisted_closure`** / **`external_record`**), and new request statuses (**`under_review`**, **`supplier_selected`**, **`closed_assisted`**, **`closed_external`**; legacy **`fulfilled`** rows migrated to **`closed_assisted`**). **Admin:** dedicated **`POST /admin/custom-requests/{id}/resolution`** for commercial states; **`PATCH /admin/custom-requests/{id}`** **cannot** set **`supplier_selected`**, **`closed_*`**, or legacy **`fulfilled`** (contract enforced in **`AdminCustomRequestPatch`**). **Selection integrity:** winning response must be **`proposed`** and **`request_id`** must match (**`CustomMarketplaceRequestService.admin_apply_resolution`**). **Suppliers:** responses only while **`open`** or **`under_review`**; list/detail include won requests after commercial closure. **Customer:** minimal read-only **`GET /mini-app/custom-requests`** (+ detail by id) with **`customer_visible_summary`** — **no** quote-comparison UI, **no** self-serve winner pick. **Explicit non-goals (verified):** **no** `Order` / reservation / payment session creation from RFQ, **no** checkout redesign, **no** ranking/auction, **no** Layer A service calls from resolution code paths. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §26, **`docs/CURSOR_PROMPT_TRACK_5A_STABILIZATION_AND_REVIEW.md`** (prompt). **Deploy gate:** **`COMMIT_PUSH_DEPLOY.md`** (**`20260422_11`**). **Forward:** Track **5b.1** bridge persistence (**bullet below**); **5b.2+** — invoke Layer A hold/payment only when explicitly scoped — run Track **0** §4–§5 before any booking execution change.
- **V2 supplier marketplace — Track 5b.1 (RFQ booking bridge record) — completed (implementation + stabilization review):** Alembic **`20260423_12`** — table **`custom_request_booking_bridges`**, enum **`custom_request_booking_bridge_status`**; **admin-only** **`POST` / `PATCH /admin/custom-requests/{id}/booking-bridge`** (explicit trigger — **not** a side effect of resolution); admin detail includes **`booking_bridge`** (latest row). **No** `Order` creation, **no** **`TemporaryReservationService`**, **no** payment sessions. Eligibility: request **`supplier_selected`** or **`closed_assisted`** with **`selected_supplier_response_id`** pointing at a **`proposed`** response for the **same** **`request_id`** (**`CustomRequestBookingBridgeService._validate_eligibility`**). **Active-bridge** cap: at most one row in **`pending_validation`**, **`ready`**, **`linked_tour`**, **`customer_notified`** per request — second **`POST` → 409** (application check; see §27 for concurrency note). Optional **`tour_id`**: **`open_for_sale`**, future **`departure_datetime`**, **`sales_deadline`** null or future, **`seats_available` ≥ 1** — **does not** evaluate **`tour.sales_mode`**; linking **`full_bus`** is **metadata only** (no Layer A invocation); **5b.2+** must apply **`TourSalesModePolicyService`** before any self-serve checkout. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §27; deploy **`COMMIT_PUSH_DEPLOY.md`** (**`20260423_12`**).
- **V2 supplier marketplace — Track 5b.2 (RFQ bridge execution entry) — completed (implementation + stabilization review):** Mini App **`GET /mini-app/custom-requests/{id}/booking-bridge/preparation`**, **`POST .../booking-bridge/reservations`** — explicit customer entry only; **`TourSalesModePolicyService`** gate; reuses **`MiniAppReservationPreparationService`** + **`MiniAppBookingService.create_temporary_reservation`**; **`full_bus`** blocked (assisted message / **400** on hold); **no** new payment path; bridge → **`customer_notified`** after successful hold only. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §28 (closure subsection).
- **V2 supplier marketplace — Track 5b.3a (RFQ supplier policy fields + effective commercial execution resolver) — completed (implementation + stabilization review):** Alembic **`20260424_13`** — nullable **`supplier_declared_sales_mode`** / **`supplier_declared_payment_mode`** on **`supplier_custom_request_responses`** (reuse **`tour_sales_mode`**, **`supplier_offer_payment_mode`** enums). **Proposed** supplier **`PUT .../response`** **must** declare both fields; **`declined`** clears them; **`full_bus` + `platform_checkout`** rejected at validation. **`EffectiveCommercialExecutionPolicyService`** composes **`TourSalesModePolicyService`**, supplier declaration, and Track **5a** external signals — **narrows** self-serve vs tour-only gate (assisted / incomplete / external blocks platform self-serve and **`platform_checkout_allowed`**). Bridge execution (**5b.2** routes) uses this resolver; **`sales_mode_policy`** on preparation responses **unchanged** (additive **`effective_execution_policy`**). Admin **`GET /admin/custom-requests/{id}`** adds **`effective_execution_policy`** when bridge has **`tour_id`**; response reads expose supplier-declared fields. **No** payment entry/sessions, **no** bridge payment route, **no** checkout changes. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §29; deploy **`COMMIT_PUSH_DEPLOY.md`** (**`20260424_13`**).
- **V2 supplier marketplace — Track 5b.3b (Bridge payment eligibility + existing payment-entry reuse) — completed (implementation + stabilization review):** Mini App **`GET /mini-app/custom-requests/{id}/booking-bridge/payment-eligibility`** (`telegram_user_id`, **`order_id`** from bridge hold) — read-only; **`payment_entry_allowed`** only when **`platform_checkout_allowed`**, bridge/order/tour/user alignment, and **`PaymentEntryService.is_order_valid_for_payment_entry`** (same rules as **`start_payment_entry`**). Customer then uses **existing** **`POST /mini-app/orders/{order_id}/payment-entry`** — **no** new payment provider, **no** payment rows from eligibility. **No** migration. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §30 (closure subsection); **`COMMIT_PUSH_DEPLOY.md`** (smoke note).
- **V2 supplier marketplace — Track 5c (RFQ Mini App UX wiring — bridge execution + payment continuation) — completed (implementation + stabilization reviewed):** Flet route **`/custom-requests/{request_id}/bridge`** drives **`RfqBridgeExecutionScreen`**, calling **existing** **`GET/POST .../booking-bridge/preparation|reservations`** and **`GET .../payment-eligibility`**; when **`self_service_available`** is false, show blocked/assisted copy (**no** reserve/pay CTAs); otherwise reuse seat/boarding + **`preparation-summary`** preview, then **`Continue to payment`** only if the hold is active **and** **`payment_entry_allowed`**, then **`open_payment_entry`** → standard **`PaymentEntryScreen`** (**`POST .../payment-entry`** only). Optional entry: custom-request success dialog CTA or deep link. **No** migration. **Stabilization review:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §31 (closure subsection); **`COMMIT_PUSH_DEPLOY.md`** (Track **5c** note).
- **V2 supplier marketplace — Track 5d (Mini App “My Requests” / RFQ status hub) — completed (implementation + stabilization reviewed):** Catalog **`My requests`** → **`/my-requests`** (**`MyRequestsListScreen`**, existing **`GET /mini-app/custom-requests`**); detail **`/my-requests/{id}`** (**`MyRequestDetailScreen`**, existing **`GET .../{id}`** + bridge prep + **`GET /mini-app/bookings`** to match linked **`tour_code`**; payment eligibility only with bridge context + active hold). User-facing status/type labels (**no** raw enums in UI); dominant CTA reuses **`open_rfq_bridge_booking`**, **`open_payment_entry`**, **`open_booking_detail`** — **no** second continuation path. **No** migration. **Stabilization review:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §32 (closure subsection); **`COMMIT_PUSH_DEPLOY.md`** (Track **5d** note).
- **V2 supplier marketplace — Track 5e (Bridge supersede / cancel lifecycle) — completed (implementation + stabilization reviewed):** Admin **`POST /admin/custom-requests/{id}/booking-bridge/close`** (`superseded` / `cancelled`, optional **`admin_note`**) and **`POST .../booking-bridge/replace`** (supersede active row if present + **`create_bridge`** in same session — **no** active-bridge **409** window). Customer **`GET /mini-app/custom-requests/{id}`** adds optional **`latest_booking_bridge_status`**, **`latest_booking_bridge_tour_code`** (additive read contract). Bridge-gated Mini App endpoints (**preparation** / **reservations** / **payment-eligibility**) **fail closed** when no active bridge (terminal **`superseded`**/**`cancelled`** excluded from active set). **No** migration; **no** `Order` / **`Payment`** writes from bridge close; **no** request-status side effects. **My Requests** hub: terminal-bridge copy + **Layer A** order-based CTAs when a matching booking/hold exists on linked tour code. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §33; **`COMMIT_PUSH_DEPLOY.md`** (Track **5e** note).
- **V2 supplier marketplace — Track 5f v1 (Customer multi-quote summary / aggregate visibility) — completed (implementation + stabilization reviewed):** **`GET /mini-app/custom-requests/{id}`** adds **`proposed_response_count`** (**`proposed`** only), **`offers_received_hint`** (neutral English MVP copy), **`selected_offer_summary`** (allowlisted read-only snippet for **admin-selected** **`proposed`** response only — **no** supplier identity; excerpt capped). **`SupplierCustomRequestResponseRepository.count_proposed_for_request`**. **My Requests** detail renders hint + snippet — **no** new CTAs, **no** comparison UI, **no** customer choice. **No** migration; **no** new write routes; **no** bridge/payment logic change. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §34; **`COMMIT_PUSH_DEPLOY.md`** (Track **5f v1** note).
- **V2 supplier marketplace — Track 5g.1 (Commercial mode classification — read-side only) — completed (implementation + stabilization reviewed):** additive **`commercial_mode`** on **`MiniAppTourDetailRead`** (**`GET /mini-app/tours/{tour_code}`**) — derived from authoritative **`Tour.sales_mode`** (**`per_seat` → `supplier_route_per_seat`**, **`full_bus` → `supplier_route_full_bus`**); additive **`commercial_mode`** on **`MiniAppCustomRequestCustomerDetailRead`** (**`GET /mini-app/custom-requests/{id}`**) — always **`custom_bus_rental_request`** (Track **5g** Mode **3** / RFQ). Enum **`CustomerCommercialMode`**; mapper **`commercial_mode_for_catalog_tour_sales_mode`** (**`app/services/customer_commercial_mode_read.py`**). **No** migration; **no** booking/payment/bridge/RFQ execution/CTA/bot-routing/admin-workflow changes; **no** change to **5f v1** field meanings. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §35; **`COMMIT_PUSH_DEPLOY.md`** (Track **5g.1** note). Design gate: **`docs/CURSOR_PROMPT_TRACK_5G_THREE_COMMERCIAL_MODES_DESIGN_GATE.md`**.
- **Phase 7** (group→private→**`group_followup_start`**→admin) remains **closed enough for staging/MVP** — **`docs/PHASE_7_REVIEW.md`**; **do not** reopen old **Phase 7** followup/operator micro-slices unless product **explicitly** rescopes.
- **Current active sub-track:** **Phase 7.1 — tour sales mode** (**separate** from the closed **Phase 7** **`group_followup_*`** track).
- **Completed checkpoints in this sub-track:** **Steps 1–5** — **Step 1** admin/source-of-truth **`tour.sales_mode`**; **Step 2** backend **`TourSalesModePolicyService`** / **`TourSalesModePolicyRead`**; **Step 3** Mini App read-side adaptation to policy; **Step 4** private bot read-side adaptation to policy; **Step 5** operator-assisted full-bus path (**structured** handoff **`reason`**, tour + sales-mode context on **private bot** + **Mini App** assistance, **admin** read flags — **no** direct whole-bus reservation/payment). Summaries: **Completed Steps** → **Phase 7.1 / Sales Mode / Steps 1–4 completed** and **Phase 7.1 / Sales Mode / Step 5 completed**. Verification: **Verified** (below); production smoke: **Production stabilization after Phase 7.1 deploy** (below).
- **Next work in this sub-track:** **Phase 7.1 / Sales Mode / Step 6** — review whether **direct whole-bus self-service** is needed at all; **design explicitly** before any implementation — **Next Safe Step**. Operational deploy/migration gate: **`COMMIT_PUSH_DEPLOY.md`** (repo root).

The **latest approved checkpoint** is **Phase 7 review / closure accepted** (`docs/PHASE_7_REVIEW.md`) — **implementation** through **final consolidation** (**documentation + code**) is **complete**; **Phase 7** is **closed** for the **narrow** group→private→**`group_followup_start`**→admin chain (**no** further **Phase 7** micro-steps by default). **Phase 7 implemented surface (Steps 1–17 + consolidation polish):** Step **1** — **`docs/GROUP_ASSISTANT_RULES.md`**; Step **2** — **group** + **handoff** trigger helpers (`evaluate_group_trigger`, `evaluate_handoff_triggers`, …); Step **3** — **minimal group runtime gating**; Step **4** — **category-aware** short escalation wording in group replies; Step **5** — **private CTA** **`t.me`** deep-link foundation (`grp_private` / `grp_followup`); Step **6** — **narrow private `/start`** branching: **`grp_private`** / **`grp_followup`** intros + catalog; legacy **`tour_*`** **unchanged**; Step **7** — **narrow** **`handoffs`** persistence on **`/start grp_followup`** (**reason** **`group_followup_start`**; dedupe **open**; **`grp_private`** — **no** write); Step **8** — **focused runtime/bot-flow tests** (**`test_private_entry_grp_followup_chain.py`**); Step **9** — **admin read visibility** (**`is_group_followup`**, **`source_label`**); Step **10** — **`POST /admin/handoffs/{handoff_id}/assign-operator`** — **only** **`reason=group_followup_start`**; same narrow assignment rules as Step **21**; **`POST .../assign`** for other reasons **unchanged**; Step **11** — **read-side work-state** for **`group_followup_start`**: **`is_assigned_group_followup`**, **`group_followup_work_label`** on handoff **list**, **detail**, order-detail **`handoffs`** — **derived only**; Step **12** — **`POST /admin/handoffs/{handoff_id}/mark-in-work`** — **only** **`reason=group_followup_start`** with **`assigned_operator_id`** set; **`open` → `in_review`**; **`in_review`** idempotent; **`closed`** rejected; Steps **13–14** (combined) — **`POST /admin/handoffs/{handoff_id}/resolve-group-followup`** — **only** **`reason=group_followup_start`**; **`in_review` → `closed`**; **`closed`** idempotent (**no** extra write); **`open`** rejected; wrong reason / missing handoff → safe client errors; **read-only** **`group_followup_resolution_label`** on admin reads when **`group_followup_start`** is **`closed`** (other reasons **do not** get this label); Step **15** — **read-only** **`group_followup_queue_state`** on the same admin/order-detail handoff surfaces (**`awaiting_assignment`**, **`assigned_open`**, **`in_work`**, **`resolved`**, or **`null`** for non-**`group_followup_start`**); narrow **`GET /admin/handoffs?group_followup_queue=`** filter (AND with **`status`** when both set); Step **16** — **private** **`/start grp_followup`**: **`should_show_group_followup_resolved_confirmation`** (superseded for intro selection by Step **17** **`group_followup_private_intro_key`**, predicate retained for tests) — resolved copy when **no** **open** **`group_followup_start`** and **latest** is **`closed`**; Step **17** — **`group_followup_private_intro_key`** selects **`start_grp_followup_readiness_pending`** (open, unassigned), **`start_grp_followup_readiness_assigned`** (open + assignment), **`start_grp_followup_readiness_in_progress`** (**`in_review`**), **`start_grp_followup_resolved_intro`**, or **`start_grp_followup_intro`**; **no** operator IDs, timing promises, or chat delivery; **`_persist_group_followup_handoff`** and Step **7** dedupe **unchanged**; tests **`test_handoff_entry`**, **`test_private_entry_grp_followup_chain`**; **final consolidation** — **`app/bot/messages.py`** + **`app/services/admin_handoff_queue.py`** wording alignment; **`test_group_followup_phase7_consolidation`**, **`test_api_admin`** / **`test_admin_handoff_group_followup_visibility`** expectations refreshed — **no** new persistence, **no** enum/API surface changes, **no** assign/in-work/resolve semantics change, **no** booking/payment/public/Mini App changes. **No** automatic assignment **from Telegram `grp_*` paths**; **no** booking/payment initiation from Phase **7** **`grp_*`** paths. **Step 1** rules: **`docs/GROUP_ASSISTANT_RULES.md`**.

**Still not implemented (explicit):** **Phase 7.1** **Step 6+** — optional **direct whole-bus self-service** (only after **explicit** product/design approval — see **Next Safe Step**), **`full_bus_price`**, **`bus_capacity`**, whole-bus payment, dedicated full-bus **workflow engine** beyond **existing** handoff/support surfaces, pricing expansion, core reservation engine rewrite — **only when explicitly scoped**; **operator** two-way **chat** / free-form **messaging**, **handoff push notification** subsystem, **broad** **claim/takeover** engine, **full** **operator workflow engine**, **full** group assistant, **full** private “assistant” flow redesign; **booking/payment resolution** via Phase **7** **`grp_*`** beyond existing private/Mini App flows; **long-form** group replies; **handoff** rows from **group** chat runtime (Phase **7** Steps **3–4** remain **reply-only**). **Do not** mix **`per_seat` / `full_bus`** policy into Phase **7** handoff code **ad hoc**. **Do not** expand old **Phase 7** **`grp_followup_*`** chain by default. **Live** Telegram validation **may** still depend on **Railway** / bot deploy health.

**Baseline still true from Phase 6 closure:** **read-only** **`move_placement_snapshot`** on **`GET /admin/orders/{order_id}`** (**Phase 6 / Step 30**); **narrow** **`POST /admin/orders/{order_id}/move`** (**Step 29**); admin handoff/order surfaces unchanged in meaning — see **Completed Steps** / Phase 6.

**Phase 6 / Step 29** (still in baseline): **narrow** **`POST /admin/orders/{order_id}/move`** (**`app/services/admin_order_move_write.py`**); guarded by Step **28** readiness; **no** payment-row writes, **no** reconciliation/webhook changes.

**Admin order read** on **`GET /admin/orders/{order_id}`**: **Step 16** correction visibility, **Step 17** action preview, **Step 27** lifecycle mapping (incl. **`ready_for_departure_paid`**), **Step 28** move-readiness (**`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`**), **Step 30** **`move_placement_snapshot`** (current placement inspection only). Read-only hints do **not** authorize a move; **POST /move** enforces readiness in the service layer.

Order **write** surface: **`app/services/admin_order_write.py`** — **`POST /admin/orders/{order_id}/mark-cancelled-by-operator`** (Step **23**), **`mark-duplicate`** (Step **24**), **`mark-no-show`** (Step **25**), **`mark-ready-for-departure`** (Step **26**); **`app/services/admin_order_move_write.py`** — **`POST /admin/orders/{order_id}/move`** (Step **29**); handoff writes Steps **19–22** + Phase **7** / Step **12** **`mark-in-work`** + Phase **7** / Steps **13–14** **`resolve-group-followup`** (**`app/services/admin_handoff_write.py`**).

**Agreed narrow semantics (combined):**
- **`mark-in-review`:** **`open` → `in_review`**; **`in_review` → idempotent success** (no extra write); **`closed` → 400**; missing handoff → **404**.
- **`close`:** **`in_review` → `closed`**; **`closed` → idempotent success**; **`open` → 400** (`handoff_close_not_allowed`); **any other unexpected status → same client error shape** (narrow safe rejection); missing handoff → **404**. Admin **`close`** is intentionally **not** a shortcut from **`open`** — operators are expected to use **`mark-in-review`** first.
- **`assign`** (Step **21**): body **`{ "assigned_operator_id": <users.id> }`**. Only **`open`** or **`in_review`**; **`closed` → 400** (`handoff_assign_not_allowed`). Operator user must exist (**`handoff_assign_operator_not_found`**). **First** set of **`assigned_operator_id`** from **`null`**, or **idempotent** repeat with the **same** id — **reassigning to a different operator when one is already set** → **400** (`handoff_reassign_not_allowed`) — **no unassign** in this slice (still).
- **`assign-operator`** (Phase 7 / Step **10**): **`POST /admin/handoffs/{handoff_id}/assign-operator`** — same body and **same** assignment rules as **`assign`** (Step **21**), but **only** when **`reason=group_followup_start`**; otherwise **`400`** (`handoff_assign_group_followup_reason_only` + **`current_reason`**). Does **not** replace or broaden general **`POST .../assign`**.
- **`mark-in-work`** (Phase 7 / Step **12**): **`POST /admin/handoffs/{handoff_id}/mark-in-work`** — **only** when **`reason=group_followup_start`** and **`assigned_operator_id`** is set; **`open` → `in_review`**; **`in_review` → idempotent** (no extra write); **`closed` → 400** (`handoff_mark_in_work_not_allowed`); wrong reason → **`handoff_mark_in_work_reason_only`**; no assignment → **`handoff_mark_in_work_assignment_required`**. **Reuses** existing **`in_review`** status (**no** new column). Does **not** change **`assign`** / **`assign-operator`** semantics.
- **`resolve-group-followup`** (Phase 7 / Steps **13–14**): **`POST /admin/handoffs/{handoff_id}/resolve-group-followup`** — **only** when **`reason=group_followup_start`**; **`in_review` → `closed`**; **`closed` → idempotent success** (no extra write); **`open` → 400** (`handoff_resolve_group_followup_not_allowed` + **`current_status`**); wrong reason → **`400`** (`handoff_resolve_group_followup_reason_only` + **`current_reason`**); missing handoff → **404**. **Does not** replace or broaden general Step **20** **`close`**. Paired **read-only** signal: **`group_followup_resolution_label`** on **`GET /admin/handoffs`**, handoff detail, order-detail **`handoffs`** when **`reason=group_followup_start`** and **`status=closed`** only.
- **`reopen`** (Step **22**): **`closed` → `open`**; **`open` → idempotent success**; **`in_review` → 400** (`handoff_reopen_not_allowed`); missing handoff → **404**. Only **`status`** is updated; **`assigned_operator_id` is preserved** (not cleared) on reopen.
- **`mark-cancelled-by-operator`** (Step **23**): **active temporary hold** only (`booking_status=reserved`, `payment_status=awaiting_payment`, `cancellation_status=active`, `reservation_expires_at` **not** `null`); **`payment_status=paid` → 400**; already **`cancellation_status=cancelled_by_operator` → idempotent**; any other disallowed combination → **400**; missing order → **404**; on success: seat restore (same narrow rule as **reservation expiry**), `payment_status→unpaid`, `cancellation_status→cancelled_by_operator`, `reservation_expires_at→null`, **`booking_status` unchanged**; **no** payment-row mutation, **no** refund/reconciliation/webhook change. **Order read** (**Steps 16–17**) still exposes lifecycle, correction visibility, and action preview (unchanged).
- **`mark-duplicate`** (Step **24**): **active temporary hold** (same predicate as Step **23**) **or** **expired unpaid hold** (`reserved` + `unpaid` + `cancelled_no_payment`); **`payment_status=paid` → 400**; already **`cancellation_status=duplicate` → idempotent**; active hold: seat restore + `unpaid` / `duplicate` / `reservation_expires_at→null`; expired hold: **only** `cancellation_status→duplicate` (no duplicate seat restore); **no** payment-row mutation, **no** merge flow. **Order read** fields unchanged in meaning.
- **`mark-no-show`** (Step **25**): **confirmed** + **paid** + **`cancellation_status=active`** only; **`tour.departure_datetime` must be in the past** (UTC); already **`booking_status=no_show`** and **`cancellation_status=no_show` → idempotent**; wrong statuses → **400**; valid statuses but **departure not in past** → **400** (`reason` **`departure_not_in_past`**); on success: **`booking_status`/`cancellation_status` → `no_show`**; **`payment_status` unchanged**; **no** seat restoration, **no** payment-row mutation; missing order or missing tour → **404**.
- **`mark-ready-for-departure`** (Step **26**): **confirmed** + **paid** + **`cancellation_status=active`** only; **`tour.departure_datetime` must be strictly in the future** (UTC); already **`booking_status=ready_for_departure`** + paid + active → **idempotent**; departure not in future → **400** (`reason` **`departure_not_in_future`**); on success: **`booking_status` → `ready_for_departure` only**; **`payment_status` / `cancellation_status` unchanged**; **no** seat mutation, **no** payment-row mutation; missing order or tour → **404**. **Step 27** adds read-side **`ready_for_departure_paid`** lifecycle labeling for that steady state (see below).
- **Lifecycle read (Step 27):** **`ready_for_departure_paid`** applies only to **`ready_for_departure` + paid + active**; list filter **`lifecycle_kind=ready_for_departure_paid`** matches **`describe_order_admin_lifecycle`**; action preview treats this like **confirmed paid** (clean / no spurious **`manual_review`** from lifecycle alone). **Not** a mutation; **no** repository writes.
- **Move readiness (Step 28):** **`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`** on **`GET /admin/orders/{order_id}`** only; grounded in persisted order/tour + lifecycle + correction + open handoffs; blocker codes include **`payment_correction_manual_review`**, **`open_handoff_open`**, **`order_not_paid`**, **`cancellation_not_active`**, **`lifecycle_not_move_candidate`**, **`tour_departure_not_in_future`**. **Read-only** — hints **do not** perform a move by themselves.
- **Move mutation (Step 29):** **`POST /admin/orders/{order_id}/move`** — rejects with **`order_move_not_ready`** when Step **28**-style readiness would block; validates target tour + boarding on target tour; same-tour same-boarding **idempotent**; same-tour different-boarding updates **`boarding_point_id`** only; cross-tour restores source seats and deducts target (**no** oversell); **`total_amount`** and **payment rows** unchanged by policy.
- **Move placement inspection (Step 30):** **`move_placement_snapshot`** on order detail — **current** FK placement + timestamps **only**; **`timeline_available`** stays **false** until a future persisted-audit slice.

**Step 18** read API: **`GET /admin/handoffs`**, **`GET /admin/handoffs/{handoff_id}`** (**`is_open`**, **`needs_attention`**, **`age_bucket`**, **`assigned_operator_id`**, plus Phase **7** / Step **9** **`is_group_followup`**, **`source_label`**, Step **11** **`is_assigned_group_followup`**, **`group_followup_work_label`**, Steps **13–14** **`group_followup_resolution_label`** when **`group_followup_start`** is **`closed`**, Step **15** **`group_followup_queue_state`** for **`group_followup_start`** triage only, optional **`group_followup_queue`** list filter on **`GET /admin/handoffs`**, plus Phase **7.1** / Step **5** **`is_full_bus_sales_assistance`**, **`full_bus_sales_assistance_label`**, **`assistance_context_tour_code`** derived from structured **`full_bus_sales_assistance`** **`reason`** payloads). **Private bot (Phase 7 / Steps 16–17 + consolidation):** **`/start grp_followup`** uses **`HandoffEntryService.group_followup_private_intro_key`** — coherent short copy + **`/contact`** / **`/human`** CTAs per state (**generic**, **queued**, **assigned**, **in progress**, **closed**); admin list/detail **`group_followup_work_label`** / **`group_followup_resolution_label`** use aligned **read-side** phrasing (**no** new admin routes or response fields). **Phase 7** narrow writes: Step **10** **`POST /admin/handoffs/{handoff_id}/assign-operator`**; Step **12** **`POST /admin/handoffs/{handoff_id}/mark-in-work`**; Steps **13–14** **`POST /admin/handoffs/{handoff_id}/resolve-group-followup`** — see **Agreed narrow semantics** above. **Still not implemented:** **unassign**, broader **reassignment** policy redesign, full **operator workflow engine**, **notifications** from admin handoff actions, **public** customer handoff flow changes, **refund / capture / cancel-payment** admin actions, **broad** order workflow editor, **merge** tooling, **persisted** move timeline / audit history, **full** admin SPA, **operator↔customer chat**.

**Phase 6 / Steps 1–30** (completed): **`ADMIN_API_TOKEN`**; tours, boarding, translations, archive/unarchive; orders **16–17** (read + preview) + **Steps 27–28** (lifecycle **`ready_for_departure_paid`** + move-readiness) + **Step 30** (**`move_placement_snapshot`**) + **Step 29** (narrow **move** **POST**) + **Steps 23–26** (cancel + duplicate + no-show + ready-for-departure); handoff **queue read** + **four** narrow mutations (**status progression + assign + reopen**). **Public** booking/payment/waitlist/customer handoff flows were **not** retargeted by these admin slices — they remain as in Phase 5 acceptance.

**Historical (closed for MVP narrative):** **Phase 5 (Mini App MVP) accepted** for staging; details in `docs/PHASE_5_ACCEPTANCE_SUMMARY.md` — **not** the forward checkpoint.

**Next work:** **Phase 7.1 — tour sales mode** — **Step 6** (review / design gate for **direct whole-bus self-service** — see **Next Safe Step**); design reference **`docs/TOUR_SALES_MODE_DESIGN.md`**; keep **`docs/CHAT_HANDOFF.md`**, **`docs/IMPLEMENTATION_PLAN.md`**, **`docs/TECH_SPEC_TOURS_BOT.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** aligned; routine staging/production smoke when deploy changes — **not** default **Phase 7** **`grp_followup`** code unless product **rescopes** Phase **7**. **Admin payment mutations** remain **not** the default.

### Operational note (production — Step 6 schema recovery)
After Step 6 backend shipped to Railway **before** production Postgres had applied Alembic revision **`20260405_04`**, the missing column **`tours.cover_media_reference`** caused **`ProgrammingError` / `UndefinedColumn`** and **500**s on routes that load tours (e.g. **`/mini-app/catalog`**, **`/mini-app/bookings`**). Root cause was **schema mismatch**, not Mini App UI logic. **Recovery completed:** migrations applied against the Railway DB (using the **public** Postgres URL and a local driver URL such as **`postgresql+psycopg://...`** where internal hostnames are not resolvable), backend **redeployed**, **`/health`**, catalog, and bookings smoke-checked. **Going forward:** any schema-changing step must include **migration apply → redeploy → smoke** for affected endpoints. Details: **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` section 17**.

### Production stabilization after Phase 7.1 deploy
This records an **operational** issue **after** Phase **7.1** Steps **1–4** shipped — **not** part of the feature definition itself.

- Deployed **Railway** application code began **reading** **`tours.sales_mode`** (ORM + API + surfaces).
- **Railway production** Postgres had **not** yet applied the Alembic migration that adds that column.
- **Runtime failures** affected **bot** and **Mini App** paths (any code loading **`Tour`**).
- **Confirmed error:** **`psycopg.errors.UndefinedColumn: column tours.sales_mode does not exist`**.
- **Resolution:** run **`python -m alembic upgrade head`** in the **Railway `Tours_BOT` service shell** (target DB reachable from that environment).
- **After migration:** **Telegram webhook** requests handled again; **`/mini-app/settings`** **200**; **`/mini-app/catalog`** **200**; **`/mini-app/tours/...`** **200**; **`/mini-app/bookings`** **200**; **`/health`** **200**; **`/healthz`** **200**.

**Deploy-critical (repeat):** **Phase 7.1** **must not** be deployed to a target environment unless the **`tours.sales_mode`** migration is applied there as well — **`COMMIT_PUSH_DEPLOY.md`** (**Deploy-critical**), **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` §17**.

## Current Phase

**Current phase (forward work):** **Phase 7 — Group Assistant And Operator Handoff** — **closed** (**implementation** Steps **1–17** + **final consolidation** + **review / closure** in **`docs/PHASE_7_REVIEW.md`**). **Active implementation sub-track:** **Phase 7.1 — tour sales mode** — **Steps 1–5 completed**; **Step 6** is **next** (see **Next Safe Step**). Phase 6 narrow admin API track **closed** through **Step 30** — see **`docs/PHASE_6_REVIEW.md`**.

**Latest approved checkpoint:** **Phase 7 review / closure accepted** — narrative closure in **`docs/PHASE_7_REVIEW.md`**; **shipped** surface remains: core chain (**Steps 1–17**) plus **read-side polish** (private **`grp_followup`** + admin **`group_followup_*`** labels share one **queued / assigned / in progress / closed** model with **`group_followup_queue_state`**); **`HandoffEntryService.group_followup_private_intro_key`** behavior as shipped; **`should_show_group_followup_resolved_confirmation`** retained for tests; **no** new workflow capabilities added in closure pass. **`grp_private`** unchanged. **Step 1** docs: **`docs/GROUP_ASSISTANT_RULES.md`**. **Also shipped (separate sub-track):** **Phase 7.1 / Sales Mode / Steps 1–5** — admin **`tour.sales_mode`**, **`TourSalesModePolicyService`**, Mini App + private bot read-side policy reflection, **Step 5** structured **full-bus assistance** handoff **`reason`** + **admin** triage fields — see **Completed Steps** → **Phase 7.1 / Sales Mode / Steps 1–4 completed** and **Phase 7.1 / Sales Mode / Step 5 completed**; **Railway production** stabilized after **`tours.sales_mode`** migration (**Production stabilization after Phase 7.1 deploy** above). **Prior code baseline** unchanged: **Phase 6 / Step 30** **`move_placement_snapshot`**, **Step 29** move **POST**, admin handoffs/orders as implemented. **Admin payment mutations** remain **intentionally postponed** (see **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** **§1f**). **Still not:** **full** group assistant; **operator↔customer chat**; **handoff push notifications**; **broad** **claim/takeover** engine; **broad** **operator workflow engine**; **booking/payment resolution** **via** the Phase **7** **`grp_*`** chain beyond existing private/Mini App flows; **persisted** move audit/timeline rows; **unassign**; broader **reassignment** redesign; **refund / capture / cancel-payment**; **Phase 7.1** **Step 6+** items (**Next Safe Step**, **Postponed** in **Current Architecture State**). Internal **ops** JSON stays **separate** from **`/admin/*`**.

**Earlier checkpoints:** Phase 7 **final consolidation** (private + admin **read-side** wording alignment); Phase 7 / Step 17 (**private** **`group_followup_private_intro_key`** + **`start_grp_followup_readiness_*`**); Phase 7 / Step 16 (**private** **`start_grp_followup_resolved_intro`** path); Phase 7 / Step 15 (**`group_followup_queue_state`** + **`group_followup_queue`** list filter); Combined Phase 7 / Steps 13–14 (**`resolve-group-followup`** + **`group_followup_resolution_label`**); Phase 7 / Step 12 (**`mark-in-work`** for **assigned** **`group_followup_start`**); Phase 7 / Step 11 (**read-side** **`is_assigned_group_followup`**, **`group_followup_work_label`**); Phase 7 / Step 10 (**`assign-operator`** for **`group_followup_start`** only); Phase 7 / Step 9 (admin **`group_followup_start`** visibility — **`is_group_followup`**, **`source_label`**); Phase 7 / Step 8 (focused **`grp_followup`** chain tests); Phase 7 / Step 7 (narrow **`grp_followup`** handoff persistence); Phase 7 / Step 6 (narrow **`grp_*`** private `/start`); Phase 7 / Step 5 (private CTA deep-link foundation on group replies); Phase 7 / Step 4 (handoff-aware short replies in narrow group path); Phase 7 / Step 3 (narrow group runtime gating + default ack); Phase 7 / Step 2 (trigger helper services + unit tests); Phase 7 / Step 1 ( **`docs/GROUP_ASSISTANT_RULES.md`** — rules only); Phase 6 / Steps 1–7 (foundation through core tour patch); Phase 6 / Steps 8–10 (boarding create / patch / delete); Phase 6 / Steps 11–12 (tour translation upsert/delete); Phase 6 / Steps 13–14 (boarding point translation upsert/delete); Phase 6 / Step 15 (tour archive/unarchive); Phase 6 / Step 16 (order detail payment correction visibility); Phase 6 / Step 17 (order detail action preview); Phase 6 / Step 18 (admin handoff queue read API); Phase 6 / Step 19 (admin handoff mark-in-review); Phase 6 / Step 20 (admin handoff close-only); Phase 6 / Step 21 (admin handoff assign); Phase 6 / Step 22 (admin handoff reopen); Phase 6 / Step 23 (admin mark-cancelled-by-operator); Phase 6 / Step 24 (admin mark-duplicate); Phase 6 / Step 25 (admin mark-no-show); Phase 6 / Step 26 (admin mark-ready-for-departure); Phase 6 / Step 27 (admin lifecycle **`ready_for_departure_paid`** read refinement); Phase 6 / Step 28 (admin order move-readiness read-only fields); Phase 6 / Step 29 (admin order narrow **move** mutation); Phase 6 / Step 30 (admin **`move_placement_snapshot`** read-only); Phase 5 accepted + Phase 5 Step 20 docs (`docs/PHASE_5_ACCEPTANCE_SUMMARY.md`).

**Phase 5 (closed for MVP):** Execution checkpoints **Steps 4–19** are summarized in `docs/PHASE_5_ACCEPTANCE_SUMMARY.md` and per-step notes under `docs/PHASE_5_STEP_*_NOTES.md`; **Phase 5 / Step 20** was documentation/consolidation only (no intended production-code churn for acceptance).

**Forward:** **Next Safe Step** — do **not** use legacy Phase 5 “next step” prompts for new code.

**Optional follow-ups** (not Phase 5 blockers; prioritize with product): Telegram Web App init-data validation for Mini App APIs, real payment provider (PSP), broader handoff/waitlist customer notifications.

`docs/IMPLEMENTATION_PLAN.md` lists phases 1–9; **Step N** labels in **this** file are **project checkpoints** (not substeps inside the plan table).

## Completed Steps

### Phase 1
- Phase 1 / Step 1 completed
  - backend skeleton created
  - config/settings structure added
  - PostgreSQL setup added
  - SQLAlchemy base added
  - Alembic initialized
  - `/health` and `/healthz` added
  - modular folder layout created

- Phase 1 / Step 2 completed
  - `.gitignore` refined
  - `.env.example` refined
  - `README.md` refined with local bootstrap instructions
  - `docs/DEPLOYMENT.md` refined
  - local PostgreSQL bootstrap notes added
  - Alembic local migration workflow documented

### Phase 2
- Phase 2 / Step 1 completed
  - first core ORM models added
  - initial meaningful Alembic migration added
  - tables added:
    - users
    - tours
    - tour_translations
    - boarding_points
    - orders

- Phase 2 / Step 2 completed
  - supporting ORM models added
  - second Alembic migration added
  - tables added:
    - payments
    - waitlist
    - handoffs
    - messages
    - content_items
    - knowledge_base

- Phase 2 / Step 3 completed
  - repository layer added
  - Pydantic schemas added
  - repositories kept data-oriented
  - schemas kept separate from ORM

- Phase 2 / Step 4 completed
  - first read-oriented services added
  - service layer foundation added for:
    - catalog lookup
    - tour detail retrieval
    - boarding point retrieval
    - user profile read
    - order read
    - payment read
    - knowledge base lookup

- Phase 2 / Step 5 completed
  - safe preparation/read services added
  - services added for:
    - catalog preparation
    - language-aware tour read
    - order summary
    - payment summary

### Phase 2 Test Checkpoint
- enum persistence mismatch fixed
- enum-backed model columns now persist enum values correctly for PostgreSQL
- focused unit test slice added and passed
- repository/read/preparation layers verified by unit tests

### Phase 3
- Phase 3 / Step 1 completed
  - private bot foundation added under `app/bot/`
  - bot startup wiring added
  - private-only handlers added for:
    - `/start`
    - `/language`
    - `/tours`
    - language callbacks
    - simple tour detail browsing
  - safe deep-link style entry added for `tour_<CODE>`
  - multilingual templates/keyboards/minimal FSM state added
  - bot layer kept thin and service-driven
  - no reservation creation
  - no payment flow
  - no waitlist flow
  - no handoff workflow
  - no group behavior
  - no Mini App UI

- Phase 3 / Step 2 completed
  - private chat browsing extended for:
    - date preference via guided presets
    - destination/tour-name keyword
    - budget range when safe within one currency
  - reusable filtering kept in app service layer
  - handlers stayed thin
  - no booking/payment/waitlist/handoff logic added

- Phase 3 / Step 3 completed
  - reservation-preparation slice added
  - flow now supports:
    - selected tour
    - seat count choice
    - boarding point choice
    - multilingual reservation-preparation summary
  - summary clearly marked as preview only
  - no reservation row created yet
  - no seat mutation yet
  - no payment flow yet

- Phase 3 / Step 4 completed
  - first real temporary reservation creation added
  - implemented through app-layer `TemporaryReservationService`
  - private bot now creates a temporary reservation/order from prepared flow
  - minimal write state now includes:
    - `booking_status=reserved`
    - `payment_status=awaiting_payment`
    - `cancellation_status=active`
    - `reservation_expires_at`
  - available seats are reduced at reservation time
  - multilingual temporary reservation confirmation added
  - still postponed:
    - payment session creation
    - payment reconciliation
    - waitlist actions
    - handoff workflow
    - reminder workers
    - expiry worker execution
    - group behavior
    - Mini App UI

### Phase 4
- Phase 4 / Step 1 completed
  - first payment-entry slice added
  - implemented through `PaymentEntryService`
  - private bot now supports continue-to-payment for an existing temporary reservation
  - validates that:
    - order belongs to the user
    - order is still `reserved`
    - order is still `awaiting_payment`
    - order is not canceled
    - order has not expired
  - creates a minimal payment session/payment record tied to the order
  - reuses latest pending payment session instead of creating duplicates
  - payment step response now shows:
    - reservation reference
    - payment session reference
    - amount due
    - reservation expiry
  - uses a minimal mock/provider-agnostic payment-entry foundation
  - nothing is marked as paid yet

- Phase 4 / Step 2 completed
  - payment reconciliation slice added
  - implemented through `app/services/payment_reconciliation.py`
  - reconciliation now consumes a verified, provider-agnostic payment result payload
  - matching payment and linked order are locked during reconciliation
  - optional amount/currency validation is applied
  - confirmed payment now:
    - sets payment status to `paid`
    - updates order `payment_status` to `paid`
    - confirms a still-active reserved order
  - duplicate paid results are idempotent and harmless
  - later non-paid results do not regress an already paid order
  - supporting schema contracts added in `app/schemas/payment.py`:
    - `PaymentProviderResult`
    - `PaymentReconciliationRead`
  - repository support added for locked lookup by `(provider, external_payment_id)`

- Phase 4 / Step 3 completed
  - minimal payment webhook/API delivery slice added
  - `POST /payments/webhooks/{provider}` added in `app/api/routes/payments.py`
  - isolated webhook parsing/verification helper added in `app/api/payment_webhook.py`
  - HMAC signature verification via `X-Payment-Signature`
  - provider-agnostic payload parsing and status normalization into `PaymentProviderResult`
  - `PaymentWebhookPayload` and `PaymentWebhookResponse` added to `app/schemas/payment.py`
  - `PAYMENT_WEBHOOK_SECRET` added to config
  - payments router wired into `app/api/router.py`
  - route layer stays thin: verify, parse, delegate, respond
  - `PaymentReconciliationService` remains the only place that mutates payment/order state

- Phase 4 / Step 4 completed
  - first reservation expiry automation slice added
  - implemented through `app/services/reservation_expiry.py`
  - thin worker entry added in `app/workers/reservation_expiry.py`
  - eligible expired temporary reservations now:
    - keep `booking_status=reserved`
    - set `payment_status=unpaid`
    - set `cancellation_status=cancelled_no_payment`
    - clear `reservation_expires_at`
  - seats are restored safely to the related tour
  - expiry behavior is idempotent and PostgreSQL-first

- Phase 4 / Step 5 completed
  - notification preparation foundation added
  - implemented through `app/services/notification_preparation.py`
  - multilingual notification payload preparation added for:
    - temporary reservation created
    - payment pending
    - payment confirmed
    - reservation expired
  - safe event selection uses existing lifecycle states only
  - language fallback stays explicit and service-layer driven

- Phase 4 / Step 6 completed
  - notification dispatch/envelope foundation added
  - implemented through `app/services/notification_dispatch.py`
  - dispatch preparation now wraps prepared notification payloads into a channel-specific envelope
  - minimal dispatch key generation added for de-duplication-friendly preparation
  - current channel support is limited to `telegram_private`
  - no real sending or scheduler/orchestrator complexity added yet

- Phase 4 / Step 7 completed
  - first payment-pending reminder worker slice added
  - implemented through `app/services/payment_pending_reminder.py`
  - thin worker entry added in `app/workers/payment_pending_reminder.py`
  - due reminder selection now covers active temporary reservations that are approaching expiry
  - current reminder window is the first narrow slice only:
    - payment pending shortly before reservation expiry
  - reminder preparation reuses existing notification dispatch groundwork
  - repeated execution stays safe because this slice does not mutate order/payment state or perform real delivery yet

- Phase 4 / Step 8 completed
  - first real `telegram_private` notification delivery slice added
  - implemented through `app/services/notification_delivery.py`
  - minimal delivery adapter/service boundary added for prepared dispatches
  - payment-pending reminder delivery slice added on top of the existing reminder groundwork
  - delivery result handling stays explicit and testable

- Phase 4 / Step 9 completed
  - notification outbox / persistence groundwork added
  - notification outbox model, repository, and service added
  - deterministic dispatch-key dedupe now persists pending notification entries safely
  - payment-pending reminder outbox slice added for enqueueing due reminder dispatches

- Phase 4 / Step 10 completed
  - notification outbox processing slice added
  - implemented through `app/services/notification_outbox_processing.py`
  - pending outbox entries can be picked up in narrow batches for processing
  - processing reuses the existing delivery service and marks entries delivered or failed explicitly

- Phase 4 / Step 11 completed
  - notification outbox recovery groundwork added
  - implemented through `app/services/notification_outbox_recovery.py`
  - failed and stale-processing outbox entries can be safely recovered to `pending`
  - repeated recovery execution stays explicit and repeat-safe

- Phase 4 / Step 12 completed
  - notification outbox retry execution slice added
  - implemented through `app/services/notification_outbox_retry_execution.py`
  - recovered or targeted pending outbox entries can be reprocessed through the existing processing path
  - retry execution remains narrow and does not add scheduler/orchestrator complexity

- Phase 4 / Step 13 completed
  - predeparture reminder groundwork added
  - implemented through `app/services/predeparture_reminder.py` and `app/services/predeparture_reminder_outbox.py`
  - `predeparture_reminder` event support added to notification preparation
  - eligible confirmed, paid, active orders departing within the reminder window can now be prepared and enqueued for `telegram_private`
  - repeated prepare/enqueue execution stays dedupe-friendly and state-safe

- Phase 4 / Step 14 completed
  - departure-day reminder groundwork added
  - implemented through `app/services/departure_day_reminder.py` and `app/services/departure_day_reminder_outbox.py`
  - `departure_day_reminder` event support added to notification preparation
  - eligible confirmed, paid, active same-day departure orders can now be prepared and enqueued for `telegram_private`
  - repeated prepare/enqueue execution stays dedupe-friendly and state-safe

- Phase 4 / Step 15 completed
  - post-trip reminder groundwork added
  - implemented through `app/services/post_trip_reminder.py` and `app/services/post_trip_reminder_outbox.py`
  - `post_trip_reminder` event support added to notification preparation
  - eligible confirmed, paid, active returned trips within the reminder window can now be prepared and enqueued for `telegram_private`
  - repeated prepare/enqueue execution stays dedupe-friendly and state-safe

### Phase 5
- Phase 5 / Step 1 completed
  - Mini App UX definition added in `docs/MINI_APP_UX.md`
  - screen map, CTA hierarchy, loading/empty/error states, timer states, and postponed behaviors documented
  - Mini App UX aligned with current Phase 2-4 service capabilities and postponed scope

- Phase 5 / Step 2 completed
  - first Mini App implementation slice added for foundation + catalog + filters
  - minimal Mini App catalog endpoint added at `GET /mini-app/catalog`
  - Mini App read-only catalog/filter service added in `app/services/mini_app_catalog.py`
  - Flet Mini App foundation added under `mini_app/`
  - scope kept narrow:
    - no reservation UI
    - no payment UI
    - no waitlist flow
    - no handoff/operator workflow
    - no Mini App auth/init expansion

- Phase 5 / Step 3 completed
  - read-only Mini App tour detail screen added
  - catalog cards now navigate to a dedicated tour detail view
  - minimal read-only tour detail endpoint added at `GET /mini-app/tours/{tour_code}`
  - Mini App read-only detail service added in `app/services/mini_app_tour_detail.py`
  - detail screen reuses existing localization and boarding-point read capabilities
  - scope kept narrow:
    - no reservation UI
    - no payment UI
    - no waitlist flow
    - no handoff/operator workflow
    - no Mini App auth/init expansion

- Phase 5 / Step 4 completed
  - commit: `a9342cc` — `feat: add mini app reservation preparation ui`
  - Mini App reservation **preparation** UI (seat count, boarding point, preparation-only summary)
  - preparation endpoints: `GET /mini-app/tours/{tour_code}/preparation`, `GET /mini-app/tours/{tour_code}/preparation-summary`
  - service: `app/services/mini_app_reservation_preparation.py`
  - scope kept narrow:
    - preparation-only — **no** real reservation/order creation in this step
    - no payment UI
    - no waitlist flow
    - no handoff/operator workflow
    - no Mini App auth/init expansion

- Phase 5 / Step 5 completed
  - commit: `929988f` — `feat: add mini app reservation creation and payment start`
  - real Mini App temporary reservation creation added
  - implemented through thin Mini App glue on top of existing service-layer foundations
  - Mini App now supports:
    - real temporary reservation creation from preparation flow
    - reservation success screen with:
      - reservation reference
      - amount to pay
      - payment status
      - reservation expiry / timer-friendly text
    - payment start / continue-to-payment from Mini App
    - payment screen with:
      - amount due
      - reservation deadline
      - payment session reference
      - provider-neutral `Pay Now` flow
  - added Mini App reservation overview glue for user-facing reservation/payment state display
  - business rules remain owned by existing backend services:
    - `TemporaryReservationService`
    - `PaymentEntryService`
  - payment reconciliation remains unchanged and is still the only source of truth for paid-state transition
  - scope kept narrow:
    - no waitlist workflow
    - no handoff/operator workflow
    - no Mini App auth/init expansion
    - no my bookings screen
    - no provider-specific payment integration
    - no admin/group/content changes

### Phase 5 / Step 5 manual local validation
- local backend startup passed
- `/health` returned 200
- `/healthz` returned 200
- Mini App manual flow passed locally using a temporary local test tour:
  - catalog
  - tour detail
  - reservation preparation
  - preparation summary
  - confirm reservation
  - reservation success state
  - reservation overview
  - payment entry
  - payment screen
- current payment screen remains honest/provider-neutral and does not mark anything as paid before backend reconciliation

- Phase 5 / Step 6 completed
  - commit: `<PUT_COMMIT_HASH_HERE>` — `feat: add mini app bookings and booking status view`
  - Mini App My Bookings screen added
  - Mini App Booking Detail / Status View added
  - thin Mini App facade layer added for user-facing booking/payment state translation
  - added:
    - `GET /mini-app/bookings`
    - `GET /mini-app/orders/{id}/booking-status`
  - Flet Mini App now supports:
    - bookings list
    - booking detail / status view
    - state-based CTA:
      - `Pay now`
      - `Browse tours`
      - `Back to bookings`
  - current facade behavior includes:
    - active temporary hold -> `Pay now`
    - expired hold before worker cleanup -> `Browse tours`
    - released hold after worker cleanup -> human-readable released/expired state + `Browse tours`
    - confirmed/paid booking -> `Back to bookings`
  - payment summary is reused through existing read/summary services
  - payment reconciliation remains unchanged and is still the only source of truth for paid-state transition
  - scope kept narrow:
    - no waitlist workflow
    - no handoff/operator workflow
    - no Mini App auth/init expansion
    - no provider-specific checkout
    - no refund flow
    - no admin/group/content changes

### Phase 5 / Step 6 test checkpoint
- tests run:
  - `python -m unittest tests.unit.test_api_mini_app tests.unit.test_services_mini_app_booking_facade tests.unit.test_services_mini_app_booking -v`
- result:
  - all listed tests passed

- Phase 5 / Step 7 completed
  - commit: `<PUT_COMMIT_HASH_HERE>` — `feat: add mini app help placeholder and language settings`
  - Mini App help placeholder added
  - Mini App language/settings screens added
  - added:
    - `GET /mini-app/help`
    - `GET /mini-app/settings`
    - `POST /mini-app/language-preference`
  - Flet Mini App now supports:
    - `/help`
    - `/settings`
    - help/settings entry points from high-friction screens
    - server-backed language hydration after startup
    - language preference update through the existing user context path
  - current help behavior stays honest:
    - support/help information is available
    - real operator handoff from Mini App is still not implemented
  - language preference is persisted through existing Telegram user context service behavior
  - scope kept narrow:
    - no waitlist workflow
    - no real handoff/operator workflow
    - no Mini App auth/init expansion
    - no provider-specific checkout
    - no refund flow
    - no admin/group/content changes

### Phase 5 / Step 7 test checkpoint
- tests run:
  - `python -m unittest tests.unit.test_api_mini_app -v`
- result:
  - all listed tests passed

### Phase 5 — extended execution (Steps 8–20, historical)

These steps are **closed** for the Phase 5 MVP acceptance narrative; detail lives in `docs/PHASE_5_ACCEPTANCE_SUMMARY.md` and `docs/PHASE_5_STEP_*_NOTES.md`. This subsection records **durable facts** and a **compact map** (not a live “next step” checklist).

**Staging / ops facts (still relevant):**
- Typical hosted layout: **API backend** + **Telegram bot (webhook)** + **Mini App UI** as separate processes/services; **PostgreSQL** is the staging DB; `TEST_BELGRADE_001` is a staging-oriented test tour.
- **Data hygiene:** accumulated staging holds/orders can make a tour look sold out; `reset_test_belgrade_tour_state.py` resets the test tour and related artifacts when needed before smoke tests.
- **Lazy expiry** (Step 9): expiry can run without relying on a dedicated cron for several paths; configurable override **`TEMP_RESERVATION_TTL_MINUTES`** (defaults preserve the 6h/24h rule family documented elsewhere).
- **Mock payment completion** (Step 10): `ENABLE_MOCK_PAYMENT_COMPLETION` + `POST /mini-app/orders/{id}/mock-payment-complete` funnels through the same **`PaymentReconciliationService`** path as webhooks.
- **Expired hold DB shape** (admin/read-model caution): expired unpaid holds may combine **`booking_status=reserved`** with **`payment_status=unpaid`**, **`cancellation_status=cancelled_no_payment`**, **`reservation_expires_at=null`** — see `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` for interpretation risk.

**Compact step map (pointers):**
- **Step 8–8C:** private chat ↔ Mini App staging alignment; scroll/shell i18n iterations; smoke checklist — see early step notes / commit history.
- **Step 9–9A:** lazy expiry + configurable TTL — notes above.
- **Step 10:** mock payment completion — `docs/PHASE_5_STEP_10_NOTES.md`.
- **Step 11:** My bookings sections — `docs/PHASE_5_STEP_11_NOTES.md`.
- **Step 12:** booking detail + payment UX hardening — `docs/PHASE_5_STEP_12_NOTES.md`.
- **Step 12A / 12B:** private chat message cleanup + `/start` `/tours` edit/replace behavior — `docs/PHASE_5_STEP_12A_NOTES.md`, `docs/PHASE_5_STEP_12B_NOTES.md`.
- **Step 13:** support/handoff entry — `docs/PHASE_5_STEP_13_NOTES.md`.
- **Step 14:** waitlist interest entry — `docs/PHASE_5_STEP_14_NOTES.md`.
- **Step 15–17:** internal ops JSON queues + claim/close — `docs/PHASE_5_STEP_15_NOTES.md` … `docs/PHASE_5_STEP_17_NOTES.md`.
- **Step 18:** waitlist status visibility — `docs/PHASE_5_STEP_18_NOTES.md`.
- **Step 19:** My bookings history compaction — `docs/PHASE_5_STEP_19_NOTES.md`.
- **Step 20:** documentation-only acceptance/consolidation — `docs/PHASE_5_ACCEPTANCE_SUMMARY.md`.

**Still not done (product/ops; not Phase 5 MVP acceptance blockers):** real PSP integration, richer mock failure/cancel paths, production Telegram Web App init-data validation for Mini App APIs, full operator inbox/notifications — track via `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`.

### Phase 6
- Phase 6 / Step 1 completed
  - **Config:** `ADMIN_API_TOKEN` in `app/core/config.py`; documented in `.env.example`
  - **Auth dependency:** `app/api/admin_auth.py` — `require_admin_api_token` (Bearer or `X-Admin-Token`; same ergonomics as ops queue)
  - **Routes:** `app/api/routes/admin.py` — `GET /admin/overview`, `GET /admin/tours`, `GET /admin/orders` (lists; wired in `app/api/router.py`)
  - **Read-side:** `app/services/admin_read.py`, `app/services/admin_order_lifecycle.py` — orders expose **`lifecycle_kind`** / **`lifecycle_summary`** instead of relying on raw enums alone for ambiguous expired holds
  - **Repositories:** `TourRepository.list_by_departure_desc`, `OrderRepository.list_recent_for_admin` (read-only lists)
  - **Tests:** `tests/unit/test_api_admin.py`, `tests/unit/test_services_admin_order_lifecycle.py`
  - **Scope respected:** no public Mini App / bot / customer API behavior changes; no booking/payment/waitlist/handoff workflow changes
  - **Historical prompt:** `docs/CURSOR_PROMPT_PHASE_6_STEP_1.md`

- Phase 6 / Step 2 completed
  - **Route:** `GET /admin/orders/{order_id}` — read-only **order detail** (`AdminOrderDetailRead` in `app/schemas/admin.py`)
  - **Includes:** tour + boarding point summaries, capped payment rows, linked handoff summaries, **`persistence_snapshot`** for raw enums while **`lifecycle_*`** stays primary
  - **Repository:** `OrderRepository.get_by_id_for_admin_detail`; payments via `PaymentRepository.list_by_order`
  - **Tests:** extended `tests/unit/test_api_admin.py` (detail, 404, auth, expired-hold projection)
  - **Scope respected:** public flows unchanged; no mutations
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_2.md` (historical); use **Next Safe Step** for new work

- Phase 6 / Step 3 completed
  - **Route:** `GET /admin/tours/{tour_id}` — read-only **tour detail** (`AdminTourDetailRead`, `AdminTranslationSummaryItem` in `app/schemas/admin.py`)
  - **Includes:** core tour fields, translation snippets (language + title), boarding point summaries, **`orders_count`** (row count for visibility only)
  - **Repository:** `TourRepository.get_by_id_for_admin_detail` (eager-load translations + boarding points)
  - **Tests:** extended `tests/unit/test_api_admin.py` (tour detail, 404, auth, translations/boarding/`orders_count`)
  - **Scope respected:** public flows unchanged; no CRUD / mutations
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_3.md` (historical)

- Phase 6 / Step 4 completed
  - **Read-only list filtering:** optional query parameters on **`GET /admin/tours`** and **`GET /admin/orders`** (no mutations)
  - **`GET /admin/tours`:** `status`, `guaranteed_only`
  - **`GET /admin/orders`:** `lifecycle_kind`, `tour_id` — **`lifecycle_kind`** filtering stays **service-driven** and consistent with **`describe_order_admin_lifecycle`** / **`sql_predicate_for_lifecycle_kind`**
  - **Repositories:** `TourRepository.list_by_departure_desc`, `OrderRepository.list_recent_for_admin` (filter args)
  - **Tests:** extended `tests/unit/test_api_admin.py` (filtered lists + auth; unfiltered defaults unchanged)
  - **Scope respected:** public flows unchanged; no CRUD
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_4.md` (historical)

- Phase 6 / Step 5 completed
  - **Route:** **`POST /admin/tours`** — **create-only** core **`Tour`** (`AdminTourCreate` → **`AdminTourDetailRead`** in `app/schemas/admin.py`)
  - **Write service:** `app/services/admin_tour_write.py` — **`AdminTourWriteService.create_tour`**; validation (dates, **`sales_deadline`** vs departure, duplicate **`code`**) in **service layer**; **`seats_available`** = **`seats_total`** on create
  - **Repository:** `TourRepository.create` (base repository) for persistence; route **`db.commit()`** after success
  - **Not in this step:** translations/boarding/media/update/delete/archive
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, duplicate **409**, validation **400**)
  - **Scope respected:** public Mini App / bot / customer flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_5.md` (historical)

- Phase 6 / Step 6 completed
  - **Route:** **`PUT /admin/tours/{tour_id}/cover`** — set/replace **one** **`cover_media_reference`** (`AdminTourCoverSet` → **`AdminTourDetailRead`**)
  - **Persistence:** `tours.cover_media_reference` (nullable string); Alembic revision **`20260405_04`**
  - **Write service:** `AdminTourWriteService.set_tour_cover`; **`TourRepository.set_cover_media_reference`**
  - **Explicitly not in this step:** real **upload** subsystem, **gallery**/media library, **public catalog / Mini App** cover delivery changes, **full** tour update/delete/archive
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success + overwrite, 404, blank payload)
  - **Scope respected:** public booking/payment/waitlist/handoff flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_6.md` (historical)

- Phase 6 / Step 7 completed
  - **Route:** **`PATCH /admin/tours/{tour_id}`** — **`AdminTourCoreUpdate`** (partial core fields only; **`extra='forbid'`** for `code` / `cover_media_reference` / unknown keys)
  - **Write service:** `AdminTourWriteService.update_tour_core`; date/`sales_deadline` validation; **conservative `seats_total`** rule (see **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** **section 18**)
  - **Repository:** `TourRepository.update_core_fields`
  - **Explicitly not in this step:** **`code`** mutation, cover via PATCH, **delete/archive**, translations CRUD, boarding CRUD, public catalog/Mini App changes, full tour-management platform
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, 404, validation, seats rule, forbidden extra fields)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_7.md` (historical)

- Phase 6 / Step 8 completed
  - **Route:** **`POST /admin/tours/{tour_id}/boarding-points`** — **`AdminBoardingPointCreate`** → **`AdminTourDetailRead`**
  - **Write service:** `AdminTourWriteService.add_boarding_point`; **Repository:** `BoardingPointRepository.create_for_tour`
  - **Explicitly not in this step:** boarding **update/delete**, **translations**, **`tour_id` reassignment**, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, tour 404, blank fields)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_8.md` (historical)

- Phase 6 / Step 9 completed
  - **Route:** **`PATCH /admin/boarding-points/{boarding_point_id}`** — **`AdminBoardingPointUpdate`** → **`AdminTourDetailRead`**
  - **Write service:** `AdminTourWriteService.update_boarding_point`; **Repository:** `BoardingPointRepository.update_core_fields`
  - **Explicitly not in this step:** boarding **delete**, **translations**, **`tour_id` reassignment**, full route/itinerary, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, 404, validation, empty body, **`tour_id` in body rejected**)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_9.md` (historical)

- Phase 6 / Step 10 completed
  - **Route:** **`DELETE /admin/boarding-points/{boarding_point_id}`** — **204 No Content** when deleted; **409** if orders reference the point
  - **Write service:** `AdminTourWriteService.delete_boarding_point`; **Repositories:** `OrderRepository.count_by_boarding_point`, base **`delete`** on **`BoardingPoint`**
  - **Explicitly not in this step:** batch delete, boarding **translations**, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, 404, order-reference conflict)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_10.md` (historical)

- Phase 6 / Step 11 completed
  - **Route:** **`PUT /admin/tours/{tour_id}/translations/{language_code}`** — **`AdminTourTranslationUpsert`** → **`AdminTourDetailRead`**
  - **Write service:** `AdminTourWriteService.upsert_tour_translation`; **Repository:** `TourTranslationRepository` create + **`update_fields_for_tour_language`**; language allowlist via **`get_settings().telegram_supported_language_codes`**
  - **Explicitly not in this step:** translation **delete**, **boarding** translations, bulk ops, publication workflow, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, create/update, unsupported language, tour 404, empty body, create without title)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_11.md` (historical)

- Phase 6 / Step 12 completed
  - **Route:** **`DELETE /admin/tours/{tour_id}/translations/{language_code}`** — **204 No Content** when deleted
  - **Write service:** `AdminTourWriteService.delete_tour_translation`; **Repository:** delete by tour + language; language allowlist via **`get_settings().telegram_supported_language_codes`**
  - **Explicitly not in this step:** **boarding** translations, bulk ops, publication workflow, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, tour 404, translation 404, unsupported language, validation)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_12.md` (historical)

- Phase 6 / Step 13 completed
  - **Route:** **`PUT /admin/boarding-points/{boarding_point_id}/translations/{language_code}`** — **`AdminBoardingPointTranslationUpsert`** → **`AdminTourDetailRead`**
  - **Migration:** Alembic **`20260405_05`** — table **`boarding_point_translations`**
  - **Write service:** `AdminTourWriteService.upsert_boarding_point_translation`; **Repository:** boarding point translation create/update; language allowlist via **`get_settings().telegram_supported_language_codes`**
  - **Explicitly not in this step:** boarding translation **delete**, bulk ops, publication workflow, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, create/update, boarding point 404, unsupported language, validation, empty body)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_13.md` (historical)

- Phase 6 / Step 14 completed
  - **Route:** **`DELETE /admin/boarding-points/{boarding_point_id}/translations/{language_code}`** — **204 No Content** when deleted
  - **Write service:** `AdminTourWriteService.delete_boarding_point_translation`; **Repository:** `BoardingPointTranslationRepository.delete_for_boarding_point_language`; language allowlist via **`get_settings().telegram_supported_language_codes`**
  - **Explicitly not in this step:** bulk ops, publication workflow, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success removes one language only, boarding point 404, translation 404, unsupported language)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_14.md` (historical)

- Phase 6 / Step 15 completed
  - **Routes:** **`POST /admin/tours/{tour_id}/archive`**, **`POST /admin/tours/{tour_id}/unarchive`** → **`AdminTourDetailRead`**
  - **Write service:** `AdminTourWriteService.archive_tour`, `unarchive_tour`; **`sales_closed`** reused as archived bucket; unarchive → **`open_for_sale`**; **no** schema migration
  - **Explicitly not in this step:** hard delete, full status editor, order/payment mutations, publication, public catalog logic changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, archive success, archive idempotent, unsafe status, unarchive success, unarchive idempotent, unarchive rejects non-archived, 404)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_15.md` (historical)

- Phase 6 / Step 16 completed
  - **Endpoint:** **`GET /admin/orders/{order_id}`** — extended **`AdminOrderDetailRead`** with **`payment_correction_hint`**, **`needs_manual_review`**, **`payment_records_count`**, **`latest_payment_status`**, **`latest_payment_provider`**, **`latest_payment_created_at`**, **`has_multiple_payment_entries`**, **`has_paid_entry`**, **`has_awaiting_payment_entry`**
  - **Service:** `compute_payment_correction_visibility` in **`app/services/admin_order_payment_visibility.py`**; **`AdminReadService.get_order_detail`** loads all payment rows once for count + capped list
  - **Explicitly not in this step:** order/payment **mutations**, reconciliation **changes**, webhooks, public API changes
  - **Tests:** `tests/unit/test_api_admin.py` (existing detail + multiple payments + mismatch cases)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_16.md` (historical)

- Phase 6 / Step 17 completed
  - **Endpoint:** **`GET /admin/orders/{order_id}`** — extended **`AdminOrderDetailRead`** with **`suggested_admin_action`**, **`allowed_admin_actions`**, **`payment_action_preview`** (advisory only)
  - **Service:** `compute_admin_action_preview` in **`app/services/admin_order_action_preview.py`**; uses **`lifecycle_kind`**, Step 16 **correction** visibility, and **open handoff** count
  - **Explicitly not in this step:** order/payment **mutations**, new mutating routes, webhooks, public API changes
  - **Tests:** `tests/unit/test_api_admin.py` (detail + manual_review / handoff / clean / active-hold cases)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_17.md` (historical)

- Phase 6 / Step 18 completed
  - **Routes:** **`GET /admin/handoffs`**, **`GET /admin/handoffs/{handoff_id}`** → **`AdminHandoffListRead`** / **`AdminHandoffRead`**
  - **Repository:** `HandoffRepository.list_for_admin`, `get_by_id_for_admin_detail`; **service:** `compute_handoff_queue_fields`, **`AdminReadService.list_handoffs`**, **`get_handoff_detail`**
  - **Read fields:** **`is_open`**, **`needs_attention`**, **`age_bucket`**, plus status, reason, priority, user/order/tour linkage, timestamps
  - **Explicitly not in this step:** admin handoff **mutations**, claim/assign/close, notifications, public/catalog changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, list, filter, detail, 404)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_18.md` (historical)

- Phase 6 / Step 19 completed
  - **Route:** **`POST /admin/handoffs/{handoff_id}/mark-in-review`** → **`AdminHandoffRead`**
  - **Semantics:** **`open` → `in_review`**; **`in_review`** idempotent; **`closed`** → **400**; not found → **404**
  - **Service:** **`AdminHandoffWriteService.mark_in_review`** in **`app/services/admin_handoff_write.py`**; **no** claim/assign, **no** notifications
  - **Explicitly not in this step:** **`close`**, claim/assign, order/payment mutations, public flow changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, idempotent, 404, closed → 400)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_19.md` (historical)

- Phase 6 / Step 20 completed
  - **Route:** **`POST /admin/handoffs/{handoff_id}/close`** → **`AdminHandoffRead`**
  - **Semantics:** **`in_review` → `closed`**; **`closed`** idempotent (**200**); **`open`** → **400** (`handoff_close_not_allowed`); not found → **404**
  - **Service:** **`AdminHandoffWriteService.close_handoff`** in **`app/services/admin_handoff_write.py`**; **no** claim/assign, **no** notifications, **no** order/payment mutations
  - **Explicitly not in this step:** reopen, claim/assign, workflow engine, public flow changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, closed idempotent, 404, open → 400)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_20.md` (historical)

- Phase 6 / Step 21 completed
  - **Route:** **`POST /admin/handoffs/{handoff_id}/assign`** + body **`AdminHandoffAssignBody`** → **`AdminHandoffRead`**
  - **Semantics:** **`open` / `in_review`** only; **`closed` → 400**; operator **`users.id`** must exist; first assign or idempotent same id; **reassign to a different operator when already set → 400** (`handoff_reassign_not_allowed`); uses existing **`assigned_operator_id`**
  - **Service:** **`AdminHandoffWriteService.assign_handoff`** in **`app/services/admin_handoff_write.py`**; **no** notifications, **no** order/payment mutations
  - **Explicitly not in this step:** unassign, broad workflow, public flow changes (**reopen** added in Step **22**)
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success open/in_review, 404, closed → 400, idempotent, reassign rejected, bad operator id)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_21.md` (historical)

- Phase 6 / Step 22 completed
  - **Route:** **`POST /admin/handoffs/{handoff_id}/reopen`** → **`AdminHandoffRead`**
  - **Semantics:** **`closed` → `open`**; **`open` → idempotent**; **`in_review` → 400** (`handoff_reopen_not_allowed`); not found → **404**; **`assigned_operator_id` preserved** (only **`status`** updated)
  - **Service:** **`AdminHandoffWriteService.reopen_handoff`** in **`app/services/admin_handoff_write.py`**; **no** notifications, **no** order/payment mutations, **no** unassign
  - **Explicitly not in this step:** unassign, reassignment policy change, public flow changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, closed→open + assignment preserved, idempotent open, 404, in_review → 400)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_22.md` (historical)

- Phase 6 / Step 23 completed
  - **Route:** **`POST /admin/orders/{order_id}/mark-cancelled-by-operator`** → **`AdminOrderDetailRead`**
  - **Semantics:** **active temporary hold** only (`reserved` + `awaiting_payment` + `active` + `reservation_expires_at` **not** `null`); seat restore matches **reservation expiry** math; sets **`payment_status=unpaid`**, **`cancellation_status=cancelled_by_operator`**, **`reservation_expires_at=null`**; **`booking_status` unchanged**; **`cancellation_status=cancelled_by_operator` → idempotent**; **`payment_status=paid` → 400**; any other disallowed combo → **400**; missing order → **404**
  - **Service:** **`AdminOrderWriteService.mark_cancelled_by_operator`** in **`app/services/admin_order_write.py`**; **no** payment-row mutation, **no** refund, **no** reconciliation/webhook change, **no** public/catalog/Mini App change
  - **Explicitly not in this step:** refunds, capture/cancel-payment, broad order editor, move/duplicate-merge, paid-order cancellation
  - **Tests:** `tests/unit/test_api_admin.py` (focused)
  - **Scope respected:** public booking/payment/waitlist/handoff flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_23.md` (historical)

- Phase 6 / Step 24 completed
  - **Route:** **`POST /admin/orders/{order_id}/mark-duplicate`** → **`AdminOrderDetailRead`**
  - **Semantics:** **active temporary hold** (same predicate as Step **23**) **or** **expired unpaid hold** (`reserved` + `unpaid` + `cancelled_no_payment`); **`payment_status=paid` → 400**; **`cancellation_status=duplicate` → idempotent**; active hold: seat restore + `unpaid` / `duplicate` / `reservation_expires_at` cleared; expired hold: **only** `cancellation_status→duplicate`; **no** payment-row mutation, **no** merge
  - **Service:** **`AdminOrderWriteService.mark_duplicate`** in **`app/services/admin_order_write.py`**
  - **Explicitly not in this step:** merge, paid-order duplicate, move, refund, reconciliation change
  - **Tests:** `tests/unit/test_api_admin.py` (focused)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_24.md` (historical)

- Phase 6 / Step 25 completed
  - **Route:** **`POST /admin/orders/{order_id}/mark-no-show`** → **`AdminOrderDetailRead`**
  - **Semantics:** **confirmed** + **paid** + **`cancellation_status=active`**; **`tour.departure_datetime` in the past** (UTC); **`booking_status=no_show` + `cancellation_status=no_show` → idempotent**; else **400**; departure still future → **400** (`reason` **`departure_not_in_past`**); success: **`booking_status`/`cancellation_status` → `no_show`**; **`payment_status` unchanged**; **no** seat restore, **no** payment-row mutation; missing order or tour → **404**
  - **Service:** **`AdminOrderWriteService.mark_no_show`** in **`app/services/admin_order_write.py`**
  - **Explicitly not in this step:** refund, move, merge, broad editor, reconciliation change
  - **Tests:** `tests/unit/test_api_admin.py` (focused)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_25.md` (historical)

- Phase 6 / Step 26 completed
  - **Route:** **`POST /admin/orders/{order_id}/mark-ready-for-departure`** → **`AdminOrderDetailRead`**
  - **Semantics:** **confirmed** + **paid** + **`cancellation_status=active`**; **`tour.departure_datetime` strictly in the future** (UTC); **`booking_status=ready_for_departure` + paid + active → idempotent**; departure not in future → **400** (`reason` **`departure_not_in_future`**); success: **`booking_status` → `ready_for_departure` only**; **`payment_status` / `cancellation_status` unchanged**; **no** seat mutation, **no** payment-row mutation; missing order or tour → **404**
  - **Service:** **`AdminOrderWriteService.mark_ready_for_departure`** in **`app/services/admin_order_write.py`**
  - **Lifecycle labeling** for the resulting steady state was deferred to **Step 27** (read-side only)
  - **Explicitly not in this step:** reconciliation/webhook change, payment-row mutation, public/catalog/Mini App change, move/merge/refund/broad editor
  - **Tests:** `tests/unit/test_api_admin.py` (focused)
  - **Scope respected:** public booking/payment/waitlist/handoff flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_26.md` (historical)

- Phase 6 / Step 27 completed
  - **Read-side only** — **no** new **`/admin/*`** routes, **no** order/payment mutations
  - **`AdminOrderLifecycleKind.READY_FOR_DEPARTURE_PAID`** (`ready_for_departure_paid`): **`describe_order_admin_lifecycle`**, **`sql_predicate_for_lifecycle_kind`** ( **`GET /admin/orders?lifecycle_kind=`** ), **`compute_admin_action_preview`** (aligned with **confirmed paid** / clean preview for this kind)
  - **Narrow predicate:** **`booking_status=ready_for_departure`**, **`payment_status=paid`**, **`cancellation_status=active`**
  - **Explicitly not in this step:** move/merge/refund, payment-row admin ops, reconciliation rewrite, public flow changes
  - **Tests:** `tests/unit/test_services_admin_order_lifecycle.py`, `tests/unit/test_api_admin.py` (focused)
  - **Scope respected:** public booking/payment/waitlist/handoff flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_27.md` (historical)

- Phase 6 / Step 28 completed
  - **Read-side only** — extends **`GET /admin/orders/{order_id}`** (`AdminOrderDetailRead`) with **`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`** — **`compute_move_readiness`** in **`app/services/admin_order_move_readiness.py`**
  - **No** move mutation endpoint; **no** seat/payment writes; conservative blocker codes (see **Current Status**)
  - **Explicitly not in this step:** move **POST**, refund, merge, reconciliation rewrite, public flow changes
  - **Tests:** `tests/unit/test_api_admin.py` (focused)
  - **Scope respected:** public booking/payment/waitlist/handoff flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_28.md` (historical)

- Phase 6 / Step 29 completed
  - **Route:** **`POST /admin/orders/{order_id}/move`** — body **`AdminOrderMoveBody`**: **`target_tour_id`**, **`target_boarding_point_id`** → **`AdminOrderDetailRead`**
  - **Write service:** **`AdminOrderMoveWriteService.move_order`** in **`app/services/admin_order_move_write.py`**; readiness via **`compute_move_readiness`** (reject if not **`can_consider_move`**-equivalent); **`OrderRepository.get_by_id_for_admin_detail_for_update`** for row lock
  - **Semantics:** missing order → **404**; not ready → **400** **`order_move_not_ready`**; target tour missing → **400** **`order_move_target_tour_not_found`**; boarding not on target tour → **400** **`order_move_boarding_not_on_target_tour`**; same tour + same boarding **idempotent**; same tour + different boarding → **`boarding_point_id`** only; cross-tour → restore source **`seats_available`**, deduct target, update **`tour_id`** + **`boarding_point_id`**; **`total_amount`** unchanged; **no** payment-row writes
  - **Explicitly not in this step:** refund/capture, reconciliation rewrite, broad move workflow/history engine, public/catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (`post_admin_order_move` slice)
  - **Scope respected:** public booking/payment/waitlist/handoff flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_29.md` (historical)

- Phase 6 / Step 30 completed
  - **Read-side only** — **no** new routes, **no** mutations — extends **`GET /admin/orders/{order_id}`** (`AdminOrderDetailRead`) with **`move_placement_snapshot`** (`AdminOrderMovePlacementSnapshot`)
  - **Service:** **`compute_move_placement_snapshot`** in **`app/services/admin_order_move_inspection.py`** — **`kind=current_placement_only`**, **`timeline_available=false`**, current tour/boarding identifiers + display fields + **`order_updated_at`** + explanatory **`note`** (no persisted move history rows)
  - **Explicitly not in this step:** audit table, payment mutation, reconciliation/public flow changes
  - **Tests:** `tests/unit/test_api_admin.py` (`move_placement_snapshot` cases)
  - **Scope respected:** public booking/payment/waitlist/handoff flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_30.md` (historical)

### Phase 7
- Phase 7 / Step 1 completed
  - **Documentation-only** — **`docs/GROUP_ASSISTANT_RULES.md`**: allowed group triggers (mentions, approved commands, approved trigger phrases); forbidden group behavior (no private data in group, no long negotiation, no payment-sensitive discussion in group, no reply to every message); CTA strategy (private chat vs Mini App); anti-spam principles; handoff trigger categories (discount, group booking, custom pickup, complaint, unclear payment issue, explicit human request, low-confidence answer); minimal operator continuity (context, language, reason/category)
  - **Aligns with:** **`docs/AI_ASSISTANT_SPEC.md`**, **`docs/AI_DIALOG_FLOWS.md`**, **`docs/TELEGRAM_SETUP.md`**, Phase 7 in **`docs/IMPLEMENTATION_PLAN.md`**
  - **Explicitly not in this step:** Telegram group bot runtime, webhooks, new API routes, public booking/payment/Mini App changes, admin payment mutations, full operator workflow engine
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_1.md` (historical)

- Phase 7 / Step 2 completed
  - **Service-layer only** — **`app/schemas/group_assistant_triggers.py`** (`GroupTriggerReason`, `HandoffCategory`, `GroupTriggerResult`, `HandoffTriggerResult`, `AssistantTriggerSnapshot`); **`app/services/group_trigger_evaluation.py`** (`evaluate_group_trigger` — command before mention, default commands per TELEGRAM_SETUP, default trigger phrases); **`app/services/handoff_trigger_evaluation.py`** (`evaluate_handoff_triggers` — ordered keyword categories, `low_confidence_signal` only when passed in); **`app/services/assistant_trigger_evaluation.py`** (`evaluate_assistant_trigger_snapshot`)
  - **Tests:** `tests/unit/test_group_assistant_triggers.py`
  - **Explicitly not in this step:** Telegram group handler wiring, automatic handoff persistence, new HTTP routes, repository changes, public booking/payment/Mini App behavior changes
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_2.md` (historical)

- Phase 7 / Step 3 completed
  - **Narrow group runtime** — **`app/bot/handlers/group_gating.py`**: **`group`** / **`supergroup`** + **`F.text`** → **`resolve_group_trigger_ack_reply`** (`app/services/group_chat_gating.py`) → silent if no trigger; one short **`GROUP_TRIGGER_ACK_REPLY_TEXT`** if trigger; **`TELEGRAM_BOT_USERNAME`** required for mention-style behavior; **`create_dispatcher`** includes **`group_gating_router`**
  - **Tests:** `tests/unit/test_group_chat_gating.py`
  - **Explicitly not in this step:** handoff DB, booking/payment in group, `evaluate_handoff_triggers` in group path, full CTA/sales flow, public API changes
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_3.md` (historical)

- Phase 7 / Step 4 completed
  - **Narrow category-aware escalation recommendation (reply shaping only, no persistence)** — extends **`resolve_group_trigger_ack_reply`**: after **`evaluate_group_trigger`** succeeds, calls **`evaluate_handoff_triggers`**; if **`handoff_required`** and **`handoff_category`** set → one short category-specific line (`_HANDOFF_CATEGORY_REPLY_TEXT`); else default **`GROUP_TRIGGER_ACK_REPLY_TEXT`**
  - **Service:** **`app/services/group_chat_gating.py`**; handler unchanged aside from doc alignment (**`app/bot/handlers/group_gating.py`**)
  - **Tests:** `tests/unit/test_group_chat_gating.py` (discount, group booking, complaint, explicit human, unclear payment, non-trigger silence, default ack when generic)
  - **Explicitly not in this step:** handoff DB rows from group, operator assignment, workflow engine, booking/payment resolution in group, long replies, public API / Mini App changes
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_4.md` (historical)

- Phase 7 / Step 5 completed
  - **Private CTA / deep-link routing foundation** — **`app/schemas/group_private_cta.py`** (`GroupPrivateEntryMode`, `GroupPrivateCtaTarget`); **`app/services/group_private_cta.py`** (`build_group_private_cta_target`, `entry_mode_from_handoff`); **`group_chat_gating`** appends **`https://t.me/<bot>?start=grp_private`** or **`…grp_followup`** to every group trigger reply; **`docs/TELEGRAM_SETUP.md`** documents payloads
  - **Tests:** `tests/unit/test_group_private_cta.py`, updated `tests/unit/test_group_chat_gating.py`
  - **Explicitly not in this step:** private **`/start`** branching on **`grp_*`**, handoff persistence, booking/payment, Mini App changes, campaign engine
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_5.md` (historical)

- Phase 7 / Step 6 completed
  - **Narrow private `/start` for `grp_private` / `grp_followup`** — **`handle_start`** (**`app/bot/handlers/private_entry.py`**): after language resolved, **`match_group_cta_start_payload`**; **distinct** intros **`start_grp_private_intro`** vs **`start_grp_followup_intro`** (**`app/bot/messages.py`**); then **`_send_catalog_overview`**; **`tour_*`** / legacy **`/start`** unchanged
  - **Service:** **`match_group_cta_start_payload`**, exported **`START_PAYLOAD_GRP_*`** in **`app/services/group_private_cta.py`**
  - **Tests:** `tests/unit/test_group_private_cta.py` (matcher), `tests/unit/test_private_start_grp_messages.py`
  - **Explicitly not in this step:** handoff DB, operator assignment, booking/payment mutations, Mini App changes
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_6.md` (historical)

- Phase 7 / Step 7 completed
  - **Narrow runtime handoff persistence for `grp_followup`** — **`HandoffEntryService.create_for_group_followup_start`** (**`app/services/handoff_entry.py`**); **`HandoffRepository.find_open_by_user_reason`** dedupe for **open** rows; private **`handle_start`** persists **only** when payload is **`grp_followup`** (**reason** **`group_followup_start`**); **`grp_private`** — no handoff write
  - **Tests:** `tests/unit/test_handoff_entry.py` (create, dedupe, reopen after close), `tests/unit/test_group_private_cta.py` (payload gate vs **`grp_private`**)
  - **Explicitly not in this step:** operator assignment, workflow engine, booking/payment side effects, public API changes, Mini App changes
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_7.md` (historical)

- Phase 7 / Step 8 completed
  - **Focused runtime/bot-flow test coverage for the `grp_followup` chain** — **`tests/unit/test_private_entry_grp_followup_chain.py`**: exercises **`handle_start`** with **`grp_followup`** / **`grp_private`** / **`tour_*`**; asserts short intros, **`group_followup_start`** persistence + dedupe, no **`group_followup_start`** row for **`grp_private`**, legacy tour detail path; test **`SessionLocal`** bound to **`FoundationDBTestCase`** session; **`_send_catalog_overview`** mocked — **no** production code or behavior changes
  - **Explicitly not in this step:** operator assignment, workflow engine expansion, public API/Mini App changes, new persistence semantics beyond Step **7**
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_8.md` (historical)

- Phase 7 / Step 9 completed
  - **Narrow admin read-side visibility for `group_followup_start`** — **`compute_group_followup_visibility`** (**`app/services/admin_handoff_queue.py`**); **`AdminHandoffRead`** / **`AdminHandoffSummaryItem`** (**`app/schemas/admin.py`**) add **`is_group_followup`**, **`source_label`**; **`AdminReadService`** (**`app/services/admin_read.py`**) maps list, detail, and order-detail handoff summaries — **read-only**; **no** mutation semantics change
  - **Tests:** **`tests/unit/test_admin_handoff_group_followup_visibility.py`**, **`tests/unit/test_api_admin.py`** (list/detail/order summary + mark-in-review response still exposes flags)
  - **Explicitly not in this step:** new assignment/claim workflow, booking/payment/public/Mini App changes, DB migration
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_9.md` (historical)

- Phase 7 / Step 10 completed
  - **Narrow operator assignment for `group_followup_start` only** — **`POST /admin/handoffs/{handoff_id}/assign-operator`** (**`app/api/routes/admin.py`**); **`AdminHandoffWriteService.assign_group_followup_operator`** (**`app/services/admin_handoff_write.py`**) — **only** when **`reason=group_followup_start`**; shares **`_apply_operator_assignment`** with Step **21** **`assign`** (open/in_review, operator exists, idempotent same id, **no** reassign); general **`POST .../assign`** **unchanged**; **no** notifications, **no** booking/payment/public/Mini App changes
  - **Tests:** **`tests/unit/test_api_admin.py`** (`assign-operator` success, 404, bad operator, wrong reason, idempotent, reassign rejected, 401)
  - **Explicitly not in this step:** broad claim engine, ops JSON takeover, workflow redesign
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_10.md` (historical)

- Phase 7 / Step 11 completed
  - **Read-side operator work-state visibility for assigned `group_followup_start`** — **`compute_group_followup_assignment_visibility`** (**`app/services/admin_handoff_queue.py`**); **`AdminHandoffRead`** / **`AdminHandoffSummaryItem`** add **`is_assigned_group_followup`**, **`group_followup_work_label`**; **`AdminReadService`** (**`app/services/admin_read.py`**) maps handoff **list**, **detail**, order-detail **`handoffs`** — **read-only**; **no** mutation semantics change
  - **Tests:** **`tests/unit/test_admin_handoff_group_followup_visibility.py`**, **`tests/unit/test_api_admin.py`** (focused list/detail/order/assign-operator response cases)
  - **Explicitly not in this step:** acknowledge/take-in-work mutation, claim engine, notifications, booking/payment/public/Mini App, DB migration
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_11.md` (historical)

- Phase 7 / Step 12 completed
  - **Narrow take-in-work for assigned `group_followup_start`** — **`POST /admin/handoffs/{handoff_id}/mark-in-work`** (**`app/api/routes/admin.py`**); **`AdminHandoffWriteService.mark_group_followup_in_work`** (**`app/services/admin_handoff_write.py`**) — **only** when **`reason=group_followup_start`** and **`assigned_operator_id`** set; **`open` → `in_review`**; **`in_review`** idempotent; **`closed`** rejected; **no** DB migration, **no** notifications, **no** booking/payment/public/Mini App changes
  - **Tests:** **`tests/unit/test_api_admin.py`** (`mark_in_work` success, 404, wrong reason, unassigned, idempotent, closed, 401)
  - **Explicitly not in this step:** broad claim engine, close/resolve shortcut for all reasons, notifications
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_12.md` (historical)

- Combined Phase 7 / Steps 13–14 completed
  - **Narrow operator resolve/close for `group_followup_start`** — **`POST /admin/handoffs/{handoff_id}/resolve-group-followup`**; **`AdminHandoffWriteService.resolve_group_followup_handoff`** (**`app/services/admin_handoff_write.py`**) — **only** **`reason=group_followup_start`**; **`in_review` → `closed`**; **`closed`** idempotent; **`open`** rejected; wrong reason / missing handoff → safe errors; **does not** replace Step **20** general **`close`**
  - **Tiny resolved-state read refinement** — **`compute_group_followup_resolution_label`** (**`app/services/admin_handoff_queue.py`**); **`group_followup_resolution_label`** on **`AdminHandoffRead`** / **`AdminHandoffSummaryItem`**; **`AdminReadService`** (**`app/services/admin_read.py`**) — **closed** **`group_followup_start`** only; **no** new read routes
  - **Tests:** **`tests/unit/test_api_admin.py`** (resolve success, 404, wrong reason, open rejected, closed idempotent, list label + non-`group_followup_start` **no** false label); **`tests/unit/test_admin_handoff_group_followup_visibility.py`** (resolution label helper)
  - **Explicitly not in this combined step:** broad workflow engine, notifications, booking/payment/public/Mini App changes, schema migration, **`per_seat` / `full_bus`**
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_13_14_COMBINED.md` (historical)

- Phase 7 / Step 15 completed
  - **Post-resolution operator queue visibility / narrow list filter for `group_followup_start`** — **`compute_group_followup_queue_state`** (**`app/services/admin_handoff_queue.py`**); **`group_followup_queue_state`** on **`AdminHandoffRead`** / **`AdminHandoffSummaryItem`**; **`GET /admin/handoffs?group_followup_queue=`** (**`AdminHandoffGroupFollowupQueueFilter`**, **`HandoffRepository.list_for_admin`**) — **read-side only**; **no** write-path or assignment/resolve semantics change
  - **Tests:** **`tests/unit/test_admin_handoff_group_followup_visibility.py`**, **`tests/unit/test_api_admin.py`** (queue state, filter, resolve regression)
  - **Explicitly not in this step:** notifications, booking/payment/public/Mini App changes, workflow engine, **`per_seat` / `full_bus`**
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_15.md` (historical)

- Phase 7 / Step 16 completed
  - **Narrow private resolved-followup confirmation for `group_followup_start`** — **`HandoffRepository.find_latest_by_user_reason`**; **`HandoffEntryService.should_show_group_followup_resolved_confirmation`**; **`private_entry`** **`handle_start`** chooses **`start_grp_followup_resolved_intro`** vs **`start_grp_followup_intro`** for **`grp_followup`**; **`app/bot/messages.py`** i18n for **`start_grp_followup_resolved_intro`**; **no** operator chat, **no** notification subsystem; Step **7** **`_persist_group_followup_handoff`** unchanged
  - **Tests:** **`tests/unit/test_handoff_entry.py`**, **`tests/unit/test_private_entry_grp_followup_chain.py`**
  - **Explicitly not in this step:** two-way human messaging, booking/payment/public/Mini App changes, **`per_seat` / `full_bus`**
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_16.md` (historical)

- Phase 7 / Step 17 completed
  - **Narrow private followup history/readiness for repeat `grp_followup`** — **`HandoffEntryService.group_followup_private_intro_key`**; **`start_grp_followup_readiness_pending`**, **`start_grp_followup_readiness_assigned`**, **`start_grp_followup_readiness_in_progress`** in **`app/bot/messages.py`**; **`private_entry`** uses single intro-key resolver; **`should_show_group_followup_resolved_confirmation`** retained for tests; **no** write-path change, **no** **`grp_private`** change
  - **Tests:** **`tests/unit/test_handoff_entry.py`**, **`tests/unit/test_private_entry_grp_followup_chain.py`**
  - **Explicitly not in this step:** operator chat, handoff push notifications, booking/payment/public/Mini App changes, **`per_seat` / `full_bus`**
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_STEP_17.md` (historical)

- Phase 7 final followup/operator consolidation block completed
  - **Unified private `grp_followup` copy + admin read-side label alignment** — **`app/bot/messages.py`**; **`app/services/admin_handoff_queue.py`** (**`group_followup_work_label`**, **`group_followup_resolution_label`**); tests **`test_group_followup_phase7_consolidation`**, updated **`test_private_entry_grp_followup_chain`**, **`test_admin_handoff_group_followup_visibility`**, **`test_api_admin`**; **no** new workflow, **no** API shape change, **no** public/Mini App churn
  - **Explicitly not in this block:** operator chat, handoff notifications, **`per_seat` / `full_bus`**, booking/payment mutations
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_FINAL_CONSOLIDATION_BLOCK.md` (historical)

- Phase 7 review / closure completed
  - **Documentation-only acceptance** — **`docs/PHASE_7_REVIEW.md`**: **MVP-sufficient** for the **narrow** group→private→**`group_followup_start`**→admin chain; **explicit** stop for Phase **7** micro-steps; **next** recommended track **tour sales mode** (`per_seat` / `full_bus`) — **separate** design (**do not** mix **ad hoc** into Phase **7** handoff code)
  - **Explicitly not in this step:** **`per_seat` / `full_bus`** implementation, new **Phase 7** features, booking/payment/public flow changes
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_7_REVIEW_CLOSURE.md` (historical)

### Phase 7.1 / Sales Mode / Steps 1–4 completed
Checkpoint for the **Phase 7.1** sub-track through **read-side adaptation** (production **schema drift** after deploy is documented separately under **Production stabilization after Phase 7.1 deploy**).

#### Step 1 — source of truth
- Added **`TourSalesMode`** enum.
- Added **`Tour.sales_mode`** (Postgres + ORM); **existing tours** land safely on **`per_seat`** (migration **`server_default`** + backfill).
- **Admin** read/write surfaces expose **`sales_mode`** (list, detail, create, patch).

#### Step 2 — backend/service policy
- Introduced **centralized backend interpretation** of **`tour.sales_mode`** (**`TourSalesModePolicyService`** / **`TourSalesModePolicyRead`**).
- Policy is **owned by the backend/service layer**, not by UI-only rules.
- **Shared** policy read model/service exists for downstream consumers.

#### Step 3 — Mini App read-side adaptation
- **Mini App** reflects **backend sales-mode policy** on relevant read payloads and CTAs.
- **`per_seat`** tours keep the **normal self-service** path.
- **`full_bus`** tours **do not** present **normal per-seat self-service** where policy forbids it — **read-side / routing** adaptation only, **not** direct whole-bus booking.

#### Step 4 — private bot read-side adaptation
- **Private bot** reflects **centralized sales-mode policy** (tour presentation + CTA routing).
- **`per_seat`** tours keep the **guided self-service reservation** flow.
- **`full_bus`** tours route to the **existing assistance / contact / handoff** path instead of misleading self-service booking; **forged** prepare/reservation entry is **blocked** when policy disallows self-service.
- **Core reservation engine** was **not** rewritten.

#### Explicitly still not in Steps 1–4
- **Direct whole-bus reservation**, **whole-bus self-service payment**, **dedicated operator-assisted full-bus workflow** beyond routing into **existing** assistance/handoff surfaces, **`full_bus_price`**, **`bus_capacity`**, **pricing expansion**, **core reservation engine rewrite**, **old Phase 7** **`grp_followup_*`** chain expansion.

### Phase 7.1 / Sales Mode / Step 5 completed
**Operator-assisted full-bus path** — **narrow** slice: clearer **commercial** assistance **category** and **tour / sales-mode context** on **existing** support/handoff surfaces (**not** a separate operator subsystem; **not** direct whole-bus booking or payment).

- **Structured handoff/support `reason`:** full-bus assistance uses a compact **`full_bus_sales_assistance|…`** encoding in **`handoffs.reason`** (varchar **255**) instead of relying only on generic **`private_chat_contact`** / **`mini_app_support|…`** for those entry points.
- **Private bot:** full-bus **request booking assistance** callback is **tour-scoped**; persisted handoff **`reason`** includes **tour code** and **`sales_mode`** when policy disallows per-seat self-service (forged/invalid callback ids fall back to generic contact **`reason`**).
- **Mini App:** optional **`tour_code`** on **`POST /mini-app/support-request`**; when the tour is **not** per-seat self-service per policy, the same structured **`full_bus_sales_assistance`** **`reason`** is used (**`channel=mini_app`**); assisted tour detail includes a **Request full-bus assistance** control that sends that payload.
- **Admin read models** (handoff **list**, **detail**, order-embedded **`handoffs`**): **`is_full_bus_sales_assistance`**, **`full_bus_sales_assistance_label`**, **`assistance_context_tour_code`** — so operators can distinguish **full-bus commercial assistance** from **generic support** even when **`order_id`** is **null**.
- **Implementation:** reused **`HandoffEntryService`** + **`/admin/handoffs`** reads; helpers centralize **build/parse** of the structured **`reason`**; **no** Alembic migration for this step; **no** **`TemporaryReservationService`** / reservation-engine rewrite.
- **Explicitly not in this step:** **direct whole-bus reservation**, **whole-bus self-service payment**, **`full_bus_price`**, **`bus_capacity`**, **pricing engine expansion**, **reservation engine rewrite**, **broad Phase 7** **`grp_followup_*`** refactor, any **“many seats ⇒ whole bus”** heuristic.

#### Phase 7.1 / Sales Mode / Step 5 — verification notes
- **Focused tests** for full-bus assistance **`reason`**, admin read flags, Mini App support-request branching, and private bot keyboard callback shape — **passed** (local verification at Step **5** closure).
- **No migration** required for Step **5** (context lives in **`handoffs.reason`** only).
- **Private bot** and **Mini App** now preserve **explicit commercial context** for **full-bus assistance**; **admin** views can triage **full-bus assistance** without inferring from **`order_id`**.

#### Phase 7.1 / Sales Mode / Step 5 — architecture notes (narrow MVP)
- **`handoffs.reason`** is the **structured carrier** for this **MVP slice** of full-bus assistance context (**acceptable** for current scope; **not** a general JSON metadata column).
- **Parsing/building** is **centralized** in **`HandoffEntryService`** (and **read-side** labels in **`admin_handoff_queue`** / **`admin_read`**).
- **Still not implemented** after Step **5:** **direct whole-bus reservation**, **whole-bus payment**, **full-bus pricing model**, **capacity model expansion**, **reservation engine rewrite**.

### Phase 7.1 / Sales Mode / Step 1 completed
- **Status:** **finalized / frozen** — treat Step **1** as **done**; extend **`sales_mode`** behavior only via **Step 2+** with explicit scope.
- **Sub-track:** **Phase 7.1 — tour sales mode** (**separate** from closed **Phase 7** **`group_followup_*`** chain; **do not** reopen **Phase 7** for this work).
- **Narrow source-of-truth slice only** — **no** customer-facing booking/payment/Mini App/private bot behavior change.
- **Enum:** **`TourSalesMode`** (`per_seat`, `full_bus`) in **`app/models/enums.py`**.
- **ORM:** **`Tour.sales_mode`** in **`app/models/tour.py`**; **safe default** for existing rows: **`per_seat`** (migration **`server_default`** + ORM default).
- **Admin read surfaces:** **`sales_mode`** on **`GET /admin/tours`** list items and **`GET /admin/tours/{tour_id}`** detail (**`app/services/admin_read.py`**, **`app/schemas/admin.py`**).
- **Admin write surfaces:** **`sales_mode`** on **`POST /admin/tours`** and **`PATCH /admin/tours/{tour_id}`** (**`app/services/admin_tour_write.py`**, **`app/schemas/admin.py`**).
- **Migration:** Alembic **`20260416_06`** — Postgres enum **`tour_sales_mode`** + **`tours.sales_mode`** column (**`alembic/versions/20260416_06_add_tour_sales_mode.py`**).
- **Tests:** focused **`sales_mode`** admin API tests + narrow adjacent admin tour regression subset (**`tests/unit/test_api_admin.py`**).
- **Explicitly not in this step:** booking policy, pricing policy, availability policy, Mini App adaptation, private bot adaptation, operator-assisted full-bus path, direct whole-bus booking, **`full_bus_price`**, **`bus_capacity`**.

### Phase 7.1 / Sales Mode / Step 2 completed
- **Scope (at Step 2 closure):** backend/service-layer interpretation of **`tour.sales_mode`** only — **no** customer-surface changes in that slice.
- **Continuity:** Steps **3–4** later **wired** Mini App and private bot **read-side** to this policy; **`reservation_creation`** remains **unwired** to policy (channel layers gate — see checkpoint **Steps 1–4**).
- **Source of truth:** still **`tours.sales_mode`** (Step **1**); policy **never** infers mode from seat counts.
- **Schema:** **`TourSalesModePolicyRead`** — **`app/schemas/tour_sales_mode_policy.py`** (frozen Pydantic read model: **`effective_sales_mode`**, **`per_seat_self_service_allowed`**, **`direct_customer_booking_blocked_or_deferred`**, **`operator_path_required`**).
- **Service:** **`TourSalesModePolicyService.policy_for_sales_mode`** / **`policy_for_tour`** — **`app/services/tour_sales_mode_policy.py`**.
- **Tests:** **`tests/unit/test_tour_sales_mode_policy.py`** ( **`per_seat` / `full_bus`**, large **`seats_total`** + **`per_seat`**, default **`per_seat`**, **`reservation_creation`** file must **not** import **`tour_sales_mode_policy`**).
- **Explicitly not in this step (historical scope line):** at Step **2** only — catalog/API/bot wiring came in Steps **3–4**; operator-assisted flow, direct whole-bus booking, **`full_bus_price`**, **`bus_capacity`** remain **postponed** (**Next Safe Step**).

---

## Verified

### Environment / Runtime
- `.venv` created and active
- Python 3.13.x is used in project venv
- local PostgreSQL is installed and running
- app starts successfully with `uvicorn`

### Health / Startup
- `/health` returns OK
- `/healthz` returns OK

### Phase 7.1 checkpoint — local verification (Steps 1–4 closure)
- **`python -m compileall`** / **`python -m compileall app tests`** — passed at closure of this checkpoint
- **Full unit suite:** **`python -m pytest tests/unit -q`** — **485 passed**
- **Local startup** — **`uvicorn`**; **`/health`**, **`/healthz`** — OK

### Phase 7.1 / Sales Mode / Step 5 — verification (closure)
- **Focused pytest slice** (handoff entry + admin handoff visibility + admin handoff list full-bus fields + Mini App support-request branching + private tour-detail keyboard callback) — **passed** at Step **5** closure.
- **No DB migration** for Step **5**; **`tours.sales_mode`** migration gate (**`20260416_06`**) remains **unchanged** and **deploy-critical** for environments running Phase **7.1** code.

### Phase 7.1 checkpoint — Railway production (after migration)
- **Migration applied successfully** on **Railway production** Postgres (**`python -m alembic upgrade head`** from **`Tours_BOT`** service shell).
- **Smoke after migration:** **Telegram webhook** requests handled; **`GET /mini-app/settings`** **200**; **`GET /mini-app/catalog`** **200**; **`GET /mini-app/tours/...`** **200**; **`GET /mini-app/bookings`** **200**; **`GET /health`** **200**; **`GET /healthz`** **200**.

### Migrations
- Alembic migrations work
- `alembic current` / `heads` checked
- `alembic downgrade -1` and `upgrade head` passed for both migration slices
- **Phase 7.1 / Sales Mode / Step 1:** `python -m alembic upgrade head` applied **`20260416_06`** (**`tour_sales_mode`** enum + **`tours.sales_mode`**) successfully (local verification)

### Code Sanity
- `python -m compileall app alembic` passed repeatedly after major steps
- `python -m compileall app tests` passed at latest checkpoints
- no major startup/import/mapping crashes at latest checkpoint

### Tests
- **Phase 7.1 / Sales Mode / Step 2 (policy):** `python -m pytest tests/unit/test_tour_sales_mode_policy.py -v` — **7 passed** (local verification after Step **2** closure)
- **Phase 7.1 / Sales Mode / Step 1 (freeze verification):** `python -m pytest tests/unit/test_api_admin.py -v` — **195 passed** (includes calendar-drift fix: **`test_post_admin_order_move_rejects_target_not_open_for_sale`** tour departures moved to **Aug 2026** so source tour is still **in the future** vs wall-clock)
- **Phase 7.1 / Sales Mode / Step 1:** `python -m pytest tests/unit/test_api_admin.py -k sales_mode` — **passed** (focused **`sales_mode`** admin API tests)
- **Phase 7.1 / Sales Mode / Step 1 (narrow regression):** `python -m pytest tests/unit/test_api_admin.py -k "post_admin_tour_success_and_seats_available or patch_admin_tour_core_success or put_admin_tour_cover_success_and_get_detail"` — **passed**
- **Phase 7.1 / Sales Mode / Step 5 (full-bus assistance):** focused pytest on **`test_handoff_entry`**, **`test_admin_handoff_group_followup_visibility`**, **`test_api_admin`** (full-bus handoff list), **`test_api_mini_app`** (support-request branching), **`test_bot_private_foundation`** (assistance callback) — **passed** (local verification at Step **5** closure)
- focused Phase 2 unit slice passes
- bot foundation tests pass
- reservation service tests pass
- reservation expiry tests pass
- payment entry tests pass
- payment reconciliation tests pass
- API payment tests pass
- notification preparation tests pass
- notification dispatch tests pass
- notification delivery tests pass
- payment-pending reminder worker tests pass
- payment-pending reminder delivery tests pass
- notification outbox tests pass
- payment-pending reminder outbox tests pass
- notification outbox processing tests pass
- notification outbox recovery tests pass
- notification outbox retry execution tests pass
- predeparture reminder tests pass
- predeparture reminder outbox tests pass
- departure-day reminder tests pass
- departure-day reminder outbox tests pass
- post-trip reminder tests pass
- post-trip reminder outbox tests pass
- `python -m unittest discover -s tests/unit -v` currently passes
- re-run and refresh this line after major phases; last intentional full-unit note was kept current through Phase 5 MVP acceptance work
- previous `psycopg ResourceWarning` no longer appears in full suite output

### Latest Payment/Webhook Checkpoint
- payment webhook/API delivery slice passes tests
- route layer remains thin
- reconciliation logic remains isolated in service layer
- app startup after webhook slice passed
- `/health` and `/healthz` both returned 200 after latest changes

### Latest Expiry/Notification Checkpoint
- reservation expiry slice passes tests
- notification preparation slice passes tests
- notification dispatch slice passes tests
- `telegram_private` notification delivery slice passes tests
- payment-pending reminder selection, delivery, and outbox slices pass tests
- notification outbox persistence, processing, recovery, and retry execution slices pass tests
- predeparture reminder groundwork and outbox slices pass tests
- departure-day reminder groundwork and outbox slices pass tests
- post-trip reminder groundwork and outbox slices pass tests
- notification preparation, dispatch, delivery, outbox, and reminder logic remain service-layer driven
- current real notification delivery remains limited to `telegram_private`

---

## Current Architecture State

### Ready
- **Phase 7 / Step 1 (documentation)** — **`docs/GROUP_ASSISTANT_RULES.md`**: operational rules for group triggers, CTAs, anti-spam, handoff categories, operator continuity
- **Phase 7 / Step 2 (helpers)** — **`app/schemas/group_assistant_triggers.py`**, **`app/services/group_trigger_evaluation.py`**, **`handoff_trigger_evaluation.py`**, **`assistant_trigger_evaluation.py`**; **tests** `tests/unit/test_group_assistant_triggers.py`
- **Phase 7 / Step 3 (narrow group runtime)** — **`app/bot/handlers/group_gating.py`** (group/supergroup **text**); **`app/services/group_chat_gating.py`** (`resolve_group_trigger_ack_reply`); **tests** `tests/unit/test_group_chat_gating.py`; **not** full assistant / **not** group-side handoff DB writes (private **`grp_followup`** persistence is Step **7**)
- **Phase 7 / Step 4 (category-aware escalation recommendation in replies)** — same files; **`evaluate_handoff_triggers`** used **only** for **narrow category-aware** short reply text after the group trigger fired (**escalation recommendation**, not persistence); **tests** `tests/unit/test_group_chat_gating.py`
- **Phase 7 / Step 5 (private CTA deep links)** — **`app/services/group_private_cta.py`**, **`app/schemas/group_private_cta.py`**; replies include **`t.me`** deep link; **tests** `tests/unit/test_group_private_cta.py` + gating tests
- **Phase 7 / Step 6 (private `/start` for `grp_*`)** — **`app/bot/handlers/private_entry.py`** + **`match_group_cta_start_payload`**; distinct intros **`start_grp_private_intro`** vs **`start_grp_followup_intro`** (+ Phase **7** / Steps **16–17** follow-up keys via **`group_followup_private_intro_key`**); **tests** `test_group_private_cta`, `test_private_start_grp_messages`
- **Phase 7 / Step 7 (narrow `grp_followup` handoff persistence)** — **`HandoffEntryService`**, **`HandoffRepository.find_open_by_user_reason`**; **`private_entry`** **`/start grp_followup`** → **`group_followup_start`** row (dedupe **open**); **tests:** `test_handoff_entry`, `test_group_private_cta`
- **Phase 7 / Step 8 (focused `grp_followup` chain tests)** — **`tests/unit/test_private_entry_grp_followup_chain.py`** validates runtime boundary for **`grp_followup`** / **`grp_private`** / legacy **`tour_*`**; **no** production behavior change
- **Phase 7 / Step 9 (admin `group_followup_start` visibility)** — **`is_group_followup`**, **`source_label`** on **`GET /admin/handoffs`**, **`GET /admin/handoffs/{id}`**, order-detail **`handoffs`**; derived from **`reason`**; **read-only**
- **Phase 7 / Step 10 (narrow `assign-operator` for `group_followup_start`)** — **`POST /admin/handoffs/{id}/assign-operator`**; **`reason=group_followup_start`** only; Step **21**-style rules; general **`POST .../assign`** unchanged
- **Phase 7 / Step 11 (assigned `group_followup_start` work-state read labels)** — **`is_assigned_group_followup`**, **`group_followup_work_label`** on **`GET /admin/handoffs`**, **`GET /admin/handoffs/{id}`**, order-detail **`handoffs`**; derived from **`reason`** + **`assigned_operator_id`** + **`status`**; **read-only**
- **Phase 7 / Step 12 (narrow `mark-in-work` for assigned `group_followup_start`)** — **`POST /admin/handoffs/{id}/mark-in-work`**; **`open` → `in_review`**; gated reason + assignment; **no** new columns
- **Combined Phase 7 / Steps 13–14 (narrow `resolve-group-followup` + resolved read label)** — **`POST /admin/handoffs/{id}/resolve-group-followup`** (**`group_followup_start`** only; **`in_review` → `closed`**, **`closed`** idempotent); **`group_followup_resolution_label`** on handoff reads when that reason is **`closed`**
- **Phase 7 / Step 15 (queue-state read + narrow handoff list filter)** — **`group_followup_queue_state`** on handoff **list** / **detail** / order-detail **`handoffs`**; **`GET /admin/handoffs?group_followup_queue=`** (**`awaiting_assignment`**, **`assigned_open`**, **`in_work`**, **`resolved`**) — **read-side only**
- **Phase 7 / Step 16 (private resolved-followup confirmation)** — **`/start grp_followup`** may show **`start_grp_followup_resolved_intro`** when latest **`group_followup_start`** is **`closed`** and **no** **open** row; **`HandoffEntryService`** + **`HandoffRepository`** read helpers for the predicate (**Step 17** centralizes intro key selection)
- **Phase 7 / Step 17 (private followup history/readiness signal)** — **`HandoffEntryService.group_followup_private_intro_key`**; messages **`start_grp_followup_readiness_pending`**, **`start_grp_followup_readiness_assigned`**, **`start_grp_followup_readiness_in_progress`**; repeat **`grp_followup`** distinguishes **open** / **assigned** / **`in_review`** / **resolved** / **none** — **read-only**
- **Phase 7 final followup/operator consolidation (polish)** — **`app/bot/messages.py`** unified **`grp_followup`** copy; **`app/services/admin_handoff_queue.py`** **`group_followup_work_label`** / **`group_followup_resolution_label`** aligned to **`group_followup_queue_state`** terminology; **`tests/unit/test_group_followup_phase7_consolidation.py`**; **no** new workflow or persistence
- **Phase 7 review / closure (documentation)** — **`docs/PHASE_7_REVIEW.md`** — **accepted** stop point for the **narrow** group→private→**`group_followup_start`**→admin chain; **default** forward work is **not** more **Phase 7** micro-slices
- **Phase 7.1 / Sales Mode / Steps 1–4 (checkpoint)** — **`tour.sales_mode`** tour-level **commercial source of truth**; **backend policy** centralized in **`TourSalesModePolicyService`**; **Mini App** and **private bot** **read-side** surfaces reflect that policy (**no** direct whole-bus booking, **no** whole-bus payment, **no** dedicated full-bus operator workflow beyond **existing** assistance/handoff routing); **core reservation engine** unchanged by this checkpoint
- **Phase 7.1 / Sales Mode / Step 5 (operator-assisted full-bus path)** — structured **`full_bus_sales_assistance`** payload in **`handoffs.reason`**; **private bot** + **Mini App** assistance entry points carry **tour** + **`sales_mode`** context when policy requires operator path; **admin** handoff reads expose **`is_full_bus_sales_assistance`**, **`full_bus_sales_assistance_label`**, **`assistance_context_tour_code`**; **no** new operator subsystem; **no** direct whole-bus reservation/payment; **no** reservation engine rewrite (**see Completed Steps**)
- **Phase 7.1 / Sales Mode / Step 1 (admin source-of-truth)** — **`TourSalesMode`** + **`Tour.sales_mode`**; admin **list/detail/create/patch** expose **`sales_mode`**; Alembic **`20260416_06`**; **initial values** **`per_seat`**, **`full_bus`**
- **Phase 7.1 / Sales Mode / Step 2 (backend policy)** — **`TourSalesModePolicyRead`** + **`TourSalesModePolicyService`**; enum-only interpretation; tests **`test_tour_sales_mode_policy`** (shared **`reservation_creation`** remains free of policy import; channel layers gate where needed)
- **bot layer** — Telegram private chat + **minimal** group gating router; thin handlers; service-driven
- **api layer** — FastAPI; public routes + Mini App routes + payments webhooks + **internal ops** JSON endpoints + **admin API** (`/admin/*`, `ADMIN_API_TOKEN`: overview, tours/orders **lists** with **optional read-only filters** incl. **`lifecycle_kind=ready_for_departure_paid`** (Step **27**), **`GET /admin/handoffs`** (optional **`status`**, Phase **7** / Step **15** **`group_followup_queue`**) and **`GET /admin/handoffs/{handoff_id}`** handoff queue visibility (incl. Phase **7.1** / Step **5** **`is_full_bus_sales_assistance`**, **`full_bus_sales_assistance_label`**, **`assistance_context_tour_code`**), **`POST /admin/handoffs/{handoff_id}/mark-in-review`** (Step **19**), **`POST /admin/handoffs/{handoff_id}/close`** (Step **20**), **`POST /admin/handoffs/{handoff_id}/assign`** (Step **21**), **`POST /admin/handoffs/{handoff_id}/assign-operator`** (Phase **7** / Step **10**, **`group_followup_start`** only), **`POST /admin/handoffs/{handoff_id}/mark-in-work`** (Phase **7** / Step **12**, **assigned** **`group_followup_start`** only), **`POST /admin/handoffs/{handoff_id}/resolve-group-followup`** (Phase **7** / Steps **13–14**, **`group_followup_start`** only), **`POST /admin/handoffs/{handoff_id}/reopen`** (Step **22**), **`GET /admin/orders/{order_id}`** order detail with **Step 16** correction + **Step 17** action-preview + **Step 27** lifecycle mapping + **Step 28** move-readiness (**`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`**) + **Step 30** **`move_placement_snapshot`** (current placement only), **`POST /admin/orders/{order_id}/mark-cancelled-by-operator`** (Step **23**), **`POST /admin/orders/{order_id}/mark-duplicate`** (Step **24**), **`POST /admin/orders/{order_id}/mark-no-show`** (Step **25**), **`POST /admin/orders/{order_id}/mark-ready-for-departure`** (Step **26**), **`POST /admin/orders/{order_id}/move`** (Step **29**), **tour + order detail** incl. **`cover_media_reference`**, **`POST /admin/tours`** create **core** tours, **`POST /admin/tours/{tour_id}/archive`** and **`POST /admin/tours/{tour_id}/unarchive`**, **`PUT /admin/tours/{tour_id}/cover`** for **one** media reference string, **`PATCH /admin/tours/{tour_id}`** for **core** field updates only, **`POST` / `PATCH` / `DELETE`** boarding points, **`PUT` / `DELETE`** **`/admin/tours/{tour_id}/translations/{language_code}`** for **tour** translations, **`PUT` / `DELETE`** **`/admin/boarding-points/{boarding_point_id}/translations/{language_code}`** for **boarding** translations)
- **services layer** — business rules and orchestration
- **repositories layer** — persistence-oriented data access
- **mini_app** — Flet Mini App UI (separate deploy surface in staging); **MVP accepted** for agreed scope (`docs/PHASE_5_ACCEPTANCE_SUMMARY.md`); **no business logic in the frontend** — UI calls APIs only
- **booking/payment core** — temporary reservations, payment entry, idempotent reconciliation, lazy expiry, staging mock payment completion path when enabled
- **waitlist / handoff (MVP)** — customer interest/support entry; **internal ops** JSON retains separate tooling; **`/admin/*`** has queue **read** (Step **18**) + Phase **7** / Step **15** **`group_followup_queue_state`** / **`group_followup_queue`** filter for **`group_followup_start`** triage + narrow **`mark-in-review` / `close` / `assign` / `assign-operator`** (Phase **7** / Step **10**, **`group_followup_start`** only) / **`mark-in-work`** (Phase **7** / Step **12**, **assigned** **`group_followup_start`** only) / **`resolve-group-followup`** (Phase **7** / Steps **13–14**, **`group_followup_start`** only) / **`reopen`** (Steps **19–22**) — assignment **narrow** (no reassign-to-other-operator once set; **no unassign**); **reopen** restores **`open`** from **`closed`** and **preserves `assigned_operator_id`**; **private** **`/start grp_followup`** (Phase **7** / Steps **16–17** + **consolidation**) — coherent **readiness** / **resolved** / **generic** copy + aligned admin **read-side** labels — **not** operator chat, **not** handoff push notifications; **not** a full operator inbox or customer notification suite

### Architecture boundaries (non-negotiable)
- **PostgreSQL-first** for MVP-critical behavior; do not treat SQLite as source of truth for booking/payment paths
- **Service layer** owns business logic; **repositories** stay persistence-oriented; **route layer** stays thin (verify/parse/delegate)
- **Payment reconciliation** remains the single place for confirmed paid-state transitions on orders
- **Mini App / any web UI**: presentation only — no duplicated booking/payment rules in the client
- **`tour.sales_mode` (Phase 7.1):** tour-level **commercial source of truth**; **`TourSalesModePolicyService`** is the **single service-layer interpretation** — **Mini App** and **private bot** (Steps **3–4**) **consume** that policy on read-side/CTA paths; **do not** duplicate commercial rules in UI-only layers

### Not Implemented Yet
- **Next (forward, active sub-track):** **Phase 7.1 / Sales Mode / Step 6** — **product/design review**: is **direct whole-bus self-service** needed for MVP/staging, or is the **operator-assisted** path (**Step 5**) sufficient? **Design explicitly** before any implementation — **Next Safe Step**; **separate** from Phase **7** handoff/operator chain expansion. Optional **later** slices: i18n polish, group **rate limits** — product-scoped.
- **Phase 7.1 — explicitly postponed:** **`full_bus_price`**; **`bus_capacity`**; **direct whole-bus reservation flow**; **whole-bus payment flow**; **pricing expansion**; **`TemporaryReservationService` / reservation engine refactor**; **broad operator workflow rewrite**; any **“many seats ⇒ whole bus”** heuristic; **old Phase 7** **`grp_followup_*`** chain expansion; broader **payment** / **availability** / **seat-semantics** changes driven by **`sales_mode`** without an explicit slice — **unless** product approves a scoped Step **6+** implementation.
- **Group / handoff (Phase 7 — closed):** Steps **1–17** + **final consolidation** + **`docs/PHASE_7_REVIEW.md`** = **rules + helpers + group gating + escalation wording + deep links + private `/start`** + **narrow** **`handoffs`** write on **`/start grp_followup`** (**Step 7**) + **focused tests** (**Step 8**) + **admin read visibility** (**Step 9**) + **narrow `assign-operator`** (**Step 10**) + **read-side work-state labels** (**Step 11**) + **narrow `mark-in-work`** (**Step 12**) + **narrow `resolve-group-followup`** + **`group_followup_resolution_label`** (**Steps 13–14**) + **`group_followup_queue_state`** + **`group_followup_queue`** list filter (**Step 15**) + **private resolved confirmation** on **`grp_followup`** (**Step 16**) + **private readiness/history** (**Step 17**) + **aligned private/admin wording** (**consolidation**); **group** chat path (Steps **3–4**) still **no** DB handoff rows — **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §**19**.
- **Still valid:** staging smoke on **`/admin/*`** through Phase 6 Step 30 when convenient; **`docs/PHASE_6_REVIEW.md`** remains the Phase 6 closure reference; **`docs/PHASE_7_REVIEW.md`** is the Phase **7** closure reference.
- **Optional later (product-prioritized only):** narrow **persisted move placement audit** on successful **`POST /move`**, **or** another **low-risk** admin read refinement — **never** default to **admin payment** mutation; requires **explicit** design checkpoint (**`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** **§1f**).
- **Still postponed:** admin **refund / capture / cancel-payment**, **broad** order status editor, **merge** tooling, **payment reconciliation** rewrite, **persisted** move timeline without an explicit slice, handoff **unassign**, broader **reassignment** policy, full **operator queue/workflow engine**, **notifications** from admin actions, **full** admin SPA, **publication**, **bulk** ops — per plan / product.
- **Longer-term:** optional group assistant at scale, content assistant, handoff notifications, analytics — **explicit** product scope per `docs/IMPLEMENTATION_PLAN.md`.

## Next Safe Step

### Next safe step
**Phase 7.1 / Sales Mode / Step 6** — **review whether direct whole-bus self-service is needed at all**, and **if so**, **design it explicitly** before implementation.

**Goal:**
- **Avoid premature** direct-booking implementation for **`full_bus`** tours.
- Decide whether the **operator-assisted** path (**Phase 7.1 / Step 5**) is **already sufficient** for **MVP/staging**.
- **Only proceed** to **direct whole-bus** customer flow if there is a **clear business requirement** and an **approved** design checkpoint.

**Must not expand into (unless explicitly approved):**
- **Direct whole-bus reservation** implementation
- **Whole-bus payment** implementation
- **Pricing engine expansion** (**`full_bus_price`**, **`bus_capacity`**, and similar)

**Baseline (shipped):** **Phase 7.1 / Steps 1–5** — **`tour.sales_mode`**, **`TourSalesModePolicyService`**, Mini App + private bot **read-side** policy reflection, **structured full-bus assistance** handoff **`reason`** + **admin** triage fields (**Step 5**); **`COMMIT_PUSH_DEPLOY.md`** migration gate for **`20260416_06`**.

**Out of scope unless explicitly re-scoped:** new **Phase 7** **`grp_followup`** workflow features, **admin payment** mutations.

**Not the default:** **admin payment** mutations, **Phase 6 / Step 31**, **payment reconciliation** semantics change.

**`payment reconciliation`** remains the **single** place for **confirmed paid-state** transitions on orders until **§1f** in **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** is satisfied.

**Staging (recommended):** routine smoke (**`/health`**, **`grp_followup`**, admin handoffs, Mini App catalog) when deploy changes; **never** deploy Phase **7.1** code without matching **`tours.sales_mode`** DDL on the target DB.

### Safe scope boundaries
- **Preserve** booking/payment behavior unless a future step explicitly scopes enforcement.
- **V2 expansion:** preserve **Layer A** per **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`**; supplier marketplace tracks must not break frozen core without explicit compatibility plan.
- **Phase 6 review** (`docs/PHASE_6_REVIEW.md`) remains the admin-track closure record.
- **Phase 7 review** (`docs/PHASE_7_REVIEW.md`) remains the group/handoff narrow-chain closure record.
- **Phase 7.1:** keep commercial interpretation in **`TourSalesModePolicyService`**; **do not** invent **full_bus** rules in UI-only layers.

**Completed step references:** `docs/CURSOR_PROMPT_PHASE_6_STEP_1.md` … `docs/CURSOR_PROMPT_PHASE_6_STEP_30.md` (historical); **`docs/CURSOR_PROMPT_PHASE_7_STEP_1.md`** … **`docs/CURSOR_PROMPT_PHASE_7_REVIEW_CLOSURE.md`** (historical). **Closure:** **`docs/PHASE_7_REVIEW.md`**. **Phase 7.1:** **Completed Steps** → **Phase 7.1 / Sales Mode / Steps 1–4 completed**, **Phase 7.1 / Sales Mode / Step 5 completed** (+ granular Step **1** / Step **2** entries).  
**Plan:** `docs/IMPLEMENTATION_PLAN.md` — Phase 7 **closed**; **active sub-track:** **Phase 7.1 — tour sales mode** (**Steps 1–5** done; **Step 6** next). **V2 supplier marketplace:** `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` — **Track 0** through **Track 5e** complete for scoped slices (request marketplace + RFQ bridge execution + supersede/cancel lifecycle); **next V2 marketplace slices** (product-prioritized): customer **multi-quote** UX, notifications, bot deep links — see that plan’s status table.

## Recommended Next Prompt
Continue **Phase 7.1 / Sales Mode / Step 6** (see **Next Safe Step**): **review / design gate** for **direct whole-bus self-service** — confirm **business need**, compare to **operator-assisted** (**Step 5**) sufficiency, **no** reservation/payment/pricing implementation until **explicitly approved**. **Phase 7** remains **closed** — **`docs/PHASE_7_REVIEW.md`**; **do not** reopen **Phase 7** **`grp_followup_*`** by default. Sources: **`docs/TOUR_SALES_MODE_DESIGN.md`**, **`docs/CHAT_HANDOFF.md`**, **`docs/TECH_SPEC_TOURS_BOT.md`**, **`docs/IMPLEMENTATION_PLAN.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`**, **`docs/TESTING_STRATEGY.md`**, **`docs/PHASE_6_REVIEW.md`**, **`docs/PHASE_7_REVIEW.md`**.

---

## Important Technical Notes

- PostgreSQL is the primary target database
- do not treat SQLite as source of truth for booking/payment-critical behavior
- repository layer must stay persistence-oriented only
- service layer must stay separate from repositories
- handlers must stay thin and service-driven
- enum persistence was already fixed and must not be broken again
- current bot foundation uses `MemoryStorage()` as an early-stage temporary choice
- bot process and backend process should remain separable
- temporary reservation creation already reduces `seats_available`, so later payment and expiry logic must respect this existing write behavior
- payment reconciliation is already idempotent and must remain the single place for confirmed payment state transitions
- webhook/API route layer must remain thin and must not duplicate reconciliation logic
- DB-backed test harness now disposes the engine pool centrally after class teardown
- see `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` for accepted temporary decisions, open architectural questions, and future review triggers

---

## Current Bot Layer Notes

### Existing bot capabilities
- private `/start`
- explicit language selection
- language resolution/persistence for Telegram users
- `/tours`
- safe list of open tours
- safe tour detail browsing
- `/start tour_<CODE>` style deep-link handling
- `/start grp_private` / `/start grp_followup` (Phase 7 / Step 6) — **distinct** short intros (`start_grp_private_intro` vs `start_grp_followup_intro`) then catalog; **`/start grp_followup`** also persists **narrow** handoff (**Phase 7 / Step 7**, reason **`group_followup_start`**, dedupe **open**); **Phase 7 / Step 8** adds **focused tests** for that private chain (**no** behavior change); **Phase 7 / Step 9** adds **admin** **`is_group_followup`** / **`source_label`** on handoff reads (**no** write change); **Phase 7 / Step 10** adds **`POST /admin/handoffs/{id}/assign-operator`** for that reason **only** (general **`assign`** unchanged); **Phase 7 / Step 11** adds **`is_assigned_group_followup`** / **`group_followup_work_label`** on those same admin reads (**no** write change); **Phase 7 / Step 12** adds **`POST /admin/handoffs/{id}/mark-in-work`** (**assigned** **`group_followup_start`** only); **Combined Phase 7 / Steps 13–14** add **`POST /admin/handoffs/{id}/resolve-group-followup`** and **`group_followup_resolution_label`** on admin reads when that reason is **`closed`**; **Phase 7 / Step 15** adds **`group_followup_queue_state`** + **`group_followup_queue`** on **`GET /admin/handoffs`** (**admin-only**); **Phase 7 / Step 16** adds **`start_grp_followup_resolved_intro`** when latest **`group_followup_start`** is **`closed`** and **no** **open** row; **Phase 7 / Step 17** adds **`group_followup_private_intro_key`** + **`start_grp_followup_readiness_*`**; **final consolidation** — aligned private + admin **read-side** wording (**private** path only for copy)
- guided browsing by:
  - date presets
  - destination keyword
  - budget range when safe
- reservation-preparation preview flow
- temporary reservation creation confirmation
- continue-to-payment entry for temporary reservations

### Bot constraints
- **waitlist:** interest entry exists for sold-out open tours (MVP); no group-chat waitlist UX
- **handoff:** support/contact entry exists; full operator inbox and customer notifications are **not** implemented
- **group chat:** Phase **7 / Steps 3–6** — **trigger gating** + **category-aware** wording + **`t.me`** CTA (`group_gating`); Phase **7 / Step 6** — matching **`grp_*`** private `/start` intros; Phase **7 / Step 7** — **`/start grp_followup`** private handoff row (**not** group-side persistence); Phase **7 / Step 8** — **tests** validate the **`grp_followup`** private chain; Phase **7 / Step 9** — **admin** read labels for **`group_followup_start`**; Phase **7 / Step 10** — **admin** **`assign-operator`** for that reason **only**; Phase **7 / Step 11** — **admin** read **work-state** labels for **assigned** **`group_followup_start`**; Phase **7 / Step 12** — **admin** **`mark-in-work`** for **assigned** **`group_followup_start`**; **Combined Phase 7 / Steps 13–14** — **admin** **`resolve-group-followup`** + **`group_followup_resolution_label`**; Phase **7 / Step 15** — **admin-only** **`group_followup_queue_state`** + list **`group_followup_queue`** filter; Phase **7 / Step 16** — **private** **`start_grp_followup_resolved_intro`** when prior follow-up **resolved**; Phase **7 / Step 17** — **private** **readiness** copy; **final consolidation** — aligned **private + admin** wording — **not** operator chat (see **`docs/GROUP_ASSISTANT_RULES.md`**)

### Mini App (Phase 5 MVP — accepted)
- End-to-end staging-realistic flow: catalog → detail → preparation → **temporary reservation** → **payment entry** → optional **mock completion** → **My bookings** (with documented limits); see `docs/PHASE_5_ACCEPTANCE_SUMMARY.md`
- Production **Telegram Web App init-data** validation for API identity remains a **follow-up**, not a blocker for this handoff narrative

---

## Reservation Expiration Assumption Currently Implemented

- departure in 1–3 days: 6 hours
- departure in 4+ days: 24 hours
- always capped by `sales_deadline` if earlier

This logic already exists in the temporary reservation creation slice and must be preserved unless deliberately revised.

---

## Payment Logic Status Currently Implemented

### Already implemented
- payment entry
- minimal payment session creation/reuse
- idempotent payment reconciliation
- paid result can confirm the order
- later non-paid result cannot regress a paid order
- webhook/API delivery slice with isolated signature verification and payload parsing
- provider-agnostic reconciliation entry via `POST /payments/webhooks/{provider}`

### Not yet implemented
- refund workflow
- advanced provider SDK integration
- admin-facing payment operations beyond current core flow

---

## Notification Logic Status Currently Implemented

### Already implemented
- multilingual notification preparation for:
  - temporary reservation created
  - payment pending
  - payment confirmed
  - reservation expired
- multilingual notification preparation for:
  - predeparture reminder
  - departure-day reminder
  - post-trip reminder
- notification event/type definitions
- channel-specific dispatch envelope preparation for `telegram_private`
- real `telegram_private` notification delivery
- deterministic dispatch key generation for prepared dispatches

### Not yet implemented
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications

---

## New Chat Startup Prompt

Start this task as a continuation of the current project state, but in a fresh chat.

Use the following as source of truth for continuity:
- project rules
- current codebase
- docs/TECH_SPEC_TOURS_BOT.md
- docs/IMPLEMENTATION_PLAN.md
- docs/PHASE_6_REVIEW.md (Phase 6 closure / MVP-sufficient assessment)
- docs/PHASE_7_REVIEW.md (Phase 7 closure — group→private→handoff→operator narrow chain)
- docs/TOUR_SALES_MODE_DESIGN.md (Phase 7.1 — tour sales mode design / rollout order)
- docs/GROUP_ASSISTANT_RULES.md (Phase 7 Step 1 — group + handoff operational rules)
- docs/CHAT_HANDOFF.md (latest approved checkpoint and **Next Safe Step**)
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/TESTING_STRATEGY.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/TELEGRAM_SETUP.md

Continuity rules:
- preserve the existing architecture and phase sequence
- do not repeat already completed work
- do not reintroduce previously postponed logic
- **Approved checkpoint:** **Phase 7 closed** — **`docs/PHASE_7_REVIEW.md`** (**review / closure accepted**); **implementation** through Steps **1–17** + **final consolidation** (private **`grp_followup`** + admin **`group_followup_*`** read labels; **no** operator chat, **no** handoff push notifications in this track); **`grp_private`** unchanged; **`tour_*`** / legacy **`/start`** unchanged; **no** automatic assignment from **Telegram `grp_*`** entry; **`TELEGRAM_BOT_USERNAME`** required for full group gating. **Active sub-track:** **Phase 7.1 — tour sales mode** — **Steps 1–5 completed** (admin **`tour.sales_mode`**, **`TourSalesModePolicyService`**, Mini App + private bot read-side, **Step 5** structured **full-bus assistance** handoffs — **not** direct whole-bus booking); **Railway production** stabilized after **`tours.sales_mode`** migration; **Forward:** **Step 6** (review/design for **direct whole-bus self-service** — **Next Safe Step**) — **separate** from **Phase 7** **`grp_followup_*`** expansion. **Deploy-critical:** **`tours.sales_mode`** DDL (**`20260416_06`**) must be applied on target DB before Phase **7.1** app deploy — **`COMMIT_PUSH_DEPLOY.md`**. Phase 6 closure: **`docs/PHASE_6_REVIEW.md`**. **Not** old **Phase 5 / Step 4–5** checkpoints; **not** admin payment mutation or **Phase 6 / Step 31** unless scoped.

**Primary continuity document:** `docs/CHAT_HANDOFF.md` (**Current Status** + **Next Safe Step**); Phase 7 closure: **`docs/PHASE_7_REVIEW.md`**; Phase 7 rules: **`docs/GROUP_ASSISTANT_RULES.md`**; Phase 6 closure: **`docs/PHASE_6_REVIEW.md`**; Phase 7.1 design: **`docs/TOUR_SALES_MODE_DESIGN.md`**.

Default forward path is **Phase 7.1 — tour sales mode** — **Step 6** (direct whole-bus self-service **review/design**; **no** implementation until approved) — do not use legacy Phase 5 “next step” prompts; **do not** assume further Phase **7** **`grp_followup`** implementation without **explicit** product rescoping.

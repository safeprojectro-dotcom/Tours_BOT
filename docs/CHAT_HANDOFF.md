# Chat Handoff

## Project
Tours_BOT

**Continuity anchor (read this first):** The **live** approved checkpoint is **Phase 7 / Step 4 completed** — **narrow group runtime** (**`app/bot/handlers/group_gating.py`**, **`app/services/group_chat_gating.py`**): **group/supergroup text only**; **non-trigger** → **no reply**; **mention / approved command / approved trigger phrase** → **one** short safe reply — **trigger gating** + **short safe acknowledgment** + **narrow category-aware escalation recommendation** when **`evaluate_handoff_triggers`** matches (**discount**, **group booking**, **custom pickup**, **complaint**, **unclear payment**, **explicit human**, **low confidence**); **no** handoff DB rows, **no** operator assignment, **no** sensitive booking/payment handling in group; **`TELEGRAM_BOT_USERNAME`** unset → **silent** in groups. **Next:** **Phase 7 / Step 5** — **private CTA / deep-link routing foundation for group replies** — see **Next Safe Step**. **Phase 6** / **`docs/PHASE_6_REVIEW.md`** — historical admin closure. **Not** **Phase 6 / Step 31**, **not** **admin payment** mutation. **Phase 5** — do **not** resume old **Step 4–5** narratives. Use **`Next Safe Step`** + **Current Status**.

## Current Status
The **latest approved checkpoint** is **Phase 7 / Step 4 completed** (**documentation + code checkpoint aligned**). **Agreed group runtime semantics:** scope is **group / supergroup text** only; **trigger gating** (`evaluate_group_trigger`); if **no** trigger → **no** bot reply; if trigger → **one** short safe acknowledgment; **narrow category-aware escalation recommendation** — when **`evaluate_handoff_triggers`** returns **`handoff_required`** with a **`handoff_category`**, use the matching short line in **`app/services/group_chat_gating.py`** (covers e.g. **discount**, **group booking**, **complaint**, **unclear payment issue**, **explicit human request**; plus **custom pickup** / **low confidence** per helper); **no** prices, **no** invented facts, **no** promise that a human was already assigned; otherwise **`GROUP_TRIGGER_ACK_REPLY_TEXT`**; **`TELEGRAM_BOT_USERNAME`** not configured → bot **stays silent** in groups (mention path inactive). **Step 1** rules: **`docs/GROUP_ASSISTANT_RULES.md`**. **`create_dispatcher`** includes **`group_gating`** router. **Public** booking / payment / waitlist / Mini App **flows and APIs did not change**.

**Still not implemented (explicit):** **real** handoff **persistence** from group runtime; **operator workflow engine**; **full** group assistant behavior; **booking/payment resolution** or other sensitive handling **in group**; **long-form** group replies; **public** booking/payment/waitlist/Mini App **behavior changes**. **Step 4** intentionally does **not** create handoff rows or assign operators.

**Baseline still true from Phase 6 closure:** **read-only** **`move_placement_snapshot`** on **`GET /admin/orders/{order_id}`** (**Phase 6 / Step 30**); **narrow** **`POST /admin/orders/{order_id}/move`** (**Step 29**); admin handoff/order surfaces unchanged in meaning — see **Completed Steps** / Phase 6.

**Phase 6 / Step 29** (still in baseline): **narrow** **`POST /admin/orders/{order_id}/move`** (**`app/services/admin_order_move_write.py`**); guarded by Step **28** readiness; **no** payment-row writes, **no** reconciliation/webhook changes.

**Admin order read** on **`GET /admin/orders/{order_id}`**: **Step 16** correction visibility, **Step 17** action preview, **Step 27** lifecycle mapping (incl. **`ready_for_departure_paid`**), **Step 28** move-readiness (**`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`**), **Step 30** **`move_placement_snapshot`** (current placement inspection only). Read-only hints do **not** authorize a move; **POST /move** enforces readiness in the service layer.

Order **write** surface: **`app/services/admin_order_write.py`** — **`POST /admin/orders/{order_id}/mark-cancelled-by-operator`** (Step **23**), **`mark-duplicate`** (Step **24**), **`mark-no-show`** (Step **25**), **`mark-ready-for-departure`** (Step **26**); **`app/services/admin_order_move_write.py`** — **`POST /admin/orders/{order_id}/move`** (Step **29**); handoff writes Steps **19–22** (**`app/services/admin_handoff_write.py`**).

**Agreed narrow semantics (combined):**
- **`mark-in-review`:** **`open` → `in_review`**; **`in_review` → idempotent success** (no extra write); **`closed` → 400**; missing handoff → **404**.
- **`close`:** **`in_review` → `closed`**; **`closed` → idempotent success**; **`open` → 400** (`handoff_close_not_allowed`); **any other unexpected status → same client error shape** (narrow safe rejection); missing handoff → **404**. Admin **`close`** is intentionally **not** a shortcut from **`open`** — operators are expected to use **`mark-in-review`** first.
- **`assign`** (Step **21**): body **`{ "assigned_operator_id": <users.id> }`**. Only **`open`** or **`in_review`**; **`closed` → 400** (`handoff_assign_not_allowed`). Operator user must exist (**`handoff_assign_operator_not_found`**). **First** set of **`assigned_operator_id`** from **`null`**, or **idempotent** repeat with the **same** id — **reassigning to a different operator when one is already set** → **400** (`handoff_reassign_not_allowed`) — **no unassign** in this slice (still).
- **`reopen`** (Step **22**): **`closed` → `open`**; **`open` → idempotent success**; **`in_review` → 400** (`handoff_reopen_not_allowed`); missing handoff → **404**. Only **`status`** is updated; **`assigned_operator_id` is preserved** (not cleared) on reopen.
- **`mark-cancelled-by-operator`** (Step **23**): **active temporary hold** only (`booking_status=reserved`, `payment_status=awaiting_payment`, `cancellation_status=active`, `reservation_expires_at` **not** `null`); **`payment_status=paid` → 400**; already **`cancellation_status=cancelled_by_operator` → idempotent**; any other disallowed combination → **400**; missing order → **404**; on success: seat restore (same narrow rule as **reservation expiry**), `payment_status→unpaid`, `cancellation_status→cancelled_by_operator`, `reservation_expires_at→null`, **`booking_status` unchanged**; **no** payment-row mutation, **no** refund/reconciliation/webhook change. **Order read** (**Steps 16–17**) still exposes lifecycle, correction visibility, and action preview (unchanged).
- **`mark-duplicate`** (Step **24**): **active temporary hold** (same predicate as Step **23**) **or** **expired unpaid hold** (`reserved` + `unpaid` + `cancelled_no_payment`); **`payment_status=paid` → 400**; already **`cancellation_status=duplicate` → idempotent**; active hold: seat restore + `unpaid` / `duplicate` / `reservation_expires_at→null`; expired hold: **only** `cancellation_status→duplicate` (no duplicate seat restore); **no** payment-row mutation, **no** merge flow. **Order read** fields unchanged in meaning.
- **`mark-no-show`** (Step **25**): **confirmed** + **paid** + **`cancellation_status=active`** only; **`tour.departure_datetime` must be in the past** (UTC); already **`booking_status=no_show`** and **`cancellation_status=no_show` → idempotent**; wrong statuses → **400**; valid statuses but **departure not in past** → **400** (`reason` **`departure_not_in_past`**); on success: **`booking_status`/`cancellation_status` → `no_show`**; **`payment_status` unchanged**; **no** seat restoration, **no** payment-row mutation; missing order or missing tour → **404**.
- **`mark-ready-for-departure`** (Step **26**): **confirmed** + **paid** + **`cancellation_status=active`** only; **`tour.departure_datetime` must be strictly in the future** (UTC); already **`booking_status=ready_for_departure`** + paid + active → **idempotent**; departure not in future → **400** (`reason` **`departure_not_in_future`**); on success: **`booking_status` → `ready_for_departure` only**; **`payment_status` / `cancellation_status` unchanged**; **no** seat mutation, **no** payment-row mutation; missing order or tour → **404**. **Step 27** adds read-side **`ready_for_departure_paid`** lifecycle labeling for that steady state (see below).
- **Lifecycle read (Step 27):** **`ready_for_departure_paid`** applies only to **`ready_for_departure` + paid + active**; list filter **`lifecycle_kind=ready_for_departure_paid`** matches **`describe_order_admin_lifecycle`**; action preview treats this like **confirmed paid** (clean / no spurious **`manual_review`** from lifecycle alone). **Not** a mutation; **no** repository writes.
- **Move readiness (Step 28):** **`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`** on **`GET /admin/orders/{order_id}`** only; grounded in persisted order/tour + lifecycle + correction + open handoffs; blocker codes include **`payment_correction_manual_review`**, **`open_handoff_open`**, **`order_not_paid`**, **`cancellation_not_active`**, **`lifecycle_not_move_candidate`**, **`tour_departure_not_in_future`**. **Read-only** — hints **do not** perform a move by themselves.
- **Move mutation (Step 29):** **`POST /admin/orders/{order_id}/move`** — rejects with **`order_move_not_ready`** when Step **28**-style readiness would block; validates target tour + boarding on target tour; same-tour same-boarding **idempotent**; same-tour different-boarding updates **`boarding_point_id`** only; cross-tour restores source seats and deducts target (**no** oversell); **`total_amount`** and **payment rows** unchanged by policy.
- **Move placement inspection (Step 30):** **`move_placement_snapshot`** on order detail — **current** FK placement + timestamps **only**; **`timeline_available`** stays **false** until a future persisted-audit slice.

**Step 18** read API: **`GET /admin/handoffs`**, **`GET /admin/handoffs/{handoff_id}`** (**`is_open`**, **`needs_attention`**, **`age_bucket`**, **`assigned_operator_id`**). **Still not implemented:** **unassign**, broader **reassignment** policy redesign, full **operator workflow engine**, **notifications** from admin handoff actions, **public** customer handoff flow changes, **refund / capture / cancel-payment** admin actions, **broad** order workflow editor, **merge** tooling, **persisted** move timeline / audit history, **full** admin SPA.

**Phase 6 / Steps 1–30** (completed): **`ADMIN_API_TOKEN`**; tours, boarding, translations, archive/unarchive; orders **16–17** (read + preview) + **Steps 27–28** (lifecycle **`ready_for_departure_paid`** + move-readiness) + **Step 30** (**`move_placement_snapshot`**) + **Step 29** (narrow **move** **POST**) + **Steps 23–26** (cancel + duplicate + no-show + ready-for-departure); handoff **queue read** + **four** narrow mutations (**status progression + assign + reopen**). **Public** booking/payment/waitlist/customer handoff flows were **not** retargeted by these admin slices — they remain as in Phase 5 acceptance.

**Historical (closed for MVP narrative):** **Phase 5 (Mini App MVP) accepted** for staging; details in `docs/PHASE_5_ACCEPTANCE_SUMMARY.md` — **not** the forward checkpoint.

**Next work:** **Phase 7 / Step 5** — **private CTA / deep-link routing foundation for group replies** (see **Next Safe Step**): clearer path from short group replies toward **private chat** and documented **`/start`** / deep-link patterns — **foundation only**, **not** a full in-group sales flow. **Admin payment mutations** are **not** the default.

### Operational note (production — Step 6 schema recovery)
After Step 6 backend shipped to Railway **before** production Postgres had applied Alembic revision **`20260405_04`**, the missing column **`tours.cover_media_reference`** caused **`ProgrammingError` / `UndefinedColumn`** and **500**s on routes that load tours (e.g. **`/mini-app/catalog`**, **`/mini-app/bookings`**). Root cause was **schema mismatch**, not Mini App UI logic. **Recovery completed:** migrations applied against the Railway DB (using the **public** Postgres URL and a local driver URL such as **`postgresql+psycopg://...`** where internal hostnames are not resolvable), backend **redeployed**, **`/health`**, catalog, and bookings smoke-checked. **Going forward:** any schema-changing step must include **migration apply → redeploy → smoke** for affected endpoints. Details: **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` section 17**.

## Current Phase

**Current phase (forward work):** **Phase 7 — Group Assistant And Operator Handoff**. **Phase 7 / Steps 1–4** **completed**. **Next:** **Phase 7 / Step 5** (see **Next Safe Step**). Phase 6 narrow admin API track **closed** through **Step 30** — see **`docs/PHASE_6_REVIEW.md`**.

**Latest approved checkpoint:** **Phase 7 / Step 4** — **group/supergroup** text → **`group_gating`** handler → **`resolve_group_trigger_ack_reply`** (**trigger gating** + **short safe ack** + **narrow category-aware escalation recommendation** via **`evaluate_handoff_triggers`** when applicable); **no** handoff DB writes from this path, **no** booking/payment handling in group; **public** flows **unchanged**. **Step 1** docs: **`docs/GROUP_ASSISTANT_RULES.md`**. **Prior code baseline** unchanged: **Phase 6 / Step 30** **`move_placement_snapshot`**, **Step 29** move **POST**, admin handoffs/orders as implemented. **Admin payment mutations** remain **intentionally postponed** (see **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** **§1f**). **Still not:** **full** group assistant, **real** handoff **persistence** from group, **operator workflow engine**, **booking/payment resolution in group**, **handoff** rows **created from group runtime** (when not scoped), **persisted** move audit/timeline rows, **unassign**, broader **reassignment** redesign, **notifications** from admin handoff actions, **refund / capture / cancel-payment**, **public** customer/Mini App flow redesign. Internal **ops** JSON stays **separate** from **`/admin/*`**.

**Earlier checkpoints:** Phase 7 / Step 4 (handoff-aware short replies in narrow group path); Phase 7 / Step 3 (narrow group runtime gating + default ack); Phase 7 / Step 2 (trigger helper services + unit tests); Phase 7 / Step 1 ( **`docs/GROUP_ASSISTANT_RULES.md`** — rules only); Phase 6 / Steps 1–7 (foundation through core tour patch); Phase 6 / Steps 8–10 (boarding create / patch / delete); Phase 6 / Steps 11–12 (tour translation upsert/delete); Phase 6 / Steps 13–14 (boarding point translation upsert/delete); Phase 6 / Step 15 (tour archive/unarchive); Phase 6 / Step 16 (order detail payment correction visibility); Phase 6 / Step 17 (order detail action preview); Phase 6 / Step 18 (admin handoff queue read API); Phase 6 / Step 19 (admin handoff mark-in-review); Phase 6 / Step 20 (admin handoff close-only); Phase 6 / Step 21 (admin handoff assign); Phase 6 / Step 22 (admin handoff reopen); Phase 6 / Step 23 (admin mark-cancelled-by-operator); Phase 6 / Step 24 (admin mark-duplicate); Phase 6 / Step 25 (admin mark-no-show); Phase 6 / Step 26 (admin mark-ready-for-departure); Phase 6 / Step 27 (admin lifecycle **`ready_for_departure_paid`** read refinement); Phase 6 / Step 28 (admin order move-readiness read-only fields); Phase 6 / Step 29 (admin order narrow **move** mutation); Phase 6 / Step 30 (admin **`move_placement_snapshot`** read-only); Phase 5 accepted + Phase 5 Step 20 docs (`docs/PHASE_5_ACCEPTANCE_SUMMARY.md`).

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

### Migrations
- Alembic migrations work
- `alembic current` / `heads` checked
- `alembic downgrade -1` and `upgrade head` passed for both migration slices

### Code Sanity
- `python -m compileall app alembic` passed repeatedly after major steps
- `python -m compileall app tests` passed at latest checkpoints
- no major startup/import/mapping crashes at latest checkpoint

### Tests
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
- **Phase 7 / Step 3 (narrow group runtime)** — **`app/bot/handlers/group_gating.py`** (group/supergroup **text**); **`app/services/group_chat_gating.py`** (`resolve_group_trigger_ack_reply`); **tests** `tests/unit/test_group_chat_gating.py`; **not** full assistant / **not** handoff persistence
- **Phase 7 / Step 4 (category-aware escalation recommendation in replies)** — same files; **`evaluate_handoff_triggers`** used **only** for **narrow category-aware** short reply text after the group trigger fired (**escalation recommendation**, not persistence); **tests** `tests/unit/test_group_chat_gating.py`
- **bot layer** — Telegram private chat + **minimal** group gating router; thin handlers; service-driven
- **api layer** — FastAPI; public routes + Mini App routes + payments webhooks + **internal ops** JSON endpoints + **admin API** (`/admin/*`, `ADMIN_API_TOKEN`: overview, tours/orders **lists** with **optional read-only filters** incl. **`lifecycle_kind=ready_for_departure_paid`** (Step **27**), **`GET /admin/handoffs`** and **`GET /admin/handoffs/{handoff_id}`** handoff queue visibility, **`POST /admin/handoffs/{handoff_id}/mark-in-review`** (Step **19**), **`POST /admin/handoffs/{handoff_id}/close`** (Step **20**), **`POST /admin/handoffs/{handoff_id}/assign`** (Step **21**), **`POST /admin/handoffs/{handoff_id}/reopen`** (Step **22**), **`GET /admin/orders/{order_id}`** order detail with **Step 16** correction + **Step 17** action-preview + **Step 27** lifecycle mapping + **Step 28** move-readiness (**`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`**) + **Step 30** **`move_placement_snapshot`** (current placement only), **`POST /admin/orders/{order_id}/mark-cancelled-by-operator`** (Step **23**), **`POST /admin/orders/{order_id}/mark-duplicate`** (Step **24**), **`POST /admin/orders/{order_id}/mark-no-show`** (Step **25**), **`POST /admin/orders/{order_id}/mark-ready-for-departure`** (Step **26**), **`POST /admin/orders/{order_id}/move`** (Step **29**), **tour + order detail** incl. **`cover_media_reference`**, **`POST /admin/tours`** create **core** tours, **`POST /admin/tours/{tour_id}/archive`** and **`POST /admin/tours/{tour_id}/unarchive`**, **`PUT /admin/tours/{tour_id}/cover`** for **one** media reference string, **`PATCH /admin/tours/{tour_id}`** for **core** field updates only, **`POST` / `PATCH` / `DELETE`** boarding points, **`PUT` / `DELETE`** **`/admin/tours/{tour_id}/translations/{language_code}`** for **tour** translations, **`PUT` / `DELETE`** **`/admin/boarding-points/{boarding_point_id}/translations/{language_code}`** for **boarding** translations)
- **services layer** — business rules and orchestration
- **repositories layer** — persistence-oriented data access
- **mini_app** — Flet Mini App UI (separate deploy surface in staging); **MVP accepted** for agreed scope (`docs/PHASE_5_ACCEPTANCE_SUMMARY.md`); **no business logic in the frontend** — UI calls APIs only
- **booking/payment core** — temporary reservations, payment entry, idempotent reconciliation, lazy expiry, staging mock payment completion path when enabled
- **waitlist / handoff (MVP)** — customer interest/support entry; **internal ops** JSON retains separate tooling; **`/admin/*`** has queue **read** (Step **18**) + narrow **`mark-in-review` / `close` / `assign` / `reopen`** (Steps **19–22**) — assignment **narrow** (no reassign-to-other-operator once set; **no unassign**); **reopen** restores **`open`** from **`closed`** and **preserves `assigned_operator_id`**; **not** a full operator inbox or customer notification suite

### Architecture boundaries (non-negotiable)
- **PostgreSQL-first** for MVP-critical behavior; do not treat SQLite as source of truth for booking/payment paths
- **Service layer** owns business logic; **repositories** stay persistence-oriented; **route layer** stays thin (verify/parse/delegate)
- **Payment reconciliation** remains the single place for confirmed paid-state transitions on orders
- **Mini App / any web UI**: presentation only — no duplicated booking/payment rules in the client

### Not Implemented Yet
- **Next (Phase 7):** **Phase 7 / Step 5** — **private CTA / deep-link routing foundation for group replies** (documented, testable wiring toward **private chat** + **`/start`** / deep-link alignment — **not** full group sales) — see **Next Safe Step**.
- **Group / handoff:** Steps **3–4** = **trigger gating + short safe ack + narrow category-aware escalation recommendation** (Step **4**: **`evaluate_handoff_triggers`** for reply text only); **real handoff persistence** from group / **operator** engine / **full** assistant — **future** — **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §**19**.
- **Still valid:** staging smoke on **`/admin/*`** through Phase 6 Step 30 when convenient; **`docs/PHASE_6_REVIEW.md`** remains the Phase 6 closure reference.
- **Optional later (product-prioritized only):** narrow **persisted move placement audit** on successful **`POST /move`**, **or** another **low-risk** admin read refinement — **never** default to **admin payment** mutation; requires **explicit** design checkpoint (**`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** **§1f**).
- **Still postponed:** admin **refund / capture / cancel-payment**, **broad** order status editor, **merge** tooling, **payment reconciliation** rewrite, **persisted** move timeline without an explicit slice, handoff **unassign**, broader **reassignment** policy, full **operator queue/workflow engine**, **notifications** from admin actions, **full** admin SPA, **publication**, **bulk** ops — per plan / product.
- **Phase 7–9 (beyond Step 5):** optional group assistant at scale, content assistant, analytics — per `docs/IMPLEMENTATION_PLAN.md`

## Next Safe Step

**Primary (single outcome):** **Phase 7 / Step 5** — **private CTA / deep-link routing foundation for group replies**.

- **Why this step:** Step **2** added evaluation helpers; Step **3** added **minimal** group **gating** + one short ack; Step **4** added **narrow category-aware** reply text via **`evaluate_handoff_triggers`**. The **next smallest safe increment** is a **clearer, documented foundation** for how group replies point users to **private chat** and to **`/start`** / **deep-link** patterns aligned with **`docs/TELEGRAM_SETUP.md`** and **`docs/GROUP_ASSISTANT_RULES.md`** — **without** building a full in-group assistant or resolving bookings/payments in group.
- **In scope (typical):** centralized **CTA / link text or URL building** (service/helper layer where appropriate), **narrow** handler or reply assembly hooks, **focused tests**; keep replies **short** and **safe**.
- **Out of scope for Step 5 unless explicitly rescoped:** **handoff row creation** from group, **operator assignment**, **full** operator workflow, **i18n** / **rate limits** as standalone goals (may follow later), **public** API or Mini App contract changes, **booking/payment** mutations.
- **Baseline (Steps 3–4):** **`app/bot/handlers/group_gating.py`**, **`app/services/group_chat_gating.py`**.
- **Not the default:** **admin payment** mutations, **Phase 6 / Step 31**, **payment reconciliation** semantics change.
- **`payment reconciliation`** remains the **single** place for **confirmed paid-state** transitions on orders until **§1f** in **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** is satisfied.

**Staging (recommended):** after Step **5** implementation, smoke in a test **group**: replies still **one** short message; **private** / deep-link path behaves as documented (**no** sensitive data in group).

### Goal (Step 5)
Make **private routing** from **group** **explicit and consistent** at the **foundation** layer — so later steps (persistence, richer assistant) can build on it **without** redesigning the whole Telegram surface.

### Safe scope boundaries
- **Preserve** public customer flows and existing APIs; **no** booking/payment/Mini App logic changes unless a future step scopes them.
- **Phase 6 review** (`docs/PHASE_6_REVIEW.md`) remains the admin-track closure record.

**Completed step references:** `docs/CURSOR_PROMPT_PHASE_6_STEP_1.md` … `docs/CURSOR_PROMPT_PHASE_6_STEP_30.md` (historical); **`docs/CURSOR_PROMPT_PHASE_7_STEP_1.md`** … **`docs/CURSOR_PROMPT_PHASE_7_STEP_4.md`** (historical).  
**Plan:** `docs/IMPLEMENTATION_PLAN.md` — Phase 7.

## Recommended Next Prompt
Implement **Phase 7 / Step 5** — **private CTA / deep-link routing foundation for group replies** (see **Next Safe Step**): **foundation** for consistent **private chat** + **`/start`** / deep-link alignment from the narrow group path; **no** handoff persistence, **no** full group assistant, **no** public booking/payment/Mini App behavior changes unless explicitly scoped. Sources: **`docs/CHAT_HANDOFF.md`**, **`docs/GROUP_ASSISTANT_RULES.md`**, **`docs/TELEGRAM_SETUP.md`**, `docs/IMPLEMENTATION_PLAN.md`, `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`.

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
- **group chat:** Phase **7 / Steps 3–4** — **trigger gating + one short reply** (`group_gating` handler); Step **4** adds **handoff-category-aware** wording when **`evaluate_handoff_triggers`** matches — **not** full group assistant, **not** handoff rows from this path (see **`docs/GROUP_ASSISTANT_RULES.md`**)

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
- docs/GROUP_ASSISTANT_RULES.md (Phase 7 Step 1 — group + handoff operational rules; required for Phase 7 work)
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
- **Approved checkpoint:** **Phase 7 / Step 4** complete — **trigger gating** + **short safe acknowledgment** + **narrow category-aware escalation recommendation** via **`evaluate_handoff_triggers`** (non-trigger **silent**; **no** handoff DB, **no** operator assignment, **no** booking/payment resolution in group; **`TELEGRAM_BOT_USERNAME`** required for full gating). **Forward:** **Phase 7 / Step 5** — **private CTA / deep-link routing foundation for group replies** (see **Next Safe Step**). Phase 6 closure: **`docs/PHASE_6_REVIEW.md`**. **Not** old **Phase 5 / Step 4–5** checkpoints; **not** admin payment mutation or **Phase 6 / Step 31** unless scoped.

**Primary continuity document:** `docs/CHAT_HANDOFF.md` (**Current Status** + **Next Safe Step**); Phase 7 rules: **`docs/GROUP_ASSISTANT_RULES.md`**; Phase 6 closure: **`docs/PHASE_6_REVIEW.md`**.

Default forward path is **Phase 7 / Step 5** — **private CTA / deep-link routing foundation** — do not use legacy Phase 5 “next step” prompts for new implementation slices.

# B14A — Channel CTA, publish / execution-link sequencing, reservation preparation (read-only diagnostic)

**Project:** Tours_BOT. **Type:** documentation-only inspection (no code, tests, migrations, or production I/O).

**Trigger:** B13G full conversion smoke — **Supplier Offer #12**, **Tour #6**, **`tour_code`** **`B10-SO12-04fb1f`**, **execution link #5** **`active`**, showcase audit **attempt id 2** **`persisted`** (**`showcase_message_id` 25**). Mini App: supplier landing and tour detail look healthy; **`GET /mini-app/tours/{tour_code}/preparation`** returns **404** with detail **`tour is not available for reservation preparation`**.

---

## 1. Context and recorded facts (smoke)

| Area | Recorded value |
|------|----------------|
| Offer | **12** — *Excursie Timisoara Oradea*, **`published`** |
| Tour | **6**, **`B10-SO12-04fb1f`**, **`open_for_sale`**, **`per_seat`**, seats **10** |
| Execution link | **id 5**, **`active`** (offer **12** ↔ tour **6**) |
| Conversion panel | **`booking_link`**: **`active`**, **`customer_action`**: **`open_exact_mini_app_tour`**, **`tour_code=B10-SO12-04fb1f`** |
| Channel | Telegram post live; **Rezervă** opens Mini App **`/supplier-offers/12`** (not **`/tours/{code}`**) |
| Prep | Reservation preparation screen hits API **404** with exact string below |

---

## 2. Channel CTA findings (Telegram → Mini App)

### 2.1 What builds the **Rezervă** URL?

- **`build_showcase_publication`** (`app/services/supplier_offer_showcase_message.py`) assembles caption HTML including **`_cta_block_html`**.
- **`_cta_block_html`** sets **Rezervă** href via **`mini_app_supplier_offer_url(mini_app_url=…, offer_id=offer_id)`** — see module docstring: *“**Rezervă** → Mini App supplier-offer landing”*.

```288:299:app/services/supplier_offer_showcase_message.py
def _cta_block_html(*, offer_id: int, settings: Settings) -> str | None:
    """One line: Detalii → bot ``supoffer_<id>`` | Rezervă → Mini App landing."""
    ...
    if mini_base:
        mini_url = html.escape(mini_app_supplier_offer_url(mini_app_url=mini_base, offer_id=offer_id))
        segments.append(f'✅ <a href="{mini_url}">{html.escape(_CTA_RESERVE_LABEL)}</a>')
```

- **`mini_app_supplier_offer_url`** (`app/services/supplier_offer_deep_link.py`) is **`{base}/supplier-offers/{id}`** only.

```33:37:app/services/supplier_offer_deep_link.py
def mini_app_supplier_offer_url(*, mini_app_url: str, offer_id: int) -> str:
    ...
    return f"{base}/supplier-offers/{int(offer_id)}"
```

- A separate helper **`mini_app_tour_detail_url`** exists for **`{base}/tours/{tour_code}`** (comment: *B11, align with `MiniAppTourDetailService`*), but **it is not referenced** from **`build_showcase_publication`** / **`_cta_block_html`**.

### 2.2 Answers (section A)

| # | Question | Answer |
|---|----------|--------|
| 1 | Exact function for **Rezervă** URL | **`mini_app_supplier_offer_url`**, called from **`_cta_block_html`** inside **`build_showcase_publication`**. |
| 2 | Always **`/supplier-offers/{id}`**? | **Yes** for channel assembly today. |
| 3 | Ever **`/tours/{tour_code}`**? | **Not** from showcase builder; **`mini_app_tour_detail_url`** exists for other flows (e.g. B11), not wired into showcase CTA. |
| 4 | Can builder see execution links? | **No.** **`build_showcase_publication(offer, settings)`** takes only **`SupplierOffer`** + **`Settings`** — no `Session`, no bridge, no **`tour_code`**, no execution-link repository. |
| 5 | Does publish expect execution link already? | **No.** **`publish_showcase_channel`** / **`SupplierOfferModerationService.publish`** do not load or check execution links; they call **`build_showcase_publication(row, cfg)`** then the Telegram adapter. |
| 6 | Publish allowed before execution link? | **Yes**, by code: publish gates are lifecycle **`APPROVED`**, packaging/showcase readiness, channel config, media gates — **not** execution link. |
| 7 | Consistent with docs? | **Yes.** **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** describes content from **`SupplierOffer`** + settings, not conversion-chain I/O. **[`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)** canonical chain lists **showcase publish → bridge → activate-for-catalog → execution link (after `published`)** — i.e. **execution link is explicitly later than channel publish**, not a prerequisite. **`_booking_link_row`** in **`build_conversion_status_panel`** states execution links are **created after showcase publish** when offer is not published. |
| 8 | Product options | **(a)** Keep stable **`/supplier-offers/{id}`** landing (current). **(b)** Require execution link before publish (would be a **new** product gate; contradicts current operator-workflow sequencing docs). **(c)** **Hybrid:** use **`mini_app_tour_detail_url`** when an active link + **`tour_code`** are knowable at **assembly time** — would need **`build_showcase_publication`** (or a wrapper) to accept **derived tour context** (session/read-model change; not present today). |

**Conclusion (CTA):** Pointing **Rezervă** at **`/supplier-offers/12`** is **current intentional design** (explicit in code comments and deep-link helper split), **not** an accidental omission in the narrow sense. Whether **marketing** should deep-link **`/tours/{code}`** once the chain is complete is an **open product decision** (B14B-class), not a sequencing bug relative to written runbooks.

---

## 3. Publish vs execution-link sequencing

| Question | Finding |
|----------|---------|
| Publish first, link later? | **Yes** in **docs** and **code**. Runbook: publish step precedes execution link in the canonical checklist. **`SupplierOfferModerationService.publish`** has no execution-link dependency. |
| **`operator_workflow`** | **`publish_showcase_channel`** is enabled from lifecycle/preview/packaging/media. **`create_execution_link`** is gated by **`execution_links_review.can_create_execution_link`** — independent boolean from publish action. Typical **order**: publish offer to channel → then create link when tour/catalog ready. |
| **`build_showcase_publication`** inputs | **Supplier offer snapshot + settings only** — cannot “see” active execution links without API changes. |

---

## 4. Reservation preparation blocker

### 4.1 Exact source of the string

- **HTTP:** **`app/api/routes/mini_app.py`** — **`get_tour_preparation`** raises **`HTTPException(404, detail="tour is not available for reservation preparation")`** when **`MiniAppReservationPreparationService.get_preparation`** returns **`None`**.

```441:454:app/api/routes/mini_app.py
@router.get("/tours/{tour_code}/preparation", ...)
def get_tour_preparation(...):
    preparation = MiniAppReservationPreparationService().get_preparation(...)
    if preparation is None:
        raise HTTPException(status_code=404, detail="tour is not available for reservation preparation")
```

### 4.2 Call chain

1. **`MiniAppReservationPreparationService.get_preparation`** — loads tour by code; requires **`OPEN_FOR_SALE`**; delegates to **`PrivateReservationPreparationService.get_preparable_tour`**.

```28:45:app/services/mini_app_reservation_preparation.py
    def get_preparation(...):
        tour = self.catalog_lookup_service.get_tour_by_code(session, code=code)
        if tour is None or tour.status not in self.STATUS_SCOPE:
            return None

        detail = self.reservation_preparation_service.get_preparable_tour(
            session,
            tour_id=tour.id,
            language_code=language_code,
        )
        if detail is None:
            return None
```

2. **`PrivateReservationPreparationService.get_preparable_tour`** — after catalog visibility (via **`PrivateTourBrowseService.get_tour_detail`**), enforces **status**, **seats_available > 0**, and **boarding points** (with **B10.4/B10.5** auto-default **only** for **full-bus catalog self-serve** package path).

```313:354:app/bot/services.py
    def get_preparable_tour(...):
        ...
        detail = self.tour_browse_service.get_tour_detail(...)
        if detail is None:
            return None
        if detail.tour.status != TourStatus.OPEN_FOR_SALE:
            return None
        if detail.tour.seats_available <= 0:
            return None
        if not detail.boarding_points:
            policy = TourSalesModePolicyService.policy_for_catalog_tour(detail.tour)
            if not policy.bookable_as_full_bus_package:
                return None
            ...  # auto-create default boarding for whole-bus package only
        return detail
```

### 4.3 Why tour **detail** can still load

- **`MiniAppTourDetailService.get_tour_detail`** requires **`OPEN_FOR_SALE`**, **`tour_is_customer_catalog_visible`**, and localized assembly — it does **not** require non-empty **`boarding_points`** for the read model; it returns **`boarding_points`** as stored (possibly empty).

```27:42:app/services/mini_app_tour_detail.py
    def get_tour_detail(...):
        ...
        if not tour_is_customer_catalog_visible(...):
            return None
        detail = self.language_aware_tour_service.get_localized_tour_detail(...)
```

So **read/detail** and **preparation/hold** intentionally diverge: **Layer A preparation** is stricter.

### 4.4 Answers (section B) for Tour #6

| # | Question | Answer |
|---|----------|--------|
| 1 | Service/function | **`MiniAppReservationPreparationService.get_preparation`** → **`PrivateReservationPreparationService.get_preparable_tour`** returns **`None`**; route maps that to **404**. |
| 2 | Trigger route | **`GET /mini-app/tours/{tour_code}/preparation`** (Mini App reservation prep screen). |
| 3 | Guard failed | First failing clause inside **`get_preparable_tour`**: most plausibly **`not detail.boarding_points`** with **`per_seat`** ( **`bookable_as_full_bus_package`** false) → immediate **`return None`**. Other possibilities: **`get_tour_detail`** **`None`** (visibility), **`seats_available <= 0`** — less consistent with “seats shown” smoke unless UI shows capacity from another field. |
| 4 | Failure category | **Boarding data** (no **`BoardingPoint`** rows for **per_seat**) is the **leading** hypothesis; not Telegram identity, not execution-link layer in this API path, not RFQ bridge. **`tour_is_customer_catalog_visible`** is enforced in browse path before preparable checks — if detail loads, visibility likely passed. |
| 5 | Data vs code | **Most likely data / tour setup gap** for a **per_seat** tour missing boarding stops, **not** a random bug in preparation logic (logic matches unit tests and B10.5 docs). |
| 6 | Read-only checks (next) | **Admin/ops:** inspect **Tour #6** **`boarding_points`** (count, times). **API (staging/local):** same **`GET …/preparation`**; compare with **`GET /mini-app/tours/B10-SO12-04fb1f`** body **`boarding_points`**. **Optional:** `TourDetailService` / admin tour read if available in your environment. |

---

## 5. Risk analysis

| Risk | Notes |
|------|--------|
| **Marketing vs execution deep link** | Channel always lands on **supplier-offer** URL; **B11** bot path can route to exact tour when conversion closure says so. Mixed UX if users expect **one-tap** catalog tour from channel — **product** clarity, not a failed audit. |
| **Publish before bookable tour** | The documented operator chain allows channel marketing before execution link; landing may show “bookable” only after downstream steps — operators must follow **[`docs/ADMIN_OPERATOR_WORKFLOW.md`](ADMIN_OPERATOR_WORKFLOW.md)** / runbook order. |
| **Prep 404 while detail looks fine** | **Operational:** **per_seat** tours without boarding points look “fine” on detail but **cannot** enter reservation preparation — confusing for smoke testers; **admin data completeness** should be checklisted after bridge activation. |

---

## 6. Recommendations (forward work — not implemented here)

| Track | Suggestion |
|-------|------------|
| **B14B** (channel CTA / sequencing) | If product wants **Rezervă** → **`/tours/{code}`** when link exists: extend **showcase assembly** (or post-publish **edit** flow) with **read-model inputs** (`tour_code`, link active) and use **`mini_app_tour_detail_url`**; or keep landing-only and document. Optional: **soft gate** “warn if publishing without execution link” — **product** decision (today **not** enforced). |
| **B14C** (reservation readiness) | For **Tour #6**: **verify/add `BoardingPoint` rows** for **`per_seat`** (or re-run bridge/tour activation checklist that creates them). If boarding exists and prep still **404**, re-check **`seats_available`**, **`PrivateTourBrowseService`** visibility vs catalog detail path, and **`LanguageAwareTourRead`** / **`TourDetailService`** consistency. |

---

## 7. Explicit non-goals (B14A)

- **No** application code changes.
- **No** test changes.
- **No** migrations.
- **No** API calls (including production).
- **No** publish / retry / resend.
- **No** execution-link create/close/replace.
- **No** orders, reservations, or payments.
- **No** Mini App behavior changes.

---

## 8. References (inspected)

**Docs:** [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md), [`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md), [`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md), [`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md), [`docs/HANDOFF_B13G_FULL_CONVERSION_SMOKE_RESULT_TO_NEXT_STEP.md`](HANDOFF_B13G_FULL_CONVERSION_SMOKE_RESULT_TO_NEXT_STEP.md), [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md), [`docs/MINI_APP_UX.md`](MINI_APP_UX.md), [`docs/TECH_SPEC_TOURS_BOT_v1.1.md`](TECH_SPEC_TOURS_BOT_v1.1.md), [`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`](IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md) — B14A used them for cross-checking **operator sequencing** and UX intent where cited above; primary evidence is **source code**.

**Code paths:** `supplier_offer_showcase_message.py`, `supplier_offer_deep_link.py`, `supplier_offer_moderation_service.py`, `supplier_offer_operator_workflow.py`, `supplier_offer_conversion_status_panel.py`, `mini_app.py` (preparation route), `mini_app_reservation_preparation.py`, `mini_app_tour_detail.py`, `app/bot/services.py` (`PrivateReservationPreparationService`).

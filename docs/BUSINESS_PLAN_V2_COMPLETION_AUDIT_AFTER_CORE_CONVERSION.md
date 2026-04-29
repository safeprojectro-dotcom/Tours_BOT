# BUSINESS-plan-v2 completion audit (after core supplier-offer conversion closure)

**Scope:** Documentation audit only. **No** `BUSINESS_PLAN_V3` **;** **no** full roadmap rewrite **.**  
**Anchor milestone:** **SUPPLIER OFFER → CENTRAL MINI APP CATALOG CONVERSION CLOSURE** is **test-proven** **`tests/unit/test_supplier_offer_catalog_conversion_closure.py`** **(2026-04-29)** alongside **`GET /admin/supplier-offers/{offer_id}/review-package`** **`conversion_closure`** **.**

---

## 1. What BUSINESS-plan-v2 wanted (authoritative sources)

From **`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`** (**B1–B13**):

- **Core rule:** A supplier offer becomes visible as a customer **`Tour`** in the Mini App catalog **only** via an **explicit, auditable bridge** — **not** silent ORM/AI/supplier-only shortcuts **.**
- **Separation of gates:** Packaging approval (**`approved_for_publish`**), moderation/publication lifecycle, **Telegram channel** showcase, **B10** bridge (**draft `Tour`**), **B10.2** catalog activation (**`open_for_sale`**), **execution link** (**`supplier_offer` → `tour`**), and **Layer A** booking/payment **remain distinct** **.**
- **Track map:** Intake/data/dialog (**B1–B3**), AI packaging draft-only (**B4**), admin moderation (**B5**), branded showcase (**B6**), media/card (**B7**), recurrence (**B8**), bridge design/implementation (**B9–B10**), deep links (**B11**), ops visibility (**B12**), production smoke (**B13**) **.**

From **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`**:

- **V2 Tracks 0–5g.x :** supplier foundation, offer publication/moderation, RFQ marketplace and bridges — **Layer A** preserved **;** **B-line** (**supplier offer → Mini App**) is **called out separately** from V2 row numbering **.**

From **`docs/IMPLEMENTATION_PLAN.md`** (legacy phase tracker):

- Remains **historical / MVP phase** framing **;** live marketplace work is tracked in **V2** + **B-line** docs **.**

---

## 2. What is now done (high level)

| Area | Status |
|------|--------|
| **Core booking / Layer A** | Frozen per **`TRACK_0`** **;** semantics unchanged by supplier marketplace **.** |
| **V2 supplier marketplace tracks** | Tracks **0–5g.1** marked **completed** in **`IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`** **.** |
| **B2 / offer data** | Implemented handoffs per BUSINESS plan §5 **.** |
| **B5–B7.2** | Packaging review, branded preview, media/card metadata & **`card_render_preview`** plan **.** |
| **B8** | Draft recurrence **`POST …/recurrence/draft-tours`**, **B8.2** activation policy, **B8.3** duplicate-active guard **.** |
| **B9 / B10–B10.5** | Bridge creation/linking, **draft** **`Tour`**, **activate-for-catalog**, **full_bus** Layer A / Mini App semantics, boarding fallback **.** |
| **B11 (first slice)** | **`supoffer_<id>`** → Mini App **`/tours/{code}`** when active execution link + **`OPEN_FOR_SALE`** + visibility — see **`CHAT_HANDOFF`**, **`OPEN_QUESTIONS`** **.** |
| **B12/B13 (showcase slice)** | Deterministic showcase template, **`GET …/showcase-preview`**, ops runbook **`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`** **.** |
| **Admin review gate** | **`GET …/review-package`** + **`conversion_closure`** read-only aggregation **.** |
| **Core conversion closure** | Explicit chain **test-proven:** bridge → activate-for-catalog → **`MiniAppCatalogService`** lists **`Tour`** **without** execution link → publish → execution link → landing + B11 routing → **`conversion_closure`** complete **`next_missing_step` null** **.** |

**Proven invariants (tests + docs):**

- **Moderation approval alone** does **not** create **`Tour`** / bridge **.**
- **Catalog visibility** is **`Tour`**- / **`OPEN_FOR_SALE`**-driven **;** **not** gated on execution link **.**
- **Supplier-offer landing** and **bot exact** **`/tours/{code}`** routing **require** active **execution link** **.**
- **Layer A** booking/payment **unchanged** in scope of closure tests **.**

---

## 3. Partially done

| Item | Notes |
|------|--------|
| **B7.3** | Policy **B7.3A** accepted **;** **download / durable storage / pixels / channel `sendPhoto`** **not** shipped until an explicit slice (**B7.3B** stub or storage) **.** |
| **B10.6** | Bot **router/consultant** (avoid duplicate catalog in chat) **:** parts implemented **;** posture **postponed / iterative** per **`CHAT_HANDOFF`** **.** |
| **B11** | **First** routing slice **done** **;** further product expansion **optional** **.** |
| **B12** | Admin/ops visibility **ongoing** alongside operator surfaces **.** |
| **B13** | Showcase/marketing slices **in progress** **;** full production **E2E** checklist **not** replaced by unit closure tests alone **.** |
| **`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md` § Status** | Some lines remain dense/historical (**e.g.** **B11** wording); **authoritative** completion signals are **`CHAT_HANDOFF`**, **`OPEN_QUESTIONS`**, this audit **.** |

---

## 4. Still open

- **B7.3** implementation vs **metadata-only** MVP **.**
- **B10.6** completion vs **Mini App** as single catalog truth **.**
- **Recurring / B8** re-run idempotency clutter **;** **second vehicle same date** — **ops** policy (**see** **`OPEN_QUESTIONS`** **).**
- **Production E2E smoke** on real infra/supplier (**see** **`HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE.md`** **next after** block **).**
- **Admin workflow consolidation/UI** (optional product track **).**
- **AI-approved marketing draft → deterministic showcase** wiring (**`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`** — **not** auto-publish **).**

---

## 5. Next large functional block (explicit choice — not auto-started)

Per **`HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE.md`** and **`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`** §5:

1. **Production / staging E2E smoke** for a **real** supplier offer through the same explicit gates **.**
2. **Admin workflow UX** consolidation (surface **`review-package`** / closure checks **without** collapsing gates **).**
3. **Media pipeline** (**B7.3B** / storage) **if** marketing priority **.**
4. **Further B10.6 / B11 / B12/B13** polish **per** stakeholder priority **.**

**Do not** treat this audit as approval to start **BUSINESS_PLAN_V3** **.**

---

## 6. References

| Document | Role |
|----------|------|
| [`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) | **B1–B13** roadmap + guardrails |
| [`IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`](IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md) | **V2** tracks **0–5g.x** |
| [`CHAT_HANDOFF.md`](CHAT_HANDOFF.md) | Continuity + closure proof pointer |
| [`OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) | Tech debt + checkpoints |
| [`HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE.md`](HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE.md) | Block goals + **next after** |
| [`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) | Showcase publish ops procedure |

---

## Document control

| Field | Value |
|-------|--------|
| **Created** | 2026-04-29 |
| **Kind** | BUSINESS-plan-v2 **completion audit** (post core conversion) |
| **Supersedes** | — (**does not** retire **`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`**) |

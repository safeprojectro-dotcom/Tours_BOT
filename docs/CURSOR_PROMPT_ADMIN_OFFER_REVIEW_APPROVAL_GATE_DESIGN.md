# CURSOR_PROMPT_ADMIN_OFFER_REVIEW_APPROVAL_GATE_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

Это design/contract step для большого функционального блока:

ADMIN OFFER REVIEW & APPROVAL GATE

Не менять код в этом шаге.

---

## Главная бизнес-цель

Закрыть безопасный admin review gate перед тем, как supplier offer попадёт в центральную Mini App витрину.

Правильная цепочка:

Supplier raw offer
→ AI/deterministic packaging draft
→ Admin review / approve
→ Create/link Tour
→ Activate Tour for Mini App catalog
→ Channel showcase / Bot / Mini App conversion
→ Booking/payment through Layer A

---

## Почему этот блок нужен сейчас

Мы уже сделали:

- Telegram showcase post template
- safe CTA
- channel link preview disabled
- showcase preview endpoint
- bot router / consultant behavior
- supplier offer deep-link routing
- offer → tour bridge pieces
- tour activation pieces

Но бизнес-процесс всё ещё не закрыт, потому что перед попаданием оферты в центральную Mini App витрину нужен понятный admin review gate.

Админ должен видеть:

1. raw supplier/admin input
2. AI/deterministic prepared public copy
3. final showcase preview
4. proposed Tour fields
5. missing fields / blockers / warnings
6. readiness for bridge
7. readiness for Mini App catalog activation
8. recommended next admin action

---

## Source documents to read first

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/IMPLEMENTATION_PLAN.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/MINI_APP_UX.md
- docs/TESTING_STRATEGY.md

Also inspect current code:

- app/api/routes/admin.py
- app/schemas/supplier_admin.py
- app/models/supplier.py
- app/models/tour.py
- app/models/enums.py
- app/services/supplier_offer_moderation_service.py
- app/services/supplier_offer_showcase_message.py
- app/services/supplier_offer_tour_bridge_service.py
- app/services/admin_tour_write.py
- app/services/mini_app_supplier_offer_landing.py
- app/repositories/supplier_offer.py
- app/repositories/supplier_offer_execution_link.py
- app/repositories/supplier_offer_tour_bridge.py if present
- tests/unit/test_supplier_offer_track3_moderation.py
- tests/unit/test_supplier_offer_tour_bridge_b10.py
- tests/unit/test_supplier_offer_showcase_ro.py
- any admin supplier offer tests

If some paths differ, locate equivalents.

---

## Architecture rules

Preserve these rules:

- Supplier Offer = raw/source facts.
- AI/deterministic packaging = draft only.
- Admin = final decision maker.
- Tour = customer-facing sellable catalog object.
- Mini App = execution truth and conversion.
- Layer A = booking/payment authority.
- Channel = marketing showcase.
- Bot = router/consultant.
- visibility != bookability.
- approved package != Telegram publish.
- approved package != Mini App catalog activation.
- bridge creation != open_for_sale.
- no hidden ORM trigger from SupplierOffer to Tour.
- no AI-created Tour.
- no supplier bypass.
- no booking/payment side effects in admin review.
- no automatic publish.

---

## Goal of this Plan step

Design the first implementation slice for Admin Offer Review & Approval Gate.

Do not implement code yet.

Answer:

What read model / endpoint / service should admin use to decide whether a supplier offer package is ready for:

1. approval,
2. bridge/create-link Tour,
3. catalog activation,
4. channel showcase publish?

---

## Questions to answer

### 1. Current admin offer lifecycle

Map current lifecycle and endpoints:

- supplier offer creation/intake
- ready_for_moderation
- approve/reject
- showcase-preview
- publish/retract
- bridge/create-link Tour
- activate Tour for catalog
- execution link creation
- recurring/generated Tour if relevant

For each:
- endpoint
- service
- lifecycle/status precondition
- side effects
- whether it is read-only or mutating

---

### 2. Current admin review gaps

Identify what admin cannot currently see in one place:

- raw supplier input
- AI/deterministic packaging draft
- public copy / showcase preview
- missing required fields
- proposed Tour data
- bridge status
- active execution link status
- catalog visibility status
- Mini App actionability
- full_bus/per_seat interpretation
- price/package truth
- program/included/excluded completeness
- warnings/blockers

---

### 3. Proposed review package endpoint

Design a read-only endpoint:

```http
GET /admin/supplier-offers/{offer_id}/review-package
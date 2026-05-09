# CURSOR_PROMPT_B11_SUPPLIER_OFFER_DEEP_LINK_ROUTING_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Используй самый сильный доступный reasoning model.

Cursor mode: Plan.

Это design/contract step. Не менять код в этом шаге.

---

## Before coding / before editing

Сначала проанализируй текущий код и документы, но не вноси изменения.

Нужно спроектировать B11 — Telegram deep-link routing для Supplier Offer → exact Tour / Mini App.

---

## Current checkpoint

B8 recurring supplier offers line закрыта.

Completed:
- B8 recurring draft Tour generation
- B8 stabilization
- B8.2 activation policy design
- B8.3 duplicate active Tour activation guard
- B8.4 docs sync

B7 status:
- B7.1 media review metadata completed
- B7.2 card render preview plan completed
- B7.3A media policy accepted
- B7.3B metadata-only publish_safe stub implemented

Latest known B7.3B behavior:
- packaging_draft_json["publish_safe"] is metadata-only
- status = deferred
- reason = no_durable_media_storage
- storage_kind = none
- object_key/public_url = null
- no Telegram download
- no object storage
- no real card rendering
- no media publish

Current business context:
- Telegram Channel = marketing showcase
- Telegram Bot = router / consultant / entry point, not duplicate Mini App catalog
- Mini App = execution truth and conversion
- Layer A = booking/payment authority
- Supplier Offer = raw supplier proposal/source facts
- Tour = customer-facing sellable catalog object
- Admin = final decision maker
- AI = draft generator only

Core principle:
- visibility != bookability
- Mini App execution truth must stay strict and current
- Telegram/channel can be softer showcase but must not contradict Mini App truth

---

## B11 business goal

Implement/prepare Telegram Deep Link Routing:

`supoffer_<id>` should route as follows:

1. If Supplier Offer has a linked Tour and that Tour is active/open_for_sale:
   - direct user toward exact Tour detail in Mini App
   - do not show generic catalog only

2. If linked Tour exists but is draft / not open_for_sale:
   - do not allow booking
   - show safe fallback:
     - offer is being prepared / not bookable yet
     - ask question/help
     - request custom trip if appropriate
     - maybe open general catalog

3. If no linked Tour exists:
   - show offer landing / fallback CTA
   - do not invent availability
   - do not create Tour
   - do not activate Tour
   - do not publish

4. If Supplier Offer exists but was rejected/invalid:
   - show safe unavailable message or route to help/catalog

5. If Supplier Offer does not exist:
   - show generic safe fallback

---

## Source documents to read first

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/MINI_APP_UX.md
- docs/TESTING_STRATEGY.md

Inspect current code:

- app/bot/handlers/start/private start handlers
- app/bot/handlers/supplier offer deep-link handling if exists
- supplier offer repositories/services
- SupplierOfferTourBridge service/repository/model
- supplier_offer_execution_links if present
- Mini App tour detail route generation / API client / URLs
- admin routes around Supplier Offer / Tour bridge
- existing tests for bot deep links and supplier offer bridge

If some files do not exist, mention in final report and continue with available code.

---

## Goal of this Plan step

Design the smallest safe B11 implementation slice.

Do not implement code.

Answer:

How should `/start supoffer_<id>` behave now that Supplier Offer → Tour bridge and Tour activation exist?

---

## Questions to answer

### 1. Current deep-link behavior

Find current behavior for:

- `/start supoffer_<id>`
- `/start tour_<code>`
- Mini App tour detail links
- existing supplier offer publish CTA

Report:
- current handler location
- current fallback behavior
- whether it already resolves SupplierOffer
- whether it already checks linked Tour
- whether it opens Mini App or just text/catalog

---

### 2. Source of truth for linked Tour

Determine what should be used as source of truth:

Options:
- SupplierOfferTourBridge
- supplier_offer_execution_links / Y27
- direct field on SupplierOffer if exists
- Tour code/source relation
- B8 audit table for generated recurring Tours

Recommend for B11 MVP.

Expected direction:
- If B10 bridge exists and Tour is active/open_for_sale, use that exact linked Tour.
- Do not use B8 recurring generated Tours unless an explicit selected/active link exists.
- Do not infer from titles/dates.

---

### 3. Tour status gate

Define status rules:

- open_for_sale → can route to exact Mini App Tour detail
- draft → not bookable, fallback
- sales_closed/cancelled/postponed/completed → fallback
- guaranteed? clarify if guaranteed is catalog-visible or separate from open_for_sale in this codebase
- full_bus fixed package semantics must not be broken

Do not change booking/payment logic.

---

### 4. Mini App URL contract

Identify how the bot should create a Mini App link.

Questions:
- Is there already route `/tours/{tour_code}` in Mini App UI?
- Is there a URL pattern for exact tour detail?
- Does Telegram WebApp button need a specific URL?
- Do we need backend route to build URL or can bot build from config?
- What env var/base URL is used?

Define recommended contract.

---

### 5. Fallback copy and CTA

Design safe user messages for:

A. linked active Tour exists  
B. linked Tour exists but draft/not active  
C. no linked Tour  
D. rejected/unavailable Supplier Offer  
E. invalid supplier offer id

Rules:
- concise
- factual
- no invented price/seats
- one main CTA
- bot is router/consultant, not duplicated Mini App catalog
- if uncertain, route to help/custom request/general catalog

---

### 6. Scope boundaries for implementation

Decide what B11 first implementation should do.

Possible small slice:
- update `/start supoffer_<id>` handler
- resolve SupplierOffer
- resolve linked active Tour
- return Mini App exact Tour button
- safe fallback text otherwise
- tests for routing decisions

Do not implement:
- Telegram channel publish changes
- media/photo posting
- new Tour creation
- activation
- booking/payment
- Mini App UI redesign
- B10.6 bot redesign
- B12/B13 template library

---

### 7. Tests needed

Recommend focused tests:

- active linked Tour → exact Mini App Tour link
- linked draft Tour → no booking link / fallback
- no linked Tour → fallback
- invalid SupplierOffer id → fallback
- rejected SupplierOffer → fallback
- full_bus active Tour → still exact Mini App link, but no per-seat wording
- existing `/start tour_<code>` behavior unchanged

---

## Non-goals

Do not propose implementing now:

- Telegram publish
- channel post editing
- sendPhoto/sendMediaGroup
- media pipeline
- real card rendering
- storage
- supplier lifecycle side effects
- auto bridge
- auto activation
- booking/order/reservation/payment changes
- Mini App UI changes
- B10.6 full bot router redesign
- B12/B13 template library
- B8 recurrence changes

---

## Required final report

Return structured report:

1. Current deep-link behavior found
2. Recommended B11 routing contract
3. Source of truth for linked Tour
4. Tour status gate
5. Mini App URL/button contract
6. Fallback copy/CTA rules
7. Files likely affected in implementation
8. Tests needed
9. Risks / ambiguities
10. Recommended next Agent prompt name

Do not change files in this Plan step.
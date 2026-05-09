# CURSOR_PROMPT_B10_6_BOT_ROUTER_CONSULTANT_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

Это design/contract step. Не менять код в этом шаге.

---

## Current checkpoint

B7/B8/B11 recent lines:

### B7 media
- B7.1 media review metadata completed.
- B7.2 card render preview plan completed.
- B7.3A media policy accepted.
- B7.3B metadata-only publish_safe stub implemented.
- No real download/storage/render/publish.

### B8 recurring supplier offers
- B8 recurring draft Tour generation completed.
- B8.2 activation policy accepted.
- B8.3 duplicate active Tour activation guard implemented.
- B8.4 docs sync completed.

### B11 deep-link routing
- `/start supoffer_<id>` now resolves active `supplier_offer_execution_link`.
- If linked Tour is `OPEN_FOR_SALE` and customer-visible:
  - bot gives exact Mini App CTA to `/tours/{tour_code}`;
  - generic catalog overview is skipped after exact Tour CTA.
- Fallback remains safe for no link / draft / invalid / unavailable offers.
- Commit:
  - b29d7e4 — feat: route supplier offer deep links to exact tours
  - 72af8bc — docs: add B11 exact tour CTA handoff

---

## Business context

Telegram Channel = marketing showcase.  
Telegram Bot = router / consultant / entry point, not duplicate Mini App catalog.  
Mini App = execution truth and conversion.  
Layer A = booking/payment authority.  
Supplier Offer = raw supplier proposal / source facts.  
Tour = customer-facing sellable catalog object.  
Admin = final decision maker.  
AI = draft generator only.

Core principle:

- visibility != bookability
- Mini App execution truth must stay strict and current
- Telegram/channel can be softer showcase but must not contradict Mini App truth
- Bot must not invent price/seats/status
- Bot should route to Mini App or ask clarifying/help question instead of duplicating full catalog

---

## Why B10.6 now

B11 fixed exact deep-link routing for supplier offers.

But Telegram Bot may still duplicate too much Mini App catalog behavior:
- sending generic catalog overviews;
- showing too many tour cards;
- exposing buttons/actions that belong in Mini App;
- using old/full-bus-inconsistent copy;
- mixing consultant/router role with catalog UI.

B10.6 should define a safer bot role:

- short summary
- exact Mini App CTA when possible
- ask one question/help
- request custom trip
- route to Mini App catalog
- no duplicated booking/catalog UX
- no old full_bus wording like “choose seats” when full_bus package semantics apply

---

## Source documents to read first

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/HANDOFF_B11_1_EXACT_TOUR_CTA_SKIP_GENERIC_CATALOG_FIX.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/MINI_APP_UX.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/TESTING_STRATEGY.md

If some files are missing, do not invent content. Mention missing files in the final report and continue with available code/docs.

---

## Code to inspect

Inspect current bot behavior:

- app/bot/handlers/private_entry.py
- app/bot/handlers/catalog browsing handlers
- app/bot/keyboards.py
- app/bot/messages.py
- app/bot/services.py
- app/services/group_private_cta.py
- app/services/supplier_offer_bot_start_routing.py
- app/services/supplier_offer_deep_link.py
- any tests around private entry, tour browsing, supoffer, full_bus

Look specifically for:
- where generic catalog overview is sent;
- where in-chat tour cards/details are rendered;
- where Mini App root vs exact Tour URL is used;
- where reservation/preparation buttons are exposed in bot;
- whether full_bus wording is safe;
- what `/start`, `/tours`, `/start tour_<code>`, `/start supoffer_<id>` currently do.

---

## Goal of this Plan step

Design B10.6: Telegram Bot router/consultant redesign.

Answer:

What is the smallest safe implementation slice to make the Telegram Bot stop duplicating Mini App catalog behavior while preserving useful routing and existing flows?

Do not implement code in this step.

---

## Questions to answer

### 1. Current duplication map

Identify where bot duplicates Mini App catalog:

- generic catalog overview
- catalog cards in chat
- tour detail in chat
- reserve/preparation buttons
- filters/search buttons
- full_bus/per_seat copy
- supplier offer deep-link behavior after B11
- group-to-private CTA behavior

For each, classify:

- keep as-is
- simplify
- replace with Mini App CTA
- defer
- risky to touch now

---

### 2. Desired bot role by entry point

Define desired behavior for each entry:

#### `/start` generic
Should it:
- show short intro + Mini App catalog CTA?
- still show small catalog preview?
- ask one question?
- show language/help?

#### `/tours`
Should it:
- open Mini App catalog?
- show very short 1–3 teaser options?
- avoid full in-chat catalog?

#### `/start tour_<code>`
Should it:
- route to exact Mini App Tour detail?
- keep in-chat detail?
- show short summary + exact Tour CTA?
- preserve existing behavior for now?

#### `/start supoffer_<id>`
Already B11:
- exact linked Tour CTA when possible
- fallback when not possible
Should B10.6 adjust fallback copy/buttons?

#### Group chat
Should remain short CTA to private/Mini App, no personal data, no long catalog.

---

### 3. Full_bus / per_seat safety

Review whether bot copy/buttons still imply per-seat self-serve for full_bus fixed package.

Rules:
- per_seat = customer books individual seats
- full_bus = customer books whole bus/package
- custom_request = separate flow for another route/date/bus/capacity
- bot must not say “choose 5 seats” for full_bus
- Mini App/Layer A remain execution authority

Recommend B10.6 changes if any old copy/buttons violate this.

---

### 4. Mini App CTA hierarchy

Define button strategy:

- exact Tour button when exact Tour known
- Mini App catalog button when not exact
- Ask question / Help
- Request custom trip
- My bookings
- Language

Avoid too many competing buttons.

---

### 5. Scope boundaries

B10.6 must not implement:
- new booking/payment logic
- Mini App UI changes
- supplier lifecycle changes
- Telegram publish changes
- media changes
- B12/B13 templates
- broad AI assistant runtime
- RAG
- custom request marketplace changes unless already existing CTA is reused

---

### 6. Recommended first implementation slice

Choose the smallest safe Agent step.

Possible candidates:

A. `/start` and `/tours` become router-first: short text + Mini App catalog CTA, no generic catalog overview.  
B. `/start tour_<code>` becomes exact Mini App Tour CTA, with minimal in-chat summary.  
C. Remove/guard reservation/preparation buttons from bot for full_bus cases.  
D. Update copy/buttons only, no behavior changes.  
E. B10.6 docs-only policy acceptance first.

Recommend one first slice and explain why.

Expected bias:
- small, testable, reversible
- avoid breaking existing private browsing completely
- preserve B11 exact supplier-offer path
- prefer router-first over duplicated catalog

---

### 7. Tests needed

Recommend focused tests:

- `/start` generic still works
- `/tours` or catalog entry routes to Mini App catalog
- `/start supoffer_<id>` B11 exact path still works
- `/start tour_<code>` unchanged or changed intentionally
- full_bus copy does not include per-seat wording if touched
- no booking/payment side effects

---

## Non-goals

Do not propose implementing now:

- Mini App UI redesign
- booking/payment/order/reservation changes
- SupplierOffer/Tour creation
- Tour activation
- Telegram channel publish
- media/photo/card changes
- B7.4/B7.5/B7.6
- B12/B13 template/channel adapters
- RAG/AI assistant runtime
- broad group bot rewrite
- custom request marketplace redesign

---

## Required final report

Return a structured report:

1. Current duplication map
2. Desired bot role by entry point
3. Full_bus/per_seat risk assessment
4. Mini App CTA hierarchy recommendation
5. Recommended B10.6 first implementation slice
6. Files likely affected
7. Tests needed
8. Risks / ambiguities
9. Non-goals preserved
10. Recommended next Agent prompt name

Do not change files in this Plan step.
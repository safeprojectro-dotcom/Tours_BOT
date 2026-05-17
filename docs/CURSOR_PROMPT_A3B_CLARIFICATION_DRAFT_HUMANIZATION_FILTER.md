# CURSOR_PROMPT_A3B_CLARIFICATION_DRAFT_HUMANIZATION_FILTER

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- b0143e7 feat: add supplier clarification draft split
- 79010f5 feat: add supplier intake auto validation
- ba6564b feat: standardize cockpit card detail UX
- 80a3a87 feat: standardize cockpit queue list UX
- 5112c21 feat: polish admin cockpit telegram ux

## Current state

A3 implemented read-only supplier clarification drafts:

- SupplierClarificationDraftRead
- SupplierClarificationDraftService
- AdminAutomationCockpitCardRead.clarification_draft
- Telegram card detail clarification block
- no sending
- no supplier notification
- no AI
- no DB/migrations/writes

Manual UAT after A3 shows the architecture is correct, but quality is not acceptable yet.

Problem seen in Telegram supplier-offer card detail:

The supplier-facing block still contains technical/internal/debug content such as:

- content_quality
- orphan_promo_code
- description_thin
- prepare_chain:blocked:create_tour_bridge
- cta_safety:missing_execution_link
- offer_debug.flags_publish_not_ready
- publish_readiness:blocked
- publish_readiness:Cover/media gate...
- gate:showcase_media
- gate:showcase_preview
- execution link
- Mini App
- media_review_replacement_requested

This violates the A3 critical requirement.

## Critical product requirement

Supplier-side users may be:

- drivers
- elderly people
- non-technical supplier staff
- people who only understand practical route/vehicle/price/date/photo questions

Therefore the supplier-facing message must be:

- short
- simple
- polite
- sequential
- in Romanian
- understandable without any platform knowledge
- free of all internal platform/debug terms
- max 5 questions
- one question per line
- no English technical copy

If a phrase is not clearly safe for supplier-facing communication, it must NOT be included in the supplier-facing draft.

---

# Current block

# A3B — Clarification Draft Humanization & Hard Technical Filter

## Goal

Fix A3 supplier clarification drafts so supplier-facing copy is safe, human, and simple.

This is a targeted production fix, not a new feature.

## Safety boundaries

Do NOT:
- add migrations
- add write endpoints
- mutate supplier_offers
- mutate tours
- mutate orders/payments/reservations
- publish to Telegram
- send supplier notifications
- schedule messages
- call AI
- call external providers
- change B11 routing
- change Layer A logic
- execute prepare_conversion_chain
- create execution links

This block is read-only draft generation/rendering only.

---

# Required references

Inspect and align with:

- app/schemas/supplier_clarification_draft.py
- app/services/supplier_clarification_draft_service.py
- app/schemas/supplier_offer_intake_validation.py
- app/services/supplier_offer_intake_validation_service.py
- app/schemas/admin_automation_cockpit.py
- app/services/admin_automation_cockpit_service.py
- app/bot/automation_cockpit_telegram.py
- app/bot/messages.py
- tests/unit/test_supplier_clarification_draft_service.py
- tests/unit/test_supplier_offer_intake_validation_service.py
- tests/unit/test_admin_automation_cockpit.py
- tests/unit/test_automation_cockpit_telegram.py
- docs/HANDOFF_A3_MISSING_INFO_CLARIFICATION_DRAFTS.md

---

# Required behavior

## 1. Hard forbidden terms filter for supplier-facing text

Supplier-facing asks and supplier_facing_message_ro must never contain these terms or patterns:

- execution link
- conversion chain
- CTA
- exact-tour
- Mini App
- blockers_count
- prepare_chain
- prepare conversion
- prepare_conversion_chain
- cta_safety
- publish_readiness
- offer_debug
- flags_publish_not_ready
- content_quality
- orphan_promo_code
- description_thin
- media_review_replacement_requested
- publish_safe
- showcase_media
- showcase_preview
- catalog gate
- gate:
- B7
- B10
- B11
- B15
- Layer A
- internal path
- admin_action_path
- admin_tour_path
- route key
- payload
- debug
- blocker code
- snake_case technical identifiers
- bracketed technical codes like [media_review_replacement_requested]

If a candidate supplier ask contains any forbidden term, it must be routed to internal_admin_tasks or dropped.

The supplier-facing message must be generated only from safe mapped questions.

---

## 2. Whitelist supplier-facing asks

Supplier-facing asks should only come from a small whitelist of human questions.

Allowed Romanian asks:

1. `Vă rugăm să trimiteți o fotografie clară pentru ofertă.`
2. `Vă rugăm să confirmați prețul pentru această ofertă.`
3. `Vă rugăm să confirmați moneda prețului.`
4. `Vă rugăm să confirmați data și ora plecării.`
5. `Vă rugăm să confirmați data și ora întoarcerii.`
6. `Vă rugăm să confirmați ruta și destinația.`
7. `Vă rugăm să confirmați locul de îmbarcare.`
8. `Vă rugăm să confirmați durata aproximativă a drumului.`
9. `Vă rugăm să confirmați câte locuri sunt disponibile.`
10. `Vă rugăm să confirmați tipul vehiculului.`
11. `Vă rugăm să confirmați ce este inclus în preț.`
12. `Vă rugăm să confirmați ce nu este inclus în preț.`
13. `Vă rugăm să trimiteți o descriere scurtă a excursiei.`
14. `Vă rugăm să confirmați dacă există reducere pentru această ofertă.`
15. `Dacă există reducere, vă rugăm să confirmați valoarea, perioada și condițiile reducerii.`
16. `Vă rugăm să confirmați condițiile de plată.`
17. `Vă rugăm să confirmați condițiile de anulare.`

Do not pass through arbitrary validation text as supplier-facing copy.

If a validation phrase cannot be mapped to one of these simple allowed questions, it must not appear in supplier-facing asks.

---

## 3. Supplier-facing message format

Use exactly this style:

```text
Bună ziua! Pentru ofertă avem nevoie de câteva clarificări:

1. Vă rugăm să trimiteți o fotografie clară pentru ofertă.
2. Vă rugăm să confirmați prețul pentru această ofertă.
3. Vă rugăm să confirmați data și ora plecării.

Mulțumim!
```

Implemented in `SupplierClarificationDraftService`: whitelist-only `supplier_facing_asks` (max 5), `supplier_facing_message_ro`, hard forbidden filter, `draft_version` `a3b_v1`.
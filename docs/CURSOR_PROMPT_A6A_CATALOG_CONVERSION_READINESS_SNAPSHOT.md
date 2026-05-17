# A6A — Catalog / Conversion Readiness Snapshot

## Context

We are continuing Tours_BOT.

A5 passed UAT:
- supplier clarification outbox works
- save/list consistency fixed
- draft → ready_for_review → sent_externally_later lifecycle passed
- no automatic supplier sending
- production migration 20260617_33 was applied

Now implement the next safe block:

A6A — Catalog / Conversion Readiness Snapshot

This is NOT conversion execution.
This is NOT bridge creation.
This is NOT tour creation.
This is NOT catalog activation.
This is NOT public publish.

It is a read-only admin/cockpit projection that helps the admin understand whether a supplier offer is ready for catalog/conversion preparation.

## Business goal

For supplier-offer cockpit cards, show a clear read-only “Catalog / conversion readiness” section in Telegram card detail.

The admin should quickly understand:

1. Is this offer ready to prepare for catalog?
2. Is it blocked?
3. What is missing?
4. Is there an associated tour / execution link / active catalog route?
5. Is the Mini App exact-tour CTA safe?
6. What is the next safe internal action?

The copy must be simple Romanian, understandable by non-technical admins.

## Architecture constraints

Preserve all current invariants:

- PostgreSQL-first.
- Service layer owns business rules.
- Repository layer is persistence only.
- Bot/UI only renders projections and calls services.
- Layer A booking/payment remains untouched.
- No order/payment/reservation mutation.
- No B11 routing changes.
- No public Telegram publish.
- No supplier notification send.
- No scheduler.
- No QR/token work.
- No AI execution.
- No external provider calls.
- No bridge/tour/execution-link creation in this step.

## Scope

### In scope

Add a pure read-only projection for supplier-offer cards:

Suggested name:
- `SupplierOfferCatalogConversionReadinessRead`
- `SupplierOfferCatalogConversionReadinessService`

or, if existing naming suggests better, use a consistent name.

The projection may use only already available read data attached to the automation cockpit / publishing console item / commercial context / prepare-chain hints.

It must be deterministic and side-effect free.

Attach the projection to supplier-offer cockpit cards where applicable.

Render it in Telegram card detail as a compact block:

RO example:

🧭 Catalog / conversie:
Status: Necesită pregătire
Blocaj principal: lipsește legătura ofertă–tur
Mini App CTA: nu este încă sigur
Următorul pas: pregătește legătura ofertă–tur în admin

For ready state:

🧭 Catalog / conversie:
Status: Pregătit pentru verificare
Tur: disponibil
Mini App CTA: verifică linkul exact înainte de publicare
Următorul pas: verifică turul în Mini App

For non supplier-offer cards / tour-only cards:
- do not show supplier-offer conversion readiness unless meaningful.
- do not invent data.
- if the card is tour-only, keep current detail behavior.

### Optional but useful

If queue list already shows `Catalog / conversie`, make list lines more readable, but do not expand scope too much.

### Out of scope

Do NOT implement:
- POST/PUT/PATCH routes for conversion
- bridge creation
- tour creation
- activate_tour_for_catalog
- execution link creation
- B11 deep-link routing changes
- public publish
- supplier send
- background job
- AI generation
- schema migrations unless absolutely required; expected: no migration
- any Layer A mutation
- any payment/order/reservation mutation

## Implementation expectations

Inspect before editing:

- app/services/admin_automation_cockpit_service.py
- app/schemas/admin_automation_cockpit.py
- app/bot/automation_cockpit_telegram.py
- app/bot/messages.py
- tests/unit/test_admin_automation_cockpit.py
- tests/unit/test_automation_cockpit_telegram.py
- existing supplier clarification / intake validation files for pattern reuse:
  - app/schemas/supplier_offer_intake_validation.py
  - app/services/supplier_offer_intake_validation_service.py
  - app/schemas/supplier_clarification_draft.py
  - app/services/supplier_clarification_draft_service.py

Add files only if justified:
- app/schemas/supplier_offer_catalog_conversion_readiness.py
- app/services/supplier_offer_catalog_conversion_readiness_service.py
- tests/unit/test_supplier_offer_catalog_conversion_readiness_service.py
- docs/CURSOR_PROMPT_A6A_CATALOG_CONVERSION_READINESS_SNAPSHOT.md
- docs/HANDOFF_A6A_CATALOG_CONVERSION_READINESS_SNAPSHOT.md

## Projection content

Design stable fields, for example:

- readiness_status:
  - ready_for_review
  - needs_internal_preparation
  - blocked
  - not_applicable

- status_label_key or simple prelocalized render support
- main_blocker
- warnings
- next_internal_step
- has_tour_link
- has_execution_link
- mini_app_cta_safe
- catalog_visible
- projection_note
- version = "a6a_v1"

Avoid leaking raw internal keys into Telegram:
- no snake_case debug blobs
- no raw `prepare_chain:*`
- no raw `cta_safety:*`
- no raw JSON path dumps
- no long English technical strings in Romanian UI

If raw data cannot be safely humanized, use:
- RO: “Necesită verificare internă.”
- EN: “Requires internal verification.”

## Telegram copy rules

Romanian text must be short and simple.

Good:
- “Lipsește legătura ofertă–tur.”
- “Turul există, dar linkul de rezervare trebuie verificat.”
- “Nu publica încă.”
- “Verifică turul în Mini App.”

Bad:
- “prepare_chain:blocked:create_tour_bridge”
- “cta_safety:missing_execution_link”
- “publish_readiness:blocked”
- long backend diagnostics

## Tests

Run at minimum:

```powershell
python -m compileall app tests
python -m pytest tests/unit/test_admin_automation_cockpit.py -q
python -m pytest tests/unit/test_automation_cockpit_telegram.py -q
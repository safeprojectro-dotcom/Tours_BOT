You are continuing Tours_BOT after B10.2.

Goal:
B10.3 — Full Bus Catalog Conversion Semantics.

Current state:
- Supplier Offer #8 was bridged to Tour #4.
- Tour #4 is open_for_sale and visible in Mini App catalog.
- sales_mode = full_bus.
- Mini App catalog policy returns:
  - operator_path_required = true
  - mini_app_catalog_reservation_allowed = true
  - catalog_charter_fixed_seats_count = 56
  - catalog_actionability_state = bookable
- This is acceptable for a fixed full-bus offer, but UI/copy must not look like per-seat booking.

Business decision:
Do NOT block ready-made full_bus offers by default.
A fixed full_bus supplier offer may be bookable in Mini App as a whole-bus reservation if:
- route/date/price/capacity are fixed
- admin approved packaging
- bridge created Tour
- admin activated Tour for catalog

Important distinction:
1. per_seat = customer books individual seats
2. full_bus fixed offer = customer books the whole bus/package
3. custom_request = customer asks for another route/date/capacity/vehicle

Goal:
Make catalog/detail/preparation semantics explicit so full_bus does not look like “choose 5 seats”.

Rules:
- per_seat:
  - CTA: Reserve seats / Rezerva locuri
  - customer chooses seats_count
  - price displayed per person
- full_bus:
  - CTA: Reserve the bus / Rezerva autobuzul
  - seats_count must be fixed to seats_total / catalog_charter_fixed_seats_count
  - do not present “choose number of seats” as free input
  - display capacity as capacity, not live free seats
  - price displayed as total bus/package price
  - include copy: for individual seats, another route, or another bus size, use custom request
- custom_request:
  - CTA: Request custom offer / Cere oferta personalizata
  - separate flow, not this endpoint

Scope:
- adjust policy/read DTO/copy/UI semantics only where needed
- keep Layer A reservation behavior unchanged unless existing full_bus fixed seats_count already expects catalog_charter_fixed_seats_count
- add tests for catalog/detail/preparation semantics
- no Telegram publish
- no supplier lifecycle change
- no payment/order logic rewrite
- no media/download work
- no recurring offers

Check existing relevant services:
- TourSalesModePolicyService
- MiniAppCatalogService
- MiniAppTourDetailService
- MiniAppReservationPreparationService
- Mini App Flet labels/UI strings if present

Implementation expectations:
1. Catalog response for full_bus should expose clear labels:
   - actionability: bookable_as_full_bus or equivalent if enum/string supports it
   - reservation CTA text / semantic key
   - capacity label
   - price label
2. Detail/preparation should not ask customer to choose arbitrary seats for full_bus.
3. For full_bus preparation:
   - seats_count defaults/fixes to seats_total or catalog_charter_fixed_seats_count
   - UI copy says whole bus reservation
4. Per-seat behavior must remain unchanged.
5. Existing smoke full_bus view_only tour with seats_available=0 should remain view_only.

Tests:
- fixed full_bus with seats_available == seats_total is bookable as whole bus
- full_bus policy exposes fixed seats count
- full_bus copy/semantic payload does not say per-seat free seat selection
- per_seat still allows normal seats_count selection
- full_bus with unavailable state remains view_only
- no order/payment/publish/supplier lifecycle side effects

Before coding:
1. summarize current B10.2 smoke result
2. explain fixed full_bus vs custom_request distinction
3. list files expected to change
4. state non-goals

After coding:
1. files changed
2. exact policy/copy semantics
3. tests run
4. confirm per_seat unchanged
5. confirm no Telegram/payment/order/supplier lifecycle/media changes
6. next safe step: B10.4 smoke full_bus Mini App UX or B8 recurring offers
You are continuing Tours_BOT after B7.2.

Goal:
B9 — Supplier Offer → Tour Bridge Design.

Current state:
- B1–B4.3: supplier offer intake, packaging, marketing, truth rules.
- B5: admin packaging review; approved_for_publish does not publish.
- B6: branded Telegram preview JSON.
- B7.1: media review metadata.
- B7.2: card render preview plan.
- Supplier offer still does NOT become a Tour in Mini App catalog.

Business problem:
An approved/published supplier offer must become or attach to a Tour in the Mini App catalog through an explicit bridge.
No silent ORM trigger.
No AI-created Tour.
No supplier bypass.
Admin-controlled only.

Create design doc:
docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md

Design must cover:

1. Core principle:
Supplier Offer = source/raw/commercial proposal.
Tour = customer-facing sellable catalog object.
Bridge = explicit admin action that creates/links Tour from approved offer.

2. Preconditions:
- supplier offer must have packaging_status = approved_for_publish
- lifecycle_status must be approved or ready_for_moderation depending on existing moderation policy; define exact safe policy
- required fields present: title, route/description, departure/return or recurrence policy, price, currency, sales_mode, capacity/vehicle, program, included/excluded
- warnings must be accepted or resolved
- media can be optional but flagged

3. Bridge output:
Option A: create new Tour
Option B: link to existing Tour
Recommended MVP: create new Tour once, store supplier_offer_id linkage later if field/table exists or propose additive bridge table.

4. Data mapping:
supplier_offers.title → tours.title_default
supplier_offers.description/marketing_summary → tour descriptions
program_text/included_text/excluded_text → tour_translations or tour fields depending current schema
departure/return → Tour datetimes
base_price/currency → Tour base_price/currency
seats_total → Tour seats_total/seats_available policy
sales_mode → Tour.sales_mode
cover/media → Tour cover/media later, not blocking if media not public-ready

5. Full bus vs per seat:
- per_seat: seats_total and seats_available map normally
- full_bus: define current safe behavior:
  - if Layer A supports full_bus assisted mode, create Tour with sales_mode full_bus and non-self-serve / assisted policy
  - do not allow accidental per-seat booking for full_bus
  - no direct whole-bus self-service unless already supported by policy

6. Status mapping:
- new Tour should not automatically be open_for_sale unless policy says so
- recommended:
  created Tour starts draft or open_for_sale only after admin bridge confirmation
- define exact safest MVP recommendation

7. Idempotency:
- bridge must be idempotent
- one active Tour link per supplier offer unless explicitly replacing
- repeated bridge call should return existing bridge/Tour, not create duplicates

8. Audit:
record:
- supplier_offer_id
- tour_id
- bridge_status
- created_by / approved_by
- created_at
- source packaging snapshot/version
- reason/notes

9. Non-goals:
- no Telegram publish
- no payment changes
- no booking changes
- no Mini App UI redesign
- no recurring generation yet
- no media download/storage
- no AI mutation of source truth

10. Next implementation:
B10 — explicit admin bridge implementation:
- migration for bridge table or supplier_offer.tour_id field
- admin POST create/link Tour
- read bridge status
- tests
- smoke: offer #8 approved_for_publish → Tour created/linked → appears in Mini App catalog only if status policy allows

Update:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Before writing:
- summarize B7.2 state
- explain why B9 is design-only

After writing:
- files changed
- bridge policy decisions captured
- next safe step B10
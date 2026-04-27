You are continuing Tours_BOT after B4.1.

Goal:
B4.2 — Marketing Post Template Rules.

Problem:
B4.1 removed technical formatting noise, but the generated Telegram draft is still too dry and unclear:
- Price line does not explain full_bus vs per_seat well enough
- Route sometimes uses boarding place instead of actual offer route
- Full-bus post does not clearly explain “whole bus only”
- Per-seat post must not claim live availability unless confirmed
- Discount fields exist but are not formatted as a sales block
- Vehicle/capacity need cleaner presentation

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md
- docs/AI_ASSISTANT_SPEC.md

Scope:
Improve deterministic Telegram packaging template rules only.

Implement rules:

1. Three marketing models:
- per_seat
- full_bus
- custom_request CTA text block if needed as fallback/secondary CTA

2. Price display:
if sales_mode == "full_bus":
    "💰 {price} {currency} — tot autobuzul"
elif sales_mode == "per_seat":
    "👤 {price} {currency} / persoană"

3. Vehicle/capacity display:
- Prefer vehicle_label if present
- full_bus:
  "🚍 {vehicle_label}" or "🚍 Microbuz / autocar"
  If capacity known and not already included in vehicle_label, add "(N locuri)"
- per_seat:
  "🚍 {vehicle_label}" or "🚍 Transport confort"
  Do NOT show fake live seats unless live availability is confirmed
  Use:
  "📩 Locurile se confirmă la rezervare"
  unless a real confirmed availability source exists

4. Discount display:
- If discount_percent > 0:
  "🔥 -{percent}% până la {valid_until}"
- If discount_amount > 0:
  "🔥 -{amount} {currency} reducere"
- If discount_code exists:
  "🏷 Cod: {code}"
- Show discount block immediately after price
- Do not show discount if amount/percent are zero or missing

5. Route display:
- Use supplier offer route facts / description, not boarding_places_text
- boarding_places_text must not replace route
- If route text is comma-separated short locations, convert to:
  A → B → C
- Keep boarding place for future detailed views, not Telegram route line

6. Full bus disclaimer:
For full_bus posts add a short line:
"🔒 Rezervare exclusivă pentru grup (autobuz complet)"
And a custom alternative:
"🧭 Ai nevoie de alt traseu sau alt număr de locuri? Cere ofertă personalizată în platformă."

7. CTA by model:
- full_bus:
  "👉 Rezervă pentru grupul tău"
- per_seat:
  "👉 Rezervă locul tău"
- custom:
  "👉 Cere ofertă personalizată"

8. Style:
- Keep the post structured and scannable
- Keep program block but label it as:
  "✨ Ce faci:" or "✨ Ce vezi:"
- Do not invent data
- Do not claim availability
- Do not publish
- Do not create Tour
- Do not call AI
- Do not touch Mini App / booking / payment

Tests:
- full_bus price line says tot autobuzul
- per_seat price line says / persoană
- full_bus includes exclusivity disclaimer
- per_seat does not show fake “X locuri disponibile”
- discount code/percent/amount format correctly
- route uses description, not boarding_places_text
- no raw enums or ISO timestamps in Telegram draft
- existing B4/B4.1 tests still pass

Before coding:
1. summarize current B4.1 output issue
2. list files expected to change
3. explain why this is marketing formatting only and safe

After coding:
1. files changed
2. template rules implemented
3. before/after example
4. tests run
5. confirm no AI/publish/Tour/Mini App/booking/payment changes
6. next safe step: B4.3 Pricing / Discount / Availability Truth Rules or B5 Admin Moderation & Review
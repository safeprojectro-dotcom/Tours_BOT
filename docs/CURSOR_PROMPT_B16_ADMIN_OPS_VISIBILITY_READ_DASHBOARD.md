# CURSOR_PROMPT_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD

## Context

Project: Tours_BOT.

We are continuing after B15 publishing-console foundation closure.

Recent clean checkpoint:
- `1083fa9 docs: close B15 publishing console foundation`
- `2808d2b feat: add publishing console template source channel read model`
- `1aeeb10 feat: add publishing console action affordances`
- `fab43a6 feat: enrich admin publishing console read view`
- `d4489e1 docs: close B15C exact CTA chain checkpoint`

B15B–B15F closed safe publishing console foundation:
- `GET /admin/publishing-console`
- read-only publishing candidates
- readiness/blockers
- exact CTA safety
- action affordances metadata
- source/template/channel/media metadata
- future disabled hints
- no action execution
- no scheduler
- no auto-publish
- no template editor
- no channel selector

B15C accepted conversion chain:

Supplier offer approved/packaged
→ Tour bridge created/linked
→ Tour activated for Mini App catalog
→ Active execution link created
→ Showcase/channel publish
→ Channel `Rezervă` opens exact Mini App tour
→ Layer A handles reservation/payment.

Production smoke evidence:
- Offer #15
- Tour #9
- Tour code `B10-SO15-460344`
- Execution link #8
- Publish attempt #6
- Showcase message #28
- Temp hold/order #55
- Mini App opened exact tour without identity warning
- reservation/payment-entry screen reached

## Goal

Start B16 as a read-only Admin / OPS visibility dashboard.

The goal is to help an operator understand what is happening after publication:

1. What tours are currently active / upcoming.
2. What orders or temporary holds exist.
3. Which reservations are pending payment, paid, expired, or problematic.
4. Which supplier-offer publication/conversion records are connected to orders.
5. Which items need operator attention.
6. What the operator should inspect next.

This must be read-only.

## Important boundary

B16 Step 1 must NOT mutate anything.

Do NOT:
- change order statuses;
- complete payment;
- expire reservations;
- refund;
- cancel;
- send Telegram messages;
- publish;
- retry;
- create supplier execution attempts;
- create execution links;
- touch Layer A reservation/payment logic;
- change Mini App routing.

## Existing useful surfaces

Before implementing, inspect current code for existing admin/order/tour/read models.

Likely relevant areas:
- admin routes/services/schemas for tours/orders/overview
- Layer A order/reservation/payment services
- Mini App booking facade/read services
- supplier offer bridge/execution link/publication audit services
- publishing console read model
- existing tests around admin overview/orders/tours

Reuse existing read models and services where possible.

Do not duplicate business rules.

## Required behavior

Create a new read-only admin endpoint, suggested:

`GET /admin/ops-dashboard`

If an existing route name is more consistent, use it, but document it clearly.

The response should include sections such as:

```json
{
  "summary": {
    "upcoming_tours_count": 0,
    "open_for_sale_tours_count": 0,
    "active_holds_count": 0,
    "pending_payment_orders_count": 0,
    "confirmed_orders_count": 0,
    "expired_or_closed_orders_count": 0,
    "attention_items_count": 0
  },
  "attention_items": [
    {
      "kind": "payment_pending",
      "severity": "info",
      "title": "Order #55 pending payment",
      "summary": "Temporary hold is active; payment is not confirmed yet.",
      "admin_path": "/admin/orders/55",
      "related_tour_id": 9,
      "related_supplier_offer_id": 15
    }
  ],
  "recent_orders": [],
  "upcoming_tours": [],
  "recent_publications": [],
  "conversion_links": [],
  "audit_hint": "Read-only OPS dashboard; no mutation or Telegram send is performed."
}
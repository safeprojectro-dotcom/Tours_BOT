# CURSOR_PROMPT_S1D2_ADMIN_GATED_OPERATIONAL_SALES_PUSH_CHANNEL_PUBLISH

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a redesign.

## Cursor mode

Agent

## Block name

S1D-2 — Admin-Gated Operational Sales Push Channel Publish

## Execution mode

Narrow-step mode.

Reason:
- This block sends a real Telegram channel post.
- Telegram channel publish is a public external side effect.
- Operational urgency/scarcity copy must be system-confirmed.
- This block must be admin-gated and explicit.
- No scheduler/worker automation in this block.

---

## Context

S1A completed:
- read-only supplier/tour/departure passenger counts.

S1B completed:
- supplier Telegram contact resolver.

S1C completed:
- supplier notification outbox foundation;
- manual supplier Telegram delivery from outbox;
- outbox enqueue after channel publish;
- outbox enqueue after customer reservation/order.

S1D-1 completed:
- operational sales push eligibility and preview;
- endpoint:
  - `GET /admin/tours/{tour_id}/operational-sales-push-preview`
- supports push types:
  - `predeparture`
  - `low_availability`
  - `combined`
  - `not_eligible`
- default predeparture window:
  - `PREDEPARTURE_SALES_PUSH_DAYS_BEFORE = 2`
- default low availability threshold:
  - `LOW_AVAILABILITY_SEATS_THRESHOLD = 2`
- no Telegram publish in S1D-1.

S1D-2 must publish the already-previewed operational sales push to Telegram channel only after explicit admin action.

---

## Goal

Implement admin-gated operational sales push channel publish.

Flow:

```text
admin requests operational sales push preview
→ system confirms eligible=true
→ admin explicitly calls publish action
→ system re-runs eligibility/preview
→ if still eligible, sends preview text to Telegram channel
→ records/logs publish result if existing patterns support it
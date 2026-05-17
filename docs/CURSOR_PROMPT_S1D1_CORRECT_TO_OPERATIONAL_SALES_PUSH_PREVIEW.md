# CURSOR_PROMPT_S1D1_CORRECT_TO_OPERATIONAL_SALES_PUSH_PREVIEW

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a redesign.

## Cursor mode

Debug / Agent

## Block

S1D-1 — Operational Sales Push Eligibility & Preview

## Why correction is needed

The current S1D-1 implementation was shaped as “last seats” eligibility.

Reported current behavior:
- service: `AdminLastSeatsOperationalPreviewService`
- endpoint: `GET /admin/tours/{tour_id}/last-seats-operational-preview`
- config: `LAST_SEATS_OPERATIONAL_MAX_SEATS`, default 5
- eligibility: `1 <= seats_available <= max`
- preview focused on last seats.

This is too narrow and partially wrong for the business goal.

The business goal is not only “2 seats left”.

The channel needs two different operational sales push triggers:

1. **Predeparture urgency**
   - departure is close, for example in 2 days;
   - seats are still available;
   - channel post creates desire to buy before departure.

2. **Low availability urgency**
   - few seats remain, for example 2;
   - this can happen earlier or later than 2 days before departure.

If both are true, the preview should become a combined urgency post.

---

## Correct model

Refactor S1D-1 into:

# S1D-1 — Operational Sales Push Eligibility & Preview

Do not treat “2” as only seats.
There are two configurable thresholds:

```text
PREDEPARTURE_SALES_PUSH_DAYS_BEFORE = 2
LOW_AVAILABILITY_SEATS_THRESHOLD = 2
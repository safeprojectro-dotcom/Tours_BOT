# HANDOFF_S1D1_OPERATIONAL_SALES_PUSH_ELIGIBILITY_AND_PREVIEW

## Project

Tours_BOT

## Block

S1D-1 — Operational Sales Push Eligibility & Preview

## Purpose

Create read-only admin preview for operational channel sales pushes.

The block supports two independent marketing triggers:

1. **Predeparture urgency** — departure is within **`PREDEPARTURE_SALES_PUSH_DAYS_BEFORE`** (default **2** calendar-day window), with seats still available.
2. **Low availability urgency** — **`seats_available`** is between **1** and **`LOW_AVAILABILITY_SEATS_THRESHOLD`** inclusive (default **2**).

If both are true, the preview becomes **combined** urgency text.

When neither applies after safety gates pass, the API reports **`not_eligible`** via **`eligibility_block_codes`** **`[`** **`s1d1_no_operational_sales_push_trigger`** **`]`**.

## Mode

Narrow-step mode.

Reason:

- urgency/scarcity claims are public-risk;
- public channel publish must be gated later (**`S1D-2`**);
- this block only previews.

## Implementation (shipped)

| Piece | Location |
|-------|-----------|
| Service | **`AdminOperationalSalesPushPreviewService`** — **`app/services/admin_operational_sales_push_preview_service.py`** |
| Schema | **`AdminOperationalSalesPushPreviewRead`** — **`app/schemas/admin_operational_sales_push_preview.py`** |
| Endpoint | **`GET /admin/tours/{tour_id}/operational-sales-push-preview`** |
| Inventory truth | Reuses **S1A** **`AdminDeparturePassengerCountsService.read_for_tour`** |
| Config | **`PREDEPARTURE_SALES_PUSH_DAYS_BEFORE`** (default **2**, clamp **1–30**) **`;`** **`LOW_AVAILABILITY_SEATS_THRESHOLD`** (default **2**, clamp **1–500**) — **`app/core/config.py`** |
| Tests | **`tests/unit/test_admin_operational_sales_push_preview.py`** |

## Safety gates (must hold)

- Tour **`OPEN_FOR_SALE`** **`;`** departure strictly in the future **`;`** **`sales_deadline`** not passed **`;`** **`seats_available`** **`>`** **0** **`;`** no **`s1a_inventory_vs_active_order_seats_mismatch`** on S1A read.

## Included

- Dual-trigger eligibility **`/`** **`predeparture_urgency_triggered`** **`/`** **`low_availability_urgency_triggered`** on read model **`;`** combined preview plain text **`;`** Layer A **`/`** S1A-backed **`seats_available`** **`;`** admin read-only HTTPS **`GET`** **`;`** focused tests **`;`** docs checkpoint.

## Excluded

- no Telegram channel publish **`;`** no supplier notification **`;`** no scheduler **`/`** worker **`;`** no customer personal data **`/`** passenger manifest **`;`** no Layer A mutation **`;`** no payment **`/`** reconciliation changes **`;`** no seat inventory mutation **`;`** no B11 routing changes **`;`** no QR **`;`** no marketing broadcast **`;`** no fake urgency.

## Expected future block

**`S1D-2`** — Admin-Gated Operational Sales Push Channel Publish

## Verification expected

Run:

```bash
python -m pytest tests/unit/test_admin_operational_sales_push_preview.py -q
python -m pytest tests -k "operational_sales_push or predeparture_sales_push or last_seats or departure_passenger_counts or supplier" -q
python -m compileall app tests
```

## Obsolete doc removed

**`docs/HANDOFF_S1D1_LAST_SEATS_ELIGIBILITY_AND_PREVIEW.md`** — superseded by this handoff (**operational sales push**, not last-seats-only).

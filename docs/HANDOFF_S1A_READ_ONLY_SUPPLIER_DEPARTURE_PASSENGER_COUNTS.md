# HANDOFF_S1A_READ_ONLY_SUPPLIER_DEPARTURE_PASSENGER_COUNTS

## Project

Tours_BOT

## Block

S1A — Read-Only Passenger Counts per Supplier / Tour / Departure

## Purpose

Implement the first safe S1 supplier operations step: aggregated read-only passenger counts for supplier-linked departures.

## Mode

Functional-block mode.

Reason:
- read-only service/read model/admin visibility;
- no supplier send;
- no passenger manifest;
- no public publish;
- no scheduler;
- no Layer A mutation.

## Included

- Inspect supplier → supplier_offer → execution_link/bridge → tour → order relationships.
- Create read-only count service.
- Add read-only schemas/DTOs if needed.
- Add protected admin read endpoint only if existing route patterns make it safe.
- Optionally add read-only admin Telegram summary if trivial and safe.
- Add focused tests.
- Update `CHAT_HANDOFF.md` and `OPEN_QUESTIONS_AND_TECH_DEBT.md`.

## Excluded

- no supplier notifications
- no Telegram channel publish
- no scheduler/workers
- no passenger manifest
- no personal customer data
- no payment/reconciliation changes
- no order/reservation/payment mutation
- no seat inventory mutation
- no B11 routing change
- no marketing broadcast
- no QR
- no AI agent execution

## Count semantics

Separate:

- order counts
- passenger/seat counts
- paid/confirmed
- reserved unpaid
- cancelled/no-payment
- capacity / seats_available / remaining capacity when safe

## Safety

The service must read from Layer A truth only.

Do not infer paid/confirmed state outside existing order/payment lifecycle.

If semantics are ambiguous, return warnings instead of guessing.

## Expected files

Likely:

- `app/services/supplier_departure_counts.py`
- `app/schemas/supplier_departure_counts.py`
- existing admin route file if endpoint added
- focused tests
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

## Verification expected

Run:

```bash
python -m compileall app tests
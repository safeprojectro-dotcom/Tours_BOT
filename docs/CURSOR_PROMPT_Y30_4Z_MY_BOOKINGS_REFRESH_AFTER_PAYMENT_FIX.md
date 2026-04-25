Continue Tours_BOT strict continuation.

Identity bridge is fixed.
Custom requests are fixed.
Now investigate My bookings after successful reservation/payment.

Evidence from production logs:
- POST /mini-app/tours/SMOKE_PER_SEAT_001/reservations -> 200
- GET /mini-app/orders/46/reservation-overview -> 200
- POST /mini-app/orders/46/payment-entry -> 200
- POST /mini-app/orders/46/mock-payment-complete -> 200
- subsequent GET /mini-app/bookings?telegram_user_id=... -> 200

Issue:
After booking/payment test for one seat, booking information did not appear in My bookings UI.

Task:
Investigate and fix only My bookings refresh/rendering after reservation/payment completion.

Rules:
- Do NOT touch identity bridge.
- Do NOT touch Supplier/RFQ semantics.
- Do NOT redesign Layer A booking/payment.
- Do NOT change backend contracts unless evidence proves mismatch.
- Keep existing order/payment semantics.

Investigate:
1. Mini App payment success / mock payment complete flow.
2. Whether My bookings screen reloads after payment completion.
3. API client parsing for /mini-app/bookings.
4. Whether confirmed/paid/reserved orders are filtered out by UI.
5. Whether backend /mini-app/bookings response includes order 46.
6. Whether language/status/lifecycle mapping hides the item.

Implementation goal:
After successful payment completion:
- user sees clear success state
- My bookings refreshes/reloads
- created/paid order appears in My bookings if backend returns it
- empty state appears only when truly empty

Add focused tests if existing patterns allow.

Checks:
- python -m compileall app mini_app
- focused unit tests

Report:
- root cause
- files changed
- migrations none
- tests run
- compatibility notes
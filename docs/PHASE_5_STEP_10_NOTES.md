# Phase 5 / Step 10 — mock payment outcome & confirmed booking

## What was added

- **Config:** `ENABLE_MOCK_PAYMENT_COMPLETION` (default `false`). When `true`, the API exposes `POST /mini-app/orders/{order_id}/mock-payment-complete` with body `{ "telegram_user_id": <int> }`.
- **Behavior:** The handler builds a verified `PaymentProviderResult` for the latest **mockpay** payment on that order and runs the existing **`PaymentReconciliationService`** — same path as the payment webhook. No new PSP, no schema change.
- **Order cleanup:** On successful reconciliation to **paid**, `reservation_expires_at` is cleared on the order so confirmed bookings do not carry a stale hold deadline.
- **Mini App:** **Pay now** (when there is no external `payment_url`) calls the mock-complete endpoint. On **403** (feature off), the user sees a short message about enabling the flag or using the webhook. On **200**, the payment screen shows a **confirmed** outcome and **Back to bookings**.
- **Settings API:** `GET /mini-app/settings` includes `mock_payment_completion_enabled` so clients can reflect capability (optional).

## Staging / local

Set on the **API** service (not only the Mini App UI):

```text
ENABLE_MOCK_PAYMENT_COMPLETION=true
```

Restart the API after changing env (settings are cached).

## Out of scope (this step)

- Real payment provider integration.
- Failure/cancel mock paths (success-only slice).
- Changing webhook HMAC behavior or Railway service split.

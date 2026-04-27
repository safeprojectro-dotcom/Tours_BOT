B10 — Supplier Offer → Tour Bridge Implementation is completed.

Current state:
- Admin can explicitly create/link a Tour from an approved Supplier Offer.
- Bridge is persisted.
- Bridge is idempotent.
- Repeated POST returns existing bridge instead of creating duplicate Tour.
- New Tour starts in safe status, preferably draft.
- Supplier Offer does not silently become Tour.
- No Telegram publish happens in B10.
- No Order/Payment/Reservation is created.

Still unchanged:
- no channel publish
- no Telegram send
- no AI call
- no media download/storage
- no recurring generation
- no Mini App UI redesign
- catalog visibility remains controlled by existing Tour.status policy

Next safe step:
B10.1 — production smoke + docs sync
or B8 — recurring supplier offers
or B7.3 — publish-safe media preparation.
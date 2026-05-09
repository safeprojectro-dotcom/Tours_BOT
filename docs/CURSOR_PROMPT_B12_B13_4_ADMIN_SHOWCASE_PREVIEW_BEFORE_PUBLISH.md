# CURSOR_PROMPT_B12_B13_4_ADMIN_SHOWCASE_PREVIEW_BEFORE_PUBLISH

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a focused B12/B13.4 implementation step.

Do not change booking/payment/order/reservation logic.
Do not change Mini App UI.
Do not change B11 routing.
Do not change B10.6 bot behavior.
Do not change media/photo publishing.
Do not add sendPhoto/sendMediaGroup.
Do not add object storage/download/rendering.
Do not change SupplierOffer lifecycle transitions except read-only preview support.

---

## Current checkpoint

B12/B13.2 and B12/B13.3 are completed.

Current Telegram showcase behavior:

- branded Romanian text-first channel post;
- FULL_BUS price shown as `{price} {currency} / grup`;
- FULL_BUS individual seats not sold separately;
- Program section supported from `program_text`;
- CTA: `ℹ️ Detalii | ✅ Rezervă`;
- Detalii -> bot deep link `supoffer_<id>`;
- Rezervă -> Mini App supplier-offer landing;
- no direct `/tours/{code}`;
- no photo/sendPhoto;
- Telegram link preview disabled.

Manual check showed that if admin/test input contains low-quality text, that exact text appears in the channel post. That is expected behavior and should not be fixed with automatic translation.

Correct architectural solution: admin preview before publish.

---

## Goal

Add a read-only admin preview endpoint/service for the final Telegram showcase post before actual publish.

Admin should be able to see exactly what would be sent to the channel, including:

- final HTML/text caption;
- whether it is text-only or photo;
- whether link preview is disabled;
- primary/secondary CTA links if available;
- warning/metadata that this is preview only.

This step must not send anything to Telegram.

---

## Source files to inspect

Inspect before editing:

- app/api/routes/admin.py
- app/services/supplier_offer_showcase_message.py
- app/services/telegram_showcase_client.py
- app/services/supplier_offer_moderation_service.py
- app/schemas or DTOs used by admin API
- tests/unit/test_supplier_offer_showcase_ro.py
- tests/unit/test_supplier_offer_track3_moderation.py
- existing admin API tests if any
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

If a dedicated admin schema module exists, use it. If not, follow existing project style.

---

## Desired endpoint

Add a read-only endpoint, for example:

```http
GET /admin/supplier-offers/{offer_id}/showcase-preview
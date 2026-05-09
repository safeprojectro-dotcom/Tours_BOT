# CURSOR_PROMPT_B12_B13_SHOWCASE_TEMPLATE_CHANNEL_ADAPTER_IMPLEMENTATION

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is the first small B12/B13 implementation slice.

---

## Current checkpoint

B12/B13 design contract accepted.

Accepted design:

- Telegram Channel = marketing showcase.
- Telegram Bot = router / consultant / entry point.
- Mini App = execution truth and conversion.
- Supplier Offer = source facts.
- Tour = customer-facing sellable object.
- Admin = final decision maker.
- AI may draft, but does not publish.
- approved_for_publish does not equal channel-published.
- publish_safe media does not equal published media.
- visibility != bookability.

Current publication behavior found:

- POST /admin/supplier-offers/{offer_id}/publish calls SupplierOfferModerationService.publish.
- build_showcase_publication(offer, settings) builds Romanian HTML from SupplierOffer ORM fields.
- send_showcase_publication uses sendPhoto if offer.showcase_photo_url exists, otherwise sendMessage.
- current channel caption includes:
  - Detalii: bot deep link supoffer_<id>
  - Rezervă: Mini App supplier-offer landing
- current build path does not consult B7.3B publish_safe metadata.
- current build path does not consult active execution link / Tour for actionability.
- publish success stores published_at, showcase_chat_id, showcase_message_id.
- retract deletes the stored channel message and returns lifecycle to approved.

Accepted B12/B13 target:

- First implementation slice should be deterministic, text-first, and safe.
- Do not implement AI final publish.
- Do not implement direct /tours/{code} channel links.
- Use stable supoffer_<id> bot deep link as canonical public CTA.
- Let B11 route the user to exact Tour when active execution link exists.
- Channel text must not claim booking if execution truth is unknown.
- No media expansion in this slice.
- Do not implement B7.4/B7.5/B7.6.

---

## Business goal

Refactor Telegram showcase publication toward a clean template/channel adapter contract without changing broad publication behavior unexpectedly.

The first slice should:

1. Make deterministic text-only showcase structure explicit.
2. Make CTA strategy safer:
   - primary CTA = stable bot deep link supoffer_<id>;
   - optional Mini App link, if kept, must use non-booking wording like “Vezi în aplicație / Detalii ofertă”, not hard “Rezervă” unless actionability is known.
3. Preserve admin-triggered publish flow.
4. Avoid media/photo publish expansion.
5. Prevent copy that contradicts Mini App truth.

---

## Source files to inspect

Inspect before editing:

- app/services/supplier_offer_showcase_message.py
- app/services/telegram_showcase_client.py
- app/services/supplier_offer_moderation_service.py
- app/services/supplier_offer_deep_link.py
- app/models/supplier.py
- app/models/enums.py
- app/api/routes/admin.py
- tests/unit/test_supplier_offer_showcase_ro.py
- tests/unit/test_supplier_offer_track3_moderation.py
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md

If some files differ, locate equivalents.

---

## Implementation scope

### 1. Template / adapter structure

Refactor supplier offer showcase building so responsibilities are clearer.

Acceptable lightweight implementation:

- keep existing `build_showcase_publication(...)` public API if tests depend on it;
- internally split:
  - template/content section builder;
  - Telegram HTML adapter / formatting;
  - CTA builder.

Do not overbuild a large framework.

Recommended minimal shapes:

- dataclass for semantic content sections, or small internal helper functions.
- Keep output compatible with existing `ShowcasePublication(caption_html, photo_url)` unless there is a strong reason not to.

---

### 2. CTA strategy

Primary CTA should remain stable bot deep link:

```text
https://t.me/<bot>?start=supoffer_<id>
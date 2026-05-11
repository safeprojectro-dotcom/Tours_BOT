# CURSOR_PROMPT_B15C4_COVER_REPLACEMENT_WORKFLOW_SUPPLIER_AND_ADMIN

Implement a safe cover replacement workflow for supplier-offer showcase publishing.

## Context

B15C and B15C1 are complete.

Relevant commits:

- `37f213e feat: require exact tour CTA before supplier offer publish`
- `18278cf docs: record B15C production smoke result`
- `17ddd4c fix: open channel tour CTA through Telegram Mini App`

B15C1 production smoke discovered a new media workflow issue on Supplier Offer #14.

Offer #14 state before failed publish:

- Supplier Offer: `#14`
- Tour: `#8`
- Tour code: `B10-SO14-31f95e`
- Sales mode: `full_bus`
- Execution link: `#7`
- `cta_rezerva_href = https://t.me/tours_tm_bot?startapp=tour_B10-SO14-31f95e`
- `showcase_preview.can_publish_now = True`
- `publish_showcase_channel = True`

But publish failed:

`telegram_send_failed: Bad Request: wrong type of the web page content`

Root observed media problem:

- `cover_media_reference = https://share.google/aslSRRhI6yMkRSuMV`
- This is a Google/share webpage, not a Telegram photo/file_id and not a direct image URL.
- Telegram cannot send it via sendPhoto.

Operational workflow gap:

- Admin can request cover photo replacement.
- But supplier is not clearly informed/actioned to replace the photo.
- Admin has no clean tool to replace/clear the bad cover.
- Old bad `cover_media_reference` remains active.
- `approve_cover_for_card` can still approve the old bad reference.
- Publish can proceed and fail at Telegram send time.

This is not a B15C/B15C1 CTA bug. The CTA is correct. The issue is B7/B15 publish-safe media workflow.

## Business principle

From BUSINESS plan v2:

- Supplier gives raw facts/media.
- AI/system packages.
- Admin controls showcase.
- Channel sells.
- Mini App converts.
- Layer A executes booking/payment.

Supplier photo is raw media. Admin must approve/reject/fallback. Bad photo must not break channel publication.

## Required docs to read first

Read:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B15C_PRODUCTION_SMOKE_RESULT.md`
- `docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`
- any B7 media/publish-safe docs present in repo
- supplier offer media/review docs if present

Inspect code:

- `app/services/supplier_offer_showcase_message.py`
- `app/services/supplier_offer_moderation_service.py`
- `app/services/supplier_offer_review_package_service.py`
- `app/services/supplier_offer_operator_workflow.py`
- media approval/replacement services, likely:
  - `app/services/supplier_offer_media_review_service.py`
  - or equivalent
- admin routes for:
  - request_cover_photo_replacement
  - approve_cover_for_card
  - publish
- supplier-admin offer intake/update/photo handling paths
- tests around:
  - supplier offer review package
  - moderation workflow
  - showcase publish
  - media review
  - B15C/B15C1 CTA generation

## Goal

Close the cover replacement workflow safely.

Implement the smallest safe code change that prevents this class of production incident:

1. non-sendable cover references must not be approved for card;
2. replacement-requested cover must block publish until resolved;
3. admin must have a clear way to resolve:
   - supplier replacement needed; and/or
   - admin clears cover for text-only publish; and/or
   - admin replaces cover manually if existing route exists;
4. supplier-facing replacement request must be recorded clearly, even if actual supplier notification is not implemented yet;
5. B15C/B15C1 exact CTA must not regress.

## Definitions

### Sendable cover reference for Telegram showcase

Treat as sendable only if one of these is true:

1. `telegram_photo:<file_id>`
2. already-supported Telegram file_id format if code uses another internal representation
3. direct HTTPS image URL only if existing code explicitly supports it safely

Do NOT treat these as sendable:

- `https://share.google/...`
- Google Drive/share links
- generic webpage URLs
- empty/unknown non-image URLs
- malformed references

Do not do network probing in tests unless existing code already does it. Prefer deterministic validation by reference shape/kind.

## Required behavior

### 1. Request replacement must become a blocking workflow state

When admin requests cover photo replacement:

- mark media review as replacement requested;
- include reason if current endpoint/body supports it, or support a minimal optional reason field;
- keep audit metadata if available:
  - requested_at;
  - requested_by;
  - reason;
  - current/old cover reference;
- publish must be blocked;
- approve_cover_for_card for that old reference must be blocked or disabled;
- review-package must show a clear warning/next step:
  - supplier replacement needed;
  - admin replacement/clear needed.

### 2. Approve cover must validate sendability

`approve_cover_for_card` must not approve a non-sendable cover reference.

For `https://share.google/...`, expected result:

- action disabled or endpoint rejects with clear 400/409;
- review-package warning explains:
  - cover reference is not sendable to Telegram;
  - upload a Telegram photo or clear cover / text-only fallback.

### 3. Publish must not reach Telegram with non-sendable cover

Before calling Telegram sendPhoto/sendMessage:

- validate the chosen cover media mode.
- If cover is non-sendable and no safe text-only mode is selected, block before external Telegram call.
- Do not create a Telegram send attempt that tries to send the bad media.
- If current audit model records blocked attempts, use existing pattern; otherwise do not invent broad new persistence.

### 4. Admin clear/text-only fallback

Add the smallest safe admin capability to resolve bad cover without waiting for supplier.

Preferred:

`POST /admin/supplier-offers/{offer_id}/media/clear-cover-for-text-only`

or equivalent existing route if one already exists.

Behavior:

- clear/ignore cover for channel showcase media;
- mark media_review or publish_safe block as text-only approved / no cover selected;
- do not delete supplier raw media history if current model can preserve it;
- allow publish as text-only using sendMessage/caption-only path;
- review-package should show:
  - cover not used;
  - text-only publish allowed;
  - no media warnings.

If adding a route is too large, implement a service method and docs-only route proposal, but prefer route if easy and consistent with existing admin media routes.

### 5. Supplier replacement request visibility

If actual supplier notification/outbound message exists and is safe, wire request_cover_photo_replacement to it.

If not implemented, do NOT invent a send path. Instead:

- record supplier-facing message/copy in review-package and handoff docs;
- expose a clear field/warning such as:
  - `supplier_action_needed: replace_cover_photo`
  - `supplier_replacement_message`
  - `replacement_requested = true`

Recommended Romanian supplier message:

`Fotografia pentru oferta ta nu poate fi folosită pentru publicare. Te rugăm să trimiți o fotografie nouă ca imagine în Telegram, nu ca link. Imaginea trebuie să fie clară și relevantă pentru excursie.`

### 6. Do not break B15C/B15C1 CTA

Existing exact-tour CTA behavior must remain:

- before publish, if exact tour + execution link exist:
  - `Rezervă` uses `https://t.me/{bot}?startapp=tour_{tour_code}` when bot username exists;
  - fallback to HTTPS `/tours/{tour_code}` only if bot username missing.
- Do not change execution-link gating.
- Do not change booking/payment/Layer A.

## Suggested implementation areas

Likely changes:

- media review service:
  - add sendable media validation helper;
  - add replacement_requested blocking state;
  - add clear/text-only fallback state;
- operator workflow:
  - disable/enable `approve_cover_for_card`, `request_cover_photo_replacement`, `publish_showcase_channel` correctly;
  - add clear text-only action if route/action architecture supports it;
- review package:
  - expose media warnings and supplier/admin next steps;
- moderation publish:
  - preflight media sendability before Telegram send;
- showcase message:
  - support text-only mode cleanly if no cover is approved/selected;
- tests:
  - request replacement blocks publish;
  - non-sendable Google share cannot be approved;
  - publish does not call Telegram with non-sendable media;
  - clear/text-only fallback allows publish gate;
  - B15C1 startapp CTA unchanged.

## Tests required

Run focused tests, likely:

```bash
python -m pytest tests/unit/test_supplier_offer_review_package.py tests/unit/test_supplier_offer_track3_moderation.py tests/unit/test_supplier_offer_showcase_ro.py tests/unit/test_supplier_offer_deep_link.py -q
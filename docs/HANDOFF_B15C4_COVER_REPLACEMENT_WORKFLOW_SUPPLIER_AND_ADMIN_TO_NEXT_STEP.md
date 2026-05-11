# Handoff — B15C4 cover replacement / publish-safe media

## Production context (historical)

During **B15C1** smoke, **Supplier Offer #14** had a correct exact-tour **Rezervă**:

`https://t.me/tours_tm_bot?startapp=tour_B10-SO14-31f95e`

**Publish** failed at Telegram with:

`telegram_send_failed: Bad Request: wrong type of the web page content`

**Root cause:** `cover_media_reference` pointed at a **Google share page** (`https://share.google/...`), not `telegram_photo:{file_id}` and not a **sendable** direct image URL for Bot API **`sendPhoto`**.

This was **not** a B15C/B15C1 CTA bug.

## What shipped (in-repo, B15C4)

1. **Sendability rules** — `app/services/supplier_offer_showcase_cover_sendability.py`  
   Host blocklist (incl. `share.google`, Drive/Docs, etc.) + `telegram_photo:{file_id}` or allowed https URLs.

2. **Showcase builder** — `showcase_photo_send_argument_from_offer` uses sendability → bad URLs → **no** `photo_url` → **text-only** channel path (`sendMessage`).

3. **`POST …/media/approve-for-card`** — rejects non-sendable `cover_media_reference` (**400**).

4. **`SupplierOfferModerationService.publish`** — if `publication.photo_url` is set, preflight sendability + consistency with the offer row **before** calling Telegram.

5. **`replacement_requested`** — unchanged semantics: still blocks publish via existing **`cover_media_publish_blocking_reasons`** / operator workflow.

6. **Admin clear hero** — `POST /admin/supplier-offers/{offer_id}/media/clear-cover-for-text-only`  
   Clears row `cover_media_reference`, sets `media_review.status = cover_cleared_for_channel_text_only`, keeps prior URL in review snapshot for audit.

7. **Review-package** — `cover_media_quality_review`: `replacement_requested`, `supplier_action_needed`, `supplier_notice_message_ro` (fixed RO copy for ops/supplier-facing comms).

8. **Operator workflow** — action `clear_cover_for_text_only_channel` (HTTP hint); **B15C/B15C1** CTA / execution-link gating **unchanged**.

### Tests (examples)

- `tests/unit/test_supplier_offer_showcase_cover_sendability.py`
- `tests/unit/test_supplier_offer_b7_1_media_review.py` (approve reject + clear)
- `tests/unit/test_supplier_offer_cover_media_quality_review.py`
- `tests/unit/test_supplier_offer_track3_moderation.py` (publish text-only when share link cover)

## Safety (still valid for ops)

- Do **not** retry failed production publish blindly; fix cover / clear / approve, then publish again when ready.
- Do **not** edit existing Telegram channel posts from this handoff.
- Do **not** weaken identity or Layer A; **no** scraping Google share pages for images.

## Follow-ups (not in B15C4)

- **Supplier notification:** no automated Telegram message to supplier yet — use **`supplier_notice_message_ro`** on **`GET …/review-package`** until a safe outbound path exists.
- **Telegram admin UX:** optional button for **`clear_cover_for_text_only_channel`** (parity with HTTP operator workflow).
- **stricter https policy:** current ship uses host blocklist + “looks like URL”; optional future: path/extension heuristics if ops need fewer false positives.

## Related

- Implementation pointer: **`docs/CHAT_HANDOFF.md`** (B15C4 bullet).
- Prompt: **`docs/CURSOR_PROMPT_B15C4_COVER_REPLACEMENT_WORKFLOW_SUPPLIER_AND_ADMIN.md`**.

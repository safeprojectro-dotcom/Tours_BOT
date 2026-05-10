
---

## HANDOFF name

`HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP

## Status

**B13D-alt implemented.** Read-only **`ShowcaseChannelPublishRequest`**-shaped payload for the **Telegram** showcase channel: **`build_showcase_publication`** → **`telegram_showcase_channel_publish_request_preview`** → Pydantic **`AdminSupplierOfferShowcaseChannelPayloadRead`**. **Dedicated** **`GET /admin/supplier-offers/{offer_id}/showcase-channel-payload`** (not folded into **`review-package`** in this slice). **No** Telegram I/O, **no** DB mutation, **no** publish, **no** migrations, **no** attempt table/idempotency enforcement, **no** readiness/Mini App/booking changes.

## Project

Tours_BOT — showcase channel preview payload (adapter bridge).

## Step

B13D-alt — Channel preview payload read model.

## Checkpoint (before this step)

- **B13B:** **`ShowcaseChannelAdapter`** + **`TelegramShowcaseChannelAdapter`**; moderation **`publish`** via adapter.
- **B13C:** **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** — audit/idempotency design only.

## Delivered (code)

| Area | Path |
|------|------|
| Preview request helper | **`app/services/showcase_channel_adapter.py`** — **`telegram_showcase_channel_publish_request_preview`** |
| Read DTOs | **`app/schemas/supplier_admin.py`** — **`AdminShowcasePublicationPayloadRead`**, **`AdminSupplierOfferShowcaseChannelPayloadRead`** |
| Service | **`app/services/supplier_offer_moderation_service.py`** — **`showcase_channel_payload_preview`** |
| HTTP | **`app/api/routes/admin.py`** — **`GET …/showcase-channel-payload`** |

## Payload shape (summary)

- **`provider`:** **`telegram_showcase_channel`** (**`TELEGRAM_SHOWCASE_PROVIDER`**).
- **`channel_ref`:** configured **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`** (may be **`null`** if unset).
- **`publication`:** **`caption_html`**, **`photo_url`** (same as **`ShowcasePublication`** / **`send_showcase_publication`** args).
- **`idempotency_key`:** **`null`** (reserved for B13C+).
- **`disable_web_page_preview`:** **`True`** when text-only (**no** photo), matches **`sendMessage`** path semantics.

**Not in this slice:** content fingerprint/hash field (optional future for audit); **`review-package`** embedding (optional follow-up).

## Non-goals (preserved)

No publish/send, migrations, attempt table, retry logic, extra channels, readiness changes, Mini App, booking/payment/orders.

## Tests

- **`tests/unit/test_showcase_channel_adapter.py`** — preview helper + **`channel_ref`** from settings.
- **`tests/unit/test_supplier_offer_track3_moderation.py`** — **`GET …/showcase-channel-payload`** 200 + **`_post_telegram_api`** not called; 404 unknown offer.

```text
python -m pytest tests/unit/test_showcase_channel_adapter.py ^
  tests/unit/test_supplier_offer_track3_moderation.py -q
```

## Validation checklist

- [x] Same **`build_showcase_publication`** as publish preview
- [x] **`channel_ref`** matches publish’s configured channel id
- [x] No Telegram client call from new path
- [x] Existing **`GET …/showcase-preview`** and publish tests unchanged in intent

## Next likely steps

1. **B13D** — publish attempt **table / repository / service** skeleton, **if** migration approved.
2. **B13E** — manual-copy / audit wiring (per product).
3. **Optional** — embed **`showcase_channel_payload`** in **`GET …/review-package`**; add **payload fingerprint** for audit alignment.
4. **B13F** (or later) — retry / resend admin workflow **design** then implementation with idempotency.

```

---

## Notes (wrapper)

**Docs finalize (2026-05-09):** B13D-alt completion pointers synced in **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** (§9b, §12), **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** (bridge + §9 forward), **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)** (B13D-alt bullet), **[`docs/CURSOR_PROMPT_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL.md`](CURSOR_PROMPT_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL.md)** (completion block) — **docs-only** pass; **no** code or test edits in that pass.

Implementation context: **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** · **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)**. Prompt: **[`docs/CURSOR_PROMPT_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL.md`](CURSOR_PROMPT_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL.md)**. Prior: **[`docs/HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md)**.

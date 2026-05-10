
---

## HANDOFF name

`HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP

## Status

**B13E implemented.** Publish path creates/updates **`supplier_offer_showcase_publish_attempts`** rows inside **`SupplierOfferModerationService.publish`** — **same** HTTP/Telegram outcomes, readiness, adapter, and lifecycle semantics as before B13E.

## Project

Tours_BOT — Showcase publish attempt audit integration.

## Step

B13E — wire publish attempt audit into publish path.

## Checkpoint (before this step)

- **B13D:** table + **`SupplierOfferShowcasePublishAttemptService`** + **`RESTRICT`** FK (**[`docs/HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`](HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md)**).
- **B13B:** **`TelegramShowcaseChannelAdapter`**; moderation **`publish`** via adapter.

## Delivered (code)

| Area | Path / detail |
|------|----------------|
| Orchestration | **`app/services/supplier_offer_moderation_service.py`** — **`publish`**: `requested` row before adapter; **`provider_sent`** after successful Telegram I/O; offer flush; **`persisted`** with `showcase_chat_id` / `showcase_message_id`; **`failed`** on **`TelegramShowcaseSendError`** or missing `message_id`. **`_showcase_publish_payload_fingerprint`** (SHA-256 of caption + photo ref). |
| HTTP admin | **`app/api/routes/admin.py`** — **`POST …/publish`** passes **`requested_by="http_admin"`**; **`actor_surface`** default **`HTTP_ADMIN`**. |
| Telegram C2B8B | **`app/bot/handlers/admin_moderation.py`** — **`actor_surface=TELEGRAM_BOT`**, **`requested_by=f"telegram:{user_id}"`**. |
| Attempt service | **`app/services/supplier_offer_showcase_publish_attempt_service.py`** — docstring updated (wired from moderation). |

## Attempt lifecycle (as shipped)

- **Success:** `requested` → `provider_sent` → (offer `PUBLISHED` + ids) → `persisted`.
- **Telegram send failure:** `requested` → `failed` (`error_code=telegram_showcase_send`, message from exception).
- **Missing `message_id`:** `requested` → `failed` (`error_code=missing_message_id`).
- **Early validation** (not approved, already published, missing channel/token): **no** attempt row (unchanged guards before insert).

## Non-goals (still)

No publish readiness/operator-workflow/Telegram output/`build_showcase_publication` changes; no retries; no idempotency key enforcement; no Mini App; no booking/payment/orders.

## Tests

**`tests/unit/test_supplier_offer_track3_moderation.py`** — successful publish asserts **`PERSISTED`** attempt + `http_admin` + ids + fingerprint; Telegram error asserts **`FAILED`** + `telegram_showcase_send`. **`tests/unit/test_supplier_offer_showcase_publish_attempt.py`** (B13D regression). **`tests/unit/test_showcase_channel_adapter.py`**.

- `python -m unittest tests.unit.test_supplier_offer_track3_moderation -v`
- `python -m unittest tests.unit.test_supplier_offer_showcase_publish_attempt -v`
- `python -m unittest tests.unit.test_showcase_channel_adapter -v`

## Next likely steps

1. **B13F** — admin read surface for publish **attempt history** (API and/or review-package).
2. **B13G** — **manual** retry/resend **design** (then implementation only with idempotency product approval).
3. **Production** showcase publish **smoke** with **audit** row verification (ops checklist).

```

---

## Notes (wrapper)

Docs finalize (**`CURSOR_PROMPT_B13E_DOCS_FINALIZE`**): **B13C**, **B13_CHANNEL_ADAPTER_DESIGN**, **CHAT_HANDOFF**, this handoff, **CURSOR_PROMPT_B13E** completion note aligned with wired publish attempt audit; **`OPEN_QUESTIONS_AND_TECH_DEBT`** unchanged (no new item).

Prompt: **[`docs/CURSOR_PROMPT_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT.md`](CURSOR_PROMPT_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT.md)**. B13C design: **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)**. Adapter: **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)**. Prior: **[`docs/HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`](HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md)**.

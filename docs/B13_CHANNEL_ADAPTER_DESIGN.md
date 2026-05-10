# B13 — Channel adapter design & implementation (showcase publishing)

**Project:** Tours_BOT. **B13A:** design-only. **B13B:** behavior-preserving adapter + Telegram wrapper (**implemented**).

**Related:** [`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`](B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md) · [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) · [`docs/ADMIN_OPERATOR_WORKFLOW.md`](ADMIN_OPERATOR_WORKFLOW.md) · [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md) · [`docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`](B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md) · [`docs/HANDOFF_B13A_CHANNEL_ADAPTER_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B13A_CHANNEL_ADAPTER_DESIGN_TO_NEXT_STEP.md) · [`docs/HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md`](HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md) · **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** (publish attempt / audit — **docs only**).

**B13C pointer:** **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** records the **future** publish **attempt / idempotency / audit** model. **B13C is documentation only** — **no** publish-attempt table implemented, **no** behavior or readiness change. **Next coding or migrations** (**B13D** / **B13E** or similar) require an **explicit product decision**; **do not** auto-start implementation from this design alone.

---

## 1. Purpose

Showcase publishing must stay **safe** as more surfaces appear. A **channel adapter** layer separates:

- **What** is published (canonical content, already passing admin and policy gates) from **how** it is delivered (Telegram Bot API, future APIs, or manual copy flows).

Without this boundary, teams tend to merge **content generation**, **approval**, **media rendering**, **network I/O**, **retries**, **conversion links**, and **analytics** into one fragile path—raising the risk of duplicate posts, truth drift, or bypassing moderation.

**Future channel examples** (not all shipped; **B13B** delivers **Telegram channel** adapter only — see **§9**):

- Telegram channel (today’s baseline).
- Telegram group.
- WhatsApp broadcast / manual copy export.
- Facebook / Instagram manual copy.
- Website / blog card.
- Email / newsletter.
- Partner feeds.

---

## 2. Core principles

- The channel adapter publishes **approved content only** (per product-defined “ready to publish” state—not the adapter’s own judgment).
- The channel adapter **does not decide business truth** (price, inventory, dates, program—that stays on **`SupplierOffer`** and related models).
- The channel adapter **does not approve** content or packaging.
- The channel adapter **does not create** a **`Tour`** or conversion-chain side effects beyond what the orchestration layer already prescribes.
- The channel adapter **does not create** booking, order, or payment rows (Layer A stays separate).
- The channel adapter **does not invent** discounts, seat scarcity, or urgency.
- The channel adapter **does not bypass** **`media_review`** / publish-safe rules enforced upstream.
- The channel adapter **does not bypass** the read-model intent of **`operator_workflow.actions.publish_showcase_channel`** for the **primary** Telegram showcase UX (operators should still see the same **enabled/disabled** semantics before calling publish).
- The adapter layer must be **idempotent** where repeat delivery is harmful, or **explicitly non-retryable** (surface failure to orchestration; avoid blind retries that duplicate channel posts).

---

## 3. Existing Telegram baseline

**Human / read-model gate (Telegram):** **`app/services/supplier_offer_operator_workflow.py`** exposes **`publish_showcase_channel`** with C2B8A cover hard reasons; admin bot **C2B8B** proposes publish only when that action is **enabled**, with confirmation and re-read of review-package.

**HTTP `POST /admin/supplier-offers/{offer_id}/publish`:** Enforces **`lifecycle_status == approved`**, channel + bot token config, then:

```text
SupplierOfferModerationService.publish
  → build_showcase_publication(row, settings)
  → TelegramShowcaseChannelAdapter.publish(ShowcaseChannelPublishRequest(...))
       → send_showcase_publication(bot_token, chat_id, caption_html, photo_url)
  → persist lifecycle PUBLISHED + showcase_chat_id + showcase_message_id
```

- **Preview** path: **`showcase_preview`** uses **`build_showcase_publication`** only—**no** Telegram I/O.
- **Send:** **`app/services/telegram_showcase_client.py`** — **`send_showcase_publication`**: **sendPhoto** + HTML caption when **`photo_url`** is set; otherwise **sendMessage** with HTML and **`disable_web_page_preview=True`** for text-only.

**B12 note:** **`build_showcase_publication`** does **not** yet consume **`showcase_marketing_template_library_v1`**; **effective template** wiring is a **future content-assembly** concern, not a transport-layer shortcut.

---

## 4. Target layering (future implementation)

```mermaid
flowchart LR
  subgraph gates [Gates_read_model]
    RP[ReviewPackage_OperatorWorkflow]
  end
  subgraph assembly [Content_assembly]
    Build[ShowcaseContentAssembly_build]
  end
  subgraph delivery [Delivery_optional]
    Outbox[Idempotency_audit_outbox_future]
  end
  subgraph adapters [Channel_adapters]
    Tg[TelegramChannelAdapter]
    Other[Other_channels]
  end
  RP --> Build
  Build --> Outbox
  Outbox --> Tg
  Outbox --> Other
```

- **Gates:** unchanged semantics; adapter never re-derives “can publish.”
- **Assembly:** produces a **neutral publication payload** (caption HTML, optional photo reference, flags, CTA URLs from config)—**no** per-channel HTML hacks inside adapters.
- **Outbox / audit (optional later):** dedupe keys, attempt log, retry policy—design-only in B13A.
- **Adapters:** map payload → platform API or export string; return **channel receipt** (e.g. message id).

---

## 5. Contract sketch (normative for B13B+)

Conceptual types (names illustrative):

- **Input:** offer id + immutable snapshot references + settings + **already-validated** “publish allowed” decision from orchestration.
- **Output:** success with **opaque channel ids** or **terminal failure** (retryable vs non-retryable classification).

B13B **implemented** a **Telegram-only** wrapper with regression tests; see **§9**. Further channels, outbox, and publish-attempt storage remain **future**.

---

## 9. B13B (implemented) — adapter interface + Telegram wrapper

- **Module:** **`app/services/showcase_channel_adapter.py`**
- **DTOs:** **`ShowcaseChannelPublishRequest`** (`offer_id`, **`ShowcasePublication`**, optional `channel_ref` / `idempotency_key`); **`ShowcaseChannelPublishResult`** (`provider`, `chat_id`, `message_id` string, optional `raw_reference`).
- **Contract:** **`ShowcaseChannelAdapter`** — sync **`publish(request) -> result`** (matches existing synchronous moderation path).
- **Telegram:** **`TelegramShowcaseChannelAdapter`** delegates to **`send_showcase_publication`** with the same arguments as before B13B.
- **Orchestration:** **`SupplierOfferModerationService.publish`** builds **`ShowcasePublication`** via **`build_showcase_publication`**, calls the adapter with **`channel_ref`** = configured channel id, then persists **`showcase_chat_id`**, **`showcase_message_id`**, lifecycle **`published`** as before.
- **Unchanged:** **`build_showcase_publication`**; **`operator_workflow`** / review-package gates; admin C2B8B flow; **no** publish readiness or caption/photo behavior change; **no** outbox or publish-attempt persistence; **no** additional channels shipped.
- **Tests:** regression on moderation publish + Telegram admin publish + adapter unit test (see **[`docs/HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md`](HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md)**).

---

## 10. Media (B7.4D)

Pipeline is **paused** before durable rendered card integration. Adapters must accept **today’s** **`photo_url`** shapes (`telegram_photo:…`, HTTPS URL) and future **stable asset** URLs without weakening B7.x review rules—see [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md).

---

## 11. Conversion and Layer A

Deep links in captions (**bot** + **Mini App** base URL) are **assembled in the content step**; adapters **emit** them only. No booking/payment calls from adapters. Conversion ordering stays as documented in ops runbooks and conversion smoke docs.

---

## 12. Explicit non-goals (cumulative)

**B13A (design):** No speculative multi-channel product in the design doc alone.

**B13B (implemented refactor):** **No** change to publish **readiness**, **output**, or **external** **`POST …/publish`** contract beyond delegating the send through **`TelegramShowcaseChannelAdapter`**; **no** outbox, **no** publish-attempt table, **no** migrations, **no** new non-Telegram channels, **no** Mini App / booking / payment / order changes.

**Still future / explicit product gates:** **B13C** design (**[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)**) — **implementation** of attempt table / idempotency **not** started; additional channel adapters; **B12** effective template in **`build_showcase_publication`**, B7.4+ durable rendered assets.

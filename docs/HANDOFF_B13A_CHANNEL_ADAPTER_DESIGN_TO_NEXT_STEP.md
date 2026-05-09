
---

## HANDOFF name

`HANDOFF_B13A_CHANNEL_ADAPTER_DESIGN_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13A_CHANNEL_ADAPTER_DESIGN_TO_NEXT_STEP

## Status

**B13A completed (documentation only).** Channel adapter **design** captured in **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)**. **No** code, **no** tests, **no** migrations; **no** Telegram publish behavior, publish readiness, Mini App, or booking/payment/order changes.

## Checkpoint (before this step)

- **B12A–C:** Template library, review-package preview/PATCH, Telegram Template/Șablon UI; **`build_showcase_publication`** still **does not** read template metadata (wiring remains future).
- **B7.4D:** Media pipeline paused before durable rendered-card integration.

## Docs created / updated (finalize)

| Doc | Role |
|-----|------|
| [`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md) | Main B13A design (purpose, principles, Telegram baseline, layering, contract sketch, media, conversion, non-goals). |
| [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) | B13A completed bullet + link to main doc. |
| [`docs/CURSOR_PROMPT_B13A_CHANNEL_ADAPTER_DESIGN.md`](CURSOR_PROMPT_B13A_CHANNEL_ADAPTER_DESIGN.md) | Closed truncation; completion note + B13B pointer. |
| [`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`](B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md) | Optional cross-link + next steps → B13B / design baseline. |

## Key design decisions

- **Separate concerns:** review-package / **`operator_workflow`** gates vs **content assembly** vs optional future **idempotency / audit / outbox** vs **channel adapters** (transport I/O).
- **Adapters** consume a **neutral publication payload**; they do not approve, infer templates, or invent commercial truth.
- **Telegram today** is the **documented baseline** (`SupplierOfferModerationService.publish` → `build_showcase_publication` → `send_showcase_publication`).
- **Primary showcase UX** must keep **`publish_showcase_channel`** read-model intent (no silent bypass).

## Existing Telegram baseline (summary)

```text
operator_workflow / review-package (Telegram C2B8B)
  → POST …/publish (when orchestrated)
  → SupplierOfferModerationService.publish
  → build_showcase_publication
  → telegram_showcase_client.send_showcase_publication
  → channel message id + lifecycle PUBLISHED
```

## Future adapter contract (summary)

- Conceptual **input:** offer context + settings + orchestration-confirmed “publish allowed.”
- **Output:** channel receipt (e.g. message id) or classified error (retry vs terminal).
- **B13B:** Introduce **interface + Telegram wrapper** around current client — **behavior-preserving**; no readiness or HTML/photo policy change.

## Non-goals (preserved for B13A)

- No new routes, no shipped non-Telegram channels, no publish output/readiness changes, no Mini App or Layer A booking/payment changes, no migrations.

## Recommended next step

**`B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER`**

- Behavior-preserving refactor only: extract adapter seam + Telegram implementation behind it.
- **No** publish readiness change; **no** showcase output change; full regression on existing publish/preview/moderation tests.
- Optional **follow-on** (separate scope): wire **effective** B12 template into **`build_showcase_publication`** per B12 spec.

```

---

## Notes (wrapper)

Implementation prompt (historical): [`docs/CURSOR_PROMPT_B13A_CHANNEL_ADAPTER_DESIGN.md`](CURSOR_PROMPT_B13A_CHANNEL_ADAPTER_DESIGN.md). B12 canon: [`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`](B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md).

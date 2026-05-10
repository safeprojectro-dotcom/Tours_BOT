
---

## HANDOFF name

`HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP

## Status

**B13F implemented (read-only).** Docs finalized per **`CURSOR_PROMPT_B13F_DOCS_FINALIZE`**.

## Project

Tours_BOT — Showcase publish attempt audit visibility.

## Step

B13F — Admin publish attempt history read surface.

## Checkpoint (before this step)

- **B13D:** `supplier_offer_showcase_publish_attempts` + repository/service.
- **B13E:** `SupplierOfferModerationService.publish` creates/updates attempt rows (`requested` → `provider_sent` → `persisted` | `failed`).

## Implementation files (reference; unchanged in docs-finalize pass)

| Area | Path |
|------|------|
| Read DTOs | `app/schemas/supplier_admin.py` — `AdminSupplierOfferShowcasePublishAttemptRead`, `AdminSupplierOfferShowcasePublishAttemptsReviewRead`; field on `AdminSupplierOfferReviewPackageRead` |
| Review-package field | **`showcase_publish_attempts_review`** |
| Service | `app/services/supplier_offer_showcase_publish_attempt_service.py` — **`list_attempts_review_read`** (newest first, limit **50**) |
| Aggregation | `app/services/supplier_offer_review_package_service.py` |
| Telegram | `app/bot/handlers/admin_moderation.py` — **`_showcase_publish_attempts_telegram_compact`**; `app/bot/messages.py` — **en** / **ro** strings |
| Tests | `tests/unit/test_supplier_offer_showcase_publish_attempt.py`, `tests/unit/test_supplier_offer_review_package.py` |

## Read model names

- **`AdminSupplierOfferShowcasePublishAttemptRead`**
- **`AdminSupplierOfferShowcasePublishAttemptsReviewRead`**

## HTTP / Telegram behavior (MVP)

- **HTTP:** **`GET /admin/supplier-offers/{offer_id}/review-package`** only — **no** dedicated **`GET …/showcase-publish-attempts`** in B13F MVP (review-package is the main admin read model).
- **Telegram:** admin offer detail appends a **compact** audit summary (up to **5** attempts, error text trimmed) on the same read-only path as operator workflow / conversion panel / template preview.

## Non-goals (preserved)

No retry, resend, manual attempt creation from this surface, readiness or workflow gate changes, Telegram **channel send** / adapter output changes, migrations, new channels, Mini App, booking/payment/orders.

## Tests run

```bash
python -m unittest tests.unit.test_supplier_offer_showcase_publish_attempt tests.unit.test_supplier_offer_review_package -v
python -m unittest tests.unit.test_supplier_offer_ai_public_copy_fact_lock tests.unit.test_supplier_offer_catalog_conversion_closure -v
```

## Likely next steps

1. **Production** showcase publish **smoke** with **audit** verification (review-package JSON or DB).
2. **B13G** — manual retry/resend **design**, **docs-only first** (no behavior until product approves idempotency/safety).
3. **Optional** dedicated admin **`GET …/showcase-publish-attempts`** (+ auth, limit, 404 tests) if operators need a slimmer payload than full review-package.
```

---

## Notes (wrapper)

Docs finalize: **`CURSOR_PROMPT_B13F_DOCS_FINALIZE`** — **`B13C`** §12, **`B13_CHANNEL_ADAPTER_DESIGN`** §9e + pointers, **`CHAT_HANDOFF`** B13F bullet, this handoff, **`CURSOR_PROMPT_B13F`** completion; **`OPEN_QUESTIONS_AND_TECH_DEBT`** unchanged unless a new item is filed separately.

Prompt: **[`docs/CURSOR_PROMPT_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE.md`](CURSOR_PROMPT_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE.md)**. Audit design: **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** §12. Adapter doc: **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** §9e. Prior: **[`docs/HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md`](HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md)**.

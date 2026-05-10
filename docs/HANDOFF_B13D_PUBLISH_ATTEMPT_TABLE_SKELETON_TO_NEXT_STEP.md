
---

## HANDOFF name

`HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP

## Status

**B13D implemented.** Durable **`supplier_offer_showcase_publish_attempts`** table + repository + **`SupplierOfferShowcasePublishAttemptService`** skeleton. **`SupplierOfferModerationService.publish`** is **unchanged** — **no** live-path wiring yet.

## Project

Tours_BOT — Showcase publish attempt audit foundation.

## Step

B13D — publish attempt table + repository/service skeleton.

## Checkpoint (before this step)

- **B13B:** channel adapter wrapper implemented.
- **B13C:** **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** — design only.
- **B13D-alt:** read-only **`GET …/showcase-channel-payload`**.

## Delivered (code)

| Area | Path |
|------|------|
| Enums | **`app/models/enums.py`** — `SupplierOfferShowcasePublishAttemptStatus`, `SupplierOfferShowcasePublishActorSurface` |
| ORM | **`app/models/supplier_offer_showcase_publish_attempt.py`** — `SupplierOfferShowcasePublishAttempt` |
| Offer relationship | **`app/models/supplier.py`** — `showcase_publish_attempts` |
| Model registry | **`app/models/__init__.py`** |
| Migration | **`alembic/versions/20260531_29_supplier_offer_showcase_publish_attempts.py`** (`revision` **`20260531_29`**) |
| Repository | **`app/repositories/supplier_offer_showcase_publish_attempt.py`** |
| Service | **`app/services/supplier_offer_showcase_publish_attempt_service.py`** |

## Table summary

- **FK:** `supplier_offer_id` → `supplier_offers.id` **`ON DELETE RESTRICT`** — **audit retention**: deleting an offer **fails** while attempt rows exist (contrast: **`supplier_offer_tour_bridge`**, **`supplier_offer_execution_links`** use **`CASCADE`** as operational children).
- **ORM:** **`SupplierOffer.showcase_publish_attempts`** — **`passive_deletes=True`** only (**no** **`delete-orphan`**).
- **status:** `requested` → `provider_sent` → `persisted` | `failed` (enum **`SupplierOfferShowcasePublishAttemptStatus`**)
- **actor_surface:** `http_admin` | `telegram_bot` (enum **`SupplierOfferShowcasePublishActorSurface`**)
- **Optional audit fields:** `requested_by`, `idempotency_key`, `payload_fingerprint`, `showcase_chat_id` / `showcase_message_id`, `error_*`, `retryable_failure`

**Not in this slice:** idempotency uniqueness constraints; wiring **`publish`** to create/update rows; fingerprint helper (columns exist for future use).

## Repository / service (skeleton)

- **Repository:** `get_by_id`, `list_for_offer`, `create`, `update`
- **Service:** `create_requested_attempt`, `mark_provider_sent`, `mark_persisted`, `mark_failed`

## Non-goals (preserved)

No Telegram send; **no** live publish integration; **no** publish/readiness behavior changes; **no** retries; **no** worker; **no** new channels; **no** Mini App; **no** booking/payment/orders.

## Tests

**`tests/unit/test_supplier_offer_showcase_publish_attempt.py`** — create, transitions, failure fields, list-for-offer, missing id, **`OFFER DELETE RESTRICT`** when attempts exist, delete offer after removing attempts.

- `python -m alembic upgrade head`
- `python -m unittest tests/unit/test_supplier_offer_showcase_publish_attempt.py -v`
- `python -m unittest tests/unit/test_supplier_offer_track3_moderation.py -v`

## Next likely steps

1. **Wire** attempt create/update into **`publish`** (and optional B13D-alt alignment) with **behavior-preserving** semantics — product-ticket **B13E** (or equivalent naming).
2. **Manual retry / idempotency** design + enforcement — **B13F**+.
3. **Admin read** API/UI for attempt history — **B13G**+.

```

---

## Notes (wrapper)

**Audit retention (pre-commit):** FK changed from **`CASCADE`** to **`RESTRICT`** — publish attempts are **not** silently cascade-deleted with **`supplier_offers`**; aligns with audit intent vs operational child tables (**`supplier_offer_tour_bridge`**, etc.). Developers who already applied an older **`20260531_29`** draft with **`CASCADE`** should **`alembic downgrade 20260530_28`** then **`alembic upgrade head`**.

Prompt: **[`docs/CURSOR_PROMPT_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON.md`](CURSOR_PROMPT_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON.md)**. Design: **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** · **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)**.

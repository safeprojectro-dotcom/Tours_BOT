# HANDOFF — B15B read-only Admin Publishing Console → next step

## What was implemented

- **`GET /admin/publishing-console`** on the Admin API (same **`/admin`** router and **`require_admin_api_token`** as other admin reads).
- **`AdminPublishingConsoleService`** merges:
  - **Supplier-offer** candidates via existing **`SupplierOfferReviewPackageService.review_package`** (aligned with **`GET /admin/supplier-offers/{id}/review-package`**).
  - **Tour promotion** candidates from **`open_for_sale`** tours + **`tour_is_customer_catalog_visible`** + seat/departure checks.
- **DTOs:** `app/schemas/admin_publishing_console.py` (`AdminPublishingConsoleRead`, `AdminPublishingConsoleItemRead`, debug sub-models).
- **Query:** `limit` default 20, max 50; `kind` = `supplier_offer_initial` | `tour_promotion` | `ready` | `blocked` | `needs_attention`.
- **Docs:** **[`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md)** (full contract and non-goals).

## Endpoint (reference)

`GET /admin/publishing-console?limit=20[&kind=…]`

- Auth: **`Authorization: Bearer …`** or **`X-Admin-Token`** with **`ADMIN_API_TOKEN`**.

## Tests

- **`tests/unit/test_admin_publishing_console.py`**
  - 401 without credentials
  - 200 response shape (`items`, `total_returned`, notices)
  - `kind=supplier_offer_initial` → only offer cards
  - `kind=tour_promotion` → only tour cards  

**Reported:** 4 passed (`python -m pytest tests/unit/test_admin_publishing_console.py -v`).

## Limitations

- **Scan cost:** offer path runs **full review-package** per scanned offer (batch size capped in service); not a substitute for a future materialized queue table.
- **Published offers** with **fully green** conversion (`next_missing_step` null) are **omitted** to reduce noise.
- **Tour rows** are **promotion candidates** only — no B15 tour draft entity, no send.
- **No** RFQ / custom-request / service cards in B15B.

## Safety boundaries

B15B must **not** publish, schedule, skip, create console drafts, call Telegram, mutate execution links, activate tours, or touch orders / payments / reservations. **No** change to **`build_showcase_publication`** or **Rezervă** URLs (**B15C**).

## Next prompt

**`CURSOR_PROMPT_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`**

**Goal:** Gate supplier-offer channel publish on a valid **exact tour** conversion target where product requires it; make **Rezervă** point to **`/tours/{tour_code}`** for new posts (see B15A/B14A alignment).

Start B15C only after B15B is **committed** and **verified** in your environment.

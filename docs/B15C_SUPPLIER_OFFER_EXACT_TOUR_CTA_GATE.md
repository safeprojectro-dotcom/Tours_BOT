# B15C — Supplier-offer exact Mini App tour CTA gate

**Status:** Implemented (code + tests).  
**Prompt:** [`docs/CURSOR_PROMPT_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](CURSOR_PROMPT_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md).

## Purpose

For **new** supplier-offer **showcase channel** posts, the public **Rezervă** CTA must open the **exact** bookable tour in the Mini App: `{TELEGRAM_MINI_APP_URL}/tours/{tour_code}` — not the generic supplier-offer landing.

**Detalii** remains the bot deep link (`/start=supoffer_{offer_id}`) and **`/supplier-offers/{id}`** landing stays available for older posts, **Detalii**, and tooling.

## Old vs new sequence

| Phase | Before (risky) | After B15C (safe) |
|--------|----------------|-------------------|
| Conversion | Moderation → **channel publish** → execution link later | Packaging + media gates → moderation → **bridge** → **catalog** → **active execution link** → **then** channel publish |
| Rezervă URL | Often **`/supplier-offers/{id}`** at publish time | **`/tours/{tour_code}`** from active execution link + bridged tour |

## Execution link before publish (when safe)

**`POST /admin/supplier-offers/{id}/execution-link`** (and operator **`link-tour`** / **`replace-link`**) use **`validate_execution_link_target_before_publish`** in **`app/services/supplier_offer_channel_publish_gate.py`**:

- Supplier offer exists; not **rejected**.
- **Packaging** **`approved_for_publish`**.
- **Lifecycle** **`approved`** or **`published`**.
- **Active tour bridge** exists and **tour_id** matches the link target.
- **Tour** **`open_for_sale`**, future departure, **`sales_mode`** matches offer.
- **Catalog:** **`AdminTourWriteService.preview_catalog_activation_for_tour`** → **`catalog_listed_for_mini_app`**.
- No duplicate active link when using **`create_link_for_offer`**.

Published-only is **no longer** required to create an execution link.

## Publish gate (exact target)

**`SupplierOfferModerationService.publish`** and **`showcase_preview` / `can_publish_now`** require **`channel_publish_exact_tour_ready`**: active execution link aligned with bridge, tour open for sale, catalog-listed for Mini App, non-empty **`tour_code`**.

If missing, operators see a bilingual reason (EN/RO), e.g. execution link required before channel publish because **Rezervă** must open the exact Mini App tour.

## Showcase builder

- **`build_showcase_publication`** / **`_cta_block_html`**: **`rezerva_tour_code`** + **`channel_rezerva_requires_exact_tour`** for approved/preview paths.
- **`mini_app_tour_detail_url`** used for **Rezervă** when **`tour_code`** is known; no silent fallback to supplier-offer URL for channel publish when exact tour is required.

## Backward compatibility

- **Do not** edit existing Telegram channel messages.
- **Do not** remove supplier-offer landing or **`supoffer_<id>`** start behavior.
- **Layer A** booking, payment, reservation, temp-hold expiry: **unchanged** by B15C.

## Tests

- **`tests/unit/test_supplier_offer_track3_moderation.py`** — publish / preview / execution-link flows with B15C ordering.
- **`tests/unit/test_supplier_offer_catalog_conversion_closure.py`** — execution link **before** publish; **`next_missing_step`** **`create_execution_link`** mid-chain.
- **`tests/unit/test_admin_publishing_console.py`** — B15B read-only console unchanged.

## Limitations

- **Replacing** execution link to a **different** tour requires the **active bridge** to point at that tour (no HTTP “re-bridge” helper yet; tests may supersede bridge rows locally).
- **B15D–G** items (tour promotion drafts, private transport ads, scheduler, auto-publish) remain **out of scope**.

## Production smoke checklist

**(Operators only — not from Cursor.)**

1. New supplier offer, future departure; complete packaging, media/card, moderation.
2. **`POST .../tour-bridge`** (or link existing tour per `existing_tour_id`).
3. **`POST /admin/tours/{id}/activate-for-catalog`**.
4. **`POST .../execution-link`** **before** **`POST .../publish`**.
5. **`GET .../review-package`** / **`showcase-preview`**: **`publish_showcase_channel`** / **`can_publish_now`** enabled; **`cta_rezerva_href`** contains **`/tours/{tour_code}`**.
6. Publish; open **Rezervă** from the new post → exact tour in Mini App.
7. Spot-check booking/payment unchanged.

## Next steps

- Optional: admin API to **replace tour bridge** without raw DB steps.
- **B15D+** per publishing-console design (drafts, scheduler, etc.).

**Handoff:** [`docs/HANDOFF_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE_TO_NEXT_STEP.md`](HANDOFF_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE_TO_NEXT_STEP.md).

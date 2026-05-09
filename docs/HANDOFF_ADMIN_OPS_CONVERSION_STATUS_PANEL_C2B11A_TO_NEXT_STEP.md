# HANDOFF — Admin/OPS conversion status panel (C2B11A)

## Project

Tours_BOT — Admin/OPS conversion visibility (supplier offer → showcase / bridge / catalog / execution link / customer path).

## Checkpoint

**C2B11A is complete (implementation + docs finalize).** Operators can see a single **read-only** five-layer **`conversion_status_panel`** on **`GET …/review-package`** and a **compact** mirror on the **Telegram** private admin offer card (under **`operator_workflow`**).

**Telegram conversion chain** (unchanged): **Link tour → List for sale → Publish → Booking link** when actions are enabled.

## Files touched (implementation summary)

| Area | Path |
|------|------|
| Panel logic | [`app/services/supplier_offer_conversion_status_panel.py`](../app/services/supplier_offer_conversion_status_panel.py) — `build_conversion_status_panel` |
| Review-package wiring | [`app/services/supplier_offer_review_package_service.py`](../app/services/supplier_offer_review_package_service.py) |
| API schema | [`app/schemas/supplier_admin.py`](../app/schemas/supplier_admin.py) — `AdminSupplierOfferConversionStatusPanelRead`, `…LayerRead`; field on `AdminSupplierOfferReviewPackageRead` |
| Telegram formatter | [`app/bot/supplier_offer_conversion_status_panel_telegram.py`](../app/bot/supplier_offer_conversion_status_panel_telegram.py) |
| Telegram handler | [`app/bot/handlers/admin_moderation.py`](../app/bot/handlers/admin_moderation.py) — appends panel when payload is real Pydantic |
| i18n | [`app/bot/messages.py`](../app/bot/messages.py) — `admin_conversion_panel_*` |
| Tests | [`tests/unit/test_supplier_offer_review_package.py`](../tests/unit/test_supplier_offer_review_package.py), [`tests/unit/test_supplier_offer_conversion_status_panel.py`](../tests/unit/test_supplier_offer_conversion_status_panel.py), [`tests/unit/test_telegram_admin_moderation_y281.py`](../tests/unit/test_telegram_admin_moderation_y281.py) |

**This finalize pass:** docs only — [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md), this handoff.

## Panel shape (HTTP / JSON)

Top-level key: **`conversion_status_panel`**.

Each layer is an object:

- **`showcase`**, **`tour_bridge`**, **`catalog`**, **`booking_link`**, **`customer_action`**
- Fields per layer: **`status`** (string), **`summary`** (operator-facing English), optional **`detail`**

Example layer values:

| Layer | Typical `status` values |
|-------|-------------------------|
| Showcase | `published`, `not_published`, `blocked` |
| Tour bridge | `linked`, `missing` |
| Catalog | `listed_for_sale`, `not_listed`, `blocked` |
| Booking link | `active`, `missing`, `stale` |
| Customer action | `open_exact_mini_app_tour`, `not_bookable_yet`, `assisted_fallback` |

## Derivation summary

**No new business gates:** the panel is **derived only** from data already assembled for **`review-package`** (lifecycle, **`showcase_preview`**, **`bridge_readiness`**, **`linked_tour_catalog`**, **`execution_links_review`**, **`conversion_closure`**, **`mini_app_conversion_preview`**, **`operator_workflow`** actions such as **`publish_showcase_channel`**, and **`SupplierOfferConversionPreviewForAdmin`**).

- **Showcase:** lifecycle published vs approved + **`can_publish_now`** vs operator publish action disabled (cover/packaging path).
- **Tour bridge:** **`conversion_closure.has_tour_bridge`** / bridge readiness hints.
- **Catalog:** linked-tour preview — listing, **`can_activate_for_catalog`**, B8.3 conflict, missing fields.
- **Booking link:** active execution link; **stale** when active link **`tour_id`** ≠ bridged **`tour_id`**; missing when unpublished or no link.
- **Customer action:** Mini App conversion preview **actionability** + closure (e.g. **BOOKABLE** + execution link + bot deep link → open exact tour).

## Telegram output summary

- Header/footer lines (**C2B11A** / full JSON hint).
- Five bullet lines (EN/RO via **`admin_conversion_panel_*`** keys), optional **`detail`** sub-line (`· …`).
- Rendered **after** the existing **operator workflow** block; **skipped** if **`review_package`** mock has no real **`AdminSupplierOfferConversionStatusPanelRead`** (unit tests).

## Tests run (regression suites for C2B11A)

**Not re-run in the docs-only finalize pass.** Suites that cover the panel:

- `tests/unit/test_supplier_offer_review_package.py`
- `tests/unit/test_supplier_offer_conversion_status_panel.py`
- `tests/unit/test_telegram_admin_moderation_y281.py`

## Non-goals (preserved)

- **Read-only** — panel does **not** POST, mutate lifecycle, bridge, catalog, links, or Telegram.
- **No migrations.**
- **No Mini App** surface or API behavior changes.
- **No** booking, payment, or order logic changes.
- **No B11** routing / deep-link behavior changes.

## Next steps

1. **Production/OPS smoke** — [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md); include **`conversion_status_panel`** in **`GET …/review-package`** checks — [`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`](CONVERSION_CHAIN_OPS_SMOKE_READINESS.md).
2. **B10.6 Bot-as-router** (when product prioritizes) — [`docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`](B10_6_BOT_AS_ROUTER_DESIGN_GATE.md).
3. **Optional visibility polish** — tighter copy, extra **`detail`** rules, or admin-only web view; still **read-only** and derived from **`review-package`**.

## References

- Design: [`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`](ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md)
- Prompt: [`docs/CURSOR_PROMPT_ADMIN_OPS_CONVERSION_STATUS_PANEL_C2B11A.md`](CURSOR_PROMPT_ADMIN_OPS_CONVERSION_STATUS_PANEL_C2B11A.md)
- Closeout ordering: [`docs/NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md`](NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md)
- Continuity: [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) — **Slice C2B11A**

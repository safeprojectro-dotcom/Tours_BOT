# HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS

## Project
Tours_BOT

## Block
B15H — Read-only publish readiness / suggest-only metadata

## Prerequisites

- B15G design — [`docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md`](B15G_GUARDED_AUTO_PUBLISH_DESIGN.md)
- B16D2C/D/E, B15E2 — `prepare_conversion_chain` execution + affordances (internal; not publish)

## Delivered

- **Schema:** `app/schemas/admin_publish_readiness.py` — `AdminPublishReadinessRead`, gate DTOs; `can_auto_publish` always `False`; `auto_publish_mode` `disabled`.
- **Service:** `app/services/supplier_offer_publish_readiness.py` — `derive_supplier_offer_publish_readiness`, `publish_readiness_for_tour_promotion`, placeholder stub for assembly.
- **Navigation:** `supplier_offer_publish_showcase_path` in `app/services/admin_navigation_paths.py` — documents manual POST path only (read models).
- **Wiring:** `SupplierOfferReviewPackageService` (`app/services/supplier_offer_review_package_service.py`) adds `publish_readiness` to `AdminSupplierOfferReviewPackageRead` (`app/schemas/supplier_admin.py`). `AdminPublishingConsoleService` (`app/services/admin_publishing_console_service.py`) attaches `rp.publish_readiness` for supplier-offer rows and `not_applicable` readiness for `tour_promotion`. **B15I** adds compact **UX fields** on the same DTO — see [`docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md`](HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md).

## Boundaries (must hold)

- **Read-only:** no Telegram send, no publish execution, no scheduler, no auto-publish, no new `publish_attempt` rows from these paths, no guarded-action attempts from GETs, no Layer A / bridge / execution-link mutation, no migration.
- **Suggest-only:** operator still uses existing explicit **POST …/publish** (or Telegram parity) after confirmation.

## Tests

- [`tests/unit/test_supplier_offer_publish_readiness.py`](../tests/unit/test_supplier_offer_publish_readiness.py)
- Updates: `test_supplier_offer_review_package.py`, `test_admin_publishing_console.py`

## Next (optional)

- Surface short **publish_readiness** summary in admin/OPS UIs (still read-only).
- UX for `needs_review` vs `ready_to_suggest` in console (no behavior change).
- Any future **auto-publish** remains gated per B15G and separate go/no-go.

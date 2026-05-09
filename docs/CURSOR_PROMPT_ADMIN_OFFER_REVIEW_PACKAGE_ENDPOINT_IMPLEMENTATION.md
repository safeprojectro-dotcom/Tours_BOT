# CURSOR_PROMPT_ADMIN_OFFER_REVIEW_PACKAGE_ENDPOINT_IMPLEMENTATION

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is the implementation step for:

ADMIN OFFER REVIEW & APPROVAL GATE — Slice 1

Implement a read-only admin review package endpoint.

---

## Business goal

Admin needs one safe read model before deciding what to do with a Supplier Offer:

Supplier raw offer
→ AI/deterministic packaging draft
→ Admin review / approve
→ Create/link Tour
→ Activate Tour for Mini App catalog
→ Channel showcase / Bot / Mini App conversion
→ Booking/payment through Layer A

This step implements the read-only review package only.

---

## Critical architecture rules

Preserve strictly:

- Supplier Offer = raw/source facts.
- Packaging approval axis is separate from moderation/showcase lifecycle axis.
- `packaging_status == approved_for_publish` does not mean Telegram published.
- `lifecycle_status == published` does not mean Tour is visible/bookable in Mini App.
- Tour = customer-facing sellable catalog object.
- Mini App = execution truth.
- Layer A = booking/payment authority.
- Channel = marketing showcase.
- Bot = router/consultant.
- visibility != bookability.
- No hidden ORM trigger from SupplierOffer to Tour.
- No AI-created Tour.
- No supplier bypass.
- No booking/payment side effects in review.
- No automatic publish.
- No automatic bridge.
- No automatic catalog activation.

---

## Current design accepted

The accepted design identified two orthogonal axes:

### Packaging axis

- `SupplierOfferPackagingStatus`
- `POST .../packaging/approve`
- target: `approved_for_publish`
- B10 Tour bridge requires packaging approved for publish.

### Moderation / showcase axis

- `SupplierOfferLifecycle`
- `POST .../moderation/approve`
- `ready_for_moderation → approved`
- `POST .../publish`
- `approved → published`
- Showcase publish requires `approved`.
- Execution link creation requires `published`.

Review package must surface both axes and must not collapse them.

---

## Goal

Add read-only endpoint:

```http
GET /admin/supplier-offers/{offer_id}/review-package
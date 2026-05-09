# HANDOFF_B11_SUPPLIER_OFFER_DEEP_LINK_ROUTING_TO_IMPLEMENTATION

Project: Tours_BOT

## Current checkpoint (B11 design done — implementation next)

**Prerequisites unchanged:** B8 line closed (recurrence/guards/docs); B7.1–B7.3B done; no durable media pipeline.

**B11 routing contract (design / Plan step): agreed direction for implementation:**

- **Source of truth for “which Tour” for a published offer:** active row in **`supplier_offer_execution_links`** (same as Mini App supplier-offer landing / `MiniAppSupplierOfferLandingService`), **not** `SupplierOfferTourBridge` alone and **not** inferred B8 recurrence rows.
- **Mini App URLs:** exact tour detail `{TELEGRAM_MINI_APP_URL}/tours/{tour_code}`; offer landing fallback `{base}/supplier-offers/{offer_id}` (existing `mini_app_supplier_offer_url` pattern in `supplier_offer_deep_link.py`). Bot builds from config; no new publish/activation.
- **Actionability / copy:** align read-side rules with **`MiniAppSupplierOfferLandingService._resolve_actionability`** (open_for_sale, visibility window, per_seat vs full_bus policy) so bot messaging does not contradict Mini App truth; **visibility ≠ bookability**.

Spec source: `docs/CURSOR_PROMPT_B11_SUPPLIER_OFFER_DEEP_LINK_ROUTING_DESIGN.md` (design questions + non-goals); handler today: `app/bot/handlers/private_entry.py` (`handle_start` for `supoffer_<id>`).

## B11 purpose (implementation)

Implement Telegram deep-link routing for Supplier Offers.

`/start supoffer_<id>` should not only send generic catalog + root Mini App.

Route users safely:

1. Linked tour via **execution link** + **sellable/actionable** per landing rules → short context → **primary WebApp button to `/tours/{tour_code}`**.
2. Linked tour exists but **not** bookable (draft / view-only / assisted-only / sold out / visibility) → **no** misleading booking CTA; safe text + **`/supplier-offers/{id}`** and/or catalog/help as chosen in implementation slice.
3. **No** active execution link → offer landing fallback and/or catalog; **no** create Tour, **no** activate.
4. Offer missing / not **published** / rejected → existing-style unavailable fallback.

## Architecture rules

- Telegram Bot = router / consultant / entry point
- Mini App = execution truth and conversion
- Supplier Offer = source facts; Tour = customer-facing sellable object
- Admin remains final decision maker; AI does not create or activate Tour
- visibility != bookability; no automatic publish; no booking/payment side effects

## Non-goals

Do not implement:

- Telegram channel publishing; media/photo posting; B7 storage/rendering
- B10.6 full bot redesign; B12/B13 template/channel adapter
- booking/payment/order changes
- SupplierOfferTourBridge **creation**; Tour **activation**; B8 recurrence changes

## Next step (implementation Agent)

Use a **single** small implementation prompt (suggested name: **`CURSOR_PROMPT_B11_SUPPLIER_OFFER_DEEP_LINK_ROUTING_IMPLEMENTATION.md`**) when ready to code.

Likely work:

- Update `/start supoffer_<id>` in `private_entry.py` (reuse or call shared resolver aligned with **`MiniAppSupplierOfferLandingService`**).
- Exact Mini App **`/tours/{code}`** WebApp URL when appropriate; **`/supplier-offers/{id}`** otherwise.
- Translation keys + keyboard helpers; **`/start tour_<code>`** behavior unchanged unless explicitly included.
- Focused tests (execution link matrix, regressions).

Do not start implementation automatically until that prompt is run.


---

## HANDOFF name

`HANDOFF_B10_6A_BOT_AS_ROUTER_SUPPLIER_OFFER_START_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B10_6A_BOT_AS_ROUTER_SUPPLIER_OFFER_START_TO_NEXT_STEP

## Status

**B10.6A implemented (docs finalized 2026-05-09).** Customer `/start supoffer_<id>` copy is driven by **`nav.copy_bucket`** from **`resolve_sup_offer_start_mini_app_routing`**; the private entry handler adds **no** new routing rules.

## Project

Tours_BOT — Bot-as-router for Supplier Offer deep links (customer copy layer).

## Step

B10.6A — `/start supoffer_<id>` customer routing/copy improvement.

## Purpose

Make the bot a safe customer-facing router after supplier-offer publication and conversion-link work — **without** changing execution truth or admin pipelines.

## Preconditions (unchanged)

Admin/OPS chain exists: **Link tour → List for sale → Publish → Booking link.**

## Implementation summary

- **B11** URL and gate **semantics preserved**; resolver gains read-only **`copy_bucket`** / **`context_tour_code`** for messaging only.
- **`app/bot/handlers/private_entry.py`**: **`_supplier_offer_start_intro()`** maps buckets to **`start_sup_offer_router_*`** keys.
- **Exact tour** path: customer copy + Mini App CTA; **`linked_is_full_bus`** adds the full-bus note.
- **Published / no link** and **unavailable / fallback** buckets use safe customer wording (no internal terms).
- **Translations:** **sr** / **hu** / **it** / **de** (and **ru**) include new keys so **`translate()`** does not miss strings.
- **Tests passed:** **`test_supplier_offer_bot_start_routing_b11.py`**, **`test_private_entry_supoffer_start_hotfix.py`**.

## Explicit non-scope (unchanged by B10.6A)

- **No** tour-bridge / catalog / execution-link / publish **mutations** from this slice.
- **No** Mini App code or behavior changes.
- **No** booking / payment / orders changes.
- **No** database migrations.

## Next likely step

**Production / OPS Mode A / B smoke** — operator walkthrough: [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md) (dry-run Mode **A** / live Mode **B**).

## Optional follow-ups

- Prod copy review (native polish for EN fallbacks in secondary locales).
- Retire or repurpose legacy keys **`start_sup_offer_intro`** / **`start_sup_offer_intro_exact_tour`** if unused.
- Media pipeline: remain paused at **B7.4D** until chartered.
```

---

## Notes (wrapper)

The block above is the portable handoff payload for the next chat or PR description.

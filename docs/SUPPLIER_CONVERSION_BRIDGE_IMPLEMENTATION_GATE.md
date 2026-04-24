# Supplier Conversion Bridge Implementation Gate

## 1) Current state
- Mini App Telegram identity/runtime isolation is stabilized and accepted:
  - local `assets/telegram-web-app.js` is used;
  - `assets/index.html` injects `tg_bridge_user_id` before Flet starts;
  - runtime evidence confirms `has_identity=True` (`source=route_query_user_id`).
- User-scoped Mini App flows are stabilized in accepted scope:
  - `My bookings`, `My requests`, `Settings`,
  - custom request submit/create,
  - reservation/payment continuation.
- Custom request bridge-preparation `404` for fresh requests is handled as a normal non-error waiting UX state.
- Phase 7.1 full-bus actionability boundaries are refined and accepted:
  - `bookable` only when `seats_total > 0` and `seats_available == seats_total`;
  - partial full-bus inventory => `assisted_only`;
  - sold out => `view_only`;
  - invalid snapshot => `blocked`.
- Supplier -> Conversion Bridge runtime implementation has **not** started yet.

## 2) Existing entities and assumed tables
- `supplier_offers` (supplier/publication/showcase identity).
- `tours` (Layer A executable inventory + booking/payment context).
- `supplier_offer_execution_links` (authoritative linkage between offer and executable tour context).
- `orders` (+ existing payment tables) as Layer A execution truth.
- `custom_marketplace_requests` (+ RFQ bridge tables) as separate Mode 3 domain.

Hard boundary remains mandatory: `supplier_offer != tour`.

## 3) What is already implemented
- Stable supplier-offer Mini App landing path is implemented and used as channel-to-mini-app entry contract.
- Landing actionability is resolved from current runtime truth (`bookable`/`sold_out`/`assisted_only`/`view_only`), not from stale publication hints.
- Direct booking CTA is already constrained to authoritative execution truth conditions.
- Fail-safe behavior is already present: no direct execution CTA if target/actionability is not valid.

## 4) What is missing
- A finalized, implementation-ready first runtime slice specifically for Supplier Offer -> Conversion Bridge execution gating.
- Explicitly locked transition rules for these states:
  - published offer with no active authoritative link;
  - published offer with active link but non-bookable runtime state;
  - published offer with active link and currently bookable runtime state.
- A documented first-step rollback/fail-safe playbook tied to conversion resolver behavior.

## 5) Safe first implementation slice
- Implement/lock a narrow conversion resolver flow for supplier-offer landing that uses only:
  1. published offer identity,
  2. active authoritative `supplier_offer_execution_links` row,
  3. current Mini App execution truth (tour visibility + sales mode policy + current inventory/actionability).
- Keep CTA gate strict:
  - direct booking CTA is shown only when an active authoritative execution link exists and current runtime state is `bookable`;
  - all other cases degrade to non-bookable actionability (`assisted_only`/`view_only`/`blocked`) with safe fallback CTA.
- Reuse existing Layer A execution routes only when gate passes; do not introduce new booking/payment semantics.

## 6) Explicit out-of-scope items
- Any merge of `supplier_offer` and `tour`.
- Any Layer A booking/payment redesign.
- Any RFQ/request-bridge semantic redesign.
- Any identity-bridge redesign.
- Coupons/incidents/automation expansion.
- Broad admin workflow redesign in the same slice.

## 7) Tests required before runtime change
- Resolver/unit tests for conversion actionability with linkage-aware scenarios:
  - published + no active link => non-bookable safe state;
  - published + active link + runtime bookable => direct booking CTA available;
  - published + active link + partial full-bus => `assisted_only`;
  - published + active link + sold out => non-bookable (`sold_out`/`view_only`);
  - invalid inventory snapshot => `blocked`.
- Contract tests: direct booking CTA is never exposed without active authoritative link.
- Regression tests proving no change in:
  - Layer A booking/payment behavior,
  - RFQ bridge semantics,
  - identity fail-closed behavior.

## 8) Rollback/fail-safe behavior
- If linkage is missing/invalid/stale at runtime: degrade to non-bookable landing state; never expose direct booking CTA.
- If runtime tour state becomes non-bookable after publication: keep visibility, remove direct-booking actionability.
- If resolver cannot establish trustworthy execution truth: default to safest non-bookable state (`assisted_only`/`view_only`; `blocked` for invalid snapshots).
- Rollback priority: disable conversion CTA exposure first; do not mutate Layer A or RFQ semantics during rollback.

---

## Next safe order
1. Supplier -> Conversion Bridge design/implementation gate (this document).
2. Admin operational visibility for bookings/requests.
3. Operator workflows.

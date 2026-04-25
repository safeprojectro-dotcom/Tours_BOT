# Operator Execution Link UI Gate

## 1) Current state
- Authoritative execution linkage exists as `supplier_offer_execution_links`.
- Y32.1 supplier-offer landing/read-side actionability is accepted:
  - direct booking CTA is enabled only through an active authoritative execution link;
  - linked tour must be currently `bookable` by execution / `sales_mode` policy;
  - no active link falls back to non-bookable customer state and catalog browsing.
- Operator/admin execution-link workflow is already defined in `docs/OPERATOR_EXECUTION_LINK_WORKFLOW_GATE.md`:
  - create link;
  - replace active link;
  - close active link;
  - view link history.
- Manual smoke confirmed:
  - active link `supplier_offer_id=5 -> tour_id=3`;
  - linked execution metrics appeared for the supplier offer;
  - `full_bus` sold out / `0` seats kept direct booking CTA unavailable;
  - `full_bus` offer cannot link to `per_seat` tour;
  - supplier-admin sees own offers only, central admin sees all through `/admin`.
- This document is a UI design gate only. It does not add runtime code, migrations, schemas, or API semantics.

## 2) User roles / permissions
- Central admin/operator:
  - may view all supplier offers;
  - may view current execution link status and link history;
  - may create, replace, and close links when validations pass.
- Supplier operator:
  - may view only own supplier offers and safe aggregate execution metrics when an active link exists;
  - must not create, replace, close, or edit execution links.
- Customer / Mini App user:
  - sees only customer landing/actionability results;
  - must not see operator controls or link-management internals.
- Telegram admin workspace, if used for this UI later, must remain fail-closed to allowlisted admins.
- Backend/admin web UI, if used for this UI later, must remain protected by the existing admin auth surface.

## 3) UI entry points
- Central admin supplier-offer detail:
  - primary entry for link status and actions.
- Central admin supplier-offer list:
  - may show compact link badge: `No active link`, `Linked`, `Linked but non-bookable`, or `Link attention needed`.
- Telegram admin offer workspace:
  - optional operational client for quick view/actions;
  - should not replace backend/service validation.
- Supplier offer publication/moderation workspace:
  - may show read-only link status after publication;
  - must not imply that approval or publication creates an execution link.
- Tour picker/search:
  - operator chooses an existing Layer A tour;
  - UI must never offer "create tour from offer" inside this workflow.

## 4) Screen/button flow

### Offer link status panel
- Show supplier offer id, title, lifecycle status, sales mode, departure time.
- Show current link state:
  - no active link;
  - active link with tour id/code, tour status, sales mode, seats available/total, derived actionability;
  - closed link history exists.
- Show customer-facing consequence:
  - `Direct booking CTA available` only if active linked tour is currently bookable;
  - otherwise `No direct booking CTA; fallback remains safe`.

### Create link flow
- Button: `Link to tour`.
- Prompt/search: enter or choose existing `tour_id` / tour code.
- Confirmation screen shows:
  - supplier offer summary;
  - selected tour summary;
  - sales mode comparison;
  - warning that no tour/order/payment state will be created or changed.
- Final action: create active link if no active link exists.

### Replace link flow
- Button: `Replace link` only when an active link exists.
- Prompt/search: choose different existing tour.
- Confirmation screen shows:
  - current active link target;
  - replacement target;
  - old link close reason: `replaced`;
  - warning that customer direct CTA may remain disabled if new tour is not bookable.
- Final action: close old link and activate new link in one logical operation.

### Close link flow
- Button: `Close link`.
- Prompt: choose allowlisted reason (`unlinked`, `retracted`, `invalidated`) and optional note if available.
- Confirmation screen states:
  - direct execution authority will be removed;
  - supplier-offer landing remains visible when published;
  - customer direct booking CTA will be disabled.
- Final action: close active link.

### Link history flow
- Button: `View link history`.
- Show rows newest first:
  - link id;
  - tour id/code;
  - status;
  - close reason;
  - note if present;
  - created/closed timestamps.
- No edit controls for historical rows.

## 5) Validation messages
- Offer not found: `Supplier offer not found.`
- Offer not published: `Only published supplier offers can be linked to execution tours.`
- Tour not found: `Tour not found for execution linkage.`
- Sales mode mismatch: `Tour sales_mode must match supplier offer sales_mode.`
- Invalid tour status: `Tour status is not valid for operational linkage.`
- Past departure: `Only future-departure tours can be linked.`
- Active link already exists on create: `Active execution link already exists. Use Replace link instead.`
- No active link on close: `No active execution link to close.`
- Invalid close reason: `Choose one of: unlinked, retracted, invalidated.`
- Generic fail-safe: `Could not prove safe execution target. No link was changed.`

## 6) Fail-safe states
- No active link:
  - show `No active execution link`;
  - disable direct execution actions for customers;
  - keep browse/catalog fallback.
- Active link but tour non-bookable:
  - show active link status;
  - show reason if available (`sold out`, `assisted only`, `view only`, `unavailable`);
  - keep direct customer CTA disabled.
- Validation failure during create/replace:
  - keep existing active link unchanged;
  - show specific validation message.
- Close failure:
  - keep active link unchanged;
  - show `No active execution link to close` or validation message.
- Backend/API unavailable:
  - do not update local UI optimistically;
  - show retry-safe error;
  - require refresh before another mutation attempt.
- Unknown or inconsistent state:
  - prefer read-only display and disabled mutation buttons.

## 7) Minimal first runtime slice
- Add UI only on the central admin/operator surface first.
- Reuse existing admin API actions:
  - create: `POST /admin/supplier-offers/{id}/link-tour`;
  - replace: `POST /admin/supplier-offers/{id}/replace-link`;
  - close: `POST /admin/supplier-offers/{id}/close-link`;
  - history: `GET /admin/supplier-offers/{id}/links`.
- Show current link status on supplier-offer detail.
- Provide a minimal tour selector by explicit `tour_id` or tour code search.
- Require confirmation before create, replace, and close.
- Keep Telegram admin UI as optional follow-up unless product wants the first runtime slice there.
- Tests for the future implementation should cover:
  - link status panel with no active link;
  - active link panel with non-bookable tour;
  - create / replace / close button visibility;
  - validation message rendering;
  - history rows shown without customer PII.

## 8) Out of scope
- Runtime implementation in this design gate.
- Migrations or schema changes.
- Auto-create tours.
- Merging `supplier_offer` and `tour`.
- Layer A booking/payment changes.
- RFQ semantic changes.
- Identity bridge changes.
- Supplier-side link mutation controls.
- Customer-facing link-management UI.
- Coupon/promo logic.
- Incident/disruption runtime behavior.
- Broad operator workflow engine, assignments, notifications, dashboards, or SLA tooling.

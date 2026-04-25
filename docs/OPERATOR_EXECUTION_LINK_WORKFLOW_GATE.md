# Operator Execution Link Workflow Gate

## 1) Current state
- `supplier_offers` remain supplier/publication/showcase records; they are not executable Layer A tours.
- `tours` remain Layer A execution truth for inventory, booking, reservation, and payment paths.
- `supplier_offer_execution_links` is the authoritative bridge between a published supplier offer and an executable tour context.
- Link persistence and narrow admin/service primitives already exist:
  - create or replace active link;
  - close active link;
  - list link history for an offer.
- Y32.1 supplier-offer landing/read-side actionability is accepted:
  - direct booking CTA is enabled only when an active authoritative link exists and the linked tour is currently bookable by execution / `sales_mode` policy;
  - no active link falls back to `view_only` + `browse_catalog`;
  - non-bookable linked tours do not expose false booking CTA.
- This gate is documentation-only and does not change runtime code, schema, migrations, booking/payment behavior, RFQ behavior, or identity bridge behavior.

## 2) Required operator actions

### Create link
- Operator selects one published `supplier_offer`.
- Operator selects one existing Layer A `tour` as execution target.
- System creates one active `supplier_offer_execution_links` row when validation passes.
- No tour is created automatically.
- No booking, reservation, hold, payment, or RFQ state is mutated.

### Replace link
- Operator selects a published `supplier_offer` with an existing active link.
- Operator selects a different existing Layer A `tour`.
- System closes the old active link as `replaced` and creates the new active link in the same logical operation.
- Historical link rows remain visible for audit and rollback investigation.
- Replacement must not silently preserve a direct booking CTA unless the new linked tour is bookable by current runtime policy.

### Close link
- Operator closes the active link with an explicit reason such as `unlinked`, `retracted`, or `invalidated`.
- Closing a link removes direct execution authority from supplier-offer landing.
- Closing a link must not mutate Layer A tour status, orders, reservations, payments, RFQ bridges, or supplier-offer publication text.
- If no active link exists, operator UX should show a safe no-active-link state rather than inventing a target.

### View link history
- Operator can view all links for a supplier offer in reverse chronological order.
- History must show at minimum: target tour, link status, close reason, operator/admin note if present, created timestamp, closed timestamp if present.
- History is read-only in this workflow; editing prior rows is postponed.

## 3) Required validations
- Supplier offer exists.
- Supplier offer is `published` before a new active execution link can be created.
- Target tour exists.
- Target tour is not cancelled or completed.
- Target tour departure is in the future.
- Target tour `sales_mode` matches supplier offer `sales_mode`.
- At most one active link exists per supplier offer.
- Replacing with the same active target should be idempotent or a no-op, not duplicate history.
- Close reason must be allowlisted.
- Operator note must be optional, bounded, and non-customer-PII.
- Validation must fail closed: if the system cannot prove the target is valid, it must not create or keep an active execution link.

## 4) Fail-safe behavior
- Missing active link: supplier-offer landing remains visible when published, but direct booking CTA stays disabled.
- Invalid target tour: link creation/replacement must fail; existing valid active link should not be replaced by an invalid target.
- Linked tour later becomes non-bookable: supplier-offer landing keeps visibility but removes direct booking CTA using current Y32.1 read-side actionability.
- Closed/retracted/invalidated link: treated as no active execution authority.
- Resolver disagreement or missing execution truth: prefer `view_only` / `unavailable` over false-positive `bookable`.
- Rollback priority: close or disable the active link first; do not patch Layer A booking/payment or RFQ semantics as rollback.

## 5) Admin permissions/security
- Link workflow is admin/operator-only.
- Suppliers cannot create, replace, close, or edit execution links directly.
- Customer Mini App screens cannot mutate links.
- Admin identity must be fail-closed using the existing admin auth surface for backend routes and allowlisted Telegram-admin surface where applicable.
- Link history must not expose customer PII, payment provider data, order-level customer lists, or RFQ-sensitive supplier data outside existing permissions.
- Operator notes must be treated as internal operational metadata and should not appear on public/customer/supplier-facing landing pages unless explicitly scoped later.

## 6) Audit/history requirements
- Every create, replace, and close operation must leave deterministic history.
- Replacement must preserve the old link row with a terminal close reason such as `replaced`.
- Retraction-driven close should preserve `retracted`.
- Manual close should preserve the chosen allowlisted reason.
- Future implementation should record who performed the action when an operator identity/audit field is available; if the current table does not support this, do not fake it in free text.
- History must be enough to answer:
  - which supplier offer was linked;
  - which tour was the execution target;
  - when the link became active;
  - when and why it stopped being active;
  - which link was active at the time of a customer-facing actionability decision.

## 7) What remains postponed
- Automatic tour creation from supplier offers.
- Automatic matching/linking by title/date/price/text heuristics.
- Merging `supplier_offer` and `tour`.
- Layer A booking/payment workflow changes.
- RFQ bridge semantic changes.
- Supplier-facing link mutation controls.
- Customer-facing link mutation controls.
- Coupon/promo logic tied to supplier-offer conversion.
- Incident/disruption runtime behavior; design gate first.
- Broad operator workflow engine, assignments, SLA tracking, notifications, and dashboards.
- Rich audit columns or actor attribution if not already supported by persistence.

## 8) First safe implementation slice
- Keep the first runtime slice narrow and operational:
  1. expose or polish admin/operator surface for existing create/replace/close/list primitives;
  2. require explicit published offer ID and existing tour ID;
  3. reuse existing service-layer validations;
  4. preserve one-active-link invariant;
  5. show link history and current active target in admin/operator context;
  6. verify that supplier-offer landing Y32.1 actionability changes only through active link state and linked tour bookability.
- Required tests for that future slice:
  - create link for valid published offer and future matching tour;
  - reject unpublished offer;
  - reject missing, cancelled, completed, past, or sales-mode-mismatched tour;
  - replace closes old link and creates one active new link;
  - close removes direct booking CTA by causing no active execution link;
  - link history lists active and closed rows without customer PII.
- Out of scope for the first slice:
  - creating tours;
  - changing booking/payment/RFQ semantics;
  - direct supplier mutation;
  - incident/coupon/operator automation.

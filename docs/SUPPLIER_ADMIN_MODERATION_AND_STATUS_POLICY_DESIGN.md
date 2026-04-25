# Supplier Admin Moderation And Status Policy Design (Y29)

## Status
- Design-only gate.
- No runtime changes in this step.
- No migration/test changes in this step.

## Purpose
Define a narrow supplier-governance layer on top of already implemented supplier onboarding/intake/moderation/publication/admin Telegram operations:
1. supplier onboarding Telegram navigation polish (`/supplier`),
2. Telegram admin supplier-profile moderation workspace (separate from offer moderation),
3. supplier profile status policy (including suspend/revoke effects on offer visibility).

This design preserves the existing architecture and explicitly keeps supplier profile lifecycle separate from supplier offer lifecycle.

---

## 1) Core Domain Separation (Non-Negotiable)

## Supplier profile lifecycle (entity governance)
Controls whether a supplier entity is operationally allowed on platform surfaces.

## Supplier offer lifecycle (content/publication governance)
Controls whether an individual offer is draft/moderation-ready/approved/published/retracted.

## Rule
Never reuse offer terms (`publish`, `retract`) as supplier-profile actions.
Supplier-profile actions must be entity-governance terms (`approve`, `reject`, `suspend`, `reactivate`, `revoke`).

---

## 2) `/supplier` Onboarding Navigation Polish Recommendation

## Decision
Add narrow navigation controls in onboarding FSM aligned with already accepted `/supplier_offer` pattern:
- `Inapoi` (step back),
- `Acasa` (cancel/home).

## Safe semantics
- `Inapoi`:
  - move exactly one FSM step back,
  - preserve already-entered draft onboarding data in FSM context,
  - do not persist partial onboarding to database on back action.
- `Acasa`:
  - clear onboarding FSM state fully,
  - clear in-memory draft onboarding fields,
  - return to neutral supplier entry message.

## Rationale
- Reduces correction friction without changing onboarding policy semantics.
- Keeps behavior predictable and consistent with supplier offer intake UX.

## Non-goal
- No broad menu/router redesign in onboarding.
- No auto-save of half-completed onboarding drafts in this slice.

---

## 3) Telegram Admin Supplier Moderation Workspace (Profiles, Not Offers)

## Recommended v1 entry points
- `/admin_suppliers`
- `/admin_supplier_queue` (alias acceptable)

Same access model as Y28.1:
- fail-closed Telegram allowlist gate,
- no self-enrollment or dynamic RBAC in v1.

## Workspace model
- Queue -> detail -> actions.
- Navigation: `prev / next / back / home`.

## Queue views (narrow)
- `pending_review` (primary moderation queue),
- `approved` (for governance audit and suspension/revoke actions),
- `rejected` (for audit/read-side checks),
- optional `suspended`/`revoked` views once status model is added.

## Supplier detail card (minimum useful fields)
- supplier id/code/display name,
- onboarding status + reviewed timestamps,
- legal/compliance onboarding fields currently collected,
- last moderation reason (reject/suspend/revoke reason where applicable),
- operational status summary (allowed/blocked for supplier bot actions).

## Explicit exclusion
- No supplier-offer edit/publish actions in this workspace.
- Offer moderation remains in `/admin_offers` workspace.

---

## 4) Supplier Profile Lifecycle Recommendation

## Recommended profile statuses
Use additive supplier-profile governance statuses:
- `pending_review`
- `approved`
- `rejected`
- `suspended`
- `revoked`

`reactivated` is an action, not a long-lived status (result status: `approved`).

## Action semantics
- `approve`: `pending_review` -> `approved`
- `reject` (with reason): `pending_review` -> `rejected`
- `suspend` (with reason): `approved` -> `suspended`
- `reactivate` (with reason/note): `suspended` -> `approved`
- `revoke` (with reason): `approved|suspended` -> `revoked` (terminal governance exclusion)

## Distinction: suspend vs revoke
- `suspend`: temporary operational block, reversible.
- `revoke`: long-term/terminal exclusion, no direct self-recovery in supplier bot flow.

---

## 5) Operational Consequences By Supplier Status

## `pending_review`
- `/supplier`: onboarding state messaging and resubmission flow as already accepted.
- `/supplier_offer`: blocked.
- `/supplier_offers`: blocked (or minimal gate message only).
- Admin offer publish/approve/reject still possible only if policy explicitly allows legacy edge cases; recommended to block new publication.

## `approved`
- Supplier operational entry allowed.
- `/supplier_offer` and `/supplier_offers` allowed.
- Offer moderation/publication flow works per existing offer lifecycle rules.

## `rejected`
- Supplier operational offer access blocked.
- `/supplier` allows correction/resubmission.
- Existing offers remain in DB/history; no physical deletion.
- No new publication actions for this supplier.

## `suspended`
- Supplier bot operating access blocked (`/supplier_offer`, `/supplier_offers` blocked).
- Existing draft editing blocked while suspended.
- Admin must not publish offers for suspended supplier.
- Published offers should be policy-retracted from active visibility (see section 6).

## `revoked`
- Supplier bot operating access blocked.
- No onboarding self-recovery path; requires explicit admin governance action (outside v1 bot self-service).
- All publication eligibility blocked.
- Published offers policy-retracted from active visibility.
- Data retained for audit/history.

---

## 6) Offer And Public Visibility Effects (When Supplier Is Excluded)

User requirement accepted: excluded/revoked supplier offers must be removed from active bot/channel visibility.

## Recommended safe model
Use policy-driven operational retraction and publication blocking, not deletes:
- No physical delete of supplier or offers.
- Keep full audit/history.

## Effects by offer state when supplier becomes `suspended` or `revoked`
- `draft`: retained; blocked from further supplier edits while excluded.
- `ready_for_moderation`: retained; blocked from moderation progression until supplier returns to `approved`.
- `approved` (unpublished): retained; blocked from publish while excluded.
- `published`: operationally retracted (best-effort channel delete, lifecycle moved to non-published state by existing retract semantics).

## Reactivation policy
- Do not auto-republish previously retracted offers.
- After supplier returns to `approved`, publication remains explicit manual admin action.

This preserves `approve != publish` and avoids hidden reactivation side effects.

---

## 7) Relationship Between Supplier Moderation And Offer Moderation

## Gate rules
- Supplier profile status gates what offer actions are allowed.
- Offer lifecycle still governs offer-specific steps.

## Recommended gating matrix
- Supplier not `approved` => supplier cannot create new offers.
- Supplier not `approved` => supplier cannot edit drafts.
- Supplier not `approved` => admin publish action for that supplier's offers must fail-closed.
- Supplier transitions to `suspended|revoked` => trigger policy retraction for currently published offers.
- Supplier returns to `approved` => offers remain retained, but publication is manual (no auto-restore).

---

## 8) Backward Compatibility And Migration Stance

## Principles
- Additive change only.
- Keep legacy already-approved suppliers operationally compatible by default.
- Do not retroactively force destructive cleanup.

## Recommended compatibility approach
- Existing approved suppliers map to `approved` profile status.
- New profile statuses (`suspended`, `revoked`) are opt-in governance actions by admin.
- Existing offer lifecycle/history remains untouched unless policy action requires retraction of currently published visibility.
- Legal/compliance compatibility nuance remains as previously accepted:
  - pending approval path enforces legal completeness,
  - legacy approved rows can remain as-is until explicitly reviewed.

---

## 9) Safest Implementation Sequence (Post-Design)

1. **Y29.1** `/supplier` onboarding navigation polish:
   - add `Inapoi`/`Acasa` behavior with strict FSM safety.
2. **Y29.2** supplier profile status model (additive):
   - introduce `suspended`/`revoked` profile governance statuses and reason fields.
3. **Y29.3** Telegram admin supplier moderation workspace:
   - `/admin_suppliers` queue/detail/actions (approve/reject/suspend/reactivate/revoke).
4. **Y29.4** policy gating integration:
   - enforce supplier-profile gates on `/supplier_offer`, `/supplier_offers`, and admin publish action.
5. **Y29.5** exclusion visibility policy:
   - on suspend/revoke, operationally retract currently published offers (best-effort channel cleanup, no delete).
6. **Y29.6** focused safety tests + docs sync:
   - gating correctness, no cross-domain semantic leakage, explicit audit retention.

---

## 10) Postponed Items / Non-Goals

- Broad supplier/org RBAC redesign.
- Supplier legal/commercial profile editing UI redesign in Telegram.
- Mass supplier moderation actions.
- Automatic republish on reactivation.
- Hard-delete/compliance purge workflows.
- Analytics/finance supplier governance dashboard expansion.
- Any Layer A booking/payment or RFQ/bridge/payment-entry/reconciliation redesign.

---

## Compatibility Notes

- Preserves strict separation: supplier profile governance vs supplier offer moderation/publication.
- Preserves existing offer lifecycle semantics (`approve != publish`, manual publication control).
- Preserves Layer A and RFQ/payment boundaries.
- Meets exclusion requirement using policy-driven retraction/blocking with full history retention.

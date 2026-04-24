# Phase 7.1 Sales Mode / Full Bus Review Gate

## Purpose
- Design/review checkpoint before any new runtime implementation in Phase 7.1 sales-mode continuation.
- Scope is architecture and sequencing only; no code/migration/API contract changes in this gate.

## 1) Current Sales Mode Implementation State
- Phase 7.1 is active as a separate sub-track from closed Phase 7 `grp_followup_*`.
- `tour.sales_mode` is the commercial source of truth (`per_seat` / `full_bus`).
- `TourSalesModePolicyService` is the single backend interpretation layer for sales-mode behavior.
- Mini App and private bot consume policy read-side outputs; UI is not allowed to invent commercial rules.

## 2) What Is Already Done For `per_seat`
- Existing Layer A per-seat reservation and payment path remains the baseline.
- Catalog/detail/preparation/payment-entry/booking-status user journey is preserved and production-validated.
- Payment flow still uses existing Layer A services (`TemporaryReservationService`, `PaymentEntryService`, reconciliation path).

## 3) What Is Already Done For `full_bus`
- Mode-2 catalog whole-bus line (tracks 5g.4a-5g.4e + follow-ups) is implemented in narrow accepted scope.
- Accepted behavior:
  - whole-bus path is policy-governed;
  - existing Layer A order/payment stack is reused where actionability allows;
  - user-facing read-side labels and flow continuity are stabilized.

## 4) Current `full_bus` Policy Posture: Allowed vs Blocked vs Assisted
- **Allowed (narrow accepted surface):**
  - catalog whole-bus self-service only in accepted constrained Mode-2 conditions (existing 5g.4 scope).
- **Blocked/assisted-only (by design):**
  - RFQ/bridge execution paths where policy disallows self-service (explicit assisted handling; no forced checkout).
- **Not auto-approved globally:**
  - broader direct whole-bus self-service beyond accepted 5g.4 surface remains gated by explicit Phase 7.1 Step-6/Track-6 product decision.

## 5) How `sales_mode` Affects Mini App Actionability
- Mini App actionability must come from current backend truth, not publication hints or UI heuristics.
- `visibility != bookability` remains mandatory:
  - visible items can exist while self-service booking is unavailable.
- Actionability decisions must remain policy + runtime-state based and fail-safe.

## 6) Interaction With `supplier_offer_execution_links`
- `supplier_offer` and `tour` remain separate entities (`supplier_offer != tour`).
- Supplier/public visibility does not directly grant executable Layer A actions.
- Authoritative conversion to execution requires explicit linkage (`supplier_offer_execution_links`) and current actionability truth.
- Sales-mode continuation must preserve this boundary: linkage controls execution context; sales-mode policy controls allowed customer actions inside that context.

## 7) What Remains Postponed
- Any broad Layer A booking/payment redesign.
- Any RFQ/bridge semantics redesign.
- Any merge of supplier offer lifecycle and Layer A tour lifecycle.
- Any reopening of identity bridge work without concrete runtime regression evidence.
- Any coupon/incident automation or broad operational automation before explicit design gate.

## 8) Next Safe Implementation Slice (After This Gate)
- **Safe next slice:** Phase 7.1 continuation as a narrow, backend-policy-first/read-side-first increment:
  - formalize/update sales-mode/full-bus decision matrix for all relevant customer entry surfaces;
  - align Mini App actionability contracts to that matrix without changing Layer A payment/reconciliation semantics;
  - add admin/ops read-side visibility needed to reason about bookings/requests across users (separate from user-scoped screens).
- **Out of scope for immediate next slice:**
  - broad runtime refactor,
  - new booking/payment semantics,
  - cross-domain coupling between supplier publication and Layer A execution without explicit authoritative linkage.

## Guardrails (Must Stay True)
- Preserve Layer A booking/payment core and existing per-seat flow.
- Preserve existing payment-entry flow.
- Preserve Mini App execution truth and `visibility != bookability`.
- Preserve `supplier_offer != tour`.
- Preserve fail-closed identity model.

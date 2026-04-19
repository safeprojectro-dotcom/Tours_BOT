# Y2 — Supplier Telegram Operating Model (Design Gate)

## Status
- Design/architecture decision document.
- No backend/frontend behavior changes in this step.
- Preserves existing Layer A, RFQ bridge, moderation/publication, and payment semantics.

## Context
Current platform already has:
- Supplier foundation and credentials (`suppliers`, `supplier_api_credentials`).
- Supplier offer lifecycle with moderation/publication.
- Supplier RFQ request visibility and response workflow clarity (X1/X2).
- Customer and admin operational surfaces (U/V/W/A tracks).

What is still missing is a practical supplier-first operating model in Telegram.

## Guardrails (non-negotiable)
- **Layer A remains source of truth** for booking/order/payment facts.
- Supplier Telegram intake must not bypass moderation/publication.
- Mode 2 (published/catolog offer operations) and Mode 3 (RFQ/custom requests) remain separate domains.
- Supplier visibility must default to non-PII aggregated read-side.
- No implied payment readiness, customer completion, or delivery evidence beyond existing truth.

---

## 1) Recommended supplier identity/access model (v1)

## Decision
Use **supplier entity + one primary Telegram-bound operator** in v1.

- Keep existing supplier entity model as the account anchor.
- Add Telegram as the practical access anchor for supplier operations.
- v1 operational assumption: one primary Telegram user per supplier.
- Keep future multi-operator support as postponed (do not build org/RBAC platform now).

## Why this model
- Matches real operating behavior (suppliers work in Telegram).
- Minimizes auth complexity while preserving current supplier boundaries.
- Avoids introducing a broad organization/roles subsystem prematurely.

## v1 access rules
- Supplier bot actions are allowed only for Telegram users bound to an approved supplier.
- Unbound users can start onboarding but cannot act as operational suppliers until admin approval.
- Existing supplier API credential model remains valid and unchanged for current `/supplier-admin/*` routes.

---

## 2) Recommended Telegram onboarding model (v1)

## Decision
Introduce a narrow supplier onboarding FSM in Telegram that creates a moderation-gated supplier onboarding record (or draft supplier profile), then requires admin approval before operational use.

## v1 onboarding data collection
- Supplier/company display name.
- Legal/company name (or legal identifier placeholder if applicable by market).
- Primary contact phone and Telegram username/handle.
- Operating region (free text + normalized shortlist where possible).
- Service composition and commercial capability declarations already aligned with existing offer domain enums.
- Optional short fleet summary (text) and optional photo set (postponed for strict validation workflows).

## Approval gate
- Onboarding submission status: `pending_admin_review`.
- Supplier becomes operational only after explicit admin approval.
- Admin approval binds supplier to the submitting Telegram user as primary operator (v1).

## Postponed in onboarding
- Full KYC/legal verification workflow.
- Multi-operator organization membership and delegated permissions.
- Rich document pipeline / storage lifecycle management.

---

## 3) Recommended supplier offer submission through Telegram

## Decision
Supplier bot offer intake should map to the **existing supplier offer domain** and moderation lifecycle:
- Create/update **draft** offers.
- Explicitly submit draft as **ready_for_moderation**.
- Never publish directly from supplier bot flow.

## Telegram offer FSM (v1)
Collect fields already aligned with supplier offer model:
- Title/route summary and description.
- Departure date/time (and optional return).
- Media references (same handling limits as current platform).
- Sales mode declaration (`per_seat` vs allowed full-bus declarations under current policy).
- Payment mode declaration compatible with existing enums.
- Basic restrictions/conditions text.

## Mapping to existing pipeline
- Save as supplier-owned `draft`.
- Supplier action “submit for moderation” transitions to `ready_for_moderation`.
- Admin moderation/publish remains unchanged (`approved`/`rejected`/`published` flow).

## Explicit non-goals
- No direct creation of live Layer A tours from supplier bot intake.
- No bypass of admin moderation/publish steps.

---

## 4) Recommended supplier visibility model

Keep two separate sections in supplier surfaces:
- **Mode 2 operations visibility** (published/catalog side).
- **Mode 3 RFQ visibility** (custom requests and responses).

## 4A. Mode 2 published-tour operations visibility (supplier-safe read side)

## Decision
Expose only aggregated, non-PII operational metrics, and only when a safe offer-to-operational-context mapping exists.

## v1 visibility candidates
- Published status and publication timestamps/message linkage (already available from supplier offer lifecycle).
- Aggregate counts from Layer A read-side where mapping is explicit:
  - Seats sold count.
  - Seats remaining.
  - Active temporary holds count.
  - Confirmed bookings count.
  - Load factor percentage.

## Privacy defaults
- No customer names, phone numbers, Telegram IDs, payment identifiers, or booking-level personal details by default.
- No raw payment row visibility to suppliers.

## Important caveat
- If an offer is not explicitly mapped to a concrete operational tour context, show lifecycle-only data and mark operational metrics as unavailable.

## 4B. Mode 3 RFQ visibility (supplier request domain)

## Decision
Continue using current supplier RFQ domain model and X1/X2 clarity:
- Open requests visible per current eligibility/routing rules.
- Supplier’s own response state visible.
- Selection/read-only closure status visible where already modeled.
- No admin-internal only fields leakage.

## Scope boundaries
- Do not collapse RFQ state with published-trip operational metrics.
- Keep RFQ history visibility limited to supplier-relevant record fields already present or explicitly allowlisted.

---

## 5) Recommended supplier notification model (Telegram)

## Decision
Start with low-risk lifecycle notifications that mirror existing domain events and avoid implying new ownership semantics.

## v1 notification events
- Onboarding submitted / approved / rejected.
- Offer submitted for moderation.
- Offer approved.
- Offer rejected (with moderation reason summary if available).
- Offer published.
- RFQ response selected (supplier-visible, if already represented in current truth).

## Optional later (postponed)
- High-frequency operational booking updates (holds/bookings deltas) until noise policy and throttling are defined.
- Complex digests, escalation routing, and role-based notification preferences.

## Safety note
- Notification copy must remain factual to existing state.
- No notification should imply payment settlement, customer completion, or outcomes not evidenced by existing services.

---

## 6) Minimal safe implementation order (post-design)

1. **Y2.1 Identity binding + onboarding gate**
   - Telegram supplier onboarding FSM (pending review).
   - Admin approve/reject onboarding.
   - Bind approved supplier to primary Telegram user.

2. **Y2.2 Supplier offer intake via Telegram**
   - Draft creation/edit in bot flow.
   - Explicit submit to `ready_for_moderation`.
   - No publish from supplier bot.

3. **Y2.3 Supplier read-side workspace split by domain**
   - Mode 2 section: lifecycle + safe aggregate operational metrics (only where mapping exists).
   - Mode 3 section: RFQ visibility via existing X1/X2 truth.

4. **Y2.4 Supplier Telegram notifications (narrow lifecycle set)**
   - Onboarding and moderation lifecycle first.
   - RFQ selected notification as additive event.

---

## 7) Postponed items (explicit)
- Multi-operator supplier organizations, role hierarchy, delegated permissions.
- Broad auth platform redesign.
- Direct supplier self-publish bypass or moderation bypass.
- Layer A booking/payment semantic changes.
- RFQ bridge execution semantic changes.
- Payment-entry/reconciliation semantic changes.
- Full supplier portal rewrite.

## Continuity note
This Y2 model is a narrow operating-model design gate on top of existing architecture.  
It is not a mandate to redesign marketplace, admin, booking, payment, or RFQ core semantics.

# Telegram Admin Moderation Workspace Design (Y28)

## Status
- Design-only block.
- No runtime changes in this step.
- No migration/test changes in this step.

## Purpose
Define a narrow Telegram admin moderation/publication workspace v1 on top of existing admin/service truth:
- supplier offer moderation lifecycle already implemented,
- approve/reject/publish/retract already implemented,
- execution-link persistence already implemented,
- admin is moderator/publisher, not content editor.

---

## 1) Admin Identity / Access Model (Fail-Closed)

## Decision
Use a narrow dual gate for Telegram admin workspace v1:
1. **Telegram admin allowlist** (`telegram_user_id` explicit allowlist).
2. **Existing admin API trust boundary** remains source of permission truth for actions.

## Recommended v1 mechanics
- Add a dedicated admin allowlist configuration (example: `TELEGRAM_ADMIN_ALLOWLIST_IDS`).
- Telegram command handler checks:
  - user id present in allowlist,
  - otherwise returns safe deny message and exits.
- No dynamic self-enrollment in bot.
- No role editor in Telegram workspace v1.

## Why
- Simple and explicit.
- Operationally safe for mobile-first moderation.
- No RBAC platform expansion in this step.

---

## 2) Entry Point / Command Model

## Decision
Use two narrow commands:
- **`/admin_ops`**: admin workspace home (status + quick actions).
- **`/admin_offers`**: moderation queue entry.

Optional narrow alias:
- `/admin_queue` -> same as `/admin_offers`.

## Not in v1
- No broad command tree.
- No command-driven editing actions.

---

## 3) Workspace Model (Queue -> Detail -> Actions)

## Queue view (list)
Show compact moderation queue rows from existing admin truth:
- offer id,
- lifecycle status,
- supplier display summary,
- title snippet,
- updated_at,
- published/retracted marker,
- linkage summary marker (linked/unlinked; no deep analytics here).

Queue filters (narrow):
- `ready_for_moderation`
- `approved`
- `published`
- `rejected` (for re-review after resubmission visibility)

## Detail card
For selected offer show:
- supplier summary (code/display name),
- lifecycle + moderation reason (if rejected),
- publication fields (`published_at`, `showcase_message_id`),
- content summary (title/description/program/departure/return/capacity/price/currency),
- execution-link summary (active link present? linked tour id),
- timestamps.

## Navigation
- inline buttons:
  - `Prev`, `Next`, `Back to queue`, `Home`.
- keep single-focus operator flow:
  - scan list -> open detail -> action -> next item.

---

## 4) Moderation / Publication Actions In Telegram v1

## Allowed actions (must map to existing backend actions)
- `Approve`
- `Reject` (with reason)
- `Publish`
- `Retract`

## Preserved behavior
- **approve != publish** remains mandatory.
- publish allowed only when backend already allows it.
- retract allowed only when backend already allows it.
- Telegram workspace only triggers existing service/API paths; it does not redefine lifecycle.

## Explicitly disallowed
- Admin content edits.
- Admin supplier-authored field rewrites.

---

## 5) Supplier Rework Loop (Return For Rework)

## Decision
Reuse current lifecycle semantics:
- `reject + reason` is the v1 rework mechanism.

## Operational loop
1. Supplier submits offer (`ready_for_moderation`).
2. Admin rejects with concrete reason in Telegram workspace.
3. Supplier sees reject reason in existing supplier workspace.
4. Supplier edits and resubmits through existing supplier flow.
5. Admin re-reviews from queue.

## Future refinement (postponed)
- Dedicated `changes_requested` lifecycle state may be evaluated later, but is **not** introduced in v1.

---

## 6) Admin Read-Side Data Boundaries (Telegram v1)

## Admin can see
- Supplier identity summary relevant for moderation (display name/code).
- Offer content summary as submitted by supplier.
- Lifecycle + reject reason.
- Publication status and channel message metadata.
- Narrow execution-link status summary (linked/unlinked + tour id where linked).

## Admin should not see in this workspace
- Full order/payment control surfaces.
- RFQ admin workspace concerns.
- Broad analytics/finance views.
- Unrelated admin portal data.

---

## 7) Hard Prohibitions In Telegram Admin Workspace v1

- No editing supplier-authored content.
- No editing supplier legal/compliance records.
- No direct mutation of booking/payment/order semantics.
- No customer data expansion beyond existing allowed boundaries.
- No broad admin portal replacement behavior.

---

## 8) Publication Behavior (Reinforced)

- Publication still uses existing publication truth/service.
- Telegram admin workspace is an operational client layer only.
- Approve/publish/retract semantics remain exactly as already implemented.
- No shortcut that auto-publishes on approve.

---

## 9) Future Items Explicitly Postponed

- Scheduled publish.
- Content editing in admin workspace.
- Mass moderation/bulk actions.
- RFQ Telegram admin workspace.
- Order/payment admin controls in Telegram.
- Analytics/finance dashboard.
- Full portal replacement / broad RBAC redesign.

---

## 10) Recommended Narrow Implementation Sequence

1. Add Telegram admin access gate (allowlisted IDs, fail-closed).
2. Add `/admin_ops` and `/admin_offers` entry handlers.
3. Implement queue rendering via existing admin supplier-offer read endpoints.
4. Implement detail card rendering.
5. Wire action buttons to existing approve/reject/publish/retract endpoints.
6. Add reject-reason capture UX (minimal text step + confirm).
7. Add safe navigation (`next/prev/back/home`) and idempotent action feedback.
8. Add focused tests:
   - access gate fail-closed,
   - action availability by lifecycle,
   - no edit path exists,
   - approve/publish separation preserved.

---

## Compatibility Notes

- Preserves Layer A booking/payment semantics.
- Preserves RFQ/bridge semantics.
- Preserves payment-entry/reconciliation semantics.
- Preserves supplier-authored content ownership boundary.
- Reuses existing admin/service truth; no shadow moderation model.

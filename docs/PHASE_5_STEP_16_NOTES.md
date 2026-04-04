# Phase 5 / Step 16 — Minimal handoff operator actions

## Status model (no migration)

`handoffs.status` is a `String(32)` column (no PostgreSQL enum). Convention for this step:

| Status | Meaning |
|--------|---------|
| `open` | New request (created by private chat / Mini App). Listed on `GET /internal/ops/handoffs/open`. |
| `in_review` | Claimed by ops (`PATCH .../claim`). No longer in the open queue. |
| `closed` | Resolved (`PATCH .../close`). Not in the open queue. |

Other values are not used by this slice; future phases may add more.

## Internal API (same auth as Step 15)

Requires `OPS_QUEUE_TOKEN` via `Authorization: Bearer …` or `X-Ops-Token`.

| Method | Path | Body | Effect |
|--------|------|------|--------|
| PATCH | `/internal/ops/handoffs/{id}/claim` | `{ "operator_id": <int optional> }` | If status is `open`: set `in_review`, set `assigned_operator_id` when `operator_id` is provided. |
| PATCH | `/internal/ops/handoffs/{id}/close` | `{ "operator_id": <int optional> }` | If status is not `closed`: set `closed`; optional `assigned_operator_id` when `operator_id` is sent. |

**Claim**

- Allowed only when `status == open`.
- If `operator_id` is set, it must exist in `users.id` (otherwise **400** `invalid_operator_id`).
- If status is not `open` (**409**): `{"code":"handoff_not_open","current_status":"..."}`.
- Missing handoff: **404** `handoff_not_found`.

**Close**

- Allowed when status is `open` or `in_review` (not already `closed`).
- Second close: **409** `{"code":"handoff_already_closed","current_status":"closed"}`.
- Optional `operator_id` on close updates `assigned_operator_id` (e.g. who closed the case).

**No side effects:** no notifications, no order/booking/payment/waitlist mutations.

## Manual checklist (Step 16)

1. Insert or create a handoff with `status=open`.
2. `GET /internal/ops/handoffs/open` — row visible.
3. `PATCH .../claim` with optional `operator_id` — response `status=in_review`, open queue empty for that row.
4. Repeat `PATCH .../claim` — **409**.
5. `PATCH .../close` — `status=closed`.
6. `GET /internal/ops/handoffs/open` — row not listed.
7. Confirm Mini App / private bot flows unchanged.

## Out of scope

- Waitlist mutations are covered in **Phase 5 / Step 17** (`docs/PHASE_5_STEP_17_NOTES.md`).
- Operator roles, SSO, admin UI.
- Telegram notifications to users or operators.
- Order-level `assigned_operator_id` and full CRM workflows.

# Operator Workflow Gate (Custom Marketplace Requests / RFQ)

**Phase:** Y37.1 (docs-only design gate)  
**Depends on:**  
- [`docs/OPERATOR_ASSIGNMENT_GATE.md`](OPERATOR_ASSIGNMENT_GATE.md) (assignment model)  
- **Y36.2–Y36.5** accepted: assign-to-me, ORM fix, Telegram owner UI, docs acceptance  
- **Y36.6** accepted: admin Telegram **Travel date** read-only formatting (no workflow semantics)

**Accepted input state (Y37.1 builds on this):**

- **Assign to me** works and is **stable** (Y36.2+).
- **Owner** is **`users.id`** on `assigned_operator_id` / `assigned_by_user_id` (not a raw Telegram id in FK columns).
- **Assignment does not change** `CustomMarketplaceRequest.status` (ownership/triage only).

**Next safe runtime slice after this gate (Y37.2+; not in Y37.1):**

- **Only** the first narrow workflow action: **Mark as under review** / **Start handling** (conceptually: `open` → `under_review`), and **only** for requests **assigned to the current operator** (actor).
- **Out of scope** for that first slice: **resolve**, **close**, **reassign**, **unassign**, **internal note**, and any other operator workflow — each **later**, behind its own explicit gate/iteration if added.

This gate designs the **next safe operator workflow layer** after **assignment**: moving a request through **operational handling** using existing **lifecycle status** where possible, without conflating **owner** (`assigned_operator_id`) with **status** semantics.

**Scope:** **Custom marketplace requests only** (Layer C RFQ). **Not** Mini App customer surfaces, **not** supplier routes, **not** booking/payment execution, **not** `custom_request_booking_bridges` mutations, **not** execution links, **not** identity bridge.

**This document does not add** runtime code, migrations, API routes, or Telegram handlers.

---

## 1. Current accepted state (post–Y36 MVP)

| Area | Truth |
|------|--------|
| **Visibility** | Admin can list/detail custom requests (Y35.2/Y35.3 + admin API). |
| **Assignment** | Operator can **Assign to me**; `assigned_operator_id` / `assigned_by_user_id` store **`users.id`**; assignment is **ownership / triage only**. |
| **Lifecycle** | **Y36 does not change** `CustomMarketplaceRequest.status` when assigning. |
| **ORM** | Symmetric `User` ↔ `CustomMarketplaceRequest` relationships (Y36.2A); mapper smoke test exists. |
| **Telegram** | Owner line, compact list, **Assign to me** hidden when already assigned (Y36.4). |
| **Dates** | Detail **Travel date** line uses safe formatting (Y36.6). |

---

## 2. Workflow goal

Enable an **assigned** operator to perform **safe, explicit** workflow steps that update **RFQ lifecycle status** (or derived admin state) in a controlled way—**after** they own the row—so ops can signal “I am handling this” without mixing that signal with **who** is assigned.

**Principle:** **Assignment** answers *who*; **status** answers *where the case is* in the product lifecycle (open, under review, supplier selected, closed, etc.).

---

## 3. Status model options

**Reuse** existing [`CustomMarketplaceRequestStatus`](../app/models/enums.py) where possible:

| Value | Role in workflow (conceptual) |
|-------|---------------------------------|
| `open` | Default customer-facing “open” RFQ. |
| `under_review` | Internal / operator **handling in progress** (suppliers may still be engaging per existing rules). |
| `supplier_selected`, `closed_assisted`, `closed_external`, `cancelled` | **Commercial / terminal** paths — already governed by resolution flows; **not** the first workflow button target without a separate gate. |
| `fulfilled` | Legacy; treat as read-only / migrated per Track 5a. |

**New enum values** are **not required** for the first workflow slice if **`under_review`** is accepted as the “start handling / mark in progress” state.

**Do not** encode “assigned vs unassigned” as a **status** value; that remains **`assigned_operator_id` NULL vs non-NULL** ([`OPERATOR_ASSIGNMENT_GATE.md`](OPERATOR_ASSIGNMENT_GATE.md)).

**Later (optional product):** separate **operational** flags or admin-only labels (e.g. *waiting on supplier*) would need their **own** gate to avoid duplicating `status`.

---

## 4. First safe workflow action (recommended implementation slice)

**Action (conceptual name):** **Mark as under review** / **Start handling**

**Effect:** If allowed, set `CustomMarketplaceRequest.status` → **`under_review`** (idempotent if already `under_review`).

**Preconditions (all required):**

1. Request is **assigned** to the **current actor** (`assigned_operator_id == actor_user.id`).  
2. Current status is **`open`** (or as narrowly agreed: only from `open` in v1; do not sweep from other states without analysis).  
3. Request is **not** in a **terminal** / **non-workflow** bucket for this action (see §7).

**Rationale:** Matches existing enum; aligns with “operator has taken ownership and is now actively handling” without inventing a parallel “in_progress” status in v1.

---

## 5. Future actions (postponed — separate gates)

| Action | Notes |
|--------|--------|
| **Resolve** / **close** (admin) | Overlaps `POST .../resolution`, `PATCH` rules, terminal statuses — **separate** gate. |
| **Reassign** | Changes `assigned_operator_id` — **separate** gate (see [`OPERATOR_ASSIGNMENT_GATE.md`](OPERATOR_ASSIGNMENT_GATE.md)). |
| **Unassign** | Clears assignment — **separate** gate. |
| **Internal note** | May be `admin_intervention_note` or additive audit — **separate** gate. |

No implied ordering beyond: **first** ship **mark under review**; then re-open this document or add **Y37.x** addenda.

---

## 6. Permissions

| Actor | Custom requests |
|-------|-------------------|
| **Admin API** (`ADMIN_API_TOKEN`) | Full read; workflow mutations as implemented per service rules. |
| **Telegram** | Allowlisted admin/operator (same as Y35.3 / Y36); **no** PII in `callback_data`. |
| **Customer Mini App** | Stays **user-scoped**; **no** all-requests visibility; unchanged. |
| **Supplier** | Unchanged; supplier-admin RFQ routes unchanged. |

---

## 7. Fail-safe rules (must hold in implementation)

1. **Unassigned** request: **no** workflow mutation that changes **status** from this action (reject with 403/400 as per API style).  
2. **Assigned to another operator:** actor **not** the assignee → **reject** (same as Y36 assign conflict family).  
3. **Terminal / closed / cancelled / supplier already selected** (as defined for the slice): **block** (no side effects on booking/payment/bridge).  
4. **No** automatic creates/updates to **`orders`**, **`payments`**, or **bridge** rows from this action.  
5. **Idempotency:** e.g. `open` → `under_review` twice = success / no-op; define explicitly in the implementation ticket.  
6. **Auditing (optional in v1):** `updated_at` and existing fields only unless a follow-up adds audit rows.

---

## 8. Telegram UI concept (target)

- **Detail** already shows **Owner** and **Status**; keep both visible.  
- **Button** (e.g. “Start handling” / “Mark under review”): **only** when: allowlisted, request **assigned to me**, status **`open`**, and not blocked by §7.  
- **Callback_data:** **compact**, numeric `request_id` + **page** if needed (same 64-byte discipline as Y36); **no** names, phones, or free text in callbacks.  
- **After success:** refresh detail; hide button if status is no longer `open` (or show disabled / message—product choice in implementation).  
- **Unassigned** or **other owner:** **no** workflow button (or show short disabled reason in copy—product choice).

---

## 9. API concept (first slice)

**Narrow admin endpoint (example only — naming can vary):**

`POST /admin/custom-requests/{request_id}/mark-under-review`

- **Auth:** same **admin** auth as other `/admin/custom-requests/*` routes.  
- **Actor (Telegram alignment):** reuse **Y36** pattern: header **`X-Admin-Actor-Telegram-Id`** (or project-standard equivalent) resolving to `User.id` for “who is acting”; require **actor == assigned_operator** for this action.  
- **Response:** updated read DTO for the request (same family as `GET` admin detail or list read).  
- **Errors:** 404 (not found), 403/409/400 for guards in §7 (map to project conventions).  
- **No** semantic change to existing **assign-to-me** endpoint.

---

## 10. Tests required (acceptance for a future implementation PR)

| # | Case |
|---|------|
| 1 | **Success:** `open` + assigned to me → `under_review`; response reflects new status. |
| 2 | **Blocked:** unassigned → error; status unchanged. |
| 3 | **Blocked:** assigned to **another** operator → error; status unchanged. |
| 4 | **Blocked:** terminal/closed/cancelled (slice-defined) → error. |
| 5 | **Telegram:** button **visible** only when preconditions pass; **hidden** or absent otherwise. |
| 6 | **Mini App regression:** `GET /mini-app/custom-requests*`, identity scoping **unchanged** (smoke or existing tests). |
| 7 | **Supplier / booking / payment:** no new writes to supplier-offer, order, or payment services from this path (grep / integration guard). |
| 8 | **Callback** length ≤ 64 bytes for new callback if any. |

---

## 11. Out of scope (explicit)

- Reassign, unassign, resolve, close, new migrations (unless a later change **requires** a column—this gate does **not** add columns).  
- Mini App, bot customer flows, execution links, payment entry, bridge execution.  
- Broadening `under_review` semantics for supplier `PUT` rules—coordinate with existing [`CustomMarketplaceRequestService`](../app/services/custom_marketplace_request_service.py) and admin resolution contracts.

---

## 12. Summary

| Item | Choice |
|------|--------|
| **First action** | `open` → `under_review` when **assigned to actor** |
| **Status enum** | Reuse `under_review` |
| **Assignment** | Unchanged; orthogonal to status |
| **Next implementation** | Separate Y37.2+ runtime ticket after this gate is accepted |

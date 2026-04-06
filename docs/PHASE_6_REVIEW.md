# Phase 6 review — post Step 30 (documentation checkpoint)

**Date role:** stabilization / alignment document — **not** an implementation slice.  
**Approved code checkpoint:** **Phase 6 / Step 30 completed**.

---

## 1. Current approved checkpoint

| Field | Value |
|--------|--------|
| Checkpoint | **Phase 6 / Step 30 completed** |
| Last admin read extension | **`move_placement_snapshot`** on **`GET /admin/orders/{order_id}`** (current placement only; **`timeline_available: false`**) |
| Companion mutation | **Phase 6 / Step 29** — **`POST /admin/orders/{order_id}/move`** (narrow; no payment-row writes) |

---

## 2. What Phase 6 already covers (fact)

Aligned with **`docs/CHAT_HANDOFF.md`** Completed Steps — **Steps 1–30**:

- **Foundation:** **`ADMIN_API_TOKEN`**, protected **`/admin/*`** (overview, lists, detail reads).
- **Tours:** narrow create/core patch/cover/archive-unarchive; **boarding** narrow CRUD; **tour + boarding translations** (per-language upsert/delete).
- **Orders (read):** payment **correction visibility** (Step 16), **action preview** (Step 17), **lifecycle** incl. **`ready_for_departure_paid`** (Step 27), **move-readiness** (Step 28), **move placement snapshot** (Step 30).
- **Orders (write, narrow):** mark-cancelled-by-operator, mark-duplicate, mark-no-show, mark-ready-for-departure, **move** (Step 29).
- **Handoffs:** queue/detail read; **mark-in-review**, **close**, **assign**, **reopen**.

**Explicit boundary:** Customer **public** booking / payment / waitlist / handoff **entry** flows were **not** redesigned by these admin slices; they stay as in Phase 5 acceptance.

---

## 3. Alignment with `docs/IMPLEMENTATION_PLAN.md` (Phase 6)

The plan’s **Phase 6** block lists a **broad** admin surface (publication approval visibility, notification history, audit logging, role separation beyond a single token, etc.). **Implemented to date** is a **deliberately narrow, API-first** admin track (see **`docs/CHAT_HANDOFF.md`**) rather than the full checklist in one go.

| Plan theme | Status in repo (high level) |
|------------|-----------------------------|
| Protected admin API + auth baseline | **Done** (Bearer / `X-Admin-Token` style) |
| Tour + boarding + translations | **Done** (narrow slices) |
| Order list/detail + filters + restricted updates | **Done** (narrow mutations + rich read model) |
| Handoff list + assignment/resolve-style flows | **Done** (narrow; **no unassign**) |
| Publication approval / content pipeline visibility | **Not** in Phase 6 Steps 1–30 — **postponed** |
| Notification history / broad audit log | **Not** in Steps 1–30 — **postponed** |
| Multi-role RBAC beyond single admin token | **Not** implemented — **postponed** |

**Conclusion:** The **narrow Phase 6 track** is **coherent and sufficient for staging operations** (tour ops, order oversight, handoff queue) **as implemented**. The **full** `IMPLEMENTATION_PLAN.md` Phase 6 **paragraph** still describes **future** work; that is **not** a blocker to calling this **“MVP-sufficient admin API surface for current staging goals”** if product accepts API-only ops.

---

## 4. Alignment with `docs/TECH_SPEC_TOURS_BOT.md` (§11 Admin)

The spec’s **§11** includes items (e.g. **search by user**, **full order history**, **notification history**) that are **not** fully covered by the current **`/admin/*`** API. Those gaps remain **intentionally postponed** or deferred to **later phases** (analytics, full admin UI, content assistant), not as failures of Steps 1–30.

---

## 5. Intentionally postponed (not bugs)

- **Admin payment mutations** (refund / capture / cancel-payment / forced reconciliation) — **separate design checkpoint**; **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** **§1f**.
- **Persisted** move timeline / audit rows — optional future slice.
- **Full** admin SPA, **publication** workflow visibility, **bulk** ops, **merge** tooling, **full** operator inbox + customer notifications from admin actions.
- **Multi-role** admin RBAC, **comprehensive** audit engine.

---

## 6. Must-have before “leaving” Phase 6 (operational)

For **staging**, product should **explicitly** confirm:

1. **Staging smoke** on **`/admin/*`** (auth, tours, orders, handoffs, move path) — see **`docs/CHAT_HANDOFF.md` Next Safe Step** historical checklist.
2. **Reconciliation boundary:** payment **paid-state** transitions remain **only** via existing **reconciliation** path — **no** admin mutation slice until designed.
3. **Product sign-off** that API-only admin is acceptable until a UI exists.

No **additional code** is required for this document to be “accepted”; acceptance is a **process** decision.

---

## 7. Is Phase 6 “MVP-sufficient” for admin surface **for now**?

**Yes**, for the **agreed narrow definition**: **API-first** admin with **Steps 1–30** coverage — **provided** stakeholders accept the **postponed** items in §5 and the **partial** overlap with the **full** `IMPLEMENTATION_PLAN.md` Phase 6 text (§3).

---

## 8. Recommended next direction (single choice)

**Phase 6 review accepted; prepare transition.**

- Treat **Step 30** as the **closure** of the **current** Phase 6 **narrow implementation** track.
- **Next** work is **not** defaulted to **admin payment** mutation or **Phase 6 Step 31** code — it is **product/backlog choice**: Phase **7** (group assistant / handoff at scale per plan), **content assistant**, **analytics**, or a **future** optional **narrow** admin slice (e.g. move audit) **only** after explicit approval and design.

**Admin payment mutations** remain **off** the default path until a **separate design checkpoint** (`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` **§1f**).

---

## 9. References

- `docs/CHAT_HANDOFF.md` — primary continuity  
- `docs/IMPLEMENTATION_PLAN.md` — Phase 6 broad intent vs narrow delivery  
- `docs/TECH_SPEC_TOURS_BOT.md` — §11 full admin vision vs current API  
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` — payment / reconciliation boundaries  

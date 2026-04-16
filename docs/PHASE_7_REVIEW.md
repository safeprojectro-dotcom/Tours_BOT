# Phase 7 review / closure

**Purpose:** Close the **Group Assistant And Operator Handoff** implementation track without further micro-step churn; record MVP/staging sufficiency for the **narrow** group→private→handoff→operator slice; separate **Phase 7** from the next product line.

## Current approved checkpoint

- **Phase 7 implementation** is **complete** through **Steps 1–17** plus the **final followup/operator consolidation** polish (unified private **`grp_followup`** copy, aligned admin read-side labels, focused tests).
- **Phase 7 review / closure** is **accepted** as of this document: no additional Phase 7 feature slices are assumed unless product **explicitly** rescopes.

## What Phase 7 now covers

- **Group:** trigger evaluation, minimal gating, category-aware short escalation wording, **`t.me`** deep links (`grp_private` / `grp_followup`).
- **Private:** narrow **`/start`** branching; **`/start grp_followup`** → **`handoffs`** row (**reason** **`group_followup_start`**, dedupe **open**); **`grp_private`** unchanged (no handoff write from that entry).
- **Admin / operator (narrow):** read visibility, **`assign-operator`**, **`mark-in-work`**, **`resolve-group-followup`**, queue/read-side state (**`group_followup_queue_state`**, labels), list filter.
- **Private follow-up UX:** resolved confirmation, readiness/history intros, consolidation-aligned wording and CTAs (**`/contact`** / **`/human`**, browse tours).
- **Tests:** chain tests, admin API/visibility tests, **`test_group_followup_phase7_consolidation`**.
- **Explicitly not in Phase 7:** handoff rows from **group** chat (group path remains **reply-only**); automatic assignment from Telegram **`grp_*`**; booking/payment changes via this chain.

## MVP / staging sufficiency (this chain)

For the **agreed narrow** path — **group engagement → private deep link → `group_followup_start` persistence → admin triage and narrow status progression → consistent customer copy** — Phase 7 is **MVP-sufficient** for **staging**: operators can see, assign, take in-work, resolve, and customers get consistent private messaging without new booking/payment surface area.

**Caveats (by design, not blockers for this closure):**

- No **two-way operator↔customer chat** in Telegram; no **handoff push notifications**.
- No **full** operator inbox, claim engine, or workflow product.

## What remains intentionally postponed

- **Operator chat** / free-form messaging bridged to handoffs.
- **Handoff** (and related) **push notifications** from admin or customer events.
- **Broad** assignment/claim/reassign/unassign policy redesign.
- **Full** group assistant, long-form group negotiation, handoff persistence from group messages.
- **Admin payment** mutations and other items documented in **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** (e.g. **§1f**).

## What must NOT be added inside Phase 7 without explicit rescoping

- Further **`grp_followup`** “micro-steps” (copy tweaks, extra admin fields, new mutations) **by default** — treat as **new product tickets** or a **rescoped Phase 7b**, not implicit continuation.
- **`per_seat` / `full_bus`** or tour **sales-mode** behavior **bolted into** existing Phase 7 services **ad hoc** — that belongs in a **separate design track** (schema, catalog, booking rules, admin).

## Recommended next track

- **Tour sales mode: `per_seat` / `full_bus`** — end-to-end **design first** (data model, tour configuration, seat math, admin panel, customer/Mini App implications, migrations, test strategy). **Do not** implement in the same pass as Phase 7 closure documentation.

## References

- **`docs/CHAT_HANDOFF.md`** — operational handoff, **Next Safe Step**
- **`docs/GROUP_ASSISTANT_RULES.md`** — Phase 7 Step 1 rules
- **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** — §19 and global debt
- **`docs/IMPLEMENTATION_PLAN.md`**, **`docs/TECH_SPEC_TOURS_BOT.md`**

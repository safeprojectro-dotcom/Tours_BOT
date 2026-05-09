# CURSOR_PROMPT_COMPLETE_CONVERSION_CLOSEOUT_DELIVERABLES

Continue the conversion closeout docs block.

You already created:

`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`

Now complete the remaining deliverables from:

`docs/CURSOR_PROMPT_CONVERSION_CLOSEOUT_AND_NEXT_BLOCK_GATE.md`

This is docs-only.

## Already done

- `docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`
- Cross-link added in:
  - `docs/TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`
  - `docs/CHAT_HANDOFF.md`

Do not duplicate that work.

## Required remaining deliverables

### 1. Create B10.6 bot-as-router design gate

Create:

`docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`

Must include:

- purpose;
- current B11 behavior summary;
- source-of-truth rules;
- customer-facing states:
  - published but not linked;
  - linked but not catalog-visible;
  - catalog-visible but no execution link;
  - execution-linked and bookable;
  - unavailable / assisted fallback;
- EN/RO draft copy for each state;
- what must not be exposed to customer:
  - raw enum names;
  - media review blockers;
  - internal bridge/execution wording;
- design questions:
  - should bot show explanation before opening Mini App?
  - should bot offer Open tour / Ask operator / Browse alternatives?
  - should assisted fallback be added before implementation?
- non-goals:
  - no code;
  - no Mini App changes;
  - no booking/payment changes;
  - no B11 route change in this docs step.
- recommendation:
  - implement later only after Admin/OPS visibility panel, unless product prioritizes customer routing first.

### 2. Create Admin/OPS visibility polish design

Create:

`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`

Must include:

- purpose;
- current problem:
  - operators may confuse published / linked / catalog-visible / execution-linked / bookable;
- proposed read-only status panel;
- recommended labels:
  - Showcase
  - Tour bridge
  - Catalog
  - Booking link
  - Customer action
- status examples:
  - Showcase: Published / Not published / Blocked
  - Tour bridge: Linked / Missing
  - Catalog: Listed for sale / Not listed / Blocked
  - Booking link: Active / Missing / Stale
  - Customer action: Open exact Mini App Tour / Not bookable yet / Assisted fallback
- what not to show:
  - raw enum leakage;
  - generic “active” without layer;
  - “bookable” unless Layer A can execute.
- recommended implementation slice:
  - `C2B11A_ADMIN_OPS_CONVERSION_STATUS_PANEL`
- implementation scope for future:
  - read-only;
  - review-package/admin Telegram card;
  - no mutations;
  - no Mini App;
  - no booking/payment/order changes.

### 3. Create next block recommendation

Create:

`docs/NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md`

Compare:

- Option A — Production/OPS smoke
- Option B — B10.6 Bot-as-router
- Option C — Admin/OPS visibility panel
- Option D — resume media pipeline later

Recommended order should be explicit:

1. C2B11A Admin/OPS conversion status panel
2. Production/OPS smoke
3. B10.6 Bot-as-router
4. Media pipeline later by explicit decision

Explain why:

- status panel is read-only and reduces operator mistakes;
- production smoke is safer after visibility is clear;
- bot-as-router benefits from confirmed state labels;
- media pipeline is lower immediate business value and already paused at B7.4D.

### 4. Update CHAT_HANDOFF

Update `docs/CHAT_HANDOFF.md` with a concise closeout section:

```md
## Closeout: conversion chain completed; next block gate

Completed closeout docs:
- `docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`
- `docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`
- `docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`
- `docs/NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md`

Recommended next implementation block:
- `C2B11A_ADMIN_OPS_CONVERSION_STATUS_PANEL`

Media pipeline remains paused at B7.4D.

---

## Completed (agent)

Deliverables **1–4** implemented in-repo:

- [`docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`](B10_6_BOT_AS_ROUTER_DESIGN_GATE.md)
- [`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`](ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md)
- [`docs/NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md`](NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md)
- [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) — new **Closeout** section after **Project**

Also aligned [`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`](CONVERSION_CHAIN_OPS_SMOKE_READINESS.md) §8, [`docs/HANDOFF_CONVERSION_CLOSEOUT_AND_NEXT_BLOCK_GATE_TO_NEXT_STEP.md`](HANDOFF_CONVERSION_CLOSEOUT_AND_NEXT_BLOCK_GATE_TO_NEXT_STEP.md), and [`docs/TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`](TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md) §7 with **`NEXT_BLOCK_RECOMMENDATION`**.
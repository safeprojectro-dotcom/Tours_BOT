# CURSOR_PROMPT_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT

## Context

Project: Tours_BOT.

We have completed a connected B15C chain around supplier offer showcase publish safety and exact Mini App conversion.

Recent commits:
- `37f213e feat: require exact tour CTA before supplier offer publish`
- `18278cf docs: record B15C production smoke result`
- `17ddd4c fix: open channel tour CTA through Telegram Mini App`
- `19f50da fix: guard showcase cover replacement workflow`
- `06741d fix: support direct Mini App short-name tour links`
- `a19a1ab docs: record B15C5 direct Mini App smoke result`
- `c3dda1c fix: keep admin on supplier offer after bridge actions`
- `f444a15 fix: align supplier offer publish copy with execution link order`

Production smoke evidence:
- Offer #15
- Tour #9
- Tour code `B10-SO15-460344`
- Execution link #8
- Publish attempt #6
- Showcase message #28
- CTA:
  `https://t.me/tours_tm_bot/banattours?startapp=tour_B10-SO15-460344`
- Channel `Rezervă` opened Mini App directly.
- No identity warning.
- Reservation/order #55 was created during operator smoke.
- Payment screen opened.
- Layer A behavior was unchanged.

## Goal

Create a short B15C closing checkpoint doc and update handoff/debt docs so the project has a clear stable baseline before starting B15D or another next block.

This is docs-only.

## Required docs changes

Create:
- `docs/B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md`
- `docs/HANDOFF_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT_TO_NEXT_STEP.md`
- `docs/CURSOR_PROMPT_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT.md`

Update:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Optionally update:
- `docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`
- `docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`

## Required content

The checkpoint doc must include:

1. What B15C solved:
   - exact tour CTA before publish;
   - execution link before publish;
   - direct Telegram Mini App short-name link;
   - cover/photo sendability guard;
   - admin stays on offer after bridge/catalog actions;
   - misleading copy fixed.

2. Final accepted conversion chain:
   - supplier offer package/moderation approved;
   - create/link tour bridge;
   - activate tour for catalog;
   - create active execution link;
   - publish showcase;
   - channel Rezervă opens exact Mini App tour;
   - Mini App uses Layer A for reservation/payment.

3. Production evidence:
   - Offer #15;
   - Tour #9;
   - Tour code `B10-SO15-460344`;
   - execution link #8;
   - publish attempt #6;
   - message #28;
   - temp hold/order #55.

4. Safety boundaries preserved:
   - no hidden bridge;
   - no publish without exact conversion target;
   - no supplier-side publish;
   - no Layer A changes;
   - no arbitrary identity trust;
   - no fake availability/urgency.

5. Known follow-ups:
   - optional Detalii behavior decision;
   - RO copy/typo cleanup;
   - B15D Admin Publishing Console deeper polish;
   - B12/B13 template/channel library later;
   - B16 Admin/OPS visibility later;
   - test order #55 should expire naturally or be handled as test data if needed.

6. Next recommended step:
   - B15D Admin Publishing Console: richer read/admin view and action affordances, still no auto-publish/scheduler.

## Non-goals

Do NOT:
- change app code;
- change tests;
- call production APIs;
- publish/retry/send Telegram messages;
- mutate production data;
- create migrations;
- alter Mini App routes;
- touch Layer A.

## After completion report

Return:

1. Files changed.
2. Checkpoint summary.
3. Next recommended step.
4. `git status --short`.
5. `git diff --stat`.
6. Confirmations:
   - docs-only;
   - no app code changes;
   - no tests required;
   - no production calls;
   - no mutation;
   - no Telegram send/publish;
   - no Layer A changes.

---

## Deliverables (implemented)

- **[`docs/B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md`](B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md)** — closure narrative (**B15C6**).
- **[`docs/HANDOFF_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT_TO_NEXT_STEP.md`](HANDOFF_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT_TO_NEXT_STEP.md)** — next recommended step (**B15D**).
- **`docs/CURSOR_PROMPT_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT.md`** (this file) — prompt archive.
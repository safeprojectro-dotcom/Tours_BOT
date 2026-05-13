# CURSOR_PROMPT_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT

## Context

Project: Tours_BOT.

We have completed the safe Admin Publishing Console foundation across B15B–B15F.

Recent clean checkpoint:
- `2808d2b feat: add publishing console template source channel read model`
- `1aeeb10 feat: add publishing console action affordances`
- `fab43a6 feat: enrich admin publishing console read view`
- `d4489e1 docs: close B15C exact CTA chain checkpoint`
- `f444a15 fix: align supplier offer publish copy with execution link order`
- `c3dda1c fix: keep admin on supplier offer after bridge actions`

Completed B15 blocks:

## B15B — read-only Admin Publishing Console

Implemented:
- `GET /admin/publishing-console`
- read-only candidate view
- no publish/send/retry/scheduler/mutation

## B15C — exact CTA / conversion safety chain

Closed accepted conversion chain:

Supplier offer approved/packaged
→ Tour bridge created/linked
→ Tour activated for Mini App catalog
→ Active execution link created
→ Showcase/channel publish allowed
→ Channel `Rezervă` opens exact Mini App tour via Telegram Mini App short-name link
→ Layer A handles reservation/payment.

Production evidence:
- Offer #15
- Tour #9
- Tour code `B10-SO15-460344`
- Execution link #8
- Publish attempt #6
- Showcase message #28
- CTA `https://t.me/tours_tm_bot/banattours?startapp=tour_B10-SO15-460344`
- Temp hold/order #55 during smoke
- No identity warning
- Payment screen reached

## B15D — richer read/admin view

`GET /admin/publishing-console` enriched with:
- readiness_summary
- readiness_level
- conversion_target_kind
- conversion_target_url
- cta_safety_status
- primary_blocker
- blocker_codes
- next_action_code
- next_action_label
- admin_action_path
- preview_path
- source_status_summary
- audit_hint

## B15E — action affordances metadata

`GET /admin/publishing-console` enriched with read-only `actions[]` metadata:
- code
- label
- kind
- enabled
- requires_confirmation
- danger_level
- admin_path
- method
- implemented
- disabled_reason
- source

No action execution was added.

## B15F — template/source/channel read model

`GET /admin/publishing-console` enriched with:
- source metadata
- template/source metadata
- channel metadata
- media policy metadata
- template_actions
- channel_actions
- future capability hints

No template editor, channel selector, scheduler, send, or publish mutation was added.

## Goal

Create a docs-only B15 foundation closure checkpoint.

The checkpoint must clearly record that B15B–B15F established a safe read/admin publishing console foundation, while all dangerous/execution functionality remains future gated.

## Required docs changes

Create:
- `docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`
- `docs/HANDOFF_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md`
- `docs/CURSOR_PROMPT_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT.md`

Update:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`
- `docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`
- `docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`
- `docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`

## Required checkpoint content

`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md` must include:

1. Scope:
   - B15B–B15F safe publishing console foundation is closed.

2. What is now available:
   - read-only console endpoint;
   - readiness/blocker summaries;
   - exact CTA safety visibility;
   - next action hints;
   - read-only action affordances;
   - source/template/channel/media metadata;
   - future-disabled capability hints.

3. Correct supplier offer publish/conversion order:
   - packaging/moderation approved;
   - tour bridge created/linked;
   - tour activated for catalog;
   - execution link created;
   - showcase/channel publish;
   - channel CTA opens exact Mini App tour;
   - Layer A handles reservation/payment.

4. Production evidence from B15C/B15C5:
   - Offer #15;
   - Tour #9;
   - Tour code `B10-SO15-460344`;
   - execution link #8;
   - publish attempt #6;
   - message #28;
   - order/temp hold #55.

5. Safety boundaries preserved:
   - no auto-publish;
   - no scheduler;
   - no action execution endpoint from console;
   - no template editor;
   - no channel selector;
   - no Telegram send/retry from console read;
   - no Layer A changes;
   - no Mini App routing changes;
   - no supplier-side publish;
   - no fake urgency/availability.

6. Tests referenced:
   - `tests/unit/test_admin_publishing_console.py` — 8 passed for B15D/E/F slices.
   - B15C smoke docs remain source for production smoke evidence.

7. Future gated options:
   - B15F2 template editor design/read model only if explicitly approved.
   - B15F3 channel selector design/read model only if explicitly approved.
   - B15E2 explicit action execution design only if explicitly approved.
   - B15G guarded auto-publish design only after explicit approval.
   - B16/Admin OPS visibility if product priority shifts.

8. Recommended next step:
   - Either pause B15 and return to broader business plan sequence,
   - or choose B15F2/B15F3/B15E2 as explicit design-only next slice.

## Required handoff content

`docs/HANDOFF_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md` must summarize:

- B15 foundation closed.
- Current API capability of `GET /admin/publishing-console`.
- What remains read-only.
- What is explicitly not implemented.
- Future gated options.
- Recommended next decision point.

## Update CHAT_HANDOFF

Add a concise top-level B15 closure bullet:

- B15B–B15F closed safe publishing console foundation.
- `GET /admin/publishing-console` now exposes readiness, blockers, exact CTA safety, action affordances, source/template/channel/media metadata, and future-disabled hints.
- No action execution/send/scheduler/template editor/channel selector.
- Next options require explicit design gate.

## Update OPEN_QUESTIONS_AND_TECH_DEBT

Mark B15B–B15F foundation as closed.

Keep open gated future rows:
- B15F2 template editor design.
- B15F3 channel selector design.
- B15E2 explicit action execution design.
- B15G guarded auto-publish design.
- B16/Admin OPS visibility, if prioritized.

## Non-goals

Do NOT:
- change app code;
- change tests;
- change schemas/services;
- call production APIs;
- publish/send/retry Telegram messages;
- mutate production data;
- add migrations;
- modify Mini App routing;
- modify Layer A.

## After completion report

Return:

1. Files changed.
2. Checkpoint summary.
3. Future gated next-step options.
4. `git status --short`.
5. `git diff --stat`.
6. Confirmations:
   - docs-only;
   - no app code changes;
   - no tests required;
   - no production calls;
   - no production data mutation;
   - no Telegram send/publish/retry;
   - no Layer A changes;
   - no Mini App routing changes.

---

## Doc artifacts produced by this sync

| Artifact | Role |
|----------|------|
| [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md) | Consolidated **B15B–B15F** foundation closure record. |
| [`docs/HANDOFF_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md`](HANDOFF_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md) | Next-step decision summary. |
| Updates to [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md), [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md), [`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md), [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md), [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md), [`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md) | Cross-links to the closure checkpoint. |
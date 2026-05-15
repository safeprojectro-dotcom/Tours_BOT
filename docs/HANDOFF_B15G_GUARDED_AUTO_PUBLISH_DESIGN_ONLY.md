# HANDOFF_B15G_GUARDED_AUTO_PUBLISH_DESIGN_ONLY

## Project
Tours_BOT

## Block
B15G — Guarded Auto-Publish Design Only

## Prerequisites

Closed checkpoints:
- f8f146f feat: add guarded prepare conversion chain admin endpoint
- fd4e25d feat: expose prepare conversion chain action affordances
- 9e4b8d docs: record prepare conversion chain production smoke
- aa1dc8 feat: add publishing console prepare chain action execution
- 81b65c5 docs: record publishing console prepare chain smoke

## Goal

Define future guarded auto-publish policy without implementing it.

## Deliverable

**Primary:** [`docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md`](B15G_GUARDED_AUTO_PUBLISH_DESIGN.md) — full design (§§1–12: definitions, gates, non-gates, modes, audit/idempotency, rollback, future data/API sketches, testing strategy, recommendation).

**Continuity updates:** [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (B15G bullet); [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md) (§7 B15G link + slice index); [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) (B15G pointer — design delivered, runtime still gated).

**Prompt / spec:** [`docs/CURSOR_PROMPT_B15G_GUARDED_AUTO_PUBLISH_DESIGN_ONLY.md`](CURSOR_PROMPT_B15G_GUARDED_AUTO_PUBLISH_DESIGN_ONLY.md).

**Reference gap:** `docs/BUSINESS-план-v2.txt` not in repo — called out in B15G §1; use existing business docs as needed.

## Status

**Closed (design gate only).**

- No runtime code, endpoint, scheduler, Telegram publish/send/retry, or migration.
- No change to `prepare_conversion_chain` semantics beyond what future **read-only** readiness work would add when chartered.

## Core principle

Internal conversion preparation is not public publishing.

Auto-publish, if ever implemented, must remain gated, audited, idempotent, and reversible.

## Expected recommendation (documented)

Default remains:
- auto-publish disabled
- suggest-only / readiness evaluation first
- public Telegram publish stays explicit until separate go/no-go

## Next after B15G

If design is accepted (per B15G §12):
- **First safe implementation:** read-only publish readiness evaluation (`GET`-class), not automatic channel send.
- Or continue another B15 publishing-console refinement (e.g. B15F2/B15F3) per roadmap.
- **Do not** jump directly to fully automatic Telegram publish without a separate product/security go/no-go.

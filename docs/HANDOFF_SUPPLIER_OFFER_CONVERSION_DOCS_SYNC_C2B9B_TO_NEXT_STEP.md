# HANDOFF_SUPPLIER_OFFER_CONVERSION_DOCS_SYNC_C2B9B_TO_NEXT_STEP

Project: Tours_BOT — Supplier Offer → Tour / Mini App conversion (**documentation sync**).

## Status

**C2B9B complete (docs-only, 2026-05-09).** No code, migrations, Mini App, or booking/payment changes.

## Context

- **C2B8B** is closed: Telegram **Publică / Publish** is workflow-gated by **`operator_workflow.actions.publish_showcase_channel.enabled`**, with propose/confirm and double **`GET …/review-package`** re-read; legacy one-step publish is retired on the detail keyboard.
- **C2B9A** audit: the **B10** offer→Tour bridge is **already implemented** (model/service, admin **`tour-bridge`**, **`activate-for-catalog`**, execution-link HTTP + partial Telegram, **`review-package` / `operator_workflow`**, **B11** **`supoffer_<id>`** routing when active execution link + **`OPEN_FOR_SALE`** + catalog visibility).

## What C2B9B did

Aligned operator-facing docs with that reality:

- [`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) — conversion chain, B11 row, C2 slices / Telegram UX vs **C2B8B**.
- [`docs/ADMIN_OPERATOR_WORKFLOW.md`](ADMIN_OPERATOR_WORKFLOW.md) — §1 narrative; step 9 **HTTP** or **Telegram** publish; C2A / UX / C2B3 text.
- [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) — pointer to full chain + playbook.
- [`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md) — gaps / §4 / §5 updated for **C2B9B** done.
- [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) — **C2B9B** line; C2B2 / UX / C2B3 bullets.
- [`docs/HANDOFF_SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A_TO_NEXT_STEP.md`](HANDOFF_SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A_TO_NEXT_STEP.md) — C2B9B struck through as done.
- Prompt + deliverables: [`docs/CURSOR_PROMPT_SUPPLIER_OFFER_CONVERSION_DOCS_SYNC_C2B9B.md`](CURSOR_PROMPT_SUPPLIER_OFFER_CONVERSION_DOCS_SYNC_C2B9B.md).

## Key documentation truth (conversion chain)

Operators should read this as **one narrative**; **`GET …/review-package`** remains the single read surface before mutations. **Technical order** in the canonical table often runs **bridge → activate-for-catalog → (optional) catalog smoke → showcase publish → execution link**; **execution link** normally expects **`published`** lifecycle. Product-facing phrasing:

```text
Supplier Offer (facts / intake)
-> AI/admin packaging + moderation + publish readiness (review-package / conversion_closure)
-> showcase publication (HTTP POST …/publish OR Telegram C2B8B when publish_showcase_channel.enabled)
-> explicit Tour bridge (POST …/tour-bridge; create_tour_bridge)
-> catalog activation when allowed (activate_tour_for_catalog; B8.3 guard)
-> create/activate execution link (HTTP; Telegram link wizard when published)
-> B11 /start supoffer_<id> -> exact Mini App /tours/{code} only when
   active execution link + OPEN_FOR_SALE + catalog visibility
-> Layer A reservation / payment (unchanged)
```

**Telegram today:** packaging + showcase publish + (for **published** offers) execution-link UX; **`create_tour_bridge`** and **`activate_tour_for_catalog`** stay **Admin API** on the card unless a future **C2B10T-*** slice ships them.

## Next (product / engineering)

Optional **C2B10T-*** Telegram buttons (**one** conversion action at a time, same propose/confirm/double **review-package** pattern as **C2B8B**) — requires product sign-off.

Parallel tracks per [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md): e.g. **B7.3B** media bytes, **B10.6** bot-as-router, **B11** polish.

## Pointers

- Audit: [`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md)
- Continuity: [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (C2B9A / C2B9B)

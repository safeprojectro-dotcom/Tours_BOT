# HANDOFF_SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A_TO_NEXT_STEP

## Project

Tours_BOT — Supplier Offer -> Tour / Mini App Conversion Bridge.

## Current checkpoint before C2B9A

C2B8B is closed and pushed.

Implemented:

- Telegram admin `Publică / Publish` button.
- Workflow-gated by `operator_workflow.actions.publish_showcase_channel.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Legacy one-step Telegram publish suppressed/retired from main detail keyboard.
- HTTP publish semantics preserved.
- No Mini App changes.
- No booking/payment/order changes.
- No Tour/catalog/execution link changes.
- No migrations.

## Why C2B9A exists

Next strategic block is Supplier Offer -> Tour / Mini App conversion bridge.

This crosses the boundary between:

- Supplier Offer / marketing showcase / publication;
- Tour / catalog / booking/payment execution truth.

Therefore, C2B9A must be a Plan/readiness audit before implementation.

## Core principles

- Supplier Offer is raw/commercial/marketing source, not automatically bookable.
- Telegram channel is discovery/showcase.
- Mini App/catalog execution truth must be strict and current.
- `visibility != bookability`.
- No hidden Tour creation.
- No hidden ORM trigger.
- No AI mutation of source-of-truth execution data.
- Admin must explicitly create/link/activate conversion path.
- Layer A booking/payment/order truth must remain untouched.
- Service layer owns business logic.
- Repository layer remains persistence-only.

## C2B9A expected output

Cursor should inspect current docs and code and report:

1. existing bridge-related models/tables/services/endpoints;
2. existing `/start supoffer_<id>` and Mini App landing behavior if any;
3. existing execution link or bridge entities if any;
4. gaps for safe Offer -> Tour conversion;
5. risks;
6. proposed next implementation sequence;
7. recommended immediate next prompt.

## C2B9A non-goals

Do not implement:

- Tour creation;
- bridge table/model;
- execution link activation;
- Mini App routing;
- Telegram routing changes;
- booking/payment/order changes;
- migrations.

Docs-only updates are allowed if needed.

## After C2B9A (audit outcome — 2026-05-09)

**Authoritative report:** [`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md).

**Finding:** The **explicit** offer→Tour conversion path (**B10**) is **already implemented** in the backend: `supplier_offer_tour_bridges`, `SupplierOfferTourBridgeService`, admin `POST/GET …/tour-bridge`, execution-link HTTP, `POST …/tours/{tour_id}/activate-for-catalog`, `review-package` (`bridge_readiness`, `conversion_closure`, `operator_workflow`), and **`/start supoffer_<id>`** routing via `resolve_sup_offer_start_mini_app_routing` when an active execution link + `OPEN_FOR_SALE` + catalog visibility allow it.

**Main gaps are not “missing bridge”** but: **(1)** **`create_execution_link`** still **mostly** HTTP + published-offer wizard (**optional** **C2B10T-C**), **(2)** **~~docs drift~~** **cleared by C2B9B** (**2026-05-09**) **+** **C2B10T-*** in **`CHAT_HANDOFF`**, **(3)** product follow-ups: B7.3 media bytes, B10.6 bot-as-router, optional B11 polish.

Continuity: [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (C2B9A planning line).

## Likely next steps after audit (revised)

Order follows current repo — **do not** treat “implement bridge HTTP” as greenfield.

1. ~~**C2B9B (docs-only, recommended first):** Sync `SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md` / `ADMIN_OPERATOR_WORKFLOW.md`; add a short **conversion checklist** (bridge → activate-for-catalog → execution link → verify `conversion_closure` + optional `supoffer_` smoke). Suggested prompt: `CURSOR_PROMPT_SUPPLIER_OFFER_CONVERSION_DOCS_SYNC_C2B9B`.~~ **Done (2026-05-09):** BUSINESS plan + `ADMIN_OPERATOR_WORKFLOW.md` + `ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md` + `CHAT_HANDOFF.md` + C2B9A doc updates.
2. ~~**C2B10T-A / C2B10T-B (optional):** Telegram **Link tour** / **List for sale** with propose/confirm + double **`review-package`**.~~ **Done** — see **`docs/CHAT_HANDOFF.md`** **`;`** **optional** **C2B10T-C** — Telegram entry for **`create_execution_link`** / execution-link activation (same pattern) **or** OPS smoke per **`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`**.
3. **B7.3B / B10.6 / B11** — per [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md); not assumed here.

**Obsolete placeholders** (if an older plan assumed no B10 — **not** current repo):

- ~~C2B10A — central admin create/link Tour~~ → **done (B10)**.
- ~~C2B10B — execution link~~ → **HTTP + partial Telegram** exist.
- ~~C2B11 exact deep link~~ → **implemented** in `supplier_offer_bot_start_routing` (gated).

## Post-Cursor review checklist

Before any commit/push, GPT must check:

- did Cursor change only docs, or no files?
- no code implementation unless explicitly approved;
- no migrations;
- no Mini App changes;
- no booking/payment/order changes;
- no publish semantics changes;
- `git status --short`;
- `git diff --stat`.

Commit/push only after user provides Cursor report and GPT reviews it.

# HANDOFF_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE_TO_NEXT_STEP

## Status

**B16D2** is a **design gate** for future guarded execution of **`prepare_conversion_chain`**. Authoritative spec: **[`docs/B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`](B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md)**. Prompt archive: **[`docs/CURSOR_PROMPT_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`](CURSOR_PROMPT_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md)**. Parent automation framing: **[`docs/B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md)**.

**No app code** was changed as part of recording this gate.

---

## Future action

**Preferred endpoint:**

`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`

**Purpose (internal chain only):**

1. Ensure **tour bridge** (create/link if missing).
2. **Activate tour for catalog** when eligible (existing B10.2 semantics).
3. Ensure **active execution link** when missing (B15C-aligned).

Request body (see design gate §3): **`idempotency_key`**, **`confirm`**, **`dry_run`**.

---

## Boundary

This action **must never** publish to Telegram.

It **must not**:

- send Telegram messages;
- retry publish;
- mutate orders / payments / reservations (except side effects already inherent in existing catalog activation services, if any);
- call Layer A booking/payment mutations;
- change Mini App routing;
- run automatic retry loops or hidden publish after partial success.

**`publish_showcase_channel`** stays a **separate**, confirmation-gated step (B16D Level 3).

---

## Required future implementation features

- **Admin auth** (existing token patterns).
- **Idempotency key** (body and/or header — single source of truth TBD in implementation).
- **Explicit `confirm`** for **`conversion_enabling`** classification (B16D §7).
- **Audit record** for the top-level POST and **step-level** outcomes.
- **`partial_success`** support with honest **`steps[]`** and next actions for operators.
- **No rollback** in MVP (forward remediation; parent B16D §5).
- **No automatic retry** without a new explicit request.
- **No hidden publish.**

---

## Recommended implementation split

1. **B16D2A** — Audit / idempotency persistence foundation **if** not already sufficient for offer-scoped actions.
2. **B16D2B** — Service-level execution (bridge → activate → execution link), shared by HTTP and any future callers.
3. **B16D2C** — **`POST`** endpoint + OpenAPI + request/response schemas.
4. **B16D2D** — Read-model / **`operator_workflow`** or publishing-console affordance integration (metadata + safe CTA wiring).
5. **B16D2E** — Production smoke / runbook updates (**`ADMIN_OPERATOR_WORKFLOW`**, showcase runbook as needed).

---

## Continuity

- **Read-only plan (today):** `GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan` (B16D1) — POST must stay consistent with its blockers.
- **OPS visibility:** `GET /admin/ops-dashboard` **`audit_events`** (B16E) — implementation should emit auditable signals for failures/success of this POST where policy allows.

**Docs slice delivery:** design gate + this handoff + continuity updates to **`docs/CHAT_HANDOFF.md`** / **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`**. **Not delivered:** routes, services, migrations, tests (until B16D2A–E execution slices).

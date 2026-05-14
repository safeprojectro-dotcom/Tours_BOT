# B16D2 — Prepare conversion chain execution (design gate)

**Status:** Design gate only — **no** application code, **no** new route registration, **no** migrations in this slice.  
**Parent:** [`docs/B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md) (Level 2 — guarded internal chain).  
**Read path today:** `GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan` (B16D1 family) must remain the non-mutating preview auditors can trust.  
**Handoff:** [`docs/HANDOFF_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE_TO_NEXT_STEP.md`](HANDOFF_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE_TO_NEXT_STEP.md).  
**Prompt archive:** [`docs/CURSOR_PROMPT_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`](CURSOR_PROMPT_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md).

---

## 1. Objective

**B16D2** defines the first **guarded mutation** that automates **internal** supplier-offer conversion prep so operators do not have to issue three separate admin calls for the usual happy path.

Goals:

- **Reduce admin burden** for an already-approved offer on the path to showcase readiness.
- Stay **strictly below** the **public publish** boundary (no Telegram channel publish, no Telegram send, no publish retry loops).
- Reuse **existing** domain services and their preconditions (B9/B10 bridge, B10.2 catalog activation, B15C-aligned execution link), so behavior matches **today’s** manual HTTP/Telegram parity.
- Remain **auditable**, **idempotent** where artifacts already exist, and **honest** about **partial success** (see parent doc §5–§6).

Non-goals for B16D2:

- Replacing **`publish_showcase_channel`** or hiding publish inside this POST.
- Scheduler / auto-publish (**B15G** remains separately gated).

---

## 2. Future endpoint

**Preferred:**

```http
POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain
```

**Rationale:**

- **Source entity** is explicit (`offer_id`).
- Aligns with existing **`/admin/supplier-offers/...`** admin surface and review-package/plan routes.
- **Audit** and **correlation** are straightforward (one resource, one action).
- **Idempotency** can be scoped to `(offer_id, idempotency_key)` without a generic action executor.
- Avoids a vague **`POST /admin/actions`** until multiple actions truly need one router.

**Auth:** Same as other mutating admin supplier-offer routes (existing admin API token pattern).

---

## 3. Request body

Proposed JSON body:

```json
{
  "idempotency_key": "uuid-or-client-generated-key",
  "confirm": true,
  "dry_run": false
}
```

| Field | Role |
|--------|------|
| **`idempotency_key`** | Client-generated stable key per intended real mutation. Same key + same `offer_id` must **not** create duplicate bridges, duplicate activations, or duplicate active links; safe replay returns the same logical outcome. (Align with existing `Idempotency-Key` header patterns where the codebase already uses them — implementation may accept **either** body or header if product prefers one source of truth; this gate requires **at least one** stable key.) |
| **`confirm`** | **`true`** required for live execution when the action class is **`conversion_enabling`** per B16D §7. Server rejects or returns **409/422** when preconditions or confirmation policy fail. **`false`** reserved for early validation-only responses if implementation chooses; **live chain must not run without explicit confirm.** |
| **`dry_run`** | When **`true`**, implementation **must not** mutate persistence: validate preconditions, return the **same structural shape** as a real run (planned steps, blockers, would-skip vs would-run), and use a distinct result flag such as **`dry_run": true`** in the response. When **`false`**, perform the chain under normal transaction/commit rules. |

---

## 4. Intended execution chain (single POST)

When preconditions pass and **`dry_run`** is **`false`**, the handler runs **in order** (stop on first hard failure unless design explicitly allows continue — **default: fail-fast after first sub-step error**, with partial state visible in response and audit):

1. **Create / link tour bridge** if missing — existing **`SupplierOfferTourBridgeService`** (or equivalent) semantics; no new bridge “shapes”.
2. **Activate linked tour for catalog** if **eligible** — existing **`AdminTourWriteService.activate_tour_for_catalog`** (B10.2) semantics; respect boarding / duplicate-active-tour guards (B8.3, B14 family).
3. **Create active execution link** if missing — existing **`SupplierOfferExecutionLinkService.link_offer_to_tour`** (or equivalent); **B15C** policy remains: publish readiness still expects this link before channel publish when product gates require it.

**Seat / inventory:** No direct seat mutation APIs in this chain. Any **catalog** state change must be **only** what existing activation already does today (documented in those services).

---

## 5. Preconditions and gates

**Before** starting the chain, the implementation must align with **B16D §4** and with **`GET .../prepare-conversion-chain/plan`** (B16D1):

- Packaging / lifecycle / media / quality gates as **policy** defines for “safe to prepare”.
- Sufficient offer + tour data for bridge and Layer A prep (boarding, etc.) per existing validation.
- Operator identity attributable (for audit `requested_by` / admin subject).

If any gate fails: **do not** partially mutate unless a later explicit product decision documents safe partial application — **default for B16D2 implementation is fail-fast with no commits beyond already-completed sub-steps in the same transaction policy** (parent doc: no silent rollback; forward remediation).

---

## 6. Response (shape to implement)

Exact schema is an implementation task; the gate requires:

- **`offer_id`**, **`status`** (`success` | `partial_success` | `failed`).
- **`steps[]`**: per-step `code`, `status` (`completed` | `skipped` | `failed`), optional `detail` / error codes, stable machine-readable identifiers.
- **`links`**: e.g. `review_package_path`, `plan_path`, `tour_admin_path` when IDs exist.
- **`dry_run`**: boolean echo when applicable.
- No success response that implies publish occurred.

---

## 7. Audit and ops visibility

- **Top-level** audit record for each POST (who, when, offer_id, idempotency_key, dry_run, outcome).
- **Per-sub-step** audit or structured log lines (start/end/error) so **`GET /admin/ops-dashboard`** **`audit_events`** (B16E) can surface failures without new product features in this gate.

---

## 8. Explicitly out of scope (must never be bundled)

- Telegram **publish**, **send**, **retry**, or any **bot** outbound I/O.
- **Payment** or **order** mutation; **reservation** / hold manipulation; Layer A booking flows.
- **Supplier outbound** messaging (separate channels/products).
- **Mini App** routing / B11 resolver changes.
- **Auto-retry** of failed sub-steps without a **new** explicit request.

---

## 9. Relationship to other tickets

| Item | Relationship |
|------|----------------|
| **B16D1 plan GET** | Source of truth preview; POST must not contradict plan blockers without explicit error. |
| **B15E2** | Publishing console may later invoke the same service; HTTP route above remains canonical for offer-scoped execution. |
| **B15G** | Auto-publish remains a **separate** approval surface. |
| **`publish_showcase_channel`** | **Level 3** — always separate POST / confirm flow after internal prep is satisfied. |

---

## 10. Implementation exit criteria (future PR, not this doc)

- Unit/integration tests for idempotency, partial failure, dry_run, and gate alignment with plan endpoint.
- OpenAPI / admin client docs updated.
- Ops runbook note: when to use POST vs three manual steps.

This design gate **does not** approve production enablement until stakeholders accept the risk of chained **`conversion_enabling`** automation and sign off the implementation PR.

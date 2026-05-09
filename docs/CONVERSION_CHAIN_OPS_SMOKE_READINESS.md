# Conversion chain — OPS smoke readiness (closeout gate)

**Date context:** 2026. **Type:** docs / operator readiness — **no** application behavior change.

**Why this doc:** Consolidates **production OPS smoke**, the **B10.6 bot-as-router design gate**, **admin/OPS visibility polish** (design-only), **media pipeline pause** confirmation, and a **recommended next implementation block** after the Telegram conversion workflow (**C2B8B**, **C2B10T-A/B/C**, **C2B10T-D**) and media foundation checkpoint (**B7.4A–D**).

**Companion pages:** [`docs/TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`](TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md) · [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) · [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md).

---

## 1. Core architecture rules (must preserve)

- **published ≠ bookable** — showcase / Telegram marketing is orthogonal to **Mini App** catalog **`open_for_sale`**.
- **linked ≠ catalog-visible** — bridge/materialized **`Tour`** is not listed until **activate-for-catalog**.
- **catalog-visible ≠ execution-linked** — catalog can list **`Tour`** before an active **execution link**.
- **execution-linked ≠ paid booking** — Layer A remains **booking / payment / order** truth.
- **Mini App** execution truth stays **strict / current**; **bot/UI must not invent readiness** — use **`GET …/review-package`** and **`operator_workflow`**.

**Safety invariants:** No hidden **Tour** creation, **publish**, **execution link**, or **media ingestion**. Telegram workflow buttons rely on **`operator_workflow.actions.*.enabled`**. **Dangerous** actions use **propose → confirm** and a **fresh** **`review-package`** re-read where implemented. Do **not** change **publish readiness** or **booking/payment** behavior from smoke docs.

---

## 2. Safe read-only checks (PowerShell)

**Purpose:** Inspect gates and closure state **without** POST mutations.

**Setup:** Use deployed API origin as **`$BASE`** (no path prefix — admin mounts at **`/admin`**). **`ADMIN_API_TOKEN`** must be configured server-side; without it admin returns **503**. Auth accepts **`Authorization: Bearer`** or **`X-Admin-Token`** (see [`app/api/admin_auth.py`](../app/api/admin_auth.py) and the walkthrough).

```powershell
$BASE = "https://<your-api-host>"   # e.g. staging/production origin
$token = "<ADMIN_API_TOKEN>"        # from env / secret store — do not commit

$Headers = @{
  "Authorization" = "Bearer $token"
  # Alternative: "X-Admin-Token" = $token
}

$OFFER_ID = <OFFER_ID>  # integer

$r = Invoke-RestMethod -Uri "$BASE/admin/supplier-offers/$OFFER_ID/review-package" -Headers $Headers -Method GET
$r.operator_workflow.actions | Format-Table code, enabled, danger_level, requires_confirmation, disabled_reason -AutoSize
$r.conversion_closure | Format-List
$r.linked_tour_catalog | Format-List
```

**How to interpret (high level):**

- **`operator_workflow.actions`:** Each row’s **`code`** matches the workflow gate (e.g. **`create_tour_bridge`**, **`activate_tour_for_catalog`**, **`publish_showcase_channel`**, **`create_execution_link`**). **`enabled: false`** with a **`disabled_reason`** explains why Telegram (and operators) should not see that action. **`danger_level`** includes **`public_dangerous`** for channel publish; **`requires_confirmation`** flags the propose/confirm pattern for mutating steps.
- **`conversion_closure`:** Aggregated booleans (**`has_tour_bridge`**, **`has_catalog_visible_tour`**, **`has_active_execution_link`**, routing flags, **`next_missing_step`**) — same helper as the unit E2E-style proof in **`test_supplier_offer_catalog_conversion_closure`**. **`next_missing_step: null`** with all trues means the modeled chain is complete for that offer snapshot.
- **`linked_tour_catalog`:** Bridged **`tour_id`**, **`tour_code`**, **`tour_status`**, **`catalog_listed_for_mini_app`**, **`can_activate_for_catalog`**, etc. Present only when a bridge links an offer to a **`Tour`**.

**C2B11A panel:** [`docs/C2B11A_READ_ONLY_SMOKE_LOG.md`](C2B11A_READ_ONLY_SMOKE_LOG.md) — **`conversion_status_panel`** JSON + operator actions table; operator run log template.

**Optional extra read-only probes** (same session):

```powershell
$r.conversion_status_panel | ConvertTo-Json -Depth 5
$r.operator_workflow | Select-Object state, primary_next_action, blocking_reasons, warnings | Format-List
$r.execution_links_review | Format-List
$r.warnings
$r.recommended_next_actions
```

**Ordering note (Telegram vs HTTP):** On the admin card, when conversion actions are enabled, keyboard order is **Link tour → List for sale → Publish → Booking link** (see walkthrough § «Telegram admin card parity»). **HTTP** checklist order is **bridge → activate-for-catalog → (preview) publish → execution-link**. Business rules are unchanged (e.g. **execution link** still requires **`lifecycle_status === published`**).

---

## 3. Full procedure and mutating smoke

**Primary checklist:** [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md) — **Mode A** (dry-run / API, no live secrets in repo) vs **Mode B** (live staging/production with redacted run log).

**Publish / preview runbook:** [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md).

**Operator workflow semantics:** [`docs/ADMIN_OPERATOR_WORKFLOW.md`](ADMIN_OPERATOR_WORKFLOW.md).

**Conversion chain business narrative:** [`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) · bridge readiness audit [`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md).

---

## 4. Automated regression (before release)

Run in CI locally or in pipeline (examples cited from the checkpoint):

- **`test_supplier_offer_catalog_conversion_closure`**
- **`test_operator_workflow_c2b3_keyboard`**
- **`test_operator_workflow_c2b10ta_specs`**, **`test_operator_workflow_c2b10tb_specs`**, **`test_operator_workflow_c2b10tc_specs`**
- **`test_telegram_admin_moderation_y281`**

Live Telegram smoke remains **operator-owned**; API **`review-package`** checks above complement tests and catch drift in **`enabled`** / **`disabled_reason`** for a real **`OFFER_ID`**.

---

## 5. B10.6 — Bot-as-router / consultant (design gate)

**Status:** **Postponed** as a **large refactor**; **not** blocking the conversion checkpoint. Track until a **scoped ticket** exists.

**Intent:** Private Telegram bot as **router / consultant** (exact **Mini App** deep links, help/RFQ entry) — **not** a second catalog that duplicates Mini App tour body or **full_bus** semantics.

**Risks if deferred long-term:** Stale or inconsistent copy in bot vs **Mini App** execution truth.

**References:** [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) (**B10.6**) · [`docs/B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md) · handoffs [`docs/HANDOFF_B10_6_BOT_ROUTER_CONSULTANT_IMPLEMENTATION_TO_NEXT_STEP.md`](HANDOFF_B10_6_BOT_ROUTER_CONSULTANT_IMPLEMENTATION_TO_NEXT_STEP.md), [`docs/HANDOFF_B10_6B_START_TOURS_ROUTER_FIRST_TO_NEXT_STEP.md`](HANDOFF_B10_6B_START_TOURS_ROUTER_FIRST_TO_NEXT_STEP.md), [`docs/HANDOFF_B10_6C_BOT_COPY_BUTTONS_FULL_BUS_AUDIT_TO_NEXT_STEP.md`](HANDOFF_B10_6C_BOT_COPY_BUTTONS_FULL_BUS_AUDIT_TO_NEXT_STEP.md).

**Design gate before implementation:** Product scope (consultant vs router-only), **no duplicated** catalog cards, alignment with **B11** **`supoffer_*`** / **`tour_*`** entry paths, and copy ownership (bot vs Mini App).

---

## 6. Admin / OPS visibility polish (design-only)

**Current state:** **`GET …/review-package`** is the **read-only hub** (offer snapshot, **`operator_workflow`**, **`conversion_closure`**, warnings, execution link slice, etc.). Telegram moderation workspace shows a **compact** operator_workflow block; full detail remains on HTTP **review-package**.

**Polish directions (no code in this block):**

- Keep **HTTP review-package** the canonical ops surface for investigations; ensure runbooks link here first.
- Optional future: richer **OPS** dashboards or filtered list views — still **read** from the same aggregates; **do not** re-encode gate logic client-side.
- **Dangerous** actions stay **propose/confirm + re-read**; polish should not short-circuit that.

---

## 7. Media pipeline — intentional pause

**Shipped in this checkpoint:** **B7.4A** audit, **B7.4B** contract, **B7.4C** conservative foundation (config/adapter/eligibility), **B7.4D** **`publish_safe`** vNext metadata helpers — **no** durable byte ingest, **no** publish wiring to storage.

**Do not** continue **B7.4D2** / **B7.4C2** / **B7.4E** / **B7.5** / **B7.6** until a **charter** (ticket + stakeholder agreement). See [`docs/TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`](TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md) §3–4 and [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md) / [`docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`](B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md).

---

## 8. Recommended next implementation block (pick one explicitly)

**Canonical ordered recommendation** (rationale and options **A–D**): [`docs/NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md`](NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md) — **1.** **`C2B11A_ADMIN_OPS_CONVERSION_STATUS_PANEL`** · **2.** production/OPS smoke · **3.** B10.6 bot-as-router · **4.** media pipeline by explicit charter only.

This closeout **stops the micro-step chain**; **next** work should be **chosen** with stakeholder sign-off, not an implied automatic sequence.

| Block | When to choose |
|--------|----------------|
| **C2B11A** (ops visibility panel) | **First** when following closeout ordering — read-only **five-layer** panel; see [`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`](ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md). |
| **Production/staging E2E** | After **C2B11A** (per above link): **Mode A** then **Mode B** where allowed; record outcomes — closes the gap between **unit tests** and **real** **`OFFER_ID`** + infra. |
| **B10.6** | Product prioritizes **private bot** consultant/router UX — design gate: [`docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`](B10_6_BOT_AS_ROUTER_DESIGN_GATE.md). |
| **B11 depth** | Product wants more **execution-link / Mini App** behavior beyond current **`supoffer_*`** slice. |
| **B12/B13** | Showcase copy, channel UX, preview ergonomics **without** assuming durable media. |
| **B8 follow-up** | Recurrence / draft-tour policy, re-run idempotency, activation discipline per **OPEN_QUESTIONS**. |
| **Scoped media charter** | If bytes are prioritized: **B7.4C2 + orchestrator + B7.4E** (or equivalent) as **one** approved initiative — **not** drive-by micro-PRs. |

**Short recommendation:** Prefer **`C2B11A`** **then** **production smoke**, **then** **B10.6**, as in **`NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT`** — **do not** auto-resume **B7.4** micro-slices without the media charter.

---

## 9. Open questions / debt pointer

Cross-cutting backlog and deferred items: [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md).

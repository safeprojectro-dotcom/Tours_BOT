# HANDOFF — B16D OPS guarded automation design → next step

## Status

**B16D** is a **design-only** checkpoint for guarded OPS automation. Full detail: **[`docs/B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md)** · prompt archive **[`docs/CURSOR_PROMPT_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](CURSOR_PROMPT_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md)**.

---

## Core decision

Do **not** jump to auto-publish.

Use **staged** automation:

1. **Read-only** visibility (done: publishing console, ops dashboard).
2. **Assisted** one-click actions (future; audit + confirmation by danger level).
3. **Guarded internal** preparation chain (future: **`prepare_conversion_chain`**).
4. **Public publish** with **explicit** confirmation (**`publish_showcase_channel`** — **`public_dangerous`**).
5. **Scheduler / auto-publish** only after a **separate** future design gate (**B15G**).

---

## Proposed future action: `prepare_conversion_chain`

**Purpose:** For an **approved** supplier offer, **internally** prepare it so it can reach **`ready_to_publish`** **without** public Telegram side effects.

**Sub-steps (when preconditions pass):**

1. Create/link **tour bridge** if missing.
2. **Activate** linked tour **for catalog** if **eligible**.
3. Create **active execution link** if missing.

**Explicitly excluded:** Telegram publish/send; payment changes; order changes; supplier outbound messages; auto-retry; hidden publish after partial success.

**Partial success:** Each sub-step is audited; the UI must show **remaining** **next** action; idempotent replay must **not** duplicate bridges/links (see design doc §5, §10).

---

## Public publish boundary

**`publish_showcase_channel`** remains **separate** from **`prepare_conversion_chain`**. It is **`public_dangerous`** and must require **explicit** confirmation — **no** bundling into the internal chain.

---

## Recommended API (future B16D2 — Option B)

`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`

**Reason:** Clear **source** entity; matches existing **`/admin/supplier-offers/...`** routes; **easier audit** and **idempotency**; less abstract than a generic **`POST /admin/actions`** executor. Headers/body: **`Idempotency-Key`**, server-side confirmation for **`conversion_enabling`** (design doc §9–§10).

---

## Suggested implementation order

1. **B16B** — filters/limits/time-window for **`GET /admin/ops-dashboard`**.
2. **B16C** — dashboard-to-detail navigation polish.
3. **B16D1** — **read-only** action **plan preview** (no execution).
4. **B16D2** — **`prepare_conversion_chain`** execution + **audit** storage.
5. **B15E2** — publishing console **action execution** integration.
6. **B15G** — guarded auto-publish (**design / gate** only until explicitly approved).

**Prefer B16B/C before execution slices** so operators can navigate and filter before mutating actions ship.

---

## What was delivered (this docs slice)

- **No** application code, **no** new endpoints, **no** tests.
- **No** production calls, **no** data mutation, **no** Telegram send/publish/retry, **no** Layer A or Mini App routing changes **from this design record alone**.

---

## Safety requirements for **future** implementation

Any **B16D2** / **B15E2** implementation should include:

- **Admin** auth (existing patterns).
- **`Idempotency-Key`** (or equivalent) per action + source entity.
- **Audit** record per top-level action **and** per sub-step **`prepare_conversion_chain`**.
- **Explicit** confirmation for **`conversion_enabling`** actions.
- **`partial_success`** reporting and **disabled_reason** / **next_action_code** for the UI.
- **No** hidden publish, **no** payment/order mutations in **`prepare_conversion_chain`**.
- **Layer A** only through **existing**, **explicitly scoped** services — no drive-by semantics changes.

If persistence for the audit model in §6 of the design doc is missing, treat richer audit storage as an **implementation** requirement, **not** assumed today.

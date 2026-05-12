# B15E — Admin Publishing Console action affordances (design)

**Status:** Implemented (additive read-model only; **metadata**, not execution).  
**Builds on:** [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md), [`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md).  
**Code:** `app/schemas/admin_publishing_console.py` · `app/services/admin_publishing_console_service.py`.  
**Handoff:** [`docs/HANDOFF_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN_TO_NEXT_STEP.md).

**B15F (implemented):** **[`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md)** adds **source / template / channel / media** read metadata and future-disabled **`template_actions[]`** / **`channel_actions[]`** on the **same** **`GET /admin/publishing-console`** response. **B15E** **`actions[]`** remain **metadata only**; neither slice turns the console into an execution endpoint.

---

## 1. Objective

B15E adds **read-only action affordance metadata** to **`GET /admin/publishing-console`** so UIs can list possible next steps (labels, HTTP methods/paths, danger level, disabled reasons, implementation status) **without** the console endpoint performing any mutation.

---

## 2. Endpoint

- **`GET /admin/publishing-console`**
- **Remains read-only:** no mutation, send, retry, publish, scheduler, bridge, catalog activation, or execution-link side effects from this route.

---

## 3. New schema / model

- **`AdminPublishingConsoleActionAffordanceRead`** — one row in the **`actions`** array.
- **`AdminPublishingConsoleItemRead.actions`** — `list[AdminPublishingConsoleActionAffordanceRead]` (default empty for backward compatibility at the type level; populated for offer/tour rows).

---

## 4. Action fields

| Field | Purpose |
|--------|---------|
| `code` | Stable action identifier (e.g. matches `operator_workflow` action `code` where applicable). |
| `label` | Human-facing label. |
| `kind` | Same family as workflow danger tier (`safe_read`, `safe_mutation`, `conversion_enabling`, `public_dangerous`). |
| `enabled` | Whether gates allow this action in the current state. |
| `requires_confirmation` | From workflow when applicable. |
| `danger_level` | Mirrors `kind` for offer rows sourced from workflow. |
| `admin_path` | Expanded HTTP path (e.g. `{offer_id}` replaced for supplier offers). |
| `method` | `GET` / `POST` / `PATCH`. |
| `implemented` | `true` for real routes; `false` for future-only placeholders. |
| `disabled_reason` | Why disabled, when present. |
| `source` | `operator_workflow` · `console_read_only` · `future`. |

---

## 5. Sources

- **Supplier-offer** items: affordances are **projected** from existing **`review-package` → `operator_workflow.actions`** (order and fields aligned; paths expanded with offer id).
- **Tour promotion** items: **console-only** safe/read affordances (e.g. open tour admin, verify catalog) plus **future** placeholders (e.g. tour promotion draft) with **`implemented: false`**.

---

## 6. Safety

- Action rows are **metadata only**; the console **does not** call mutation services, Telegram, or publish adapters.
- **No** publish / retry / send from this endpoint.
- **No** bridge, catalog activation, or execution-link **creation** from this read path.
- **No** Layer A changes; **no** Mini App routing changes.

---

## 7. Tour promotion behavior

- **Safe / read** affordances only for implemented paths (`GET`-style navigation hints).
- **Future** draft/promotion affordance is **`implemented: false`**, **`enabled: false`**, with **`source: future`** and an explanatory **`disabled_reason`**.

---

## 8. Tests

```powershell
python -m pytest tests/unit/test_admin_publishing_console.py -q
```

**Result:** `8 passed`.

---

## 9. Next steps

1. **B15F** — **done:** **[`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md)**.
2. **B15F2** / **B15F3** — template editor / channel selector **read or design** slices **only** if explicitly approved.
3. **B15E2** — explicit **action execution** from the console (or dedicated flow) **only if approved**; remains guarded.
4. **B15G** — guarded **auto-publish** design **only** after explicit product/security approval.

See [`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`](B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md).

# B15D — Admin Publishing Console rich read view

**Status:** Implemented (additive read-model only).  
**Builds on:** [`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md).  
**Code:** `app/schemas/admin_publishing_console.py` · `app/services/admin_publishing_console_service.py`.  
**Handoff:** [`docs/HANDOFF_B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW_TO_NEXT_STEP.md`](HANDOFF_B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW_TO_NEXT_STEP.md).

**B15E extends B15D:** **[`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md)** adds additive per-item **`actions[]`** (read-only affordance metadata). All B15D readiness fields remain **unchanged** in meaning and **backward-compatible**.

**B15F extends the same endpoint:** **[`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md)** adds **source / template / channel / media** metadata plus future-disabled **`template_actions[]`** / **`channel_actions[]`** hints. **B15D** readiness fields (**`readiness_summary`**, **`readiness_level`**, blockers, CTA safety, **`preview_path`**, etc.) remain **unchanged** and **backward-compatible**.

---

## 1. Objective

B15D extends the **read-only** Admin Publishing Console with richer **readiness** and **action guidance** so operators can see what is ready, what is blocked, and what to open next—without adding publish automation.

---

## 2. Endpoint

- **`GET /admin/publishing-console`**
- **Still read-only:** no publish, send, retry, scheduler, or persistence/mutation from this route.
- Authentication and query parameters (`limit`, `kind`) are unchanged from B15B; see the B15B doc.

---

## 3. Additive response fields (per item)

Each **`AdminPublishingConsoleItemRead`** may include these fields (defaults keep older clients safe):

| Field | Role |
|--------|------|
| `readiness_summary` | Short machine-oriented summary (lifecycle, packaging, publish gate, B15C gate). |
| `readiness_level` | `ready` · `needs_action` · `blocked` · `published` · `unknown` (aligned from `console_status`). |
| `conversion_target_kind` | `exact_tour` · `supplier_offer_landing` · `none`. |
| `conversion_target_url` | Resolved Mini App / deep-link style URL when settings allow (may be `null`). |
| `cta_safety_status` | e.g. `exact_tour_ready`, `missing_execution_link`, `tour_not_listed`, `media_blocked`, `not_applicable`, `already_published`. |
| `primary_blocker` | First human-facing blocker when present. |
| `blocker_codes` | Short codes / step ids (e.g. `create_execution_link`, `missing_execution_link`). |
| `next_action_code` | Operator workflow action code when inferred. |
| `next_action_label` | Label for that action when present. |
| `admin_action_path` | Suggested HTTP admin path (or review-package fallback). |
| `preview_path` | e.g. `/admin/supplier-offers/{id}/showcase-preview` for offer rows; tours: `null`. |
| `source_status_summary` | Compact status line for the row. |
| `audit_hint` | Where to drill in for full audit (`GET …/review-package`, etc.). |

Existing B15B fields (`candidate_key`, `kind`, `console_status`, `offer_debug`, `tour_debug`, …) are unchanged in meaning.

---

## 4. Source of truth

The console **does not** own business rules. It **aggregates**:

- **`SupplierOfferReviewPackageService.review_package`** (conversion closure, linked tour catalog, showcase preview, operator workflow).
- **`channel_publish_exact_tour_ready`** (**B15C** exact-tour readiness for channel **Rezervă**).
- **Tour catalog visibility** reads for promotion rows (`tour_is_customer_catalog_visible`).
- **Settings** (`telegram_mini_app_url`, `telegram_bot_username`, optional short name) for URL hints.

---

## 5. Example semantics

**Ready supplier-offer candidate**

- Conversion chain and execution link satisfy B15C; `cta_safety_status` can be **`exact_tour_ready`**.
- `conversion_target_kind` **`exact_tour`** when a bridged `tour_code` exists; `readiness_level` **`ready`** when publish workflow action is enabled (same as B15B `console_status` mapping).

**Supplier-offer candidate missing execution link**

- `cta_safety_status` **`missing_execution_link`**; `blocker_codes` / `next_action_code` can point at **`create_execution_link`**.
- `readiness_level` **`needs_action`** when `console_status` is **`needs_attention`**.

**Tour promotion candidate**

- `conversion_target_kind` **`exact_tour`**; CTA gate enums reflect tour/catalog state, not supplier-offer execution links.
- `audit_hint` clarifies that supplier-offer-only CTA gate wording does not apply to tour rows; **`next_action_code`** may be `null` with an **`Open tour in admin`**-style label on `next_action_label`.

---

## 6. Tests

```powershell
python -m pytest tests/unit/test_admin_publishing_console.py -q
```

**Result:** `8 passed` (auth, shape, `kind` filters, B15D scenarios, B15E `actions[]` / affordances, B15F source/template/channel/media fields, backward-compatible keys).

---

## 7. Non-goals

- No **auto-publish**, **scheduler**, or **Telegram send** from this slice.
- No **template editor**, **channel selector**, or **media storage/rendering** here.
- No **Layer A**, **Mini App routing**, or **B15C gate** behavior changes.
- No new **migrations** for B15D.

---

## 8. Next step

**B15E** — implemented: **[`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md)** (additive **`actions[]`** on the same endpoint). **B15F** — implemented: **[`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md)** (template/source/channel/media read metadata). Further roadmap: **B15F2** / **B15F3** / **B15E2** (only if approved), **B15G** (guarded auto-publish **only** after explicit design approval)—see [`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`](B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md).

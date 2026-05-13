# B15F — Admin Publishing Console template / source / channel read model

**Status:** Implemented (additive read-model only).  
**Builds on:** [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md), [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md), [`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md).  
**Code:** `app/schemas/admin_publishing_console.py` · `app/services/admin_publishing_console_service.py`.  
**Handoff:** [`docs/HANDOFF_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL_TO_NEXT_STEP.md`](HANDOFF_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL_TO_NEXT_STEP.md).  
**Original prompt:** [`docs/CURSOR_PROMPT_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](CURSOR_PROMPT_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md).  
**Foundation closure (B15B–B15F):** [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md).

---

## 1. Objective

B15F extends the **read-only** `GET /admin/publishing-console` response with **source**, **template / packaging**, **channel**, and **media policy** metadata so operators can see where a candidate row comes from, what template/read path exists, whether a showcase channel is configured, and how cover/media gates read today—**without** building a template editor or channel selector.

---

## 2. Endpoint

- **`GET /admin/publishing-console`**
- **Remains read-only:** no mutation, send, retry, publish, scheduler, template editing, or channel selection from this route.

---

## 3. New read-model sections (per item)

1. **Source metadata** — what primary object backs the row (`supplier_offer` vs `tour`).
2. **Template / source metadata** — showcase template kind, version string, availability of packaging-driven preview material, human summary.
3. **Channel metadata** — intended channel family (e.g. Telegram showcase), configuration status, optional ref (e.g. channel id from settings).
4. **Media policy metadata** — coarse publish/media stance derived from review-package cover quality + showcase preview publication mode (metadata-first; not durable asset pipeline).
5. **Future template/channel affordances** — static **`template_actions[]`** and **`channel_actions[]`** rows documenting UX not built yet (`implemented: false`).

---

## 4. Schema: new types and fields

**Literal / enum types** (string values on `AdminPublishingConsoleItemRead`):

| Type name | Values |
|-----------|--------|
| `PublishingConsoleSourceKind` | `supplier_offer`, `tour` |
| `PublishingConsoleTemplateKind` | `supplier_offer_showcase`, `tour_promotion_placeholder`, `none` |
| `PublishingConsoleTemplateSourceStatus` | `available`, `partial`, `unavailable`, `not_applicable` |
| `PublishingConsoleChannelKind` | `telegram_showcase_channel`, `none` |
| `PublishingConsoleChannelStatus` | `configured`, `not_configured`, `not_applicable` |
| `PublishingConsoleMediaPolicyStatus` | `publish_safe_metadata_only`, `media_review_pending`, `media_blocked`, `text_only_channel_ok`, `not_applicable` |

**Future capability hint model:** `AdminPublishingConsoleFutureCapabilityHintRead`

| Field | Purpose |
|--------|---------|
| `code` | Stable hint id (e.g. `edit_showcase_template`, `select_channel`). |
| `label` | Human-facing label. |
| `implemented` | `false` in B15F for these placeholders. |
| `enabled` | `false` when not implemented. |
| `disabled_reason` | Why disabled (e.g. editor/selector not in B15F). |

**Additive fields on `AdminPublishingConsoleItemRead`:**

| Section | Fields |
|---------|--------|
| Source | `source_kind`, `source_id`, `source_title` |
| Template | `template_kind`, `template_version`, `template_source_status`, `template_source_summary`, `template_preview_available`, `template_preview_path` |
| Channel | `channel_kind`, `channel_status`, `channel_ref`, `channel_summary` |
| Media policy | `media_policy_status`, `media_summary` |
| Future hints | `template_actions`, `channel_actions` (each `list[AdminPublishingConsoleFutureCapabilityHintRead]`) |

B15D readiness fields and B15E **`actions[]`** are unchanged in meaning and remain on the same model.

---

## 5. Supplier-offer semantics

- **`source_kind`** **`supplier_offer`**; **`source_id`** is the offer id; **`source_title`** from the console row title.
- **`template_kind`** **`supplier_offer_showcase`**. Template availability is driven by **`review-package`** → **`showcase_template_preview`** (effective template id + preview fact lines); summaries reference packaging / B12B-style deterministic preview.
- **`template_preview_available`** is **`true`** for supplier rows; **`template_preview_path`** is **`/admin/supplier-offers/{id}/showcase-preview`** (HTTP read/preview route—not a mutation).
- **Channel:** **`channel_kind`** **`telegram_showcase_channel`**; **`channel_status`** / **`channel_ref`** / **`channel_summary`** reflect whether **`telegram_offer_showcase_channel_id`** (settings) is set.
- **Media policy:** derived from **`cover_media_quality_review`**, **`showcase_preview.publication_mode`**, and **`cover_media_publish_blocking_reasons`** (blocking → `media_blocked`; warnings → `media_review_pending`; text-only mode → `text_only_channel_ok`; else metadata-only publish stance → `publish_safe_metadata_only` with explanatory **`media_summary`**).

---

## 6. Tour promotion semantics

- **`source_kind`** **`tour`**; **`source_id`** is the tour id.
- **`template_kind`** **`tour_promotion_placeholder`**; **`template_version`** **`not_implemented`**; **`template_source_status`** **`not_applicable`** with a short summary that tour promotion templates are not implemented in B15F.
- **`template_preview_available`** **`false`**; **`template_preview_path`** **`null`**.
- **`channel_kind`** **`none`**; **`channel_status`** **`not_applicable`**; no supplier-offer showcase channel binding on these rows.
- **`media_policy_status`** **`not_applicable`**; **`media_summary`** clarifies supplier-offer cover gating does not apply.
- Same static **`template_actions`** / **`channel_actions`** as supplier rows (future UX only)—no supplier-offer-only template or channel projection is implied.

---

## 7. Safety

- **Metadata only:** the console service **does not** call mutation services, publish adapters, or Telegram I/O for B15F.
- **No** Telegram send, publish, or retry from this endpoint.
- **No** bridge, catalog activation, or execution-link **creation** from the console read path.
- **No** Layer A changes; **no** Mini App routing changes; **no** migrations for B15F.

---

## 8. Tests

```powershell
python -m pytest tests/unit/test_admin_publishing_console.py -q
```

**Result:** `8 passed`.

---

## 9. Next steps (approval-gated)

1. **B15F2** — Template editor design/read model **only** if explicitly approved.
2. **B15F3** — Channel selector design/read model **only** if explicitly approved.
3. **B15E2** — Explicit action execution from the console (or dedicated flow) **only** if approved.
4. **B15G** — Guarded auto-publish design **only** after explicit approval.

See [`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`](B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md).

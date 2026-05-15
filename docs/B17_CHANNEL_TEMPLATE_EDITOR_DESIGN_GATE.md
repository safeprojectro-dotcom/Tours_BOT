# B17 — Channel / Template Editor Design Gate

**Status:** **B17** (this file) = design / documentation gate for **B17C+** (mutations: persisted selection, drafts, publish automation — separately chartered). **B17A** + **B17B** = read-only **`GET …/editor`** — **shipped** (see records below). **B17B exposes response metadata only on the read-only editor GET; it does not persist channel selection, template selection, draft edits, or editor state.**  
**Purpose:** Define conservative boundaries before channel/template **persistence**, draft editing, or publish automation.  
**Aligned with:** closed **B15** publishing console foundation ([`docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md`](B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md), [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md)), **B15P** UI hints ([`docs/HANDOFF_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md`](HANDOFF_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md)), **B15G** auto-publish design-only ([`docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md`](B15G_GUARDED_AUTO_PUBLISH_DESIGN.md)), marketplace context ([`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`](IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md), [`docs/TECH_SPEC_TOURS_BOT_v1.1.md`](TECH_SPEC_TOURS_BOT_v1.1.md)).

**References / gaps:** `docs/BUSINESS-план-v2.txt` is **not present** in-repo; use [`docs/BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md`](BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md) and [`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) for v2 business-line context.  
**Terminology alignment (read-only today):** [`app/schemas/admin_publishing_console.py`](app/schemas/admin_publishing_console.py) — e.g. `PublishingConsoleChannelKind`, `PublishingConsoleTemplateFamily`, `PublishingConsoleTemplateLibraryFamily`, B15P `ui_card` / `ui_sections`; [`app/services/admin_publishing_console_service.py`](app/services/admin_publishing_console_service.py) — how list/detail read models are composed (B17 must **extend**, not replace).

### B17A — Implementation record (read-only, in-repo)

**Status:** **Shipped** — HTTP **GET** only; **B17** remains the **design gate** for **B17C+** (DB persistence for selection/drafts, publish — separate charter), not for the read-only **B17A/B17B** editor **GET** surface.

| Deliverable | Notes |
|-------------|--------|
| **`GET /admin/publishing-console/supplier-offers/{offer_id}/editor`** | Response **`AdminPublishingConsoleEditorDetailRead`**; **404** if offer missing; same admin auth as other **`/admin`** routes. |
| **Section DTOs** | **`channel_section`**, **`template_section`**, **`preview_section`**, **`cta_section`**, **`media_section`**, **`readiness_section`**, **`safety_section`**; **`future_actions`** (merged template/channel capability hints; metadata only / disabled where not implemented); **`source_snapshot`** with **`publish_readiness`**, **`console_preview`**, **`template_library`**, **`preview_payload`**, **`ui_card`**, **`safety_summary`**. |
| **Boundaries** | **No** channel/template selection persistence; **no** draft edit persistence; **no** frontend; **no** Telegram I/O; **no** publish attempts; **no** scheduler; **no** auto-publish; **no** **`prepare_conversion_chain`** execution from this **GET**; **no** Layer A mutation; **no** Mini App/B11 routing changes; **no** migration. |

**Handoff:** [`docs/HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md`](HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md)

### B17B — Implementation record (read-only response metadata, in-repo)

**Status:** **Shipped** — extends the same **`GET …/editor`** only; **no** new routes; **no** POST/PATCH; **no** DB persistence.

| Deliverable | Notes |
|-------------|--------|
| **`channel_selection`**, **`template_selection`** | Additive fields on **`AdminPublishingConsoleEditorDetailRead`**: picker-oriented metadata (options, current projection, recommendation, disabled reasons, safety notes, **`future_capability_hints`**) derived from existing B15 row / **`template_library`**. |
| **Boundaries** | **B17B exposes response metadata only on the read-only editor GET; it does not persist channel selection, template selection, draft edits, or editor state.** Same non-goals as **B17A** for Telegram, publish, scheduler, **`prepare_conversion_chain`** on this **GET**, Layer A, Mini App/B11, migration. |

**Handoff:** [`docs/HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md`](HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md)

### B17Z — Read-only editor foundation closure (documentation only)

**Status:** **Closed (docs).** Summarizes **B17** + **B17A** + **B17A.1** + **B17B** as a single read-only foundation line; **no** runtime changes in B17Z. See **[`docs/B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md`](B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md)**. **B17C+** mutations (persistent selection, drafts, publish) remain **future-gated** and separately chartered.

---

## 1. Status and scope

| Rule | Applies |
|------|---------|
| The **B17** design gate (**this** markdown) authorizes **B17C+** implementation only when separately chartered | Yes |
| **B17A** + **B17B** read-only **`GET …/editor`** | **Shipped** in-repo — see **B17A** / **B17B** records above |
| No **publish** / **send** / **scheduler** / **auto-publish** introduced **by B17C+** without explicit go/no-go | Yes |
| No **migration** | Yes |
| No **admin web frontend** implementation | Yes |
| No **Telegram** (or other provider) **API calls** introduced by this gate | Yes |

This document **does not** authorize **mutating** implementation beyond the **B17A/B17B** read-only **GET** slices already shipped (see records above). It records **requirements and boundaries** for future charters (**B17C+**).

---

## 2. Product purpose (future)

The future **Channel / Template Editor** lets operators:

- **Choose or review** channel strategy (where content *may* go, subject to gates).
- **Choose or review** template **family** and **variant** (structured layouts, not raw supplier copy as the publish source).
- **Preview** composed content **before** any customer-visible or channel-visible action.
- **See** whether the next step is **read-only**, **local preview**, **guarded internal preparation** (e.g. `prepare_conversion_chain`), or **public publish** (explicit, confirmation-gated).

**Non-goals for messaging clarity:**

- Do **not** treat **showcase / discovery** copy as **booking or payment truth**.
- **Mini App / catalog / execution link** state remains **execution truth**; channel posts are **softer** and must not imply guarantees the system has not checked.

---

## 3. Relationship to the closed B15 foundation

B15 **already** exposes read models and affordances. B17 **builds on** these; it **must not** replace or fork them into a parallel “truth.”

| B15 surface | Role today | B17 future use |
|-------------|------------|----------------|
| `publish_readiness` | Suggest-only readiness, gates, UX fields | Editor shows same gates; **draft/template choice** may not bypass gate semantics |
| `console_preview` | Compact preview/display metadata | Editor **detail** may deepen layout; list row stays consistent |
| `template_library` | Variants, selection hints, `future` entries | Editor **selects** among variants **after** product approves mutation slice |
| `preview_payload` | Structured payload mirror for admin UI | Editor **preview** should align with or **supersede display-only** payload (not double-truth) |
| `ui_card` / `ui_sections` | Presentation hints for a future admin UI | Editor UX **consumes** these as input for grouping/labels |
| `GET …/publishing-console/supplier-offers/{offer_id}` | Aggregated detail read view | Natural companion: **B17A** **`GET …/editor`** — section-oriented read-only layout |
| `prepare_conversion_chain` (POST, guarded) | Internal bridge/catalog/link prep **below** Telegram publish | Editor labels it **guarded internal**, **not** “publish to channel” |

**Principle:** additive APIs and DTOs only in future implementation; **preserve** existing GET contracts and safety flags (`read_only`, `no_telegram_io`, etc.) where they apply.

---

## 4. Channel model (conceptual — future)

*Current MVP read-model channel kinds in code are narrow (e.g. `telegram_showcase_channel`, `none` in `PublishingConsoleChannelKind`). The table below is the **product target taxonomy** for B17 planning; most rows are **future** until explicitly implemented.*

| Channel family | MVP readiness | Allowed content (typical) | Direct publish (future) | Approval | Media | CTA target | Audit (future) |
|----------------|---------------|----------------------------|-------------------------|----------|-------|------------|----------------|
| `telegram_showcase_channel` | **First likely executable** | Text/photo post, links | Yes, **explicit** confirm | **Mandatory** admin | Often required for photo mode; policy per B7 | **Exact-tour** Mini App link when B15C gates pass | Attempt + message ids + actor |
| `telegram_group_discussion` | Future | Short promo, link | Optional; policy TBD | Mandatory | Optional | Mini App / bot | Attempt + link |
| `mini_app_banner` | Future | In-app promo slots | No Telegram send; in-app only | Mandatory | Optional | Tour/offer routes | Config audit |
| `whatsapp_broadcast` | Future | Text/media broadcast | If product approves provider | Mandatory | TBD | Deep link / web | Provider message ids |
| `instagram_post` | Future | Card + caption | Provider API | Mandatory | Usually | Link in bio / ad | External refs |
| `facebook_post` | Future | Card + caption | Provider API | Mandatory | Optional | Link | External refs |
| `external_marketplace` | Future | Listing copy | Per integration | Mandatory | Per platform | Platform PDP | Integration log |
| `none` / `not_configured` | **Now** | N/A | **No** | N/A | N/A | N/A | N/A |

**Notes:**

- **Telegram showcase** remains the default “marketing channel” in scope discussions; others are **placeholders** until chartered.
- Any **future** direct publish requires **separate** go/no-go (see §8, §14 **B17E/F**).

---

## 5. Template model (conceptual — future)

Align names with **B15** where they already exist (`PublishingConsoleTemplateFamily`, template library entries, template ids such as `supplier_offer_showcase`, `custom_request_cta`, `tour_promotion_placeholder`, `tour_promotion_rich_card` in service/constants). Additional rows are **marketing patterns** for later product selection — **not** implemented until chartered.

| Template family / variant | Source data required | Safety gates | Prohibited claims (non-exhaustive) | CTA type | Channel compatibility (typical) | Live availability / urgency | Discounts |
|---------------------------|----------------------|--------------|------------------------------------|----------|----------------------------------|-----------------------------|-----------|
| `supplier_offer_showcase` | Approved packaging, showcase preview, cover policy | B5/B6/B7, B15C execution link when Rezervă | Fake scarcity, unverified price | Rezervă / Detalii → Mini App | `telegram_showcase_channel` | **Only** if **inventory field** confirms | **Only** if **pricing fields** confirm |
| `custom_request_cta` | Same + assisted-closure mode | Same + mode-specific copy | Implies instant booking without ops | RFQ / consult | Showcase + private ops | Same rules | Same rules |
| `tour_promotion_placeholder` | Tour catalog fields | Catalog visible window | “Last seats” without inventory | Exact-tour link | Placeholder today | **No** urgency | **No** promo claims |
| `tour_promotion_rich_card` | Tour + creative assets | **Future** compose gate | Same | Same | Future | Same | Same |
| `per_seat_standard` | Per-seat tour + dates | Catalog + execution link | Overbook | Standard Rezervă | Showcase | From `seats_available` only | From **source** discount fields only |
| `full_bus_private_group` | Group/private semantics | Capacity, mode | Public per-seat confusion | Contact / quote | Showcase / ops | From capacity truth | If contract allows |
| `last_seats_urgent` | **Low** `seats_available` threshold | **Blocked** unless rule fires from **live** counts | Invented urgency | Rezervă | Showcase | **Required** signal | N/A unless sourced |
| `early_bird_discount` | Priced offer + window | Time window in source | Expired / fake discount | Rezervă | Showcase | N/A | **Required** in source |
| `supplier_service_promo` | Service descriptors | Claims match intake | Overpromise | Soft CTA | Various | N/A | N/A unless sourced |
| `brand_awareness_post` | Brand-safe copy | No booking claims | Availability numbers | Learn more | Social | N/A | N/A |

---

## 6. Truth and safety rules

These are **non-negotiable** for any future editor or automation:

- **No fake urgency** — “last seats,” “almost full,” countdowns only when **live inventory / rules** support them.
- **No discount** language unless **source fields** (or approved pricing snapshot) confirm it.
- **No publish** straight from **unreviewed supplier raw input** — AI and supplier text remain **draft** until **admin-approved** package (existing B1/B5 invariant).
- **AI content** = **draft / review** only; never auto-public **send**.
- **Admin approval** mandatory for **public** channel publish (human confirmation; see §9).
- **Telegram showcase** = discovery / soft CTA; **Mini App + catalog + execution link** = **execution truth**.
- **visibility ≠ bookability** — catalog/listing visibility does not imply channel post is safe or CTA is exact-tour-ready.
- **publish_readiness ≠ payment/booking readiness** — readiness DTOs describe *marketing/publish* path, not Layer A payment state.
- **`prepare_conversion_chain` ≠ Telegram publish** — internal preparation only; **separate** POST and labeling in UI.

---

## 7. Editor workflow states (future — not implemented)

| State | Meaning | Now vs future |
|-------|---------|---------------|
| `not_configured` | No channel/template choice **persisted in DB** | **Future** (**B17C+**); **B17B** may still surface read-only projection metadata on **`GET …/editor`** |
| `draft_available` | Draft exists but not preview-ready | Future |
| `preview_ready` | Deterministic preview can render | Future |
| `needs_review` | Blocking gates or policy warnings | Partially mirrored by `publish_readiness` **today** (read-only) |
| `blocked` | Hard blockers | Mirrors console `blocked` / readiness today |
| `approved_for_manual_publish` | Human approved content; **not** sent | Future |
| `queued_for_publish` | Schedule/queue holding (if product adopts) | **Future-only** (see B15G) |
| `publish_in_progress` | Provider send in flight | Future |
| `published` | Message/live artifact recorded | Partially mirrored by publication summaries **today** |
| `publish_failed` | Attempt failed; **no** silent retry | Future |
| `unpublished` / `archived` | Taken down or retired | Future |

**Today:** B15 **does not** persist these as an editor state machine; operators use **`review-package`**, publishing console read models, and existing **publish** flows outside this document.

---

## 8. Action taxonomy

Classify **future** editor actions. **“Allowed now”** means already available **elsewhere** in product (not necessarily from a unified editor UI).

| Action | Description | Classification |
|--------|-------------|----------------|
| `safe_read` | GET review-package, console, plans | **Allowed now** (B15/B16 read paths) |
| `local_preview` | Render HTML/text preview **without** provider I/O | **Allowed now** (e.g. showcase preview reads); editor may consolidate |
| `edit_draft` | Change draft copy/layout in admin | **Future guarded mutation** (draft store only) |
| `select_template` | Persist template variant | **Future guarded mutation** (metadata only); **no** send |
| `select_channel` | Persist channel target | **Future guarded mutation**; **no** send until publish |
| `guarded_prepare_chain` | `prepare_conversion_chain` POST | **Allowed now** as guarded POST; editor must **label** separately from publish |
| `request_approval` | Submit draft for second admin | **Future** workflow |
| `confirm_publish` | Explicit confirm + idempotency | **Future public side effect** — **separate go/no-go** |
| `schedule_publish` | Queue for later | **Future** — **forbidden** until B15G/B17 schedule charter |
| `retry_publish` | Retry after failure | **Future public side effect** — explicit only; **no** default auto-retry |
| `cancel_schedule` | Remove queued job | **Future** |
| `unpublish` / `archive` | Remove or hide public artifact | **Future** — **separate** design |

---

## 9. Confirmation and audit rules (future implementation requirements)

Any **public side-effect** publish path **must**:

1. Require **explicit confirmation** (no one-click “Send” without friction).
2. Record **actor identity** (admin user / token subject / Telegram admin id — product-specific).
3. Require **idempotency key** for mutating publish attempts (align with **`admin_guarded_action_*`** precedent).
4. Write **audit rows**: who, what, when, channel, template version, snapshot id.
5. Store an **immutable preview snapshot** (hash or JSON blob) **before** send for disputes/regression.
6. After success, **store channel message ids** / URLs (Telegram `message_id`, chat id, permalink).
7. **Retry** is **opt-in** per attempt, **not** background auto-retry by default.
8. **Rollback / unpublish** is a **separate** design (may be provider-limited); not assumed in MVP.

---

## 10. Data model sketch (conceptual — no migration)

| Entity | Purpose | Why future-only |
|--------|---------|-----------------|
| `publishing_channels` | Registry of configured channels, credentials refs, policies | No editor DB today |
| `publishing_templates` | Template definitions, versions, **family** | Templates live in code + review-package today |
| `publishing_template_variants` | Per-family variants (layout, tone, locale) | B15K is **read-only** hints |
| `publishing_drafts` | Edited copy / layout **before** publish | No draft persistence in B17 gate |
| `publishing_attempts` | Mirrors/replaces ad-hoc attempt tracking for editor-initiated sends | Attempts exist for showcase; editor may unify |
| `publishing_schedules` | Queue / cron hooks | **Forbidden** until explicit schedule charter |
| `publishing_channel_messages` | Mapping offer/tour → provider message artifacts | Partially implied by publications today |
| `publishing_audit_events` | Fine-grained editor audit | May extend **B16E** patterns |

---

## 11. API sketch (**B17A** editor GET implemented; remainder future)

*Illustrative for **B17C+**.* **`GET …/supplier-offers/{offer_id}/editor`** is **live** (read-only; **B17A** sections + **B17B** **`channel_selection`** / **`template_selection`** metadata — **not** persisted).

**GET (target: safe_read)**

| Endpoint | Intent | Classification |
|----------|--------|----------------|
| `GET /admin/publishing-console/channels` | List channel strategies + **configured** flag | safe_read (**future**) |
| `GET /admin/publishing-console/templates` | List template families/variants | safe_read (**future**) |
| `GET /admin/publishing-console/supplier-offers/{offer_id}/editor` | Editor sections + **`source_snapshot`** (**B17A**) + **`channel_selection`** / **`template_selection`** (**B17B** — response only, **not** persisted) | safe_read (**shipped**) |
| `GET /admin/publishing-console/supplier-offers/{offer_id}/editor/preview` | Deterministic preview payload | safe_read (**future**) |

**POST / PATCH (future)**

| Operation | Classification |
|-----------|----------------|
| Select template / channel | **Draft mutation** — no provider I/O |
| Update draft copy | **Draft mutation** |
| Request approval | **Workflow mutation** |
| Confirm publish | **Guarded public side effect** |
| Schedule publish | **Future only** (charter) |
| Retry publish | **Guarded public side effect** |
| Cancel scheduled publish | **Future only** |

---

## 12. Frontend UX guidance (admin)

Recommended sections (map to B15 `ui_sections` / `ui_card`):

- **Channel** — current/future channel; disabled with **reason** when not configured.
- **Template** — family + variant; show **`template_library`** hints.
- **Preview** — `preview_payload` / live compose; **read-only** until edit slice exists.
- **CTA** — exact-tour vs landing; **B15C** safety clear.
- **Media** — cover / `publish_safe` policy reminders (B7).
- **Readiness** — `publish_readiness` gates; no false “ready to book.”
- **Safety** — short copy: read-only vs guarded POST vs publish **never** from this button.
- **Audit** — last attempt, actor, id (when available).

Rules:

- Use **B15** `ui_card` / detail as **inputs**, not bypass them.
- **Disabled / future** actions must show **why** (mirror `actions[]` / `template_actions` patterns).
- **Safety copy** adjacent to any control that could be mistaken for **Send**.
- **Never** “Send now” **without** confirmation + audit trail design.
- **No hidden auto-publish** or schedule toggles in **read-only** slices.

---

## 13. Testing strategy (future implementation)

When implementation exists:

- **Read-only editor GET** — **no** DB mutation except read; snapshot tests on DTO shape.
- **Draft edit** — mutates **draft** tables only; **no** Telegram mocks invoked.
- **Template/channel select** — **no** publish; **no** outbound HTTP.
- **Confirm publish** — requires auth, confirmation flag, actor, idempotency; **integration** tests **mock** Telegram.
- **Replay** — same idempotency key does not double-send; or returns prior result safely.
- **Failure** — records **`publish_failed`**; **does not** corrupt offer/tour source rows.
- **No Layer A mutation** from editor publish path.
- **No Mini App / B11 routing** mutation from editor.
- **Copy guards** — unit tests forbid urgency/discount strings unless **fixture** supplies inventory/discount facts.

---

## 14. Rollout plan (recommended incremental order)

| Phase | Label | Scope |
|-------|-------|--------|
| 1 | **B17A** | Read-only **editor detail** **`GET …/editor`** — **shipped** (no mutation); handoff [`HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md`](HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md) |
| 2 | **B17B** | **Channel/template selection metadata** on the read-only editor **`GET`** — **response body only**; **B17B exposes response metadata only on the read-only editor GET; it does not persist channel selection, template selection, draft edits, or editor state.** **No** send. Handoff: [`HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md`](HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md) |
| 3 | **B17C** | **Draft copy** editor — **no** publish |
| 4 | **B17D** | **Manual approval** state — **no** provider send |
| 5 | **B17E** | **Public publish execution** — **design gate** (confirmation, audit, idempotency) |
| 6 | **B17F** | **Telegram publish** implementation — **only** after explicit **go/no-go** |
| 7 | **B17G** | **Schedule / retry / unpublish** — later charter (**B15G** alignment) |

---

## 15. Explicit non-goals (this gate)

- **No** further implementation **authorized by this markdown alone** beyond documenting **B17C+** requirements (**B17A/B17B** **`GET …/editor`** are separate shipped read-only slices — see top of this doc).
- **No** public **publish** or **schedule** from **B17C+** without charter.
- **No** **auto-publish** now (**B15G** remains design-only for automation modes).
- **No** provider (**Telegram**, Meta, etc.) **API** integration triggered by this gate.
- **No** **migration** specified here.
- **No** **admin web frontend** shipped here.
- **No** **AI** auto-send to public channels.
- **No** **Layer A** booking/payment mutation.
- **No** **Mini App** or **B11** deep-link routing changes.

---

## Related handoffs (B15 read surfaces)

- [`docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md`](HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md)
- [`docs/HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md`](HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md)
- [`docs/HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW.md`](HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW.md)
- [`docs/HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md`](HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md)
- [`docs/HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md`](HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md)
- [`docs/B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md`](B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md)

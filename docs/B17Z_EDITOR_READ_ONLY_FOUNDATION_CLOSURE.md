
# B17Z — Editor Read-only Foundation Closure

**Project:** Tours_BOT  

**Status:** **Closed (documentation / architecture checkpoint only).**  

**B17Z does not change runtime code**, schemas, services, routes, tests, or data. **No** migration, **no** Telegram/public side effects, **no** publish/scheduler/auto-publish.

---

## 1. Status

- The **B17 read-only editor foundation** (**B17** gate + **B17A** + **B17A.1** + **B17B**) is **closed** as a cohesive read-model slice.
- **B17Z** records closure only; it **does not** ship behavior.
- **Aligned with:** **[`docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md`](B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md)** (product boundaries), **[`docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md`](B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md)** / **[`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md)** (publishing console foundation), **[`docs/HANDOFF_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md`](HANDOFF_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md)** (B15P presentation hints consumed by the same read models).

---

## 2. Scope closed

| Slice | Role |
|-------|------|
| **B17** | Design gate: channel/template editor boundaries, truth/safety rules, future action taxonomy, rollout phases — **[`docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md`](B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md)** |
| **B17A** | Read-only editor detail **`GET /admin/publishing-console/supplier-offers/{offer_id}/editor`** — section-oriented layout + **`future_actions`** + **`source_snapshot`** — **[`docs/HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md`](HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md)** |
| **B17A.1** | Explicit machine-readable **`can_*`**, **`preview_available`**, expanded **`safety_section`** booleans on the same **GET** (frontend safety chrome); **no** behavior change |
| **B17B** | Additive **`channel_selection`** / **`template_selection`** — **response JSON only** — **[`docs/HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md`](HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md)** |

---

## 3. Available read-only editor surface

**Endpoint**

`GET /admin/publishing-console/supplier-offers/{offer_id}/editor`

**Top-level / sections (representative)**

- **`channel_section`**, **`template_section`**, **`preview_section`**, **`cta_section`**, **`media_section`**, **`readiness_section`**, **`safety_section`**
- **`future_actions`**
- **`source_snapshot`**
- **`channel_selection`**, **`template_selection`** (B17B)

(Plus navigation/metadata fields documented on **`AdminPublishingConsoleEditorDetailRead`** — e.g. **`editor_status`**, paths, **`editor_notice`**, **`generated_at`**.)

---

## 4. Source snapshot

**`source_snapshot`** embeds the same B15/B15P nested data as the publishing-console supplier-offer detail read path:

- **`publish_readiness`**
- **`console_preview`**
- **`template_library`**
- **`preview_payload`**
- **`ui_card`** (list-row presentation hint)
- **`safety_summary`**

The editor **GET** **reuses** this bundle; it does **not** define a second source of truth.

---

## 5. Safety flags (`safety_section`)

Explicit machine-readable flags (all **`true`** on this **GET**):

- **`read_only`**
- **`no_telegram_io`**
- **`no_publish_attempt`**
- **`no_scheduler`**
- **`no_auto_publish`**
- **`no_prepare_chain_execution`**
- **`no_layer_a_mutation`**
- **`no_mini_app_b11_change`**

Human-readable safety copy remains in **`detail_notice`**, **`ui_card_safety_line`**, **`editor_boundary_note`**.

---

## 6. Selection metadata (B17B)

- **`channel_selection`** and **`template_selection`** are **response metadata only**.
- **No** DB persistence for channel/template choice, draft body, or editor state.
- **No** POST/PATCH on this surface for selection.
- Values are derived from existing settings/review-package/console row projections and **`template_library`**.

---

## 7. Disabled future public actions

- **`confirm_publish`** and **`schedule_publish`** appear in **`future_actions`** as **`FutureCapabilityHint`** rows with **`implemented=false`**, **`enabled=false`**, and explicit **`disabled_reason`** (not implemented on this read-only slice; separate go/no-go for real publish/schedule).
- **Actual** public publish / schedule automation remains **out of scope** for this foundation and **future-gated**.

---

## 8. Railway smoke evidence (operator)

**Context:** **`GET /admin/publishing-console/supplier-offers/12/editor`** — **HTTP 200**.

**Recorded observations (Offer #12)**

| Check | Result |
|--------|--------|
| Endpoint | **200** |
| **ChannelRecommended** | `telegram_showcase_channel` |
| **ChannelCurrentStatus** | `configured` |
| **ChannelOptionsCount** | **2** |
| **TelegramConfigured** | **True** |
| **TelegramRecommended** | **True** |
| **TelegramCurrent** | **True** |
| **TemplateSelected** | `custom_request_cta` |
| **TemplateRecommended** | `custom_request_cta` |
| **TemplateOptionsCount** | **2** |
| **CustomRequestAvailable** | `available` |
| **CustomRequestRecommended** | **True** |
| **CustomRequestCurrent** | **True** |
| **ConfirmPublishEnabled** | **False** |
| **SchedulePublishEnabled** | **False** |
| **SafetyReadOnly** | **True** |
| **NoTelegramIo** | **True** |
| **NoPublishAttempt** | **True** |
| **NoAutoPublish** | **True** |

**Interpretation:** read-only metadata and safety flags present; publish/schedule hints disabled; **no** selection persistence implied by the API contract.

---

## 9. What is intentionally not done

- **No** persisted channel/template selection
- **No** draft copy editor or draft store
- **No** approval state persistence for the editor
- **No** Telegram publish/send/retry from this **GET**
- **No** scheduler / **no** auto-publish / **no** batch publish
- **No** publish attempts created by this **GET**
- **No** **`prepare_conversion_chain`** **execution** from this **GET**
- **No** Layer A mutation
- **No** Mini App / B11 routing changes
- **No** migration for B17A/B17A.1/B17B/B17Z

---

## 10. Future gated work

**Separate design and/or explicit go/no-go** before implementation:

- **B17C** — draft-copy editor (design gate first)
- **Persistent** channel/template selection (guarded mutations)
- **Approval** workflow persistence
- **Public publish execution** (confirmation, audit, idempotency)
- **Schedule / retry / unpublish**
- **Telegram** (or other provider) **publish** implementation
- **Campaign / channel automation**

Rollout alignment remains in the B17 design gate **§14** (B17C–B17G as product charters **[`docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md`](B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md)**).

---

## 11. Relationship to upcoming priority clusters

After this closure, product/tech planning may prioritize:

### Marketing cluster — **M1** (design gate)

**M1 — Marketing Identity & Deep Link Capture Design Gate**

- **Rezervă / Catalog** CTA model alignment
- **source / campaign / referral** tracking
- **Audience profiles**, **events**, **segments**
- **Consent** baseline
- **Marketing QR / entry points** (non-order QR)

**Out of scope for M1:** marketing **broadcasts** / bulk sends.

### QR cluster — split concerns

1. **Marketing QR / entry points** — belongs under **M1** (flyer, bus, partner, catalog, exact tour, referral entry).
2. **Secure Order / Ticket / Boarding QR** — booking QR, payment/order status QR, boarding QR, passenger check-in, secure tokens, boarding scans — **future block O1 — Order / Ticket QR & Boarding Validation Design Gate**.

---

## 12. Recommended next

1. **Treat B17Z as closed** — use this doc as the checkpoint for the read-only editor line.
2. Use **[`docs/OPERATIONAL_AUTOMATION_ROADMAP.md`](OPERATIONAL_AUTOMATION_ROADMAP.md)** as the broader planning layer for post-B17 operational automation priorities.
3. **Open M1** design gate next when marketing/deep-link capture is the chosen priority.
4. **Hold O1** until operational secure QR / boarding validation needs a chartered design (can follow M1 or run in parallel if resourcing allows — product decision).
5. **Do not** jump to publish automation or Telegram send without **B17E/F**-class go/no-go and implementation charter.

---

## Related handoffs

- **[`docs/HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md`](HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md)**
- **[`docs/HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md`](HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md)**
- **[`docs/OPERATIONAL_AUTOMATION_ROADMAP.md`](OPERATIONAL_AUTOMATION_ROADMAP.md)**
- Prompt (input spec): **[`docs/CURSOR_PROMPT_B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md`](CURSOR_PROMPT_B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md)**

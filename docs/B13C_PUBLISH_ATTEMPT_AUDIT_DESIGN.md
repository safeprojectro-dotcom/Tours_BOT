# B13C — Publish attempt / audit design

**Project:** Tours_BOT. **B13C slice:** design documentation. **Update:** **B13D** supplies the attempt table; **B13E** wires **`publish`** to create/update attempt rows (**§11**); **B13F** exposes read-only attempt history via **`review-package`** and Telegram admin detail (**§12**). **No** automatic retry or **`idempotency_key`** enforcement yet.

**Related:** [`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md) · [`docs/HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md`](HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md) · [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) · [`docs/HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md) · [`docs/HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP.md`](HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP.md) · [`docs/HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`](HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md) · [`docs/HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md`](HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md) · [`docs/HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md`](HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md).

---

## 1. Purpose

Publish attempt / audit design is needed because showcase publish is a **public side effect**:

- **Accountability** — operators and automation need a clear record of *who* triggered publish and *what* was sent.
- **Duplicate prevention** — retries and double-clicks must not silently create duplicate channel posts.
- **Provider reference tracking** — store or correlate **`chat_id`** / **`message_id`** (and future multi-channel receipts) with a **logical** publish attempt, not only on **`SupplierOffer`**.
- **Operator traceability** — distinguish HTTP admin vs Telegram bot (**`telegram:{admin_id}`** style) for audits.
- **Future retries** — classify failures (transient vs terminal) only after an idempotency contract exists.
- **Future multi-channel** — one offer may eventually have multiple channel attempts; attempts must not collapse into ambiguous state.

---

## 2. Current behavior baseline

**Entry points:** HTTP **`POST /admin/supplier-offers/{offer_id}/publish`** and Telegram **C2B8B** confirm both invoke **`SupplierOfferModerationService.publish`** (after **read-model** / UX gates on the bot side).

**In-process flow (today):**

```text
admin action / HTTP publish
→ lifecycle APPROVED + channel/token config checks (moderation service)
→ build_showcase_publication
→ TelegramShowcaseChannelAdapter.publish
→ send_showcase_publication (Telegram Bot API)
→ on success: SupplierOffer → lifecycle PUBLISHED, published_at,
             showcase_chat_id, showcase_message_id (same DB transaction path)
→ on Telegram error: TelegramShowcaseSendError → HTTP/Telegram error; offer stays APPROVED
```

**Gaps today (by design or not yet implemented):**

- **B13E (implemented):** durable **attempt rows** on **`publish`** — see **§11**.
- **Still:** **no** cross-request **idempotency** usage on **`ShowcaseChannelPublishRequest.idempotency_key`**; **no** operator “safe resend” / dedupe automation.
- **No** automatic retry of Telegram send.
- **Edge risk (unchanged):** Telegram may accept a message while the **DB commit** for **`SupplierOffer`** / attempt **`persisted`** **fails** — a channel post could exist while the offer stays **`approved`** and/or the attempt row stops at **`provider_sent`** (rare; orphan-post playbook remains a future ops/implementation concern). Same class of risk as pre-B13E; audit rows improve traceability but do not eliminate the boundary.

**B13D-alt bridge (implemented in product code, after this design doc):** a **read-only** admin **`GET /admin/supplier-offers/{offer_id}/showcase-channel-payload`** exposes the same logical **`ShowcaseChannelPublishRequest`** shape as **`publish`** (from **`build_showcase_publication`** + **`telegram_showcase_channel_publish_request_preview`**), **without** Telegram I/O and **without** persisting rows in **`supplier_offer_showcase_publish_attempts`**. It gives operators a **stable preview/read model** and can **support** future **content fingerprinting** / correlation with audit rows (e.g. hash of caption + photo ref per §4). **No** idempotency enforcement from this endpoint alone. **B13D** table (**§10**) + **B13E** wiring (**§11**).

---

## 3. Whether a publish-attempt table is needed

| Approach | Pros | Cons |
|---------|------|------|
| **Dedicated `supplier_offer_publish_attempts` table** (or equivalent) | Queryable history; FK to offer; clear state machine; supports multi-channel | Requires migration; retention/index policy |
| **Append-only JSON in `packaging_draft_json` or offer JSONB** | No new table in minimal form | Harder to query; concurrent writes need care |
| **Structured logs only** | Fast to ship | Weak operator UX; no DB source of truth for reconciling lifecycle vs Telegram |

**Recommendation:** treat a **durable attempt record** as **recommended before** automatic retries or concurrent multi-channel publish. **Optional** for read-only “shadow” audit in a first implementation slice. Product must **explicitly approve** migration scope.

---

## 4. What to audit (before / during / after)

- **Before send:** actor, surface (HTTP vs Telegram), correlation/idempotency key, optional **payload fingerprint** (e.g. hash of caption + photo ref — avoid storing full marketing copy if policy requires).
- **During:** attempt status **`requested` → `provider_sent` → `persisted`** (or **`failed`**); provider error class.
- **After success:** link attempt to **`showcase_message_id`** / **`showcase_chat_id`** already on **`SupplierOffer`** (or denormalize on attempt row).
- **After failure:** terminal vs retryable flag; **no** lifecycle flip to **`published`**.

Audit must **not** replace **`operator_workflow`** or **`review-package`** as readiness authority.

---

## 5. Duplicate sends and idempotency

- **In-flight single-flight:** at most one **active** publish attempt per **`(offer_id, provider)`** (or global per offer until multi-channel is specified).
- **Idempotency key:** align with **`ShowcaseChannelPublishRequest.idempotency_key`** — same key → same outcome (either return prior success receipt or reject duplicate safely **without** second Telegram post).
- **Never** silently retry POST to Telegram without dedupe or explicit operator “retry” action.

---

## 6. Retry policy (future implementation)

- **Default:** **operator-initiated** retry only until automation is proven.
- Classify **`TelegramShowcaseSendError`** (e.g. network/5xx vs explicit “bad request”) — only **transient** class eligible for retry, and only with idempotency.
- **No** background worker or cron in B13C design scope; any worker is a separate ticket.

---

## 7. Transaction and side-effect boundary

- **Today:** Telegram I/O runs **before** lifecycle fields are updated in the same synchronous request; failure leaves offer **approved**.
- **With attempt rows (B13E):** an attempt is inserted after existing **readiness/config** guards and **`build_showcase_publication`**, then **`provider_sent`** after successful adapter I/O, then offer **`published`** + attempt **`persisted`** in the same request **if** commit succeeds. If the process fails **after** Telegram returns **`message_id`** but **before** commit, reconciliation may require matching provider state to a **`provider_sent`** or partial row — same **orphan-post** class as §2.
- **Future:** single-flight / outbox / **do not** flip lifecycle to **`published`** until a consistent durable record — see B13C §4–5; **not** enforced by B13E.

---

## 8. Preserving current Telegram behavior until implementation

- **Phase 0 (pre–B13D):** no attempt storage.
- **Phase 1 (B13D–B13E):** append-only attempt log on **`publish`** — **no** change to success/failure **semantics** or **readiness** vs pre-B13E product behavior; **no** idempotency / auto-retry.
- **Phase 2 (forward):** idempotent adapter or orchestration wrapping send — **requires** tests proving no duplicate posts.

---

## 9. Forward: B13D / B13E

- **B13D-alt (implemented):** read-only **channel payload** preview — **no** attempt rows from that endpoint; see **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** §9b.
- **B13D (implemented):** table + repository + **`SupplierOfferShowcasePublishAttemptService`** — **§10**.
- **B13E (implemented):** **`publish`** writes attempt rows — **§11**; **no** idempotency enforcement; manual-copy / **exported**-without-**`message_id`** adapters remain a separate product track.
- **B13F (implemented):** read-only **attempt history** for operators — **§12**; **no** dedicated list-only HTTP route in MVP ( **`review-package`** is the main admin read model ) ; **no** retry/resend.

---

## 10. B13D implementation snapshot (skeleton, unwired)

**Migration / model:** **`alembic/versions/20260531_29_supplier_offer_showcase_publish_attempts.py`** · **`app/models/supplier_offer_showcase_publish_attempt.py`**.

**Statuses in use** (enum **`SupplierOfferShowcasePublishAttemptStatus`):** **`requested`**, **`provider_sent`**, **`persisted`**, **`failed`** — aligned with §4 “during / after” language; transitions are **service-level** today (`create_requested_attempt`, `mark_provider_sent`, `mark_persisted`, `mark_failed`).

**Actor surfaces** (enum **`SupplierOfferShowcasePublishActorSurface`):** **`http_admin`**, **`telegram_bot`** — used on **§11** **`publish`** for HTTP vs Telegram **C2B8B**.

**Live publish (B13D slice only):** table and service existed **without** **`SupplierOfferModerationService.publish`** integration — superseded by **§11(B13E)**.

**Retention / delete policy:** FK **`supplier_offer_id` → `supplier_offers.id`** is **`ON DELETE RESTRICT`**. Operational children of **`supplier_offers`** (e.g. **`supplier_offer_tour_bridge`**, **`supplier_offer_execution_links`**) use **`CASCADE`** in this codebase; **publish attempts** are treated as **audit history** and **must not** disappear silently when an offer row is deleted. Deleting an offer while attempts exist **fails** until attempts are removed or a future archival/purge flow exists. ORM: **`SupplierOffer.showcase_publish_attempts`** uses **`passive_deletes=True`** (no **`delete-orphan`** cascade).

Handoff: **[`docs/HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`](HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md)**.

---

## 11. B13E implementation (publish path wiring)

**Orchestration:** **`SupplierOfferModerationService.publish`** (after existing lifecycle/config guards and **`build_showcase_publication`**) creates a **`requested`** row, calls **`TelegramShowcaseChannelAdapter.publish`** (**unchanged**), then on success **`provider_sent`** → update **`SupplierOffer`** (**unchanged** semantics) → **`persisted`** with `showcase_chat_id` / `showcase_message_id` on the attempt. On **`TelegramShowcaseSendError`** or missing **`message_id`**, attempt **`failed`**; **same** domain/API/bot errors as pre-B13E.

**Lifecycle mapping (DB enum values):** **`requested`** → **`provider_sent`** → **`persisted`**; **`requested`** → **`failed`** (Telegram error or missing id).

**Actor / source:** **`SupplierOfferShowcasePublishActorSurface`** — HTTP **`POST …/publish`** uses **`http_admin`** + **`requested_by="http_admin"`**; Telegram **C2B8B** confirm uses **`telegram_bot`** + **`requested_by="telegram:{admin_telegram_user_id}"`**. **Payload fingerprint:** SHA-256 of caption + photo ref on the attempt row (correlates with §4).

**Not in B13E:** automatic retry/resend; **`idempotency_key`** on **`ShowcaseChannelPublishRequest`** still **unused**; no new channels; **no** Mini App / booking / payment / orders.

Handoff: **[`docs/HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md`](HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md)**.

---

## 12. B13F implementation (read-only attempt history for admin/OPS)

**HTTP:** **`GET /admin/supplier-offers/{offer_id}/review-package`** includes **`showcase_publish_attempts_review`** — nested **`AdminSupplierOfferShowcasePublishAttemptsReviewRead`** with **`items`** (**`AdminSupplierOfferShowcasePublishAttemptRead`**, newest first, service limit **50** via **`SupplierOfferShowcasePublishAttemptService.list_attempts_review_read`**). **No** new admin route in B13F MVP; a dedicated **`GET …/showcase-publish-attempts`** remains **optional** if clients want a slimmer payload than full review-package.

**Telegram admin:** offer detail appends a **compact** publish-audit block (**`_showcase_publish_attempts_telegram_compact`**, up to **5** rows, error text trimmed) on the same read-only path as operator workflow / conversion panel / template preview — **no** channel send change.

**Not in B13F:** retry/resend, attempt row creation from this surface, publish or readiness changes, **`idempotency_key`** enforcement, migrations, new channels, Mini App / booking / payment / orders.

Handoff: **[`docs/HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md`](HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md)**.

---

## 13. Non-goals (B13C document)


- **No** code **in the B13C authoring slice**, **no** migrations **from that slice**, **no** new routes **from that slice**, **no** retry logic, **no** publish readiness or output change, **no** Mini App / booking / payment / orders, **no** new channels **in that design-only deliverable**. **Note:** **B13D-alt**, **B13D**, **B13E**, and **B13F** are **separate** implementation slices — see §2, **§10**, **§11**, **§12**.


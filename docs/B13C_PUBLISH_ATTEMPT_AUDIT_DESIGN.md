# B13C — Publish attempt / audit design

**Project:** Tours_BOT. **B13C slice:** design documentation. **Update:** **B13D** publish-attempt **table skeleton** is **implemented** in product code (see **§10**); **live `publish`** remains **unwired** to attempts.

**Related:** [`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md) · [`docs/HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md`](HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md) · [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) · [`docs/HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md) · [`docs/HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP.md`](HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP.md) · [`docs/HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`](HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md).

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

**Gaps today (by design):**

- **No** publish-attempt row or outbox; **no** cross-request idempotency key usage (**`ShowcaseChannelPublishRequest.idempotency_key`** exists but is unused).
- **No** automatic retry of Telegram send.
- **Edge risk:** process/Crash after provider accepts message but before ORM commit could orphan a channel post (rare; document only until implementation addresses it).

**B13D-alt bridge (implemented in product code, after this design doc):** a **read-only** admin **`GET /admin/supplier-offers/{offer_id}/showcase-channel-payload`** exposes the same logical **`ShowcaseChannelPublishRequest`** shape as **`publish`** (from **`build_showcase_publication`** + **`telegram_showcase_channel_publish_request_preview`**), **without** Telegram I/O and **without** persisting rows in **`supplier_offer_showcase_publish_attempts`**. It gives operators a **stable preview/read model** and can **support** future **content fingerprinting** / correlation with audit rows (e.g. hash of caption + photo ref per §4). **No** idempotency enforcement from this endpoint alone. **B13D** skeleton (**§10**) adds the attempt table (**unwired** to **`publish`** in that slice).

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
- **Future with attempt row:** document whether attempt is **inserted before** send (for single-flight) and how to reconcile **provider success + DB failure** (orphan post playbook). **Do not** flip lifecycle to **`published`** until the system has a consistent record (implementation detail for B13D+).

---

## 8. Preserving current Telegram behavior until implementation

- **Phase 0 (current):** no attempt storage; behavior unchanged.
- **Phase 1 (optional):** append-only attempt logging / shadow table — **no** change to success/failure semantics of **`publish`**.
- **Phase 2:** idempotent adapter or orchestration wrapping send — **requires** tests proving no duplicate posts.

---

## 9. Forward: B13D / B13E

- **B13D-alt (implemented):** read-only **channel payload** preview endpoint + read models — **no** DB attempt rows from that endpoint; see **§2 baseline** footnote and **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** §9b.
- **B13D (implemented, skeleton):** table **`supplier_offer_showcase_publish_attempts`**, **`SupplierOfferShowcasePublishAttemptService`**, repository — **see §10**; **live `publish` not wired** yet.
- **B13E (forward):** wire attempt create/update into **`publish`** while preserving behavior; manual-copy / export adapters (**`exported`** without **`message_id`**) remain a separate track per product naming.

---

## 10. B13D implementation snapshot (skeleton, unwired)

**Migration / model:** **`alembic/versions/20260531_29_supplier_offer_showcase_publish_attempts.py`** · **`app/models/supplier_offer_showcase_publish_attempt.py`**.

**Statuses in use** (enum **`SupplierOfferShowcasePublishAttemptStatus`):** **`requested`**, **`provider_sent`**, **`persisted`**, **`failed`** — aligned with §4 “during / after” language; transitions are **service-level** today (`create_requested_attempt`, `mark_provider_sent`, `mark_persisted`, `mark_failed`).

**Actor surfaces** (enum **`SupplierOfferShowcasePublishActorSurface`):** **`http_admin`**, **`telegram_bot`** — for future correlation with HTTP **`POST …/publish`** vs Telegram **C2B8B**.

**Live publish:** **`SupplierOfferModerationService.publish`** does **not** read or write attempt rows in this slice — **no** Telegram behavior change, **no** readiness change, **no** retries.

**Retention / delete policy:** FK **`supplier_offer_id` → `supplier_offers.id`** is **`ON DELETE RESTRICT`**. Operational children of **`supplier_offers`** (e.g. **`supplier_offer_tour_bridge`**, **`supplier_offer_execution_links`**) use **`CASCADE`** in this codebase; **publish attempts** are treated as **audit history** and **must not** disappear silently when an offer row is deleted. Deleting an offer while attempts exist **fails** until attempts are removed or a future archival/purge flow exists. ORM: **`SupplierOffer.showcase_publish_attempts`** uses **`passive_deletes=True`** (no **`delete-orphan`** cascade).

Handoff: **[`docs/HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`](HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md)**.

---

## 11. Non-goals (B13C document)


- **No** code **in the B13C authoring slice**, **no** migrations **from that slice**, **no** new routes **from that slice**, **no** retry logic, **no** publish readiness or output change, **no** Mini App / booking / payment / orders, **no** new channels **in that design-only deliverable**. **Note:** **B13D-alt** and **B13D** are **separate** implementation slices (read-only preview route; attempt table skeleton) — see §2 **B13D-alt bridge** and **§10**.


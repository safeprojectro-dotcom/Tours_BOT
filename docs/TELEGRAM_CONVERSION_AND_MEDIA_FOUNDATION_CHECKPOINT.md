# Telegram conversion workflow and media foundation — checkpoint

**Date context:** 2026. **Status:** completed to defined boundaries; **media/storage micro-steps intentionally paused.**

**Companion:** This page expands the checkpoint recorded in [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (*«Checkpoint: Telegram conversion workflow + media foundation pause»*). Handoff pointer: [`docs/HANDOFF_CLOSE_TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md`](HANDOFF_CLOSE_TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md).

---

## 1. Executive summary

The **Telegram supplier-offer conversion chain** is implemented through **operator-workflow-gated** buttons (**C2B8B**, **C2B10T-A/B/C**), with **C2B10T-D** documenting **OPS** validation. Actions that mutate public or catalog state use **propose → confirm** and a **fresh `GET …/review-package`** re-read where required.

Separately, the **media storage / publish-safe** track advanced only to a **safe foundation**: **B7.4A** audit, **B7.4B** ingestion **design**, **B7.4C** **config + adapter + eligibility** (no real storage), **B7.4D** **`publish_safe` vNext metadata helpers** (no byte ingest, no publish wiring). **Durable ingestion, Telegram `getFile`, real object storage, and readiness policy changes** are **not** part of this checkpoint.

**Next work** should be chosen as a **larger product/engineering block**, not an automatic continuation of B7.4 micro-slices.

---

## 2. Completed Telegram conversion workflow

| Slice | Telegram action | `operator_workflow` gate (conceptual) |
|-------|-----------------|--------------------------------------|
| **C2B8B** | Publică / Publish | `actions.publish_showcase_channel.enabled` |
| **C2B10T-A** | Link tour / Leagă tur | `actions.create_tour_bridge.enabled` |
| **C2B10T-B** | List for sale / În catalog | `actions.activate_tour_for_catalog.enabled` |
| **C2B10T-C** | Booking link / Link rezervări | `actions.create_execution_link.enabled` |
| **C2B10T-D** | OPS smoke / runbook validation | Docs-only verification |

**Keyboard order** (when the above actions are enabled on the admin offer card):

```text
Link tour → List for sale → Publish → Booking link
```

**Explicit non-touch:** Layer A **booking / payment / orders**; **Mini App** surface/semantics; **B11** deep-link routing code.

---

## 3. Completed media storage foundation

| Step | Deliverable |
|------|-------------|
| **B7.4A** | Readiness audit — [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md) |
| **B7.4B** | Ingestion contract — [`docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`](B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md) |
| **B7.4C** | `MEDIA_STORAGE_*` settings, `MediaStorageAdapter` (+ disabled / in-memory), pure eligibility — see [`docs/HANDOFF_MEDIA_STORAGE_FOUNDATION_B7_4C_TO_NEXT_STEP.md`](HANDOFF_MEDIA_STORAGE_FOUNDATION_B7_4C_TO_NEXT_STEP.md) |
| **B7.4D** | `publish_safe` vNext builders/merge (`app/services/supplier_offer_publish_safe_vnext.py`) — see [`docs/HANDOFF_PUBLISH_SAFE_VNEXT_METADATA_B7_4D_TO_NEXT_STEP.md`](HANDOFF_PUBLISH_SAFE_VNEXT_METADATA_B7_4D_TO_NEXT_STEP.md) |

**Not** shipped: Telegram **`getFile`/download**, **S3** (or other) **upload**, **URL** fetch for ingest, **orchestrated** row updates from a worker, **publish** path calling ingestion, **readiness** rules requiring durable assets without product sign-off.

---

## 4. What is intentionally paused

Until a **new charter** (ticket + stakeholder agreement):

- **Ingestion orchestrator** (informal **B7.4D2** label — not a committed code name).
- **B7.4C2** — Telegram **downloader** mock or contract-only slice.
- **B7.4E** — **Readiness / policy** if **`publish_safe.ready`** must gate showcase or other flows.
- **B7.5** — Rendered **branded card** asset pipeline.
- **B7.6** — Channel **`sendPhoto` / `sendMediaGroup`** tied to **durable** URLs or equivalent.

---

## 5. Current terminology / source-of-truth distinctions

- **`GET …/review-package`** — **Read-only** aggregate: offer snapshot, `operator_workflow`, warnings, bridge/catalog/execution state, etc. **Does not** execute conversions or publish.
- **`operator_workflow.actions.*.enabled`** — Whether a **Telegram** (or HTTP) **mutation** may be offered; **disabled** actions stay **hidden** on the card (policy).
- **`approved_for_card` (B7.1 / `media_review`)** — Human **OK** on **hero** for **card/showcase preview** context; **not** the same as a **durable blob** in storage.
- **`publish_safe`** (`packaging_draft_json`) — **future-facing** metadata for **durable, app-owned** asset identity (**`object_key`**, **`public_url`**, vNext **status**). **B7.4D** can build **ready/pending/failed/blocked** dicts; **nothing** in this checkpoint **requires** storage or auto-writes them from publish.
- **`published` / showcase channel post** — **Explicit** marketing action (**C2B8B** / HTTP parity); **orthogonal** to `publish_safe` being `ready`.
- **Mini App** — **Execution / bookability** truth; **Telegram channel** — **marketing**; must not contradict catalog **open_for_sale** and pricing truth.
- **`cover_media_reference`** — Supplier/intake **reference** (e.g. `telegram_photo:{file_id}` or URL string); **not** a stable public CDN URL by itself.

---

## 6. Safe OPS smoke recommendation

- **Primary procedure:** [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md) — use **dry-run / Mode A** where possible; **Mode B** (live mutating) only with confirmed **staging**, **test channel**, and safe **`OFFER_ID`** / tenant rules.
- **Telegram parity:** Exercise **C2B10T-A → B → C2B8B → C** (or product-approved order) and compare to **HTTP** equivalents; **C2B10T-D** documents expectations.
- **Automated regression (examples):** `test_supplier_offer_catalog_conversion_closure`, `test_operator_workflow_c2b3_keyboard`, `test_operator_workflow_c2b10t*_specs`, `test_telegram_admin_moderation_y281` — run in CI before release; **live** Telegram smoke remains **operator-owned**.

---

## 7. Recommended next larger project blocks

Choose **one** direction explicitly (examples, not an implied roadmap):

- **B8** recurrence / draft-tours **follow-up** (Open Questions, re-run policy, activation discipline).
- **B10.6** — private bot / consultant UX (postponed historically; scope with product).
- **B11** — execution-link / Mini App **depth** (beyond current `supoffer_*` slice).
- **B12/B13** — showcase copy, channel UX, or **preview** ergonomics (**without** assuming durable media).
- **Production/staging E2E** — real walkthrough outcomes → backlog.
- **Scoped media charter** — if product prioritizes bytes: **B7.4C2 + orchestrator + B7.4E** as a **single** approved initiative, not drive-by micro-PRs.

---

## 8. Must-not-reopen-without-explicit-decision list

Do **not** implement or merge without **ticket + stakeholder / security review** as appropriate:

1. **Hidden ingestion** on **`review-package` read**, **publish confirm**, or customer paths.
2. **Weakening** **C2B8A** / **media_review** / **operator_workflow** gates for convenience.
3. **Mandatory durable `publish_safe`** for showcase (or other) **without** **B7.4E**-class **policy** sign-off.
4. **Production** object storage credentials, bucket ACLs, or **live** `getFile` in unscoped code paths.
5. **Automatic** Telegram **channel** publish from **ingestion** or **cron** without explicit UX and idempotency design.
6. **Conflating** **Mini App bookability** with **channel** or **bot** marketing state.

---

## References

- [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)
- [`docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`](B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md)
- [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) (B7.3 / B7.4 open decisions)
- `docs/CURSOR_PROMPT_CLOSE_TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`

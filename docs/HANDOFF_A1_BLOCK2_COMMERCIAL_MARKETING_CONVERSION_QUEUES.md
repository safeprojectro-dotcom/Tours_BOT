# HANDOFF_A1_BLOCK2_COMMERCIAL_MARKETING_CONVERSION_QUEUES

## Project

Tours_BOT

## Block

**A1-Block 2 — Commercial / Marketing / Conversion Queues**

## Endpoint

Extends existing **`GET /admin/automation-cockpit`** only (no new route).

## New queue codes

| `queue_code`         | Purpose |
|----------------------|---------|
| `marketing_review`   | Packaging / template / preview payload posture for marketing review (read-only). |
| `publishing_queue`   | Publish readiness + publication state hints (no send). |
| `catalog_conversion` | Tour bridge, catalog visibility, execution link, prepare-chain hints. |

Existing Block 1 queues unchanged: **`supplier_intake`**, **`missing_info`**, **`offer_readiness`**, **`risk_conflict`**.

## Behavior notes

- **Commercial lanes list every publishing-console row** in the snapshot (same row may appear in multiple commercial queues for flow context). Operational queues still classify each row into **one** lane.
- **Supplier offers:** commercial cards load **`AdminPublishingConsoleService.read_supplier_offer_detail`** once per offer (cached per request) so **`conversion_summary`**, **`publication_summary`**, and aligned fields populate **`commercial_context`** without duplicating readiness rules in the cockpit service.
- **`include_queues`** accepts the new codes; invalid tokens still **422**.

## Response additions

- **`commercial_context`** on cards (**required** on the three commercial lanes): preview/payload/template/publish/prepare-chain signals + **`fact_lock_note`** (marketing vs supplier-truth boundary).
- Operational-queue cards may include a **minimal** `commercial_context` stub (supplier-offer id + fact-lock note) when applicable.

## Fact-lock presentation

Static read-only copy (also exposed as **`COCKPIT_FACT_LOCK_NOTE`** on the schema module): supplier/catalog **facts** are not editable from the cockpit; marketing packaging/copy may be **reviewed**; price/route/discount/capacity changes require supplier clarification or governed source updates.

## Next-best actions

Lane-specific deterministic codes (examples): **`open_marketing_review`**, **`review_missing_marketing_data`**, **`review_publish_readiness`**, **`review_already_published`**, **`future_confirm_publish`** (disabled), **`open_prepare_chain_plan`**, **`run_conversion_dry_run_future`** (disabled), **`review_conversion_health`**. Only **`safe_read`** and **`future_disabled`** kinds; **`future_disabled`** is never enabled.

## Safety

Response **`safety_summary`** unchanged (all boundary flags **true**). No Telegram, publish, scheduler, supplier send, QR, Layer A mutation, B11, AI, or external calls.

## Tests

- `tests/unit/test_admin_automation_cockpit.py` — seven queues, commercial `fact_lock_note`, `include_queues` on **`marketing_review`**, action-kind guards.
- Focused regression bundle per prompt: **46 passed** after implementation.

## Next recommended block

**A1-Block 3 — Operations / Handoff / RFQ Queues** (`docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md` §17).

## Related

- `docs/HANDOFF_A1_BLOCK1_COCKPIT_READ_ONLY_FOUNDATION.md`
- `docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md`
- `docs/OPERATIONAL_AUTOMATION_ROADMAP.md`

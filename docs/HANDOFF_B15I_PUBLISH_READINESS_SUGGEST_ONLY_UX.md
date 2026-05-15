# HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX

## Project
Tours_BOT

## Block
B15I — Suggest-only UX / read-model refinement for `publish_readiness`

## Prerequisites

- B15H — [`docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md`](HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md)
- B15G — [`docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md`](B15G_GUARDED_AUTO_PUBLISH_DESIGN.md)

## Delivered

Additive fields on **`AdminPublishReadinessRead`** (`app/schemas/admin_publish_readiness.py`):

| Field | Role |
|--------|------|
| **`summary`** | One-line explanation for admin/OPS. |
| **`badge`** | Display key; mirrors **`status`** (`PublishReadinessBadge`). |
| **`next_action_code`** | Suggested admin **intent** (e.g. `review_conversion_health`, `manual_publish_available`) — **not** an HTTP executor. |
| **`next_action_label`** | Human-readable label for **`next_action_code`**. |
| **`primary_blocker`** | First failed **blocker** gate reason, if any. |
| **`warning_summary`** | Compact list of warning gate codes. |
| **`gate_summary`** | Counts: passed / failed / warnings / not applicable. |

Computation: **`_PublishReadinessUxParts`**, **`_compute_publish_readiness_ux`**, **`_finalize_publish_readiness`** in `app/services/supplier_offer_publish_readiness.py` — all read paths (`stub`, tour promotion, `derive_supplier_offer_publish_readiness`) go through **`_finalize_publish_readiness`**.

## Boundaries

Same as B15H: **no** publish, Telegram I/O, scheduler, mutations, migrations, or `prepare_conversion_chain` execution from this slice.

## Tests

Extended: `tests/unit/test_supplier_offer_review_package.py`, `test_supplier_offer_publish_readiness.py`, `test_admin_publishing_console.py`.

## Next (optional)

Wire **`summary` / `badge`** into admin web or Telegram card copy (display only).

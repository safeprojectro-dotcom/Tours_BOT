
---

## HANDOFF name

`HANDOFF_B13G_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13G_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP

## Status

**B13G production publish audit smoke — completed and recorded (2026-05-10).** Evidence: **[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)** § Run log — 2026-05-10. Recording-only slice — **no** code, **no** tests, **no** API calls from documentation authoring.

## Checkpoint (before this smoke)

- **B13D:** migration **`20260531_29`**, table **`supplier_offer_showcase_publish_attempts`**.
- **B13E / B13F:** publish writes attempts; **`review-package`** exposes **`showcase_publish_attempts_review`**.
- **B13G:** runbook published for operator checklist.

## Smoke result (summary)

| Item | Value |
|------|--------|
| **Environment** | Railway **production** |
| **Migration verify** | **`railway ssh`** → **`python -m alembic current`** → **`20260531_29 (head)`** |
| **Offer** | **ID 11** — *Excursie Timisoara Cluj* |
| **Publish path** | **Admin API** **`POST /admin/supplier-offers/11/publish`** |
| **Telegram** | Showcase post created; **no** duplicate post observed in smoke |
| **Audit attempt** | **`id` 1**, **`persisted`**, **`provider`** `telegram_showcase_channel`, **`http_admin`** / **`requested_by`** `http_admin`, **`showcase_message_id` 23**, **`showcase_chat_id`** **`-1003955096010`**, errors **null** |
| **Pre-publish review-package** | **`showcase_publish_attempts_review.total_returned`** = **0**; **`cover_media_quality_review.has_warnings`** = **false** (after approve-for-card); **`publish_showcase_channel.enabled`** = **true**; **`can_publish_now`** = **true**; **`publication_mode`** = **`photo_with_caption`** |
| **Post-publish review-package** | **`total_returned`** = **1**; **`conversion_status_panel`**: showcase **published**, tour_bridge **linked**, catalog **listed_for_sale**, **booking_link** **missing**, customer_action **not_bookable_yet** (**detail** **view_only**) |

## Confirmed behavior (B13 audit chain)

- **B13D** table + **B13E** lifecycle on publish (**`persisted`**) + **B13F** read surface + **B13G** runbook verification **align** for this production path.
- **Not** in scope of smoke: automatic retry/resend, idempotency, duplicate-send prevention (process still required).

## Remaining gap

- **`booking_link` / execution link** still **missing** for Offer **11** — Mini App direct booking CTA path not complete per **`conversion_status_panel`**.

## Recommended next step (functional)

1. **Create or verify** **`supplier_offer_execution_link`** for **Offer 11** (central admin execution-link flow per **[`docs/ADMIN_OPERATOR_WORKFLOW.md`](ADMIN_OPERATOR_WORKFLOW.md)** / review-package **`execution_links_review`**).
2. **Do not** treat the smoke as a reason to **retry** or **resend** showcase publish.

## Security reminder

- **`ADMIN_API_TOKEN`** may have been **visible** in **manual smoke** screenshots or chat — **rotate** in **Railway** environment variables and **distribute** new secret **only** through trusted channels. **Do not** commit tokens or paste them into docs.

## Non-goals (this recording)

No app changes, no migrations, no Mini App / booking / payment / order logic changes, no automated publish.

## References

- Run log: **`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`** (Run log — 2026-05-10).
- Continuity: **`docs/CHAT_HANDOFF.md`** (B13G bullet).
- Token note: **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** (Postponed — ADMIN_API_TOKEN / B13G line).
```

---

## Notes (wrapper)

Prompt: **[`docs/CURSOR_PROMPT_B13G_RECORD_PRODUCTION_SMOKE_RESULT.md`](CURSOR_PROMPT_B13G_RECORD_PRODUCTION_SMOKE_RESULT.md)**. Runbook: **[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)**. Prior B13G handoff: **[`docs/HANDOFF_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK_TO_NEXT_STEP.md`](HANDOFF_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK_TO_NEXT_STEP.md)**.

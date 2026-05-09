# CURSOR_PROMPT_ADMIN_CONTENT_QUALITY_GATE_SLICE_1

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN WORKFLOW / CONTENT QUALITY GATE — Slice 1

This is a read-only admin quality/readiness slice.

Do not change booking/payment/order/reservation logic.
Do not change Mini App UI.
Do not change Telegram showcase template.
Do not change publish behavior.
Do not change Tour bridge/catalog activation behavior.
Do not add migrations.
Do not call external AI.
Do not block existing flows yet unless explicitly stated below.
Do not add hidden triggers.
Do not auto-fix supplier data.

---

## Context

Recent production smoke proved:

Supplier Offer #11
→ packaging approved
→ moderation approved
→ tour bridge created Tour #5
→ migration blocker fixed
→ Tour activated open_for_sale
→ central Mini App catalog contains Tour

But the same smoke also showed a real operator/content risk:

- short_hook / marketing_summary had generated text but source data was weak.
- discount_code was `Ura` while discount value was zero/null.
- content quality was not good enough for real channel publishing.
- PowerShell showed UTF-8 badly, but the larger issue remains: admin needs quality warnings before publish/catalog decisions.

Recent AI fact-lock Slice 1A added:

- source facts snapshot
- fact_claims validator
- ai_public_copy_review in review-package
- public behavior unchanged

Now we need admin-visible content quality/readiness warnings.

---

## Goal

Add a read-only `content_quality_review` section to:

GET /admin/supplier-offers/{offer_id}/review-package

It should help admin see bad/suspicious content before publish/catalog/AI/public copy work.

This slice should not block existing flows yet. It surfaces warnings and recommended_next_actions only.

---

## Required behavior

### 1. Add content quality reviewer service/helper

Create a small deterministic helper/service, for example:

```python
app/services/supplier_offer_content_quality_review.py
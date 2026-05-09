# CURSOR_PROMPT_B12_B13_5_ADMIN_PREVIEW_BEFORE_PUBLISH_WORKFLOW_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

Это design/contract step. Не менять код.

---

## Current checkpoint

B12/B13 showcase line is now implemented up to preview endpoint.

Recent commits:
- dfb9c45 feat: add branded Telegram showcase template
- b4f57af fix: polish Telegram showcase copy and CTA links
- b2367af feat: add showcase preview and disable link previews

Current behavior:
- Channel showcase post is branded RO text-first.
- FULL_BUS price is rendered as group/package price.
- Individual seats are not sold separately for FULL_BUS.
- Program section is supported from factual program_text.
- CTA line: `ℹ️ Detalii | ✅ Rezervă`.
- Detalii -> bot deep link `supoffer_<id>`.
- Rezervă -> Mini App supplier-offer landing.
- No direct `/tours/{code}` in channel.
- No photo/sendPhoto.
- Telegram link preview disabled.
- GET /admin/supplier-offers/{offer_id}/showcase-preview exists.
- Preview is read-only, does not call Telegram, does not mutate DB.
- Preview returns caption_html, publication metadata, lifecycle_status, can_publish_now, warnings.

Manual lesson:
- Bad/test raw input will appear in final channel post.
- That is expected; admin preview is the correct safety point.

---

## Goal

Design the operational workflow for admin preview-before-publish.

Question:
Should preview be optional, recommended, or mandatory before POST /admin/supplier-offers/{offer_id}/publish?

Design a safe MVP workflow without overbuilding.

---

## Source files/docs to read

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- app/api/routes/admin.py
- app/services/supplier_offer_moderation_service.py
- app/schemas/supplier_admin.py
- app/services/supplier_offer_showcase_message.py
- tests/unit/test_supplier_offer_track3_moderation.py

If other admin UI/API docs exist, inspect them too.

---

## Questions to answer

### 1. Current publish workflow

Map current admin flow:
- moderation approve
- publish
- retract
- preview endpoint
- lifecycle statuses
- whether admin UI exists or only API
- whether publish endpoint can be called without preview

### 2. MVP workflow options

Evaluate:

A. Preview optional only.
- Admin may call preview, then publish.
- No DB changes.
- Fastest.

B. Preview recommended + documented.
- Same as A but documented as operational procedure.

C. Mandatory preview before publish, no DB migration.
- Publish requires a preview token/hash passed in request.
- Hard without state.

D. Mandatory preview with DB state.
- Store preview_hash / preview_seen_at / preview_seen_by.
- Publish checks current hash matches last preview.
- Safer but more schema and UI work.

E. Admin approve-preview endpoint.
- Separate action: preview accepted, then publish.
- More ceremony.

Recommend MVP path.

Expected bias:
- Do not add DB state yet.
- Keep preview optional/recommended now.
- If product needs safety, design future hash-based mandatory preview.

### 3. Preview hash / versioning

Should we compute a preview_hash now?
- It can be returned in preview without being persisted.
- Future publish could require it.
- Is it worth adding now?
- Risks of overengineering?

### 4. Warnings and admin decision

Define warnings that admin should see before publish:
- not approved
- already published
- missing channel config
- missing bot/Mini App URL
- text contains obvious placeholder like “Test”
- optional future: non-RO/Cyrillic detection
- long post/truncation risk
- missing program
- missing include/exclude

Which are blockers vs non-blocking warnings?

### 5. Recommended next implementation slice

Choose smallest useful follow-up, if any.

Possible:
- docs-only operational procedure
- add preview_hash to preview response only
- add non-blocking warnings for placeholder/test/cyrillic
- add admin preview endpoint tests for warnings
- no code; proceed to B7.4 or admin UI

### 6. Tests needed if implementation follows

Recommend test cases.

---

## Non-goals

Do not propose implementing now:
- full admin UI
- forced preview state with DB migration
- AI translation/rewrite
- automatic text normalization
- media pipeline
- booking/payment changes
- Mini App UI changes
- direct channel `/tours/{code}` URL

---

## Required final report

Return:

1. Current workflow map
2. Preview-before-publish options
3. Recommended MVP decision
4. Future mandatory preview design, if needed
5. Warning/blocker policy
6. Recommended next implementation slice
7. Files likely affected
8. Tests needed
9. Risks/ambiguities
10. Recommended next prompt name

Do not change files.
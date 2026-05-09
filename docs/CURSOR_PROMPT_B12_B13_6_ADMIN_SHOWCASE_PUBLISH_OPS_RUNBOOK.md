# CURSOR_PROMPT_B12_B13_6_ADMIN_SHOWCASE_PUBLISH_OPS_RUNBOOK

Ты продолжаешь проект Tours_BOT.

## Cursor mode

Agent.

Это docs-only step.

Не менять app/.
Не менять tests/.
Не менять alembic/.
Не менять mini_app/.
Не менять runtime-код.

---

## Current checkpoint

B12/B13.5 design accepted.

Decision:

- Admin showcase preview before publish is recommended operational workflow for MVP.
- It is not mandatory in code yet.
- No DB state now.
- No preview_seen_at / preview_seen_by now.
- No preview_hash requirement now.
- Future preview_hash / mandatory preview can be added only when product/audit requirement is explicit.

Current implemented behavior:

- GET /admin/supplier-offers/{offer_id}/showcase-preview exists.
- Preview is read-only.
- Preview uses the same showcase builder as real publish.
- Preview does not call Telegram.
- Preview does not mutate DB.
- Preview returns:
  - caption_html
  - publication metadata
  - lifecycle_status
  - can_publish_now
  - warnings
- POST /admin/supplier-offers/{offer_id}/publish remains unchanged.
- Publish can still be called without preview.
- Admin remains final publisher.

---

## Goal

Document the recommended admin operation:

Preview → verify → publish.

This is an ops/runbook documentation step only.

---

## Files to update

Update briefly:

1. docs/CHAT_HANDOFF.md
2. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
3. docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Optionally create a short runbook doc if project style supports it:

- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md

Create it only if useful and keep it concise.

---

## Required content

Document the MVP operational procedure:

### Admin showcase publish checklist

1. Offer must be approved.
2. Admin calls:

   GET /admin/supplier-offers/{offer_id}/showcase-preview

3. Admin checks:
   - caption_html text
   - route/date/price/program/include/exclude
   - no bad placeholder/test copy
   - no wrong language if channel is Romanian
   - CTA line exists: Detalii | Rezervă
   - can_publish_now is true
   - warnings are empty or consciously accepted

4. Admin publishes:

   POST /admin/supplier-offers/{offer_id}/publish

5. If mistake is found after publish:
   - use retract endpoint if needed
   - correct offer data
   - preview again
   - publish again if appropriate

---

## Important policy notes

Document clearly:

- Preview is recommended, not enforced by code.
- `can_publish_now=true` means technical/lifecycle readiness, not marketing quality approval.
- Copy quality remains admin responsibility.
- The system does not auto-translate or rewrite supplier/admin text at publish time.
- Bad raw input will appear in the preview and post.
- No mandatory preview hash in MVP.
- No DB migration for preview tracking.
- Future option: preview_hash / mandatory preview if required by audit or product policy.

---

## Boundaries

Do not introduce or document as implemented:

- mandatory preview enforcement
- preview_hash requirement
- preview_seen_at DB field
- admin UI
- AI rewrite/translation
- media pipeline
- sendPhoto
- direct /tours/{code} channel links
- booking/payment changes
- Mini App UI changes

---

## Final report

Report:

1. Files changed
2. Runbook/checklist added
3. Whether new doc was created
4. Confirmation docs-only
5. Remaining future work
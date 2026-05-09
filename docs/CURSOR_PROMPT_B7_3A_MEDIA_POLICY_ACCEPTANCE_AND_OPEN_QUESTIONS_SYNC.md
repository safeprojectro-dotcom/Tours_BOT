# CURSOR_PROMPT_B7_3A_MEDIA_POLICY_ACCEPTANCE_AND_OPEN_QUESTIONS_SYNC

You are continuing the Tours_BOT project.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a documentation-only acceptance/sync step after the B7.3 media pipeline policy Plan.

Do not change runtime code.
Do not create migrations.
Do not change tests.
Do not add storage clients.
Do not download Telegram files.
Do not implement card rendering.
Do not implement Telegram publishing.
Do not change Mini App UI.

---

## Accepted B7.3 Plan decision

The B7.3 media pipeline policy design was accepted.

Accepted policy:

1. Raw supplier media is not publish-safe.
2. Telegram file_id / telegram_photo:{file_id} is not a stable public URL.
3. Do not download Telegram files in the first B7.3 implementation.
4. Do not use Railway local filesystem as canonical durable media storage.
5. Keep current metadata-first model for MVP:
   - cover_media_reference
   - media_references JSON
   - packaging_draft_json.media_review
   - B7.2 card render preview JSON
6. Durable publish-safe assets should use future object storage / S3-compatible storage when download/storage is explicitly scoped.
7. approved_for_card is not the same as publish_safe.
8. publish_safe is not the same as published.
9. publication remains a separate explicit admin action.
10. B7.3 does not send Telegram messages.
11. B7.3 does not call getFile or download bytes.
12. B7.3 does not implement real pixel rendering.
13. Mini App UI does not change in this step.
14. Mini App execution truth must stay independent of marketing media pipeline.
15. AI/card prompt/render plan is metadata, not a binary media asset.
16. Fallback branded card can remain a planned/placeholder derived asset until real renderer/storage exists.

Recommended MVP trajectory:
- B7.3A = docs-only media policy acceptance and OPEN_QUESTIONS sync.
- B7.3B later = optional metadata-only publish_safe stub in packaging_draft_json, no download.
- Future = storage abstraction / object storage / Telegram getFile / card rendering only after explicit policy and prompt.

---

## Current project checkpoint

B8 recurring supplier offers line is closed.

Completed:
- B8 recurring draft Tour generation
- B8 stabilization
- B8.2 activation policy design
- B8.3 duplicate active Tour activation guard
- B8.4 docs sync

Latest B8 commits:
- fba45d9 — docs: add B8 recurring activation policy design
- 460ef50 — feat: guard recurring tour activation conflicts
- 4c0faf5 — docs: sync B8 recurring supplier offers closure

B7 status:
- B7.1 media review metadata completed.
- B7.2 card render preview plan completed.
- B7.3 policy accepted in Plan.
- B7.3 implementation pipeline is not yet implemented.

Still not implemented:
- real Telegram media download
- durable object storage
- real public URL lifecycle
- real card pixel rendering
- Telegram sendPhoto/sendMediaGroup
- automatic publish
- Mini App media UI redesign
- B10.6 bot router/consultant redesign
- B11 deep-link routing
- B12/B13 template/channel adapters

---

## Source documents to read/update

Read and update only as needed:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md if it exists
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md if it has B7/B7.3 section
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md only if it already tracks this B-line continuation

If a file does not exist, do not invent it unless it is clearly the best place for the accepted policy. Prefer updating existing docs.

---

## Goal of this step

Save the accepted B7.3 policy decision into normal project documentation.

The next agent must clearly understand:

- B7.3 policy is accepted.
- First B7.3 implementation should be metadata/docs-first.
- Telegram file_id is not publish-safe.
- Raw supplier media is not publish-safe.
- approved_for_card != publish_safe.
- publish_safe != published.
- No download/storage/render/publish has been implemented.
- Railway filesystem must not be used as durable canonical media storage.
- Object storage is the future durable option, not implemented now.
- B7.3B metadata-only stub may be next if needed.

---

## Expected files to change

Prefer:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md

Optional:

- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Do not touch:

- app/
- tests/
- alembic/
- mini_app/

---

## Required updates

### 1. CHAT_HANDOFF

Add a B7.3A policy acceptance checkpoint:

- B7.3 media pipeline policy accepted.
- Raw supplier media is not publish-safe.
- Telegram file_id is not a public/stable asset.
- Metadata-first MVP remains current.
- No getFile/download/storage/render/publish implemented.
- Object storage is future explicit slice.
- Publication remains a separate explicit admin action.
- Mini App execution truth remains independent from marketing media.
- Next safe B7.3 implementation option:
  - B7.3B metadata-only publish_safe stub, or
  - continue business plan with B11/B12/B13 if media implementation is not priority.

### 2. OPEN_QUESTIONS_AND_TECH_DEBT

Add/update B7.3 section:

#### B7.3 publish-safe media policy accepted

Current decision:
- keep Telegram references and media review metadata only for now.
- raw media is not publish-safe.
- approved_for_card is not publish_safe.
- publish_safe is not published.
- no Railway local filesystem as canonical durable storage.
- future durable assets should use object storage/S3-compatible solution.

Risks:
- Telegram file_id is not usable as public web URL.
- future publication/media pipeline needs storage credentials and retention/deletion policy.
- generated cards must remain grounded in source facts.
- public URLs may leak unpublished media if ACLs are wrong.
- Telegram media access can expire or be unsuitable for non-Telegram surfaces.
- real image moderation, size/type limits, and copyright/quality checks remain future scope.

Revisit trigger:
- before implementing getFile/download.
- before real card rendering.
- before Telegram photo publication.
- before Mini App starts displaying real approved media assets.
- before object storage/S3 credentials are introduced.

Status:
- open / accepted policy.

### 3. Photo moderation / card generation design doc

If the file exists, add a short B7.3A decision log:

- B7.1 = review metadata.
- B7.2 = render preview plan.
- B7.3A = accepted media policy only.
- B7.3B future = metadata-only publish_safe stub.
- B7.4+ future = real storage/download/rendering if approved.
- raw_received / approved_for_card / publish_safe / published are separate concepts.
- no auto-publish from media approval.

Do not rewrite the document.

### 4. Business plan

If B7/B7.3 is tracked there, update minimally:

- B7.3 policy accepted.
- implementation remains postponed until metadata/storage slice is explicitly selected.
- no auto-publish.
- real pixels/download/storage remain future explicit steps.

---

## Non-goals

Do not:

- change code
- add migrations
- change tests
- add S3/object storage config
- add Telegram getFile/download
- add image processing
- add card rendering
- add sendPhoto/sendMediaGroup
- change Mini App UI
- change payment/order/reservation
- implement B10.6
- implement B11
- implement B12/B13

---

## Checks

Run:

git diff --stat

Review diffs only for docs.

No pytest needed if docs-only.

If code changes occur accidentally, stop and report.

---

## Final report required

Report:

1. Files changed
2. Sections updated
3. Confirmation that no app/tests/alembic/mini_app files changed
4. Whether B7.3 policy is now visible in CHAT_HANDOFF
5. Whether OPEN_QUESTIONS records the media/storage/download risks
6. Whether raw media / approved_for_card / publish_safe / published separation is documented
7. Whether no implementation was added
8. git diff summary
9. Recommended next options, without choosing automatically
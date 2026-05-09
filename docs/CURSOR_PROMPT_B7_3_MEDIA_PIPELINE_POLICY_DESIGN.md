# CURSOR_PROMPT_B7_3_MEDIA_PIPELINE_POLICY_DESIGN

You are continuing the Tours_BOT project.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

This is a design/policy step only.

Do not write code.
Do not create migrations.
Do not add storage clients.
Do not download Telegram files.
Do not implement real card rendering.
Do not implement Telegram publishing.

---

## Current checkpoint

B8 recurring supplier offers line is closed.

Completed:
- B8 recurring draft Tour generation
- B8 stabilization
- B8.2 activation policy design
- B8.3 duplicate active Tour activation guard
- B8.4 docs sync

Latest commits:
- fba45d9 — docs: add B8 recurring activation policy design
- 460ef50 — feat: guard recurring tour activation conflicts
- 4c0faf5 — docs: sync B8 recurring supplier offers closure

Production smoke after B8.3:
- /health -> ok
- /healthz -> ready
- Mini App UI -> HTTP 200

Current postponed items:
- B7.3 publish-safe media pipeline is NOT implemented.
- B10.6 Telegram bot router/consultant redesign is NOT implemented.
- B11 Telegram deep-link routing is NOT implemented.

---

## Business context

Telegram Channel = marketing showcase.
Telegram Bot = router / consultant / entry point, not duplicate Mini App catalog.
Mini App = execution truth and conversion.
Layer A = booking/payment authority.
Supplier Offer = raw supplier proposal / source facts.
Tour = customer-facing sellable catalog object.
Admin = final decision maker.
AI = draft generator only.

Core principle:

- visibility != bookability.
- Mini App execution truth must stay strict and current.
- Telegram/channel can be softer showcase, but must not contradict Mini App truth.

---

## B7 context

Already completed:

### B7.1
- Media review metadata exists.
- Supplier media can be tracked/reviewed as metadata.
- No real publish-safe storage/download pipeline yet.

### B7.2
- Card render preview plan exists.
- No real pixels/download/storage yet.
- No real public media asset pipeline yet.

Now we are planning:

### B7.3
Publish-safe media pipeline.

This must decide storage/download/publication policy before implementation.

---

## Source documents to review first

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/TECH_SPEC_TOURS_BOT.md
- docs/MINI_APP_UX.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/TESTING_STRATEGY.md

If some files are missing, do not invent content. Mention missing files in the final report and continue with available sources.

---

## Goal of this Plan step

Design a safe B7.3 publish-safe media pipeline policy.

Answer:

How should raw supplier media become safe, approved, publishable media for Telegram/channel/Mini App/card previews without breaking architecture or creating hidden publish behavior?

This is not implementation.

---

## Questions to answer

### 1. Media source model

Clarify how raw media enters the system.

Known current source:
- supplier sends Telegram cover photo
- telegram_file_id is stored

Questions:
- Should B7.3 download Telegram files now, or only preserve file references?
- Should raw Telegram file_id be treated as publish-safe?
- Should raw media and approved media be separate concepts?
- Should AI-generated card prompt/preview be treated as media or content metadata?

Expected direction:
- raw supplier media != publish-safe media
- admin approval required

---

### 2. Storage strategy

Compare options:

A. Keep Telegram file_id only for now  
B. Download to local/Railway filesystem  
C. Store in external object storage/S3-compatible bucket  
D. Store only public URL references managed manually by admin  
E. Hybrid MVP: metadata now, external storage later

For each option, analyze:
- safety
- Railway compatibility
- public URL support
- rollback complexity
- GDPR/privacy/data deletion implications
- publish reliability
- implementation complexity
- MVP suitability

Recommend safest MVP default.

---

### 3. Publish-safe media lifecycle

Design lifecycle states.

Possible states:
- raw_received
- pending_review
- approved
- rejected
- publish_safe
- published
- archived

Questions:
- Which states already exist?
- Which are needed now?
- Which should be future?
- Is approved media automatically publish_safe?
- Can a rejected supplier photo still produce fallback branded card?
- Should fallback branded card require admin approval?

Expected principle:
- approval does not automatically mean Telegram publish
- publish-safe does not automatically mean published

---

### 4. Media references and data model

Without implementing migrations, propose the minimal data model direction.

Consider:
- supplier offer media metadata
- Telegram file_id
- storage object key
- public URL
- media type
- source
- review status
- approved_by
- approved_at
- rejection reason
- derived card reference
- publish_safe flag/status

Questions:
- Can existing fields support B7.3 MVP?
- Is a new table needed later?
- Can B7.3 first implementation be docs-only or metadata-only?

---

### 5. Card generation / rendering boundary

B7.2 was a card render preview plan, no real pixels.

Questions:
- Should B7.3 implement real card rendering?
- Or should B7.3 only prepare publish-safe media contract and leave rendering to B7.4?
- How should fallback branded card be represented if no rendering exists yet?

Expected safe default:
- do not implement real rendering until storage policy is accepted
- fallback card can be represented as a planned derived asset / placeholder until renderer exists

---

### 6. Publication boundaries

Clarify how media connects to publication.

Questions:
- Can approved media trigger Telegram publish?
- Should Telegram publication remain separate admin action?
- Should B7.3 touch Telegram Bot API sendPhoto/sendMediaGroup?
- Should B7.3 only prepare media references for future publication?

Expected principle:
- no automatic publish
- publication remains separate explicit admin action
- B7.3 should not send Telegram messages unless explicitly scoped later

---

### 7. Mini App impact

Questions:
- Should Mini App consume publish-safe media now?
- Should Mini App continue using current placeholder/cover references?
- Should B7.3 change Mini App UI?

Expected principle:
- no Mini App UI change in design step
- Mini App may later consume approved cover/media references only if backend exposes them safely
- Mini App execution truth must not depend on marketing media pipeline

---

### 8. Security and operational risks

Analyze risks:

- Telegram file links expire or are not public
- local filesystem not persistent on Railway
- public URLs leak unpublished media
- unapproved supplier photos accidentally published
- generated cards use incorrect facts
- media deletion/retention policy unclear
- copyright/quality concerns
- large file size / unsupported format
- image moderation needs
- external storage credentials/secrets

---

### 9. Recommended B7.3 implementation slice

Recommend the next small Agent step after this Plan is accepted.

Choose one:

A. Docs-only media policy acceptance  
B. Metadata-only publish-safe state model using existing fields  
C. Add storage abstraction interface but no provider  
D. Add external storage integration  
E. Add Telegram media download  
F. Add card rendering

Pick the safest smallest next slice.

Expected bias:
- probably A or B first, unless existing schema already supports enough metadata safely

---

## Non-goals

Do not propose implementing now:

- real Telegram file download
- external storage integration
- local filesystem storage on Railway
- real card pixel rendering
- sendPhoto/sendMediaGroup publication
- automatic publish
- automatic card generation
- Mini App UI media redesign
- AI changing Tour/SupplierOffer facts
- payment/order/reservation changes
- B10.6 bot redesign
- B11 deep-link routing
- B12/B13 template/channel adapters

---

## Required output

Return a structured design report with:

1. Current state summary
2. Media source policy
3. Storage option decision matrix
4. Recommended MVP storage/download policy
5. Publish-safe media lifecycle
6. Data model direction
7. Card rendering boundary
8. Publication boundary
9. Mini App impact
10. Security/ops risks
11. Recommended next Agent implementation step
12. Files likely affected in next implementation
13. Tests/checks likely needed
14. Non-goals preserved
15. Recommended next prompt name

Do not change files in this Plan step.
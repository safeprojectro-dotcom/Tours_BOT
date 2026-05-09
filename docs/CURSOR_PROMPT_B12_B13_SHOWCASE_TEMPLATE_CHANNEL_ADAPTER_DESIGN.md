# CURSOR_PROMPT_B12_B13_SHOWCASE_TEMPLATE_CHANNEL_ADAPTER_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

Это design/contract step. Не менять код в этом шаге.

---

## Current checkpoint

Recent completed work:

### B7 media
- B7.1 media review metadata completed.
- B7.2 card render preview plan completed.
- B7.3A media policy accepted.
- B7.3B metadata-only publish_safe stub implemented.
- No real download/storage/render/publish.

### B8 recurring supplier offers
- B8 recurring draft Tour generation completed.
- B8.2 activation policy accepted.
- B8.3 duplicate active Tour activation guard implemented.
- B8.4 docs sync completed.

### B11 deep-link routing
- `/start supoffer_<id>` resolves active `supplier_offer_execution_link`.
- If linked Tour is `OPEN_FOR_SALE` and customer-visible:
  - bot gives exact Mini App CTA to `/tours/{tour_code}`;
  - generic catalog overview is skipped.
- Safe fallback remains.

### B10.6 bot router/consultant
- `/start tour_<code>` has exact Mini App Tour CTA.
- Generic `/start` and `/tours` are router-first.
- Bot no longer auto-sends catalog cards for generic entry.
- Copy/button alignment and full_bus wording audit completed.

---

## Business context

Telegram Channel = marketing showcase.  
Telegram Bot = router / consultant / entry point.  
Mini App = execution truth and conversion.  
Layer A = booking/payment authority.  
Supplier Offer = raw supplier proposal / source facts.  
Tour = customer-facing sellable object.  
Admin = final decision maker.  
AI = draft generator only.

Core principle:

- visibility != bookability.
- Telegram/channel can be softer showcase.
- Mini App execution truth must stay strict and current.
- Channel post must not contradict Mini App truth.
- AI may draft copy, but admin approves final publication.
- Approved package does not equal published post.
- Publish-safe media does not equal published media.

---

## Why B12/B13 now

We have:

- Supplier Offer intake/review.
- AI/deterministic packaging.
- Admin approval.
- Bridge to Tour.
- Tour activation.
- Bot exact deep-link routing.
- Bot router-first behavior.

But the marketing showcase layer still needs a clean contract:

- what content template is used for Telegram channel posts;
- how CTA links are generated;
- whether CTA is `supoffer_<id>` or exact Tour;
- how unavailable/draft/not linked offers are handled;
- how channel-specific formatting differs from Mini App truth;
- how media/publish_safe placeholders are handled before B7.4/B7.5/B7.6.

---

## Source documents to read first

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/MINI_APP_UX.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/TESTING_STRATEGY.md

Inspect current code:

- supplier offer publication / showcase services
- supplier_offer_showcase_message if exists
- supplier_offer_deep_link.py
- bot/channel publishing handlers if any
- admin supplier offer publish endpoints
- current Telegram channel post generation logic
- tests around supplier offer publication / channel / showcase

If some files do not exist, report that clearly and continue with available code/docs.

---

## Goal of this Plan step

Design B12/B13: marketing showcase template library + channel adapter contract.

Do not implement code.

Answer:

How should an admin-approved Supplier Offer become a safe Telegram channel showcase post that routes users correctly without pretending to be Mini App execution truth?

---

## Questions to answer

### 1. Current publication/showcase behavior

Find current behavior:

- What admin action publishes Supplier Offer to channel?
- What service builds the post text?
- Does it use AI packaging, deterministic template, or raw offer fields?
- Does it include media?
- Does it include `supoffer_<id>` bot deep link?
- Does it store `showcase_message_id`, `published_at`, `showcase_photo_url`, etc.?
- Does it support edit/repost/delete?
- What happens if Supplier Offer has linked active Tour?
- What happens if no linked Tour exists?

Report exact files/functions.

---

### 2. Template source of truth

Define what source data templates may use.

Allowed:

- approved supplier offer package facts
- deterministic packaging fields
- admin-approved marketing copy
- B6 branded Telegram preview JSON if still valid
- current linked Tour status only for CTA/actionability text, not as marketing fact mutation

Forbidden:

- AI inventing dates/prices/availability
- raw unreviewed supplier media as publish-safe
- draft Tour treated as bookable
- channel copy contradicting Mini App truth

---

### 3. CTA strategy

Define CTA strategy for channel posts.

Options:

A. Always use bot deep link:
`https://t.me/<bot>?start=supoffer_<id>`

B. If linked active Tour exists, use exact Tour Mini App link directly.

C. Use bot deep link as stable router always, because B11 now resolves exact Tour.

Recommended likely direction:

- Use `supoffer_<id>` bot deep link as stable public CTA.
- Let B11 route to exact Tour when active link exists.
- Do not put direct Mini App Tour URL in channel yet unless Telegram WebApp/channel behavior is confirmed.
- This preserves stable post even if Tour link changes later.

Evaluate pros/cons.

---

### 4. Channel adapter responsibility

Define responsibilities:

Template library:
- builds structured message content from approved package.

Channel adapter:
- adapts content to Telegram channel constraints:
  - plain text / Markdown / HTML
  - length limits
  - emoji policy
  - CTA formatting
  - media placeholder vs sendPhoto future
  - language selection
  - source attribution if needed

Publication service:
- sends message or prepares preview depending on admin action.

Admin:
- final publish approval.

---

### 5. Media handling

Given current B7 status:

- `publish_safe.status = deferred`
- no public_url
- no object storage
- no rendered card

Define B12/B13 policy:

- Telegram channel post should be text-first for now.
- Do not attempt sendPhoto/sendMediaGroup.
- Do not treat Telegram file_id as public media.
- If media is not publish_safe, use no media or text-only fallback.
- Future B7.4/B7.5/B7.6 can add media.

---

### 6. Offer/Tour/actionability status in copy

Define copy rules:

If linked active Tour exists:
- CTA: “Open / details / reserve in Mini App”
- But actual booking truth still lives in Mini App.

If linked Tour draft/not active:
- CTA: “Details / ask us / notify me” but no booking claim.

If no linked Tour:
- CTA: “Ask us / see details / request trip” but no booking claim.

If full_bus:
- avoid “choose seats”
- use whole-bus/charter wording.

If per_seat:
- seat wording allowed only if backend truth says sellable.

---

### 7. Language/channel strategy

Decide MVP language behavior:

- single default language?
- use supplier offer language?
- use admin-selected language?
- multilingual post?
- Romanian-first because local market?
- preserve existing translations?

Do not overbuild.

---

### 8. Recommended first implementation slice

Choose smallest safe Agent step.

Possible slices:

A. Docs-only B12/B13 acceptance first.
B. Deterministic text-only Telegram showcase template refactor.
C. Channel adapter interface / service without changing send behavior.
D. Admin preview endpoint/read model for final post before publish.
E. Publish service update to use stable `supoffer_<id>` CTA and B11 routing.
F. Media integration — should likely be deferred.

Recommend one first implementation slice.

Expected bias:
- text-only and deterministic
- no media
- no AI final publish
- no automatic publish
- no Mini App/payment changes

---

### 9. Tests needed

Recommend focused tests:

- approved package builds deterministic text-only channel post
- post contains `supoffer_<id>` deep link
- no direct booking claim when no active execution link
- linked active Tour copy does not contradict Mini App truth
- full_bus copy does not mention choosing seats
- no media send when publish_safe is deferred
- existing publish/admin tests remain passing

---

## Non-goals

Do not propose implementing now:

- sendPhoto/sendMediaGroup
- Telegram media download
- object storage
- card rendering
- automatic channel publish
- Mini App UI changes
- booking/payment/order changes
- Tour activation
- SupplierOfferTourBridge creation
- B10.6 bot redesign changes
- B11 routing changes
- B8 recurrence changes
- RAG/AI runtime

---

## Required final report

Return a structured report:

1. Current publication/showcase behavior found
2. Recommended B12/B13 template/channel adapter contract
3. CTA strategy recommendation
4. Media handling policy
5. Offer/Tour/actionability copy rules
6. Language strategy
7. Recommended first implementation slice
8. Files likely affected
9. Tests needed
10. Risks / ambiguities
11. Non-goals preserved
12. Recommended next Agent prompt name

Do not change files in this Plan step.
You are continuing Tours_BOT.

Goal:
B1 — Supplier Offer Intake + AI Packaging + Moderation Design.

This is DESIGN ONLY.
No code implementation.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/TECH_SPEC_TOURS_BOT.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/MINI_APP_UX.md

Create:
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md

Update:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Define:

1. Business principle:
- supplier provides raw facts
- AI creates draft packaging
- admin reviews/edits/approves
- only approved package can be published
- published supplier offer should later become/attach to Tour in Mini App catalog via explicit bridge

2. Supplier intake data requirements:
- required fields
- optional fields
- photo/media requirements
- program requirements
- included/excluded
- price/currency
- capacity/seats
- dates or recurrence
- discount/promo fields
- supplier contact/admin-only notes

3. Supplier dialog structure:
- step-by-step questions
- one question at a time
- validation / missing-field handling
- ready_for_moderation criteria

4. AI packaging output:
- Telegram post draft
- short hook
- brief program
- Mini App short_description
- Mini App full_description
- normalized program_text
- included_text
- excluded_text
- CTA variants
- image/card prompt or layout data
- quality warnings
- missing fields

5. Admin moderation flow:
- raw supplier data view
- AI draft view
- Telegram preview
- Mini App preview
- photo/card preview
- approve package
- edit package
- regenerate package
- request supplier clarification
- reject

6. Status model:
- draft
- ready_for_moderation
- packaging_pending
- packaging_generated
- needs_admin_review
- approved_for_publish
- published
- linked_to_tour
- visible_in_catalog
- bookable / not_bookable

7. Guardrails:
- AI is draft-only
- AI must not invent dates/prices/seats
- AI must not publish
- AI must not create bookings/orders/payments
- AI must not silently create Tour
- admin approval is required
- Layer A booking/payment remains unchanged

8. Next steps:
- B2 Supplier Offer Content/Data Upgrade
- B3 Supplier Dialog Upgrade
- B4 AI Packaging Layer
- B5 Admin Moderation UI
- B9 Offer-to-Tour bridge

After editing:
- files changed
- business principle documented
- required supplier data documented
- AI output contract documented
- moderation flow documented
- next safe step
Continue Tours_BOT strict continuation.

Task:
Create a docs-only design gate for safe Telegram admin tour selection UI for execution link create/replace.

Context:
Y32.7 accepted:
- Telegram admin can create execution link via explicit tour_id / exact tour code.
- Telegram admin can start replace flow.
- sales_mode mismatch guard is confirmed.
- Manual ID/code input works but is not operator-friendly.

Read first:
- docs/CHAT_HANDOFF.md
- docs/HANDOFF_Y32_7_OPERATOR_LINK_REPLACE_GUARD_SMOKE.md
- docs/OPERATOR_LINK_CREATE_REPLACE_UI_GATE.md
- docs/OPERATOR_EXECUTION_LINK_WORKFLOW_GATE.md

Goal:
Design safe tour selection UX so admin/operator can choose compatible tours without manually knowing IDs.

Rules:
- Docs only.
- No runtime code.
- No migrations.
- No Mini App changes.
- No Layer A booking/payment changes.
- No auto-create tours.
- supplier_offer != tour.
- Direct booking CTA remains controlled only by active authoritative link + bookable linked tour.

Create:
docs/OPERATOR_LINK_TOUR_SELECTION_UI_GATE.md

Include:
1. Current state
2. Why manual ID/code is not enough
3. Required filters
   - same sales_mode
   - existing tour only
   - status visibility
   - seats/actionability summary
4. Tour list card format
5. Pagination rules
6. Search rules
7. Create flow with tour selection
8. Replace flow with tour selection
9. Fail-safe behavior
10. Tests required
11. First safe runtime slice recommendation

Update:
docs/CHAT_HANDOFF.md with reference to this gate.

Do not touch runtime code.
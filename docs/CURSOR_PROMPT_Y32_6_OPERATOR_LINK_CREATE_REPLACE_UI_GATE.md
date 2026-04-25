Continue Tours_BOT strict continuation.

Task:
Create a docs-only design gate for Telegram admin UI create/replace execution link flow.

Context:
Y32.5 accepted:
- /admin_published -> offer detail -> Execution link
- admin can view active link/history
- admin can close active link
- create/replace via Telegram UI postponed because safe tour-selection pattern was not yet defined

Read first:
- docs/CHAT_HANDOFF.md
- docs/HANDOFF_Y32_5_OPERATOR_EXECUTION_LINK_UI_SLICE_ACCEPTED.md
- docs/OPERATOR_EXECUTION_LINK_UI_GATE.md
- docs/OPERATOR_EXECUTION_LINK_WORKFLOW_GATE.md
- docs/SUPPLIER_CONVERSION_BRIDGE_IMPLEMENTATION_GATE.md

Goal:
Design the safe Telegram UI flow for:
1. selecting a compatible tour
2. creating execution link
3. replacing active execution link
4. preventing invalid sales_mode mismatch
5. preventing unsafe auto-tour creation

Rules:
- Docs only.
- No runtime code.
- No migrations.
- Do not change Layer A booking/payment.
- Do not change Mini App.
- Do not auto-create tours.
- supplier_offer != tour.
- Direct booking CTA remains controlled by active authoritative execution link + bookable linked tour.

Create:
docs/OPERATOR_LINK_CREATE_REPLACE_UI_GATE.md

Include:
1. Current accepted state
2. Why create/replace was postponed
3. Required tour selection UX
4. Compatibility filters:
   - same sales_mode
   - tour exists
   - tour status safe to show
   - optional: operator can still link non-bookable tour, but CTA remains disabled by resolver
5. Create link flow
6. Replace link flow
7. Confirmation / danger messages
8. Fail-safe behavior
9. Tests required
10. First safe runtime slice recommendation

Update:
docs/CHAT_HANDOFF.md with reference to this gate.

Do not touch runtime code.
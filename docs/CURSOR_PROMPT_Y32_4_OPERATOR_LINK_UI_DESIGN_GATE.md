Continue Tours_BOT strict continuation.

Task:
Create a docs-only design gate for Telegram/admin operator UI to manage supplier_offer_execution_links.

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPERATOR_EXECUTION_LINK_WORKFLOW_GATE.md
- docs/SUPPLIER_CONVERSION_BRIDGE_IMPLEMENTATION_GATE.md
- docs/DESIGN_1_SUPPLIER_MARKETPLACE_ARCHITECTURE_CHECKPOINT.md

Goal:
Design operator/admin UI flow for:
1. View supplier offer execution link status
2. Create link offer -> tour
3. Replace active link
4. Close active link
5. View link history

Rules:
- Docs only.
- No runtime code.
- No migrations.
- Do not change Layer A booking/payment.
- Do not auto-create tours.
- Do not merge supplier_offer and tour.
- Preserve direct CTA only through active authoritative link.

Create:
docs/OPERATOR_EXECUTION_LINK_UI_GATE.md

Include:
1. Current state
2. User roles / permissions
3. UI entry points
4. Screen/button flow
5. Validation messages
6. Fail-safe states
7. Minimal first runtime slice
8. Out of scope

Update:
docs/CHAT_HANDOFF.md with reference to this gate.
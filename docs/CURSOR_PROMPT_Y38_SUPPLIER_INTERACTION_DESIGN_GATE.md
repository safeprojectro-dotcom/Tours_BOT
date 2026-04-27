You are continuing Tours_BOT as a strict production continuation.

Cursor mode: Plan first, then Agent only for documentation edits.

Goal:
Implement Y38 — Supplier Interaction Design Gate.

Before doing anything, read:
- docs/CHAT_HANDOFF.md
- docs/IMPLEMENTATION_PLAN.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/OPERATOR_WORKFLOW_GATE.md
- docs/OPERATOR_DECISION_GATE.md

Task:
Create a documentation-only design gate before any supplier interaction logic.

Add:
- docs/SUPPLIER_INTERACTION_GATE.md

Update:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

The gate must define:
1. Operator workflow remains decision-only.
2. operator_workflow_intent does not execute supplier logic.
3. Supplier interaction must be a separate future layer.
4. No supplier messages, RFQ, bridge, booking, payment, Mini App, execution links, identity bridge, or customer notifications.
5. Future supplier logic must consume intent as input only, never be triggered directly by intent setting.
6. Current Y36/Y37.2/Y37.4/Y37.5 behavior remains unchanged.

Hard constraints:
- documentation only
- no app/ changes
- no tests/ changes
- no migrations
- no API changes
- no side effects
- no runtime behavior changes

Before editing:
Summarize what Y38 is and why it is safe.

After editing:
Report:
- files changed
- exact boundary decisions added
- what remains out of scope
- next safe step
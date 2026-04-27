You are continuing Tours_BOT.

Current state:
Y38 — Supplier Interaction Design Gate is completed and validated.

--------------------------------
🔒 SOURCE OF TRUTH
--------------------------------

Read:

- docs/CHAT_HANDOFF.md
- docs/IMPLEMENTATION_PLAN.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/OPERATOR_WORKFLOW_GATE.md
- docs/OPERATOR_DECISION_GATE.md

--------------------------------
🎯 GOAL (Y39)
--------------------------------

Define:

👉 Supplier Interaction Entry Points

IMPORTANT:
This is still DESIGN ONLY.
NO IMPLEMENTATION.

--------------------------------
🧱 TASK
--------------------------------

Create:

- docs/SUPPLIER_ENTRY_POINTS.md

Define clearly:

1. What CAN start supplier interaction in future:
   - admin explicit action
   - scheduled job
   - external trigger
   - manual operator-triggered action (NOT intent itself)

2. What MUST NOT start supplier interaction:
   - operator_workflow_intent change
   - operator decision endpoint
   - any implicit side effect

3. Entry point types:
   - explicit API endpoints
   - background workers
   - admin panel actions

4. Separation:
   - operator workflow ≠ supplier execution
   - intent ≠ trigger

5. Required invariants:
   - idempotency
   - auditability
   - explicit invocation
   - no hidden triggers

--------------------------------
🚫 HARD CONSTRAINTS
--------------------------------

❌ no supplier messaging  
❌ no RFQ implementation  
❌ no booking/order/payment  
❌ no Mini App changes  
❌ no execution links  
❌ no identity bridge  
❌ no notifications  

--------------------------------
📌 OUTPUT
--------------------------------

Before editing:
- explain what entry points are and why needed after Y38

After editing:
- files created
- defined entry points
- what is explicitly forbidden
- how it preserves Y38
- next step
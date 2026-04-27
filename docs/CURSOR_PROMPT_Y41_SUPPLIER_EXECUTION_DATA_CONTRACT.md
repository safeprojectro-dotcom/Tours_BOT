You are continuing Tours_BOT after Y38, Y39, and Y40.

Current accepted gates:
- Y38: Supplier Interaction Design Gate
- Y39: Supplier Entry Points Design
- Y40: Supplier Execution Flow Design

Cursor mode:
Plan first, then Agent only for documentation edits.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/SUPPLIER_ENTRY_POINTS.md
- docs/SUPPLIER_EXECUTION_FLOW.md
- docs/OPERATOR_WORKFLOW_GATE.md
- docs/OPERATOR_DECISION_GATE.md

Goal:
Define Y41 — Supplier Execution Data Contract Design.

Create:
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md

Update:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Define documentation-only data contracts for future supplier execution.

Must define:
1. Minimal future execution request record:
   - id
   - source_entry_point
   - source_entity_type
   - source_entity_id
   - operator_workflow_intent_snapshot
   - requested_by_user_id
   - status
   - idempotency_key
   - created_at
   - updated_at

2. Minimal future execution attempt record:
   - id
   - execution_request_id
   - attempt_number
   - channel_type
   - target_supplier_ref
   - status
   - provider_reference
   - error_code
   - error_message
   - created_at

3. Minimal future result/audit fields:
   - final_status
   - completed_at
   - completed_by
   - raw_response_reference
   - audit_notes

4. Status boundaries:
   - pending
   - validated
   - blocked
   - attempted
   - succeeded
   - failed
   - cancelled

5. Separation rules:
   - no mutation of orders/payments/bookings
   - no Mini App dependency
   - no execution link mutation
   - no identity bridge mutation
   - no customer notifications

6. Intent usage:
   - operator_workflow_intent may be snapshotted for context
   - must not be live trigger
   - must not be the primary execution state

Hard constraints:
- documentation only
- no migrations
- no models
- no schemas
- no app/ changes
- no tests/ changes
- no API changes
- no runtime behavior changes

Before editing:
Explain why a data contract is needed before implementation.

After editing:
Report:
- files changed
- proposed records/contracts
- invariants
- forbidden mutations
- next safe step
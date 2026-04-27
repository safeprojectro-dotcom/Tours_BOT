You are continuing Tours_BOT after Y38–Y42.

Goal:
Implement Y43 — Supplier Execution Persistence Foundation.

This is the FIRST implementation slice, but it is persistence-only.

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/SUPPLIER_ENTRY_POINTS.md
- docs/SUPPLIER_EXECUTION_FLOW.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md

Create only:
- Alembic migration
- ORM models/enums
- minimal repository helpers if required for tests
- focused tests for schema/model persistence

Implement future persistence records from Y41:
1. supplier_execution_requests
2. supplier_execution_attempts

Required rules:
- no supplier messaging
- no execution runtime
- no API endpoints
- no workers
- no Mini App changes
- no booking/order/payment mutation
- no RFQ implementation
- no execution links
- no identity bridge
- no customer notifications
- no operator-decision behavior changes

Data rules:
- operator_workflow_intent may be stored only as snapshot/context
- it must not be trigger/state machine driver
- execution status must be separate from operator intent
- include idempotency_key
- include audit fields from Y42 where appropriate
- fail closed in model/repository validation where possible

Before coding:
1. summarize Y38–Y42 constraints
2. list exact files expected to change
3. explain why this is safe

After coding:
1. list changed files
2. list migration name
3. list tests added/run
4. confirm no runtime behavior changed
5. state next safe step
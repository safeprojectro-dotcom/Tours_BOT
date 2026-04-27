You are continuing Tours_BOT after Y47.

Current state:
- Y46 admin trigger can create supplier_execution_request
- Y47 defines request != attempt
- NO supplier messaging exists
- NO execution runtime exists

Cursor mode:
Plan first, then Agent.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_EXECUTION_TRIGGER_DESIGN.md
- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md

Goal:
Implement Y48 — safe supplier execution attempt creation.

Add one admin endpoint:

POST /admin/supplier-execution-requests/{request_id}/attempts

Allowed behavior:
- require ADMIN_API_TOKEN
- validate supplier_execution_request exists
- validate request is in allowed status
- create supplier_execution_attempt row only
- assign next attempt_number safely
- status must be pending / created-equivalent
- return attempt data

Must NOT:
- send supplier messages
- call supplier APIs
- run workers
- retry automatically
- change request into executed/succeeded
- create RFQ
- create booking/order/payment
- touch Mini App
- create execution links
- modify identity bridge
- notify customers or suppliers
- change operator-decision behavior

Implementation requirements:
- add request/response schemas if needed
- add service method for attempt creation only
- repository helper for next attempt_number if needed
- fail closed on missing/invalid request
- no hidden triggers
- no outbound I/O

Tests:
- auth required
- missing ADMIN_API_TOKEN behavior matches admin API
- unknown request returns 404
- invalid request status rejected
- valid request creates one pending attempt
- repeated calls create explicit attempt_number 1, 2, 3 only when endpoint is called again
- no supplier messaging/outbound calls
- no order/payment/Mini App changes

Before coding:
1. summarize Y47 separation
2. list files expected to change
3. explain why this remains safe

After coding:
1. files changed
2. endpoint added
3. tests added/run
4. confirm no outbound messaging/execution
5. next safe step
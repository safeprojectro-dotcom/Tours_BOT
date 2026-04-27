You are continuing Tours_BOT after Y45.

Current state:
- Y43 persistence exists
- Y44 admin read-only visibility exists
- Y45 trigger design accepted
- NO supplier execution runtime exists
- NO supplier messaging exists

Cursor mode:
Plan first, then Agent.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/SUPPLIER_ENTRY_POINTS.md
- docs/SUPPLIER_EXECUTION_FLOW.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md
- docs/SUPPLIER_EXECUTION_TRIGGER_DESIGN.md

Goal:
Implement Y46 — Safe Admin Supplier Execution Trigger Endpoint.

Add one admin endpoint:

POST /admin/supplier-execution-requests

What it may do:
- require ADMIN_API_TOKEN
- validate input
- validate source_entity_type/source_entity_id
- require idempotency_key
- create or idempotently resolve supplier_execution_request
- store audit/context fields
- return created/existing request

What it must NOT do:
- contact supplier
- send supplier messages
- call supplier APIs
- create attempt rows
- create RFQ
- create booking/order/payment
- touch Mini App
- create execution links
- modify identity bridge
- notify customers
- change operator-decision behavior

Implementation requirements:
- add request schema
- add service method for trigger/create only
- use existing Y43 repository/model
- reuse admin auth
- fail closed
- idempotency safe
- no hidden triggers

Tests:
- auth required
- missing ADMIN_API_TOKEN returns existing admin behavior
- missing/blank idempotency key rejected
- invalid source entity rejected
- valid request creates supplier_execution_request
- repeated same idempotency key returns/resolves existing request without duplicate
- no attempt rows created
- no unrelated tables mutated where practical

Before coding:
1. summarize Y45 trigger rules
2. list files expected to change
3. explain why this remains safe

After coding:
1. files changed
2. endpoint added
3. tests added/run
4. confirm no supplier messaging/execution/attempt rows
5. next safe step
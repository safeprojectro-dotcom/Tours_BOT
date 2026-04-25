Continue Tours_BOT after Y36 operator assignment MVP.

Task:
Create docs-only design gate for operator workflow on custom marketplace requests.

Context:
Accepted:
- Y36.2 Assign to me works for custom marketplace requests.
- Y36.2A ORM mapper crash fixed.
- Y36.4 Telegram assignment UI polish accepted.
- Y36.6 admin request date formatting fixed.
- Assignment is ownership only and does not change request lifecycle/status.

Goal:
Design the next safe operator workflow layer after assignment.

Scope:
Custom marketplace requests only.
Docs only.

Do not modify:
- runtime code
- migrations
- API routes
- Telegram handlers
- Mini App
- booking/payment
- supplier routes
- execution links
- identity bridge

Design must cover:

1. Current accepted state
- admin can view requests
- admin/operator can assign to self
- status remains unchanged

2. Workflow goal
- allow operator to move an assigned request through safe operational states

3. Status model options
- reuse existing CustomMarketplaceRequestStatus where possible
- document if new statuses are needed later
- avoid mixing owner assignment with lifecycle status

4. First safe workflow action
Recommended:
- Mark as under review / start handling
Only if request is assigned to current operator.

5. Future actions
- resolve
- close
- reassign
- unassign
- add internal note
All future-only unless separately gated.

6. Permissions
- admin/operator only
- customer Mini App remains user-scoped
- supplier routes unchanged

7. Fail-safe rules
- cannot workflow-change unassigned request
- cannot change request assigned to another operator
- terminal states blocked
- no payment/booking/bridge side effects

8. Telegram UI concept
- request detail shows owner + status
- button appears only when allowed
- no PII in callback_data
- compact callbacks

9. API concept
- narrow admin endpoint for first action
- example: POST /admin/custom-requests/{id}/mark-under-review
- actor resolved using existing Y36 actor pattern

10. Tests required
- success for assigned-to-me
- blocked when unassigned
- blocked when assigned to another operator
- blocked terminal
- Telegram button visibility
- Mini App privacy regression
- no supplier/booking/payment changes

Create:
docs/OPERATOR_WORKFLOW_GATE.md

Update:
docs/CHAT_HANDOFF.md with Y37.1 docs-only gate and next-safe pointer.

Stop after docs-only design gate.
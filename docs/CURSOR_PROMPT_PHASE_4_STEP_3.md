# Cursor Prompt — Phase 4 / Step 3

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, and `docs/CHAT_HANDOFF.md`, implement only the minimal payment webhook/API delivery slice on top of the existing payment reconciliation service.

Goal:
Expose payment reconciliation through a minimal API/webhook entry point while keeping signature verification and provider parsing isolated from the reconciliation logic.

Allowed scope:
- add a minimal payment webhook/API route or routes
- add isolated signature verification/helper logic for the mock/provider-agnostic input format
- parse incoming provider payload into the existing reconciliation schema
- call the existing payment reconciliation service
- return safe API responses
- keep reconciliation logic in the service layer, not in the route layer

Requirements:
- route layer must stay thin
- provider parsing/verification must stay separate from reconciliation logic
- reconciliation service must remain the single place for state updates
- do not implement refunds
- do not implement waitlist logic
- do not implement handoff logic
- do not implement reminder/expiry workers
- do not implement group behavior
- do not implement Mini App UI
- do not add admin workflows

Do not implement yet:
- refund workflow
- reminder workers
- expiry worker execution
- waitlist actions
- handoff lifecycle
- group bot behavior
- Mini App UI
- full provider-specific SDK integration beyond minimal mock/provider-agnostic handling

Before writing code:
1. list the routes, services, schemas, and helpers you will add or extend
2. explain the boundary between webhook/API delivery and reconciliation logic
3. explain the signature verification/parsing assumptions
4. explain what remains postponed

Then generate the code and tests.
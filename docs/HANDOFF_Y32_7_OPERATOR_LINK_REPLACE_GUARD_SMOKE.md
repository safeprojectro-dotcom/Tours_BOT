# Y32.7 — Operator Execution Link Replace Guard Smoke

## Scope
Validation of Telegram admin create/replace execution link flow and safety guards.

## Verified

### Create flow
- Execution link created from Telegram UI
- Only one active link exists per offer

### View flow
- Active link displayed correctly
- Tour id/code/status/sales_mode visible
- Link history visible

### Close flow
- Active link can be closed
- System transitions to safe no-link state
- History correctly updated with close_reason=unlinked

### Replace flow (UI)
- Replace action available when active link exists
- System requests explicit tour_id or exact tour code

### Safety guard (critical)
- sales_mode mismatch correctly blocked
- No state change occurs on mismatch
- Admin receives clear error message

## Result
System behaves according to OPERATOR_EXECUTION_LINK_WORKFLOW_GATE:
- single active link enforced
- no auto-tour creation
- strict compatibility validation
- fail-closed behavior

## Limitations (expected)
- No tour search UI yet (manual ID/code only)
- No second compatible full_bus tour for full replace test

## Status
ACCEPTED — safe to proceed to next iteration
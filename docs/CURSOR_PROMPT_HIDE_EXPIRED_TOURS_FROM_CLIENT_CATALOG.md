Implement a small hygiene fix:

Hide expired / no-longer-sellable tours from **customer-facing catalog and public read paths**,
without changing admin visibility or breaking Layer A booking/admin behavior.

## Goal
Customer-facing Mini App / public tour listing should not show tours that are already expired for sale or already departed.

Example problem:
`TEST_BELGRADE_001` still appears in the customer catalog even though its departure date is already in the past, which creates false expectations and confuses smoke testing.

## Scope
Touch only the minimum read-side filtering needed for:
- Mini App catalog
- customer-facing/public tour list/read paths that reuse the same catalog visibility rules

Do not redesign admin listing behavior.

## Mandatory rule
Admin visibility must remain unchanged:
- admin can still list/read expired, past, archived, or diagnostic tours as before
- this change is only for customer/public visibility

## Recommended customer visibility rule
A tour should be hidden from customer-facing catalog/read paths if it is no longer sellable.

Prefer a safe filter like:
- hide when `departure_datetime < now`
and/or
- hide when `sales_deadline` exists and `sales_deadline < now`

Use the project’s existing business logic and statuses where appropriate.
Do not invent a broad new visibility system.

## Expected behavior
Customer/Mini App catalog should include only tours that are still relevant for sale/use.
At minimum, expired past tours like `TEST_BELGRADE_001` should no longer appear in the public catalog.

Smoke tours such as:
- `SMOKE_PER_SEAT_001`
- `SMOKE_FULL_BUS_001`

should remain visible while they are future-dated and sellable.

## Constraints
Do NOT:
- change admin APIs or admin filtering semantics
- change booking/payment logic
- change reservation logic
- change marketplace/RFQ logic
- change showcase publication logic
- add migrations unless absolutely unnecessary
- redesign statuses

## Files/modules to touch
Only the minimum necessary catalog/public read paths and related tests.

Likely areas:
- customer-facing tour query/filter logic
- Mini App catalog route/service/repository
- tests covering catalog visibility

## Testing expectations
Add/update focused tests for:
1. future open/sellable tour appears in customer catalog
2. past/expired tour does not appear in customer catalog
3. admin visibility remains unchanged
4. smoke tours still appear if future-dated
5. no regression in normal Mini App catalog behavior

## Before coding
Summarize:
1. exact files/modules you plan to touch
2. whether any migration is needed
3. exact customer-facing visibility rule you will implement
4. what stays out of scope

## After coding
Report:
1. files changed
2. whether migration was needed
3. tests run
4. results
5. exact customer-facing visibility rule now applied
6. confirmation that admin visibility is unchanged
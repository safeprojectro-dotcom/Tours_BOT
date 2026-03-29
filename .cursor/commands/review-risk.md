---
description: Review implementation risks for the current code or feature
argument-hint: <feature, module, or current changes>
---

# /review-risk

Review the current implementation or proposed change for:

1. architecture violations
2. hidden coupling
3. missing tests
4. unsafe database changes
5. booking/payment race conditions
6. multilingual issues
7. handoff logic gaps
8. maintainability risks

Return the answer in this structure:

## Risks found
## Why each risk matters
## Recommended fixes
## What to test next

Important:
- be concrete
- prefer small actionable fixes
- pay extra attention to booking, payment, reservation status, and waitlist logic

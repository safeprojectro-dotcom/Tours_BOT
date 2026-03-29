---
description: Analyze feature testing before and after implementation
argument-hint: <feature or change>
---

# /test-feature

For the requested feature or code change:

1. identify affected modules
2. identify business risks
3. propose unit tests
4. propose integration tests
5. list edge cases
6. explain manual verification steps
7. recommend the smallest safe implementation step first

Return the answer in this structure:

## Affected modules
## Risks
## Unit tests
## Integration tests
## Edge cases
## Manual verification
## Smallest safe implementation step

Important:
- focus on booking, payment, reservation expiration, waitlist, multilingual behavior, and handoff if relevant
- do not claim something is tested unless it was actually tested


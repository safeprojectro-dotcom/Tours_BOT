Implement **Phase 7.1 / Sales Mode / Step 4** as a narrow private bot read-side adaptation.

Prerequisite:
- Step 1 completed
- Step 2 completed
- Mini App adaptation may or may not already exist, but this bot step must still be narrow and backend-policy-driven

## Goal
Make private bot tour presentation and CTA routing reflect backend sales-mode policy, without introducing direct whole-bus booking behavior.

## Constraints
Do not implement:
- direct whole-bus booking
- payment changes
- operator-assisted full-bus workflow
- old Phase 7 followup/operator chain changes
- UI-only policy not backed by backend services

## Safe scope
The bot may:
- read the centralized backend sales-mode policy
- keep current guided flow for `per_seat`
- avoid misleading per-seat booking prompts for `full_bus`
- replace inappropriate booking CTA with a safe placeholder/escalation-oriented response only if it is backed by current available flow constraints

## Must not change yet
- no real full-bus reservation creation
- no real whole-bus payment path
- no handoff workflow expansion unless separately scheduled

## Tests
Add focused bot tests:
- `per_seat` behavior remains compatible
- `full_bus` does not present misleading per-seat booking path
- no regression in unchanged private-tour browsing scenarios

Before coding:
1. summarize current policy stack
2. list exact files to touch
3. list what remains postponed

After coding:
1. files changed
2. private bot behavior changed
3. tests run
4. results
5. postponed items
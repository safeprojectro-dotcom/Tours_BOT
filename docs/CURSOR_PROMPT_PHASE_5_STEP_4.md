Execute Phase 5 / Step 4 and implement the code and tests exactly within that scope.

Keep it narrow:
- implement only the Mini App reservation preparation UI
- connect the read-only tour detail screen to seat-count and boarding-point selection
- provide a preparation-only summary
- use only already existing reservation-preparation, boarding-point, and localized tour preparation capabilities
- keep it mobile-first and aligned with docs/MINI_APP_UX.md
- keep business rules in the existing service layer

Do not implement:
- real reservation creation in this step
- payment UI
- waitlist flow
- handoff workflow
- Mini App auth/init expansion
- unrelated backend expansion

Preparation must remain preparation-only.
Use only already implemented read/preparation capabilities and keep all state-changing reservation creation postponed to the next step.

After implementation, report:
1. files changed
2. tests run
3. results
4. what remains postponed
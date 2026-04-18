Do not implement new feature code yet.

Run a decision/review gate for **Phase 7.1 / Sales Mode / Step 6**.

Current confirmed continuity:
- Step 1 completed: admin/source-of-truth (`tour.sales_mode`)
- Step 2 completed: backend/service-layer sales mode policy
- Step 3 completed: Mini App read-side adaptation
- Step 4 completed: private bot read-side adaptation
- Step 5 completed: operator-assisted full-bus path
- production schema-drift issue was already fixed by applying the Railway migration
- do not reopen old Phase 7 followup/operator chain broadly

## Goal
Decide whether direct whole-bus self-service is actually needed for MVP/staging, or whether the current operator-assisted full-bus path is already sufficient.

This is a design/review checkpoint, not an implementation step.

## What to review
Review the current state across:
- admin/source-of-truth
- backend policy
- Mini App behavior
- private bot behavior
- handoff/operator-assisted full-bus path
- staging/production operational risk

## Main question
Should the project proceed to direct whole-bus self-service implementation at all?

Possible outcomes:
1. **No — current operator-assisted full-bus path is sufficient for MVP/staging**
2. **Yes — direct whole-bus self-service is needed later, but must be designed first**
3. **Yes — direct whole-bus self-service is needed soon and can be broken into narrow future slices**

## Evaluation criteria
Evaluate at minimum:

### Product / UX
- does the current full-bus assisted path already satisfy the likely real user journey?
- is direct self-service likely to reduce friction materially?
- would users realistically complete full-bus booking without human confirmation anyway?

### Operational / business
- is operator review desirable for full-bus requests?
- does full-bus usually imply pricing/conditions that still benefit from human handling?
- would direct self-service create commercial/operational risk?

### Technical
- what is still missing before direct whole-bus booking could be safe?
- do we currently lack required concepts such as:
  - `full_bus_price`
  - capacity/commercial constraints
  - dedicated payment semantics
  - operator approval state
  - booking lifecycle separation for full-bus requests
- would direct self-service require meaningful new schema/service work?

### Risk
- what could break if we rush into direct whole-bus booking now?
- does current architecture suggest keeping full-bus as assisted-only for MVP?

## Required output
Produce a concise but concrete review document or summary that includes:

1. **Current state summary**
   - what Phase 7.1 already implemented successfully
   - what the current user-visible behavior is for `per_seat` and `full_bus`

2. **Gap analysis for direct whole-bus self-service**
   - what is missing
   - what would need explicit design before implementation

3. **Recommendation**
   Choose one:
   - stop at current operator-assisted path for MVP/staging
   - postpone direct whole-bus flow to later roadmap
   - proceed to a future design phase only
   - proceed to a very narrow implementation plan only if strongly justified

4. **If direct whole-bus flow is recommended later**
   outline the minimum safe future rollout order, for example:
   - commercial fields / pricing model
   - dedicated request/approval lifecycle
   - payment semantics
   - customer UX
   - final confirmation path

5. **If current assisted path is sufficient**
   say so explicitly and explain why

## Constraints
- do not change application code
- do not add migrations
- do not refactor services
- do not modify user flows
- do not broaden scope
- keep this as a decision gate only

## After completion
Report:
1. final recommendation
2. whether Step 6 implementation should happen now or not
3. if not, what Phase 7.1 should be considered “good enough” for MVP/staging
4. if yes, the exact minimum next design step before any code

---

## Outcome (completed decision gate)

**Recorded in:** `docs/PHASE_7_1_STEP_6_DECISION_REVIEW.md` — **no** direct whole-bus self-service for MVP/staging; Phase **7.1** Steps **1–5** treated as sufficient until a future **design-first** slice if product requires it.
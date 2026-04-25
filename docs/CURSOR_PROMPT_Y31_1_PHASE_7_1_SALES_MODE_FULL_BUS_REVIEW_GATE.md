Continue Tours_BOT strict continuation.

Task:
Create a design/review gate for Phase 7.1 sales_mode / full_bus continuation before any runtime implementation.

Read first:
- docs/CHAT_HANDOFF.md
- docs/DESIGN_1_SUPPLIER_MARKETPLACE_ARCHITECTURE_CHECKPOINT.md
- docs/TOUR_SALES_MODE_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Goal:
Determine the next safe step for sales_mode / full_bus logic without breaking Layer A.

Must preserve:
- Layer A booking/payment core
- existing per-seat booking flow
- existing payment-entry flow
- Mini App execution truth
- visibility != bookability
- supplier_offer != tour
- fail-closed identity model

Review and document:
1. Current sales_mode implementation state
2. What is already done for per_seat
3. What is already done for full_bus
4. Whether full_bus self-service is still allowed, blocked, or assisted-only
5. How sales_mode affects Mini App actionability
6. How this interacts with supplier_offer_execution_links
7. What remains postponed
8. Next implementation slice, if safe

Create:
docs/PHASE_7_1_SALES_MODE_FULL_BUS_REVIEW_GATE.md

Update:
docs/CHAT_HANDOFF.md

Do not change runtime code.
Do not add migrations.
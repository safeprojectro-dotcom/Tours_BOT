Docs-only handoff sync after manual smoke of operator execution link workflow.

Record in docs/CHAT_HANDOFF.md:
- Admin API execution link workflow was manually smoke-tested.
- Created active link: supplier_offer_id=5 -> tour_id=3.
- Supplier offer view changed from no live booking aggregates to linked execution metrics.
- Because linked tour is full_bus sold out / 0 seats left, direct booking CTA correctly stayed unavailable.
- Sales mode mismatch guard was confirmed: full_bus offer cannot link to per_seat tour.
- Supplier isolation was confirmed: supplier admin sees only own supplier offers, central admin sees all via /admin.
- No Layer A/payment/identity changes were made.

Do not change runtime code.
Do not add migrations.
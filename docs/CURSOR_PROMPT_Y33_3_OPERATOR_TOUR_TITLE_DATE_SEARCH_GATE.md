Continue Tours_BOT strict continuation.

Task:
Create a docs-only design gate for expanding Telegram admin compatible tour search from code-only to title + optional date hint/filter.

Context:
Y33.2 accepted:
- Compatible tour code search works.
- Exact/partial code match works.
- Search results remain filtered by same sales_mode.
- Search result selection reuses confirmation.
- No auto-linking.
- Manual fallback remains.

Read first:
- docs/CHAT_HANDOFF.md
- docs/HANDOFF_Y33_1_OPERATOR_TOUR_SEARCH_GATE_ACCEPTED.md
- docs/OPERATOR_LINK_TOUR_SEARCH_GATE.md
- docs/HANDOFF_Y32_9_OPERATOR_LINK_TOUR_SELECTION_ACCEPTED.md

Goal:
Design next search refinement:
1. title substring search
2. optional date hint/filter in YYYY-MM-DD
3. keep code search behavior unchanged

Rules:
- Docs only.
- No runtime code.
- No migrations.
- No Mini App changes.
- No Layer A booking/payment changes.
- No identity bridge changes.
- No auto-linking.
- supplier_offer != tour.
- Direct booking CTA remains controlled only by active authoritative link + bookable linked tour.

Create:
docs/OPERATOR_LINK_TOUR_TITLE_DATE_SEARCH_GATE.md

Include:
1. Current accepted state
2. Why title/date search is needed
3. Supported input formats
4. Search interpretation rules
5. Compatibility filters
6. Result ordering
7. No-results behavior
8. Fail-safe behavior
9. Tests required
10. First safe runtime slice recommendation

Update:
docs/CHAT_HANDOFF.md with Y33.3 reference.

Do not touch runtime code.
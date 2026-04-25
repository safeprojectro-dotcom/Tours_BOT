Continue Tours_BOT strict continuation.

Task:
Create a docs-only design gate for bounded search/refinement in Telegram admin compatible tour selection UI.

Context:
Y32.9 accepted:
- Compatible tour list works for create/replace execution links.
- Callback_data limit fixed with compact el:* callbacks.
- Candidate selection opens confirmation.
- Confirm replace works.
- Manual fallback remains.
- Postponed: bounded search by tour code/title/date.

Read first:
- docs/CHAT_HANDOFF.md
- docs/HANDOFF_Y32_9_OPERATOR_LINK_TOUR_SELECTION_ACCEPTED.md
- docs/OPERATOR_LINK_TOUR_SELECTION_UI_GATE.md
- docs/OPERATOR_LINK_CREATE_REPLACE_UI_GATE.md

Goal:
Design bounded search/refinement for operator tour selection.

Required design:
1. Search by exact/partial tour code
2. Search by title text
3. Optional date filter or date hint
4. Preserve same sales_mode filter always
5. No auto-linking from search result
6. Search result still goes through confirmation screen
7. Manual fallback remains
8. Pagination/search context is preserved safely

Rules:
- Docs only.
- No runtime code.
- No migrations.
- No Mini App changes.
- No Layer A booking/payment changes.
- No identity bridge changes.
- No auto-create tours.
- supplier_offer != tour.
- Direct booking CTA remains controlled only by active authoritative link + bookable linked tour.

Create:
docs/OPERATOR_LINK_TOUR_SEARCH_GATE.md

Include:
1. Current accepted state
2. Why search is needed
3. Search input UX
4. Supported search fields
5. Filtering and compatibility rules
6. Result card format
7. Pagination/search-state rules
8. Fail-safe behavior
9. Tests required
10. First safe runtime slice recommendation

Update:
docs/CHAT_HANDOFF.md with Y33.1 reference.

Do not touch runtime code.
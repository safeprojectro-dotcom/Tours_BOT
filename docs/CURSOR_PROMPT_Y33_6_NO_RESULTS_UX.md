Continue Tours_BOT from Y33.5 (title + date search completed and accepted).

Implement Y33.6: no-results UX for execution-link tour search.

Requirements:

1. When search returns empty:
   - Show clear message:
     "No compatible tours found."

2. Add guidance:
   - Suggest removing date
   - Suggest using shorter query
   - Suggest manual input

3. Keep buttons:
   - Back to compatible list
   - Manual tour_id/code input
   - Back

4. Do NOT:
   - change search logic
   - change filters
   - change execution-link semantics
   - introduce fuzzy search

5. Keep FSM safe:
   - reuse existing state
   - do not expand callback payload

After implementation:
- run tests
- verify empty search scenario
- report behavior

Stop after Y33.6.
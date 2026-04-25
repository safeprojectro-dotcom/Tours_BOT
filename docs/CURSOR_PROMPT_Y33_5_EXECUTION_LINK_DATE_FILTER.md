Y33.5 — Execution Link Tour Search: Date Hint Filter

Scope

Extend existing search (Y33.2–Y33.4) with optional YYYY-MM-DD date hint.

Do not change:
- existing code/title search behavior
- filtering rules
- confirmation flow
- FSM structure (only extend)

Expected behavior

User can send:

- "2026-06-16"
- "SMOKE 2026-06-16"
- "full-bus 2026-06-16"

System should:

1. Extract date if present (YYYY-MM-DD only)
2. Keep remaining text as query (code/title)
3. Apply filters:

- same sales_mode (mandatory)
- future departure
- not cancelled/completed

4. If date present:
   filter by departure date == YYYY-MM-DD

5. If both query + date:
   apply BOTH filters

6. If only date:
   return all compatible tours on that date

7. If no valid results:
   return safe "no results" message (no mutation)

FSM

- store:
  - search_query
  - search_date (optional)

Do NOT put date into callback data.

UX

Update prompt:

"Send tour code or title. Optionally add date YYYY-MM-DD"

Update result header:

"... — "SMOKE 2026-06-16" — page 1"

Tests required

- date only
- code + date
- title + date
- invalid date ignored
- filter correctness
- confirmation unchanged

Out of scope

- fuzzy date parsing
- ranges
- locale formats
Continue Tours_BOT strict continuation.

Task:
Create final docs-only acceptance handoff for Y33 operator execution-link tour search.

Context:
Y33 implemented and smoke-verified:
- Y33.2 code search
- Y33.4 title search
- Y33.5 YYYY-MM-DD date hint filter
- Y33.6 no-results UX
- Y33.6A FSM routing fix for search input not handled

Create:
docs/HANDOFF_Y33_OPERATOR_LINK_SEARCH_ACCEPTED.md

Update:
docs/CHAT_HANDOFF.md

Document:
- current accepted behavior
- supported inputs:
  - code
  - title
  - YYYY-MM-DD
  - code/title + date
- compatibility filters preserved
- no-results UX
- confirmation flow preserved
- callback/FSM safety
- manual smoke evidence
- postponed items:
  - fuzzy search
  - ranking/scoring
  - advanced filters
  - richer i18n polish
- next safe step recommendation

Strict scope:
Docs only.
No runtime code.
No migrations.
No Mini App.
No Layer A.
No identity bridge.
No execution-link semantics changes.

After completion report files changed and confirm docs-only scope.
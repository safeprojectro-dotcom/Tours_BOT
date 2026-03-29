Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, and `docs/CHAT_HANDOFF.md`, implement only Phase 3 / Step 2.

Current context:
- Phase 3 / Step 1 is already completed
- private bot foundation already exists under `app/bot/`
- current bot layer already supports:
  - `/start`
  - `/language`
  - `/tours`
  - language callbacks
  - simple private tour detail browsing
  - safe deep-link style entry for `tour_<CODE>`
- existing handlers, bot services, keyboards, messages, and minimal FSM state must be extended, not replaced
- keep the current architecture and do not rework completed foundations without necessity

Goal:
Extend the private chat flow for richer tour selection and browsing, while keeping it strictly read-only and preparation-oriented.

Allowed scope:
- extend private chat flow to support richer selection inputs such as:
  - date preference
  - destination preference
  - basic budget-oriented browsing, only if it can be supported safely by the current read/preparation layer
- add or extend thin private handlers
- add or extend bot-layer services only where needed for read-only orchestration
- add multilingual bot messages and keyboards for this richer selection flow
- keep using existing repositories, read services, and preparation services
- keep deep-link behavior compatible with current implementation

Requirements:
- keep handlers thin and service-driven
- keep bot-layer orchestration separate from app service layer
- do not duplicate catalog/tour logic already present in app/services
- if new read/preparation helpers are needed, add them carefully without introducing booking or payment workflows
- preserve language detection/selection behavior already implemented
- handle empty results safely and clearly
- support read-only browsing flow only

Do not implement yet:
- reservation creation
- reservation expiry
- seat decrement logic
- payment flow
- payment reconciliation
- waitlist actions
- handoff workflow
- Telegram group behavior
- Mini App UI
- admin workflows
- content publication workflows
- business workflow logic inside handlers

Implementation constraints:
- extend existing files where appropriate instead of scattering unnecessary new modules
- do not break current `/start`, `/language`, `/tours`, or deep-link behavior
- keep outputs multilingual and aligned with `docs/AI_ASSISTANT_SPEC.md`
- keep private flow aligned with `docs/AI_DIALOG_FLOWS.md`
- preserve PostgreSQL-first architecture even if this step is read-only
- add tests for the new private selection behavior if there is already a test pattern for the bot layer

Before writing code:
1. list the handlers, bot services, schemas, and helper files you will add or extend
2. explain the boundary between read-only selection flow and later reservation workflow
3. explain what logic will stay in bot layer vs app service layer
4. explain what is intentionally postponed
5. explain any assumptions about supported filters and language behavior

Then generate the code.
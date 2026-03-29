Using `docs/TECH_SPEC_TOURS_BOT.md` and `docs/IMPLEMENTATION_PLAN.md`, implement only Phase 2 / Step 4.

Scope:
- add the first service-layer foundations on top of the current repositories and schemas
- implement only safe read-oriented and simple data-access services needed by later phases
- keep services separate from repositories
- keep the design PostgreSQL-first

Allowed service areas:
- catalog lookup service
- tour detail retrieval service
- boarding point retrieval service
- user retrieval/profile read service
- basic order read service
- basic payment read service
- knowledge base lookup service

Requirements:
- services may orchestrate repository calls
- services must not implement booking workflows yet
- services must not implement payment workflows yet
- services must not implement waitlist behavior yet
- services must not implement handoff behavior yet
- keep logic simple, explicit, and data-oriented

Do not implement yet:
- reservation creation/expiry workflow
- payment reconciliation workflow
- waitlist queue/release workflow
- handoff lifecycle workflow
- Telegram handlers
- Mini App UI
- admin workflows
- content publication workflows

Before writing code:
1. list the services you will add
2. explain service boundaries vs repository boundaries
3. explain what is intentionally postponed
4. explain any assumptions

Then generate the code.
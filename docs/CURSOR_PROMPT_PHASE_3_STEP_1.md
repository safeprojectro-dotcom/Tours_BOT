Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, and `docs/AI_DIALOG_FLOWS.md`, implement only Phase 3 / Step 1.

Scope:
- add the private bot foundation for Telegram
- implement only the safe entry-level private chat flow
- support language detection or explicit language selection
- support simple private-chat tour lookup using the existing read/preparation services
- keep the architecture modular and bot layer separate from services

Allowed areas:
- bot startup wiring if needed for the private bot layer
- private chat entry handlers
- /start
- language selection flow
- simple private tour browsing/lookup entry points
- safe use of existing catalog/tour read services
- multilingual message templates for this minimal flow

Requirements:
- do not create reservations yet
- do not implement payment flow yet
- do not implement waitlist flow yet
- do not implement handoff workflow yet
- do not implement group behavior yet
- do not implement Mini App UI yet
- do not add business workflow logic to handlers
- keep handlers thin and service-driven

Before writing code:
1. list the bot files/handlers you will add
2. explain the boundary between handler layer and service layer
3. explain what is intentionally postponed to later Phase 3 steps
4. explain any assumptions about Telegram configuration

Then generate the code.
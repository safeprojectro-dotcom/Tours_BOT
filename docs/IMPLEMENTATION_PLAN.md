# Tours_BOT MVP Implementation Plan

## Goal

Prepare a production-realistic, operationally complete MVP implementation plan for Tours_BOT without changing the approved MVP product scope. The plan remains aligned with [docs/TECH_SPEC_TOURS_BOT.md](docs/TECH_SPEC_TOURS_BOT.md), [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md), [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md), and [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md), while preserving the current 9-phase structure.

## Source Of Truth

- Product and architecture requirements: [docs/TECH_SPEC_TOURS_BOT.md](docs/TECH_SPEC_TOURS_BOT.md)
- Testing priorities and validation approach: [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md)
- AI assistant constraints and policies: [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md)
- AI dialog flow references: [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md)
- Target file for this document: [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)

## Revised Phase Structure

1. Phase 1. Foundation And Architecture
2. Phase 2. Data Model And Booking Core
3. Phase 3. Private Bot Sales Flow
4. Phase 4. Payment And Background Automation
5. Phase 5. Mini App MVP
6. Phase 6. Admin Panel MVP
7. Phase 7. Group Assistant And Operator Handoff
8. Phase 8. Content Assistant And Publication
9. Phase 9. Analytics, Security, And MVP Readiness

## Progress Tracker

| Phase | Name | Status | Key Dependencies | Exit Signal |
|------:|------|--------|------------------|-------------|
| 1 | Foundation And Architecture | planned | Approved tech spec | Repo, env strategy, Telegram/Railway assumptions, startup, health endpoints, process model |
| 2 | Data Model And Booking Core | planned | Phase 1 | PostgreSQL schema, migrations, booking engine, concurrency safety, waitlist base |
| 3 | Private Bot Sales Flow | planned | Phases 1-2 | Telegram private delivery, BotFather setup assumptions, deep links, language routing, reservation guidance |
| 4 | Payment And Background Automation | planned | Phases 2-3 | Payment adapter, webhook safety, expiry/reminder workers, Railway staging verification |
| 5 | Mini App MVP | planned | Phases 2-4 | Mini App UX defined first, then screens, booking, payment, and help flow implemented |
| 6 | Admin Panel MVP | planned | Phases 2-5 | Admin manages tours, translations, orders, handoffs, audit visibility, approval lifecycle |
| 7 | Group Assistant And Operator Handoff | planned | Phases 3-6 | Group delivery rules, anti-spam, CTA routing, operator takeover and return |
| 8 | Content Assistant And Publication | planned | Phases 5-6 | AI-constrained content drafts, approval-before-publish, source-of-truth enforcement, audit trail |
| 9 | Analytics, Security, And MVP Readiness | planned | Phases 1-8 | KPI visibility, production deployment validation, release hardening, rollback readiness |

## Operational Foundations

### Environment Strategy

- Use three explicit environments from the start: `local`, `staging`, and `production`.
- Keep local development close to production for booking, payment, reservation expiry, waitlist, and webhook-sensitive behavior.
- Use staging as the first hosted verification environment before any production release.
- Separate environment variables, bot endpoints, webhooks, databases, and release procedures by environment.

### Secrets Strategy

- Keep bot tokens, payment credentials, admin secrets, database URLs, Redis URLs, webhook secrets, and publication credentials out of source control.
- Standardize secret loading through application settings/config rather than scattered environment reads.
- Provide `.env.example` with placeholder values and documentation for required variables.
- Ensure secret rotation is operationally possible without redesigning the system.

### Process Model

- Define an explicit base process model early:
- `backend` process for FastAPI API and webhook/public endpoints
- `bot` process for Telegram bot delivery logic
- `workers` process or processes for reservation expiry, reminders, waitlist release, publication jobs, and scheduled automation
- Keep process responsibilities clear to avoid mixing bot, business logic, and worker-only behavior.

### Health And Readiness Endpoints

- Define `/health` and `/healthz` as baseline operational endpoints from the beginning.
- Use them for local smoke checks, Railway staging validation, and production readiness checks.
- Keep health checks simple but meaningful enough to validate app startup and core dependencies at the right level.

### PostgreSQL-First Development Rule

- PostgreSQL is the primary target environment for all MVP-critical behavior.
- Local development should be Postgres-first, especially for schema, migrations, seat reservation, concurrency-sensitive updates, idempotency, and payment-related state transitions.
- SQLite may be used only temporarily for limited non-critical convenience work and must not be treated as the source of truth for booking/payment-critical logic.
- Migration and concurrency assumptions must be verified against PostgreSQL before considering a phase done.

### Testing Layers Overview

- `Local terminal tests`: fast unit and integration checks during implementation.
- `Local manual functional tests`: manual validation of Telegram flows, Mini App, admin flows, and operator scenarios.
- `Staging tests on Railway`: deployed validation for bot/webhook delivery, database migrations, workers, payments, health checks, and environment assumptions.
- `Release checks before production`: smoke tests, multilingual checks, payment safety checks, waitlist checks, handoff checks, and rollback readiness.

### GitHub + Railway Deployment Overview

- Treat GitHub repository readiness as an early operational requirement, not a final cleanup task.
- Use Railway for first staging deployment and production hosting path.
- Ensure app startup, process model, health endpoints, migrations, and secrets strategy are Railway-compatible from the beginning.
- Separate feature completion from deployment readiness and release hardening.

### Telegram Delivery Overview

- Treat Telegram as a first-class delivery layer across group chat, private chat, deep links, and Mini App entry.
- Cover BotFather setup, token/secret handling, webhook strategy, commands/menu, group permissions, private routing, and Mini App launch planning explicitly.
- Keep group and private chat behavior separate by design and by testing strategy.

## Telegram Delivery Layer

### Scope

- BotFather setup
- bot token and secret handling
- webhook strategy
- deep links
- group behavior and permissions
- private chat routing
- Mini App launch flow
- bot commands/menu planning
- Telegram-specific test checklist

### BotFather Setup

- Define the bot creation/setup assumptions explicitly before implementation starts.
- Record bot username, command list, menu button behavior, Mini App entry, and allowed interaction modes in operations docs.
- Keep BotFather setup reflected in [docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md).

### Bot Token And Secret Handling

- Store bot token securely through environment/config only.
- Keep webhook secret or validation token separate from bot token.
- Use different secrets per environment where applicable.

### Webhook Strategy

- Use explicit webhook strategy for staging and production.
- Validate webhook routing, security, and environment-specific endpoints.
- Keep local development compatible with webhook or controlled local delivery assumptions.

### Deep Links

- Plan Telegram deep links for private entry, tour-specific entry, and Mini App handoff.
- Ensure deep-link behavior is tested for language, CTA routing, and booking continuity.

### Group Behavior And Permissions

- Define what the bot is allowed to do in groups.
- Capture mention behavior, trigger behavior, command behavior, reply rules, and anti-spam boundaries.
- Prevent collection of private/sensitive booking data in group contexts.

### Private Chat Routing

- Make private chat the main guided booking surface.
- Define transition rules from group to private, from private to Mini App, and from private to handoff.

### Mini App Launch Flow

- Define how the user launches the Mini App from Telegram.
- Cover menu button, CTA button, deep-link handoff, and return-path assumptions.

### Bot Commands/Menu Planning

- Define initial command set and menu behavior before implementation.
- Keep commands aligned with private booking flow, help, bookings, language, and Mini App access.

### Telegram-Specific Test Checklist

- BotFather assumptions verified
- commands/menu behavior verified
- webhook delivery verified
- deep links verified
- group trigger behavior verified
- anti-spam behavior verified
- private chat routing verified
- Mini App launch verified
- handoff from Telegram contexts verified

## Deployment And Environment Track

### Scope

- GitHub repository readiness
- `.gitignore` and `.env.example`
- local development environment
- Railway staging deployment
- Railway Postgres connection
- migrations in staging
- production deployment
- release and rollback checklist

### GitHub Repository Readiness

- Treat repository structure, ignore rules, environment documentation, and operational docs as part of Phase 1 readiness.
- Keep deployment-related documentation versioned with the codebase.

### `.gitignore` And `.env.example`

- Add `.gitignore` early enough to prevent secrets, local caches, build artifacts, and transient files from leaking into the repository.
- Add `.env.example` early enough to make local and Railway environment setup repeatable.

### Local Development Environment

- Prefer Postgres-first local setup.
- Ensure local run assumptions exist for backend, bot, workers, migrations, and tests.
- Capture these steps in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

### Railway Staging Deployment

- Use staging as the first hosted validation target.
- Validate backend, bot, and worker process startup in Railway.
- Confirm environment variables, health checks, migrations, and webhook routing in staging.

### Railway Postgres Connection

- Treat Railway Postgres as the first hosted database verification target.
- Verify connection settings, migrations, reservation logic assumptions, and worker compatibility there.

### Migrations In Staging

- Run and verify migrations in staging before production.
- Treat migration safety as a required gate for booking/payment-critical work.

### Production Deployment

- Separate production deployment readiness from feature completeness.
- Confirm secrets, webhooks, bot delivery, workers, health checks, migrations, and release validation before production cutover.

### Release And Rollback Checklist

- Maintain an explicit release and rollback checklist in [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).
- Include production smoke tests, webhook checks, payment safety checks, and rollback triggers.

## Database Strategy

### Primary Target

- PostgreSQL is the primary database target for the MVP.

### Local Development Rule

- Local development should be Postgres-first.
- Reservation, payment, waitlist, migration, and concurrency-sensitive behavior must be developed and verified against PostgreSQL semantics.

### Temporary SQLite Rule

- SQLite can only be temporary for limited convenience scenarios.
- SQLite must not be treated as the source of truth for booking/payment-critical logic.
- SQLite behavior must not be used to sign off on reservation safety, idempotency, locking, or payment-sensitive flows.

### Migration Safety

- Plan migrations as a first-class part of the implementation, not as cleanup after model work.
- Validate migrations locally on PostgreSQL and again in Railway staging.
- Treat failed migration rollback/recovery planning as part of operational readiness.

### Concurrency Considerations

- Make concurrency behavior explicit for reservation creation, seat decrementing, reservation expiry, payment confirmation, and waitlist release.
- Protect against double booking and duplicate payment-sensitive updates.
- Keep idempotency and concurrency safety in the service/data layer rather than UI logic.

## Testing Layers

### Local Terminal Tests

- Unit tests for business rules, status transitions, language fallback, and assistant decision helpers.
- Integration tests for API endpoints, repositories, migrations, booking engine, payment webhooks, and worker behavior.

### Local Manual Functional Tests

- Telegram private booking flow
- Telegram group CTA flow
- Mini App browse/reserve/pay flow
- admin tour/order/handoff flow
- multilingual display and fallback
- operator escalation flow

### Staging Tests On Railway

- app startup and health endpoints
- Railway Postgres connectivity
- staging migrations
- Telegram webhook delivery
- payment sandbox flow
- worker execution for expiry/reminders/waitlist
- Mini App launch and return flow
- admin operational access

### Release Checks Before Production

- production deploy smoke checks
- production webhook validation
- multilingual smoke tests
- payment safety verification
- waitlist verification
- operator handoff verification
- release checklist completion
- rollback readiness confirmation

## AI Assistant Track

### Source Documents

- [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md)
- [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md)

### Group Vs Private Behavior

- Group behavior must stay brief, factual, CTA-oriented, trigger-driven, and free of private data collection.
- Private chat is the guided booking and qualification surface.
- Mini App support behavior must explain implemented flows only.

### Tool-Driven Assistant Behavior

- Assistant responses for tours, availability, reservation, payment, waitlist, and handoff must rely on actual system tools/services.
- The assistant must not invent prices, dates, availability, payment confirmation, or guarantee statuses.

### Multilingual Behavior

- Detect or confirm user language.
- Persist language preference.
- Use language fallback rules explicitly.
- Avoid confusing language switching.

### Escalation Policy

- Handoff is mandatory for complex, risky, discount, complaint, custom-route, unclear payment, large-group, low-confidence, or explicitly human-requested scenarios.
- Preserve user context and avoid forcing the user to repeat everything.

### Content Assistant Constraints

- Content generation must remain fact-bound and source-of-truth-driven.
- Assistant-generated content must stay in draft/approval flow until explicitly approved.
- The content assistant must not become the source of truth for dates, prices, availability, or status.

## Mini App UX Definition

### Explicit Pre-Implementation Step

Before full Mini App implementation, define the UX in [docs/MINI_APP_UX.md](docs/MINI_APP_UX.md).

### Required UX Definition Scope

- screen map
- CTA hierarchy
- loading states
- empty states
- error states
- reservation timer state
- help/handoff entry points

### Intent

- Make Mini App structure explicit before coding full screens.
- Ensure booking, payment, timer, error recovery, and human-help entry are designed before implementation spreads across multiple surfaces.

## Delivery Principles

- Keep bot layer, service layer, repository layer, Mini App layer, content logic, and analytics logic separated from the start.
- Treat multilingual support as a cross-cutting architectural requirement, not a final polish step.
- Use service methods for business rules and keep statuses, languages, and policy values out of UI-only logic.
- Make Telegram delivery rules explicit for group, private chat, Mini App entry, and handoff flows.
- Validate critical flows with small targeted tests before expanding scope.
- Prefer minimal vertical slices that prove one working path before broadening features.
- Keep the assistant fact-bound, tool-driven, escalation-aware, and aligned with the AI assistant documents.

## Required Companion Documents

- [docs/MINI_APP_UX.md](docs/MINI_APP_UX.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)
- [docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md)

## Proposed Repository Targets

- `docs/IMPLEMENTATION_PLAN.md`
- `docs/MINI_APP_UX.md`
- `docs/DEPLOYMENT.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/TELEGRAM_SETUP.md`
- `app/` or `src/` as the backend root
- `app/bot/`, `app/api/`, `app/services/`, `app/repositories/`, `app/models/`, `app/schemas/`, `app/workers/`, `app/admin/`, `app/content/`, `app/analytics/`
- `mini_app/` for Flet UI
- `tests/unit/`, `tests/integration/`, `tests/manual/`
- `alembic/` for migrations

## Phase 1

### Phase Number

1

### Phase Name

Foundation And Architecture

### Goal

Establish the repository structure, environment strategy, Telegram/Railway readiness, app bootstrap, health contracts, process model, module boundaries, and architectural conventions required for all later MVP work.

### Included Scope

- Create the initial project layout for FastAPI backend, aiogram bot integration points, Flet Mini App area, workers, and shared domain layers.
- Prepare GitHub repository readiness: `.gitignore`, `.env.example`, baseline docs layout, test folders, and stable folder conventions.
- Define explicit environment strategy for local, staging, and production.
- Define environment-based settings for PostgreSQL, Redis, bot credentials, payment adapter settings, publication credentials, and webhook/base URL configuration.
- Ensure startup design is Railway-compatible for backend API, bot process, and workers.
- Define base process model: backend, bot, workers, and admin surface assumptions.
- Add `/health` and `/healthz` as standard operational endpoints.
- Set up base dependency wiring, logging, structured error handling, and operational error-reporting conventions.
- Define shared enums/constants strategy for booking, payment, cancellation, and tour statuses without hardcoding them in UI logic.
- Define multilingual-ready primitives: language codes, translation lookup conventions, fallback rules, and user language persistence rules.
- Define Telegram integration assumptions: BotFather setup requirements, token/secret handling assumptions, webhook mode, group vs private delivery split, deep-link usage, Mini App launch entry points, and command/menu planning.
- Define Postgres-first local setup rule and explicitly reject SQLite as a source of truth for booking/payment-critical validation.
- Document module responsibilities and boundaries before feature work starts.
- Project README with local run and environment notes

### Done-When Criteria

- The repository has a clear modular skeleton and startup entry points for backend, bot, and workers.
- GitHub repository support files are part of the planned foundation work.
- Settings are loaded from environment/config instead of hardcoded values.
- Railway-compatible startup assumptions are documented.
- `/health` and `/healthz` are part of the baseline operational contract.
- Core architectural decisions are documented and consistent with the tech spec.
- Base logging and error-handling patterns are defined.
- Multilingual support has a defined persistence and fallback model.
- Telegram delivery assumptions are documented for group, private, deep links, Mini App launch, and command/menu behavior.
- Postgres-first local setup is the explicit rule for critical flows.
- Base process model is explicitly defined.

### Dependencies

- Approved requirements from [docs/TECH_SPEC_TOURS_BOT.md](docs/TECH_SPEC_TOURS_BOT.md)
- Assistant behavior constraints from [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md)

### Suggested Tests/Checks

- Local terminal smoke check: backend app starts with local config.
- Local terminal smoke check: settings validation fails cleanly on missing required env vars.
- Local terminal smoke check: health endpoint contract is defined and testable.
- Unit tests for config parsing and language fallback helper behavior.
- Local manual review of Telegram assumptions, command/menu plan, and process model.
- Local manual review of module boundaries against the spec.
- Staging readiness review for Railway-compatible startup and process model.

### Status

planned

## Phase 2

### Phase Number

2

### Phase Name

Data Model And Booking Core

### Goal

Implement the foundational PostgreSQL-first data model and business services for tours, users, orders, reservation windows, seat accounting, idempotent booking-sensitive actions, and waitlist behavior.

### Included Scope

- Design and implement the MVP schema for `users`, `tours`, `tour_translations`, `boarding_points`, `orders`, `payments`, `waitlist`, `handoffs`, `messages`, `content_items`, and `faq/knowledge_base`.
- Treat PostgreSQL migrations as the primary target and plan all schema behavior around PostgreSQL semantics.
- Create migrations and initial seed/demo data strategy for statuses, languages, sample tours, and local/staging validation flows.
- Implement repositories and service methods for tour search, tour details, seat availability, reservation creation, reservation cancellation, and order confirmation.
- Implement reservation expiration calculations based on departure timing and sales deadlines.
- Make concurrency assumptions explicit for reservations, seat deduction, expiration, and payment-sensitive updates.
- Add idempotency assumptions and protections for reservation creation, payment callbacks, confirmation, cancellation, and worker reprocessing.
- Implement waitlist enqueue/release rules and alternative-tour suggestion hooks.
- Store user profile basics needed for language and lead-source tracking.
- Add staging DB verification note so booking-critical behavior is explicitly revalidated against hosted PostgreSQL before later phases depend on it.

### Done-When Criteria

- All MVP entities from the spec exist in schema and migrations.
- PostgreSQL is the verified reference environment for schema and migration behavior.
- Booking services can create, hold, expire, confirm, and cancel reservations safely.
- Seat counts cannot oversell under normal concurrent access patterns.
- Idempotent behavior is defined for booking/payment-sensitive operations.
- Waitlist records can be created and linked to future release logic.
- Service interfaces exist for bot, Mini App, admin, and worker usage.
- Seed/demo data assumptions are sufficient for local and staging validation.

### Dependencies

- Phase 1 foundations

### Suggested Tests/Checks

- Local terminal unit tests for reservation window calculation.
- Local terminal unit tests for booking status transitions and cancellation transitions.
- Local terminal unit tests for waitlist queue behavior.
- Local terminal integration tests for create reservation, expire reservation, and seat restoration.
- Local terminal integration tests for race-condition-sensitive seat booking logic.
- Local Postgres migration safety check on a clean database.
- Staging check on Railway Postgres to confirm migrations and reservation-critical behavior match local expectations.

### Status

planned

## Phase 3

### Phase Number

3

### Phase Name

Private Bot Sales Flow

### Goal

Deliver the first end-to-end customer sales flow in Telegram private chat: identify user intent, determine language, propose tours, create a reservation, and guide the user toward Mini App, payment, or human help.

### Included Scope

- Implement Telegram private chat routing, commands, callbacks, and deep-link entry points.
- Add explicit Telegram setup work: BotFather setup assumptions, bot commands, menu button behavior, and Mini App launch entry assumptions.
- Define bot token/secret handling assumptions as they affect delivery and environment setup.
- Define group-to-private and private-to-Mini-App routing rules.
- Add language detection and explicit language selection fallback.
- Support required sales scenarios: search by date, destination, budget, seat count, and boarding point.
- Implement intent coverage for the MVP list in the spec with rules-based or pluggable classification architecture.
- Align assistant behavior with [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md): one step at a time, no invented facts, 1-3 options only, tool-driven answers, and safe handoff behavior.
- Align private flow sequence with [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md): tour selection, reservation creation, reservation-to-payment transition, waitlist fallback, and human request handling.
- Connect private flow to booking services for temporary reservation creation.
- Provide CTA transitions into Mini App and payment flow.
- Add core multilingual templates for sales, reservation, payment reminder, confirmation, waitlist, and escalation messaging.
- Store message history and key intent metadata for auditability and future analytics.

### Done-When Criteria

- A user can start in private chat, choose language, receive 1-3 relevant tour options, and create a temporary reservation.
- BotFather assumptions, commands, menu design, webhook/deep-link expectations, and Mini App launch strategy are defined well enough to support implementation and deployment.
- The bot can explain booking/payment next steps and link the user to Mini App or payment.
- Low-confidence or complex scenarios can be routed toward handoff hooks.
- Message templates and flows work with language fallback.
- Private behavior is consistent with the assistant spec and dialog flows.

### Dependencies

- Phase 1 architecture and Telegram assumptions
- Phase 2 booking and user services
- Assistant behavior sources: [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md), [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md)

### Suggested Tests/Checks

- Local terminal unit tests for intent-to-action routing.
- Local terminal unit tests for multilingual template fallback in private chat.
- Local terminal integration tests for private chat booking transition through service layer.
- Local manual Telegram tests for BotFather command/menu assumptions, webhook/deep-link behavior, language selection, date search, destination search, budget search, and reservation creation.
- Local manual checks for unsupported/complex requests routing toward human help.
- Staging tests on Railway for webhook delivery to private flow and deep-link entry behavior.

### Status

planned

## Phase 4

### Phase Number

4

### Phase Name

Payment And Background Automation

### Goal

Add safe payment processing abstractions plus automated expiry, reminder, and status-update workers that make reservation flow production-safe for MVP across local and Railway staging environments.

### Included Scope

- Implement provider-agnostic payment adapter interface and first concrete provider integration.
- Add payment session creation, payment status polling/checking, and webhook processing.
- Enforce idempotent payment confirmation and duplicate-payment protection.
- Update order/payment statuses after successful or failed payment events.
- Validate webhook signatures/secrets and define safe staging/production webhook strategy.
- Implement workers for reservation expiration, one-hour-before-expiry reminders, predeparture messages, departure-day reminders, post-trip follow-up, and waitlist release notifications.
- Ensure payment and reservation logs are stored for traceability.
- Define Railway staging worker/process deployment assumptions for backend, bot, and worker execution.
- Add explicit Railway staging verification for payment sandbox flow, webhook validation, worker execution, and reminder processing.

### Done-When Criteria

- Payment sessions can be created from an order and reconciled back into order status.
- Webhook processing is validated, logged, and idempotent.
- Sandbox payment flow is proven in a safe test environment.
- Expired reservations automatically release seats and notify the user.
- Scheduled notifications can be triggered against order lifecycle events.
- Waitlist release notifications can use freed seats according to business rule.
- Railway staging process assumptions for workers are documented and validated.
- Staging webhook/payment/worker verification is complete.

### Dependencies

- Phase 2 order/payment models and services
- Phase 3 reservation flow entry points

### Suggested Tests/Checks

- Local terminal unit tests for payment status mapping and idempotent update logic.
- Local terminal integration tests for payment webhook handling.
- Local terminal integration tests for reservation expiration worker and seat restoration.
- Local terminal integration tests for waitlist release worker behavior.
- Local manual sandbox test for successful payment and expired unpaid reservation.
- Staging tests on Railway for webhook validation, payment reconciliation, and reminder worker execution.
- Staging verification that backend, bot, and workers can run with the expected process model.

### Status

planned

## Phase 5

### Phase Number

5

### Phase Name

Mini App MVP

### Goal

Define the Mini App UX explicitly before full implementation, then deliver the Flet Mini App experience for browsing tours, viewing details, reserving seats, starting payment, viewing bookings, and requesting help.

### Included Scope

- Add an explicit pre-implementation step: `Mini App UX Definition`.
- Create [docs/MINI_APP_UX.md](docs/MINI_APP_UX.md) before or together with implementation.
- Define screen map for catalog, filters, tour card, booking, payment, my bookings, language/settings, and help/operator entry points.
- Define CTA hierarchy for browse, details, reserve, pay, join waitlist, ask human, and return to bookings.
- Define loading, empty, and error states.
- Define reservation timer state.
- Define help/handoff entry points.
- Implement Mini App authentication/init flow with Telegram context.
- Build mobile-first catalog with filters, availability, pricing, and status badges.
- Build tour detail screen with gallery, descriptions, program, included/excluded, boarding points, price, seats, and policies.
- Build reservation screen for seat count, boarding point, reservation timer, and reserve action.
- Build payment screen with amount, timer, and transition into payment scenario.
- Build my bookings screen with active bookings, confirmed bookings, canceled items, waitlist entries, and payment status.
- Add language/settings/help entry points and operator-contact CTA.
- Reuse service layer from phases 2-4; do not duplicate business rules in the Mini App.
- Align Mini App support behavior with [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md) and [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md).

### Done-When Criteria

- Mini App UX is explicitly defined before or together with implementation, including screen structure, CTA hierarchy, loading/empty/error states, timer state, and help entry points.
- A Telegram user can open the Mini App and browse available tours.
- The user can view a tour, reserve seats, start payment, and later view booking status.
- The Mini App shows multilingual content and graceful fallback where translations are missing.
- The UI exposes help/operator paths without embedding business logic in the frontend.

### Dependencies

- Phase 2 domain services and schemas
- Phase 4 payment lifecycle and reservation timer behavior
- Telegram delivery assumptions from Phases 1 and 3

### Suggested Tests/Checks

- Local terminal integration tests for Mini App auth/init endpoint and catalog endpoint.
- Local terminal integration tests for Mini App booking and payment endpoints.
- Local manual mobile-first checks for catalog, tour card, booking, payment, timer state, error state, waitlist fallback, and my bookings.
- Local manual multilingual display check for translated and fallback tour content.
- Staging tests on Railway for Mini App entry, auth context, payment redirect/return behavior, and help entry points.

### Status

planned

## Phase 6

### Phase Number

6

### Phase Name

Admin Panel MVP

### Goal

Provide the operational control surface for tours, translations, media assumptions, orders, boarding points, handoffs, approval-driven workflows, and audit visibility.

### Included Scope

- Implement admin authentication/authorization baseline and protected admin API.
- Build tour CRUD including dates, pricing, capacity, deadlines, status, guaranteed flag, and media references.
- Define media management assumptions for tour assets and content-related media handling.
- Build translation management for multilingual tour fields.
- Build boarding point CRUD.
- Build order list/detail views with status filters, payment visibility, history, and restricted status updates.
- Build handoff list/assignment/resolve flows.
- Build or plan publication approval lifecycle visibility for generated content.
- Provide operational views for notification history, publication state, and audit visibility where relevant.
- Enforce role separation for admin, operator, and restricted actions.
- Keep all admin actions backed by service-layer validations and audit logging.

### Done-When Criteria

- Admin can create and edit tours from one source of truth.
- Admin can manage multilingual content for tours and boarding points.
- Media assumptions are explicit enough to avoid blocking tour/content workflows.
- Admin can inspect orders, payment state, handoff queue, and publication approval state.
- Sensitive actions are permission-checked, role-scoped, and logged.
- Audit visibility exists for critical operational actions.

### Dependencies

- Phase 2 schema/services
- Phase 4 payment data and lifecycle
- Phase 5 operational needs revealed by Mini App flow

### Suggested Tests/Checks

- Local terminal integration tests for tours CRUD, translations CRUD, and boarding points CRUD.
- Local terminal integration tests for order listing/detail and restricted status update rules.
- Local manual checks for admin tour creation, media assumptions, publication approval visibility, and order oversight flow.
- Security review for admin auth, role separation, and audit logging.
- Staging checks on Railway for protected admin access and operational visibility.

### Status

planned

## Phase 7

### Phase Number

7

### Phase Name

Group Assistant And Operator Handoff

### Goal

Enable group warm-up behavior, controlled CTA-driven routing to private flow, explicit Telegram group safety rules, and robust human escalation for complex cases.

### Included Scope

- Implement group bot behavior for mentions, commands, approved trigger phrases, and explicitly permitted Telegram group interactions.
- Define Telegram group permissions assumptions and operational setup needs.
- Keep group replies short, concrete, action-oriented, and conversion-oriented toward private chat or Mini App.
- Add anti-spam behavior so the bot does not answer every message and stays within approved trigger strategy.
- Prevent collection of personal data in group context and avoid long personal negotiations there.
- Add no-private-data-in-group checks to the delivery rules and manual verification checklist.
- Implement handoff triggers from group and private chat: discounts, group bookings, custom pickup, complaints, payment issues, low-confidence answers, and direct human requests.
- Align behavior with group, handoff, complaint, and human-request flows from [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md).
- Create operator queue behavior with reason, priority, assignment, and return-to-bot state.
- Store message context needed for operator continuity.

### Done-When Criteria

- The bot can respond in group context with CTA without violating group constraints from the spec or AI assistant documents.
- Group permissions assumptions and trigger strategy are documented well enough for deployment setup.
- Anti-spam behavior works as intended.
- Complex or risky cases reliably create handoff records with context.
- Operators can take over and later release a conversation back to bot automation.
- Handoff works consistently from both group and private entry points.

### Dependencies

- Phase 3 private flow foundations
- Phase 6 admin/operator management surfaces
- Assistant behavior sources: [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md), [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md)

### Suggested Tests/Checks

- Local terminal unit tests for handoff trigger evaluation rules.
- Local terminal integration tests for handoff creation and assignment lifecycle.
- Local manual checks in a test Telegram group for mention, trigger, CTA, anti-spam behavior, and no-private-data enforcement.
- Local manual checks for return-to-bot flow after operator intervention.
- Staging tests on Railway for group webhook delivery and handoff persistence.

### Status

planned

## Phase 8

### Phase Number

8

### Phase Name

Content Assistant And Publication

### Goal

Generate reusable multilingual content from a single tour source, support admin approval, and publish approved content to target channels under explicit AI assistant constraints.

### Included Scope

- Implement content generation requests based on tour records and translations.
- Explicitly apply AI assistant content constraints from [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md): fact-bound generation, no source-data mutation, no invented prices/dates/availability, channel-aware formatting, multilingual handling, and draft-only assistant behavior until approval.
- Use [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md) as a reference for content-adjacent assistant interactions where relevant.
- Generate tour card content, Telegram group copy, Facebook copy, Instagram copy, TikTok/Reels structure, CTA variants, last-seats variants, and waitlist variants.
- Store content items with status lifecycle such as draft, generated, approved, published, failed.
- Enforce multilingual content fallback behavior explicitly.
- Enforce source-of-truth behavior so admin-managed tour data remains authoritative.
- Build admin approval/edit/publish workflow with manual approval required before publish.
- Implement publication workers/adapters for MVP target channels as approved in scope.
- Track publication status, timestamps, and publication audit trail per content item.

### Done-When Criteria

- Admin can generate content from a tour without duplicating or overriding source data.
- AI assistant content constraints are reflected in how drafts are generated and reviewed.
- Admin can review, approve, edit, and publish content.
- Manual approval is required before publication.
- Publication status and audit trail are visible and traceable.
- Multilingual content generation and fallback rules are preserved through approval flow.

### Dependencies

- Phase 6 admin panel
- Tour source of truth from Phase 2
- Notification/publication worker patterns from Phase 4
- Assistant behavior sources: [docs/AI_ASSISTANT_SPEC.md](docs/AI_ASSISTANT_SPEC.md), [docs/AI_DIALOG_FLOWS.md](docs/AI_DIALOG_FLOWS.md)

### Suggested Tests/Checks

- Local terminal unit tests for content item status transitions.
- Local terminal integration tests for generate, approve, and publish API flow.
- Local manual checks for content quality, editability, multilingual fallback, and publication audit trail.
- Local manual checks that generated content remains linked to one tour source of truth and cannot bypass manual approval.
- Staging tests on Railway for publication workflow and operational visibility.

### Status

planned

## Phase 9

### Phase Number

9

### Phase Name

Analytics, Security, And MVP Readiness

### Goal

Complete MVP with KPI visibility, operational safeguards, production deployment readiness, release validation, rollback planning, and final acceptance criteria aligned with the expected result.

### Included Scope

- Implement KPI capture for leads, group dialogs, private-chat transitions, Mini App opens, booking conversion, payment conversion, no-show rate, cancellations, tour load, source channels, first-response time, handoff count, and content effectiveness.
- Add dashboards or report endpoints needed for admin visibility.
- Finalize webhook validation, rate limiting, secret handling, role separation, action logging, and defensive error paths.
- Create or finalize [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md), and [docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md) as operational outputs.
- Add explicit production deployment checklist for Railway.
- Add GitHub release checklist.
- Add production webhook validation and production bot delivery validation.
- Add rollback plan and rollback verification steps.
- Run regression validation across the full MVP path: group -> private chat -> reservation -> payment -> confirmation -> notifications.
- Add release smoke tests, multilingual smoke tests, payment safety verification, waitlist verification, and operator handoff verification.
- Document known non-MVP items explicitly so roadmap work does not leak into release scope.

### Done-When Criteria

- MVP KPI metrics are visible to operators/admins.
- Critical security controls from the spec are implemented and verified.
- Railway production deployment and GitHub release steps are documented in operationally usable form.
- Production webhook validation and rollback plan are defined.
- Core user journeys pass targeted regression and smoke checks.
- Multilingual, payment safety, waitlist, and handoff verifications are complete.
- Outstanding gaps are documented and acceptable for MVP release.
- The release scope matches the spec's MVP and excludes non-MVP roadmap work.

### Dependencies

- All previous phases

### Suggested Tests/Checks

- Local terminal integration tests for analytics event creation on key flows.
- Security checks for webhook validation, rate limits, secret handling, and protected admin endpoints.
- Staging tests on Railway for production-like deploy validation, migrations, and webhook behavior.
- Focused release smoke suite for booking logic, payment flow, reservation expiration, waitlist behavior, multilingual fallback, operator handoff, and Mini App entry.
- Manual release checklist covering Telegram setup, group, private chat, Mini App, admin, content, workers, and notifications.
- Rollback drill or documented rollback verification before production release.

### Status

planned

## Cross-Phase Risk Controls

- Booking and payment logic must remain service-layer owned to avoid duplicated rules between bot, Mini App, and admin surfaces.
- Reservation expiry and payment confirmation must be idempotent and concurrency-safe before broader UX rollout.
- PostgreSQL behavior, not SQLite behavior, should decide booking/payment confidence.
- Waitlist and multilingual fallback should be tested from the moment they first appear, not deferred to final QA.
- Handoff must preserve enough conversation context for human continuity.
- Telegram group behavior must remain short, factual, trigger-driven, and free of private data collection.
- Content generation should never become the source of truth for pricing, dates, or availability.
- Deployment readiness must be treated as a parallel track, not a final afterthought.

## Recommended Execution Order

1. Build Phases 1-2 first and verify booking core on PostgreSQL before any UI-heavy work.
2. Deliver the first customer value slice with Phases 3-4 and verify it in local plus Railway staging.
3. Define Mini App UX before full Phase 5 implementation, then build against validated services.
4. Add operational tooling in Phases 6-8 with auditability and approval rules intact.
5. Finish with Phase 9 hardening, staging validation, release checklists, and production readiness review.

## MVP Acceptance Summary

The MVP should be considered implementation-ready when the plan above results in one coherent system where an admin manages tours in one place, Telegram delivery is operationally defined, customers discover and book through group/private chat plus Mini App, reservations expire safely, full payment confirms the order, waitlist and handoff work, multilingual behavior follows documented assistant rules, content can be generated and manually approved before publication, Railway deployment and release operations are documented, and core analytics/security requirements are met.

## Immediate Next Execution Step

Start with **Phase 1 / Step 1** only.

### Scope
- create the backend project skeleton
- define configuration/settings structure
- set up PostgreSQL connection
- initialize SQLAlchemy base
- initialize Alembic
- add `/health` and `/healthz` endpoints
- define modular folder layout

### Do Not Implement Yet
- Telegram bot handlers
- Mini App UI
- booking logic
- payment logic
- admin business features
- content publication features

### Expected Output
- runnable backend skeleton
- environment-based configuration
- database foundation ready for migrations
- health endpoints available
- clear module boundaries for future phases
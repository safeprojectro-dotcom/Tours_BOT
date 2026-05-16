# CURSOR_PROMPT_A1V_VISIBLE_ADMIN_BUTTON_SURFACE_OVER_COCKPIT

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 1dfc53c feat: add cockpit commercial marketing conversion queues
- 8f9180e feat: add read-only admin automation cockpit
- c95bbb8 docs: add admin automation cockpit design gate
- d916f13 docs: add operational automation roadmap
- 2609dd1 docs: close publishing editor read-only foundation

## Previous blocks

A1-Block 1 implemented:

- GET /admin/automation-cockpit
- summary
- supplier_intake
- missing_info
- offer_readiness
- risk_conflict
- safety_summary

A1-Block 2 implemented:

- marketing_review
- publishing_queue
- catalog_conversion
- commercial_context
- fact_lock_note
- read-only commercial/marketing/conversion flow

Railway smoke PASS:

- TotalCards = 20
- Queues:
  - supplier_intake=0
  - missing_info=6
  - offer_readiness=5
  - risk_conflict=9
  - marketing_review=20
  - publishing_queue=20
  - catalog_conversion=20
- safety flags true:
  - read_only
  - no_telegram_io
  - no_publish_attempt
  - no_scheduler
  - no_supplier_notification_send
  - no_qr_token
  - no_layer_a_mutation
  - no_b11_change

## Current block

# A1V — Visible Admin Button Surface over Cockpit

## Block mode

Functional-block mode.

This block is allowed to be larger because it is UI/read-only over an existing read-only cockpit endpoint/service.

It may add:

- Telegram/admin button entry
- admin callback handlers
- rendering helpers
- tests
- docs/handoff

It must NOT add:

- DB migrations
- write endpoints
- POST/PATCH/DELETE
- Telegram channel publish/send
- scheduler
- supplier notification send
- QR tokens
- Layer A booking/payment/order/reservation mutation
- B11 routing changes
- AI execution
- external provider calls
- public customer buttons

---

# Goal

Expose the existing Admin Automation Cockpit through admin-only Telegram buttons so it can be demonstrated and used without PowerShell/API calls.

Admin should be able to click:

📊 Automation Cockpit

and see:

- cockpit summary
- queue counts
- safety flags
- list of queues
- first cards in selected queue
- next-best-action metadata
- fact-lock note for commercial queues
- back/refresh navigation

This is a read-only admin surface.

---

# Required references

Inspect and align with:

- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
- docs/OPERATIONAL_AUTOMATION_ROADMAP.md
- docs/HANDOFF_A1_BLOCK1_COCKPIT_READ_ONLY_FOUNDATION.md
- docs/HANDOFF_A1_BLOCK2_COMMERCIAL_MARKETING_CONVERSION_QUEUES.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- app/services/admin_automation_cockpit_service.py
- app/schemas/admin_automation_cockpit.py
- app/api/routes/admin.py
- existing app/bot admin handlers
- app/bot/constants.py
- existing admin moderation / operator workflow button patterns
- tests/unit/test_admin_automation_cockpit.py
- existing Telegram admin/bot tests if present

If paths differ, inspect project structure and report.

---

# Admin-only entry

Use existing admin menu / admin bot handler pattern if present.

Add a visible admin button:

- `📊 Automation Cockpit`

If there is an existing admin/operator menu, add it there.

If no suitable menu exists, add the smallest safe admin-only command/callback entry consistent with project conventions.

Do not expose to ordinary customers.

Do not add public customer menu buttons.

---

# Screens / button flow

## 1. Cockpit summary screen

Admin clicks:

`📊 Automation Cockpit`

Show:

- title: Admin Automation Cockpit
- total cards
- urgent count
- needs attention count
- ready count
- blocked count
- future disabled count
- queue counts:
  - supplier_intake
  - missing_info
  - offer_readiness
  - risk_conflict
  - marketing_review
  - publishing_queue
  - catalog_conversion
- safety summary:
  - read_only
  - no Telegram publish/send
  - no scheduler
  - no supplier notification send
  - no QR
  - no Layer A mutation
  - no B11 change

Buttons:

- `📥 Supplier Intake`
- `⚠️ Missing Info`
- `✅ Offer Readiness`
- `🚨 Risk / Conflict`
- `🧩 Marketing Review`
- `📣 Publishing`
- `🔗 Catalog / Conversion`
- `🔄 Refresh`

Optional:
- `⬅️ Back`

---

## 2. Queue screen

When admin opens a queue, show:

- queue label
- queue description
- total count
- first 5 cards
- each card compactly:
  - title
  - source type / source id
  - status / tone
  - priority
  - next action label
  - action kind
  - action enabled
  - blocker / warning if present

Buttons:

- `Open #<source_id>` or `Open card`
- `🔄 Refresh`
- `⬅️ Back to Cockpit`

If pagination already has project conventions, implement small safe pagination.

If pagination is too large for this slice, show first 5 cards and document limitation.

---

## 3. Card detail screen

When admin opens a card, show:

- title
- source type / source id
- status
- status label
- status tone
- priority
- next best action code / label / kind / enabled
- blocker summary
- warning summary
- risk summary
- owner role
- source paths if available
- safety flags

If `commercial_context` exists, show:

- publish_status
- preview_status
- payload_status
- template_family
- selected_template_id
- tour_code
- already_published
- has_tour_bridge
- has_catalog_visible_tour
- has_active_execution_link
- fact_lock_note

Buttons:

- `⬅️ Back to Queue`
- `📊 Back to Cockpit`
- `🔄 Refresh`

No action button should execute mutation.

Future/disabled actions may be shown as text, not active callback.

---

# Callback naming

Use existing callback naming conventions.

If adding new callback prefixes, keep them short and documented.

Suggested examples only:

- `ac:home`
- `ac:q:<queue_code>`
- `ac:card:<queue_code>:<source_type>:<source_id>`
- `ac:refresh`

Adapt to existing callback prefix style.

---

# Rendering rules

Keep messages compact and admin-readable.

Avoid dumping raw JSON.

Translate technical fields into understandable labels where easy, but do not hide safety flags.

Do not use unsupported claims.

If values are missing, show `—` or omit safely.

Commercial queues must show fact-lock note or a short version:

“Supplier/catalog facts are read-only. Marketing review may change copy only, not price/route/inclusions/discounts/capacity.”

---

# Service usage

Prefer service-layer reuse:

- AdminAutomationCockpitService.read_cockpit()

Do not call internal HTTP from bot handler if service access is available.

Bot handlers must remain thin:
- load read model
- render text
- build keyboard
- answer callback

No business rules in bot handler.

---

# Security / admin access

Preserve existing admin-only access controls.

Use existing admin user check / admin Telegram id logic if present.

If current admin Telegram authorization is different from ADMIN_API_TOKEN route auth, follow existing Telegram admin conventions.

Tests should cover that the cockpit button/callback is not available to non-admins if current test infrastructure supports this.

---

# Safety boundaries

Absolutely do not:

- publish to Telegram channel
- call Bot API to channel except normal callback/message reply to admin chat
- schedule posts
- send supplier notifications
- create publish attempts
- execute prepare_conversion_chain
- call dry-run if it is not already part of this block
- mutate supplier offers
- mutate tours
- mutate bridges
- mutate execution links
- mutate orders/payments/reservations/seats
- change Mini App routes
- change B11 deep links
- implement AI agents
- call external providers
- create migrations

---

# Tests

Add/update focused tests.

If Telegram callback tests already exist, use project pattern.

If bot callback integration is hard to test, extract pure rendering helpers and test them.

Required coverage target:

1. Cockpit summary renderer includes queue counts and safety summary.
2. Queue renderer includes cards and next-best-action fields.
3. Card detail renderer includes commercial_context and fact-lock when present.
4. Future/disabled/public-side-effect actions are not rendered as enabled mutation buttons.
5. Callback data is generated safely for queue/card navigation.
6. Existing automation cockpit API tests still pass.
7. Existing publishing console tests still pass.

Run:

python -m compileall app tests

python -m pytest tests/unit/test_admin_automation_cockpit.py -q
python -m pytest tests/unit/test_admin_publishing_console.py -q

Run any relevant existing Telegram admin/bot tests if modified modules have tests.

If no Telegram admin tests exist, report and rely on renderer/unit tests plus manual UAT.

---

# Docs

Create:

docs/HANDOFF_A1V_VISIBLE_ADMIN_BUTTON_SURFACE_OVER_COCKPIT.md

Update minimally:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md

Document:

- admin button entry
- callback flow
- screens added
- read-only boundaries
- tests
- manual UAT path
- next recommended block

Do not rewrite large sections.

---

# Manual UAT path

Document and support this manual path:

1. Open admin bot/menu.
2. Click `📊 Automation Cockpit`.
3. See summary.
4. Open `🧩 Marketing Review`.
5. Open `📣 Publishing`.
6. Open `🔗 Catalog / Conversion`.
7. Open one card.
8. Confirm fact-lock appears.
9. Confirm safety flags appear.
10. Confirm no publish/send/schedule/supplier notification button exists.

---

# Before coding

Before editing files, report briefly:

1. Existing Telegram admin menu/handler structure found.
2. Where `📊 Automation Cockpit` entry will be added.
3. Which service method will be reused.
4. New callback prefixes.
5. Files to change.
6. Tests to add/update.
7. Explicit no-go list.

Then implement.

---

# After coding

Report:

1. Files changed.
2. Admin button / callback flow added.
3. Screens/renderers added.
4. How admin-only access is preserved.
5. How read-only/no-side-effect boundaries are preserved.
6. Tests run and results.
7. Manual UAT path.
8. Any deviations from planned scope.
9. Confirm:
   - no migrations
   - no write endpoints
   - no POST/PATCH/DELETE
   - no Telegram channel publish/send
   - no scheduler
   - no supplier notification send
   - no QR tokens
   - no Layer A mutation
   - no B11 changes
   - no AI execution
   - no external provider calls

Do not commit.
Do not push.
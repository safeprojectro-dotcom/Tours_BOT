
---

# HANDOFF

**HANDOFF file name:**  
`HANDOFF_A6B_CATALOG_CONVERSION_GUIDED_ACTIONS.md`

**HANDOFF content:**

```md
# HANDOFF_A6B_CATALOG_CONVERSION_GUIDED_ACTIONS

## Project

Tours_BOT

## Current checkpoint

A6A is complete and committed.

Latest known commit:
- `6a87691` — `feat: add catalog conversion readiness snapshot`

## What A6A did

A6A added read-only catalog/conversion readiness into Admin Automation Cockpit:

- Cockpit card read model now carries `catalog_conversion_readiness`
- Telegram card detail renders:
  - status
  - main blocker
  - warnings
  - tour/catalog/Mini App CTA safety
  - next step
- Queue list can show a short `Catalog / conversion` status line
- Copy is translated via `admin_a6a_*`
- Tests passed:
  - supplier offer readiness service
  - admin automation cockpit
  - Telegram cockpit formatter

## Why A6B is next

A6A tells the admin what is wrong, but does not yet guide the admin to the next safe action.

A6B should add Telegram guided action buttons/hints for the catalog/conversion blocker states.

## Safety principle

A6B is NOT an automatic conversion chain.

It must not:
- create/link tours directly
- activate catalog directly
- create execution links directly
- publish publicly
- notify suppliers
- mutate reservations/orders/payments
- bypass existing confirm/propose gates

A6B may:
- show safe action buttons
- route to existing guarded workflows
- route to safe detail screens
- show instructions when no guarded callback exists

## Target behavior

For `Catalog / conversie` readiness:

- Missing offer-tour bridge:
  - show a safe button/instruction to prepare/link offer-tour through the existing guarded workflow

- Tour exists but not catalog-active:
  - show safe button/instruction to prepare catalog activation through existing guarded/admin flow

- Missing execution link:
  - show safe button/instruction to prepare execution link through existing guarded flow if it exists; otherwise safe text instruction/detail route

- Ready:
  - show ready state and safe view/open buttons only
  - no mutation button needed

## Guardrails

- No migrations
- No Layer A changes
- No payment changes
- No booking/reservation changes
- No B11 routing changes
- No public Telegram publish/send
- No supplier notification send
- No raw backend tokens in user-facing text

## Expected verification

Run:

```bash
python -m compileall app tests
pytest tests/unit/test_supplier_offer_catalog_conversion_readiness_service.py tests/unit/test_admin_automation_cockpit.py tests/unit/test_automation_cockpit_telegram.py -q
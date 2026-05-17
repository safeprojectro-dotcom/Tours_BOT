
---

# HANDOFF

**HANDOFF file name:**  
`HANDOFF_A6C_OPERATOR_WORKFLOW_INTEGRATION_AND_ADMIN_TEXT_CLEANUP.md`

**HANDOFF content:**

```md
# HANDOFF_A6C_OPERATOR_WORKFLOW_INTEGRATION_AND_ADMIN_TEXT_CLEANUP

## Project

Tours_BOT

## Current checkpoint

A6A and A6B are complete.

Recent commits:
- `6a87691` — `feat: add catalog conversion readiness snapshot`
- `924426` — `feat: add guided catalog conversion actions`

## Why A6C exists

A6B successfully added a guided cockpit button from catalog/conversion readiness to the existing operator workflow screen.

Manual Telegram UAT showed that the destination screen works functionally, but is still not production-readable.

Observed raw/internal text:
- `awaiting_packaging_approval`
- `generate_packaging_draft`
- `full_bus_private_group`
- `GET .../review-package`
- `C2B11A`
- `Admin API`
- `JSON complet`
- mixed EN/RO copy

A6C must clean this up.

## Scope

A6C is a Telegram/admin UX cleanup and integration block.

It should:
- humanize operator workflow state
- humanize next-step labels
- humanize conversion status panel
- remove internal endpoint/phase-code text from Telegram
- clean up button labels
- preserve all guarded workflows

## Safety boundaries

A6C must NOT:
- create/link tours directly
- activate catalog directly
- create execution links directly
- publish publicly
- notify suppliers
- mutate orders/reservations/payments
- change Layer A
- change B11 routing
- add migrations

## Desired admin understanding

After clicking `Flux ofertă — pași ghidați`, the admin should understand:

1. What offer this is.
2. What state it is in.
3. What blocks catalog/conversion.
4. What the next safe internal step is.
5. Whether anything is sent externally.
6. Which buttons are safe to use.

## Verification

Run:

```bash
python -m compileall app tests
pytest tests/unit/test_operator_workflow_telegram_format.py tests/unit/test_supplier_offer_conversion_status_panel.py tests/unit/test_automation_cockpit_telegram.py -q
# CURSOR_PROMPT_A6C_OPERATOR_WORKFLOW_INTEGRATION_AND_ADMIN_TEXT_CLEANUP

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

## Block

A6C — Operator Workflow Integration & Admin Text Cleanup

## Mode

Functional block mode with strict safety boundaries.

## Current checkpoint

A6A and A6B are complete and committed.

Known recent commits:
- `6a87691` — `feat: add catalog conversion readiness snapshot`
- `924426` — `feat: add guided catalog conversion actions`

A6B added guided actions from Admin Automation Cockpit catalog/conversion readiness to the existing guarded operator workflow screen.

Manual UAT confirmed:
- The cockpit card shows `🧭 Catalog / conversie`.
- The guided button `Flux ofertă — pași ghidați` appears.
- The button routes to the existing operator workflow surface.
- However, that destination screen still leaks technical/internal strings and is not production-readable.

## Problem observed in Telegram UAT

After clicking `Flux ofertă — pași ghidați`, the operator workflow screen displays raw or semi-raw internal text such as:

- `awaiting_packaging_approval`
- `generate_packaging_draft`
- `full_bus_private_group`
- `GET .../review-package`
- `C2B11A`
- `Admin API`
- `JSON complet`
- mixed EN/RO wording
- internal endpoint-style explanations

This is not acceptable for a production admin/operator UI.

The admin should understand, in simple Romanian/English:

- what is the current state
- what blocks catalog/conversion
- what is the next safe step
- which buttons are safe
- that nothing is sent/published automatically

## Goal

Make the operator workflow destination screen readable and consistent with the A6A/A6B cockpit style.

A6C should clean/humanize the existing operator workflow screen and conversion status panel used after clicking the guided action button.

This is a UX/readability/integration block only.

## Hard safety boundaries

Do NOT:
- create a tour
- create an offer-tour bridge directly
- activate catalog directly
- create execution links directly
- publish to Telegram channel
- send supplier messages
- mutate orders/reservations/payments
- change Layer A
- change B11 routing
- add migrations
- add new public side effects
- bypass existing propose/confirm gates

A6C may:
- change Telegram text formatting
- change button labels
- add humanization helpers
- route/call existing read-only panels
- keep existing guarded propose/confirm callbacks
- add tests
- update docs minimally

## Target UX

When admin opens the operator workflow from cockpit guided action, the screen should be business-readable.

Example Romanian shape:

```text
Ofertă #10
Furnizor: NEXTRON
Rută: ...
Plecare: ...
Preț: ... | Locuri: ...

— Flux ofertă —
Stare: Necesită pregătire pachet
Următorul pas: Pregătește pachetul pentru verificare
Confirmare necesară: Da / Nu

Blocaj principal:
• Necesită verificare internă.

Atenționări:
• Câmpurile promo/reducere trebuie verificate.
• Calitatea textului trebuie verificată.

— Conversie catalog —
Showcase: Publicat
Legătură ofertă–tur: Lipsește
Catalog: Nu este listat pentru vânzare
Link rezervări: Lipsește
Client: Încă nu este self-service

Siguranță:
✅ Doar flux intern
✅ Nimic nu se trimite furnizorului automat
✅ Nu se modifică rezervări/plăți
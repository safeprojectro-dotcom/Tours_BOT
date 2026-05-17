# CURSOR_PROMPT_A6D_PRODUCTION_ADMIN_UX_FINAL_CLEANUP

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

## Block

A6D — Production Admin UX Final Cleanup for Catalog Conversion Flow

## Mode

Functional consolidation block, UX/readability only.

## Current checkpoint

A6A, A6B, A6C are complete and committed.

Recent commits:
- `6a87691` — `feat: add catalog conversion readiness snapshot`
- `924426` — `feat: add guided catalog conversion actions`
- `2befca9` — `fix: clean up operator workflow catalog conversion text`

Manual Telegram UAT after A6C shows the flow is functional, but still not fully production-readable.

## What is already good

The cockpit card now shows a readable catalog/conversion block:

- `🧭 Catalog / conversie`
- `Stare: Necesită pregătire`
- `Blocaj principal: Lipsește legătura ofertă–tur`
- `Catalog Mini App: Încă nu este listat`
- `Mini App CTA: Nu este încă sigur`
- `Următorul pas: Pregătește legătura ofertă–tur în admin`

The guided button works:

- `Flux ofertă — pași ghidați`

It routes into the existing guarded operator workflow.

## Remaining production UX issues from Telegram UAT

The destination/admin screens still show some raw or awkward text:

1. Raw template token:
   - `full_bus_private_group`

2. Mixed/awkward English/Romanian button labels:
   - `Preview`
   - `Execution link`

3. Technical/business wording that is still too console-like:
   - `Lifecycle`
   - `Șablon showcase (metadata ambalare)`
   - `Inferat: full_bus_private_group`
   - `previzualizare efectivă: full_bus_private_group`

4. Repeated generic lines:
   - multiple `Necesită verificare internă.` lines in the same block

5. The operator workflow block is still long and partially debug-like.

## Goal

Make the full A6 admin flow production-readable for a real Romanian-speaking admin/operator.

This is the flow:

`/admin_cockpit`
→ `Catalog / conversie`
→ supplier-offer card
→ `Flux ofertă — pași ghidați`
→ operator workflow / conversion status / related keyboard

The admin should understand:
- what is blocked
- what to do next
- which buttons are safe
- nothing is sent/published automatically

## Hard safety boundaries

Do NOT:
- add migrations
- create/link tours directly
- activate catalog directly
- create execution links directly
- publish to Telegram channel
- notify suppliers
- mutate orders/reservations/payments
- change Layer A
- change B11 routing
- bypass propose/confirm flows
- add new background jobs
- add AI/external calls

Allowed:
- Telegram text cleanup
- i18n key additions/changes
- humanization mapping
- dedupe/truncation of repeated lines
- button label cleanup
- focused tests
- minimal handoff doc update

## Required cleanup

### 1. Humanize showcase template tokens

No raw `full_bus_private_group` should appear in Telegram admin text.

Map template tokens such as:

- `full_bus_private_group`

to:

RO:
`Grup privat / autocar complet`

EN:
`Private group / full bus`

If other known template tokens exist, map them too if easy and safe.

Unknown template token fallback:
RO:
`Șablon intern`
EN:
`Internal template`

### 2. Replace awkward template section

Current bad shape:

```text
Șablon showcase (metadata ambalare)
Inferat: full_bus_private_group
— previzualizare efectivă:
full_bus_private_group
Ieșirea publicării pe canal rămâne...
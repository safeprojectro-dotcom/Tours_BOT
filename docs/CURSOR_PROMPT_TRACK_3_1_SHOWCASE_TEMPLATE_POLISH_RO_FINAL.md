Improve the supplier-offer Telegram showcase publication template for the Romania market.

Do not change booking logic, moderation logic, supplier lifecycle, auth rules, or Layer A core behavior.

## Context
Track 3 publication is already working:
- supplier offer can be approved
- admin can publish it into the Telegram showcase channel
- a post appears in the channel
- CTA links already exist
- the current system is stable and must not be broken

However, the current publication output is still too technical and not market-facing enough.

## Goal
Upgrade the supplier-offer showcase publication so that published Telegram channel posts look like customer-friendly Romanian marketing posts.

## Mandatory market rules
1. All customer-facing publication text must be in **Romanian**.
2. Date/time shown in the post must be formatted in **Romania local time** using `Europe/Bucharest`.
3. The template must support **one or more departure places / boarding places**.
4. Publication should be **photo-first** when media exists; otherwise safe text-only fallback.
5. The publication must avoid raw technical labels and raw enum values.
6. The publication must preserve existing routing:
   - `Detalii` -> bot
   - `Rezervă` -> Mini App

## CTA model to implement
The final customer-facing CTA line in the post should use:

**Detalii | Rezervă**

Do not add `Chat` or `Grup` as a third main CTA in this step.

Instead, add a soft subscribe line at the bottom in Romanian, for example:
- `Abonează-te la canal pentru rute noi și oferte viitoare.`
or equivalent wording in the same style.

## Publication style to implement
The post should follow this Romanian showcase structure:

### 1. Photo first
If a publishable image/media reference exists:
- publish photo + caption

If not:
- publish text-only fallback safely

### 2. Romanian marketing caption
The caption should follow this shape:

**[TITLE]**

[short Romanian marketing hook / 1-2 lines]

**Plecare:** [Romania-local datetime]  
**Întoarcere:** [Romania-local datetime]  
**Îmbarcare:** [one or multiple boarding places, if available]  
**Transport:** [vehicle or transport label, if available]  
**Locuri:** [seats total, if available]  
**Preț:** de la [price] [currency], if price exists

[optional Include / Nu include block, if source data supports it]

**Detalii | Rezervă**

[soft subscribe line]

## Romanian wording rules

### A. Avoid raw technical labels
Do not show customer-facing raw values like:
- `Sales mode full_bus`
- `payment_mode`
- enum names
- technical field names
- machine-style labels

### B. Romanian labels to use
Use Romanian-friendly labels such as:
- `Plecare`
- `Întoarcere`
- `Îmbarcare`
- `Transport`
- `Locuri`
- `Preț`
- `Include`
- `Nu include`

### C. Romanian commercial wording for group/full-bus style offers
If the offer is `full_bus`, do not show `full_bus` raw.
Use natural Romanian phrasing if needed, such as:
- `Potrivit pentru grupuri`
- `Ofertă pentru grup privat`
- `Rezervare pentru grup`

But keep the caption concise and not overloaded.

## Date/time formatting
Convert departure/return timestamps into `Europe/Bucharest` before rendering.

Expected style examples:
- `10 mai 2026, 11:00`
- `10 mai 2026, 21:00`

Do not display UTC in the customer-facing post.

## Departure places / multiple boarding places
Support one or more departure places.

If multiple places exist, render them in a compact Romanian-friendly style, for example:
- `Îmbarcare: Timișoara • Lugoj • Caransebeș`
or another compact readable separator.

Rules:
- do not invent boarding places
- only show them if source data actually provides them
- if no departure/boarding places exist, omit the block gracefully

## Include / Nu include
If source data makes this possible, add a short Romanian block:

Examples:
- `Include: transport`
- `Nu include: bilete de intrare și cheltuieli personale`

Rules:
- keep it short
- do not dump long lists
- omit the block if source data is missing or unreliable
- do not invent include/exclude values

## Scope
Touch only the minimum needed showcase rendering/publication layer, likely around:
- supplier offer showcase message builder
- media-aware publish selection
- Romania local datetime formatting helper
- Romanian customer-facing labels and wording
- optional boarding-place rendering if supplier-offer/source data supports it

## Constraints
Do NOT:
- change approval workflow
- change publish authorization rules
- change supplier/admin auth
- change booking/payment logic
- change Mini App routing
- change private bot routing
- redesign request marketplace
- redesign group assistant
- introduce AI content generation
- invent missing boarding places
- invent missing include/exclude data

## Backward compatibility
Must preserve:
- approved -> publish flow
- existing Telegram publish success path
- existing bot deep links
- existing Mini App links
- text-only fallback when no photo exists
- current Track 0 Layer A contracts

## Testing expectations
Add focused tests for:
- Romanian publication rendering
- `Europe/Bucharest` datetime formatting
- one departure place rendering
- multiple departure places rendering
- text fallback when no media exists
- photo publish path when media exists
- existing publish workflow still works
- `Detalii` and `Rezervă` links remain intact

## Before coding
First summarize:
1. exact files/modules you plan to change
2. whether supplier offers currently already have usable media data
3. whether supplier offers currently already have usable departure-place data
4. what fallback you will use if media or boarding places are missing
5. what remains explicitly out of scope

## After coding
Report:
1. files changed
2. whether migration was needed
3. tests run
4. results
5. what Romanian showcase format is now supported
6. remaining limitations
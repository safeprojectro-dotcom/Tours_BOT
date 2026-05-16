# HANDOFF_A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE

## Project
Tours_BOT

## Block
A1 — Admin Automation Cockpit & Controlled Operations Design Gate

## Mode
Functional-block mode.

## Why functional-block mode is allowed
A1 is documentation/design only.
It does not touch runtime code, schema, endpoints, workers, public sends, payment/booking/order logic, QR security, supplier notifications, or personal-data manifests.

## Purpose
Design the Admin Automation Cockpit that will allow the platform to scale to many suppliers, offers, routes, guides, discounts, coupons, customer questions, private bus requests, marketing flows, departure operations, and supplier notifications without turning admin work into manual chaos.

## Main principle
Normal flow → automated  
Risky flow → admin confirmation  
Exceptional flow → operator/admin  
Public action → gated  
Facts → supplier/catalog truth  
Marketing → AI draft + admin copy review  
Booking/payment → Layer A only

## Required document
Create:

`docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md`

Update:

`docs/CHAT_HANDOFF.md`  
`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Optionally update:

`docs/OPERATIONAL_AUTOMATION_ROADMAP.md`

## Must define
- cockpit queues
- queue card model
- action taxonomy
- next-best-action model
- fact-lock
- AI1 / AI2 / AI3 boundaries
- supplier clarification automation design
- marketing review workflow
- catalog / conversion workflow
- departure operations workflow
- customer questions / handoff workflow
- custom bus / RFQ workflow
- implementation roadmap after A1
- manual UAT vision
- non-goals and safety boundaries

## Must not happen
- code changes
- migrations
- endpoints
- Telegram publish
- scheduler
- broadcast
- supplier notification send
- passenger manifest export
- QR tokens
- AI agent implementation
- Layer A changes
- B11 changes
- external provider calls

## Expected result
A1 becomes the authoritative design gate for the future admin cockpit and controlled operations console.

Future implementation must start from read-only projections and only move to guarded actions after separate design gates.
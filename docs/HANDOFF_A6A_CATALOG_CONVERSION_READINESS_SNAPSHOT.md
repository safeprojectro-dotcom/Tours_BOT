# HANDOFF — A6A Catalog / Conversion Readiness Snapshot

## Purpose

A6A adds a read-only catalog/conversion readiness projection to admin automation cockpit cards.

It helps the admin understand whether a supplier offer is ready for internal catalog/conversion preparation, without executing any conversion.

## Scope

Read-only projection only.

Expected output in Telegram card detail:

- catalog/conversion status
- main blocker
- Mini App CTA safety
- tour/link/execution-link availability if known
- next safe internal step

## Non-goals

A6A must not:

- create SupplierOfferTourBridge
- create Tour
- activate Tour for catalog
- create execution link
- publish to Telegram channel
- send supplier notification
- modify B11 routing
- mutate Layer A booking/payment/order/reservation
- introduce QR/token logic
- add scheduler/job
- call AI/external providers

## UX principle

Admin text must be short, human, Romanian-first, and understandable by non-technical admins.

No raw debug keys in Telegram:
- no prepare_chain:...
- no cta_safety:...
- no snake_case diagnostics
- no JSON/path dumps

Unknown technical data should become:
- RO: “Necesită verificare internă.”
- EN: “Requires internal verification.”

## Expected verification

- `/admin_cockpit`
- open supplier-offer card
- verify new Catalog / conversie block
- verify no mutation buttons are introduced
- verify safety remains read-only
- run unit tests

## Status

Pending Cursor implementation report.
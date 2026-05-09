# HANDOFF_ADMIN_OPERATOR_WORKFLOW_TELEGRAM_BUTTON_UX_POLICY

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — Telegram Button UX Policy

## Purpose

Before adding more Telegram admin workflow actions, define human-friendly button labels and ordering.

## Product principle

Admin Telegram card is not a developer console.

Buttons must be:

- sequential
- 1–2 words
- human-readable
- action-oriented
- safe for admins with mixed experience

## Current issue

Technical labels are correct but too verbose / technical:

- Reîncarcă review-package
- Previzualizare showcase
- Generează packaging
- Aprobă packaging

Also legacy `Aprobă` becomes ambiguous once `Aprobă text` exists.

## Policy to define

- mapping action_code → RO/EN button label
- button order
- stage-based visibility
- confirmation tiers
- dangerous/public action separation
- legacy Aprobă / Respinge handling
- future implementation slice

## Hard boundaries

Do not implement publish / bridge / activate / execution-link buttons in this policy step.

Do not change booking/payment/Mini App.

Do not start implementation automatically.
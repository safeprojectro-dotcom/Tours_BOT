# Telegram Setup

## Project
Tours_BOT

## Purpose
Document Telegram-specific setup, assumptions, configuration, and operational rules for the Tours_BOT project.

This document covers:
- BotFather setup
- bot commands
- menu button / Mini App entry
- webhook assumptions
- group behavior
- private chat behavior
- deep links
- environment-related Telegram settings

---

## 1. Telegram Delivery Model

The project uses one main customer bot.

The same bot is responsible for:
- Telegram group warm-up behavior
- private chat sales flow
- Mini App launch
- payment-related guidance
- booking status messaging
- handoff initiation

Telegram usage is split into:
- group chat = engagement, short answers, CTA, routing to private
- private chat = guided sales flow and booking support
- Mini App = structured catalog, booking, payment, booking status

---

## 2. BotFather Setup

## Required BotFather actions
Create and maintain one main bot for Tours_BOT.

Record and maintain:
- bot username
- bot token
- display name
- description
- about text
- command list
- menu button behavior
- Mini App launch button if used
- bot privacy mode decision
- bot group permissions assumptions

## To document after real setup
- bot username
- production bot link
- staging bot link if applicable
- configured commands
- configured menu button
- webhook mode confirmation
- Mini App URL binding

---

## 3. Commands

Initial command set should stay minimal and useful.

Recommended MVP commands:
- /start
- /tours
- /bookings
- /language
- /help
- /contact

Command design principles:
- short
- multilingual-capable
- aligned with private booking flow
- no operational/debug commands exposed to customers

---

## 4. Menu Button / Mini App Entry

The menu button should support one of these strategies:
1. open Mini App directly
2. open main bot action flow
3. open a booking/catalog entry point

Recommended MVP approach:
- menu button opens Mini App or a simple main entry point that clearly leads to Mini App

Mini App entry must support:
- opening from private chat
- opening from CTA messages
- return path back to chat support
- booking continuity where possible

---

## 5. Webhook Strategy

## Environments
Telegram delivery must support:
- local development assumptions
- staging webhook
- production webhook

## Rules
- production and staging should use webhook mode
- local environment may use controlled development assumptions
- webhook URL must be environment-specific
- webhook secret/validation must be separated from bot token
- webhook configuration must be documented per environment

## Required webhook checks
- endpoint reachable
- correct Telegram secret validation if used
- updates are received
- private chat flow works
- group flow works
- Mini App-related callbacks/flows work if applicable

---

## 6. Group Behavior Setup

## Purpose of group mode
The bot in group is not a full booking processor.
It is a warm-up and routing assistant.

**Normative rule detail (Phase 7):** operational constraints for triggers, forbidden group behavior, CTAs, anti-spam, handoff categories, and operator continuity are centralized in **[docs/GROUP_ASSISTANT_RULES.md](GROUP_ASSISTANT_RULES.md)**. This section stays high-level; implementers align both documents.

## Allowed behavior
- answer when mentioned
- answer to approved trigger phrases
- answer to approved commands
- provide short factual answers
- route users to private chat or Mini App
- create handoff when required

## Not allowed
- collecting personal data publicly
- long personal negotiations in group
- asking for phone number publicly
- asking for documents publicly
- discussing payment-sensitive details publicly
- replying to every message

## Operational group setup assumptions
Must define:
- whether privacy mode is enabled or disabled
- what permissions the bot has
- whether mention-only mode is used
- how trigger phrases are handled
- anti-spam boundaries

---

## 7. Private Chat Behavior

Private chat is the main guided booking surface.

Private chat should support:
- language selection / detection
- tour search
- tour recommendation
- reservation initiation
- payment guidance
- waitlist fallback
- handoff to operator
- Mini App transition

---

## 8. Deep Links

Deep links should be planned for:
- generic private start
- specific tour entry
- campaign entry
- group-to-private CTA
- Mini App handoff

Deep links must preserve, where possible:
- source channel
- campaign/source tag
- relevant tour context
- language hints if appropriate

Deep links must be tested for:
- routing correctness
- CTA continuity
- language behavior
- reservation continuity assumptions

---

## 9. Multilingual Telegram Behavior

Telegram delivery must support multilingual behavior.

At minimum:
- detect user language when possible
- allow explicit language choice
- persist preferred language
- use fallback language rules when needed

Telegram messages must avoid confusing language mixing.

---

## 10. Telegram Handoff Rules

The bot must escalate to human support when:
- user requests a human
- user requests discount
- user wants custom pickup
- user wants custom route
- payment issue is unclear
- complaint/escalation occurs
- group booking exceeds threshold
- assistant confidence is low

Telegram handoff must preserve:
- source chat context
- language
- relevant user intent
- relevant booking state if any

---

## 11. Telegram Test Checklist

## Local manual checks
- /start works
- commands visible and sensible
- language selection works
- private chat can guide toward tour selection
- CTA to Mini App works
- group mention behavior works
- group trigger behavior works
- anti-spam behavior works
- handoff routing works

## Staging checks
- webhook receives updates
- private chat delivery works
- group flow works
- deep links work
- Mini App launch works
- operator handoff persists correctly

## Production release checks
- correct bot token in production
- correct webhook URL in production
- commands set correctly
- menu button correct
- Mini App URL correct
- no staging secrets leaked
- rollback steps known

---

## 12. Operational Notes

This file should be updated whenever:
- bot token strategy changes
- commands change
- menu button behavior changes
- webhook setup changes
- group permissions change
- Mini App entry changes

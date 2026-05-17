# CURSOR_PROMPT_A3E_CAP_INTERNAL_TASKS_TO_5_CORRECTION

You are continuing the existing Tours_BOT project.

This is a correction to A3E, not a new feature.

Current A3E report says Telegram internal tasks are capped at 8 bullets, but the required behavior was max 5 visible internal tasks.

## Goal

Fix A3E so Telegram admin-facing card detail shows at most 5 internal tasks.

## Required behavior

In Telegram cockpit card detail:

- `Sarcini interne` must show max 5 unique human-readable items.
- If more than 5 internal tasks exist, append:
  - RO: `• Mai există sarcini interne suplimentare.`
  - EN: `• Additional internal tasks exist.`
- Do not show 6, 7, 8, or more normal task bullets.
- Keep deduplication after humanization.
- Do not reintroduce raw technical/debug text.
- Do not change supplier-facing draft logic.
- Do not change business/service behavior unless strictly needed for rendering.

## Preferred files

Likely only:

- app/bot/automation_cockpit_telegram.py
- app/bot/messages.py if overflow string is missing
- tests/unit/test_automation_cockpit_telegram.py

Do not touch unrelated modules unless necessary.

## Safety boundaries

Do NOT:
- add migrations
- add write endpoints
- mutate DB models/data
- publish/send Telegram messages
- send supplier notifications
- schedule anything
- call AI
- call external providers
- change Layer A
- change B11

## Tests

Update/add tests:

1. internal tasks are capped at 5 visible task bullets.
2. overflow note appears when more than 5 tasks exist.
3. no raw debug keys appear.
4. supplier-facing draft remains unchanged.

Run:

```bash
python -m compileall app tests
python -m pytest tests/unit/test_automation_cockpit_telegram.py -q
python -m pytest tests/unit/test_supplier_clarification_draft_service.py -q
python -m pytest tests/unit/test_operator_workflow_telegram_format.py -q
python -m pytest tests/unit/test_supplier_offer_conversion_status_panel.py -q
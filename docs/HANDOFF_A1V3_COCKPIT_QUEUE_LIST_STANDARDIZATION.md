# Handoff: A1V3 — Cockpit Queue List Standardization

## Summary

All Telegram **queue list** screens use one **compact card template** (same for every `queue_code`):

1. `{n}) {title}` (title trimmed ~72 chars)
2. `{Offer|Tour #id} · {emoji + short status}` — status from `metadata.console_status` / `card.status` with translated **Blocked / Needs attention / Ready / In queue** (not English `status_label` blobs).
3. **`Next step:` / `Următorul pas:`** — mapped from `next_best_action_code` to **`admin_automation_cockpit_action_*`** strings; **Romanian** uses a **generic “see card”** line when the code is unmapped (avoids raw English labels in RO).
4. **Optional one issue line**: `⛔` blocker snippet (≤100 chars) or `⚠️` warning if no blocker.

No changes to API, services, classification, or DB.

## Files

- `app/bot/automation_cockpit_telegram.py` — `_format_queue_list_card`, `_list_next_step_line`, `_list_console_status_message_key`, `_snippet`, action code → i18n map.
- `app/bot/messages.py` — queue card lines, list status phrases, action label keys (`en`, `ro`).
- `tests/unit/test_automation_cockpit_telegram.py`
- This handoff; **`docs/CHAT_HANDOFF.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** (checkpoint line).

## Tests

```text
python -m pytest tests/unit/test_automation_cockpit_telegram.py tests/unit/test_admin_automation_cockpit.py tests/unit/test_admin_publishing_console.py -q
```

## Follow-ups (optional)

- Expand `\_COCKPIT_LIST_ACTION_KEYS` when new `next_best_action_code` values appear.
- Localize long blocker/warning **snippets** (currently truncated raw backend text).

## Next

**A1-Block 3** or Telegram pagination for >5 cards per lane.

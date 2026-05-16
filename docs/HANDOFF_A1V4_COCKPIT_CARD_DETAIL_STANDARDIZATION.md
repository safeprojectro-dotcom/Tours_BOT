# Handoff: A1V4 — Cockpit Card Detail Standardization

## Summary

All Telegram **card detail** screens (`format_cockpit_card_detail_text`) use one **business-readable** layout:

1. **📄** header + **title** + same **L2** line as queue list (`source · localized status`).
2. **`Suggested next step:` / `Pas sugerat:`** — same **`next_best_action_code → admin_automation_cockpit_action_*`** mapping as A1V3 list cards.
3. Optional **blocker / note / risk** sections with emoji-prefixed bodies (truncated notes; **RO** substring substitution for frequent English risk phrases).
4. Optional **owner** line (hidden when `owner_role` is `admin_operator`).
5. **`Sources:` / `Surse:`** — human labels for known **`source_paths`** keys (tour admin, admin action, review package, console, conversion plan, preview) with **available / not linked** — **no** raw path dict keys in the message text.
6. **`Commercial context`** + **`🔒 Fact lock`** when `commercial_context` is present; boolean flags use **Yes/No** / **Da/Nu** via **`cc_bool_*`**.
7. **`🛡 Safety:`** — fixed human lines (no `read_only=True` dump).

No changes to API, services, classification, or DB.

## Files

- `app/bot/automation_cockpit_telegram.py` — detail formatter, source bullets, human safety, RO risk substitutions, commercial booleans.
- `app/bot/messages.py` — **`en` / `ro`** keys for detail sections, source labels, safety lines, risk RO catalogue, `cc_bool_*`.
- `tests/unit/test_automation_cockpit_telegram.py`
- This handoff; **`docs/CHAT_HANDOFF.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** (checkpoint line).

## Tests

```text
python -m compileall app tests
python -m pytest tests/unit/test_automation_cockpit_telegram.py -q
```

## Follow-ups (optional)

- Extend **`_SOURCE_PATH_ORDER`** / **`_SOURCE_PATH_LABEL_KEY`** when backend adds new path keys.
- Expand **`_risk_note_ro_substitutions`** or move long blocker text into i18n if operators need full Romanian for every lane.

## Next

**A1-Block 3** or Telegram pagination for >5 cards per lane.

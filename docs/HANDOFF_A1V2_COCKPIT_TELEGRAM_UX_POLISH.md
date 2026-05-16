# Handoff: A1V2 — Cockpit Telegram UX Polish

## Summary

Read-only polish on the A1V Telegram cockpit: **demo-ready labels**, no raw queue codes on the **summary** and **queue list**, compact **safe mode** + **fact-lock** one-liners on the home screen, full **safety flags** behind **🛡 Detalii siguranță / Safety details** (`ac:s`), shorter card rows (no `safe_read` / `kind=` / priority noise), **Deschide ofertă #…** / **Open offer #…** and tour variants on open buttons.

## Callback added

| Callback | Meaning |
|----------|---------|
| `ac:s` | Snapshot safety detail (all `read.safety_summary` flags). Back → `ac:h`. |

## Files touched

- `app/bot/automation_cockpit_telegram.py`
- `app/bot/handlers/automation_cockpit_admin.py`
- `app/bot/constants.py` — `ADMIN_AUTOMATION_COCKPIT_SAFETY_DETAIL`
- `app/bot/messages.py` — `admin_automation_cockpit_*` additions/rewrites (`en`, `ro`)
- `tests/unit/test_automation_cockpit_telegram.py`
- `docs/HANDOFF_A1V_VISIBLE_ADMIN_BUTTON_SURFACE_OVER_COCKPIT.md` (callback table + UAT tweak)

## Tests

```text
python -m compileall app tests
python -m pytest tests/unit/test_admin_automation_cockpit.py tests/unit/test_admin_publishing_console.py tests/unit/test_automation_cockpit_telegram.py -q
```

## Boundaries

Unchanged: no migrations, writes, channel publish, scheduler, supplier sends, QR, Layer A, B11, AI, external calls.

## Next

**A1V3** — **[`docs/HANDOFF_A1V3_COCKPIT_QUEUE_LIST_STANDARDIZATION.md`](HANDOFF_A1V3_COCKPIT_QUEUE_LIST_STANDARDIZATION.md)** (standardized queue list cards).

Then **A1-Block 3** or Telegram queue pagination if five cards per lane is too tight in production demos.

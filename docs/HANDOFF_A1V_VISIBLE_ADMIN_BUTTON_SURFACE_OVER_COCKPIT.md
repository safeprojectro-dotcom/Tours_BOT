# Handoff: A1V — Visible Admin Button Surface over Cockpit

## Summary

Adds an **admin-only, read-only** Telegram surface over the existing **`AdminAutomationCockpitService.read_cockpit`** snapshot: summary → per-queue (first 5 cards) → card detail (including **`commercial_context`** + fact-lock note where present).

## Entry points

- **Command:** `/admin_cockpit` (allowlisted Telegram admins only).
- **Inline button:** **📊 Automation Cockpit** on the supplier-offer admin detail keyboard (`/admin_ops` flow), next to Orders / Requests.

## Callback prefixes (`ac:`)

| Callback | Meaning |
|----------|---------|
| `ac:h` | Cockpit home (summary). |
| `ac:r` | Refresh summary. |
| `ac:rq:<q>` | Refresh current queue (`si` … `cc` abbrev). |
| `ac:q:<q>` | Open queue. |
| `ac:c:<q>:<st>:<id>` | Open / refresh card (`so` = supplier_offer, `tu` = tour). |
| `ac:x` | Close (delete message if possible). |

## Files

- `app/bot/automation_cockpit_telegram.py` — text + inline keyboards.
- `app/bot/handlers/automation_cockpit_admin.py` — commands + callbacks; uses `materialize_cards=False` for summary; scoped `include_queues` + card limit for queue/card views.
- `app/bot/constants.py` — `ac:*` constants.
- `app/bot/messages.py` — `admin_automation_cockpit_*` keys (`en`, `ro`).
- `app/bot/handlers/admin_moderation.py` — menu button wiring.
- `app/bot/app.py` — router registration.
- `tests/unit/test_automation_cockpit_telegram.py` — renderer + callback safety tests.

## Safety / boundaries (unchanged from A1)

No DB migrations, no new write HTTP routes, no POST/PATCH/DELETE from this block, no Telegram **channel** publish/send, no scheduler, no supplier notification send, no QR, no Layer A mutation, no B11 changes, no AI execution, no external provider calls. Handlers only **read** the cockpit service and **edit/reply** in the admin private chat.

## Tests

```text
python -m compileall app tests
python -m pytest tests/unit/test_admin_automation_cockpit.py -q
python -m pytest tests/unit/test_admin_publishing_console.py -q
python -m pytest tests/unit/test_automation_cockpit_telegram.py -q
```

## Manual UAT

1. Open admin bot; run `/admin_ops` (or open an offer card).
2. Tap **📊 Automation Cockpit** (or `/admin_cockpit`).
3. Confirm summary: queue counts + safety flags + short fact-lock line.
4. Open **🧩 Marketing Review**, **📣 Publishing**, **🔗 Catalog / Conversion**; confirm first cards list.
5. Open one card; confirm commercial context + fact-lock + per-card safety flags.
6. Confirm there is no publish / schedule / supplier-send / prepare-chain action button.

## Limitations

- Queue view shows **up to 5** cards per open (same as service `limit_per_queue` for that view). No pagination in this slice.
- Summary mode uses **`materialize_cards=False`** for performance; **`future_disabled_count`** on the summary may stay **0** until a later optimization counts disabled actions without full card materialization.

## Next recommended block

**A1-Block 3** — operations / handoff / RFQ-style queues (per A1 design gate §17), or dedicated cockpit pagination if Telegram operators need deeper queues before that.

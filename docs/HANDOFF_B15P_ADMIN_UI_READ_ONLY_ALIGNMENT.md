# HANDOFF_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT

## Project

Tours_BOT

## Block

**B15P** — Admin UI polish / read-only frontend alignment (**closed** in-repo)

## What shipped

Additive **read-only** admin presentation metadata on existing Publishing Console **GET** responses (no new routes, no mutations, no migrations).

- **`GET /admin/publishing-console`** — each list item includes **`ui_card`**:
  - `card_title`, `card_subtitle`
  - `status_badge`, `status_label`, `status_tone`
  - `primary_line`, `secondary_line`
  - `primary_action_label`, `primary_action_code`, `primary_action_enabled`, `primary_action_kind`, `primary_action_path`
  - `secondary_action_label`, `secondary_action_code`, `secondary_action_enabled`
  - `warning_line`, `blocker_line`, `safety_line`
- **`GET /admin/publishing-console/supplier-offers/{offer_id}`** — detail includes ordered **`ui_sections`** (section keys + titles for a future admin layout).

**Semantics:** **`primary_action_kind`** values include **`safe_read`**, **`guarded_post`**, **`future`**, **`none`**. Ready supplier-offer rows may expose **`primary_action_kind=guarded_post`** with **`prepare_conversion_chain`** — that flags **internal guarded preparation** (separate **POST** path), **not** Telegram showcase publish.

## Tests / contract

- **`tests/unit/test_admin_publishing_console.py`** — backward-compatible per-item keys include **`ui_card`**; smoke/detail tests cover **`ui_card`** / **`ui_sections`** shape (**11 passed** at last docs update).

## Explicit non-goals (unchanged)

- **No** admin web frontend implementation in this gate.
- **No** Telegram I/O, publish attempts, scheduler, or auto-publish.
- **No** **`prepare_conversion_chain`** execution from **GET** list or detail.
- **No** Layer A mutation; **no** Mini App / **B11** routing changes.
- **No** database migration for B15P.

## Prerequisites (closed)

Foundation slices through **B15M** and docs closure **B15O**; see [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md).

## Suggested next

- Optional: short read-only smoke on deployed admin for **`ui_card`** / **`ui_sections`** JSON.
- Product follow-ups: **B17** channel/template editor design gate and/or frontend planning — **not** auto-publish without separate go/no-go (**B15G** remains design-only).

## Related

- Prompt: [`docs/CURSOR_PROMPT_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md`](CURSOR_PROMPT_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md)
- Continuity: [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (**B15P** bullet)

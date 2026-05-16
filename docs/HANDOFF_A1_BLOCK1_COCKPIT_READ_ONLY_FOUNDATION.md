# HANDOFF_A1_BLOCK1_COCKPIT_READ_ONLY_FOUNDATION

## Project

Tours_BOT

## Block

**A1-Block 1 — Cockpit Read-Only Foundation**

## Endpoint

- **`GET /admin/automation-cockpit`**
- **Auth:** same as other admin routes (`ADMIN_API_TOKEN` via `Authorization: Bearer …` or `X-Admin-Token`).
- **Query:**
  - `limit` (default 20, max 100): max **cards per queue** returned.
  - `include_queues` (optional): comma-separated subset of `supplier_intake`, `missing_info`, `offer_readiness`, `risk_conflict`. When set, only those queues include **cards**; **counts** still reflect the full publishing-console snapshot; unknown tokens → **422**.

## Queues (read-only projections)

All rows are sourced from **`AdminPublishingConsoleService.read_console`** (no duplicated publish-readiness or conversion rules).

| `queue_code`      | Role |
|-------------------|------|
| `supplier_intake` | Early lifecycle / packaging not yet in steady operational flow. |
| `missing_info`    | Blockers, clarification/rejected packaging, rejected lifecycle, blocked readiness. |
| `offer_readiness` | Ready / suggest-publish posture when signals align. |
| `risk_conflict`   | `needs_review`, ambiguous or attention states, published rows with follow-up risk signals, contradictions. |

## Read-model assembly

- **Service:** `app/services/admin_automation_cockpit_service.py` — `AdminAutomationCockpitService.read_cockpit`
- **Schemas:** `app/schemas/admin_automation_cockpit.py`
- **Route:** `app/api/routes/admin.py` — thin handler on existing `/admin` router.

## Safety / boundaries

Response **`safety_summary`** and per-card **`safety_flags`** document:

- `read_only`, `no_telegram_io`, `no_publish_attempt`, `no_scheduler`, `no_auto_publish`, `no_supplier_notification_send`, `no_qr_token`, `no_layer_a_mutation`, `no_b11_change` (all **true** on this GET).

**Next-best-action (Block 1):** card `next_best_action_kind` is only **`safe_read`** or **`future_disabled`**; **`future_disabled`** is never enabled. No **`public_side_effect`**.

**Not done (by design):** migrations, POST/PATCH/DELETE, Telegram, scheduler, supplier/customer sends, `prepare_conversion_chain` execution, inventory/order/payment mutation, AI tools, external providers.

**Snapshot limits:** `summary` / `queue` **counts** match items returned by `read_console` up to an internal fetch cap (see response `query.publishing_console_limit`). Not a full-table scan.

## Tests

- `tests/unit/test_admin_automation_cockpit.py`
- Regression suite (prompt): publishing console, publish readiness, review package, prepare-chain affordances — **45 passed** in the focused run after implementation.

## Next recommended block

**A1-Block 2 — Commercial / Marketing / Conversion Queues** (see `docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md` §17).

## Related

- `docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md`
- `docs/OPERATIONAL_AUTOMATION_ROADMAP.md`
- `docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md`
- `docs/CHAT_HANDOFF.md`

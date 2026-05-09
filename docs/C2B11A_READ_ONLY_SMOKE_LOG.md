# C2B11A — Read-only smoke log (Admin/OPS Conversion Status Panel)

**Project:** Tours_BOT. **Type:** documentation / operator log template — **no** code or config changes.

**Slice:** **C2B11A** — **`conversion_status_panel`** on **`GET /admin/supplier-offers/{offer_id}/review-package`**, plus compact mirror on Telegram admin offer detail.

**Related:** [`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`](CONVERSION_CHAIN_OPS_SMOKE_READINESS.md) · [`docs/HANDOFF_ADMIN_OPS_CONVERSION_STATUS_PANEL_C2B11A_TO_NEXT_STEP.md`](HANDOFF_ADMIN_OPS_CONVERSION_STATUS_PANEL_C2B11A_TO_NEXT_STEP.md) · [`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`](ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md) · [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (Slice C2B11A).

---

## Purpose

Record a **single** read-only verification that production (or staging) returns **`conversion_status_panel`** with five layers and that **`operator_workflow.actions`** still aligns with expectations for the same **`OFFER_ID`**. **No POSTs**, **no** Telegram mutations, **no** Mini App or booking checks required for this log.

---

## Preconditions

| Item | Notes |
|------|--------|
| **`$BASE`** | API origin only (e.g. `https://api.example.com`) — admin routes use prefix **`/admin`**. |
| **`ADMIN_API_TOKEN`** | Same secret the API expects; admin disabled → **503**. |
| **`OFFER_ID`** | Integer supplier offer id known in target env. |
| Auth | **`Authorization: Bearer <token>`** and/or **`X-Admin-Token`** per [`app/api/admin_auth.py`](../app/api/admin_auth.py). |

Redact tokens and internal hostnames if this file is committed with real runs; prefer pasting **sanitized** JSON excerpts into the run log below.

---

## Read-only PowerShell check (copy/paste)

```powershell
$BASE = "https://<your-api-host>"
$token = "<ADMIN_API_TOKEN>"

$Headers = @{
  "Authorization" = "Bearer $token"
  # Alternative: "X-Admin-Token" = $token
}

$OFFER_ID = <OFFER_ID>

$r = Invoke-RestMethod -Uri "$BASE/admin/supplier-offers/$OFFER_ID/review-package" -Headers $Headers -Method GET

# C2B11A — five-layer panel (showcase, tour_bridge, catalog, booking_link, customer_action)
$r.conversion_status_panel | ConvertTo-Json -Depth 5

# Sanity: operator gates for same snapshot
 $r.operator_workflow.actions | Format-Table code, enabled, danger_level, requires_confirmation, disabled_reason -AutoSize
```

**Optional same session:**

```powershell
$r.conversion_closure | Format-List
$r.linked_tour_catalog | Format-List
```

---

## What “good” looks like (quick)

- **`conversion_status_panel`** is present and has keys: **`showcase`**, **`tour_bridge`**, **`catalog`**, **`booking_link`**, **`customer_action`**.
- Each layer includes **`status`**, **`summary`**; **`detail`** may be **`null`** or a short string.
- **Statuses** are plain vocabulary (e.g. `published` / `not_published` / `blocked` for showcase; `stale` on booking link only when link **tour_id** ≠ bridge **tour_id**, etc.) — see implementation summary in [`HANDOFF_ADMIN_OPS_CONVERSION_STATUS_PANEL_C2B11A_TO_NEXT_STEP.md`](HANDOFF_ADMIN_OPS_CONVERSION_STATUS_PANEL_C2B11A_TO_NEXT_STEP.md).
- **`operator_workflow.actions`** rows match known **`code`** values (`create_tour_bridge`, `activate_tour_for_catalog`, `publish_showcase_channel`, `create_execution_link`, …); **`enabled` / `disabled_reason`** should be consistent with the panel narrative (panel does not replace **`operator_workflow`** — it summarizes layers for ops).

---

## Run log (template)

| Field | Value |
|--------|--------|
| **Environment** | e.g. staging / production |
| **Date (UTC)** | YYYY-MM-DD |
| **Operator** | name or ticket id |
| **`OFFER_ID`** | integer (redact if needed for public export) |
| **HTTP status** | expect **200** |
| **Panel present** | yes / no |
| **Notes** | e.g. “showcase blocked + detail matches cover gate”; “booking_link stale after manual tour relink” |

**Paste (redacted) `conversion_status_panel` JSON** — optional:

```json
{
  "showcase": { "status": "…", "summary": "…", "detail": null },
  "tour_bridge": { "…": "…" },
  "catalog": { "…": "…" },
  "booking_link": { "…": "…" },
  "customer_action": { "…": "…" }
}
```

---

## Non-goals (this smoke)

- **No** POST / publish / bridge / catalog / execution-link mutations.
- **No** migration or schema changes.
- **No** Mini App or B11 routing validation (beyond what **`customer_action`** text implies).
- **No** booking, payment, or order assertions.

---

## Prompt reference

[`docs/CURSOR_PROMPT_C2B11A_READ_ONLY_SMOKE_LOG.md`](CURSOR_PROMPT_C2B11A_READ_ONLY_SMOKE_LOG.md)

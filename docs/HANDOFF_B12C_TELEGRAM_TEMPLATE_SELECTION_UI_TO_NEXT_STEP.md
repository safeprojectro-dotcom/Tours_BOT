

---

## HANDOFF name

`HANDOFF_B12C_TELEGRAM_TEMPLATE_SELECTION_UI_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B12C_TELEGRAM_TEMPLATE_SELECTION_UI_TO_NEXT_STEP

## Status

**B12C implemented.** Telegram admin offer detail adds **Template** / **Șablon** when **`operator_workflow.patch_showcase_marketing_template`** is enabled; picker lists **`showcase_template_preview.template_choices`** (one-tap select only when **`requires_verified_live_seats`** is false); **last seats** via prompt + **positive integer** reply; **clear** + back to offer card; all mutations call **`SupplierOfferPackagingReviewService.patch_showcase_marketing_template`** (same as HTTP PATCH, approved-packaging lock, **`flag_modified`**). **Publish output** and **publish readiness** unchanged; lifecycle / **media_review** unchanged except **selected template metadata** in packaging JSON.

## Project

Tours_BOT — Supplier Offer showcase marketing templates.

## Step

B12C — Telegram admin template selection UI.

## Checkpoint (before this step)

- **B12A:** Template library + **`showcase_marketing_template_library_v1`** on packaging generate; deterministic inference; no fake last seats from row alone.
- **B12B:** **`GET …/review-package`** **`showcase_template_preview`**; **`PATCH …/packaging/showcase-template`**; **`operator_workflow`** **`patch_showcase_marketing_template`**; Telegram **read-only** B12B summary when preview exists.

## Preconditions (for B12C)

- **B12A** + **B12B** as above; review-package supplies **`template_choices`** and **`notes`**.

## Goal (achieved)

- **Template** / **Șablon** after **Approve text** / **Aprobă text**, **before** bridge/publish workflow actions.
- Picker shows inferred / effective / selected, intro, optional **`notes`**, blocked summary for last-seats-in-one-tap.
- Selectable inline buttons = choices with **`requires_verified_live_seats == false`**; apply path re-reads review-package and checks **`_template_id_allowed_for_telegram_direct_apply`** before **`patch_showcase_marketing_template`**.
- **Last seats:** callback **`ao:ow:tmls:`** → FSM **`awaiting_showcase_template_last_seats`** → positive integer → PATCH with **`last_seats_urgent`** + **`live_seats_remaining`** (back / înapoi / cancel returns to offer card).
- **Clear:** **`ao:ow:tcx:`** → PATCH **`template_id: null`** when selection present.
- Success / clear sends fresh offer detail message + keyboard.
- **No** fake urgency / discount / availability beyond B12A/B12B honesty rules.

## Non-goals (preserved)

No publish output/readiness changes, auto-publish, **packaging text approval** via this UI, lifecycle/media_review changes beyond template metadata, Mini App, booking/payment/orders, migrations, or duplicate validation outside **`template_choices`** + B12B service.

## Files touched (summary)

| Area | Path |
|------|------|
| Callback prefixes | `app/bot/constants.py` — **`ADMIN_OPS_OW_TEMPLATE_*`** |
| FSM | `app/bot/state.py` — **`awaiting_showcase_template_last_seats`** |
| Handlers + helpers | `app/bot/handlers/admin_moderation.py` — **`_showcase_template_*`**, **`_b12c_*`**, **`admin_ops_operator_workflow_b12c_showcase_template`**, **`admin_showcase_template_last_seats_input`**, **`OPERATOR_WORKFLOW_B12C_TEMPLATE_PATCH_CODE`** |
| Copy EN/RO | `app/bot/messages.py` — template screen + per-id labels |

## Telegram behavior

- **Open picker** → inferred / effective / selected (or none), **`notes`**, and blocked last-seats hint when a verified seat count is required.
- **Direct apply** only for safe **`template_choices`**; seat-gated ids use the last-seats FSM path.
- **Clear** → **`template_id: null`** via service; **Back** → fresh offer detail without applying a template (unless a previous step already wrote one).

## Callback prefixes + FSM (Telegram UX summary)

| Callback prefix | Role |
|-----------------|------|
| **`ao:ow:tm:`** | Open picker (`{offer_id}`) |
| **`ao:ow:ta:`** | Apply `{offer_id}:{template_id}` (direct apply only if choice not seat-gated) |
| **`ao:ow:tcx:`** | Clear selection |
| **`ao:ow:tmls:`** | Last seats → numeric reply |
| **`ao:ow:tmback:`** | Back to offer card |

**FSM:** **`AdminModerationState.awaiting_showcase_template_last_seats`** — operator sends one **positive integer** for **`live_seats_remaining`**, then PATCH **`last_seats_urgent`** aligned with B12B.

## Validation / re-read

- Handlers **re-read** review-package before mutating; **`patch_showcase_marketing_template`** must stay **enabled** in **`operator_workflow`**.
- **Direct apply:** id must pass **`_template_id_allowed_for_telegram_direct_apply`** (consistent with **`template_choices`** / **`requires_verified_live_seats`**).
- Persistence: **`SupplierOfferPackagingReviewService.patch_showcase_marketing_template`** + **`flag_modified`** on **`packaging_draft_json`**; **blocked** when packaging **`approved_for_publish`** (B12B guard).

## Tests

- **`tests/unit/test_operator_workflow_b12c_specs.py`** — open callback, apply parse, direct-apply gate vs **`requires_verified_live_seats`**.
- **`tests/unit/test_operator_workflow_c2b3_keyboard.py`** — RO order **Șablon** after **Aprobă text**; open prefix present when patch action enabled.
- **`tests/unit/test_telegram_admin_moderation_y281.py`** — regression (full suite green with implementation).

Representative run:

```text
pytest tests/unit/test_operator_workflow_b12c_specs.py tests/unit/test_operator_workflow_c2b3_keyboard.py tests/unit/test_telegram_admin_moderation_y281.py -q
```

## Validation checklist

- [x] Button visible when PATCH workflow enabled
- [x] Picker driven by **`template_choices`**; last seats not one-tap unless FSM path
- [x] Re-read + **`patch_showcase_marketing_template`** before/after rules aligned with B12B
- [x] Clear + refreshed detail
- [x] No publish / readiness / packaging-approve / lifecycle side effects beyond template metadata

## Next likely steps

1. **B13** — Channel adapter: wire effective/selected template into **`build_showcase_publication`** (tests + regression).
2. **Production content QA** — ops smoke, tone/locale.
3. **Optional** — Template picker copy polish; extra locales beyond EN/RO for B12C strings if needed.

```

---

## Notes (wrapper)

Implementation prompt: [`docs/CURSOR_PROMPT_B12C_TELEGRAM_TEMPLATE_SELECTION_UI.md`](CURSOR_PROMPT_B12C_TELEGRAM_TEMPLATE_SELECTION_UI.md). Canonical B12 spec: [`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`](B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md). Prior slice: [`docs/HANDOFF_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT_TO_NEXT_STEP.md`](HANDOFF_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT_TO_NEXT_STEP.md).

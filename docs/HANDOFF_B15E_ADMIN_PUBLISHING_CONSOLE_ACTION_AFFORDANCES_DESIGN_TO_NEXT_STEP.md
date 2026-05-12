# HANDOFF_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN_TO_NEXT_STEP

## Status: B15E implemented (docs synced)

- **Spec:** [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md).
- **Slice:** Read-only **action affordance metadata** on **`GET /admin/publishing-console`** (additive **`actions[]`** per item).
- **Code:** `app/schemas/admin_publishing_console.py` (`AdminPublishingConsoleActionAffordanceRead`, item `actions`); `app/services/admin_publishing_console_service.py` (`_affordances_from_operator_workflow`, `_tour_promotion_action_affordances`).
- **Tests passed:** **`8`** — `python -m pytest tests/unit/test_admin_publishing_console.py -q`.

## Scope

B15E adds **read-only** action affordance metadata so an admin UI can see what could be done next **without** this endpoint performing any mutation.

Each affordance includes: `code`, `label`, `kind`, `enabled`, `requires_confirmation`, `danger_level`, `admin_path`, `method`, `implemented`, `disabled_reason`, `source` (`operator_workflow` | `console_read_only` | `future`).

## Important boundary

B15E **does not execute** actions. It only **projects** metadata.

## Expected result (as shipped)

- **Action metadata is additive** on **`AdminPublishingConsoleItemRead`** (`actions[]`); **B15D** readiness fields remain unchanged.
- **Supplier-offer** rows: `actions` mirrors **`review-package` → `operator_workflow.actions`** (paths expanded with `offer_id`); `implemented: true`, `source: operator_workflow`.
- **Tour promotion** rows: **safe/read** affordances (`open_tour_admin`, `verify_mini_app_catalog`) with `source: console_read_only`; plus a **future** placeholder (`compose_tour_promotion_draft`) with `implemented: false`, `enabled: false`, `source: future`.

## Must remain read-only

`GET /admin/publishing-console` must not: publish; send Telegram messages; create bridge/tour/execution link; activate catalog; schedule posts; or otherwise mutate production data.

## Preserved architecture

- **Review-package / operator workflow** remains the source of truth for supplier-offer action lists.
- **B15C** exact CTA gate remains the source of truth for publish safety (unchanged).
- **Layer A** and **Mini App routing** untouched.
- No Telegram send path is introduced by B15E.

## Next recommended step

**B15F** (template/source/channel read expansion) **or** **B15E2** (explicit action execution / console UX) **only** after **explicit** product **/** security **/** design **approval**. **B15G** remains roadmap-only until separately approved.

### Later (per B15A roadmap)

1. **B15F** — template/source/channel expansion (read-first / design + read models as scoped).
2. **B15E2** — explicit **action execution** from the console (or a dedicated flow), **only** if approved; still guarded, no auto-publish by default.
3. **B15G** — guarded auto-publish design **only** after explicit product/security approval.

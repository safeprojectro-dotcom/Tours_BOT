# HANDOFF_REPAIR_TRUNCATED_PROMPT_DOCS_AFTER_C2B7_2

Project: Tours_BOT

## Purpose

Repair three truncated untracked CURSOR_PROMPT docs so future agents do not run broken or obsolete prompts.

## Files

- docs/CURSOR_PROMPT_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md
- docs/CURSOR_PROMPT_ADMIN_COVER_REAPPROVAL_OK_PHOTO_C2B7_2_IMPLEMENTATION.md
- docs/CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_GENERATE_PACKAGING_BUTTON_C2B2.md

## Required safety

Docs-only.
No app/.
No tests/.
No alembic/.
No mini_app/.
No runtime behavior changes.

## Expected result

Each repaired prompt has:

- closed code fences;
- clear status banner;
- pointer to CHAT_HANDOFF and relevant HANDOFF;
- no misleading duplicate implementation instruction if already implemented.

## Important

C2B2 is already implemented.

C2B7.1 is implemented and deployed.

C2B7.2 OK photo status must be determined from code search:
- if implemented: mark prompt as archive;
- if not implemented: make prompt complete and safe as current implementation prompt.

---

## Completion (repair applied)

**Code check:** C2B7.2 is **implemented** (`approve_cover_for_card`, `admin_ops_operator_workflow_c2b7_2_ok_photo` in `app/bot/handlers/admin_moderation.py`, wiring in `supplier_offer_operator_workflow.py` **`/`** `supplier_offer_review_package_service.py`, tests e.g. `tests/unit/test_operator_workflow_c2b7_2_specs.py`).

**Docs:** The three **`CURSOR_PROMPT_*`** files above were repaired (closed fences, archive banners, **Canonical pointers** to **`docs/CHAT_HANDOFF.md`** + relevant **`docs/HANDOFF_*.md`**). **`docs/CHAT_HANDOFF.md`** includes an explicit **Slice C2B7.2** line linking **`HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md`**.

Do **not** paste these **`CURSOR_PROMPT_*`** files into Agent as fresh implementation tasks **`;`** use HANDOFF **`/`** CHAT_HANDOFF instead.
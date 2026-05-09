# CURSOR_PROMPT_MINI_APP_FLET_085_BORDER_HOTFIX_CONTEXT7

You continue Tours_BOT.

## Mode

Agent.

## Mandatory source

Before editing code, use Context7 to check current Flet / flet-web 0.85.x API for borders and colors.

Do not rely on memory.

Also inspect the installed package if needed to confirm available APIs.

## Problem

Mini_App_UI deploy no longer fails on ft.padding.*, but now crashes on catalog render with:

AttributeError: module 'flet.controls.border' has no attribute 'all'

Crash location from Railway logs:

mini_app/app.py
_build_tour_card
border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT)

## Scope

Mini App compatibility hotfix only.

Search mini_app/ for:

ft.border.all
ft.border.only
ft.border.Border
ft.border

Also check whether the color constant used there is valid in Flet 0.85.x:

ft.Colors.OUTLINE_VARIANT

Replace according to actual Flet 0.85.x API confirmed through Context7 and/or installed package.

Likely target may be class-based API such as:

ft.Border.all(...)

but verify first.

## Files likely affected

mini_app/app.py

## Boundaries

Do not change backend business logic.
Do not change bot/admin workflow.
Do not change C2B7.2.
Do not change booking/payment/order logic.
Do not change DB/migrations.
Do not redesign UI.
Only Flet 0.85 compatibility fix.

## Verification

Run:

python -m compileall mini_app app alembic -q

Run existing Mini App unit test:

python -m pytest tests/unit/test_mini_app_my_request_detail_controls.py -v

Search after fix:

Select-String -Path mini_app/*.py -Pattern "ft\.border\." -CaseSensitive
Select-String -Path mini_app/*.py -Pattern "ft\.padding\." -CaseSensitive

Expected: no old lowercase helper usage remains unless explicitly justified by Context7/package inspection.

## Final report

Report exactly:

1. Context7 / package findings for Flet 0.85 border API
2. Files changed
3. Replacements made
4. Any remaining ft.border.* or ft.padding.*
5. Checks run
6. Railway manual verification steps
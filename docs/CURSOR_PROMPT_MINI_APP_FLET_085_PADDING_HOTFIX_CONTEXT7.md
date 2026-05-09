# CURSOR_PROMPT_MINI_APP_FLET_085_PADDING_HOTFIX_CONTEXT7

You continue Tours_BOT.

## Mode

Agent.

## Mandatory documentation source

Before editing code, use Context7 to check the current Flet / flet-web API for version 0.85.x, especially padding / margin helpers.

Do not rely on memory.

Use Context7 as the source of truth for:

- current padding API;
- whether `ft.padding.symmetric(...)` is still valid;
- replacement syntax;
- any compatibility notes for Flet 0.85.x.

After checking Context7, report briefly what API should be used.

## Problem

Railway Mini_App_UI crashes on catalog render:

```text
AttributeError: module 'flet.controls.padding' has no attribute 'symmetric'
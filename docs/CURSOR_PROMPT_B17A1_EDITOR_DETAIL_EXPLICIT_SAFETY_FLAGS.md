# CURSOR_PROMPT_B17A1_EDITOR_DETAIL_EXPLICIT_SAFETY_FLAGS

Continue the existing Tours_BOT project.

This is a tiny corrective polish after B17A Railway smoke.

Current checkpoint:
- e21a85f feat: add read-only publishing editor detail view

B17A Railway smoke:
- GET /admin/publishing-console/supplier-offers/12/editor returns 200.
- Existing sections are present and populated.
- Actual section fields are text/summary-oriented.
- However, the response lacks some explicit machine-readable frontend safety/action booleans from the B17A contract.

Observed actual structure:
- channel_section has channel_kind/channel_status/channel_ref/editor_note
- template_section has template_family/selected_template_id/etc.
- preview_section has console_preview_status/payload_status/has_caption_html
- readiness_section has readiness_summary/console_status/gate_summary/etc.
- safety_section has text notes only
- future_actions currently has edit_showcase_template/select_channel only

Goal:
Add explicit read-only frontend safety/action booleans without changing behavior.

This is additive and backward-compatible.

## Required additive fields

### channel_section

Add:
- can_select_channel: bool = false
- can_publish_to_channel: bool = false

### template_section

Add:
- can_select_template: bool = false
- can_edit_template: bool = false

### preview_section

Add:
- preview_available: bool
- can_edit_copy: bool = false
- can_refresh_preview: bool = false

`preview_available` should be true when console_preview_status or payload_status indicates available; otherwise false.

### media_section

If media_section exists, ensure it has:
- can_upload_media: bool = false
- can_generate_card: bool = false

### safety_section

Add explicit booleans:
- read_only: bool = true
- no_telegram_io: bool = true
- no_publish_attempt: bool = true
- no_scheduler: bool = true
- no_auto_publish: bool = true
- no_prepare_chain_execution: bool = true
- no_layer_a_mutation: bool = true
- no_mini_app_b11_change: bool = true

Keep existing text fields:
- detail_notice
- ui_card_safety_line
- editor_boundary_note

### future_actions

Ensure these future public-side-effect actions are present and disabled:
- confirm_publish
- schedule_publish

Each should be:
- implemented=false
- enabled=false
- requires_confirmation=true
- danger_level/public-side-effect equivalent if the existing action schema supports it
- disabled_reason clearly says not implemented in B17A and requires separate go/no-go

Do not remove existing future actions:
- edit_showcase_template
- select_channel

If the current future action DTO is narrower and does not support requires_confirmation/danger_level/method, keep within the existing schema but include code/label/implemented/enabled/disabled_reason.

## Strict boundaries

Do NOT publish.
Do NOT send Telegram messages.
Do NOT retry Telegram messages.
Do NOT schedule publish.
Do NOT implement auto-publish.
Do NOT create publish attempts.
Do NOT execute prepare_conversion_chain.
Do NOT mutate supplier offers, tours, bridges, execution links, orders, payments, reservations, seats, or content items.
Do NOT create migration.
Do NOT change Mini App routing.
Do NOT change B11 deep-link behavior.
Do NOT introduce provider/Telegram API calls.
Do NOT add POST/PATCH endpoints.
Do NOT add frontend implementation.

## Expected files

Likely:
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py
- tests/unit/test_admin_publishing_console.py
- docs/HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md if needed

No migration.

## Tests

Update focused tests to assert:

1. editor channel_section has can_select_channel=false and can_publish_to_channel=false.
2. template_section has can_select_template=false and can_edit_template=false.
3. preview_section has preview_available bool and can_edit_copy=false.
4. safety_section all explicit safety booleans are true.
5. future_actions includes confirm_publish and schedule_publish disabled.
6. existing B17A tests still pass.

Run:
python -m compileall app tests
python -m pytest tests/unit/test_admin_publishing_console.py -q
python -m pytest tests/unit/test_supplier_offer_publish_readiness.py -q
python -m pytest tests/unit/test_supplier_offer_review_package.py -q
python -m pytest tests/unit/test_admin_publishing_console_prepare_chain_action.py -q
python -m pytest tests/unit/test_prepare_conversion_chain_d2d_affordance.py -q

Docs:
- Minimal handoff note only if useful.
- Do not commit.
- Do not push.

Report:
1. files changed
2. fields added
3. future actions added
4. test results
5. confirm no Telegram/publish/scheduler/auto-publish/prepare-chain execution/mutation/migration
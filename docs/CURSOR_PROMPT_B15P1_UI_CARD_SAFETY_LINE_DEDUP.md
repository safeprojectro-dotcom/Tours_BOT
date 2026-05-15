# CURSOR_PROMPT_B15P1_UI_CARD_SAFETY_LINE_DEDUP

Continue the existing Tours_BOT project.

This is a tiny corrective polish after B15P Railway smoke.

Current checkpoint:
- 42a6eec feat: add publishing console admin ui metadata

B15P Railway smoke passed:
- GET /admin/publishing-console?kind=supplier_offer_initial returns `ui_card`
- supplier-offer rows have `ui_card`
- `primary_action_kind=guarded_post`
- already-published / blocked rows do not execute publish
- no Telegram I/O
- no publish attempts
- no scheduler
- no auto-publish

Observed cosmetic issue:
- `ui_card.safety_line` repeats the same read-only safety copy twice, because it appears to combine console_preview/preview_payload safety notes without deduplication.

Example observed:
"Publishing console is read-only: no Telegram publish ... · Publishing console is read-only: no Telegram publish ... preview_payload mirrors ..."

Goal:
Deduplicate / compact `ui_card.safety_line` so admin UI sees a clear single safety line.

Rules:
- Keep safety copy conservative.
- It may mention:
  - read-only console
  - no Telegram publish/schedule/channel send
  - preview_payload does not call Telegram APIs
  - guarded prepare-chain is separate from Telegram publish
- Do not remove safety meaning.
- Do not add new behavior.
- Do not change endpoint paths.
- Do not change runtime side effects.

Strict boundaries:
- Do NOT publish.
- Do NOT send Telegram messages.
- Do NOT schedule publish.
- Do NOT implement auto-publish.
- Do NOT create publish attempts.
- Do NOT execute prepare_conversion_chain.
- Do NOT mutate supplier offers, tours, bridges, execution links, orders, payments, reservations, or seats.
- Do NOT create migration.
- Do NOT change Mini App/B11 routing.
- Do NOT change frontend implementation.

Expected code area:
- app/services/admin_publishing_console_service.py
- tests/unit/test_admin_publishing_console.py if needed

Expected test:
- add/adjust a test asserting `ui_card.safety_line` contains the read-only safety meaning only once, or at least does not duplicate the exact "Publishing console is read-only" phrase.
- existing B15P tests must still pass.

Run:
python -m compileall app tests
python -m pytest tests/unit/test_admin_publishing_console.py -q
python -m pytest tests/unit/test_supplier_offer_publish_readiness.py -q
python -m pytest tests/unit/test_supplier_offer_review_package.py -q
python -m pytest tests/unit/test_admin_publishing_console_prepare_chain_action.py -q
python -m pytest tests/unit/test_prepare_conversion_chain_d2d_affordance.py -q

Docs:
- No docs update required unless you think the handoff needs one short sentence.
- Do not commit.
- Do not push.

Report:
1. files changed
2. how safety_line is deduplicated
3. tests run/results
4. confirm no Telegram/publish/scheduler/auto-publish/mutation/migration
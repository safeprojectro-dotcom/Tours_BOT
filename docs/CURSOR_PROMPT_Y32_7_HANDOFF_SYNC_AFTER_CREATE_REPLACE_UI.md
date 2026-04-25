Docs-only handoff sync after Y32.7 Telegram admin create execution link UI smoke.

Update docs/CHAT_HANDOFF.md and create:
docs/HANDOFF_Y32_7_OPERATOR_LINK_CREATE_REPLACE_UI_ACCEPTED.md

Record:
- Telegram admin UI can create execution link from /admin_published -> offer detail -> Execution link.
- Tested offer #5 with explicit tour_id=3.
- Confirmation screen showed offer/tour sales_mode, tour status, seats, and Mini App CTA warning.
- Link was created successfully: supplier_offer_id=5 -> tour_id=3.
- Status screen shows active link and link history.
- Previous closed link remains in history.
- DB confirms active link id=3 for offer #5 and closed historical link id=2.
- No auto-tour creation.
- No Mini App changes.
- No Layer A booking/payment changes.
- No identity bridge changes.
- Current postponed item: paginated compatible tour search/list UI.

Docs only. No runtime code. No migrations.
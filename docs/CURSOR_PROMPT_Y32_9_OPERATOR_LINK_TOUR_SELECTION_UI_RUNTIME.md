Continue Tours_BOT strict continuation.

Task:
Implement first safe runtime slice for Telegram admin compatible tour selection UI for execution link create/replace.

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPERATOR_LINK_TOUR_SELECTION_UI_GATE.md
- docs/OPERATOR_LINK_CREATE_REPLACE_UI_GATE.md
- docs/HANDOFF_Y32_7_OPERATOR_LINK_REPLACE_GUARD_SMOKE.md

Goal:
Replace manual-only tour_id/code flow with a safe compatible tour list for admin/operator.

Scope:
1. From /admin_published -> offer detail -> Execution link:
   - Create execution link
   - Replace execution link
2. Show compatible tour candidates before asking manual input.
3. Candidate list must filter by same sales_mode as supplier_offer.
4. Each tour card/button must show enough context:
   - tour id
   - code
   - title
   - status
   - sales_mode
   - seats available/total
5. Selecting candidate opens existing confirmation screen.
6. Keep manual tour_id/code input as fallback if already implemented.
7. Preserve existing create/replace service behavior and validation.

Strict rules:
- no auto-create tours
- supplier_offer != tour
- no Layer A booking/payment changes
- no Mini App changes
- no identity bridge changes
- no migrations unless absolutely unavoidable
- direct booking CTA remains controlled by active authoritative link + linked tour policy

Pagination:
- If candidate count > page size, add Next/Previous.
- Preserve offer_id and action mode (create/replace) across pages.
- Stable ordering by departure/date/id if available.

Fail-safe:
- If no compatible tours: show clear message and no mutation.
- If selected tour becomes invalid/stale: block at confirmation/service validation.
- Sales mode mismatch remains blocked.
- Existing active link duplicate creation still blocked.

Tests:
- compatible tour list filters same sales_mode
- no candidates state
- selecting candidate opens confirmation
- create from candidate
- replace from candidate
- manual fallback still works if present
- mismatch guard still passes
- close/status existing tests still pass

After coding report:
- files changed
- UI path implemented
- pagination behavior
- fallback behavior
- tests run
- postponed items
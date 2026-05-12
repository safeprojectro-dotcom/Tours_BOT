# HANDOFF_B15C2_ADMIN_NAV_STAY_ON_OFFER_AFTER_BRIDGE_TO_NEXT_STEP

## Scope

B15C2 improves admin/operator Telegram navigation after supplier-offer workflow actions (bridge, catalog, execution link, packaging, media, publish, legacy approve/retract/reject).

## Goal

After actions such as **Leagă tur** and **În catalog** (and the other wired flows below), the admin stays on the **same** `supplier_offer_id` and sees the refreshed **review-package-backed** detail + keyboard (**Prev/Next** FSM matches that offer).

## Must preserve (verified by design)

- Layer A booking/payment/reservation behavior
- Supplier-offer publish gate
- Execution-link semantics (validation unchanged)
- Mini App `startapp` routing
- Confirmation boundaries for dangerous/conversion actions
- No automatic publish
- No automatic execution-link creation

## Expected result

```text
supplier offer review panel
  → admin runs bridge/catalog/workflow action (with existing confirmations)
  → mutation succeeds
  → success line + same offer panel refreshed (operator_workflow / conversion panel / buttons)
```

## Shipped

**B15C2** pins the moderation **FSM** to the mutated offer:

- **`_queue_state_after_offer_mutation`** — with a **fresh** `_load_queue_ids`, keep index for `offer_id` or fall back to `[offer_id]` (legacy **Approve / Retract / Reject** + reject reason path; avoids jumping to **`queue_ids[0]`** when the offer drops out of the filter).
- **`_sync_offer_queue_after_mutation`** — **FSM-only** re-pin from existing `queue_offer_ids` snapshot (from **`/admin_ops`**) or `[offer_id]`; avoids extra `list_offers` on the post-commit handler session.

### Code (pointers)

- **`app/bot/handlers/admin_moderation.py`** — wiring after success for **C2B1** / **C2B2** / **C2B6** / **C2B7.2** / **C2B8B** / **C2B10T-A/B/C**, legacy execution-link wizard **create/replace/close** (link status, then **full** offer panel), **Approve / Retract / Reject**. Removed **`_refresh_queue`** in favor of **`_queue_state_after_offer_mutation`**.
- **`app/bot/messages.py`** — EN/RO success lines for bridge / catalog / workflow execution-link mention **panel refreshed below**.

### Tests

- **`tests/unit/test_queue_state_after_offer_mutation.py`** — pure helper.
- **`tests/unit/test_telegram_admin_moderation_y281.py`** — workflow strings: **tour linked**, **booking link set** (subset of y281; some legacy link tests may still fail on packaging gate if offer fixtures lack `approved_for_publish`).

## Verification

- **Automated:**  
  `pytest tests/unit/test_queue_state_after_offer_mutation.py tests/unit/test_operator_workflow_c2b10ta_specs.py tests/unit/test_operator_workflow_c2b10tb_specs.py tests/unit/test_operator_workflow_c2b10tc_specs.py`  
  plus optional y281 workflow cases:  
  `test_workflow_tour_bridge_confirm_calls_service_when_gate_enabled`,  
  `test_workflow_activate_catalog_confirm_calls_service_when_gate_enabled`,  
  `test_workflow_execution_link_confirm_calls_service_when_gate_enabled`.

- **Manual (ops):** Open **`/admin_ops`** queue → pick offer → **Leagă tur** → confirm → new message shows updated workflow; **Prev/Next** still centered on that offer where the snapshot allows.

## Next possible steps

- **B15C3** — copy polish: replace confusing “execution links after showcase publish” wording where execution link can exist **before** publish.
- **B15D** — deeper admin publishing console polish.
- **B15E/B15F/B15G** — only if explicitly selected later.

## Related

- Prompt: **`docs/CURSOR_PROMPT_B15C2_ADMIN_NAV_STAY_ON_OFFER_AFTER_BRIDGE.md`**

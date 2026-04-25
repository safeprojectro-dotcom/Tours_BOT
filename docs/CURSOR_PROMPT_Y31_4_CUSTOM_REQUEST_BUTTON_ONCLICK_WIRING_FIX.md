Continue narrow debug for CustomRequestScreen submit regression.

Evidence:
After reproduction, none of these markers appeared in Mini_App_UI logs:
- custom_request_submit_clicked
- custom_request_submit_start
- validate_custom_request_form_local
- custom_request_post_before

Therefore the issue is before submit logic:
- button on_click not wired,
- wrong button instance rendered,
- submit button disabled,
- wrong CustomRequestScreen instance,
- or route renders a stale/non-instrumented control.

Task:
Inspect CustomRequestScreen rendering in mini_app/app.py.

Find every submit/send/create request button in CustomRequestScreen and ensure:
1. The visible submit button has on_click wired to the instrumented click/start handler.
2. The button is not permanently disabled by loading/identity/form state.
3. Route /custom-request renders the same CustomRequestScreen instance that has telegram_user_id set.
4. If disabled, show visible reason.
5. Keep fail-closed identity behavior.

Do not touch:
- Telegram identity bridge
- Layer A booking/payment
- supplier conversion bridge
- backend contracts
- tour sales mode policy

Expected:
Pressing submit must at least emit custom_request_submit_clicked/custom_request_submit_start.
If form is valid, it must emit custom_request_post_before and send POST /mini-app/custom-requests.

Tests:
Run/extend:
python -m pytest tests/unit/test_mini_app_custom_request_submit_hotfix.py tests/unit/test_mini_app_supplier_offer_landing_wiring.py

Report:
- exact root cause
- changed files
- whether visible button was stale/unwired/disabled
- confirmation no Layer A/identity/supplier bridge changes
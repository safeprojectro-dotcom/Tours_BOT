Debug narrow regression after Phase 7.1 full_bus actionability changes.

Observed in Railway Mini_App_UI logs:
- Mini App identity is OK:
  route=/?tg_bridge_user_id=5330304811 has_identity=True source=route_query_user_id
- Custom request screen loads:
  GET /mini-app/custom-request?telegram_user_id=5330304811... 200
- But pressing submit does NOT produce:
  POST /mini-app/custom-requests

Task:
Find why CustomRequestScreen submit button no longer triggers POST.

Scope:
- mini_app/app.py only unless tests require update
- Do not touch Telegram identity bridge
- Do not touch Layer A booking/payment
- Do not touch supplier conversion bridge
- Do not change backend contracts

Check:
1. Is submit button on_click still wired to _submit_async / submit handler?
2. Is button disabled because loading/validation/telegram_user_id state is wrong?
3. Is telegram_user_id propagated into CustomRequestScreen after latest policy changes?
4. Is form validation silently blocking without visible error?
5. Did recent actionability helper/refactor accidentally affect custom request route/screen lifecycle?

Expected fix:
- Minimal UI/runtime fix only.
- Pressing submit must call POST /mini-app/custom-requests with runtime telegram_user_id.
- If validation fails, show visible validation message.
- If identity missing, show identity_required_my_data.

Tests:
Run/extend:
python -m pytest tests/unit/test_mini_app_custom_request_submit_hotfix.py tests/unit/test_mini_app_supplier_offer_landing_wiring.py

Report:
- exact root cause
- changed files
- confirmation that POST is triggered again
- confirmation no identity/Layer A/supplier bridge semantics changed
URGENT production regression fix.

Problem:
After Y36.2 deploy, bot is down. Any command triggers SQLAlchemy mapper initialization error.

Railway log:
InvalidRequestError:
Mapper 'Mapper[User(users)]' has no property 'ops_assigned_custom_marketplace_requests'.

Triggering mapper:
Mapper[CustomMarketplaceRequest(custom_marketplace_requests)]

Root cause likely:
CustomMarketplaceRequest defines relationship/back_populates to User using:
ops_assigned_custom_marketplace_requests
or similar, but app/models/user.py does not define the matching relationship property.

Task:
Fix SQLAlchemy model relationship mapping narrowly.

Requirements:
- Do not change database schema.
- Do not create a new migration.
- Do not change assignment semantics.
- Do not change API behavior.
- Do not change Mini App, booking/payment, execution-link, identity bridge.
- Keep assigned_operator_id / assigned_by_user_id as FKs to users.id.
- Fix mapper initialization.

Check:
1. app/models/custom_marketplace_request.py relationships for assigned_operator / assigned_by_user.
2. app/models/user.py must contain matching relationship properties if back_populates is used.
3. Prefer adding explicit User relationships matching the back_populates names.
4. If multiple FKs point to users.id, use foreign_keys correctly on both sides to avoid ambiguity.

Expected safe pattern:
- CustomMarketplaceRequest.assigned_operator -> User, back_populates="ops_assigned_custom_marketplace_requests"
- User.ops_assigned_custom_marketplace_requests -> list[CustomMarketplaceRequest], back_populates="assigned_operator", foreign_keys=[CustomMarketplaceRequest.assigned_operator_id]

- CustomMarketplaceRequest.assigned_by_user -> User, back_populates="ops_assigned_custom_marketplace_requests_by_actor"
- User.ops_assigned_custom_marketplace_requests_by_actor -> list[CustomMarketplaceRequest], back_populates="assigned_by_user", foreign_keys=[CustomMarketplaceRequest.assigned_by_user_id]

Use exact names based on current model code.

Tests:
- add/adjust mapper import test if needed
- run:
python -m compileall app tests/unit/test_api_admin.py tests/unit/test_telegram_admin_moderation_y281.py
python -m pytest tests/unit/test_api_admin.py -k "assign"
python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -k "admin_ops"

Also run a lightweight import/mapping smoke if available:
python - <<'PY'
from sqlalchemy.orm import configure_mappers
from app.models.user import User
from app.models.custom_marketplace_request import CustomMarketplaceRequest
configure_mappers()
print("mappers ok")
PY

Report:
- root cause
- exact files changed
- no migration
- tests run
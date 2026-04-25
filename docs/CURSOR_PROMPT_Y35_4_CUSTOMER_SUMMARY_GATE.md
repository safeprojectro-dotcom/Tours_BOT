Continue Tours_BOT strict continuation.

Task:
Create docs-only design gate for Admin/Ops customer summary layer.

Context:
Y35.2/Y35.3 accepted:
- Admin API read-only visibility exists for orders and custom requests.
- Telegram admin UI shows orders and requests.
- Current customer display is raw telegram_user_id, e.g. customer 5330304811.
- This is acceptable for dev but weak for operator UX.

Goal:
Design safe customer summary display for admin/operator surfaces.

Scope:
Admin/Ops read surfaces only:
- /admin/orders
- /admin/orders/{id}
- /admin/custom-requests
- /admin/custom-requests/{id}
- Telegram admin orders/requests UI

Rules:
- Docs only.
- No runtime code.
- No migrations.
- No customer Mini App changes.
- No My bookings / My requests privacy changes.
- No booking/payment changes.
- No execution-link changes.
- No identity bridge changes.
- No sensitive data expansion without explicit existing source.
- Fail closed if customer profile fields are missing.

Design must cover:
1. Current state
2. Why raw telegram_user_id is not enough
3. Safe customer summary fields
4. Data sources already available
5. Fallback display rules
6. Privacy/security boundaries
7. Admin API representation
8. Telegram UI representation
9. Tests required
10. First safe runtime slice recommendation

Recommended summary format:
- primary: display_name if available
- secondary: @username if available
- fallback: tg:{telegram_user_id}
- optional: phone only if already explicitly stored and already authorized for admin view

Update:
docs/CHAT_HANDOFF.md with Y35.4 reference and next-safe pointer.

Do not touch runtime code.
# Admin/Ops Visibility Gate

## 1. Current State

- Customer Mini App self-service views are intentionally user-scoped:
  - `My bookings` shows only bookings/orders for the current Telegram user context.
  - `My requests` shows only custom requests/RFQ records for the current Telegram user context.
- This privacy model is accepted and must not be reused as an admin/operator shortcut.
- Existing admin Telegram work currently covers supplier/profile/offer moderation and supplier-offer execution-link operations.
- Admin/ops still needs a separate operational visibility layer for all bookings/orders and all custom requests/RFQ records.
- This gate is docs-only. It does not add routes, handlers, schemas, migrations, UI screens, or runtime behavior.

## 2. Privacy Boundary

- `My bookings` and `My requests` remain customer self-service surfaces only.
- Customer Mini App screens must never expose all-user bookings, all-user requests, operational queues, or cross-user search.
- Admin/operator visibility must live in separate authenticated admin/ops surfaces.
- Admin/ops must not instruct operators to use customer buttons, customer deep links, or customer-scoped Mini App pages to inspect global data.
- Missing or uncertain admin identity must fail closed and show no cross-user data.
- Supplier-facing views remain supplier-scoped and must not become a proxy for all-customer operational visibility.

## 3. Admin Roles and Permissions

- Central admin/operator may need read visibility across bookings/orders and custom requests/RFQ records for operations support.
- Read visibility and mutation permissions must be separated:
  - first slice should be read-only;
  - future close/resolve/reassign actions require explicit design and runtime approval;
  - destructive or customer-impacting actions require confirmation and audit trail.
- Telegram admin allowlisting may be sufficient for a first Telegram slice, but broader role-based access remains postponed unless explicitly designed.
- Supplier operators must not receive global booking/request visibility.
- Customers must not receive admin/ops controls or global identifiers.

## 4. Required Booking Visibility

Admin/ops booking visibility should allow operators to inspect all relevant Layer A booking/order records without changing booking/payment semantics.

Minimum list fields:
- order/booking id;
- tour id/code/title when available;
- departure date/time;
- booking/order status;
- reservation/hold state when available;
- payment state or payment-entry status summary;
- customer identifier suitable for support lookup, bounded to what admin permissions allow;
- seat/passenger count summary;
- created/updated timestamps.

Important boundaries:
- The view is operational read-side only in the first slice.
- It must not create reservations, extend holds, start payments, refund payments, or alter order status.
- Payment provider raw payloads and sensitive payment details should not be shown in the first slice.

## 5. Required Request/RFQ Visibility

Admin/ops request visibility should allow operators to inspect all custom marketplace requests/RFQ records across users in a separate admin surface.

Minimum list fields:
- request id;
- customer identifier suitable for support lookup, bounded to what admin permissions allow;
- request lifecycle/status;
- requested route/destination/date/party-size summary where available;
- bridge/preparation state when available;
- linked booking/order id when a request converts;
- supplier offer or execution-link context when relevant and available;
- created/updated timestamps.

Important boundaries:
- The first slice should not change request lifecycle or RFQ semantics.
- It must not auto-create supplier offers, tours, bookings, or execution links.
- Customer request detail should show enough context for support while avoiding unnecessary PII expansion.

## 6. Filters

Booking/order filters should include:
- order/booking status;
- payment status;
- reservation/hold state;
- tour id/code/title;
- departure date window;
- created date window;
- customer identifier/contact search where admin-authorized.

Request/RFQ filters should include:
- request lifecycle/status;
- request date or created date window;
- destination/title/text search where available;
- customer identifier/contact search where admin-authorized;
- bridge/preparation state;
- linked booking/order state;
- assignment/owner once assignment exists.

Filter behavior must be bounded:
- pagination is required for broad lists;
- filters must fail closed on invalid input;
- no fuzzy or broad PII search should be introduced without explicit approval.

## 7. Detail Screens

Booking/order detail should show:
- booking/order identity and current status;
- linked tour/departure context;
- reservation/hold summary;
- payment state summary;
- customer support context appropriate for admin permissions;
- related supplier-offer execution link context when available;
- immutable event/timestamp summary where available.

Request/RFQ detail should show:
- request identity and current lifecycle;
- submitted customer request data;
- bridge/preparation state;
- linked booking/order if conversion exists;
- supplier offer/linkage context if relevant;
- operational notes or assignment only after a future design gate approves them.

Detail screens should default to read-only in the first runtime slice.

## 8. Safe Operational Actions, Future Only

The following actions are explicitly future-only and must not be implemented by this gate:
- close a booking-support case;
- resolve a custom request/RFQ;
- reassign request or booking support ownership;
- add internal operational notes;
- escalate to supplier/operator workflow;
- trigger customer notification;
- alter order, reservation, hold, payment, refund, or RFQ lifecycle state.

Future actions must require:
- separate design gate or explicit runtime prompt;
- role/permission check;
- confirmation for customer-impacting changes;
- bounded reason/note fields;
- audit trail;
- regression tests proving customer self-service privacy remains unchanged.

## 9. Fail-Safe and Security Behavior

- No admin auth means no cross-user data.
- Missing or malformed filter values should return a safe validation message, not a broad unfiltered dump.
- Detail lookup for missing records should return a safe not-found response.
- Customer Mini App routes must continue enforcing current-user scope.
- Supplier surfaces must continue enforcing supplier ownership scope.
- Admin/ops views must avoid exposing raw payment provider data, secrets, tokens, or unnecessary PII.
- Any runtime implementation must include tests proving:
  - customer `My bookings` remains user-scoped;
  - customer `My requests` remains user-scoped;
  - admin/ops visibility is available only through admin-authenticated surfaces;
  - read-only admin views do not mutate booking, payment, RFQ, Mini App, or execution-link state.

## 10. First Safe Runtime Slice Recommendation

Recommended first runtime slice:
1. Add read-only admin/ops booking list with pagination and narrow filters.
2. Add read-only admin/ops booking detail.
3. Add read-only admin/ops custom request/RFQ list with pagination and narrow filters.
4. Add read-only admin/ops request/RFQ detail.
5. Keep all future close/resolve/reassign/notes actions hidden or disabled.
6. Reuse existing service/query boundaries where possible; do not duplicate booking/payment policy in UI.
7. Add regression tests that prove customer self-service routes remain scoped to the current Telegram user.

Postponed until later gates:
- close/resolve/reassign actions;
- internal notes;
- assignment queues;
- SLA dashboards;
- supplier escalation workflows;
- payment/refund controls;
- incident/disruption automation.

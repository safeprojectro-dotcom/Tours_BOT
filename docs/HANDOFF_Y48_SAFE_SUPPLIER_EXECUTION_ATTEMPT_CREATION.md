Y48 — Safe Supplier Execution Attempt Creation is completed.

Current state:
- supplier_execution_request can be created by admin trigger
- supplier_execution_attempt can be created explicitly by admin endpoint
- no supplier messaging exists
- no outbound execution exists

Endpoint:
POST /admin/supplier-execution-requests/{request_id}/attempts

Allowed behavior:
- ADMIN_API_TOKEN required
- validate request exists/status
- create pending attempt row
- assign attempt_number explicitly
- return attempt data

Still forbidden:
- supplier messages
- supplier API calls
- workers
- automatic retry
- RFQ implementation
- booking/order/payment mutation
- Mini App changes
- execution links
- identity bridge
- customer/supplier notifications
- operator-decision behavior changes

Next safe step:
Y49 — supplier outbound messaging design gate.
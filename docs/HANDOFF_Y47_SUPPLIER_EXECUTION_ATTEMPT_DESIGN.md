Y47 — Supplier Execution Attempt Design is completed.

Current architecture:

- request = created by admin trigger
- attempt = future execution unit

Important:

Attempts:
- are NOT created by trigger
- are NOT automatic
- require separate explicit step

Still no supplier messaging exists.

Next step:
Y48 — safe attempt creation (still no messaging).
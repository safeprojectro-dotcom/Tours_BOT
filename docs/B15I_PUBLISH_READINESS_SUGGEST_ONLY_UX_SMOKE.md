\# B15I — Publish Readiness Suggest-only UX Railway Smoke



\## Purpose



Verify that B15I compact suggest-only `publish\_readiness` display fields are visible on Railway production read models without public side effects.



\## Environment



\- Environment: Railway production

\- Commit tested: `06cc17`

\- Date/time UTC: 2026-05-15

\- Scope: read-only GET verification



\## Endpoints checked



\- `GET /admin/supplier-offers/12/review-package`

\- `GET /admin/publishing-console?kind=supplier\_offer\_initial`



\## Review package result



Checked supplier offer `12`.



Result:



\- offer\_id: `12`

\- title: `Excursie Timisoara Oradea`

\- status: `already\_published`

\- badge: `already\_published`

\- summary: `Already published — not a candidate for first-time publish suggestion.`

\- next\_action\_code: `review\_conversion\_health`

\- next\_action\_label: `Review conversion health on review-package (avoid duplicate showcase without ops review).`

\- primary\_blocker: `Offer is already published.`

\- warning\_summary: `2 warning(s): content\_quality, publish\_safe`

\- gate\_summary: `8 passed · 1 failed · 2 warnings · 1 not applicable`

\- can\_suggest\_manual\_publish: `false`

\- can\_auto\_publish: `false`

\- auto\_publish\_mode: `disabled`



\## Publishing console result



Checked supplier-offer row `supplier\_offer:11`.



Result:



\- candidate\_key: `supplier\_offer:11`

\- kind: `supplier\_offer\_initial`

\- title: `Excursie Timisoara Cluj`

\- status: `already\_published`

\- badge: `already\_published`

\- summary: `Already published — not a candidate for first-time publish suggestion.`

\- next\_action\_code: `review\_conversion\_health`

\- next\_action\_label: `Review conversion health on review-package (avoid duplicate showcase without ops review).`

\- primary\_blocker: `Offer is already published.`

\- warning\_summary: `2 warning(s): content\_quality, publish\_safe`

\- gate\_summary: `6 passed · 3 failed · 2 warnings · 1 not applicable`

\- can\_suggest\_manual\_publish: `false`

\- can\_auto\_publish: `false`

\- auto\_publish\_mode: `disabled`



\## Safety confirmation



\- No POST requests were executed.

\- No Telegram publish/send/retry was executed.

\- No showcase channel post was created.

\- No publish attempt was created.

\- No scheduler/auto-publish was triggered.

\- No prepare\_conversion\_chain execution was triggered.

\- No order/payment/reservation/seat mutation was triggered.

\- No migration was involved.



\## Final status



Passed.


\# B15H — Read-only Publish Readiness Railway Smoke



\## Purpose



Verify that B15H read-only `publish\_readiness` metadata is visible on Railway production read models without public side effects.



\## Environment



\- Environment: Railway production

\- Commit tested: `30321e9`

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

\- lifecycle: `published`

\- prepare\_conversion\_chain\_plan\_status: `already\_prepared`

\- publish\_readiness.status: `already\_published`

\- publish\_readiness.can\_suggest\_manual\_publish: `false`

\- publish\_readiness.can\_auto\_publish: `false`

\- publish\_readiness.auto\_publish\_mode: `disabled`

\- gates\_passed\_count: `8`

\- gates\_failed\_count: `1`

\- gates\_warning\_count: `2`

\- prepare\_conversion\_chain\_plan\_path: `/admin/supplier-offers/12/prepare-conversion-chain/plan`



\## Publishing console result



Checked:



\- `GET /admin/publishing-console?kind=supplier\_offer\_initial`

\- total\_returned: `11`

\- row checked: `supplier\_offer:11`



Result:



\- candidate\_key: `supplier\_offer:11`

\- kind: `supplier\_offer\_initial`

\- title: `Excursie Timisoara Cluj`

\- review\_package\_path: `/admin/supplier-offers/11/review-package`

\- publish\_readiness.status: `already\_published`

\- publish\_readiness.can\_suggest\_manual\_publish: `false`

\- publish\_readiness.can\_auto\_publish: `false`

\- publish\_readiness.auto\_publish\_mode: `disabled`

\- gates\_passed\_count: `6`

\- gates\_failed\_count: `3`

\- gates\_warning\_count: `2`

\- prepare\_conversion\_chain\_plan\_path: `/admin/supplier-offers/11/prepare-conversion-chain/plan`



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


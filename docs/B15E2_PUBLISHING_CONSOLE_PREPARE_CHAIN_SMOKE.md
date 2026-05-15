\# B15E2 — Publishing Console prepare\_conversion\_chain smoke



\## Purpose



Verify the publishing console execution endpoint:



`POST /admin/publishing-console/supplier-offers/{offer\_id}/prepare-conversion-chain`



This is a smoke checklist and run log only.



\## Endpoint



`POST /admin/publishing-console/supplier-offers/{offer\_id}/prepare-conversion-chain`



\## Safe known offer



`offer\_id = 12`



Previous B16D2E smoke confirmed:



\- `bridge\_id = 3`

\- `tour\_id = 6`

\- `tour\_code = B10-SO12-04fb1f`

\- `execution\_link\_id = 5`

\- `plan\_status = already\_prepared`



\## Run log



| Field | Value |

|--------|--------|

| \*\*Environment\*\* | Railway production |

| \*\*Date/time (UTC)\*\* | 2026-05-15 08:53–08:55 UTC |

| \*\*Commit tested\*\* | `aa1dc8` |

| \*\*offer\_id\*\* | `12` |

| \*\*offer title\*\* | `Excursie Timisoara Oradea` |

| \*\*Endpoint tested\*\* | `POST /admin/publishing-console/supplier-offers/12/prepare-conversion-chain` |

| \*\*dry\_run idempotency\_key\*\* | `b15e2-smoke-dry-run-20260515115336` |

| \*\*live idempotency\_key\*\* | `b15e2-smoke-live-20260515115433` |

| \*\*Step 1 precheck\*\* | Review package confirmed `plan\_status=already\_prepared`, `blockers=0`, `prepare\_conversion\_chain\_action.enabled=true`, `bridge\_id=3`, `tour\_id=6`, `tour\_code=B10-SO12-04fb1f`, `tour\_status=open\_for\_sale`, `catalog\_listed\_for\_mini\_app=true`, `execution\_link\_id=5`. |

| \*\*Step 2 dry\_run\*\* | Passed. Response: `actor\_surface=publishing\_console`, `overall\_status=dry\_run\_preview`, `attempt\_id=null`, message: `Dry run: no audit rows or business mutations.` All steps were `skipped` with reason `already\_satisfied`. |

| \*\*Step 3 live execution\*\* | Passed. Response: `actor\_surface=publishing\_console`, `overall\_status=succeeded`, `attempt\_status=succeeded`, `attempt\_id=2`, `tour\_id=6`, `execution\_link\_id=5`, message: `All preparation steps already satisfied; no business mutations performed.` |

| \*\*Step 4 replay\*\* | Passed. Same live idempotency key returned `attempt\_id=2`; message: `Idempotent replay of a succeeded prepare\_conversion\_chain attempt.` |

| \*\*Step 5 post-read\*\* | Review package after live/replay confirmed `plan\_status=already\_prepared`, `blockers=0`, `bridge\_id=3`, `tour\_id=6`, `tour\_code=B10-SO12-04fb1f`, `tour\_status=open\_for\_sale`, `catalog\_listed\_for\_mini\_app=true`, `execution\_link\_id=5`, `ActionEnabled=true`. |

| \*\*Telegram I/O\*\* | None. No Telegram publish, send, retry, or showcase channel post was executed by this smoke. |

| \*\*Layer A mutations\*\* | None. No order, payment, reservation, or seat mutation was executed by this smoke. |

| \*\*Issues / warnings\*\* | None observed during B15E2 smoke. |



\*\*Final status:\*\* passed.


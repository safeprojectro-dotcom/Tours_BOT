# HANDOFF_B13G_FULL_CONVERSION_SMOKE_RESULT_TO_NEXT_STEP

## Status

**B13G full conversion smoke — completed and recorded (2026-05-10).** Evidence: **[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)** (second run log — Offer #12). Recording-only — **no** code, **no** tests, **no** API calls from documentation authoring.

## Checkpoint (before this smoke)

- **B13D–B13F:** migration **`20260531_29`**, publish attempts **`persisted`**, **`review-package`** includes **`showcase_publish_attempts_review`**.
- **B10.x chain:** supplier-offer bridge → tour → catalog listing → execution link contract available in admin/review surfaces.
- **Offer #11** (earlier B13G run log): **publish-audit path** validated; **execution link** not completed on that record (**past-tour / publish-audit-only** operator context).

## Facts recorded (production)

| Item | Value |
|------|--------|
| **Environment** | Railway **production**; Admin API + Telegram admin UI + Mini App manual checks |
| **Migration head** | **`20260531_29`** (already applied) |
| **Supplier offer** | **ID 12** — *Excursie Timisoara Oradea* — **`lifecycle`** **`published`** |
| **Publish path** | **Admin API** |
| **Showcase** | Telegram channel post **visible** |
| **Audit (`showcase_publish_attempts_review`)** | **`total_returned`** **1**; attempt **`id`** **2**; **`status`** **`persisted`**; **`provider`** **`telegram_showcase_channel`**; **`actor_surface`** / **`requested_by`** **`http_admin`**; **`showcase_chat_id`** **`-1003955096010`**; **`showcase_message_id`** **25**; **`error_code`** / **`error_message`** **null** |
| **`active_tour_bridge`** | Offer **12** → **`tour_id`** **6**, **`bridge_status`** **`active`**, **`bridge_kind`** **`created_new_tour`** |
| **`linked_tour_catalog`** | **`tour_code`** **`B10-SO12-04fb1f`**, **`tour_status`** **`open_for_sale`**, **`sales_mode`** **`per_seat`**, **`seats_available`** **10**, **`catalog_listed_for_mini_app`** **true** |
| **`execution_links_review`** | **`total_links_returned`** **1**; **`active_link.id`** **5**; offer **12**, tour **6**, **`link_status`** **`active`**; **`can_create_execution_link`** **false** (precheck: active link exists) |
| **`conversion_status_panel`** | **`showcase`**: published · **`tour_bridge`**: linked · **`catalog`**: listed_for_sale · **`booking_link`**: **active** · **`customer_action`**: **open_exact_mini_app_tour**, **`detail`** **`tour_code=B10-SO12-04fb1f`** |

## API / admin evidence (summary)

- **Publish audit:** single **`persisted`** attempt with showcase ids as in the table above — consistent with **B13E/B13F** expectations.
- **Bridge + catalog + execution link:** review surfaces aligned with **full conversion** — **Offer #12** linked to **Tour #6**, catalog **open_for_sale**, **execution link #5** **active**.

## Mini App evidence (manual)

- **Catalog** lists *Excursie Timisoara Oradea*.
- **Supplier offer landing** **`/supplier-offers/12`**: publication **published**, **availability** / **bookable** copy, CTA to **open linked trip** and continue booking.
- **Exact tour route** opens the same tour; **tour detail** shows **seats** and **price**.
- **Reservation preparation:** UI shows **tour is not available for reservation preparation** (or equivalent wording).

## What passed

- **B13** showcase publish + **audit persistence** for **Offer #12**.
- **Bridge** to **Tour #6**, **catalog** listing for Mini App, **`open_for_sale`** with **`per_seat`** and available seats.
- **Execution link #5** **active**; **`conversion_status_panel`** shows **`booking_link`**: **active** and customer action **open_exact_mini_app_tour**.

## Remaining gap (explicitly not B13 / not execution-link)

- **Reservation preparation** blocked at Layer A / Mini App readiness — **separate** diagnostic from **B13** publish audit or execution-link creation (both **passed** in this smoke).

## Recommended next step

1. **Scoped ticket:** **Tour #6** (**`B10-SO12-04fb1f`**) — trace **`MiniAppReservationPreparationService`** (and related tour readiness gates): sales window, deadlines, seat policy, and API contract vs catalog/detail surfaces.
2. **Do not** use this gap as justification for **retry/resend** showcase publish or for **mutating** execution links without a product/ops decision.

## Security reminder

**`ADMIN_API_TOKEN`** may have appeared in **manual smoke** screenshots, terminal history, or chat — **rotate** the token in **Railway** environment/config after smoke and distribute the new secret only through trusted channels. **Do not** paste tokens into docs or commits.

## Non-goals (this recording)

No app changes, no tests, no migrations, no production API calls from doc work, no publish, no execution-link or booking/payment/order/reservation mutations.

## References

- Runbook: **[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)** (Run log — full conversion Offer #12).
- Continuity: **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)** (B13G full conversion bullet).
- Tech debt / follow-up: **[`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md)** (Layer A reservation preparation vs **open_for_sale**).
- Prior publish-audit-only handoff (Offer #11): **[`docs/HANDOFF_B13G_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`](HANDOFF_B13G_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md)**.

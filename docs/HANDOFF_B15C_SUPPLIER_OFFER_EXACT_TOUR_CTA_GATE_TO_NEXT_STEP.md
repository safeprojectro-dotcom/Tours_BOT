# HANDOFF_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE_TO_NEXT_STEP

## Checkpoint

B15B is committed:

- `785acb9 feat: add read-only admin publishing console`

## B15C purpose

Change supplier-offer channel publication readiness so public publish happens only after the exact conversion target is ready.

New intended sequence:

1. packaging approved  
2. media/card approved  
3. moderation approved  
4. tour bridge exists  
5. tour `open_for_sale` / catalog-listed for Mini App  
6. active execution link exists  
7. showcase preview/payload uses exact tour CTA (`Rezervă` → `/tours/{tour_code}`)  
8. channel publish  

## Required customer behavior

For new supplier-offer channel posts:

- **Rezervă** must open the exact Mini App tour: `/tours/{tour_code}`  
- **Detalii** may remain: bot deep-link `/start=supoffer_{offer_id}` (and supplier-offer landing stays for older posts / fallback)

## Safety

Do not change Layer A booking/payment/reservation logic.

Do not publish from Cursor.

Do not mutate production data.

Do not edit old Telegram posts.

Supplier offer landing remains available for older links / fallback / details.

---

## What changed (implementation summary)

- **Execution link** can be created when the offer is **`approved`** (or **`published`**), **not only** after channel publish, provided packaging, bridge, tour, and Mini App catalog gates pass (**`app/services/supplier_offer_channel_publish_gate.py`**).
- **Channel publish** (`SupplierOfferModerationService.publish`) and **`can_publish_now` / `publish_showcase_channel`** require an **active execution link** that matches the bridge and a **catalog-listed**, **`open_for_sale`** tour with a **`tour_code`**.
- **Showcase CTAs:** **Rezervă** → **`{MINI_APP}/tours/{tour_code}`** when the gate passes; **Detalii** remains **`supoffer_<id>`**. **No** silent **`/supplier-offers/{id}`** fallback for required channel publish paths.

## Key files

- `app/services/supplier_offer_channel_publish_gate.py` — validation + bilingual publish gate messages + `tour_code_for_active_execution_link`.
- `app/services/supplier_offer_execution_link_service.py` — uses shared gate for link targets.
- `app/services/supplier_offer_showcase_message.py` — `rezerva_tour_code`, `channel_rezerva_requires_exact_tour`.
- `app/services/supplier_offer_moderation_service.py` — preview/publish exact-tour wiring.
- `app/services/supplier_offer_review_package_service.py` — pre-publish execution link readiness, recommended actions, `conversion_closure`.
- `app/services/supplier_offer_operator_workflow.py` — `publish_showcase_channel` disabled reason when execution link missing.

## Tests

- `tests/unit/test_supplier_offer_track3_moderation.py` — B15C helpers (`_ready_offer` includes included/excluded for bridge); publish after execution link; bridge supersede for replace-tour scenarios.
- `tests/unit/test_supplier_offer_catalog_conversion_closure.py` — execution link **before** publish; `next_missing_step` **`create_execution_link`** mid-chain.
- `tests/unit/test_admin_publishing_console.py` — B15B read-only console still passes.
- `tests/unit/test_supplier_offer_review_package.py` — publish blocked without execution link.

**Suggested:**

```bash
python -m pytest tests/unit/test_supplier_offer_track3_moderation.py tests/unit/test_supplier_offer_catalog_conversion_closure.py tests/unit/test_admin_publishing_console.py tests/unit/test_supplier_offer_review_package.py -q
```

## Documentation

- **Spec:** [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md)
- **Runbook:** [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)
- **B15B note:** [`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md)
- **Debt / roadmap:** [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) (B15 row)
- **Continuity:** [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)

## Production smoke

Use the checklist in **`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`** § Production smoke checklist (operator-run only).

## Known limitations

- No first-class HTTP API to **re-point** the tour bridge to another tour (tests may supersede bridge rows in DB); consider a future admin route if operators need this often.

## Expected next step after B15C

Manual production smoke after deploy using a new supplier offer, then record the result.

Possible next prompt (only after B15C is committed and smoke-tested):

`CURSOR_PROMPT_B15D_TOUR_PROMOTION_LAST_SEATS_DRAFTS.md`

Alternatively: tour promotion / **B15D** per [`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`](B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md) when product prioritizes.

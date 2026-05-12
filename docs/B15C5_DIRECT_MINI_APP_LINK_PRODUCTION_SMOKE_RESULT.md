# B15C5 — Direct Mini App short-name channel CTA — production smoke result

**Documentation only.** Operator-run validation after **`06741d`** (*fix: support direct Mini App short-name tour links*) with BotFather + Railway config applied.

## 1. Objective

Confirm that **new** supplier-offer channel **Rezervă** uses **`https://t.me/{bot}/{mini_app_short_name}?startapp=tour_{tour_code}`** when **`TELEGRAM_MINI_APP_SHORT_NAME`** is set, and that users get **one-tap** entry into the Mini App with **Telegram identity**, **exact tour**, and the existing **Layer A** reservation → temporary hold → payment-entry path (no booking/payment logic changes in B15C5).

## 2. Config confirmed (operator)

| Item | Value |
|------|--------|
| BotFather **Main Mini App** URL | `https://miniappui-production.up.railway.app` |
| Railway / API **`TELEGRAM_MINI_APP_SHORT_NAME`** | `banattours` |
| Example **Rezervă** URL shape (preview / publish) | `https://t.me/tours_tm_bot/banattours?startapp=tour_<tour_code>` |

**Related commits (context):** `06741d` (B15C5), `19f50da` (cover workflow guard), `17ddd4c` (channel tour CTA via Mini App), `37f213e` (exact-tour gate before publish).

## 3. API evidence table

| Field | Value |
|--------|--------|
| Supplier offer | **#15** |
| Offer title | *Test Direct Mini app link* |
| Tour | **#9** |
| Tour code | **`B10-SO15-460344`** |
| Execution link | **#8** |
| Publish attempt | **#6** |
| Telegram **`showcase_message_id`** | **28** |
| Showcase channel ref | **`-1003955096010`** |
| **`cta_rezerva_href`** (observed) | `https://t.me/tours_tm_bot/banattours?startapp=tour_B10-SO15-460344` |

### API status signals (post-publish, as reported)

| Signal | Reported value |
|--------|----------------|
| Showcase | `published` |
| Tour bridge | `linked` |
| Catalog | `listed_for_sale` |
| Booking link (execution) | `active` |
| Customer action | `open_exact_mini_app_tour` |
| **`showcase_publish_attempts_review.items[0].status`** | `persisted` |

## 4. Manual Telegram evidence

- Channel post **published** successfully (new publication; **no** edit of older messages).
- **Rezervă** opened the **Mini App directly** — **no** intermediate private-bot “open Mini App” launcher step on this path.
- No **red identity warning** in the Mini App for this session.

## 5. Mini App evidence

- **Exact tour** opened: **`B10-SO15-460344`**.
- **Telegram identity** recognized (reported: dev user **`5330304811`**).
- **Reservation preparation** completed successfully from the operator’s perspective.
- **Temporary hold / order** **#55** created — amount **100 RON**; **payment** screen opened; payment **pending / awaiting** (Layer A behavior unchanged by B15C5).

This validates: **channel direct short-name CTA → Mini App → exact tour → Layer A hold → payment entry**.

## 6. Safety notes

- **Existing** channel posts were **not** edited; validation used a **new** post only.
- **B15C5** changes **URL shaping** for **Rezervă** only; it does **not** change booking, payment, or reservation business logic (**Layer A** unchanged).
- **Identity** handling remains **fail-closed** where designed; this smoke did **not** show a bypass.
- **Order #55** is a **test** temporary hold from operator smoke; it should **expire naturally** unless paid or otherwise handled — optional support/admin cleanup after expiry.

## 7. Follow-up notes (non-blockers)

1. **`Detalii`** still uses the **informational** supplier-offer / bot deep-link behavior. Under B15C, **Rezervă** is the **exact conversion** CTA; a future polish may route **Detalii** to a Mini App landing/details route — **not required** for B15C5 **PASS**.
2. Optional **copy / translation** cleanup for generated Romanian showcase text and typos.
3. Optional **support/admin** hygiene for test order **#55** after expiry.

## 8. Conclusion

**B15C5 direct Mini App short-name channel CTA — PASS** (operator-recorded, **2026-05-09**).

## Related

- Gate / design: [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md)
- Earlier B15C smoke: [`docs/B15C_PRODUCTION_SMOKE_RESULT.md`](B15C_PRODUCTION_SMOKE_RESULT.md)
- Implementation handoff (pre-smoke): [`docs/HANDOFF_B15C5_DIRECT_MINI_APP_LINK_SHORT_NAME_TO_NEXT_STEP.md`](HANDOFF_B15C5_DIRECT_MINI_APP_LINK_SHORT_NAME_TO_NEXT_STEP.md)
- Post-smoke handoff: [`docs/HANDOFF_B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`](HANDOFF_B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md)

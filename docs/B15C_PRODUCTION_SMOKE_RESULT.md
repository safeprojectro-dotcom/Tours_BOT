# B15C — Production smoke result (documentation only)

## 1. Purpose

Record **operator-run** production validation that commit **`37f213e`** (*feat: require exact tour CTA before supplier offer publish*) behaves as intended: **execution link and exact tour target before channel publish**, channel **Rezervă** opens **`/tours/{tour_code}`**, and downstream Mini App tour/prep UX matches expectations up to documented follow-ups.

This document **does not** change code, data, or runtime behavior.

## 2. Commit under test

- **`37f213e`** — `feat: require exact tour CTA before supplier offer publish` (B15C).

## 3. Operator evidence table

| Field | Value |
|--------|--------|
| Supplier offer | **#13** |
| Offer title | *Excursie In Arad* |
| Tour | **#7** |
| Tour code | **`B10-SO13-e9f389`** |
| Execution link | **#6** |
| Publish attempt | **#3** |
| Telegram `showcase_message_id` | **26** |
| Showcase channel ref | **`-1003955096010`** |
| **`cta_rezerva_href`** (observed) | `https://miniappui-production.up.railway.app/tours/B10-SO13-e9f389` |

## 4. Exact sequence actually run (B15C ordering)

Operators followed the **new** flow (not “publish first, link later”):

1. Packaging / media-card / moderation approved (per product gates).  
2. Tour bridge created (**linked**).  
3. Tour activated for catalog (**listed / open for sale**).  
4. **Execution link created before channel publish.**  
5. Publish enabled only when exact target was valid.  
6. Channel post created; **Rezervă** used exact Mini App tour URL.

## 5. API PASS evidence (as reported)

Observed **`review-package`** / admin read model aligned with success:

| Signal | Reported value |
|--------|----------------|
| Showcase | `published` |
| Tour bridge | `linked` |
| Catalog | `listed_for_sale` |
| Booking link (execution) | `active` |
| Customer action | `open_exact_mini_app_tour` |
| Customer action detail | `tour_code=B10-SO13-e9f389` |
| **`showcase_publish_attempts_review.items[0].status`** | `persisted` |
| **`showcase_publish_attempts_review.items[0].showcase_message_id`** | **26** |
| **`execution_links_review.active_link.id`** | **6** |
| **`execution_links_review.active_link.tour_id`** | **7** |

## 6. Telegram / Mini App PASS evidence (as reported)

- Channel post **created** successfully.  
- **Rezervă** opened the **exact** Mini App tour: **`/tours/B10-SO13-e9f389`**.  
- Mini App showed: **Excursie In Arad**, **Open For Sale**, seats **15 / 15** left, **Reserve seats**, boarding **Timisoara**.  
- **Reservation preparation** screen: seat selector, boarding selector, and preview summary **visible** and usable **until** user-scoped actions hit the identity follow-up (§8.1).

## 7. Conclusion

- **B15C exact-tour CTA gate:** **PASS** — publish proceeded only with an active execution link and exact tour context; **`cta_rezerva_href`** pointed at **`/tours/B10-SO13-e9f389`**.  
- **Channel Rezervă:** **PASS** — opens exact Mini App tour route.  
- **Preparation UX:** **PASS up to identity-gated flows** — preparation UI rendered; completing reservation / My bookings / Settings from this entry path hit **Telegram identity/session** messaging (separate from B15C CTA correctness).

## 8. Follow-ups (out of B15C scope)

### 8.1 — Mini App identity / session (channel exact-tour entry)

When continuing into **user-scoped** flows after opening the Mini App from the **channel exact-tour** link, the app showed:

*Unable to verify your Telegram identity for this session. Reopen the Mini App from Telegram.*

Affected: reservation creation / final booking action, **My bookings**, **Settings**.  

**Not** a B15C CTA failure; exact tour opened correctly. Track under **B15C1** prompt (see handoff).

### 8.2 — Telegram admin navigation after **Leagă tur**

After **Leagă tur**, Telegram admin **moved to the next offer** in the moderation queue instead of **staying on the current offer** and surfacing the next step (**În catalog**).

**Backend** was reported correct (bridge existed, tour draft, **`activate_tour_for_catalog`** available in review-package). **UX** gap only. Track under **B15C2**.

### 8.3 — Stale wording post-B15C

Some review/conversion copy still says execution links are created **after** showcase publish. **B15C** requires **create execution link before channel publish** (bilingual / RO updates as needed). Track under **B15C3**.

## 9. Non-goals (this doc)

- **No** application code changes.  
- **No** test changes.  
- **No** production API calls from doc authoring.  
- **No** publish / retry / resend.  
- **No** production data mutation.  
- **No** new orders, payments, or reservations.  
- **No** Layer A semantic changes.  
- **No** migrations.

## Related

- Design / gate: [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md)  
- Handoff (implementation): [`docs/HANDOFF_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE_TO_NEXT_STEP.md`](HANDOFF_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE_TO_NEXT_STEP.md)  
- Smoke handoff: [`docs/HANDOFF_B15C_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`](HANDOFF_B15C_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md)

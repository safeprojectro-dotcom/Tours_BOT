# Handoff — B15C5 direct Mini App link — production smoke recorded

## Outcome

**B15C5** production smoke is **PASS** and recorded in **[`docs/B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md`](B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md)**.

**Summary:** With **`TELEGRAM_MINI_APP_SHORT_NAME=banattours`** and BotFather Mini App URL on **`https://miniappui-production.up.railway.app`**, Offer **#15** / Tour **`B10-SO15-460344`** / showcase message **#28** showed **Rezervă** → **direct Mini App** (no private-bot launcher), **no** identity warning, **exact tour**, reservation flow through temporary hold **#55** and payment screen.

## Next steps (optional / product)

- **Polish:** Decide whether **`Detalii`** should stay **bot/informational** or open a **Mini App** details/landing route (not required for B15C5).
- **Ops:** Romanian copy/typo cleanup on generated showcase text if desired.
- **Support:** After natural expiry, optional cleanup or annotation for test order **#55**.

## No further B15C5 code work implied

URL builder + env + tests shipped with **`06741d`**; this handoff closes the **documentation** loop for operator smoke.

## Related

- Pre-smoke implementation handoff: [`docs/HANDOFF_B15C5_DIRECT_MINI_APP_LINK_SHORT_NAME_TO_NEXT_STEP.md`](HANDOFF_B15C5_DIRECT_MINI_APP_LINK_SHORT_NAME_TO_NEXT_STEP.md)
- B15C baseline smoke (older offer): [`docs/B15C_PRODUCTION_SMOKE_RESULT.md`](B15C_PRODUCTION_SMOKE_RESULT.md)
- Exact-tour gate: [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md)

# B15C — Exact CTA chain closure checkpoint

**Project:** Tours_BOT. **Type:** documentation-only closure record.  
**Slice:** **B15C6** — consolidates the connected **B15C** work (exact tour **Rezervă**, execution link before publish, direct Mini App short-name links, cover guard, admin nav, copy alignment) into a single baseline before **B15D** or other roadmap forks.

**Handoff:** [`docs/HANDOFF_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT_TO_NEXT_STEP.md`](HANDOFF_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT_TO_NEXT_STEP.md).  
**Design gate:** [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md).

---

## 1. What B15C solved

- **Exact tour CTA before publish** — channel **Rezervă** must target the bookable Mini App tour (`tour_code`), not a generic supplier-offer landing, when the publish path requires it.
- **Execution link before publish** — **`can_publish_now`** / publish flow requires an active execution link aligned with the bridge and catalog-ready tour.
- **Direct Telegram Mini App short-name link** — **`t.me/{bot}/{short}?startapp=tour_{code}`** when short name is configured (**B15C5**); preserves WebApp / identity semantics for **Rezervă** from the channel.
- **Cover / photo sendability guard** — showcase cover replacement / publication modes guarded so operators cannot publish channel posts with inconsistent or unsendable media where gates apply.
- **Admin stays on offer after bridge/catalog actions** — Telegram admin queue FSM pins to the same supplier offer after **Leagă tur** / **În catalog** / related workflow actions (**B15C2**).
- **Misleading copy fixed** — review-package, conversion panel, and Telegram confirm strings no longer imply execution links are created *after* showcase publish (**B15C3**).

---

## 2. Final accepted conversion chain

1. Supplier offer **packaging** and **moderation** approved (per existing gates).
2. **Create/link tour bridge** (B10).
3. **Activate tour for catalog** (open for sale + Mini App catalog semantics).
4. **Create active execution link** (booking link) for the bridged tour.
5. **Publish showcase** to the public channel (HTTP or Telegram operator workflow).
6. Channel **Rezervă** opens the **exact** Mini App tour (direct **`startapp`** path where configured).
7. **Mini App** uses **Layer A** for reservation, payment, and operational truth (unchanged by B15C).

---

## 3. Production evidence (operator smoke)

Canonical detail: **[`docs/B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md`](B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md)**. Summary for this checkpoint:

| Item | Value |
|------|--------|
| Offer | **#15** |
| Tour | **#9** |
| Tour code | **`B10-SO15-460344`** |
| Execution link | **#8** |
| Publish attempt | **#6** |
| Showcase message | **#28** |
| CTA (example) | `https://t.me/tours_tm_bot/banattours?startapp=tour_B10-SO15-460344` |
| Temp hold / order | **#55** (operator test — payment screen opened; allow natural expiry or treat as test data) |

**Observed:** **Rezervă** opened the Mini App directly; **no** identity warning; Layer A behavior **unchanged**.

---

## 4. Safety boundaries preserved

- **No hidden bridge** — tour bridge remains explicit admin/API materialization.
- **No publish without exact conversion target** — when gates apply, missing execution link / mismatched bridge / missing **`tour_code`** blocks publish.
- **No supplier-side publish** — channel showcase publish stays on controlled admin/operator surfaces.
- **No Layer A changes** — booking, payments, reservation prep, and catalog rules were not rewritten for B15C.
- **No arbitrary identity trust** — channel HTML still cannot invent Telegram identity; WebApp / **`startapp`** paths follow existing bridge patterns.
- **No fake availability or urgency** — marketing copy and templates remain subject to existing approval and fact-lock policies; B15C does not auto-invent seats or dates.

---

## 5. Known follow-ups

- **Detalii** behavior — optional product decision whether **Detalii** (bot `supoffer_<id>` / landing) should evolve for older posts or stay as-is.
- **RO copy / typo cleanup** — ongoing bilingual polish outside this checkpoint.
- **B15D** — Admin Publishing Console: richer read-model and admin affordances; **no** auto-publish scheduler in scope unless explicitly chartered.
- **B12 / B13** — template and channel library evolution later.
- **B16** — Admin / OPS visibility slices later.
- **Order #55** — test reservation from smoke; **expire naturally** or **clean up** as test data per operator policy.

---

## 6. Next recommended step

**B15D — Admin Publishing Console:** deepen the **read-model** and **admin UX** (e.g. richer **`GET /admin/publishing-console`** surfaces, filters, links into review-package), with **no** automatic publish, **no** scheduler, and **no** trust expansion without an explicit product decision.

**Prompt (spec):** [`docs/CURSOR_PROMPT_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT.md`](CURSOR_PROMPT_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT.md).

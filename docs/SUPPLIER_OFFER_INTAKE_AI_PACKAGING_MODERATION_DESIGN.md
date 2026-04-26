# B1 — Supplier offer intake + AI packaging + moderation (design)

**Phase:** **B1** — **design only**. **No** implementation, **no** migrations, **no** new routes in this document.

**Parent roadmap:** [`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) (BUSINESS **B1–B13**).

**Aligns with:** `docs/AI_ASSISTANT_SPEC.md` (no inventing commercial facts; draft-only in admin contexts), `docs/AI_DIALOG_FLOWS.md` (stepwise patterns), `docs/MINI_APP_UX.md` (catalog/tour are customer truth surfaces), `docs/TECH_SPEC_TOURS_BOT.md` / `v1.1` (product layering). Current codebase uses `SupplierOfferLifecycle` (`draft`, `ready_for_moderation`, `approved`, `rejected`, `published`)—this design introduces **additional logical states** for **packaging** and **tour link**; **B2** is expected to map them to storage/enums.

---

## 1. Business principle

| Principle | Description |
|------------|-------------|
| **Raw facts from supplier** | The supplier (or operator on their behalf) enters **structured facts**: dates, prices, capacity, inclusions, text notes, media pointers—not marketing copy as the source of truth. |
| **AI creates draft packaging** | After facts pass minimum completeness, a **packaging** step produces **draft** copy and layout hints for Telegram + Mini App. |
| **Admin reviews, edits, approves** | Platform **admin** (or product-defined **moderator** role) reviews **raw** + **AI draft**, may edit, **regenerate** with constraints, or **send back** for supplier clarification. |
| **Only an approved package may be published** | No public channel post and no “customer-visible” packaging without **explicit admin approval** of the **package** (not merely “approve supplier text blind”). |
| **Tour attachment is explicit and later** | A **published** supplier offer **later** becomes or attaches to a **Tour** in the Mini App catalog **via B9/B10 bridge**—see **§6** and [`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) **§1**. B1 does **not** create **Tour** rows. |

---

## 2. Supplier intake data requirements

### 2.1 Required fields (minimum for “complete intake” / `ready_for_moderation` eligibility)

Product may tighten this list; implementation tickets must **fail-closed** if required data is missing.

- **Identifier context:** which **supplier** (already bound in bot context after onboarding).
- **Route / product title (working title)** — short internal name (may differ from final marketing title).
- **Departure** — at least one **concrete** departure window or **explicit** “on request / TBD” per policy (must not be invented by AI).
- **Base commercial facts:** **price** (and **currency**), **capacity / seats** (or **full-bus** equivalent label), **sales/payment mode** intent (map to existing `SupplierOfferPaymentMode` or successor).
- **Program outline** — structured bullets or form sections (stops, duration), minimum length/quality as policy defines.
- **Inclusions** and **exclusions** — at least one side with explicit content, or a declared “none / standard package” per template.
- **One** **primary** **contact** path for the supplier (e.g. Telegram user id already known + optional phone/email policy).

### 2.2 Optional fields

- Boarding / pickup **locations** (map to future `BoardingPoint` only when bridge exists).
- **Child** / **discount** **rules** (text + structured hints).
- **Equipment** / **luggage** / **accessibility** notes.
- **Language** of the tour, **group type** (public/private), **insurance** mentions (non-legal where required).
- **Internal supplier notes** (customer-invisible) — see **§2.8**.

### 2.3 Photo / media requirements

- **Minimum count** and **max size** per policy (e.g. ≥1 **hero** image for packaging).
- **Formats** (JPEG/WEBP) and **aspect ratio** hints for **Telegram** vs **card** template (**B6**/**B7**).
- **No** **auto**-publish of unmoderated **external** URLs without fetch/moderation policy (**B7**).

### 2.4 Program requirements

- **Day-by-day** or **stage** blocks (title + short text).
- **Meals** (included / not) as structured flags where possible.
- **Optional** **attachment** of itinerary PDF/Doc **reference** (storage id—**B2**).

### 2.5 Included / excluded

- Distinct text blocks: **`included_text`**, **`excluded_text`** (source for AI; AI must not contradict without flagging).
- For **gifts** / **promo** items, separate **optional** **structured** list with **validity** dates if supplier supplies them.

### 2.6 Price / currency

- **Amount**, **currency** (ISO), **per seat** vs **per bus** as applicable.
- **Tax / VAT** **disclaimer** text if supplier provides; **not** invented by AI.

### 2.7 Capacity / seats

- **Seats** **total** and/or **per departure**; **waitlist** intent if supported later.
- **AI** rephrases but **may not** change numeric **facts**.

### 2.8 Dates or recurrence

- **Single** departure: date/time + timezone policy.
- **Recurring** / **series:** supplier declares pattern (e.g. “every Saturday in July”) as **raw**; normalization is **B8**-heavy—B1 may store **raw** string + parse attempts with **quality warnings** (see **§4**).

### 2.9 Discount / promo fields

- **Code**, **percent**, **validity** window—**optional**; must be **supplier-provided** or **empty**.

### 2.10 Supplier contact / admin-only notes

- **Supplier-facing** support line vs **admin-only** ops notes (fraud, risk, “do not promote”).
- **Admin-only** fields **must not** be shown to the supplier in **Telegram** preview copy by default.

---

## 3. Supplier dialog structure (Telegram)

### 3.1 Step-by-step, one question at a time

- **Linear** or **small-branching** FSM: each step **one** main question (with **Back** / **Save draft** as already supported in Y2.2a spirit).
- **Progress** indicator (e.g. step *k* / *N*) to reduce drop-off.
- **Summary** screen **before** submit to `ready_for_moderation` with **edit** per section.

### 3.2 Validation and missing fields

- **Inline** validation (format, min/max, required).
- If blocked: show **which** field, **example** of valid input, and **do not** call **AI packaging** until **minimum** **B1** completeness is met (or call with explicit **degraded** mode + **quality warnings** only—product choice in **B4**).
- **Server-side** validation remains authoritative (bot is not trusted for business truth).

### 3.3 `ready_for_moderation` criteria

The offer may transition to **`ready_for_moderation`** (see current `SupplierOfferLifecycle` / **B2** mapping) when:

- All **required** fields in **§2.1** pass validation.
- **Media** minimums in **§2.3** satisfied (or explicit waiver flag if product allows with warning).
- Supplier **explicitly confirms** the review summary (no accidental submit).

**Note:** B1’s extended status model (§6) may split “submitted to platform” from “packaging job finished”—see **§6**.

---

## 4. AI packaging output (draft contract)

All outputs are **proposals** until **admin** approves. Suggested DTO shape (logical):

| Output | Description |
|--------|-------------|
| **Telegram post draft** | Full message text for channel (markdown/HTML per channel policy), with placeholders for **links**. |
| **Short hook** | 1–2 lines for feed/card glance. |
| **Brief program** | Condensed program for Telegram length limits. |
| **Mini App `short_description`** | Scannable text for list/card. |
| **Mini App `full_description`** | Long-form for detail page. |
| **Normalized `program_text`** | Cleaned, sectioned program matching template. |
| **`included_text` / `excluded_text`** | Polished, **aligned** to supplier **facts**; contradictions → **quality warnings** (see below). |
| **CTA variants** | 2+ candidate CTAs (book / ask / call) for admin to pick. |
| **Image/card prompt or layout data** | Prompt or **structured** **layout** JSON for **B7** (not a binary image in B1 spec unless product chooses). |
| **Quality warnings** | List: ambiguous dates, **missing** **hero** **image**, weak inclusion list, **language** **inconsistency**, **price** **format** risk, **discrimination** of legal claims. |
| **Missing fields** | Explicit list of missing optional fields (for admin to chase supplier). |

**Hard rule:** the packaging step **receives** **grounding** (supplier field snapshot). **No** **invention** of **dates**/**prices**/**seats**; if a field is null, the AI outputs **TBD/ask** or leaves placeholder **and** a **quality warning**—**never** silent fabrication.

---

## 5. Admin moderation flow

| Step | Description |
|------|-------------|
| **Raw supplier data** | Read-only view of **structured** **intake** as entered (with audit timestamps / version if **B2** adds revisioning). |
| **AI draft** | View of **§4** outputs; diff vs raw where useful. |
| **Telegram preview** | Renders as close as possible to public channel (length, **links**, **escaping**). |
| **Mini App preview** | List + detail **mock** (not live publish). |
| **Photo/card preview** | If **B7** provides assets, show in context. |
| **Approve package** | Freezes **approved** **copy** and **selects** CTA/variant; may set lifecycle toward **`approved_for_publish`** (see **§6**). |
| **Edit package** | Admin overwrites any draft field; **source** of truth after edit is **admin-edited** text, still **traceable** to **AI** **version** id if **B2** stores generations. |
| **Regenerate** | Re-run **AI** with same **or** **edited** **grounding**; **regeneration** is **idempotent** at **semantic** level only if keyed by `generation_id` (implementation detail in **B4**). |
| **Request supplier clarification** | Reverts or holds offer in a **returned** state; supplier receives **templated** message listing **gaps** (no raw admin insults; professional tone). |
| **Reject** | **Reject** with **reason** (supplier-visible), lifecycle **`rejected`** (existing pattern). |

**Separation:** **approving the package** is **not** the same as **publishing to Telegram** or **creating a Tour**; those are separate explicit actions (Track **3**-style + **B9/10**).

---

## 6. Status model (B1 — logical; storage mapping in B2)

B1 needs finer granularity than the current `SupplierOfferLifecycle` enum. Treat these as **logical** states; **B2** maps to **DB** (new enum values, or parallel **packaging** **state** column).

| State | Meaning |
|-------|--------|
| **draft** | Intake in progress. |
| **ready_for_moderation** | Supplier submitted; passes **§3.3**; queued for or awaiting **packaging** / **moderation** entry. |
| **packaging_pending** | Job accepted: **AI** **or** **human** **template** **fill** in progress. |
| **packaging_generated** | **§4** outputs exist for admin review. |
| **needs_admin_review** | Human must decide (e.g. **quality** **warnings** **high**, or first-time supplier). |
| **approved_for_publish** | **Package** (possibly admin-edited) **approved**; still **not** **public** until **publish** action. |
| **published** | **Public** **Telegram** (and any **list** **surfaces** **defined** in **B5** / Track **3**). |
| **linked_to_tour** | **B9/10** **bridge** **created** a **definitive** **link** `supplier_offer` → `tour`. |
| **visible_in_catalog** | **Tour** **appears** in Mini App **catalog** **per** **visibility** **rules** (may depend on `TourStatus`, time windows). |
| **bookable** / **not_bookable** | **Derived** from Layer A + **tour** **actionability** (not a second lifecycle; **align** Y30.2 / Phase **7.1** **actionability** patterns). **May** be **cached** **flags** for UX. |

**Not bookable** examples: no seats, tour **passed**, **suspended** supplier, **link** **inactive**.

---

## 7. Guardrails

| Guardrail | Rule |
|-----------|------|
| **AI is draft-only** | No direct **publish**, **no** **customer** **notification** **of** **false** **facts**. |
| **No invented commercial facts** | **Dates, prices, seats,** **currency,** and **inclusions** must come from **grounding**; otherwise **TBD** + **warning**. |
| **AI does not publish** | **Publish** is **admin** (or product-defined) **only**. |
| **No bookings/orders/payments** | B1 does **not** call booking **prepare**, **hold**, **order**, or **payment** APIs. |
| **No silent Tour** | **Tour** **creation** / **link** = **B9/10** **only**. |
| **Admin approval** | Required before **any** **customer-facing** “official” **packaged** **content** is **used** in **public** **surfaces** as **authoritative** (draft previews may be **admin**-only). |
| **Layer A unchanged** | **Booking/payment** **semantics** **unchanged**; **B1** is **strictly** **supplier** **offer** **+** **moderation** **+** **draft** **AI** (see `TRACK_0` / operator gates). |

---

## 8. Next steps (after B1 design acceptance)

| Next | Description |
|------|-------------|
| **B2** | **Supplier offer content / data upgrade** — persist **B1** fields, **packaging** **versions**, **state** **machine** mapping. **← Next safe implementation-design step.** |
| **B3** | Supplier **dialog** upgrade in Telegram (step order, i18n, error UX). |
| **B4** | **AI packaging** **service** contract + safety filters + idempotent generation. |
| **B5** | **Admin** **UI** for moderation (may split **API** / **Telegram** **admin** **surfaces**). |
| **B9** | **Offer** → **tour** **bridge** design (publication to **catalog** **truth**). |

---

## 9. Summary

| Area | B1 design stance |
|------|------------------|
| **Principle** | Raw **facts** → **AI** **draft** **packaging** → **admin** **approval** → **publish**; **tour** **link** **explicit** **later**. |
| **Data** | **§2** field catalog for **B2** schema work. |
| **Dialog** | **One**-question-**at**-**a**-**time** + **ready_for_moderation** **criteria** **§3**. |
| **AI** | **Output** **contract** **§4**; **grounded**, **no** **invention** **§7**. |
| **Moderation** | **End-to-end** **flow** **§5**. |
| **Status** | **Logical** **states** **§6**; **B2** **maps** to **persistence**. |
| **Next** | **B2** **—** **content/data** **upgrade**. |

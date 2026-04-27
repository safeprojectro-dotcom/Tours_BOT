# Supplier offer — photo moderation & card generation (B7 design)

**Status:** design only (B7).  
**Scope:** This document does **not** add migrations, `app/` code, Telegram `getFile` calls, image downloads, image generation, or publication. It is the rulebook for **B7.1+** implementation.

**Relationship to B6:** [B6](HANDOFF_B6_BRANDED_TELEGRAM_POST_CARD_TEMPLATE.md) adds deterministic `branded_telegram_preview` inside `packaging_draft_json` (title, cover ref, `card_lines`, `caption`, `warnings`, etc.). B7 takes the **next step**: **human** review of the **actual image** (or explicit fallback) and, later, **card asset** production — still under admin control and without automatic public publish.

---

## 1. Photo states (lifecycle)

These states refer to the **primary cover / hero** used for a branded social card, not the entire supplier-offer lifecycle. One offer has at most one **active** cover workflow path at a time; terminal rejections may require a new upload (new `raw_uploaded` or replacement).

| State | Meaning |
|--------|---------|
| **raw_uploaded** | Supplier (or system) has attached a media reference: Telegram photo file id, URL, or other ref. **Not** yet accepted for any customer-facing or channel use. |
| **needs_admin_visual_review** | A human must open and judge the image (or confirm fallback is acceptable). Default when new media appears or `telegram_photo` cannot be published as a URL. |
| **approved_for_card** | Admin accepts this image (or a hosted derivative **after** a future B7.3 “publish-safe” step) as the **source** to **compose** a card. Does **not** mean the card is generated or the offer is published. |
| **rejected_bad_quality** | Too low resolution, illegible, unusable in layout — supplier should replace. |
| **rejected_irrelevant** | Image does not match the tour/vehicle/destination (or is misleading). |
| **fallback_card_required** | No usable supplier image; the pipeline must use a **template-only** or **brand** background (no **invented** tour-specific scene). B6 can already flag `fallback_branded_card_needed` when there is no cover. |
| **card_generated** | A render step produced a card image (bitmap or file handle) from approved facts + design template. **Not** public until separately approved. |
| **card_approved** | Admin approved the **generated** card asset for **later** use (e.g. channel publish, Mini App, bridge). **Still** not an automatic public publish. |

**Recommended transitions (high level):**

- `raw_uploaded` → `needs_admin_visual_review` (automatic when intake stores media).
- `needs_admin_visual_review` → `approved_for_card` | `rejected_*` | `fallback_card_required` (admin).
- `fallback_card_required` → (after generation) `card_generated` when only template/background is used — **or** a new `raw_uploaded` if supplier later supplies an image.
- `approved_for_card` → `card_generated` (implementation: B7.2+).
- `card_generated` → `card_approved` (admin) **or** back to a prior state if a new cover replaces the design input.

**Note:** Reuse or align naming with B6’s `branded_telegram_preview.cover.status` where helpful (`needs_admin_visual_review` is already aligned in spirit).

---

## 2. Media source rules

- **`telegram_photo:` + file_id** (see `SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX`) is a **bot-internal** handle. It is **not** a public URL and **not** directly usable in web or some channel APIs. Any **public** or **re-host** path (future B7.3) requires either:
  - sending via Telegram with `file_id` in allowed contexts, **or**
  - **downloading** (via `getFile` + HTTP) and storing in a **-controlled** object store with a stable URL, under explicit security and policy.
- **HTTP(S) URLs** may be slightly easier to preview in a browser but are **not** “trusted for publish” without the same **admin visual** review: hotlinking, expiring links, and copyright issues are still possible.
- **Principle:** **No** supplier media is **trusted** for public or “representative of the product” use **without** `needs_admin_visual_review` and an explicit allow transition to `approved_for_card` (or a deliberate `fallback_branded_card_needed` / `fallback_card_required` path).

---

## 3. Quality rules (admin checklist)

All are **human-judged** in B7.x unless/until a future automated pre-check is explicitly scoped (not B7 design-only).

- **Resolution / sharpness:** Minimum bar TBD in implementation (e.g. long edge in px); below bar → `rejected_bad_quality` or “replace” request.
- **Relevance:** Image should plausibly relate to the **declared** route/destination, vehicle, or experience — not random stock, competitor tours, or unrelated geographies → `rejected_irrelevant` or clarification.
- **Non-misleading:** Must not show dates, prices, or seat counts in the **image** that **contradict** grounded `supplier_offers` / packaging facts. If the image embeds false numbers, treat as `rejected_irrelevant` or require new asset.
- **IP / watermarks:** Obvious **third-party** or **competitor** watermarks, unlicensed art, or scraped promotional images → reject or require replacement. (Automated detection is out of B7 design scope.)
- **Safety / appropriateness:** No unsafe, hateful, or adult content; standard moderation expectations.

---

## 4. Card generation model (B7+ implementation)

**Design only:** future B7.2 may render a **branded** card (e.g. **16:9** channel post or **4:5** story-style), driven only by **grounded** fields:

- **Title** — from offer title (locale stays supplier’s / existing packaging rules; **no** invented destination).
- **Date** — from `departure_datetime` / `return_datetime` (formatted as in B4/B6, no raw ISO in customer-facing layer).
- **Route** — from same sourcing as B6 `branded_telegram_preview` route line (e.g. `format_route_for_telegram` inputs).
- **Price** — from grounded price + `sales_mode` (full bus vs per seat) — **no** invented discount or “last seats” language.
- **Vehicle / capacity** — from `vehicle_label` / `seats_total` with the same “not live availability” rules as B4.3.
- **Visual** — **either** `approved_for_card` **supplier** media (or B7.3-prepared byte blob) **or** **fallback** background + **brand** mark; template must **not** invent **facts** (no fake place names, no fake prices in artwork).

**Brand mark:** Platform logo / wordmark as configured (implementation: asset path or URL in config, not in this design file).

**Output:** A **new** file or attachment record points to `card_generated`; it must pass **`card_approved`** before any publish/bridge step consumes it.

---

## 5. Admin flow

1. **Review photo** — Open the actual media (in-client preview or, for `file_id`, future bot-rendered preview after explicit implementation; **B7.1** may start with metadata + “seen” only).
2. **Approve for card** — Transition to `approved_for_card` (image is allowed as input to the card renderer or to B7.3 re-hosting).
3. **Reject (quality / relevance)** — `rejected_bad_quality` or `rejected_irrelevant` with a **short internal reason** (supplier may get a **separate** message in a later slice — not implied by B7 design only).
4. **Request replacement** — Same as reject + state that blocks card generation until a new `raw_uploaded` appears.
5. **Use fallback branded card** — If no image is approved, set / confirm `fallback_card_required` and generate a **template-only** or solid + typography card using **grounded** text only.
6. **Approve generated card** — After `card_generated`, admin reviews the **pixel** result and sets `card_approved` before any downstream “publish this asset” feature.

**Ordering:** **Packaging text approval (B5)** and **branded JSON preview (B6)** are orthogonal but should both be “ready” before any **public** channel post that uses the card; B7 does not change B5’s “approve package ≠ publish” rule.

---

## 6. Data model options

### Minimal (short term)

- Continue storing **per-offer** cover in `supplier_offers.cover_media_reference` and optional `media_references` JSON; extend **`packaging_draft_json`** (e.g. under a `b7_moderation` or `card_pipeline` key) with:
  - photo state, reviewer id, timestamps, reasons, and references to any generated file paths or attachment ids.
- **Pros:** No migration in B7.1; fast to implement; aligns with B6.
- **Cons:** Harder to query “all offers awaiting photo review,” harder to support **multiple** assets per offer (gallery), weaker audit history.

### Better (later)

- Dedicated **`supplier_offer_media`** (or `supplier_offer_cover_attachements`) table: `supplier_offer_id`, `kind` (cover, gallery, generated_card), `source` (telegram, url, generated), `storage_ref`, `moderation_state`, `reviewed_by`, `reviewed_at`, `rejection_code`, `created_at`, etc.
- **Pros:** Clean audit, list screens, future multi-image, and separation from copy/packaging JSON.
- **Cons:** Migration + more CRUD; should be introduced when B7.1 scope includes listing/filtering in admin API.

**Recommendation:** Implement **B7.1** with **JSON extension + existing columns** where possible; plan **`supplier_offer_media` for B7.2+** if multiple files or strong audit is needed before public launch.

---

## 7. Safety invariants (must hold in code)

- **No automatic public** Telegram channel post, **no** `Tour` creation, **no** Mini App catalog mutation, **no** booking/order/payment change as a result of **card** generation or media approval.
- **Generated** card (`card_generated`) **always** goes through **admin** **`card_approved`** (or a named equivalent) before use in a publish pipeline.
- **No customer notification** from B7.x actions alone.
- **No** change to B5/B6 **copy** truth rules: card pixels must not introduce **new** commercial facts.

---

## 8. Next implementation slices

| Slice | Content |
|--------|--------|
| **B7.1** | Persist **media review metadata** (state, reviewer, reason, timestamps) in the chosen store; **admin API** to transition states (approve for card, reject, request replacement, set fallback) **without** `getFile` or image bytes if product chooses. |
| **B7.2** | **Card rendering preview** (local or server): layout engine + 16:9/4:5 output; may still be staff-only; **no** public publish. |
| **B7.3** | **Publish-safe media (implementation)** — optional download, virus/size checks, object storage, stable URL or Telegram re-upload; still **no** automatic customer-facing publish. **Policy** for what “publish-safe” means and what is **not** implemented yet: see **B7.3A decision log** below. |

(B9/B10 **offer → Tour** bridge and channel publish are **separate** tracks; B7 only prepares **assets** and **governance**.)

---

## B7.3A decision log (policy acceptance, docs-only)

**Status:** accepted as **project policy** (no `app/` changes in B7.3A). **Next** implementation may be **B7.3B** (metadata-only `publish_safe` stub in `packaging_draft_json`) or a **future** explicit slice for storage / `getFile` / rendering.

| Slice | Role |
|--------|------|
| **B7.1** | Media review **metadata** (`packaging_draft_json.media_review`); admin transitions; **no** bytes. |
| **B7.2** | Card render **preview plan** (structured JSON); **no** real pixels. |
| **B7.3A** | **Accepted policy only:** raw supplier media is **not** publish-safe; Telegram `file_id` / `telegram_photo:{file_id}` is **not** a stable public URL; **no** `getFile` / download / durable storage / real rendering / Telegram send in this step; **no** Railway local FS as canonical store; **metadata-first** MVP (`cover_media_reference`, `media_references`, `media_review`, B7.2 JSON); **approved_for_card** ≠ **publish_safe**; **publish_safe** ≠ **published**; publication remains **separate** explicit admin action; **no** auto-publish from media approval. |
| **B7.3B** (optional) | Metadata-only `publish_safe` **stub**; still **no** download. |
| **B7.4+** (future) | Real storage, download, rendering, publication wiring — **only** after **explicit** prompt and scope. |

**Concept separation:** **raw_received** (intake) → **approved_for_card** (B7.1) → **publish_safe** (durable asset, when built) → **published** (e.g. channel/showcase; **not** automatic from prior steps).

---

## Document history

- **2026-04-25:** B7 design gate — initial version (no code).
- **2026 (B7.3A):** Policy acceptance log added; **B7.3** implementation still **not** started beyond existing B7.1/B7.2.

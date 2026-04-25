# Admin/Ops Customer Summary Layer (Design Gate)

**Phase:** Y35.4 (docs-only)  
**Depends on:** Y35.1 (visibility gate), Y35.2 (admin API read slice), Y35.3 (Telegram admin read UI) — accepted.

This gate designs a **safe customer summary** for admin/operator read surfaces. It does **not** add routes, handlers, schema fields, migrations, or runtime behavior. Implementation must be a **separate** explicitly scoped runtime slice.

---

## 1. Current state

- **Admin API (read-only):** `GET /admin/orders`, `GET /admin/orders/{id}`, `GET /admin/custom-requests`, `GET /admin/custom-requests/{id}` return operational booking/request data. Customer identity is currently anchored on **`customer_telegram_user_id`** (and related order/request fields) populated from the linked **`User`** row where available.
- **Telegram admin UI:** `/admin_orders`, `/admin_requests`, and offer-detail entry buttons show list and detail views. Customer-facing lines in messages use the raw numeric **Telegram user id** (e.g. `5330304811`) as the main human cue.
- **Customer Mini App:** `My bookings` and `My requests` remain **strictly user-scoped**; this design does not change that model.
- **Gaps:** Profile-adjacent fields already persisted on `users` (**`username`**, **`first_name`**, **`last_name`**, optional **`phone`**) are not yet surfaced as a coherent **operator-facing summary** on admin/ops read APIs or Telegram.

---

## 2. Why raw `telegram_user_id` is not enough

- **Cognitive load:** Long numeric ids are hard to read, compare aloud, and match to support tickets or Telegram chats.
- **Operational matching:** Operators often think in **display names** and **@username** when correlating a booking with a private Telegram thread or a forwarded message.
- **Stability of cue:** A single number does not signal whether the account has a **public username**, a **name-only** profile, or **no usable profile string**; operators cannot tell without opening another tool.
- **Acceptable for dev, weak for production ops:** The numeric id remains the **authoritative join key** and must stay available; it should not be the **only** human-oriented field when safer alternatives exist in the same `User` row.

---

## 3. Safe customer summary fields

The summary is for **labeling and support correlation**, not for a new PII product surface.

| Field | Role | Notes |
|--------|------|--------|
| **display_name** | Primary line | Derived only from existing stored name parts (see section 4). **Omit or null** if no non-empty, bounded-safe combination exists — **fail closed**, do not fabricate. |
| **username** | Secondary line | Telegram @handle without `@` in storage; present as `@username` in UI when non-null. |
| **telegram_user_id** | Fallback / join key | Always retain for machines and deep correlation; format `tg:{id}` in display templates when used as the human-primary line. |
| **phone** | Optional, strict | Only if **already stored** on `User` in DB **and** product policy explicitly treats it as showable to central admin/ops in this context. If policy is not yet explicit, first runtime slice should **omit phone** or gate behind a single explicit “admin may see stored phone for support” decision documented alongside implementation. **Never** pull phone from Telegram API at runtime. |

**Out of scope for this gate (do not add without a new design):**

- Email, address, document ids, payment instrument details.
- “Rich” contact resolution via Telegram Bot API `getChat` in hot paths.
- New profile fields, new consent flows, or new storage solely for admin display.

---

## 4. Data sources already available (no new external sources)

All candidates come from the existing **`User`** model (table `users`), reachable via `Order.user_id` / `Order.user` and `CustomMarketplaceRequest.user_id` / `CustomMarketplaceRequest.user` (already loaded on admin list/detail paths in Y35.2).

| Source column | Use |
|---------------|-----|
| `telegram_user_id` | Canonical id; used in `tg:{id}` fallback and for any future admin-only search/filter that is explicitly approved. |
| `username` | Secondary `@username` when not null/empty. |
| `first_name`, `last_name` | **display_name** candidates (see section 5). |
| `phone` | Optional summary segment **only** under section 3 rules. |
| `preferred_language`, `home_city`, `source_channel` | **Not** part of the first customer summary string unless a later gate extends scope; they are not required for the core Y35.4 operator UX goal. |

**Identity bridge / Mini App:** No changes; no new identity rules. Admin reads **server-side `User`**, not client-supplied unauthenticated labels.

---

## 5. Fallback display rules

**display_name (derived, bounded):**

1. If `first_name` and `last_name` are both non-empty (after trim), use `"{first_name} {last_name}"` (single internal space; collapse duplicate spaces if needed).
2. Else if `first_name` is non-empty, use `first_name`.
3. Else if `last_name` is non-empty, use `last_name`.
4. Else **no display_name** (null/absent) — do not use placeholder text like “Unknown” in API fields; UIs may apply a **template-level** `tg:{id}` only as the visible primary line (see below).

**Human-visible single-line summary (recommended default):**

1. **Primary:** `display_name` if present.  
2. **Else primary:** `tg:{telegram_user_id}`.  
3. **Secondary (when present and distinct):** `@username` (if `username` is set).  
4. **Optional:** `phone` only when allowed by section 3 (typically on **detail** more than list rows).

**List vs detail:**

- **List rows:** Keep compact: primary + optional short secondary (e.g. truncating long names) + avoid duplicating the full id if `tg:` is already primary.  
- **Detail:** May show `telegram_user_id` on its own line for copy/paste, plus structured fields if API exposes a small `customer` object (section 7).

**Sanitization:**

- Trim whitespace; cap display string length for Telegram messages to avoid message overflow (reuse existing truncation patterns from admin ops UI).  
- Do not echo unsanitized control characters; optional ASCII-focused strip for message safety.

---

## 6. Privacy and security boundaries

- **Scope:** **Admin/ops authenticated surfaces only** (same `ADMIN_API_TOKEN` / same Telegram allowlist as Y35.2/Y35.3).  
- **Customer Mini App:** Unchanged; no new cross-user or elevated endpoints for customers.  
- **No sensitive data expansion:** Do not add fields that are not already persisted, except pure derivations (e.g. `display_name` string) from existing columns.  
- **Fail closed:** If `User` is missing or not joinable, expose **`customer_telegram_user_id` as null** (existing behavior) and summary fields **absent**; never invent profile data.  
- **Phone:** If implementation cannot confirm an explicit “stored phone is OK for central admin” policy, **leave phone out** of v1.  
- **No identity bridge changes** and **no execution-link** changes.  
- **No booking/payment** semantic changes.  
- **Supplier-scoped** surfaces must **not** gain this summary unless a separate gate extends supplier read models (out of Y35.4 scope).

---

## 7. Admin API representation

**Approach (recommended):** Add a small, reusable embedded object, e.g. `customer_summary`, to list and detail read models for **orders** and **custom requests** (both list items and detail where applicable), rather than overloading a single opaque string in the API.

**Suggested shape (illustrative — actual names follow project conventions):**

- `display_name: string | null`
- `username: string | null` (raw storage form without `@`; clients format `@` for display)
- `telegram_user_id: int | null` (duplicate allowed for clarity next to summary; or rely on existing `customer_telegram_user_id` — avoid redundant conflicting fields; **migration not required** if only computed fields are added to response DTOs)
- `phone: string | null` — **optional slice**; omit entirely from v1 if policy not explicit
- `summary_line: string | null` — **optional** convenience: server-computed string following section 5 for clients that only need one line (must be deterministic from the same fields)

**Backward compatibility:** Existing `customer_telegram_user_id` field stays; new fields are **additive**. Older clients can ignore new keys.

**Authorization:** Unchanged; same admin token and route guards as current `/admin/orders` and `/admin/custom-requests`.

---

## 8. Telegram UI representation

- **List rows (orders / requests):** Replace or augment the bare numeric customer id only snippet with: **primary = display_name or `tg:{id}`**, and **@username** on the same or next line if present and not redundant.  
- **Detail views:** Show structured lines, e.g. `Name: …`, `Username: @…`, `Telegram: …` (numeric id and/or `tg:` as needed for support). Optional phone only if API exposes it and policy allows.  
- **Callback data:** Unchanged; still under **64 bytes**; **no** profile data in `callback_data`.  
- **Truncation:** Long names must not break Telegram message limits; use existing line truncation helper patterns.

---

## 9. Tests required (for a future runtime slice)

- **Unit/service:** Given a `User` with various combinations of name/username/phone, `customer_summary` (or equivalent builder) returns deterministic `display_name` and summary lines per section 5; missing `User` → null-safe summary, no exceptions.  
- **Admin API:** Authenticated `GET` list/detail responses include new fields; JSON stable; existing `customer_telegram_user_id` still correct.  
- **Telegram (optional in same slice or follow-up):** List/detail text contains expected `tg:` / `@` patterns for fixture users; callback lengths unchanged.  
- **Regression / privacy:** Mini App `GET` routes for `My bookings` / `My requests` still **404** or scope correctly for other users’ data (reuse patterns from Y35.2 tests).  
- **No execution-link** or **identity bridge** test churn beyond proving unrelated modules untouched.

---

## 10. First safe runtime slice recommendation

1. **Server-only derived fields** from existing `User` columns: add **`display_name`**, **`username`**, and **`summary_line`** (or equivalent) to admin order list/detail and custom request list/detail **Pydantic** models; populate in **AdminReadService** and **CustomMarketplaceRequestService** with **one shared helper** (e.g. `build_customer_summary(user: User | None) -> ...`) to avoid drift.  
2. **Do not** add migrations or new columns in v1.  
3. **Defer `phone`** until an explicit one-line product/policy note authorizes it; otherwise **omit** from API and Telegram.  
4. **Telegram admin UI:** Switch list/detail message templates to use the new strings; keep **numeric id** visible on **detail** for support.  
5. **Tests** as in section 9, focused and minimal.  
6. **Postponed:** Telegram `getChat` enrichment, admin search by @username, internationalized name collation, supplier-facing summary.

This slice improves operator UX while staying **read-only**, **fail-closed**, and **bounded to existing data**.

# O1A — Production IAM Baseline Design / Schema Review

**Status:** docs-only inventory and gap analysis (no migrations, endpoints, or IAM implementation in this step)  
**Parents:** [O1-DG design gate](O1_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md), [OPERATIONAL_AUTOMATION_ROADMAP.md](OPERATIONAL_AUTOMATION_ROADMAP.md) §9–10 (O1 placement)  
**Purpose:** List **existing** identity and auth mechanisms so future IAM work does **not** introduce duplicate user or credential models.

---

## 1. What user / identity / auth models already exist?

### 1.1 Core customer / operator “person” table

| Table | File | Role |
|-------|------|------|
| **`users`** | [`app/models/user.py`](../app/models/user.py) | Canonical end-user row: **`telegram_user_id`** (unique, **BigInteger**), profile fields (`username`, names, **`phone`**, **`preferred_language`**, `home_city`, **`source_channel`**). **No** `role` column. |

**Relationships (same table used for multiple human operational concepts):**

- **Customer orders:** `orders.user_id` → `users.id`
- **Operator assignment (soft):** `orders.assigned_operator_id` → `users.id`; `handoffs.assigned_operator_id` → `users.id`
- **Handoffs, waitlist, messages, content approval, custom marketplace ops assignments** — see relationships on `User` in [`app/models/user.py`](../app/models/user.py)

**Implication:** “Human operator” in the handoff/order sense is currently **the same `User` ORM type** as the customer, distinguished only by **foreign-key usage**, not a dedicated staff table or RBAC flags.

### 1.2 Supplier commercial entity

| Table | File | Role |
|-------|------|------|
| **`suppliers`** | [`app/models/supplier.py`](../app/models/supplier.py) | `code`, `display_name`, **`primary_telegram_user_id`** (optional **unique** Telegram link for DMs/onboarding), onboarding/legal fields, **`is_active`**. **Not** a user-password identity; org root for offers. |
| **`supplier_api_credentials`** | [`app/models/supplier.py`](../app/models/supplier.py) | **`token_hash`** (SHA-256 hex of bearer token), **`label`**, **`revoked_at`**, FK **`supplier_id`**. Machine/API identity for **HTTP supplier-admin** (`/supplier-admin/...`). |
| **`supplier_offers`**, execution links, bridges, etc. | same module | Commercial Layer B data; auth is indirect via supplier credential or admin paths. |

### 1.3 Other security-relevant persistence (not “users,” but auth-adjacent)

| Area | Notes |
|------|--------|
| **`admin_guarded_action_attempts` / `admin_guarded_action_steps`** | [`app/models/admin_guarded_action.py`](../app/models/admin_guarded_action.py) — **audit/idempotency** for guarded admin actions (e.g. prepare-conversion-chain), not login identity. |
| **`supplier_notification_outbox`** | Operational Telegram DM **queue**; resolves Telegram targets; not credential store. |
| **Payment webhooks** | Signature verification via configured secret — **provider** auth, not user IAM. |

### 1.4 Explicitly **absent** in schema (relevant to O1)

- **No** `drivers`, **no** `vehicles`, **no** `departure_assignments` tables as of this review.
- **No** JWT/session table, **no** OAuth account link table, **no** `roles` / `permissions` tables.
- **No** second `User`-like table for staff (admins are not modeled as `users` rows today).

---

## 2. What supplier / supplier-admin auth already exists?

| Mechanism | Where | Behavior |
|-----------|--------|----------|
| **Bearer API token → supplier** | [`app/api/supplier_admin_auth.py`](../app/api/supplier_admin_auth.py) **`require_supplier`**, alias **`SupplierAuth`** | Client sends **`Authorization: Bearer <raw_token>`**. Server hashes with **`hash_supplier_api_token`** (SHA-256), looks up [`SupplierApiCredentialRepository`](../app/repositories/supplier.py) **active** credential, returns **`Supplier`**. **401** if missing/invalid. |
| **Credential storage** | **`supplier_api_credentials.token_hash`** | **Unique** hash; **`revoked_at`** for soft revoke. **No** plaintext token in DB. |
| **Bootstrap (central admin)** | Admin route uses **`AdminSupplierWriteService.create_supplier_with_credential`** ([`app/services/admin_supplier_write.py`](../app/services/admin_supplier_write.py)) | Creates supplier + hashed credential; raw token returned once to admin — **not** end-user self-signup. |
| **Supplier Telegram linkage** | **`suppliers.primary_telegram_user_id`** | Used for onboarding flows and **supplier-facing Telegram notifications** (e.g. lifecycle DMs), **not** for HTTP **`/supplier-admin`** authentication. |

**There is no separate “supplier_admin” user table:** supplier **HTTP** API access is **per-org machine tokens**, not per-person accounts with passwords.

---

## 3. How customer Telegram identity currently works

| Layer | Mechanism |
|-------|-----------|
| **Bot / private handlers** | Aiogram handlers use **`message.from_user.id`** as Telegram id; services resolve or create **`User`** via [`UserRepository.get_by_telegram_user_id`](../app/repositories/user.py) and bot services ([`app/bot/services.py`](../app/bot/services.py)). |
| **Supplier-side Telegram** | **`SupplierOnboardingService.get_by_telegram_user_id`** maps Telegram id → **`Supplier`** for supplier bot flows ([`app/bot/handlers/supplier_onboarding.py`](../app/bot/handlers/supplier_onboarding.py), supplier offer workspace). **Distinct** from customer `User` row — same Telegram id could theoretically collide in product terms if not disciplined (design should keep supplier vs customer flows explicit). |
| **Webhook security** | [`app/api/routes/telegram_webhook.py`](../app/api/routes/telegram_webhook.py) — optional **`TELEGRAM_WEBHOOK_SECRET`** via Telegram **secret_token** header; protects **ingest** path, not customer “login.” |

Customer identity in DB = **one row per `telegram_user_id`**.

---

## 4. How Mini App identity currently works

| Aspect | Current pattern |
|--------|------------------|
| **Backend API** | Most Mini App routes take **`telegram_user_id`** as **query parameter** or in **JSON body** (e.g. [`app/api/routes/mini_app.py`](../app/api/routes/mini_app.py) — booking, bookings list, orders). **No** `initData` validation was found in **`app/`** (repository search for `init_data` under **`app`** returned **no** matches). |
| **Trust boundary** | Documented as transitional: schemas note “until Telegram init-data auth exists” ([`MiniAppCreateReservationRequest`](../app/schemas/mini_app.py)). **Caller is expected to pass a valid id** in trusted contexts. |
| **Flet client** | [`mini_app/config.py`](../mini_app/config.py): **`MINI_APP_DEV_TELEGRAM_USER_ID`**, **`MINI_APP_ALLOW_DEV_IDENTITY_FALLBACK`** — local/dev identity resolution; [`mini_app/app.py`](../mini_app/app.py) resolves runtime `telegram_user_id` with dev/fallback rules. |
| **User must exist** | Some flows return **400** if `telegram_user_id` is unknown to the system (e.g. custom requests — see DEMO playbook). |

**Conclusion:** Mini App “identity” is **parameterized Telegram user id + existing `User` row**, not cryptographically verified Telegram Web App init data in the API layer (as of this review).

---

## 5. How admin authentication currently works

| Surface | Auth |
|---------|------|
| **HTTP Admin API** (`/admin/...`) | [`require_admin_api_token`](../app/api/admin_auth.py): **`ADMIN_API_TOKEN`** from settings; accept **`Authorization: Bearer`** or **`X-Admin-Token`**. Constant-time compare. **503** if token unset (admin disabled). **One shared secret** = **no per-admin identity** in HTTP layer. |
| **Telegram “admin workspace” / cockpit** | **`TELEGRAM_ADMIN_ALLOWLIST_USER_IDS`** — comma-separated Telegram user ids ([`app/core/config.py`](../app/core/config.py) **`telegram_admin_allowlist_ids`**). Used for **bot-side** admin-only features (e.g. automation cockpit — see `app/bot/`). **Fail-closed** if not allowlisted. |
| **Internal ops JSON** | **`OPS_QUEUE_TOKEN`** — separate shared secret for **`/internal/ops/...`** when enabled (config docstring). Not RBAC. |

**There is no `AdminUser` table** and **no** super-admin split in the database; “admin” is **env secret + optional Telegram allowlist**.

---

## 6. What can be reused for production IAM?

| Building block | Reuse guidance |
|----------------|----------------|
| **`users` + `telegram_user_id` uniqueness** | Keep as **canonical customer identity**; extend with **care** (optional columns vs sidecar profile tables) rather than a parallel “Customer” table. |
| **`suppliers` + `supplier_api_credentials` + bearer gate** | Keep as **machine-to-machine** supplier API auth; future **per-person** supplier staff can **reference** `supplier_id` without replacing this hash model overnight. |
| **`Order` / `Handoff` operator FKs to `users`** | Reuse **`users.id`** for “assigned operator” **or** plan a **migration** to `staff_users` if product requires strict separation from customers (breaking change if conflated ids are already in use). |
| **Telegram allowlist + shared admin token** | Operational stopgap; replace with **proper admin accounts** gradually — do not add a *second* parallel global secret without a migration story. |
| **Webhook / payment / ops secrets** | Keep as **integration** auth only; do not overload as human IAM. |

---

## 7. What must be added later (aligned with O1-DG, not implemented here)

From [O1_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md](O1_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md) and gaps found above:

- **Explicit RBAC** (roles, scopes) for platform admin, super admin, supplier org members, drivers — **not** inferable from a single shared `ADMIN_API_TOKEN`.
- **Supplier org membership** (multiple humans per supplier) if product requires it — today auth is **token-per-org**, not **user-per-org**.
- **Driver identity**, **vehicle**, **departure assignment** tables and **assignment-scoped** sessions — **none** exist yet.
- **Verified Mini App identity** (Telegram **initData** validation or equivalent) to remove trust-on-query-param pattern.
- **Ticket / QR** signing keys and **artifact** tables — out of IAM baseline but depend on stable **order/user/trip** references.
- **Audit** tables for PII/manifest views and **scan** events — separate from login tables.

---

## 8. What must **NOT** be duplicated

| Anti-pattern | Why |
|--------------|-----|
| A **second** “User” or “Customer” table with overlapping `telegram_user_id` | Violates single source of truth; migrate/extend **`users`** instead. |
| A **parallel** admin auth mechanism (e.g. new global bearer) without deprecating **`ADMIN_API_TOKEN`** | Operators will use weakest link; migrate with env + doc cutover. |
| A **second** supplier credential model (duplicate hash tables) | Extend **`supplier_api_credentials`** (e.g. scopes, labels, rotation metadata) or add **staff** tables that **reference** supplier_id. |
| Mixing **M1 marketing QR** and **O1 secure ticket/boarding** signing keys | Roadmap already separates clusters — duplicate signing would be a **security** duplicate, not just schema. |
| Encoding **driver** or **admin** identity only as Telegram allowlist **without** DB-backed audit for O1 operations | Allowlist can remain a **gate**, not the **long-term** audit identity for boarding/manifest. |

---

## 9. Safest implementation sequence **after** this review

Order minimizes data-model churn and respects [OPERATIONAL_AUTOMATION_ROADMAP.md](OPERATIONAL_AUTOMATION_ROADMAP.md) narrow-step policy:

1. **Document + freeze** current auth surfaces (this O1A doc) — **done** when merged into team baseline.
2. **Admin IAM (platform)** — introduce **admin user / role** persistence *or* structured API keys with **audit**, and map legacy **`ADMIN_API_TOKEN`** to a break-glass bridge (design sub-gate; no big-bang).
3. **Mini App trust** — implement **initData** (or agreed alternative) **before** exposing sensitive entitlements (ticket QR, manifest).
4. **Supplier org IAM** — optional **`supplier_members`** (user link + role) **while retaining** `supplier_api_credentials` for automation until migrated.
5. **Operational entities** — **vehicle**, **driver**, **departure instance**, **assignment** tables — **before** boarding scan apps.
6. **O1 artifacts** — ticket references, QR signing, scan audit — **after** assignment and Mini App trust are clear.
7. **Manifest surfaces** — only with O1-DG privacy/audit gates.

This sequence matches O1-DG §13 with codebase-specific emphasis on **not** splitting `User` without a migration plan for `assigned_operator_id` / orders.

---

## 10. Source docs (context only)

Reviewed for alignment, not reproduced here:

- [O1_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md](O1_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md)
- [CHAT_HANDOFF.md](CHAT_HANDOFF.md), [OPEN_QUESTIONS_AND_TECH_DEBT.md](OPEN_QUESTIONS_AND_TECH_DEBT.md)
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), [IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md](IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md) (MVP / marketplace scope)
- [TECH_SPEC_TOURS_BOT.md](TECH_SPEC_TOURS_BOT.md), [TECH_SPEC_TOURS_BOT_v1.1.md](TECH_SPEC_TOURS_BOT_v1.1.md)
- [DEMO1_PHYSICAL_TELEGRAM_DEMO_SMOKE_PLAYBOOK.md](DEMO1_PHYSICAL_TELEGRAM_DEMO_SMOKE_PLAYBOOK.md) (admin token + Mini App query identity)

---

## 11. Review metadata

| Item | Value |
|------|--------|
| Repository paths reviewed | `app/models`, `app/api/admin_auth.py`, `app/api/supplier_admin_auth.py`, `app/api/routes/admin.py` (pattern), `app/api/routes/supplier_admin.py`, `app/api/routes/mini_app.py`, `app/core/config.py`, `mini_app/config.py`, `mini_app/app.py`, `app/repositories/user.py`, `app/models/supplier.py`, `app/models/order.py`, `app/models/handoff.py` |
| `grep` highlights | No `class User` duplicates in `app` (single `User` model). No `init_data` in `app/`. **`require_admin_api_token`** / **`require_supplier`** are the two primary HTTP auth gates besides payment webhook verification. |

**Next suggested doc (not this file):** child design for **O1A-step-2** — “Admin user model vs shared token cutover” or **O1B** vehicle/driver schema — pick in product priority order.

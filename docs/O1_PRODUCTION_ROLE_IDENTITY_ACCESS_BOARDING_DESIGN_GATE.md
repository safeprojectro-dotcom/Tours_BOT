# O1-DG — Production Role, Identity, Access, Supplier/Driver Operations & Boarding Design Gate

**Status:** design gate (no implementation in this document)  
**Roadmap placement:** [P0 → O1 — Order / Ticket QR & Boarding Validation](OPERATIONAL_AUTOMATION_ROADMAP.md) (see §9 *QR cluster*).  
**Related:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) (baseline MVP), [TECH_SPEC_TOURS_BOT.md](TECH_SPEC_TOURS_BOT.md) (product truth).

This document defines **production-grade** identity, roles, operational access, vehicle/device boundaries, ticket/QR **architecture**, boarding validation, and trip closeout **before** any code, migrations, secure tokens, manifest surfaces, or driver UX.

---

## 1. Purpose and hard boundaries

### 1.1 What this gate must produce

- A single **permission and data-exposure model** for **customer**, **supplier org**, **driver**, **operator admin**, and **super admin**.
- Explicit separation of **authentication** vs **authorization** vs **audit**.
- A **QR/ticket** model that is **not** marketing QR (see §2).
- A **boarding validation** approach (online-first vs offline tolerant, duplicate scans, fallback when QR lost).
- A **manifest** policy (who sees PII, when, under what audit).
- An **implementation sequence** that respects narrow steps and dangerous-area gates from [OPERATIONAL_AUTOMATION_ROADMAP.md](OPERATIONAL_AUTOMATION_ROADMAP.md) (e.g. §15 split rules).

### 1.2 Out of scope for O1-DG (this file)

- Choosing vendor-specific hardware (specific scanner OEMs, MDM products) beyond generic requirements.
- Full legal/DPA text (flag requirements only).
- Implementations: no endpoints, migrations, QR generation, scan apps, or manifest UI are specified as built here.

### 1.3 Relationship to M1 (marketing QR)

Per roadmap **§9 QR cluster**:

| Cluster | Owns | Must never impersonate |
|---------|------|-------------------------|
| **M1** — Marketing identity & entry / deep links | Campaign/source, marketing QR **fences**, catalog/tour/referral **entry context** | Ticket, payment proof, boarding credential |
| **O1** — Order / ticket / boarding | Secure **order/ticket/boarding** tokens, validation, operational scan audit | Marketing attribution |

**Rule:** Any QR rendered to the customer must be **labeled by purpose** in product copy and analytics (marketing entry vs operational ticket). Payloads and signing keys must not be shared across clusters.

---

## 2. Baseline today (MVP) vs production target

Honest baseline to avoid fictional “already implemented” claims:

| Actor | Today (indicative MVP posture) | Production target (this gate) |
|-------|--------------------------------|--------------------------------|
| **Customer** | Telegram identity + Mini App flows keyed by `telegram_user_id` (and related booking APIs); not a full IAM | Strong customer session model (Telegram + Mini App), device binding where needed, order-scoped capabilities |
| **Admin** | Shared-secret **Admin API token** (`ADMIN_API_TOKEN`) for HTTP admin | Role-based admin, super-admin split, auditable grants, optional SSO later |
| **Supplier** | Supplier entities + HTTP surfaces as implemented per project; notifications via outbox patterns (e.g. S1C*) | Supplier **org**, membership, least-privilege API keys or OAuth-style flows, portal RBAC |
| **Driver** | Not a first-class production role in MVP | Driver identity, assignment-scoped access, **no** standing access to full manifest by default |
| **Vehicle / device** | Not standardized as trusted devices | Device registration, short-lived credentials, optional per-departure pairing |

Everything in the **production target** column is **design intent** until broken into future narrow implementation blocks.

---

## 3. Authentication — question 1

### 3.1 Customer

**Principles**

- Primary identity: **Telegram** (`user_id`) as stable handle; **Mini App** continues to need verifiable linkage (init-data validation when available; until then, documented trust boundaries per existing API).
- Session: customer capabilities must be **order-scoped** and **tour-scoped** (see what they can read or prove).

**Production-oriented options (pick in a follow-on spec)**

| Option | Pros | Cons |
|--------|------|------|
| A — Telegram-only trust boundary | Simple | Web/Mini App abuse risk if init-data not enforced everywhere |
| B — Short-lived server session + refresh | Hardened | More moving parts |
| C — Magic link / email for non-Telegram (future) | Coverage | Not required for Telegram-first MVP |

**Design decision for gate:** Customer auth MUST bind **Telegram identity ↔ internal User** consistently; any “show my ticket QR” action MUST require that binding plus **order entitlement** (paid/confirmed per business rules).

### 3.2 Supplier (organization user)

**Principles**

- Supplier is an **organization**; humans are **members** with roles (owner, ops, read-only finance, etc.).
- Authentication options: **password + MFA**, **magic link**, or **OIDC** (later). For mobile-first ops, prefer **MFA** on sensitive actions.

**Design decision for gate:** No long-lived opaque “supplier master token” shared across people; prefer **per-user** credentials or per-user API tokens with **role scopes**.

### 3.3 Driver

**Principles**

- Driver identity is **employment/contract scoped** to supplier org (or platform if multi-supplier drivers—explicitly rare; default: **one supplier org**).
- Authentication must work on a **shared phone** scenario (device may not equal person). Use **device enrollment** + optional **PIN/biometric** on top of driver login.

**Design decision for gate:** Driver session must be **short-lived** and **re-anchorable** to “this device is approved for today”.

### 3.4 Admin and super admin

| Role | Intent |
|------|--------|
| **Operator admin** | Day-to-day catalog, orders, handoff, operational corrections within policy |
| **Super admin** | Break-glass: account recovery, permission grants, fatal corrections; **must** be audited |

**Design decision for gate:** Split **super admin** from normal admin **conceptually** even if same codebase; require **stronger MFA**, **session recording** (metadata), and **dual control** for selected actions *if* regulatory or insurance requires (optional policy flag).

### 3.5 Service accounts / automation

- **Bots**, **workers**, and **integration** keys are **not** human roles; they get **scoped machine tokens** with explicit rotation and **no** blanket impersonation of customers.

---

## 4. Roles, assignment, and revocation — question 2

### 4.1 Role model (conceptual)

| Role | Typical capabilities |
|------|----------------------|
| `customer` | Own orders; Mini App; receive operational QR **for own order** |
| `supplier_member` | Org-scoped; manage offers per policy; read operational aggregates vs manifest per policy |
| `supplier_admin` | Membership, vehicles, driver linking, policy boundaries |
| `driver` | **Assignment-scoped** departure ops; boarding scan; **no** org-wide catalog write |
| `operator_admin` | Platform ops; cross-supplier read/write per policy |
| `super_admin` | Break-glass; grants; configuration |
| `service_bot` | Outbound/inbound messaging under strict tool policy |

**Revocation**

- Immediate effect for sessions (server-side **session version** or **token jti blocklist**) for humans.
- API keys: rotate prefix, set expiry, and audit last use.
- Driver: revoke **device enrollment** without deleting historical scan audit **if** legally required to retain.

---

## 5. Supplier organization model — question 3

### 5.1 Entities (conceptual)

- **Supplier organization** — legal/commercial root.
- **Offer lifecycle** — existing marketplace flows remain source of commercial truth.
- **Vehicle** — asset registered to org; **license plate**, capacity, safety metadata as required.
- **Driver** — person; may be linked to **one primary supplier org** (default).
- **Departure / trip instance** — operational occurrence: *tour + datetime + vehicle + driver assignment* (exact schema is a future migration block).

### 5.2 Who manages what

| Object | Supplier admin | Supplier ops | Platform admin |
|--------|----------------|--------------|----------------|
| Offers / packaging | ✓ (policy) | ✓ | override / moderation |
| Vehicles | ✓ | propose | revoke |
| Drivers (org roster) | ✓ | ✓ read | suspend platform-wide |
| **Departure assignment** (driver + vehicle) | ✓ | ✓ | ✓ audit override |

**Design decision for gate:** **Departure assignment** is the **authorization root** for driver boarding mode (see §6).

---

## 6. Driver access to assigned departures only — question 4

### 6.1 Authorization rule

**Default deny.** A driver may only:

- List **today/near-future** departures **explicitly assigned** to them **or** to a vehicle they are logged into (choose one primary model—see §7).

**Anti-patterns (forbidden)**

- “Driver can query by tour_id and see all passengers” without manifest policy.
- Standing read access to **historical** manifests beyond retention window.

### 6.2 Assignment sources

- **Pre-departure plan**: ops assigns driver + vehicle to departure.
- **Exception**: substitute driver — must emit **audit event** (who changed assignment, when).

---

## 7. Service phones and vehicle devices — question 5

### 7.1 Device classes

| Class | Typical use | Trust model |
|-------|-------------|-------------|
| **Driver phone** (BYOD or company) | Scanning, checklist | App install + org enrollment |
| **Vehicle-mounted tablet** | Same | Device certificate + physical control |
| **Supplier back-office PC** | Ops, not scanning | Standard web session |

### 7.2 Enrollment

- **Device enrollment record**: supplier org, device fingerprint (best-effort), optional **phone number attest**, approved by supplier admin.
- **Per-departure session**: “Open boarding mode for departure **D**” requires **driver auth** + **active assignment** + **time window** (departure day ± configurable).

### 7.3 Lost / stolen device

- Remote **wipe app session** (+ revoke refresh).
- Do not rely on long-lived secrets stored only on device for **server trust**; use **short-lived tokens**.

---

## 8. Tickets and QR — question 6 (later implementation)

This section defines **models**, not byte layouts.

### 8.1 Ticket vs QR encoding

| Artifact | Meaning |
|----------|---------|
| **Order** | Commercial and payment truth (Layer A) |
| **Ticket** | Per-passenger **entitlement** artifact for a specific departure instance (may be 1:n with seats) |
| **QR payload** | References **ticket id** + **nonce/version** + **expiry** + **HMAC/signature**; **no** raw PII in signed QR if avoidable |

### 8.2 QR types under O1 (operational only)

| Type | Consumer | Notes |
|------|----------|------|
| **Boarding / check-in QR** | Driver scanner | Short TTL; encodes ticket reference; **offline verify** is optional mode with risk acceptance |
| **Customer ticket QR** | Traveller phone | Display-only; refresh if rotated |
| **Order status QR** (optional) | Support | Read-only state; never substitute boarding |

### 8.3 Expiry and rotation

- Tie validity to **departure instance** + **status** (cancelled → invalidate).
- Support **rotation** if screenshot leak suspected (new nonce; old invalid).

### 8.4 Signing / keys

- **Separate signing keys** from M1 marketing link signing.
- **Key rotation** story: v1/v2 keys verify during overlap window.

---

## 9. Boarding validation — question 7

### 9.1 Scan flow (canonical)

1. Driver opens **boarding mode** for departure **D** (authorized).
2. Scanner captures QR → server validates signature + ticket state.
3. Server returns **allow / deny** + reason code (**duplicate**, **wrong departure**, **cancelled**, **unpaid**, **child rule**, etc.).
4. Persist **scan audit event**: timestamp, actor (driver id), device id, ticket id, result, optional geolocation **if** policy allows.

### 9.2 Offline / degraded modes (explicit risk acceptance)

| Mode | Behavior | Risk |
|------|----------|------|
| Online-only (default) | No boarding without connectivity | Ops stops if network down |
| Offline cache | Device caches **public keys** + **recent ticket allowlist snapshot** | Stale data, clock skew |
| Manual list | Paper / admin override | Human error; needs **dual witness** policy optional |

**Design decision for gate:** **Default online-first**; offline is a **separate** narrow block with threat analysis.

### 9.3 Duplicate boarding

- **Idempotent success**: second scan returns **already_boarded** (not a hard error to the driver UX if silent acknowledgment is preferred).

---

## 10. Visibility matrix — question 8

High level; exact fields are a future privacy table.

| Data | Customer | Driver | Supplier ops | Supplier admin | Platform admin |
|------|----------|--------|--------------|----------------|----------------|
| Own booking summary | ✓ | — | per-order support view | ✓ aggregates | ✓ |
| **PII** (name, phone) | self | **only if manifest policy allows** | policy | policy | policy |
| **Full manifest** | — | **default deny** | gated | gated | gated |
| Payment instrument details | masked/None | — | — | — | restricted |
| Scan audit trail | — | own device actions | org-scoped | org-scoped | ✓ |
| Operational KPIs | — | — | ✓ | ✓ | ✓ |

**Principle:** **Manifest** is a **controlled surface**; in the **Supplier Operations** cluster of the roadmap, a future **secure passenger manifest** must mean **permissions + audit + purpose limitation**—not a CSV export by default (see [OPERATIONAL_AUTOMATION_ROADMAP.md](OPERATIONAL_AUTOMATION_ROADMAP.md), *Supplier Operations*).

---

## 11. Trip completion report — question 9

### 11.1 Purpose

- Formal **closeout** for a departure: boarded count vs expected, no-shows, incidents, optional notes, linkage to financial/settlement **if** applicable later.

### 11.2 Contents (conceptual)

- **Identity of departure** (tour instance, supplier, driver, vehicle).
- **Counts**: tickets validated, duplicate scans, manual overrides.
- **Exceptions**: denied boarding reasons aggregated.
- **Timestamp** and **sign-off** by driver and/or supplier ops.

### 11.3 Integrity

- Immutable **report record** after sign-off; corrections via **append-only** adjustment with audit (not silent edits).

---

## 12. Privacy, compliance, and audit (cross-cutting)

- **Data minimization:** QR carries references, not full name/phone, where possible.
- **Retention:** manifest retention window defined per jurisdiction; **right to erasure** conflicts with **audit/fraud**—document legal pick.
- **Audit:** who exported manifest, who ran scan override, who viewed PII fields.
- **AI:** operational assistants must be **tool-gated** per roadmap AI separation (no inventing boarding state).

---

## 13. What to implement first after this design gate — question 10

Recommended **narrow** sequence (each step owns tests + explicit no-go list). Order may be adjusted after dependency analysis; dependencies flow **down**.

1. **Identity & admin RBAC foundation**  
   Replace or wrap flat admin token with **user accounts + roles** for platform operators (super admin split optional but planned).  
   *Still no customer PII expansion.*

2. **Supplier org membership model**  
   Users belong to supplier org with roles; audit membership changes.

3. **Vehicle + driver roster + assignment to departure instance**  
   Schema and admin UX at minimal viable level; still **no** public QR.

4. **Ticket entitlement model** (DB + invariants) tied to order + departure instance  
   **No QR graphic** yet; **no** scanner app yet.

5. **Operational QR signing service + customer “show ticket” surface**  
   Cryptographic format frozen; short TTL; rotation hooks.

6. **Driver boarding scan API + audit log**  
   Online-first; driver session rules enforced.

7. **Manifest read surfaces** under strict policy flags  
   Start with **aggregates**, then **row-level** with audit.

8. **Offline / backup boarding** (optional branch)  
   Only after online path + audit shipped.

9. **Trip closeout report**  
   After scan pipeline exists.

**Explicit deferrals**

- **M1** marketing QR and campaign deep links — separate design gate; never reuse O1 keys.
- **Broad AI tooling** on manifest — after permissions exist.

---

## 14. Open decisions checklist (before coding)

- [ ] Single vs split **signing keys** per environment (staging vs prod mandatory split).
- [ ] Driver **assignment** model: by **driver id** only vs **vehicle device** as primary.
- [ ] Manifest **lawful basis** and export rules (RO/EU/US variants if relevant).
- [ ] Whether **super admin** actions require **two-person approval**.
- [ ] Whether boarding scan stores **GPS** (privacy impact).

---

## 15. References

- [OPERATIONAL_AUTOMATION_ROADMAP.md](OPERATIONAL_AUTOMATION_ROADMAP.md) — P0 clusters, QR split (§9), O1 listing (§10 execution order #10), narrow-step policy (§15).
- [HANDOFF_O1_DG_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md](HANDOFF_O1_DG_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md) — block boundary / exclusions.
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — MVP baseline.
- [TECH_SPEC_TOURS_BOT.md](TECH_SPEC_TOURS_BOT.md) — product scope and channels.
- Implemented context (non-O1 but informs operations): S1C supplier notification outbox/delivery, S1D operational sales push, [DEMO1_PHYSICAL_TELEGRAM_DEMO_SMOKE_PLAYBOOK.md](DEMO1_PHYSICAL_TELEGRAM_DEMO_SMOKE_PLAYBOOK.md).

---

**Document owner:** architecture / product **before** scheduling O1 implementation slices.  
**Next artifact:** child prompts per §13 with explicit **no-go** lists mirroring [OPERATIONAL_AUTOMATION_ROADMAP.md](OPERATIONAL_AUTOMATION_ROADMAP.md) §15.

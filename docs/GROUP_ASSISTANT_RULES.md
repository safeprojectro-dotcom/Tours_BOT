# Group Assistant — operational rules foundation

## Project
Tours_BOT

## Purpose
Define the **narrow operational foundation** for **Phase 7 — Group Assistant And Operator Handoff**: what the bot may do in **Telegram groups**, what is **forbidden**, how **CTAs** route users to **private chat** and **Mini App**, how **anti-spam** is conceived, which **handoff categories** apply in **group vs private**, and what **operator continuity** must preserve.

This document is **behavioral and operational**. It does **not** implement runtime code, webhooks, or new APIs. Implementation slices (trigger evaluation, handoff helper logic, persistence) come in later Phase 7 steps.

**Status:** introduced in **Phase 7 / Step 1** (documentation-first).

---

## Alignment with project sources

| Source | Relationship |
|--------|----------------|
| [docs/IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — **Phase 7** | This file instantiates Phase 7’s **group warm-up**, **CTA routing**, **group safety**, **anti-spam**, and **handoff escalation** themes as **rules before code**. Full Phase 7 scope (e.g. operator queue lifecycle, return-to-bot) remains in the plan for **later** steps — **not** claimed as done here. |
| [docs/AI_ASSISTANT_SPEC.md](AI_ASSISTANT_SPEC.md) | **§3.1 Group Chat Behavior**, **§2 Core Product Constraints**, **§4 CTA / uncertainty**, **§5 tool-driven facts**, **handoff** expectations — this document **narrows** them into **group-specific** operational rules. Group stays **brief, factual, CTA-oriented**; private + Mini App own booking/payment depth. |
| [docs/AI_DIALOG_FLOWS.md](AI_DIALOG_FLOWS.md) | **§1 Group → Private**, **§7 Payment Issue → Handoff**, **§8 Discount / Custom → Handoff**, **§9 Complaint** — exemplify flows; **handoff categories** below map to those patterns. |
| [docs/TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) | **§6 Group Behavior Setup**, **§10 Telegram Handoff Rules** — setup and permissions stay in `TELEGRAM_SETUP.md`; **normative rule detail** for group + handoff **lives here** (`GROUP_ASSISTANT_RULES.md`) for Phase 7. |

---

## 1. Allowed group triggers (when the assistant may respond)

The bot must **not** behave like an always-on chatbot in the group. Responses are allowed only when **intentionally triggered**:

1. **Mentions** — user addresses the bot via `@bot_username` / explicit mention (exact mechanism per Telegram client).
2. **Approved commands** — a **closed, product-maintained** list (e.g. `/help`, `/tours` — final list to be frozen before production group rollout). Commands must stay **minimal** and aligned with [docs/TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) §3.
3. **Approved trigger phrases** — short, curated patterns (locale-specific as needed) signaling **sales / info intent** (e.g. price, seats, departure time, “how to book”). **Implementation** (matching, fuzzy bounds) is **out of scope** for this document; only the **policy** is fixed here.

**Default:** if none of the above apply, **no reply** (see **Anti-spam**).

---

## 2. Forbidden behavior in group

| Rule | Rationale |
|------|-----------|
| **No private data collection in group** | No phone numbers, IDs, full names, payment identifiers, booking codes, or step-by-step personal itineraries in public chat. Aligns with [docs/AI_ASSISTANT_SPEC.md](AI_ASSISTANT_SPEC.md) §3.1. |
| **No long personal negotiation in group** | No multi-turn haggling, custom deal threads, or case-by-case commercial debate in public. Move to **private** or **handoff**. |
| **No payment-sensitive discussion in group** | No card/bank details, no “did my payment go through?” resolution, no refund math, no dispute resolution in group. Aligns with [docs/AI_DIALOG_FLOWS.md](AI_DIALOG_FLOWS.md) §7 and **unclear payment issue** handoff category. |
| **No answering every message** | Anti-spam and signal-to-noise; only **§1 triggers** qualify. Aligns with [docs/AI_ASSISTANT_SPEC.md](AI_ASSISTANT_SPEC.md) §3.1 (not every message). |

---

## 3. CTA strategy

**Primary objective:** convert interest into **private chat** or **Mini App**, where booking and payment rules apply.

| Route | When |
|-------|------|
| **Private chat** | User needs qualification, seat count, boarding choice, human nuance, or any path toward **reservation / handoff**. Prefer short factual line + “write in private” (variants per [docs/AI_DIALOG_FLOWS.md](AI_DIALOG_FLOWS.md) §1). |
| **Mini App** | User needs **catalog, structured availability, self-serve booking UI**, or **payment / booking status** inside the product UI — **without** exposing payment details in the group thread. |

**Rules:**
- Prefer **one clear CTA** per group reply when a CTA is used ([docs/AI_ASSISTANT_SPEC.md](AI_ASSISTANT_SPEC.md) §4.2 — adapted for group brevity).
- Never imply **payment success** or **confirmed availability** without system-backed facts ([docs/AI_ASSISTANT_SPEC.md](AI_ASSISTANT_SPEC.md) §5).

---

## 4. Anti-spam principles

- **Trigger-gated replies** — see **§1**; silence is valid.
- **Rate awareness** (operational) — product may later cap replies per user/time window; not implemented in Step 1.
- **Short, single-purpose messages** — avoid walls of text; no duplicate CTAs in one message.
- **No broadcast-style spam** — group is not a newsletter channel unless product defines separate campaigns (out of scope here).

---

## 5. Handoff trigger categories (group and private)

These categories are **semantic** targets for escalation. They apply to **both** entry points unless noted. Actual **detection** and **handoff record creation** are **implementation** concerns for later steps; admin queue behavior remains as in Phase 6 until extended by product.

| Category | Meaning | Typical source |
|----------|---------|----------------|
| **Discount request** | Any non-standard pricing, promo, or commercial exception. | [docs/AI_DIALOG_FLOWS.md](AI_DIALOG_FLOWS.md) §8 |
| **Group booking** | Larger party / bulk coordination beyond normal single-flow booking. | [docs/AI_DIALOG_FLOWS.md](AI_DIALOG_FLOWS.md) §8 (e.g. “we are N people”) |
| **Custom pickup** | Pickup/boarding exceptions, extra stops, non-catalog logistics. | [docs/AI_DIALOG_FLOWS.md](AI_DIALOG_FLOWS.md) §8 |
| **Complaint** | Dissatisfaction, conflict, reputational risk — de-escalate and hand off. | [docs/AI_DIALOG_FLOWS.md](AI_DIALOG_FLOWS.md) §9 |
| **Unclear payment issue** | Paid vs unpaid mismatch, failed payment, ambiguous status — **never** debug in group. | [docs/AI_DIALOG_FLOWS.md](AI_DIALOG_FLOWS.md) §7 |
| **Explicit human request** | User asks for a person / operator. | [docs/AI_ASSISTANT_SPEC.md](AI_ASSISTANT_SPEC.md) escalation |
| **Low-confidence answer** | Assistant cannot ground an answer in catalog/system/policy. | [docs/AI_ASSISTANT_SPEC.md](AI_ASSISTANT_SPEC.md) §4.3 |

**Group-specific emphasis:** categories that touch **payment**, **personal data**, or **multi-turn negotiation** must **not** be resolved in group — acknowledge briefly if at all, then **private** or **handoff**.

---

## 6. Minimal operator continuity requirements

When a case moves to a human (existing or future pipeline), the following must be **preserved** for operator UX and audit ([docs/TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) §10):

1. **Context** — enough recent intent and thread summary (implementation-defined).
2. **Language** — user’s active or preferred language for replies.
3. **Reason / category** — one of the **§5** categories (or a controlled superset later), for queue triage.

---

## 7. Explicit non-goals (Phase 7 / Step 1)

- No **full Telegram group bot implementation**, webhook changes, or new **API** routes.
- No change to **public booking / payment / Mini App** customer flows.
- No **admin payment** mutations or **operator workflow engine** as defined in [docs/IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Phase 7 “Included Scope” — those remain **future slices** after rules + narrow helpers.

---

## 8. Next implementation alignment (forward pointer)

The **next safe implementation slice** (per [docs/CHAT_HANDOFF.md](CHAT_HANDOFF.md)) should be: **narrow** logic for **group trigger evaluation** and/or **handoff trigger helper** (classification toward **§5**), with tests per [docs/TESTING_STRATEGY.md](TESTING_STRATEGY.md), **without** widening public or admin surfaces beyond scope.

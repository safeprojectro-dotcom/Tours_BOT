
---

## HANDOFF name

`HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP

## Status

**B13C completed (documentation only).** Publish **attempt / audit / idempotency / retry** model documented in **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)**. **No** code, **no** tests, **no** migrations, **no** publish behavior or readiness changes, **no** retry logic, **no** new channels, **no** Mini App / booking / payment / orders.

## Checkpoint (before this step)

- **B13A:** Channel adapter layering design.
- **B13B:** **`ShowcaseChannelAdapter`** + **`TelegramShowcaseChannelAdapter`**; **`SupplierOfferModerationService.publish`** unchanged externally.

## Docs created / updated (finalize)

| Doc | Role |
|-----|------|
| [`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md) | Main B13C design (purpose, baseline, table options, audit, idempotency, retry, transaction boundary, phases, B13D/E). |
| [`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md) | B13C pointer + Related link. |
| [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) | B13C completed bullet. |
| [`docs/CURSOR_PROMPT_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](CURSOR_PROMPT_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md) | Closed truncation; completion note. |

## Key design decisions

- **Publish attempt storage** (table vs JSONB vs logs): trade-offs documented; **durable attempts** recommended **before** automatic retries or aggressive multi-channel concurrency; **product approves** migration.
- **Audit:** actor, correlation/idempotency, status timeline, provider ids; **does not** replace **`operator_workflow`** / **`review-package`** as gate authority.
- **Duplicates:** single-flight + **idempotency key** aligned with **`ShowcaseChannelPublishRequest.idempotency_key`** (still unused in code).
- **Retries:** operator-initiated / classified errors first; **no** silent auto-retry in B13C scope.
- **Side-effect boundary:** document orphan-post / DB-after-send edge; lifecycle **`published`** only when consistent.

## Non-goals (preserved)

B13C slice: **no** implementation, **no** readiness semantics change, **no** showcase output change.

## Tests run (this finalize pass)

**None** — docs-only. B13B matrix (**89** tests) unchanged by this pass.

## Recommended next options

1. **B13D** — publish **attempt table + repository + service skeleton**, **if** product approves migration and scope.
2. **B13D-alt** — **channel preview payload read model** (no migration / lower scope) **if** deferring attempt persistence.
3. **Production publish smoke / content QA** before investing in audit implementation.

(do **not** auto-start migrations or code without explicit decision.)

```

---

## Notes (wrapper)

Canonical design: **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)**. B13 stack: **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)**. Prior: **[`docs/HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md`](HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md)**.
